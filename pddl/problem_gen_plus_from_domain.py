#!/usr/bin/env python3
"""Generate compact PDDL problems for domain_plus_from_domain.pddl."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

import problem_gen as base  # type: ignore  # noqa: E402


def _read_level(level_input: str) -> str:
    if level_input.endswith('.txt'):
        return Path(level_input).read_text(encoding='utf-8').strip()
    return level_input


def _cell_name(r: int, c: int) -> str:
    return f"c_{r}_{c}"


def generate_compact_problem(level_str: str, problem_name: str, domain_name: str) -> str:
    rows, cols, _max_time, _required_gems, cell_ids = base.parse_level_string(level_str)

    cells = [_cell_name(r, c) for r in range(rows) for c in range(cols)]

    contents = {}
    falling_cells = set()
    agent_pos = None

    for idx, cell_id in enumerate(cell_ids):
        r = idx // cols
        c = idx % cols
        kind = base.classify_cell_id(cell_id)
        contents[(r, c)] = kind
        if cell_id in base.STONE_FALLING_IDS or cell_id in base.GEM_FALLING_IDS:
            falling_cells.add((r, c))
        if kind == 'agent':
            if agent_pos is not None:
                raise ValueError('Multiple agent cells found; expected exactly one.')
            agent_pos = (r, c)

    if agent_pos is None:
        raise ValueError('No agent found in level.')

    init_lines = []
    init_lines.append('    (agent-alive)')
    init_lines.append('    (scan-complete)')
    init_lines.append(f"    (agent-at {_cell_name(agent_pos[0], agent_pos[1])})")

    for r in range(rows):
        for c in range(cols):
            cname = _cell_name(r, c)
            kind = contents[(r, c)]
            if kind == 'empty':
                init_lines.append(f"    (empty {cname})")
            elif kind == 'dirt':
                init_lines.append(f"    (dirt {cname})")
            elif kind == 'stone':
                init_lines.append(f"    (stone {cname})")
            elif kind == 'gem':
                init_lines.append(f"    (gem {cname})")
            elif kind == 'brick':
                init_lines.append(f"    (brick {cname})")
            elif kind == 'agent':
                # Agent occupies this cell; do not mark empty.
                pass

            if (r, c) in falling_cells:
                init_lines.append(f"    (falling {cname})")

            if r == rows - 1:
                init_lines.append(f"    (bottom {cname})")

    for r in range(rows):
        for c in range(cols):
            here = _cell_name(r, c)
            if r > 0:
                init_lines.append(f"    (up {here} {_cell_name(r - 1, c)})")
            if r < rows - 1:
                init_lines.append(f"    (down {here} {_cell_name(r + 1, c)})")
            if c < cols - 1:
                init_lines.append(f"    (right-of {here} {_cell_name(r, c + 1)})")

    order = [_cell_name(r, c) for r in range(rows) for c in range(cols)]
    init_lines.append(f"    (first-cell {order[0]})")
    init_lines.append(f"    (last-cell {order[-1]})")
    for i in range(len(order) - 1):
        init_lines.append(f"    (next-cell {order[i]} {order[i + 1]})")

    goal_lines = [
        '    (got-gem)',
        '    (scan-complete)',
        '    (not (crushed))',
        '    (agent-alive)',
    ]

    pddl = f"""\
(define (problem {problem_name})
  (:domain {domain_name})
  (:objects
    {' '.join(cells)}
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
    ap = argparse.ArgumentParser(description='Convert a Stones & Gems level into a compact PDDL+ problem.')
    ap.add_argument('level_input', help='Level string or .txt path')
    ap.add_argument('-p', '--problem-name', default='')
    ap.add_argument('-d', '--domain-name', default='mine-tick-gravity-plus-from-domain')
    args = ap.parse_args()

    if not args.problem_name:
        args.problem_name = args.level_input.rsplit('.', 1)[0] if args.level_input.endswith('.txt') else 'level_plus'

    try:
        level_str = _read_level(args.level_input)
        pddl = generate_compact_problem(level_str, args.problem_name, args.domain_name)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    sys.stdout.write(pddl)

    try:
        Path(f"{args.problem_name}.pddl").write_text(pddl, encoding='utf-8')
    except Exception as exc:
        sys.stderr.write(f"Warning: failed to write {args.problem_name}.pddl: {exc}\n")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
