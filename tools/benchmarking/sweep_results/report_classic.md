# Fast Downward settings sweep

Variant **inv0** (translator options; +fa = forced-action fork). Other variants in the data: none (pick with --variant=NAME).

1392 runs from host(s) vm; models: scan-comb, scan-sep, orderfree-comb, orderfree-sep.

- **vm**: host=vm; cpus=4; ram_gb=16; cpu=Intel(R) Xeon(R) Processor @ 2.10GHz (groups A, C and the first 41 group-B jobs, until a container restart 2026-11-25 ~00:45 UTC); Intel(R) Xeon(R) Processor @ 2.30GHz (remaining group-B jobs); platform=Linux-6.18.44-fc-v819-x86_64-with-glibc2.39, then Linux-6.18.44-fc-v880-x86_64-with-glibc2.39; run[results_vm.csv]=jobs=4 timeout=300s mem=3G mem_limit=rlimit (FD driver) fd=upstream fast-downward release-24.06.1 (downward@1eef26b) classic configs only domains=a9f6ad1

Problems with no plan (search space exhausted; [models that proved it]), excluded from coverage for all models: L11 t115 [scan-comb], L11 t168 [scan-comb], testing_level_2 [scan-comb,scan-sep,orderfree-comb], testing_level_3 [scan-comb,scan-sep,orderfree-comb]

## Coverage (solved / solvable problems run)


### small (hand-made, 5x5..40x11)

| model | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp | astar-ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 9/10 (1TO) |
| scan-sep | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 9/10 (1TO) |
| orderfree-comb | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 9/10 (1TO) | 0/10 (10unsupported) | 0/10 (10unsupported) |
| orderfree-sep | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2TO) | 8/10 (2MO) | 8/10 (2TO) | 0/10 (10unsupported) | 0/10 (10unsupported) |

### bd_level_01 20x38 (h1+h2)

| model | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp | astar-ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 24/24 | 24/24 | 24/24 | 18/24 (6TO) | 3/24 (21TO) | 24/24 | 24/24 | 6/24 (16MO 2TO) | 20/24 (4TO) | 7/24 (16MO 1TO) |  |
| scan-sep | 22/24 (2TO) | 12/24 (12TO) | 22/24 (2TO) | 8/24 (16TO) | 3/24 (21TO) | 22/24 (2TO) | 4/24 (20TO) | 4/24 (20MO) | 3/24 (21TO) | 4/24 (20MO) |  |
| orderfree-comb | 0/6 (6TO) |  |  |  |  |  |  |  | 0/6 (6TO) |  |  |
| orderfree-sep | 0/6 (6TO) |  |  |  |  |  |  |  | 0/6 (6TO) |  |  |

### bd_levels 02..14

| model | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp | astar-ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 14/16 (2TO) | 14/16 (2TO) | 16/16 | 12/16 (4TO) | 1/16 (4MO 11TO) | 14/16 (2TO) | 12/16 (4TO) | 1/16 (15MO) | 11/16 (5TO) | 2/16 (14MO) |  |
| scan-sep | 10/16 (6TO) | 4/16 (12TO) | 9/16 (7TO) | 3/16 (13TO) | 1/16 (15TO) | 9/16 (7TO) | 1/16 (15TO) | 1/16 (15MO) | 1/16 (15TO) | 1/16 (15MO) |  |
| orderfree-comb |  |  |  |  |  |  |  |  |  |  |  |
| orderfree-sep |  |  |  |  |  |  |  |  |  |  |  |

## Search effort on tasks every listed config solved (per model)

Geometric mean of search time and expansions over the tasks solved by all configs in the row group; plan quality is the mean of cost / best known optimum.


**scan-comb / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.05s | 444 | 17 | 1.04 (n=10, max 1.38) |
| eager-gbfs-ff | 0.10s | 704 | 17 | 1.00 (n=10, max 1.00) |
| gbfs-add | 0.06s | 444 | 17 | 1.04 (n=10, max 1.38) |
| gbfs-cea | 0.22s | 635 | 25 | 1.02 (n=10, max 1.25) |
| gbfs-cg | 0.20s | 3625 | 240 | 1.05 (n=10, max 1.33) |
| wastar3-ff | 0.05s | 444 | 17 | 1.04 (n=10, max 1.38) |
| lama-first | 0.06s | 745 | 16 | 1.16 (n=10, max 1.67) |

