#!/usr/bin/env python3
"""Generate a PDDL problem for pddl/domain_cellscan_separated.pddl.

Level interpretation (agent, start/target gem metadata, 90/91 target markers)
is shared with pddl/problem_gen.py.  Differences from that generator:

* walls are flat (steel 19, exits 7/8, unmodelled elements, the 1-cell padding)
  or rounded (brick 18); walls inside the level also get (brick c);
* the scan chain is gate(row) -> open (non-wall) cells of the row -> next
  gate ... -> `scan_done`; all rows start dirty;
* the initial state is between ticks (scan pointer on `scan_done`).

Usage:
  python pddl/problem_gen_cellscan.py pddl/level_5_5.txt [-p name] [-d domain]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import problem_gen as base  # noqa: E402

ROUNDED_WALL_IDS = {18}
DONE = "scan_done"


def cell(r: int, c: int) -> str:
    return f"c_{r}_{c}"


def row(r: int) -> str:
    return f"row_{r}"


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


def generate_problem(level_text: str, problem_name: str = "level", domain_name: str = "mine-tick-gravity") -> str:
    prepared = base.prepare_level(level_text)
    rows, cols = prepared.rows, prepared.cols
    ids = list(prepared.cell_ids)
    target = None if prepared.initial_got_gem else prepared.target_gem_pos
    pr, pc = rows + 2, cols + 2  # padded

    def is_open(r: int, c: int) -> bool:
        if r in (0, pr - 1) or c in (0, pc - 1):
            return False
        return base.classify_cell_id(ids[(r - 1) * cols + (c - 1)]) != "brick"

    interior = [cell(r, c) for r in range(1, pr - 1) for c in range(1, pc - 1)]
    border = [cell(r, c) for r in range(pr) for c in range(pc) if r in (0, pr - 1) or c in (0, pc - 1)]
    row_objs = [row(r) for r in range(pr)] + [DONE]

    init = ["(agent-alive)", f"(scan-at {DONE})", f"(scan-done {DONE})"]
    if prepared.initial_got_gem:
        init.append("(got-gem)")
    for r in range(pr):
        if r > 0:
            init.append(f"(row-above {row(r)} {row(r - 1)})")
        for c in range(pc):
            name = cell(r, c)
            init.append(f"(cell-row {name} {row(r)})")
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

    # scan chain: gate -> open cells of the row -> next gate ... -> done
    gated = [r for r in range(1, pr - 1) if any(is_open(r, c) for c in range(1, pc - 1))]
    if gated:
        init.append(f"(first-row {row(gated[0])})")
    for i, r in enumerate(gated):
        nxt = row(gated[i + 1]) if i + 1 < len(gated) else DONE
        init.append(f"(next-row {row(r)} {nxt})")
        init.append(f"(row-dirty {row(r)})")
        open_cols = [c for c in range(1, pc - 1) if is_open(r, c)]
        init.append(f"(row-start {row(r)} {cell(r, open_cols[0])})")
        for j, c in enumerate(open_cols):
            succ = cell(r, open_cols[j + 1]) if j + 1 < len(open_cols) else nxt
            init.append(f"(next-pos {cell(r, c)} {succ})")

    nl = "\n"
    return f"""(define (problem {problem_name})
  (:domain {domain_name})
  (:objects
    {' '.join(interior)} - real-cell
    {' '.join(border)} - border-cell
    {' '.join(row_objs)} - row
  )
  (:init
    (= (total-cost) 0)
{nl.join('    ' + a for a in init)}
  )
  (:goal (and (got-gem) (agent-alive) (scan-at {DONE})))
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
