# Multi-gem test problems

Written by `python3 tools/generate_multigem_problems.py`; used by
`tools/benchmarking/fd_sweep.py --multigem` with the
`pddl/test_domains_target/domain_*_multigem.pddl` domains.

Each problem extends one of the 24 bd_level_01 start/target problems the
sweep samples from `pddl/test_problems/{h1,h2}` (set `n1`):

- `n2/`: the same start gem and target, plus one more target gem;
- `n3/`: plus two more (a superset of the n2 targets).

The extra targets are picked with a seed derived from the base file name.
Targets are marked 90 / 91 in the level, the agent stands on the start gem,
and file names use the original level-1 gem ordinals:
`bd_level_01_start_gem_<s>_targets_<a>_<b>[_<c>].txt`.
