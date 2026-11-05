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
  - `*_scanner_combined` -> `pddl/domain_rowscan.pddl` (scanner with row and
    column-block gates; problems from `pddl/problem_gen_rowscan.py`)
  - `*_scanner_separated` -> `pddl/domain_cellscan_separated.pddl` (row-gated
    scanner with separate check / act actions; problems from
    `pddl/problem_gen_cellscan.py`)
  - `*_non-scanner_combined` -> `pddl/domain_orderfree_combined.pddl` (order-free
    physics with pending and dirty flags, one action per outcome; problems from
    `pddl/problem_gen_orderfree.py`)
  - `*_non-scanner_separated` -> `pddl/domain_orderfree_separated.pddl` (order-free
    physics with pending and dirty flags, select + check / act actions; problems
    from `pddl/problem_gen_orderfree.py`)

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
conformance" below). They are checked against the engine with
`tools/sim_check`, and the classic files were run through Fast Downward
24.06.1 on eight levels (see "Performance"). Upstream Fast Downward treats
`__FORCED__` actions as ordinary actions, and the forced-action fork in
`planners/` was not reachable from the environment the measurements were made
in, so the FA files are covered by the fuzzer and by forced-action replays
(`tools/sim_check/plan_check.py`) only.

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
| `*_scanner_combined` | `domain_rowscan.pddl` | 500/500 (and 500/500 each with 2- and 3-column blocks, 200/200 on levels up to 30 columns, 4/4 on 20x38 levels) | 18/18 | one applicable action per step |
| `*_scanner_separated` | `domain_cellscan_separated.pddl` | 500/500 (and 4/4 on 20x38 levels) | 18/18 | one applicable action per step |
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
provide, hence the new generators. Collecting a gem is one action,
`move_into_gem`, which sets `got-gem` when the gem is the target (see
"Performance" for why there is no separate `move_into_target_gem`).

### Why only part of the board is updated

The engine updates every object in every tick, but an object whose
surroundings did not change since its last update provably stays put: a
resting object with a non-empty support that cannot roll keeps doing nothing.
Within a tick, an update can only *block* objects later in the scan, never
enable them: a later object's support (the cell below it) and down-right cell
cannot be changed by earlier objects, its left, down-left and right cells
can only be filled, or vacated by a left neighbour that falls into (or needs a
full) down-left cell. So it is enough to revisit the objects that read a cell
that was vacated (the cell itself, above, left, right, up-left, up-right), whose
support stopped falling (the object above), or that moved (they are falling).
All models below use this.

### Scanner, combined (`domain_rowscan.pddl`)

Row-major scan with the engine's `has_updated` skipping. Rows have gates that
skip the whole row unless it is dirty; on levels wider than 16 columns, a
scanned row is further split into blocks of 8 columns with their own gates,
and a change dirties only the blocks of the cells that read it. Narrower
levels have no block gates (they did not pay off there).
`ROWSCAN_BLOCK_WIDTH=<n>` forces n-column blocks (used to fuzz block
boundaries on small levels).

### Scanner, separated (`domain_cellscan_separated.pddl`)

The scan pointer visits the open (non-wall) cells of a dirty row one at a
time (rows have the same gates as scanner-combined). A cell without a
stone/gem, or whose object already moved this tick (`updated`), is passed by
`skip_cell` / `skip_updated`. For a stone/gem, the engine's decision is split
into check actions (`can_fall` / `not_fall` / `fall_on_agent`, then
`can_roll_left` / `not_roll_left`, then `can_roll_right` / `not_roll_right`),
followed by one act action (`stone_fall`, `gem_fall`, `stone_roll_left`, ...,
`stone_gem_settle`) and `advance_scan`. Exactly one physics action is
applicable at every step of a tick, so the model is exact and fully
deterministic.

### Non-scanner (`domain_orderfree_{combined,separated}.pddl`)

