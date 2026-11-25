# Forced-action vs classic Fast Downward sweep

- FA side: **inv0+fa** (1728 runs)
- classic side: **inv0** (1392 runs)
- no same-machine classic baseline: time ratios compare different machines
- **m5pro**: host=m5pro; cpus=18; ram_gb=48; cpu=Apple M5 Pro; platform=macOS-26.5.2-arm64-arm-64bit-Mach-O; run[results_m5pro_fa.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0
- **vm**: host=vm; cpus=4; ram_gb=16; cpu=Intel(R) Xeon(R) Processor @ 2.10GHz (groups A, C and the first 41 group-B jobs, until a container restart 2026-11-25 ~00:45 UTC); Intel(R) Xeon(R) Processor @ 2.30GHz (remaining group-B jobs); platform=Linux-6.18.44-fc-v819-x86_64-with-glibc2.39, then Linux-6.18.44-fc-v880-x86_64-with-glibc2.39; run[results_vm.csv]=jobs=4 timeout=300s mem=3G mem_limit=rlimit (FD driver) fd=upstream fast-downward release-24.06.1 (downward@1eef26b) classic configs only

## No-plan problems and disagreements

Problems some search exhausted (no plan), excluded from coverage: L11 t115 [FA/orderfree-comb, FA/scan-comb, classic/scan-comb], L11 t168 [FA/orderfree-comb, FA/scan-comb, classic/scan-comb], testing_level_2 [FA/orderfree-comb, FA/orderfree-sep, FA/scan-comb, FA/scan-sep, classic/orderfree-comb, classic/scan-comb, classic/scan-sep], testing_level_3 [FA/orderfree-comb, FA/orderfree-sep, FA/scan-comb, FA/scan-sep, classic/orderfree-comb, classic/scan-comb, classic/scan-sep]

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
| wastar3-ff | 10/10 → 10/10 | 24/24 → 24/24 | 14/16 (2TO) → 16/16 |
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
| lazy-astar-hmax | – → 10/10 | – → 15/24 (5MO 4TO) | – → 5/16 (9MO 2TO) |
| lazy-astar-hmax-tb | – → 10/10 | – → 22/24 (2MO) | – → 12/16 (4MO) |

### orderfree-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 8/10 (2TO) → 10/10 | 0/6 (6TO) → 17/17 | – → 1/1 |
| eager-gbfs-ff | 8/10 (2TO) → – | – → – | – → – |
| gbfs-add | 8/10 (2TO) → 10/10 | – → 17/17 | – → 1/1 |
| gbfs-cea | 8/10 (2TO) → 10/10 | – → 17/17 | – → 1/1 |
| gbfs-cg | 8/10 (2TO) → 10/10 | – → 4/17 (13MO) | – → 1/1 |
| wastar3-ff | 8/10 (2TO) → 10/10 | – → 17/17 | – → 1/1 |
| lama-first | 8/10 (2TO) → 10/10 | – → 17/17 | – → 1/1 |
| astar-blind | 8/10 (2MO) → – | – → – | – → – |
| astar-hmax | 8/10 (2TO) → – | 0/6 (6TO) → – | – → – |
| astar-lmcp | 0/10 (10unsupported) → – | – → – | – → – |
| astar-ms | 0/10 (10unsupported) → – | – → – | – → – |
| lazy-astar-blind | – → 10/10 | – → 5/17 (11MO 1TO) | – → 1/1 |
| lazy-astar-hmax | – → 10/10 | – → 7/17 (6MO 4TO) | – → 1/1 |
| lazy-astar-hmax-tb | – → 10/10 | – → 7/17 (9MO 1TO) | – → 1/1 |

## Search effort on tasks solved by both (same config)

Geometric means over the tasks the config solved on both sides. Times: classic and FA come from different machines (not comparable in absolute terms). Classic expansions include every physics step; FA expansions are agent decision states only, FA evaluated includes the forced intermediate states.


**scan-comb**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 10 | 0.05s | 0.00s | 18x | 444 | 16 | 446 | 680 |
| gbfs-ff | large | 38 | 19s | 0.30s | 64x | 5358 | 32 | 5360 | 7020 |
| gbfs-add | small | 10 | 0.06s | 0.00s | 20x | 444 | 16 | 446 | 680 |
| gbfs-add | large | 40 | 23s | 0.35s | 65x | 6501 | 38 | 6503 | 8309 |
| gbfs-cea | small | 10 | 0.22s | 0.00s | 52x | 635 | 16 | 637 | 678 |
| gbfs-cea | large | 30 | 124s | 0.60s | 205x | 4637 | 25 | 4638 | 5845 |
| gbfs-cg | small | 10 | 0.20s | 0.01s | 19x | 3625 | 67 | 3628 | 3848 |
| gbfs-cg | large | 4 | 121s | 1.12s | 108x | 23k | 53 | 23k | 31k |
| wastar3-ff | small | 10 | 0.05s | 0.00s | 17x | 444 | 16 | 446 | 708 |
| wastar3-ff | large | 38 | 20s | 0.32s | 63x | 5524 | 33 | 5525 | 7173 |
| lama-first | small | 10 | 0.06s | 0.00s | 21x | 745 | 18 | 747 | 821 |
| lama-first | large | 36 | 12s | 0.45s | 26x | 5750 | 44 | 5751 | 13k |

**scan-sep**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 10 | 0.08s | 0.00s | 24x | 906 | 15 | 908 | 1288 |
| gbfs-ff | large | 32 | 86s | 0.76s | 113x | 27k | 28 | 27k | 35k |
| gbfs-add | small | 10 | 0.07s | 0.00s | 21x | 906 | 15 | 908 | 1288 |
| gbfs-add | large | 31 | 80s | 0.73s | 110x | 26k | 27 | 26k | 34k |
| gbfs-cea | small | 10 | 0.33s | 0.01s | 56x | 1172 | 15 | 1174 | 1274 |
| gbfs-cea | large | 11 | 160s | 0.43s | 372x | 10k | 12 | 10k | 14k |
| gbfs-cg | small | 10 | 0.12s | 0.01s | 15x | 3479 | 44 | 3481 | 4279 |
| gbfs-cg | large | 4 | 46s | 1.08s | 43x | 46k | 41 | 46k | 51k |
| wastar3-ff | small | 10 | 0.08s | 0.00s | 23x | 906 | 16 | 908 | 1336 |
| wastar3-ff | large | 31 | 84s | 0.72s | 116x | 26k | 27 | 26k | 34k |
| lama-first | small | 10 | 0.18s | 0.00s | 48x | 2683 | 19 | 2685 | 1617 |
| lama-first | large | 5 | 31s | 0.18s | 168x | 16k | 7 | 16k | 8776 |

**orderfree-comb**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 9 | 0.02s | 0.00s | 10x | 241 | 16 | 244 | 125 |
| gbfs-add | small | 9 | 0.02s | 0.00s | 10x | 241 | 16 | 244 | 125 |
| gbfs-cea | small | 9 | 0.03s | 0.00s | 14x | 259 | 16 | 262 | 124 |
| gbfs-cg | small | 9 | 0.05s | 0.00s | 12x | 1312 | 58 | 1318 | 489 |
| wastar3-ff | small | 9 | 0.02s | 0.00s | 9x | 241 | 16 | 244 | 129 |
| lama-first | small | 9 | 0.01s | 0.00s | 8x | 284 | 18 | 286 | 145 |

**orderfree-sep**

| config | set | tasks | classic time | FA time | speed-up | classic expanded | FA expanded | classic evaluated | FA evaluated |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | small | 8 | 0.01s | 0.00s | 6x | 282 | 16 | 284 | 291 |
| gbfs-add | small | 8 | 0.01s | 0.00s | 6x | 282 | 16 | 283 | 291 |
| gbfs-cea | small | 8 | 0.03s | 0.00s | 11x | 303 | 16 | 304 | 290 |
| gbfs-cg | small | 8 | 0.02s | 0.00s | 5x | 1000 | 44 | 1002 | 887 |
| wastar3-ff | small | 8 | 0.01s | 0.00s | 6x | 282 | 17 | 284 | 302 |
| lama-first | small | 8 | 0.02s | 0.00s | 10x | 498 | 20 | 500 | 355 |

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
| orderfree-sep | lazy-astar-blind | 10/10 | 5/17 (11MO 1TO) | 1/1 | 16 | 0 |
| orderfree-sep | lazy-astar-hmax | 10/10 | 7/17 (6MO 4TO) | 1/1 | 18 | 0 |
| orderfree-sep | lazy-astar-hmax-tb | 10/10 | 7/17 (9MO 1TO) | 1/1 | 18 | 0 |

## Satisficing plan quality (cost / known optimum), classic → FA

Mean (max) of cost / optimum over the solved tasks with a known optimum (optimum from any side, model or optimal config).

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first |
|---|---|---|---|---|---|---|
| scan-comb | 1.04 (1.60, n=44) → 1.01 (1.25, n=44) | 1.04 (1.60, n=44) → 1.01 (1.25, n=44) | 1.02 (1.25, n=39) → 1.01 (1.25, n=44) | 1.03 (1.33, n=14) → 1.02 (1.25, n=16) | 1.03 (1.60, n=44) → 1.02 (1.25, n=44) | 1.06 (1.67, n=44) → 1.03 (1.50, n=44) |
| scan-sep | 1.04 (1.50, n=41) → 1.03 (1.50, n=43) | 1.04 (1.50, n=40) → 1.09 (3.40, n=44) | 1.00 (1.00, n=21) → 1.09 (3.40, n=44) | 1.00 (1.00, n=14) → 1.00 (1.00, n=15) | 1.04 (1.50, n=40) → 1.03 (1.50, n=43) | 1.00 (1.00, n=15) → 1.03 (1.50, n=43) |
| orderfree-comb | 1.04 (1.38, n=9) → 1.01 (1.22, n=44) | 1.04 (1.38, n=9) → 1.01 (1.22, n=44) | 1.00 (1.00, n=9) → 1.01 (1.22, n=44) | 1.00 (1.00, n=9) → 1.01 (1.10, n=18) | 1.04 (1.38, n=9) → 1.02 (1.25, n=44) | 1.01 (1.12, n=9) → 1.01 (1.12, n=44) |
| orderfree-sep | 1.02 (1.12, n=8) → 1.01 (1.22, n=27) | 1.02 (1.12, n=8) → 1.01 (1.22, n=27) | 1.00 (1.00, n=8) → 1.01 (1.22, n=27) | 1.00 (1.00, n=8) → 1.00 (1.00, n=15) | 1.02 (1.12, n=8) → 1.01 (1.22, n=27) | 1.02 (1.12, n=8) → 1.02 (1.50, n=27) |

## Models compared under FA

Per config, on the large problems (l1 + other). Coverage is solved / problems run for that model (`–` = not run). `common` counts the large tasks solved by every model that ran the config; the time columns are geometric-mean search times over that common set.

| config | scan-comb cov | scan-sep cov | orderfree-comb cov | orderfree-sep cov | common | scan-comb time | scan-sep time | orderfree-comb time | orderfree-sep time |
|---|---|---|---|---|---|---|---|---|---|
| gbfs-ff | 40/40 | 38/40 | 40/40 | 18/18 | 18 | 0.21s | 0.50s | 0.14s | 0.88s |
| gbfs-add | 40/40 | 36/40 | 40/40 | 18/18 | 18 | 0.20s | 0.50s | 0.14s | 0.84s |
| gbfs-cea | 40/40 | 36/40 | 40/40 | 18/18 | 18 | 0.47s | 0.73s | 0.26s | 1.05s |
| gbfs-cg | 6/40 | 5/40 | 8/40 | 5/18 | 5 | 1.74s | 2.20s | 0.72s | 3.44s |
| wastar3-ff | 40/40 | 36/40 | 40/40 | 18/18 | 18 | 0.22s | 0.50s | 0.14s | 0.86s |
| lama-first | 39/40 | 36/40 | 40/40 | 18/18 | 18 | 0.31s | 0.69s | 0.16s | 1.11s |
| lazy-astar-blind | 8/40 | 5/40 | 8/40 | 6/18 | 5 | 1.55s | 2.72s | 0.61s | 4.40s |
| lazy-astar-hmax | 19/40 | 5/40 | 20/40 | 8/18 | 5 | 0.41s | 1.76s | 0.14s | 2.06s |
| lazy-astar-hmax-tb | 34/40 | 7/40 | 34/40 | 8/18 | 7 | 0.21s | 3.29s | 0.08s | 3.73s |

Search time relative to scan-comb under FA (pairwise: geometric mean of time / scan-comb time over the large tasks both solved; >1 = slower than scan-comb).

| config | scan-sep | orderfree-comb | orderfree-sep |
|---|---|---|---|
| gbfs-ff | 3.06x (n=38) | 0.66x (n=40) | 4.27x (n=18) |
| gbfs-add | 3.50x (n=36) | 0.67x (n=40) | 4.17x (n=18) |
| gbfs-cea | 2.01x (n=36) | 0.50x (n=40) | 2.23x (n=18) |
| gbfs-cg | 1.27x (n=5) | 0.47x (n=6) | 1.98x (n=5) |
| wastar3-ff | 2.88x (n=36) | 0.64x (n=40) | 4.02x (n=18) |
| lama-first | 2.66x (n=36) | 0.51x (n=39) | 3.57x (n=18) |
| lazy-astar-blind | 1.75x (n=5) | 0.59x (n=8) | 3.31x (n=6) |
| lazy-astar-hmax | 4.28x (n=5) | 0.75x (n=19) | 17.94x (n=8) |
| lazy-astar-hmax-tb | 15.53x (n=7) | 0.67x (n=34) | 28.73x (n=8) |
