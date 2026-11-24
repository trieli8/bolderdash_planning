#!/usr/bin/env python3
"""Planner-settings sweep over the engine-conformant test domains.

Runs Fast Downward with many search configurations on the classic (or FA)
variants in pddl/test_domains_target/, over a fixed, seeded problem set:

  small   the hand-made levels in pddl/ (5x5 .. 40x11)
  l1      24 start/target problems on bd_level_01 (12 from test_problems/h1, 12 from h2)
  other   2 target-gem problems from each of bd_levels 2, 3, 6, 7, 8, 9, 11, 13, 14
          (pddl/test_problems_save/)

Each job is one (model, problem): the problem is generated and translated once,
then every configuration of the job runs on the same output.sas with its own
search time / memory limit, so translation time is reported separately.

The translator runs with --invariant-generation-max-candidates 0 by default.
With FD's default invariant synthesis the current domains blow up on the
20x38 benchmark levels (negated target-gem / agent-at preconditions are
multiplied out over the mutex group; MemoryError at 3 GB). Pass
--translator-default to use FD's default translation instead.

Groups (pick with --groups, split across machines with --shard i/N):
  A  scanner_combined: every problem, every config
  B  scanner_separated: every problem, every config
  C  both order-free models: small problems with every config, and the first
     6 large problems with gbfs-ff and astar-hmax (to confirm the timeouts);
     with --fa every problem with every FA_AWARE config

Results are appended to <out>/results_<host>.csv; reruns skip rows already
present, so an interrupted sweep can be resumed with the same command.

Examples:
  # this machine, groups A and C, 4 parallel jobs
  python3 tools/benchmarking/fd_sweep.py --fd ~/downward --groups A,C --jobs 4
  # three machines sharing group B
  python3 tools/benchmarking/fd_sweep.py --fd ~/downward --groups B --shard 0/3
  python3 tools/benchmarking/fd_sweep.py --fd ~/downward --groups B --shard 1/3
  python3 tools/benchmarking/fd_sweep.py --fd ~/downward --groups B --shard 2/3
  # list jobs without running them
  python3 tools/benchmarking/fd_sweep.py --groups A,B,C --dry-run
  # forced-action sweep, and a classic baseline with the same (lazy) configs on the same machine
  python3 tools/benchmarking/fd_sweep.py --fd planners/fast-downward --fa --groups A,B,C
  python3 tools/benchmarking/fd_sweep.py --fd planners/fast-downward --groups A,B,C \
      --configs gbfs-ff,gbfs-add,gbfs-cea,gbfs-cg,wastar3-ff,lama-first,lazy-astar-blind,lazy-astar-hmax

--fd is a Fast Downward checkout with a release build (./build.py). Without
--fd, upstream release-24.06.1 is cloned and built into ~/.cache/fd_sweep.

--fa runs the domain_FA_* files instead; that only makes sense with the
forced-action fork (planners/fast-downward), and only its lazy searches
(FA_AWARE: gbfs-ff, gbfs-add, gbfs-cea, gbfs-cg, wastar3-ff, lama-first and
the lazy A* configs lazy-astar-blind / lazy-astar-hmax) apply __FORCED__
actions automatically. The eager / A* configs would treat them as ordinary
actions and reproduce the classic runs, so --fa runs only the FA_AWARE configs.
With --fa, group C runs every FA_AWARE config on every problem: forced
semantics apply the order-free physics in one fixed order, so the classic
interleaving blow-up that kept group C to 6 large problems does not apply.

lazy-astar-blind / lazy-astar-hmax are lazy_wastar(w=1) with an admissible
heuristic (reopening on), i.e. optimal; under --fa they are the fork's optimal
setting (tools/plan.py --optimal uses lazy-astar-blind).

The fork logs a JSON line per search state for its GUI unless FD_STATE_DUMP=0;
the sweep sets FD_STATE_DUMP=0 for every planner call (no effect on upstream FD).

Memory limits: FD cannot set memory limits on macOS (RLIMIT_AS is not
enforced there and the driver refuses --*-memory-limit). On macOS the sweep
leaves the limit out and kills a translate/search process tree whose resident
set size exceeds --mem instead (polled every 0.2 s), recording it as memout.
There peak_mem_kb is the largest sampled RSS of the search process tree (FD's
own "Peak memory" is the virtual size on macOS, which is meaningless).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import os
import platform
import random
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import psutil
except ImportError:  # the watchdog falls back to ps
    psutil = None

ROOT = Path(__file__).resolve().parents[2]
DOMAINS = ROOT / "pddl" / "test_domains_target"

MODELS = ["scanner_combined", "scanner_separated", "non-scanner_combined", "non-scanner_separated"]

SMALL = [
    "pddl/level_5_5.txt", "pddl/level_5_5_high_stone.txt", "pddl/level_5_5_low_branch.txt",
    "pddl/level_5_5_brick.txt", "pddl/level_5_5_high_branch.txt", "pddl/level_10_5.txt",
    "pddl/level_10_10.txt", "pddl/level_10_10_long.txt", "pddl/test_mini.txt",
    "pddl/testing_level_1.txt", "pddl/testing_level_2.txt", "pddl/testing_level_3.txt",
]
OTHER_LEVELS = ["02", "03", "06", "07", "08", "09", "11", "13", "14"]

SAT, OPT = "satisficing", "optimal"
CONFIGS = {
    "gbfs-ff": (SAT, ["--search", "lazy_greedy([ff()], preferred=[ff()])"]),
    "eager-gbfs-ff": (SAT, ["--search", "eager_greedy([ff()], preferred=[ff()])"]),
    "gbfs-add": (SAT, ["--search", "lazy_greedy([add()], preferred=[add()])"]),
    "gbfs-cea": (SAT, ["--search", "lazy_greedy([cea()], preferred=[cea()])"]),
    "gbfs-cg": (SAT, ["--search", "lazy_greedy([cg()], preferred=[cg()])"]),
    "wastar3-ff": (SAT, ["--search", "lazy_wastar([ff()], w=3, preferred=[ff()])"]),
    "lama-first": (SAT, ["--alias", "lama-first"]),
    "astar-blind": (OPT, ["--search", "astar(blind())"]),
    "astar-hmax": (OPT, ["--search", "astar(hmax())"]),
    "astar-lmcp": (OPT, ["--search", "astar(landmark_cost_partitioning(lm_rhw()))"]),
    "astar-ms": (OPT, ["--search",
                       "astar(merge_and_shrink(shrink_strategy=shrink_bisimulation(greedy=false),"
                       "merge_strategy=merge_sccs(order_of_sccs=topological,merge_selector="
                       "score_based_filtering(scoring_functions=[goal_relevance(),dfp(),total_order()])),"
                       "label_reduction=exact(before_shrinking=true,before_merging=false),"
                       "max_states=50000,threshold_before_merge=1,main_loop_max_time=60))"]),
    "lazy-astar-blind": (OPT, ["--search", "lazy_wastar([blind()], w=1)"]),
    "lazy-astar-hmax": (OPT, ["--search", "lazy_wastar([hmax()], w=1)"]),
}
# configs whose search is LazySearch, the only one that applies __FORCED__ actions in the fork
FA_AWARE = ["gbfs-ff", "gbfs-add", "gbfs-cea", "gbfs-cg", "wastar3-ff", "lama-first",
            "lazy-astar-blind", "lazy-astar-hmax"]

# FD's driver cannot limit memory on macOS; watch the RSS there instead
WATCHDOG = sys.platform == "darwin"
PLANNER_ENV = {**os.environ, "FD_STATE_DUMP": "0"}

FIELDS = ["host", "group", "model", "set", "problem", "config", "kind", "status", "translate_s",
          "search_s", "search_wall_s", "operators", "variables", "expanded", "evaluated",
          "generated", "plan_cost", "plan_len", "peak_mem_kb", "rc", "translator", "fd"]

# FD driver exit codes
EXIT = {0: "solved", 1: "solved", 2: "solved", 3: "solved", 10: "unsolvable", 11: "unsolvable",
        12: "incomplete", 20: "memout", 21: "timeout", 22: "memout", 23: "timeout", 24: "timeout",
        34: "unsupported"}


def problems() -> list[tuple[str, str]]:
    """Deterministic (set, relative path) list."""
    out = [("small", p) for p in SMALL]
    for half in ("h1", "h2"):
        files = sorted((ROOT / "pddl/test_problems" / half).glob("*.txt"))
        for f in random.Random(f"sweep-{half}").sample(files, 12):
            out.append(("l1", str(f.relative_to(ROOT))))
    save = ROOT / "pddl/test_problems_save"
    for lv in OTHER_LEVELS:
        files = sorted(save.glob(f"bd_level_{lv}_target_gem_*.txt"))
        for f in random.Random(f"sweep-{lv}").sample(files, min(2, len(files))):
            out.append(("other", str(f.relative_to(ROOT))))
    return out


def jobs(groups: list[str], fa: bool = False) -> list[tuple[str, str, str, str, list[str]]]:
    """(group, model, set, problem, configs)."""
    probs = problems()
    large = [p for p in probs if p[0] != "small"]
    if fa:
        # only the lazy searches apply forced actions; the rest would just repeat the classic runs
        cfgs = lambda s: list(FA_AWARE)  # noqa: E731
    else:
        # merge-and-shrink needs its full 60 s construction budget even on 5x5 levels and is
        # no better than blind there, so it only runs on the small levels
        cfgs = lambda s: [c for c in CONFIGS if s == "small" or c != "astar-ms"]  # noqa: E731
    out = []
    if "A" in groups:
        out += [("A", "scanner_combined", s, p, cfgs(s)) for s, p in probs]
    if "B" in groups:
        out += [("B", "scanner_separated", s, p, cfgs(s)) for s, p in probs]
    if "C" in groups:
        for m in ("non-scanner_combined", "non-scanner_separated"):
            if fa:
                out += [("C", m, s, p, cfgs(s)) for s, p in probs]
            else:
                out += [("C", m, s, p, list(CONFIGS)) for s, p in probs if s == "small"]
                out += [("C", m, s, p, ["gbfs-ff", "astar-hmax"]) for s, p in large[:6]]
    return out


def last(pattern: str, text: str, cast=float):
    m = re.findall(pattern, text)
    try:
        return cast(m[-1].replace(",", "")) if m else None
    except ValueError:
        return None


def ram_gb() -> float:
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30
    except (ValueError, OSError):
        return 8.0


def cpu_name() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    if sys.platform == "darwin":
        try:
            return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                  capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            pass
    return platform.processor()


def default_jobs() -> int:
    # one planner process per core, at most one per 3.5 GB of RAM (3 GB limit + headroom)
    return max(1, min(os.cpu_count() or 1, int(ram_gb() // 3.5)))


def parse_mem(s: str) -> int:
    """'3G' / '3000M' / '3000000K' / bytes -> bytes (FD driver syntax)."""
    m = re.fullmatch(r"(\d+)([KMG]?)", s.strip().upper())
    if not m:
        raise ValueError(f"bad memory limit {s!r}")
    return int(m.group(1)) * {"": 1, "K": 2**10, "M": 2**20, "G": 2**30}[m.group(2)]


def tree_rss(pid: int) -> int:
    """Resident set size of pid and all its descendants, in bytes."""
    if psutil is not None:
        try:
            procs = [psutil.Process(pid)]
            procs += procs[0].children(recursive=True)
        except psutil.NoSuchProcess:
            return 0
        total = 0
        for p in procs:
            try:
                total += p.memory_info().rss
            except psutil.NoSuchProcess:
                pass
        return total
    out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True).stdout
    kids, rss = {}, {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3:
            p, pp, r = (int(x) for x in parts)
            kids.setdefault(pp, []).append(p)
            rss[p] = r * 1024
    total, todo = 0, [pid]
    while todo:
        p = todo.pop()
        total += rss.get(p, 0)
        todo += kids.get(p, [])
    return total


def run_limited(cmd: list[str], cwd: Path, mem_bytes: int | None) -> tuple[int, str, bool, int | None]:
    """Run cmd (stdout+stderr captured). With mem_bytes, poll the RSS of the process tree
    every 0.2 s and kill the process group as soon as it exceeds mem_bytes.
    Returns (returncode, output, killed_for_memory, peak sampled RSS in KB or None)."""
    with tempfile.TemporaryFile("w+") as out:
        p = subprocess.Popen(cmd, cwd=cwd, stdout=out, stderr=subprocess.STDOUT, text=True,
                             env=PLANNER_ENV, start_new_session=True)
        memout, peak = False, 0
        while True:
            try:
                rc = p.wait(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                pass
            if mem_bytes:
                rss = tree_rss(p.pid)
                peak = max(peak, rss)
                if rss > mem_bytes:
                    memout = True
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
        out.seek(0)
        return rc, out.read(), memout, (peak // 1024 if peak else None)


def ensure_fd(fd: Path | None) -> Path:
    if fd:
        fd = fd.expanduser().resolve()
        if not (fd / "fast-downward.py").exists():
            sys.exit(f"no fast-downward.py in {fd}")
        return fd
    fd = Path.home() / ".cache/fd_sweep/downward"
    if not (fd / "builds/release/bin/downward").exists():
        fd.parent.mkdir(parents=True, exist_ok=True)
        if not fd.exists():
            subprocess.run(["git", "clone", "--depth", "1", "--branch", "release-24.06.1",
                            "https://github.com/aibasel/downward.git", str(fd)], check=True)
        subprocess.run([sys.executable, "build.py", "release", f"-j{os.cpu_count() or 2}"], cwd=fd, check=True)
    return fd


def run_job(job, fd: Path, args, done: set) -> list[dict]:
    group, model, pset, prob, cfgs = job
    cfgs = [c for c in cfgs if (model, prob, c) not in done]
    if not cfgs:
        return []
    host = args.host
    domain_stem = f"domain_{'FA' if args.fa else 'classic'}_{model}"
    domain = DOMAINS / f"{domain_stem}.pddl"
    gen = DOMAINS / f"problem_gen_domain_{'FA_' if args.fa else ''}{model}.py"
    base = {"host": host, "group": group, "model": model, "set": pset, "problem": prob,
            "translator": "default" if args.translator_default else "inv0", "fd": str(fd)}
    rows = []
    with tempfile.TemporaryDirectory(prefix="fdsweep_") as td:
        work = Path(td)
        try:
            text = subprocess.run([sys.executable, str(gen), str(ROOT / prob), "-p", "sweep"],
                                  capture_output=True, text=True, check=True).stdout
        except subprocess.CalledProcessError as e:
            return [{**base, "config": c, "kind": CONFIGS[c][0], "status": "gen-error", "rc": e.returncode}
                    for c in cfgs]
        (work / "problem.pddl").write_text(text)
        watch = parse_mem(args.mem) if WATCHDOG else None
        tcmd = [sys.executable, str(fd / "fast-downward.py"), "--translate",
                "--translate-time-limit", f"{args.translate_timeout}s"]
        if not WATCHDOG:
            tcmd += ["--translate-memory-limit", args.mem]
        tcmd += [str(domain), str(work / "problem.pddl")]
        if not args.translator_default:
            tcmd += ["--translate-options", "--invariant-generation-max-candidates", "0"]
        t0 = time.time()
        trc, ttext, tmem, _ = run_limited(tcmd, work, watch)
        tr = {"translate_s": round(time.time() - t0, 2),
              "operators": last(r"Translator operators: ([0-9]+)", ttext, int),
              "variables": last(r"Translator variables: ([0-9]+)", ttext, int)}
        if trc != 0 or tmem or not (work / "output.sas").exists():
            st = "translate-" + ("memout" if tmem or "MemoryError" in ttext or trc == 20
                                 else "timeout" if trc == 21 else f"error({trc})")
            return [{**base, **tr, "config": c, "kind": CONFIGS[c][0], "status": st, "rc": trc}
                    for c in cfgs]
        for c in cfgs:
            kind, cargs = CONFIGS[c]
            cmd = [sys.executable, str(fd / "fast-downward.py"),
                   "--search-time-limit", f"{args.timeout}s", "--plan-file", str(work / "plan")]
            if not WATCHDOG:
                cmd += ["--search-memory-limit", args.mem]
            if cargs[0] == "--alias":
                cmd += cargs + [str(work / "output.sas")]
            else:
                cmd += [str(work / "output.sas")] + cargs
            t1 = time.time()
            rc, text, memout, rss_kb = run_limited(cmd, work, watch)
            solved = "Solution found." in text and not memout
            status = ("solved" if solved else "memout" if memout
                      else EXIT.get(rc, f"error({rc})"))
            rows.append({**base, **tr, "config": c, "kind": kind, "status": status,
                         "search_s": last(r"Search time: ([0-9.]+)s", text),
                         "search_wall_s": round(time.time() - t1, 2),
                         "expanded": last(r"Expanded ([0-9]+) state", text, int),
                         "evaluated": last(r"Evaluated ([0-9]+) state", text, int),
                         "generated": last(r"Generated ([0-9]+) state", text, int),
                         "plan_cost": last(r"Plan cost: ([0-9]+)", text, int) if solved else None,
                         "plan_len": last(r"Plan length: ([0-9]+) step", text, int) if solved else None,
                         # FD reports the virtual size on macOS (includes ~34 GB of shared cache)
                         "peak_mem_kb": rss_kb if WATCHDOG else last(r"Peak memory: ([0-9]+) KB", text, int),
                         "rc": rc})
            for f in work.glob("plan*"):
                f.unlink()
    return rows


def fd_revision(fd: Path) -> str:
    """Commit of the FD checkout, plus the files with local changes, if any."""
    try:
        rev = subprocess.run(["git", "-C", str(fd), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(fd), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True, check=True).stdout.split("\n")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    changed = [l[3:] for l in dirty if l.strip()]
    return rev + (f" + local changes ({', '.join(changed)})" if changed else "")


def write_host_file(path: Path, csv_name: str, a, fd: Path) -> None:
    """Machine description plus one 'run' line per results CSV written from this machine."""
    runs = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith("run["):
                runs[line[4:line.index("]")]] = line
    mem = "rss-watchdog (macOS: FD cannot set memory limits)" if WATCHDOG else "rlimit (FD driver)"
    runs[csv_name] = (f"run[{csv_name}]=jobs={a.jobs} timeout={a.timeout}s mem={a.mem} mem_limit={mem} "
                      f"fd={fd.name}@{fd_revision(fd)} FD_STATE_DUMP=0")
    path.write_text(
        f"host={a.host}\ncpus={os.cpu_count()}\nram_gb={ram_gb():.0f}\ncpu={cpu_name()}\n"
        f"platform={platform.platform()}\n" + "".join(l + "\n" for _, l in sorted(runs.items())))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fd", type=Path, help="Fast Downward checkout (default: build upstream 24.06.1)")
    ap.add_argument("--groups", default="A,B,C")
    ap.add_argument("--configs", help="comma-separated subset of CONFIGS to run (default: the group's list)")
    ap.add_argument("--shard", default="0/1", help="i/N: run every N-th job starting at i")
    ap.add_argument("--jobs", type=int, default=default_jobs(), help="parallel jobs (default: cores, capped by RAM)")
    ap.add_argument("--timeout", type=int, default=300, help="search time limit per config (s)")
    ap.add_argument("--translate-timeout", type=int, default=600)
    ap.add_argument("--mem", default="3G", help="memory limit per translate/search process")
    ap.add_argument("--translator-default", action="store_true", help="keep FD's invariant synthesis")
    ap.add_argument("--fa", action="store_true", help="use the domain_FA_* files (needs the forced-action fork)")
    ap.add_argument("--out", type=Path, default=ROOT / "tools/benchmarking/sweep_results")
    ap.add_argument("--host", default=socket.gethostname(),
                    help="machine label for the CSV / host file names (default: hostname)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    groups = [g.strip() for g in a.groups.split(",") if g.strip()]
    si, sn = (int(x) for x in a.shard.split("/"))
    all_jobs = jobs(groups, a.fa)
    if a.configs:
        keep = [c.strip() for c in a.configs.split(",") if c.strip()]
        unknown = [c for c in keep if c not in CONFIGS]
        if unknown:
            sys.exit(f"unknown configs: {', '.join(unknown)} (have: {', '.join(CONFIGS)})")
        all_jobs = [(g, m, st, p, [c for c in cs if c in keep]) for g, m, st, p, cs in all_jobs]
        all_jobs = [j for j in all_jobs if j[4]]
    mine = [j for i, j in enumerate(all_jobs) if i % sn == si]
    n_runs = sum(len(j[4]) for j in mine)
    print(f"{len(mine)} jobs / {n_runs} planner runs (shard {si}/{sn} of {len(all_jobs)} jobs, groups {groups})",
          flush=True)
    if a.dry_run:
        for j in mine:
            print(f"  {j[0]} {j[1]:22s} {j[2]:6s} {j[3]}  [{','.join(j[4])}]")
        return 0

    fd = ensure_fd(a.fd)
    a.out.mkdir(parents=True, exist_ok=True)
    host = a.host
    csv_path = a.out / f"results_{host}{'_fa' if a.fa else ''}{'_default' if a.translator_default else ''}.csv"
    done = set()
    if csv_path.exists():
        for r in csv.DictReader(csv_path.open()):
            if not r["status"].startswith(("error", "gen-error")):
                done.add((r["model"], r["problem"], r["config"]))
    write_host_file(a.out / f"host_{host}.txt", csv_path.name, a, fd)
    new = not csv_path.exists()
    t0, finished = time.time(), 0
    with csv_path.open("a", newline="") as fh, cf.ThreadPoolExecutor(a.jobs) as ex:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        if new:
            w.writeheader()
        futs = {ex.submit(run_job, j, fd, a, done): j for j in mine}
        for f in cf.as_completed(futs):
            j = futs[f]
            try:
                rows = f.result()
            except Exception as e:  # noqa: BLE001
                rows = [{"host": host, "group": j[0], "model": j[1], "set": j[2], "problem": j[3],
                         "config": c, "status": f"error(crash:{type(e).__name__})"} for c in j[4]]
            for r in rows:
                w.writerow(r)
            fh.flush()
            finished += 1
            solved = sum(r.get("status") == "solved" for r in rows)
            print(f"[{finished}/{len(mine)}] {time.time()-t0:7.0f}s {j[0]} {j[1]:22s} {Path(j[3]).stem:45s} "
                  f"solved {solved}/{len(rows)}", flush=True)
    print(f"done: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
