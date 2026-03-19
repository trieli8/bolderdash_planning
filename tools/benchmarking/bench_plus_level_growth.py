#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import os
import re
import subprocess
import sys
import tempfile
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

TOOLS_DIR = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
PLOT_LEVEL_GROWTH_SCRIPT = BENCHMARK_DIR / "ploters" / "plot_level_growth.py"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))


def repo_root() -> Path:
    return REPO_ROOT


PLUS_RUNNER_DIR = repo_root() / "planners" / "pddl-plus"
sys.path.insert(0, str(PLUS_RUNNER_DIR))
from pddl_plus_runner import PlusPlanResult, solve as solve_plus  # type: ignore  # noqa: E402
from plan import PlanResult, solve_with_fd, solve_with_ff  # type: ignore  # noqa: E402


def safe_tag(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9_+\-]+", "_", lowered)
    return lowered.strip("_") or "x"


def collect_paths(explicit: Optional[Sequence[str]], globs: Optional[Sequence[str]]) -> List[Path]:
    root = repo_root()
    collected: List[Path] = []
    seen = set()

    for raw in explicit or []:
        p = Path(raw)
        p = (root / p).resolve() if not p.is_absolute() else p.resolve()
        if p not in seen:
            seen.add(p)
            collected.append(p)

    for pattern in globs or []:
        for hit in sorted(root.glob(pattern)):
            p = hit.resolve()
            if p not in seen:
                seen.add(p)
                collected.append(p)

    return collected


@dataclass
class LevelInfo:
    path: Path
    rows: int
    cols: int
    cells: int


def parse_level_size(level_path: Path) -> LevelInfo:
    text = level_path.read_text(encoding="utf-8", errors="replace").strip()
    parts = [p.strip() for p in text.split("|") if p.strip()]
    if len(parts) < 2:
        raise ValueError(f"Could not read rows/cols from level file: {level_path}")
    rows = int(parts[0])
    cols = int(parts[1])
    return LevelInfo(path=level_path, rows=rows, cols=cols, cells=rows * cols)


def select_levels(
    level_paths: Sequence[Path],
    unique_sizes_only: bool,
) -> List[LevelInfo]:
    parsed: List[LevelInfo] = []
    for p in level_paths:
        parsed.append(parse_level_size(p))

    parsed.sort(key=lambda x: (x.cells, x.rows, x.cols, x.path.name))
    if not unique_sizes_only:
        return parsed

    out: List[LevelInfo] = []
    seen_sizes = set()
    for info in parsed:
        size_key = (info.rows, info.cols)
        if size_key in seen_sizes:
            continue
        seen_sizes.add(size_key)
        out.append(info)
    return out


def parse_size_token(token: str) -> Tuple[int, int]:
    m = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", token)
    if not m:
        raise ValueError(f"Invalid size token '{token}'. Use ROWSxCOLS format (e.g. 6x11).")
    rows = int(m.group(1))
    cols = int(m.group(2))
    return rows, cols


def parse_size_values(values: Optional[Sequence[str]]) -> List[Tuple[int, int]]:
    if not values:
        return []
    sizes: List[Tuple[int, int]] = []
    for raw in values:
        for part in raw.split(","):
            token = part.strip()
            if not token:
                continue
            sizes.append(parse_size_token(token))
    return sizes


def build_generated_sizes(
    explicit_sizes: Optional[Sequence[str]],
    min_size: int,
    max_size: int,
    size_step: int,
) -> List[Tuple[int, int]]:
    if size_step <= 0:
        raise ValueError("--size-step must be >= 1")

    if explicit_sizes:
        sizes = parse_size_values(explicit_sizes)
    else:
        if min_size < 2 or max_size < 2:
            raise ValueError("--min-size and --max-size must be >= 2")
        if min_size > max_size:
            raise ValueError("--min-size must be <= --max-size")
        sizes = [(n, n) for n in range(min_size, max_size + 1, size_step)]

    deduped = sorted(set(sizes), key=lambda x: (x[0] * x[1], x[0], x[1]))
    if not deduped:
        raise ValueError("No generated sizes selected.")

    for rows, cols in deduped:
        if rows <= 0 or cols <= 0:
            raise ValueError(f"Invalid size {rows}x{cols}; dimensions must be > 0.")
        if rows * cols < 4:
            raise ValueError(
                f"Invalid size {rows}x{cols}; need at least 4 cells to include agent/dirt/stone/gem."
            )
    return deduped


