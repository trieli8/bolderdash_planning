#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple


SEARCH_CHOICES = [
    "astar",
    "bfs",
    "bfws1",
    "bfws2",
    "bfws1-rx",
    "bfws2-rx",
    "dq-bfws1-rx",
    "dq-bfws2-rx",
    "alt-bfws1",
    "alt-bfws2",
    "gbfs",
    "iw1",
    "iw1gc",
    "iw2",
    "iw2gc",
    "lazy",
    "lazy-po",
    "lazy-prune",
]

EVALUATOR_CHOICES = ["blind", "goalcount", "add", "hmax", "ff", "rff"]

GENERATOR_CHOICES = [
    "yannakakis",
    "join",
    "random_join",
    "ordered_join",
    "full_reducer",
    "clique_bk",
    "clique_kckp",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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


def run_cmd_capture(cmd: List[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_cmd_stream(cmd: List[str], cwd: Optional[Path] = None, prefix: str = "") -> Tuple[int, str, str]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    out_lines: List[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        out_lines.append(line)
        if prefix:
            sys.stdout.write(f"{prefix}{line}")
        else:
            sys.stdout.write(line)
        sys.stdout.flush()
    rc = proc.wait()
    return rc, "".join(out_lines), ""


def normalise_problem_name(problem: Path) -> str:
    try:
        txt = problem.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\(\s*problem\s+([^\s\)]+)\s*\)", txt, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return problem.stem


def write_plan_file(path: Path, actions: List[Tuple[str, List[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    for name, args in actions:
        if args:
            lines.append(f"({name} {' '.join(args)})")
        else:
            lines.append(f"({name})")
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


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


def write_direction_plan(path: Path, actions: List[Tuple[str, List[str]]]) -> None:
    tokens: List[str] = []
    for name, args in actions:
        n = name.lower()
        if n.startswith(("__forced__", "ev_", "fa_", "forced-")):
            continue
        if len(args) >= 3:
            d = _dir_from_coords(args[1], args[2])
            if d:
                tokens.append(d)
                continue
        if len(args) >= 2:
            d = _dir_from_coords(args[0], args[1])
            if d:
                tokens.append(d)
                continue
    if tokens:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(f"({t})" for t in tokens) + "\n", encoding="utf-8")


def select_problem_gen(domain: Path) -> Path:
    domain_name = domain.name.lower()
    root = repo_root()
    if "scanner_separated" in domain_name or "scaner_separated" in domain_name:
        return root / "pddl" / "problem_gen_scanner_separated.py"
    return root / "pddl" / "problem_gen.py"


def generate_problem_from_level(level_txt: Path, problem_name: str, domain: Path, explicit_gen: Optional[Path]) -> Tuple[Path, tempfile.TemporaryDirectory]:
    gen_py = explicit_gen.resolve() if explicit_gen else select_problem_gen(domain)
    if not gen_py.exists():
        raise FileNotFoundError(f"Missing problem generator at {gen_py}")
    tmpdir = tempfile.TemporaryDirectory(prefix="gen_lifted_problem_")
    out_path = Path(tmpdir.name) / f"{problem_name}.pddl"
    cmd = [sys.executable, str(gen_py), str(level_txt), "-p", problem_name]
    rc, out, err = run_cmd_capture(cmd, cwd=Path(tmpdir.name))
    if rc != 0:
        tmpdir.cleanup()
        raise RuntimeError(f"{gen_py.name} failed (rc={rc}): {err or out}")
    # Keep our canonical copy at out_path even if generator already wrote one.
    out_path.write_text(out, encoding="utf-8")
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


def parse_powerlifted_plan(path: Path) -> List[Tuple[str, List[str]]]:
    actions: List[Tuple[str, List[str]]] = []
    if not path.exists():
        return actions

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if re.match(r"^\d+\s*:\s*", line):
            line = re.sub(r"^\d+\s*:\s*", "", line)
        m = re.search(r"\(\s*([^\s()]+)(.*?)\)", line)
        if not m:
            continue
        name = m.group(1)
        rest = m.group(2).strip()
        args = rest.split() if rest else []
        actions.append((name, args))
    return actions


def solve_with_lifted(
    domain: Path,
    problem: Path,
    search: str,
    evaluator: str,
    generator: str,
    time_limit: Optional[int],
    seed: int,
    build: bool,
    debug: bool,
    cxx_compiler: str,
    unit_cost: bool,
    only_effects_novelty_check: bool,
    novelty_early_stop: bool,
    planner_args: str,
    stream: bool,
) -> Tuple[str, List[Tuple[str, List[str]]], str, str, dict]:
    root = repo_root()
    runner = root / "planners" / "powerlifted" / "powerlifted.py"
    if not runner.exists():
        raise FileNotFoundError(f"Powerlifted entrypoint not found: {runner}")

    start = time.time()
    with tempfile.TemporaryDirectory(prefix="lifted_run_") as td:
        td_path = Path(td)
        raw_plan_path = td_path / "plan.powerlifted"

        cmd: List[str] = [
            sys.executable,
            str(runner),
            "-d",
            str(domain),
            "-i",
            str(problem),
            "-s",
            search,
            "-e",
            evaluator,
            "-g",
            generator,
            "--seed",
            str(seed),
            "--plan-file",
            str(raw_plan_path),
            "--translator-output-file",
            str(td_path / "output.lifted"),
        ]

        if time_limit is not None:
            cmd.extend(["--time-limit", str(time_limit)])
        if build:
            cmd.append("--build")
        if debug:
            cmd.append("--debug")
        if cxx_compiler:
            cmd.extend(["--cxx-compiler", cxx_compiler])
        if unit_cost:
            cmd.append("--unit-cost")
        if only_effects_novelty_check:
            cmd.append("--only-effects-novelty-check")
        if novelty_early_stop:
            cmd.append("--novelty-early-stop")
        if planner_args.strip():
            cmd.extend(shlex.split(planner_args))

        if stream:
            rc, out, err = run_cmd_stream(cmd, cwd=td_path, prefix="[LIFTED] ")
        else:
            rc, out, err = run_cmd_capture(cmd, cwd=td_path)

        actions = parse_powerlifted_plan(raw_plan_path)
        raw_plan_text = raw_plan_path.read_text(encoding="utf-8", errors="replace") if raw_plan_path.exists() else ""

    lower_out = (out + "\n" + err).lower()
    solved = (
        rc == 0
        or "solution found" in lower_out
        or "goal found at:" in lower_out
        or "plan length:" in lower_out
    )
    timed_out = rc == 23 or "ran out of time" in lower_out or (
        rc == 255 and ("time" in lower_out and ("out" in lower_out or "limit" in lower_out))
    )

    if solved:
        status = "solved"
    elif timed_out:
        status = "timeout"
    elif rc in (11, 12, 22, 23, 255):
        status = "unsolved"
    else:
        status = "error"

    metrics = {
        "returncode": rc,
        "time_sec": round(time.time() - start, 3),
    }
    return status, actions, out, err, {"metrics": metrics, "raw_plan_text": raw_plan_text}


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Powerlifted and save plans under plans/<problem_name>/.")
    ap.add_argument("--domain", type=Path, help="Domain PDDL (required unless using --play-plan)")
    ap.add_argument("--problem", type=Path, help="Problem PDDL or level .txt (required unless using --play-plan)")
    ap.add_argument("--search", choices=SEARCH_CHOICES, default="alt-bfws1")
    ap.add_argument("--evaluator", choices=EVALUATOR_CHOICES, default="ff")
    ap.add_argument("--generator", choices=GENERATOR_CHOICES, default="yannakakis")
    ap.add_argument("--time-limit", type=int, default=None, help="Powerlifted time limit in seconds.")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--build", action="store_true", help="Build Powerlifted before running.")
    ap.add_argument("--debug", action="store_true", help="Use debug Powerlifted build.")
    ap.add_argument("--cxx-compiler", default="default", help="C++ compiler passed to Powerlifted.")
    ap.add_argument("--unit-cost", action="store_true")
    ap.add_argument("--only-effects-novelty-check", action="store_true")
    ap.add_argument("--novelty-early-stop", action="store_true")
    ap.add_argument("--planner-args", default="", help="Additional raw args passed to powerlifted.py")
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
        status, actions, out, err, extra = solve_with_lifted(
            domain=domain,
            problem=problem,
            search=args.search,
            evaluator=args.evaluator,
            generator=args.generator,
            time_limit=args.time_limit,
            seed=args.seed,
            build=args.build,
            debug=args.debug,
            cxx_compiler=args.cxx_compiler,
            unit_cost=args.unit_cost,
            only_effects_novelty_check=args.only_effects_novelty_check,
            novelty_early_stop=args.novelty_early_stop,
            planner_args=args.planner_args,
            stream=args.stream,
        )
    except Exception as exc:
        print(f"[ERR] Lifted planner execution failed: {exc}", file=sys.stderr)
        if temp_problem_dir is not None:
            temp_problem_dir.cleanup()
        return 1

    plan_path = out_dir / "lifted.plan"
    raw_plan_path = out_dir / "lifted.raw.plan"
    play_path = out_dir / "lifted.play.plan"

    write_plan_file(plan_path, actions)
    write_text_file(raw_plan_path, extra["raw_plan_text"])
    write_direction_plan(play_path, actions)
    write_text_file(out_dir / "lifted.stdout.txt", out)
    write_text_file(out_dir / "lifted.stderr.txt", err)

    print("\n== Summary ==")
    print("- planner: powerlifted")
    print(f"- status: {status}")
    print(f"- actions: {len(actions)}")
    print(f"- time: {extra['metrics'].get('time_sec')}s")
    print(f"\nPlans saved under: {out_dir}")

    if args.view and status == "solved" and play_path.exists():
        level_file = resolve_level_file_for_view(input_problem, args.play_level)
        try:
            print(f"[PLAY] Launching plan_player with {play_path}" + (f" and level {level_file}" if level_file else ""))
            rc, out_play, err_play = play_plan(play_path, level_file)
            if out_play:
                sys.stdout.write(out_play)
            if err_play:
                sys.stderr.write(err_play)
            if rc != 0:
                print(f"[WARN] plan_player exited with code {rc}", file=sys.stderr)
        except Exception as exc:
            print(f"[WARN] Could not launch plan_player: {exc}", file=sys.stderr)

    if temp_problem_dir is not None:
        temp_problem_dir.cleanup()

    return 0 if status in ("solved", "unsolved", "timeout") else 1


if __name__ == "__main__":
    raise SystemExit(main())
