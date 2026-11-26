# Old vs new test domains, same planner

Variant **inv0**. Old: `tools/benchmarking/sweep_results` (1392 runs). New: `tools/benchmarking/sweep_results_v2` (1392 runs).

**old**
- `host_vm.txt`: host=vm; cpus=4; ram_gb=16; cpu=Intel(R) Xeon(R) Processor @ 2.10GHz (groups A, C and the first 41 group-B jobs, until a container restart 2026-11-25 ~00:45 UTC); Intel(R) Xeon(R) Processor @ 2.30GHz (remaining group-B jobs); platform=Linux-6.18.44-fc-v819-x86_64-with-glibc2.39, then Linux-6.18.44-fc-v880-x86_64-with-glibc2.39; run[results_vm.csv]=jobs=4 timeout=300s mem=3G mem_limit=rlimit (FD driver) fd=upstream fast-downward release-24.06.1 (downward@1eef26b) classic configs only domains=a9f6ad1

**new**
- `host_vm.txt`: host=vm; cpus=4; ram_gb=16; cpu=Intel(R) Xeon(R) Processor @ 2.10GHz (all jobs; the container restarted three times, 2026-11-25 ~16:30 and ~19:00 UTC and 2026-11-26 ~04:25 UTC, and the run was resumed on the same CPU type and kernel each time; jobs cut off by a restart were rerun in full); platform=Linux-6.18.44-fc-v880-x86_64-with-glibc2.39; run[results_vm.csv]=jobs=4 timeout=300s mem=3G mem_limit=rlimit (FD driver) fd=downward@1eef26b FD_STATE_DUMP=0 domains=a1a50ba

## Same game?

- Problems with a proven optimum on both sides: 41; **all optimal costs are the same before and after.**
- Proven optimum only on the old side: 0; only on the new side: 1 (L01 s016 t009 h2)
- No plan (search space exhausted): old L11 t115, L11 t168, testing_level_2, testing_level_3; new L11 t115, L11 t168, testing_level_2, testing_level_3

## Coverage (solved / solvable problems run), old → new


### scan-comb

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 → 10/10 | 24/24 → 24/24 | 14/16 (2TO) → 16/16 |
| eager-gbfs-ff | 10/10 → 10/10 | 24/24 → 24/24 | 14/16 (2TO) → 16/16 |
| gbfs-add | 10/10 → 10/10 | 24/24 → 24/24 | 16/16 → 16/16 |
| gbfs-cea | 10/10 → 10/10 | 18/24 (6TO) → 20/24 (4TO) | 12/16 (4TO) → 12/16 (4TO) |
| gbfs-cg | 10/10 → 10/10 | 3/24 (21TO) → 3/24 (21TO) | 1/16 (4MO 11TO) → 1/16 (6MO 9TO) |
| wastar3-ff | 10/10 → 10/10 | 24/24 → 24/24 | 14/16 (2TO) → 16/16 |
| lama-first | 10/10 → 10/10 | 24/24 → 24/24 | 12/16 (4TO) → 14/16 (2TO) |
| astar-blind | 10/10 → 10/10 | 6/24 (16MO 2TO) → 7/24 (15MO 2TO) | 1/16 (15MO) → 1/16 (15MO) |
| astar-hmax | 10/10 → 10/10 | 20/24 (4TO) → 21/24 (3TO) | 11/16 (5TO) → 11/16 (5TO) |
| astar-lmcp | 10/10 → 10/10 | 7/24 (16MO 1TO) → 7/24 (14MO 3TO) | 2/16 (14MO) → 1/16 (15MO) |
| astar-ms | 9/10 (1TO) → 9/10 (1TO) |  |  |