def generate_level_text(
    rows: int,
    cols: int,
    required_gems: int,
    max_time_min: int,
    max_time_scale: int,
) -> str:
    # HiddenCellType IDs expected by existing problem generators.
    AGENT = 0
    DIRT = 2
    STONE = 3
    GEM = 5

    grid = [[DIRT for _ in range(cols)] for _ in range(rows)]

    agent_pos = (0, 0)
    # Place gem as far from the agent as possible to avoid trivial maps.
    gem_pos = None
    best_dist = -1
    for r in range(rows):
        for c in range(cols):
            if (r, c) == agent_pos:
                continue
            dist = abs(r - agent_pos[0]) + abs(c - agent_pos[1])
            if dist > best_dist:
                best_dist = dist
                gem_pos = (r, c)
            elif dist == best_dist and gem_pos is not None and (r, c) > gem_pos:
                # Deterministic tie-breaker: prefer bottom-right-ish coordinates.
                gem_pos = (r, c)
    if gem_pos is None or best_dist <= 1:
        raise ValueError(f"Could not place non-adjacent gem for {rows}x{cols}")

    blocked = {agent_pos, gem_pos}
    stone_candidates = [
        (rows // 2, cols // 2),
        (rows - 1, 0),
        (0, cols - 1),
        (rows - 1, cols - 1),
    ]
    stone_pos = None
    for r, c in stone_candidates:
        if 0 <= r < rows and 0 <= c < cols and (r, c) not in blocked:
            stone_pos = (r, c)
            break
    if stone_pos is None:
        for r in range(rows - 1, -1, -1):
            for c in range(cols - 1, -1, -1):
                if (r, c) not in blocked:
                    stone_pos = (r, c)
                    break
            if stone_pos is not None:
                break
    if stone_pos is None:
        raise ValueError(f"Could not place stone for {rows}x{cols}")

    grid[agent_pos[0]][agent_pos[1]] = AGENT
    grid[gem_pos[0]][gem_pos[1]] = GEM
    grid[stone_pos[0]][stone_pos[1]] = STONE

    max_time = max(max_time_min, rows * cols * max_time_scale)
    header = f"{rows}|{cols}|{max_time}|{required_gems}|"
    body = "\n".join("|".join(f"{cell:02d}" for cell in row) + "|" for row in grid)
    return f"{header}\n{body}\n"


def write_generated_levels(
    out_dir: Path,
    sizes: Sequence[Tuple[int, int]],
    required_gems: int,
    max_time_min: int,
    max_time_scale: int,
) -> List[LevelInfo]:
    out_dir.mkdir(parents=True, exist_ok=True)
    levels: List[LevelInfo] = []
    for rows, cols in sizes:
        path = out_dir / f"generated_{rows:03d}x{cols:03d}.txt"
        txt = generate_level_text(
            rows=rows,
            cols=cols,
            required_gems=required_gems,
            max_time_min=max_time_min,
            max_time_scale=max_time_scale,
        )
        path.write_text(txt, encoding="utf-8")
        levels.append(LevelInfo(path=path, rows=rows, cols=cols, cells=rows * cols))
    levels.sort(key=lambda x: (x.cells, x.rows, x.cols, x.path.name))
    return levels


def select_problem_gen(domain: Path) -> Path:
    name = domain.name.lower()
    root = repo_root()

    if "scanner_separated_events_fluents_trimmed" in name:
        return root / "pddl" / "problem_gen_plus_scanner_separated_events_fluents_trimmed.py"
    if "scanner_separated_events_fluents" in name:
        return root / "pddl" / "problem_gen_plus_scanner_separated_events_fluents.py"
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

    tmpdir = tempfile.TemporaryDirectory(prefix="bench_plus_level_growth_")
    out_path = Path(tmpdir.name) / f"{level_txt.stem}.pddl"

    cmd = [sys.executable, str(gen_py), str(level_txt), "-p", level_txt.stem]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        tmpdir.cleanup()
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"{gen_py.name} failed (rc={proc.returncode}): {detail}")

    out_path.write_text(proc.stdout, encoding="utf-8")
    return out_path, tmpdir


