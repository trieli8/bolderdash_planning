#!/usr/bin/env python3
"""Compare two sweeps of the same models run with different planner builds (markdown report).

  python3 tools/benchmarking/compare_builds.py [sweep_dir]
      --base=inv0+fa@m5pro --new=inv0+fa+fixpt@m5pro > compare_builds.md

Both sides must use the same search semantics (e.g. two builds of the forced-action
fork), so expansions, evaluations and plans are the same unit and, for a
deterministic search that explores the same states, should match exactly. The
report covers what changed: status transitions (memout -> solved / timeout ...),
coverage per model, config and problem set, plan costs and plan identity (by
length and cost) on tasks both solve, and search time and peak memory on those
tasks. Search times are only comparable when both sides ran on the same machine
with the same parallelism.
"""
from __future__ import annotations

import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_sweep import (EXHAUSTED, MODELS, OPT_CFGS, SAT_CFGS, SET_LABEL, SETS, SHORT,  # noqa: E402
                           fmt_n, fmt_t, fnum, gmean, load, short_problem)
from compare_sweep import cov_cell, label, parse_sel, select, solved  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
ST = {"solved": "solved", "memout": "MO", "timeout": "TO"}


def st(r) -> str:
    return "–" if r is None else ST.get(r["status"], r["status"])


def mb(kb) -> str:
    return "–" if kb is None else f"{kb / 1024:.0f} MB" if kb < 1024 * 1024 else f"{kb / 1024 / 1024:.1f} GB"


