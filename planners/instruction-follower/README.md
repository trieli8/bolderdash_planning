# Instruction Follower Planner

Minimal “planner” that checks the PDDL parses and then emits a plan using a prewritten list of actions.

## Usage

```bash
# actions.txt contains one action per line, e.g.
# (move a c1 c2)
# 0: (move a c2 c3)
python planners/instruction-follower/plan.py \
  --domain pddl/domain.pddl \
  --problem pddl/problem.pddl \
  --actions path/to/actions.txt
```

- Parsing is done with Fast Downward’s `--translate` stage (no search). Forced actions (operators whose name starts with `fa-`, `fa_`, or `forced-`) are automatically applied to closure before/after each provided action unless you pass `--no-forced`.
- Outputs land in `plans/<problem-name>/plan.txt` and `plan.json` (same format as `tools/plan.py`).
- Use `--skip-parse` to bypass the PDDL parse/grounding step if you only want to emit the provided actions.
