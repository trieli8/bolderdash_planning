#!/usr/bin/env python3
"""Compare a forced-action (FA) sweep with a classic sweep (markdown report).

  python3 tools/benchmarking/compare_sweep.py [sweep_dir]
      [--fa=inv0+fa[@host,host]] [--classic=inv0[@host,host]] [--timing=inv0@host] > compare.md

--fa / --classic pick the variant (and optionally the hosts) of the two sides.
Coverage compares the two sides as given. Search times are only comparable on
the same machine, so --timing names a second classic selection (e.g. a classic
baseline run on the FA machine) used for the time ratios; without it the time
columns compare across machines and are labelled so.

Expansions are not the same unit on both sides: classic search expands every
intermediate physics state, FA search only the states where the agent moves
(forced actions are applied inside one expansion). "evaluated" counts every
state FA reaches, forced intermediate states included.
"""
from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_sweep import (EXHAUSTED, MODELS, OPT_CFGS, SAT_CFGS, SET_LABEL, SETS, SHORT,  # noqa: E402
                           fmt_n, fmt_t, fnum, gmean, load, short_problem)

ROOT = Path(__file__).resolve().parents[2]
FA_AWARE = ["gbfs-ff", "gbfs-add", "gbfs-cea", "gbfs-cg", "wastar3-ff", "lama-first",
            "lazy-astar-blind", "lazy-astar-hmax", "lazy-astar-hmax-tb"]


def parse_sel(s: str):
    var, _, hosts = s.partition("@")
    return var, (set(hosts.split(",")) if hosts else None)


def select(rows, sel):
    var, hosts = sel
    return {(r["model"], r["problem"], r["config"]): r for r in rows
            if r["_variant"] == var and (hosts is None or r["host"] in hosts)}


def label(sel):
    var, hosts = sel
    return var + (f"@{','.join(sorted(hosts))}" if hosts else "")


def solved(r):
    return r is not None and r["status"] == "solved"


def cov_cell(idx, m, c, ps):
    rs = [idx.get((m, p, c)) for p in ps]
    rs = [r for r in rs if r]
    if not rs:
        return ""
    n = sum(solved(r) for r in rs)
    fails = defaultdict(int)
    for r in rs:
        if not solved(r):
            fails[{"timeout": "TO", "memout": "MO"}.get(r["status"], r["status"])] += 1
    extra = " (" + " ".join(f"{v}{k}" for k, v in sorted(fails.items())) + ")" if fails else ""
    return f"{n}/{len(rs)}{extra}"


