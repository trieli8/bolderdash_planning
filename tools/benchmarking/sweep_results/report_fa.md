# Fast Downward settings sweep

Variant **inv0+fa** (translator options; +fa = forced-action fork). Other variants in the data: inv0 (pick with --variant=NAME).

1728 runs from host(s) m5pro; models: scan-comb, scan-sep, orderfree-comb, orderfree-sep.

- **m5pro**: host=m5pro; cpus=18; ram_gb=48; cpu=Apple M5 Pro; platform=macOS-26.5.2-arm64-arm-64bit-Mach-O; run[results_m5pro_fa.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0

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
| scan-comb | 24/24 | 24/24 | 24/24 | 5/24 (19MO) | 24/24 | 24/24 | 7/24 (17MO) | 14/24 (10MO) | 22/24 (2MO) |
| scan-sep | 24/24 | 24/24 | 24/24 | 4/24 (20MO) | 24/24 | 24/24 | 4/24 (20MO) | 4/24 (20MO) | 6/24 (18MO) |
| orderfree-comb | 24/24 | 24/24 | 24/24 | 7/24 (11MO 6TO) | 24/24 | 24/24 | 7/24 (14MO 3TO) | 15/24 (5MO 4TO) | 22/24 (2MO) |
| orderfree-sep | 17/17 | 17/17 | 17/17 | 4/17 (13MO) | 17/17 | 17/17 | 5/17 (11MO 1TO) | 7/17 (6MO 4TO) | 7/17 (9MO 1TO) |

### bd_levels 02..14

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 16/16 | 16/16 | 16/16 | 1/16 (15MO) | 16/16 | 15/16 (1MO) | 1/16 (15MO) | 5/16 (11MO) | 12/16 (4MO) |
| scan-sep | 14/16 (2MO) | 12/16 (4MO) | 12/16 (4MO) | 1/16 (15MO) | 12/16 (4MO) | 12/16 (4MO) | 1/16 (15MO) | 1/16 (15MO) | 1/16 (15MO) |
| orderfree-comb | 16/16 | 16/16 | 16/16 | 1/16 (11MO 4TO) | 16/16 | 16/16 | 1/16 (12MO 3TO) | 5/16 (9MO 2TO) | 12/16 (4MO) |
| orderfree-sep | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |

## Search effort on tasks every listed config solved (per model)

Geometric mean of search time and expansions over the tasks solved by all configs in the row group; plan quality is the mean of cost / best known optimum.


**scan-comb / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| gbfs-add | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| gbfs-cea | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| gbfs-cg | 0.01s | 67 | 255 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| lama-first | 0.00s | 18 | 0 | 1.01 (n=10, max 1.12) |

**scan-comb / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.27s | 28 | 115 | 1.01 (n=22, max 1.22) |
| gbfs-add | 0.27s | 27 | 116 | 1.01 (n=22, max 1.22) |
| gbfs-cea | 0.67s | 27 | 182 | 1.01 (n=22, max 1.22) |
| wastar3-ff | 0.29s | 28 | 117 | 1.01 (n=22, max 1.22) |
| lama-first | 0.44s | 38 | 144 | 1.02 (n=22, max 1.50) |

**scan-comb / satisficing / other** (15 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.44s | 53 | 265 | 1.01 (n=12, max 1.08) |
| gbfs-add | 0.48s | 56 | 174 | 1.01 (n=12, max 1.08) |
| gbfs-cea | 1.14s | 53 | 224 | 1.01 (n=12, max 1.08) |
| wastar3-ff | 0.44s | 55 | 227 | 1.02 (n=12, max 1.08) |
| lama-first | 0.83s | 104 | 339 | 1.04 (n=12, max 1.44) |

**scan-comb / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.01s | 74 | 0 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.01s | 46 | 0 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.00s | 24 | 0 | 1.00 (n=10, max 1.00) |

**scan-comb / optimal / l1** (14 common tasks; left out for low coverage: lazy-astar-blind)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax | 1.66s | 186 | 973 | 1.00 (n=14, max 1.00) |
| lazy-astar-hmax-tb | 0.23s | 20 | 92 | 1.00 (n=14, max 1.00) |

**scan-comb / optimal / other** (12 common tasks; left out for low coverage: lazy-astar-blind, lazy-astar-hmax)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax-tb | 0.79s | 112 | 2015 | 1.00 (n=12, max 1.00) |

**scan-sep / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.00s | 15 | 54 | 1.01 (n=10, max 1.12) |
| gbfs-add | 0.00s | 15 | 54 | 1.01 (n=10, max 1.12) |
| gbfs-cea | 0.01s | 15 | 87 | 1.01 (n=10, max 1.12) |
| gbfs-cg | 0.01s | 44 | 402 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.00s | 16 | 54 | 1.00 (n=10, max 1.00) |
| lama-first | 0.00s | 19 | 65 | 1.01 (n=10, max 1.12) |

**scan-sep / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.77s | 29 | 219 | 1.04 (n=22, max 1.50) |
| gbfs-add | 0.78s | 29 | 220 | 1.04 (n=22, max 1.50) |
| gbfs-cea | 1.11s | 29 | 266 | 1.04 (n=22, max 1.50) |
| wastar3-ff | 0.77s | 29 | 221 | 1.04 (n=22, max 1.50) |
| lama-first | 1.10s | 41 | 285 | 1.02 (n=22, max 1.50) |

**scan-sep / satisficing / other** (11 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 1.04s | 37 | 261 | 1.04 (n=11, max 1.44) |
| gbfs-add | 1.11s | 40 | 590 | 1.04 (n=11, max 1.44) |
| gbfs-cea | 1.59s | 42 | 909 | 1.04 (n=11, max 1.44) |
| wastar3-ff | 1.15s | 41 | 599 | 1.04 (n=11, max 1.44) |
| lama-first | 1.58s | 56 | 468 | 1.04 (n=11, max 1.44) |

**scan-sep / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.01s | 63 | 57 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.01s | 55 | 67 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.01s | 50 | 70 | 1.00 (n=10, max 1.00) |

**scan-sep / optimal / l1** (4 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 3.06s | 120 | 1705 | 1.00 (n=4, max 1.00) |
| lazy-astar-hmax | 1.81s | 67 | 728 | 1.00 (n=4, max 1.00) |
| lazy-astar-hmax-tb | 1.16s | 43 | 660 | 1.00 (n=4, max 1.00) |

**scan-sep / optimal / other** (1 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 1.69s | 65 | 116 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax | 1.55s | 56 | 142 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax-tb | 0.63s | 23 | 110 | 1.00 (n=1, max 1.00) |

**orderfree-comb / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.00s | 16 | 0 | 1.01 (n=10, max 1.12) |
| gbfs-add | 0.00s | 16 | 0 | 1.01 (n=10, max 1.12) |
| gbfs-cea | 0.00s | 16 | 0 | 1.01 (n=10, max 1.12) |
| gbfs-cg | 0.01s | 57 | 222 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.00s | 16 | 0 | 1.02 (n=10, max 1.25) |
| lama-first | 0.00s | 18 | 0 | 1.01 (n=10, max 1.12) |

**orderfree-comb / satisficing / l1** (24 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.22s | 28 | 105 | 1.01 (n=22, max 1.22) |
| gbfs-add | 0.21s | 27 | 109 | 1.01 (n=22, max 1.22) |
| gbfs-cea | 0.39s | 27 | 138 | 1.01 (n=22, max 1.22) |
| wastar3-ff | 0.21s | 28 | 106 | 1.01 (n=22, max 1.22) |
| lama-first | 0.26s | 38 | 111 | 1.00 (n=22, max 1.04) |

**orderfree-comb / satisficing / other** (16 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.29s | 52 | 114 | 1.01 (n=12, max 1.08) |
| gbfs-add | 0.28s | 50 | 121 | 1.01 (n=12, max 1.08) |
| gbfs-cea | 0.50s | 50 | 147 | 1.01 (n=12, max 1.08) |
| wastar3-ff | 0.33s | 60 | 143 | 1.02 (n=12, max 1.08) |
| lama-first | 0.38s | 81 | 147 | 1.01 (n=12, max 1.08) |

**orderfree-comb / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.00s | 62 | 0 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.00s | 42 | 0 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.00s | 23 | 0 | 1.00 (n=10, max 1.00) |

**orderfree-comb / optimal / l1** (15 common tasks; left out for low coverage: lazy-astar-blind)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax | 1.72s | 260 | 2780 | 1.00 (n=15, max 1.00) |
| lazy-astar-hmax-tb | 0.19s | 29 | 479 | 1.00 (n=15, max 1.00) |

**orderfree-comb / optimal / other** (12 common tasks; left out for low coverage: lazy-astar-blind, lazy-astar-hmax)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-hmax-tb | 0.46s | 109 | 539 | 1.00 (n=12, max 1.00) |

**orderfree-sep / satisficing / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.00s | 15 | 61 | 1.01 (n=10, max 1.12) |
| gbfs-add | 0.00s | 15 | 60 | 1.01 (n=10, max 1.12) |
| gbfs-cea | 0.01s | 15 | 84 | 1.01 (n=10, max 1.12) |
| gbfs-cg | 0.01s | 45 | 807 | 1.00 (n=10, max 1.00) |
| wastar3-ff | 0.00s | 16 | 61 | 1.00 (n=10, max 1.00) |
| lama-first | 0.00s | 19 | 62 | 1.01 (n=10, max 1.12) |

**orderfree-sep / satisficing / l1** (17 common tasks; left out for low coverage: gbfs-cg)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.97s | 22 | 175 | 1.02 (n=16, max 1.22) |
| gbfs-add | 0.92s | 21 | 142 | 1.01 (n=16, max 1.22) |
| gbfs-cea | 1.13s | 21 | 188 | 1.01 (n=16, max 1.22) |
| wastar3-ff | 0.95s | 22 | 177 | 1.01 (n=16, max 1.22) |
| lama-first | 1.23s | 29 | 158 | 1.03 (n=16, max 1.50) |

**orderfree-sep / satisficing / other** (1 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| gbfs-ff | 0.17s | 5 | 104 | 1.00 (n=1, max 1.00) |
| gbfs-add | 0.16s | 5 | 102 | 1.00 (n=1, max 1.00) |
| gbfs-cea | 0.32s | 7 | 144 | 1.00 (n=1, max 1.00) |
| gbfs-cg | 2.66s | 81 | 2266 | 1.00 (n=1, max 1.00) |
| wastar3-ff | 0.17s | 5 | 100 | 1.00 (n=1, max 1.00) |
| lama-first | 0.20s | 6 | 96 | 1.00 (n=1, max 1.00) |

**orderfree-sep / optimal / small** (10 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 0.01s | 63 | 41 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax | 0.01s | 49 | 57 | 1.00 (n=10, max 1.00) |
| lazy-astar-hmax-tb | 0.01s | 36 | 62 | 1.00 (n=10, max 1.00) |

**orderfree-sep / optimal / l1** (5 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 10s | 247 | 3000 | 1.00 (n=5, max 1.00) |
| lazy-astar-hmax | 4.28s | 95 | 1142 | 1.00 (n=5, max 1.00) |
| lazy-astar-hmax-tb | 2.45s | 55 | 651 | 1.00 (n=5, max 1.00) |

**orderfree-sep / optimal / other** (1 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lazy-astar-blind | 2.66s | 81 | 79 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax | 1.93s | 56 | 105 | 1.00 (n=1, max 1.00) |
| lazy-astar-hmax-tb | 1.02s | 30 | 93 | 1.00 (n=1, max 1.00) |

## Optimal cost agreement

44 problems solved optimally; 44 of them by more than one model. All optimal costs agree across configs and models.

## Translation (per model and problem set)

| model | set | problems | translate s (median / max) | operators (median / max) | translate failures |
|---|---|---|---|---|---|
| scan-comb | small | 12 | 0.5 / 1.2 | 449 / 2262 | 0 |
| scan-comb | l1 | 24 | 11.2 / 11.6 | 21k / 21k | 0 |
| scan-comb | other | 18 | 8.1 / 11.4 | 16k / 22k | 0 |
| scan-sep | small | 12 | 0.3 / 2.6 | 2289 / 19k | 0 |
| scan-sep | l1 | 24 | 5.9 / 6.1 | 36k / 36k | 0 |
| scan-sep | other | 18 | 6.6 / 7.0 | 39k / 40k | 0 |
| orderfree-comb | small | 12 | 0.5 / 1.7 | 494 / 3207 | 0 |
| orderfree-comb | l1 | 24 | 8.9 / 9.9 | 23k / 23k | 0 |
| orderfree-comb | other | 18 | 6.6 / 9.7 | 18k / 24k | 0 |
| orderfree-sep | small | 12 | 0.3 / 2.3 | 1806 / 15k | 0 |
| orderfree-sep | l1 | 17 | 5.5 / 6.0 | 30k / 30k | 0 |
| orderfree-sep | other | 1 | 6.3 / 6.3 | 32k / 32k | 0 |

## Per-problem detail (search time, cost)


### scan-comb / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 0.13s [3] | 0.12s [3] | 0.22s [3] | 0.88s [3] | 0.14s [3] | 0.15s [3] | 0.72s [3] | 0.23s [3] | 0.17s [3] |
| L01 s004 t005 h1 | 0.15s [4] | 0.12s [4] | 0.21s [4] | 0.53s [4] | 0.17s [4] | 0.11s [6] | 0.88s [4] | 0.31s [4] | 0.15s [4] |
| L01 s007 t005 h1 | 0.11s [4] | 0.12s [4] | 0.20s [4] | 2.08s [5] | 0.12s [4] | 0.14s [4] | 1.69s [4] | 0.62s [4] | 0.35s [4] |
| L01 s005 t004 h1 | 0.13s [7] | 0.15s [7] | 0.28s [7] | 10s [7] | 0.14s [7] | 0.15s [7] | 6.54s [7] | 0.66s [7] | 0.19s [7] |
| L01 s007 t004 h1 | 0.14s [8] | 0.13s [8] | 0.25s [8] | 51s [8] | 0.14s [8] | 0.22s [8] | 27s [8] | 0.92s [8] | 0.24s [8] |
| L01 s018 t008 h2 | 0.19s [11] | 0.18s [11] | 0.43s [11] | MO | 0.20s [11] | 0.36s [9] | 36s [9] | 0.99s [9] | 0.33s [9] |
| L01 s003 t016 h1 | 0.29s [33] | 0.30s [33] | 0.90s [33] | MO | 0.31s [33] | 0.53s [33] | MO | 7.45s [33] | 0.35s [33] |
| L01 s003 t017 h1 | 0.31s [34] | 0.31s [34] | 0.92s [34] | MO | 0.33s [34] | 0.61s [34] | MO | 7.95s [34] | 0.34s [34] |
| L01 s012 t010 h2 | 0.12s [10] | 0.12s [10] | 0.26s [10] | MO | 0.13s [10] | 0.15s [10] | 48s [10] | 0.51s [10] | 0.12s [10] |
| L01 s013 t018 h2 | 0.18s [19] | 0.18s [19] | 0.48s [19] | MO | 0.17s [19] | 0.30s [19] | MO | 31s [19] | 0.17s [19] |
| L01 s009 t017 h1 | 0.35s [43] | 0.36s [43] | 1.05s [43] | MO | 0.37s [43] | 0.67s [43] | MO | MO | 0.36s [43] |
| L01 s010 t008 h2 | 0.29s [28] | 0.29s [28] | 0.80s [28] | MO | 0.31s [28] | 0.58s [28] | MO | MO | 0.43s [28] |
| L01 s002 t013 h1 | 0.50s [55] | 0.47s [57] | 1.28s [57] | MO | 0.55s [55] | 0.87s [57] | MO | MO | 0.59s [55] |
| L01 s005 t014 h1 | 0.46s [55] | 0.41s [55] | 1.20s [55] | MO | 0.51s [55] | 0.76s [55] | MO | MO | 0.54s [55] |
| L01 s008 t011 h1 | 0.42s [41] | 0.39s [41] | 0.97s [41] | MO | 0.43s [41] | 0.77s [41] | MO | MO | 5.19s [41] |
| L01 s001 t016 h1 | 0.70s [83] | 0.75s [83] | 1.90s [83] | MO | 0.80s [83] | 1.33s [83] | MO | MO | 0.90s [83] |
| L01 s017 t013 h2 | 0.25s [16] | 0.23s [16] | 0.64s [16] | MO | 0.24s [16] | 0.42s [16] | MO | 1.11s [16] | 0.22s [16] |
| L01 s011 t010 h2 | 0.16s [14] | 0.15s [14] | 0.41s [14] | MO | 0.17s [14] | 0.27s [14] | MO | 1.72s [14] | 0.18s [14] |
| L01 s018 t002 h2 | 0.61s [58] | 0.62s [58] | 1.72s [58] | MO | 0.55s [58] | 1.00s [60] | MO | MO | MO |
| L01 s012 t001 h2 | 0.36s [34] | 0.35s [34] | 1.01s [34] | MO | 0.38s [34] | 0.69s [34] | MO | 13s [34] | 0.37s [34] |
| L01 s013 t014 h2 | 0.19s [14] | 0.18s [14] | 0.49s [14] | MO | 0.22s [14] | 0.37s [14] | MO | 2.05s [14] | 0.17s [14] |
| L01 s016 t009 h2 | 0.47s [42] | 0.46s [42] | 1.37s [42] | MO | 0.50s [42] | 0.86s [42] | MO | MO | 19s [42] |
| L01 s014 t011 h2 | 0.62s [58] | 0.65s [58] | 1.76s [58] | MO | 0.66s [58] | 1.02s [58] | MO | MO | 22s [58] |
| L01 s016 t002 h2 | 0.69s [70] | 0.66s [72] | 1.89s [72] | MO | 0.72s [70] | 1.25s [74] | MO | MO | MO |

### scan-comb / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 0.11s [4] | 0.11s [4] | 0.22s [4] | 1.60s [4] | 0.11s [4] | 0.12s [4] | 1.28s [4] | 0.40s [4] | 0.14s [4] |
| L07 t001 | 0.29s [33] | 0.29s [33] | 0.88s [33] | MO | 0.28s [33] | 0.33s [33] | MO | 23s [33] | 0.97s [33] |
| L03 t018 | 0.17s [27] | 0.15s [27] | 0.49s [27] | MO | 0.17s [27] | 0.27s [36] | MO | 7.38s [25] | 5.77s [25] |
| L08 t001 | 0.35s [21] | 0.31s [21] | 0.64s [20] | MO | 0.32s [21] | 0.47s [20] | MO | 4.63s [20] | 3.16s [20] |
| L06 t005 | 0.18s [24] | 0.17s [24] | 0.59s [24] | MO | 0.17s [24] | 0.24s [24] | MO | MO | 0.15s [24] |
| L06 t002 | 0.14s [25] | 0.14s [25] | 0.47s [25] | MO | 0.14s [25] | 0.18s [25] | MO | MO | 0.12s [25] |
| L02 t005 | 0.66s [29] | 0.61s [29] | 1.38s [29] | MO | 1.09s [29] | 4.26s [30] | MO | MO | 73s [29] |
| L11 t115 | incomplete | incomplete | incomplete | MO | incomplete | incomplete | MO | incomplete | incomplete |
| L08 t003 | 0.49s [25] | 0.45s [25] | 0.94s [25] | MO | 0.43s [25] | 0.71s [25] | MO | MO | 0.49s [25] |
| L11 t168 | incomplete | incomplete | incomplete | MO | incomplete | incomplete | MO | incomplete | incomplete |
| L07 t008 | 0.38s [41] | 0.37s [41] | 1.11s [41] | MO | 0.35s [41] | 0.45s [41] | MO | MO | 0.33s [41] |
| L09 t005 | 0.39s [24] | 0.37s [24] | 0.87s [24] | MO | 0.39s [24] | 0.72s [24] | MO | MO | 0.45s [24] |
| L09 t003 | 0.34s [23] | 0.35s [23] | 0.78s [23] | MO | 0.35s [23] | 0.60s [23] | MO | MO | 0.33s [23] |
| L03 t002 | 8.18s [38] | 3.58s [37] | 6.40s [37] | MO | 6.55s [31] | 8.14s [34] | MO | MO | MO |
| L13 t006 | 0.76s [34] | 0.73s [34] | 1.17s [34] | MO | 0.60s [36] | 0.98s [34] | MO | 24s [34] | 0.81s [34] |
| L14 t006 | 0.92s [76] | 3.20s [80] | 7.14s [76] | MO | 1.08s [75] | 6.07s [79] | MO | MO | MO |
| L14 t016 | 1.05s [89] | 3.47s [93] | 7.88s [89] | MO | 1.25s [88] | 9.40s [92] | MO | MO | MO |
| L13 t003 | 24s [99] | 2.59s [60] | 6.16s [60] | MO | 151s [93] | MO | MO | MO | MO |

### scan-sep / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 0.15s [3] | 0.16s [3] | 0.25s [3] | 0.90s [3] | 0.16s [3] | 0.18s [3] | 0.87s [3] | 0.44s [3] | 0.31s [3] |
| L01 s004 t005 h1 | 0.16s [6] | 0.16s [6] | 0.24s [6] | 1.45s [4] | 0.16s [6] | 0.18s [6] | 1.41s [4] | 0.86s [4] | 0.69s [4] |
| L01 s007 t005 h1 | 0.16s [4] | 0.15s [4] | 0.24s [4] | 0.58s [4] | 0.16s [4] | 0.18s [4] | 1.94s [4] | 1.85s [4] | 0.62s [4] |
| L01 s005 t004 h1 | 0.24s [7] | 0.23s [7] | 0.39s [7] | 38s [7] | 0.24s [7] | 0.33s [7] | 37s [7] | 16s [7] | 14s [7] |
| L01 s007 t004 h1 | 0.28s [8] | 0.29s [8] | 0.47s [8] | MO | 0.29s [8] | 0.42s [8] | MO | MO | 51s [8] |
| L01 s018 t008 h2 | 0.40s [11] | 0.40s [11] | 0.51s [11] | MO | 0.36s [11] | 0.49s [9] | MO | MO | 70s [9] |
| L01 s003 t016 h1 | 1.16s [33] | 1.17s [33] | 1.74s [33] | MO | 1.16s [33] | 1.75s [33] | MO | MO | MO |
| L01 s003 t017 h1 | 1.22s [34] | 1.26s [34] | 1.69s [34] | MO | 1.27s [34] | 1.83s [34] | MO | MO | MO |
| L01 s012 t010 h2 | 0.38s [10] | 0.38s [10] | 0.54s [10] | MO | 0.36s [10] | 0.52s [10] | MO | MO | MO |
| L01 s013 t018 h2 | 0.71s [19] | 0.72s [19] | 0.91s [19] | MO | 0.73s [19] | 1.02s [19] | MO | MO | MO |
| L01 s009 t017 h1 | 1.53s [43] | 1.52s [43] | 2.04s [43] | MO | 1.48s [43] | 2.12s [43] | MO | MO | MO |
| L01 s010 t008 h2 | 0.87s [28] | 0.90s [28] | 1.35s [28] | MO | 0.85s [28] | 1.33s [28] | MO | MO | MO |
| L01 s002 t013 h1 | 1.88s [57] | 1.93s [57] | 2.79s [57] | MO | 1.98s [57] | 3.01s [57] | MO | MO | MO |
| L01 s005 t014 h1 | 1.79s [55] | 1.77s [55] | 2.57s [55] | MO | 1.76s [55] | 2.62s [55] | MO | MO | MO |
| L01 s008 t011 h1 | 1.39s [41] | 1.43s [41] | 2.13s [41] | MO | 1.43s [41] | 2.39s [41] | MO | MO | MO |
| L01 s001 t016 h1 | 2.96s [83] | 2.96s [83] | 4.26s [83] | MO | 3.07s [83] | 4.46s [83] | MO | MO | MO |
| L01 s017 t013 h2 | 0.59s [16] | 0.58s [16] | 0.81s [16] | MO | 0.59s [16] | 0.87s [16] | MO | MO | MO |
| L01 s011 t010 h2 | 0.60s [14] | 0.64s [14] | 0.93s [14] | MO | 0.60s [14] | 0.93s [14] | MO | MO | MO |
| L01 s018 t002 h2 | 1.93s [60] | 1.94s [60] | 2.68s [60] | MO | 1.95s [60] | 2.91s [60] | MO | MO | MO |
| L01 s012 t001 h2 | 1.13s [34] | 1.14s [34] | 1.55s [34] | MO | 1.20s [34] | 1.66s [34] | MO | MO | MO |
| L01 s013 t014 h2 | 0.55s [14] | 0.53s [14] | 0.68s [14] | MO | 0.55s [14] | 0.74s [14] | MO | MO | MO |
| L01 s016 t009 h2 | 1.43s [44] | 1.50s [44] | 1.99s [44] | MO | 1.43s [44] | 2.15s [42] | MO | MO | MO |
| L01 s014 t011 h2 | 1.92s [60] | 1.86s [60] | 2.67s [60] | MO | 1.83s [60] | 2.82s [58] | MO | MO | MO |
| L01 s016 t002 h2 | 2.39s [74] | 2.38s [74] | 3.39s [74] | MO | 2.39s [74] | 3.69s [74] | MO | MO | MO |

### scan-sep / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 0.10s [4] | 0.11s [4] | 0.17s [4] | 1.79s [4] | 0.10s [4] | 0.11s [4] | 1.69s [4] | 1.55s [4] | 0.63s [4] |
| L07 t001 | 1.16s [33] | 1.14s [33] | 1.56s [33] | MO | 1.16s [33] | 1.71s [33] | MO | MO | MO |
| L03 t018 | 1.50s [36] | 1.47s [36] | 1.95s [36] | MO | 1.49s [36] | 2.15s [36] | MO | MO | MO |
| L08 t001 | MO | 38s [68] | 53s [68] | MO | MO | MO | MO | MO | MO |
| L06 t005 | 0.73s [24] | 0.74s [24] | 0.98s [24] | MO | 0.75s [24] | 1.09s [24] | MO | MO | MO |
| L06 t002 | 0.65s [25] | 0.64s [25] | 0.82s [25] | MO | 0.64s [25] | 0.92s [25] | MO | MO | MO |
| L02 t005 | 4.09s [30] | 12s [30] | 27s [30] | MO | 12s [30] | 9.61s [30] | MO | MO | MO |
| L11 t115 | MO | MO | MO | MO | MO | MO | MO | MO | MO |
| L08 t003 | 1.04s [25] | 1.06s [25] | 1.38s [25] | MO | 1.07s [25] | 1.47s [25] | MO | MO | MO |
| L11 t168 | MO | MO | MO | MO | MO | MO | MO | MO | MO |
| L07 t008 | 1.55s [41] | 1.57s [41] | 2.24s [41] | MO | 1.57s [41] | 2.59s [41] | MO | MO | MO |
| L09 t005 | 1.09s [24] | 1.11s [24] | 1.49s [24] | MO | 1.06s [24] | 1.69s [24] | MO | MO | MO |
| L09 t003 | 1.04s [23] | 1.05s [23] | 1.52s [23] | MO | 1.04s [23] | 1.66s [23] | MO | MO | MO |
| L03 t002 | 4.15s [39] | MO | MO | MO | 4.69s [39] | 8.81s [41] | MO | MO | MO |
| L13 t006 | 2.43s [34] | 1.59s [34] | 2.06s [34] | MO | 2.47s [34] | 3.62s [34] | MO | MO | MO |
| L14 t006 | 9.89s [78] | MO | MO | MO | MO | MO | MO | MO | MO |
| L14 t016 | 11s [91] | MO | MO | MO | MO | MO | MO | MO | MO |
| L13 t003 | MO | MO | MO | MO | MO | MO | MO | MO | MO |

### orderfree-comb / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 0.05s [3] | 0.05s [3] | 0.09s [3] | 0.35s [3] | 0.05s [3] | 0.05s [3] | 0.22s [3] | 0.07s [3] | 0.05s [3] |
| L01 s004 t005 h1 | 0.06s [4] | 0.05s [4] | 0.09s [4] | 0.16s [4] | 0.06s [4] | 0.04s [4] | 0.31s [4] | 0.10s [4] | 0.05s [4] |
| L01 s007 t005 h1 | 0.04s [4] | 0.04s [4] | 0.10s [4] | 0.78s [4] | 0.05s [4] | 0.05s [4] | 0.52s [4] | 0.20s [4] | 0.12s [4] |
| L01 s005 t004 h1 | 0.07s [7] | 0.08s [7] | 0.15s [7] | 10s [7] | 0.07s [7] | 0.07s [7] | 7.96s [7] | 0.36s [7] | 0.09s [7] |
| L01 s007 t004 h1 | 0.08s [8] | 0.08s [8] | 0.15s [8] | 46s [8] | 0.07s [8] | 0.09s [8] | 33s [8] | 0.49s [8] | 0.10s [8] |
| L01 s018 t008 h2 | 0.14s [11] | 0.16s [11] | 0.26s [11] | 53s [9] | 0.14s [11] | 0.17s [9] | 37s [9] | 0.57s [9] | 0.16s [9] |
| L01 s003 t016 h1 | 0.32s [33] | 0.32s [33] | 0.58s [33] | MO | 0.31s [33] | 0.39s [33] | MO | 8.73s [33] | 0.33s [33] |
| L01 s003 t017 h1 | 0.32s [34] | 0.33s [34] | 0.64s [34] | MO | 0.32s [34] | 0.41s [34] | MO | 9.89s [34] | 0.33s [34] |
| L01 s012 t010 h2 | 0.08s [10] | 0.07s [10] | 0.15s [10] | 88s [11] | 0.08s [10] | 0.08s [10] | 59s [10] | 0.38s [10] | 0.09s [10] |
| L01 s013 t018 h2 | 0.16s [19] | 0.15s [19] | 0.28s [19] | MO | 0.17s [19] | 0.18s [19] | TO | 36s [19] | 0.16s [19] |
| L01 s009 t017 h1 | 0.42s [43] | 0.39s [43] | 0.71s [43] | MO | 0.38s [43] | 0.48s [43] | MO | TO | 0.39s [43] |
| L01 s010 t008 h2 | 0.26s [28] | 0.27s [28] | 0.46s [28] | TO | 0.28s [28] | 0.35s [28] | MO | MO | 0.29s [28] |
| L01 s002 t013 h1 | 0.52s [55] | 0.56s [57] | 0.86s [57] | MO | 0.52s [55] | 0.71s [57] | MO | MO | 0.56s [55] |
| L01 s005 t014 h1 | 0.51s [55] | 0.50s [55] | 0.84s [55] | MO | 0.54s [55] | 0.67s [55] | MO | MO | 0.51s [55] |
| L01 s008 t011 h1 | 0.40s [41] | 0.37s [41] | 0.61s [41] | MO | 0.40s [41] | 0.53s [41] | TO | MO | 5.85s [41] |
| L01 s001 t016 h1 | 0.88s [83] | 0.83s [83] | 1.41s [83] | MO | 0.85s [83] | 1.10s [83] | TO | MO | 0.81s [83] |
| L01 s017 t013 h2 | 0.18s [16] | 0.18s [16] | 0.33s [16] | TO | 0.17s [16] | 0.24s [16] | MO | 1.29s [16] | 0.16s [16] |
| L01 s011 t010 h2 | 0.11s [14] | 0.11s [14] | 0.20s [14] | MO | 0.10s [14] | 0.13s [14] | MO | 1.28s [14] | 0.13s [14] |
| L01 s018 t002 h2 | 0.59s [58] | 0.56s [58] | 0.94s [58] | TO | 0.56s [58] | 0.73s [60] | MO | TO | MO |
| L01 s012 t001 h2 | 0.33s [34] | 0.32s [34] | 0.59s [34] | MO | 0.31s [34] | 0.41s [34] | MO | 19s [34] | 0.33s [34] |
| L01 s013 t014 h2 | 0.15s [14] | 0.16s [14] | 0.31s [14] | MO | 0.14s [14] | 0.18s [14] | MO | 2.24s [14] | 0.14s [14] |
| L01 s016 t009 h2 | 0.42s [42] | 0.42s [42] | 0.73s [42] | TO | 0.41s [42] | 0.54s [42] | MO | 295s [42] | 26s [42] |
| L01 s014 t011 h2 | 0.58s [58] | 0.57s [58] | 0.98s [58] | TO | 0.54s [58] | 0.69s [58] | MO | TO | 26s [58] |
| L01 s016 t002 h2 | 0.67s [70] | 0.68s [72] | 1.14s [72] | TO | 0.66s [70] | 0.95s [74] | MO | TO | MO |

### orderfree-comb / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 0.03s [4] | 0.03s [4] | 0.07s [4] | 0.43s [4] | 0.03s [4] | 0.03s [4] | 0.32s [4] | 0.09s [4] | 0.03s [4] |
| L07 t001 | 0.25s [33] | 0.24s [33] | 0.45s [33] | TO | 0.24s [33] | 0.30s [33] | MO | 24s [33] | 1.04s [33] |
| L03 t018 | 0.22s [27] | 0.21s [27] | 0.33s [27] | MO | 0.21s [27] | 0.29s [27] | TO | 11s [25] | 9.42s [25] |
| L08 t001 | 0.22s [21] | 0.21s [21] | 0.40s [21] | MO | 0.21s [21] | 0.23s [20] | MO | 3.10s [20] | 1.94s [20] |
| L06 t005 | 0.04s [24] | 0.04s [24] | 0.12s [24] | TO | 0.04s [24] | 0.04s [24] | MO | TO | 0.03s [24] |
| L06 t002 | 0.03s [25] | 0.03s [25] | 0.10s [25] | TO | 0.04s [25] | 0.04s [25] | MO | TO | 0.03s [25] |
| L02 t005 | 0.36s [29] | 0.35s [29] | 0.61s [29] | MO | 0.55s [29] | 0.85s [30] | TO | MO | 30s [29] |
| L11 t115 | incomplete | incomplete | incomplete | MO | incomplete | incomplete | MO | incomplete | incomplete |
| L08 t003 | 0.29s [25] | 0.29s [25] | 0.49s [25] | MO | 0.28s [25] | 0.34s [25] | MO | MO | 0.30s [25] |
| L11 t168 | incomplete | incomplete | incomplete | MO | incomplete | incomplete | MO | incomplete | incomplete |
| L07 t008 | 0.38s [41] | 0.38s [41] | 0.70s [41] | TO | 0.37s [41] | 0.47s [41] | MO | MO | 0.39s [41] |
| L09 t005 | 0.27s [24] | 0.27s [24] | 0.47s [24] | MO | 0.27s [24] | 0.36s [24] | MO | MO | 0.27s [24] |
| L09 t003 | 0.24s [23] | 0.24s [23] | 0.44s [23] | MO | 0.24s [23] | 0.30s [23] | MO | MO | 0.23s [23] |
| L03 t002 | 2.57s [28] | 3.09s [37] | 4.78s [37] | MO | 4.80s [28] | 4.57s [28] | TO | MO | MO |
| L13 t006 | 0.69s [34] | 0.70s [34] | 0.59s [34] | MO | 0.69s [36] | 0.87s [34] | MO | 44s [34] | 0.82s [34] |
| L14 t006 | 0.72s [76] | 0.60s [76] | 1.01s [76] | MO | 0.87s [76] | 1.27s [77] | MO | MO | MO |
| L14 t016 | 0.87s [89] | 0.74s [89] | 1.23s [89] | MO | 1.04s [89] | 1.43s [90] | MO | MO | MO |
| L13 t003 | 1.51s [58] | 1.21s [58] | 2.07s [59] | MO | 3.99s [57] | 2.26s [60] | MO | MO | MO |

### orderfree-sep / l1

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L01 s009 t010 h1 | 0.26s [3] | 0.25s [3] | 0.33s [3] | 1.52s [3] | 0.25s [3] | 0.29s [3] | 1.48s [3] | 0.72s [3] | 0.51s [3] |
| L01 s004 t005 h1 | 0.33s [4] | 0.26s [4] | 0.33s [4] | 2.23s [4] | 0.32s [4] | 0.31s [6] | 2.27s [4] | 1.36s [4] | 1.06s [4] |
| L01 s007 t005 h1 | 0.25s [4] | 0.25s [4] | 0.31s [4] | 0.88s [4] | 0.25s [4] | 0.29s [4] | 3.11s [4] | 3.00s [4] | 1.02s [4] |
| L01 s005 t004 h1 | 0.47s [7] | 0.42s [7] | 0.58s [7] | 61s [7] | 0.47s [7] | 0.54s [7] | 59s [7] | 6.58s [7] | 3.97s [7] |
| L01 s007 t004 h1 | 0.47s [8] | 0.47s [8] | 0.64s [8] | MO | 0.47s [8] | 0.65s [8] | 195s [8] | 75s [8] | 40s [8] |
| L01 s018 t008 h2 | 0.66s [11] | 0.71s [11] | 0.72s [11] | MO | 0.57s [11] | 0.78s [9] | MO | 112s [9] | 111s [9] |
| L01 s003 t016 h1 | 1.94s [33] | 1.95s [33] | 2.45s [33] | MO | 1.94s [33] | 2.80s [33] | MO | MO | MO |
| L01 s003 t017 h1 | 2.04s [34] | 2.05s [34] | 2.43s [34] | MO | 1.99s [34] | 2.91s [34] | MO | MO | MO |
| L01 s012 t010 h2 | 0.63s [10] | 0.64s [10] | 0.80s [10] | MO | 0.64s [10] | 0.89s [10] | MO | 187s [10] | 108s [10] |
| L01 s013 t018 h2 | 1.13s [19] | 1.14s [19] | 1.27s [19] | MO | 1.12s [19] | 1.52s [19] | MO | MO | MO |
| L01 s010 t008 h2 | 1.50s [28] | 1.48s [28] | 1.94s [28] | MO | 1.52s [28] | 2.20s [28] | MO | TO | MO |
| L01 s002 t013 h1 | 5.81s [57] | 3.63s [55] | 4.46s [55] | MO | 5.93s [55] | 4.73s [57] | MO | MO | MO |
| L01 s008 t011 h1 | 2.26s [41] | 2.29s [41] | 3.03s [41] | MO | 2.30s [41] | 3.49s [41] | MO | MO | MO |
| L01 s017 t013 h2 | 1.05s [16] | 0.96s [16] | 1.21s [16] | MO | 0.98s [16] | 1.41s [16] | TO | MO | TO |
| L01 s011 t010 h2 | 1.03s [14] | 1.08s [14] | 1.13s [14] | MO | 0.95s [14] | 1.55s [14] | MO | TO | MO |
| L01 s018 t002 h2 | 3.69s [58] | 3.26s [60] | 3.82s [60] | MO | 3.82s [58] | 4.94s [60] | MO | TO | MO |
| L01 s013 t014 h2 | 0.86s [14] | 0.90s [14] | 1.03s [14] | MO | 0.85s [14] | 1.16s [14] | MO | TO | MO |

### orderfree-sep / other

| problem | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| L02 t007 | 0.17s [4] | 0.16s [4] | 0.32s [4] | 2.66s [4] | 0.17s [4] | 0.20s [4] | 2.66s [4] | 1.93s [4] | 1.02s [4] |
