#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from bench_config_matrix import (
    BENCHMARK_DIR,
    LevelInfo,
    RunTask,
    append_csv_rows,
    build_pairings,
    discover_domains,
    format_eta_hms,
    generate_plots,
    load_json_config,
    parse_level_size,
    parse_planner_settings,
    resolve_path,
    run_single_task,
    status_summary,
    write_csv,
)


def default_run_dir(stamp: str) -> Path:
    return BENCHMARK_DIR / "results" / f"levels-matrix_{stamp}"


def collect_folder_levels(
    *,
    config: Dict[str, Any],
    config_dir: Path,
) -> Tuple[List[LevelInfo], Path, str]:
    raw_levels_dir = config.get("levels_dir")
    if raw_levels_dir is None or not str(raw_levels_dir).strip():
        raise ValueError("config.levels_dir must be a folder of input level files.")

    levels_dir = resolve_path(str(raw_levels_dir), config_dir=config_dir)
    if not levels_dir.exists():
        raise FileNotFoundError(f"Levels directory not found: {levels_dir}")
    if not levels_dir.is_dir():
        raise ValueError(f"config.levels_dir must point to a directory, got: {levels_dir}")

    level_glob = str(config.get("level_glob", "*.txt") or "*.txt").strip()
    if not level_glob:
        raise ValueError("config.level_glob must not be empty.")

    matches = sorted(path.resolve() for path in levels_dir.glob(level_glob) if path.is_file())
    if not matches:
        raise FileNotFoundError(f"No levels matched {level_glob!r} in {levels_dir}")

    levels: List[LevelInfo] = []
    seen = set()
    for path in matches:
        if path in seen:
            continue
        seen.add(path)
        rows, cols = parse_level_size(path)
        levels.append(
            LevelInfo(
                path=path,
                rows=rows,
                cols=cols,
                cells=rows * cols,
                source="custom",
            )
        )
    return levels, levels_dir, level_glob


def build_tasks(pairings: Sequence[Any], levels: Sequence[LevelInfo]) -> List[RunTask]:
    tasks: List[RunTask] = []
    run_id = 0
    for pairing in pairings:
        for level in levels:
            run_id += 1
            tasks.append(
                RunTask(
                    run_id=run_id,
                    pairing_id=pairing.id,
                    setting=pairing.setting,
                    domain=pairing.domain,
                    level=level,
                    phase="custom",
                )
            )
    return tasks


