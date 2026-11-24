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
replayed in the engine). With Fast Downward 24.06.1 (A* + hmax) the four
classic files all give the optimal 12 moves on `pddl/level_10_10.txt` and 8
moves on `pddl/level_5_5_high_stone.txt`, and those plans replay correctly in
the engine. See "Problem size" below for the translator on 20x38 levels.

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

### Problem size (Fast Downward translator)

Fast Downward 24.06.1 translator, default settings, on the 20x38 benchmark
level `test_problems/h1/bd_level_01_start_gem_001_target_gem_005.txt` (the FA
files give the same numbers; they differ only in action names):

| variant | SAS operators | SAS variables | translate time | peak memory |
|---|---|---|---|---|
| `*_scanner_combined` | 18,168 | 4,881 | 22 s | 255 MB |
| `*_scanner_separated` | 37,535 | 4,311 | 16 s | 259 MB |
| `*_non-scanner_combined` | 20,313 | 4,713 | 24 s | 395 MB |
| `*_non-scanner_separated` | 30,659 | 5,833 | 17 s | 243 MB |

Every 15th level of `test_problems/h1` and `h2` (22 levels; all the same map
with different start / target gems) gives the same picture: each model
translates in 15-26 s using at most 400 MB, with 18,168 (`scanner_combined`),
37,535-37,977 (`scanner_separated`), 20,313 (`non-scanner_combined`) and
30,659-30,883 (`non-scanner_separated`) operators. Before the fix all four
models ran out of memory (3 GB) on the level in the table. With
`*_scanner_combined`, Fast Downward's `lama-first` now solves that level in 18 s
of search (32 moves; the plan is valid when replayed in the engine).

Reproduce with the translator alone (`fast-downward.py --translate`), e.g.

```bash
python3 pddl/problem_gen_rowscan.py pddl/test_problems/h1/bd_level_01_start_gem_001_target_gem_005.txt > /tmp/h1.pddl
```

```bash
fast-downward.py --translate pddl/test_domains_target/domain_classic_scanner_combined.pddl /tmp/h1.pddl
```

(`problem_gen_cellscan.py` for the scanner-separated files,
`problem_gen_orderfree.py` for the non-scanner ones.) The translator prints
`Translator operators: N`.

**No negated preconditions on "one per level" facts.** FD's invariant
synthesis turns every predicate of which at most one atom can be true into a
single variable with one value per cell: always `agent-at`, `target-gem`
(together with `got-gem`) and the scan pointer `scan-at`, and `stone` / `gem` /
`obj` on a level with only one stone or gem. On the 20x38 level above these
are `agent-at` with 695-760 values and `target-gem` / `got-gem` with 459-495,
depending on the model. The translator compiles a negated precondition (or
effect condition) on such a fact into one operator per *other* value of that
variable. Until this was fixed, every 20x38 level in `test_problems/h1` and
`h2` failed with a `MemoryError` in `translate_strips_operators` at 3 GB, for
all four models; on `pddl/test_mini.txt` (19x11, a single gem)
`*_scanner_separated` gave 309,841 operators, 162,184 of them from
`move_into_gem` (`(not (target-gem ?to))`: 776 groundings x 209 values), most
of the rest from `not_fall` (`(not (agent-at ?down))`) and `not_roll_left` /
`not_roll_right` (`(not (gem ?down))`, `gem` being one variable on that
level). The domains now avoid this:

- `move_into_gem` also collects the target gem, with the conditional effect
  `(when (target-gem ?to) (and (got-gem) (not (target-gem ?to))))`, instead of
  a separate `move_into_target_gem` and a `(not (target-gem ?to))`
  precondition (the physics actions already carry the marker with
  `(when (target-gem ?c) ...)`; positive effect conditions do not expand);
- `not_fall`, `not_roll_left` and `not_roll_right` (separated models) test
  the support cell positively over its contents, e.g. "not empty, and not the
  agent unless the object is resting" is
  `(or (dirt ?down) (stone ?down) (gem ?down) (rounded-wall ?down) (flat-wall ?down) (and (agent-at ?down) (not (falling ?c))))`.

The negations left are on `empty`, `falling`, `updated`, `pending`, `pushed`,
`row-dirty` and 0-ary flags. Each of these predicates is added somewhere
without a matching delete (e.g. `empty` when the agent mines dirt), so the
translator never builds such a variable for them.

`pddl/test_mini.txt` (19x11, one gem), SAS operators before / after:

| variant | before | after |
|---|---|---|
| `*_scanner_combined` | 1,338 | 1,337 |
| `*_scanner_separated` | 309,841 | 8,654 |
| `*_non-scanner_combined` | 1,129 | 1,128 |
| `*_non-scanner_separated` | 272,008 | 7,250 |

On this level the combined models had nothing to expand: relaxed
reachability already keeps the agent in the top row (11 `agent-at` values) and
the gem on its start cell (1 `target-gem` value). In the separated models the
check and act actions are linked only by 0-ary flags (`can_fall`, ...), which
makes relaxed reachability much coarser: 209 cells are reachable for the
agent and the gem, hence the expansion. On the 20x38 levels every model has
large `agent-at` and `target-gem` variables (see above).

`tools/sim_check/plan_check.py` finds a 30-move plan on the 20x38 level above
with each model, and the plan is valid when replayed in the engine.

The table used to show `tools/sim_check/pddl_exec.task_stats` estimates
(~16.6k / ~32.5k / ~7.6k / ~8.7k). They count STRIPS operators and do not
model the negation expansion, so they did not show the problem; use the FD
translator for operator counts.
