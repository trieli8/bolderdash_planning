#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EMPTY_IDS = {1}
DIRT_IDS = {2}
STONE_IDS = {3, 4, 48}
STONE_FALLING_IDS = {4}
GEM_IDS = {5, 6, 90, 91}
GEM_FALLING_IDS = {6, 91}
AGENT_IDS = {0, 9}
BRICK_IDS = {
    7, 8,
    10, 11, 12, 13,
    14, 15, 16, 17,
    18, 19,
    20, 21, 22,
    23,
}
RECONSTRUCTIBLE_IDS = EMPTY_IDS | DIRT_IDS | STONE_IDS | GEM_IDS | AGENT_IDS | BRICK_IDS

IGNORED_ACTION_NAMES = {"end_tick", "physics_on_bottom", "physics_agent_noop"}


@dataclass(frozen=True)
class LevelData:
    rows: int
    cols: int
    max_time: int
    required_gems: int
    cell_ids: tuple[int, ...]


@dataclass(frozen=True)
class IterationSummary:
    iteration: int
    input_level: str
    output_level: str | None
    plan_dir: str
    raw_actions: int
    direction_actions: int
    gems_remaining: int | None
    stop_reason: str | None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def plan_script_path() -> Path:
    return repo_root() / "tools" / "plan.py"


def stones_trace_path() -> Path:
    return repo_root() / "stonesandgem" / "build" / "bin" / "stones_trace"


