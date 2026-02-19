#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from plan import (  # type: ignore
    PlanResult,
    normalise_problem_name,
    repo_root,
    solve_with_fd,
    solve_with_ff,
    write_direction_plan,
    write_plan_file,
    write_text_file,
)


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
    domain_name = domain.name.lower()
    if "scanner_separated" in domain_name or "scaner_separated" in domain_name:
        return repo_root() / "pddl" / "problem_gen_scanner_separated.py"
    return repo_root() / "pddl" / "problem_gen.py"


def generate_problem_from_level(
    level_txt: Path,
    domain: Path,
    explicit_gen: Optional[Path],
) -> Tuple[Path, tempfile.TemporaryDirectory]:
    gen_py = explicit_gen.resolve() if explicit_gen else select_problem_gen(domain)
    if not gen_py.exists():
        raise FileNotFoundError(f"Missing problem generator at {gen_py}")

    tmpdir = tempfile.TemporaryDirectory(prefix="bench_classic_problem_")
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


def safe_tag(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9_+\-]+", "_", lowered)
    return lowered.strip("_") or "x"


def variant_to_run(variant: str, domain: Path, problem: Path, timeout: int | None, stream: bool) -> PlanResult:
    if variant == "ff":
        return solve_with_ff(domain, problem, timeout=timeout, stream=stream)
    if variant == "fd":
        return solve_with_fd(domain, problem, timeout=timeout, optimal=False, stream=stream, keep_searching=False)
    if variant == "fd-opt":
        return solve_with_fd(domain, problem, timeout=timeout, optimal=True, stream=stream, keep_searching=False)
    if variant == "fd-any":
        return solve_with_fd(domain, problem, timeout=timeout, optimal=False, stream=stream, keep_searching=True)
    raise ValueError(f"Unsupported variant: {variant}")


def default_variants(planner: str) -> List[str]:
    if planner == "ff":
        return ["ff"]
    if planner == "fd":
        return ["fd"]
    return ["ff", "fd"]


def default_output_csv() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return repo_root() / "plans" / "classic-bench" / f"classic_sweep_{stamp}.csv"


@dataclass
class BenchRow:
    domain: str
    input_problem: str
    compiled_problem: str
    variant: str
    planner: str
    status: str
    actions: int
    time_sec: float
    returncode: Optional[int]
    stdout_file: str
    stderr_file: str


