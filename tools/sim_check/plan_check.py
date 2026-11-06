#!/usr/bin/env python3
"""Plan with a PDDL model, then replay the plan in the real engine.

A small greedy best-first search over agent moves: every successor is one
move_* action followed by physics (non-move / __FORCED__) actions until none is
applicable, i.e. forced-action semantics.  If several physics actions are
applicable the first by name is taken (as tools/validate_pddl.py does).  The
heuristic is the shortest path from the agent to the target gem, or with
--collect-gems N (goal: any N gems) the gems still missing, then the shortest
path to the nearest gem.

The plan is then executed in stonesngems (tools/sim_check/build/engine_trace)
and the run counts as valid only if the engine agent is alive and the target
gem (followed by engine object id) has been collected, or with --collect-gems
the engine has counted at least N collected gems.

This is not a replacement for Fast Downward; it measures how expensive the
model's transitions are and whether its plans work in the real game.

Usage:
  python3 tools/sim_check/plan_check.py --domain pddl/test_domains_target/domain_FA_scanner_combined.pddl \
      pddl/test_problems/h1/bd_level_01_start_gem_001_target_gem_005.txt [...]
  python3 tools/sim_check/plan_check.py --domain ... --collect-gems 3 LEVEL.txt
"""

from __future__ import annotations

import argparse
import heapq
import itertools
import re
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
    def __init__(self, task: Task, collect_gems: Optional[int] = None):
        self.task = task
        self.collect_gems = collect_gems
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
        self.gem_atoms: Dict[int, Tuple[int, int]] = {}
        self.count_atoms: Dict[int, int] = {}  # (gems-collected gems_k) -> k
        for aid, atom in enumerate(task.atoms):
            if len(atom) == 2 and atom[0] == "gems-collected":
                self.count_atoms[aid] = int(atom[1].rsplit("_", 1)[1])
            elif len(atom) == 2:
                m = CELL_RE.match(atom[1])
                if not m:
                    continue
                rc = (int(m.group(1)), int(m.group(2)))
                if atom[0] == "agent-at":
                    self.agent_atoms[aid] = rc
                elif atom[0] == "target-gem":
                    self.target_atoms[aid] = rc
                elif atom[0] == "gem":
                    self.gem_atoms[aid] = rc
        self.physics_steps = 0
        # open-cell adjacency (4-neighbourhood) and per-cell stone atoms for the heuristic
        open_cells = {rc for rc in self.agent_atoms.values()}
        self.neighbours: Dict[Tuple[int, int], List[Tuple[int, int]]] = {
            (r, c): [n for n in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)) if n in open_cells]
            for (r, c) in open_cells
        }
        self.stone_atoms: Dict[int, Tuple[int, int]] = {}
        for aid, atom in enumerate(task.atoms):
            if len(atom) == 2 and atom[0] == "stone":
                m = CELL_RE.match(atom[1])
                if m:
                    self.stone_atoms[aid] = (int(m.group(1)), int(m.group(2)))

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
        """Shortest path from the agent to the target gem through cells the
        agent could enter (stones block); Manhattan distance + 100 if none.
        Gem-count goal: 1000 per gem still missing beyond the next one, plus
        the shortest path to the nearest gem."""
        a = self.agent(state)
        if a is None:
            return 10 ** 6
        if self.collect_gems is not None:
            have = max((self.count_atoms[aid] for aid in state if aid in self.count_atoms), default=0)
            missing = self.collect_gems - have
            if missing <= 0:
                return 0
            gems = {self.gem_atoms[aid] for aid in state if aid in self.gem_atoms}
            if not gems:
                return 10 ** 6
            return (missing - 1) * 1000 + self.path_length(state, a, gems)
        target = next((self.target_atoms[aid] for aid in state if aid in self.target_atoms), None)
        if target is None:
            return 0
        return self.path_length(state, a, {target})

    def path_length(self, state, a: Tuple[int, int], targets: Set[Tuple[int, int]]) -> int:
        stones = {self.stone_atoms[aid] for aid in state if aid in self.stone_atoms}
        frontier, dist = [a], {a: 0}
        while frontier:
            nxt = []
            for cell in frontier:
                if cell in targets:
                    return dist[cell]
                for n in self.neighbours.get(cell, ()):
                    if n not in dist and n not in stones:
                        dist[n] = dist[cell] + 1
                        nxt.append(n)
            frontier = nxt
        return min(abs(t[0] - a[0]) + abs(t[1] - a[1]) for t in targets) + 100


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
    ap.add_argument("--collect-gems", default=None, metavar="N|level",
                    help="goal: any N gems instead of the target gem ('level': the level's required_gems field)")
    ap.add_argument("levels", nargs="+", type=Path)
    args = ap.parse_args()
    domain_text = args.domain.read_text()
    print(f"domain: {args.domain}")
    for lvl_path in args.levels:
        level: Level = parse_level_file(lvl_path)
        # level.text() drops comment lines, so pass a `; collect-gems:` line on explicitly
        collect = args.collect_gems
        if collect is None:
            meta = re.search(r"^\s*[;#]\s*collect[-_]gems\s*:\s*(\S+)", lvl_path.read_text(), re.MULTILINE | re.IGNORECASE)
            collect = meta.group(1) if meta else None
        generate = load_generator(args.domain, args.generator, ["--collect-gems", collect] if collect else [])
        t0 = time.time()
        try:
            problem_text = generate(level.text(), lvl_path.stem)
        except RuntimeError as exc:
            print(f"  {lvl_path.name}: {exc}")
            continue
        task = load_task(domain_text, problem_text)
        t_ground = time.time() - t0
        stats = task_stats(task)
        goal_count = re.search(r"\(:goal \(and \(gems-collected gems_(\d+)\)", problem_text)
        model = MacroModel(task, int(goal_count.group(1)) if goal_count else None)
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
        if model.collect_gems is not None:
            done = final.gems >= model.collect_gems
            what = f"gems {final.gems}/{model.collect_gems}"
        else:
            done = final.tracked == -1
            what = f"target {'collected' if done else 'not collected'}"
        valid = final.status == "A" and done
        print(line + f" plan_len={len(plan)} engine_replay={'VALID' if valid else 'INVALID'}"
              f" (agent {'alive' if final.status == 'A' else 'dead'}, {what})")
        print(f"    directions: {dirs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