There is no scan order. Every change marks the objects that read the changed
cell `dirty`; after the agent moves, `start_tick` makes the dirty stones/gems
`pending` (except a stone the agent just pushed, which stays dirty for the
next tick). The generator marks only the objects that can move on the initial
board. A pending object at row r, column k may be updated as soon as no
pending object is left in its *conflict window*: (r, k-2), (r, k-1) and
(r-1, k-2 .. k+2). These are exactly the cells that come earlier in the
engine's row-major scan and whose update can read a cell this object's update
writes, or write a cell it reads (an object reads its own cell and the cells
below, left, down-left, right and down-right, and writes its own cell and the
one it moves to). Every pair of conflicting updates is therefore executed in
the engine's order, and all other pairs commute, so **every admissible order
ends the tick in the engine's state**. `end_tick` fires when nothing is
pending.

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
runs, independent pending objects can be updated in any order. Making exactly
one physics action applicable at each step would need a fixed total order over
the objects, which is a scanner, i.e. it would remove the order-free style.
Consequences:

- forced-action planners apply forced actions until none is applicable; any
  order is fine. In the separated model the candidate `select_object` actions
  disable each other (`busy`), so forced actions must be applied one at a time
  and re-checked (`tools/validate_pddl.py` does this);
- classic planners see the interleavings as extra search. In quiet ticks there
  are few of them (on the 20x38 benchmark levels 4.6-6.3 / 17.7-36.3
  intermediate states per tick on average for combined / separated), but when many independent
  objects fall at once (the opening rockfall of those levels: 6 of 40 measured
  ticks) a tick has more than 5,000. Every intermediate state has the same FF
  value (the "nothing pending" test of `end_tick` is a universally quantified
  precondition, i.e. a negated axiom that the delete relaxation does not see),
  so greedy search has to sweep the whole plateau: Fast Downward needs 13,827
  expansions for the first tick of that level and does not solve it in 300 s.
  On benchmark-sized levels, use a scanner variant with classic planners.

An agent killed by a falling object does not stop the physics (it does not
depend on `agent-alive`), so such a tick still ends in a unique state; no
`move_*` action is applicable afterwards.

## Performance

