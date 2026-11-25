# Fast Downward settings sweep

Variant **inv0** (translator options; +fa = forced-action fork). Other variants in the data: inv0+fa (pick with --variant=NAME).

1200 runs from host(s) m5pro; models: scan-comb, scan-sep, orderfree-comb, orderfree-sep.

- **m5pro**: host=m5pro; cpus=18; ram_gb=48; cpu=Apple M5 Pro; platform=macOS-26.5.2-arm64-arm-64bit-Mach-O; run[results_m5pro.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0 domains=a9f6ad1; run[results_m5pro_fa.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0 domains=a9f6ad1

Problems with no plan (search space exhausted; [models that proved it]), excluded from coverage for all models: L11 t115 [scan-comb], L11 t168 [scan-comb], testing_level_2 [scan-comb,scan-sep,orderfree-comb], testing_level_3 [scan-comb,scan-sep,orderfree-comb]

## Coverage (solved / solvable problems run)


### small (hand-made, 5x5..40x11)

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| scan-sep | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| orderfree-comb | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) |
| orderfree-sep | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) |

### bd_level_01 20x38 (h1+h2)

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 24/24 | 24/24 | 24/24 | 3/24 (21TO) | 24/24 | 10/24 (14TO) | 6/24 (18MO) | 13/24 (11TO) | 20/24 (4TO) |
| scan-sep | 21/24 (3TO) | 21/24 (3TO) | 7/24 (17TO) | 4/24 (20TO) | 19/24 (5TO) | 4/24 (20TO) | 4/24 (20MO) | 3/24 (21TO) | 3/24 (21TO) |
| orderfree-comb | 0/6 (6TO) |  |  |  |  |  |  |  |  |
| orderfree-sep | 0/6 (6TO) |  |  |  |  |  |  |  |  |

### bd_levels 02..14

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 14/16 (2TO) | 15/16 (1TO) | 12/16 (4TO) | 1/16 (2MO 13TO) | 14/16 (2TO) | 4/16 (12TO) | 1/16 (15MO) | 4/16 (12TO) | 11/16 (5TO) |
| scan-sep | 10/16 (6TO) | 9/16 (7TO) | 3/16 (13TO) | 1/16 (15TO) | 9/16 (7TO) | 1/16 (15TO) | 1/16 (15MO) | 1/16 (15TO) | 1/16 (15TO) |
| orderfree-comb |  |  |  |  |  |  |  |  |  |
| orderfree-sep |  |  |  |  |  |  |  |  |  |

## Search effort on tasks every listed config solved (per model)

Geometric mean of search time and expansions over the tasks solved by all configs in the row group; plan quality is the mean of cost / best known optimum.


**scan-comb / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.03s | 621 | 31 | 1.02 (n=10, max 1.25) |
| gbfs-add | 0.03s | 621 | 31 | 1.02 (n=10, max 1.25) |
| gbfs-cea | 0.07s | 636 | 39 | 1.02 (n=10, max 1.25) |
| gbfs-cg | 0.07s | 3624 | 255 | 1.04 (n=10, max 1.25) |
| wastar3-ff | 0.04s | 635 | 31 | 1.00 (n=10, max 1.00) |
| lama-first | 0.03s | 1102 | 32 | 1.31 (n=10, max 1.67) |

**scan-comb / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-cg, lama-first)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 24s | 5118 | 117 | 1.01 (n=20, max 1.22) |
| gbfs-add | 23s | 5080 | 124 | 1.01 (n=20, max 1.22) |
| gbfs-cea | 131s | 5170 | 180 | 1.01 (n=20, max 1.25) |
| wastar3-ff | 22s | 5143 | 118 | 1.01 (n=20, max 1.22) |

**scan-comb / satisficing / other** (12 common tasks; left out for low coverage: gbfs-cg, lama-first)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 21s | 5065 | 123 | 1.02 (n=11, max 1.12) |
| gbfs-add | 20s | 5036 | 120 | 1.02 (n=11, max 1.12) |
| gbfs-cea | 118s | 5023 | 185 | 1.02 (n=11, max 1.12) |
| wastar3-ff | 24s | 5783 | 130 | 1.01 (n=11, max 1.08) |

**scan-comb / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.01s | 4392 | 29 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.03s | 1261 | 29 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.02s | 724 | 30 | 1.00 (n=10, max 1.00) |

