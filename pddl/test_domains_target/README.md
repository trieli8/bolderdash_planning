# Test Domain Matrix

This folder contains the generated matrix requested from:

- `{domain, domain_FA, domain_plus}`
- `{scanner, non-scanner}`
- `{combined, separated}`
- `events/actions` only for `domain_plus`

## Source Mapping

- `domain_*` and `domain_FA_*` (all eight files are written by
  `python pddl/make_target_variants.py`; the classic file is the source unchanged,
  the FA file prefixes every physics action, i.e. every action that is not a
  `move_*` agent action, with `__FORCED__`)
  - `*_scanner_combined` -> `pddl/domain_rowscan.pddl` (row-gated scanner;
    problems from `pddl/problem_gen_rowscan.py`)
  - `*_scanner_separated` -> `pddl/domain_cellscan_separated.pddl` (cell-by-cell
    scanner with separate check / act actions; problems from
    `pddl/problem_gen_cellscan.py`)
  - `*_non-scanner_combined` -> `pddl/domain_orderfree_combined.pddl` (order-free
    physics with pending flags, one action per outcome; problems from
    `pddl/problem_gen_orderfree.py`)
  - `*_non-scanner_separated` -> `pddl/domain_orderfree_separated.pddl` (order-free
    physics with pending flags, select + check / act actions; problems from
    `pddl/problem_gen_orderfree.py`)

  The problem generator is picked through the `; source:` header
  (`problem_gen_common.py`, `tools/plan.py`, `tools/benchmarking/bench_config_matrix.py`).

  Goals: the target gem (`got-gem`), or any n gems with `--collect-gems N` / a
  `; collect-gems: N` line in the level file (`(gems-collected gems_n)`, a
  saturating counter stepped by the gem moves). See "Gem-count goal" in the
  top-level `README.md`.

- `domain_plus_*_actions`
  - `scanner_combined_actions` -> `pddl/domain_scanner_combined.pddl`
  - `scanner_separated_actions` -> `pddl/domain_scanner_separated.pddl`
  - `non-scanner_combined_actions` -> `pddl/domain_merged.pddl`
  - `non-scanner_separated_actions` -> `pddl/domain.pddl`

- `domain_plus_*_events`
  - `scanner_combined_events` -> `pddl/domain_plus_scanner_separated_events.pddl`
  - `scanner_separated_events` -> `pddl/domain_plus_scanner_separated_events.pddl`
  - `non-scanner_combined_events` -> `pddl/domain_plus_from_domain.pddl`
  - `non-scanner_separated_events` -> `pddl/domain_plus_from_domain.pddl`

## Validation

All 16 files were validated to solve `pddl/level_5_5.txt` by:

- generating a domain-matched problem with the appropriate generator script
- running `tools/plan.py` (`fd`) for non-event files
- running `tools/plan_plus.py` (`enhsp`) for event files

Observed status: all 16 solved.

The eight classic / FA files have since been rewritten (see "Engine
conformance" below); they were checked with `tools/sim_check` (differential
fuzzing, and plans found on `pddl/level_5_5.txt` and a 20x38 benchmark level
replayed in the engine). All eight also solve `pddl/level_5_5.txt` with
`tools/plan.py` (`fd`), and every plan replays correctly in the engine; see
"Problem size" below for the 20x38 level.

## Variant Problem Generators (No-Write)

Each domain variant has a matching generator script:

- `pddl/test_domains/problem_gen_<domain-file-stem>.py`

Examples:

- `python pddl/test_domains/problem_gen_domain_FA_scanner_combined.py pddl/level_5_5.txt -p test_case`
- `python pddl/test_domains/problem_gen_domain_plus_scanner_combined_events.py pddl/level_5_5.txt -p test_case`

Behavior:

- These scripts print the generated problem to `stdout` only.
- They do not write `<problem>.pddl` files anywhere.

## Engine conformance (tools/sim_check/fuzz.py)

Differential test against the stonesngems engine (random levels up to 6x7,
25-step random walks; full board, falling state, agent death and target-gem
position compared after every tick):

```bash
python3 tools/sim_check/fuzz.py --domain pddl/test_domains_target/<variant>.pddl --cases 500
python3 tools/sim_check/fuzz.py --domain pddl/test_domains_target/<variant>.pddl --cases-file tools/sim_check/regression_cases.txt
```