def read_level_text(path: Path) -> str:
    lines: list[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith((";", "#")):
            continue
        lines.append(stripped)
    if not lines:
        raise ValueError(f"No level string found in {path}")
    return "\n".join(lines)


def parse_level_string(level_text: str) -> LevelData:
    parts = [p for p in level_text.strip().split("|") if p != ""]
    if len(parts) < 4:
        raise ValueError("Level string must be rows|cols|max_time|required_gems|...")
    rows = int(parts[0])
    cols = int(parts[1])
    max_time = int(parts[2])
    required_gems = int(parts[3])
    cell_strs = parts[4:]
    expected = rows * cols
    if len(cell_strs) != expected:
        raise ValueError(f"Expected {expected} cells, got {len(cell_strs)}")
    cell_ids = tuple(int(s) for s in cell_strs)
    return LevelData(
        rows=rows,
        cols=cols,
        max_time=max_time,
        required_gems=required_gems,
        cell_ids=cell_ids,
    )


def render_level_string(level: LevelData) -> str:
    fields = [
        str(level.rows),
        str(level.cols),
        str(level.max_time),
        str(level.required_gems),
    ]
    for cell_id in level.cell_ids:
        fields.append(f"{cell_id:02d}" if cell_id < 10 else str(cell_id))
    return "|".join(fields)


def validate_reconstructible(level: LevelData, path: Path) -> None:
    unsupported = sorted({cell_id for cell_id in level.cell_ids if cell_id not in RECONSTRUCTIBLE_IDS})
    if unsupported:
        raise ValueError(
            f"{path} contains unsupported cell ids for board reconstruction: {unsupported}. "
            "This wrapper currently supports agent/empty/dirt/stone/gem/brick-style levels."
        )


def parse_sexp_plan_line(line: str) -> tuple[str, list[str]] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith(";"):
        return None
    match = re.match(r"^\(\s*([^\s()]+)(.*?)\)\s*$", stripped)
    if not match:
        return None
    name = match.group(1)
    rest = match.group(2).strip()
    return name, (rest.split() if rest else [])


def read_plan_actions(plan_path: Path) -> list[tuple[str, list[str]]]:
    if not plan_path.exists():
        return []
    actions: list[tuple[str, list[str]]] = []
    for line in plan_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parsed = parse_sexp_plan_line(line)
        if parsed is not None:
            actions.append(parsed)
    return actions


def _dir_from_coords(src: str, dst: str) -> str | None:
    match_src = re.fullmatch(r"c_(\d+)_(\d+)", src)
    match_dst = re.fullmatch(r"c_(\d+)_(\d+)", dst)
    if not (match_src and match_dst):
        return None
    r1, c1 = int(match_src.group(1)), int(match_src.group(2))
    r2, c2 = int(match_dst.group(1)), int(match_dst.group(2))
    delta = (r2 - r1, c2 - c1)
    mapping = {
        (-1, 0): "up",
        (1, 0): "down",
        (0, -1): "left",
        (0, 1): "right",
    }
    return mapping.get(delta)


def to_direction_tokens(actions: list[tuple[str, list[str]]]) -> list[str]:
    tokens: list[str] = []
    for name, args in actions:
        lower_name = name.lower()
        if lower_name in IGNORED_ACTION_NAMES:
            continue
        if lower_name.startswith("fa") or "__forced__" in lower_name:
            continue
        direction = None
        if len(args) >= 3:
            direction = _dir_from_coords(args[1], args[2])
        if direction is None and len(args) >= 2:
            direction = _dir_from_coords(args[0], args[1])
        if direction is not None:
            tokens.append(direction)
    return tokens


def write_direction_plan(path: Path, tokens: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(f"({token})\n" for token in tokens)
    path.write_text(text, encoding="utf-8")


def run_plan_py(args: argparse.Namespace, current_level: Path) -> None:
    cmd = [
        sys.executable,
        str(plan_script_path()),
        "--planner",
        args.planner,
        "--domain",
        str(args.domain),
        "--problem",
        str(current_level),
        "--planner-args",
        args.planner_args,
    ]
    if args.timeout is not None:
        cmd.extend(["--timeout", str(args.timeout)])
    if args.optimal:
        cmd.append("--optimal")
    if args.fd_keep_searching:
        cmd.append("--fd-keep-searching")
    if args.stream:
        cmd.append("--stream")

    print(f"[plan] step={current_level.stem} command={' '.join(cmd)}", flush=True)
    completed = subprocess.run(cmd, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"tools/plan.py failed with exit code {completed.returncode}")


def run_stones_trace(play_plan: Path, level_path: Path, trace_out: Path) -> list[dict[str, Any]]:
    cmd = [str(stones_trace_path()), str(play_plan), str(level_path)]
    completed = subprocess.run(
        cmd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"stones_trace failed with exit code {completed.returncode}: "
            f"{(completed.stderr or completed.stdout).strip()}"
        )
    trace_out.parent.mkdir(parents=True, exist_ok=True)
    trace_out.write_text(completed.stdout, encoding="utf-8")

    states: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        states.append(json.loads(stripped))
    if not states:
        raise RuntimeError("stones_trace returned no states")
    return states


def reconstruct_level(previous: LevelData, final_state: dict[str, Any]) -> LevelData:
    total_cells = previous.rows * previous.cols
    agent_index = int(final_state["agent"])
    if agent_index < 0 or agent_index >= total_cells:
        raise ValueError(f"Trace reported invalid agent index {agent_index}")

    gems = {int(v) for v in final_state.get("gems", [])}
    stones = {int(v) for v in final_state.get("stones", [])}
    dirt = {int(v) for v in final_state.get("dirt", [])}
    falling_gems = {int(v) for v in final_state.get("falling_gems", [])}
    falling_stones = {int(v) for v in final_state.get("falling_stones", [])}

    cell_ids: list[int] = []
    for idx in range(total_cells):
        base_id = previous.cell_ids[idx]
        if idx == agent_index:
            cell_ids.append(9 if base_id in {7, 8} else 0)
            continue
        if idx in falling_stones:
            cell_ids.append(4)
            continue
        if idx in stones:
            cell_ids.append(3)
            continue
        if idx in falling_gems:
            cell_ids.append(6)
            continue
        if idx in gems:
            cell_ids.append(5)
            continue
        if idx in dirt:
            cell_ids.append(2)
            continue
        if base_id in BRICK_IDS:
            cell_ids.append(base_id)
            continue
        cell_ids.append(1)

    return LevelData(
        rows=previous.rows,
        cols=previous.cols,
        max_time=previous.max_time,
        required_gems=previous.required_gems,
        cell_ids=tuple(cell_ids),
    )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Repeatedly run tools/plan.py on a level, replay the resulting plan in "
            "stones_trace, and use the resulting board as the next start state."
        )
    )
    parser.add_argument("--domain", required=True, type=Path, help="PDDL domain passed through to tools/plan.py")
    parser.add_argument("--problem", required=True, type=Path, help="Initial level .txt used as the first planning problem")
    parser.add_argument("--planner", choices=["ff", "fd"], default="fd")
    parser.add_argument("--planner-args", default="", help="Passed through to tools/plan.py")
    parser.add_argument("--timeout", type=int, default=None)
    parser.add_argument("--optimal", action="store_true", help="FD only: pass through to tools/plan.py")
    parser.add_argument("--fd-keep-searching", action="store_true", help="FD only: pass through to tools/plan.py")
    parser.add_argument("--stream", action="store_true", help="Pass through to tools/plan.py")
    parser.add_argument("--iterations", type=int, default=50, help="Maximum number of planning iterations")
    parser.add_argument(
        "--run-name",
        default="",
        help="Prefix for generated state files. Defaults to <problem-stem>_replan.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directory for generated state files, traces, combined plan, and summary JSON.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    args.domain = args.domain.resolve()
    args.problem = args.problem.resolve()

    if args.problem.suffix.lower() != ".txt":
        raise SystemExit("--problem must be a .txt level file for this wrapper.")

    if not args.domain.exists():
        raise SystemExit(f"Domain file not found: {args.domain}")
    if not args.problem.exists():
        raise SystemExit(f"Problem file not found: {args.problem}")
    if not plan_script_path().exists():
        raise SystemExit(f"Missing tools/plan.py at {plan_script_path()}")
    if not stones_trace_path().exists():
        raise SystemExit(
            f"Missing stones_trace at {stones_trace_path()}. "
            "Build it with: cmake --build stonesandgem/build --target stones_trace"
        )

    initial_level_text = read_level_text(args.problem)
    initial_level = parse_level_string(initial_level_text)
    validate_reconstructible(initial_level, args.problem)

    run_name = args.run_name or f"{args.problem.stem}_replan"
    out_dir = args.out_dir.resolve() if args.out_dir else (repo_root() / "plans" / "replan" / run_name)
    if out_dir.exists():
        raise SystemExit(f"Output directory already exists: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=False)
    trace_dir = out_dir / "traces"
    state_dir = out_dir / "states"
    state_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)

    current_level_path = state_dir / f"{run_name}_step_000.txt"
    current_level_path.write_text(render_level_string(initial_level) + "\n", encoding="utf-8")

    combined_direction_tokens: list[str] = []
    iteration_summaries: list[IterationSummary] = []
    stop_reason = "max-iterations"

    for iteration in range(args.iterations):
        current_level_text = read_level_text(current_level_path)
        current_level = parse_level_string(current_level_text)
        validate_reconstructible(current_level, current_level_path)

        run_plan_py(args, current_level_path)

        problem_stem = current_level_path.stem
        plan_dir = repo_root() / "plans" / problem_stem
        plan_name = "ff" if args.planner == "ff" else ("fd-opt" if args.optimal else "fd")
        plan_path = plan_dir / f"{plan_name}.plan"
        if not plan_path.exists():
            stop_reason = "missing-plan-file"
            iteration_summaries.append(
                IterationSummary(
                    iteration=iteration,
                    input_level=str(current_level_path),
                    output_level=None,
                    plan_dir=str(plan_dir),
                    raw_actions=0,
                    direction_actions=0,
                    gems_remaining=None,
                    stop_reason=stop_reason,
                )
            )
            break

        raw_actions = read_plan_actions(plan_path)
        direction_tokens = to_direction_tokens(raw_actions)
        if not raw_actions or not direction_tokens:
            stop_reason = "no-plan"
            iteration_summaries.append(
                IterationSummary(
                    iteration=iteration,
                    input_level=str(current_level_path),
                    output_level=None,
                    plan_dir=str(plan_dir),
                    raw_actions=len(raw_actions),
                    direction_actions=len(direction_tokens),
                    gems_remaining=None,
                    stop_reason=stop_reason,
                )
            )
            break

        iter_play_plan = out_dir / f"{problem_stem}.play.plan"
        write_direction_plan(iter_play_plan, direction_tokens)
        combined_direction_tokens.extend(direction_tokens)

        trace_path = trace_dir / f"{problem_stem}.jsonl"
        states = run_stones_trace(iter_play_plan, current_level_path, trace_path)
        final_state = states[-1]
        next_level = reconstruct_level(current_level, final_state)
        next_level_text = render_level_string(next_level)
        next_level_path = state_dir / f"{run_name}_step_{iteration + 1:03}.txt"
        next_level_path.write_text(next_level_text + "\n", encoding="utf-8")

        gems_remaining = len(final_state.get("gems", []))
        print(
            f"[state] iter={iteration} raw_actions={len(raw_actions)} "
            f"moves={len(direction_tokens)} gems_remaining={gems_remaining} "
            f"next={next_level_path}",
            flush=True,
        )

        summary_stop_reason = None
        if next_level_text == current_level_text:
            summary_stop_reason = "unchanged-state"
            stop_reason = summary_stop_reason
        elif gems_remaining == 0:
            summary_stop_reason = "no-gems-remaining"
            stop_reason = summary_stop_reason

        iteration_summaries.append(
            IterationSummary(
                iteration=iteration,
                input_level=str(current_level_path),
                output_level=str(next_level_path),
                plan_dir=str(plan_dir),
                raw_actions=len(raw_actions),
                direction_actions=len(direction_tokens),
                gems_remaining=gems_remaining,
                stop_reason=summary_stop_reason,
            )
        )

        current_level_path = next_level_path

        if summary_stop_reason is not None:
            break

    combined_plan_path = out_dir / "combined.play.plan"
    write_direction_plan(combined_plan_path, combined_direction_tokens)
    write_json(
        out_dir / "summary.json",
        {
            "run_name": run_name,
            "domain": str(args.domain),
            "initial_problem": str(args.problem),
            "planner": args.planner,
            "planner_args": args.planner_args,
            "iterations_requested": args.iterations,
            "iterations_completed": len([s for s in iteration_summaries if s.output_level is not None]),
            "stop_reason": stop_reason,
            "combined_play_plan": str(combined_plan_path),
            "final_level": str(current_level_path),
            "steps": [summary.__dict__ for summary in iteration_summaries],
        },
    )

    print(f"[done] stop_reason={stop_reason} out_dir={out_dir}", flush=True)
    print(f"[done] combined_play_plan={combined_plan_path}", flush=True)
    print(f"[done] final_level={current_level_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
