# Engine-vs-PDDL differential tests

`fuzz.py` checks that a PDDL model behaves exactly like the stonesngems engine
(`stonesandgem/`, the source of truth). It runs random levels and random
agent walks through both, and compares the whole board after every tick:

- cell contents, including whether each stone/gem is falling or resting,
- agent death,
- the position of the planner's target gem (tracked through the engine's own
  object ids, so a gem that falls or rolls must keep its marker).

On the PDDL side the agent's `move_*` action is applied, then every other
action (physics, or `__FORCED__` in the FA variants) until none is applicable.
**All** interleavings of physics actions are explored, so a tick that can end
in more than one state is reported as `nondeterministic`. The summary also
counts ticks in which some physics step had more than one distinct successor
(harmless for correctness, but wasted search for classic planners).

```bash
# random levels (default 200 cases, levels up to 6x7, 25-step walks)
python3 tools/sim_check/fuzz.py --domain pddl/test_domains_target/domain_FA_scanner_combined.pddl

# bigger campaign
python3 tools/sim_check/fuzz.py --domain pddl/domain_rowscan.pddl \
  --cases 500 --seed 3 --max-rows 8 --max-cols 10 --walk 40

# hand-written regression cases (corner cases random levels rarely hit)
python3 tools/sim_check/fuzz.py --domain pddl/domain_rowscan.pddl \
  --cases-file tools/sim_check/regression_cases.txt

# real benchmark levels (grounding a 20x38 level takes ~20 s in Python)
python3 tools/sim_check/fuzz.py --domain pddl/domain_rowscan.pddl \
  --level pddl/test_problems/h1/bd_level_01_start_gem_001_target_gem_005.txt --cases 4 --walk 60
```

The problem generator is found next to the domain (`problem_gen_<stem>.py`)
or given with `--generator`. Exit status is 0 only if every case matched.

All eight classic / FA files in `pddl/test_domains_target/` match on 500 random
cases and on the regression cases; see the conformance table in
`pddl/test_domains_target/README.md`. For the order-free (non-scanner) models
the "several distinct successors" count is non-zero by design: independent
objects can be updated in any order, and every order ends the tick in the same
state.

Random levels are at most 7 columns wide, so they fit in one column block of
the scanner-combined model; to exercise block boundaries, force narrow blocks:

```bash
ROWSCAN_BLOCK_WIDTH=2 python3 tools/sim_check/fuzz.py \
  --domain pddl/test_domains_target/domain_classic_scanner_combined.pddl --cases 500
```

## Model cost (`model_stats.py`)

```bash
python3 tools/sim_check/model_stats.py --domain pddl/test_domains_target/domain_classic_non-scanner_combined.pddl \
  --interleavings --fd ../downward/fast-downward.py pddl/level_10_10.txt
```

Per level: ground operators and grounding time, physics steps per tick along
fixed random walks (forced-action semantics; the walks depend only on
`--seed` and the level, so all models see the same moves), with
`--interleavings` the number of distinct intermediate states per tick when
every order of physics actions is explored (what a classic planner can run
into inside one tick), and with `--fd` a Fast Downward run (translator
operators, expansions, times). `--json` appends one line per level for
comparisons.

## Files

- `engine_trace.cpp` – batch tracer linked against `stonesandgem/src`. Built
  automatically into `build/engine_trace` (needs `g++` with C++20). It only
  uses the public `RNDGameState` API, so it also builds against a fork of the
  engine; rerun the fuzzer there if the fork changes game rules.
- `pddl_exec.py` – small PDDL parser / grounder / executor (typing, negative,
  disjunctive and quantified preconditions, conditional and universal effects).
  `task_stats()` reports operator counts after relaxed-reachability pruning
  and disjunction splitting. This is only a rough proxy: Fast Downward also
  splits negated conditions on facts it groups into multi-valued variables
  (the agent position, the target-gem marker), so use `model_stats.py --fd`
  for real translator counts. Grounding takes candidates for a parameter from
  any static literal (also from disjunctions, and from atoms with only some
  arguments bound), and each ground action is indexed under its most
  selective precondition atom, so grounding a 20x38 level takes a few seconds
  and successor generation does not scan thousands of actions.
- `model_stats.py` – per-level cost of a model (see above).
- `regression_cases.txt` – `name;level;actions` lines.

## Scope

Modelled engine elements: agent, empty, dirt, stone, gem, brick wall (rounded),
steel wall / exit / level border (not rounded). Other elements are treated as
flat walls by the problem generators; random levels use exits only with an
unreachable gem requirement so they stay closed. Explosions are not modelled
beyond the agent dying (the game ends there).
