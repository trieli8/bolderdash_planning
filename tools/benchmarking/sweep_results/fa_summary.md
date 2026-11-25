# Forced-action (FA) sweep: summary

Full tables: `compare_fa_vs_classic.md` (FA vs classic), `report_fa.md`, `report_classic.md`
(regenerate with `analyze_sweep.py [--variant=inv0+fa]` and `compare_sweep.py --speed=2`).

## Setup

- **FA**: `results_m5pro_fa.csv`, 1944 runs (groups A, B, C; 9 LazySearch configs on every
  problem of every model). Apple M5 Pro, 12 parallel jobs, 300 s search (CPU time), 3 GB.
  Fork `planners/fast-downward` @ 3afd349, built natively (arm64), plus the local
  `FD_STATE_DUMP` gate (the fork otherwise logs every search state as JSON); the sweep sets
  `FD_STATE_DUMP=0`. macOS cannot set memory limits, so `fd_sweep.py` kills a process tree
  above 3 GB RSS (memout). The machine was on AC and awake for jobs 1–210; the last six
  (order-free separated) overlapped a sleep, which only affects their wall-clock columns
  (search time and the limit are CPU time).
- **Classic**: `results_vm.csv`, 1392 runs, upstream FD 24.06.1 on the 4-core Xeon VM.
- **Hardware**: the translator (same Python, identical tasks, identical operator counts) is
  1.86x faster per job on the M5 Pro (median, range 1.6–3.5). `--speed=2` marks FA solves
  that need more than 150 s; that changes coverage in only a handful of cells, so the coverage
  gains below are not a hardware effect. No same-machine classic baseline was run (see below).
- In `--fa` mode only LazySearch applies `__FORCED__` actions, so eager-gbfs-ff and
  astar-* are not run under FA. New optimal configs: `lazy-astar-blind` / `lazy-astar-hmax`
  (`lazy_wastar(w=1)`, what `tools/plan.py --optimal` uses with blind) and
  `lazy-astar-hmax-tb` = `let(h, hmax(), lazy(tiebreaking([sum([g(), h]), h]), reopen_closed=true))`
  (lazy A* that breaks f ties on h, as `astar()` does).

## Findings

**Correctness.** No problem is solved by one model/side and proved plan-less by another.
All optimal costs agree across sides, models and configs (44 problems), every FA optimal
cost equals the classic optimum where classic has one (41/41), and no satisficing plan is
cheaper than an optimum. No-plan problems: testing_level_2, testing_level_3, L11 t115,
L11 t168 (FA proves the L11 ones with scan-comb and orderfree-comb too).

**Coverage, large problems (l1 24 + other 16 solvable), classic (VM) → FA:**

| model | best satisficing | gbfs-cea | lama-first | best optimal |
|---|---|---|---|---|
| scan-comb | 40 (gbfs-add) → 40 (4 configs) | 30 → 40 | 36 → 39 | 31 (astar-hmax) → 34 (hmax-tb) |
| scan-sep | 32 (gbfs-ff) → 38 (gbfs-ff) | 11 → 36 | 5 → 36 | 5 (astar-blind/lmcp) → 7 (hmax-tb) |
| orderfree-comb | 0/6 tried → 40 (5 configs) | – → 40 | – → 40 | 0/6 → 34 (hmax-tb) |
| orderfree-sep | 0/6 tried → 34 (wastar3-ff) | – → 30 | – → 30 | 0/6 → 8 (hmax, hmax-tb) |

Small problems: every FA config solves all 10 solvable problems on every model.

**Effort on tasks both sides solve (large, same config)**, classic VM time → FA M5 Pro time,
expansions classic → FA: scan-comb gbfs-ff 19 s → 0.30 s, 5358 → 32 (38 tasks); gbfs-cea
124 s → 0.60 s; scan-sep gbfs-ff 86 s → 0.76 s, 27k → 28 (32 tasks); gbfs-cea 160 s → 0.43 s.
Even allowing ~2x for hardware, FA is 13–190x faster (lama-first gains least). FA does not reach fewer states:
"evaluated" (forced intermediate states included) is about the same as classic (scan-comb
7.0k vs 5.4k), but the heuristic is computed only at agent decision states (1 in 126–1251
states).

**Optimal.** `lazy-astar-hmax-tb` is the FA optimal setting that scales: 34/40 large on
scan-comb and orderfree-comb (classic best: astar-hmax 31/40 on scan-comb, 0/6 on
order-free). The two settings that exist in the fork today scale poorly: `lazy_wastar` breaks f
ties FIFO and sweeps the whole f = C* plateau (`lazy-astar-hmax` 19–20/40), and blind 8/40.
FA proves optima for all 41 problems classic proved plus 3 more. On the separated models
every FA optimal config fails on memory (at most 7–8/40).

**Satisficing quality** (cost / optimum) is essentially unchanged: mean 1.00–1.03 under FA
(classic 1.00–1.06), except scan-sep gbfs-add / gbfs-cea at 1.09 because of one problem at 3.40.

**Order-free models under FA.** The interleaving blow-up is gone. orderfree-comb has the same
coverage as scan-comb and is the fastest model (0.47–0.75x scan-comb's search time on the
same tasks, every config). orderfree-sep is the weakest (2–6x slower than scan-comb for the
satisficing configs, more memouts).

**What limits FA: memory.** 477 FA runs hit the memory limit against 83 timeouts (plus 100
exhausted runs on the no-plan problems).
The fork's `apply_forced_actions` registers every intermediate forced state in the state
registry (about 1–1.3 KB each): 126 (orderfree-comb), 225 (scan-comb), 611 (orderfree-sep) and 1251
(scan-sep) per expansion, so 3 GB holds only a few thousand expansions on the separated
models. Registering only the fixed point of each forced chain (the chain is deterministic, so
duplicate detection on fixed points is enough; plan extraction re-applies the chain) would
cut memory by two to three orders of magnitude, and would most likely lift the separated
models and the optimal configs.

## Not done

- **Same-machine classic baseline**: not run (the machine went to sleep on battery after the
  FA sweep). On the M5 Pro, on AC:
  `python3 tools/benchmarking/fd_sweep.py --fd planners/fast-downward --groups A,B,C --jobs 12 --host m5pro --configs gbfs-ff,gbfs-add,gbfs-cea,gbfs-cg,wastar3-ff,lama-first,lazy-astar-blind,lazy-astar-hmax,lazy-astar-hmax-tb`
  then `compare_sweep.py --classic=inv0@vm --timing=inv0@m5pro`.
