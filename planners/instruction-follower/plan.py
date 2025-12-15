#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Tuple

# Make repo utilities importable (tools/common.py)
THIS_DIR = Path(__file__).resolve().parent
# parents[0]=planners, parents[1]=repo root
REPO_ROOT = THIS_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from common import (  # type: ignore  # noqa: E402
    PlanResult,
    parse_sexp_action,
    run_cmd,
    write_plan_outputs,
)


def problem_name_from_path(problem: Path) -> str:
    return problem.stem


def parse_pddl_with_fd(domain: Path, problem: Path, timeout: int | None) -> tuple[int, str, str, float, str]:
    """
    Run Fast Downward's translate component to ensure the domain/problem parse.
    No search is performed; only parsing/grounding.
    """
    fd_py = REPO_ROOT / "planners" / "fast-downward" / "fast-downward.py"
    if not fd_py.exists():
        raise FileNotFoundError(f"Fast Downward entrypoint not found: {fd_py}")

    start = time.time()
    with tempfile.TemporaryDirectory(prefix="if_translate_") as td:
        td_path = Path(td)
        sas_path = td_path / "output.sas"
        rc, out, err = run_cmd(
            [sys.executable, str(fd_py), "--translate", str(domain), str(problem), "--sas-file", str(sas_path)],
            cwd=td_path,
            timeout_sec=timeout,
        )
        sas_text = sas_path.read_text(encoding="utf-8", errors="replace") if sas_path.exists() else ""
    return rc, out, err, round(time.time() - start, 3), sas_text


def load_actions(actions_path: Path) -> List[Tuple[str, List[str]]]:
    """
    Accepts a text file with one action per line, e.g.:
      (move a c1 c2)
      0: (move a c2 c3)
    Blank lines and lines starting with '#' or ';' are ignored.
    """
    if not actions_path.exists():
        raise FileNotFoundError(f"Actions file not found: {actions_path}")

    actions: List[Tuple[str, List[str]]] = []
    for raw_line in actions_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith(";") or line.startswith("#"):
            continue
        parsed = parse_sexp_action(line)
        if not parsed:
            raise ValueError(f"Could not parse action line: {raw_line}")
        actions.append(parsed)
    return actions


class SASOperator:
    def __init__(self, name_tokens: List[str], pre: List[Tuple[int, int]], eff: List[Tuple[int, int]]):
        self.name_tokens = name_tokens
        self.pre = pre
        self.eff = eff

    @property
    def key(self) -> Tuple[str, Tuple[str, ...]]:
        name = self.name_tokens[0].lower() if self.name_tokens else ""
        args = tuple(tok.lower() for tok in self.name_tokens[1:])
        return name, args

    @property
    def is_forced(self) -> bool:
        return self.name_tokens and self.name_tokens[0].lower().startswith(("fa-", "fa_", "forced-"))


def parse_sas(sas_text: str) -> Tuple[List[int], List[SASOperator]]:
    """
    Minimal SAS parser to get initial state and grounded operators.
    """
    lines = sas_text.splitlines()
    it = iter(lines)

    # Skip version/metric
    for _ in range(4):
        next(it, None)

    # Variables count
    var_count_line = next(it, "0")
    try:
        var_count = int(var_count_line)
    except ValueError:
        var_count = 0

    # Skip variables blocks
    for _ in range(var_count):
        # begin_variable ... end_variable
        while True:
            line = next(it, None)
            if line is None or line.strip() == "end_variable":
                break

    # Mutex groups count (skip)
    mutex_count_line = next(it, "0")
    try:
        mutex_count = int(mutex_count_line)
    except ValueError:
        mutex_count = 0
    for _ in range(mutex_count):
        while True:
            line = next(it, None)
            if line is None or line.strip() == "end_mutex_group":
                break

    # Initial state
    init_state: List[int] = []
    line = next(it, "")
    if line.strip() != "begin_state":
        raise ValueError("SAS parse: expected begin_state")
    for _ in range(var_count):
        val_line = next(it, "0")
        init_state.append(int(val_line.strip()))
    # consume end_state
    next(it, None)

    # Goal (skip)
    line = next(it, "")
    if line.strip() != "begin_goal":
        raise ValueError("SAS parse: expected begin_goal")
    goal_count = int(next(it, "0").strip())
    for _ in range(goal_count):
        next(it, None)
    next(it, None)  # end_goal

    # Operators count (line with int)
    op_count_line = next(it, "0")
    try:
        op_count = int(op_count_line)
    except ValueError:
        op_count = 0

    operators: List[SASOperator] = []
    for _ in range(op_count):
        line = next(it, None)
        if line is None or line.strip() != "begin_operator":
            break
        name_line = next(it, "").strip()
        name_tokens = name_line.replace("(", "").replace(")", "").split()
        prevail_count = int(next(it, "0").strip())
        pre: List[Tuple[int, int]] = []
        for _ in range(prevail_count):
            var, val = next(it, "0 0").split()
            pre.append((int(var), int(val)))
        pre_post_count = int(next(it, "0").strip())
        eff: List[Tuple[int, int]] = []
        for _ in range(pre_post_count):
            parts = next(it, "").split()
            if len(parts) < 3:
                continue
            var = int(parts[0])
            old = int(parts[1])
            new = int(parts[2])
            # remaining parts are conditional effects; we ignore them but treat them as extra preconditions if present
            conds: List[Tuple[int, int]] = []
            if len(parts) > 3:
                num_conds = int(parts[3])
                cond_parts = parts[4:]
                for i in range(num_conds):
                    c_var = int(cond_parts[2 * i])
                    c_val = int(cond_parts[2 * i + 1])
                    conds.append((c_var, c_val))
            if old != -1:
                pre.append((var, old))
            pre.extend(conds)
            eff.append((var, new))
        # cost line
        next(it, None)
        # end_operator
        next(it, None)
        operators.append(SASOperator(name_tokens, pre, eff))

    return init_state, operators


