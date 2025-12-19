#!/usr/bin/env python3
"""
Compare PDDL simulation (via Fast Downward translate/SAS) against native stonesngems trace.

Usage:
  python tools/validate_pddl.py --domain pddl/domain.pddl --problem pddl/level01.pddl \
      --plan plans/level-1/fd-opt.plan --native-trace native_trace.jsonl
  python tools/validate_pddl.py --problem pddl/level01.pddl \
      --human-plan plans/level-1/fd.play.plan --human-plan-format directions

Steps:
  - Run FD translator to get SAS.
  - Parse plan actions and SAS operators; simulate to build a PDDL trace.
  - Load native trace (from stones_trace) and compare agent/gem/stone/dirt positions per step.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Iterable, Set
from plan import write_direction_plan



def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


# -------------------- Plan parsing --------------------

def parse_sexp_action(line: str) -> Optional[Tuple[str, List[str]]]:
    line = line.strip()
    m = re.search(r"\(\s*([^\s()]+)\s*([^()]*)\)", line)
    if not m:
        return None
    name = m.group(1).strip()
    rest = m.group(2).strip()
    args = [tok for tok in rest.split() if tok]
    return name.lower(), [a.lower() for a in args]


def read_plan(plan_path: Path) -> List[Tuple[str, List[str]]]:
    actions: List[Tuple[str, List[str]]] = []
    for raw in plan_path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith(";"):
            continue
        parsed = parse_sexp_action(raw)
        if parsed:
            actions.append(parsed)
    return actions


_DIRECTION_ALIASES = {
    "up": "up",
    "w": "up",
    "n": "up",
    "north": "up",
    "down": "down",
    "s": "down",
    "south": "down",
    "left": "left",
    "a": "left",
    "l": "left",
    "west": "left",
    "right": "right",
    "d": "right",
    "r": "right",
    "east": "right",
    "noop": "noop",
    "no-op": "noop",
    "stay": "noop",
}


def _token_from_plan_line(raw: str) -> Optional[str]:
    stripped = raw.strip()
    if not stripped or stripped[0] in (";", "#"):
        return None
    if "(" in stripped:
        lparen = stripped.find("(")
        rparen = stripped.find(")", lparen + 1)
        inside = stripped[lparen + 1: (rparen if rparen != -1 else len(stripped))]
        token = inside.strip().split()[0] if inside.strip() else ""
    else:
        token = stripped.split()[0]
    return token.lower() if token else None


def detect_human_plan_format(plan_path: Path) -> str:
    tokens: List[str] = []
    for raw in plan_path.read_text(encoding="utf-8", errors="replace").splitlines():
        token = _token_from_plan_line(raw)
        if token:
            tokens.append(token)
    if not tokens:
        raise ValueError(f"No usable actions found in plan: {plan_path}")
    if all(token in _DIRECTION_ALIASES for token in tokens):
        return "directions"
    return "actions"


def read_direction_plan(plan_path: Path) -> List[str]:
    directions: List[str] = []
    for raw in plan_path.read_text(encoding="utf-8", errors="replace").splitlines():
        token = _token_from_plan_line(raw)
        if not token:
            continue
        mapped = _DIRECTION_ALIASES.get(token)
        if not mapped:
            raise ValueError(f"Unrecognized direction token '{token}' in {plan_path}")
        if mapped == "noop":
            raise ValueError("Direction 'noop' is not supported by the PDDL domain.")
        directions.append(mapped)
    if not directions:
        raise ValueError(f"No usable actions found in plan: {plan_path}")
    return directions


# -------------------- SAS parsing --------------------

@dataclass
class SASVar:
    name: str
    atoms: List[str]  # length = domain size (excluding <none>)


@dataclass
class SASOp:
    name_tokens: List[str]
    pre: List[Tuple[int, int]]
    eff: List[Tuple[int, int]]

    @property
    def key(self) -> Tuple[str, Tuple[str, ...]]:
        if not self.name_tokens:
            return "", ()
        return self.name_tokens[0].lower(), tuple(t.lower() for t in self.name_tokens[1:])

    @property
    def is_forced(self) -> bool:
        if not self.name_tokens:
            return False
        name = self.name_tokens[0].lower()
        return name.startswith("__forced__") or name.startswith("fa_") or name.startswith("forced-")


def run_translate(domain: Path, problem: Path, timeout: Optional[int]) -> str:
    fd_py = repo_root() / "planners" / "fast-downward" / "fast-downward.py"
    if not fd_py.exists():
        raise FileNotFoundError(f"fast-downward.py not found at {fd_py}")
    with tempfile.TemporaryDirectory(prefix="fd_translate_") as td:
        sas_file = Path(td) / "output.sas"
        cmd = [sys.executable, str(fd_py), "--translate", str(domain), str(problem), "--sas-file", str(sas_file)]
        try:
            subprocess.run(
                cmd,
                check=True,
                cwd=td,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"[ERR] FD translate failed (rc={e.returncode})\n")
            if e.stdout:
                sys.stderr.write(e.stdout)
            if e.stderr:
                sys.stderr.write(e.stderr)
            raise
        return sas_file.read_text(encoding="utf-8", errors="replace")


def parse_sas(sas_text: str) -> Tuple[List[SASVar], List[int], List[SASOp]]:
    lines = [ln.strip() for ln in sas_text.splitlines() if ln.strip() != ""]
    it = iter(lines)

    # Header: begin_version, <num>, end_version, begin_metric, <num>, end_metric
    if next(it, "") != "begin_version":
        raise ValueError("SAS parse: expected begin_version")
    next(it, None)  # version number
    if next(it, "") != "end_version":
        raise ValueError("SAS parse: expected end_version")
    if next(it, "") != "begin_metric":
        raise ValueError("SAS parse: expected begin_metric")
    next(it, None)  # metric value
    if next(it, "") != "end_metric":
        raise ValueError("SAS parse: expected end_metric")

    var_count = int(next(it, "0"))
    vars_out: List[SASVar] = []
    for _ in range(var_count):
        assert next(it, "") == "begin_variable"
        name = next(it, "").strip()
        next(it, None)  # axiom layer
        domain_size = int(next(it, "0"))
        atoms: List[str] = []
        for _ in range(domain_size):
            atom_line = next(it, "").strip()
            atoms.append(atom_line)
        assert next(it, "") == "end_variable"
        vars_out.append(SASVar(name=name, atoms=atoms))

    mutex_count = int(next(it, "0"))
    for _ in range(mutex_count):
        while True:
            line = next(it, None)
            if line is None or line.strip() == "end_mutex_group":
                break

    assert next(it, "") == "begin_state"
    init_state: List[int] = []
    for _ in range(var_count):
        init_state.append(int(next(it, "0").strip()))
    assert next(it, "") == "end_state"

    # goal skip
    assert next(it, "") == "begin_goal"
    goal_n = int(next(it, "0"))
    for _ in range(goal_n):
        next(it, None)
    assert next(it, "") == "end_goal"

    op_count = int(next(it, "0"))
    ops: List[SASOp] = []
    for _ in range(op_count):
        if next(it, "") != "begin_operator":
            break
        name_line = next(it, "").strip()
        name_tokens = name_line.replace("(", "").replace(")", "").split()

        prevails = int(next(it, "0"))
        pre: List[Tuple[int, int]] = []
        for _ in range(prevails):
            v, val = next(it, "0 0").split()
            pre.append((int(v), int(val)))

        pe_count = int(next(it, "0"))
        eff: List[Tuple[int, int]] = []
        for _ in range(pe_count):
            parts = next(it, "").split()
            if not parts:
                continue
            idx = 0
            num_conds = int(parts[idx]); idx += 1
            conds: List[Tuple[int, int]] = []
            for _ in range(num_conds):
                if idx + 1 >= len(parts):
                    break
                c_var = int(parts[idx]); c_val = int(parts[idx + 1])
                conds.append((c_var, c_val))
                idx += 2
            if idx + 2 >= len(parts):
                continue
            v = int(parts[idx]); old = int(parts[idx + 1]); new = int(parts[idx + 2])
            if old != -1:
                pre.append((v, old))
            pre.extend(conds)
            eff.append((v, new))
        next(it, None)  # cost
        next(it, None)  # end_operator
        ops.append(SASOp(name_tokens, pre, eff))

    return vars_out, init_state, ops


def normalise_problem_name(problem: Path) -> str:
    try:
        txt = problem.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\(\s*problem\s+([^\s\)]+)\s*\)", txt, flags=re.IGNORECASE)
        if m:
            return m.group(1)
    except Exception:
        pass
    return problem.stem


# -------------------- Simulation --------------------

def applicable(op: SASOp, state: List[int]) -> bool:
    return all(state[v] == val for v, val in op.pre)


def apply(op: SASOp, state: List[int]) -> None:
    for v, val in op.eff:
        state[v] = val


def build_op_map(ops: List[SASOp]) -> Dict[Tuple[str, Tuple[str, ...]], SASOp]:
    return {op.key: op for op in ops}


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


def op_direction(op: SASOp) -> Optional[str]:
    if not op.name_tokens:
        return None
    name = op.name_tokens[0].lower()
    if not name.startswith("move"):
        return None
    if len(op.name_tokens) < 4:
        return None
    return _dir_from_coords(op.name_tokens[2], op.name_tokens[3])


def _action_from_op(op: SASOp) -> Tuple[str, List[str]]:
    name = op.name_tokens[0].lower() if op.name_tokens else ""
    args = [tok.lower() for tok in op.name_tokens[1:]]
    return name, args


def run_forced_actions(
    forced_ops: List[SASOp],
    state: List[int],
    *,
    max_steps: int = 10000,
) -> List[Tuple[str, List[str]]]:
    executed: List[Tuple[str, List[str]]] = []
    steps = 0
    while steps < max_steps:
        applicable_ops = [op for op in forced_ops if applicable(op, state)]
        if not applicable_ops:
            break
        for op in sorted(applicable_ops, key=lambda o: " ".join(o.name_tokens)):
            apply(op, state)
            executed.append(_action_from_op(op))
            steps += 1
            if steps >= max_steps:
                break
    if steps >= max_steps:
        raise RuntimeError("Forced action expansion exceeded max_steps; possible infinite loop.")
    return executed


def expand_actions_with_forced(
    user_actions: List[Tuple[str, List[str]]],
    ops: List[SASOp],
    init_state: List[int],
) -> List[Tuple[str, List[str]]]:
    if any(is_forced_action_name(name) for name, _ in user_actions):
        raise ValueError("Human plan includes forced actions; use --plan instead.")
    state = list(init_state)
    forced_ops = [op for op in ops if op.is_forced]
    op_map = build_op_map(ops)
    executed: List[Tuple[str, List[str]]] = []
    executed.extend(run_forced_actions(forced_ops, state))
    for name, args_list in user_actions:
        key = (name.lower(), tuple(a.lower() for a in args_list))
        op = op_map.get(key)
        if not op:
            raise ValueError(f"Missing operator for action: {name} {' '.join(args_list)}")
        if not applicable(op, state):
            raise ValueError(f"Inapplicable action: {name} {' '.join(args_list)}")
        apply(op, state)
        executed.append((name.lower(), [a.lower() for a in args_list]))
        executed.extend(run_forced_actions(forced_ops, state))
    executed.extend(run_forced_actions(forced_ops, state))
    return executed


def expand_directions_with_forced(
    directions: List[str],
    ops: List[SASOp],
    init_state: List[int],
) -> List[Tuple[str, List[str]]]:
    state = list(init_state)
    forced_ops = [op for op in ops if op.is_forced]
    user_ops = [op for op in ops if not op.is_forced]
    ops_by_dir: Dict[str, List[SASOp]] = {}
    for op in user_ops:
        direction = op_direction(op)
        if not direction:
            continue
        ops_by_dir.setdefault(direction, []).append(op)
    executed: List[Tuple[str, List[str]]] = []
    executed.extend(run_forced_actions(forced_ops, state))
    for direction in directions:
        candidates = [op for op in ops_by_dir.get(direction, []) if applicable(op, state)]
        if not candidates:
            raise ValueError(f"No applicable action found for direction '{direction}'.")
        if len(candidates) > 1:
            names = [f"{op.name_tokens[0]} {' '.join(op.name_tokens[1:])}" for op in candidates]
            raise ValueError(f"Ambiguous actions for direction '{direction}': {names}")
        op = candidates[0]
        apply(op, state)
        executed.append(_action_from_op(op))
        executed.extend(run_forced_actions(forced_ops, state))
    executed.extend(run_forced_actions(forced_ops, state))
    return executed


def is_forced_action_name(name: str) -> bool:
    lower = name.lower()
    return lower.startswith("__forced__") or lower.startswith("fa_") or lower.startswith("forced-")


def extract_state_atoms(vars_out: List[SASVar], state: List[int]) -> List[str]:
    atoms: List[str] = []
    for var, val in zip(vars_out, state):
        if val < 0 or val >= len(var.atoms):
            continue
        atoms.append(var.atoms[val])
    return atoms


def cells_from_atoms(atoms: Iterable[str]) -> Tuple[Optional[int], Set[int], Set[int], Set[int], int, int]:
    agent: Optional[int] = None
    gems: Set[int] = set()
    stones: Set[int] = set()
    dirt: Set[int] = set()
    max_r = -1
    max_c = -1

    cell_re = re.compile(r"c_(\d+)_(\d+)")

    for atom in atoms:
        # atom lines look like "Atom agent-at(c_0_0)" or "Atom stone(c_1_2)"
        lower = atom.lower()
        m = cell_re.search(lower)
        if not m:
            continue
        r = int(m.group(1)); c = int(m.group(2))
        max_r = max(max_r, r); max_c = max(max_c, c)

    cols = max_c if max_c >= 0 else 0
    rows = max_r if max_r >= 0 else 0

    for atom in atoms:
        lower = atom.lower()
        m = cell_re.search(lower)
        if not m:
            continue
        r = int(m.group(1)); c = int(m.group(2))

        if "negatedatom" == lower[:11]:
            continue

        if r == 0 or c == 0 or r == (rows+1) or c == (cols+1):
            continue  # border cells are ignored

        idx = (r-1) * cols + (c-1) 
        if "agent-at" in lower:
            agent = idx
        elif "gem" in lower:
            gems.add(idx)
        elif "stone" in lower:
            stones.add(idx)
        elif "dirt" in lower:
            dirt.add(idx)

    return agent, gems, stones, dirt, rows, cols


# -------------------- Native trace --------------------

@dataclass
class NativeStep:
    action: str
    agent: int
    gems: Set[int]
    stones: Set[int]
    dirt: Set[int]


def load_native_trace(path: Path) -> List[NativeStep]:
    steps: List[NativeStep] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        steps.append(
            NativeStep(
                action=data.get("action", ""),
                agent=int(data["agent"]),
                gems=set(int(x) for x in data.get("gems", [])),
                stones=set(int(x) for x in data.get("stones", [])),
                dirt=set(int(x) for x in data.get("dirt", [])),
            )
        )
    return steps


def parse_native_trace_text(text: str) -> List[NativeStep]:
    steps: List[NativeStep] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        steps.append(
            NativeStep(
                action=data.get("action", ""),
                agent=int(data["agent"]),
                gems=set(int(x) for x in data.get("gems", [])),
                stones=set(int(x) for x in data.get("stones", [])),
                dirt=set(int(x) for x in data.get("dirt", [])),
            )
        )
    return steps


def dump_native_trace(path: Path, steps: List[NativeStep]) -> None:
    lines = []
    for s in steps:
        lines.append(json.dumps({
            "action": s.action,
            "agent": s.agent,
            "gems": sorted(s.gems),
            "stones": sorted(s.stones),
            "dirt": sorted(s.dirt),
        }))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_stones_trace(plan: Path, level: Path, timeout: Optional[int]) -> List[NativeStep]:
    tracer = repo_root() / "stonesandgem" / "build" / "bin" / "stones_trace"
    if not tracer.exists():
        raise FileNotFoundError(f"stones_trace not found at {tracer} (build with: cmake --build stonesandgem/build --target stones_trace)")
    cmd = [str(tracer), str(plan), str(level)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    if proc.returncode != 0:
        sys.stderr.write(f"[ERR] stones_trace failed (rc={proc.returncode})\n")
        sys.stderr.write(proc.stdout or "")
        sys.stderr.write(proc.stderr or "")
        raise RuntimeError("stones_trace failed")
    return parse_native_trace_text(proc.stdout)


def launch_trace_viewer(native: List[NativeStep],
                        pddl_trace: List[Tuple[int, Set[int], Set[int], Set[int]]],
                        actions: List[Tuple[str, List[str]]],
                        level_path: Path) -> None:
    viewer = repo_root() / "stonesandgem" / "build" / "bin" / "trace_viewer"
    if not viewer.exists():
        print(f"[WARN] trace_viewer not found at {viewer} (build with: cmake --build stonesandgem/build --target trace_viewer)")
        return
    with tempfile.TemporaryDirectory(prefix="trace_viewer_") as td:
        native_path = Path(td) / "native.jsonl"
        pddl_path = Path(td) / "pddl.jsonl"
        dump_native_trace(native_path, native)
        dump_pddl_trace(pddl_path, actions, pddl_trace)
        cmd = [str(viewer), str(native_path), str(pddl_path), str(level_path)]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[WARN] trace_viewer exited with code {e.returncode}")


# -------------------- Comparison --------------------

def compare_traces(native: List[NativeStep], pddl_trace: List[Tuple[int, Set[int], Set[int], Set[int]]]) -> int:
    mismatches = 0
    length = min(len(native), len(pddl_trace))
    for i in range(length):
        n = native[i]
        agent, gems, stones, dirt = pddl_trace[i]
        errs = []
        if n.agent != agent:
            errs.append(f"agent {n.agent} != {agent}")
        if n.gems != gems:
            errs.append(f"gems {sorted(n.gems)} != {sorted(gems)}")
        if n.stones != stones:
            errs.append(f"stones {sorted(n.stones)} != {sorted(stones)}")
        if n.dirt != dirt:
            errs.append(f"dirt {sorted(n.dirt)} != {sorted(dirt)}")
        if errs:
            print(f"[MISMATCH] step {i}: " + "; ".join(errs))
            mismatches += 1
    if len(native) != len(pddl_trace):
        print(f"[MISMATCH] trace length native={len(native)} pddl={len(pddl_trace)}")
        mismatches += 1
    if mismatches == 0:
        print("[OK] traces match")
    return mismatches


def dump_pddl_trace(path: Path, actions: List[Tuple[str, List[str]]], trace: List[Tuple[int, Set[int], Set[int], Set[int]]]) -> None:
    lines = []
    for (act, (agent, gems, stones, dirt)) in zip(["init"] + [f"{n} {' '.join(a)}" for n, a in actions], trace):
        lines.append(json.dumps({
            "action": act,
            "agent": agent,
            "gems": sorted(gems),
            "stones": sorted(stones),
            "dirt": sorted(dirt),
        }))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare stonesngems native trace vs PDDL simulation step-by-step.")
    ap.add_argument("--domain", type=Path, default=repo_root() / "pddl" / "domain.pddl",
                    help="Domain PDDL (default: pddl/domain.pddl)")
    ap.add_argument("--problem", required=True, type=Path, help="Problem PDDL or level txt (used for both planning and stones_trace)")
    ap.add_argument("--plan", type=Path, help="Plan in S-expression (e.g., fd-opt.plan). If omitted, FD will generate one.")
    ap.add_argument("--human-plan", type=Path,
                    help="Human-readable plan containing only agent moves (directions or PDDL actions). Forced actions will be generated.")
    ap.add_argument("--human-plan-format", choices=["auto", "directions", "actions"], default="auto",
                    help="Interpretation of --human-plan. 'directions' expects up/down/left/right; 'actions' expects PDDL S-expr.")
    ap.add_argument("--native-trace", type=Path, help="Trace from stones_trace (JSONL). If omitted, stones_trace will be run in-memory using the plan.")
    ap.add_argument("--pddl-trace-out", type=Path, help="Optional path to write the simulated PDDL trace as JSONL for external viewers.")
    ap.add_argument("--view", action="store_true", help="Open a simple GUI to view native vs PDDL states side-by-side.")
    ap.add_argument("--timeout", type=int, default=None, help="Translate timeout (seconds)")
    args = ap.parse_args()

    if args.plan and args.human_plan:
        sys.stderr.write("[ERR] --plan and --human-plan are mutually exclusive.\n")
        return 2

    domain = args.domain.resolve()
    problem_input = args.problem.resolve()

    # If problem is a level .txt, generate a temp PDDL and remember the level path.
    temp_problem_dir: Optional[tempfile.TemporaryDirectory] = None
    if problem_input.suffix.lower() == ".txt":
        level_path = problem_input
        problem_name = problem_input.stem
        gen_py = repo_root() / "pddl" / "problem_gen.py"
        if not gen_py.exists():
            sys.stderr.write(f"[ERR] problem_gen.py not found at {gen_py}\n")
            return 1
        temp_problem_dir = tempfile.TemporaryDirectory(prefix="gen_problem_")
        problem = Path(temp_problem_dir.name) / f"{problem_name}.pddl"
        cmd = [sys.executable, str(gen_py), str(problem_input), "-p", problem_name]
        rc = subprocess.run(cmd, text=True, capture_output=True)
        if rc.returncode != 0:
            sys.stderr.write(f"[ERR] problem_gen failed (rc={rc.returncode})\n")
            sys.stderr.write(rc.stdout or "")
            sys.stderr.write(rc.stderr or "")
            return 1
        problem.write_text(rc.stdout, encoding="utf-8")
    else:
        problem = problem_input
        # Try to find a level txt alongside the problem or fallback to pddl/level.txt
        cand = problem.with_suffix(".txt")
        default_level = repo_root() / "pddl" / "level.txt"
        if cand.exists():
            level_path = cand
        elif default_level.exists():
            level_path = default_level
        else:
            sys.stderr.write("[ERR] Level file required for stones_trace (provide problem as .txt or add <problem>.txt or pddl/level.txt)\n")
            return 1

    plan_path: Optional[Path] = args.plan.resolve() if args.plan else None
    human_plan_path: Optional[Path] = args.human_plan.resolve() if args.human_plan else None

    if plan_path is None and human_plan_path is None:
        # Auto-generate plan using tools/plan.py with FD
        problem_name = normalise_problem_name(problem)
        gen_cmd = [
            sys.executable,
            str(repo_root() / "tools" / "plan.py"),
            "--planner", "fd",
            "--domain", str(domain),
            "--problem", str(problem),
        ]
        print(f"[INFO] Generating plan via Fast Downward: {' '.join(gen_cmd)}")
        rc = subprocess.run(gen_cmd, text=True, capture_output=True)
        if rc.returncode != 0:
            sys.stderr.write(f"[ERR] Failed to generate plan (rc={rc.returncode})\n")
            sys.stderr.write(rc.stdout or "")
            sys.stderr.write(rc.stderr or "")
            return 1
        plan_dir = repo_root() / "plans" / problem_name
        plan_path = plan_dir / "fd.plan"
        if not plan_path.exists():
            sys.stderr.write(f"[ERR] Generated plan not found at {plan_path}\n")
            return 1

    sas_text = run_translate(domain, problem, args.timeout)
    vars_out, init_state, ops = parse_sas(sas_text)
    op_map = build_op_map(ops)
    if human_plan_path:
        try:
            fmt = args.human_plan_format
            if fmt == "auto":
                fmt = detect_human_plan_format(human_plan_path)
            if fmt == "directions":
                directions = read_direction_plan(human_plan_path)
                plan_actions = expand_directions_with_forced(directions, ops, init_state)
            else:
                user_actions = read_plan(human_plan_path)
                plan_actions = expand_actions_with_forced(user_actions, ops, init_state)
        except Exception as e:
            sys.stderr.write(f"[ERR] Failed to expand human plan: {e}\n")
            return 1
    else:
        if plan_path is None:
            sys.stderr.write("[ERR] Plan path is required if --human-plan is not provided.\n")
            return 1
        plan_actions = read_plan(plan_path)

    play_plan_path = Path(tempfile.mkdtemp(prefix="play_plan_")) / "plan.play"
    write_direction_plan(play_plan_path, plan_actions)
    if not play_plan_path.exists():
        play_plan_path.write_text("", encoding="utf-8")

    state = list(init_state)
    pddl_trace: List[Tuple[int, Set[int], Set[int], Set[int]]] = []
    atoms = extract_state_atoms(vars_out, state)
    agent, gems, stones, dirt, _, _ = cells_from_atoms(atoms)
    pddl_trace.append((agent, gems, stones, dirt))

    for (name, args_list) in plan_actions:
        op = op_map.get((name, tuple(args_list)))
        if not op:
            print(f"[ERR] Missing operator for action: {name} {' '.join(args_list)}")
            return 1
        # TODO WARNING: skipping applicability check
        # if not applicable(op, state):
        #     print(f"[ERR] Inapplicable action: {name} {' '.join(args_list)}")
        #     return 1
        apply(op, state)
        atoms = extract_state_atoms(vars_out, state)
        agent, gems, stones, dirt, _, _ = cells_from_atoms(atoms)
        # if '__forced__' != op.name_tokens[0][0:3]:
        if "__forced__end-tick" == op.name_tokens[0]:
            pddl_trace.append((agent or -1, gems, stones, dirt))

    if args.native_trace:
        native_steps = load_native_trace(args.native_trace.resolve())
    else:
        native_steps = run_stones_trace(play_plan_path, level_path, args.timeout)
    mismatches = compare_traces(native_steps, pddl_trace)

    if args.pddl_trace_out:
        dump_pddl_trace(args.pddl_trace_out, plan_actions, pddl_trace)

    if args.view:
        launch_trace_viewer(native_steps, pddl_trace, plan_actions, level_path)

    return 0 if mismatches == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
