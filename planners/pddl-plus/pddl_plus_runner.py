#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclasses.dataclass
class TimedAction:
    name: str
    args: List[str]
    time: Optional[float] = None
    duration: Optional[float] = None


@dataclasses.dataclass
class PlusPlanResult:
    planner: str
    status: str  # solved | unsolved | timeout | error
    actions: List[TimedAction]
    raw_stdout: str
    raw_stderr: str
    metrics: Dict[str, Any]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_enhsp_jar(root: Path) -> Optional[Path]:
    candidates = [
        root / "planners" / "pddl-plus" / "enhsp.jar",
        root / "planners" / "pddl-plus" / "enhsp" / "enhsp.jar",
        root / "planners" / "pddl-plus" / "enhsp" / "enhsp-dist" / "enhsp.jar",
        root / "planners" / "pddl-plus" / "enhsp" / "target" / "enhsp.jar",
        root / "planners" / "pddl-plus" / "enhsp" / "build" / "libs" / "enhsp.jar",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _default_optic_bin(root: Path) -> Optional[Path]:
    candidates = [
        root / "planners" / "pddl-plus" / "optic-clp",
        root / "planners" / "pddl-plus" / "optic",
        root / "planners" / "pddl-plus" / "OPTIC" / "optic-clp",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _build_command(
    planner: str,
    domain: Path,
    problem: Path,
    planner_args: str,
    cmd_template: Optional[str],
    enhsp_jar: Optional[Path],
    optic_bin: Optional[Path],
) -> Tuple[str, List[str]]:
    root = repo_root()

    if planner == "auto":
        if enhsp_jar is None:
            enhsp_jar = _default_enhsp_jar(root)
        if enhsp_jar and enhsp_jar.exists():
            planner = "enhsp"
        else:
            if optic_bin is None:
                optic_bin = _default_optic_bin(root)
            if optic_bin and optic_bin.exists():
                planner = "optic"
            else:
                raise FileNotFoundError(
                    "No PDDL+ planner found. Put enhsp.jar or optic-clp under planners/pddl-plus/, "
                    "or pass --planner with --cmd-template."
                )

    extra = shlex.split(planner_args or "")

    if planner == "enhsp":
        jar = enhsp_jar or _default_enhsp_jar(root)
        if jar is None or not jar.exists():
            raise FileNotFoundError(
                "ENHSP jar not found. Expected planners/pddl-plus/enhsp.jar or pass --enhsp-jar."
            )
        if "-pe" not in extra and "--print-events-plan" not in extra:
            extra = [*extra, "-pe"]
        java_bin = shutil.which("java")
        brew_candidates = (
            "/usr/local/opt/openjdk@17/bin/java",
            "/opt/homebrew/opt/openjdk@17/bin/java",
        )
        if java_bin == "/usr/bin/java":
            for candidate in brew_candidates:
                if Path(candidate).exists():
                    java_bin = candidate
                    break
        if not java_bin:
            for candidate in brew_candidates:
                if Path(candidate).exists():
                    java_bin = candidate
                    break
        if not java_bin:
            raise FileNotFoundError(
                "Java runtime not found. Install OpenJDK and ensure `java` is on PATH, or install via Homebrew openjdk@17."
            )
        cmd = [java_bin, "-jar", str(jar), "-o", str(domain), "-f", str(problem)] + extra
        return "enhsp", cmd

    if planner == "optic":
        optic = optic_bin or _default_optic_bin(root)
        if optic is None or not optic.exists():
            raise FileNotFoundError(
                "OPTIC binary not found. Expected planners/pddl-plus/optic-clp or pass --optic-bin."
            )
        cmd = [str(optic), "-N", str(domain), str(problem)] + extra
        return "optic", cmd

    if planner == "cmd":
        if not cmd_template:
            raise ValueError("--planner cmd requires --cmd-template.")
        rendered = cmd_template.format(domain=str(domain), problem=str(problem))
        cmd = shlex.split(rendered)
        if not cmd:
            raise ValueError("Rendered --cmd-template produced an empty command.")
        return "cmd", cmd

    raise ValueError(f"Unsupported planner: {planner}")


_PLAN_LINE_RE = re.compile(
    r"^\s*(?:(\d+(?:\.\d+)?)\s*:\s*)?\(\s*([A-Za-z][A-Za-z0-9_+\-]*)([^()]*)\)\s*(?:\[\s*(\d+(?:\.\d+)?)\s*\])?\s*$"
)


def parse_actions(raw_text: str) -> List[TimedAction]:
    actions: List[TimedAction] = []
    seen = set()
    valid_token = re.compile(r"^[A-Za-z0-9_+\-]+$")

    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";"):
            continue

        m = _PLAN_LINE_RE.match(line)
        if not m:
            # Also accept prefixed lines like "step 0: (move ...)"
            idx = line.find("(")
            if idx >= 0:
                maybe = line[idx:]
                m = _PLAN_LINE_RE.match(maybe)
            if not m:
                continue

        t_str, name, arg_blob, d_str = m.groups()
        args = [tok for tok in arg_blob.strip().split() if tok]
        if not valid_token.match(name):
            continue
        if any(not valid_token.match(tok) for tok in args):
            continue
        timed = TimedAction(
            name=name.lower(),
            args=args,
            time=float(t_str) if t_str is not None else None,
            duration=float(d_str) if d_str is not None else None,
        )

        key = (
            timed.time,
            timed.name,
            tuple(a.lower() for a in timed.args),
            timed.duration,
        )
        if key in seen:
            continue
        seen.add(key)
        actions.append(timed)

    # Preserve planner-reported order. Some planners print every action at time 0
    # for sequential plans; re-sorting would scramble executability.
    return actions


def _run_capture(cmd: List[str], timeout_sec: Optional[int]) -> Tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _run_stream(cmd: List[str], timeout_sec: Optional[int], prefix: str) -> Tuple[int, str, str]:
    start = time.time()
    proc = subprocess.Popen(
        cmd,
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
            sys.stdout.write(f"{prefix}{line}" if prefix else line)
            sys.stdout.flush()

            if timeout_sec is not None and (time.time() - start) > timeout_sec:
                proc.kill()
                raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout_sec)

        rc = proc.wait()
        return rc, "".join(out_lines), ""
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        raise


def solve(
    domain: Path,
    problem: Path,
    planner: str = "auto",
    timeout: Optional[int] = None,
    stream: bool = False,
    planner_args: str = "",
    cmd_template: Optional[str] = None,
    enhsp_jar: Optional[Path] = None,
    optic_bin: Optional[Path] = None,
) -> PlusPlanResult:
    start = time.time()
    planner_used, cmd = _build_command(
        planner=planner,
        domain=domain,
        problem=problem,
        planner_args=planner_args,
        cmd_template=cmd_template,
        enhsp_jar=enhsp_jar,
        optic_bin=optic_bin,
    )

    try:
        if stream:
            rc, out, err = _run_stream(cmd, timeout_sec=timeout, prefix="[PDDL+] ")
        else:
            rc, out, err = _run_capture(cmd, timeout_sec=timeout)
    except subprocess.TimeoutExpired:
        return PlusPlanResult(
            planner=planner_used,
            status="timeout",
            actions=[],
            raw_stdout="",
            raw_stderr="",
            metrics={"returncode": None, "time_sec": round(time.time() - start, 3), "command": cmd},
        )

    full = (out or "") + "\n" + (err or "")
    actions = parse_actions(full)

    lowered = full.lower()
    if any(token in lowered for token in ["runtimeexception", "some syntax error", "severe:"]):
        status = "error"
    elif actions:
        status = "solved"
    elif rc == 0 and any(token in lowered for token in ["unsat", "no plan", "unsolvable", "unsolvable problem"]):
        status = "unsolved"
    elif rc == 0:
        status = "unsolved"
    else:
        status = "error"

    return PlusPlanResult(
        planner=planner_used,
        status=status,
        actions=actions,
        raw_stdout=out,
        raw_stderr=err,
        metrics={"returncode": rc, "time_sec": round(time.time() - start, 3), "command": cmd},
    )


def _format_action(a: TimedAction) -> str:
    if a.duration is not None and a.time is not None:
        return f"{a.time:.3f}: ({a.name} {' '.join(a.args)}) [{a.duration:.3f}]"
    if a.time is not None:
        return f"{a.time:.3f}: ({a.name} {' '.join(a.args)})"
    return f"({a.name} {' '.join(a.args)})".rstrip()


def _ensure_executable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing executable: {path}")
    mode = path.stat().st_mode
    path.chmod(mode | 0o100)


def _plan_player_path() -> Path:
    return repo_root() / "stonesandgem" / "build" / "bin" / "plan_player"


def _play_plan(plan_file: Path, level_file: Optional[Path]) -> Tuple[int, str, str]:
    player = _plan_player_path()
    _ensure_executable(player)
    cmd = [str(player), str(plan_file)]
    if level_file:
        cmd.append(str(level_file))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _normalise_problem_name(problem: Path) -> str:
    try:
        txt = problem.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\(\s*problem\s+([^\s\)]+)\s*\)", txt, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return problem.stem


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


