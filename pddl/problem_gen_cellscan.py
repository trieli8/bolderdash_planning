#!/usr/bin/env python3
"""Generate a PDDL problem for pddl/domain_cellscan_separated.pddl.

Level interpretation (agent, start/target gem metadata, 90/91 target markers)
is shared with pddl/problem_gen.py.  Differences from that generator:

* walls are flat (steel 19, exits 7/8, unmodelled elements, the 1-cell padding)
  or rounded (brick 18); walls inside the level also get (brick c);
* the scan chain visits every cell inside the level in row-major order and
  ends on the `scan_end` sentinel;
* the initial state is between ticks (scan-complete).

Goal: the target gem, or with --collect-gems N (or a `; collect-gems: N` line
in the level file) any N gems; `level` uses the level's required_gems field.

Usage:
  python pddl/problem_gen_cellscan.py pddl/level_5_5.txt [-p name] [-d domain] [--collect-gems N|level]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import problem_gen as base  # noqa: E402

ROUNDED_WALL_IDS = {18}
SCAN_END = "scan_end"


def cell(r: int, c: int) -> str:
    return f"c_{r}_{c}"


def content_facts(name: str, cid: int, target: bool) -> list[str]:
    """Init facts for a cell inside the level (padded name, engine id)."""
    kind = base.classify_cell_id(cid)
    if kind == "brick":
        return [f"(brick {name})", f"({'rounded-wall' if cid in ROUNDED_WALL_IDS else 'flat-wall'} {name})"]
    if kind == "agent":
        return [f"(agent-at {name})"]
    if kind in ("empty", "dirt"):
        return [f"({kind} {name})"]
    facts = [f"({kind} {name})"]  # stone / gem
    if cid in base.STONE_FALLING_IDS or cid in base.GEM_FALLING_IDS:
        facts.append(f"(falling {name})")
    if kind == "gem" and target:
        facts.append(f"(target-gem {name})")
    return facts


def generate_problem(
    level_text: str,
    problem_name: str = "level",
    domain_name: str = "mine-tick-gravity",
    collect_gems: int | str | None = None,
) -> str:
    prepared = base.prepare_level(level_text, base.LevelMetadata(collect_gems=collect_gems))
    counts, count_init, count_goal = base.gem_counter(prepared.collect_gems)
    rows, cols = prepared.rows, prepared.cols
    ids = list(prepared.cell_ids)
    target = None if prepared.initial_got_gem else prepared.target_gem_pos
    pr, pc = rows + 2, cols + 2  # padded

    interior = [cell(r, c) for r in range(1, pr - 1) for c in range(1, pc - 1)]
    border = [cell(r, c) for r in range(pr) for c in range(pc) if r in (0, pr - 1) or c in (0, pc - 1)]

    init = ["(agent-alive)", "(scan-complete)"]
    if prepared.initial_got_gem:
        init.append("(got-gem)")
    init.extend(count_init)
    for r in range(pr):
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

    order = interior + [SCAN_END]
    init.append(f"(first-cell {order[0]})")
    init.extend(f"(next-cell {a} {b})" for a, b in zip(order, order[1:]))
    init.append(f"(last-cell {SCAN_END})")

    nl = "\n"
    return f"""(define (problem {problem_name})
  (:domain {domain_name})
  (:objects
    {' '.join(interior)} - real-cell
    {' '.join(border + [SCAN_END])} - border-cell
    {' '.join(counts)} - {base.GEM_COUNT_TYPE}
  )
  (:init
    (= (total-cost) 0)
{nl.join('    ' + a for a in init)}
  )
  (:goal (and {count_goal or '(got-gem)'} (agent-alive) (scan-complete)))
  (:metric minimize (total-cost))
)
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("level_input", help="Level string or .txt path")
    ap.add_argument("-p", "--problem-name", default="", help="Problem name (default: level file stem)")
    ap.add_argument("-d", "--domain-name", default="mine-tick-gravity")
    ap.add_argument("-a", "--agent-name", default="player", help="ignored (compatibility)")
    ap.add_argument(
        "--collect-gems",
        default=None,
        metavar="N|level",
        help="Goal: collect any N gems instead of the target gem ('level': the level's "
        "required_gems field).  Overrides a `; collect-gems:` line in the level file.",
    )
    args = ap.parse_args()
    if args.level_input.endswith(".txt"):
        text = Path(args.level_input).read_text(encoding="utf-8")
        name = args.problem_name or Path(args.level_input).stem
    else:
        text = args.level_input
        name = args.problem_name or "level"
    try:
        sys.stdout.write(generate_problem(text, name, args.domain_name, args.collect_gems))
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