**scan-comb / satisficing / l1** (18 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 15s | 4203 | 82 | 1.05 (n=15, max 1.50) |
| eager-gbfs-ff | 20s | 5550 | 86 | 1.00 (n=15, max 1.00) |
| gbfs-add | 15s | 4207 | 82 | 1.05 (n=15, max 1.50) |
| gbfs-cea | 136s | 4427 | 147 | 1.02 (n=15, max 1.25) |
| wastar3-ff | 15s | 4304 | 82 | 1.01 (n=15, max 1.22) |
| lama-first | 8.88s | 4399 | 68 | 1.02 (n=15, max 1.22) |

**scan-comb / satisficing / other** (12 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 16s | 5254 | 88 | 1.07 (n=11, max 1.60) |
| eager-gbfs-ff | 21s | 7000 | 88 | 1.06 (n=11, max 1.44) |
| gbfs-add | 15s | 5124 | 88 | 1.07 (n=11, max 1.60) |
| gbfs-cea | 108s | 4970 | 152 | 1.02 (n=11, max 1.12) |
| wastar3-ff | 16s | 5281 | 88 | 1.06 (n=11, max 1.60) |
| lama-first | 13s | 7148 | 69 | 1.06 (n=11, max 1.44) |

**scan-comb / optimal / small** (9 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 0.02s | 3926 | 18 | 1.00 (n=9, max 1.00) |
| astar-hmax | 0.04s | 682 | 16 | 1.00 (n=9, max 1.00) |
| astar-lmcp | 0.01s | 2883 | 18 | 1.00 (n=9, max 1.00) |
| astar-ms | 0.03s | 3739 | 77 | 1.00 (n=9, max 1.00) |

**scan-comb / optimal / l1** (20 common tasks; left out for low coverage: astar-blind, astar-lmcp)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-hmax | 13s | 6303 | 105 | 1.00 (n=20, max 1.00) |

**scan-comb / optimal / other** (11 common tasks; left out for low coverage: astar-blind, astar-lmcp)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-hmax | 18s | 10k | 95 | 1.00 (n=11, max 1.00) |

**scan-sep / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.08s | 906 | 40 | 1.01 (n=10, max 1.12) |
| eager-gbfs-ff | 0.16s | 1737 | 40 | 1.00 (n=10, max 1.00) |
| gbfs-add | 0.07s | 906 | 40 | 1.01 (n=10, max 1.12) |
| gbfs-cea | 0.33s | 1172 | 69 | 1.00 (n=10, max 1.00) |
| gbfs-cg | 0.12s | 3479 | 408 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.08s | 906 | 40 | 1.01 (n=10, max 1.12) |
| lama-first | 0.18s | 2683 | 42 | 1.00 (n=10, max 1.00) |

**scan-sep / satisficing / l1** (12 common tasks; left out for low coverage: gbfs-cea, gbfs-cg, lama-first)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 39s | 13k | 95 | 1.06 (n=12, max 1.50) |
| eager-gbfs-ff | 93s | 29k | 125 | 1.00 (n=12, max 1.00) |
| gbfs-add | 37s | 13k | 95 | 1.06 (n=12, max 1.50) |
| wastar3-ff | 39s | 13k | 95 | 1.06 (n=12, max 1.50) |

**scan-sep / satisficing / other** (9 common tasks; left out for low coverage: eager-gbfs-ff, gbfs-cea, gbfs-cg, lama-first)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 90s | 29k | 117 | 1.05 (n=9, max 1.44) |
| gbfs-add | 88s | 29k | 117 | 1.05 (n=9, max 1.44) |
| wastar3-ff | 95s | 29k | 117 | 1.05 (n=9, max 1.44) |

**scan-sep / optimal / small** (9 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 0.02s | 5758 | 46 | 1.00 (n=9, max 1.00) |
| astar-hmax | 0.12s | 2996 | 45 | 1.00 (n=9, max 1.00) |
| astar-lmcp | 0.02s | 5561 | 43 | 1.00 (n=9, max 1.00) |
| astar-ms | 0.03s | 5561 | 1428 | 1.00 (n=9, max 1.00) |

**scan-sep / optimal / l1** (3 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 5.30s | 115k | 269 | 1.00 (n=3, max 1.00) |
| astar-hmax | 30s | 18k | 69 | 1.00 (n=3, max 1.00) |
| astar-lmcp | 1.99s | 39k | 105 | 1.00 (n=3, max 1.00) |

**scan-sep / optimal / other** (1 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 7.43s | 190k | 203 | 1.00 (n=1, max 1.00) |
| astar-hmax | 48s | 28k | 75 | 1.00 (n=1, max 1.00) |
| astar-lmcp | 2.82s | 68k | 97 | 1.00 (n=1, max 1.00) |

**orderfree-comb / satisficing / small** (9 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.02s | 241 | 96 | 1.04 (n=9, max 1.38) |
| eager-gbfs-ff | 0.03s | 363 | 89 | 1.00 (n=9, max 1.00) |
| gbfs-add | 0.02s | 241 | 96 | 1.04 (n=9, max 1.38) |
| gbfs-cea | 0.03s | 259 | 95 | 1.00 (n=9, max 1.00) |
| gbfs-cg | 0.05s | 1312 | 410 | 1.00 (n=9, max 1.00) |
| wastar3-ff | 0.02s | 241 | 96 | 1.04 (n=9, max 1.38) |
| lama-first | 0.01s | 284 | 29 | 1.01 (n=9, max 1.12) |

**orderfree-comb / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-ff)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

**orderfree-comb / optimal / small** (9 common tasks; left out for low coverage: astar-lmcp, astar-ms)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 0.01s | 1460 | 306 | 1.00 (n=9, max 1.00) |
| astar-hmax | 0.02s | 398 | 86 | 1.00 (n=9, max 1.00) |

**orderfree-comb / optimal / l1** (24 common tasks; left out for low coverage: astar-hmax)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

**orderfree-sep / satisficing / small** (8 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.01s | 282 | 16 | 1.02 (n=8, max 1.12) |
| eager-gbfs-ff | 0.03s | 515 | 16 | 1.00 (n=8, max 1.00) |
| gbfs-add | 0.01s | 282 | 16 | 1.02 (n=8, max 1.12) |
| gbfs-cea | 0.03s | 303 | 20 | 1.00 (n=8, max 1.00) |
| gbfs-cg | 0.02s | 1000 | 153 | 1.00 (n=8, max 1.00) |
| wastar3-ff | 0.01s | 282 | 16 | 1.02 (n=8, max 1.12) |
| lama-first | 0.02s | 498 | 15 | 1.02 (n=8, max 1.12) |

**orderfree-sep / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-ff)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

**orderfree-sep / optimal / small** (8 common tasks; left out for low coverage: astar-lmcp, astar-ms)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-blind | 0.01s | 1898 | 16 | 1.00 (n=8, max 1.00) |
| astar-hmax | 0.02s | 702 | 14 | 1.00 (n=8, max 1.00) |

**orderfree-sep / optimal / l1** (24 common tasks; left out for low coverage: astar-hmax)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|

## Optimal cost agreement

41 problems solved optimally; 15 of them by more than one model. All optimal costs agree across configs and models.

## Translation (per model and problem set)

| model | set | problems | translate s (median / max) | operators (median / max) | translate failures |
|---|---|---|---|---|---|
| scan-comb | small | 12 | 1.2 / 3.8 | 449 / 2262 | 0 |
| scan-comb | l1 | 24 | 20.7 / 39.5 | 21k / 21k | 0 |
| scan-comb | other | 18 | 14.2 / 23.6 | 16k / 22k | 0 |
| scan-sep | small | 12 | 0.4 / 4.4 | 2289 / 19k | 0 |
| scan-sep | l1 | 24 | 10.9 / 14.8 | 36k / 36k | 0 |
| scan-sep | other | 18 | 11.8 / 13.7 | 39k / 40k | 0 |
| orderfree-comb | small | 12 | 0.8 / 3.4 | 494 / 3207 | 0 |
| orderfree-comb | l1 | 6 | 17.7 / 20.6 | 23k / 23k | 0 |
| orderfree-sep | small | 12 | 0.4 / 4.7 | 1806 / 15k | 0 |
| orderfree-sep | l1 | 6 | 10.6 / 11.1 | 30k / 30k | 0 |

## Per-problem detail (search time, cost)


### scan-comb / l1

| problem | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp |
|---|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 7.85s [3] | 7.26s [3] | 6.82s [3] | 91s [3] | 191s [3] | 9.16s [3] | 4.73s [3] | 2.88s [3] | 3.55s [3] | 1.26s [3] |
| L01 s005 t004 h1 | 12s [7] | 11s [7] | 13s [7] | 156s [7] | TO | 16s [7] | 6.79s [8] | 20s [7] | 7.16s [7] | 14s [7] |
| L01 s007 t004 h1 | 13s [8] | 21s [8] | 12s [8] | 191s [8] | TO | 12s [8] | 7.43s [8] | 133s [8] | 8.33s [8] | 85s [8] |
| L01 s002 t013 h1 | 45s [55] | 68s [55] | 54s [57] | TO | TO | 76s [55] | 33s [55] | TO | 42s [55] | TO |
| L01 s005 t014 h1 | 65s [55] | 80s [55] | 55s [55] | TO | TO | 65s [55] | 32s [56] | TO | 27s [55] | MO |
| L01 s003 t016 h1 | 43s [33] | 45s [33] | 45s [33] | TO | TO | 46s [33] | 19s [33] | MO | 14s [33] | MO |
| L01 s007 t005 h1 | 7.05s [4] | 14s [4] | 6.67s [4] | 71s [4] | 242s [4] | 6.74s [4] | 4.02s [4] | 9.29s [4] | 8.03s [4] | 3.11s [4] |
| L01 s004 t005 h1 | 8.00s [6] | 9.79s [4] | 8.48s [6] | 106s [5] | 49s [4] | 12s [4] | 4.47s [4] | 2.61s [4] | 4.97s [4] | 1.66s [4] |
| L01 s009 t017 h1 | 59s [43] | 72s [43] | 54s [43] | 254s [43] | TO | 25s [43] | 15s [43] | MO | 24s [43] | MO |
| L01 s003 t017 h1 | 20s [34] | 24s [34] | 20s [34] | 195s [34] | TO | 23s [34] | 14s [34] | MO | 15s [34] | MO |
| L01 s018 t008 h2 | 9.23s [11] | 14s [9] | 9.64s [11] | 90s [9] | TO | 9.58s [11] | 6.49s [11] | 88s [9] | 8.18s [9] | 36s [9] |
| L01 s013 t018 h2 | 14s [19] | 18s [19] | 14s [19] | 131s [19] | TO | 12s [19] | 7.69s [19] | MO | 9.67s [19] | MO |
| L01 s008 t011 h1 | 32s [41] | 47s [41] | 31s [41] | TO | TO | 29s [41] | 15s [41] | MO | 126s [41] | MO |
| L01 s001 t016 h1 | 47s [83] | 75s [83] | 48s [83] | TO | TO | 46s [83] | 30s [83] | MO | 45s [83] | MO |
| L01 s012 t010 h2 | 10s [10] | 9.53s [10] | 9.52s [10] | 104s [10] | TO | 9.62s [10] | 7.11s [10] | MO | 5.41s [10] | 92s [10] |
| L01 s010 t008 h2 | 20s [28] | 30s [28] | 20s [28] | 178s [28] | TO | 20s [28] | 13s [28] | MO | 19s [28] | MO |
| L01 s018 t002 h2 | 31s [58] | 65s [58] | 33s [58] | 286s [58] | TO | 31s [58] | 23s [58] | MO | TO | MO |
| L01 s016 t002 h2 | 38s [70] | 55s [70] | 41s [72] | TO | TO | 36s [70] | 22s [70] | MO | TO | MO |
| L01 s017 t013 h2 | 11s [16] | 12s [16] | 11s [16] | 75s [16] | TO | 11s [16] | 6.86s [16] | MO | 6.31s [16] | MO |
| L01 s016 t009 h2 | 24s [42] | 31s [42] | 24s [42] | 162s [42] | TO | 24s [42] | 13s [42] | MO | TO | MO |
| L01 s013 t014 h2 | 9.94s [14] | 16s [14] | 9.85s [14] | 80s [14] | TO | 9.93s [14] | 6.07s [14] | MO | 8.55s [14] | MO |
| L01 s011 t010 h2 | 11s [14] | 16s [14] | 11s [14] | 100s [14] | TO | 11s [14] | 8.31s [14] | MO | 7.91s [14] | MO |
| L01 s014 t011 h2 | 38s [58] | 49s [58] | 31s [58] | 245s [58] | TO | 38s [58] | 19s [58] | MO | TO | MO |
| L01 s012 t001 h2 | 24s [34] | 26s [34] | 23s [34] | 161s [34] | TO | 24s [34] | 15s [34] | MO | 16s [34] | MO |

### scan-comb / other

| problem | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp |
|---|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 6.88s [4] | 8.93s [4] | 6.46s [4] | 50s [4] | 96s [4] | 6.54s [4] | 6.67s [4] | 4.77s [4] | 4.53s [4] | 1.68s [4] |
| L03 t018 | 22s [40] | 14s [36] | 17s [40] | 51s [25] | TO | 23s [40] | 7.08s [36] | MO | 85s [25] | MO |
| L02 t005 | 17s [30] | 44s [29] | 17s [30] | 219s [29] | TO | 17s [30] | 14s [30] | MO | TO | MO |
| L06 t005 | 5.53s [24] | 10s [24] | 5.43s [24] | 43s [24] | TO | 5.52s [24] | 3.65s [24] | MO | 4.01s [24] | MO |
| L06 t002 | 4.85s [25] | 8.15s [25] | 5.23s [25] | 37s [25] | TO | 5.89s [25] | 3.08s [25] | MO | 4.85s [25] | MO |
| L07 t001 | 16s [33] | 17s [33] | 15s [33] | 132s [33] | MO | 16s [33] | 8.97s [33] | MO | 21s [33] | MO |
| L07 t008 | 18s [41] | 24s [41] | 18s [41] | 139s [41] | MO | 19s [41] | 11s [41] | MO | 15s [41] | MO |
| L08 t001 | 23s [21] | 26s [21] | 22s [21] | 171s [21] | MO | 22s [21] | 17s [25] | MO | 65s [20] | 109s [20] |
| L08 t003 | 26s [25] | 49s [25] | 25s [25] | 267s [25] | MO | 26s [25] | 36s [25] | MO | 28s [25] | MO |
| L09 t005 | 23s [24] | 37s [24] | 23s [24] | 184s [24] | TO | 22s [24] | 39s [24] | MO | 22s [24] | MO |
| L03 t002 | TO | TO | 183s [39] | TO | TO | TO | TO | MO | TO | MO |
| L11 t115 | incomplete | incomplete | incomplete | incomplete | TO | incomplete | incomplete | MO | incomplete | incomplete |
| L11 t168 | incomplete | incomplete | incomplete | incomplete | TO | incomplete | incomplete | MO | incomplete | incomplete |
| L09 t003 | 21s [23] | 39s [23] | 20s [23] | 148s [23] | TO | 21s [23] | 39s [23] | MO | 21s [23] | MO |
| L13 t006 | 37s [38] | 25s [38] | 36s [38] | 124s [38] | TO | 36s [34] | 33s [34] | MO | 25s [34] | MO |
| L14 t006 | 48s [95] | 49s [76] | 234s [80] | TO | TO | 67s [75] | TO | MO | TO | MO |
| L14 t016 | 58s [108] | 61s [89] | 267s [93] | TO | TO | 82s [88] | TO | MO | TO | MO |
| L13 t003 | TO | TO | 224s [63] | TO | TO | TO | TO | MO | TO | MO |

### scan-sep / l1

| problem | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp |
|---|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 12s [3] | 23s [3] | 11s [3] | 69s [3] | 22s [3] | 12s [3] | 11s [3] | 2.41s [3] | 14s [3] | 0.74s [3] |
| L01 s005 t004 h1 | 26s [7] | 51s [7] | 24s [7] | 147s [7] | TO | 25s [7] | 57s [7] | 77s [7] | TO | 38s [7] |
| L01 s007 t004 h1 | 29s [8] | 72s [8] | 28s [8] | 186s [8] | TO | 30s [8] | TO | MO | TO | MO |
| L01 s002 t013 h1 | 252s [57] | TO | 241s [57] | TO | TO | 250s [57] | TO | MO | TO | MO |
| L01 s005 t014 h1 | 239s [55] | TO | 231s [55] | TO | TO | 239s [55] | TO | MO | TO | MO |
| L01 s003 t016 h1 | 136s [33] | TO | 132s [33] | TO | TO | 136s [33] | TO | MO | TO | MO |
| L01 s007 t005 h1 | 17s [4] | 44s [4] | 15s [4] | 102s [4] | 101s [4] | 14s [4] | 53s [4] | 12s [4] | 47s [4] | 5.17s [4] |
| L01 s004 t005 h1 | 23s [6] | 33s [4] | 21s [6] | 133s [4] | 24s [4] | 23s [6] | 17s [4] | 5.08s [4] | 42s [4] | 2.07s [4] |
| L01 s009 t017 h1 | 196s [43] | TO | 193s [43] | TO | TO | 189s [43] | TO | MO | TO | MO |
| L01 s003 t017 h1 | 149s [34] | TO | 146s [34] | TO | TO | 147s [34] | TO | MO | TO | MO |
| L01 s018 t008 h2 | 43s [11] | 112s [9] | 41s [11] | 217s [9] | TO | 44s [11] | TO | MO | TO | MO |
| L01 s013 t018 h2 | 79s [19] | 226s [19] | 77s [19] | TO | TO | 79s [19] | TO | MO | TO | MO |
| L01 s008 t011 h1 | 183s [41] | TO | 172s [41] | TO | TO | 178s [41] | TO | MO | TO | MO |
| L01 s001 t016 h1 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L01 s012 t010 h2 | 38s [10] | 100s [10] | 35s [10] | 225s [10] | TO | 38s [10] | TO | MO | TO | MO |
| L01 s010 t008 h2 | 124s [28] | TO | 119s [28] | TO | TO | 123s [28] | TO | MO | TO | MO |
| L01 s018 t002 h2 | 285s [60] | TO | 278s [60] | TO | TO | 283s [60] | TO | MO | TO | MO |
| L01 s016 t002 h2 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L01 s017 t013 h2 | 65s [16] | 187s [16] | 61s [16] | TO | TO | 63s [16] | TO | MO | TO | MO |
| L01 s016 t009 h2 | 181s [44] | TO | 182s [44] | TO | TO | 180s [44] | TO | MO | TO | MO |
| L01 s013 t014 h2 | 55s [14] | 156s [14] | 53s [14] | TO | TO | 56s [14] | TO | MO | TO | MO |
| L01 s011 t010 h2 | 56s [14] | 149s [14] | 53s [14] | 292s [14] | TO | 57s [14] | TO | MO | TO | MO |
| L01 s014 t011 h2 | 257s [60] | TO | 240s [60] | TO | TO | 259s [60] | TO | MO | TO | MO |
| L01 s012 t001 h2 | 156s [34] | 288s [34] | 148s [34] | TO | TO | 149s [34] | TO | MO | TO | MO |

### scan-sep / other

| problem | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | astar-blind | astar-hmax | astar-lmcp |
|---|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 15s [4] | 50s [4] | 14s [4] | 118s [4] | 85s [4] | 15s [4] | 53s [4] | 7.43s [4] | 48s [4] | 2.82s [4] |
| L03 t018 | 196s [36] | 222s [25] | 194s [36] | TO | TO | 206s [36] | TO | MO | TO | MO |
| L02 t005 | 228s [30] | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L06 t005 | 32s [24] | TO | 31s [24] | 182s [24] | TO | 31s [24] | TO | MO | TO | MO |
| L06 t002 | 30s [25] | 184s [25] | 32s [25] | 221s [25] | TO | 37s [25] | TO | MO | TO | MO |
| L07 t001 | 179s [33] | TO | 182s [33] | TO | TO | 204s [33] | TO | MO | TO | MO |
| L07 t008 | 222s [41] | TO | 214s [41] | TO | TO | 236s [41] | TO | MO | TO | MO |
| L08 t001 | TO | 181s [20] | TO | TO | TO | TO | TO | MO | TO | MO |
| L08 t003 | 145s [25] | TO | 140s [25] | TO | TO | 150s [25] | TO | MO | TO | MO |
| L09 t005 | 150s [24] | TO | 150s [24] | TO | TO | 153s [24] | TO | MO | TO | MO |
| L03 t002 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L11 t115 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L11 t168 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L09 t003 | 160s [23] | TO | 140s [23] | TO | TO | 162s [23] | TO | MO | TO | MO |
| L13 t006 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L14 t006 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
| L14 t016 | TO | TO | TO | TO | TO | TO | TO | MO | TO | MO |
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
