# Forced-action vs classic Fast Downward sweep

- FA side: **inv0+fa** (1944 runs)
- classic side: **inv0@vm** (1392 runs)
- classic timing baseline: **inv0@m5pro** (1200 runs, same machine as FA)
- translate time classic / FA side (same tasks, 96 problems): median 1.86x (range 1.58-3.53), a rough machine speed ratio
- `[k ≤150s]` in an FA coverage cell: solves within 300/2 s of search time (the classic machine's limit scaled by --speed); shown only where it differs
- **m5pro**: host=m5pro; cpus=18; ram_gb=48; cpu=Apple M5 Pro; platform=macOS-26.5.2-arm64-arm-64bit-Mach-O; run[results_m5pro.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0 domains=a9f6ad1; run[results_m5pro_fa.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0 domains=a9f6ad1
- **vm**: host=vm; cpus=4; ram_gb=16; cpu=Intel(R) Xeon(R) Processor @ 2.10GHz (groups A, C and the first 41 group-B jobs, until a container restart 2026-11-25 ~00:45 UTC); Intel(R) Xeon(R) Processor @ 2.30GHz (remaining group-B jobs); platform=Linux-6.18.44-fc-v819-x86_64-with-glibc2.39, then Linux-6.18.44-fc-v880-x86_64-with-glibc2.39; run[results_vm.csv]=jobs=4 timeout=300s mem=3G mem_limit=rlimit (FD driver) fd=upstream fast-downward release-24.06.1 (downward@1eef26b) classic configs only domains=a9f6ad1

## No-plan problems and disagreements

Problems some search exhausted (no plan), excluded from coverage: L11 t115 [FA/orderfree-comb, FA/scan-comb, classic-base/scan-comb, classic/scan-comb], L11 t168 [FA/orderfree-comb, FA/scan-comb, classic-base/scan-comb, classic/scan-comb], testing_level_2 [FA/orderfree-comb, FA/orderfree-sep, FA/scan-comb, FA/scan-sep, classic-base/orderfree-comb, classic-base/scan-comb, classic-base/scan-sep, classic/orderfree-comb, classic/scan-comb, classic/scan-sep], testing_level_3 [FA/orderfree-comb, FA/orderfree-sep, FA/scan-comb, FA/scan-sep, classic-base/orderfree-comb, classic-base/scan-comb, classic-base/scan-sep, classic/orderfree-comb, classic/scan-comb, classic/scan-sep]

No problem is solved by one model/side and proved plan-less by another.

Optimal costs: 44 problems solved optimally on some side; all optimal costs agree (across sides, models and configs).
No plan is cheaper than a proven optimum.

## Coverage (solved / solvable problems run), classic → FA

Cells are `classic → FA`; a config only on one side shows `–` on the other. FA runs only the LazySearch configs (the eager / A* configs ignore __FORCED__).


### scan-comb

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 → 10/10 | 24/24 → 24/24 | 14/16 (2TO) → 16/16 |
| eager-gbfs-ff | 10/10 → – | 24/24 → – | 14/16 (2TO) → – |
| gbfs-add | 10/10 → 10/10 | 24/24 → 24/24 | 16/16 → 16/16 |
| gbfs-cea | 10/10 → 10/10 | 18/24 (6TO) → 24/24 | 12/16 (4TO) → 16/16 |
| gbfs-cg | 10/10 → 10/10 | 3/24 (21TO) → 5/24 (19MO) | 1/16 (4MO 11TO) → 1/16 (15MO) |
| wastar3-ff | 10/10 → 10/10 | 24/24 → 24/24 | 14/16 (2TO) → 16/16 [15 ≤150s] |
| lama-first | 10/10 → 10/10 | 24/24 → 24/24 | 12/16 (4TO) → 15/16 (1MO) |
| astar-blind | 10/10 → – | 6/24 (16MO 2TO) → – | 1/16 (15MO) → – |
| astar-hmax | 10/10 → – | 20/24 (4TO) → – | 11/16 (5TO) → – |
| astar-lmcp | 10/10 → – | 7/24 (16MO 1TO) → – | 2/16 (14MO) → – |
| astar-ms | 9/10 (1TO) → – | – → – | – → – |
| lazy-astar-blind | – → 10/10 | – → 7/24 (17MO) | – → 1/16 (15MO) |
| lazy-astar-hmax | – → 10/10 | – → 14/24 (10MO) | – → 5/16 (11MO) |
| lazy-astar-hmax-tb | – → 10/10 | – → 22/24 (2MO) | – → 12/16 (4MO) |

### scan-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 → 10/10 | 22/24 (2TO) → 24/24 | 10/16 (6TO) → 14/16 (2MO) |
| eager-gbfs-ff | 10/10 → – | 12/24 (12TO) → – | 4/16 (12TO) → – |
| gbfs-add | 10/10 → 10/10 | 22/24 (2TO) → 24/24 | 9/16 (7TO) → 12/16 (4MO) |
| gbfs-cea | 10/10 → 10/10 | 8/24 (16TO) → 24/24 | 3/16 (13TO) → 12/16 (4MO) |
| gbfs-cg | 10/10 → 10/10 | 3/24 (21TO) → 4/24 (20MO) | 1/16 (15TO) → 1/16 (15MO) |
| wastar3-ff | 10/10 → 10/10 | 22/24 (2TO) → 24/24 | 9/16 (7TO) → 12/16 (4MO) |
| lama-first | 10/10 → 10/10 | 4/24 (20TO) → 24/24 | 1/16 (15TO) → 12/16 (4MO) |
| astar-blind | 10/10 → – | 4/24 (20MO) → – | 1/16 (15MO) → – |
| astar-hmax | 10/10 → – | 3/24 (21TO) → – | 1/16 (15TO) → – |
| astar-lmcp | 10/10 → – | 4/24 (20MO) → – | 1/16 (15MO) → – |
| astar-ms | 9/10 (1TO) → – | – → – | – → – |
| lazy-astar-blind | – → 10/10 | – → 4/24 (20MO) | – → 1/16 (15MO) |
| lazy-astar-hmax | – → 10/10 | – → 4/24 (20MO) | – → 1/16 (15MO) |
| lazy-astar-hmax-tb | – → 10/10 | – → 6/24 (18MO) | – → 1/16 (15MO) |

### orderfree-comb

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 9/10 (1TO) → 10/10 | 0/6 (6TO) → 24/24 | – → 16/16 |
| eager-gbfs-ff | 9/10 (1TO) → – | – → – | – → – |
| gbfs-add | 9/10 (1TO) → 10/10 | – → 24/24 | – → 16/16 |
| gbfs-cea | 9/10 (1TO) → 10/10 | – → 24/24 | – → 16/16 |
| gbfs-cg | 9/10 (1TO) → 10/10 | – → 7/24 (11MO 6TO) | – → 1/16 (11MO 4TO) |
| wastar3-ff | 9/10 (1TO) → 10/10 | – → 24/24 | – → 16/16 |
| lama-first | 9/10 (1TO) → 10/10 | – → 24/24 | – → 16/16 |
| astar-blind | 9/10 (1TO) → – | – → – | – → – |
| astar-hmax | 9/10 (1TO) → – | 0/6 (6TO) → – | – → – |
| astar-lmcp | 0/10 (10unsupported) → – | – → – | – → – |
| astar-ms | 0/10 (10unsupported) → – | – → – | – → – |
| lazy-astar-blind | – → 10/10 | – → 7/24 (14MO 3TO) | – → 1/16 (12MO 3TO) |
| lazy-astar-hmax | – → 10/10 | – → 15/24 [14 ≤150s] (5MO 4TO) | – → 5/16 (9MO 2TO) |
| lazy-astar-hmax-tb | – → 10/10 | – → 22/24 (2MO) | – → 12/16 (4MO) |

### orderfree-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 8/10 (2TO) → 10/10 | 0/6 (6TO) → 18/24 (3MO 3TO) | – → 13/16 [12 ≤150s] (3MO) |
| eager-gbfs-ff | 8/10 (2TO) → – | – → – | – → – |
| gbfs-add | 8/10 (2TO) → 10/10 | – → 18/24 (6MO) | – → 14/16 (2MO) |
| gbfs-cea | 8/10 (2TO) → 10/10 | – → 18/24 (5MO 1TO) | – → 12/16 (2MO 2TO) |
| gbfs-cg | 8/10 (2TO) → 10/10 | – → 4/24 (20MO) | – → 1/16 (13MO 2TO) |
| wastar3-ff | 8/10 (2TO) → 10/10 | – → 18/24 (1MO 5TO) | – → 16/16 [12 ≤150s] |
| lama-first | 8/10 (2TO) → 10/10 | – → 18/24 (6MO) | – → 12/16 (1MO 3TO) |
| astar-blind | 8/10 (2MO) → – | – → – | – → – |
| astar-hmax | 8/10 (2TO) → – | 0/6 (6TO) → – | – → – |
| astar-lmcp | 0/10 (10unsupported) → – | – → – | – → – |
| astar-ms | 0/10 (10unsupported) → – | – → – | – → – |
| lazy-astar-blind | – → 10/10 | – → 5/24 [4 ≤150s] (17MO 2TO) | – → 1/16 (9MO 6TO) |
| lazy-astar-hmax | – → 10/10 | – → 7/24 [6 ≤150s] (9MO 8TO) | – → 1/16 (9MO 6TO) |
| lazy-astar-hmax-tb | – → 10/10 | – → 7/24 (11MO 6TO) | – → 1/16 (8MO 7TO) |

## Search effort on tasks solved by both (same config)

Geometric means over the tasks the config solved on both sides. Times: classic from the same-machine baseline. Classic expansions include every physics step; FA expansions are agent decision states only, FA evaluated includes the forced intermediate states.


**scan-comb**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 10 | 0.03s | 0.00s | 10x | 621 | 16 | 623 | 680 |
| gbfs-ff | large | 38 | 24s | 0.30s | 79x | 5411 | 32 | 5413 | 7020 |
| gbfs-add | small | 10 | 0.03s | 0.00s | 10x | 621 | 16 | 623 | 680 |
| gbfs-add | large | 39 | 27s | 0.33s | 80x | 6185 | 36 | 6186 | 7815 |
| gbfs-cea | small | 10 | 0.07s | 0.00s | 16x | 636 | 16 | 637 | 678 |
| gbfs-cea | large | 36 | 126s | 0.69s | 184x | 5121 | 29 | 5122 | 6296 |
| gbfs-cg | small | 10 | 0.07s | 0.01s | 6x | 3624 | 67 | 3626 | 3848 |
| gbfs-cg | large | 4 | 106s | 1.12s | 95x | 23k | 53 | 23k | 31k |
| wastar3-ff | small | 10 | 0.04s | 0.00s | 11x | 635 | 16 | 637 | 708 |
| wastar3-ff | large | 38 | 24s | 0.32s | 76x | 5718 | 33 | 5719 | 7173 |
| lama-first | small | 10 | 0.03s | 0.00s | 12x | 1102 | 18 | 1104 | 821 |
| lama-first | large | 14 | 14s | 0.25s | 56x | 11k | 21 | 11k | 7851 |
| lazy-astar-blind | small | 10 | 0.01s | 0.01s | 1x | 4392 | 74 | 4395 | 4310 |
| lazy-astar-blind | large | 7 | 8.35s | 3.66s | 2x | 164k | 377 | 164k | 124k |
| lazy-astar-hmax | small | 10 | 0.03s | 0.01s | 5x | 1261 | 46 | 1263 | 2351 |
| lazy-astar-hmax | large | 17 | 25s | 1.75s | 14x | 17k | 198 | 17k | 48k |
| lazy-astar-hmax-tb | small | 10 | 0.02s | 0.00s | 5x | 724 | 24 | 726 | 1086 |
| lazy-astar-hmax-tb | large | 31 | 14s | 0.39s | 35x | 7071 | 44 | 7072 | 11k |

**scan-sep**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 10 | 0.06s | 0.00s | 19x | 1128 | 15 | 1130 | 1288 |
| gbfs-ff | large | 31 | 86s | 0.74s | 116x | 26k | 28 | 26k | 34k |
| gbfs-add | small | 10 | 0.07s | 0.00s | 19x | 1128 | 15 | 1129 | 1288 |
| gbfs-add | large | 30 | 83s | 0.71s | 117x | 25k | 26 | 25k | 33k |
| gbfs-cea | small | 10 | 0.25s | 0.01s | 42x | 1173 | 15 | 1174 | 1274 |
| gbfs-cea | large | 10 | 174s | 0.40s | 438x | 9571 | 11 | 9572 | 13k |
| gbfs-cg | small | 10 | 0.06s | 0.01s | 7x | 3464 | 44 | 3466 | 4279 |
| gbfs-cg | large | 5 | 31s | 2.20s | 14x | 80k | 83 | 80k | 104k |
| wastar3-ff | small | 10 | 0.07s | 0.00s | 21x | 1199 | 16 | 1201 | 1336 |
| wastar3-ff | large | 28 | 78s | 0.65s | 119x | 23k | 24 | 23k | 30k |
| lama-first | small | 10 | 0.17s | 0.00s | 45x | 4486 | 19 | 4488 | 1617 |
| lama-first | large | 5 | 28s | 0.18s | 153x | 20k | 7 | 20k | 8776 |
| lazy-astar-blind | small | 10 | 0.02s | 0.01s | 2x | 6210 | 63 | 6213 | 6212 |
| lazy-astar-blind | large | 5 | 7.31s | 2.72s | 3x | 224k | 106 | 224k | 133k |
| lazy-astar-hmax | small | 10 | 0.11s | 0.01s | 11x | 4052 | 55 | 4055 | 5172 |
| lazy-astar-hmax | large | 4 | 43s | 1.02s | 42x | 31k | 38 | 31k | 48k |
| lazy-astar-hmax-tb | small | 10 | 0.11s | 0.01s | 12x | 3957 | 50 | 3960 | 4679 |
| lazy-astar-hmax-tb | large | 4 | 24s | 0.54s | 44x | 18k | 20 | 18k | 25k |

**orderfree-comb**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 9 | 0.02s | 0.00s | 10x | 319 | 16 | 322 | 125 |
| gbfs-add | small | 9 | 0.02s | 0.00s | 9x | 320 | 16 | 323 | 125 |
| gbfs-cea | small | 9 | 0.02s | 0.00s | 10x | 259 | 16 | 262 | 124 |
| gbfs-cg | small | 9 | 0.04s | 0.00s | 8x | 1314 | 58 | 1320 | 489 |
| wastar3-ff | small | 9 | 0.02s | 0.00s | 9x | 334 | 16 | 337 | 129 |
| lama-first | small | 9 | 0.01s | 0.00s | 9x | 383 | 18 | 385 | 145 |
| lazy-astar-blind | small | 9 | 0.01s | 0.00s | 4x | 1454 | 61 | 1460 | 521 |
| lazy-astar-hmax | small | 9 | 0.02s | 0.00s | 7x | 730 | 44 | 734 | 357 |
| lazy-astar-hmax-tb | small | 9 | 0.02s | 0.00s | 7x | 398 | 23 | 402 | 188 |

**orderfree-sep**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 8 | 0.01s | 0.00s | 6x | 345 | 16 | 347 | 291 |
| gbfs-add | small | 8 | 0.01s | 0.00s | 6x | 353 | 16 | 355 | 291 |
| gbfs-cea | small | 8 | 0.02s | 0.00s | 8x | 307 | 16 | 309 | 290 |
| gbfs-cg | small | 8 | 0.01s | 0.00s | 4x | 1005 | 44 | 1007 | 887 |
| wastar3-ff | small | 8 | 0.01s | 0.00s | 6x | 395 | 17 | 397 | 302 |
| lama-first | small | 8 | 0.02s | 0.00s | 8x | 695 | 20 | 697 | 355 |
| lazy-astar-blind | small | 8 | 0.01s | 0.01s | 2x | 1894 | 67 | 1898 | 1366 |
| lazy-astar-hmax | small | 8 | 0.02s | 0.00s | 4x | 1008 | 52 | 1010 | 1002 |
| lazy-astar-hmax-tb | small | 8 | 0.02s | 0.00s | 4x | 706 | 36 | 709 | 664 |

## FA optimal configs

| model | config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 | cost = known optimum | cost ≠ |
|---|---|---|---|---|---|---|
| scan-comb | lazy-astar-blind | 10/10 | 7/24 (17MO) | 1/16 (15MO) | 18 | 0 |
| scan-comb | lazy-astar-hmax | 10/10 | 14/24 (10MO) | 5/16 (11MO) | 29 | 0 |
| scan-comb | lazy-astar-hmax-tb | 10/10 | 22/24 (2MO) | 12/16 (4MO) | 41 | 0 |
| scan-sep | lazy-astar-blind | 10/10 | 4/24 (20MO) | 1/16 (15MO) | 15 | 0 |
| scan-sep | lazy-astar-hmax | 10/10 | 4/24 (20MO) | 1/16 (15MO) | 15 | 0 |
| scan-sep | lazy-astar-hmax-tb | 10/10 | 6/24 (18MO) | 1/16 (15MO) | 17 | 0 |
| orderfree-comb | lazy-astar-blind | 10/10 | 7/24 (14MO 3TO) | 1/16 (12MO 3TO) | 18 | 0 |
| orderfree-comb | lazy-astar-hmax | 10/10 | 15/24 (5MO 4TO) | 5/16 (9MO 2TO) | 29 | 0 |
| orderfree-comb | lazy-astar-hmax-tb | 10/10 | 22/24 (2MO) | 12/16 (4MO) | 41 | 0 |
| orderfree-sep | lazy-astar-blind | 10/10 | 5/24 (17MO 2TO) | 1/16 (9MO 6TO) | 16 | 0 |
| orderfree-sep | lazy-astar-hmax | 10/10 | 7/24 (9MO 8TO) | 1/16 (9MO 6TO) | 18 | 0 |
| orderfree-sep | lazy-astar-hmax-tb | 10/10 | 7/24 (11MO 6TO) | 1/16 (8MO 7TO) | 18 | 0 |

## Satisficing plan quality (cost / known optimum), classic → FA

Mean (max) of cost / optimum over the solved tasks with a known optimum (optimum from any side, model or optimal config).

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first |
|---|---|---|---|---|---|---|
| scan-comb | 1.04 (1.60, n=44) → 1.01 (1.25, n=44) | 1.04 (1.60, n=44) → 1.01 (1.25, n=44) | 1.02 (1.25, n=39) → 1.01 (1.25, n=44) | 1.03 (1.33, n=14) → 1.02 (1.25, n=16) | 1.03 (1.60, n=44) → 1.02 (1.25, n=44) | 1.06 (1.67, n=44) → 1.03 (1.50, n=44) |
| scan-sep | 1.04 (1.50, n=41) → 1.03 (1.50, n=43) | 1.04 (1.50, n=40) → 1.09 (3.40, n=44) | 1.00 (1.00, n=21) → 1.09 (3.40, n=44) | 1.00 (1.00, n=14) → 1.00 (1.00, n=15) | 1.04 (1.50, n=40) → 1.03 (1.50, n=43) | 1.00 (1.00, n=15) → 1.03 (1.50, n=43) |
| orderfree-comb | 1.04 (1.38, n=9) → 1.01 (1.22, n=44) | 1.04 (1.38, n=9) → 1.01 (1.22, n=44) | 1.00 (1.00, n=9) → 1.01 (1.22, n=44) | 1.00 (1.00, n=9) → 1.01 (1.10, n=18) | 1.04 (1.38, n=9) → 1.02 (1.25, n=44) | 1.01 (1.12, n=9) → 1.01 (1.12, n=44) |
| orderfree-sep | 1.02 (1.12, n=8) → 1.02 (1.24, n=38) | 1.02 (1.12, n=8) → 1.01 (1.22, n=38) | 1.00 (1.00, n=8) → 1.01 (1.22, n=38) | 1.00 (1.00, n=8) → 1.00 (1.00, n=15) | 1.02 (1.12, n=8) → 1.02 (1.50, n=39) | 1.02 (1.12, n=8) → 1.03 (1.50, n=38) |

## Models compared under FA

Per config, on the large problems (l1 + other). Coverage is solved / problems run for that model (`–` = not run). `common` counts the large tasks solved by every model that ran the config; the time columns are geometric-mean search times over that common set.

| config | scan-comb cov | scan-sep cov | orderfree-comb cov | orderfree-sep cov | common | scan-comb time | scan-sep time | orderfree-comb time | orderfree-sep time |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | 40/40 | 38/40 | 40/40 | 31/40 | 30 | 0.28s | 0.76s | 0.18s | 1.24s |
| gbfs-add | 40/40 | 36/40 | 40/40 | 32/40 | 29 | 0.24s | 0.74s | 0.16s | 0.98s |
| gbfs-cea | 40/40 | 36/40 | 40/40 | 30/40 | 29 | 0.59s | 1.06s | 0.30s | 1.32s |
| gbfs-cg | 6/40 | 5/40 | 8/40 | 5/40 | 5 | 1.74s | 2.20s | 0.72s | 3.44s |
| wastar3-ff | 40/40 | 36/40 | 40/40 | 34/40 | 30 | 0.28s | 0.79s | 0.18s | 1.25s |
| lama-first | 39/40 | 36/40 | 40/40 | 30/40 | 30 | 0.43s | 1.11s | 0.22s | 1.49s |
| lazy-astar-blind | 8/40 | 5/40 | 8/40 | 6/40 | 5 | 1.55s | 2.72s | 0.61s | 4.40s |
| lazy-astar-hmax | 19/40 | 5/40 | 20/40 | 8/40 | 5 | 0.41s | 1.76s | 0.14s | 2.06s |
| lazy-astar-hmax-tb | 34/40 | 7/40 | 34/40 | 8/40 | 7 | 0.21s | 3.29s | 0.08s | 3.73s |

Search time relative to scan-comb under FA (pairwise: geometric mean of time / scan-comb time over the large tasks both solved; >1 = slower than scan-comb).

| config | scan-sep | orderfree-comb | orderfree-sep |
|---|---|---|---|
| gbfs-ff | 3.06x (n=38) | 0.66x (n=40) | 4.46x (n=31) |
| gbfs-add | 3.50x (n=36) | 0.67x (n=40) | 4.50x (n=32) |
| gbfs-cea | 2.01x (n=36) | 0.50x (n=40) | 2.28x (n=30) |
| gbfs-cg | 1.27x (n=5) | 0.47x (n=6) | 1.98x (n=5) |
| wastar3-ff | 2.88x (n=36) | 0.64x (n=40) | 5.95x (n=34) |
| lama-first | 2.66x (n=36) | 0.51x (n=39) | 3.48x (n=30) |
| lazy-astar-blind | 1.75x (n=5) | 0.59x (n=8) | 3.31x (n=6) |
| lazy-astar-hmax | 4.28x (n=5) | 0.75x (n=19) | 17.94x (n=8) |
| lazy-astar-hmax-tb | 15.53x (n=7) | 0.67x (n=34) | 28.73x (n=8) |
