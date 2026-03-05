#!/usr/bin/env python3
"""Generate typed scanner-separated event problems with per-entity x/y fluents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import problem_gen as base  # type: ignore  # noqa: E402


def _read_level(level_input: str) -> str:
    if level_input.endswith(".txt"):
        return Path(level_input).read_text(encoding="utf-8").strip()
    return level_input


def _cell_name(r: int, c: int) -> str:
    return f"c_{r}_{c}"


def _interior_cell_name(r: int, c: int) -> str:
    return _cell_name(r + 1, c + 1)


def generate_compact_problem(level_str: str, problem_name: str, domain_name: str) -> str:
    rows, cols, _max_time, _required_gems, cell_ids = base.parse_level_string(level_str)

    padded_rows = rows + 2
    padded_cols = cols + 2

    interior_cells = [_interior_cell_name(r, c) for r in range(rows) for c in range(cols)]
    border_cells = [
        _cell_name(r, c)
        for r in range(padded_rows)
        for c in range(padded_cols)
        if r == 0 or r == padded_rows - 1 or c == 0 or c == padded_cols - 1
    ]
    left_void = "left_void"
    border_cells.append(left_void)

    contents = {}
    falling_cells = set()
    agent_pos = None
    stone_positions = []
    gem_positions = []

    for idx, cell_id in enumerate(cell_ids):
        r = idx // cols
        c = idx % cols
        kind = base.classify_cell_id(cell_id)
        contents[(r, c)] = kind
        if cell_id in base.STONE_FALLING_IDS or cell_id in base.GEM_FALLING_IDS:
            falling_cells.add((r, c))
        if kind == "agent":
            if agent_pos is not None:
                raise ValueError("Multiple agent cells found; expected exactly one.")
            agent_pos = (r, c)
        elif kind == "stone":
            stone_positions.append((r, c))
        elif kind == "gem":
            gem_positions.append((r, c))

    if agent_pos is None:
        raise ValueError("No agent found in level.")

    agent_obj = "agent_0"
    stone_objs = [f"stone_{i}" for i in range(len(stone_positions))]
    gem_objs = [f"gem_{i}" for i in range(len(gem_positions))]

    init_lines = []
    init_lines.append("    (agent-alive)")
    init_lines.append("    (scan-complete)")
    init_lines.append(f"    (agent-entity {agent_obj})")

    ar, ac = agent_pos[0] + 1, agent_pos[1] + 1
    agent_cell = _cell_name(ar, ac)
    init_lines.append(f"    (agent-at {agent_cell})")
    init_lines.append(f"    (agent-at-obj {agent_obj} {agent_cell})")
    init_lines.append(f"    (= (x {agent_obj}) {ar})")
    init_lines.append(f"    (= (y {agent_obj}) {ac})")

    for stone_obj, (r, c) in zip(stone_objs, stone_positions):
        pr, pc = r + 1, c + 1
        cell = _cell_name(pr, pc)
        init_lines.append(f"    (stone-entity {stone_obj})")
        init_lines.append(f"    (stone-at {stone_obj} {cell})")
        init_lines.append(f"    (= (x {stone_obj}) {pr})")
        init_lines.append(f"    (= (y {stone_obj}) {pc})")

    for gem_obj, (r, c) in zip(gem_objs, gem_positions):
        pr, pc = r + 1, c + 1
        cell = _cell_name(pr, pc)
        init_lines.append(f"    (gem-entity {gem_obj})")
        init_lines.append(f"    (gem-at {gem_obj} {cell})")
        init_lines.append(f"    (= (x {gem_obj}) {pr})")
        init_lines.append(f"    (= (y {gem_obj}) {pc})")

    for r in range(padded_rows):
        for c in range(padded_cols):
            cname = _cell_name(r, c)
            init_lines.append(f"    (= (cx {cname}) {r})")
            init_lines.append(f"    (= (cy {cname}) {c})")
    init_lines.append(f"    (= (cx {left_void}) -1)")
    init_lines.append(f"    (= (cy {left_void}) -1)")

    for r in range(padded_rows):
        for c in range(padded_cols):
            cname = _cell_name(r, c)
            is_border = r == 0 or r == padded_rows - 1 or c == 0 or c == padded_cols - 1

            if is_border:
                init_lines.append(f"    (border-cell {cname})")
                init_lines.append(f"    (not (empty {cname}))")
                continue

            init_lines.append(f"    (real-cell {cname})")
            kind = contents[(r - 1, c - 1)]

            if kind == "agent":
                init_lines.append(f"    (not (empty {cname}))")
            elif kind == "empty":
                init_lines.append(f"    (empty {cname})")
            elif kind == "dirt":
                init_lines.append(f"    (dirt {cname})")
            elif kind == "stone":
                init_lines.append(f"    (stone {cname})")
            elif kind == "gem":
                init_lines.append(f"    (gem {cname})")
            elif kind == "brick":
                init_lines.append(f"    (brick {cname})")

            if (r - 1, c - 1) in falling_cells:
                init_lines.append(f"    (falling {cname})")

    init_lines.append(f"    (border-cell {left_void})")
    init_lines.append(f"    (not (empty {left_void}))")

    for r in range(padded_rows):
        for c in range(padded_cols):
            here = _cell_name(r, c)
            if r > 0:
                init_lines.append(f"    (up {here} {_cell_name(r - 1, c)})")
            if r < padded_rows - 1:
                init_lines.append(f"    (down {here} {_cell_name(r + 1, c)})")
            if c == 0:
                init_lines.append(f"    (right-of {left_void} {here})")
            else:
                init_lines.append(f"    (right-of {_cell_name(r, c - 1)} {here})")

    order = [_interior_cell_name(r, c) for r in range(rows) for c in range(cols)]
    if order:
        init_lines.append(f"    (first-cell {order[0]})")
        init_lines.append(f"    (last-cell {order[-1]})")
        for i in range(len(order) - 1):
            init_lines.append(f"    (next-cell {order[i]} {order[i + 1]})")

    obj_lines = []
    obj_lines.append(f"    {' '.join(interior_cells + border_cells)} - cell")
    obj_lines.append(f"    {agent_obj} - agent")
    if stone_objs:
        obj_lines.append(f"    {' '.join(stone_objs)} - stone")
    if gem_objs:
        obj_lines.append(f"    {' '.join(gem_objs)} - gem")

    goal_lines = [
        "    (got-gem)",
        "    (scan-complete)",
        "    (not (crushed))",
        "    (agent-alive)",
    ]

    pddl = f"""\