| variant | source | random (500) | regression | physics |
|---|---|---|---|---|
| `*_scanner_combined` | `domain_rowscan.pddl` | all (thousands of cases, also real benchmark levels) | 18/18 | one applicable action per step |
| `*_scanner_separated` | `domain_cellscan_separated.pddl` | 500/500 | 18/18 | one applicable action per step |
| `*_non-scanner_combined` | `domain_orderfree_combined.pddl` | 500/500 | 18/18 | unique end-of-tick state, objects in any admissible order |
| `*_non-scanner_separated` | `domain_orderfree_separated.pddl` | 500/500 | 18/18 | unique end-of-tick state, objects in any admissible order |

Classic and FA files give identical results (they differ only in action names).
Before the rewrite: scanner_combined 69/150, scanner_separated 28/60,
non-scanner_combined 22/60 (with nondeterministic ticks: a classic planner
could choose physics outcomes), non-scanner_separated 0/60 (no `move_noop`).

All four models encode the same engine rules (`stonesandgem/src/stonesngems_base.cpp`,
`RNDGameState::apply_action`): the agent moves first; falling stones *and*
gems landing on the agent kill it; only resting stones/gems and brick walls
(id 18) are rounded (steel walls, exits, the border and the agent are not);
a pushed stone is skipped for the rest of the push tick and is falling iff the
cell below its destination is empty; the target-gem marker moves with its gem;
an object that moved this tick is not updated again (engine `has_updated`).
Walls are encoded as `rounded-wall` / `flat-wall`, which the old
`pddl/problem_gen.py` / `pddl/problem_gen_scanner_separated.py` problems do not
provide, hence the new generators.

### Scanner, separated (`domain_cellscan_separated.pddl`)

A scan pointer visits every cell of the level in row-major order. A cell
without a stone/gem, or whose object already moved this tick (`updated`), is
passed by `skip_cell`. For a stone/gem, the engine's decision is split into
check actions (`can_fall` / `not_fall` / `fall_on_agent`, then
`can_roll_left` / `not_roll_left`, then `can_roll_right` / `not_roll_right`),
followed by one act action (`stone_fall`, `gem_fall`, `stone_roll_left`, ...,
`stone_gem_settle`) and `advance_scan`. Exactly one physics action is
applicable at every step of a tick, so the model is exact and fully
deterministic. It also matches the engine tick for tick on real 20x38
benchmark levels (`fuzz.py --level`). The cost is at least one physics step
per cell and tick: ~40 steps per tick on 6x7 levels, ~1250 on 20x38 levels,
where the row-gated `*_scanner_combined` skips unchanged rows and needs ~96.

### Non-scanner (`domain_orderfree_{combined,separated}.pddl`)

There is no scan order. After the agent moves, `start_tick` marks every
stone/gem `pending` (except a stone the agent just pushed). A pending object at
row r, column k may be updated as soon as no pending object is left in its
*conflict window*: (r, k-2), (r, k-1) and (r-1, k-2 .. k+2). These are exactly
the cells that come earlier in the engine's row-major scan and whose update
can read a cell this object's update writes, or write a cell it reads (an
object reads its own cell and the cells below, left, down-left, right and
down-right, and writes its own cell and the one it moves to). Every pair of
conflicting updates is therefore executed in the engine's order, and all other
pairs commute, so **every admissible order ends the tick in the engine's
state**. `end_tick` fires when nothing is pending.

`tools/sim_check/regression_cases.txt` has one case per window cell
(`window_*`) that becomes nondeterministic when that cell is dropped from the
window. The exception is (r, k-1), which is redundant: the left neighbour can
only leave its cell by falling (filling the down-left cell) or by rolling left
(which needs the down-left cell full), so this object can never roll into the
vacated cell, and symmetrically the neighbour can never roll right into this
object's cell. Dropping it changed nothing in testing; it stays in the window
because it is sound and removes interleavings.

- combined: one action per outcome (`physics_fall`, `physics_fall_on_agent`,
  `physics_roll_left`, `physics_roll_right`, `physics_settle`,
  `physics_settle_blocked`), each carrying the conflict window; exactly one of
  them is applicable per pending object.
- separated: `select_object` picks any pending object whose window is clear
  and locks it; then the same check / act decomposition as the scanner model
  runs on it (exactly one physics action applicable until the act releases it).