def parse_ms(text: str, pattern: str) -> Optional[float]:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1)) / 1000.0
    except Exception:
        return None


def parse_int(text: str, pattern: str) -> Optional[int]:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def parse_sec(text: str, pattern: str) -> Optional[float]:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def is_plus_domain(domain: Path) -> bool:
    return "plus" in domain.name.lower()


def parse_plus_metrics(full_text: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[int]]:
    grounding_sec = parse_ms(full_text, r"Grounding Time:\s*([0-9]+(?:\.[0-9]+)?)")
    heuristic_sec = parse_ms(full_text, r"Heuristic Time\s*\(msec\):\s*([0-9]+(?:\.[0-9]+)?)")
    search_sec = parse_ms(full_text, r"Search Time\s*\(msec\):\s*([0-9]+(?:\.[0-9]+)?)")
    action_set_size = parse_int(full_text, r"\|A\|:\s*([0-9]+)")
    return grounding_sec, heuristic_sec, search_sec, action_set_size


def parse_classic_metrics(full_text: str) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[int]]:
    grounding_sec = parse_sec(full_text, r"Done!\s*\[[0-9]+(?:\.[0-9]+)?s CPU,\s*([0-9]+(?:\.[0-9]+)?)s wall-clock\]")
    if grounding_sec is None:
        grounding_sec = parse_sec(full_text, r"translator wall-clock time:\s*([0-9]+(?:\.[0-9]+)?)s")

    heuristic_sec = None

    search_sec = parse_sec(full_text, r"Search time:\s*([0-9]+(?:\.[0-9]+)?)s")
    if search_sec is None:
        search_sec = parse_sec(full_text, r"Actual search time:\s*([0-9]+(?:\.[0-9]+)?)s")

    action_set_size = parse_int(full_text, r"Translator operators:\s*([0-9]+)")
    return grounding_sec, heuristic_sec, search_sec, action_set_size


@dataclass
class GrowthRow:
    domain: str
    domain_kind: str
    level: str
    rows: int
    cols: int
    cells: int
    planner: str
    heuristic: str
    search: str
    planner_args: str
    status: str
    runtime_sec: float
    grounding_sec: Optional[float]
    heuristic_sec: Optional[float]
    search_sec: Optional[float]
    action_set_size: Optional[int]
    plan_action_count: int
    returncode: Optional[int]
    stdout_file: str
    stderr_file: str
    plan_file: str
    timed_plan_file: str


CSV_FIELDS = list(GrowthRow.__annotations__.keys())


def default_output_csv() -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return default_run_dir(stamp) / "level_growth.csv"


def default_run_dir(stamp: str) -> Path:
    return BENCHMARK_DIR / "results" / f"plus-level-growth_{stamp}"


def default_output_plot(run_dir: Path) -> Path:
    return run_dir / "growth.svg"


