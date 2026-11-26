# Forced-action vs classic Fast Downward sweep

- FA side: **inv0+fa+fixpt@m5pro** (1944 runs)
- classic side: **inv0@m5pro** (1200 runs)
- classic timing baseline: **inv0@m5pro** (1200 runs, same machine as FA)
- translate time classic / FA side (same tasks, 96 problems): median 1.25x (range 0.98-1.57), a rough machine speed ratio
- **m5pro**: host=m5pro; cpus=18; ram_gb=48; cpu=Apple M5 Pro; platform=macOS-26.5.2-arm64-arm-64bit-Mach-O; run[results_m5pro.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0; run[results_m5pro_fa.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0; run[results_m5pro_fa_fixpt.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fd-fixpoint@52938c8b5 FD_STATE_DUMP=0 domains=a9f6ad1

## No-plan problems and disagreements

Problems some search exhausted (no plan), excluded from coverage: L11 t115 [FA/orderfree-comb, FA/scan-comb, classic-base/scan-comb, classic/scan-comb], L11 t168 [FA/orderfree-comb, FA/scan-comb, classic-base/scan-comb, classic/scan-comb], testing_level_2 [FA/orderfree-comb, FA/orderfree-sep, FA/scan-comb, FA/scan-sep, classic-base/orderfree-comb, classic-base/scan-comb, classic-base/scan-sep, classic/orderfree-comb, classic/scan-comb, classic/scan-sep], testing_level_3 [FA/orderfree-comb, FA/orderfree-sep, FA/scan-comb, FA/scan-sep, classic-base/orderfree-comb, classic-base/scan-comb, classic-base/scan-sep, classic/orderfree-comb, classic/scan-comb, classic/scan-sep]

No problem is solved by one model/side and proved plan-less by another.

Optimal costs: 45 problems solved optimally on some side; all optimal costs agree (across sides, models and configs).
No plan is cheaper than a proven optimum.

## Coverage (solved / solvable problems run), classic → FA

Cells are `classic → FA`; a config only on one side shows `–` on the other. FA runs only the LazySearch configs (the eager / A* configs ignore __FORCED__).


### scan-comb

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 → 10/10 | 24/24 → 24/24 | 14/16 (2TO) → 16/16 |
| gbfs-add | 10/10 → 10/10 | 24/24 → 24/24 | 15/16 (1TO) → 16/16 |
| gbfs-cea | 10/10 → 10/10 | 24/24 → 24/24 | 12/16 (4TO) → 16/16 |
| gbfs-cg | 10/10 → 10/10 | 3/24 (21TO) → 7/24 (17TO) | 1/16 (2MO 13TO) → 1/16 (2MO 13TO) |
| wastar3-ff | 10/10 → 10/10 | 24/24 → 24/24 | 14/16 (2TO) → 16/16 |
| lama-first | 10/10 → 10/10 | 10/24 (14TO) → 24/24 | 4/16 (12TO) → 16/16 |
| lazy-astar-blind | 10/10 → 10/10 | 6/24 (18MO) → 8/24 (16TO) | 1/16 (15MO) → 1/16 (15TO) |
| lazy-astar-hmax | 10/10 → 10/10 | 13/24 (11TO) → 16/24 (8TO) | 4/16 (12TO) → 8/16 (8TO) |
| lazy-astar-hmax-tb | 10/10 → 10/10 | 20/24 (4TO) → 22/24 (2TO) | 11/16 (5TO) → 13/16 (3TO) |

### scan-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 → 10/10 | 21/24 (3TO) → 24/24 | 10/16 (6TO) → 14/16 (2TO) |
| gbfs-add | 10/10 → 10/10 | 21/24 (3TO) → 24/24 | 9/16 (7TO) → 14/16 (2TO) |
| gbfs-cea | 10/10 → 10/10 | 7/24 (17TO) → 24/24 | 3/16 (13TO) → 14/16 (2TO) |
| gbfs-cg | 10/10 → 10/10 | 4/24 (20TO) → 7/24 (17TO) | 1/16 (15TO) → 1/16 (15TO) |
| wastar3-ff | 10/10 → 10/10 | 19/24 (5TO) → 24/24 | 9/16 (7TO) → 15/16 (1TO) |
| lama-first | 10/10 → 10/10 | 4/24 (20TO) → 24/24 | 1/16 (15TO) → 15/16 (1TO) |
| lazy-astar-blind | 10/10 → 10/10 | 4/24 (20MO) → 7/24 (17TO) | 1/16 (15MO) → 1/16 (15TO) |
| lazy-astar-hmax | 10/10 → 10/10 | 3/24 (21TO) → 7/24 (17TO) | 1/16 (15TO) → 1/16 (15TO) |
| lazy-astar-hmax-tb | 10/10 → 10/10 | 3/24 (21TO) → 7/24 (17TO) | 1/16 (15TO) → 1/16 (15TO) |

### orderfree-comb

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 9/10 (1TO) → 10/10 | 0/6 (6TO) → 24/24 | – → 16/16 |
| gbfs-add | 9/10 (1TO) → 10/10 | – → 24/24 | – → 16/16 |
| gbfs-cea | 9/10 (1TO) → 10/10 | – → 24/24 | – → 16/16 |
| gbfs-cg | 9/10 (1TO) → 10/10 | – → 7/24 (17TO) | – → 1/16 (15TO) |
| wastar3-ff | 9/10 (1TO) → 10/10 | – → 24/24 | – → 16/16 |
| lama-first | 9/10 (1TO) → 10/10 | – → 24/24 | – → 16/16 |
| lazy-astar-blind | 9/10 (1TO) → 10/10 | – → 7/24 (17TO) | – → 1/16 (15TO) |
| lazy-astar-hmax | 9/10 (1TO) → 10/10 | – → 16/24 (8TO) | – → 8/16 (8TO) |
| lazy-astar-hmax-tb | 9/10 (1TO) → 10/10 | – → 22/24 (2TO) | – → 13/16 (3TO) |

### orderfree-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 8/10 (2TO) → 10/10 | 0/6 (6TO) → 18/24 (6TO) | – → 13/16 (3TO) |
| gbfs-add | 8/10 (2TO) → 10/10 | – → 18/24 (6TO) | – → 14/16 (2TO) |
| gbfs-cea | 8/10 (2TO) → 10/10 | – → 18/24 (6TO) | – → 12/16 (4TO) |
| gbfs-cg | 8/10 (2TO) → 10/10 | – → 6/24 (18TO) | – → 1/16 (15TO) |
| wastar3-ff | 8/10 (2TO) → 10/10 | – → 18/24 (6TO) | – → 16/16 |
| lama-first | 8/10 (2TO) → 10/10 | – → 18/24 (6TO) | – → 15/16 (1TO) |
| lazy-astar-blind | 8/10 (2TO) → 10/10 | – → 6/24 (18TO) | – → 1/16 (15TO) |
| lazy-astar-hmax | 8/10 (2TO) → 10/10 | – → 7/24 (17TO) | – → 1/16 (15TO) |
| lazy-astar-hmax-tb | 8/10 (2TO) → 10/10 | – → 7/24 (17TO) | – → 1/16 (15TO) |

## Search effort on tasks solved by both (same config)

Geometric means over the tasks the config solved on both sides. Times: classic from the same-machine baseline. Classic expansions include every physics step; FA expansions are agent decision states only, FA evaluated counts the states the FA build registers: every forced intermediate state in the original fork, only the decision states in the fixpoint build (claude/lazy-forced-fixpoints).


**scan-comb**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 10 | 0.03s | 0.00s | 12x | 621 | 16 | 623 | 17 |
| gbfs-ff | large | 38 | 24s | 0.18s | 130x | 5411 | 32 | 5413 | 34 |
| gbfs-add | small | 10 | 0.03s | 0.00s | 12x | 621 | 16 | 623 | 17 |
| gbfs-add | large | 39 | 27s | 0.20s | 130x | 6185 | 36 | 6186 | 37 |
| gbfs-cea | small | 10 | 0.07s | 0.00s | 17x | 636 | 16 | 637 | 17 |
| gbfs-cea | large | 36 | 126s | 0.57s | 222x | 5121 | 29 | 5122 | 31 |
| gbfs-cg | small | 10 | 0.07s | 0.01s | 8x | 3624 | 67 | 3626 | 69 |
| gbfs-cg | large | 4 | 106s | 0.50s | 214x | 23k | 53 | 23k | 54 |
| wastar3-ff | small | 10 | 0.04s | 0.00s | 14x | 635 | 16 | 637 | 18 |
| wastar3-ff | large | 38 | 24s | 0.19s | 124x | 5718 | 33 | 5719 | 35 |
| lama-first | small | 10 | 0.03s | 0.00s | 15x | 1102 | 18 | 1104 | 19 |
| lama-first | large | 14 | 14s | 0.11s | 129x | 11k | 21 | 11k | 23 |
| lazy-astar-blind | small | 10 | 0.01s | 0.01s | 2x | 4392 | 74 | 4395 | 76 |
| lazy-astar-blind | large | 7 | 8.35s | 1.10s | 8x | 164k | 377 | 164k | 381 |
| lazy-astar-hmax | small | 10 | 0.03s | 0.00s | 7x | 1261 | 46 | 1263 | 47 |
| lazy-astar-hmax | large | 17 | 25s | 0.70s | 36x | 17k | 198 | 17k | 201 |
| lazy-astar-hmax-tb | small | 10 | 0.02s | 0.00s | 7x | 724 | 24 | 726 | 25 |
| lazy-astar-hmax-tb | large | 31 | 14s | 0.19s | 71x | 7071 | 44 | 7072 | 46 |

**scan-sep**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 10 | 0.06s | 0.00s | 32x | 1128 | 15 | 1130 | 16 |
| gbfs-ff | large | 31 | 86s | 0.17s | 508x | 26k | 28 | 26k | 29 |
| gbfs-add | small | 10 | 0.07s | 0.00s | 35x | 1128 | 15 | 1129 | 16 |
| gbfs-add | large | 30 | 83s | 0.16s | 516x | 25k | 26 | 25k | 28 |
| gbfs-cea | small | 10 | 0.25s | 0.00s | 54x | 1173 | 15 | 1174 | 16 |
| gbfs-cea | large | 10 | 174s | 0.20s | 876x | 9571 | 11 | 9572 | 12 |
| gbfs-cg | small | 10 | 0.06s | 0.00s | 18x | 3464 | 44 | 3466 | 45 |
| gbfs-cg | large | 5 | 31s | 0.30s | 106x | 80k | 83 | 80k | 85 |
| wastar3-ff | small | 10 | 0.07s | 0.00s | 36x | 1199 | 16 | 1201 | 17 |
| wastar3-ff | large | 28 | 78s | 0.15s | 525x | 23k | 24 | 23k | 26 |
| lama-first | small | 10 | 0.17s | 0.00s | 87x | 4486 | 19 | 4488 | 20 |
| lama-first | large | 5 | 28s | 0.04s | 765x | 20k | 7 | 20k | 8 |
| lazy-astar-blind | small | 10 | 0.02s | 0.00s | 5x | 6210 | 63 | 6213 | 64 |
| lazy-astar-blind | large | 5 | 7.31s | 0.31s | 23x | 224k | 106 | 224k | 108 |
| lazy-astar-hmax | small | 10 | 0.11s | 0.00s | 25x | 4052 | 55 | 4055 | 56 |
| lazy-astar-hmax | large | 4 | 43s | 0.16s | 262x | 31k | 38 | 31k | 40 |
| lazy-astar-hmax-tb | small | 10 | 0.11s | 0.00s | 25x | 3957 | 50 | 3960 | 51 |
| lazy-astar-hmax-tb | large | 4 | 24s | 0.09s | 265x | 18k | 20 | 18k | 21 |

**orderfree-comb**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 9 | 0.02s | 0.00s | 10x | 319 | 16 | 322 | 17 |
| gbfs-add | small | 9 | 0.02s | 0.00s | 10x | 320 | 16 | 323 | 17 |
| gbfs-cea | small | 9 | 0.02s | 0.00s | 10x | 259 | 16 | 262 | 17 |
| gbfs-cg | small | 9 | 0.04s | 0.00s | 9x | 1314 | 58 | 1320 | 59 |
| wastar3-ff | small | 9 | 0.02s | 0.00s | 10x | 334 | 16 | 337 | 17 |
| lama-first | small | 9 | 0.01s | 0.00s | 9x | 383 | 18 | 385 | 19 |
| lazy-astar-blind | small | 9 | 0.01s | 0.00s | 5x | 1454 | 61 | 1460 | 63 |
| lazy-astar-hmax | small | 9 | 0.02s | 0.00s | 8x | 730 | 44 | 734 | 45 |
| lazy-astar-hmax-tb | small | 9 | 0.02s | 0.00s | 7x | 398 | 23 | 402 | 25 |

**orderfree-sep**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 8 | 0.01s | 0.00s | 6x | 345 | 16 | 347 | 17 |
| gbfs-add | small | 8 | 0.01s | 0.00s | 6x | 353 | 16 | 355 | 17 |
| gbfs-cea | small | 8 | 0.02s | 0.00s | 7x | 307 | 16 | 309 | 17 |
| gbfs-cg | small | 8 | 0.01s | 0.00s | 4x | 1005 | 44 | 1007 | 45 |
| wastar3-ff | small | 8 | 0.01s | 0.00s | 7x | 395 | 17 | 397 | 18 |
| lama-first | small | 8 | 0.02s | 0.00s | 8x | 695 | 20 | 697 | 21 |
| lazy-astar-blind | small | 8 | 0.01s | 0.00s | 3x | 1894 | 67 | 1898 | 68 |
| lazy-astar-hmax | small | 8 | 0.02s | 0.00s | 5x | 1008 | 53 | 1010 | 54 |
| lazy-astar-hmax-tb | small | 8 | 0.02s | 0.00s | 5x | 706 | 36 | 709 | 38 |

## FA optimal configs

| model | config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 | cost = known optimum | cost ≠ |
|---|---|---|---|---|---|---|
| scan-comb | lazy-astar-blind | 10/10 | 8/24 (16TO) | 1/16 (15TO) | 19 | 0 |
| scan-comb | lazy-astar-hmax | 10/10 | 16/24 (8TO) | 8/16 (8TO) | 33 | 0 |
| scan-comb | lazy-astar-hmax-tb | 10/10 | 22/24 (2TO) | 13/16 (3TO) | 41 | 0 |
| scan-sep | lazy-astar-blind | 10/10 | 7/24 (17TO) | 1/16 (15TO) | 18 | 0 |
| scan-sep | lazy-astar-hmax | 10/10 | 7/24 (17TO) | 1/16 (15TO) | 18 | 0 |
| scan-sep | lazy-astar-hmax-tb | 10/10 | 7/24 (17TO) | 1/16 (15TO) | 18 | 0 |
| orderfree-comb | lazy-astar-blind | 10/10 | 7/24 (17TO) | 1/16 (15TO) | 18 | 0 |
| orderfree-comb | lazy-astar-hmax | 10/10 | 16/24 (8TO) | 8/16 (8TO) | 33 | 0 |
| orderfree-comb | lazy-astar-hmax-tb | 10/10 | 22/24 (2TO) | 13/16 (3TO) | 41 | 0 |
| orderfree-sep | lazy-astar-blind | 10/10 | 6/24 (18TO) | 1/16 (15TO) | 17 | 0 |
| orderfree-sep | lazy-astar-hmax | 10/10 | 7/24 (17TO) | 1/16 (15TO) | 18 | 0 |
| orderfree-sep | lazy-astar-hmax-tb | 10/10 | 7/24 (17TO) | 1/16 (15TO) | 18 | 0 |

## Satisficing plan quality (cost / known optimum), classic → FA

Mean (max) of cost / optimum over the solved tasks with a known optimum (optimum from any side, model or optimal config).

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first |
|---|---|---|---|---|---|---|
| scan-comb | 1.02 (1.25, n=44) → 1.02 (1.36, n=45) | 1.02 (1.32, n=45) → 1.02 (1.32, n=45) | 1.02 (1.25, n=44) → 1.02 (1.32, n=45) | 1.03 (1.25, n=14) → 1.02 (1.25, n=18) | 1.01 (1.22, n=44) → 1.02 (1.25, n=45) | 1.22 (1.67, n=24) → 1.03 (1.50, n=45) |
| scan-sep | 1.03 (1.50, n=41) → 1.04 (1.50, n=44) | 1.03 (1.50, n=40) → 1.09 (3.40, n=44) | 1.00 (1.00, n=20) → 1.09 (3.40, n=44) | 1.00 (1.00, n=15) → 1.00 (1.00, n=18) | 1.03 (1.50, n=38) → 1.04 (1.50, n=45) | 1.00 (1.00, n=15) → 1.09 (3.25, n=45) |
| orderfree-comb | 1.03 (1.25, n=9) → 1.01 (1.22, n=45) | 1.03 (1.25, n=9) → 1.02 (1.32, n=45) | 1.00 (1.00, n=9) → 1.02 (1.32, n=45) | 1.00 (1.00, n=9) → 1.01 (1.10, n=18) | 1.00 (1.00, n=9) → 1.01 (1.25, n=45) | 1.00 (1.00, n=9) → 1.01 (1.12, n=45) |
| orderfree-sep | 1.00 (1.00, n=8) → 1.02 (1.24, n=39) | 1.00 (1.00, n=8) → 1.02 (1.22, n=39) | 1.00 (1.00, n=8) → 1.01 (1.22, n=39) | 1.00 (1.00, n=8) → 1.01 (1.11, n=17) | 1.00 (1.00, n=8) → 1.02 (1.50, n=40) | 1.00 (1.00, n=8) → 1.04 (1.54, n=39) |

## Models compared under FA

Per config, on the large problems (l1 + other). Coverage is solved / problems run for that model (`–` = not run). `common` counts the large tasks solved by every model that ran the config; the time columns are geometric-mean search times over that common set.

| config | scan-comb cov | scan-sep cov | orderfree-comb cov | orderfree-sep cov | common | scan-comb time | scan-sep time | orderfree-comb time | orderfree-sep time |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | 40/40 | 38/40 | 40/40 | 31/40 | 30 | 0.17s | 0.17s | 0.19s | 1.08s |
| gbfs-add | 40/40 | 38/40 | 40/40 | 32/40 | 31 | 0.17s | 0.23s | 0.19s | 1.13s |
| gbfs-cea | 40/40 | 38/40 | 40/40 | 30/40 | 29 | 0.48s | 0.50s | 0.30s | 1.17s |
| gbfs-cg | 8/40 | 8/40 | 8/40 | 7/40 | 7 | 2.37s | 0.96s | 1.89s | 6.83s |
| wastar3-ff | 40/40 | 39/40 | 40/40 | 34/40 | 33 | 0.18s | 0.29s | 0.21s | 1.59s |
| lama-first | 40/40 | 39/40 | 40/40 | 33/40 | 32 | 0.23s | 0.29s | 0.23s | 1.68s |
| lazy-astar-blind | 9/40 | 8/40 | 8/40 | 7/40 | 7 | 1.10s | 0.95s | 1.30s | 7.86s |
| lazy-astar-hmax | 24/40 | 8/40 | 24/40 | 8/40 | 8 | 0.20s | 1.44s | 0.17s | 5.52s |
| lazy-astar-hmax-tb | 35/40 | 8/40 | 35/40 | 8/40 | 8 | 0.09s | 0.83s | 0.07s | 3.47s |

Search time relative to scan-comb under FA (pairwise: geometric mean of time / scan-comb time over the large tasks both solved; >1 = slower than scan-comb).

| config | scan-sep | orderfree-comb | orderfree-sep |
|---|---|---|---|
| gbfs-ff | 1.13x (n=38) | 1.13x (n=40) | 6.41x (n=31) |
| gbfs-add | 1.46x (n=38) | 1.15x (n=40) | 6.62x (n=32) |
| gbfs-cea | 1.33x (n=38) | 0.61x (n=40) | 2.45x (n=30) |
| gbfs-cg | 0.44x (n=8) | 0.81x (n=8) | 2.88x (n=7) |
| wastar3-ff | 1.50x (n=39) | 1.09x (n=40) | 8.07x (n=34) |
| lama-first | 1.35x (n=39) | 0.95x (n=40) | 6.77x (n=33) |
| lazy-astar-blind | 1.03x (n=8) | 1.30x (n=8) | 7.15x (n=7) |
| lazy-astar-hmax | 7.21x (n=8) | 1.49x (n=24) | 27.56x (n=8) |
| lazy-astar-hmax-tb | 9.64x (n=8) | 1.29x (n=35) | 40.10x (n=8) |
