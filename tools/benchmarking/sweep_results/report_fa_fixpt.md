# Fast Downward settings sweep

Variant **inv0+fa+fixpt** (translator options; +fa = forced-action fork). Other variants in the data: inv0, inv0+fa (pick with --variant=NAME).

1944 runs from host(s) m5pro; models: scan-comb, scan-sep, orderfree-comb, orderfree-sep.

- **m5pro**: host=m5pro; cpus=18; ram_gb=48; cpu=Apple M5 Pro; platform=macOS-26.5.2-arm64-arm-64bit-Mach-O; run[results_m5pro.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0; run[results_m5pro_fa.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0; run[results_m5pro_fa_fixpt.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fd-fixpoint@52938c8b5 FD_STATE_DUMP=0 domains=a9f6ad1

Problems with no plan (search space exhausted; [models that proved it]), excluded from coverage for all models: L11 t115 [scan-comb,orderfree-comb], L11 t168 [scan-comb,orderfree-comb], testing_level_2 [scan-comb,scan-sep,orderfree-comb,orderfree-sep], testing_level_3 [scan-comb,scan-sep,orderfree-comb,orderfree-sep]

## Coverage (solved / solvable problems run)


### small (hand-made, 5x5..40x11)

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| scan-sep | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| orderfree-comb | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| orderfree-sep | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |

### bd_level_01 20x38 (h1+h2)

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 24/24 | 24/24 | 24/24 | 7/24 (17TO) | 24/24 | 24/24 | 8/24 (16TO) | 16/24 (8TO) | 22/24 (2TO) |
| scan-sep | 24/24 | 24/24 | 24/24 | 7/24 (17TO) | 24/24 | 24/24 | 7/24 (17TO) | 7/24 (17TO) | 7/24 (17TO) |
| orderfree-comb | 24/24 | 24/24 | 24/24 | 7/24 (17TO) | 24/24 | 24/24 | 7/24 (17TO) | 16/24 (8TO) | 22/24 (2TO) |
| orderfree-sep | 18/24 (6TO) | 18/24 (6TO) | 18/24 (6TO) | 6/24 (18TO) | 18/24 (6TO) | 18/24 (6TO) | 6/24 (18TO) | 7/24 (17TO) | 7/24 (17TO) |

### bd_levels 02..14

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 16/16 | 16/16 | 16/16 | 1/16 (2MO 13TO) | 16/16 | 16/16 | 1/16 (15TO) | 8/16 (8TO) | 13/16 (3TO) |
| scan-sep | 14/16 (2TO) | 14/16 (2TO) | 14/16 (2TO) | 1/16 (15TO) | 15/16 (1TO) | 15/16 (1TO) | 1/16 (15TO) | 1/16 (15TO) | 1/16 (15TO) |
| orderfree-comb | 16/16 | 16/16 | 16/16 | 1/16 (15TO) | 16/16 | 16/16 | 1/16 (15TO) | 8/16 (8TO) | 13/16 (3TO) |
| orderfree-sep | 13/16 (3TO) | 14/16 (2TO) | 12/16 (4TO) | 1/16 (15TO) | 16/16 | 15/16 (1TO) | 1/16 (15TO) | 1/16 (15TO) | 1/16 (15TO) |

## Search effort on tasks every listed config solved (per model)

Geometric mean of search time and expansions over the tasks solved by all configs in the row group; plan quality is the mean of cost / best known optimum.


**scan-comb / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| gbfs-add | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| gbfs-cea | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| gbfs-cg | 0.01s | 67 | 253 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| lama-first | 0.00s | 18 | 0 | 1.01 (n=10, max 1.12) |

**scan-comb / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.17s | 28 | 108 | 1.01 (n=22, max 1.22) |
| gbfs-add | 0.17s | 27 | 105 | 1.01 (n=22, max 1.22) |
| gbfs-cea | 0.57s | 27 | 171 | 1.01 (n=22, max 1.22) |
| wastar3-ff | 0.18s | 28 | 105 | 1.01 (n=22, max 1.22) |
| lama-first | 0.20s | 38 | 107 | 1.02 (n=22, max 1.50) |

**scan-comb / satisficing / other** (16 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.32s | 67 | 107 | 1.04 (n=13, max 1.36) |
| gbfs-add | 0.30s | 62 | 110 | 1.03 (n=13, max 1.32) |
| gbfs-cea | 0.98s | 59 | 180 | 1.03 (n=13, max 1.32) |
| wastar3-ff | 0.38s | 80 | 141 | 1.02 (n=13, max 1.11) |
| lama-first | 0.56s | 156 | 246 | 1.06 (n=13, max 1.44) |

**scan-comb / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.01s | 74 | 0 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.00s | 46 | 0 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.00s | 24 | 0 | 1.00 (n=10, max 1.00) |

**scan-comb / optimal / l1** (16 common tasks; left out for low coverage: lazy-astar-blind)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax | 1.26s | 378 | 238 | 1.00 (n=16, max 1.00) |
| lazy-astar-hmax-tb | 0.15s | 30 | 93 | 1.00 (n=16, max 1.00) |

**scan-comb / optimal / other** (8 common tasks; left out for low coverage: lazy-astar-blind)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax | 10s | 3986 | 227 | 1.00 (n=8, max 1.00) |
| lazy-astar-hmax-tb | 0.36s | 93 | 88 | 1.00 (n=8, max 1.00) |

**scan-sep / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.00s | 15 | 56 | 1.01 (n=10, max 1.12) |
| gbfs-add | 0.00s | 15 | 56 | 1.01 (n=10, max 1.12) |
| gbfs-cea | 0.00s | 15 | 65 | 1.01 (n=10, max 1.12) |
| gbfs-cg | 0.00s | 44 | 381 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.00s | 16 | 55 | 1.00 (n=10, max 1.00) |
| lama-first | 0.00s | 19 | 54 | 1.01 (n=10, max 1.12) |

**scan-sep / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.18s | 29 | 101 | 1.04 (n=22, max 1.50) |
| gbfs-add | 0.18s | 29 | 103 | 1.04 (n=22, max 1.50) |
| gbfs-cea | 0.53s | 29 | 146 | 1.04 (n=22, max 1.50) |
| wastar3-ff | 0.18s | 29 | 103 | 1.04 (n=22, max 1.50) |
| lama-first | 0.20s | 41 | 102 | 1.02 (n=22, max 1.50) |

**scan-sep / satisficing / other** (13 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.32s | 51 | 111 | 1.04 (n=11, max 1.44) |
| gbfs-add | 0.53s | 86 | 119 | 1.04 (n=11, max 1.44) |
| gbfs-cea | 1.57s | 90 | 171 | 1.04 (n=11, max 1.44) |
| wastar3-ff | 0.48s | 78 | 112 | 1.04 (n=11, max 1.44) |
| lama-first | 0.64s | 127 | 131 | 1.04 (n=11, max 1.44) |

**scan-sep / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.00s | 63 | 24 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.00s | 55 | 43 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.00s | 50 | 44 | 1.00 (n=10, max 1.00) |

**scan-sep / optimal / l1** (7 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 2.13s | 704 | 77 | 1.00 (n=7, max 1.00) |
| lazy-astar-hmax | 1.89s | 430 | 94 | 1.00 (n=7, max 1.00) |
| lazy-astar-hmax-tb | 1.14s | 254 | 93 | 1.00 (n=7, max 1.00) |

**scan-sep / optimal / other** (1 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.18s | 65 | 51 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax | 0.22s | 56 | 91 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax-tb | 0.09s | 23 | 67 | 1.00 (n=1, max 1.00) |

**orderfree-comb / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.00s | 16 | 0 | 1.01 (n=10, max 1.12) |
| gbfs-add | 0.00s | 16 | 0 | 1.01 (n=10, max 1.12) |
| gbfs-cea | 0.00s | 16 | 0 | 1.01 (n=10, max 1.12) |
| gbfs-cg | 0.00s | 57 | 222 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| lama-first | 0.00s | 18 | 0 | 1.01 (n=10, max 1.12) |

**orderfree-comb / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.23s | 28 | 99 | 1.01 (n=22, max 1.22) |
| gbfs-add | 0.23s | 27 | 100 | 1.01 (n=22, max 1.22) |
| gbfs-cea | 0.39s | 27 | 130 | 1.01 (n=22, max 1.22) |
| wastar3-ff | 0.23s | 28 | 99 | 1.01 (n=22, max 1.22) |
| lama-first | 0.25s | 38 | 97 | 1.00 (n=22, max 1.04) |

**orderfree-comb / satisficing / other** (16 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.29s | 52 | 104 | 1.01 (n=13, max 1.08) |
| gbfs-add | 0.28s | 50 | 103 | 1.03 (n=13, max 1.32) |
| gbfs-cea | 0.51s | 50 | 136 | 1.03 (n=13, max 1.32) |
| wastar3-ff | 0.33s | 60 | 102 | 1.01 (n=13, max 1.08) |
| lama-first | 0.35s | 81 | 101 | 1.01 (n=13, max 1.08) |

**orderfree-comb / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.00s | 62 | 0 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.00s | 42 | 0 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.00s | 23 | 0 | 1.00 (n=10, max 1.00) |

**orderfree-comb / optimal / l1** (16 common tasks; left out for low coverage: lazy-astar-blind)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax | 1.80s | 364 | 177 | 1.00 (n=16, max 1.00) |
| lazy-astar-hmax-tb | 0.19s | 30 | 86 | 1.00 (n=16, max 1.00) |

**orderfree-comb / optimal / other** (8 common tasks; left out for low coverage: lazy-astar-blind)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax | 17s | 3799 | 177 | 1.00 (n=8, max 1.00) |
| lazy-astar-hmax-tb | 0.51s | 90 | 84 | 1.00 (n=8, max 1.00) |

**orderfree-sep / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.00s | 15 | 57 | 1.01 (n=10, max 1.12) |
| gbfs-add | 0.00s | 15 | 62 | 1.01 (n=10, max 1.12) |
| gbfs-cea | 0.01s | 15 | 82 | 1.01 (n=10, max 1.12) |
| gbfs-cg | 0.01s | 45 | 797 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.00s | 16 | 62 | 1.00 (n=10, max 1.00) |
| lama-first | 0.00s | 19 | 61 | 1.01 (n=10, max 1.12) |

**orderfree-sep / satisficing / l1** (18 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.91s | 23 | 101 | 1.02 (n=17, max 1.22) |
| gbfs-add | 0.88s | 22 | 99 | 1.01 (n=17, max 1.22) |
| gbfs-cea | 1.07s | 21 | 141 | 1.01 (n=17, max 1.22) |
| wastar3-ff | 0.91s | 23 | 100 | 1.01 (n=17, max 1.22) |
| lama-first | 1.06s | 30 | 93 | 1.03 (n=17, max 1.50) |

**orderfree-sep / satisficing / other** (12 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 1.37s | 52 | 109 | 1.03 (n=12, max 1.24) |
| gbfs-add | 1.21s | 46 | 106 | 1.03 (n=12, max 1.21) |
| gbfs-cea | 1.66s | 48 | 148 | 1.02 (n=12, max 1.11) |
| wastar3-ff | 1.52s | 59 | 107 | 1.02 (n=12, max 1.08) |
| lama-first | 1.49s | 65 | 98 | 1.08 (n=12, max 1.54) |

**orderfree-sep / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.01s | 63 | 34 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.01s | 49 | 53 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.01s | 36 | 53 | 1.00 (n=10, max 1.00) |

**orderfree-sep / optimal / l1** (6 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 10s | 418 | 58 | 1.00 (n=6, max 1.00) |
| lazy-astar-hmax | 4.40s | 162 | 84 | 1.00 (n=6, max 1.00) |
| lazy-astar-hmax-tb | 2.83s | 103 | 82 | 1.00 (n=6, max 1.00) |

**orderfree-sep / optimal / other** (1 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 1.56s | 81 | 47 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax | 1.14s | 56 | 85 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax-tb | 0.66s | 30 | 84 | 1.00 (n=1, max 1.00) |

## Optimal cost agreement

45 problems solved optimally; 45 of them by more than one model. All optimal costs agree across configs and models.

## Translation (per model and problem set)

| model | set | problems | translate s (median / max) | operators (median / max) | translate failures |
|---|---|---|---|---|---|
| scan-comb | small | 12 | 0.4 / 1.1 | 449 / 2262 | 0 |
| scan-comb | l1 | 24 | 11.0 / 12.3 | 21k / 21k | 0 |
| scan-comb | other | 18 | 8.6 / 11.3 | 16k / 22k | 0 |
| scan-sep | small | 12 | 0.3 / 2.5 | 2289 / 19k | 0 |
| scan-sep | l1 | 24 | 5.9 / 6.1 | 36k / 36k | 0 |
| scan-sep | other | 18 | 6.6 / 6.8 | 39k / 40k | 0 |
| orderfree-comb | small | 12 | 0.5 / 1.7 | 494 / 3207 | 0 |
| orderfree-comb | l1 | 24 | 8.6 / 8.9 | 23k / 23k | 0 |
| orderfree-comb | other | 18 | 6.7 / 9.2 | 18k / 24k | 0 |
| orderfree-sep | small | 12 | 0.3 / 2.3 | 1806 / 15k | 0 |
| orderfree-sep | l1 | 24 | 5.1 / 5.3 | 30k / 30k | 0 |
| orderfree-sep | other | 18 | 5.8 / 6.3 | 32k / 33k | 0 |

## Per-problem detail (search time, cost)


### scan-comb / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 0.06s [3] | 0.06s [3] | 0.13s [3] | 0.39s [3] | 0.06s [3] | 0.06s [3] | 0.21s [3] | 0.09s [3] | 0.06s [3] |
| L01 s004 t005 h1 | 0.07s [4] | 0.06s [4] | 0.15s [4] | 0.23s [4] | 0.08s [4] | 0.06s [6] | 0.25s [4] | 0.12s [4] | 0.07s [4] |
| L01 s007 t005 h1 | 0.06s [4] | 0.06s [4] | 0.16s [4] | 0.92s [5] | 0.06s [4] | 0.06s [4] | 0.47s [4] | 0.22s [4] | 0.13s [4] |
| L01 s005 t004 h1 | 0.07s [7] | 0.08s [7] | 0.19s [7] | 5.00s [7] | 0.08s [7] | 0.07s [7] | 1.99s [7] | 0.24s [7] | 0.09s [7] |
| L01 s007 t004 h1 | 0.08s [8] | 0.07s [8] | 0.18s [8] | 32s [8] | 0.08s [8] | 0.09s [8] | 8.46s [8] | 0.35s [8] | 0.10s [8] |
| L01 s018 t008 h2 | 0.11s [11] | 0.11s [11] | 0.38s [11] | 44s [9] | 0.12s [11] | 0.15s [9] | 11s [9] | 0.39s [9] | 0.13s [9] |
| L01 s012 t010 h2 | 0.07s [10] | 0.08s [10] | 0.25s [10] | 74s [11] | 0.08s [10] | 0.08s [10] | 15s [10] | 0.21s [10] | 0.07s [10] |
| L01 s003 t016 h1 | 0.21s [33] | 0.20s [33] | 0.79s [33] | TO | 0.23s [33] | 0.27s [33] | TO | 2.90s [33] | 0.19s [33] |
| L01 s003 t017 h1 | 0.22s [34] | 0.20s [34] | 0.80s [34] | TO | 0.24s [34] | 0.27s [34] | TO | 3.30s [34] | 0.19s [34] |
| L01 s013 t018 h2 | 0.12s [19] | 0.12s [19] | 0.46s [19] | TO | 0.12s [19] | 0.14s [19] | TO | 13s [19] | 0.10s [19] |
| L01 s009 t017 h1 | 0.23s [43] | 0.24s [43] | 0.97s [43] | TO | 0.29s [43] | 0.32s [43] | TO | 139s [43] | 0.25s [43] |
| L01 s017 t013 h2 | 0.14s [16] | 0.14s [16] | 0.53s [16] | TO | 0.13s [16] | 0.16s [16] | TO | 0.57s [16] | 0.12s [16] |
| L01 s005 t014 h1 | 0.31s [55] | 0.30s [55] | 1.15s [55] | TO | 0.38s [55] | 0.40s [55] | TO | TO | 0.33s [55] |
| L01 s002 t013 h1 | 0.33s [55] | 0.34s [57] | 1.15s [57] | TO | 0.41s [55] | 0.45s [57] | TO | TO | 0.35s [55] |
| L01 s008 t011 h1 | 0.26s [41] | 0.25s [41] | 0.78s [41] | TO | 0.30s [41] | 0.34s [41] | TO | TO | 3.00s [41] |
| L01 s001 t016 h1 | 0.48s [83] | 0.59s [83] | 1.71s [83] | TO | 0.57s [83] | 0.65s [83] | TO | TO | 0.52s [83] |
| L01 s010 t008 h2 | 0.20s [28] | 0.20s [28] | 0.75s [28] | TO | 0.18s [28] | 0.26s [28] | TO | TO | 0.21s [28] |
| L01 s018 t002 h2 | 0.41s [58] | 0.40s [58] | 1.44s [58] | TO | 0.38s [58] | 0.47s [60] | TO | TO | TO |
| L01 s011 t010 h2 | 0.10s [14] | 0.10s [14] | 0.34s [14] | TO | 0.10s [14] | 0.11s [14] | TO | 0.60s [14] | 0.09s [14] |
| L01 s016 t002 h2 | 0.49s [70] | 0.50s [72] | 1.79s [72] | TO | 0.41s [70] | 0.54s [74] | TO | TO | TO |
| L01 s016 t009 h2 | 0.29s [42] | 0.28s [42] | 1.05s [42] | TO | 0.34s [42] | 0.37s [42] | TO | 94s [42] | 8.49s [42] |
| L01 s013 t014 h2 | 0.13s [14] | 0.12s [14] | 0.46s [14] | TO | 0.12s [14] | 0.15s [14] | 271s [14] | 0.84s [14] | 0.09s [14] |
| L01 s012 t001 h2 | 0.26s [34] | 0.28s [34] | 1.09s [34] | TO | 0.24s [34] | 0.29s [34] | TO | 5.63s [34] | 0.20s [34] |
| L01 s014 t011 h2 | 0.41s [58] | 0.41s [58] | 1.36s [58] | TO | 0.44s [58] | 0.47s [58] | TO | TO | 11s [58] |

### scan-comb / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 0.05s [4] | 0.05s [4] | 0.18s [4] | 0.74s [4] | 0.06s [4] | 0.06s [4] | 0.42s [4] | 0.17s [4] | 0.06s [4] |
| L03 t018 | 0.12s [27] | 0.13s [27] | 0.48s [27] | TO | 0.11s [27] | 0.14s [36] | TO | 3.14s [25] | 2.49s [25] |
| L08 t001 | 0.19s [21] | 0.18s [21] | 0.52s [20] | MO | 0.19s [21] | 0.26s [22] | TO | 1.94s [20] | 1.22s [20] |
| L06 t005 | 0.10s [24] | 0.10s [24] | 0.47s [24] | TO | 0.11s [24] | 0.10s [24] | TO | TO | 0.07s [24] |
| L06 t002 | 0.09s [25] | 0.09s [25] | 0.44s [25] | TO | 0.08s [25] | 0.08s [25] | TO | TO | 0.05s [25] |
| L02 t005 | 0.34s [29] | 0.37s [29] | 1.20s [29] | TO | 0.53s [29] | 1.52s [30] | TO | TO | 27s [29] |
| L07 t001 | 0.18s [33] | 0.18s [33] | 0.63s [33] | TO | 0.20s [33] | 0.18s [33] | TO | 11s [33] | 0.51s [33] |
| L08 t003 | 0.25s [25] | 0.25s [25] | 0.70s [25] | MO | 0.25s [25] | 0.30s [25] | TO | TO | 0.24s [25] |
| L03 t002 | 4.40s [38] | 1.92s [37] | 4.76s [37] | TO | 2.99s [31] | 3.83s [34] | TO | TO | 108s [28] |
| L07 t008 | 0.28s [41] | 0.27s [41] | 1.01s [41] | TO | 0.28s [41] | 0.25s [41] | TO | 134s [41] | 0.21s [41] |
| L09 t005 | 0.23s [24] | 0.22s [24] | 0.64s [24] | TO | 0.23s [24] | 0.32s [24] | TO | 80s [24] | 0.23s [24] |
| L11 t115 | incomplete | incomplete | incomplete | TO | incomplete | incomplete | TO | incomplete | incomplete |
| L11 t168 | incomplete | incomplete | incomplete | TO | incomplete | incomplete | TO | incomplete | incomplete |
| L09 t003 | 0.20s [23] | 0.20s [23] | 0.60s [23] | TO | 0.21s [23] | 0.26s [23] | TO | 128s [23] | 0.17s [23] |
| L13 t006 | 0.34s [34] | 0.34s [34] | 0.66s [34] | TO | 0.34s [36] | 0.40s [34] | TO | 9.35s [34] | 0.34s [34] |
| L14 t016 | 0.61s [89] | 1.81s [93] | 5.67s [89] | TO | 0.77s [88] | 4.43s [92] | TO | TO | TO |
| L14 t006 | 0.56s [76] | 1.59s [80] | 5.09s [76] | TO | 0.59s [75] | 2.66s [79] | TO | TO | TO |
| L13 t003 | 14s [99] | 1.22s [60] | 4.02s [60] | TO | 113s [93] | 174s [125] | TO | TO | TO |

### scan-sep / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 0.03s [3] | 0.03s [3] | 0.12s [3] | 0.13s [3] | 0.03s [3] | 0.03s [3] | 0.12s [3] | 0.08s [3] | 0.05s [3] |
| L01 s004 t005 h1 | 0.04s [6] | 0.04s [6] | 0.13s [6] | 0.18s [4] | 0.04s [6] | 0.04s [6] | 0.16s [4] | 0.14s [4] | 0.11s [4] |
| L01 s007 t005 h1 | 0.04s [4] | 0.03s [4] | 0.12s [4] | 0.09s [4] | 0.04s [4] | 0.04s [4] | 0.22s [4] | 0.31s [4] | 0.11s [4] |
| L01 s005 t004 h1 | 0.05s [7] | 0.05s [7] | 0.19s [7] | 4.67s [7] | 0.05s [7] | 0.06s [7] | 4.06s [7] | 2.39s [7] | 2.20s [7] |
| L01 s007 t004 h1 | 0.07s [8] | 0.07s [8] | 0.23s [8] | 16s [8] | 0.07s [8] | 0.08s [8] | 14s [8] | 19s [8] | 7.76s [8] |
| L01 s018 t008 h2 | 0.08s [11] | 0.08s [11] | 0.23s [11] | 20s [9] | 0.08s [11] | 0.08s [9] | 17s [9] | 16s [9] | 10s [9] |
| L01 s012 t010 h2 | 0.08s [10] | 0.09s [10] | 0.28s [10] | 61s [10] | 0.08s [10] | 0.09s [10] | 50s [10] | 38s [10] | 22s [10] |
| L01 s003 t016 h1 | 0.28s [33] | 0.27s [33] | 0.86s [33] | TO | 0.26s [33] | 0.30s [33] | TO | TO | TO |
| L01 s003 t017 h1 | 0.29s [34] | 0.29s [34] | 0.84s [34] | TO | 0.27s [34] | 0.34s [34] | TO | TO | TO |
| L01 s013 t018 h2 | 0.16s [19] | 0.15s [19] | 0.46s [19] | TO | 0.15s [19] | 0.17s [19] | TO | TO | TO |
| L01 s009 t017 h1 | 0.35s [43] | 0.36s [43] | 1.03s [43] | TO | 0.33s [43] | 0.38s [43] | TO | TO | TO |
| L01 s017 t013 h2 | 0.13s [16] | 0.13s [16] | 0.38s [16] | TO | 0.13s [16] | 0.15s [16] | TO | TO | TO |
| L01 s005 t014 h1 | 0.45s [55] | 0.43s [55] | 1.23s [55] | TO | 0.43s [55] | 0.50s [55] | TO | TO | TO |
| L01 s002 t013 h1 | 0.48s [57] | 0.48s [57] | 1.33s [57] | TO | 0.47s [57] | 0.57s [57] | TO | TO | TO |
| L01 s008 t011 h1 | 0.31s [41] | 0.32s [41] | 0.95s [41] | TO | 0.32s [41] | 0.40s [41] | TO | TO | TO |
| L01 s001 t016 h1 | 0.70s [83] | 0.70s [83] | 1.94s [83] | TO | 0.70s [83] | 0.82s [83] | TO | TO | TO |
| L01 s010 t008 h2 | 0.20s [28] | 0.20s [28] | 0.59s [28] | TO | 0.21s [28] | 0.25s [28] | TO | TO | TO |
| L01 s018 t002 h2 | 0.48s [60] | 0.48s [60] | 1.38s [60] | TO | 0.48s [60] | 0.55s [60] | TO | TO | TO |
| L01 s011 t010 h2 | 0.12s [14] | 0.12s [14] | 0.34s [14] | TO | 0.13s [14] | 0.15s [14] | TO | TO | TO |
| L01 s016 t002 h2 | 0.56s [74] | 0.58s [74] | 1.59s [74] | TO | 0.58s [74] | 0.70s [74] | TO | TO | TO |
| L01 s016 t009 h2 | 0.33s [44] | 0.34s [44] | 0.91s [44] | TO | 0.34s [44] | 0.40s [42] | TO | TO | TO |
| L01 s013 t014 h2 | 0.11s [14] | 0.11s [14] | 0.34s [14] | TO | 0.11s [14] | 0.12s [14] | TO | TO | TO |
| L01 s012 t001 h2 | 0.27s [34] | 0.27s [34] | 0.75s [34] | TO | 0.25s [34] | 0.30s [34] | TO | TO | TO |
| L01 s014 t011 h2 | 0.46s [60] | 0.46s [60] | 1.28s [60] | TO | 0.44s [60] | 0.53s [58] | TO | TO | TO |

### scan-sep / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 0.02s [4] | 0.02s [4] | 0.09s [4] | 0.22s [4] | 0.03s [4] | 0.02s [4] | 0.18s [4] | 0.22s [4] | 0.09s [4] |
| L03 t018 | 0.33s [36] | 0.34s [36] | 0.88s [36] | TO | 0.32s [36] | 0.39s [36] | TO | TO | TO |
| L08 t001 | TO | 6.36s [68] | 21s [68] | TO | 282s [21] | 15s [65] | TO | TO | TO |
| L06 t005 | 0.23s [24] | 0.20s [24] | 0.43s [24] | TO | 0.23s [24] | 0.28s [24] | TO | TO | TO |
| L06 t002 | 0.19s [25] | 0.20s [25] | 0.42s [25] | TO | 0.19s [25] | 0.24s [25] | TO | TO | TO |
| L02 t005 | 0.70s [30] | 1.95s [30] | 11s [30] | TO | 1.93s [30] | 1.22s [30] | TO | TO | TO |
| L07 t001 | 0.25s [33] | 0.25s [33] | 0.71s [33] | TO | 0.25s [33] | 0.30s [33] | TO | TO | TO |
| L08 t003 | 0.22s [25] | 0.23s [25] | 0.65s [25] | TO | 0.22s [25] | 0.26s [25] | TO | TO | TO |
| L03 t002 | 0.79s [39] | TO | TO | TO | 0.94s [39] | 1.50s [41] | TO | TO | TO |
| L07 t008 | 0.35s [41] | 0.35s [41] | 1.01s [41] | TO | 0.35s [41] | 0.42s [41] | TO | TO | TO |
| L09 t005 | 0.23s [24] | 0.22s [24] | 0.68s [24] | TO | 0.22s [24] | 0.27s [24] | TO | TO | TO |
| L11 t115 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L11 t168 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L09 t003 | 0.21s [23] | 0.21s [23] | 0.65s [23] | TO | 0.21s [23] | 0.27s [23] | TO | TO | TO |
| L13 t006 | 0.47s [34] | 0.35s [34] | 0.84s [34] | TO | 0.49s [34] | 0.60s [34] | TO | TO | TO |
| L14 t016 | 2.17s [91] | 39s [108] | 119s [114] | TO | 16s [90] | 58s [90] | TO | TO | TO |
| L14 t006 | 1.93s [78] | 37s [95] | 108s [101] | TO | 16s [77] | 56s [77] | TO | TO | TO |
| L13 t003 | TO | TO | TO | TO | TO | TO | TO | TO | TO |

### orderfree-comb / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 0.04s [3] | 0.04s [3] | 0.08s [3] | 0.29s [3] | 0.04s [3] | 0.04s [3] | 0.15s [3] | 0.06s [3] | 0.05s [3] |
| L01 s004 t005 h1 | 0.06s [4] | 0.05s [4] | 0.08s [4] | 0.12s [4] | 0.06s [4] | 0.04s [4] | 0.21s [4] | 0.08s [4] | 0.05s [4] |
| L01 s007 t005 h1 | 0.04s [4] | 0.05s [4] | 0.09s [4] | 0.63s [4] | 0.05s [4] | 0.05s [4] | 0.35s [4] | 0.15s [4] | 0.09s [4] |
| L01 s005 t004 h1 | 0.07s [7] | 0.08s [7] | 0.14s [7] | 7.55s [7] | 0.08s [7] | 0.07s [7] | 5.26s [7] | 0.27s [7] | 0.08s [7] |
| L01 s007 t004 h1 | 0.08s [8] | 0.09s [8] | 0.15s [8] | 35s [8] | 0.08s [8] | 0.09s [8] | 21s [8] | 0.37s [8] | 0.10s [8] |
| L01 s018 t008 h2 | 0.14s [11] | 0.14s [11] | 0.24s [11] | 42s [9] | 0.15s [11] | 0.15s [9] | 25s [9] | 0.43s [9] | 0.13s [9] |
| L01 s012 t010 h2 | 0.09s [10] | 0.09s [10] | 0.16s [10] | 68s [11] | 0.09s [10] | 0.09s [10] | 38s [10] | 0.29s [10] | 0.09s [10] |
| L01 s003 t016 h1 | 0.34s [33] | 0.33s [33] | 0.58s [33] | TO | 0.34s [33] | 0.38s [33] | TO | 6.18s [33] | 0.34s [33] |
| L01 s003 t017 h1 | 0.36s [34] | 0.37s [34] | 0.64s [34] | TO | 0.35s [34] | 0.39s [34] | TO | 7.21s [34] | 0.36s [34] |
| L01 s013 t018 h2 | 0.17s [19] | 0.18s [19] | 0.29s [19] | TO | 0.18s [19] | 0.18s [19] | TO | 24s [19] | 0.16s [19] |
| L01 s009 t017 h1 | 0.43s [43] | 0.43s [43] | 0.76s [43] | TO | 0.43s [43] | 0.49s [43] | TO | 277s [43] | 0.43s [43] |
| L01 s017 t013 h2 | 0.18s [16] | 0.18s [16] | 0.31s [16] | TO | 0.18s [16] | 0.21s [16] | TO | 0.99s [16] | 0.17s [16] |
| L01 s005 t014 h1 | 0.58s [55] | 0.55s [55] | 0.91s [55] | TO | 0.58s [55] | 0.63s [55] | TO | TO | 0.54s [55] |
| L01 s002 t013 h1 | 0.56s [55] | 0.60s [57] | 0.94s [57] | TO | 0.59s [55] | 0.69s [57] | TO | TO | 0.54s [55] |
| L01 s008 t011 h1 | 0.43s [41] | 0.42s [41] | 0.67s [41] | TO | 0.44s [41] | 0.52s [41] | TO | TO | 4.37s [41] |
| L01 s001 t016 h1 | 0.89s [83] | 0.88s [83] | 1.49s [83] | TO | 0.91s [83] | 1.03s [83] | TO | TO | 0.90s [83] |
| L01 s010 t008 h2 | 0.29s [28] | 0.29s [28] | 0.48s [28] | TO | 0.29s [28] | 0.34s [28] | TO | TO | 0.31s [28] |
| L01 s018 t002 h2 | 0.61s [58] | 0.59s [58] | 0.98s [58] | TO | 0.63s [58] | 0.72s [60] | TO | TO | TO |
| L01 s011 t010 h2 | 0.13s [14] | 0.12s [14] | 0.22s [14] | TO | 0.12s [14] | 0.14s [14] | TO | 0.97s [14] | 0.13s [14] |
| L01 s016 t002 h2 | 0.73s [70] | 0.74s [72] | 1.22s [72] | TO | 0.72s [70] | 0.92s [74] | TO | TO | TO |
| L01 s016 t009 h2 | 0.43s [42] | 0.43s [42] | 0.72s [42] | TO | 0.43s [42] | 0.51s [42] | TO | 212s [42] | 18s [42] |
| L01 s013 t014 h2 | 0.16s [14] | 0.16s [14] | 0.28s [14] | TO | 0.16s [14] | 0.18s [14] | TO | 1.63s [14] | 0.15s [14] |
| L01 s012 t001 h2 | 0.35s [34] | 0.36s [34] | 0.61s [34] | TO | 0.36s [34] | 0.41s [34] | TO | 13s [34] | 0.35s [34] |
| L01 s014 t011 h2 | 0.60s [58] | 0.62s [58] | 0.98s [58] | TO | 0.61s [58] | 0.69s [58] | TO | TO | 19s [58] |

### orderfree-comb / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 0.03s [4] | 0.03s [4] | 0.07s [4] | 0.34s [4] | 0.03s [4] | 0.03s [4] | 0.22s [4] | 0.08s [4] | 0.03s [4] |
| L03 t018 | 0.25s [27] | 0.24s [27] | 0.38s [27] | TO | 0.26s [27] | 0.30s [27] | TO | 7.63s [25] | 6.48s [25] |
| L08 t001 | 0.23s [21] | 0.23s [21] | 0.40s [21] | TO | 0.23s [21] | 0.23s [20] | TO | 2.38s [20] | 1.46s [20] |
| L06 t005 | 0.04s [24] | 0.04s [24] | 0.12s [24] | TO | 0.04s [24] | 0.04s [24] | TO | TO | 0.03s [24] |
| L06 t002 | 0.04s [25] | 0.04s [25] | 0.12s [25] | TO | 0.04s [25] | 0.03s [25] | TO | TO | 0.03s [25] |
| L02 t005 | 0.33s [29] | 0.33s [29] | 0.63s [29] | TO | 0.49s [29] | 0.66s [30] | TO | TO | 23s [29] |
| L07 t001 | 0.27s [33] | 0.27s [33] | 0.47s [33] | TO | 0.26s [33] | 0.31s [33] | TO | 17s [33] | 0.83s [33] |
| L08 t003 | 0.28s [25] | 0.29s [25] | 0.46s [25] | TO | 0.30s [25] | 0.31s [25] | TO | TO | 0.29s [25] |
| L03 t002 | 2.08s [28] | 2.32s [37] | 4.29s [37] | TO | 3.40s [28] | 3.42s [28] | TO | TO | 262s [28] |
| L07 t008 | 0.41s [41] | 0.41s [41] | 0.72s [41] | TO | 0.39s [41] | 0.45s [41] | TO | 245s [41] | 0.38s [41] |
| L09 t005 | 0.29s [24] | 0.29s [24] | 0.49s [24] | TO | 0.28s [24] | 0.35s [24] | TO | 149s [24] | 0.27s [24] |
| L11 t115 | incomplete | incomplete | incomplete | TO | incomplete | incomplete | TO | incomplete | incomplete |
| L11 t168 | incomplete | incomplete | incomplete | TO | incomplete | incomplete | TO | incomplete | incomplete |
| L09 t003 | 0.26s [23] | 0.26s [23] | 0.46s [23] | TO | 0.25s [23] | 0.29s [23] | TO | 276s [23] | 0.24s [23] |
| L13 t006 | 0.64s [34] | 0.67s [34] | 0.62s [34] | TO | 0.64s [36] | 0.77s [34] | TO | 28s [34] | 0.70s [34] |
| L14 t016 | 0.89s [89] | 0.77s [89] | 1.21s [89] | TO | 0.99s [89] | 1.25s [90] | TO | TO | TO |
| L14 t006 | 0.73s [76] | 0.62s [76] | 0.95s [76] | TO | 0.83s [76] | 1.10s [77] | TO | TO | TO |
| L13 t003 | 1.35s [58] | 1.14s [58] | 1.87s [59] | TO | 3.17s [57] | 1.87s [60] | TO | TO | TO |

### orderfree-sep / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 0.21s [3] | 0.21s [3] | 0.28s [3] | 0.91s [3] | 0.21s [3] | 0.23s [3] | 0.90s [3] | 0.47s [3] | 0.35s [3] |
| L01 s004 t005 h1 | 0.28s [4] | 0.23s [4] | 0.29s [4] | 1.37s [4] | 0.28s [4] | 0.30s [6] | 1.36s [4] | 0.86s [4] | 0.68s [4] |
| L01 s007 t005 h1 | 0.23s [4] | 0.23s [4] | 0.29s [4] | 0.61s [4] | 0.23s [4] | 0.25s [4] | 1.79s [4] | 1.78s [4] | 0.66s [4] |
| L01 s005 t004 h1 | 0.43s [7] | 0.41s [7] | 0.54s [7] | 34s [7] | 0.43s [7] | 0.47s [7] | 34s [7] | 3.93s [7] | 2.39s [7] |
| L01 s007 t004 h1 | 0.44s [8] | 0.45s [8] | 0.59s [8] | 112s [8] | 0.45s [8] | 0.55s [8] | 110s [8] | 42s [8] | 22s [8] |
| L01 s018 t008 h2 | 0.61s [11] | 0.61s [11] | 0.69s [11] | 149s [10] | 0.57s [11] | 0.63s [9] | 146s [9] | 61s [9] | 61s [9] |
| L01 s012 t010 h2 | 0.58s [10] | 0.56s [10] | 0.68s [10] | TO | 0.57s [10] | 0.69s [10] | TO | 105s [10] | 62s [10] |
| L01 s003 t016 h1 | 1.85s [33] | 1.86s [33] | 2.24s [33] | TO | 1.84s [33] | 2.31s [33] | TO | TO | TO |
| L01 s003 t017 h1 | 1.91s [34] | 1.92s [34] | 2.27s [34] | TO | 1.88s [34] | 2.39s [34] | TO | TO | TO |
| L01 s013 t018 h2 | 1.06s [19] | 1.08s [19] | 1.24s [19] | TO | 1.07s [19] | 1.28s [19] | TO | TO | TO |
| L01 s009 t017 h1 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L01 s017 t013 h2 | 0.89s [16] | 0.89s [16] | 1.06s [16] | TO | 0.86s [16] | 1.12s [16] | TO | TO | TO |
| L01 s005 t014 h1 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L01 s002 t013 h1 | 4.82s [57] | 3.37s [55] | 4.07s [55] | TO | 4.69s [55] | 3.93s [57] | TO | TO | TO |
| L01 s008 t011 h1 | 2.20s [41] | 2.24s [41] | 2.83s [41] | TO | 2.21s [41] | 2.90s [41] | TO | TO | TO |
| L01 s001 t016 h1 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L01 s010 t008 h2 | 1.46s [28] | 1.44s [28] | 1.80s [28] | TO | 1.47s [28] | 1.80s [28] | TO | TO | TO |
| L01 s018 t002 h2 | 3.37s [58] | 3.15s [60] | 3.70s [60] | TO | 3.39s [58] | 3.98s [60] | TO | TO | TO |
| L01 s011 t010 h2 | 0.85s [14] | 0.83s [14] | 0.98s [14] | TO | 0.84s [14] | 1.14s [14] | TO | TO | TO |
| L01 s016 t002 h2 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L01 s016 t009 h2 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L01 s013 t014 h2 | 0.81s [14] | 0.79s [14] | 0.90s [14] | TO | 0.81s [14] | 0.96s [14] | TO | TO | TO |
| L01 s012 t001 h2 | 1.82s [34] | 1.86s [34] | 2.19s [34] | TO | 1.80s [34] | 2.25s [34] | TO | TO | TO |
| L01 s014 t011 h2 | TO | TO | TO | TO | TO | TO | TO | TO | TO |

### orderfree-sep / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 0.16s [4] | 0.17s [4] | 0.27s [4] | 1.61s [4] | 0.16s [4] | 0.18s [4] | 1.56s [4] | 1.14s [4] | 0.66s [4] |
| L03 t018 | 4.49s [31] | 6.72s [28] | 8.14s [27] | TO | 12s [27] | 3.16s [36] | TO | TO | TO |
| L08 t001 | TO | TO | TO | TO | 50s [30] | TO | TO | TO | TO |
| L06 t005 | 0.08s [24] | 0.08s [24] | 0.17s [24] | TO | 0.08s [24] | 0.10s [24] | TO | TO | TO |
| L06 t002 | 0.09s [25] | 0.09s [25] | 0.20s [25] | TO | 0.09s [25] | 0.10s [25] | TO | TO | TO |
| L02 t005 | 1.87s [29] | 2.01s [29] | 3.90s [29] | TO | 2.71s [29] | 8.05s [29] | TO | TO | TO |
| L07 t001 | 1.62s [33] | 1.63s [33] | 1.99s [33] | TO | 1.59s [33] | 2.08s [33] | TO | TO | TO |
| L08 t003 | 1.34s [25] | 1.32s [25] | 1.62s [25] | TO | 1.31s [25] | 1.53s [25] | TO | TO | TO |
| L03 t002 | 94s [30] | 18s [34] | 15s [31] | TO | 93s [30] | 16s [43] | TO | TO | TO |
| L07 t008 | 2.24s [41] | 2.20s [41] | 2.79s [41] | TO | 2.20s [41] | 2.81s [41] | TO | TO | TO |
| L09 t005 | 1.49s [24] | 1.46s [24] | 1.76s [24] | TO | 1.46s [24] | 1.82s [24] | TO | TO | TO |
| L11 t115 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L11 t168 | TO | TO | TO | TO | TO | TO | TO | TO | TO |
| L09 t003 | 1.36s [23] | 1.38s [23] | 1.64s [23] | TO | 1.39s [23] | 1.71s [23] | TO | TO | TO |
| L13 t006 | 4.78s [34] | 3.48s [34] | 3.88s [34] | TO | 4.58s [36] | 5.82s [34] | TO | TO | TO |
| L14 t016 | TO | 29s [104] | TO | TO | 62s [94] | 211s [93] | TO | TO | TO |
| L14 t006 | TO | 28s [91] | TO | TO | 60s [81] | 209s [80] | TO | TO | TO |
| L13 t003 | 63s [65] | TO | TO | TO | 85s [62] | 144s [67] | TO | TO | TO |