`tools/sim_check/model_stats.py` with Fast Downward 24.06.1
(`lazy_greedy([ff()],preferred=[ff()])`, the default of `tools/plan.py`;
300 s per run, the timeout counting translation) on the classic files.
"before" is the previous version of each model, "operator fix only" adds just
the first change listed below, "now" is the current version. Cells: search
time (Fast Downward's "Total time", which does not include translation) /
expansions / translator operators; end-to-end wall times on the 20x38 levels,
translation included, are in the list below the tables. steps/tick: physics actions per game tick
along the same random walks (forced-action semantics); states/tick: distinct
intermediate states of a tick when every order of physics actions is explored
(capped at 5,000).

#### `*_scanner_combined`

| level | before | operator fix only | now | steps/tick before -> now |
|---|---|---|---|---|
| 5x5 | 0.02s / 177 exp / 279 ops | 0.01s / 177 exp / 276 ops | 0.01s / 177 exp / 276 ops | 13.5 -> 13.5 |
| 5x5 stones | 0.07s / 255 exp / 1050 ops | 0.02s / 255 exp / 420 ops | 0.02s / 255 exp / 420 ops | 11.2 -> 11.2 |
| 5x5 brick | 0.01s / 163 exp / 245 ops | 0.01s / 163 exp / 243 ops | 0.01s / 163 exp / 243 ops | 9.5 -> 9.5 |
| 10x10 | 3.33s / 1084 exp / 14811 ops | 0.27s / 1084 exp / 1731 ops | 0.30s / 1084 exp / 1731 ops | 45.0 -> 45.0 |
| 10x5 | 0.48s / 619 exp / 3906 ops | 0.08s / 619 exp / 816 ops | 0.08s / 619 exp / 816 ops | 27.6 -> 27.6 |
| 6x11 | 1.08s / 288 exp / 16801 ops | 0.08s / 288 exp / 1621 ops | 0.09s / 288 exp / 1621 ops | 18.9 -> 18.9 |
| 20x38 (h1) | timeout (1181946 ops) | 13.04s / 5266 exp / 18168 ops | 9.98s / 3149 exp / 18352 ops | 176.4 -> 117.0 |
| 20x38 (h2) | timeout (? ops) | 16.03s / 6007 exp / 18168 ops | 12.60s / 3634 exp / 18352 ops | 203.1 -> 135.2 |

#### `*_scanner_separated`

| level | before | operator fix only | now | steps/tick before -> now |
|---|---|---|---|---|
| 5x5 | 0.03s / 293 exp / 878 ops | 0.02s / 293 exp / 548 ops | 0.02s / 230 exp / 556 ops | 42.5 -> 16.1 |
| 5x5 stones | 0.12s / 575 exp / 2612 ops | 0.04s / 575 exp / 782 ops | 0.04s / 426 exp / 790 ops | 65.7 -> 19.1 |
| 5x5 brick | 0.03s / 337 exp / 796 ops | 0.02s / 337 exp / 506 ops | 0.01s / 216 exp / 469 ops | 42.5 -> 12.2 |
| 10x10 | 4.06s / 1675 exp / 35013 ops | 0.33s / 1675 exp / 3153 ops | 0.31s / 1249 exp / 3171 ops | 122.2 -> 52.0 |
| 10x5 | 0.58s / 896 exp / 9198 ops | 0.10s / 896 exp / 1518 ops | 0.10s / 729 exp / 1536 ops | 65.5 -> 32.3 |
| 6x11 | 2.42s / 830 exp / 31238 ops | 0.19s / 830 exp / 2774 ops | 0.12s / 385 exp / 2784 ops | 103.6 -> 24.3 |
| 20x38 (h1) | timeout (2487273 ops) | 125.50s / 37577 exp / 36167 ops | 29.87s / 8724 exp / 33955 ops | 1251.2 -> 280.6 |
| 20x38 (h2) | timeout (? ops) | 127.51s / 37378 exp / 36609 ops | 40.66s / 10505 exp / 34397 ops | 1249.0 -> 332.9 |

#### `*_non-scanner_combined`

| level | before | operator fix only | now | steps/tick before -> now | states/tick avg/max before -> now |
|---|---|---|---|---|---|
| 5x5 | 0.01s / 48 exp / 224 ops | 0.01s / 48 exp / 221 ops | 0.01s / 30 exp / 221 ops | 6.0 -> 2.5 | 7.0/7 -> 3.5/6 |
| 5x5 stones | 0.04s / 179 exp / 1093 ops | 0.02s / 217 exp / 463 ops | 0.02s / 79 exp / 463 ops | 11.9 -> 3.1 | 17.1/28 -> 4.5/16 |
| 5x5 brick | 0.01s / 59 exp / 196 ops | 0.01s / 59 exp / 194 ops | 0.01s / 33 exp / 194 ops | 6.0 -> 2.5 | 7.2/10 -> 3.5/6 |
| 10x10 | 0.68s / 275 exp / 15010 ops | 0.09s / 275 exp / 1930 ops | 0.11s / 209 exp / 1930 ops | 8.0 -> 4.2 | 18.5/22 -> 9.4/22 |
| 10x5 | 0.11s / 97 exp / 4005 ops | 0.02s / 97 exp / 915 ops | 0.03s / 80 exp / 915 ops | 6.0 -> 3.5 | 7.0/7 -> 4.5/7 |
| 6x11 | 1.00s / 604 exp / 16993 ops | 0.13s / 604 exp / 1813 ops | 0.05s / 36 exp / 1813 ops | 11.0 -> 2.6 | 76.4/98 -> 4.0/14 |
| 20x38 (h1) | timeout (1184091 ops) | timeout (20313 ops) | timeout (20313 ops) | 125.0 -> 5.4 | >5000 all ticks -> 4.6/29 (6 ticks >5000) |
| 20x38 (h2) | timeout (1687209 ops) | timeout (20313 ops) | timeout (20313 ops) | 124.6 -> 6.5 | >5000 all ticks -> 6.3/56 (6 ticks >5000) |

#### `*_non-scanner_separated`

| level | before | operator fix only | now | steps/tick before -> now | states/tick avg/max before -> now |
|---|---|---|---|---|---|
| 5x5 | 0.02s / 145 exp / 705 ops | 0.01s / 145 exp / 375 ops | 0.01s / 55 exp / 375 ops | 21.4 -> 3.7 | 22.4/23 -> 4.7/14 |
| 5x5 stones | 0.12s / 838 exp / 2257 ops | 0.06s / 838 exp / 657 ops | 0.03s / 199 exp / 657 ops | 50.6 -> 6.7 | 87.8/170 -> 10.2/82 |
| 5x5 brick | 0.02s / 199 exp / 641 ops | 0.01s / 199 exp / 351 ops | 0.01s / 58 exp / 351 ops | 21.4 -> 3.7 | 24.0/40 -> 4.7/14 |
| 10x10 | 2.32s / 1358 exp / 29415 ops | 0.26s / 1358 exp / 2455 ops | 0.27s / 879 exp / 2455 ops | 28.2 -> 9.4 | 101.7/122 -> 35.8/122 |
| 10x5 | 0.21s / 251 exp / 7650 ops | 0.04s / 251 exp / 1170 ops | 0.05s / 166 exp / 1170 ops | 19.4 -> 7.0 | 20.4/23 -> 8.0/17 |
| 6x11 | 7.43s / 6464 exp / 27977 ops | 0.84s / 6464 exp / 2305 ops | 0.08s / 86 exp / 2305 ops | 46.6 -> 4.8 | 827.6/1098 -> 8.5/76 |
| 20x38 (h1) | timeout (? ops) | timeout (29253 ops) | timeout (29253 ops) | 614.2 -> 16.3 | >5000 all ticks -> 17.7/245 (6 ticks >5000) |
| 20x38 (h2) | timeout (? ops) | timeout (29477 ops) | timeout (29477 ops) | 611.6 -> 21.1 | >5000 all ticks -> 36.3/596 (6 ticks >5000) |

What changed, and what each change bought (measured on these levels):

- **No negated preconditions on multi-valued facts** (all models). Fast
  Downward merges mutually exclusive facts into one multi-valued variable (the
  agent position, the target-gem marker, `gem` on one-gem levels) and splits a
  negated precondition on one value into one operator per other value. The
  former `move_into_gem` needed `(not (target-gem ?to))`, so it was copied once
  per cell: 13,080 of the 14,811 operators of scanner-combined on a 10x10 level,
  ~1.2M on a 20x38 level, where every model timed out in the translator. Gem
  collection is now one action that sets `got-gem` conditionally, and the
  separated models' `not_fall` / `not_roll_*` checks are written without
  negating `agent-at` / `gem`. 7.8-12x fewer operators on 10x10, 58-69x on
  20x38 (where the old count is known); both scanners now solve the 20x38
  levels, with the same number of expansions as before on the levels both
  versions solve.
- **Row gates for scanner-separated** (and walls out of the scan). 1,250 ->
  ~300 physics steps per tick on 20x38; search 125 s -> 30-41 s there, end to
  end (translation included, idle machine) 153-159 s -> 53-61 s.
- **Column-block gates for scanner-combined** on wide levels. 176-203 -> 117-135
  steps per tick and ~40% fewer expansions on 20x38, search 13.9-16.8 s ->
  10.4-13.0 s; but translation takes 4-8 s longer (more action parameters), so
  end to end it is no faster with Fast Downward (37.9-39.8 s -> 38.4-43.8 s).
  It does help planners that pay per physics step (forced-action replays
  below: 23,945 -> 13,893 steps per plan). Levels up to 16 columns get no
  block gates.
- **Dirty marking for the order-free models.** 125 -> 5-7 (combined) and
  612 -> 16-21 (separated) physics steps per tick on 20x38, and up to 75x fewer
  expansions on the medium levels. The 20x38 levels still time out with a
  classic planner (see above).
- With **forced-action semantics** (physics applied in one fixed order after
  every move, as an FA planner does; `tools/sim_check/plan_check.py` on the FA
  files, 20x38 level h1, same 30-move plan found by every model, valid when
  replayed in the engine), the physics work per plan shrinks to:

  | variant | physics steps before -> now | search time before -> now |
  |---|---|---|
  | `*_scanner_combined` | 23,945 -> 13,893 | 7.8 s -> 5.6 s |
  | `*_scanner_separated` | 214,123 -> 46,291 | 60.6 s -> 15.3 s |
  | `*_non-scanner_combined` | 21,373 -> 732 | 3.6 s -> 0.5 s |
  | `*_non-scanner_separated` | 105,194 -> 2,245 | 39.4 s -> 1.0 s |

  so for forced-action planners the order-free models are now the cheapest.
- **Fast Downward partial-order reduction** (stubborn sets) would prune exactly
  these interleavings, but its implementation refuses tasks with axioms or
  conditional effects ("This configuration does not support axioms!"), and the
  order-free models need both (`end_tick`'s quantified test, the pending
  marking in `start_tick`, the kind-preserving moves). Not usable without
  giving up the order-free style.
