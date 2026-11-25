#!/usr/bin/env python3
"""Generate a PDDL problem for pddl/domain_rowscan.pddl.

Level interpretation (agent, start/target gem metadata, 90/91 target markers)
is shared with pddl/problem_gen.py.  Differences from the classic generator:

* walls (and the 1-cell padding) are border-cell objects and are not part of
  the scan chain; brick walls (id 18) are rounded, every other wall-like id
  (steel 19, exits 7/8, unmodelled hazards) and the padding are flat;
* the scan chain is gate(row) -> gate(block of BLOCK_WIDTH columns) -> open
  cells of the block -> next block gate ... -> next row gate ... -> done (a
  row whose open cells lie in a single block has no block gate);
* all rows and blocks start dirty, the scan pointer starts on the done sentinel.

Usage:
  python pddl/problem_gen_rowscan.py pddl/level_5_5.txt [-p name] [-d domain]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import problem_gen as base  # noqa: E402

ROUNDED_WALL_IDS = {18}
DONE = "scan_done"
# Columns per block gate inside a row.  Block gates only pay off on wide
# levels (about -40% scan steps on the 38-column benchmark levels, nothing on
# 10-column ones), so by default narrower levels get one block per row, i.e.
# no block gates.  ROWSCAN_BLOCK_WIDTH=<n> forces n-column blocks on every
# level (ROWSCAN_BLOCK_WIDTH=2 is a stress test for tools/sim_check/fuzz.py).
BLOCK_WIDTH = 8
MIN_COLS_FOR_BLOCKS = 17
FORCED_BLOCK_WIDTH = int(os.environ["ROWSCAN_BLOCK_WIDTH"]) if os.environ.get("ROWSCAN_BLOCK_WIDTH") else None


def cell(r: int, c: int) -> str:
    return f"c_{r}_{c}"


def row(r: int) -> str:
    return f"row_{r}"


def block(r: int, i: int) -> str:
    return f"blk_{r}_{i}"


def generate_problem(level_text: str, problem_name: str = "level", domain_name: str = "mine-tick-gravity",
                     block_width: int | None = None) -> str:
    prepared = base.prepare_level(level_text)
    rows, cols = prepared.rows, prepared.cols
    ids = list(prepared.cell_ids)
    target = prepared.target_gem_pos
    pr, pc = rows + 2, cols + 2  # padded

    kind = {}
    for idx, cid in enumerate(ids):
        r, c = divmod(idx, cols)
        kind[(r + 1, c + 1)] = base.classify_cell_id(cid)

    def is_open(r: int, c: int) -> bool:
        return (r, c) in kind and kind[(r, c)] != "brick"

    open_cells = [cell(r, c) for r in range(1, pr - 1) for c in range(1, pc - 1) if is_open(r, c)]
    solid_cells = [cell(r, c) for r in range(pr) for c in range(pc) if not is_open(r, c)]
    row_objs = [row(r) for r in range(pr)] + [DONE]
    if block_width is None:
        block_width = FORCED_BLOCK_WIDTH or (BLOCK_WIDTH if cols >= MIN_COLS_FOR_BLOCKS else cols)
    if block_width < 2 and cols >= 2:
        # (marks c ...) names the blocks of columns k-1 and k+1, which must
        # include column k's block
        raise ValueError("block width must be at least 2")
    nblocks = -(-cols // block_width)

    def blk_index(c: int) -> int:
        """Block of padded column c (border columns belong to the nearest block)."""
        return (min(max(c, 1), cols) - 1) // block_width

    block_objs = [block(r, i) for r in range(pr) for i in range(nblocks)]

    init = ["(agent-alive)", f"(scan-at {DONE})", f"(scan-done {DONE})"]
    if prepared.initial_got_gem:
        init.append("(got-gem)")

    for r in range(pr):
        for c in range(pc):
            name = cell(r, c)
            init.append(f"(cell-row {name} {row(r)})")
            init.append(f"(block-of {name} {block(r, blk_index(c))})")
            ra = max(r - 1, 0)
            init.append(f"(marks {name} {block(r, blk_index(c - 1))} {block(r, blk_index(c + 1))} "
                        f"{block(ra, blk_index(c - 1))} {block(ra, blk_index(c + 1))})")
            if r > 0:
                init.append(f"(up {name} {cell(r - 1, c)})")
            if r < pr - 1:
                init.append(f"(down {name} {cell(r + 1, c)})")
            if c < pc - 1:
                init.append(f"(right-of {name} {cell(r, c + 1)})")
            if not is_open(r, c):
                init.append(f"(full {name})")
                cid = ids[(r - 1) * cols + (c - 1)] if (r, c) in kind else None
                if cid is not None:
                    init.append(f"(brick {name})")
                if cid in ROUNDED_WALL_IDS:
                    init.append(f"(rounded-wall {name})")
                else:
                    init.append(f"(flat-wall {name})")
                continue
            k = kind[(r, c)]
            src_id = ids[(r - 1) * cols + (c - 1)]
            if k == "empty":
                init.append(f"(empty {name})")
            else:
                init.append(f"(full {name})")
                if k == "agent":
                    init.append(f"(agent-at {name})")
                elif k == "dirt":
                    init.append(f"(dirt {name})")
                elif k in ("stone", "gem"):
                    init.append(f"(obj {name})")
                    init.append(f"({k} {name})")
                    falling = src_id in base.STONE_FALLING_IDS or src_id in base.GEM_FALLING_IDS
                    init.append(f"({'falling' if falling else 'resting'} {name})")
                    if k == "gem" and target == (r - 1, c - 1) and not prepared.initial_got_gem:
                        init.append(f"(target-gem {name})")
                else:
                    raise ValueError(f"unexpected cell kind {k}")
        if r > 0:
            init.append(f"(row-above {row(r)} {row(r - 1)})")

    # scan chain: row gate -> block gate -> open cells of the block -> next
    # block gate ... -> next row gate ... -> done (blocks without open cells
    # are left out)
    gated_rows = [r for r in range(1, pr - 1) if any(is_open(r, c) for c in range(1, pc - 1))]
    if gated_rows:
        init.append(f"(first-row {row(gated_rows[0])})")
    for i, r in enumerate(gated_rows):
        nxt_row = row(gated_rows[i + 1]) if i + 1 < len(gated_rows) else DONE
        init.append(f"(next-row {row(r)} {nxt_row})")
        init.append(f"(row-dirty {row(r)})")
        blocks = []
        for b in range(nblocks):
            cs = [c for c in range(1 + b * block_width, min(cols, (b + 1) * block_width) + 1) if is_open(r, c)]
            if cs:
                blocks.append((b, cs))
        if len(blocks) == 1:  # no block gate needed: row gate -> cells -> next row gate
            cs = blocks[0][1]
            init.append(f"(row-start {row(r)} {cell(r, cs[0])})")
            for k, c in enumerate(cs):
                succ = cell(r, cs[k + 1]) if k + 1 < len(cs) else nxt_row
                init.append(f"(next-pos {cell(r, c)} {succ})")
            continue
        init.append(f"(row-first-block {row(r)} {block(r, blocks[0][0])})")
        for j, (b, cs) in enumerate(blocks):
            nxt = block(r, blocks[j + 1][0]) if j + 1 < len(blocks) else nxt_row
            init.append(f"(next-block {block(r, b)} {nxt})")
            init.append(f"(block-dirty {block(r, b)})")
            init.append(f"(block-start {block(r, b)} {cell(r, cs[0])})")
            for k, c in enumerate(cs):
                succ = cell(r, cs[k + 1]) if k + 1 < len(cs) else nxt
                init.append(f"(next-pos {cell(r, c)} {succ})")

    objects = [
        f"    {' '.join(open_cells)} - real-cell",
        f"    {' '.join(solid_cells)} - border-cell",
        f"    {' '.join(row_objs)} - row",
        f"    {' '.join(block_objs)} - block",
    ]
    goal = ["(got-gem)", "(agent-alive)", f"(scan-at {DONE})"]
    nl = "\n"
    return f"""(define (problem {problem_name})
  (:domain {domain_name})
  (:objects
{nl.join(objects)}
  )
  (:init
    (= (total-cost) 0)
{nl.join('    ' + a for a in init)}
  )
  (:goal (and {' '.join(goal)}))
  (:metric minimize (total-cost))
)
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("level_input", help="Level string or .txt path")
    ap.add_argument("-p", "--problem-name", default="", help="Problem name (default: level file stem)")
    ap.add_argument("-d", "--domain-name", default="mine-tick-gravity")
    ap.add_argument("-a", "--agent-name", default="player", help="ignored (compatibility)")
    args = ap.parse_args()
    if args.level_input.endswith(".txt"):
        text = Path(args.level_input).read_text(encoding="utf-8")
        name = args.problem_name or Path(args.level_input).stem
    else:
        text = args.level_input
        name = args.problem_name or "level"
    try:
        sys.stdout.write(generate_problem(text, name, args.domain_name))
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
