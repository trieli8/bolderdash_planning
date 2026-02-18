#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


# Make planner runner importable.
PLUS_RUNNER_DIR = repo_root() / "planners" / "pddl-plus"
sys.path.insert(0, str(PLUS_RUNNER_DIR))

from pddl_plus_runner import PlusPlanResult, TimedAction, solve as solve_plus  # type: ignore  # noqa: E402


def ensure_executable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing executable: {path}")
    mode = path.stat().st_mode
    path.chmod(mode | 0o100)


def plan_player_path() -> Path:
    return repo_root() / "stonesandgem" / "build" / "bin" / "plan_player"


def play_plan(plan_file: Path, level_file: Optional[Path]) -> Tuple[int, str, str]:
    player = plan_player_path()
    ensure_executable(player)
    cmd = [str(player), str(plan_file)]
    if level_file:
        cmd.append(str(level_file))

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def normalise_problem_name(problem: Path) -> str:
    try:
        txt = problem.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\(\s*problem\s+([^\s\)]+)\s*\)", txt, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return problem.stem


def write_plan_file(path: Path, actions: List[TimedAction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for a in actions:
        if a.args:
            lines.append(f"({a.name} {' '.join(a.args)})")
        else:
            lines.append(f"({a.name})")
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_timed_plan_file(path: Path, actions: List[TimedAction]) -> None:
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


def _dir_from_coords(src: str, dst: str) -> Optional[str]:
    m1 = re.match(r"c_(\d+)_(\d+)", src)
    m2 = re.match(r"c_(\d+)_(\d+)", dst)
    if not (m1 and m2):
        return None

    r1, c1 = int(m1.group(1)), int(m1.group(2))
    r2, c2 = int(m2.group(1)), int(m2.group(2))
    dr, dc = r2 - r1, c2 - c1

    if dr == -1 and dc == 0:
        return "up"
    if dr == 1 and dc == 0:
        return "down"
    if dr == 0 and dc == -1:
        return "left"
    if dr == 0 and dc == 1:
        return "right"
    return None


def write_direction_plan(path: Path, actions: List[TimedAction]) -> None:
    tokens: List[str] = []

    for action in actions:
        name = action.name.lower()
        args = action.args

        if name.startswith(("__forced__", "ev_", "fa_", "forced-")):
            continue

        if name in ("start_scan", "advance_scan", "end_scan"):
            continue

        if len(args) >= 3:
            direction = _dir_from_coords(args[1], args[2])
            if direction:
                tokens.append(direction)
                continue

        if len(args) >= 2:
            direction = _dir_from_coords(args[0], args[1])
            if direction:
                tokens.append(direction)
                continue

    if tokens:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(f"({t})" for t in tokens) + "\n", encoding="utf-8")


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


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


def generate_problem_from_level(level_txt: Path, problem_name: str, domain: Path, explicit_gen: Optional[Path]) -> Tuple[Path, tempfile.TemporaryDirectory]:
    gen_py = explicit_gen.resolve() if explicit_gen else select_problem_gen(domain)
    if not gen_py.exists():
        raise FileNotFoundError(f"Missing problem generator at {gen_py}")

    tmpdir = tempfile.TemporaryDirectory(prefix="gen_plus_problem_")
    out_path = Path(tmpdir.name) / f"{problem_name}.pddl"

    cmd = [sys.executable, str(gen_py), str(level_txt), "-p", problem_name]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        tmpdir.cleanup()
        raise RuntimeError(f"{gen_py.name} failed (rc={proc.returncode}): {proc.stderr or proc.stdout}")

    out_path.write_text(proc.stdout, encoding="utf-8")
    return out_path, tmpdir


def resolve_level_file_for_view(problem: Path, explicit_level: Optional[Path]) -> Optional[Path]:
    if explicit_level:
        return explicit_level.resolve()
    if problem.suffix.lower() == ".txt":
        return problem.resolve()
    candidate = problem.with_suffix(".txt")
    if candidate.exists():
        return candidate.resolve()
    fallback = repo_root() / "pddl" / "level.txt"
    return fallback.resolve() if fallback.exists() else None


def planner_tag(planner_used: str) -> str:
    if planner_used == "enhsp":
        return "plus-enhsp"
    if planner_used == "optic":
        return "plus-optic"
    if planner_used == "cmd":
        return "plus-cmd"
    return "plus"


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a PDDL+ planner and save plans under plans/<problem_name>/.")
    ap.add_argument("--domain", type=Path, help="Domain PDDL (required unless using --play-plan)")
    ap.add_argument("--problem", type=Path, help="Problem PDDL or level .txt (required unless using --play-plan)")
    ap.add_argument("--planner", choices=["auto", "enhsp", "optic", "cmd"], default="auto")
    ap.add_argument("--planner-args", default="", help="Extra args passed to the selected planner binary/jar")
    ap.add_argument("--cmd-template", default=None, help="Custom planner command template for --planner cmd; use {domain} and {problem}")
    ap.add_argument("--enhsp-jar", type=Path, default=None)
    ap.add_argument("--optic-bin", type=Path, default=None)
    ap.add_argument("--timeout", type=int, default=None)
    ap.add_argument("--stream", action="store_true", help="Stream planner output live")
    ap.add_argument("--view", action="store_true", help="Open solved play plan in plan_player")
    ap.add_argument("--play-plan", type=Path, help="Play an existing plan file and exit")
    ap.add_argument("--play-level", type=Path, help="Optional level file for plan_player")
    ap.add_argument("--problem-gen", type=Path, default=None, help="Override problem generator script when --problem is a .txt level")
    args = ap.parse_args()

    if args.play_plan:
        plan_file = args.play_plan.resolve()
        level_file = args.play_level.resolve() if args.play_level else None
        try:
            rc, out, err = play_plan(plan_file, level_file)
            if out:
                sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            return rc
        except Exception as exc:
            print(f"[ERR] Failed to launch plan_player: {exc}", file=sys.stderr)
            return 1

    if not args.domain or not args.problem:
        print("Error: --domain and --problem are required unless using --play-plan.", file=sys.stderr)
        return 2

    domain = args.domain.resolve()
    input_problem = args.problem.resolve()

    if not domain.exists():
        print(f"Domain file not found: {domain}", file=sys.stderr)
        return 2

    problem = input_problem
    temp_problem_dir: Optional[tempfile.TemporaryDirectory] = None

    if problem.suffix.lower() == ".txt":
        try:
            problem, temp_problem_dir = generate_problem_from_level(
                level_txt=problem,
                problem_name=problem.stem,
                domain=domain,
                explicit_gen=args.problem_gen,
            )
            print(f"[INFO] Generated PDDL problem from {input_problem} -> {problem}")
        except Exception as exc:
            print(f"[ERR] Failed to generate PDDL problem from {problem}: {exc}", file=sys.stderr)
            return 1

    if not problem.exists():
        print(f"Problem file not found: {problem}", file=sys.stderr)
        return 2

    problem_name = normalise_problem_name(problem)
    out_dir = repo_root() / "plans" / problem_name

    try:
        result: PlusPlanResult = solve_plus(
            domain=domain,
            problem=problem,
            planner=args.planner,
            timeout=args.timeout,
            stream=args.stream,
            planner_args=args.planner_args,
            cmd_template=args.cmd_template,
            enhsp_jar=args.enhsp_jar.resolve() if args.enhsp_jar else None,
            optic_bin=args.optic_bin.resolve() if args.optic_bin else None,
        )

        # ENHSP currently fails to solve the fully autonomous autoscan variant.
        # If user asked to view, retry with the stable domain so visualization
        # still works from the same command.
        if (
            args.view
            and result.status == "unsolved"
            and "autoscan" in domain.name.lower()
        ):
            fallback_domain = domain.with_name("domain_plus_from_domain.pddl")
            if fallback_domain.exists():
                print(
                    f"[WARN] {domain.name} returned unsolved with ENHSP; retrying with {fallback_domain.name} for visualization."
                )
                result = solve_plus(
                    domain=fallback_domain,
                    problem=problem,
                    planner=args.planner,
                    timeout=args.timeout,
                    stream=args.stream,
                    planner_args=args.planner_args,
                    cmd_template=args.cmd_template,
                    enhsp_jar=args.enhsp_jar.resolve() if args.enhsp_jar else None,
                    optic_bin=args.optic_bin.resolve() if args.optic_bin else None,
                )
    except Exception as exc:
        print(f"[ERR] PDDL+ planner execution failed: {exc}", file=sys.stderr)
        if temp_problem_dir is not None:
            temp_problem_dir.cleanup()
        return 1

    tag = planner_tag(result.planner)
    plan_path = out_dir / f"{tag}.plan"
    timed_path = out_dir / f"{tag}.timed.plan"
    play_path = out_dir / f"{tag}.play.plan"

    write_plan_file(plan_path, result.actions)
    write_timed_plan_file(timed_path, result.actions)
    write_direction_plan(play_path, result.actions)
    write_text_file(out_dir / f"{tag}.stdout.txt", result.raw_stdout)
    write_text_file(out_dir / f"{tag}.stderr.txt", result.raw_stderr)

    print("\n== Summary ==")
    print(f"- planner: {result.planner}")
    print(f"- status: {result.status}")
    print(f"- actions: {len(result.actions)}")
    print(f"- time: {result.metrics.get('time_sec')}s")
    print(f"\nPlans saved under: {out_dir}")

    if args.view and result.status == "solved" and play_path.exists():
        level_file = resolve_level_file_for_view(input_problem, args.play_level)
        try:
            print(f"[PLAY] Launching plan_player with {play_path}" + (f" and level {level_file}" if level_file else ""))
            rc, out, err = play_plan(play_path, level_file)
            if out:
                sys.stdout.write(out)
            if err:
                sys.stderr.write(err)
            if rc != 0:
                print(f"[WARN] plan_player exited with code {rc}", file=sys.stderr)
        except Exception as exc:
            print(f"[WARN] Could not launch plan_player: {exc}", file=sys.stderr)

    if temp_problem_dir is not None:
        temp_problem_dir.cleanup()

    return 0 if result.status in ("solved", "unsolved") else 1


if __name__ == "__main__":
    raise SystemExit(main())
