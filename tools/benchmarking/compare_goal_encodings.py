#!/usr/bin/env python3
"""Compare the two multi-gem goal encodings with Fast Downward on one level.

  count  domain_*_gemcount: collect ANY n gems; a counter gems_0 -> ... -> gems_n
         is stepped by move_into_gem (the encoding of main, 85adeaa)
  named  domain_*_multigem: collect THESE n gems; each target is an object whose
         marker travels with its gem

Both are generated from the same source domains (make_target_variants.py), so
the physics encoding is identical and only the goal differs.

For each n:
  1. count problem, satisficing search (--sat) -> plan.  The gems that plan
     collected, in order, are found by replaying its moves in the multigem model
     with every gem a target (tools/sim_check/pddl_exec.py, forced-action
     semantics);
  2. named problem with the first n of those gems as targets;
  3. --sat on the named problem, and every --opt config on both problems.

The problems differ on purpose: "any n" lets the planner choose the gems, so its
optimum is <= the named optimum for every choice of n gems.  What the comparison
shows is how well each goal informs the heuristic: compare the initial h value
with the plan cost.

Rows are appended to <out>/goal_encodings_<host>.csv; a rerun skips rows that
are already there.

Examples:
  # forced-action fork (eager astar with forced_actions=true), line 1 of the level file
  python3 tools/benchmarking/compare_goal_encodings.py --fd planners/fast-downward --fa \\
      --level stonesandgem/bd_levels/bd_levels.txt --line 1 --n 1,2,3,4,5 --timeout 600 --mem 16G \\
      --opt astar-hmax-fa="astar(hmax(), forced_actions=true)" \\
      --opt lazy-astar-hmax-tb="let(h, hmax(), lazy(tiebreaking([sum([g(), h]), h]), reopen_closed=true))"
  # classic upstream FD
  python3 tools/benchmarking/compare_goal_encodings.py --fd ~/downward --level pddl/level.txt --n 1,2
"""

from __future__ import annotations

import argparse
import csv
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "sim_check"))

from fd_sweep import WATCHDOG, ensure_fd, fd_revision, last, parse_mem, run_limited  # noqa: E402

DOMAINS = ROOT / "pddl" / "test_domains_target"
SAT_DEFAULT = "lazy_greedy([ff()], preferred=[ff()])"
FIELDS = ["host", "level", "model", "fa", "n", "encoding", "config", "status", "plan_cost", "h_init",
          "last_f", "expanded", "search_s", "wall_s", "translate_s", "operators", "peak_mem_kb", "targets",
          "fd", "domains"]
CELL = re.compile(r"c_(\d+)_(\d+)$")


def read_level(path: Path, line: int | None) -> str:
    lines = [l.strip() for l in path.read_text().splitlines() if l.strip()]
    if line is None:
        return "\n".join(lines)
    levels = [l for l in lines if not l.startswith((";", "#"))]
    return levels[line - 1]


