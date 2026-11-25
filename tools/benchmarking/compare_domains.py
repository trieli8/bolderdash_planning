#!/usr/bin/env python3
"""Compare two fd_sweep runs of the same planner on two versions of the test domains (markdown).

  python3 tools/benchmarking/compare_domains.py OLD_DIR NEW_DIR [--variant=inv0] [--hosts=vm] > report.md

OLD_DIR and NEW_DIR are sweep result directories (results_*.csv + host_*.txt), e.g.
tools/benchmarking/sweep_results (domains a9f6ad1) and tools/benchmarking/sweep_results_v2
(domains a1a50ba). Use the same machine and variant on both sides, or the times mean nothing.

The models are meant to describe the same game before and after the change, and only moves
cost 1, so every proven optimum must be the same on both sides; the report checks that first.
"""
from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_sweep import (EXHAUSTED, MODELS, OPT_CFGS, SAT_CFGS, SET_LABEL, SETS, SHORT,  # noqa: E402
                           fmt_n, fmt_t, fnum, gmean, load, short_problem)


def solved(r):
    return r is not None and r["status"] == "solved"


def index(d: Path, variant: str, hosts):
    return {(r["model"], r["problem"], r["config"]): r for r in load(d, hosts) if r["_variant"] == variant}


def host_lines(d: Path, hosts=None):
    out = []
    for hf in sorted(d.glob("host_*.txt")):
        if hosts and hf.stem[len("host_"):] not in hosts:
            continue
        out.append(f"- `{hf.name}`: " + "; ".join(l.strip() for l in hf.read_text().splitlines() if l.strip()))
    return out


def cov(idx, m, c, ps):
    rs = [idx[(m, p, c)] for p in ps if (m, p, c) in idx]
    if not rs:
        return ""
    n = sum(solved(r) for r in rs)
    fails = defaultdict(int)
    for r in rs:
        if not solved(r):
            fails[{"timeout": "TO", "memout": "MO"}.get(r["status"], r["status"])] += 1
    return f"{n}/{len(rs)}" + (" (" + " ".join(f"{v}{k}" for k, v in sorted(fails.items())) + ")" if fails else "")


