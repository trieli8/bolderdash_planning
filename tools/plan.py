#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any


# -----------------------------
# Data model
# -----------------------------

@dataclasses.dataclass
class PlanResult:
    planner: str
    domain: str
    problem: str
    status: str  # solved | unsolved | timeout | error
    actions: List[Tuple[str, List[str]]]
    raw_stdout: str
    raw_stderr: str
    metrics: Dict[str, Any]


# -----------------------------
# Repo helpers
# -----------------------------

def repo_root() -> Path:
    # tools/plan.py -> repo root is two levels up
    return Path(__file__).resolve().parents[1]


def ensure_executable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing executable: {path}")
    mode = path.stat().st_mode
    # add u+x
    path.chmod(mode | 0o100)


def plan_player_path() -> Path:
    return repo_root() / "stonesandgem" / "build" / "bin" / "plan_player"


def play_plan(plan_file: Path, level_file: Optional[Path]) -> Tuple[int, str, str]:
    """
    Invoke the C++ plan_player GUI with a plan file (and optional level).
    """
    player = plan_player_path()
    ensure_executable(player)
    cmd = [str(player), str(plan_file)]
    if level_file:
        cmd.append(str(level_file))
    return run_cmd_capture(cmd)


# -----------------------------
# Streaming / running commands
# -----------------------------

def run_cmd_capture(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_sec: Optional[int] = None,
) -> Tuple[int, str, str]:
    """
    Run and capture stdout/stderr. Raises subprocess.TimeoutExpired on timeout.
    """
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec,
    )
    return p.returncode, p.stdout, p.stderr


def run_cmd_stream(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_sec: Optional[int] = None,
    prefix: str = "",
) -> Tuple[int, str, str]:
    """
    Run and stream output to terminal while also capturing it.
    Uses combined stdout/stderr for simplicity but returns separated buffers
    (stderr will be empty, combined goes to stdout buffer).
    """
    start = time.time()
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

    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            out_lines.append(line)
            if prefix:
                sys.stdout.write(f"{prefix}{line}")
            else:
                sys.stdout.write(line)
            sys.stdout.flush()

            if timeout_sec is not None and (time.time() - start) > timeout_sec:
                proc.kill()
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout_sec)

        rc = proc.wait()
        out = "".join(out_lines)
        return rc, out, ""  # stderr is merged into stdout

    except subprocess.TimeoutExpired:
        # ensure process is gone
        try:
            proc.kill()
        except Exception:
            pass
        raise


# -----------------------------
# Output + parsing helpers
# -----------------------------

