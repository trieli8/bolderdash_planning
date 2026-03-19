#!/usr/bin/env python3
"""Generate border-padded PDDL+ problems for domain_plus_from_domain_int_state.pddl."""

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


def _state_for_cell_id(cell_id: int) -> int:
    """Map parsed level IDs to numeric cell-state values used in the int-state domain."""
    if cell_id in base.AGENT_IDS:
        return 0
    if cell_id in base.EMPTY_IDS:
        return 1
    if cell_id in base.DIRT_IDS:
        return 2
    if cell_id in base.STONE_IDS:
        if cell_id in base.STONE_FALLING_IDS:
            return 4
        return 3
    if cell_id in base.GEM_IDS:
        return 6 if cell_id in base.GEM_FALLING_IDS else 5
    if cell_id in base.BRICK_IDS:
        # Keep original numbering from definitions.h where available.
        if cell_id in {7, 8, 18, 19, 20, 21, 22}:
            return cell_id
        return 18
    raise ValueError(f"Unsupported cell ID {cell_id}; extend _state_for_cell_id().")


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
    agent_pos = None

    for idx, cell_id in enumerate(cell_ids):
        r = idx // cols
        c = idx % cols
        state = _state_for_cell_id(cell_id)
        contents[(r, c)] = state
        if state == 0:
            if agent_pos is not None:
                raise ValueError("Multiple agent cells found; expected exactly one.")
            agent_pos = (r, c)

    if agent_pos is None:
        raise ValueError("No agent found in level.")

    init_lines = []
    init_lines.append("    (agent-alive)")
    init_lines.append("    (scan-complete)")
    init_lines.append("    (= (sim-time) 0)")
    init_lines.append("    (= (tick) 0)")

    for r in range(padded_rows):
        for c in range(padded_cols):
            cname = _cell_name(r, c)
            is_border = r == 0 or r == padded_rows - 1 or c == 0 or c == padded_cols - 1

            if is_border:
                init_lines.append(f"    (border-cell {cname})")
                init_lines.append(f"    (= (cell-state {cname}) 19)")
                init_lines.append(f"    (= (last-updated-tick {cname}) 0)")
                continue

            init_lines.append(f"    (real-cell {cname})")
            state = contents[(r - 1, c - 1)]
            init_lines.append(f"    (= (cell-state {cname}) {state})")
            init_lines.append(f"    (= (last-updated-tick {cname}) 0)")

    init_lines.append(f"    (border-cell {left_void})")
    init_lines.append(f"    (= (cell-state {left_void}) 19)")
    init_lines.append(f"    (= (last-updated-tick {left_void}) 0)")

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
    ap = argparse.ArgumentParser(description="Convert a Stones & Gems level into a border-padded int-state PDDL+ problem.")
    ap.add_argument("level_input", help="Level string or .txt path")
    ap.add_argument("-p", "--problem-name", default="")
    ap.add_argument("-d", "--domain-name", default="mine-tick-gravity-plus-from-domain-int-state")
    args = ap.parse_args()

    if not args.problem_name:
        args.problem_name = args.level_input.rsplit(".", 1)[0] if args.level_input.endswith(".txt") else "level_plus_int_state"

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
