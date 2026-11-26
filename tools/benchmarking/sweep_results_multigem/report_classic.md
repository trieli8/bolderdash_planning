# Fast Downward settings sweep

Variant **inv0+multigem** (translator options; +fa = forced-action fork). Other variants in the data: none (pick with --variant=NAME).

216 runs from host(s) vm; models: scan-comb.

- **vm**: host=vm; cpus=4; ram_gb=16; cpu=Intel(R) Xeon(R) Processor @ 2.10GHz; platform=Linux-6.18.44-fc-v880-x86_64-with-glibc2.39; run[results_vm_multigem.csv]=jobs=4 timeout=300s mem=3G mem_limit=rlimit (FD driver) fd=downward@1eef26b FD_STATE_DUMP=0 domains=98d93c0

## Coverage (solved / solvable problems run)


### 1 target (the l1 problems)

| model | lama-first | astar-hmax | astar-lmcp |
|---|---|---|---|
| scan-comb | 24/24 | 22/24 (2TO) | 7/24 (17MO) |

### 2 targets

| model | lama-first | astar-hmax | astar-lmcp |
|---|---|---|---|
| scan-comb | 17/24 (7TO) | 8/24 (16TO) | 0/24 (24MO) |

### 3 targets

| model | lama-first | astar-hmax | astar-lmcp |
|---|---|---|---|
| scan-comb | 14/24 (10TO) | 5/24 (19TO) | 0/24 (24MO) |

## Search effort on tasks every listed config solved (per model)

Geometric mean of search time and expansions over the tasks solved by all configs in the row group; plan quality is the mean of cost / best known optimum.


**scan-comb / satisficing / n1** (24 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lama-first | 6.47s | 3133 | 62 | 1.03 (n=22, max 1.50) |

**scan-comb / satisficing / n2** (17 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lama-first | 10s | 4460 | 71 | 1.01 (n=8, max 1.07) |

**scan-comb / satisficing / n3** (14 common tasks; left out for low coverage: none)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| lama-first | 18s | 7279 | 118 | 1.01 (n=5, max 1.03) |

**scan-comb / optimal / n1** (22 common tasks; left out for low coverage: astar-lmcp)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-hmax | 11s | 5633 | 172 | 1.00 (n=22, max 1.00) |

**scan-comb / optimal / n2** (8 common tasks; left out for low coverage: astar-lmcp)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-hmax | 28s | 13k | 143 | 1.00 (n=8, max 1.00) |

**scan-comb / optimal / n3** (5 common tasks; left out for low coverage: astar-lmcp)

| config | search time (gmean) | expanded (gmean) | peak mem MB (max) | cost / opt |
|---|---|---|---|---|
| astar-hmax | 58s | 24k | 180 | 1.00 (n=5, max 1.00) |

## Optimal cost agreement

35 problems solved optimally; 0 of them by more than one model. All optimal costs agree across configs and models.

## Translation (per model and problem set)

| model | set | problems | translate s (median / max) | operators (median / max) | translate failures |
|---|---|---|---|---|---|
| scan-comb | n1 | 24 | 24.6 / 29.3 | 18k / 18k | 0 |
| scan-comb | n2 | 24 | 28.6 / 32.6 | 18k / 18k | 0 |
| scan-comb | n3 | 24 | 31.7 / 33.7 | 18k / 18k | 0 |

## Per-problem detail (search time, cost)