def main() -> int:
    opts = {a.split("=", 1)[0]: a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = Path(args[0]) if args else ROOT / "tools/benchmarking/sweep_results"
    if "--base" not in opts or "--new" not in opts:
        sys.exit(__doc__)
    bs, ns = parse_sel(opts["--base"]), parse_sel(opts["--new"])
    B, N = select(load(d, bs[1]), bs), select(load(d, ns[1]), ns)
    if not B or not N:
        print(f"no rows for {label(bs) if not B else label(ns)}")
        return 1
    keys = sorted(set(B) & set(N))
    pset, probs = {}, defaultdict(list)
    for r in list(B.values()) + list(N.values()):
        if r["problem"] not in pset:
            pset[r["problem"]] = r["set"]
            probs[r["set"]].append(r["problem"])
    models = [m for m in MODELS if any(k[0] == m for k in keys)]
    cfgs = [c for c in SAT_CFGS + OPT_CFGS if any(k[2] == c for k in keys)]
    out = print

    out(f"# Planner build comparison: {label(bs)} → {label(ns)}\n")
    out(f"- base: **{label(bs)}** ({len(B)} runs); new: **{label(ns)}** ({len(N)} runs); "
        f"{len(keys)} (model, problem, config) runs on both sides")
    for h in sorted({r["host"] for r in list(B.values()) + list(N.values())}):
        hf = d / f"host_{h}.txt"
        if hf.exists():
            out(f"- **{h}**: " + "; ".join(l.strip() for l in hf.read_text().splitlines() if l.strip()))
    # everything below compares only runs present on both sides (a partial sweep stays comparable)
    B, N = {k: B[k] for k in keys}, {k: N[k] for k in keys}

    # ---- correctness ----
    out("\n## Correctness\n")
    nop = {r["problem"] for idx in (B, N) for r in idx.values() if r["status"] in EXHAUSTED}
    solved_on = {r["problem"] for idx in (B, N) for r in idx.values() if solved(r)}
    out("No-plan problems (some search exhausted): "
        + (", ".join(short_problem(p) for p in sorted(nop)) or "none") + ".")
    bad = sorted(nop & solved_on)
    out(f"**Solved on one side and exhausted on another: {', '.join(map(short_problem, bad))}**" if bad else
        "No problem is solved anywhere and proved plan-less anywhere else.")
    opt = defaultdict(set)
    for idx in (B, N):
        for (m, p, c), r in idx.items():
            if solved(r) and r.get("kind") == "optimal" and r["plan_cost"]:
                opt[p].add(int(r["plan_cost"]))
    mism = {p: cs for p, cs in opt.items() if len(cs) > 1}
    out(f"Optimal costs: {len(opt)} problems solved optimally; "
        + ("all agree across sides, models and configs." if not mism else
           "**MISMATCH:** " + "; ".join(f"{short_problem(p)} {sorted(cs)}" for p, cs in mism.items())))
    both = [k for k in keys if solved(B[k]) and solved(N[k])]
    same = sum(B[k]["plan_cost"] == N[k]["plan_cost"] and B[k]["plan_len"] == N[k]["plan_len"] for k in both)
    same_exp = sum(B[k]["expanded"] == N[k]["expanded"] for k in both)
    out(f"\nOn the {len(both)} runs both sides solve: same plan cost and length in {same}, "
        f"same number of expansions in {same_exp}.")
    diff = [k for k in both if B[k]["plan_cost"] != N[k]["plan_cost"]]
    if diff:
        out("\nRuns whose plan cost changed (base → new):\n")
        for m, p, c in diff[:40]:
            out(f"- {SHORT[m]} {c} {short_problem(p)}: {B[(m, p, c)]['plan_cost']} → {N[(m, p, c)]['plan_cost']}")
        if len(diff) > 40:
            out(f"- … {len(diff) - 40} more")

    # ---- status transitions ----
    out("\n## Status transitions (base → new), all runs\n")
    out("| model | " + " | ".join(["changed", "unchanged"]) + " |")
    out("|---|---|---|")
    for m in models:
        tr = Counter((st(B[k]), st(N[k])) for k in keys if k[0] == m)
        ch = ", ".join(f"{a}→{b} {n}" for (a, b), n in sorted(tr.items(), key=lambda x: -x[1]) if a != b)
        un = ", ".join(f"{a} {n}" for (a, b), n in sorted(tr.items(), key=lambda x: -x[1]) if a == b)
        out(f"| {SHORT[m]} | {ch or '–'} | {un} |")

    # ---- coverage ----
    out("\n## Coverage (solved / solvable problems run), base → new\n")
    out("Failures in brackets: MO = memout, TO = timeout.\n")
    for m in models:
        sets = [s for s in SETS if s in probs]
        out(f"\n### {SHORT[m]}\n")
        out("| config | " + " | ".join(SET_LABEL[s] for s in sets) + " |")
        out("|---|" + "---|" * len(sets))
        for c in cfgs:
            cells = []
            for s in sets:
                ps = [p for p in probs[s] if p not in nop]
                a, b = cov_cell(B, m, c, ps), cov_cell(N, m, c, ps)
                cells.append(a if a == b else f"{a or '–'} → {b or '–'}")
            out(f"| {c} | " + " | ".join(cells) + " |")
        gl = []
        for c in cfgs:
            for p in (p for s in ("l1", "other") for p in probs.get(s, []) if p not in nop):
                k = (m, p, c)
                if k in B and k in N and solved(B[k]) != solved(N[k]):
                    gl.append(f"{'+' if solved(N[k]) else '−'}{c} {short_problem(p)} ({st(B[k])}→{st(N[k])})")
        if gl:
            out("\nLarge-problem gains (+) and losses (−): " + "; ".join(gl))

    # ---- effort ----
    out("\n## Search time and peak memory on runs both sides solve (large problems)\n")
    out("Geometric means of search time; peak memory is the median (max) of the sampled peak RSS per run. "
        "`all runs` peak memory is over every run of that config, solved or not.\n")
    out("| model | config | runs | base time | new time | speed-up | base peak mem | new peak mem "
        "| all runs: base max | all runs: new max |")
    out("|---|---|---|---|---|---|---|---|---|---|")
    for m in models:
        for c in cfgs:
            ks = [k for k in both if k[0] == m and k[2] == c and pset[k[1]] in ("l1", "other")]
            allk = [k for k in keys if k[0] == m and k[2] == c]
            if not ks:
                continue
            tb = gmean([max(fnum(B[k]["search_s"]) or 0, 1e-3) for k in ks])
            tn = gmean([max(fnum(N[k]["search_s"]) or 0, 1e-3) for k in ks])
            mbk = [fnum(B[k]["peak_mem_kb"]) for k in ks if fnum(B[k]["peak_mem_kb"])]
            mnk = [fnum(N[k]["peak_mem_kb"]) for k in ks if fnum(N[k]["peak_mem_kb"])]
            ab = [fnum(B[k]["peak_mem_kb"]) for k in allk if fnum(B[k]["peak_mem_kb"])]
            an = [fnum(N[k]["peak_mem_kb"]) for k in allk if fnum(N[k]["peak_mem_kb"])]
            pm = (lambda v: f"{mb(statistics.median(v))} ({mb(max(v))})" if v else "–")
            out(f"| {SHORT[m]} | {c} | {len(ks)} | {fmt_t(tb)} | {fmt_t(tn)} | {tb / tn:.1f}x | {pm(mbk)} | "
                f"{pm(mnk)} | {mb(max(ab)) if ab else '–'} | {mb(max(an)) if an else '–'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
