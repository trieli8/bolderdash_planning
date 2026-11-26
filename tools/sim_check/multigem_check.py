#!/usr/bin/env python3
"""Check a multi-gem domain against its single-target domain (no engine needed).

For random levels with k target gems (1..--max-targets) and random walks, run
the multigem model with all k targets and the single-target model once per
target, with forced-action semantics: one move, then physics until nothing is
applicable, exploring every physics interleaving (as fuzz.py does).  After
every tick, the multigem state restricted to target i must equal the
single-target state for target i: the other targets' atoms are dropped,
(target-gem c ti) is read as (target-gem c) and (collected ti) as (got-gem).

fuzz.py checks the single-target models against the stonesngems engine, so a
pass here carries that check over to the multigem models.

  python3 tools/sim_check/multigem_check.py \\
      --domain pddl/test_domains_target/domain_FA_scanner_combined_multigem.pddl --cases 200
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fuzz import (GEM, GEM_F, TARGET_GEM, TARGET_GEM_F, Level, PddlRunner, load_generator,  # noqa: E402
                  random_level, random_walk)
from pddl_exec import load_task  # noqa: E402

UNMARK = {TARGET_GEM: GEM, TARGET_GEM_F: GEM_F}
MARK = {GEM: TARGET_GEM, GEM_F: TARGET_GEM_F}


def project(task, state, target: str, all_targets: list[str]) -> frozenset:
    """Multigem state as the single-target model for `target` would have it."""
    others = set(all_targets) - {target}
    out = set()
    for aid in state:
        atom = task.atoms[aid]
        if others & set(atom[1:]):
            continue
        if atom[0] == "target-gem":
            out.add(("target-gem", atom[1]))
        elif atom[0] == "collected":
            out.add(("got-gem",))
        else:
            out.add(atom)
    return frozenset(out)


def atoms(task, state) -> frozenset:
    return frozenset(task.atoms[aid] for aid in state)


def settle(runner, state):
    out = runner.settle(state)
    if out.capped:
        return None, "explore-cap"
    if len(out.states) != 1:
        return None, f"{len(out.states)} end-of-tick states"
    return out.states[0], None


def run_case(rng, multi_dom: str, single_dom: str, gen_multi, gen_single, args):
    while True:
        lvl = random_level(rng, args.max_rows, args.max_cols)
        cells = [UNMARK.get(c, c) for c in lvl.cells]
        gems = [i for i, c in enumerate(cells) if c in (GEM, GEM_F)]
        if gems:
            break
    k = rng.randint(1, min(args.max_targets, len(gems)))
    targets = sorted(rng.sample(gems, k))
    names = [f"t{j + 1}" for j in range(k)]

    def level_with(marked):
        return Level(lvl.rows, lvl.cols, [MARK[c] if i in marked else c for i, c in enumerate(cells)]).text()

    multi = load_task(multi_dom, gen_multi(level_with(set(targets))))
    singles = [load_task(single_dom, gen_single(level_with({t}))) for t in targets]
    rm = PddlRunner(multi, lvl.rows, lvl.cols, args.max_explore)
    rs = [PddlRunner(t, lvl.rows, lvl.cols, args.max_explore) for t in singles]

    sm, err = settle(rm, multi.init_state)
    ss = []
    for r, t in zip(rs, singles):
        s, e = settle(r, t.init_state)
        err = err or e
        ss.append(s)
    if err:
        return "skip", f"init: {err}", k
    walk = random_walk(rng, args.walk)
    for tick, ch in enumerate(["-"] + list(walk)):
        if tick > 0:
            if not rm.flag(sm, "agent-alive"):
                break
            mv, e = rm.choose_move(sm, int(ch))
            if mv is None or e:
                return "skip", f"tick {tick}: multigem move: {e}", k
            sm, e = settle(rm, mv.apply(sm))
            if e:
                return "skip", f"tick {tick}: multigem {e}", k
            for i, (r, s) in enumerate(zip(rs, ss)):
                mv_i, e = r.choose_move(s, int(ch))
                if mv_i is None or e or mv_i.label != mv.label:
                    return "fail", f"tick {tick}: target {names[i]}: move {mv.label} vs {mv_i and mv_i.label} ({e})", k
                ss[i], e = settle(r, mv_i.apply(s))
                if e:
                    return "skip", f"tick {tick}: single {names[i]} {e}", k
        for i, (single, s) in enumerate(zip(singles, ss)):
            pm, ps = project(multi, sm, names[i], names), atoms(single, s)
            if pm != ps:
                return "fail", (f"tick {tick}: target {names[i]}: multigem-only {sorted(pm - ps)[:6]}, "
                                f"single-only {sorted(ps - pm)[:6]}"), k
    collected = sum(("collected", n) in atoms(multi, sm) for n in names)
    return "pass", f"{collected}/{k} collected", k


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", required=True, type=Path, help="a domain_*_multigem.pddl file")
    ap.add_argument("--cases", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-rows", type=int, default=6)
    ap.add_argument("--max-cols", type=int, default=7)
    ap.add_argument("--max-targets", type=int, default=3)
    ap.add_argument("--walk", type=int, default=25)
    ap.add_argument("--max-explore", type=int, default=20000)
    args = ap.parse_args()
    if "_multigem" not in args.domain.stem:
        sys.exit("--domain must be a *_multigem.pddl domain")
    single_path = args.domain.with_name(args.domain.name.replace("_multigem", ""))
    multi_dom, single_dom = args.domain.read_text(), single_path.read_text()
    gen_multi, gen_single = load_generator(args.domain), load_generator(single_path)
    rng = random.Random(args.seed)
    counts = {"pass": 0, "fail": 0, "skip": 0}
    by_k: dict[int, int] = {}
    collected_any = 0
    t0 = time.time()
    for case in range(args.cases):
        res, detail, k = run_case(rng, multi_dom, single_dom, gen_multi, gen_single, args)
        counts[res] += 1
        if res == "pass":
            by_k[k] = by_k.get(k, 0) + 1
            collected_any += not detail.startswith("0/")
        else:
            print(f"case {case}: {res}: {detail}", flush=True)
    print(f"{args.domain.name} vs {single_path.name}: {counts['pass']} pass, {counts['fail']} fail, "
          f"{counts['skip']} skipped of {args.cases} ({time.time() - t0:.0f}s); passes by target count "
          f"{dict(sorted(by_k.items()))}; {collected_any} passes collected at least one target")
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
