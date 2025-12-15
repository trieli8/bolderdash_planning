#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Tuple

from common import (
    PlanResult,
    ensure_executable,
    parse_sexp_action,
    repo_root,
    run_cmd,
    write_plan_outputs,
)


def problem_name_from_path(problem: Path) -> str:
    return problem.stem


def solve_with_ff(domain: Path, problem: Path, timeout: int | None) -> PlanResult:
    root = repo_root()
    ff_bin = root / "planners" / "forced-action-ff" / "ff"
    ensure_executable(ff_bin)

    # FF wants -p <dir> and -o/-f file names. If domain & problem aren't in same dir, copy to temp.
    start = time.time()
    with tempfile.TemporaryDirectory(prefix="ff_run_") as td:
        td_path = Path(td)
        dname = "domain.pddl"
        pname = "problem.pddl"
        shutil.copy2(domain, td_path / dname)
        shutil.copy2(problem, td_path / pname)

        cmd = [str(ff_bin), "-p", str(td_path), "-o", dname, "-f", pname]
        rc, out, err = run_cmd(cmd, cwd=td_path, timeout_sec=timeout)

    actions: List[Tuple[str, List[str]]] = []
    # Typical FF output has lines like: "0: (ACTION ...)"
    for line in out.splitlines():
        m = re.match(r"^\s*\d+\s*:\s*(\(.+\))\s*$", line)
        if m:
            parsed = parse_sexp_action(m.group(1))
            if parsed:
                actions.append(parsed)

    status = "solved" if actions else ("unsolved" if rc == 0 else "error")
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


def solve_with_fd(domain: Path, problem: Path, timeout: int | None, alias: str) -> PlanResult:
    root = repo_root()
    fd_py = root / "planners" / "fast-downward" / "fast-downward.py"
    if not fd_py.exists():
        raise FileNotFoundError(f"Not found: {fd_py}")

    start = time.time()
    with tempfile.TemporaryDirectory(prefix="fd_run_") as td:
        td_path = Path(td)
        plan_file = td_path / "fd_plan.txt"

        # Fast Downward writes plan to --plan-file; actions are one per line.
        cmd = [
            sys.executable,
            str(fd_py),
            "--alias", alias,
            "--plan-file", str(plan_file),
            str(domain),
            str(problem),
        ]
        rc, out, err = run_cmd(cmd, cwd=td_path, timeout_sec=timeout)

        actions: List[Tuple[str, List[str]]] = []
        if plan_file.exists():
            for line in plan_file.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith(";"):
                    continue
                parsed = parse_sexp_action(line)
                if parsed:
                    actions.append(parsed)

    status = "solved" if actions else ("unsolved" if rc == 0 else "error")
    return PlanResult(
        planner="fd",
        domain=str(domain),
        problem=str(problem),
        status=status,
        actions=actions,
        raw_stdout=out,
        raw_stderr=err,
        metrics={"returncode": rc, "time_sec": round(time.time() - start, 3), "alias": alias},
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run a planner (FF or Fast Downward) and write outputs to plans/<problem_name>/ (default: both JSON + text)."
    )
    ap.add_argument("--planner", choices=["ff", "fd", "auto"], default="auto")
    ap.add_argument("--domain", required=True, type=Path)
    ap.add_argument("--problem", required=True, type=Path)
    ap.add_argument("--timeout", type=int, default=None, help="seconds")
    ap.add_argument("--fd-alias", default="seq-sat-lama-2011", help="Fast Downward alias")
    ap.add_argument("--out-root", type=Path, default=repo_root() / "plans")

    args = ap.parse_args()
    domain = args.domain.resolve()
    problem = args.problem.resolve()

    out_dir = (args.out_root / problem_name_from_path(problem)).resolve()

    try:
        if args.planner == "ff":
            res = solve_with_ff(domain, problem, args.timeout)
        elif args.planner == "fd":
            res = solve_with_fd(domain, problem, args.timeout, args.fd_alias)
        else:
            # auto: try FF then FD
            res = solve_with_ff(domain, problem, args.timeout)
            if res.status != "solved":
                res = solve_with_fd(domain, problem, args.timeout, args.fd_alias)

        write_plan_outputs(out_dir, res)

        print(f"[OK] planner={res.planner} status={res.status} actions={len(res.actions)}")
        print(f"     wrote: {out_dir / 'plan.txt'}")
        print(f"     wrote: {out_dir / 'plan.json'}")
        return 0 if res.status == "solved" else 2

    except Exception as e:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "error.log").write_text(str(e) + "\n", encoding="utf-8")
        print(f"[ERR] {e}")
        print(f"      (details written to {out_dir / 'error.log'})")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