**scan-comb / optimal / l1** (13 common tasks; left out for low coverage: lazy-astar-blind)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax | 18s | 12k | 219 | 1.00 (n=13, max 1.00) |
| lazy-astar-hmax-tb | 7.75s | 4242 | 96 | 1.00 (n=13, max 1.00) |

**scan-comb / optimal / other** (11 common tasks; left out for low coverage: lazy-astar-blind, lazy-astar-hmax)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax-tb | 15s | 9571 | 146 | 1.00 (n=11, max 1.00) |

**scan-sep / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.06s | 1128 | 63 | 1.00 (n=10, max 1.00) |
| gbfs-add | 0.07s | 1128 | 64 | 1.00 (n=10, max 1.00) |
| gbfs-cea | 0.25s | 1173 | 87 | 1.00 (n=10, max 1.00) |
| gbfs-cg | 0.06s | 3464 | 404 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.07s | 1199 | 63 | 1.00 (n=10, max 1.00) |
| lama-first | 0.17s | 4486 | 75 | 1.00 (n=10, max 1.00) |

**scan-sep / satisficing / l1** (19 common tasks; left out for low coverage: gbfs-cea, gbfs-cg, lama-first)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 71s | 21k | 156 | 1.04 (n=18, max 1.50) |
| gbfs-add | 71s | 21k | 157 | 1.04 (n=18, max 1.50) |
| wastar3-ff | 73s | 21k | 159 | 1.04 (n=18, max 1.50) |

**scan-sep / satisficing / other** (9 common tasks; left out for low coverage: gbfs-cea, gbfs-cg, lama-first)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 86s | 29k | 150 | 1.05 (n=9, max 1.44) |
| gbfs-add | 88s | 29k | 149 | 1.05 (n=9, max 1.44) |
| wastar3-ff | 90s | 29k | 148 | 1.05 (n=9, max 1.44) |

**scan-sep / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.02s | 6210 | 57 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.11s | 4052 | 69 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.11s | 3957 | 72 | 1.00 (n=10, max 1.00) |