### scan-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 10/10 → 10/10 | 22/24 (2TO) → 24/24 | 10/16 (6TO) → 11/16 (5TO) |
| eager-gbfs-ff | 10/10 → 10/10 | 12/24 (12TO) → 16/24 (8TO) | 4/16 (12TO) → 11/16 (5TO) |
| gbfs-add | 10/10 → 10/10 | 22/24 (2TO) → 24/24 | 9/16 (7TO) → 11/16 (5TO) |
| gbfs-cea | 10/10 → 10/10 | 8/24 (16TO) → 17/24 (7TO) | 3/16 (13TO) → 8/16 (8TO) |
| gbfs-cg | 10/10 → 10/10 | 3/24 (21TO) → 3/24 (21TO) | 1/16 (15TO) → 1/16 (15TO) |
| wastar3-ff | 10/10 → 10/10 | 22/24 (2TO) → 24/24 | 9/16 (7TO) → 12/16 (4TO) |
| lama-first | 10/10 → 10/10 | 4/24 (20TO) → 22/24 (2TO) | 1/16 (15TO) → 11/16 (5TO) |
| astar-blind | 10/10 → 10/10 | 4/24 (20MO) → 6/24 (18MO) | 1/16 (15MO) → 1/16 (15MO) |
| astar-hmax | 10/10 → 10/10 | 3/24 (21TO) → 4/24 (20TO) | 1/16 (15TO) → 1/16 (15TO) |
| astar-lmcp | 10/10 → 10/10 | 4/24 (20MO) → 7/24 (17MO) | 1/16 (15MO) → 1/16 (15MO) |
| astar-ms | 9/10 (1TO) → 8/10 (2TO) |  |  |

### orderfree-comb

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 9/10 (1TO) → 9/10 (1TO) | 0/6 (6TO) → 0/6 (6TO) |  |
| eager-gbfs-ff | 9/10 (1TO) → 9/10 (1TO) |  |  |
| gbfs-add | 9/10 (1TO) → 9/10 (1TO) |  |  |
| gbfs-cea | 9/10 (1TO) → 9/10 (1TO) |  |  |
| gbfs-cg | 9/10 (1TO) → 9/10 (1TO) |  |  |
| wastar3-ff | 9/10 (1TO) → 9/10 (1TO) |  |  |
| lama-first | 9/10 (1TO) → 9/10 (1TO) |  |  |
| astar-blind | 9/10 (1TO) → 9/10 (1TO) |  |  |
| astar-hmax | 9/10 (1TO) → 9/10 (1TO) | 0/6 (6TO) → 0/6 (6TO) |  |
| astar-lmcp | 0/10 (10unsupported) → 0/10 (10unsupported) |  |  |
| astar-ms | 0/10 (10unsupported) → 0/10 (10unsupported) |  |  |

### orderfree-sep

| config | small (hand-made, 5x5..40x11) | bd_level_01 20x38 (h1+h2) | bd_levels 02..14 |
|---|---|---|---|
| gbfs-ff | 8/10 (2TO) → 8/10 (2TO) | 0/6 (6TO) → 0/6 (6TO) |  |
| eager-gbfs-ff | 8/10 (2TO) → 8/10 (2TO) |  |  |
| gbfs-add | 8/10 (2TO) → 8/10 (2TO) |  |  |
| gbfs-cea | 8/10 (2TO) → 8/10 (2TO) |  |  |
| gbfs-cg | 8/10 (2TO) → 8/10 (2TO) |  |  |
| wastar3-ff | 8/10 (2TO) → 8/10 (2TO) |  |  |
| lama-first | 8/10 (2TO) → 8/10 (2TO) |  |  |
| astar-blind | 8/10 (2MO) → 8/10 (2MO) |  |  |
| astar-hmax | 8/10 (2TO) → 8/10 (2TO) | 0/6 (6TO) → 0/6 (6TO) |  |
| astar-lmcp | 0/10 (10unsupported) → 0/10 (10unsupported) |  |  |
| astar-ms | 0/10 (10unsupported) → 0/10 (10unsupported) |  |  |

## Model size and physics work, large problems

Translator operators and translate time: medians over the large problems translated on both sides. Physics steps per move: median of (plan length − plan cost) / plan cost over large solved runs (plan length counts every action, cost only the moves).

| model | operators | translate time | physics steps per move |
|---|---|---|---|
| scan-comb | 21k → 18k | 19s → 27s | 201 → 116 |
| scan-sep | 36k → 34k | 11s → 15s | 1246 → 368 |
| orderfree-comb | 23k → 20k | 18s → 24s | – → – |
| orderfree-sep | 30k → 29k | 11s → 17s | – → – |

## Search effort on tasks both sides solved (same model and config)

Geometric means. Search time is Fast Downward's search time (translation excluded).


**scan-comb**

