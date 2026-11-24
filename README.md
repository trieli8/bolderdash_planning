# BoulderDash – Planning-Driven Stones & Gems

This repository combines:
- **Stones & Gems** (BoulderDash-like game engine + GUI)
- **Forced-Action FF** planner
- **Fast Downward** planner
- **Python wrapper tools** providing a unified interface to planners and GUI

---

## Repository Layout

```
bolderdash_planning/
├── Makefile                    # builds the planners and the game
├── view_levels_folder.sh       # browse level .txt files in the SDL renderer
├── view_plans_batch.sh         # replay plans from a benchmark run
├── stonesandgem/               # game engine + GUI (submodule; build/bin/gui after `make game`)
├── planners/
│   ├── forced-action-ff/       # submodule; ff binary after `make ff`
│   ├── fast-downward/          # submodule; fast-downward.py, built by `make fd`
│   ├── powerlifted/            # submodule, used by tools/plan_lifted.py
│   ├── pddl-plus/              # pddl_plus_runner.py + enhsp/ submodule
│   └── instruction-follower/   # emits a given action list as a plan
├── pddl/
│   ├── domain_rowscan.pddl, domain_cellscan_separated.pddl,
│   │   domain_orderfree_{combined,separated}.pddl    # source domains
│   ├── make_target_variants.py # writes the classic / FA files in test_domains_target/
│   ├── problem_gen*.py         # level .txt -> PDDL problem generators
│   ├── test_domains_target/    # current domain matrix + one problem_gen_<stem>.py per domain
│   ├── test_domains_pre_target/# previous domain matrix, kept for comparison
│   ├── test_problems/{h1,h2}/  # benchmark levels
│   └── level*.txt, testing_level_*.txt, test_mini.txt
├── tools/
│   ├── plan.py, plan_plus.py, plan_lifted.py   # planner wrappers
│   ├── validate_pddl.py, replan_from_state.py, gui.py, sng_log_to_posthoc.py, ...
│   ├── benchmarking/           # bench_*_matrix.py, config_examples/, ploters/
│   ├── sim_check/              # engine-vs-PDDL differential tests
│   └── diagram_outputs/        # SVGs from diagram_model_comparison.py
└── README.md
```

`plans/`, `results/` and `tools/benchmarking/results/` are created by the tools and are gitignored.

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
git clone --recurse-submodules https://github.com/trieli8/bolderdash_planning.git
cd bolderdash_planning
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
python tools/plan.py --domain pddl/test_domains_target/domain_FA_scanner_combined.pddl --problem pddl/level_5_5.txt
# Forced-Action FF only / both planners
python tools/plan.py --planner ff --domain ... --problem ...
python tools/plan.py --planner both --domain ... --problem ...
# Stream or optimal FD search
python tools/plan.py --planner fd --stream --domain ... --problem ...
python tools/plan.py --planner fd --optimal --domain ... --problem ...
# Play an existing plan with the C++ plan_player
python tools/plan.py --play-plan plans/<problem>/fd.plan [--play-level <level.txt>]
```

- Passing a `.txt` level file to `--problem` generates a temporary PDDL problem. The generator is the
  domain's sibling `problem_gen_<stem>.py` (every domain in `pddl/test_domains_target/` has one), else
  the one mapped from the domain's `; source:` header, else the legacy `pddl/problem_gen.py`, which only
  fits the pre-rewrite models. The source domains in `pddl/` have neither, so plan with the
  `pddl/test_domains_target/` files.
- Plans/logs are saved under `plans/<problem_name>/` (e.g., `fd.plan`, `fd.play.plan`, `ff.plan`, `*.stdout.txt`).
- `--view` opens the first solved plan in `stonesandgem/build/bin/plan_player` after planning.

### Folder Matrix Benchmark

```bash
python tools/benchmarking/bench_levels_matrix.py \
  --config tools/benchmarking/config_examples/the_benchmark_h1.json
