# PDDL+ Planner Integration

This folder is the integration point for external PDDL+ planners.

## Supported Engines

- `ENHSP` (`enhsp.jar`)
- `OPTIC` (`optic-clp`)
- Any custom command via template

## Expected Locations

None of these files are in the repository: build the ENHSP submodule
(`planners/pddl-plus/enhsp/`) or put a jar / binary in one of these places.
`--planner auto` (the default) uses the first ENHSP jar it finds, else the first
OPTIC binary.

- ENHSP, in this order: `planners/pddl-plus/enhsp.jar`, then inside the submodule
  `planners/pddl-plus/enhsp/enhsp.jar`, `planners/pddl-plus/enhsp/enhsp-dist/enhsp.jar`,
  `planners/pddl-plus/enhsp/target/enhsp.jar`, `planners/pddl-plus/enhsp/build/libs/enhsp.jar`
- OPTIC, in this order: `planners/pddl-plus/optic-clp`, `planners/pddl-plus/optic`,
  `planners/pddl-plus/OPTIC/optic-clp`

You can override paths from the CLI (`tools/plan_plus.py`) with:

- `--enhsp-jar <path>`
- `--optic-bin <path>`

## Runner

Use the low-level runner directly. It takes a PDDL problem, not a `.txt` level, so
generate one first:

```bash
python pddl/test_domains_target/problem_gen_domain_plus_non-scanner_combined_events.py pddl/level_5_5.txt > level_5_5.pddl
python planners/pddl-plus/pddl_plus_runner.py \
  --domain pddl/test_domains_target/domain_plus_non-scanner_combined_events.pddl \
  --problem level_5_5.pddl \
  --planner auto
```

For full workflow (problem generation + output files + playback), use `tools/plan_plus.py`.

## Custom Planner Command

If your planner has a different CLI, use:

```bash
python tools/plan_plus.py \
  --planner cmd \
  --cmd-template "<your-binary> {domain} {problem}" \
  --domain ... --problem ...
```

`{domain}` and `{problem}` are replaced with absolute file paths.
