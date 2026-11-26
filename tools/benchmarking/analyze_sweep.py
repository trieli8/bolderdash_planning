#!/usr/bin/env python3
"""Summarise fd_sweep.py results as markdown.

Reads every results_*.csv in the sweep directory (default
tools/benchmarking/sweep_results/), so CSVs from several machines are merged.
If the same (model, problem, config, variant) was run on more than one host,
a solved row wins over an unsolved one and the first solved row is kept.

  python3 tools/benchmarking/analyze_sweep.py [sweep_dir] [--variant=inv0|default|inv0+fa|inv0+fa+<tag>] [--hosts=h1,h2] > report.md

--hosts keeps only the rows from those hosts (e.g. to compare search times
measured on the same machine).

Status meanings (from Fast Downward exit codes):
  solved, timeout, memout, unsolvable / incomplete (search space exhausted:
  the task has no plan), unsupported, error(rc).
A problem that some search exhausted under any model is reported as having no
plan and left out of coverage for every model (the models are meant to be
equivalent; a model that solves such a problem is flagged).
"""
from __future__ import annotations

import csv
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHORT = {"scanner_combined": "scan-comb", "scanner_separated": "scan-sep",
         "non-scanner_combined": "orderfree-comb", "non-scanner_separated": "orderfree-sep"}
MODELS = list(SHORT)
SAT_CFGS = ["gbfs-ff", "eager-gbfs-ff", "gbfs-add", "gbfs-cea", "gbfs-cg", "wastar3-ff", "lama-first"]
OPT_CFGS = ["astar-blind", "astar-hmax", "astar-lmcp", "astar-ms", "lazy-astar-blind", "lazy-astar-hmax", "lazy-astar-hmax-tb",
            "lazy-astar-lmcp", "lazy-astar-ms"]
CFGS = SAT_CFGS + OPT_CFGS
SETS = ["small", "l1", "other"]
SET_LABEL = {"small": "small (hand-made, 5x5..40x11)", "l1": "bd_level_01 20x38 (h1+h2)",
             "other": "bd_levels 02..14"}
EXHAUSTED = {"unsolvable", "incomplete"}


def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load(d: Path, hosts=None):
    rows = []
    for f in sorted(d.glob("results_*.csv")):
        for r in csv.DictReader(f.open()):
            if hosts and r["host"] not in hosts:
                continue
            flags = f.stem.split("_")[2:]  # results_<host>[_fa][_default][_<tag>]
            r["_variant"] = ((r.get("translator") or "inv0") + ("+fa" if "fa" in flags else "")
                             + "".join("+" + t for t in flags if t not in ("fa", "default")))
            rows.append(r)
    best = {}
    for r in rows:
        k = (r["_variant"], r["model"], r["problem"], r["config"])
        old = best.get(k)
        if old is None or (old["status"] != "solved" and r["status"] == "solved"):
            best[k] = r
    return list(best.values())


def short_problem(p: str) -> str:
    name = Path(p).stem
    for a, b in (("bd_level_", "L"), ("_start_gem_", " s"), ("_target_gem_", " t")):
        name = name.replace(a, b)
    if "/h1/" in p:
        name += " h1"
    elif "/h2/" in p:
        name += " h2"
    return name


def fmt_n(x):
    if x is None:
        return "–"
    if x >= 1e6:
        return f"{x/1e6:.1f}M"
    if x >= 1e4:
        return f"{x/1e3:.0f}k"
    return f"{x:.0f}"


def fmt_t(x):
    if x is None:
        return "–"
    return f"{x:.2f}s" if x < 10 else f"{x:.0f}s"