def main() -> int:
    opts = {a.split("=", 1)[0]: a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = Path(args[0]) if args else ROOT / "tools/benchmarking/sweep_results"
    fa_sel = parse_sel(opts.get("--fa", "inv0+fa"))
    cl_sel = parse_sel(opts.get("--classic", "inv0"))
    tm_sel = parse_sel(opts["--timing"]) if "--timing" in opts else None
    rows = load(d)
    FA, CL = select(rows, fa_sel), select(rows, cl_sel)
    TM = select(rows, tm_sel) if tm_sel else CL
    if not FA or not CL:
        print(f"no rows for {label(fa_sel) if not FA else label(cl_sel)}")
        return 1
    allidx = list(FA.values()) + list(CL.values()) + (list(TM.values()) if tm_sel else [])
    pset, probs = {}, defaultdict(list)
    for r in allidx:
        if r["problem"] not in pset:
            pset[r["problem"]] = r["set"]
            probs[r["set"]].append(r["problem"])
    models = [m for m in MODELS if any(k[0] == m for k in FA) or any(k[0] == m for k in CL)]
    out = print

    out("# Forced-action vs classic Fast Downward sweep\n")
    out(f"- FA side: **{label(fa_sel)}** ({len(FA)} runs)")
    out(f"- classic side: **{label(cl_sel)}** ({len(CL)} runs)")
    if tm_sel:
        out(f"- classic timing baseline: **{label(tm_sel)}** ({len(TM)} runs, same machine as FA)")
    else:
        out("- no same-machine classic baseline: time ratios compare different machines")
    hosts = sorted({r["host"] for r in allidx})
    for h in hosts:
        hf = d / f"host_{h}.txt"
        if hf.exists():
            out(f"- **{h}**: " + "; ".join(l.strip() for l in hf.read_text().splitlines() if l.strip()))

    # ---- no-plan problems and disagreements ----
    exhausted = defaultdict(set)  # problem -> {side/model}
    solved_by = defaultdict(set)
    for side, idx in (("classic", CL), ("FA", FA), ("classic-base", TM if tm_sel else {})):
        for (m, p, c), r in idx.items():
            if r["status"] in EXHAUSTED:
                exhausted[p].add(f"{side}/{SHORT[m]}")
            elif solved(r):
                solved_by[p].add(f"{side}/{SHORT[m]}")
    nop = set(exhausted)
    out("\n## No-plan problems and disagreements\n")
    out("Problems some search exhausted (no plan), excluded from coverage: "
        + (", ".join(f"{short_problem(p)} [{', '.join(sorted(exhausted[p]))}]" for p in sorted(nop)) or "none"))
    dis = [p for p in sorted(nop) if solved_by[p]]
    if dis:
        out("\n**DISAGREEMENT: solved by one model/side, exhausted by another:**")
        for p in dis:
            out(f"- {short_problem(p)}: solved by {', '.join(sorted(solved_by[p]))}; "
                f"exhausted by {', '.join(sorted(exhausted[p]))}")
    else:
        out("\nNo problem is solved by one model/side and proved plan-less by another.")

    # optimal costs (problem-level: the models are meant to be equivalent)
    opt = defaultdict(set)  # problem -> costs
    opt_who = defaultdict(list)
    for side, idx in (("classic", CL), ("FA", FA), ("classic-base", TM if tm_sel else {})):
        for (m, p, c), r in idx.items():
            if solved(r) and r.get("kind") == "optimal" and r["plan_cost"]:
                opt[p].add(int(r["plan_cost"]))
                opt_who[p].append(f"{side}/{SHORT[m]}/{c}={r['plan_cost']}")
    best = {p: min(cs) for p, cs in opt.items()}
    mism = [p for p, cs in opt.items() if len(cs) > 1]
    out(f"\nOptimal costs: {len(opt)} problems solved optimally on some side; "
        + ("all optimal costs agree (across sides, models and configs)." if not mism else
           f"**{len(mism)} MISMATCHES:**"))
    for p in mism:
        out(f"- {short_problem(p)}: " + ", ".join(opt_who[p]))
    cheaper = []
    for side, idx in (("classic", CL), ("FA", FA), ("classic-base", TM if tm_sel else {})):
        for (m, p, c), r in idx.items():
            if solved(r) and r["plan_cost"] and p in best and int(r["plan_cost"]) < best[p]:
                cheaper.append(f"{side}/{SHORT[m]}/{c} {short_problem(p)} cost {r['plan_cost']} < opt {best[p]}")
    if cheaper:
        out("\n**Plans cheaper than the optimum (bug):**")
        for w in cheaper:
            out(f"- {w}")
    else:
        out("No plan is cheaper than a proven optimum.")

    # ---- coverage ----
    out("\n## Coverage (solved / solvable problems run), classic → FA\n")
    out("Cells are `classic → FA`; a config only on one side shows `–` on the other. "
        "FA runs only the LazySearch configs (the eager / A* configs ignore __FORCED__).\n")
    cfgs_all = SAT_CFGS + OPT_CFGS
    for m in models:
        out(f"\n### {SHORT[m]}\n")
        sets = [s for s in SETS if s in probs]
        out("| config | " + " | ".join(SET_LABEL[s] for s in sets) + " |")
        out("|---|" + "---|" * len(sets))
        for c in cfgs_all:
            cells, any_ = [], False
            for s in sets:
                ps = [p for p in probs[s] if p not in nop]
                a, b = cov_cell(CL, m, c, ps), cov_cell(FA, m, c, ps)
                any_ |= bool(a or b)
                cells.append(f"{a or '–'} → {b or '–'}")
            if any_:
                out(f"| {c} | " + " | ".join(cells) + " |")

    # ---- effort on tasks both sides solve ----
    out("\n## Search effort on tasks solved by both (same config)\n")
    out("Geometric means over the tasks the config solved on both sides. "
        + ("Times: classic from the same-machine baseline." if tm_sel else
           "Times: classic and FA come from different machines (not comparable in absolute terms).")
        + " Classic expansions include every physics step; FA expansions are agent decision states only, "
          "FA evaluated includes the forced intermediate states.\n")
    for m in models:
        lines = []
        for c in FA_AWARE:
            for grp, sets in (("small", ["small"]), ("large", ["l1", "other"])):
                ps = [p for s in sets for p in probs.get(s, [])]
                common = [p for p in ps if solved(TM.get((m, p, c))) and solved(FA.get((m, p, c)))]
                if not common:
                    continue
                tc = gmean([fnum(TM[(m, p, c)]["search_s"]) or 0 for p in common])
                tf = gmean([fnum(FA[(m, p, c)]["search_s"]) or 0 for p in common])
                ec = gmean([fnum(TM[(m, p, c)]["expanded"]) or 1 for p in common])
                ef = gmean([fnum(FA[(m, p, c)]["expanded"]) or 1 for p in common])
                vc = gmean([fnum(TM[(m, p, c)]["evaluated"]) or 1 for p in common])
                vf = gmean([fnum(FA[(m, p, c)]["evaluated"]) or 1 for p in common])
                lines.append(f"| {c} | {grp} | {len(common)} | {fmt_t(tc)} | {fmt_t(tf)} | "
                             f"{tc / tf:.0f}x | {fmt_n(ec)} | {fmt_n(ef)} | {fmt_n(vc)} | {fmt_n(vf)} |")
        if lines:
            out(f"\n**{SHORT[m]}**\n")
            out("| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded "
                "| classic evaluated | FA evaluated |")
            out("|---|---|---|---|---|---|---|---|---|---|")
            for l in lines:
                out(l)

    # ---- optimal under FA ----
    out("\n## FA optimal configs\n")
    out("| model | config | " + " | ".join(SET_LABEL[s] for s in SETS if s in probs)
        + " | cost = known optimum | cost ≠ |")
    out("|---|---|" + "---|" * (len([s for s in SETS if s in probs]) + 2))
    for m in models:
        for c in ("lazy-astar-blind", "lazy-astar-hmax", "lazy-astar-hmax-tb"):
            cells = [cov_cell(FA, m, c, [p for p in probs[s] if p not in nop]) for s in SETS if s in probs]
            if not any(cells):
                continue
            # agreement with the optimum from the *classic* side (independent check)
            cl_opt = {}
            for (mm, p, cc), r in list(CL.items()) + (list(TM.items()) if tm_sel else []):
                if solved(r) and r.get("kind") == "optimal" and r["plan_cost"]:
                    cl_opt.setdefault(p, set()).add(int(r["plan_cost"]))
            agree = differ = 0
            diffs = []
            for p in pset:
                r = FA.get((m, p, c))
                if solved(r) and p in cl_opt:
                    if {int(r["plan_cost"])} == cl_opt[p]:
                        agree += 1
                    else:
                        differ += 1
                        diffs.append(f"{short_problem(p)} {r['plan_cost']} vs {sorted(cl_opt[p])}")
            out(f"| {SHORT[m]} | {c} | " + " | ".join(cells) + f" | {agree} | {differ}"
                + (f" ({'; '.join(diffs)})" if diffs else "") + " |")

    # ---- satisficing quality ----
    out("\n## Satisficing plan quality (cost / known optimum), classic → FA\n")
    out("Mean (max) of cost / optimum over the solved tasks with a known optimum (optimum from any side, model or optimal config).\n")
    out("| model | " + " | ".join(c for c in SAT_CFGS if c in FA_AWARE) + " |")
    out("|---|" + "---|" * len([c for c in SAT_CFGS if c in FA_AWARE]))
    for m in models:
        cells = []
        for c in [c for c in SAT_CFGS if c in FA_AWARE]:
            parts = []
            for idx in (CL, FA):
                q = [int(r["plan_cost"]) / best[p] for (mm, p, cc), r in idx.items()
                     if mm == m and cc == c and solved(r) and r["plan_cost"] and best.get(p)]
                parts.append(f"{statistics.mean(q):.2f} ({max(q):.2f}, n={len(q)})" if q else "–")
            cells.append(" → ".join(parts))
        out(f"| {SHORT[m]} | " + " | ".join(cells) + " |")

    # ---- models under FA ----
    out("\n## Models compared under FA\n")
    out("Per config, on the large problems (l1 + other). Coverage is solved / problems run for that model "
        "(`–` = not run). `common` counts the large tasks solved by every model that ran the config; "
        "the time columns are geometric-mean search times over that common set.\n")
    large = [p for s in ("l1", "other") for p in probs.get(s, []) if p not in nop]
    out("| config | " + " | ".join(f"{SHORT[m]} cov" for m in models) + " | common | "
        + " | ".join(f"{SHORT[m]} time" for m in models) + " |")
    out("|---|" + "---|" * (2 * len(models) + 1))
    for c in FA_AWARE:
        ran = {m: [p for p in large if (m, p, c) in FA] for m in models}
        have = [m for m in models if ran[m]]
        if not have:
            continue
        common = [p for p in large if all(solved(FA.get((m, p, c))) for m in have)]
        covs = [f"{sum(solved(FA[(m, p, c)]) for p in ran[m])}/{len(ran[m])}" if ran[m] else "–"
                for m in models]
        ts = [gmean([fnum(FA[(m, p, c)]["search_s"]) or 0 for p in common]) if common and m in have else None
              for m in models]
        out(f"| {c} | " + " | ".join(covs) + f" | {len(common)} | " + " | ".join(fmt_t(t) for t in ts) + " |")

    # pairwise against a reference model, so one weak model does not empty the common set
    ref = models[0]
    others = models[1:]
    if others:
        out(f"\nSearch time relative to {SHORT[ref]} under FA (pairwise: geometric mean of "
            f"time / {SHORT[ref]} time over the large tasks both solved; >1 = slower than {SHORT[ref]}).\n")
        out("| config | " + " | ".join(SHORT[m] for m in others) + " |")
        out("|---|" + "---|" * len(others))
        for c in FA_AWARE:
            cells = []
            for m in others:
                both = [p for p in large if solved(FA.get((ref, p, c))) and solved(FA.get((m, p, c)))]
                if not both:
                    cells.append("–")
                    continue
                ratio = gmean([max(fnum(FA[(m, p, c)]["search_s"]) or 0, 1e-3)
                               / max(fnum(FA[(ref, p, c)]["search_s"]) or 0, 1e-3) for p in both])
                cells.append(f"{ratio:.2f}x (n={len(both)})")
            if any(x != "–" for x in cells):
                out(f"| {c} | " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
