#!/usr/bin/env python3
"""Write the multi-gem benchmark problems (pddl/test_problems_multigem/{n2,n3}).

Each problem extends one of the 24 bd_level_01 start/target problems that
tools/benchmarking/fd_sweep.py samples from pddl/test_problems/{h1,h2}: the
start gem and the target stay, and one (n2) or two (n3) more gems, picked with
a seed derived from the file name, are marked as targets too.  The n3 targets
contain the n2 targets, so n1 -> n2 -> n3 adds one target at a time.

Files are self-contained level text like the h1/h2 files (agent on the start
gem, targets marked 90 / 91) and are named with the original level-1 gem
ordinals:  bd_level_01_start_gem_<s>_targets_<a>_<b>[_<c>].txt

Usage:
  python3 tools/generate_multigem_problems.py
"""

from __future__ import annotations

import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pddl"))
sys.path.insert(0, str(ROOT / "tools" / "benchmarking"))

import problem_gen as base  # type: ignore  # noqa: E402
from fd_sweep import problems  # type: ignore  # noqa: E402

OUT = ROOT / "pddl" / "test_problems_multigem"
NAME_RE = re.compile(r"bd_level_01_start_gem_(\d+)_target_gem_(\d+)$")


def main() -> int:
    bases = [p for s, p in problems() if s == "l1"]
    for n in (2, 3):
        d = OUT / f"n{n}"
        d.mkdir(parents=True, exist_ok=True)
        for stale in d.glob("*.txt"):
            stale.unlink()
    written = 0
    for rel in bases:
        path = ROOT / rel
        m = NAME_RE.match(path.stem)
        if not m:
            raise SystemExit(f"unexpected base problem name {path.name}")
        s_ord, t_ord = int(m.group(1)), int(m.group(2))
        text = path.read_text().strip()
        rows, cols, max_time, required, ids = base.parse_level_string(text)
        gems = [i for i, c in enumerate(ids) if base.classify_cell_id(c) == "gem"]
        agent = next(i for i, c in enumerate(ids) if base.classify_cell_id(c) == "agent")
        target = next(i for i in gems if ids[i] in base.TARGET_GEM_IDS)
        # the start gem became the agent cell, so level-1 ordinals count it in
        orig = sorted(gems + [agent])
        ordinal = {i: orig.index(i) + 1 for i in gems}
        if orig.index(agent) + 1 != s_ord or ordinal[target] != t_ord:
            raise SystemExit(f"{path.name}: cannot recover the level-1 gem ordinals")
        extra = random.Random(f"multigem-{path.stem}").sample([g for g in gems if g != target], 2)
        for n in (2, 3):
            targets = [target] + extra[: n - 1]
            cells = list(ids)
            for i in targets:
                cells[i] = base.TARGET_GEM_FALLING_ID if ids[i] in base.GEM_FALLING_IDS else base.TARGET_GEM_STATIC_ID
            name = (f"bd_level_01_start_gem_{s_ord:03d}_targets_"
                    + "_".join(f"{ordinal[i]:03d}" for i in sorted(targets, key=ordinal.get)) + ".txt")
            out = OUT / f"n{n}" / name
            if out.exists():
                raise SystemExit(f"duplicate problem {out}")
            fields = [str(rows), str(cols), str(max_time), str(required)] + [f"{c:02d}" for c in cells]
            out.write_text("|".join(fields) + "|\n")
            written += 1
    print(f"wrote {written} problems to {OUT.relative_to(ROOT)}/n2, n3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
