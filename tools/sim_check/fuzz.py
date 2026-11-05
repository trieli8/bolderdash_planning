#!/usr/bin/env python3
"""Differential tester: PDDL domain vs. the stonesngems engine.

For random levels and random agent walks, the same moves are executed in the
real engine (tools/sim_check/build/engine_trace) and in the grounded PDDL
model.  After every game tick the full board is compared cell by cell:
contents, the falling/stationary state of stones and gems, agent death, and
the position of the planner's target gem (followed through the engine's own
object ids).

The PDDL side runs the agent's move action, then every non-agent ("physics" or
__FORCED__) action until none is applicable.  All interleavings of physics
actions are explored, so a tick that can end in more than one state is
reported as nondeterministic (a classic planner could pick the outcome).

Usage:
  python3 tools/sim_check/fuzz.py --domain pddl/test_domains_target/domain_FA_scanner_combined.pddl
  python3 tools/sim_check/fuzz.py --domain ... --cases 500 --seed 3 --max-rows 7 --max-cols 8
  python3 tools/sim_check/fuzz.py --domain ... --level pddl/level_5_5.txt --cases 50

Exit status is 0 only if every case matched.
"""

from __future__ import annotations

import argparse
import random
import re
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

from pddl_exec import Task, load_task  # noqa: E402

ENGINE_SRC = [
    REPO / "tools/sim_check/engine_trace.cpp",
    REPO / "stonesandgem/src/stonesngems_base.cpp",
    REPO / "stonesandgem/src/util.cpp",
]
ENGINE_HEADERS = sorted((REPO / "stonesandgem/src").glob("*.h"))
ENGINE_BIN = HERE / "build" / "engine_trace"

# Engine cell ids (stonesandgem/src/definitions.h)
AGENT, EMPTY, DIRT, STONE, STONE_F, GEM, GEM_F = 0, 1, 2, 3, 4, 5, 6
EXIT_CLOSED, WALL_BRICK, WALL_STEEL = 7, 18, 19
TARGET_GEM, TARGET_GEM_F = 90, 91  # planner-only markers
WALL_IDS = {7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23}

DIRS = {0: (0, 0), 1: (-1, 0), 2: (0, 1), 3: (1, 0), 4: (0, -1)}
DIR_NAMES = {0: "noop", 1: "up", 2: "right", 3: "down", 4: "left"}


# --------------------------------------------------------------------------
# engine
# --------------------------------------------------------------------------


