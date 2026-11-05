#!/usr/bin/env python3
"""Plan with a PDDL model, then replay the plan in the real engine.

A small greedy best-first search over agent moves: every successor is one
move_* action followed by physics (non-move / __FORCED__) actions until none is
applicable, i.e. forced-action semantics.  If several physics actions are
applicable the first by name is taken (as tools/validate_pddl.py does).  The
heuristic is the Manhattan distance from the agent to the target gem.

The plan is then executed in stonesngems (tools/sim_check/build/engine_trace)
and the run counts as valid only if the engine agent is alive and the target
gem (followed by engine object id) has been collected.

This is not a replacement for Fast Downward; it measures how expensive the
model's transitions are and whether its plans work in the real game.

Usage:
  python3 tools/sim_check/plan_check.py --domain pddl/test_domains_target/domain_FA_scanner_combined.pddl \
      pddl/test_problems/h1/bd_level_01_start_gem_001_target_gem_005.txt [...]
"""

from __future__ import annotations

import argparse
import heapq
import itertools
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fuzz import CELL_RE, Level, load_generator, parse_level_file, run_engine  # noqa: E402
from pddl_exec import TRUE, GroundAction, Task, holds, load_task, task_stats  # noqa: E402

DIR_CODE = {(0, 0): "0", (-1, 0): "1", (0, 1): "2", (1, 0): "3", (0, -1): "4"}


class MacroModel:
    def __init__(self, task: Task):
        self.task = task
        self.moves = [ga for ga in task.ground_actions if ga.schema.startswith("move")]
        self.move_index: Dict[int, List[GroundAction]] = {}
        for aid in task.index_keys:
            acts = [ga for ga in task.index[aid] if ga.schema.startswith("move")]
            if acts:
                self.move_index[aid] = acts
        self.move_keys = frozenset(self.move_index)
        self.phys_index: Dict[int, List[GroundAction]] = {}
        for aid in task.index_keys:
            acts = sorted((ga for ga in task.index[aid] if not ga.schema.startswith("move")), key=lambda g: g.label)
            if acts:
                self.phys_index[aid] = acts
        self.phys_keys = frozenset(self.phys_index)
        self.unindexed_phys = sorted((ga for ga in task.unindexed if not ga.schema.startswith("move")), key=lambda g: g.label)
        self.agent_atoms: Dict[int, Tuple[int, int]] = {}
        self.target_atoms: Dict[int, Tuple[int, int]] = {}
        for aid, atom in enumerate(task.atoms):
            if len(atom) == 2:
                m = CELL_RE.match(atom[1])
                if not m:
                    continue
                rc = (int(m.group(1)), int(m.group(2)))
                if atom[0] == "agent-at":
                    self.agent_atoms[aid] = rc
                elif atom[0] == "target-gem":
                    self.target_atoms[aid] = rc
        self.physics_steps = 0

    @staticmethod
    def apply_inplace(ga: GroundAction, state: Set[int]) -> None:
        adds: List[int] = []
        dels: List[int] = []
        for cond, add, dele in ga.effs:
            if cond is TRUE or holds(cond, state):
                adds.extend(add)
                dels.extend(dele)
        state.difference_update(dels)
        state.update(adds)

    def physics_closure(self, state: Set[int], limit: int = 200000) -> None:
        for _ in range(limit):
            chosen = None
            for aid in sorted(self.phys_keys & state):
                for ga in self.phys_index[aid]:
                    if holds(ga.pre, state):
                        chosen = ga
                        break
                if chosen:
                    break
            if chosen is None:
                for ga in self.unindexed_phys:
                    if holds(ga.pre, state):
                        chosen = ga
                        break
            if chosen is None:
                return
            self.apply_inplace(chosen, state)
            self.physics_steps += 1
        raise RuntimeError("physics did not settle")

    def successors(self, state: frozenset):
        for aid in self.move_keys & state:
            for ga in self.move_index[aid]:
                if holds(ga.pre, state):
                    s = set(state)
                    self.apply_inplace(ga, s)
                    self.physics_closure(s)
                    yield ga, frozenset(s)

    def agent(self, state) -> Optional[Tuple[int, int]]:
        for aid in state:
            rc = self.agent_atoms.get(aid)
            if rc:
                return rc
        return None

    def h(self, state) -> int:
        a = self.agent(state)
        if a is None:
            return 10 ** 6
        for aid in state:
            rc = self.target_atoms.get(aid)
            if rc:
                return abs(rc[0] - a[0]) + abs(rc[1] - a[1])
        return 0


def gbfs(model: MacroModel, max_expansions: int, timeout: float):
    task = model.task
    s0 = set(task.init_state)
    model.physics_closure(s0)
    s0 = frozenset(s0)
    counter = itertools.count()
    frontier = [(model.h(s0), next(counter), s0)]
    parent: Dict[frozenset, Tuple[Optional[frozenset], Optional[GroundAction]]] = {s0: (None, None)}
    expansions = 0
    t0 = time.time()
    while frontier:
        _, _, s = heapq.heappop(frontier)
        if holds(task.goal, s):
            plan = []
            while parent[s][0] is not None:
                prev, act = parent[s]
                plan.append(act)
                s = prev
            return list(reversed(plan)), expansions
        expansions += 1
        if expansions > max_expansions or time.time() - t0 > timeout:
            return None, expansions
        for act, ns in model.successors(s):
            if ns not in parent:
                parent[ns] = (s, act)
                heapq.heappush(frontier, (model.h(ns), next(counter), ns))
    return None, expansions


def plan_directions(model: MacroModel, plan: List[GroundAction]) -> str:
    out = []
    for ga in plan:
        if ga.schema == "move_noop":
            out.append("0")
            continue
        parts = ga.label.strip("()").split()
        src = CELL_RE.match(parts[1])
        dst = CELL_RE.match(parts[2])
        d = (int(dst.group(1)) - int(src.group(1)), int(dst.group(2)) - int(src.group(2)))
        out.append(DIR_CODE[d])
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--domain", required=True, type=Path)
    ap.add_argument("--generator", type=Path)
    ap.add_argument("--max-expansions", type=int, default=5000)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("levels", nargs="+", type=Path)
    args = ap.parse_args()
    generate = load_generator(args.domain, args.generator)
    domain_text = args.domain.read_text()
    print(f"domain: {args.domain}")
    for lvl_path in args.levels:
        level: Level = parse_level_file(lvl_path)
        t0 = time.time()
        task = load_task(domain_text, generate(level.text(), lvl_path.stem))
        t_ground = time.time() - t0
        stats = task_stats(task)
        model = MacroModel(task)
        t1 = time.time()
        plan, expansions = gbfs(model, args.max_expansions, args.timeout)
        t_search = time.time() - t1
        line = (f"  {lvl_path.name}: operators={stats['operators']} ground={t_ground:.1f}s "
                f"search={t_search:.1f}s expansions={expansions} physics_steps={model.physics_steps}")
        if plan is None:
            print(line + " -> no plan")
            continue
        dirs = plan_directions(model, plan)
        trace = run_engine([(level.engine_text(), dirs, level.target_index())])[0]
        final = trace[-1]
        valid = final.status == "A" and final.tracked == -1
        print(line + f" plan_len={len(plan)} engine_replay={'VALID' if valid else 'INVALID'}"
              f" (agent {'alive' if final.status == 'A' else 'dead'}, target {'collected' if final.tracked == -1 else 'not collected'})")
        print(f"    directions: {dirs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
