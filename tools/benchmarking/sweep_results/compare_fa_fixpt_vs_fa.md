# Planner build comparison: inv0+fa@m5pro → inv0+fa+fixpt@m5pro

- base: **inv0+fa@m5pro** (1944 runs); new: **inv0+fa+fixpt@m5pro** (1944 runs); 1944 (model, problem, config) runs on both sides
- **m5pro**: host=m5pro; cpus=18; ram_gb=48; cpu=Apple M5 Pro; platform=macOS-26.5.2-arm64-arm-64bit-Mach-O; run[results_m5pro.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0; run[results_m5pro_fa.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fast-downward@3afd34949 + local changes (src/search/utils/state_dump.cc, src/search/utils/state_dump.h) FD_STATE_DUMP=0; run[results_m5pro_fa_fixpt.csv]=jobs=12 timeout=300s mem=3G mem_limit=rss-watchdog (macOS: FD cannot set memory limits) fd=fd-fixpoint@52938c8b5 FD_STATE_DUMP=0 domains=a9f6ad1

## Correctness

No-plan problems (some search exhausted): L11 t115, L11 t168, testing_level_2, testing_level_3.
No problem is solved anywhere and proved plan-less anywhere else.
Optimal costs: 45 problems solved optimally; all agree across sides, models and configs.

On the 1284 runs both sides solve: same plan cost and length in 1283, same number of expansions in 1277.

Runs whose plan cost changed (base → new):

- scan-comb lama-first L08 t001: 20 → 22

## Status transitions (base → new), all runs

| model | changed | unchanged |
|---|---|---|
| scan-comb | MO→TO 86, MO→solved 10 | solved 356, incomplete 32, MO 2 |
| scan-sep | MO→TO 154, MO→solved 20 | solved 294, incomplete 18 |
| orderfree-comb | MO→TO 68, MO→solved 4, TO→solved 1 | solved 360, incomplete 32, TO 21 |
| orderfree-sep | MO→TO 130, MO→solved 3, TO→solved 3 | solved 274, TO 58, incomplete 18 |

## Coverage (solved / solvable problems run), base → new

Failures in brackets: MO = memout, TO = timeout.


### scan-comb

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 | 24/24 | 16/16 |
| gbfs-add | 10/10 | 24/24 | 16/16 |
| gbfs-cea | 10/10 | 24/24 | 16/16 |
| gbfs-cg | 10/10 | 5/24 (19MO) → 7/24 (17TO) | 1/16 (15MO) → 1/16 (2MO 13TO) |
| wastar3-ff | 10/10 | 24/24 | 16/16 |
| lama-first | 10/10 | 24/24 | 15/16 (1MO) → 16/16 |
| lazy-astar-blind | 10/10 | 7/24 (17MO) → 8/24 (16TO) | 1/16 (15MO) → 1/16 (15TO) |
| lazy-astar-hmax | 10/10 | 14/24 (10MO) → 16/24 (8TO) | 5/16 (11MO) → 8/16 (8TO) |
| lazy-astar-hmax-tb | 10/10 | 22/24 (2MO) → 22/24 (2TO) | 12/16 (4MO) → 13/16 (3TO) |

Large-problem gains (+) and losses (−): +gbfs-cg L01 s018 t008 h2 (MO→solved); +gbfs-cg L01 s012 t010 h2 (MO→solved); +lama-first L13 t003 (MO→solved); +lazy-astar-blind L01 s013 t014 h2 (MO→solved); +lazy-astar-hmax L01 s009 t017 h1 (MO→solved); +lazy-astar-hmax L01 s016 t009 h2 (MO→solved); +lazy-astar-hmax L07 t008 (MO→solved); +lazy-astar-hmax L09 t005 (MO→solved); +lazy-astar-hmax L09 t003 (MO→solved); +lazy-astar-hmax-tb L03 t002 (MO→solved)

### scan-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 | 24/24 | 14/16 (2MO) → 14/16 (2TO) |
| gbfs-add | 10/10 | 24/24 | 12/16 (4MO) → 14/16 (2TO) |
| gbfs-cea | 10/10 | 24/24 | 12/16 (4MO) → 14/16 (2TO) |
| gbfs-cg | 10/10 | 4/24 (20MO) → 7/24 (17TO) | 1/16 (15MO) → 1/16 (15TO) |
| wastar3-ff | 10/10 | 24/24 | 12/16 (4MO) → 15/16 (1TO) |
| lama-first | 10/10 | 24/24 | 12/16 (4MO) → 15/16 (1TO) |
| lazy-astar-blind | 10/10 | 4/24 (20MO) → 7/24 (17TO) | 1/16 (15MO) → 1/16 (15TO) |
| lazy-astar-hmax | 10/10 | 4/24 (20MO) → 7/24 (17TO) | 1/16 (15MO) → 1/16 (15TO) |
| lazy-astar-hmax-tb | 10/10 | 6/24 (18MO) → 7/24 (17TO) | 1/16 (15MO) → 1/16 (15TO) |

Large-problem gains (+) and losses (−): +gbfs-add L14 t006 (MO→solved); +gbfs-add L14 t016 (MO→solved); +gbfs-cea L14 t006 (MO→solved); +gbfs-cea L14 t016 (MO→solved); +gbfs-cg L01 s007 t004 h1 (MO→solved); +gbfs-cg L01 s018 t008 h2 (MO→solved); +gbfs-cg L01 s012 t010 h2 (MO→solved); +wastar3-ff L08 t001 (MO→solved); +wastar3-ff L14 t006 (MO→solved); +wastar3-ff L14 t016 (MO→solved); +lama-first L08 t001 (MO→solved); +lama-first L14 t006 (MO→solved); +lama-first L14 t016 (MO→solved); +lazy-astar-blind L01 s007 t004 h1 (MO→solved); +lazy-astar-blind L01 s018 t008 h2 (MO→solved); +lazy-astar-blind L01 s012 t010 h2 (MO→solved); +lazy-astar-hmax L01 s007 t004 h1 (MO→solved); +lazy-astar-hmax L01 s018 t008 h2 (MO→solved); +lazy-astar-hmax L01 s012 t010 h2 (MO→solved); +lazy-astar-hmax-tb L01 s012 t010 h2 (MO→solved)

### orderfree-comb

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 | 24/24 | 16/16 |
| gbfs-add | 10/10 | 24/24 | 16/16 |
| gbfs-cea | 10/10 | 24/24 | 16/16 |
| gbfs-cg | 10/10 | 7/24 (11MO 6TO) → 7/24 (17TO) | 1/16 (11MO 4TO) → 1/16 (15TO) |
| wastar3-ff | 10/10 | 24/24 | 16/16 |
| lama-first | 10/10 | 24/24 | 16/16 |
| lazy-astar-blind | 10/10 | 7/24 (14MO 3TO) → 7/24 (17TO) | 1/16 (12MO 3TO) → 1/16 (15TO) |
| lazy-astar-hmax | 10/10 | 15/24 (5MO 4TO) → 16/24 (8TO) | 5/16 (9MO 2TO) → 8/16 (8TO) |
| lazy-astar-hmax-tb | 10/10 | 22/24 (2MO) → 22/24 (2TO) | 12/16 (4MO) → 13/16 (3TO) |

Large-problem gains (+) and losses (−): +lazy-astar-hmax L01 s009 t017 h1 (TO→solved); +lazy-astar-hmax L07 t008 (MO→solved); +lazy-astar-hmax L09 t005 (MO→solved); +lazy-astar-hmax L09 t003 (MO→solved); +lazy-astar-hmax-tb L03 t002 (MO→solved)

### orderfree-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 | 18/24 (3MO 3TO) → 18/24 (6TO) | 13/16 (3MO) → 13/16 (3TO) |
| gbfs-add | 10/10 | 18/24 (6MO) → 18/24 (6TO) | 14/16 (2MO) → 14/16 (2TO) |
| gbfs-cea | 10/10 | 18/24 (5MO 1TO) → 18/24 (6TO) | 12/16 (2MO 2TO) → 12/16 (4TO) |
| gbfs-cg | 10/10 | 4/24 (20MO) → 6/24 (18TO) | 1/16 (13MO 2TO) → 1/16 (15TO) |
| wastar3-ff | 10/10 | 18/24 (1MO 5TO) → 18/24 (6TO) | 16/16 |
| lama-first | 10/10 | 18/24 (6MO) → 18/24 (6TO) | 12/16 (1MO 3TO) → 15/16 (1TO) |
| lazy-astar-blind | 10/10 | 5/24 (17MO 2TO) → 6/24 (18TO) | 1/16 (9MO 6TO) → 1/16 (15TO) |
| lazy-astar-hmax | 10/10 | 7/24 (9MO 8TO) → 7/24 (17TO) | 1/16 (9MO 6TO) → 1/16 (15TO) |
| lazy-astar-hmax-tb | 10/10 | 7/24 (11MO 6TO) → 7/24 (17TO) | 1/16 (8MO 7TO) → 1/16 (15TO) |

Large-problem gains (+) and losses (−): +gbfs-cg L01 s007 t004 h1 (MO→solved); +gbfs-cg L01 s018 t008 h2 (MO→solved); +lama-first L14 t006 (TO→solved); +lama-first L14 t016 (TO→solved); +lama-first L13 t003 (TO→solved); +lazy-astar-blind L01 s018 t008 h2 (MO→solved)

## Search time and peak memory on runs both sides solve (large problems)

Geometric means of search time; peak memory is the median (max) of the sampled peak RSS per run. `all runs` peak memory is over every run of that config, solved or not.

| model | config | runs | base time | new time | speed-up | base peak mem | new peak mem | all runs: base max | all runs: new max |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | gbfs-ff | 40 | 0.37s | 0.22s | 1.7x | 106 MB (555 MB) | 100 MB (108 MB) | 555 MB | 108 MB |
| scan-comb | gbfs-add | 40 | 0.35s | 0.22s | 1.6x | 106 MB (174 MB) | 100 MB (110 MB) | 174 MB | 110 MB |
| scan-comb | gbfs-cea | 40 | 0.86s | 0.71s | 1.2x | 173 MB (224 MB) | 166 MB (180 MB) | 224 MB | 180 MB |
| scan-comb | gbfs-cg | 6 | 3.05s | 1.46s | 2.1x | 2.0 GB (2.9 GB) | 1.7 GB (2.0 GB) | 3.1 GB | 3.0 GB |
| scan-comb | wastar3-ff | 40 | 0.40s | 0.24s | 1.6x | 109 MB (2.5 GB) | 100 MB (141 MB) | 2.5 GB | 141 MB |
| scan-comb | lama-first | 39 | 0.56s | 0.26s | 2.2x | 119 MB (339 MB) | 100 MB (113 MB) | 3.0 GB | 246 MB |
| scan-comb | lazy-astar-blind | 8 | 5.05s | 1.53s | 3.3x | 192 MB (1.9 GB) | 45 MB (72 MB) | 3.0 GB | 864 MB |
| scan-comb | lazy-astar-hmax | 19 | 2.33s | 0.94s | 2.5x | 129 MB (973 MB) | 87 MB (100 MB) | 3.0 GB | 482 MB |
| scan-comb | lazy-astar-hmax-tb | 34 | 0.57s | 0.28s | 2.0x | 92 MB (2.0 GB) | 83 MB (95 MB) | 3.0 GB | 408 MB |
| scan-sep | gbfs-ff | 38 | 1.01s | 0.23s | 4.4x | 145 MB (558 MB) | 99 MB (111 MB) | 3.0 GB | 208 MB |
| scan-sep | gbfs-add | 36 | 0.96s | 0.22s | 4.5x | 143 MB (1.5 GB) | 98 MB (110 MB) | 3.0 GB | 212 MB |
| scan-sep | gbfs-cea | 36 | 1.38s | 0.65s | 2.1x | 189 MB (1.6 GB) | 142 MB (153 MB) | 3.0 GB | 185 MB |
| scan-sep | gbfs-cg | 5 | 2.20s | 0.30s | 7.5x | 1.2 GB (2.8 GB) | 1.1 GB (1.2 GB) | 3.0 GB | 1.5 GB |
| scan-sep | wastar3-ff | 36 | 0.92s | 0.21s | 4.4x | 143 MB (599 MB) | 99 MB (108 MB) | 3.0 GB | 200 MB |
| scan-sep | lama-first | 36 | 1.30s | 0.24s | 5.5x | 167 MB (475 MB) | 98 MB (108 MB) | 3.0 GB | 228 MB |
| scan-sep | lazy-astar-blind | 5 | 2.72s | 0.31s | 8.6x | 116 MB (1.7 GB) | 48 MB (51 MB) | 3.1 GB | 249 MB |
| scan-sep | lazy-astar-hmax | 5 | 1.76s | 0.28s | 6.3x | 142 MB (728 MB) | 81 MB (91 MB) | 3.1 GB | 228 MB |
| scan-sep | lazy-astar-hmax-tb | 7 | 3.29s | 0.52s | 6.3x | 110 MB (3.0 GB) | 81 MB (86 MB) | 3.1 GB | 222 MB |
| orderfree-comb | gbfs-ff | 40 | 0.24s | 0.25s | 1.0x | 98 MB (114 MB) | 92 MB (104 MB) | 114 MB | 104 MB |
| orderfree-comb | gbfs-add | 40 | 0.24s | 0.25s | 1.0x | 95 MB (121 MB) | 93 MB (103 MB) | 121 MB | 103 MB |
| orderfree-comb | gbfs-cea | 40 | 0.43s | 0.43s | 1.0x | 128 MB (147 MB) | 126 MB (136 MB) | 147 MB | 136 MB |
| orderfree-comb | gbfs-cg | 8 | 3.79s | 2.96s | 1.3x | 1.6 GB (2.4 GB) | 1.5 GB (1.5 GB) | 3.0 GB | 2.7 GB |
| orderfree-comb | wastar3-ff | 40 | 0.25s | 0.27s | 1.0x | 97 MB (143 MB) | 94 MB (102 MB) | 143 MB | 102 MB |
| orderfree-comb | lama-first | 40 | 0.30s | 0.29s | 1.0x | 97 MB (147 MB) | 93 MB (101 MB) | 147 MB | 101 MB |
| orderfree-comb | lazy-astar-blind | 8 | 2.98s | 1.99s | 1.5x | 120 MB (735 MB) | 45 MB (61 MB) | 3.0 GB | 1.2 GB |
| orderfree-comb | lazy-astar-hmax | 20 | 2.25s | 1.67s | 1.3x | 104 MB (2.7 GB) | 79 MB (148 MB) | 3.0 GB | 654 MB |
| orderfree-comb | lazy-astar-hmax-tb | 34 | 0.38s | 0.36s | 1.1x | 79 MB (539 MB) | 77 MB (86 MB) | 3.0 GB | 179 MB |
| orderfree-sep | gbfs-ff | 31 | 1.43s | 1.23s | 1.2x | 115 MB (2.1 GB) | 99 MB (109 MB) | 3.0 GB | 124 MB |
| orderfree-sep | gbfs-add | 32 | 1.38s | 1.23s | 1.1x | 116 MB (665 MB) | 98 MB (106 MB) | 3.0 GB | 121 MB |
| orderfree-sep | gbfs-cea | 30 | 1.45s | 1.28s | 1.1x | 157 MB (413 MB) | 138 MB (148 MB) | 3.0 GB | 163 MB |
| orderfree-sep | gbfs-cg | 5 | 3.44s | 2.11s | 1.6x | 1.9 GB (2.8 GB) | 1.9 GB (2.2 GB) | 3.0 GB | 2.6 GB |
| orderfree-sep | wastar3-ff | 34 | 2.21s | 1.79s | 1.2x | 119 MB (1.9 GB) | 98 MB (107 MB) | 3.0 GB | 120 MB |
| orderfree-sep | lama-first | 30 | 1.49s | 1.22s | 1.2x | 117 MB (429 MB) | 90 MB (98 MB) | 3.0 GB | 118 MB |
| orderfree-sep | lazy-astar-blind | 6 | 8.28s | 4.83s | 1.7x | 83 MB (2.9 GB) | 47 MB (54 MB) | 3.0 GB | 386 MB |
| orderfree-sep | lazy-astar-hmax | 8 | 9.35s | 5.52s | 1.7x | 147 MB (2.1 GB) | 81 MB (87 MB) | 3.0 GB | 301 MB |
| orderfree-sep | lazy-astar-hmax-tb | 8 | 5.68s | 3.47s | 1.6x | 113 MB (1.6 GB) | 82 MB (84 MB) | 3.0 GB | 305 MB |
