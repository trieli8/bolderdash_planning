#!/usr/bin/env python3
"""
sng_log_to_posthoc.py

Convert Stones'n'Gems search logs into a Posthoc YAML with a 2D tile renderer.

Key points (updated):
- Renderer reads event payload via $.event[...] (matches your working Posthoc example).
- Tree linkage uses pId (NOT parent/parent_id). Output events include pId only.
- If log lines contain state_id + parent_id, we use them exactly:
    - id := state_id
    - pId := parent_id (or -1 if missing/None)
- Optional level file supplies width/height and static terrain and can be arbitrarily
  wrapped across lines; we ignore whitespace AND line breaks by treating it as a stream
  of integers separated by '|'.

Usage:
  python sng_log_to_posthoc.py search.log --level level.txt > out.posthoc.yaml
  cat search.log | python sng_log_to_posthoc.py - --level level.txt > out.posthoc.yaml
  python sng_log_to_posthoc.py search.log > out.posthoc.yaml   # if no level file
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# --- Render codes used in Posthoc tiles (visualisation codes, not game enums) ---
EMPTY = 0
DIRT = 1
STONE = 2
GEM = 3
AGENT = 4
BRICK = 5
FALLING_STONE = 6
FALLING_GEM = 7
OTHER = 8  # fallback for any unhandled terrain from level file


# Finds trailing JSON object in lines like: [t=...] {...}
LOG_RE = re.compile(r"\{.*\}\s*$")


@dataclass
class Level:
    w: int
    h: int
    base: List[List[int]]  # [row][col] = render code


@dataclass
class Node:
    id: int                 # state_id
    pId: int                # parent_id or -1
    type: str               # expand/dead_end/etc
    g: int
    real_g: int
    payload: Dict[str, Any]
    board: List[List[int]]  # final merged board [row][col] render codes


def parse_line_to_payload(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line:
        return None
    m = LOG_RE.search(line)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def parse_level_file(path: str) -> Level:
    """
    Level file parser that ignores ALL whitespace and ALL line breaks.

    Treat file as a stream of integers separated by '|'.

    Rules:
      - First two ints: width, height
      - Next (width * height) ints: grid, row-major
    """
    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    tokens = [tok.strip() for tok in raw_text.split("|") if tok.strip() != ""]
    values = [int(tok) for tok in tokens]

    if len(values) < 2:
        raise ValueError("Level file must contain at least width and height")

    w, h = values[1], values[0]
    expected = w * h

    if len(values) < 2 + expected:
        raise ValueError(
            f"Level file too short: expected {expected} grid values, got {len(values) - 2}"
        )

    grid_vals = values[2: 2 + expected]
    raw: List[List[int]] = [grid_vals[r * w: (r + 1) * w] for r in range(h)]

    # Detect legacy vs canonical encoding
    has_2 = any(v == 2 for v in grid_vals)
    legacy = not has_2

    def level_val_to_render_code(v: int) -> int:
        if legacy:
            # Matches your sample levels (heuristic)
            if v == 0:
                return EMPTY
            if v == 1:
                return DIRT
            if v == 3:
                return STONE
            if v == 5:
                return GEM
            if v == 18:
                return BRICK
            return OTHER
        else:
            # More canonical-ish mapping
            if v == 1:
                return EMPTY
            if v == 2:
                return DIRT
            if v in (3, 4):
                return STONE
            if v in (5, 6):
                return GEM
            if v in (18, 19):
                return BRICK
            return OTHER

    base = [[level_val_to_render_code(raw[y][x]) for x in range(w)] for y in range(h)]
    return Level(w=w, h=h, base=base)


def infer_board_dims_from_payloads(payloads: List[Dict[str, Any]]) -> Tuple[int, int]:
    """If no level file, infer (N,N) from the max index in payload lists."""
    max_idx = -1
    for p in payloads:
        for key in ("agent", "gems", "stones", "dirt", "bricks", "falling_gems", "falling_stones"):
            v = p.get(key)
            if v is None:
                continue
            if isinstance(v, int):
                max_idx = max(max_idx, v)
            elif isinstance(v, list) and v:
                max_idx = max(max_idx, max(v))

    size = max_idx + 1
    if size <= 0:
        return (1, 1)
    root = int(size ** 0.5)
    n = root
    while n * n < size:
        n += 1
    return (n, n)


def idx_to_xy(idx: int, w: int) -> Tuple[int, int]:
    """0-based linear index -> (x,y) 0-based, row-major with width w."""
    return (idx % w, idx // w)


def overlay_dynamic_on_base(p: Dict[str, Any], base: List[List[int]], w: int, h: int) -> List[List[int]]:
    """
    Merge layers:
      1) base terrain
      2) payload dirt/bricks (if present)
      3) stones/gems
      4) falling stones/gems
      5) agent (top)
    """
    board = [row[:] for row in base]

    def place(indices: List[int], code: int):
        for idx in indices:
            if idx is None or idx < 0:
                continue
            x, y = idx_to_xy(idx, w)
            if 0 <= x < w and 0 <= y < h:
                board[y][x] = code

    place(p.get("dirt", []) or [], DIRT)
    place(p.get("bricks", []) or [], BRICK)

    place(p.get("stones", []) or [], STONE)
    place(p.get("gems", []) or [], GEM)

    place(p.get("falling_stones", []) or [], FALLING_STONE)
    place(p.get("falling_gems", []) or [], FALLING_GEM)

    agent = p.get("agent", None)
    if isinstance(agent, int) and agent >= 0:
        x, y = idx_to_xy(agent, w)
        if 0 <= x < w and 0 <= y < h:
            board[y][x] = AGENT

    return board


def build_nodes(payloads: List[Dict[str, Any]], level: Level) -> List[Node]:
    """
    Build nodes using exact ids if present:
      id  := state_id (fallback to 'id' or sequence)
      pId := parent_id (fallback to -1)
    """
    nodes: List[Node] = []

    for i, p in enumerate(payloads):
        node_id = int(p.get("state_id", p.get("id", i)))
        parent_raw = p.get("parent_id", None)
        pId = int(parent_raw) if parent_raw is not None else -1

        action = str(p.get("action", "event"))
        g = int(p.get("g", 0))
        real_g = int(p.get("real_g", g))

        board = overlay_dynamic_on_base(p, level.base, level.w, level.h)

        nodes.append(
            Node(
                id=node_id,
                pId=pId,
                type=action,
                g=g,
                real_g=real_g,
                payload=p,
                board=board,
            )
        )

    return nodes


def emit_posthoc_yaml(nodes: List[Node], w: int, h: int) -> str:
    """
    Posthoc YAML:
    - tile text/fill read event payload via $.event[...] (your working pattern).
    - keys are c_<x>_<y> (1-based).
    - events include: c_x_y, id, pId, type, g, real_g, plus a few debug fields.
    """

    # NOTE: uses $.event[...] not $[...]
    glyph_expr = (
        "{{"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 0) ? '' : "
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 1) ? '.' : "
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 2) ? 'o' : "
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 3) ? '*' : "
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 4) ? '@' : "
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 5) ? '#' : "
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 6) ? 'O' : "
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 7) ? '+' : '?'"
        "}}"
    )
    fill_expr = (
        "{{"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 0) ? 'black' :"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 1) ? 'brown' :"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 2) ? 'grey' :"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 3) ? 'blue' :"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 4) ? 'yellow' :"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 5) ? 'indigo' :"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 6) ? 'grey' :"
        "(+$.event[`c_${$.tile_x}_${$.tile_y}`] === 7) ? 'blue' : 'orange'"
        "}}"
    )
    


    out: List[str] = []
    out.append("version: 1.0.5\n")
    out.append("render:\n")
    out.append("  components:\n")
    out.append("    tile:\n")
    out.append("      - $: rect\n")
    out.append("        width: 0.98\n")
    out.append("        height: 0.98\n")
    out.append(f"        text: \"{glyph_expr}\"\n")
    out.append("        textX: 0.35\n")
    out.append("        textY: 0.72\n")
    out.append(f"        fill: \"{fill_expr}\"\n")
    out.append("        fontSize: 0.75\n")
    out.append("        fontColor: \"{{$.themeBackground}}\"\n")
    out.append("        x: \"{{$.tile_x}}\"\n")
    out.append("        y: \"{{$.tile_y}}\"\n")
    out.append("        display: persistent\n\n")

    out.append("    tileboard:\n")
    for y in range(1, h + 1):
        for x in range(1, w + 1):
            out.append("      - $: tile\n")
            out.append(f"        tile_x: {x}\n")
            out.append(f"        tile_y: {y}\n")

    out.append("\n")
    out.append("  views:\n")
    out.append("    main:\n")
    out.append("      components:\n")
    out.append("        - $: tileboard\n\n")

    out.append("events:\n")
    for n in nodes:
        # Cells
        event_obj: Dict[str, Any] = {}
        for yy in range(h):
            for xx in range(w):
                event_obj[f"c_{xx+1}_{yy+1}"] = n.board[yy][xx]

        # Required-ish metadata
        event_obj["id"] = n.id
        event_obj["pId"] = n.pId
        event_obj["type"] = n.type
        event_obj["g"] = n.g
        event_obj["real_g"] = n.real_g

        # Helpful debug fields
        event_obj["action"] = n.payload.get("action", "")
        event_obj["last_op"] = n.payload.get("last_op", "")
        event_obj["agent_idx"] = n.payload.get("agent", -1)
        event_obj["state_id"] = n.payload.get("state_id", n.id)

        # YAML-ish dump (simple and Posthoc-friendly)
        out.append("  - ")
        first = True
        for k, v in event_obj.items():
            if first:
                out.append(f"\"{k}\": {json.dumps(v)}\n")
                first = False
            else:
                out.append(f"    \"{k}\": {json.dumps(v)}\n")

    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Path to log file, or '-' for stdin")
    ap.add_argument("--level", help="Optional level file path (pipe-delimited).", default=None)
    args = ap.parse_args()

    if args.input == "-":
        import sys
        lines = sys.stdin.read().splitlines()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    payloads: List[Dict[str, Any]] = []
    for line in lines:
        p = parse_line_to_payload(line)
        if p is not None:
            payloads.append(p)

    if not payloads:
        raise SystemExit("No JSON payloads found in input.")

    if args.level:
        level = parse_level_file(args.level)
    else:
        w, h = infer_board_dims_from_payloads(payloads)
        level = Level(w=w, h=h, base=[[EMPTY for _ in range(w)] for _ in range(h)])

    nodes = build_nodes(payloads, level)
    print(emit_posthoc_yaml(nodes, level.w, level.h))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())