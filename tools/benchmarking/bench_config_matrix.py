#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import json
import os
import random
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

TOOLS_DIR = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
PLOT_CONFIG_MATRIX_SCRIPT = BENCHMARK_DIR / "ploters" / "plot_config_matrix.py"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

PLUS_RUNNER_DIR = REPO_ROOT / "planners" / "pddl-plus"
if str(PLUS_RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(PLUS_RUNNER_DIR))

from plan import PlanResult, solve_with_fd, solve_with_ff, write_direction_plan  # type: ignore
from plan_lifted import solve_with_lifted  # type: ignore
from pddl_plus_runner import PlusPlanResult, TimedAction, solve as solve_plus  # type: ignore


def repo_root() -> Path:
    return REPO_ROOT


def safe_tag(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"[^a-z0-9_+\-]+", "_", lowered)
    return lowered.strip("_") or "x"


def ensure_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def write_classic_plan_file(path: Path, actions: Sequence[Tuple[str, Sequence[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    for name, args in actions:
        if args:
            lines.append(f"({name} {' '.join(args)})")
        else:
            lines.append(f"({name})")
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_plus_plan_file(path: Path, actions: Sequence[TimedAction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    for a in actions:
        if a.args:
            lines.append(f"({a.name} {' '.join(a.args)})")
        else:
            lines.append(f"({a.name})")
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_plus_timed_plan_file(path: Path, actions: Sequence[TimedAction]) -> None:
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


def parse_numeric(token: str) -> Optional[float]:
    tok = token.strip().replace(",", "")
    if not tok:
        return None
    try:
        return float(tok)
    except Exception:
        return None


def parse_first_float(text: str, pattern: str) -> Optional[float]:
    m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    return parse_numeric(m.group(1))


def parse_last_float(text: str, pattern: str) -> Optional[float]:
    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    if not matches:
        return None
    last = matches[-1]
    if isinstance(last, tuple):
        last = last[0]
    return parse_numeric(str(last))


def parse_first_int(text: str, pattern: str) -> Optional[int]:
    val = parse_first_float(text, pattern)
    if val is None:
        return None
    try:
        return int(round(val))
    except Exception:
        return None


def parse_last_int(text: str, pattern: str) -> Optional[int]:
    val = parse_last_float(text, pattern)
    if val is None:
        return None
    try:
        return int(round(val))
    except Exception:
        return None


def parse_first_ms_as_sec(text: str, pattern: str) -> Optional[float]:
    val = parse_first_float(text, pattern)
    if val is None:
        return None
    return val / 1000.0


def parse_last_ms_as_sec(text: str, pattern: str) -> Optional[float]:
    val = parse_last_float(text, pattern)
    if val is None:
        return None
    return val / 1000.0


def is_failure_status(status: str) -> bool:
    s = (status or "").strip().lower()
    return s in {"timeout", "error"}


def is_success_status(status: str) -> bool:
    return (status or "").strip().lower() == "solved"


def format_eta_hms(total_seconds: float) -> str:
    secs = max(0, int(round(total_seconds)))
    hours, rem = divmod(secs, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def resolve_path(raw: str, *, config_dir: Path) -> Path:
    p = Path(raw)
    if p.is_absolute():
        return p.resolve()
    from_config_dir = (config_dir / p).resolve()
    if from_config_dir.exists():
        return from_config_dir
    return (repo_root() / p).resolve()


def parse_size_token(token: str) -> Tuple[int, int]:
    m = re.fullmatch(r"\s*(\d+)\s*[xX]\s*(\d+)\s*", token)
    if not m:
        raise ValueError(f"Invalid size token '{token}'. Use ROWSxCOLS.")
    rows = int(m.group(1))
    cols = int(m.group(2))
    if rows <= 0 or cols <= 0:
        raise ValueError(f"Invalid size {rows}x{cols}; must be > 0.")
    if rows * cols < 4:
        raise ValueError(f"Invalid size {rows}x{cols}; need at least 4 cells.")
    return rows, cols


def parse_size_values(values: Sequence[str]) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    for raw in values:
        for part in raw.split(","):
            token = part.strip()
            if not token:
                continue
            out.append(parse_size_token(token))
    deduped = sorted(set(out), key=lambda x: (x[0] * x[1], x[0], x[1]))
    return deduped


def parse_growth_size_threshold(raw: Any) -> Optional[int]:
    if raw is None:
        return None
    if isinstance(raw, bool):
        raise ValueError("growth size threshold must be int or ROWSxCOLS, not bool.")
    if isinstance(raw, (int, float)):
        size = int(raw)
    else:
        token = str(raw).strip()
        if not token:
            return None
        if re.fullmatch(r"\d+\s*[xX]\s*\d+", token):
            rows, cols = parse_size_token(token)
            size = min(rows, cols)
        else:
            size = int(token)
    if size < 0:
        raise ValueError("growth size threshold must be >= 0.")
    return size


@dataclass(frozen=True)
class PlannerSetting:
    name: str
    family: str  # classic | fa | plus
    planner: str
    timeout_sec: int
    stream: bool
    planner_args: str
    java_opts: str
    cmd_template: Optional[str]
    enhsp_jar: Optional[Path]
    optic_bin: Optional[Path]
    fd_optimal: bool
    fd_keep_searching: bool
    lifted_search: str
    lifted_evaluator: str
    lifted_generator: str
    lifted_time_limit_sec: int
    lifted_seed: int
    lifted_build: bool
    lifted_debug: bool
    lifted_cxx_compiler: str
    lifted_unit_cost: bool
    lifted_only_effects_novelty_check: bool
    lifted_novelty_early_stop: bool
    problem_gen: Optional[Path]
    domain_include: Tuple[str, ...]
    domain_exclude: Tuple[str, ...]


@dataclass(frozen=True)
class DomainInfo:
    path: Path
    kind: str  # classic | fa | plus
    problem_gen: Optional[Path]


@dataclass(frozen=True)
class LevelInfo:
    path: Path
    rows: int
    cols: int
    cells: int
    source: str  # custom | random-repeat | growth


@dataclass(frozen=True)
class Pairing:
    id: str
    setting: PlannerSetting
    domain: DomainInfo


@dataclass
class PairState:
    pairing: Pairing
    phase: str
    custom_index: int
    random_repeat_index: int
    growth_index: int
    custom_fail_streak: int
    growth_max_nonfailure_size: int
    pending_excluded_runs: int
    in_flight: bool
    done: bool


@dataclass(frozen=True)
class RunTask:
    run_id: int
    pairing_id: str
    setting: PlannerSetting
    domain: DomainInfo
    level: LevelInfo
    phase: str
    repeat_index: int = 0


@dataclass
class TaskResult:
    row: "BenchRow"
    task: RunTask


@dataclass
class BenchRow:
    run_id: int
    pairing_id: str
    planner_setting: str
    planner_family: str
    planner: str
    planner_args: str
    domain: str
    domain_kind: str
    level: str
    level_source: str
    phase: str
    repeat_index: int
    rows: int
    cols: int
    cells: int
    status: str
    timeout_sec: int
    measured_total_sec: float
    measured_problem_gen_sec: float
    measured_solver_sec: float
    wrapper_time_sec: Optional[float]
    domain_parsed: Optional[int]
    problem_parsed: Optional[int]
    reported_grounding_msec: Optional[float]
    reported_grounding_sec: Optional[float]
    reported_h1_setup_msec: Optional[float]
    reported_h1_setup_sec: Optional[float]
    initial_heuristic_h: Optional[float]
    reported_heuristic_msec: Optional[float]
    reported_heuristic_sec: Optional[float]
    reported_search_msec: Optional[float]
    reported_search_sec: Optional[float]
    reported_total_sec: Optional[float]
    reported_planning_msec: Optional[float]
    reported_planning_sec: Optional[float]
    reported_elapsed_plan_sec: Optional[float]
    plan_length_reported: Optional[int]
    plan_action_count: int
    plan_cost_reported: Optional[float]
    action_set_size: Optional[int]
    facts_count: Optional[int]
    x_count: Optional[int]
    problem_count: Optional[int]
    predicate_count: Optional[int]
    event_count: Optional[int]
    translator_operators: Optional[int]
    expanded_nodes: Optional[int]
    reopened_nodes: Optional[int]
    evaluated_states: Optional[int]
    generated_nodes: Optional[int]
    dead_end_states: Optional[int]
    duplicate_states: Optional[int]
    registered_states: Optional[int]
    nodes_per_second_reported: Optional[float]
    nodes_per_second_derived: Optional[float]
    nodes_per_second: Optional[float]
    returncode: Optional[int]
    command: str
    stdout_file: str
    stderr_file: str
    compiled_problem_file: str
    plan_file: str
    timed_plan_file: str
    error_message: str


CSV_FIELDS = list(BenchRow.__annotations__.keys())


def default_run_dir(stamp: str) -> Path:
    return BENCHMARK_DIR / "results" / f"config-matrix_{stamp}"


def load_json_config(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Top-level config must be a JSON object.")
    return data


def infer_family(planner: str) -> str:
    p = planner.strip().lower()
    if p in {"fd", "ff", "lifted", "powerlifted"}:
        return "classic"
    if p in {"auto", "enhsp", "optic", "cmd"}:
        return "plus"
    raise ValueError(
        f"Unsupported planner '{planner}'. Supported: fd, ff, lifted, auto, enhsp, optic, cmd."
    )


def parse_planner_settings(
    raw_list: Any,
    *,
    config_dir: Path,
    default_timeout: int,
    default_stream: bool,
) -> List[PlannerSetting]:
    if not isinstance(raw_list, list) or not raw_list:
        raise ValueError("config.planner_settings must be a non-empty list.")

    settings: List[PlannerSetting] = []
    for idx, entry in enumerate(raw_list):
        if not isinstance(entry, dict):
            raise ValueError(f"planner_settings[{idx}] must be an object.")

        name = str(entry.get("name") or f"setting_{idx+1}")
        planner = str(entry.get("planner") or "").strip().lower()
        if not planner:
            raise ValueError(f"planner_settings[{idx}] is missing 'planner'.")
        if planner == "powerlifted":
            planner = "lifted"

        family = str(entry.get("family") or "").strip().lower() or infer_family(planner)
        if family not in {"classic", "fa", "plus"}:
            raise ValueError(
                f"planner_settings[{idx}] family must be 'classic', 'fa', or 'plus', got '{family}'."
            )

        if family in {"classic", "fa"} and planner not in {"fd", "ff", "lifted"}:
            raise ValueError(
                f"planner_settings[{idx}] planner '{planner}' is not valid for {family} family."
            )
        if family == "plus" and planner not in {"auto", "enhsp", "optic", "cmd"}:
            raise ValueError(
                f"planner_settings[{idx}] planner '{planner}' is not valid for plus family."
            )

        timeout_sec = int(entry.get("timeout_sec", default_timeout))
        if timeout_sec <= 0:
            raise ValueError(f"planner_settings[{idx}] timeout_sec must be > 0.")

        stream = bool(entry.get("stream", default_stream))
        planner_args = str(entry.get("planner_args", "") or "")
        java_opts = str(entry.get("java_opts", "") or "")
        cmd_template = entry.get("cmd_template")
        if cmd_template is not None:
            cmd_template = str(cmd_template)

        enhsp_jar = None
        if entry.get("enhsp_jar"):
            enhsp_jar = resolve_path(str(entry["enhsp_jar"]), config_dir=config_dir)

        optic_bin = None
        if entry.get("optic_bin"):
            optic_bin = resolve_path(str(entry["optic_bin"]), config_dir=config_dir)

        problem_gen = None
        if entry.get("problem_gen"):
            problem_gen = resolve_path(str(entry["problem_gen"]), config_dir=config_dir)

        lifted_time_limit_sec = int(entry.get("lifted_time_limit_sec", timeout_sec))
        if lifted_time_limit_sec <= 0:
            raise ValueError(f"planner_settings[{idx}] lifted_time_limit_sec must be > 0.")
        lifted_seed = int(entry.get("lifted_seed", 1))
        lifted_cxx_compiler = str(entry.get("lifted_cxx_compiler", "default") or "default")

        domain_include = tuple(str(x) for x in (entry.get("domain_include") or []))
        domain_exclude = tuple(str(x) for x in (entry.get("domain_exclude") or []))

        setting = PlannerSetting(
            name=name,
            family=family,
            planner=planner,
            timeout_sec=timeout_sec,
            stream=stream,
            planner_args=planner_args,
            java_opts=java_opts,
            cmd_template=cmd_template,
            enhsp_jar=enhsp_jar,
            optic_bin=optic_bin,
            fd_optimal=bool(entry.get("fd_optimal", False)),
            fd_keep_searching=bool(entry.get("fd_keep_searching", False)),
            lifted_search=str(entry.get("lifted_search", "alt-bfws1") or "alt-bfws1"),
            lifted_evaluator=str(entry.get("lifted_evaluator", "ff") or "ff"),
            lifted_generator=str(entry.get("lifted_generator", "yannakakis") or "yannakakis"),
            lifted_time_limit_sec=lifted_time_limit_sec,
            lifted_seed=lifted_seed,
            lifted_build=bool(entry.get("lifted_build", False)),
            lifted_debug=bool(entry.get("lifted_debug", False)),
            lifted_cxx_compiler=lifted_cxx_compiler,
            lifted_unit_cost=bool(entry.get("lifted_unit_cost", False)),
            lifted_only_effects_novelty_check=bool(entry.get("lifted_only_effects_novelty_check", False)),
            lifted_novelty_early_stop=bool(entry.get("lifted_novelty_early_stop", False)),
            problem_gen=problem_gen,
            domain_include=domain_include,
            domain_exclude=domain_exclude,
        )
        settings.append(setting)

    return settings


def match_any(path: Path, patterns: Sequence[str]) -> bool:
    if not patterns:
        return False
    for pat in patterns:
        if path.match(pat):
            return True
    return False


def domain_is_plus(path: Path) -> bool:
    # Treat explicit "domain_plus_*" variants as plus-family domains,
    # even for action-only formulations without :process/:event sections.
    if re.search(r"(?:^|_)plus(?:_|$)", path.stem, flags=re.IGNORECASE):
        return True
    text = path.read_text(encoding="utf-8", errors="replace")
    return bool(
        re.search(r"\(:\s*process\b", text, flags=re.IGNORECASE)
        or re.search(r"\(:\s*event\b", text, flags=re.IGNORECASE)
        or re.search(r":processes\b", text, flags=re.IGNORECASE)
        or re.search(r":events\b", text, flags=re.IGNORECASE)
    )


def domain_is_fa(path: Path) -> bool:
    # FA test domains are explicitly prefixed like domain_FA_*.pddl.
    stem = path.stem
    return bool(re.search(r"(?:^|_)fa(?:_|$)", stem, flags=re.IGNORECASE))


def discover_domains(
    *,
    config: Dict[str, Any],
    config_dir: Path,
) -> List[DomainInfo]:
    if "domains" in config:
        raw = config["domains"]
        if not isinstance(raw, list) or not raw:
            raise ValueError("config.domains must be a non-empty list when provided.")
        paths = [resolve_path(str(x), config_dir=config_dir) for x in raw]
    else:
        glob_pattern = str(config.get("domains_glob") or "pddl/test_domains/domain*.pddl")
        pattern_path = Path(glob_pattern)
        if pattern_path.is_absolute():
            paths = sorted(pattern_path.parent.glob(pattern_path.name))
        else:
            paths = sorted(repo_root().glob(glob_pattern))

    domains: List[DomainInfo] = []
    for p in paths:
        p = p.resolve()
        if not p.exists():
            raise FileNotFoundError(f"Domain not found: {p}")
        if p.suffix.lower() != ".pddl":
            continue
        if domain_is_plus(p):
            kind = "plus"
        elif domain_is_fa(p):
            kind = "fa"
        else:
            kind = "classic"
        domain_gen = p.parent / f"problem_gen_{p.stem}.py"
        info = DomainInfo(
            path=p,
            kind=kind,
            problem_gen=domain_gen if domain_gen.exists() else None,
        )
        domains.append(info)
    if not domains:
        raise ValueError("No domain files discovered.")
    return domains


def parse_level_size(path: Path) -> Tuple[int, int]:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    parts = [p.strip() for p in text.split("|") if p.strip()]
    if len(parts) < 2:
        raise ValueError(f"Could not parse rows/cols from level: {path}")
    rows = int(parts[0])
    cols = int(parts[1])
    return rows, cols


def collect_custom_levels(
    *,
    config: Dict[str, Any],
    config_dir: Path,
) -> List[LevelInfo]:
    raw = config.get("custom_levels") or []
    if not isinstance(raw, list):
        raise ValueError("config.custom_levels must be a list.")

    levels: List[LevelInfo] = []
    seen = set()
    for entry in raw:
        p = resolve_path(str(entry), config_dir=config_dir)
        if not p.exists():
            raise FileNotFoundError(f"Custom level not found: {p}")
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        rows, cols = parse_level_size(rp)
        levels.append(LevelInfo(path=rp, rows=rows, cols=cols, cells=rows * cols, source="custom"))
    return levels


def generate_level_text(
    rows: int,
    cols: int,
    required_gems: int,
    max_time_min: int,
    max_time_scale: int,
) -> str:
    AGENT = 0
    EMPTY = 1
    DIRT = 2
    STONE = 3
    GEM = 5

    grid = [[DIRT for _ in range(cols)] for _ in range(rows)]
    agent_pos = (0, 0)

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
                gem_pos = (r, c)
    if gem_pos is None or best_dist <= 1:
        raise ValueError(f"Could not place non-adjacent gem for {rows}x{cols}")

    grid[agent_pos[0]][agent_pos[1]] = AGENT
    grid[gem_pos[0]][gem_pos[1]] = GEM

    # Deterministic but spatially varied placement for synthetic growth maps.
    layout_seed = (
        rows * 73856093
        ^ cols * 19349663
        ^ required_gems * 83492791
        ^ max_time_scale * 2654435761
    )
    layout_rng = random.Random(layout_seed)

    stone_pool = [
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if (r, c) not in {agent_pos, gem_pos}
    ]
    if not stone_pool:
        raise ValueError(f"Could not place stones for {rows}x{cols}")
    desired_stones = max(2, min((rows * cols) // 40 + 1, 8))
    stones_to_place = min(desired_stones, len(stone_pool))
    stone_positions = layout_rng.sample(stone_pool, stones_to_place)
    for r, c in stone_positions:
        grid[r][c] = STONE

    blocked = {agent_pos, gem_pos}
    blocked.update(stone_positions)

    # Increase and spread "air" (empty cells) across the full map, not only
    # near the start corner.
    air_pool = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in blocked]
    if air_pool:
        desired_air = min(len(air_pool), max(3, min(len(air_pool) // 5, 50)))
        for r, c in layout_rng.sample(air_pool, desired_air):
            grid[r][c] = EMPTY

    max_time = max(max_time_min, rows * cols * max_time_scale)
    header = f"{rows}|{cols}|{max_time}|{required_gems}|"
    body = "\n".join("|".join(f"{cell:02d}" for cell in row) + "|" for row in grid)
    return f"{header}\n{body}\n"


def generate_random_level_text(
    *,
    rows: int,
    cols: int,
    required_gems: int,
    max_time_min: int,
    max_time_scale: int,
    rng: random.Random,
    stone_count: int,
) -> str:
    AGENT = 0
    EMPTY = 1
    DIRT = 2
    STONE = 3
    GEM = 5

    grid = [[DIRT for _ in range(cols)] for _ in range(rows)]
    agent_pos = (0, 0)

    all_cells = [(r, c) for r in range(rows) for c in range(cols) if (r, c) != agent_pos]
    if not all_cells:
        raise ValueError(f"Could not build random level for {rows}x{cols}")

    # Prefer non-adjacent gem placement to avoid trivial maps.
    non_adjacent_cells = [
        (r, c) for (r, c) in all_cells if abs(r - agent_pos[0]) + abs(c - agent_pos[1]) > 1
    ]
    gem_pool = non_adjacent_cells if non_adjacent_cells else all_cells

    # Bias gems toward higher rows while still allowing full-map variety.
    # Higher rows receive larger weight.
    gem_weights = [float((rows - r) ** 2) for (r, _c) in gem_pool]
    gem_pos = rng.choices(gem_pool, weights=gem_weights, k=1)[0]

    stone_pool = [(r, c) for (r, c) in all_cells if (r, c) != gem_pos]
    if not stone_pool:
        raise ValueError(f"Could not place stones for random level {rows}x{cols}")
    stones_to_place = max(1, min(stone_count, len(stone_pool)))
    for r, c in rng.sample(stone_pool, stones_to_place):
        grid[r][c] = STONE

    grid[agent_pos[0]][agent_pos[1]] = AGENT
    grid[gem_pos[0]][gem_pos[1]] = GEM

    occupied = {agent_pos, gem_pos}
    occupied.update((r, c) for r in range(rows) for c in range(cols) if grid[r][c] == STONE)
    air_pool = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in occupied]
    if air_pool:
        desired_air = min(len(air_pool), max(2, min(len(air_pool) // 3, 20)))
        for r, c in rng.sample(air_pool, desired_air):
            grid[r][c] = EMPTY

    max_time = max(max_time_min, rows * cols * max_time_scale)
    header = f"{rows}|{cols}|{max_time}|{required_gems}|"
    body = "\n".join("|".join(f"{cell:02d}" for cell in row) + "|" for row in grid)
    return f"{header}\n{body}\n"


def collect_random_repeat_levels(
    *,
    config: Dict[str, Any],
    run_dir: Path,
    config_seed: Any,
) -> List[LevelInfo]:
    random_repeats = config.get("random_repeats") or {}
    if not isinstance(random_repeats, dict):
        raise ValueError("config.random_repeats must be an object when provided.")

    enabled = bool(random_repeats.get("enabled", False))
    if not enabled:
        return []

    required_gems = int(random_repeats.get("required_gems", 1))
    max_time_min = int(random_repeats.get("max_time_min", 200))
    max_time_scale = int(random_repeats.get("max_time_scale", 8))

    stone_counts: List[int]
    stone_counts_raw = random_repeats.get("stone_counts")
    if stone_counts_raw is not None:
        if not isinstance(stone_counts_raw, list) or not stone_counts_raw:
            raise ValueError("random_repeats.stone_counts must be a non-empty list when provided.")
        stone_counts = [int(x) for x in stone_counts_raw]
        if any(x <= 0 for x in stone_counts):
            raise ValueError("random_repeats.stone_counts values must all be >= 1.")
    else:
        stone_count = int(random_repeats.get("stone_count", 1))
        if stone_count <= 0:
            raise ValueError("random_repeats.stone_count must be >= 1.")
        stone_counts = [stone_count]

    stone_count_mode = str(random_repeats.get("stone_count_mode", "cycle")).strip().lower()
    if stone_count_mode not in {"cycle", "random"}:
        raise ValueError("random_repeats.stone_count_mode must be 'cycle' or 'random'.")

    repeats_per_size = int(random_repeats.get("repeats_per_size", random_repeats.get("repeats", 0)))
    if repeats_per_size <= 0:
        raise ValueError("random_repeats.repeats_per_size must be >= 1 when enabled.")

    sizes: List[Tuple[int, int]]
    if random_repeats.get("sizes"):
        raw_sizes = random_repeats["sizes"]
        if not isinstance(raw_sizes, list) or not raw_sizes:
            raise ValueError("random_repeats.sizes must be a non-empty list when provided.")
        sizes = parse_size_values([str(x) for x in raw_sizes])
    elif random_repeats.get("size"):
        sizes = [parse_size_token(str(random_repeats["size"]))]
    elif random_repeats.get("rows") and random_repeats.get("cols"):
        rows = int(random_repeats["rows"])
        cols = int(random_repeats["cols"])
        sizes = [parse_size_token(f"{rows}x{cols}")]
    else:
        raise ValueError(
            "random_repeats requires one of: 'sizes', 'size', or both 'rows' and 'cols'."
        )

    section_seed = random_repeats.get("seed", config_seed)
    rng = random.Random(section_seed)

    out_dir = run_dir / "random-repeat-levels"
    out_dir.mkdir(parents=True, exist_ok=True)
    levels: List[LevelInfo] = []

    for rows, cols in sorted(set(sizes), key=lambda x: (x[0] * x[1], x[0], x[1])):
        for rep in range(1, repeats_per_size + 1):
            if stone_count_mode == "random":
                chosen_stone_count = rng.choice(stone_counts)
            else:
                chosen_stone_count = stone_counts[(rep - 1) % len(stone_counts)]

            path = out_dir / (
                f"random_{rows:03d}x{cols:03d}_r{rep:03d}_s{chosen_stone_count:03d}.txt"
            )
            txt = generate_random_level_text(
                rows=rows,
                cols=cols,
                required_gems=required_gems,
                max_time_min=max_time_min,
                max_time_scale=max_time_scale,
                rng=rng,
                stone_count=chosen_stone_count,
            )
            path.write_text(txt, encoding="utf-8")
            levels.append(
                LevelInfo(path=path, rows=rows, cols=cols, cells=rows * cols, source="random-repeat")
            )

    return levels


def collect_growth_levels(
    *,
    config: Dict[str, Any],
    run_dir: Path,
) -> List[LevelInfo]:
    growth = config.get("growth") or {}
    if not isinstance(growth, dict):
        raise ValueError("config.growth must be an object when provided.")

    enabled = bool(growth.get("enabled", True))
    if not enabled:
        return []

    required_gems = int(growth.get("required_gems", 1))
    max_time_min = int(growth.get("max_time_min", 200))
    max_time_scale = int(growth.get("max_time_scale", 8))

    sizes: List[Tuple[int, int]]
    if growth.get("sizes"):
        raw_sizes = growth["sizes"]
        if not isinstance(raw_sizes, list) or not raw_sizes:
            raise ValueError("growth.sizes must be a non-empty list when provided.")
        sizes = parse_size_values([str(x) for x in raw_sizes])
    else:
        start_size = int(growth.get("start_size", 4))
        max_size = int(growth.get("max_size", 20))
        size_step = int(growth.get("size_step", 1))
        if start_size < 2:
            raise ValueError("growth.start_size must be >= 2.")
        if max_size < start_size:
            raise ValueError("growth.max_size must be >= growth.start_size.")
        if size_step <= 0:
            raise ValueError("growth.size_step must be >= 1.")
        sizes = [(n, n) for n in range(start_size, max_size + 1, size_step)]

    if not sizes:
        return []

    out_dir = run_dir / "generated-levels"
    out_dir.mkdir(parents=True, exist_ok=True)
    levels: List[LevelInfo] = []
    for rows, cols in sorted(set(sizes), key=lambda x: (x[0] * x[1], x[0], x[1])):
        path = out_dir / f"generated_{rows:03d}x{cols:03d}.txt"
        txt = generate_level_text(
            rows=rows,
            cols=cols,
            required_gems=required_gems,
            max_time_min=max_time_min,
            max_time_scale=max_time_scale,
        )
        path.write_text(txt, encoding="utf-8")
        levels.append(LevelInfo(path=path, rows=rows, cols=cols, cells=rows * cols, source="growth"))
    return levels


def read_source_name(domain: Path) -> Optional[str]:
    try:
        text = domain.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    m = re.search(r"^;\s*source:\s*(.+)$", text, flags=re.MULTILINE)
    if not m:
        return None
    return Path(m.group(1).strip()).name


def default_problem_gen_for_domain(domain: Path) -> Path:
    root = repo_root()
    source_to_gen = {
        "domain.pddl": "problem_gen.py",
        "domain_merged.pddl": "problem_gen.py",
        "domain_scanner_combined.pddl": "problem_gen.py",
        "domain_scanner_separated.pddl": "problem_gen_scanner_separated.py",
        "domain_plus_from_domain.pddl": "problem_gen_plus_from_domain.py",
        "domain_plus_scanner_separated.pddl": "problem_gen_plus_scanner_separated.py",
        "domain_plus_scanner_separated_events.pddl": "problem_gen_plus_scanner_separated.py",
        "domain_plus_scanner_separated_events_fluents.pddl": "problem_gen_plus_scanner_separated_events_fluents.py",
        "domain_plus_scanner_separated_events_fluents_trimmed.pddl": "problem_gen_plus_scanner_separated_events_fluents_trimmed.py",
        "domain_plus_relaxed.pddl": "problem_gen_plus_relaxed.py",
    }

    source_name = read_source_name(domain)
    if source_name and source_name in source_to_gen:
        return root / "pddl" / source_to_gen[source_name]

    name = (source_name or domain.name).lower()
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
    if "scanner_separated" in name or "scaner_separated" in name:
        return root / "pddl" / "problem_gen_scanner_separated.py"
    return root / "pddl" / "problem_gen.py"


def pick_problem_gen(
    *,
    setting: PlannerSetting,
    domain: DomainInfo,
) -> Path:
    if setting.problem_gen is not None:
        return setting.problem_gen
    if domain.problem_gen is not None:
        return domain.problem_gen
    return default_problem_gen_for_domain(domain.path)


def generate_problem_from_level(
    *,
    level_path: Path,
    domain: DomainInfo,
    setting: PlannerSetting,
    problem_name: str,
) -> Tuple[Path, tempfile.TemporaryDirectory]:
    gen_py = pick_problem_gen(setting=setting, domain=domain)
    if not gen_py.exists():
        raise FileNotFoundError(f"Missing problem generator at {gen_py}")

    tmpdir = tempfile.TemporaryDirectory(prefix="bench_config_matrix_problem_")
    out_path = Path(tmpdir.name) / f"{problem_name}.pddl"
    cmd = [sys.executable, str(gen_py), str(level_path), "-p", problem_name]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        tmpdir.cleanup()
        detail = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"{gen_py.name} failed (rc={proc.returncode}): {detail}")
    out_path.write_text(proc.stdout, encoding="utf-8")
    return out_path, tmpdir


def command_to_string(cmd: Any) -> str:
    if isinstance(cmd, list):
        try:
            return " ".join(shlex.quote(str(x)) for x in cmd)
        except Exception:
            return " ".join(str(x) for x in cmd)
    if isinstance(cmd, str):
        return cmd
    return ""


def parse_plus_metrics(full_text: str) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    metrics["domain_parsed"] = (
        1 if re.search(r"^\s*Domain parsed\s*$", full_text, flags=re.IGNORECASE | re.MULTILINE) else None
    )
    metrics["problem_parsed"] = (
        1 if re.search(r"^\s*Problem parsed\s*$", full_text, flags=re.IGNORECASE | re.MULTILINE) else None
    )

    grounding_msec = parse_first_float(full_text, r"Grounding Time:\s*([0-9.,]+)")
    planning_msec = parse_first_float(full_text, r"Planning Time\s*\(msec\):\s*([0-9.,]+)")
    heuristic_msec = parse_first_float(full_text, r"Heuristic Time\s*\(msec\):\s*([0-9.,]+)")
    search_msec = parse_first_float(full_text, r"Search Time\s*\(msec\):\s*([0-9.,]+)")
    h1_setup_msec = parse_first_float(full_text, r"H1 Setup Time\s*\(msec\):\s*([0-9.,]+)")

    metrics["reported_grounding_msec"] = grounding_msec
    metrics["reported_grounding_sec"] = (grounding_msec / 1000.0) if grounding_msec is not None else None
    metrics["reported_planning_msec"] = planning_msec
    metrics["reported_planning_sec"] = (planning_msec / 1000.0) if planning_msec is not None else None
    metrics["reported_heuristic_msec"] = heuristic_msec
    metrics["reported_heuristic_sec"] = (heuristic_msec / 1000.0) if heuristic_msec is not None else None
    metrics["reported_search_msec"] = search_msec
    metrics["reported_search_sec"] = (search_msec / 1000.0) if search_msec is not None else None
    metrics["reported_h1_setup_msec"] = h1_setup_msec
    metrics["reported_h1_setup_sec"] = (h1_setup_msec / 1000.0) if h1_setup_msec is not None else None

    metrics["initial_heuristic_h"] = parse_first_float(full_text, r"h\s*\(I\)\s*:\s*([\-0-9.,]+)")
    metrics["reported_elapsed_plan_sec"] = parse_first_float(full_text, r"Elapsed Time:\s*([0-9.,]+)")

    metrics["plan_length_reported"] = parse_first_int(full_text, r"Plan-Length:\s*([0-9.,]+)")
    metrics["action_set_size"] = parse_first_int(full_text, r"\|A\|:\s*([0-9.,]+)")
    metrics["facts_count"] = parse_first_int(full_text, r"\|F\|:\s*([0-9.,]+)")
    metrics["x_count"] = parse_first_int(full_text, r"\|X\|:\s*([0-9.,]+)")
    problem_count = parse_first_int(full_text, r"\|P\|:\s*([0-9.,]+)")
    metrics["problem_count"] = problem_count
    metrics["predicate_count"] = problem_count
    metrics["event_count"] = parse_first_int(full_text, r"\|E\|:\s*([0-9.,]+)")

    metrics["expanded_nodes"] = parse_last_int(full_text, r"Expanded Nodes:\s*([0-9.,]+)")
    metrics["evaluated_states"] = parse_last_int(full_text, r"States Evaluated:\s*([0-9.,]+)")
    metrics["dead_end_states"] = parse_last_int(
        full_text, r"Number of Dead-Ends detected:\s*([0-9.,]+)"
    )
    metrics["duplicate_states"] = parse_last_int(
        full_text, r"Number of Duplicates detected:\s*([0-9.,]+)"
    )
    metrics["nodes_per_second_reported"] = parse_last_float(
        full_text, r"Avg-Speed\s*([0-9.,]+)\s*n/s"
    )
    metrics["plan_cost_reported"] = parse_first_float(full_text, r"Metric\s*\(Search\):\s*([0-9.,]+)")
    return metrics


def parse_classic_metrics(full_text: str) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    metrics["reported_grounding_sec"] = parse_first_float(
        full_text,
        r"Done!\s*\[[0-9.,]+s CPU,\s*([0-9.,]+)s wall-clock\]",
    )
    if metrics["reported_grounding_sec"] is None:
        metrics["reported_grounding_sec"] = parse_first_float(
            full_text, r"translator wall-clock time:\s*([0-9.,]+)s"
        )

    metrics["reported_search_sec"] = parse_last_float(full_text, r"Search time:\s*([0-9.,]+)s")
    metrics["reported_total_sec"] = parse_last_float(full_text, r"Total time:\s*([0-9.,]+)s")
    metrics["reported_planning_sec"] = parse_last_float(full_text, r"Planner time:\s*([0-9.,]+)s")

    metrics["translator_operators"] = parse_first_int(full_text, r"Translator operators:\s*([0-9.,]+)")
    metrics["action_set_size"] = metrics["translator_operators"]
    metrics["facts_count"] = parse_first_int(full_text, r"Translator facts:\s*([0-9.,]+)")

    metrics["plan_length_reported"] = parse_last_int(full_text, r"Plan length:\s*([0-9.,]+)\s*step")
    metrics["plan_cost_reported"] = parse_last_float(full_text, r"Plan cost:\s*([0-9.,]+)")

    metrics["expanded_nodes"] = parse_last_int(full_text, r"Expanded\s+([0-9.,]+)\s+state")
    metrics["reopened_nodes"] = parse_last_int(full_text, r"Reopened\s+([0-9.,]+)\s+state")
    metrics["evaluated_states"] = parse_last_int(full_text, r"Evaluated\s+([0-9.,]+)\s+state")
    metrics["generated_nodes"] = parse_last_int(full_text, r"Generated\s+([0-9.,]+)\s+state")
    metrics["dead_end_states"] = parse_last_int(full_text, r"Dead ends:\s*([0-9.,]+)\s+state")
    metrics["registered_states"] = parse_last_int(
        full_text, r"Number of registered states:\s*([0-9.,]+)"
    )
    return metrics


def parse_lifted_metrics(full_text: str) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    # Powerlifted logs vary by search mode; parse generic patterns when present.
    metrics["reported_search_sec"] = parse_last_float(full_text, r"Search time:\s*([0-9.,]+)s")
    metrics["reported_total_sec"] = parse_last_float(full_text, r"Total time:\s*([0-9.,]+)s")
    metrics["reported_planning_sec"] = parse_last_float(full_text, r"Planner time:\s*([0-9.,]+)s")
    metrics["reported_elapsed_plan_sec"] = parse_last_float(full_text, r"goal found at:\s*([0-9.,]+)")

    metrics["plan_length_reported"] = parse_last_int(full_text, r"Plan length:\s*([0-9.,]+)")

    metrics["expanded_nodes"] = parse_last_int(full_text, r"Expanded(?: Nodes?)?:\s*([0-9.,]+)")
    metrics["evaluated_states"] = parse_last_int(full_text, r"(?:States Evaluated|Evaluated)\s*:?\s*([0-9.,]+)")
    metrics["generated_nodes"] = parse_last_int(full_text, r"Generated(?: Nodes?)?:\s*([0-9.,]+)")
    metrics["nodes_per_second_reported"] = parse_last_float(full_text, r"Avg-Speed\s*([0-9.,]+)\s*n/s")
    return metrics


def execute_planner(
    *,
    setting: PlannerSetting,
    domain_path: Path,
    problem_path: Path,
) -> Tuple[str, int, Optional[int], Optional[float], str, str, str, Any, Any]:
    if setting.family in {"classic", "fa"}:
        if setting.planner == "lifted":
            status, actions, out, err, extra = solve_with_lifted(
                domain=domain_path,
                problem=problem_path,
                search=setting.lifted_search,
                evaluator=setting.lifted_evaluator,
                generator=setting.lifted_generator,
                time_limit=setting.lifted_time_limit_sec,
                hard_timeout=setting.timeout_sec,
                seed=setting.lifted_seed,
                build=setting.lifted_build,
                debug=setting.lifted_debug,
                cxx_compiler=setting.lifted_cxx_compiler,
                unit_cost=setting.lifted_unit_cost,
                only_effects_novelty_check=setting.lifted_only_effects_novelty_check,
                novelty_early_stop=setting.lifted_novelty_early_stop,
                planner_args=setting.planner_args,
                stream=setting.stream,
            )
            metrics = extra.get("metrics", {}) if isinstance(extra, dict) else {}
            command_obj = metrics.get("command")
            if not command_obj:
                command_obj = [
                    "powerlifted",
                    "-s",
                    setting.lifted_search,
                    "-e",
                    setting.lifted_evaluator,
                    "-g",
                    setting.lifted_generator,
                ]
            return (
                status,
                len(actions),
                metrics.get("returncode") if isinstance(metrics.get("returncode"), int) else None,
                float(metrics.get("time_sec")) if metrics.get("time_sec") is not None else None,
                out or "",
                err or "",
                "powerlifted",
                actions,
                command_obj,
            )

        result: PlanResult
        if setting.planner == "ff":
            result = solve_with_ff(
                domain=domain_path,
                problem=problem_path,
                timeout=setting.timeout_sec,
                stream=setting.stream,
                planner_args=setting.planner_args,
            )
        else:
            result = solve_with_fd(
                domain=domain_path,
                problem=problem_path,
                timeout=setting.timeout_sec,
                optimal=setting.fd_optimal,
                stream=setting.stream,
                keep_searching=setting.fd_keep_searching,
                planner_args=setting.planner_args,
            )
        return (
            result.status,
            len(result.actions),
            result.metrics.get("returncode") if isinstance(result.metrics.get("returncode"), int) else None,
            float(result.metrics.get("time_sec")) if result.metrics.get("time_sec") is not None else None,
            result.raw_stdout or "",
            result.raw_stderr or "",
            result.planner,
            result.actions,
            result.metrics.get("command"),
        )

    plus_result: PlusPlanResult = solve_plus(
        domain=domain_path,
        problem=problem_path,
        planner=setting.planner,
        timeout=setting.timeout_sec,
        stream=setting.stream,
        planner_args=setting.planner_args,
        java_opts=setting.java_opts,
        cmd_template=setting.cmd_template,
        enhsp_jar=setting.enhsp_jar,
        optic_bin=setting.optic_bin,
    )
    return (
        plus_result.status,
        len(plus_result.actions),
        plus_result.metrics.get("returncode") if isinstance(plus_result.metrics.get("returncode"), int) else None,
        float(plus_result.metrics.get("time_sec")) if plus_result.metrics.get("time_sec") is not None else None,
        plus_result.raw_stdout or "",
        plus_result.raw_stderr or "",
        plus_result.planner,
        plus_result.actions,
        plus_result.metrics.get("command"),
    )


def run_single_task(
    task: RunTask,
    *,
    run_dir: Path,
    dry_run: bool,
) -> TaskResult:
    logs_dir = run_dir / "logs"
    plans_dir = run_dir / "plans"
    problems_dir = run_dir / "compiled-problems"
    logs_dir.mkdir(parents=True, exist_ok=True)
    plans_dir.mkdir(parents=True, exist_ok=True)
    problems_dir.mkdir(parents=True, exist_ok=True)

    name_tag = (
        f"r{task.run_id:06d}_s_{safe_tag(task.setting.name)}"
        f"_d_{safe_tag(task.domain.path.stem)}_l_{safe_tag(task.level.path.stem)}"
        f"_{task.phase}"
        f"{f'_rep{task.repeat_index:02d}' if task.repeat_index > 0 else ''}"
    )
    stdout_path = logs_dir / f"{name_tag}.stdout.txt"
    stderr_path = logs_dir / f"{name_tag}.stderr.txt"
    compiled_problem_path = problems_dir / f"{name_tag}.pddl"

    plan_file = plans_dir / f"{name_tag}.plan"
    timed_plan_file = plans_dir / f"{name_tag}.timed.plan"

    measured_total_start = time.perf_counter()
    measured_problem_gen_sec = 0.0
    measured_solver_sec = 0.0

    wrapper_time_sec: Optional[float] = None
    status = "dry-run" if dry_run else "error"
    plan_action_count = 0
    returncode: Optional[int] = None
    planner_used = task.setting.planner
    out_text = ""
    err_text = ""
    command = ""
    parse_metrics: Dict[str, Any] = {}
    error_message = ""

    tmpdir: Optional[tempfile.TemporaryDirectory] = None
    generated_problem: Optional[Path] = None
    try:
        if dry_run:
            ensure_text_file(stdout_path, "")
            ensure_text_file(stderr_path, "[DRY-RUN] planner execution skipped.\n")
            row = BenchRow(
                run_id=task.run_id,
                pairing_id=task.pairing_id,
                planner_setting=task.setting.name,
                planner_family=task.setting.family,
                planner=planner_used,
                planner_args=task.setting.planner_args,
                domain=str(task.domain.path),
                domain_kind=task.domain.kind,
                level=str(task.level.path),
                level_source=task.level.source,
                phase=task.phase,
                repeat_index=task.repeat_index,
                rows=task.level.rows,
                cols=task.level.cols,
                cells=task.level.cells,
                status="dry-run",
                timeout_sec=task.setting.timeout_sec,
                measured_total_sec=round(time.perf_counter() - measured_total_start, 6),
                measured_problem_gen_sec=0.0,
                measured_solver_sec=0.0,
                wrapper_time_sec=None,
                domain_parsed=None,
                problem_parsed=None,
                reported_grounding_msec=None,
                reported_grounding_sec=None,
                reported_h1_setup_msec=None,
                reported_h1_setup_sec=None,
                initial_heuristic_h=None,
                reported_heuristic_msec=None,
                reported_heuristic_sec=None,
                reported_search_msec=None,
                reported_search_sec=None,
                reported_total_sec=None,
                reported_planning_msec=None,
                reported_planning_sec=None,
                reported_elapsed_plan_sec=None,
                plan_length_reported=None,
                plan_action_count=0,
                plan_cost_reported=None,
                action_set_size=None,
                facts_count=None,
                x_count=None,
                problem_count=None,
                predicate_count=None,
                event_count=None,
                translator_operators=None,
                expanded_nodes=None,
                reopened_nodes=None,
                evaluated_states=None,
                generated_nodes=None,
                dead_end_states=None,
                duplicate_states=None,
                registered_states=None,
                nodes_per_second_reported=None,
                nodes_per_second_derived=None,
                nodes_per_second=None,
                returncode=None,
                command="",
                stdout_file=str(stdout_path),
                stderr_file=str(stderr_path),
                compiled_problem_file="",
                plan_file="",
                timed_plan_file="",
                error_message="",
            )
            return TaskResult(row=row, task=task)

        problem_gen_start = time.perf_counter()
        problem_name = f"cfg_{safe_tag(task.domain.path.stem)}_{safe_tag(task.level.path.stem)}_{task.run_id:06d}"
        generated_problem, tmpdir = generate_problem_from_level(
            level_path=task.level.path,
            domain=task.domain,
            setting=task.setting,
            problem_name=problem_name,
        )
        measured_problem_gen_sec = time.perf_counter() - problem_gen_start
        compiled_problem_path.write_text(
            generated_problem.read_text(encoding="utf-8", errors="replace"),
            encoding="utf-8",
        )

        solver_start = time.perf_counter()
        try:
            (
                status,
                plan_action_count,
                returncode,
                wrapper_time_sec,
                out_text,
                err_text,
                planner_used,
                actions_obj,
                command_obj,
            ) = execute_planner(
                setting=task.setting,
                domain_path=task.domain.path,
                problem_path=generated_problem,
            )
            command = command_to_string(command_obj)

            if task.setting.family in {"classic", "fa"}:
                actions = actions_obj if isinstance(actions_obj, list) else []
                if actions:
                    write_classic_plan_file(plan_file, actions)
                    try:
                        write_direction_plan(
                            plans_dir / f"{name_tag}.play.plan",
                            actions,
                        )
                    except Exception:
                        pass
            else:
                timed_actions = actions_obj if isinstance(actions_obj, list) else []
                if timed_actions:
                    write_plus_plan_file(plan_file, timed_actions)
                    write_plus_timed_plan_file(timed_plan_file, timed_actions)
        except Exception as exc:
            status = "error"
            out_text = ""
            err_text = f"[ERR] Planner execution failed: {exc}\n"
            error_message = str(exc)
        measured_solver_sec = time.perf_counter() - solver_start

        ensure_text_file(stdout_path, out_text)
        ensure_text_file(stderr_path, err_text)

        full_text = (out_text or "") + "\n" + (err_text or "")
        if task.setting.family == "plus":
            parse_metrics = parse_plus_metrics(full_text)
        elif task.setting.planner == "lifted":
            parse_metrics = parse_lifted_metrics(full_text)
        else:
            parse_metrics = parse_classic_metrics(full_text)

        expanded_nodes = parse_metrics.get("expanded_nodes")
        reported_search_sec = parse_metrics.get("reported_search_sec")
        nodes_per_second_derived = None
        if isinstance(expanded_nodes, int) and isinstance(reported_search_sec, float) and reported_search_sec > 0:
            nodes_per_second_derived = expanded_nodes / reported_search_sec
        nodes_per_second_reported = parse_metrics.get("nodes_per_second_reported")
        nodes_per_second = nodes_per_second_reported if nodes_per_second_reported is not None else nodes_per_second_derived

        row = BenchRow(
            run_id=task.run_id,
            pairing_id=task.pairing_id,
            planner_setting=task.setting.name,
            planner_family=task.setting.family,
            planner=planner_used,
            planner_args=task.setting.planner_args,
            domain=str(task.domain.path),
            domain_kind=task.domain.kind,
            level=str(task.level.path),
            level_source=task.level.source,
            phase=task.phase,
            repeat_index=task.repeat_index,
            rows=task.level.rows,
            cols=task.level.cols,
            cells=task.level.cells,
            status=status,
            timeout_sec=task.setting.timeout_sec,
            measured_total_sec=round(time.perf_counter() - measured_total_start, 6),
            measured_problem_gen_sec=round(measured_problem_gen_sec, 6),
            measured_solver_sec=round(measured_solver_sec, 6),
            wrapper_time_sec=wrapper_time_sec,
            domain_parsed=parse_metrics.get("domain_parsed"),
            problem_parsed=parse_metrics.get("problem_parsed"),
            reported_grounding_msec=parse_metrics.get("reported_grounding_msec"),
            reported_grounding_sec=parse_metrics.get("reported_grounding_sec"),
            reported_h1_setup_msec=parse_metrics.get("reported_h1_setup_msec"),
            reported_h1_setup_sec=parse_metrics.get("reported_h1_setup_sec"),
            initial_heuristic_h=parse_metrics.get("initial_heuristic_h"),
            reported_heuristic_msec=parse_metrics.get("reported_heuristic_msec"),
            reported_heuristic_sec=parse_metrics.get("reported_heuristic_sec"),
            reported_search_msec=parse_metrics.get("reported_search_msec"),
            reported_search_sec=reported_search_sec,
            reported_total_sec=parse_metrics.get("reported_total_sec"),
            reported_planning_msec=parse_metrics.get("reported_planning_msec"),
            reported_planning_sec=parse_metrics.get("reported_planning_sec"),
            reported_elapsed_plan_sec=parse_metrics.get("reported_elapsed_plan_sec"),
            plan_length_reported=parse_metrics.get("plan_length_reported"),
            plan_action_count=plan_action_count,
            plan_cost_reported=parse_metrics.get("plan_cost_reported"),
            action_set_size=parse_metrics.get("action_set_size"),
            facts_count=parse_metrics.get("facts_count"),
            x_count=parse_metrics.get("x_count"),
            problem_count=parse_metrics.get("problem_count"),
            predicate_count=parse_metrics.get("predicate_count"),
            event_count=parse_metrics.get("event_count"),
            translator_operators=parse_metrics.get("translator_operators"),
            expanded_nodes=expanded_nodes,
            reopened_nodes=parse_metrics.get("reopened_nodes"),
            evaluated_states=parse_metrics.get("evaluated_states"),
            generated_nodes=parse_metrics.get("generated_nodes"),
            dead_end_states=parse_metrics.get("dead_end_states"),
            duplicate_states=parse_metrics.get("duplicate_states"),
            registered_states=parse_metrics.get("registered_states"),
            nodes_per_second_reported=nodes_per_second_reported,
            nodes_per_second_derived=nodes_per_second_derived,
            nodes_per_second=nodes_per_second,
            returncode=returncode,
            command=command,
            stdout_file=str(stdout_path),
            stderr_file=str(stderr_path),
            compiled_problem_file=str(compiled_problem_path),
            plan_file=str(plan_file) if plan_file.exists() else "",
            timed_plan_file=str(timed_plan_file) if timed_plan_file.exists() else "",
            error_message=error_message,
        )
        return TaskResult(row=row, task=task)
    finally:
        if tmpdir is not None:
            tmpdir.cleanup()


def pairing_matches_setting(setting: PlannerSetting, domain: DomainInfo) -> bool:
    if setting.family != domain.kind:
        return False
    if setting.domain_include and not match_any(domain.path, setting.domain_include):
        return False
    if setting.domain_exclude and match_any(domain.path, setting.domain_exclude):
        return False
    return True


def build_pairings(settings: Sequence[PlannerSetting], domains: Sequence[DomainInfo]) -> List[Pairing]:
    pairings: List[Pairing] = []
    for setting in settings:
        for domain in domains:
            if not pairing_matches_setting(setting, domain):
                continue
            pid = f"{safe_tag(setting.name)}::{safe_tag(domain.path.stem)}"
            pairings.append(Pairing(id=pid, setting=setting, domain=domain))
    return pairings


def next_task_for_state(
    state: PairState,
    *,
    custom_levels: Sequence[LevelInfo],
    random_repeat_levels: Sequence[LevelInfo],
    growth_levels: Sequence[LevelInfo],
    run_id: int,
    custom_levels_run_last: bool,
    custom_levels_require_growth_past_size: Optional[int],
) -> Optional[RunTask]:
    if state.done:
        return None

    if custom_levels_run_last:
        if state.phase == "random-repeat":
            if state.random_repeat_index < len(random_repeat_levels):
                level = random_repeat_levels[state.random_repeat_index]
                return RunTask(
                    run_id=run_id,
                    pairing_id=state.pairing.id,
                    setting=state.pairing.setting,
                    domain=state.pairing.domain,
                    level=level,
                    phase="random-repeat",
                )
            state.phase = "growth"

        if state.phase == "growth":
            if state.growth_index < len(growth_levels):
                level = growth_levels[state.growth_index]
                return RunTask(
                    run_id=run_id,
                    pairing_id=state.pairing.id,
                    setting=state.pairing.setting,
                    domain=state.pairing.domain,
                    level=level,
                    phase="growth",
                )

            custom_gate_ok = True
            if custom_levels_require_growth_past_size is not None:
                custom_gate_ok = (
                    state.growth_max_nonfailure_size > custom_levels_require_growth_past_size
                )
            if custom_gate_ok:
                state.phase = "custom"
            else:
                state.pending_excluded_runs += max(0, len(custom_levels) - state.custom_index)
                state.custom_index = len(custom_levels)
                state.done = True
                return None

        if state.phase == "custom":
            if state.custom_index < len(custom_levels):
                level = custom_levels[state.custom_index]
                return RunTask(
                    run_id=run_id,
                    pairing_id=state.pairing.id,
                    setting=state.pairing.setting,
                    domain=state.pairing.domain,
                    level=level,
                    phase="custom",
                )
            state.done = True
            return None

        state.done = True
        return None

    if state.phase == "custom":
        if state.custom_index < len(custom_levels):
            level = custom_levels[state.custom_index]
            return RunTask(
                run_id=run_id,
                pairing_id=state.pairing.id,
                setting=state.pairing.setting,
                domain=state.pairing.domain,
                level=level,
                phase="custom",
            )
        state.phase = "random-repeat"

    if state.phase == "random-repeat":
        if state.random_repeat_index < len(random_repeat_levels):
            level = random_repeat_levels[state.random_repeat_index]
            return RunTask(
                run_id=run_id,
                pairing_id=state.pairing.id,
                setting=state.pairing.setting,
                domain=state.pairing.domain,
                level=level,
                phase="random-repeat",
            )
        state.phase = "growth"

    if state.phase == "growth":
        if state.growth_index < len(growth_levels):
            level = growth_levels[state.growth_index]
            return RunTask(
                run_id=run_id,
                pairing_id=state.pairing.id,
                setting=state.pairing.setting,
                domain=state.pairing.domain,
                level=level,
                phase="growth",
            )
        state.done = True
        return None

    state.done = True
    return None


def advance_state_after_result(
    state: PairState,
    *,
    row: BenchRow,
    custom_fail_limit: int,
    growth_stop_on_failure: bool,
    custom_levels_count: int,
    random_repeat_levels_count: int,
    growth_levels_count: int,
    custom_levels_run_last: bool,
    custom_levels_require_growth_past_size: Optional[int],
    random_repeat_failure_stops_pair_repeats: bool,
) -> int:
    excluded_runs = 0
    if row.phase == "custom":
        state.custom_index += 1
        if is_failure_status(row.status):
            state.custom_fail_streak += 1
        else:
            state.custom_fail_streak = 0
        if state.custom_fail_streak >= custom_fail_limit:
            excluded_runs += max(0, custom_levels_count - state.custom_index)
            state.custom_index = custom_levels_count
            if custom_levels_run_last:
                state.done = True
            else:
                state.phase = "random-repeat"
    elif row.phase == "random-repeat":
        state.random_repeat_index += 1
        if random_repeat_failure_stops_pair_repeats and is_failure_status(row.status):
            excluded_runs += max(0, random_repeat_levels_count - state.random_repeat_index)
            state.random_repeat_index = random_repeat_levels_count
            state.phase = "growth"
    elif row.phase == "growth":
        if not is_failure_status(row.status):
            state.growth_max_nonfailure_size = max(
                state.growth_max_nonfailure_size,
                min(row.rows, row.cols),
            )
        state.growth_index += 1
        if growth_stop_on_failure and is_failure_status(row.status):
            excluded_runs += max(0, growth_levels_count - state.growth_index)
            state.done = True
        elif custom_levels_run_last and state.growth_index >= growth_levels_count:
            custom_gate_ok = True
            if custom_levels_require_growth_past_size is not None:
                custom_gate_ok = (
                    state.growth_max_nonfailure_size > custom_levels_require_growth_past_size
                )
            if custom_gate_ok:
                state.phase = "custom"
            else:
                excluded_runs += max(0, custom_levels_count - state.custom_index)
                state.custom_index = custom_levels_count
                state.done = True
    return excluded_runs


def remaining_base_runs_for_state(
    state: PairState,
    *,
    custom_levels_count: int,
    random_repeat_levels_count: int,
    growth_levels_count: int,
    custom_levels_run_last: bool,
    custom_levels_require_growth_past_size: Optional[int],
) -> int:
    if state.done:
        return 0
    remaining = 0
    if custom_levels_run_last:
        if state.phase == "random-repeat":
            remaining += max(0, random_repeat_levels_count - state.random_repeat_index)
            remaining += max(0, growth_levels_count - state.growth_index)
            remaining += max(0, custom_levels_count - state.custom_index)
            return remaining
        if state.phase == "growth":
            growth_left = max(0, growth_levels_count - state.growth_index)
            remaining += growth_left
            if growth_left > 0:
                remaining += max(0, custom_levels_count - state.custom_index)
            elif (
                custom_levels_require_growth_past_size is None
                or state.growth_max_nonfailure_size > custom_levels_require_growth_past_size
            ):
                remaining += max(0, custom_levels_count - state.custom_index)
            return remaining
        if state.phase == "custom":
            remaining += max(0, custom_levels_count - state.custom_index)
            return remaining
        return 0

    if state.phase == "custom":
        remaining += max(0, custom_levels_count - state.custom_index)
        remaining += max(0, random_repeat_levels_count - state.random_repeat_index)
        remaining += max(0, growth_levels_count - state.growth_index)
        return remaining
    if state.phase == "random-repeat":
        remaining += max(0, random_repeat_levels_count - state.random_repeat_index)
        remaining += max(0, growth_levels_count - state.growth_index)
        return remaining
    if state.phase == "growth":
        remaining += max(0, growth_levels_count - state.growth_index)
        return remaining
    return 0


def write_csv(path: Path, rows: Sequence[BenchRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def append_csv_rows(path: Path, rows: Sequence[BenchRow]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = True
    if path.exists():
        try:
            write_header = path.stat().st_size == 0
        except Exception:
            write_header = True
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def status_summary(rows: Sequence[BenchRow]) -> str:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    return ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))


def generate_plots(csv_path: Path, out_dir: Path) -> int:
    if not PLOT_CONFIG_MATRIX_SCRIPT.exists():
        print(f"[WARN] Plot script not found: {PLOT_CONFIG_MATRIX_SCRIPT}")
        return 0
    cmd = [
        sys.executable,
        str(PLOT_CONFIG_MATRIX_SCRIPT),
        "--csv",
        str(csv_path),
        "--out-dir",
        str(out_dir),
        "--title-prefix",
        "Config Matrix",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        print(f"[WARN] Failed to generate plots: {detail}")
        return 0
    count = 0
    try:
        count = len([p for p in out_dir.glob("*.svg") if p.is_file()])
    except Exception:
        count = 0
    out_text = (proc.stdout or "").strip()
    if out_text:
        print(out_text)
    return count


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Run planner settings from a JSON config across compatible test domains, "
            "with custom-level fail streak cutoff, optional random-repeat maps, "
            "optional repeats for solved instances, optional random-repeat early-stop, "
            "optional custom-level run-last growth gating, and growth-level timeout cutoff."
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
            "config-matrix_<timestamp>/"
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
        "--seed",
        type=int,
        default=None,
        help="Random seed override for planner/domain dispatch randomization.",
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
    custom_fail_limit = int(cfg.get("custom_fail_streak_limit", 3))
    if custom_fail_limit <= 0:
        print("[ERR] custom_fail_streak_limit must be > 0.", file=sys.stderr)
        return 2
    growth_stop_on_failure = bool(cfg.get("growth_stop_on_failure", True))
    custom_levels_run_last = bool(cfg.get("custom_levels_run_last", False))
    custom_levels_require_growth_past_size = parse_growth_size_threshold(
        cfg.get("custom_levels_require_growth_past_size")
    )
    if custom_levels_require_growth_past_size is not None:
        custom_levels_run_last = True
    random_repeat_failure_stops_pair_repeats = bool(
        cfg.get(
            "stop_remaining_random_repeats_for_pair_on_failure",
            cfg.get(
                "random_repeat_failure_stops_pair_repeats",
                cfg.get(
                    "terminate_run_on_random_repeat_failure",
                    cfg.get("random_repeat_failure_terminates_run", False),
                ),
            ),
        )
    )
    repeat_successful_runs_raw = cfg.get("repeat_successful_runs")
    if repeat_successful_runs_raw is None:
        for alias in ("repeat_successful_solvers", "repeat_successful_sovlers", "repeat_successful_solver_runs"):
            if alias in cfg:
                repeat_successful_runs_raw = cfg.get(alias)
                break
    repeat_successful_runs = int(repeat_successful_runs_raw or 0)
    if repeat_successful_runs < 0:
        print("[ERR] repeat_successful_runs must be >= 0.", file=sys.stderr)
        return 2
    seed = args.seed if args.seed is not None else cfg.get("random_seed")

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
        custom_levels = collect_custom_levels(config=cfg, config_dir=config_dir)
        random_repeat_levels = collect_random_repeat_levels(
            config=cfg,
            run_dir=run_dir,
            config_seed=seed,
        )
        growth_levels = collect_growth_levels(config=cfg, run_dir=run_dir)
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

    if any(s.stream for s in settings) and max_parallel > 1 and not args.dry_run:
        print("[WARN] stream=true with parallel runs can interleave logs.")

    rng = random.Random(seed)

    max_matrix_runs = len(pairings) * (
        len(custom_levels) + len(random_repeat_levels) + len(growth_levels)
    )
    n_classic = sum(d.kind == "classic" for d in domains)
    n_fa = sum(d.kind == "fa" for d in domains)
    n_plus = sum(d.kind == "plus" for d in domains)
    print(f"[INFO] Config: {config_path}")
    print(f"[INFO] Pairings: {len(pairings)}")
    print(f"[INFO] Domains: {len(domains)} (classic={n_classic}, fa={n_fa}, plus={n_plus})")
    print(f"[INFO] Planner settings: {len(settings)}")
    print(f"[INFO] Custom levels: {len(custom_levels)}")
    print(f"[INFO] Random repeat levels: {len(random_repeat_levels)}")
    print(f"[INFO] Growth levels: {len(growth_levels)}")
    print(f"[INFO] Max matrix runs (upper bound): {max_matrix_runs}")
    print(f"[INFO] Repeat solved instances: {repeat_successful_runs}")
    print(f"[INFO] Custom levels run last: {custom_levels_run_last}")
    print(
        "[INFO] Custom levels require growth past size: "
        f"{custom_levels_require_growth_past_size if custom_levels_require_growth_past_size is not None else 'disabled'}"
    )
    print(
        "[INFO] Random-repeat failure stops remaining repeats for that pair: "
        f"{random_repeat_failure_stops_pair_repeats}"
    )
    print(f"[INFO] Max parallel runs: {max_parallel} (QoS: equal thread priority)")
    print(f"[INFO] Random seed: {seed}")
    print(f"[INFO] Dry run: {args.dry_run}")
    print(f"[INFO] Run dir: {run_dir}")
    print(f"[INFO] Output CSV: {output_csv}")
    print(f"[INFO] Plots dir: {plots_dir}")

    states: Dict[str, PairState] = {
        p.id: PairState(
            pairing=p,
            phase=("random-repeat" if custom_levels_run_last else "custom"),
            custom_index=0,
            random_repeat_index=0,
            growth_index=0,
            custom_fail_streak=0,
            growth_max_nonfailure_size=0,
            pending_excluded_runs=0,
            in_flight=False,
            done=False,
        )
        for p in pairings
    }
    ready: List[str] = list(states.keys())
    repeat_queues: Dict[str, List[RunTask]] = {pid: [] for pid in states}
    rows: List[BenchRow] = []
    run_counter = 0
    completed = 0
    excluded_base_runs = 0
    planned_repeat_runs_total = 0

    run_meta = {
        "config_path": str(config_path),
        "run_dir": str(run_dir),
        "output_csv": str(output_csv),
        "dry_run": bool(args.dry_run),
        "seed": seed,
        "max_parallel": max_parallel,
        "custom_fail_streak_limit": custom_fail_limit,
        "growth_stop_on_failure": growth_stop_on_failure,
        "custom_levels_run_last": custom_levels_run_last,
        "custom_levels_require_growth_past_size": custom_levels_require_growth_past_size,
        "stop_remaining_random_repeats_for_pair_on_failure": random_repeat_failure_stops_pair_repeats,
        "terminate_run_on_random_repeat_failure": random_repeat_failure_stops_pair_repeats,
        "repeat_successful_runs": repeat_successful_runs,
        "domains": [str(d.path) for d in domains],
        "settings": [asdict(s) | {"enhsp_jar": str(s.enhsp_jar) if s.enhsp_jar else None, "optic_bin": str(s.optic_bin) if s.optic_bin else None, "problem_gen": str(s.problem_gen) if s.problem_gen else None} for s in settings],
        "custom_levels": [str(l.path) for l in custom_levels],
        "random_repeat_levels": [str(l.path) for l in random_repeat_levels],
        "growth_levels": [str(l.path) for l in growth_levels],
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    # Ensure a CSV exists from the beginning so partial results survive interruptions.
    write_csv(output_csv, [])

    stop_requested = False
    interrupted = False
    signal_hits = 0

    old_sigint = signal.getsignal(signal.SIGINT)
    old_sigterm = signal.getsignal(signal.SIGTERM)

    def handle_stop(sig: int, _frame: Any) -> None:
        nonlocal stop_requested, interrupted, signal_hits
        signal_hits += 1
        interrupted = True
        stop_requested = True
        name = signal.Signals(sig).name
        if signal_hits == 1:
            print(
                f"[WARN] Received {name}. Stopping new scheduling and preserving partial CSV progress."
            )
            return
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    base_max_runs = max_matrix_runs

    def estimate_remaining_timeout_sec(
        future_to_ctx: Dict[concurrent.futures.Future[TaskResult], Tuple[str, RunTask]],
    ) -> float:
        timeout_sum = 0.0
        for _pid, running_task in future_to_ctx.values():
            timeout_sum += float(running_task.setting.timeout_sec)
        for pid, st in states.items():
            timeout_sum += float(len(repeat_queues[pid]) * st.pairing.setting.timeout_sec)
            timeout_sum += float(
                remaining_base_runs_for_state(
                    st,
                    custom_levels_count=len(custom_levels),
                    random_repeat_levels_count=len(random_repeat_levels),
                    growth_levels_count=len(growth_levels),
                    custom_levels_run_last=custom_levels_run_last,
                    custom_levels_require_growth_past_size=custom_levels_require_growth_past_size,
                )
                * st.pairing.setting.timeout_sec
            )
        return timeout_sum

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as ex:
            future_to_ctx: Dict[concurrent.futures.Future[TaskResult], Tuple[str, RunTask]] = {}

            while True:
                while (not stop_requested) and len(future_to_ctx) < max_parallel and ready:
                    rng.shuffle(ready)
                    pid = ready.pop()
                    st = states[pid]
                    if st.in_flight:
                        continue

                    task: Optional[RunTask] = None
                    if repeat_queues[pid]:
                        task = repeat_queues[pid].pop(0)
                    elif not st.done:
                        run_counter += 1
                        task = next_task_for_state(
                            st,
                            custom_levels=custom_levels,
                            random_repeat_levels=random_repeat_levels,
                            growth_levels=growth_levels,
                            run_id=run_counter,
                            custom_levels_run_last=custom_levels_run_last,
                            custom_levels_require_growth_past_size=custom_levels_require_growth_past_size,
                        )
                    if task is None:
                        if st.pending_excluded_runs > 0:
                            excluded_base_runs += st.pending_excluded_runs
                            st.pending_excluded_runs = 0
                        st.done = True
                        continue

                    st.in_flight = True
                    fut = ex.submit(
                        run_single_task,
                        task,
                        run_dir=run_dir,
                        dry_run=args.dry_run,
                    )
                    future_to_ctx[fut] = (pid, task)

                if not future_to_ctx:
                    break

                try:
                    done, _ = concurrent.futures.wait(
                        future_to_ctx.keys(),
                        timeout=0.5,
                        return_when=concurrent.futures.FIRST_COMPLETED,
                    )
                except KeyboardInterrupt:
                    interrupted = True
                    stop_requested = True
                    print("[WARN] Termination requested. Waiting for running tasks to finish; no new tasks will start.")
                    continue

                if not done:
                    continue

                for fut in done:
                    pid, submitted_task = future_to_ctx.pop(fut)
                    st = states[pid]
                    st.in_flight = False
                    completed += 1

                    try:
                        task_result = fut.result()
                        row = task_result.row
                        completed_task = task_result.task
                    except Exception as exc:
                        # This should be rare; convert to a minimal synthetic error row.
                        completed_task = submitted_task
                        row = BenchRow(
                            run_id=completed_task.run_id,
                            pairing_id=completed_task.pairing_id,
                            planner_setting=completed_task.setting.name,
                            planner_family=completed_task.setting.family,
                            planner=completed_task.setting.planner,
                            planner_args=completed_task.setting.planner_args,
                            domain=str(completed_task.domain.path),
                            domain_kind=completed_task.domain.kind,
                            level=str(completed_task.level.path),
                            level_source=completed_task.level.source,
                            phase=completed_task.phase,
                            repeat_index=completed_task.repeat_index,
                            rows=completed_task.level.rows,
                            cols=completed_task.level.cols,
                            cells=completed_task.level.cells,
                            status="error",
                            timeout_sec=completed_task.setting.timeout_sec,
                            measured_total_sec=0.0,
                            measured_problem_gen_sec=0.0,
                            measured_solver_sec=0.0,
                            wrapper_time_sec=None,
                            domain_parsed=None,
                            problem_parsed=None,
                            reported_grounding_msec=None,
                            reported_grounding_sec=None,
                            reported_h1_setup_msec=None,
                            reported_h1_setup_sec=None,
                            initial_heuristic_h=None,
                            reported_heuristic_msec=None,
                            reported_heuristic_sec=None,
                            reported_search_msec=None,
                            reported_search_sec=None,
                            reported_total_sec=None,
                            reported_planning_msec=None,
                            reported_planning_sec=None,
                            reported_elapsed_plan_sec=None,
                            plan_length_reported=None,
                            plan_action_count=0,
                            plan_cost_reported=None,
                            action_set_size=None,
                            facts_count=None,
                            x_count=None,
                            problem_count=None,
                            predicate_count=None,
                            event_count=None,
                            translator_operators=None,
                            expanded_nodes=None,
                            reopened_nodes=None,
                            evaluated_states=None,
                            generated_nodes=None,
                            dead_end_states=None,
                            duplicate_states=None,
                            registered_states=None,
                            nodes_per_second_reported=None,
                            nodes_per_second_derived=None,
                            nodes_per_second=None,
                            returncode=None,
                            command="",
                            stdout_file="",
                            stderr_file="",
                            compiled_problem_file="",
                            plan_file="",
                            timed_plan_file="",
                            error_message=str(exc),
                        )

                    rows.append(row)
                    append_csv_rows(output_csv, [row])

                    if (
                        random_repeat_failure_stops_pair_repeats
                        and row.phase == "random-repeat"
                        and is_failure_status(row.status)
                        and completed_task.repeat_index == 0
                    ):
                        print(
                            "[WARN] Random-repeat failure encountered for pairing "
                            f"{row.planner_setting} / {Path(row.domain).name} at "
                            f"{Path(row.level).name if row.level else '-'} ({row.status}). "
                            "Remaining random-repeat levels for this pairing will be skipped."
                        )

                    if completed_task.repeat_index == 0:
                        excluded_base_runs += advance_state_after_result(
                            st,
                            row=row,
                            custom_fail_limit=custom_fail_limit,
                            growth_stop_on_failure=growth_stop_on_failure,
                            custom_levels_count=len(custom_levels),
                            random_repeat_levels_count=len(random_repeat_levels),
                            growth_levels_count=len(growth_levels),
                            custom_levels_run_last=custom_levels_run_last,
                            custom_levels_require_growth_past_size=custom_levels_require_growth_past_size,
                            random_repeat_failure_stops_pair_repeats=random_repeat_failure_stops_pair_repeats,
                        )
                        if repeat_successful_runs > 0 and is_success_status(row.status):
                            for rep_idx in range(1, repeat_successful_runs + 1):
                                run_counter += 1
                                repeat_queues[pid].append(
                                    RunTask(
                                        run_id=run_counter,
                                        pairing_id=completed_task.pairing_id,
                                        setting=completed_task.setting,
                                        domain=completed_task.domain,
                                        level=completed_task.level,
                                        phase=completed_task.phase,
                                        repeat_index=rep_idx,
                                    )
                                )
                            planned_repeat_runs_total += repeat_successful_runs

                    if repeat_queues[pid] or not st.done:
                        ready.append(pid)

                    total_effective_runs = max(
                        completed,
                        max(0, base_max_runs - excluded_base_runs) + planned_repeat_runs_total,
                    )
                    remaining_instances = max(0, total_effective_runs - completed)
                    remaining_timeout_sec = estimate_remaining_timeout_sec(future_to_ctx)
                    eta_parallel_upper_sec = remaining_timeout_sec / max(1, max_parallel)
                    print(
                        f"[{completed}/{total_effective_runs}] {Path(row.domain).name} | "
                        f"{Path(row.level).name if row.level else '-'} | {row.planner_setting}"
                        f"{f' [rep {row.repeat_index}]' if row.repeat_index > 0 else ''} -> {row.status} | "
                        f"measured={row.measured_total_sec:.3f}s | remaining={remaining_instances} | "
                        f"eta<={format_eta_hms(eta_parallel_upper_sec)} "
                        f"(timeout-sum={format_eta_hms(remaining_timeout_sec)})"
                    )
    finally:
        signal.signal(signal.SIGINT, old_sigint)
        signal.signal(signal.SIGTERM, old_sigterm)

    rows.sort(
        key=lambda r: (
            r.planner_setting,
            r.domain,
            r.phase,
            r.cells,
            r.rows,
            r.cols,
            r.run_id,
        )
    )
    write_csv(output_csv, rows)

    print(f"[OK] Wrote CSV: {output_csv}")
    print(f"[OK] Rows: {len(rows)}")
    print(f"[OK] Status counts: {status_summary(rows)}")
    plots_generated = 0
    if not args.skip_plots and rows:
        plots_generated = generate_plots(output_csv, plots_dir)
    print(f"[OK] Plots generated: {plots_generated}")
    print(f"[OK] Artifacts: {run_dir}")
    if interrupted:
        print("[WARN] Run interrupted. Partial results were preserved in CSV during execution.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
