#!/usr/bin/env python3
"""Measure how expensive a Boulder Dash PDDL model is, per level.

For every level (a .txt level file) it reports

* operators   - ground operators after relaxed reachability and disjunction
                splitting (pddl_exec.task_stats, roughly what Fast Downward's
                translator keeps), and the time pddl_exec needs to ground;
* steps/tick  - physics actions per game tick along fixed random walks
                (forced-action semantics: the first applicable physics action
                by name is applied until none is left).  The walks depend only
                on --seed and the level, so different models see the same
                moves;
* states/tick - with --interleavings: distinct intermediate states of a tick
                when *every* interleaving of physics actions is explored, i.e.
                the part of the state space a classic planner sees inside one
                tick (1 step per state for a deterministic scanner).  Capped at
                --cap; capped ticks are reported as ">cap";
* FD          - with --fd: translator operator count, expansions and times of a
                Fast Downward run (--fd-search, default plan.py's satisficing
                configuration).

Usage:
  python3 tools/sim_check/model_stats.py --domain pddl/test_domains_target/domain_classic_scanner_separated.pddl \
      pddl/level_10_10.txt pddl/test_problems/h1/bd_level_01_start_gem_001_target_gem_005.txt
  ... --interleavings --cap 5000 --fd ../downward/fast-downward.py --fd-timeout 300
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fuzz import PddlRunner, load_generator, parse_level_file, random_walk  # noqa: E402
from pddl_exec import Task, load_task, task_stats  # noqa: E402


def physics_closure(task: Task, state, is_auto) -> tuple:
    steps = 0
    while True:
        auto = task.applicable(state, is_auto)
        if not auto:
            return state, steps
        state = min(auto, key=lambda g: g.label).apply(state)
        steps += 1
        if steps > 10 ** 6:
            raise RuntimeError("physics did not settle")


def count_interleavings(task: Task, state, is_auto, cap: int) -> Optional[int]:
    """Distinct states reachable inside one tick, or None if more than cap."""
    seen = {state}
    stack = [state]
    while stack:
        s = stack.pop()
        for ga in task.applicable(s, is_auto):
            ns = ga.apply(s)
            if ns not in seen:
                seen.add(ns)
                if len(seen) > cap:
                    return None
                stack.append(ns)
    return len(seen)


FD_PATTERNS = {
    "translator_operators": r"Translator operators: (\d+)",
    "translate_time": r"Done! \[([\d.]+)s CPU",
    "expanded": r"Expanded (\d+) state",
    "generated": r"Generated (\d+) state",
    "search_time": r"Search time: ([\d.]+)s",
    "total_time": r"Total time: ([\d.]+)s",
    "plan_length": r"Plan length: (\d+) step",
}


def run_fd(fd: Path, domain_text: str, problem: str, search: List[str], timeout: int) -> Dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="model_stats_fd_") as td:
        d = Path(td) / "domain.pddl"
        p = Path(td) / "problem.pddl"
        d.write_text(domain_text)
        p.write_text(problem)
        t0 = time.time()
        try:
            proc = subprocess.run([sys.executable, str(fd), str(d), str(p), *search],
                                  cwd=td, capture_output=True, text=True, timeout=timeout)
            out = proc.stdout + proc.stderr
            status = "solved" if "Solution found" in out else f"rc={proc.returncode}"
        except subprocess.TimeoutExpired as exc:
            out = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            status = "timeout"
        res: Dict[str, object] = {"status": status, "wall": round(time.time() - t0, 1)}
        for key, pat in FD_PATTERNS.items():
            m = re.findall(pat, out)
            if m:
                res[key] = float(m[-1]) if "." in m[-1] else int(m[-1])
        if status.startswith("rc="):
            res["tail"] = out.strip().splitlines()[-3:]
        return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", required=True, type=Path)
    ap.add_argument("--generator", type=Path)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--walks", type=int, default=2, help="random walks per level")
    ap.add_argument("--ticks", type=int, default=20, help="ticks per walk")
    ap.add_argument("--interleavings", action="store_true", help="also count intermediate states per tick")
    ap.add_argument("--cap", type=int, default=5000)
    ap.add_argument("--fd", type=Path, help="path to fast-downward.py")
    ap.add_argument("--fd-search", default="--search lazy_greedy([ff()],preferred=[ff()])")
    ap.add_argument("--fd-timeout", type=int, default=300)
    ap.add_argument("--json", type=Path, help="append one JSON line per level here")
    ap.add_argument("levels", nargs="+", type=Path)
    args = ap.parse_args()

    generate = load_generator(args.domain, args.generator)
    domain_text = args.domain.read_text()
    print(f"domain: {args.domain}")
    for lvl_path in args.levels:
        level = parse_level_file(lvl_path)
        problem = generate(level.text(), lvl_path.stem)
        t0 = time.time()
        task = load_task(domain_text, problem)
        ground = time.time() - t0
        stats = task_stats(task)
        runner = PddlRunner(task, level.rows, level.cols, 0)
        rng = random.Random(f"{args.seed}:{lvl_path.name}")
        steps: List[int] = []
        inter: List[Optional[int]] = []
        t1 = time.time()
        for _ in range(args.walks):
            state, _ = physics_closure(task, task.init_state, runner.is_auto)
            for ch in random_walk(rng, args.ticks):
                if not runner.flag(state, "agent-alive"):
                    break
                move, _err = runner.choose_move(state, int(ch))
                if move is None:
                    break
                after_move = move.apply(state)
                if args.interleavings:
                    inter.append(count_interleavings(task, after_move, runner.is_auto, args.cap))
                state, n = physics_closure(task, after_move, runner.is_auto)
                steps.append(n)
        sim = time.time() - t1
        row: Dict[str, object] = {
            "domain": str(args.domain), "level": lvl_path.name, "size": f"{level.rows}x{level.cols}",
            "operators": stats["operators"], "ground_s": round(ground, 1),
            "ticks": len(steps),
            "steps_per_tick": round(sum(steps) / len(steps), 1) if steps else None,
            "max_steps": max(steps) if steps else None, "sim_s": round(sim, 1),
        }
        line = (f"  {lvl_path.name} ({row['size']}): operators={row['operators']} ground={row['ground_s']}s "
                f"steps/tick={row['steps_per_tick']} (max {row['max_steps']}, {row['ticks']} ticks, {row['sim_s']}s)")
        if args.interleavings and inter:
            known = [x for x in inter if x is not None]
            capped = len(inter) - len(known)
            row.update({"states_per_tick_avg": round(sum(known) / len(known), 1) if known else None,
                        "states_per_tick_max": max(known) if known else None,
                        "ticks_over_cap": capped, "cap": args.cap})
            line += (f" states/tick avg={row['states_per_tick_avg']} max={row['states_per_tick_max']}"
                     f" over-cap={capped}/{len(inter)}")
        if args.fd:
            fd = run_fd(args.fd, domain_text, problem, args.fd_search.split(), args.fd_timeout)
            row["fd"] = fd
            line += "\n    FD: " + " ".join(f"{k}={v}" for k, v in fd.items())
        print(line, flush=True)
        if args.json:
            with args.json.open("a") as fh:
                fh.write(json.dumps(row) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
