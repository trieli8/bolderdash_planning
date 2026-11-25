# Test Domain Matrix (pre target-gem)

This folder keeps the previous test-domain matrix, from before the planner's
target-gem marker was added: the former `test_domains` folder as of commit
`9006c14`, split off into this folder in commit `c434ed1` and kept for
comparison. The current matrix is `pddl/test_domains_target/`.

The matrix was requested from:

- `{domain, domain_FA, domain_plus}`
- `{scanner, non-scanner}`
- `{combined, separated}`
- `events/actions` only for `domain_plus` (only the `events` files are present, see below)

## Source Mapping

The source files below are no longer in the tree (deleted in commit `ed4a61e`;
`git show ed4a61e^:pddl/<name>` prints one). Each domain still names its source
in a `; source:` header, and that name is what selects the problem generator.

- `domain_*` and `domain_FA_*`
  - `*_scanner_combined` -> `domain_scanner_combined.pddl`
  - `*_scanner_separated` -> `domain_scanner_separated.pddl`
  - `*_non-scanner_combined` -> `domain_merged.pddl`
  - `*_non-scanner_separated` -> `domain.pddl`

- `domain_plus_*_actions`: no domain files in this folder. They were built from
  the same four sources as above; the four `problem_gen_domain_plus_*_actions.py`
  wrappers are left over and exit with "missing domain file".

- `domain_plus_*_events`
  - `scanner_combined_events` -> `domain_plus_scanner_separated_events.pddl`
  - `scanner_separated_events` -> `domain_plus_scanner_separated_events.pddl`
  - `non-scanner_combined_events` -> `domain_plus_from_domain.pddl`
  - `non-scanner_separated_events` -> `domain_plus_from_domain.pddl`

## Validation

All 16 files (including the four `domain_plus_*_actions` files, since removed)
were validated to solve `pddl/level_5_5.txt` by:

- generating a domain-matched problem with the appropriate generator script
- running `tools/plan.py` (`fd`) for non-event files
- running `tools/plan_plus.py` (`enhsp`) for event files

Observed status: all 16 solved.

## Variant Problem Generators (No-Write)

Each domain variant has a matching generator script:

- `pddl/test_domains_pre_target/problem_gen_<domain-file-stem>.py`; the classic
  files drop `classic_`, as in their `; variant:` header
  (`domain_classic_scanner_combined.pddl` ->
  `pddl/test_domains_pre_target/problem_gen_domain_scanner_combined.py`)

Examples:

- `python pddl/test_domains_pre_target/problem_gen_domain_FA_scanner_combined.py pddl/level_5_5.txt -p test_case`
- `python pddl/test_domains_pre_target/problem_gen_domain_plus_scanner_combined_events.py pddl/level_5_5.txt -p test_case`

Behavior:

- These scripts print the generated problem to `stdout` only.
- They do not write `<problem>.pddl` files anywhere.
