# Test Domain Matrix

This folder contains the generated matrix requested from:

- `{domain, domain_FA, domain_plus}`
- `{scanner, non-scanner}`
- `{combined, separated}`
- `events/actions` only for `domain_plus`

## Source Mapping

- `domain_*` and `domain_FA_*`
  - `*_scanner_combined` -> `pddl/domain_rowscan.pddl` (row-gated scanner, verified
    against the engine with `tools/sim_check/fuzz.py`; regenerate both files with
    `python pddl/make_rowscan_variants.py`; problems from `pddl/problem_gen_rowscan.py`)
  - `*_scanner_separated` -> `pddl/domain_scanner_separated.pddl`
  - `*_non-scanner_combined` -> `pddl/domain_merged.pddl`
  - `*_non-scanner_separated` -> `pddl/domain.pddl`

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

| variant | matching cases |
|---|---|
| `*_scanner_combined` (row-gated, `pddl/domain_rowscan.pddl`) | all (thousands of random cases, regression cases, real benchmark levels) |
| `*_scanner_combined` (previous version) | 69/150 |
| `*_scanner_separated` | 28/60 |
| `*_non-scanner_combined` | 22/60 |
| `*_non-scanner_separated` | 0/60 (no `move_noop`: the agent cannot wait) |

The remaining variants still encode the old rules (e.g. falling gems do not
crush the agent, steel walls and exits are treated as rounded, the target-gem
marker does not follow a falling gem).