| config | set | tasks | search time | faster by | expansions |
|---|---|---|---|---|---|
| gbfs-ff | small | 10 | 0.05s → 0.04s | 1.3x | 444 → 453 |
| gbfs-ff | large | 38 | 19s → 15s | 1.3x | 5358 → 3441 |
| eager-gbfs-ff | small | 10 | 0.10s → 0.07s | 1.6x | 704 → 704 |
| eager-gbfs-ff | large | 38 | 25s → 20s | 1.3x | 7029 → 4557 |
| gbfs-add | small | 10 | 0.06s → 0.04s | 1.6x | 444 → 453 |
| gbfs-add | large | 40 | 23s → 16s | 1.4x | 6501 → 3786 |
| gbfs-cea | small | 10 | 0.22s → 0.18s | 1.2x | 635 → 638 |
| gbfs-cea | large | 28 | 117s → 118s | 1.0x | 4407 → 3063 |
| gbfs-cg | small | 10 | 0.20s → 0.17s | 1.2x | 3625 → 3609 |
| gbfs-cg | large | 4 | 121s → 71s | 1.7x | 23k → 12k |
| wastar3-ff | small | 10 | 0.05s → 0.05s | 1.2x | 444 → 453 |
| wastar3-ff | large | 38 | 20s → 16s | 1.2x | 5524 → 3614 |
| lama-first | small | 10 | 0.06s → 0.04s | 1.5x | 745 → 738 |
| lama-first | large | 36 | 12s → 8.28s | 1.4x | 5750 → 3265 |
| astar-blind | small | 10 | 0.02s → 0.02s | 1.1x | 4395 → 4395 |
| astar-blind | large | 7 | 13s → 7.86s | 1.7x | 164k → 90k |
| astar-hmax | small | 10 | 0.05s → 0.04s | 1.3x | 765 → 765 |
| astar-hmax | large | 31 | 14s → 12s | 1.2x | 7452 → 4971 |
| astar-lmcp | small | 10 | 0.02s → 0.01s | 1.2x | 2801 → 2801 |
| astar-lmcp | large | 8 | 8.99s → 5.85s | 1.5x | 109k → 65k |
| astar-ms | small | 9 | 0.03s → 0.02s | 1.7x | 3739 → 3745 |

**scan-sep**

| config | set | tasks | search time | faster by | expansions |
|---|---|---|---|---|---|
| gbfs-ff | small | 10 | 0.08s → 0.04s | 1.9x | 906 → 548 |
| gbfs-ff | large | 32 | 86s → 24s | 3.5x | 27k → 7317 |
| eager-gbfs-ff | small | 10 | 0.16s → 0.10s | 1.6x | 1737 → 1134 |
| eager-gbfs-ff | large | 16 | 102s → 43s | 2.4x | 33k → 13k |
| gbfs-add | small | 10 | 0.07s → 0.05s | 1.4x | 906 → 548 |
| gbfs-add | large | 31 | 80s → 23s | 3.5x | 26k → 7267 |
| gbfs-cea | small | 10 | 0.33s → 0.21s | 1.6x | 1172 → 766 |
| gbfs-cea | large | 11 | 160s → 81s | 2.0x | 10k → 4617 |
| gbfs-cg | small | 10 | 0.12s → 0.10s | 1.1x | 3479 → 2744 |
| gbfs-cg | large | 4 | 46s → 52s | 0.9x | 46k → 38k |
| wastar3-ff | small | 10 | 0.08s → 0.05s | 1.6x | 906 → 548 |
| wastar3-ff | large | 31 | 84s → 24s | 3.4x | 26k → 7274 |
| lama-first | small | 10 | 0.18s → 0.07s | 2.6x | 2683 → 911 |
| lama-first | large | 5 | 31s → 9.67s | 3.2x | 16k → 5016 |
| astar-blind | small | 10 | 0.02s → 0.02s | 1.0x | 6213 → 5363 |
| astar-blind | large | 5 | 9.68s → 5.28s | 1.8x | 224k → 116k |
| astar-hmax | small | 10 | 0.17s → 0.10s | 1.7x | 3434 → 2380 |
| astar-hmax | large | 4 | 34s → 32s | 1.1x | 20k → 17k |
| astar-lmcp | small | 10 | 0.03s → 0.02s | 1.2x | 6006 → 5200 |
| astar-lmcp | large | 5 | 3.85s → 2.88s | 1.3x | 79k → 53k |
| astar-ms | small | 8 | 0.02s → 0.02s | 0.8x | 4284 → 4356 |

