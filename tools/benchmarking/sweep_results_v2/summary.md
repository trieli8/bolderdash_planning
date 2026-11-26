# New test domains vs old: classic sweep summary

Same machine (VM, 4 cores, 2.10 GHz Xeon), same planner (upstream Fast Downward
release-24.06.1), the same 11 classic configs, translator `inv0`, 300 s / 3 GB per
run, 4 jobs at a time. Only the test domains differ:

- old: `a9f6ad1` (`../sweep_results/results_vm.csv`)
- new: `a1a50ba`, the cool-ptolemy merge (`results_vm.csv` here). Changes: no
  negated preconditions, row gates in scan-sep, column blocks in scan-comb, dirty
  marking in the order-free models.

Full tables: `compare_old_vs_new_domains.md` (old vs new) and `report_classic.md`
(this sweep on its own).

## Same game

- 41 problems have a proven optimum on both sides, and **every optimal cost is the same**.
- One problem gained a proven optimum (L01 s016 t009 h2); none lost one.
- The same 4 problems have no plan on both sides (L11 t115, L11 t168, testing_level_2,
  testing_level_3).

## Coverage: 786 → 867 solved runs out of 1392 (+81)

| model | old | new |
|---|---|---|
| scan-comb | 380 | 391 (+11) |
| scan-sep | 253 | 323 (+70) |
| orderfree-comb | 81 | 81 |
| orderfree-sep | 72 | 72 |

Almost all of the gain is in **scan-sep**. On bd_level_01, 20x38, with h1 and h2
together:

- lama-first: 4/24 → 22/24
- gbfs-cea: 8/24 → 17/24
- eager-gbfs-ff: 12/24 → 16/24

On bd_levels 02..14:

- lama-first: 1/16 → 11/16
- eager-gbfs-ff: 4/16 → 11/16

Gains on scan-comb are small: gbfs-ff, eager-gbfs-ff and wastar3-ff now solve all
16 problems in levels 02..14 (before: 14). The optimal configs gain a few large
tasks on each scanner model.

The order-free models change nothing for classic planners. Large levels still
time out, because classic search has to explore the order in which objects are
updated within a tick. On small problems they need 30–60% fewer expansions.

## Why: less physics per move

Median physics steps per move in large solved plans:

- scan-comb: 201 → 116
- scan-sep: 1246 → 368

## Time (geometric means on tasks both sides solved, large problems)

| model | search time | translate + search |
|---|---|---|
| scan-sep, satisficing configs | 2.0–3.5x faster | 1.8–2.6x faster |
| scan-comb, satisficing configs | 1.2–1.4x faster | about even (0.95–1.02x) |
| optimal configs (both scanners) | 1.1–1.8x faster | |

**Translation is slower with the new domains**, although it produces fewer
operators (scan-comb ~21k → 18k, scan-sep ~36k → 34k).

- Sweep medians (new/old): scan-comb 1.37, scan-sep 1.31, orderfree-comb 1.30,
  orderfree-sep 1.61.
- Measured again on two scan-comb problems with only translations running
  (4 at a time), the slowdown was about **17%**:
  - 21.2 → 24.9 s
  - 15.8 → 18.5 s

  The sweep overstates it, probably because translations shared the machine with
  running searches.
- The extra time is all in the translator's relaxed-reachability phase
  ("Computing model": +2.4–3.2 s CPU). The row and column gates add preconditions
  to ground.
- On scan-comb this extra time cancels the search speedup. On scan-sep the
  search savings are much larger.

## Satisficing plan quality

Unchanged on the whole. lama-first on scan-sep went from a mean of 1.00 to 1.11
× the optimum. That compares different sets of tasks: the old domains solved
only the easy ones.