**scan-sep / optimal / l1** (3 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 3.74s | 115k | 303 | 1.00 (n=3, max 1.00) |
| lazy-astar-hmax | 34s | 26k | 127 | 1.00 (n=3, max 1.00) |
| lazy-astar-hmax-tb | 20s | 16k | 101 | 1.00 (n=3, max 1.00) |

**scan-sep / optimal / other** (1 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 6.43s | 190k | 216 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax | 90s | 57k | 135 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax-tb | 37s | 24k | 109 | 1.00 (n=1, max 1.00) |

**orderfree-comb / satisficing / small** (9 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.02s | 319 | 117 | 1.03 (n=9, max 1.25) |
| gbfs-add | 0.02s | 320 | 116 | 1.03 (n=9, max 1.25) |
| gbfs-cea | 0.02s | 259 | 115 | 1.00 (n=9, max 1.00) |
| gbfs-cg | 0.04s | 1314 | 436 | 1.00 (n=9, max 1.00) |
| wastar3-ff | 0.02s | 334 | 114 | 1.00 (n=9, max 1.00) |
| lama-first | 0.01s | 383 | 42 | 1.00 (n=9, max 1.00) |

**orderfree-comb / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-ff)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

**orderfree-comb / optimal / small** (9 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.01s | 1454 | 358 | 1.00 (n=9, max 1.00) |
| lazy-astar-hmax | 0.02s | 730 | 111 | 1.00 (n=9, max 1.00) |
| lazy-astar-hmax-tb | 0.02s | 398 | 108 | 1.00 (n=9, max 1.00) |

**orderfree-sep / satisficing / small** (8 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.01s | 345 | 29 | 1.00 (n=8, max 1.00) |
| gbfs-add | 0.01s | 353 | 29 | 1.00 (n=8, max 1.00) |
| gbfs-cea | 0.02s | 307 | 34 | 1.00 (n=8, max 1.00) |
| gbfs-cg | 0.01s | 1005 | 142 | 1.00 (n=8, max 1.00) |
| wastar3-ff | 0.01s | 395 | 28 | 1.00 (n=8, max 1.00) |
| lama-first | 0.02s | 695 | 29 | 1.00 (n=8, max 1.00) |

**orderfree-sep / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-ff)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

**orderfree-sep / optimal / small** (8 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.01s | 1894 | 27 | 1.00 (n=8, max 1.00) |
| lazy-astar-hmax | 0.02s | 1008 | 28 | 1.00 (n=8, max 1.00) |
| lazy-astar-hmax-tb | 0.02s | 706 | 29 | 1.00 (n=8, max 1.00) |

## Optimal cost agreement

41 problems solved optimally; 15 of them by more than one model. All optimal costs agree across configs and models.

## Translation (per model and problem set)

| model | set | problems | translate s (median / max) | operators (median / max) | translate failures |
|---|---|---|---|---|---|
| scan-comb | small | 12 | 0.4 / 1.2 | 449 / 2262 | 0 |
| scan-comb | l1 | 24 | 13.0 / 18.2 | 21k / 21k | 0 |
| scan-comb | other | 18 | 10.4 / 15.7 | 16k / 22k | 0 |
| scan-sep | small | 12 | 0.4 / 3.3 | 2289 / 19k | 0 |
| scan-sep | l1 | 24 | 7.1 / 7.7 | 36k / 36k | 0 |
| scan-sep | other | 18 | 8.4 / 9.6 | 39k / 40k | 0 |
| orderfree-comb | small | 12 | 0.6 / 2.0 | 494 / 3207 | 0 |
| orderfree-comb | l1 | 6 | 11.4 / 11.5 | 23k / 23k | 0 |
| orderfree-sep | small | 12 | 0.4 / 2.9 | 1806 / 15k | 0 |
| orderfree-sep | l1 | 6 | 6.9 / 7.0 | 30k / 30k | 0 |

## Per-problem detail (search time, cost)


### scan-comb / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 6.88s [3] | 7.51s [3] | 47s [3] | 64s [3] | 5.43s [3] | 2.27s [3] | 1.44s [3] | 2.37s [3] | 2.74s [3] |
| L01 s004 t005 h1 | 13s [4] | 10s [4] | 75s [5] | 53s [4] | 9.96s [4] | 3.60s [4] | 1.86s [4] | 3.72s [4] | 4.17s [4] |
| L01 s007 t005 h1 | 10s [4] | 11s [4] | 57s [4] | 263s [4] | 8.19s [4] | 3.66s [4] | 6.01s [4] | 10s [4] | 8.98s [4] |
| L01 s005 t004 h1 | 12s [7] | 12s [7] | 72s [7] | TO | 10.00s [7] | 5.35s [9] | 11s [7] | 9.75s [7] | 4.37s [7] |
| L01 s007 t004 h1 | 11s [8] | 12s [8] | 83s [8] | TO | 9.51s [8] | 5.57s [9] | 70s [8] | 12s [8] | 6.19s [8] |
| L01 s018 t008 h2 | 18s [11] | 14s [11] | 66s [9] | TO | 16s [11] | 13s [13] | 64s [9] | 18s [9] | 10s [9] |
| L01 s003 t016 h1 | 30s [33] | 27s [33] | 136s [33] | TO | 27s [33] | TO | MO | 99s [33] | 22s [33] |
| L01 s013 t018 h2 | 14s [19] | 14s [19] | 98s [19] | TO | 17s [19] | 13s [21] | MO | TO | 11s [19] |
| L01 s003 t017 h1 | 31s [34] | 27s [34] | 135s [34] | TO | 28s [34] | TO | MO | 114s [34] | 21s [34] |
| L01 s012 t010 h2 | 12s [10] | 11s [10] | 78s [10] | TO | 9.36s [10] | 66s [13] | MO | 7.34s [10] | 5.92s [10] |
| L01 s009 t017 h1 | 36s [43] | 32s [43] | 157s [43] | TO | 32s [43] | TO | MO | TO | 22s [43] |
| L01 s005 t014 h1 | 46s [55] | 38s [55] | 191s [55] | TO | 42s [55] | TO | MO | TO | 28s [55] |
| L01 s002 t013 h1 | 46s [55] | 38s [57] | 202s [55] | TO | 43s [55] | TO | MO | TO | 26s [55] |
| L01 s001 t016 h1 | 61s [83] | 51s [83] | 283s [83] | TO | 60s [83] | TO | MO | TO | 43s [83] |
| L01 s008 t011 h1 | 41s [41] | 36s [41] | 197s [41] | TO | 39s [41] | TO | MO | TO | 264s [41] |
| L01 s010 t008 h2 | 27s [28] | 28s [28] | 159s [28] | TO | 25s [28] | TO | MO | TO | 22s [28] |
| L01 s017 t013 h2 | 16s [16] | 17s [16] | 112s [16] | TO | 15s [16] | 30s [19] | MO | 14s [16] | 6.18s [16] |
| L01 s013 t014 h2 | 13s [14] | 14s [14] | 89s [14] | TO | 14s [14] | 105s [21] | MO | 27s [14] | 5.98s [14] |
| L01 s011 t010 h2 | 16s [14] | 16s [14] | 123s [14] | TO | 15s [14] | TO | MO | 24s [14] | 6.54s [14] |
| L01 s018 t002 h2 | 40s [58] | 47s [58] | 248s [58] | TO | 53s [58] | TO | MO | TO | TO |
| L01 s016 t002 h2 | 49s [70] | 50s [72] | 303s [70] | TO | 52s [70] | TO | MO | TO | TO |
| L01 s012 t001 h2 | 34s [34] | 34s [34] | 191s [34] | TO | 35s [34] | TO | MO | 162s [34] | 20s [34] |
| L01 s016 t009 h2 | 42s [42] | 40s [42] | 219s [42] | TO | 37s [42] | TO | MO | TO | TO |
| L01 s014 t011 h2 | 59s [58] | 57s [58] | 296s [58] | TO | 57s [58] | TO | MO | TO | TO |

### scan-comb / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 8.29s [4] | 8.32s [4] | 51s [4] | 140s [4] | 8.05s [4] | 6.46s [4] | 3.67s [4] | 5.16s [4] | 4.03s [4] |
| L06 t002 | 6.01s [25] | 6.01s [25] | 41s [25] | TO | 6.34s [25] | 9.29s [25] | MO | TO | 1.85s [25] |
| L06 t005 | 6.62s [24] | 6.82s [24] | 56s [24] | TO | 7.14s [24] | 38s [24] | MO | TO | 2.00s [24] |
| L03 t018 | 11s [27] | 11s [27] | 68s [25] | TO | 11s [27] | TO | MO | 121s [25] | 95s [25] |
| L11 t115 | incomplete | incomplete | incomplete | TO | incomplete | incomplete | MO | incomplete | incomplete |
| L11 t168 | incomplete | incomplete | incomplete | TO | incomplete | incomplete | MO | incomplete | incomplete |
| L07 t001 | 21s [33] | 22s [33] | 120s [33] | TO | 21s [33] | TO | MO | TO | 38s [33] |
| L02 t005 | 46s [29] | 47s [29] | 284s [29] | TO | 221s [29] | 175s [39] | MO | TO | TO |
| L07 t008 | 25s [41] | 25s [41] | 131s [41] | TO | 25s [41] | TO | MO | TO | 12s [41] |
| L08 t003 | 49s [25] | 49s [25] | 271s [25] | MO | 55s [25] | TO | MO | TO | 29s [25] |
| L08 t001 | 37s [21] | 35s [21] | 163s [21] | MO | 35s [21] | TO | MO | 131s [20] | 102s [20] |
| L09 t003 | 34s [23] | 33s [23] | 171s [23] | TO | 32s [23] | TO | MO | TO | 13s [23] |
| L09 t005 | 34s [24] | 34s [24] | 178s [24] | TO | 32s [24] | TO | MO | TO | 14s [24] |
| L03 t002 | TO | 261s [37] | TO | TO | TO | TO | MO | TO | TO |
| L13 t006 | 31s [38] | 30s [38] | 145s [38] | TO | 32s [34] | TO | MO | 296s [34] | 29s [34] |
| L14 t016 | 77s [89] | TO | TO | TO | 80s [88] | TO | MO | TO | TO |
| L14 t006 | 61s [76] | 287s [80] | TO | TO | 64s [75] | TO | MO | TO | TO |
| L13 t003 | TO | 273s [63] | TO | TO | TO | TO | MO | TO | TO |

### scan-sep / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 14s [3] | 14s [3] | 82s [3] | 8.53s [3] | 11s [3] | 6.35s [3] | 1.92s [3] | 13s [3] | 6.99s [3] |
| L01 s004 t005 h1 | 21s [6] | 22s [6] | 128s [4] | 9.84s [4] | 22s [6] | 14s [4] | 2.94s [4] | 38s [4] | 33s [4] |
| L01 s007 t005 h1 | 14s [4] | 14s [4] | 102s [4] | 41s [4] | 15s [4] | 32s [4] | 9.21s [4] | 80s [4] | 36s [4] |
| L01 s005 t004 h1 | 22s [7] | 23s [7] | 165s [7] | 220s [7] | 26s [7] | 161s [7] | 62s [7] | TO | TO |
| L01 s007 t004 h1 | 31s [8] | 30s [8] | 232s [8] | TO | 30s [8] | TO | MO | TO | TO |
| L01 s018 t008 h2 | 41s [11] | 41s [11] | 257s [9] | TO | 46s [11] | TO | MO | TO | TO |
| L01 s003 t016 h1 | 150s [33] | 145s [33] | TO | TO | 161s [33] | TO | MO | TO | TO |
| L01 s013 t018 h2 | 93s [19] | 88s [19] | TO | TO | 94s [19] | TO | MO | TO | TO |
| L01 s003 t017 h1 | 154s [34] | 153s [34] | TO | TO | 156s [34] | TO | MO | TO | TO |
| L01 s012 t010 h2 | 44s [10] | 44s [10] | 284s [10] | TO | 41s [10] | TO | MO | TO | TO |
| L01 s009 t017 h1 | 204s [43] | 200s [43] | TO | TO | 207s [43] | TO | MO | TO | TO |
| L01 s005 t014 h1 | 248s [55] | 258s [55] | TO | TO | 291s [55] | TO | MO | TO | TO |
| L01 s002 t013 h1 | 252s [57] | 271s [57] | TO | TO | TO | TO | MO | TO | TO |
| L01 s001 t016 h1 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L01 s008 t011 h1 | 198s [41] | 213s [41] | TO | TO | 212s [41] | TO | MO | TO | TO |
| L01 s010 t008 h2 | 125s [28] | 135s [28] | TO | TO | 139s [28] | TO | MO | TO | TO |
| L01 s017 t013 h2 | 68s [16] | 68s [16] | TO | TO | 71s [16] | TO | MO | TO | TO |
| L01 s013 t014 h2 | 64s [14] | 62s [14] | TO | TO | 64s [14] | TO | MO | TO | TO |
| L01 s011 t010 h2 | 64s [14] | 62s [14] | TO | TO | 63s [14] | TO | MO | TO | TO |
| L01 s018 t002 h2 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L01 s016 t002 h2 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L01 s012 t001 h2 | 185s [34] | 179s [34] | TO | TO | 189s [34] | TO | MO | TO | TO |
| L01 s016 t009 h2 | 204s [44] | 199s [44] | TO | TO | 204s [44] | TO | MO | TO | TO |
| L01 s014 t011 h2 | 288s [60] | 282s [60] | TO | TO | TO | TO | MO | TO | TO |

### scan-sep / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 16s [4] | 15s [4] | 139s [4] | 40s [4] | 15s [4] | 40s [4] | 6.43s [4] | 90s [4] | 37s [4] |
| L06 t002 | 21s [25] | 23s [25] | 236s [25] | TO | 24s [25] | TO | MO | TO | TO |
| L06 t005 | 22s [24] | 23s [24] | 259s [24] | TO | 24s [24] | TO | MO | TO | TO |
| L03 t018 | 240s [36] | 252s [36] | TO | TO | 260s [36] | TO | MO | TO | TO |
| L11 t115 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L11 t168 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L07 t001 | 186s [33] | 202s [33] | TO | TO | 197s [33] | TO | MO | TO | TO |
| L02 t005 | 270s [30] | TO | TO | TO | TO | TO | MO | TO | TO |
| L07 t008 | 236s [41] | 239s [41] | TO | TO | 227s [41] | TO | MO | TO | TO |
| L08 t003 | 166s [25] | 168s [25] | TO | TO | 170s [25] | TO | MO | TO | TO |
| L08 t001 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L09 t003 | 136s [23] | 140s [23] | TO | TO | 141s [23] | TO | MO | TO | TO |
| L09 t005 | 151s [24] | 138s [24] | TO | TO | 157s [24] | TO | MO | TO | TO |
| L03 t002 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L13 t006 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L14 t016 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L14 t006 | TO | TO | TO | TO | TO | TO | MO | TO | TO |
| L13 t003 | TO | TO | TO | TO | TO | TO | MO | TO | TO |

### orderfree-comb / l1

| problem | gbfs-ff |
|---|---|
| L01 s009 t010 h1 | TO |
| L01 s005 t004 h1 | TO |
| L01 s007 t004 h1 | TO |
| L01 s003 t016 h1 | TO |
| L01 s005 t014 h1 | TO |
| L01 s002 t013 h1 | TO |

### orderfree-sep / l1

| problem | gbfs-ff |
|---|---|
| L01 s009 t010 h1 | TO |
| L01 s005 t004 h1 | TO |
| L01 s007 t004 h1 | TO |
| L01 s003 t016 h1 | TO |
| L01 s005 t014 h1 | TO |
| L01 s002 t013 h1 | TO |