def applicable(op: SASOperator, state: List[int]) -> bool:
    return all(state[var] == val for var, val in op.pre)


def apply(op: SASOperator, state: List[int]) -> None:
    for var, val in op.eff:
        state[var] = val


def run_forced_actions(forced_ops: List[SASOperator], state: List[int], max_steps: int = 10000) -> List[Tuple[str, List[str]]]:
    """
    Repeatedly apply any applicable forced actions until none remain.
    """
    executed: List[Tuple[str, List[str]]] = []
    steps = 0
    while steps < max_steps:
        applicable_ops = [op for op in forced_ops if applicable(op, state)]
        if not applicable_ops:
            break
        # Stable order to avoid nondeterminism
        for op in sorted(applicable_ops, key=lambda o: " ".join(o.name_tokens)):
            apply(op, state)
            name = op.name_tokens[0] if op.name_tokens else ""
            args = op.name_tokens[1:]
            executed.append((name, args))
            steps += 1
            if steps >= max_steps:
                break
    return executed


def run_instruction_follower(
    domain: Path,
    problem: Path,
    actions_path: Path,
    *,
    out_root: Path | None = None,
    timeout: int | None = None,
    skip_parse: bool = False,
    run_forced: bool = True,
    write_outputs: bool = True,
) -> tuple[PlanResult, Path]:
    """
    Programmatic entrypoint for the instruction-follower planner.
    Returns (PlanResult, out_dir). If write_outputs is True, writes plan files to out_dir.
    """
    domain = domain.resolve()
    problem = problem.resolve()
    actions_path = actions_path.resolve()
    out_root = (out_root or (REPO_ROOT / "plans")).resolve()
    out_dir = (out_root / problem_name_from_path(problem)).resolve()

    parse_rc = 0
    parse_out = ""
    parse_err = ""
    parse_time = 0.0
    sas_text = ""
    if not skip_parse:
        parse_rc, parse_out, parse_err, parse_time, sas_text = parse_pddl_with_fd(domain, problem, timeout)
        if parse_rc != 0:
            res = PlanResult(
                planner="instruction-follower",
                domain=str(domain),
                problem=str(problem),
                status="error",
                actions=[],
                raw_stdout=parse_out,
                raw_stderr=parse_err,
                metrics={"returncode": parse_rc, "parse_time_sec": parse_time},
            )
            if write_outputs:
                write_plan_outputs(out_dir, res)
            return res, out_dir
    elif run_forced:
        # Can't run forced actions without grounded operators
        run_forced = False

    try:
        user_actions = load_actions(actions_path)
    except Exception as e:
        res = PlanResult(
            planner="instruction-follower",
            domain=str(domain),
            problem=str(problem),
            status="error",
            actions=[],
            raw_stdout=parse_out,
            raw_stderr=f"{parse_err}\n{e}",
            metrics={"returncode": parse_rc, "parse_time_sec": parse_time},
        )
        if write_outputs:
            write_plan_outputs(out_dir, res)
        return res, out_dir

    executed: List[Tuple[str, List[str]]] = []
    raw_err = parse_err
    metrics = {
        "returncode": parse_rc,
        "parse_time_sec": parse_time,
        "actions_file": str(actions_path),
        "actions_count": len(user_actions),
    }

    if run_forced and sas_text.strip():
        try:
            state, operators = parse_sas(sas_text)
        except Exception as e:
            res = PlanResult(
                planner="instruction-follower",
                domain=str(domain),
                problem=str(problem),
                status="error",
                actions=[],
                raw_stdout=parse_out,
                raw_stderr=f"{raw_err}\nFailed to parse SAS: {e}",
                metrics=metrics,
            )
            if write_outputs:
                write_plan_outputs(out_dir, res)
            return res, out_dir

        op_map = {(op.key[0], op.key[1]): op for op in operators}
        forced_ops = [op for op in operators if op.is_forced]

        # Initial forced closure
        executed.extend(run_forced_actions(forced_ops, state))

        for name, args_list in user_actions:
            key = (name.lower(), tuple(a.lower() for a in args_list))
            op = op_map.get(key)
            if not op:
                raw_err += f"\nMissing grounded action in SAS: {name} {' '.join(args_list)}"
                break
            if not applicable(op, state):
                raw_err += f"\nInapplicable action: {name} {' '.join(args_list)}"
                break
            apply(op, state)
            executed.append((name, args_list))
            executed.extend(run_forced_actions(forced_ops, state))
        else:
            # Final forced closure
            executed.extend(run_forced_actions(forced_ops, state))
    else:
        executed = user_actions

    status = "solved" if executed else "unsolved"
    res = PlanResult(
        planner="instruction-follower",
        domain=str(domain),
        problem=str(problem),
        status=status,
        actions=executed,
        raw_stdout=parse_out,
        raw_stderr=raw_err,
        metrics=metrics,
    )
    if write_outputs:
        write_plan_outputs(out_dir, res)

    return res, out_dir


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Instruction-following planner: parse PDDL with Fast Downward, then emit the given action list as the plan."
    )
    ap.add_argument("--domain", required=True, type=Path, help="Path to domain PDDL")
    ap.add_argument("--problem", required=True, type=Path, help="Path to problem PDDL")
    ap.add_argument("--actions", required=True, type=Path, help="Path to text file containing actions (one per line)")
    ap.add_argument(
        "--out-root",
        type=Path,
        default=REPO_ROOT / "plans",
        help="Directory to place plan outputs (default: repo_root/plans/<problem-name>/...)",
    )
    ap.add_argument("--timeout", type=int, default=None, help="Seconds to allow for PDDL parsing (translate only)")
    ap.add_argument(
        "--skip-parse",
        action="store_true",
        help="Skip the PDDL parse/grounding step (still writes plan from actions file)",
    )
    ap.add_argument(
        "--no-forced",
        dest="run_forced",
        action="store_false",
        help="Disable automatic forced-action closure (fa-* actions) between supplied actions",
    )
    ap.set_defaults(run_forced=True)

    args = ap.parse_args()
    domain = args.domain.resolve()
    problem = args.problem.resolve()
    actions_path = args.actions.resolve()
    res, out_dir = run_instruction_follower(
        domain,
        problem,
        actions_path,
        out_root=args.out_root,
        timeout=args.timeout,
        skip_parse=args.skip_parse,
        run_forced=args.run_forced,
        write_outputs=True,
    )

    if res.status == "error":
        if args.skip_parse and args.run_forced:
            print("[WARN] --skip-parse disables forced actions; falling back to simple plan emission.")
        print(f"[ERR] planner=instruction-follower status={res.status} actions={len(res.actions)} forced={'on' if args.run_forced else 'off'}")
        print(f"     wrote: {out_dir / 'plan.txt'}")
        print(f"     wrote: {out_dir / 'plan.json'}")
        return 1

    if args.skip_parse and not res.raw_stderr and args.run_forced:
        print("[WARN] --skip-parse disables forced actions; falling back to simple plan emission.")

    print(f"[OK] planner=instruction-follower status={res.status} actions={len(res.actions)} forced={'on' if args.run_forced else 'off'}")
    print(f"     wrote: {out_dir / 'plan.txt'}")
    print(f"     wrote: {out_dir / 'plan.json'}")
    return 0 if res.status == "solved" else 2


if __name__ == "__main__":
    raise SystemExit(main())
