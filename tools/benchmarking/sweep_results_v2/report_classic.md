# Fast Downward settings sweep

Variant **inv0** (translator options; +fa = forced-action fork). Other variants in the data: none (pick with --variant=NAME).

1392 runs from host(s) vm; models: scan-comb, scan-sep, orderfree-comb, orderfree-sep.

- **vm**: host=vm; cpus=4; ram_gb=16; cpu=Intel(R) Xeon(R) Processor @ 2.10GHz (all jobs; the container restarted three times, 2026-11-25 ~16:30 and ~19:00 UTC and 2026-11-26 ~04:25 UTC, and the run was resumed on the same CPU type and kernel each time; jobs cut off by a restart were rerun in full); platform=Linux-6.18.44-fc-v880-x86_64-with-glibc2.39; run[results_vm.csv]=jobs=4 timeout=300s mem=3G mem_limit=rlimit (FD driver) fd=downward@1eef26b FD_STATE_DUMP=0 domains=a1a50ba

Problems with no plan (search space exhausted; [models that proved it]), excluded from coverage for all models: L11 t115 [scan-comb], L11 t168 [scan-comb], testing_level_2 [scan-comb,scan-sep,orderfree-comb], testing_level_3 [scan-comb,scan-sep,orderfree-comb]

## Coverage (solved / solvable problems run)


### small (hand-made, 5x5..40x11)

| model | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp | astar-ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 9/10 (1TO) |
| scan-sep | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 8/10 (2TO) |
| orderfree-comb | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 0/10 (10unsupported) | 0/10 (10unsupported) |
| orderfree-sep | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2MO) | 8/10 (2TO) | 0/10 (10unsupported) | 0/10 (10unsupported) |

### bd_level_01 20x38 (h1+h2)

| model | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp | astar-ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 24/24 | 24/24 | 24/24 | 20/24 (4TO) | 3/24 (21TO) | 24/24 | 24/24 | 7/24 (15MO 2TO) | 21/24 (3TO) | 7/24 (14MO 3TO) |  |
| scan-sep | 24/24 | 16/24 (8TO) | 24/24 | 17/24 (7TO) | 3/24 (21TO) | 24/24 | 22/24 (2TO) | 6/24 (18MO) | 4/24 (20TO) | 7/24 (17MO) |  |
| orderfree-comb | 0/6 (6TO) |  |  |  |  |  |  |  | 0/6 (6TO) |  |  |
| orderfree-sep | 0/6 (6TO) |  |  |  |  |  |  |  | 0/6 (6TO) |  |  |

### bd_levels 02..14

| model | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp | astar-ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 16/16 | 16/16 | 16/16 | 12/16 (4TO) | 1/16 (6MO 9TO) | 16/16 | 14/16 (2TO) | 1/16 (15MO) | 11/16 (5TO) | 1/16 (15MO) |  |
| scan-sep | 11/16 (5TO) | 11/16 (5TO) | 11/16 (5TO) | 8/16 (8TO) | 1/16 (15TO) | 12/16 (4TO) | 11/16 (5TO) | 1/16 (15MO) | 1/16 (15TO) | 1/16 (15MO) |  |
| orderfree-comb |  |  |  |  |  |  |  |  |  |  |  |
| orderfree-sep |  |  |  |  |  |  |  |  |  |  |  |

## Search effort on tasks every listed config solved (per model)

Geometric mean of search time and expansions over the tasks solved by all configs in the row group; plan quality is the mean of cost / best known optimum.


**scan-comb / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.04s | 453 | 16 | 1.00 (n=10, max 1.00) |
| eager-gbfs-ff | 0.07s | 704 | 16 | 1.00 (n=10, max 1.00) |
| gbfs-add | 0.04s | 453 | 16 | 1.00 (n=10, max 1.00) |
| gbfs-cea | 0.18s | 638 | 23 | 1.02 (n=10, max 1.25) |
| gbfs-cg | 0.17s | 3609 | 230 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.05s | 453 | 16 | 1.00 (n=10, max 1.00) |
| lama-first | 0.04s | 738 | 15 | 1.16 (n=10, max 1.67) |