**orderfree-comb**

| config | set | tasks | search time | faster by | expansions |
|---|---|---|---|---|---|
| gbfs-ff | small | 9 | 0.02s → 0.01s | 1.5x | 241 → 144 |
| eager-gbfs-ff | small | 9 | 0.03s → 0.03s | 1.1x | 363 → 234 |
| gbfs-add | small | 9 | 0.02s → 0.02s | 1.0x | 241 → 144 |
| gbfs-cea | small | 9 | 0.03s → 0.04s | 0.8x | 259 → 161 |
| gbfs-cg | small | 9 | 0.05s → 0.04s | 1.4x | 1312 → 961 |
| wastar3-ff | small | 9 | 0.02s → 0.01s | 1.3x | 241 → 144 |
| lama-first | small | 9 | 0.01s → 0.01s | 1.2x | 284 → 183 |
| astar-blind | small | 9 | 0.01s → 0.02s | 0.9x | 1460 → 1110 |
| astar-hmax | small | 9 | 0.02s → 0.02s | 0.9x | 398 → 269 |

**orderfree-sep**

| config | set | tasks | search time | faster by | expansions |
|---|---|---|---|---|---|
| gbfs-ff | small | 8 | 0.01s → 0.01s | 1.6x | 282 → 108 |
| eager-gbfs-ff | small | 8 | 0.03s → 0.02s | 1.6x | 515 → 201 |
| gbfs-add | small | 8 | 0.01s → 0.01s | 1.6x | 282 → 108 |
| gbfs-cea | small | 8 | 0.03s → 0.02s | 1.3x | 303 → 117 |
| gbfs-cg | small | 8 | 0.02s → 0.01s | 1.1x | 1000 → 423 |
| wastar3-ff | small | 8 | 0.01s → 0.01s | 1.9x | 282 → 108 |
| lama-first | small | 8 | 0.02s → 0.02s | 1.2x | 498 → 199 |
| astar-blind | small | 8 | 0.01s → 0.01s | 1.4x | 1898 → 800 |
| astar-hmax | small | 8 | 0.02s → 0.01s | 1.3x | 702 → 332 |

## Satisficing plan quality (cost / known optimum), old → new

Mean (worst) over solved tasks with a known optimum.

| model | gbfs-ff | eager-gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first |
|---|---|---|---|---|---|---|---|
| scan-comb | 1.04 (1.60) → 1.03 (1.60) | 1.01 (1.44) → 1.02 (1.44) | 1.05 (1.60) → 1.03 (1.60) | 1.02 (1.25) → 1.03 (1.44) | 1.03 (1.33) → 1.00 (1.00) | 1.03 (1.60) → 1.03 (1.60) | 1.06 (1.67) → 1.07 (1.67) |
| scan-sep | 1.04 (1.50) → 1.04 (1.50) | 1.00 (1.00) → 1.01 (1.15) | 1.04 (1.50) → 1.03 (1.50) | 1.00 (1.00) → 1.01 (1.44) | 1.00 (1.00) → 1.03 (1.14) | 1.04 (1.50) → 1.04 (1.50) | 1.00 (1.00) → 1.11 (1.75) |
| orderfree-comb | 1.04 (1.38) → 1.04 (1.38) | 1.00 (1.00) → 1.00 (1.00) | 1.04 (1.38) → 1.04 (1.38) | 1.00 (1.00) → 1.03 (1.25) | 1.00 (1.00) → 1.00 (1.00) | 1.04 (1.38) → 1.04 (1.38) | 1.01 (1.12) → 1.01 (1.12) |
| orderfree-sep | 1.02 (1.12) → 1.02 (1.12) | 1.00 (1.00) → 1.00 (1.00) | 1.02 (1.12) → 1.02 (1.12) | 1.00 (1.00) → 1.02 (1.12) | 1.00 (1.00) → 1.00 (1.00) | 1.02 (1.12) → 1.02 (1.12) | 1.02 (1.12) → 1.02 (1.12) |