def build_planner_args(base_args: str, heuristic: str, search: str) -> str:
    args: List[str] = []
    if base_args.strip():
        args.append(base_args.strip())
    args.append(f"-h {heuristic}")
    args.append(f"-s {search}")
    return " ".join(args).strip()


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def write_plus_plan_file(path: Path, actions: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    for a in actions:
        if a.args:
            lines.append(f"({a.name} {' '.join(a.args)})")
        else:
            lines.append(f"({a.name})")
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_plus_timed_plan_file(path: Path, actions: list) -> None:
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


def write_classic_plan_file(path: Path, actions: list[tuple[str, list[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    for name, args in actions:
        if args:
            lines.append(f"({name} {' '.join(args)})")
        else:
            lines.append(f"({name})")
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def generate_growth_plot(csv_path: Path, out_path: Path, title: str) -> bool:
    if not PLOT_LEVEL_GROWTH_SCRIPT.exists():
        print(f"[WARN] Plot script not found, skipping plot: {PLOT_LEVEL_GROWTH_SCRIPT}")
        return False
    cmd = [
        sys.executable,
        str(PLOT_LEVEL_GROWTH_SCRIPT),
        "--csv",
        str(csv_path),
        "--out",
        str(out_path),
        "--title",
        title,
        "--include-skipped",
        "--include-dry-run",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        print(f"[WARN] Failed to generate plot: {detail}")
        return False
    return True


def run_domain(
    domain: Path,
    *,
    levels: Sequence[LevelInfo],
    total_runs: int,
    progress_counter: List[int],
    progress_lock: threading.Lock,
    args: argparse.Namespace,
    planner_args: str,
    run_dir: Path,
    plans_dir: Path,
) -> List[GrowthRow]:
    domain_rows: List[GrowthRow] = []
    domain_kind = "plus" if is_plus_domain(domain) else "classic"
    stop_after_timeout = False
    timeout_cutoff_level = ""

    for level in levels:
        with progress_lock:
            progress_counter[0] += 1
            run_idx = progress_counter[0]

        print(
            f"[{run_idx}/{total_runs}] {domain.name} | {level.path.name} "
            f"({level.rows}x{level.cols}, {level.cells} cells) [{domain_kind}]"
        )

        domain_tag = safe_tag(domain.stem)
        level_tag = safe_tag(level.path.stem)
        stdout_file = run_dir / f"growth-d_{domain_tag}-l_{level_tag}.stdout.txt"
        stderr_file = run_dir / f"growth-d_{domain_tag}-l_{level_tag}.stderr.txt"

        planner_label = args.planner if domain_kind == "plus" else args.classic_planner
        heuristic_label = args.heuristic if domain_kind == "plus" else ""
        search_label = args.search if domain_kind == "plus" else ""
        planner_args_label = planner_args if domain_kind == "plus" else ""
        plan_file = plans_dir / f"growth-d_{domain_tag}-l_{level_tag}.plan"
        timed_plan_file = plans_dir / f"growth-d_{domain_tag}-l_{level_tag}.timed.plan"

        if stop_after_timeout:
            note = (
                f"[SKIP] Skipped because {domain.name} timed out at smaller level "
                f"{timeout_cutoff_level}.\n"
            )
            write_text_file(stdout_file, "")
            write_text_file(stderr_file, note)
            domain_rows.append(
                GrowthRow(
                    domain=str(domain),
                    domain_kind=domain_kind,
                    level=str(level.path),
                    rows=level.rows,
                    cols=level.cols,
                    cells=level.cells,
                    planner=planner_label,
                    heuristic=heuristic_label,
                    search=search_label,
                    planner_args=planner_args_label,
                    status="skipped_after_timeout",
                    runtime_sec=0.0,
                    grounding_sec=None,
                    heuristic_sec=None,
                    search_sec=None,
                    action_set_size=None,
                    plan_action_count=0,
                    returncode=None,
                    stdout_file=str(stdout_file),
                    stderr_file=str(stderr_file),
                    plan_file="",
                    timed_plan_file="",
                )
            )
            print(f"  [SKIP] timeout cutoff at {timeout_cutoff_level}")
            continue

        if args.dry_run:
            write_text_file(stdout_file, "")
            write_text_file(stderr_file, "")
            domain_rows.append(
                GrowthRow(
                    domain=str(domain),
                    domain_kind=domain_kind,
                    level=str(level.path),
                    rows=level.rows,
                    cols=level.cols,
                    cells=level.cells,
                    planner=planner_label,
                    heuristic=heuristic_label,
                    search=search_label,
                    planner_args=planner_args_label,
                    status="dry-run",
                    runtime_sec=0.0,
                    grounding_sec=None,
                    heuristic_sec=None,
                    search_sec=None,
                    action_set_size=None,
                    plan_action_count=0,
                    returncode=None,
                    stdout_file=str(stdout_file),
                    stderr_file=str(stderr_file),
                    plan_file="",
                    timed_plan_file="",
                )
            )
            continue

        tmpdir: Optional[tempfile.TemporaryDirectory] = None
        compile_error = None
        compiled_problem: Optional[Path] = None

        try:
            compiled_problem, tmpdir = generate_problem_from_level(
                level_txt=level.path,
                domain=domain,
                explicit_gen=args.problem_gen,
            )
        except Exception as exc:
            compile_error = str(exc)

        if compile_error is not None or compiled_problem is None:
            err_text = f"[ERR] Problem generation failed: {compile_error}\n"
            write_text_file(stdout_file, "")
            write_text_file(stderr_file, err_text)
            domain_rows.append(
                GrowthRow(
                    domain=str(domain),
                    domain_kind=domain_kind,
                    level=str(level.path),
                    rows=level.rows,
                    cols=level.cols,
                    cells=level.cells,
                    planner=planner_label,
                    heuristic=heuristic_label,
                    search=search_label,
                    planner_args=planner_args_label,
                    status="error",
                    runtime_sec=0.0,
                    grounding_sec=None,
                    heuristic_sec=None,
                    search_sec=None,
                    action_set_size=None,
                    plan_action_count=0,
                    returncode=None,
                    stdout_file=str(stdout_file),
                    stderr_file=str(stderr_file),
                    plan_file="",
                    timed_plan_file="",
                )
            )
            continue

        try:
            plan_file_str = ""
            timed_plan_file_str = ""
            if domain_kind == "plus":
                plus_result: PlusPlanResult = solve_plus(
                    domain=domain,
                    problem=compiled_problem,
                    planner=args.planner,
                    timeout=args.timeout,
                    stream=args.stream,
                    planner_args=planner_args,
                    java_opts=args.java_opts,
                    cmd_template=args.cmd_template,
                    enhsp_jar=args.enhsp_jar.resolve() if args.enhsp_jar else None,
                    optic_bin=args.optic_bin.resolve() if args.optic_bin else None,
                )
                out_text = plus_result.raw_stdout or ""
                err_text = plus_result.raw_stderr or ""
                status = plus_result.status
                runtime_sec = float(plus_result.metrics.get("time_sec") or 0.0)
                returncode = plus_result.metrics.get("returncode")
                plan_action_count = len(plus_result.actions)
                planner_label = plus_result.planner
                heuristic_label = args.heuristic
                search_label = args.search
                planner_args_label = planner_args
                if plus_result.actions:
                    write_plus_plan_file(plan_file, plus_result.actions)
                    write_plus_timed_plan_file(timed_plan_file, plus_result.actions)
                    plan_file_str = str(plan_file)
                    timed_plan_file_str = str(timed_plan_file)
            else:
                if args.classic_planner == "ff":
                    classic_result: PlanResult = solve_with_ff(
                        domain=domain,
                        problem=compiled_problem,
                        timeout=args.timeout,
                        stream=args.stream,
                    )
                else:
                    classic_result = solve_with_fd(
                        domain=domain,
                        problem=compiled_problem,
                        timeout=args.timeout,
                        optimal=args.fd_optimal,
                        stream=args.stream,
                        keep_searching=args.fd_keep_searching,
                    )
                out_text = classic_result.raw_stdout or ""
                err_text = classic_result.raw_stderr or ""
                status = classic_result.status
                runtime_sec = float(classic_result.metrics.get("time_sec") or 0.0)
                returncode = classic_result.metrics.get("returncode")
                plan_action_count = len(classic_result.actions)
                planner_label = classic_result.planner
                heuristic_label = ""
                search_label = ""
                planner_args_label = ""
                if classic_result.actions:
                    write_classic_plan_file(plan_file, classic_result.actions)
                    plan_file_str = str(plan_file)
        except Exception as exc:
            out_text = ""
            err_text = f"[ERR] Planner execution failed: {exc}\n"
            status = "error"
            runtime_sec = 0.0
            returncode = None
            plan_action_count = 0
            plan_file_str = ""
            timed_plan_file_str = ""
        finally:
            if tmpdir is not None:
                tmpdir.cleanup()

        write_text_file(stdout_file, out_text)
        write_text_file(stderr_file, err_text)

        full_text = out_text + "\n" + err_text
        if domain_kind == "plus":
            grounding_sec, heuristic_sec, search_sec, action_set_size = parse_plus_metrics(full_text)
        else:
            grounding_sec, heuristic_sec, search_sec, action_set_size = parse_classic_metrics(full_text)

        domain_rows.append(
            GrowthRow(
                domain=str(domain),
                domain_kind=domain_kind,
                level=str(level.path),
                rows=level.rows,
                cols=level.cols,
                cells=level.cells,
                planner=planner_label,
                heuristic=heuristic_label,
                search=search_label,
                planner_args=planner_args_label,
                status=status,
                runtime_sec=runtime_sec,
                grounding_sec=grounding_sec,
                heuristic_sec=heuristic_sec,
                search_sec=search_sec,
                action_set_size=action_set_size,
                plan_action_count=plan_action_count,
                returncode=returncode,
                stdout_file=str(stdout_file),
                stderr_file=str(stderr_file),
                plan_file=plan_file_str,
                timed_plan_file=timed_plan_file_str,
            )
        )

        if status == "timeout":
            stop_after_timeout = True
            timeout_cutoff_level = level.path.name
            print(
                f"  [TIMEOUT] {domain.name} timed out at {timeout_cutoff_level}; "
                "skipping larger levels for this domain."
            )

    return domain_rows


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Run domains on levels sorted by increasing size and record runtime, "
            "grounding, heuristic, search, and action-set size."
        )
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
        "--domain-glob",
        action="append",
        default=[],
        help="Repo-root glob for domains, e.g. 'pddl/domain*.pddl'.",
    )
    ap.add_argument(
        "--level",
        action="append",
        default=[],
        help="Level .txt path. Repeat flag for multiple levels.",
    )
    ap.add_argument(
        "--levels",
        nargs="+",
        action="append",
        default=[],
        help="Level .txt paths (space-separated). Can be supplied multiple times.",
    )
    ap.add_argument(
        "--level-glob",
        action="append",
        default=[],
        help="Repo-root glob for levels, e.g. 'pddl/level*.txt'.",
    )
    ap.add_argument(
        "--sizes",
        nargs="+",
        default=None,
        help=(
            "Generated level sizes in ROWSxCOLS format (comma/space separated), "
            "e.g. '4x4 5x5 6x7'. Used only when no --level/--levels/--level-glob is supplied."
        ),
    )
    ap.add_argument("--min-size", type=int, default=4, help="Generated square min side when auto-generating levels.")
    ap.add_argument("--max-size", type=int, default=20, help="Generated square max side when auto-generating levels.")
    ap.add_argument("--size-step", type=int, default=1, help="Generated square side step (smaller steps => denser growth).")
    ap.add_argument(
        "--generated-level-dir",
        type=Path,
        default=None,
        help="Directory to write generated levels. Default: <results-dir>/generated-levels/",
    )
    ap.add_argument("--required-gems", type=int, default=1, help="Required gems value written into generated levels.")
    ap.add_argument("--max-time-min", type=int, default=200, help="Minimum max_time written into generated levels.")
    ap.add_argument(
        "--max-time-scale",
        type=int,
        default=8,
        help="Generated max_time scaling factor: max(rows*cols*scale, max-time-min).",
    )
    ap.add_argument(
        "--all-level-variants",
        action="store_true",
        help="Keep multiple levels with the same rows/cols instead of selecting one per size.",
    )
    ap.add_argument("--planner", choices=["auto", "enhsp", "optic", "cmd"], default="auto")
    ap.add_argument("--heuristic", default="ngc", help="ENHSP heuristic (default: ngc)")
    ap.add_argument("--search", default="gbfs", help="ENHSP search strategy (default: gbfs)")
    ap.add_argument(
        "--base-args",
        default="-pe -dap",
        help="Planner args prepended before -h/-s (default: '-pe -dap').",
    )
    ap.add_argument(
        "--classic-planner",
        choices=["fd", "ff"],
        default="fd",
        help="Planner used for non-plus domains (default: fd).",
    )
    ap.add_argument(
        "--fd-optimal",
        action="store_true",
        help="Classic FD only: use optimal search setup.",
    )
    ap.add_argument(
        "--fd-keep-searching",
        action="store_true",
        help="Classic FD only: keep searching for better plans until timeout.",
    )
    ap.add_argument("--timeout", type=int, default=120, help="Timeout per run in seconds.")
    ap.add_argument("--stream", action="store_true", help="Stream planner output live.")
    ap.add_argument("--java-opts", default="", help="Extra Java opts passed to ENHSP.")
    ap.add_argument("--enhsp-jar", type=Path, default=None)
    ap.add_argument("--optic-bin", type=Path, default=None)
    ap.add_argument("--cmd-template", default=None, help="Required if --planner cmd.")
    ap.add_argument(
        "--problem-gen",
        type=Path,
        default=None,
        help="Override generator script used for all .txt levels.",
    )
    ap.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help=(
            "Run output directory. Defaults to tools/benchmarking/results/plus-level-growth_<timestamp>/ "
            "(contains CSV, plot, plans/, and logs)."
        ),
    )
    ap.add_argument("--output-csv", type=Path, default=None, help="CSV output path.")
    ap.add_argument("--output-plot", type=Path, default=None, help="Growth plot SVG output path.")
    ap.add_argument(
        "--jobs",
        type=int,
        default=(os.cpu_count() or 1),
        help="Number of domain workers to execute in parallel (default: CPU cores).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Print run matrix without executing planners.")
    args = ap.parse_args()

    domain_args: List[str] = []
    domain_args.extend(args.domain)
    for group in args.domains:
        domain_args.extend(group)

    level_args: List[str] = []
    level_args.extend(args.level)
    for group in args.levels:
        level_args.extend(group)

    domain_globs: List[str] = list(args.domain_glob)
    if not domain_args and not domain_globs:
        domain_globs = ["pddl/domain*.pddl"]

    domains = collect_paths(domain_args, domain_globs)
    if not domains:
        print("[ERR] No domains found. Use --domain/--domains/--domain-glob.", file=sys.stderr)
        return 2

    missing_domains = [d for d in domains if not d.exists()]
    if missing_domains:
        for d in missing_domains:
            print(f"[ERR] Domain not found: {d}", file=sys.stderr)
        return 2

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = (
        args.results_dir.resolve()
        if args.results_dir
        else default_run_dir(stamp)
    )
    output_csv = args.output_csv.resolve() if args.output_csv else (run_dir / "level_growth.csv")
    output_plot = args.output_plot.resolve() if args.output_plot else default_output_plot(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    plans_dir = run_dir / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    level_globs: List[str] = list(args.level_glob)
    use_explicit_levels = bool(level_args or level_globs)

    if use_explicit_levels:
        level_paths = collect_paths(level_args, level_globs)
        if not level_paths:
            print("[ERR] No levels found. Use --level/--levels/--level-glob.", file=sys.stderr)
            return 2

        missing_levels = [p for p in level_paths if not p.exists()]
        if missing_levels:
            for p in missing_levels:
                print(f"[ERR] Level not found: {p}", file=sys.stderr)
            return 2

        try:
            levels = select_levels(level_paths, unique_sizes_only=not args.all_level_variants)
        except Exception as exc:
            print(f"[ERR] Failed to parse level sizes: {exc}", file=sys.stderr)
            return 2
    else:
        try:
            sizes = build_generated_sizes(
                explicit_sizes=args.sizes,
                min_size=args.min_size,
                max_size=args.max_size,
                size_step=args.size_step,
            )
        except Exception as exc:
            print(f"[ERR] Invalid generated size settings: {exc}", file=sys.stderr)
            return 2

        level_dir = (
            args.generated_level_dir.resolve()
            if args.generated_level_dir
            else (run_dir / "generated-levels")
        )
        try:
            levels = write_generated_levels(
                out_dir=level_dir,
                sizes=sizes,
                required_gems=args.required_gems,
                max_time_min=args.max_time_min,
                max_time_scale=args.max_time_scale,
            )
        except Exception as exc:
            print(f"[ERR] Failed to generate levels: {exc}", file=sys.stderr)
            return 2

        print(f"[INFO] Generated levels dir: {level_dir}")

    planner_args = build_planner_args(args.base_args, args.heuristic, args.search)
    total_runs = len(domains) * len(levels)
    rows: List[GrowthRow] = []
    if args.jobs < 1:
        print("[ERR] --jobs must be >= 1.", file=sys.stderr)
        return 2
    workers = min(args.jobs, len(domains)) if domains else 1
    if args.stream and workers > 1:
        print("[WARN] --stream with --jobs > 1 can interleave planner logs.")

    print(f"[INFO] Domains: {len(domains)}")
    print(f"[INFO] Levels: {len(levels)}")
    print(f"[INFO] Total runs: {total_runs}")
    print(f"[INFO] Workers: {workers}")
    print(f"[INFO] Run dir: {run_dir}")
    print(f"[INFO] Plans dir: {plans_dir}")
    print(f"[INFO] Output CSV: {output_csv}")
    print(f"[INFO] Output plot: {output_plot}")
    print(f"[INFO] Plus planner args: {planner_args}")
    print(f"[INFO] Classic planner: {args.classic_planner}")

    progress_counter = [0]
    progress_lock = threading.Lock()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [
            ex.submit(
                run_domain,
                domain,
                levels=levels,
                total_runs=total_runs,
                progress_counter=progress_counter,
                progress_lock=progress_lock,
                args=args,
                planner_args=planner_args,
                run_dir=run_dir,
                plans_dir=plans_dir,
            )
            for domain in domains
        ]
        for fut in concurrent.futures.as_completed(futures):
            rows.extend(fut.result())

    rows.sort(key=lambda r: (r.domain, r.cells, r.rows, r.cols, r.level))

    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    plot_generated = generate_growth_plot(
        csv_path=output_csv,
        out_path=output_plot,
        title="Level Growth Metrics",
    )

    status_counts = {}
    for row in rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
    status_summary = ", ".join(f"{k}={v}" for k, v in sorted(status_counts.items()))
    print(f"[OK] Run dir: {run_dir}")
    print(f"[OK] Plans dir: {plans_dir}")
    print(f"[OK] Wrote CSV: {output_csv}")
    print(f"[OK] Wrote plot: {output_plot if plot_generated else 'not generated'}")
    print(f"[OK] Status counts: {status_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
