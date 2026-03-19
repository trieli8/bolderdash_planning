#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

TOOLS_DIR = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
PLOT_RUNTIME_SCRIPT = BENCHMARK_DIR / "ploters" / "plot_plus_bench_runtime.py"


def repo_root() -> Path:
    return REPO_ROOT


PLUS_RUNNER_DIR = repo_root() / "planners" / "pddl-plus"
sys.path.insert(0, str(PLUS_RUNNER_DIR))
from pddl_plus_runner import PlusPlanResult, solve as solve_plus  # type: ignore  # noqa: E402


def normalise_problem_name(problem: Path) -> str:
    try:
        txt = problem.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\(\s*problem\s+([^\s\)]+)\s*\)", txt, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return problem.stem


def safe_tag(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9_+\-]+", "_", lowered)
    return lowered.strip("_") or "x"


def write_plan_file(path: Path, actions: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for a in actions:
        if a.args:
            lines.append(f"({a.name} {' '.join(a.args)})")
        else:
            lines.append(f"({a.name})")
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_timed_plan_file(path: Path, actions: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    for a in actions:
        body = f"({a.name}{(' ' + ' '.join(a.args)) if a.args else ''})"
        if a.time is not None and a.duration is not None:
            lines.append(f"{a.time:.3f}: {body} [{a.duration:.3f}]")
        elif a.time is not None:
            lines.append(f"{a.time:.3f}: {body}")
        else:
            lines.append(body)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def split_items(values: Optional[Sequence[str]]) -> List[str]:
    if not values:
        return []
    out: List[str] = []
    for raw in values:
        for part in raw.split(","):
            token = part.strip()
            if token:
                out.append(token)
    return out


def select_problem_gen(domain: Path) -> Path:
    name = domain.name.lower()
    root = repo_root()

    if "plus" in name and ("plus_scanner" in name or "scanner_separated" in name):
        return root / "pddl" / "problem_gen_plus_scanner_separated.py"
    if "plus_relaxed" in name:
        return root / "pddl" / "problem_gen_plus_relaxed.py"
    if "plus" in name:
        return root / "pddl" / "problem_gen_plus_from_domain.py"
    if "scanner_separated" in name:
        return root / "pddl" / "problem_gen_scanner_separated.py"
    return root / "pddl" / "problem_gen.py"


def generate_problem_from_level(
    level_txt: Path,
    domain: Path,
    explicit_gen: Optional[Path],
) -> Tuple[Path, tempfile.TemporaryDirectory]:
    gen_py = explicit_gen.resolve() if explicit_gen else select_problem_gen(domain)
    if not gen_py.exists():
        raise FileNotFoundError(f"Missing problem generator at {gen_py}")

    tmpdir = tempfile.TemporaryDirectory(prefix="bench_plus_problem_")
    out_path = Path(tmpdir.name) / f"{level_txt.stem}.pddl"

    cmd = [sys.executable, str(gen_py), str(level_txt), "-p", level_txt.stem]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        tmpdir.cleanup()
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"{gen_py.name} failed (rc={proc.returncode}): {detail}")

    out_path.write_text(proc.stdout, encoding="utf-8")
    return out_path, tmpdir


def collect_problem_paths(
    explicit_problems: Optional[Sequence[str]],
    problem_globs: Optional[Sequence[str]],
) -> List[Path]:
    root = repo_root()
    collected: List[Path] = []
    seen = set()

    for p in explicit_problems or []:
        candidate = Path(p)
        if not candidate.is_absolute():
            candidate = (root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if candidate not in seen:
            seen.add(candidate)
            collected.append(candidate)

    for pattern in problem_globs or []:
        for hit in sorted(root.glob(pattern)):
            path = hit.resolve()
            if path not in seen:
                seen.add(path)
                collected.append(path)

    return collected


def collect_domain_paths(
    explicit_domains: Optional[Sequence[str]],
    domain_groups: Optional[Sequence[Sequence[str]]],
) -> List[Path]:
    root = repo_root()
    collected: List[Path] = []
    seen = set()

    flat: List[str] = []
    for d in explicit_domains or []:
        flat.append(d)
    for group in domain_groups or []:
        flat.extend(group)

    for d in flat:
        candidate = Path(d)
        if not candidate.is_absolute():
            candidate = (root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if candidate not in seen:
            seen.add(candidate)
            collected.append(candidate)
    return collected


@dataclass
class BenchRow:
    domain: str
    input_problem: str
    compiled_problem: str
    heuristic: str
    search: str
    planner_args: str
    status: str
    actions: int
    time_sec: float
    returncode: Optional[int]
    stdout_file: str
    stderr_file: str


@dataclass(frozen=True)
class BenchTask:
    domain: Path
    input_problem: Path
    heuristic: str
    search: str


def default_run_dir(stamp: str) -> Path:
    return BENCHMARK_DIR / "results" / f"plus-bench_{stamp}"


def default_output_csv(run_dir: Path) -> Path:
    return run_dir / "plus_sweep.csv"


def default_output_plot(run_dir: Path) -> Path:
    return run_dir / "runtime.svg"


def generate_runtime_plot(csv_path: Path, out_path: Path, title: str) -> bool:
    if not PLOT_RUNTIME_SCRIPT.exists():
        print(f"[WARN] Plot script not found, skipping plot: {PLOT_RUNTIME_SCRIPT}")
        return False
    cmd = [
        sys.executable,
        str(PLOT_RUNTIME_SCRIPT),
        "--csv",
        str(csv_path),
        "--out",
        str(out_path),
        "--title",
        title,
        "--include-failures",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        print(f"[WARN] Failed to generate plot: {detail}")
        return False
    return True


def run_task(
    task: BenchTask,
    *,
    timeout: int,
    stream: bool,
    base_args: str,
    java_opts: str,
    problem_gen: Optional[Path],
    enhsp_jar: Optional[Path],
    run_dir: Path,
    plans_dir: Path,
) -> BenchRow:
    domain = task.domain
    input_problem = task.input_problem
    heuristic = task.heuristic
    search = task.search
    compiled_problem = input_problem
    tmpdir: Optional[tempfile.TemporaryDirectory] = None

    try:
        if input_problem.suffix.lower() == ".txt":
            compiled_problem, tmpdir = generate_problem_from_level(
                level_txt=input_problem,
                domain=domain,
                explicit_gen=problem_gen,
            )

        planner_args_parts = []
        if base_args.strip():
            planner_args_parts.extend(shlex.split(base_args))
        planner_args_parts.extend(["-h", heuristic, "-s", search])
        planner_args = " ".join(shlex.quote(p) for p in planner_args_parts)

        domain_tag = safe_tag(domain.stem)
        problem_name = normalise_problem_name(compiled_problem)
        problem_tag = safe_tag(problem_name)
        unique = f"plus-enhsp-bench-d_{domain_tag}-h_{safe_tag(heuristic)}-s_{safe_tag(search)}"
        stdout_path = run_dir / (
            f"plus-enhsp-bench-d_{domain_tag}-p_{problem_tag}-h_{safe_tag(heuristic)}-s_{safe_tag(search)}.stdout.txt"
        )
        stderr_path = run_dir / (
            f"plus-enhsp-bench-d_{domain_tag}-p_{problem_tag}-h_{safe_tag(heuristic)}-s_{safe_tag(search)}.stderr.txt"
        )

        try:
            result: PlusPlanResult = solve_plus(
                domain=domain,
                problem=compiled_problem,
                planner="enhsp",
                timeout=timeout,
                stream=stream,
                planner_args=planner_args,
                java_opts=java_opts,
                enhsp_jar=enhsp_jar.resolve() if enhsp_jar else None,
            )
        except Exception as exc:
            write_text_file(stdout_path, "")
            write_text_file(stderr_path, str(exc))
            return BenchRow(
                domain=str(domain),
                input_problem=str(input_problem),
                compiled_problem=str(compiled_problem),
                heuristic=heuristic,
                search=search,
                planner_args=planner_args,
                status="error",
                actions=0,
                time_sec=0.0,
                returncode=None,
                stdout_file=str(stdout_path),
                stderr_file=str(stderr_path),
            )

        elapsed = float(result.metrics.get("time_sec", 0.0) or 0.0)
        returncode = result.metrics.get("returncode")

        out_dir = plans_dir / problem_name
        write_plan_file(out_dir / f"{unique}.plan", result.actions)
        write_timed_plan_file(out_dir / f"{unique}.timed.plan", result.actions)
        write_text_file(stdout_path, result.raw_stdout)
        write_text_file(stderr_path, result.raw_stderr)

        return BenchRow(
            domain=str(domain),
            input_problem=str(input_problem),
            compiled_problem=str(compiled_problem),
            heuristic=heuristic,
            search=search,
            planner_args=planner_args,
            status=result.status,
            actions=len(result.actions),
            time_sec=elapsed,
            returncode=returncode if isinstance(returncode, int) else None,
            stdout_file=str(stdout_path),
            stderr_file=str(stderr_path),
        )
    finally:
        if tmpdir is not None:
            tmpdir.cleanup()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Benchmark ENHSP heuristic/search settings across multiple maps."
    )
    ap.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Domain PDDL path. Repeat flag for multiple domains.",
    )
    ap.add_argument(
        "--domains",
        nargs="+",
        action="append",
        default=[],
        help="Domain PDDL paths (space-separated). Can be supplied multiple times.",
    )
    ap.add_argument(
        "--maps",
        "--problems",
        dest="problems",
        nargs="+",
        default=None,
        help="Problem files (.pddl or .txt maps).",
    )
    ap.add_argument(
        "--problem-glob",
        action="append",
        default=[],
        help="Repo-root glob for problems, e.g. 'pddl/level_*_*.txt'.",
    )
    ap.add_argument(
        "--heuristics",
        nargs="+",
        required=True,
        help="Heuristics (space or comma separated), e.g. blind hadd hmax",
    )
    ap.add_argument(
        "--searches",
        nargs="+",
        required=True,
        help="Searches (space or comma separated), e.g. gbfs WAStar",
    )
    ap.add_argument("--enhsp-jar", type=Path, default=None, help="Path to enhsp.jar")
    ap.add_argument(
        "--java-opts",
        default="",
        help="Extra Java VM options for ENHSP. Use '--java-opts=-Xmx8g' for leading-dash opts.",
    )
    ap.add_argument("--timeout", type=int, default=120, help="Timeout per run in seconds.")
    ap.add_argument(
        "--base-args",
        default="-pe",
        help="Extra ENHSP args applied to every run, before -h/-s (default: -pe).",
    )
    ap.add_argument("--stream", action="store_true", help="Stream planner output live.")
    ap.add_argument(
        "--problem-gen",
        type=Path,
        default=None,
        help="Override generator script used for .txt maps.",
    )
    ap.add_argument("--output-csv", type=Path, default=None, help="CSV output path.")
    ap.add_argument("--output-plot", type=Path, default=None, help="Runtime plot SVG output path.")
    ap.add_argument("--output-json", type=Path, default=None, help="Optional JSON output path.")
    ap.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help=(
            "Run output directory. Defaults to tools/benchmarking/results/plus-bench_<timestamp>/ "
            "(contains CSV, plot, plans/, and logs)."
        ),
    )
    ap.add_argument(
        "--jobs",
        type=int,
        default=(os.cpu_count() or 1),
        help="Number of planner runs to execute in parallel (default: CPU cores).",
    )
    args = ap.parse_args()

    domains = collect_domain_paths(args.domain, args.domains)
    if not domains:
        print("[ERR] Provide at least one domain via --domain/--domains.", file=sys.stderr)
        return 2
    missing_domains = [d for d in domains if not d.exists()]
    if missing_domains:
        for d in missing_domains:
            print(f"[ERR] Domain not found: {d}", file=sys.stderr)
        return 2

    heuristics = split_items(args.heuristics)
    searches = split_items(args.searches)
    if not heuristics or not searches:
        print("[ERR] Provide at least one heuristic and one search strategy.", file=sys.stderr)
        return 2

    input_problems = collect_problem_paths(args.problems, args.problem_glob)
    if not input_problems:
        print("[ERR] Provide --maps/--problems and/or --problem-glob.", file=sys.stderr)
        return 2

    missing = [p for p in input_problems if not p.exists()]
    if missing:
        for p in missing:
            print(f"[ERR] Problem not found: {p}", file=sys.stderr)
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (
        args.results_dir.resolve()
        if args.results_dir
        else default_run_dir(stamp)
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    plans_dir = run_dir / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_csv.resolve() if args.output_csv else default_output_csv(run_dir)
    plot_path = args.output_plot.resolve() if args.output_plot else default_output_plot(run_dir)

    if args.jobs < 1:
        print("[ERR] --jobs must be >= 1.", file=sys.stderr)
        return 2

    tasks = [
        BenchTask(domain=domain, input_problem=input_problem, heuristic=heuristic, search=search)
        for domain in domains
        for input_problem in input_problems
        for heuristic in heuristics
        for search in searches
    ]
    total_runs = len(tasks)
    workers = min(args.jobs, total_runs) if total_runs else 1
    if args.stream and workers > 1:
        print("[WARN] --stream with --jobs > 1 can interleave planner logs.")

    rows: List[BenchRow] = []
    print(f"[INFO] Runs: {total_runs} | workers: {workers}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        future_to_task = {
            ex.submit(
                run_task,
                task,
                timeout=args.timeout,
                stream=args.stream,
                base_args=args.base_args,
                java_opts=args.java_opts,
                problem_gen=args.problem_gen,
                enhsp_jar=args.enhsp_jar,
                run_dir=run_dir,
                plans_dir=plans_dir,
            ): task
            for task in tasks
        }
        done = 0
        for fut in concurrent.futures.as_completed(future_to_task):
            done += 1
            task = future_to_task[fut]
            try:
                row = fut.result()
            except Exception as exc:
                print(
                    f"[{done}/{total_runs}] {task.domain.name} | {task.input_problem.name} | "
                    f"-h {task.heuristic} | -s {task.search} -> error ({exc})"
                )
                continue
            rows.append(row)
            print(
                f"[{done}/{total_runs}] {task.domain.name} | {task.input_problem.name} | "
                f"-h {task.heuristic} | -s {task.search} -> {row.status} | "
                f"time={row.time_sec:.3f}s | actions={row.actions}"
            )

    rows.sort(key=lambda r: (r.domain, r.input_problem, r.heuristic, r.search))

    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "domain",
                "input_problem",
                "compiled_problem",
                "heuristic",
                "search",
                "planner_args",
                "status",
                "actions",
                "time_sec",
                "returncode",
                "stdout_file",
                "stderr_file",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    plot_generated = generate_runtime_plot(csv_path=csv_path, out_path=plot_path, title="ENHSP Runtime Sweep")

    solved = [r for r in rows if r.status == "solved"]
    timeouts = [r for r in rows if r.status == "timeout"]
    errors = [r for r in rows if r.status == "error"]
    print("\n== Sweep Summary ==")
    print(f"- runs: {len(rows)}")
    print(f"- solved: {len(solved)}")
    print(f"- timeout: {len(timeouts)}")
    print(f"- error: {len(errors)}")
    print(f"- run_dir: {run_dir}")
    print(f"- plans: {plans_dir}")
    print(f"- csv: {csv_path}")
    print(f"- plot: {plot_path if plot_generated else 'not generated'}")

    if args.output_json:
        json_path = args.output_json.resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "domains": [str(d) for d in domains],
            "timeout_sec": args.timeout,
            "base_args": args.base_args,
            "java_opts": args.java_opts,
            "results_dir": str(run_dir),
            "rows": [asdict(r) for r in rows],
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