**Exact, but not step-deterministic (by design).** A planner can never choose a
physics *outcome*: the end-of-tick state is unique (the fuzzer explores every
interleaving and finds a single end state in every tick). But while a tick
runs, several independent objects are usually updatable at once (up to 4 at a
time in the fuzz cases, 289 / 3505 distinct intermediate states in the worst
tick for combined / separated). Making exactly one physics action applicable at
each step would need a fixed total order over the objects, which is a scanner,
i.e. it would remove the order-free style. Consequences:

- forced-action planners apply forced actions until none is applicable; any
  order is fine. In the separated model the candidate `select_object` actions
  disable each other (`busy`), so forced actions must be applied one at a time
  and re-checked (`tools/validate_pddl.py` now does this);
- classic planners see the interleavings as extra search, and it grows
  exponentially with the number of independent objects: every stone/gem is
  pending in every tick (leaving out the objects that provably stay put, those
  resting on a non-rounded support, would still leave 63 of the 123
  stones/gems pending on the 20x38 benchmark level below), and on that level a
  single tick already has more than 20,000 intermediate states
  (`fuzz.py --level ... --cases 1 --walk 2` stops at its exploration cap). For
  classic planners on benchmark-sized levels use a scanner variant; FA planners
  only follow one order. The exactness argument above does not depend on the
  level size, and plans found with forced-action semantics on that level replay
  correctly in the engine.

An agent killed by a falling object does not stop the physics (it does not
depend on `agent-alive`), so such a tick still ends in a unique state; no
`move_*` action is applicable afterwards.

### Problem size (20x38 benchmark level `test_problems/h1/bd_level_01_start_gem_001_target_gem_005.txt`)

Operator counts from `tools/sim_check/pddl_exec.task_stats` (after relaxed
reachability and disjunction splitting) and from the Fast Downward translator:

| variant | `task_stats` | FD translator |
|---|---|---|
| `*_scanner_combined` | ~16.6k | 19,847 |
| `*_scanner_separated` | ~32.5k | 36,823 |
| `*_non-scanner_combined` | ~7.6k | 21,992 |
| `*_non-scanner_separated` | ~8.7k | 29,909 |

`task_stats` does not model one translator step: FD merges mutually exclusive
facts into multi-valued variables (`agent-at` becomes one variable over every
cell the agent can reach, `target-gem` one over every cell the target gem can
reach), and a negated precondition on such a fact is compiled into one operator
copy per other value. Keep `(not (agent-at ...))` / `(not (target-gem ...))` out
of preconditions. Two did slip in: `move_into_gem` had `(not (target-gem ?to))`
in every variant (~1.16M operators; collecting the target gem is now a
conditional effect), and `not_fall` in the separated variants had
`(not (agent-at ?down))` (~1.07M / ~549k operators; now spelled out as the
other contents a full cell can have).

`tools/sim_check/plan_check.py` finds a 30-move plan on that level with each
of them, and the plan is valid when replayed in the engine. Fast Downward
through `tools/plan.py`, 300 s limit, FA variants with
`--planner-args "--search 'lazy_greedy([ff()], preferred=[ff()])'"`, classic
variants with the default search:

| variant | FA | classic |
|---|---|---|
| `*_scanner_combined` | 15.0 s, 41 expansions | 24.7 s, 5,551 expansions |
| `*_scanner_separated` | 24.3 s, 47 expansions | timeout |
| `*_non-scanner_combined` | 15.7 s, 43 expansions | timeout |
| `*_non-scanner_separated` | 17.0 s, 47 expansions | timeout |

Every plan has 30 agent moves and is valid when replayed in the engine.
Translation takes 9-13 s of each run. These times are with a cheaper per-state
GUI dump in `planners/fast-downward/src/search/utils/state_dump.cc`; with the
regex-based dump, `domain_FA_scanner_combined` needs 245 s (93% of it in the
dump) and the separated variants time out. `tools/plan.py`'s default search for
`*scanner_separated*` (which also matches `*non-scanner_separated*`) is eager
`astar(ff())`, which does not apply `__forced__` actions, so the FA separated
variants need the `--planner-args` above.

Gem-count goal on the same level (`--collect-gems`, `domain_FA_scanner_combined`,
same search): the target-gem problem still has 19,847 translator operators (its
counter is a single inert object); any 3 gems: 25,791 operators, 52 s, 43
moves; all 12 gems of the level's `required_gems` field (`--collect-gems level`):
48,660 operators, 216 s, 113 moves. Both plans are valid in the engine (12/12
gems collected, agent alive).
