#!/usr/bin/env python3
"""Generate a PDDL problem for pddl/domain_orderfree_{combined,separated}.pddl.

Cell contents and walls are encoded as in pddl/problem_gen_cellscan.py
(brick 18 rounded; steel, exits, unmodelled elements and the 1-cell padding
flat).  There is no scan chain.  Each padded row is extended by a
`left_void` / `right_void` neighbour so that every cell inside the level has
the full conflict window used by the order-free physics actions (two cells
left in its row, k-2..k+2 in the row above); the void cells never hold
anything.  The initial state is between ticks (no update-required).

Usage:
  python pddl/problem_gen_orderfree.py pddl/level_5_5.txt [-p name] [-d domain]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import problem_gen as base  # noqa: E402
from problem_gen_cellscan import cell, content_facts  # noqa: E402

LEFT_VOID, RIGHT_VOID = "left_void", "right_void"


def generate_problem(level_text: str, problem_name: str = "level", domain_name: str = "mine-tick-gravity") -> str:
    prepared = base.prepare_level(level_text)
    rows, cols = prepared.rows, prepared.cols
    ids = list(prepared.cell_ids)
    target = None if prepared.initial_got_gem else prepared.target_gem_pos
    pr, pc = rows + 2, cols + 2  # padded

    interior = [cell(r, c) for r in range(1, pr - 1) for c in range(1, pc - 1)]
    border = [cell(r, c) for r in range(pr) for c in range(pc) if r in (0, pr - 1) or c in (0, pc - 1)]

    init = ["(agent-alive)"]
    if prepared.initial_got_gem:
        init.append("(got-gem)")
    for r in range(pr):
        init.append(f"(right-of {LEFT_VOID} {cell(r, 0)})")
        init.append(f"(right-of {cell(r, pc - 1)} {RIGHT_VOID})")
        for c in range(pc):
            name = cell(r, c)
            if r > 0:
                init.append(f"(up {name} {cell(r - 1, c)})")
            if r < pr - 1:
                init.append(f"(down {name} {cell(r + 1, c)})")
            if c < pc - 1:
                init.append(f"(right-of {name} {cell(r, c + 1)})")
            if r in (0, pr - 1) or c in (0, pc - 1):
                init.append(f"(flat-wall {name})")
            else:
                cid = ids[(r - 1) * cols + (c - 1)]
                init.extend(content_facts(name, cid, target == (r - 1, c - 1)))

    nl = "\n"
    return f"""(define (problem {problem_name})
  (:domain {domain_name})
  (:objects
    {' '.join(interior)} - real-cell
    {' '.join(border + [LEFT_VOID, RIGHT_VOID])} - border-cell
  )
  (:init
    (= (total-cost) 0)
{nl.join('    ' + a for a in init)}
  )
  (:goal (and (got-gem) (agent-alive) (not (update-required))))
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