def ensure_engine() -> Path:
    missing = [p for p in ENGINE_SRC if not p.exists()]
    if missing:
        raise FileNotFoundError(f"engine sources missing ({missing[0]}); run: git submodule update --init stonesandgem")
    newest_src = max(p.stat().st_mtime for p in [*ENGINE_SRC, *ENGINE_HEADERS])
    if not ENGINE_BIN.exists() or ENGINE_BIN.stat().st_mtime < newest_src:
        ENGINE_BIN.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["g++", "-std=c++20", "-O2", f"-I{REPO / 'stonesandgem/src'}", *map(str, ENGINE_SRC), "-o", str(ENGINE_BIN)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError("building engine_trace failed:\n" + proc.stderr[-4000:])
    return ENGINE_BIN


@dataclass
class EngineTick:
    status: str
    gems: int
    tracked: int
    cells: List[int]


def run_engine(cases: Sequence[Tuple[str, str, int]]) -> List[List[EngineTick]]:
    binary = ensure_engine()
    payload = "".join(f"{lvl};{acts};{trk}\n" for lvl, acts, trk in cases)
    out = subprocess.run([str(binary)], input=payload, capture_output=True, text=True, check=True).stdout
    traces: List[List[EngineTick]] = []
    cur: List[EngineTick] = []
    for line in out.splitlines():
        if line.startswith("CASE"):
            cur = []
        elif line.startswith("T "):
            _, _, status, gems, tracked, cells = line.split(" ")
            cur.append(EngineTick(status, int(gems), int(tracked), [int(x) for x in cells.split(",")]))
        elif line == "END":
            traces.append(cur)
    return traces


# --------------------------------------------------------------------------
# levels
# --------------------------------------------------------------------------


@dataclass
class Level:
    rows: int
    cols: int
    cells: List[int]  # may contain planner target markers 90/91
    max_steps: int = 0
    gems_required: int = 999

    def text(self) -> str:
        body = "|".join(f"{c:02d}" for c in self.cells)
        return f"{self.rows}|{self.cols}|{self.max_steps}|{self.gems_required}|{body}"

    def engine_text(self) -> str:
        conv = {TARGET_GEM: GEM, TARGET_GEM_F: GEM_F}
        body = "|".join(f"{conv.get(c, c):02d}" for c in self.cells)
        return f"{self.rows}|{self.cols}|{self.max_steps}|{self.gems_required}|{body}"

    def target_index(self) -> int:
        for i, c in enumerate(self.cells):
            if c in (TARGET_GEM, TARGET_GEM_F):
                return i
        return -1


def parse_level_file(path: Path) -> Level:
    txt = "".join(l for l in path.read_text().splitlines(True) if not l.lstrip().startswith((";", "#")))
    parts = [p.strip() for p in txt.replace("\n", "").split("|") if p.strip() != ""]
    rows, cols, max_steps, gems = (int(x) for x in parts[:4])
    return Level(rows, cols, [int(x) for x in parts[4:]], 0, max(gems, 999))


def random_level(rng: random.Random, max_rows: int, max_cols: int) -> Level:
    rows = rng.randint(2, max_rows)
    cols = rng.randint(2, max_cols)
    n = rows * cols
    weights = {
        EMPTY: rng.uniform(0.15, 0.5),
        DIRT: rng.uniform(0.0, 0.35),
        STONE: rng.uniform(0.08, 0.3),
        GEM: rng.uniform(0.04, 0.2),
        STONE_F: 0.02,
        GEM_F: 0.02,
        WALL_BRICK: rng.uniform(0.0, 0.12),
        WALL_STEEL: rng.uniform(0.0, 0.06),
        EXIT_CLOSED: 0.01,
    }
    kinds, w = zip(*weights.items())
    cells = rng.choices(kinds, weights=w, k=n)
    cells[rng.randrange(n)] = AGENT
    gems = [i for i, c in enumerate(cells) if c in (GEM, GEM_F)]
    if gems and rng.random() < 0.9:
        t = rng.choice(gems)
        cells[t] = TARGET_GEM if cells[t] == GEM else TARGET_GEM_F
    return Level(rows, cols, cells)


def random_walk(rng: random.Random, length: int) -> str:
    # Bias towards continuing in the same direction so the agent actually
    # tunnels under things rather than jittering in place.
    out: List[int] = []
    cur = rng.randint(0, 4)
    for _ in range(length):
        if rng.random() < 0.45:
            cur = rng.choices([0, 1, 2, 3, 4], weights=[2, 2, 3, 3, 3])[0]
        out.append(cur)
    return "".join(map(str, out))


# --------------------------------------------------------------------------
# PDDL side
# --------------------------------------------------------------------------


def load_generator(domain: Path, explicit: Optional[Path] = None):
    """Return a callable level_text -> problem_text for the domain."""
    stem = domain.stem
    candidates = [explicit] if explicit else [
        domain.parent / f"problem_gen_{stem}.py",
        domain.parent / f"problem_gen_{stem.replace('domain_classic_', 'domain_')}.py",
        domain.parent / f"problem_gen_{stem.replace('domain_', '', 1)}.py",
    ]
    gen = next((c for c in candidates if c.exists()), None)
    if gen is None:
        raise FileNotFoundError(f"No problem generator next to {domain} (tried {[c.name for c in candidates]})")

    def generate(level_text: str, name: str = "fuzz") -> str:
        proc = subprocess.run([sys.executable, str(gen), level_text, "-p", name], capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"generator failed: {proc.stderr.strip()}")
        return proc.stdout

    return generate


CELL_RE = re.compile(r"c_(\d+)_(\d+)$")


@dataclass
class Outcome:
    states: List[FrozenSet[int]]
    steps: int
    explored: int
    agent_mid_tick: bool = False
    capped: bool = False
    branching: bool = False  # some physics step had >1 distinct successor


class PddlRunner:
    def __init__(self, task: Task, rows: int, cols: int, max_explore: int):
        self.task = task
        self.rows, self.cols = rows, cols
        self.max_explore = max_explore
        self.is_agent = lambda ga: ga.schema.startswith("move")
        self.is_auto = lambda ga: not ga.schema.startswith("move")
        t = task
        self.pred_atoms: Dict[str, Dict[Tuple[int, int], int]] = {}
        for aid, atom in enumerate(t.atoms):
            if len(atom) == 2:
                m = CELL_RE.match(atom[1])
                if m:
                    self.pred_atoms.setdefault(atom[0], {})[(int(m.group(1)) - 1, int(m.group(2)) - 1)] = aid
        self.nullary = {atom[0]: aid for aid, atom in enumerate(t.atoms) if len(atom) == 1}
        self.static_cells = set()
        for atom in t.static:
            if len(atom) == 2:
                m = CELL_RE.match(atom[1])
                if m:
                    self.static_cells.add((atom[0], (int(m.group(1)) - 1, int(m.group(2)) - 1)))

    def has(self, state, pred: str, rc) -> bool:
        if (pred, rc) in self.static_cells:
            return True
        aid = self.pred_atoms.get(pred, {}).get(rc)
        return aid is not None and aid in state

    def flag(self, state, pred: str) -> bool:
        if (pred,) in self.task.static:
            return True
        aid = self.nullary.get(pred)
        return aid is not None and aid in state

    def agent_pos(self, state) -> Optional[Tuple[int, int]]:
        for rc, aid in self.pred_atoms.get("agent-at", {}).items():
            if aid in state:
                return rc
        return None

    def settle(self, state: FrozenSet[int]) -> Outcome:
        """Apply physics actions to quiescence, exploring every interleaving."""
        finals: List[FrozenSet[int]] = []
        seen = {state}
        stack = [(state, 0)]
        max_depth = 0
        agent_mid = capped = branching = False
        while stack:
            s, depth = stack.pop()
            max_depth = max(max_depth, depth)
            auto = self.task.applicable(s, self.is_auto)
            if not auto:
                finals.append(s)
                continue
            if depth > 0 and self.task.applicable(s, self.is_agent):
                agent_mid = True
            succs = {ga.apply(s) for ga in auto}
            if len(succs) > 1:
                branching = True
            for ns in succs:
                if ns not in seen:
                    seen.add(ns)
                    stack.append((ns, depth + 1))
            if len(seen) > self.max_explore:
                capped = True
                break
        uniq = list(dict.fromkeys(finals))
        return Outcome(uniq, max_depth, len(seen), agent_mid, capped, branching)

    def choose_move(self, state, direction: int):
        pos = self.agent_pos(state)
        moves = self.task.applicable(state, self.is_agent)
        noop = [m for m in moves if m.schema == "move_noop"]
        if pos is None:
            return None, "no agent"
        if direction != 0:
            dr, dc = DIRS[direction]
            target = (pos[0] + dr, pos[1] + dc)
            hits = [m for m in moves if m.schema != "move_noop" and self.agent_pos(m.apply(state)) == target]
            succ = {m.apply(state) for m in hits}
            if len(succ) > 1:
                return hits[0], "ambiguous move: " + ", ".join(m.label for m in hits)
            if hits:
                return hits[0], None
        if noop:
            return noop[0], None
        return None, "no move_noop (cannot wait)"

    def board(self, state) -> List[str]:
        out = []
        for r in range(self.rows):
            for c in range(self.cols):
                rc = (r, c)
                kinds = []
                if self.has(state, "agent-at", rc):
                    kinds.append("agent")
                for p in ("stone", "gem", "dirt", "empty", "brick"):
                    if self.has(state, p, rc):
                        kinds.append(p)
                if len(kinds) != 1:
                    out.append("?" + "+".join(kinds))
                    continue
                k = kinds[0]
                if k in ("stone", "gem") and self.has(state, "falling", rc):
                    k += "~"
                out.append(k)
        return out

    def target(self, state) -> int:
        for (r, c), aid in self.pred_atoms.get("target-gem", {}).items():
            if aid in state and 0 <= r < self.rows and 0 <= c < self.cols:
                return r * self.cols + c
        return -1


def engine_board(cells: Sequence[int]) -> List[str]:
    m = {AGENT: "agent", EMPTY: "empty", DIRT: "dirt", STONE: "stone", STONE_F: "stone~", GEM: "gem", GEM_F: "gem~"}
    return [m.get(c, "brick" if c in WALL_IDS else f"id{c}") for c in cells]


# --------------------------------------------------------------------------
# comparison
# --------------------------------------------------------------------------


@dataclass
class CaseResult:
    ok: bool
    kind: str = ""
    detail: str = ""
    tick: int = -1
    steps: List[int] = field(default_factory=list)
    branching_ticks: int = 0


def render(board: List[str], rows: int, cols: int, agent_dead: bool = False) -> List[str]:
    sym = {"agent": "@", "empty": " ", "dirt": ".", "stone": "o", "stone~": "O", "gem": "*", "gem~": "%", "brick": "#"}
    lines = []
    for r in range(rows):
        lines.append("".join(sym.get(board[r * cols + c], "?") for c in range(cols)))
    return lines


def compare_case(task: Task, level: Level, actions: str, trace: List[EngineTick], max_explore: int,
                 strict_falling: bool, check_target: bool) -> CaseResult:
    runner = PddlRunner(task, level.rows, level.cols, max_explore)
    state = task.init_state
    out = runner.settle(state)
    if len(out.states) != 1:
        return CaseResult(False, "init-nondeterministic", f"{len(out.states)} initial outcomes")
    state = out.states[0]
    steps: List[int] = []
    branching_ticks = 0

    def diff(tick: int, eng: EngineTick, st) -> Optional[CaseResult]:
        eb = engine_board(eng.cells)
        pb = runner.board(st)
        p_alive = runner.flag(st, "agent-alive")
        e_alive = eng.status == "A"
        if e_alive != p_alive:
            return CaseResult(False, "death", f"engine {'alive' if e_alive else 'dead'} vs pddl {'alive' if p_alive else 'dead'}", tick)
        if not e_alive:
            return None
        bad = []
        for i, (a, b) in enumerate(zip(eb, pb)):
            if a == b:
                continue
            if not strict_falling and a.rstrip("~") == b.rstrip("~"):
                continue
            bad.append((i, a, b))
        if bad:
            kinds = Counter(f"{a}->{b}" for _, a, b in bad)
            only_falling = all(a.rstrip("~") == b.rstrip("~") for _, a, b in bad)
            kind = "falling-flag" if only_falling else "board"
            cells = ", ".join(f"({i // level.cols},{i % level.cols}) engine={a} pddl={b}" for i, a, b in bad[:6])
            return CaseResult(False, kind, f"{dict(kinds)}: {cells}", tick)
        if check_target and level.target_index() >= 0:
            pt = runner.target(st)
            if pt != eng.tracked:
                return CaseResult(False, "target", f"target gem engine={eng.tracked} pddl={pt}", tick)
        return None

    def done(res: CaseResult) -> CaseResult:
        res.steps = steps
        res.branching_ticks = branching_ticks
        return res

    res = diff(0, trace[0], state)
    if res:
        return res
    for tick, ch in enumerate(actions, start=1):
        eng = trace[tick]
        if not runner.flag(state, "agent-alive"):
            break
        move, err = runner.choose_move(state, int(ch))
        if move is None:
            return done(CaseResult(False, "no-move", f"{DIR_NAMES[int(ch)]}: {err}", tick))
        if err:
            return done(CaseResult(False, "ambiguous-move", err, tick))
        out = runner.settle(move.apply(state))
        steps.append(out.steps)
        branching_ticks += int(out.branching)
        if out.capped:
            return done(CaseResult(False, "explore-cap", f">{max_explore} intermediate states", tick))
        if not out.states:
            return done(CaseResult(False, "stuck", "physics reached no quiescent state", tick))
        if out.agent_mid_tick:
            return done(CaseResult(False, "agent-mid-tick", "agent action applicable while physics pending", tick))
        if len(out.states) > 1:
            # report whether any of the outcomes matches the engine
            matches = [s for s in out.states if diff(tick, eng, s) is None]
            return done(CaseResult(False, "nondeterministic",
                                   f"{len(out.states)} end-of-tick states ({len(matches)} match engine) after {DIR_NAMES[int(ch)]}", tick))
        state = out.states[0]
        res = diff(tick, eng, state)
        if res:
            res.detail = f"after {DIR_NAMES[int(ch)]} ({move.label}): {res.detail}"
            prev = engine_board(trace[tick - 1].cells)
            res.detail += "\n      before:  " + " | ".join(render(prev, level.rows, level.cols))
            res.detail += "\n      engine:  " + " | ".join(render(engine_board(eng.cells), level.rows, level.cols))
            res.detail += "\n      pddl:    " + " | ".join(render(runner.board(state), level.rows, level.cols))
            return done(res)
    return CaseResult(True, steps=steps, branching_ticks=branching_ticks)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", required=True, type=Path)
    ap.add_argument("--generator", type=Path, help="problem generator script (default: problem_gen_*.py next to the domain)")
    ap.add_argument("--cases", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-rows", type=int, default=6)
    ap.add_argument("--max-cols", type=int, default=7)
    ap.add_argument("--walk", type=int, default=25, help="actions per case")
    ap.add_argument("--level", type=Path, action="append", help="use these level files instead of random levels")
    ap.add_argument("--cases-file", type=Path, action="append",
                    help="fixed regression cases, one per line: name;level string;action digits")
    ap.add_argument("--max-explore", type=int, default=20000)
    ap.add_argument("--no-strict-falling", action="store_true", help="ignore falling-flag-only differences")
    ap.add_argument("--no-target", action="store_true", help="do not check the target gem position")
    ap.add_argument("--show", type=int, default=5, help="print this many failures")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    generate = load_generator(args.domain, args.generator)
    domain_text = args.domain.read_text()

    cases: List[Tuple[Level, str]] = []
    for cf in args.cases_file or []:
        for line in cf.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            _, lvl_str, acts = line.split(";")
            parts = [int(x) for x in lvl_str.split("|") if x.strip() != ""]
            cases.append((Level(parts[0], parts[1], parts[4:], parts[2], parts[3]), acts.strip()))
    n_random = 0 if args.cases_file and args.cases == ap.get_default("cases") else args.cases
    for i in range(n_random):
        if args.level:
            per = max(1, n_random // len(args.level))
            lvl = parse_level_file(args.level[min(i // per, len(args.level) - 1)])
        else:
            lvl = random_level(rng, args.max_rows, args.max_cols)
        cases.append((lvl, random_walk(rng, args.walk)))
    traces = run_engine([(lvl.engine_text(), acts, lvl.target_index()) for lvl, acts in cases])

    failures: Counter = Counter()
    shown = 0
    all_steps: List[int] = []
    total_branching = 0
    t0 = time.time()
    task_cache: Dict[str, Task] = {}
    for idx, ((lvl, acts), trace) in enumerate(zip(cases, traces)):
        task = task_cache.get(lvl.text())
        if task is None:
            try:
                problem = generate(lvl.text(), f"fuzz{idx}")
            except RuntimeError as exc:
                failures["generator"] += 1
                if shown < args.show:
                    print(f"[case {idx}] generator: {exc}")
                    shown += 1
                continue
            task = load_task(domain_text, problem)
            if args.level:
                task_cache = {lvl.text(): task}  # keep only the current level
        res = compare_case(task, lvl, acts, trace, args.max_explore,
                           not args.no_strict_falling, not args.no_target)
        all_steps.extend(res.steps)
        total_branching += res.branching_ticks
        if not res.ok:
            failures[res.kind] += 1
            if shown < args.show:
                shown += 1
                print(f"[case {idx}] {res.kind} at tick {res.tick}: {res.detail}")
                print(f"      level:   {lvl.text()}")
                print(f"      actions: {acts}")
    n_fail = sum(failures.values())
    avg_steps = sum(all_steps) / len(all_steps) if all_steps else 0.0
    print(f"{args.domain.name}: {len(cases) - n_fail}/{len(cases)} cases match the engine "
          f"({time.time() - t0:.1f}s, avg physics steps/tick {avg_steps:.1f})")
    print(f"  ticks where some physics step had several distinct successors: {total_branching}/{len(all_steps)}")
    if failures:
        print("  failures by kind: " + ", ".join(f"{k}={v}" for k, v in failures.most_common()))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