def generate(model: str, fa: bool, variant: str, level_file: Path, extra: list[str]) -> str:
    gen = DOMAINS / f"problem_gen_domain_{'FA_' if fa else ''}{model}_{variant}.py"
    p = subprocess.run([sys.executable, str(gen), str(level_file), "-p", "cmp"] + extra,
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{gen.name}: {p.stderr.strip()}")
    return p.stdout


def domain_path(model: str, fa: bool, variant: str) -> Path:
    return DOMAINS / f"domain_{'FA' if fa else 'classic'}_{model}_{variant}.pddl"


def translate(fd: Path, domain: Path, problem: str, work: Path, args) -> dict:
    (work / "problem.pddl").write_text(problem)
    cmd = [sys.executable, str(fd / "fast-downward.py"), "--translate",
           "--translate-time-limit", f"{args.translate_timeout}s"]
    if not WATCHDOG:
        cmd += ["--translate-memory-limit", args.mem]
    cmd += [str(domain), str(work / "problem.pddl")]
    if not args.translator_default:
        cmd += ["--translate-options", "--invariant-generation-max-candidates", "0"]
    t0 = time.time()
    rc, text, memout, _ = run_limited(cmd, work, parse_mem(args.mem) if WATCHDOG else None)
    ok = rc == 0 and not memout and (work / "output.sas").exists()
    return {"ok": ok, "translate_s": round(time.time() - t0, 2),
            "operators": last(r"Translator operators: ([0-9]+)", text, int),
            "error": None if ok else ("memout" if memout else f"translate rc={rc}")}


def search(fd: Path, work: Path, search_str: str, timeout: int, args) -> dict:
    plan = work / "plan"
    for f in work.glob("plan*"):
        f.unlink()
    cmd = [sys.executable, str(fd / "fast-downward.py"), "--search-time-limit", f"{timeout}s",
           "--plan-file", str(plan)]
    if not WATCHDOG:
        cmd += ["--search-memory-limit", args.mem]
    cmd += [str(work / "output.sas"), "--search", search_str]
    t0 = time.time()
    rc, text, memout, rss_kb = run_limited(cmd, work, parse_mem(args.mem) if WATCHDOG else None)
    solved = "Solution found." in text and not memout
    status = "solved" if solved else "memout" if memout else {
        10: "unsolvable", 11: "unsolvable", 12: "incomplete", 20: "memout", 22: "memout",
        21: "timeout", 23: "timeout", 24: "timeout", 34: "unsupported"}.get(rc, f"error({rc})")
    if status.startswith("error") and args.verbose:
        print(text[-2000:])
    fl = re.findall(r"f = ([0-9]+)", text)
    return {"status": status, "plan_cost": last(r"Plan cost: ([0-9]+)", text, int) if solved else None,
            "h_init": last(r"Initial heuristic value for [^:]+: ([0-9]+)", text, int),
            "last_f": int(fl[-1]) if fl else None,
            "expanded": last(r"Expanded ([0-9]+) state", text, int),
            "search_s": last(r"Search time: ([0-9.]+)s", text),
            "wall_s": round(time.time() - t0, 2),
            "peak_mem_kb": rss_kb if WATCHDOG else last(r"Peak memory: ([0-9]+) KB", text, int),
            "plan": plan.read_text() if solved and plan.exists() else None}


class Replayer:
    """Replays a plan's agent moves in the multigem model with every gem a target
    and reports which gems (row-major ordinals) were collected, in order."""

    def __init__(self, model: str, level_file: Path):
        from fuzz import PddlRunner  # noqa: E402
        from pddl_exec import load_task  # noqa: E402
        import problem_gen as base  # noqa: E402  (pddl/ is on sys.path via problem_gen_common)

        text = level_file.read_text()
        lvl, _ = base.parse_level_text(text)
        rows, cols, _, _, ids = base.parse_level_string(lvl)
        ngems = sum(base.classify_cell_id(c) == "gem" for c in ids)
        prob = generate(model, True, "multigem", level_file, ["--targets", ",".join(map(str, range(1, ngems + 1)))])
        t0 = time.time()
        self.task = load_task(domain_path(model, True, "multigem").read_text(), prob)
        self.runner = PddlRunner(self.task, rows, cols, 10 ** 9)
        print(f"  replay model grounded in {time.time() - t0:.0f}s ({ngems} gems)", flush=True)

    def settle(self, state):
        while True:
            auto = self.task.applicable(state, self.runner.is_auto)
            if not auto:
                return state
            state = auto[0].apply(state)

    def collected_order(self, plan_text: str) -> list[int]:
        state = self.settle(self.task.init_state)
        seen: list[int] = []
        for line in plan_text.splitlines():
            line = line.strip()
            if not line.startswith("("):
                continue
            parts = line.strip("()").split()
            name = parts[0].replace("__forced__", "").replace("__FORCED__", "")
            if not name.startswith("move"):
                continue
            direction = 0
            if name != "move_noop":
                a, b = CELL.match(parts[1]), CELL.match(parts[2])
                dr, dc = int(b.group(1)) - int(a.group(1)), int(b.group(2)) - int(a.group(2))
                direction = {(-1, 0): 1, (0, 1): 2, (1, 0): 3, (0, -1): 4}[(dr, dc)]
            mv, err = self.runner.choose_move(state, direction)
            if mv is None or err:
                raise RuntimeError(f"replay: {line}: {err}")
            state = self.settle(mv.apply(state))
            for aid in state:
                atom = self.task.atoms[aid]
                if atom[0] == "collected":
                    k = int(atom[1][1:])
                    if k not in seen:
                        seen.append(k)
        return seen


def domains_rev() -> str:
    try:
        rev = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h", "--",
                              "pddl/test_domains_target", "pddl/make_target_variants.py", "pddl/problem_gen*.py"],
                             capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "pddl"],
                               capture_output=True, text=True, check=True).stdout.strip()
        return rev + (" + local changes" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fd", type=Path, help="Fast Downward checkout (the forced-action fork for --fa)")
    ap.add_argument("--level", type=Path, required=True, help="level file (one level, or bd_levels.txt with --line)")
    ap.add_argument("--line", type=int, help="1-based line of a multi-level file such as bd_levels.txt")
    ap.add_argument("--model", default="scanner_combined")
    ap.add_argument("--fa", action="store_true", help="use the domain_FA_* variants")
    ap.add_argument("--n", default="1,2,3")
    ap.add_argument("--sat", default=SAT_DEFAULT, help="satisficing search for the any-n plan")
    ap.add_argument("--sat-timeout", type=int, default=300)
    ap.add_argument("--opt", action="append", default=[], metavar="NAME=SEARCH",
                    help="optimal search to run on both problems (repeatable; default astar-hmax=astar(hmax()))")
    ap.add_argument("--timeout", type=int, default=600, help="search time limit per optimal run (s)")
    ap.add_argument("--translate-timeout", type=int, default=600)
    ap.add_argument("--mem", default="16G", help="memory limit (FD driver on Linux; RSS watchdog on macOS)")
    ap.add_argument("--translator-default", action="store_true", help="keep FD's invariant synthesis")
    ap.add_argument("--host", default=socket.gethostname())
    ap.add_argument("--out", type=Path, default=HERE / "goal_encodings")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    opts = [o.split("=", 1) for o in (args.opt or ["astar-hmax=astar(hmax())"])]
    fd = ensure_fd(args.fd)
    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / f"goal_encodings_{args.host}.csv"
    level_name = f"{args.level.name}{':' + str(args.line) if args.line else ''}"
    done = set()
    if csv_path.exists():
        for r in csv.DictReader(csv_path.open()):
            done.add((r["level"], r["model"], r["fa"], r["n"], r["encoding"], r["config"]))
    new = not csv_path.exists()
    fh = csv_path.open("a", newline="")
    w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
    if new:
        w.writeheader()
    base_row = {"host": args.host, "level": level_name, "model": args.model, "fa": int(args.fa),
                "fd": f"{fd.name}@{fd_revision(fd)}", "domains": domains_rev()}
    replayer = None

    with tempfile.TemporaryDirectory(prefix="goalenc_") as td:
        work = Path(td)
        level_file = work / "level.txt"
        level_file.write_text(read_level(args.level, args.line) + "\n")
        sys.path.insert(0, str(ROOT / "pddl"))
        for n in [int(x) for x in args.n.split(",") if x.strip()]:
            print(f"== n={n}", flush=True)
            # 1. any-n problem, satisficing plan
            count_prob = generate(args.model, args.fa, "gemcount", level_file, ["--collect-gems", str(n)])
            cdir = work / f"count{n}"
            cdir.mkdir()
            tr = translate(fd, domain_path(args.model, args.fa, "gemcount"), count_prob, cdir, args)
            sat = search(fd, cdir, args.sat, args.sat_timeout, args) if tr["ok"] else {"status": tr["error"]}
            row = {**base_row, "n": n, "encoding": "count", "config": "sat", **tr, **sat}
            if (level_name, args.model, str(int(args.fa)), str(n), "count", "sat") not in done:
                w.writerow(row)
                fh.flush()
            print(f"  count sat: {sat['status']} cost {sat.get('plan_cost')} h0 {sat.get('h_init')}", flush=True)
            targets = []
            if sat.get("plan"):
                if replayer is None:
                    replayer = Replayer(args.model, level_file)
                order = replayer.collected_order(sat["plan"])
                if len(order) < n:
                    print(f"  replay found only {len(order)} collected gems: {order}")
                targets = sorted(order[:n])
            # 2. named problem with the gems the any-n plan collected
            ndir = None
            if len(targets) == n:
                named_prob = generate(args.model, args.fa, "multigem", level_file,
                                      ["--targets", ",".join(map(str, targets))])
                ndir = work / f"named{n}"
                ndir.mkdir()
                trn = translate(fd, domain_path(args.model, args.fa, "multigem"), named_prob, ndir, args)
                if not trn["ok"]:
                    ndir = None
            else:
                print("  no named problem (no any-n plan to take the gems from)")
            tstr = "+".join(map(str, targets))
            if ndir is not None and (level_name, args.model, str(int(args.fa)), str(n), "named", "sat") not in done:
                s = search(fd, ndir, args.sat, args.sat_timeout, args)
                w.writerow({**base_row, "n": n, "encoding": "named", "config": "sat", **trn, **s, "targets": tstr})
                fh.flush()
                print(f"  named sat: {s['status']} cost {s.get('plan_cost')} h0 {s.get('h_init')} (gems {tstr})",
                      flush=True)
            # 3. optimal configs on both
            for name, sstr in opts:
                for enc, d, t in (("count", cdir if tr["ok"] else None, tr), ("named", ndir, trn if ndir else None)):
                    if d is None or (level_name, args.model, str(int(args.fa)), str(n), enc, name) in done:
                        continue
                    s = search(fd, d, sstr, args.timeout, args)
                    w.writerow({**base_row, "n": n, "encoding": enc, "config": name, **t, **s,
                                "targets": tstr if enc == "named" else ""})
                    fh.flush()
                    print(f"  {enc} {name}: {s['status']} cost {s.get('plan_cost')} h0 {s.get('h_init')} "
                          f"last f {s.get('last_f')} exp {s.get('expanded')} {s.get('wall_s')}s", flush=True)
    fh.close()
    print(f"rows in {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