def main() -> int:
    opts = {a.split("=", 1)[0]: a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    old_d, new_d = Path(args[0]), Path(args[1])
    variant = opts.get("--variant", "inv0")
    hosts = set(opts["--hosts"].split(",")) if "--hosts" in opts else None
    OLD, NEW = index(old_d, variant, hosts), index(new_d, variant, hosts)
    if not OLD or not NEW:
        print(f"no {variant} rows in {old_d if not OLD else new_d}")
        return 1
    out = print
    pset, probs = {}, defaultdict(list)
    for r in list(OLD.values()) + list(NEW.values()):
        if r["problem"] not in pset:
            pset[r["problem"]] = r["set"]
            probs[r["set"]].append(r["problem"])
    models = [m for m in MODELS if any(k[0] == m for k in OLD) or any(k[0] == m for k in NEW)]

    out("# Old vs new test domains, same planner\n")
    out(f"Variant **{variant}**. Old: `{old_d}` ({len(OLD)} runs). New: `{new_d}` ({len(NEW)} runs).\n")
    for side, d in (("old", old_d), ("new", new_d)):
        out(f"**{side}**")
        for l in host_lines(d, hosts):
            out(l)
        out("")

    # ---- correctness ----
    out("## Same game?\n")
    opt = {"old": defaultdict(set), "new": defaultdict(set)}
    exhausted = {"old": set(), "new": set()}
    solved_any = {"old": set(), "new": set()}
    for side, idx in (("old", OLD), ("new", NEW)):
        for (m, p, c), r in idx.items():
            if r["status"] in EXHAUSTED:
                exhausted[side].add(p)
            if solved(r):
                solved_any[side].add(p)
                if r.get("kind") == "optimal" and r["plan_cost"]:
                    opt[side][p].add(int(r["plan_cost"]))
    both = sorted(set(opt["old"]) & set(opt["new"]))
    mism = [p for p in both if opt["old"][p] != opt["new"][p]]
    inner = [p for s in ("old", "new") for p in opt[s] if len(opt[s][p]) > 1]
    out(f"- Problems with a proven optimum on both sides: {len(both)}; "
        + ("**all optimal costs are the same before and after.**" if not mism else f"**{len(mism)} differ:**"))
    for p in mism:
        out(f"  - {short_problem(p)}: old {sorted(opt['old'][p])}, new {sorted(opt['new'][p])}")
    if inner:
        out(f"- **Optimal configs disagree within one side on:** {', '.join(sorted({short_problem(p) for p in inner}))}")
    only = {s: sorted(set(opt[s]) - set(opt[o])) for s, o in (("old", "new"), ("new", "old"))}
    out(f"- Proven optimum only on the old side: {len(only['old'])}; only on the new side: {len(only['new'])}"
        + (f" ({', '.join(short_problem(p) for p in only['new'])})" if only["new"] else ""))
    flip = sorted((exhausted["old"] & solved_any["new"]) | (exhausted["new"] & solved_any["old"]))
    out(f"- No plan (search space exhausted): old {', '.join(sorted(short_problem(p) for p in exhausted['old'])) or 'none'}; "
        f"new {', '.join(sorted(short_problem(p) for p in exhausted['new'])) or 'none'}"
        + (f". **Solved on one side, no plan on the other: {', '.join(short_problem(p) for p in flip)}**" if flip else ""))
    nop = exhausted["old"] | exhausted["new"]

    # ---- coverage ----
    out("\n## Coverage (solved / solvable problems run), old → new\n")
    for m in models:
        out(f"\n### {SHORT[m]}\n")
        sets = [s for s in SETS if s in probs]
        out("| config | " + " | ".join(SET_LABEL[s] for s in sets) + " |")
        out("|---|" + "---|" * len(sets))
        for c in SAT_CFGS + OPT_CFGS:
            cells = []
            for s in sets:
                ps = [p for p in probs[s] if p not in nop]
                a, b = cov(OLD, m, c, ps), cov(NEW, m, c, ps)
                cells.append(f"{a or '–'} → {b or '–'}" if (a or b) else "")
            if any(cells):
                out(f"| {c} | " + " | ".join(cells) + " |")

    # ---- model size and physics per move ----
    out("\n## Model size and physics work, large problems\n")
    out("Translator operators and translate time: medians over the large problems translated on both sides. "
        "Physics steps per move: median of (plan length − plan cost) / plan cost over large solved runs "
        "(plan length counts every action, cost only the moves).\n")
    out("| model | operators | translate time | physics steps per move |")
    out("|---|---|---|---|")
    for m in models:
        def per_problem(idx, f):
            v = {}
            for (mm, p, c), r in idx.items():
                if mm == m and pset.get(p) != "small" and fnum(r.get(f)):
                    v[p] = fnum(r[f])
            return v
        cells = []
        for f, fmt in (("operators", fmt_n), ("translate_s", fmt_t)):
            a, b = per_problem(OLD, f), per_problem(NEW, f)
            com = sorted(set(a) & set(b))
            cells.append(f"{fmt(statistics.median([a[p] for p in com]))} → {fmt(statistics.median([b[p] for p in com]))}"
                         if com else "–")
        steps = []
        for idx in (OLD, NEW):
            xs = [(fnum(r["plan_len"]) - fnum(r["plan_cost"])) / fnum(r["plan_cost"]) for (mm, p, c), r in idx.items()
                  if mm == m and pset.get(p) != "small" and solved(r) and fnum(r.get("plan_cost")) and fnum(r.get("plan_len"))]
            steps.append(f"{statistics.median(xs):.0f}" if xs else "–")
        out(f"| {SHORT[m]} | {cells[0]} | {cells[1]} | {steps[0]} → {steps[1]} |")

    # ---- effort ----
    out("\n## Search effort on tasks both sides solved (same model and config)\n")
    out("Geometric means. Search time is Fast Downward's search time (translation excluded).\n")
    for m in models:
        lines = []
        for c in SAT_CFGS + OPT_CFGS:
            for grp, sets in (("small", ["small"]), ("large", ["l1", "other"])):
                ps = [p for s in sets for p in probs.get(s, [])]
                com = [p for p in ps if solved(OLD.get((m, p, c))) and solved(NEW.get((m, p, c)))]
                if not com:
                    continue
                to = gmean([fnum(OLD[(m, p, c)]["search_s"]) or 0 for p in com])
                tn = gmean([fnum(NEW[(m, p, c)]["search_s"]) or 0 for p in com])
                eo = gmean([fnum(OLD[(m, p, c)]["expanded"]) or 1 for p in com])
                en = gmean([fnum(NEW[(m, p, c)]["expanded"]) or 1 for p in com])
                lines.append(f"| {c} | {grp} | {len(com)} | {fmt_t(to)} → {fmt_t(tn)} | {to / tn:.1f}x "
                             f"| {fmt_n(eo)} → {fmt_n(en)} |")
        if lines:
            out(f"\n**{SHORT[m]}**\n")
            out("| config | set | tasks | search time | faster by | expansions |")
            out("|---|---|---|---|---|---|")
            for l in lines:
                out(l)

    # ---- quality ----
    best = {}
    for s in ("old", "new"):
        for p, cs in opt[s].items():
            best[p] = min(min(cs), best.get(p, min(cs)))
    out("\n## Satisficing plan quality (cost / known optimum), old → new\n")
    out("Mean (worst) over solved tasks with a known optimum.\n")
    out("| model | " + " | ".join(SAT_CFGS) + " |")
    out("|---|" + "---|" * len(SAT_CFGS))
    for m in models:
        cells = []
        for c in SAT_CFGS:
            parts = []
            for idx in (OLD, NEW):
                q = [int(r["plan_cost"]) / best[p] for (mm, p, cc), r in idx.items()
                     if mm == m and cc == c and solved(r) and r["plan_cost"] and best.get(p)]
                parts.append(f"{statistics.mean(q):.2f} ({max(q):.2f})" if q else "–")
            cells.append(" → ".join(parts))
        out(f"| {SHORT[m]} | " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