def main() -> int:
    ap = argparse.ArgumentParser(description="Benchmark classic PDDL planners (FF/FD) across multiple maps.")
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
        "--planner",
        choices=["ff", "fd", "both"],
        default="fd",
        help="Base planner group. Ignored if --variants is supplied.",
    )
    ap.add_argument(
        "--variants",
        nargs="+",
        default=None,
        help="Planner variants (comma/space separated): ff, fd, fd-opt, fd-any",
    )
    ap.add_argument("--timeout", type=int, default=120, help="Timeout per run in seconds.")
    ap.add_argument("--stream", action="store_true", help="Stream planner output live.")
    ap.add_argument("--problem-gen", type=Path, default=None, help="Override generator script used for .txt maps.")
    ap.add_argument("--output-csv", type=Path, default=None, help="CSV output path.")
    ap.add_argument("--output-json", type=Path, default=None, help="Optional JSON output path.")
    ap.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Directory for benchmark stdout/stderr files. Default: results/classic-bench/run_<timestamp>/",
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

    input_problems = collect_problem_paths(args.problems, args.problem_glob)
    if not input_problems:
        print("[ERR] Provide --maps/--problems and/or --problem-glob.", file=sys.stderr)
        return 2

    missing = [p for p in input_problems if not p.exists()]
    if missing:
        for p in missing:
            print(f"[ERR] Problem not found: {p}", file=sys.stderr)
        return 2

    variants = split_items(args.variants) if args.variants else default_variants(args.planner)
    allowed = {"ff", "fd", "fd-opt", "fd-any"}
    bad = [v for v in variants if v not in allowed]
    if bad:
        print(f"[ERR] Unsupported variants: {', '.join(sorted(set(bad)))}", file=sys.stderr)
        print(f"[ERR] Allowed variants: {', '.join(sorted(allowed))}", file=sys.stderr)
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = (
        args.results_dir.resolve()
        if args.results_dir
        else (repo_root() / "results" / "classic-bench" / f"run_{stamp}")
    )
    results_dir.mkdir(parents=True, exist_ok=True)

    rows: List[BenchRow] = []
    total_runs = len(domains) * len(input_problems) * len(variants)
    run_idx = 0

    for domain in domains:
        for input_problem in input_problems:
            compiled_problem = input_problem
            tmpdir: Optional[tempfile.TemporaryDirectory] = None
            try:
                if input_problem.suffix.lower() == ".txt":
                    compiled_problem, tmpdir = generate_problem_from_level(
                        input_problem, domain=domain, explicit_gen=args.problem_gen
                    )

                for variant in variants:
                    run_idx += 1
                    print(f"[{run_idx}/{total_runs}] {domain.name} | {input_problem.name} | variant={variant}")

                    domain_tag = safe_tag(domain.stem)
                    problem_name = normalise_problem_name(compiled_problem)
                    problem_tag = safe_tag(problem_name)
                    variant_tag = safe_tag(variant)
                    stdout_path = results_dir / (
                        f"classic-bench-d_{domain_tag}-p_{problem_tag}-v_{variant_tag}.stdout.txt"
                    )
                    stderr_path = results_dir / (
                        f"classic-bench-d_{domain_tag}-p_{problem_tag}-v_{variant_tag}.stderr.txt"
                    )

                    try:
                        result = variant_to_run(
                            variant=variant,
                            domain=domain,
                            problem=compiled_problem,
                            timeout=args.timeout,
                            stream=args.stream,
                        )
                    except Exception as exc:
                        write_text_file(stdout_path, "")
                        write_text_file(stderr_path, str(exc))
                        rows.append(
                            BenchRow(
                                domain=str(domain),
                                input_problem=str(input_problem),
                                compiled_problem=str(compiled_problem),
                                variant=variant,
                                planner=variant,
                                status="error",
                                actions=0,
                                time_sec=0.0,
                                returncode=None,
                                stdout_file=str(stdout_path),
                                stderr_file=str(stderr_path),
                            )
                        )
                        print(f"  -> error ({exc})")
                        continue

                    elapsed = float(result.metrics.get("time_sec", 0.0) or 0.0)
                    returncode = result.metrics.get("returncode")

                    out_dir = repo_root() / "plans" / problem_name
                    tag = f"classic-bench-d_{domain_tag}-v_{variant_tag}"
                    plan_path = out_dir / f"{tag}.plan"
                    write_plan_file(plan_path, result.actions)
                    if result.actions:
                        write_direction_plan(out_dir / f"{tag}.play.plan", result.actions)
                    write_text_file(stdout_path, result.raw_stdout)
                    write_text_file(stderr_path, result.raw_stderr)

                    rows.append(
                        BenchRow(
                            domain=str(domain),
                            input_problem=str(input_problem),
                            compiled_problem=str(compiled_problem),
                            variant=variant,
                            planner=result.planner,
                            status=result.status,
                            actions=len(result.actions),
                            time_sec=elapsed,
                            returncode=returncode if isinstance(returncode, int) else None,
                            stdout_file=str(stdout_path),
                            stderr_file=str(stderr_path),
                        )
                    )
                    print(f"  -> {result.status} | time={elapsed:.3f}s | actions={len(result.actions)}")
            finally:
                if tmpdir is not None:
                    tmpdir.cleanup()

    csv_path = args.output_csv.resolve() if args.output_csv else default_output_csv()
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "domain",
                "input_problem",
                "compiled_problem",
                "variant",
                "planner",
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

    solved = [r for r in rows if r.status == "solved"]
    timeouts = [r for r in rows if r.status == "timeout"]
    errors = [r for r in rows if r.status == "error"]
    print("\n== Sweep Summary ==")
    print(f"- runs: {len(rows)}")
    print(f"- solved: {len(solved)}")
    print(f"- timeout: {len(timeouts)}")
    print(f"- error: {len(errors)}")
    print(f"- csv: {csv_path}")
    print(f"- results: {results_dir}")

    if args.output_json:
        json_path = args.output_json.resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "domains": [str(d) for d in domains],
            "variants": variants,
            "timeout_sec": args.timeout,
            "results_dir": str(results_dir),
            "rows": [asdict(r) for r in rows],
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"- json: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
