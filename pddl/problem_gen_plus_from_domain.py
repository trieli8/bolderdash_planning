#!/usr/bin/env python3
"""Generate border-padded PDDL+ problems for domain_plus_from_domain.pddl."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import problem_gen as base  # type: ignore  # noqa: E402


def _read_level(level_input: str) -> str:
    if level_input.endswith(".txt"):
        return Path(level_input).read_text(encoding="utf-8")
    return level_input


def _cell_name(r: int, c: int) -> str:
    return f"c_{r}_{c}"


def _interior_cell_name(r: int, c: int) -> str:
    return _cell_name(r + 1, c + 1)


def generate_compact_problem(level_str: str, problem_name: str, domain_name: str) -> str:
    prepared = base.prepare_level(level_str)
    rows = prepared.rows
    cols = prepared.cols
    cell_ids = list(prepared.cell_ids)
    target_gem_pos = prepared.target_gem_pos

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

    for idx, cell_id in enumerate(cell_ids):
        r = idx // cols
        c = idx % cols
        kind = base.classify_cell_id(cell_id)
        contents[(r, c)] = kind
        if cell_id in base.STONE_FALLING_IDS or cell_id in base.GEM_FALLING_IDS:
            falling_cells.add((r, c))
    agent_pos = prepared.agent_pos

    init_lines = []
    init_lines.append("    (agent-alive)")
    init_lines.append("    (scan-complete)")
    if prepared.initial_got_gem:
        init_lines.append("    (got-gem)")

    ar, ac = agent_pos[0] + 1, agent_pos[1] + 1
    init_lines.append(f"    (agent-at {_cell_name(ar, ac)})")

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
                if (r - 1, c - 1) == target_gem_pos and not prepared.initial_got_gem:
                    init_lines.append(f"    (target-gem {cname})")
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

    for c in range(cols):
        init_lines.append(f"    (bottom {_interior_cell_name(r=rows - 1, c=c)})")

    obj_lines = [f"    {' '.join(interior_cells + border_cells)}"]

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
    ap = argparse.ArgumentParser(description="Convert a Stones & Gems level into a border-padded PDDL+ problem.")
    ap.add_argument("level_input", help="Level string or .txt path")
    ap.add_argument("-p", "--problem-name", default="")
    ap.add_argument("-d", "--domain-name", default="mine-tick-gravity-plus-from-domain")
    args = ap.parse_args()

    if not args.problem_name:
        args.problem_name = args.level_input.rsplit(".", 1)[0] if args.level_input.endswith(".txt") else "level_plus"

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