def summarize_status_counts(rows: Sequence[Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Run planner settings from a small JSON config over every level in a folder, "
            "write a config-matrix-compatible CSV, and generate plots when the run finishes."
        )
    )
    ap.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to benchmark JSON config.",
    )
    ap.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help=(
            "Output run directory. Default: tools/benchmarking/results/"
            "levels-matrix_<timestamp>/"
        ),
    )
    ap.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="CSV output path. Default: <results-dir>/benchmark_matrix.csv",
    )
    ap.add_argument(
        "--jobs",
        type=int,
        default=None,
        help="Override max parallel runs. Always capped to 12.",
    )
    ap.add_argument(
        "--plots-dir",
        type=Path,
        default=None,
        help="Directory to write generated plots (default: <results-dir>/plots).",
    )
    ap.add_argument(
        "--skip-plots",
        action="store_true",
        help="Skip post-run plot generation.",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and execute the full run matrix without invoking planners.",
    )
    args = ap.parse_args()

    config_path = args.config.resolve()
    if not config_path.exists():
        print(f"[ERR] Config not found: {config_path}", file=sys.stderr)
        return 2

    try:
        cfg = load_json_config(config_path)
    except Exception as exc:
        print(f"[ERR] Failed to load config: {exc}", file=sys.stderr)
        return 2

    config_dir = config_path.parent
    default_timeout = int(cfg.get("timeout_sec", 120))
    if default_timeout <= 0:
        print("[ERR] timeout_sec must be > 0.", file=sys.stderr)
        return 2
    default_stream = bool(cfg.get("stream", False))

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = args.results_dir.resolve() if args.results_dir else default_run_dir(stamp)
    run_dir.mkdir(parents=True, exist_ok=True)
    output_csv = args.output_csv.resolve() if args.output_csv else (run_dir / "benchmark_matrix.csv")
    plots_dir = args.plots_dir.resolve() if args.plots_dir else (run_dir / "plots")

    try:
        settings = parse_planner_settings(
            cfg.get("planner_settings"),
            config_dir=config_dir,
            default_timeout=default_timeout,
            default_stream=default_stream,
        )
        domains = discover_domains(config=cfg, config_dir=config_dir)
        levels, levels_dir, level_glob = collect_folder_levels(config=cfg, config_dir=config_dir)
        pairings = build_pairings(settings, domains)
    except Exception as exc:
        print(f"[ERR] Config validation failed: {exc}", file=sys.stderr)
        return 2

    if not pairings:
        print("[ERR] No compatible planner/domain pairings found.", file=sys.stderr)
        return 2

    max_parallel_cfg = int(cfg.get("max_parallel_runs", 12))
    if max_parallel_cfg <= 0:
        print("[ERR] max_parallel_runs must be > 0.", file=sys.stderr)
        return 2
    max_parallel = min(max_parallel_cfg, 12)
    if args.jobs is not None:
        if args.jobs <= 0:
            print("[ERR] --jobs must be > 0.", file=sys.stderr)
            return 2
        max_parallel = min(args.jobs, 12)

    if any(setting.stream for setting in settings) and max_parallel > 1 and not args.dry_run:
        print("[WARN] stream=true with parallel runs can interleave logs.")

    tasks = build_tasks(pairings, levels)
    if not tasks:
        print("[ERR] No runs to execute.", file=sys.stderr)
        return 2

    n_classic = sum(domain.kind == "classic" for domain in domains)
    n_fa = sum(domain.kind == "fa" for domain in domains)
    n_plus = sum(domain.kind == "plus" for domain in domains)
    print(f"[INFO] Config: {config_path}")
    print(f"[INFO] Levels directory: {levels_dir}")
    print(f"[INFO] Level glob: {level_glob}")
    print(f"[INFO] Levels matched: {len(levels)}")
    print(f"[INFO] Planner settings: {len(settings)}")
    print(f"[INFO] Domains: {len(domains)} (classic={n_classic}, fa={n_fa}, plus={n_plus})")
    print(f"[INFO] Pairings: {len(pairings)}")
    print(f"[INFO] Total runs: {len(tasks)}")
    print(f"[INFO] Max parallel runs: {max_parallel} (QoS: equal thread priority)")

    (run_dir / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    run_meta: Dict[str, Any] = {
        "config_path": str(config_path),
        "results_dir": str(run_dir),
        "output_csv": str(output_csv),
        "plots_dir": str(plots_dir),
        "levels_dir": str(levels_dir),
        "level_glob": level_glob,
        "levels_count": len(levels),
        "planner_settings": [setting.name for setting in settings],
        "domains": [str(domain.path) for domain in domains],
        "pairings": [pairing.id for pairing in pairings],
        "total_runs": len(tasks),
        "max_parallel_runs": max_parallel,
        "dry_run": bool(args.dry_run),
        "skip_plots": bool(args.skip_plots),
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    # Ensure a CSV exists from the beginning so partial results survive interruptions.
    write_csv(output_csv, [])

    rows = []
    started_at = time.perf_counter()
    executor_failed = False
    completed_futures = 0
    submitted_tasks = 0
    drain_requested = False
    hard_stop_requested = False
    interrupted = False
    signal_hits = 0

    old_sigint = signal.getsignal(signal.SIGINT)
    old_sigterm = signal.getsignal(signal.SIGTERM)

    def handle_stop(sig: int, _frame: Any) -> None:
        nonlocal drain_requested, hard_stop_requested, interrupted, signal_hits
        signal_hits += 1
        interrupted = True
        name = signal.Signals(sig).name
        if signal_hits == 1:
            drain_requested = True
            print(
                f"[WARN] Received {name}. No new tasks will start; "
                "running work will drain before exit."
            )
            return
        if signal_hits == 2:
            drain_requested = True
            hard_stop_requested = True
            print(
                f"[WARN] Received {name} again. Scheduler is locked; "
                "waiting only for already-running work to finish."
            )
            return
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    next_task_index = 0

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as ex:
            future_to_task: Dict[concurrent.futures.Future[Any], RunTask] = {}

            while True:
                while (
                    not hard_stop_requested
                    and not drain_requested
                    and len(future_to_task) < max_parallel
                    and next_task_index < len(tasks)
                ):
                    task = tasks[next_task_index]
                    next_task_index += 1
                    submitted_tasks += 1
                    future = ex.submit(run_single_task, task, run_dir=run_dir, dry_run=args.dry_run)
                    future_to_task[future] = task

                if not future_to_task:
                    break

                try:
                    done, _ = concurrent.futures.wait(
                        future_to_task.keys(),
                        timeout=0.5,
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )
                except KeyboardInterrupt:
                    interrupted = True
                    drain_requested = True
                    hard_stop_requested = True
                    print(
                        "[WARN] Additional interrupt received. No new tasks will start; "
                        "waiting for running tasks to finish."
                    )
                    continue

                if not done:
                    continue

                for future in done:
                    task = future_to_task.pop(future)
                    completed_futures += 1
                    try:
                        result = future.result()
                    except Exception as exc:
                        executor_failed = True
                        print(
                            "[ERR] Unhandled worker failure for "
                            f"{task.setting.name} / {task.domain.path.name} / {task.level.path.name}: {exc}",
                            file=sys.stderr,
                        )
                        continue

                    rows.append(result.row)
                    append_csv_rows(output_csv, [result.row])

                    elapsed = time.perf_counter() - started_at
                    avg_per_run = elapsed / completed_futures if completed_futures > 0 else 0.0
                    eta = format_eta_hms(avg_per_run * max(0, len(tasks) - completed_futures))
                    remaining_label = (
                        "draining"
                        if drain_requested or hard_stop_requested
                        else f"queued-left={len(tasks) - next_task_index}"
                    )
                    print(
                        f"[{completed_futures}/{len(tasks)}] "
                        f"{task.setting.name} / {task.domain.path.name} / {task.level.path.name} "
                        f"-> {result.row.status} | {result.row.measured_total_sec:.2f}s | "
                        f"{remaining_label} | ETA {eta}"
                    )
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)

    rows.sort(
        key=lambda row: (
            row.planner_setting,
            Path(row.domain).name,
            row.cells,
            row.rows,
            row.cols,
            Path(row.level).name,
            row.run_id,
        )
    )
    write_csv(output_csv, rows)

    plots_generated = 0
    if not args.skip_plots and rows:
        plots_generated = generate_plots(output_csv, plots_dir)

    run_meta["elapsed_sec"] = round(time.perf_counter() - started_at, 6)
    run_meta["submitted_runs"] = submitted_tasks
    run_meta["completed_futures"] = completed_futures
    run_meta["abandoned_runs"] = max(0, len(tasks) - submitted_tasks)
    run_meta["rows_written"] = len(rows)
    run_meta["status_counts"] = summarize_status_counts(rows)
    run_meta["plots_generated"] = plots_generated
    run_meta["interrupted"] = interrupted
    run_meta["drain_requested"] = drain_requested
    run_meta["hard_stop_requested"] = hard_stop_requested
    (run_dir / "run_metadata.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    print(f"[OK] Wrote CSV: {output_csv}")
    print(f"[OK] Rows: {len(rows)}")
    print(f"[OK] Status counts: {status_summary(rows)}")
    print(f"[OK] Plots generated: {plots_generated}")
    print(f"[OK] Artifacts: {run_dir}")

    if interrupted:
        if drain_requested and not hard_stop_requested:
            print("[WARN] Run interrupted gracefully. No new tasks were started and running work drained before exit.")
        else:
            print("[WARN] Run interrupted. Partial results were preserved in CSV during execution.")
        return 130
    if executor_failed:
        print("[WARN] Some runs failed before a result row could be written.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