**scan-comb / satisficing / l1** (20 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 14s | 2867 | 79 | 1.04 (n=20, max 1.50) |
| eager-gbfs-ff | 18s | 3740 | 79 | 1.01 (n=20, max 1.25) |
| gbfs-add | 13s | 2869 | 79 | 1.04 (n=20, max 1.50) |
| gbfs-cea | 147s | 3065 | 149 | 1.01 (n=20, max 1.25) |
| wastar3-ff | 14s | 2890 | 79 | 1.04 (n=20, max 1.50) |
| lama-first | 7.67s | 2815 | 62 | 1.03 (n=20, max 1.50) |

**scan-comb / satisficing / other** (12 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 11s | 3329 | 89 | 1.06 (n=11, max 1.60) |
| eager-gbfs-ff | 16s | 4595 | 89 | 1.06 (n=11, max 1.44) |
| gbfs-add | 11s | 3288 | 89 | 1.06 (n=11, max 1.60) |
| gbfs-cea | 103s | 3520 | 158 | 1.06 (n=11, max 1.44) |
| wastar3-ff | 11s | 3350 | 89 | 1.06 (n=11, max 1.60) |
| lama-first | 7.21s | 3544 | 69 | 1.06 (n=11, max 1.44) |

**scan-comb / optimal / small** (9 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 0.02s | 3926 | 18 | 1.00 (n=9, max 1.00) |
| astar-hmax | 0.03s | 682 | 15 | 1.00 (n=9, max 1.00) |
| astar-lmcp | 0.01s | 2883 | 18 | 1.00 (n=9, max 1.00) |
| astar-ms | 0.02s | 3745 | 69 | 1.00 (n=9, max 1.00) |

**scan-comb / optimal / l1** (21 common tasks; left out for low coverage: astar-blind, astar-lmcp)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-hmax | 13s | 4878 | 168 | 1.00 (n=21, max 1.00) |

**scan-comb / optimal / other** (11 common tasks; left out for low coverage: astar-blind, astar-lmcp)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-hmax | 13s | 6844 | 72 | 1.00 (n=11, max 1.00) |

**scan-sep / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.04s | 548 | 19 | 1.01 (n=10, max 1.12) |
| eager-gbfs-ff | 0.10s | 1134 | 19 | 1.00 (n=10, max 1.00) |
| gbfs-add | 0.05s | 548 | 19 | 1.01 (n=10, max 1.12) |
| gbfs-cea | 0.21s | 766 | 29 | 1.00 (n=10, max 1.00) |
| gbfs-cg | 0.10s | 2744 | 557 | 1.04 (n=10, max 1.14) |
| wastar3-ff | 0.05s | 548 | 19 | 1.01 (n=10, max 1.12) |
| lama-first | 0.07s | 911 | 18 | 1.17 (n=10, max 1.67) |

**scan-sep / satisficing / l1** (15 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 22s | 6217 | 69 | 1.05 (n=15, max 1.50) |
| eager-gbfs-ff | 54s | 15k | 88 | 1.00 (n=15, max 1.00) |
| gbfs-add | 21s | 6212 | 69 | 1.05 (n=15, max 1.50) |
| gbfs-cea | 138s | 6339 | 134 | 1.00 (n=15, max 1.00) |
| wastar3-ff | 22s | 6217 | 69 | 1.05 (n=15, max 1.50) |
| lama-first | 17s | 7243 | 57 | 1.09 (n=15, max 1.50) |

**scan-sep / satisficing / other** (8 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 16s | 6116 | 71 | 1.05 (n=8, max 1.44) |
| eager-gbfs-ff | 39s | 14k | 92 | 1.00 (n=8, max 1.00) |
| gbfs-add | 16s | 6105 | 71 | 1.05 (n=8, max 1.44) |
| gbfs-cea | 92s | 6410 | 137 | 1.05 (n=8, max 1.44) |
| wastar3-ff | 16s | 6116 | 71 | 1.05 (n=8, max 1.44) |
| lama-first | 12s | 6790 | 60 | 1.05 (n=8, max 1.44) |

**scan-sep / optimal / small** (8 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 0.02s | 4494 | 17 | 1.00 (n=8, max 1.00) |
| astar-hmax | 0.05s | 1668 | 17 | 1.00 (n=8, max 1.00) |
| astar-lmcp | 0.02s | 4356 | 17 | 1.00 (n=8, max 1.00) |
| astar-ms | 0.02s | 4356 | 90 | 1.00 (n=8, max 1.00) |

**scan-sep / optimal / l1** (4 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 5.42s | 116k | 286 | 1.00 (n=4, max 1.00) |
| astar-hmax | 45s | 23k | 105 | 1.00 (n=4, max 1.00) |
| astar-lmcp | 3.04s | 52k | 200 | 1.00 (n=4, max 1.00) |

**scan-sep / optimal / other** (1 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 4.74s | 115k | 120 | 1.00 (n=1, max 1.00) |
| astar-hmax | 39s | 24k | 61 | 1.00 (n=1, max 1.00) |
| astar-lmcp | 2.33s | 53k | 71 | 1.00 (n=1, max 1.00) |

**orderfree-comb / satisficing / small** (9 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.01s | 144 | 58 | 1.04 (n=9, max 1.38) |
| eager-gbfs-ff | 0.03s | 234 | 55 | 1.00 (n=9, max 1.00) |
| gbfs-add | 0.02s | 144 | 58 | 1.04 (n=9, max 1.38) |
| gbfs-cea | 0.04s | 161 | 61 | 1.03 (n=9, max 1.25) |
| gbfs-cg | 0.04s | 961 | 224 | 1.00 (n=9, max 1.00) |
| wastar3-ff | 0.01s | 144 | 58 | 1.04 (n=9, max 1.38) |
| lama-first | 0.01s | 183 | 22 | 1.01 (n=9, max 1.12) |

**orderfree-comb / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-ff)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

**orderfree-comb / optimal / small** (9 common tasks; left out for low coverage: astar-lmcp, astar-ms)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 0.02s | 1110 | 161 | 1.00 (n=9, max 1.00) |
| astar-hmax | 0.02s | 269 | 52 | 1.00 (n=9, max 1.00) |

**orderfree-comb / optimal / l1** (24 common tasks; left out for low coverage: astar-hmax)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

**orderfree-sep / satisficing / small** (8 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.01s | 108 | 16 | 1.02 (n=8, max 1.12) |
| eager-gbfs-ff | 0.02s | 201 | 16 | 1.00 (n=8, max 1.00) |
| gbfs-add | 0.01s | 108 | 16 | 1.02 (n=8, max 1.12) |
| gbfs-cea | 0.02s | 117 | 22 | 1.02 (n=8, max 1.12) |
| gbfs-cg | 0.01s | 423 | 138 | 1.00 (n=8, max 1.00) |
| wastar3-ff | 0.01s | 108 | 16 | 1.02 (n=8, max 1.12) |
| lama-first | 0.02s | 199 | 15 | 1.02 (n=8, max 1.12) |

**orderfree-sep / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-ff)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

**orderfree-sep / optimal / small** (8 common tasks; left out for low coverage: astar-lmcp, astar-ms)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 0.01s | 800 | 14 | 1.00 (n=8, max 1.00) |
| astar-hmax | 0.01s | 332 | 15 | 1.00 (n=8, max 1.00) |

**orderfree-sep / optimal / l1** (24 common tasks; left out for low coverage: astar-hmax)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

## Optimal cost agreement

42 problems solved optimally; 18 of them by more than one model. All optimal costs agree across configs and models.

## Translation (per model and problem set)

| model | set | problems | translate s (median / max) | operators (median / max) | translate failures |
|---|---|---|---|---|---|
| scan-comb | small | 12 | 0.9 / 4.3 | 386 / 2261 | 0 |
| scan-comb | l1 | 24 | 27.8 / 37.6 | 18k / 18k | 0 |
| scan-comb | other | 18 | 19.4 / 28.6 | 14k / 19k | 0 |
| scan-sep | small | 12 | 0.7 / 4.4 | 2247 / 13k | 0 |
| scan-sep | l1 | 24 | 15.0 / 16.3 | 34k / 34k | 0 |
| scan-sep | other | 18 | 14.1 / 17.3 | 32k / 36k | 0 |
| orderfree-comb | small | 12 | 1.1 / 4.6 | 432 / 3156 | 0 |
| orderfree-comb | l1 | 6 | 23.6 / 24.3 | 20k / 20k | 0 |
| orderfree-sep | small | 12 | 0.7 / 8.0 | 1718 / 15k | 0 |
| orderfree-sep | l1 | 6 | 17.2 / 18.5 | 29k / 29k | 0 |

## Per-problem detail (search time, cost)


### scan-comb / l1

| problem | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp |
|---|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 5.89s [3] | 6.03s [3] | 5.55s [3] | 60s [3] | 61s [3] | 5.59s [3] | 3.20s [3] | 1.28s [3] | 3.19s [3] | 0.74s [3] |
| L01 s005 t004 h1 | 9.78s [7] | 9.28s [7] | 8.26s [7] | 93s [7] | TO | 9.04s [7] | 4.72s [8] | 10s [7] | 5.06s [7] | 5.43s [7] |
| L01 s007 t004 h1 | 7.47s [8] | 12s [8] | 8.58s [8] | 117s [8] | TO | 7.92s [8] | 4.71s [8] | 61s [8] | 6.46s [8] | 34s [8] |
| L01 s002 t013 h1 | 28s [55] | 36s [55] | 25s [57] | 260s [55] | TO | 30s [55] | 16s [55] | MO | 20s [55] | MO |
| L01 s005 t014 h1 | 29s [55] | 38s [55] | 27s [55] | 247s [55] | TO | 30s [55] | 16s [56] | MO | 24s [55] | MO |
| L01 s003 t016 h1 | 19s [33] | 21s [33] | 19s [33] | 170s [33] | TO | 18s [33] | 10s [33] | MO | 13s [33] | MO |
| L01 s007 t005 h1 | 6.78s [4] | 15s [4] | 6.29s [4] | 72s [4] | 86s [4] | 7.49s [4] | 4.42s [6] | 5.36s [4] | 8.93s [4] | 2.68s [4] |
| L01 s004 t005 h1 | 7.80s [6] | 13s [5] | 10s [6] | 117s [5] | 49s [4] | 9.16s [6] | 4.40s [4] | 2.20s [4] | 4.89s [4] | 1.27s [4] |
| L01 s009 t017 h1 | 22s [43] | 28s [43] | 24s [43] | 192s [43] | TO | 25s [43] | 13s [43] | MO | 21s [43] | MO |
| L01 s003 t017 h1 | 22s [34] | 23s [34] | 19s [34] | 195s [34] | TO | 20s [34] | 11s [34] | MO | 14s [34] | MO |
| L01 s018 t008 h2 | 8.43s [11] | 16s [9] | 9.21s [11] | 111s [9] | TO | 8.50s [11] | 4.94s [9] | 62s [9] | 7.70s [9] | 28s [9] |
| L01 s013 t018 h2 | 13s [19] | 16s [19] | 12s [19] | 128s [19] | TO | 15s [19] | 8.78s [19] | TO | 9.23s [19] | MO |
| L01 s008 t011 h1 | 31s [41] | 42s [41] | 29s [41] | 283s [41] | TO | 35s [41] | 14s [41] | TO | 101s [41] | MO |
| L01 s001 t016 h1 | 37s [83] | 67s [83] | 39s [83] | TO | TO | 42s [83] | 23s [83] | MO | 39s [83] | MO |
| L01 s012 t010 h2 | 9.15s [10] | 9.76s [10] | 9.02s [10] | 112s [10] | TO | 9.00s [10] | 5.11s [10] | 197s [10] | 5.54s [10] | 73s [10] |
| L01 s010 t008 h2 | 20s [28] | 30s [28] | 19s [28] | 228s [28] | TO | 20s [28] | 9.63s [29] | MO | 19s [28] | MO |
| L01 s018 t002 h2 | 31s [59] | 57s [58] | 35s [59] | TO | TO | 34s [59] | 16s [58] | MO | TO | TO |
| L01 s016 t002 h2 | 36s [70] | 49s [70] | 37s [72] | TO | TO | 34s [70] | 20s [70] | MO | TO | TO |
| L01 s017 t013 h2 | 11s [16] | 12s [16] | 11s [16] | 123s [16] | TO | 10s [16] | 6.69s [16] | MO | 6.21s [16] | MO |
| L01 s016 t009 h2 | 27s [42] | 33s [42] | 26s [42] | 261s [42] | TO | 26s [42] | 11s [42] | MO | 282s [42] | MO |
| L01 s011 t010 h2 | 9.91s [14] | 16s [14] | 9.66s [14] | 139s [14] | TO | 11s [14] | 6.20s [14] | MO | 7.88s [14] | MO |
| L01 s013 t014 h2 | 9.46s [14] | 14s [14] | 9.27s [14] | 105s [14] | TO | 10s [14] | 5.72s [14] | MO | 8.37s [14] | MO |
| L01 s014 t011 h2 | 40s [58] | 50s [58] | 32s [58] | TO | TO | 38s [58] | 15s [58] | MO | TO | MO |
| L01 s012 t001 h2 | 21s [34] | 22s [34] | 19s [34] | 187s [34] | TO | 20s [34] | 12s [34] | MO | 12s [34] | TO |

### scan-comb / other

| problem | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp |
|---|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 7.62s [4] | 10s [4] | 7.22s [4] | 57s [4] | 99s [4] | 7.01s [4] | 3.36s [4] | 3.19s [4] | 5.81s [4] | 1.46s [4] |
| L03 t018 | 13s [40] | 11s [36] | 11s [40] | 173s [36] | TO | 13s [40] | 6.08s [36] | MO | 60s [25] | MO |
| L02 t005 | 15s [30] | 32s [29] | 14s [30] | 223s [29] | TO | 14s [30] | 8.53s [30] | MO | TO | MO |
| L07 t001 | 8.53s [33] | 10s [33] | 8.30s [33] | 86s [33] | MO | 8.82s [33] | 6.71s [33] | MO | 12s [33] | MO |
| L06 t005 | 4.15s [24] | 7.03s [24] | 3.96s [24] | 46s [24] | TO | 3.79s [24] | 2.44s [24] | MO | 3.29s [24] | MO |
| L06 t002 | 3.96s [25] | 6.69s [25] | 3.94s [25] | 34s [25] | TO | 3.94s [25] | 2.32s [25] | MO | 3.68s [25] | MO |
| L07 t008 | 10s [41] | 15s [41] | 11s [41] | 92s [41] | MO | 11s [41] | 6.98s [41] | MO | 9.84s [41] | MO |
| L08 t001 | 19s [21] | 19s [21] | 18s [21] | 143s [21] | MO | 18s [21] | 16s [25] | MO | 45s [20] | MO |
| L08 t003 | 17s [25] | 36s [25] | 16s [25] | 227s [25] | MO | 19s [25] | 11s [25] | MO | 22s [25] | MO |
| L09 t005 | 16s [24] | 28s [24] | 16s [24] | 145s [24] | MO | 16s [24] | 10s [24] | MO | 16s [24] | MO |
| L11 t115 | incomplete | incomplete | incomplete | incomplete | TO | incomplete | incomplete | MO | incomplete | incomplete |
| L09 t003 | 15s [23] | 28s [23] | 15s [23] | 119s [23] | MO | 14s [23] | 9.21s [23] | MO | 16s [23] | MO |
| L03 t002 | 198s [44] | 193s [37] | 17s [40] | TO | TO | 283s [35] | TO | MO | TO | MO |
| L11 t168 | incomplete | incomplete | incomplete | incomplete | TO | incomplete | incomplete | MO | incomplete | incomplete |
| L13 t006 | 27s [34] | 14s [38] | 26s [34] | 92s [38] | TO | 27s [34] | 26s [34] | MO | 16s [34] | MO |
| L14 t016 | 43s [112] | 33s [89] | 82s [93] | TO | TO | 93s [90] | 75s [116] | MO | TO | MO |
| L14 t006 | 26s [95] | 26s [76] | 62s [80] | TO | TO | 75s [77] | 62s [103] | MO | TO | MO |
| L13 t003 | 136s [63] | 127s [67] | 92s [70] | TO | TO | 190s [59] | TO | MO | TO | MO |

### scan-sep / l1

| problem | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp |
|---|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 12s [3] | 23s [3] | 11s [3] | 67s [3] | 28s [3] | 12s [3] | 5.86s [3] | 2.24s [3] | 14s [3] | 0.74s [3] |
| L01 s005 t004 h1 | 15s [7] | 28s [7] | 15s [7] | 87s [7] | TO | 16s [7] | 12s [8] | 14s [7] | 143s [7] | 13s [7] |
| L01 s007 t004 h1 | 17s [8] | 43s [8] | 16s [8] | 130s [8] | TO | 19s [8] | 12s [8] | 94s [8] | TO | 70s [8] |
| L01 s002 t013 h1 | 46s [57] | TO | 45s [57] | TO | TO | 50s [57] | 41s [55] | MO | TO | MO |
| L01 s005 t014 h1 | 41s [55] | TO | 41s [55] | TO | TO | 46s [55] | 30s [55] | MO | TO | MO |
| L01 s003 t016 h1 | 37s [33] | 97s [33] | 34s [33] | 262s [33] | TO | 34s [33] | 36s [33] | MO | TO | MO |
| L01 s007 t005 h1 | 13s [4] | 36s [4] | 12s [4] | 76s [4] | 119s [4] | 13s [4] | 12s [6] | 9.57s [4] | 48s [4] | 4.55s [4] |
| L01 s004 t005 h1 | 15s [6] | 32s [4] | 15s [6] | 103s [4] | 37s [4] | 16s [6] | 8.00s [4] | 2.79s [4] | 40s [4] | 1.97s [4] |
| L01 s009 t017 h1 | 37s [43] | TO | 36s [43] | 228s [43] | TO | 39s [43] | TO | MO | TO | MO |
| L01 s003 t017 h1 | 35s [34] | 96s [34] | 34s [34] | 203s [34] | TO | 36s [34] | 36s [34] | MO | TO | MO |
| L01 s018 t008 h2 | 19s [11] | 57s [9] | 19s [11] | 143s [9] | TO | 19s [11] | 14s [13] | 86s [9] | TO | 41s [9] |
| L01 s013 t018 h2 | 21s [19] | 65s [19] | 20s [19] | 152s [19] | TO | 23s [19] | 20s [19] | MO | TO | MO |
| L01 s008 t011 h1 | 49s [41] | 175s [43] | 46s [41] | TO | TO | 48s [41] | 38s [41] | MO | TO | MO |
| L01 s001 t016 h1 | 65s [83] | TO | 62s [83] | TO | TO | 67s [83] | 58s [84] | MO | TO | MO |
| L01 s012 t010 h2 | 18s [10] | 47s [10] | 17s [10] | 133s [10] | TO | 18s [10] | 19s [13] | MO | TO | 110s [10] |
| L01 s010 t008 h2 | 34s [28] | 138s [28] | 32s [28] | 220s [28] | TO | 34s [28] | 29s [28] | MO | TO | MO |
| L01 s018 t002 h2 | 58s [60] | TO | 57s [60] | TO | TO | 61s [60] | 35s [58] | MO | TO | MO |
| L01 s016 t002 h2 | 59s [72] | TO | 60s [72] | TO | TO | 61s [72] | 43s [70] | MO | TO | MO |
| L01 s017 t013 h2 | 24s [16] | 58s [16] | 22s [16] | 147s [16] | TO | 23s [16] | 15s [16] | MO | TO | MO |
| L01 s016 t009 h2 | 33s [44] | TO | 32s [44] | 261s [42] | TO | 35s [44] | 67s [43] | MO | TO | MO |
| L01 s011 t010 h2 | 25s [14] | 72s [14] | 24s [14] | 147s [14] | TO | 23s [14] | 18s [14] | MO | TO | MO |
| L01 s013 t014 h2 | 23s [14] | 58s [14] | 22s [14] | 126s [14] | TO | 22s [14] | 18s [14] | MO | TO | MO |
| L01 s014 t011 h2 | 51s [60] | TO | 49s [60] | TO | TO | 50s [60] | TO | MO | TO | MO |
| L01 s012 t001 h2 | 46s [34] | 58s [34] | 44s [34] | 224s [34] | TO | 47s [34] | 29s [34] | MO | TO | MO |

### scan-sep / other

| problem | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp |
|---|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 10s [4] | 35s [4] | 9.82s [4] | 71s [4] | 61s [4] | 9.70s [4] | 12s [4] | 4.74s [4] | 39s [4] | 2.33s [4] |
| L03 t018 | 30s [36] | 58s [25] | 29s [36] | 175s [36] | TO | 32s [36] | 16s [36] | MO | TO | MO |
| L02 t005 | 30s [30] | 119s [29] | 28s [30] | TO | TO | 30s [30] | 32s [30] | MO | TO | MO |
| L07 t001 | 19s [33] | 31s [33] | 17s [33] | 88s [33] | TO | 18s [33] | 12s [33] | MO | TO | MO |
| L06 t005 | 4.86s [24] | 12s [24] | 5.04s [24] | 35s [24] | TO | 5.03s [24] | 3.38s [24] | MO | TO | MO |
| L06 t002 | 4.27s [25] | 11s [25] | 3.98s [25] | 25s [25] | TO | 4.42s [25] | 2.91s [25] | MO | TO | MO |
| L07 t008 | 20s [41] | 39s [41] | 20s [41] | 98s [41] | TO | 19s [41] | 12s [41] | MO | TO | MO |
| L08 t001 | 90s [22] | 62s [23] | TO | TO | TO | 148s [22] | 239s [35] | MO | TO | MO |
| L08 t003 | 38s [25] | 140s [25] | 40s [25] | TO | TO | 43s [25] | 67s [25] | MO | TO | MO |
| L09 t005 | 45s [24] | 152s [24] | 45s [24] | 245s [24] | TO | 44s [24] | 32s [24] | MO | TO | MO |
| L11 t115 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L09 t003 | 42s [23] | 112s [23] | 41s [23] | 211s [23] | TO | 40s [23] | 40s [23] | MO | TO | MO |
| L03 t002 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L11 t168 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L13 t006 | TO | TO | 167s [36] | TO | TO | 225s [36] | TO | MO | TO | MO |
| L14 t016 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L14 t006 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L13 t003 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |

### orderfree-comb / l1

| problem | gbfs-ff | astar-hmax |
|---|---|---|
| L01 s009 t010 h1 | TO | TO |
| L01 s005 t004 h1 | TO | TO |
| L01 s007 t004 h1 | TO | TO |
| L01 s002 t013 h1 | TO | TO |
| L01 s005 t014 h1 | TO | TO |
| L01 s003 t016 h1 | TO | TO |

### orderfree-sep / l1

| problem | gbfs-ff | astar-hmax |
|---|---|---|
| L01 s009 t010 h1 | TO | TO |
| L01 s005 t004 h1 | TO | TO |
| L01 s007 t004 h1 | TO | TO |
| L01 s002 t013 h1 | TO | TO |
| L01 s005 t014 h1 | TO | TO |
| L01 s003 t016 h1 | TO | TO |