def gmean(xs):
    xs = [max(x, 1e-3) for x in xs]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else None


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith(("--variant=", "--hosts="))]
    want = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--variant=")), "inv0")
    hosts = next((set(a.split("=", 1)[1].split(",")) for a in sys.argv[1:] if a.startswith("--hosts=")), None)
    d = Path(args[0]) if args else ROOT / "tools/benchmarking/sweep_results"
    allrows = load(d, hosts)
    variants = sorted({r["_variant"] for r in allrows})
    rows = [r for r in allrows if r["_variant"] == want]
    if not rows:
        print(f"no results for variant {want} in {d} (have: {', '.join(variants) or 'none'})")
        return 1
    idx = {(r["model"], r["problem"], r["config"]): r for r in rows}
    probs = defaultdict(list)  # set -> problems (in first-seen order)
    pset = {}
    for r in rows:
        if r["problem"] not in pset:
            pset[r["problem"]] = r["set"]
            probs[r["set"]].append(r["problem"])
    models = [m for m in MODELS if any(r["model"] == m for r in rows)]
    hosts = sorted({r["host"] for r in rows})

    # problems proven unsolvable (some search exhausted the space) per model
    unsolv = {(r["model"], r["problem"]) for r in rows if r["status"] in EXHAUSTED}
    solved_any = {(r["model"], r["problem"]) for r in rows if r["status"] == "solved"}
    bad = unsolv & solved_any
    nop = {p for m, p in unsolv}
    cross = sorted({(m, p) for m, p in solved_any if p in nop} - bad)
    out = print
    out(f"# Fast Downward settings sweep\n")
    out(f"Variant **{want}** (translator options; +fa = forced-action fork). Other variants in the data: "
        f"{', '.join(v for v in variants if v != want) or 'none'} (pick with --variant=NAME).\n")
    out(f"{len(rows)} runs from host(s) {', '.join(hosts)}; models: {', '.join(SHORT[m] for m in models)}.\n")
    for h in hosts:
        hf = d / f"host_{h}.txt"
        if hf.exists():
            out(f"- **{h}**: " + "; ".join(l.strip() for l in hf.read_text().splitlines() if l.strip()))
    if bad:
        out("\n**WARNING: solved and exhausted on the same task (unsound search?):** "
            + ", ".join(f"{SHORT[m]} {short_problem(p)}" for m, p in sorted(bad)))
    if cross:
        out("\n**WARNING: solved by one model but exhausted by another (models disagree):** "
            + ", ".join(f"{SHORT[m]} {short_problem(p)}" for m, p in cross))
    uns = sorted(nop)
    if uns:
        out("\nProblems with no plan (search space exhausted; [models that proved it]), excluded from coverage for all models: "
            + ", ".join(f"{short_problem(p)} [{','.join(SHORT[m] for m in models if (m, p) in unsolv)}]" for p in uns))

    # ---- coverage ----
    out("\n## Coverage (solved / solvable problems run)\n")
    for s in SETS:
        if s not in probs:
            continue
        out(f"\n### {SET_LABEL[s]}\n")
        cfgs_here = [c for c in CFGS if any(r["config"] == c for r in rows)]
        out("| model | " + " | ".join(cfgs_here) + " |")
        out("|---|" + "---|" * len(cfgs_here))
        for m in models:
            cells = []
            for c in cfgs_here:
                rs = [idx.get((m, p, c)) for p in probs[s] if p not in nop]
                rs = [r for r in rs if r]
                if not rs:
                    cells.append("")
                    continue
                n = sum(r["status"] == "solved" for r in rs)
                fails = defaultdict(int)
                for r in rs:
                    if r["status"] != "solved":
                        fails[{"timeout": "TO", "memout": "MO"}.get(r["status"], r["status"])] += 1
                extra = " (" + " ".join(f"{v}{k}" for k, v in sorted(fails.items())) + ")" if fails else ""
                cells.append(f"{n}/{len(rs)}{extra}")
            out(f"| {SHORT[m]} | " + " | ".join(cells) + " |")

    # ---- per-config speed on commonly solved tasks ----
    out("\n## Search effort on tasks every listed config solved (per model)\n")
    out("Geometric mean of search time and expansions over the tasks solved by all configs in the row group; "
        "plan quality is the mean of cost / best known optimum.\n")
    opt_cost = {}
    for r in rows:
        if r["status"] == "solved" and r.get("kind") == "optimal" and r["plan_cost"]:
            opt_cost.setdefault(r["problem"], set()).add(int(r["plan_cost"]))
    for m in models:
        for group, cfgs in (("satisficing", SAT_CFGS), ("optimal", OPT_CFGS)):
            for s in SETS:
                if s not in probs:
                    continue
                present = [c for c in cfgs if any(idx.get((m, p, c)) for p in probs[s])]
                if not present:
                    continue
                # drop configs that solve almost nothing so the common set is not empty
                cov = {c: sum(1 for p in probs[s] if (r := idx.get((m, p, c))) and r["status"] == "solved") for c in present}
                top = max(cov.values()) if cov else 0
                keep = [c for c in present if top and cov[c] >= 0.5 * top]
                common = [p for p in probs[s] if all((r := idx.get((m, p, c))) and r["status"] == "solved" for c in keep)]
                if not common:
                    continue
                out(f"\n**{SHORT[m]} / {group} / {s}** ({len(common)} common tasks; "
                    f"left out for low coverage: {', '.join(c for c in present if c not in keep) or 'none'})\n")
                out("| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |")
                out("|---|---|---|---|---|")
                for c in keep:
                    rs = [idx[(m, p, c)] for p in common]
                    st = gmean([fnum(r["search_s"]) or 0 for r in rs])
                    ex = gmean([fnum(r["expanded"]) or 1 for r in rs])
                    mem = max((fnum(r["peak_mem_kb"]) or 0) for r in rs) / 1024
                    q = [int(r["plan_cost"]) / min(opt_cost[r["problem"]]) for r in rs
                         if r["plan_cost"] and r["problem"] in opt_cost and min(opt_cost[r["problem"]]) > 0]
                    qs = f"{statistics.mean(q):.2f} (n={len(q)}, max {max(q):.2f})" if q else "–"
                    out(f"| {c} | {fmt_t(st)} | {fmt_n(ex)} | {mem:.0f} | {qs} |")

    # ---- optimal cost agreement ----
    out("\n## Optimal cost agreement\n")
    mism = []
    for p, cs in opt_cost.items():
        if len(cs) > 1:
            who = [f"{SHORT[r['model']]}/{r['config']}={r['plan_cost']}" for r in rows
                   if r["problem"] == p and r["status"] == "solved" and r.get("kind") == "optimal"]
            mism.append(f"- {short_problem(p)}: " + ", ".join(who))
    n_multi = sum(1 for p in opt_cost
                  if len({r["model"] for r in rows if r["problem"] == p and r["status"] == "solved"
                          and r.get("kind") == "optimal"}) > 1)
    out(f"{len(opt_cost)} problems solved optimally; {n_multi} of them by more than one model. "
        + ("All optimal costs agree across configs and models." if not mism else f"{len(mism)} MISMATCHES:"))
    for line in mism:
        out(line)
    worse = []
    for r in rows:
        if r["status"] == "solved" and r["plan_cost"] and r["problem"] in opt_cost:
            if int(r["plan_cost"]) < min(opt_cost[r["problem"]]):
                worse.append(f"{SHORT[r['model']]}/{r['config']} {short_problem(r['problem'])} "
                             f"cost {r['plan_cost']} < opt {min(opt_cost[r['problem']])}")
    if worse:
        out("\n**Satisficing plans cheaper than the 'optimal' cost (model or heuristic bug):**")
        for w in worse:
            out(f"- {w}")

    # ---- translation ----
    out("\n## Translation (per model and problem set)\n")
    out("| model | set | problems | translate s (median / max) | operators (median / max) | translate failures |")
    out("|---|---|---|---|---|---|")
    for m in models:
        for s in SETS:
            ps = [p for p in probs.get(s, []) if any(idx.get((m, p, c)) for c in CFGS)]
            if not ps:
                continue
            tt, ops, fails = [], [], 0
            for p in ps:
                r = next((idx[(m, p, c)] for c in CFGS if (m, p, c) in idx), None)
                if r is None:
                    continue
                if r["status"].startswith(("translate", "gen-error")):
                    fails += 1
                if fnum(r["translate_s"]) is not None:
                    tt.append(fnum(r["translate_s"]))
                if fnum(r["operators"]) is not None:
                    ops.append(fnum(r["operators"]))
            out(f"| {SHORT[m]} | {s} | {len(ps)} | "
                + (f"{statistics.median(tt):.1f} / {max(tt):.1f}" if tt else "–") + " | "
                + (f"{fmt_n(statistics.median(ops))} / {fmt_n(max(ops))}" if ops else "–") + f" | {fails} |")

    # ---- per-problem detail for the hard sets ----
    out("\n## Per-problem detail (search time, cost)\n")
    for m in models:
        for s in ("l1", "other"):
            ps = [p for p in probs.get(s, []) if any(idx.get((m, p, c)) for c in CFGS)]
            if not ps:
                continue
            cfgs = [c for c in CFGS if any(idx.get((m, p, c)) for p in ps)]
            out(f"\n### {SHORT[m]} / {s}\n")
            out("| problem | " + " | ".join(cfgs) + " |")
            out("|---|" + "---|" * len(cfgs))
            for p in ps:
                cells = []
                for c in cfgs:
                    r = idx.get((m, p, c))
                    if r is None:
                        cells.append("")
                    elif r["status"] == "solved":
                        cells.append(f"{fmt_t(fnum(r['search_s']))} [{r['plan_cost']}]")
                    else:
                        cells.append({"timeout": "TO", "memout": "MO"}.get(r["status"], r["status"]))
                out(f"| {short_problem(p)} | " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