def normalise_problem_name(problem: Path) -> str:
    """
    Prefer problem 'PROBNAME' inside the PDDL if present, else file stem.
    """
    try:
        txt = problem.read_text(encoding="utf-8", errors="replace")
        # (define (problem NAME) ...)
        m = re.search(r"\(\s*problem\s+([^\s\)]+)\s*\)", txt, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return problem.stem


def write_plan_file(path: Path, actions: List[Tuple[str, List[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for (name, args) in actions:
        if args:
            lines.append(f"({name} {' '.join(args)})")
        else:
            lines.append(f"({name})")
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


def write_direction_plan(path: Path, actions: List[Tuple[str, List[str]]]) -> None:
    """
    Write a plan in the simple token format that plan_player understands.
    Looks for actions with coordinates like c_r_c and converts to up/down/left/right.
    """
    tokens: List[str] = []
    for name, args in actions:
        if name.lower()[0:2] == "fa" or "__forced__" in name.lower():
            continue
        if len(args) >= 3:
            direction = _dir_from_coords(args[1], args[2])
            if direction:
                tokens.append(direction)
                continue
    if tokens:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(f"({t})" for t in tokens) + "\n", encoding="utf-8")

def write_text_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text or "", encoding="utf-8")


def parse_sexp_action(s: str) -> Optional[Tuple[str, List[str]]]:
    """
    Parse a single FF action line like:
      (FORCED__LOAD-TRUCK OBJ23 TRU2 POS2)
    """
    s = s.strip()
    if not (s.startswith("(") and s.endswith(")")):
        return None
    inner = s[1:-1].strip()
    if not inner:
        return None
    parts = inner.split()
    return parts[0], parts[1:]


def _find_fd_plan_files(workdir: Path) -> List[Path]:
    # Typical Fast Downward outputs: sas_plan, sas_plan.1, sas_plan.2 ...
    patterns = ["sas_plan*", "plan*", "*.plan"]
    found: List[Path] = []
    for pat in patterns:
        for p in workdir.glob(pat):
            if p.is_file():
                found.append(p)
    # dedupe + sort by mtime
    uniq = {p.resolve(): p for p in found}
    found = list(uniq.values())
    found.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0)
    return found


def _parse_fd_plan_file(plan_path: Path) -> List[Tuple[str, List[str]]]:
    """
    Parse FD plan file (sas_plan*):
      (move a b)
    Comments start with ';'
    """
    actions: List[Tuple[str, List[str]]] = []
    if not plan_path.exists():
        return actions

    for line in plan_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        m = re.match(r"^\(\s*([^\s()]+)(.*?)\)\s*$", line)
        if not m:
            continue
        name = m.group(1)
        rest = m.group(2).strip()
        args = rest.split() if rest else []
        actions.append((name, args))
    return actions


# -----------------------------
# Planners
# -----------------------------

def solve_with_ff(domain: Path, problem: Path, timeout: int | None, stream: bool) -> PlanResult:
    root = repo_root()
    ff_bin = root / "planners" / "forced-action-ff" / "ff"
    ensure_executable(ff_bin)

    start = time.time()

    with tempfile.TemporaryDirectory(prefix="ff_run_") as td:
        td_path = Path(td)
        dname = "domain.pddl"
        pname = "problem.pddl"
        shutil.copy2(domain, td_path / dname)
        shutil.copy2(problem, td_path / pname)
        
        pdir = str(td_path) + os.sep  # IMPORTANT: FF concatenates -p + filename
        cmd = [str(ff_bin), "-p", pdir, "-o", dname, "-f", pname]

        try:
            if stream:
                rc, out, err = run_cmd_stream(cmd, cwd=td_path, timeout_sec=timeout, prefix="[FF] ")
            else:
                rc, out, err = run_cmd_capture(cmd, cwd=td_path, timeout_sec=timeout)
        except subprocess.TimeoutExpired:
            return PlanResult(
                planner="ff",
                domain=str(domain),
                problem=str(problem),
                status="timeout",
                actions=[],
                raw_stdout="",
                raw_stderr="",
                metrics={"returncode": None, "time_sec": round(time.time() - start, 3)},
            )

        actions: List[Tuple[str, List[str]]] = []

        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue

            # Format A: "0: (ACTION ...)"
            m = re.match(r"^\s*\d+\s*:\s*(\(.+\))\s*$", line)
            if m:
                parsed = parse_sexp_action(m.group(1))
                if parsed:
                    actions.append(parsed)
                continue

            # Format B: "step 0: ACTION ARG1 ARG2 ..."
            m2 = re.match(r"^(?:step\s*)?\d+\s*:\s*([A-Za-z0-9_+-]+)(?:\s+(.*))?$", line, re.IGNORECASE)
            if m2:
                name = m2.group(1).lower()
                rest = (m2.group(2) or "").strip()
                args = rest.split() if rest else []
                actions.append((name, args))
                continue

            # Format C: "step    0: ACTION ..." (extra spacing)
            m3 = re.match(r"^step\s+\d+\s*:\s*([A-Za-z0-9_+-]+)(?:\s+(.*))?$", line, re.IGNORECASE)
            if m3:
                name = m3.group(1).lower()
                rest = (m3.group(2) or "").strip()
                args = rest.split() if rest else []
                actions.append((name, args))
                continue

    status = "solved" if actions else ("unsolved" if rc == 0 else "error")
    if "found legal plan" in out.lower():
        status = "solved"

    return PlanResult(
        planner="ff",
        domain=str(domain),
        problem=str(problem),
        status=status,
        actions=actions,
        raw_stdout=out,
        raw_stderr=err,
        metrics={"returncode": rc, "time_sec": round(time.time() - start, 3)},
    )


def solve_with_fd(
    domain: Path,
    problem: Path,
    timeout: int | None,
    optimal: bool,
    stream: bool,
    keep_searching: bool = False,
) -> PlanResult:
    root = repo_root()
    fd_py = root / "planners" / "fast-downward" / "fast-downward.py"
    if not fd_py.exists():
        raise FileNotFoundError(f"Missing Fast Downward entrypoint: {fd_py}")

    start = time.time()

    with tempfile.TemporaryDirectory(prefix="fd_run_") as td:
        td_path = Path(td)

        if optimal:
            # Optimal: A* with IPDB heuristic (handles ADL after compilation better than lmcut alias).
            cmd = [sys.executable, str(fd_py), str(domain), str(problem),
                   "--search", "astar(ipdb())"]
            tag = "fd-opt"
        else:
            # Satisficing: default stops after first plan; optionally run an anytime loop.
            if keep_searching:
                search = "iterated([lazy_greedy([ff()], preferred=[ff()])], repeat_last=true)"
                tag = "fd-any"
            else:
                search = "lazy_greedy([ff()], preferred=[ff()])"
                tag = "fd"
            cmd = [sys.executable, str(fd_py), str(domain), str(problem), "--search", search]

        try:
            if stream:
                rc, out, err = run_cmd_stream(cmd, cwd=td_path, timeout_sec=timeout, prefix="[FD] ")
            else:
                rc, out, err = run_cmd_capture(cmd, cwd=td_path, timeout_sec=timeout)
        except subprocess.TimeoutExpired:
            plan_files = _find_fd_plan_files(td_path)
            actions = _parse_fd_plan_file(plan_files[-1]) if plan_files else []
            return PlanResult(
                planner=tag,
                domain=str(domain),
                problem=str(problem),
                status="timeout",
                actions=actions,
                raw_stdout="",
                raw_stderr="",
                metrics={
                    "returncode": None,
                    "time_sec": round(time.time() - start, 3),
                    "plan_file": str(plan_files[-1]) if plan_files else None,
                },
            )

        plan_files = _find_fd_plan_files(td_path)
        actions = _parse_fd_plan_file(plan_files[-1]) if plan_files else []
        status = "solved" if actions else ("unsolved" if rc == 0 else "error")

        return PlanResult(
            planner=tag,
            domain=str(domain),
            problem=str(problem),
            status=status,
            actions=actions,
            raw_stdout=out,
            raw_stderr=err,
            metrics={
                "returncode": rc,
                "time_sec": round(time.time() - start, 3),
                "plan_file": str(plan_files[-1]) if plan_files else None,
                "num_plan_files": len(plan_files),
            },
        )


# -----------------------------
# CLI main
# -----------------------------

def generate_problem_from_level(
    level_txt: Path, problem_name: str
) -> Tuple[Path, tempfile.TemporaryDirectory]:
    """
    Use pddl/problem_gen.py to generate a PDDL problem from a level text file.
    Returns (pddl_path, tempdir) so caller can keep tempdir alive.
    """
    gen_py = repo_root() / "pddl" / "problem_gen.py"
    if not gen_py.exists():
        raise FileNotFoundError(f"Missing problem_gen.py at {gen_py}")
    tmpdir = tempfile.TemporaryDirectory(prefix="gen_problem_")
    out_path = Path(tmpdir.name) / f"{problem_name}.pddl"
    cmd = [sys.executable, str(gen_py), str(level_txt), "-p", problem_name]
    rc, out, err = run_cmd_capture(cmd)
    if rc != 0:
        tmpdir.cleanup()
        raise RuntimeError(f"problem_gen.py failed (rc={rc}): {err or out}")
    out_path.write_text(out, encoding="utf-8")
    return out_path, tmpdir

def main() -> int:
    ap = argparse.ArgumentParser(description="Run planners and save plans under plans/<problem_name>/, or play back an existing plan.")
    ap.add_argument("--domain", type=Path, help="Domain PDDL (required unless using --play-plan)")
    ap.add_argument("--problem", type=Path, help="Problem PDDL (required unless using --play-plan)")
    ap.add_argument("--planner", choices=["ff", "fd", "both"], default="fd")
    ap.add_argument("--timeout", type=int, default=None)
    ap.add_argument("--optimal", action="store_true", help="FD only: attempt optimal planning (alias seq-opt-lmcut)")
    ap.add_argument("--fd-keep-searching", action="store_true", help="FD only: keep searching for better solutions until timeout using iterated greedy search")
    ap.add_argument("--stream", action="store_true", help="Stream planner output live to terminal")
    ap.add_argument("--play-plan", type=Path, help="Play an existing plan file with the plan_player GUI and exit.")
    ap.add_argument("--play-level", type=Path, help="Optional level file to pass to plan_player.")
    ap.add_argument("--play-output", action="store_true", help="After planning, open the first solved plan in plan_player.")
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
        except Exception as e:
            print(f"[ERR] Failed to launch plan_player: {e}", file=sys.stderr)
            return 1

    if not args.domain or not args.problem:
        print("Error: --domain and --problem are required unless using --play-plan.", file=sys.stderr)
        return 2

    domain = args.domain.resolve()
    problem = args.problem.resolve()

    # If a level .txt is passed as the "problem", generate a PDDL problem via problem_gen.
    temp_problem_dir: Optional[tempfile.TemporaryDirectory] = None
    if problem.suffix.lower() == ".txt":
        problem_name = problem.stem
        try:
            problem, temp_problem_dir = generate_problem_from_level(problem, problem_name)
            level_file = problem
            print(f"[INFO] Generated PDDL problem from {args.problem} -> {problem}")
        except Exception as e:
            print(f"[ERR] Failed to generate PDDL problem from {problem}: {e}", file=sys.stderr)
            return 1
    else:
        problem_name = normalise_problem_name(problem)

    if not domain.exists():
        print(f"Domain file not found: {domain}", file=sys.stderr)
        return 2
    if not problem.exists():
        print(f"Problem file not found: {problem}", file=sys.stderr)
        return 2

    if problem.suffix.lower() != ".txt":
        problem_name = normalise_problem_name(problem)
    out_dir = repo_root() / "plans" / problem_name

    results: List[PlanResult] = []

    play_candidates: List[Path] = []

    if args.planner in ("ff", "both"):
        r = solve_with_ff(domain, problem, timeout=args.timeout, stream=args.stream)
        results.append(r)

        ff_plan_path = out_dir / "ff.plan"
        write_plan_file(ff_plan_path, r.actions)
        if r.actions:
            write_direction_plan(out_dir / "ff.play.plan", r.actions)
        write_text_file(out_dir / "ff.stdout.txt", r.raw_stdout)
        write_text_file(out_dir / "ff.stderr.txt", r.raw_stderr)
        if r.status == "solved" and r.actions:
            play_candidates.append(ff_plan_path)

    if args.planner in ("fd", "both"):
        r = solve_with_fd(
            domain,
            problem,
            timeout=args.timeout,
            optimal=args.optimal,
            stream=args.stream,
            keep_searching=args.fd_keep_searching,
        )
        results.append(r)

        fd_name = "fd-opt" if args.optimal else "fd"
        fd_plan_path = out_dir / f"{fd_name}.plan"
        write_plan_file(fd_plan_path, r.actions)
        if r.actions:
            write_direction_plan(out_dir / f"{fd_name}.play.plan", r.actions)
        write_text_file(out_dir / f"{fd_name}.stdout.txt", r.raw_stdout)
        write_text_file(out_dir / f"{fd_name}.stderr.txt", r.raw_stderr)
        if r.status == "solved" and r.actions:
            play_candidates.append(fd_plan_path)

    # Summary
    print("\n== Summary ==")
    for r in results:
        print(f"- {r.planner}: {r.status}  (actions={len(r.actions)})  time={r.metrics.get('time_sec')}s")
        if "plan_file" in r.metrics and r.metrics["plan_file"]:
            print(f"    fd plan source: {r.metrics['plan_file']}")

    print(f"\nPlans saved under: {out_dir}")

    if args.play_output and play_candidates:
        plan_file = play_candidates[0]
        plan_play_file = out_dir / f"{plan_file.stem}.play.plan"
        if plan_play_file.exists():
            problem = args.problem.resolve()
            if problem.suffix.lower() == ".txt":
                level_play_file = problem
            else:
                level_play_file = args.play_level.resolve() if args.play_level else None
            try:
                print(f"[PLAY] Launching plan_player with {plan_play_file}" + (f" and level {level_play_file}" if level_file else ""))
                rc, out, err = play_plan(plan_play_file, level_play_file)
                if out:
                    sys.stdout.write(out)
                if err:
                    sys.stderr.write(err)
                if rc != 0:
                    print(f"[WARN] plan_player exited with code {rc}", file=sys.stderr)
            except Exception as e:
                print(f"[WARN] Could not launch plan_player: {e}", file=sys.stderr)
        else:
            print(f"[WARN] No play plan file found at {plan_play_file}", file=sys.stderr)
    exit_code = 0

    if temp_problem_dir is not None:
        temp_problem_dir.cleanup()

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