def _write_direction_plan(path: Path, actions: List[TimedAction]) -> None:
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

    if not tokens:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"({t})" for t in tokens) + "\n", encoding="utf-8")


def _resolve_level_file_for_view(problem: Path, explicit_level: Optional[Path]) -> Optional[Path]:
    if explicit_level:
        return explicit_level.resolve()
    if problem.suffix.lower() == ".txt":
        return problem.resolve()
    candidate = problem.with_suffix(".txt")
    if candidate.exists():
        return candidate.resolve()
    fallback = repo_root() / "pddl" / "level.txt"
    return fallback.resolve() if fallback.exists() else None


def _planner_tag(planner_used: str) -> str:
    if planner_used == "enhsp":
        return "plus-enhsp"
    if planner_used == "optic":
        return "plus-optic"
    if planner_used == "cmd":
        return "plus-cmd"
    return "plus"


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a PDDL+ planner and print parsed actions.")
    ap.add_argument("--domain", type=Path, required=True)
    ap.add_argument("--problem", type=Path, required=True)
    ap.add_argument("--planner", choices=["auto", "enhsp", "optic", "cmd"], default="auto")
    ap.add_argument("--timeout", type=int, default=None)
    ap.add_argument("--stream", action="store_true")
    ap.add_argument("--planner-args", default="")
    ap.add_argument("--cmd-template", default=None)
    ap.add_argument("--enhsp-jar", type=Path, default=None)
    ap.add_argument("--optic-bin", type=Path, default=None)
    ap.add_argument("--view", action="store_true", help="After solving, open play plan in plan_player.")
    ap.add_argument("--play-level", type=Path, default=None, help="Optional level file for plan_player.")
    args = ap.parse_args()

    domain_path = args.domain.resolve()
    problem_path = args.problem.resolve()
    res = solve(
        domain=domain_path,
        problem=problem_path,
        planner=args.planner,
        timeout=args.timeout,
        stream=args.stream,
        planner_args=args.planner_args,
        cmd_template=args.cmd_template,
        enhsp_jar=args.enhsp_jar.resolve() if args.enhsp_jar else None,
        optic_bin=args.optic_bin.resolve() if args.optic_bin else None,
    )

    for a in res.actions:
        print(_format_action(a))

    print(f"status={res.status} planner={res.planner} actions={len(res.actions)}")

    if args.view and res.status == "solved":
        problem_name = _normalise_problem_name(problem_path)
        out_dir = repo_root() / "plans" / problem_name
        play_path = out_dir / f"{_planner_tag(res.planner)}.play.plan"
        _write_direction_plan(play_path, res.actions)
        if not play_path.exists():
            print("[WARN] No directional moves found to view.", file=sys.stderr)
        else:
            level_file = _resolve_level_file_for_view(problem_path, args.play_level.resolve() if args.play_level else None)
            print(
                f"[PLAY] Launching plan_player with {play_path}"
                + (f" and level {level_file}" if level_file else "")
            )
            try:
                rc, out, err = _play_plan(play_path, level_file)
                if out:
                    sys.stdout.write(out)
                if err:
                    sys.stderr.write(err)
                if rc != 0:
                    print(f"[WARN] plan_player exited with code {rc}", file=sys.stderr)
            except Exception as exc:
                print(f"[WARN] Could not launch plan_player: {exc}", file=sys.stderr)

    return 0 if res.status in ("solved", "unsolved") else 1


if __name__ == "__main__":
    raise SystemExit(main())