```

- Runs every planner setting against every compatible test domain and every level in `levels_dir`.
- `the_benchmark_h1.json` / `the_benchmark_h2.json` run forced-action Fast Downward on
  `domain_FA_scanner_combined.pddl` over `pddl/test_problems/h1` / `pddl/test_problems/h2`.
- Keeps the config small: `levels_dir`, `planner_settings`, `timeout_sec`, and `max_parallel_runs` are the main inputs.
- Writes a `benchmark_matrix.csv` plus logs, compiled problems, plans, and `run_metadata.json` under `tools/benchmarking/results/levels-matrix_<timestamp>/` by default.
- Generates the config-matrix SVG plots automatically unless `--skip-plots` is passed.
- Graceful exit: send `Ctrl-C` once to stop admitting new tasks and drain the currently running work before exit; partial CSV results stay on disk throughout the run.
- Optional config fields: `domains` or `domains_glob` to control the benchmark domains (default:
  `pddl/test_domains_target/domain*.pddl`), and `level_glob` to filter files inside `levels_dir` (default: `*.txt`).

### Config Matrix Benchmark

```bash
python tools/benchmarking/bench_config_matrix.py \
  --config tools/benchmarking/config_examples/growth_settings_comparison.json
```

- Like the folder benchmark, but on generated levels: `growth` grows random levels from `start_size` to
  `max_size` (a setting with `"validator": true` screens each generated level first), `random_repeats`
  adds random maps of fixed sizes, and `custom_levels` / `custom_levels_glob` add your own `.txt` levels.
- Each `planner_settings` entry has a `family` (`classic`, `fa` or `plus`) and a `planner` (`fd`, `ff` or
  `lifted` for classic / fa; `enhsp`, `optic`, `auto` or `cmd` for plus), plus optional `planner_args`,
  `timeout_sec`, `java_opts`, `problem_gen` and `domain_include` / `domain_exclude` path globs. A setting
  only runs on domains of its family (classic, `__FORCED__` or PDDL+).
- This covers the old `bench_classic.py` / `bench_plus.py` sweeps: add one setting per FD / FF variant, or
  one ENHSP setting per heuristic / search pair, e.g.
  `{"name": "enhsp-hadd-gbfs", "family": "plus", "planner": "enhsp", "planner_args": "-h hadd -s gbfs", "java_opts": "-Xmx8g"}`.
- Writes `benchmark_matrix.csv`, logs, plans, generated levels and SVG plots under
  `tools/benchmarking/results/config-matrix_<timestamp>/` by default. `--dry-run` builds the full run
  matrix without calling planners; `Ctrl-C` drains running work as above.

### PDDL+ planning wrapper

```bash
# Auto-detect ENHSP/OPTIC under planners/pddl-plus/
python tools/plan_plus.py --domain pddl/test_domains_target/domain_plus_non-scanner_combined_events.pddl --problem pddl/level_5_5.txt

# Scanner PDDL+ variant
python tools/plan_plus.py --domain pddl/test_domains_target/domain_plus_scanner_separated_events.pddl --problem pddl/level_5_5.txt

# Increase Java heap for larger problems
python tools/plan_plus.py --domain pddl/test_domains_target/domain_plus_scanner_separated_events.pddl --problem pddl/level_10_10.txt \
  --java-opts=-Xmx8g

# Custom planner command template
python tools/plan_plus.py --planner cmd \
  --cmd-template "<planner-bin> {domain} {problem}" \
  --domain pddl/test_domains_target/domain_plus_non-scanner_combined_events.pddl --problem pddl/level_5_5.txt
