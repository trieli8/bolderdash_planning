# BoulderDash – Planning-Driven Stones & Gems

This repository combines:
- **Stones & Gems** (BoulderDash-like game engine + GUI)
- **Forced-Action FF** planner
- **Fast Downward** planner
- **Python wrapper tools** providing a unified interface to planners and GUI

---

## Repository Layout

```
boulderdash/
├── Makefile
├── stonesandgem/
│   └── build/bin/gui
├── planners/
│   ├── forced-action-ff/ff
│   └── fast-downward/fast-downward.py
├── tools/
│   ├── plan.py
│   └── gui.py
├── pddl/
├── plans/
└── README.md
```

---

## Prerequisites

- macOS or Linux
- Python 3.9+
- CMake
- GNU Make
- C/C++ compiler

---

## Clone

```bash
git clone --recurse-submodules https://github.com/<you>/boulderdash.git
cd boulderdash
```

---

## Build

```bash
make
```

Clean:

```bash
make clean
make distclean
```

---

## Runnable commands

### Game GUI

```bash
python tools/gui.py [--level <level.txt>] [--gui-bin <path>] [--cwd <path>]
```

Runs the Stones & Gems GUI binary at `stonesandgem/build/bin/gui` (built via `make game`). Pass a level text file (e.g., `stonesandgem/bd_levels/test_level.txt`) with `--level` to load it immediately.

### Planning wrapper

```bash
# Fast Downward (default)
python tools/plan.py --domain pddl/domain.pddl --problem pddl/problem.pddl
# Forced-Action FF only / both planners
python tools/plan.py --planner ff --domain ... --problem ...
python tools/plan.py --planner both --domain ... --problem ...
# Stream or optimal FD search
python tools/plan.py --planner fd --stream --domain ... --problem ...
python tools/plan.py --planner fd --optimal --domain ... --problem ...
# Play an existing plan with the C++ plan_player
python tools/plan.py --play-plan plans/<problem>/fd.plan [--play-level <level.txt>]
```

- Passing a `.txt` level file to `--problem` autogenerates a temporary PDDL with `pddl/problem_gen.py`.
- Plans/logs are saved under `plans/<problem_name>/` (e.g., `fd.plan`, `fd.play.plan`, `ff.plan`, `*.stdout.txt`).
- `--play-output` opens the first solved plan in `stonesandgem/build/bin/plan_player` after planning.

### PDDL+ planning wrapper

```bash
# Auto-detect ENHSP/OPTIC under planners/pddl-plus/
python tools/plan_plus.py --domain pddl/domain_plus_from_domain.pddl --problem pddl/level_5_5.txt

# Scanner-separated PDDL+ variant
python tools/plan_plus.py --domain pddl/domain_plus_scanner_separated.pddl --problem pddl/level_5_5.txt

# Custom planner command template
python tools/plan_plus.py --planner cmd \
  --cmd-template "<planner-bin> {domain} {problem}" \
  --domain pddl/domain_plus_relaxed.pddl --problem pddl/level_5_5.txt
```

- Outputs are written to `plans/<problem_name>/` as `plus-*.plan`, `plus-*.timed.plan`, `plus-*.play.plan`, and planner logs.
- `.txt` levels are converted with domain-specific generators:
  - `pddl/problem_gen_plus_from_domain.py`
  - `pddl/problem_gen_plus_scanner_separated.py`
  - `pddl/problem_gen_plus_relaxed.py`

### Validate PDDL vs native trace

```bash
python tools/validate_pddl.py --domain pddl/domain.pddl --problem pddl/problem.pddl \
  [--plan plans/<problem>/fd.plan] [--native-trace native_trace.jsonl] [--timeout 60]
```

- If `--plan` is omitted, Fast Downward is invoked via `tools/plan.py` to create one.
- If the problem is a `.txt` level, it is converted through `pddl/problem_gen.py`; a `.txt` alongside the PDDL problem is also used for native traces.
- Compares the native stones_trace output to the PDDL simulation and reports mismatches.

### Batch validate levels + plans

```bash
python tools/validate_batch.py --levels-dir pddl --plans-dir plans
# or use one folder for both:
python tools/validate_batch.py --root /path/to/folder
```

- Matches levels to plans by level filename stem (e.g., `level.txt` -> `plans/level/*.plan`).
- Automatically detects if a plan is a full plan (with forced actions) or a human plan (directions/actions).

### Generate PDDL problem from level text

```bash
python pddl/problem_gen.py pddl/level.txt > pddl/level01.pddl
python pddl/problem_gen.py "<rows|cols|max_time|required_gems|...>" -p level-1 -d mine-tick-gravity
```

Accepts either a `|`-delimited level string or a path to a `.txt` file containing it. Writes the PDDL problem to stdout; redirect to a file to save it. Optional flags let you set the problem name (`-p`), domain name (`-d`), and agent object name (`-a`).

### Instruction-follower planner

```bash
python planners/instruction-follower/plan.py --domain pddl/domain.pddl --problem pddl/problem.pddl \
  --actions actions.txt [--out-root plans] [--timeout 30] [--skip-parse] [--no-forced]
```

Parses the PDDL with Fast Downward’s translator (unless `--skip-parse`), then emits the given action list as the plan (optionally inserting forced actions). Outputs land in `<out-root>/<problem-name>/plan.{txt,json}` with raw logs.

### Asset packer (dev)

```bash
python stonesandgem/src/png_to_byte.py
```

Regenerates `stonesandgem/src/assets_all.inc` from the PNG tiles in `stonesandgem/tiles/`. Requires `opencv-python` and `xxd`; used when updating art assets.

---

## Level Encoding

```
0 Agent
1 Empty
2 Dirt
3 Stone
5 Gem
7 Wall
```
