# PDDL+ Planner Integration

This folder is the integration point for external PDDL+ planners.

## Supported Engines

- `ENHSP` (`enhsp.jar`)
- `OPTIC` (`optic-clp`)
- Any custom command via template

## Expected Locations

- `planners/pddl-plus/enhsp.jar`
- `planners/pddl-plus/optic-clp`

You can override paths from the CLI (`tools/plan_plus.py`) with:

- `--enhsp-jar <path>`
- `--optic-bin <path>`

## Runner

Use the low-level runner directly:

```bash
python planners/pddl-plus/pddl_plus_runner.py \
  --domain pddl/domain_plus_from_domain.pddl \
  --problem pddl/level_5_5_plus.pddl \
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