```

- Outputs are written to `plans/<problem_name>/` as `plus-*.plan`, `plus-*.timed.plan`, `plus-*.play.plan`, and planner logs.
- `.txt` levels are converted with the generator mapped from the domain's `; source:` header (or `--problem-gen`):
  - `pddl/problem_gen_plus_from_domain.py` (`domain_plus_non-scanner_*_events.pddl`)
  - `pddl/problem_gen_plus_scanner_separated.py` (`domain_plus_scanner_*_events.pddl`)

### Plot PDDL+ sweep runtime

```bash
python tools/benchmarking/ploters/plot_plus_bench_runtime.py \
  --csv <sweep>.csv --out <sweep>.runtime.svg

# Compare by domain+problem labels on x-axis
python tools/benchmarking/ploters/plot_plus_bench_runtime.py \
  --csv <sweep>.csv --x-axis domain_problem
```

- Reads the CSV format of the removed `bench_plus.py` sweep (columns `input_problem`, `domain`,
  `heuristic`, `search`, `time_sec`, `status`). Without `--csv` it takes the newest CSV under
  `tools/benchmarking/results/*/`. Matrix benchmark CSVs use other columns; they are plotted by
  `tools/benchmarking/ploters/plot_config_matrix.py`, which the benchmarks run automatically.
- X-axis: problem
- Y-axis: runtime (seconds)
- Fill color: heuristic (`h`)
- Marker shape: search strategy (`s`)
- Outline color: domain (when multiple domains are present)
- `timeout` and `error` rows are excluded by default (use `--include-failures` to include them)

### Browse Level Folders

```bash
# Browse all level .txt files in a folder
./view_levels_folder.sh pddl

# Browse generated levels from a benchmark run
./view_levels_folder.sh tools/benchmarking/results/config-matrix_20260323_001344/generated-levels
```

- Uses the native SDL Stones & Gems renderer rather than an ASCII fallback.
- Shows the current level filename in the window title and logs the full path in the terminal when you change levels.
- Use Left/Right or Up/Down arrows to move between levels, `Home`/`End` to jump, and `Esc`/`q` to quit.

### Plot PDDL+ timing breakdown

```bash
python tools/benchmarking/ploters/plot_plus_time_breakdown.py \
  --results-dir tools/benchmarking/results/config-matrix_<timestamp>/logs \
  --out time_breakdown.svg
```

- Creates a stacked bar chart from ENHSP `*.stdout.txt` logs in `--results-dir` (`--pattern` narrows the
  files; logs without ENHSP timings are skipped).
- Stack segments: `Grounding Time`, `Planning Time`, `Heuristic Time`, `Search Time`.
- Bars are labelled by log file name. Names of the old `bench_plus.py` form
  (`plus-enhsp-bench-d_<domain>-p_<problem>-h_<h>-s_<s>.stdout.txt`) are split into domain / problem / h / s.

### Scanner model (`pddl/domain_rowscan.pddl`)

The scanner-combined test domains (`pddl/test_domains_target/domain_{classic,FA}_scanner_combined.pddl`)
are generated from `pddl/domain_rowscan.pddl` by `python pddl/make_target_variants.py`;
problems come from `pddl/problem_gen_rowscan.py` (picked automatically through the
`; source:` header).

- Matches the stonesngems engine tick for tick for agent, empty, dirt, stone, gem,
  brick wall (rounded) and steel wall / exit / border (not rounded): agent first,
  then a row-major scan with the engine's `has_updated` skipping, falling stones
  *and gems* crush the agent, pushed stones are skipped in the push tick, and the
  target-gem marker moves with its gem.
- Physics is deterministic: while a tick runs exactly one physics action is
  applicable and no `move_*` action is, so the classic and `__FORCED__` variants
  behave identically.
- Fast: walls are left out of the scan, and each row has a gate that skips the row
  in one step unless something in it or in the row below changed since it was last
  scanned. On a 20x38 benchmark level this is ~16.6k operators versus ~189k for the
  previous scanner model (after Fast Downward-style disjunction splitting), and a
  typical tick takes 96 physics steps instead of 761 (20 row gates + the two rows
  around the agent; the first few ticks of a level cost more while its initial
  rockfall settles).
- Not modelled: the level time limit, and engine elements other than the ones above
  (the generator treats them as flat walls).

### Other test-domain styles

The rest of the classic / FA matrix in `pddl/test_domains_target/` encodes the same
engine rules and is generated by the same script:

- `*_scanner_separated` <- `pddl/domain_cellscan_separated.pddl`: cell-by-cell scanner
  with separate check / act actions (problems: `pddl/problem_gen_cellscan.py`).
- `*_non-scanner_combined` <- `pddl/domain_orderfree_combined.pddl` and
  `*_non-scanner_separated` <- `pddl/domain_orderfree_separated.pddl`: order-free physics
  with pending flags (problems: `pddl/problem_gen_orderfree.py`). Objects may be updated
  in any order that respects a small conflict window, which makes the end of every tick
  match the engine exactly, but several physics actions are usually applicable at once.

See `pddl/test_domains_target/README.md` for the design, determinism and conformance results.

### Differential test against the engine

```bash
python3 tools/sim_check/fuzz.py --domain pddl/test_domains_target/domain_FA_scanner_combined.pddl
python3 tools/sim_check/fuzz.py --domain pddl/domain_rowscan.pddl --cases-file tools/sim_check/regression_cases.txt
```

Runs random levels and walks through the real engine (compiled from `stonesandgem/src`)
and through the grounded PDDL model, and compares the whole board after every tick.
See `tools/sim_check/README.md`.

### Validate PDDL vs native trace

```bash
python tools/validate_pddl.py --domain pddl/test_domains_target/domain_FA_scanner_combined.pddl --problem pddl/level_5_5.txt \
  [--plan plans/<problem>/fd.plan] [--native-trace native_trace.jsonl] [--timeout 60]
```

- `--domain` defaults to `pddl/test_domains_target/domain_FA_scanner_combined.pddl`.
- If `--plan` is omitted, Fast Downward is invoked via `tools/plan.py` to create one.
- A `.txt` level is converted with the same generator lookup as `tools/plan.py`. For a PDDL problem, the
  `.txt` with the same stem (or `pddl/level.txt`) is used for the native trace.
- Compares the native stones_trace output to the PDDL simulation and reports mismatches.

### Generate PDDL problem from level text

```bash
python pddl/test_domains_target/problem_gen_domain_FA_scanner_combined.py pddl/level_5_5.txt > level_5_5.pddl
python pddl/test_domains_target/problem_gen_domain_FA_scanner_combined.py "<rows|cols|max_time|required_gems|...>" -p level-1
```

Every domain in `pddl/test_domains_target/` has a matching `problem_gen_<stem>.py`. It accepts either a `|`-delimited level string or a path to a `.txt` file containing it, and writes the PDDL problem to stdout; redirect to a file to save it. Optional flags set the problem name (`-p`) and domain name (`-d`, default: the one declared in the domain file). They wrap the generators of the source domains, `pddl/problem_gen_rowscan.py`, `pddl/problem_gen_cellscan.py` and `pddl/problem_gen_orderfree.py`; `pddl/problem_gen.py` only fits the pre-rewrite models.

### Instruction-follower planner

```bash
python pddl/test_domains_target/problem_gen_domain_FA_scanner_combined.py pddl/level_5_5.txt > level_5_5.pddl
python planners/instruction-follower/plan.py --domain pddl/test_domains_target/domain_FA_scanner_combined.pddl --problem level_5_5.pddl \
  --actions actions.txt [--out-root plans] [--timeout 30] [--skip-parse] [--no-forced]
```

Takes a PDDL problem, not a `.txt` level, so generate one first. Parses the PDDL with Fast Downward’s translator (unless `--skip-parse`), then emits the given action list as the plan (optionally inserting forced actions). Outputs land in `<out-root>/<problem-name>/plan.{txt,json}` with raw logs.

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