(define (problem {problem_name})
  (:domain {domain_name})
  (:objects
{chr(10).join(obj_lines)}
  )
  (:init
  (= (total-cost) 0)
  (= (sim-time) 0)
{chr(10).join(init_lines)}
  )
  (:goal
  (and
{chr(10).join(goal_lines)}
  ))
  (:metric minimize (total-cost))
)
"""
    return pddl


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert a level into a typed fluent-position scanner-separated-events PDDL+ problem.")
    ap.add_argument("level_input", help="Level string or .txt path")
    ap.add_argument("-p", "--problem-name", default="")
    ap.add_argument("-d", "--domain-name", default="mine-tick-gravity-plus-scanner-separated-events-fluents-trimmed")
    args = ap.parse_args()

    if not args.problem_name:
        args.problem_name = args.level_input.rsplit(".", 1)[0] if args.level_input.endswith(".txt") else "level_plus_scanner_events_fluents_trimmed"

    try:
        level_str = _read_level(args.level_input)
        pddl = generate_compact_problem(level_str, args.problem_name, args.domain_name)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    sys.stdout.write(pddl)

    try:
        Path(f"{args.problem_name}.pddl").write_text(pddl, encoding="utf-8")
    except Exception as exc:
        sys.stderr.write(f"Warning: failed to write {args.problem_name}.pddl: {exc}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
