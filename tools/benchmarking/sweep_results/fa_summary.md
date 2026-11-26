# Forced-action (FA) sweep: summary

Full tables:
- `compare_fa_vs_classic_m5pro.md`: FA vs classic, both on the M5 Pro with the same fork binary.
- `compare_fa_vs_classic.md`: classic coverage from the VM, including the eager / A* configs, and classic times from the M5 Pro.
- `report_fa.md`, `report_classic.md` (VM) and `report_classic_m5pro.md`.
- Fixpoint build re-sweep:
  - `compare_fa_fixpt_vs_fa.md`: fixpoint build vs the original FA build (same machine, same runs).
  - `compare_fa_fixpt_vs_classic_m5pro.md`: fixpoint build vs classic, same machine.
  - `report_fa_fixpt.md`.

Regenerate with:
- `analyze_sweep.py [--variant=inv0+fa] [--hosts=vm|m5pro]`
- `compare_sweep.py --classic=inv0@vm --timing=inv0@m5pro --speed=2`
- `compare_sweep.py --classic=inv0@m5pro`
- `compare_builds.py --base=inv0+fa@m5pro --new=inv0+fa+fixpt@m5pro`
- `compare_sweep.py --fa=inv0+fa+fixpt@m5pro --classic=inv0@m5pro --timing=inv0@m5pro`
- `analyze_sweep.py --variant=inv0+fa+fixpt --hosts=m5pro`

## Setup

- **FA**: `results_m5pro_fa.csv`, 1944 runs: groups A, B and C, with all 9 LazySearch configs on every problem of every model.
  - Machine and limits: Apple M5 Pro, 12 parallel jobs, 300 s search (CPU time), 3 GB.
  - Planner: fork `planners/fast-downward` @ 3afd349, built natively (arm64). It carries the local `FD_STATE_DUMP` gate; without it the fork logs every search state as JSON. The sweep sets `FD_STATE_DUMP=0`.
  - Memory limit: macOS cannot set memory limits, so `fd_sweep.py` kills a process tree above 3 GB RSS and records a memout.
  - Sleep: jobs 1–210 ran on AC with the machine awake. The last six (order-free separated) overlapped a sleep. That only affects their wall-clock columns, because search time and the limit are CPU time.
- **FA, fixpoint build**: `results_m5pro_fa_fixpt.csv` (variant `inv0+fa+fixpt`), 1944 runs. Identical job list, configs, machine, parallelism and limits.
  - Planner: fork branch `claude/lazy-forced-fixpoints` @ 52938c8b5, built natively (arm64). It includes the `FD_STATE_DUMP` gate as a commit, so the build has no local changes.
  - The Mac stayed on AC and awake for the whole run (4.2 h).
- **Classic, same machine**: `results_m5pro.csv`, 1200 runs. Same fork binary, machine, parallelism and configs, on AC.
  - Group C here is the classic job list: the small levels, plus gbfs-ff on the first 6 large problems.
  - For roughly the first hour (of about 4), another session ran 4–5 extra planners at the same time, so 15–16 planners shared 18 cores. That inflates a few early group A times slightly. Coverage and expansions are unaffected.
- **Classic, VM**: `results_vm.csv`, 1392 runs, upstream FD 24.06.1 on a 4-core Xeon VM. It also has the eager and A* configs.
- **Fork classic is not upstream classic.** The fork is based on FD from around March 2024 (before 24.06.1) plus its forced-action code. On the same tasks as upstream 24.06.1:
  - gbfs-ff, gbfs-add and wastar3-ff expand 18–24% more states, with coverage within ±3.
  - gbfs-cea and gbfs-cg are unchanged.
  - lama-first expands 1.78× more and solves far fewer problems: 14 instead of 36 large problems on scan-comb.
  - So the cleanest FA vs classic comparison is the same-machine one: same binary, only the forced semantics differ. Where the VM is better (lama-first), the table below shows that too.
- **Hardware ratio**: the translator (same Python, identical tasks, identical operator counts) is 1.86× faster per job on the M5 Pro than on the VM.
- **Configs**:
  - In `--fa` mode only LazySearch applies `__FORCED__` actions, so eager-gbfs-ff and astar-* are not run under FA.
  - New optimal configs: `lazy-astar-blind` and `lazy-astar-hmax` (`lazy_wastar(w=1)`; `tools/plan.py --optimal` uses it with blind).
  - `lazy-astar-hmax-tb` = `let(h, hmax(), lazy(tiebreaking([sum([g(), h]), h]), reopen_closed=true))`, a lazy A* that breaks f-ties on h, as `astar()` does.

## Fixpoint build re-sweep

The fork's `claude/lazy-forced-fixpoints` branch registers only the end state of each forced chain, not every intermediate physics state. That removes FA's memory bottleneck. The search is otherwise the same: same plans and expansions on 1277 of the 1284 runs both builds solve. Full tables: `compare_fa_fixpt_vs_fa.md` and `compare_fa_fixpt_vs_classic_m5pro.md`.

**Correctness.**
- All optimal costs agree: 45 problems, across both FA builds, classic, all models and configs. That is one more problem than before, L03 t002.
- No problem is solved anywhere and proved plan-less anywhere else.
- Plans:
  - 1283 of the 1284 runs both builds solve have the same plan cost and length.
  - The exception is lama-first, scan-comb, L08 t001: cost 20 → 22. It is a satisficing config, so a different plan is allowed.
  - 7 runs expand 1–4% more states, all wastar3-ff, lazy-astar-hmax and that lama-first run. None expands fewer.
- **"evaluated" changed meaning.** The fixpoint build counts only the registered decision states (about expanded + 1). The original build counted every forced intermediate state.

**What changed, all 1944 runs:**
- Memouts: 477 → 2. The two left are gbfs-cg on scan-comb, whose own heuristic cache (cg, max_cache_size 1M) uses 1–2 GB.
- Of the former memouts, 438 now hit the 300 s time limit and 37 are solved.
- Former timeouts: 4 are now solved.
- No run that was solved before fails now.
- Solved large-problem runs: 924 → 965.
- The limit is now time: about 43 of the 45.5 h of total search time are runs at the 300 s limit.

**Coverage on large problems** (40 solvable), original FA → fixpoint FA; unchanged cells show one number:

| model | gbfs-ff | gbfs-add | gbfs-cea | gbfs-cg | wastar3-ff | lama-first | lazy-astar-blind | lazy-astar-hmax | lazy-astar-hmax-tb |
|---|---|---|---|---|---|---|---|---|---|
| scan-comb | 40 | 40 | 40 | 6 → 8 | 40 | 39 → 40 | 8 → 9 | 19 → 24 | 34 → 35 |
| scan-sep | 38 | 36 → 38 | 36 → 38 | 5 → 8 | 36 → 39 | 36 → 39 | 5 → 8 | 5 → 8 | 7 → 8 |
| orderfree-comb | 40 | 40 | 40 | 8 | 40 | 40 | 8 | 20 → 24 | 34 → 35 |
| orderfree-sep | 31 | 32 | 30 | 5 → 7 | 34 | 30 → 33 | 6 → 7 | 8 | 8 |

**Speed and memory on runs both builds solve** (large problems, geometric-mean search time, original → fixpoint):
- **scan-sep** gains most, 2.1–8.6× faster:
  - gbfs-ff 4.4×, lama-first 5.5×, lazy-astar-hmax-tb 6.3×, lazy-astar-blind 8.6×.
  - This model had the most intermediate states per expansion (1251).
- **scan-comb**: 1.2–3.3× faster (gbfs-ff 1.7×, hmax-tb 2.0×, blind 3.3×).
- **orderfree-sep**: 1.1–1.7× faster.
- **orderfree-comb**: about the same for the satisficing configs (1.0×), and 1.1–1.5× faster for the optimal ones.
- Peak memory on solved runs is now a median of 45–170 MB per config, with a maximum of 180 MB, except gbfs-cg (1.1–1.9 GB, from its cache). Before, single runs reached 2–3 GB.
- On runs that fail, the fixpoint build's peak is at most 1.2 GB (lazy-astar-blind, orderfree-comb), again except gbfs-cg.

**Against classic on the same machine** (large tasks both solve; fixpoint FA, with the original FA in brackets):

| config | scan-comb | scan-sep |
|---|---|---|
| gbfs-ff | 130× (79×) | 508× (116×) |
| gbfs-cea | 222× (184×) | 876× (438×) |
| lama-first | 129× (56×) | 765× |
| lazy-astar-hmax-tb | 71× (35×) | 265× (44×) |
| lazy-astar-blind | 8× (2×) | 23× (3×) |

Blind search now gains 8–23× instead of 2–3×. So most of the original build's remaining cost was registering the intermediate states, not computing the heuristic.

**Optimal under the fixpoint build.**
- `lazy-astar-hmax-tb` is still the setting that scales: 35/40 on scan-comb and orderfree-comb, against classic's 31/40 on scan-comb.
- Every FA optimal cost equals the classic optimum (41/41 for hmax-tb).
- The separated models stay at 7–8/40 for every optimal config. Their runs now time out instead of running out of memory.

**Order-free models.**
- orderfree-comb has the same coverage as scan-comb.
- It is no longer clearly faster: pairwise 0.61–1.49× of scan-comb's time; it was 0.47–0.75× with the original build. scan-comb gained more from fixpoints.
- orderfree-sep is the weakest model: 2.5–8× slower than scan-comb for the satisficing configs and up to 40× for hmax-tb, with the lowest satisficing coverage (30–34/40).

**Satisficing quality** is unchanged: mean cost / optimum 1.01–1.04. On scan-sep, gbfs-add, gbfs-cea and lama-first are at 1.09, each because of one problem at 3.25–3.40.

## Findings (original FA build)

**Correctness.**
- No problem is solved by one model or side and proved plan-less by another.
- All optimal costs agree across sides, models and configs (44 problems). Every FA optimal cost equals the classic optimum where classic has one (41/41).
- No satisficing plan is cheaper than an optimum.
- No-plan problems: testing_level_2, testing_level_3, L11 t115 and L11 t168. Under FA, scan-comb and orderfree-comb also prove the L11 ones.

**Coverage on large problems** (40 solvable: l1 24 + other 16), classic VM / classic same machine → FA:

| model | gbfs-ff | gbfs-cea | wastar3-ff | lama-first | optimal |
|---|---|---|---|---|---|
| scan-comb | 38 / 38 → 40 | 30 / 36 → 40 | 38 / 38 → 40 | 36 / 14 → 39 | astar-hmax 31 (VM), hmax-tb 31 → 34 |
| scan-sep | 32 / 31 → 38 | 11 / 10 → 36 | 31 / 28 → 36 | 5 / 5 → 36 | astar-blind 5 (VM), hmax-tb 4 → 7 |
| orderfree-comb | 0/6 / 0/6 → 40 | – → 40 | – → 40 | – → 40 | astar-hmax 0/6 (VM) → hmax-tb 34 |
| orderfree-sep | 0/6 / 0/6 → 31 | – → 30 | – → 34 | – → 30 | astar-hmax 0/6 (VM) → hmax 8 / hmax-tb 8 |

Small problems: every FA config solves all 10 solvable problems on every model.

**Effort on tasks both sides solve** (large problems, same config, same machine; classic → FA):

| model / config | tasks | search time (geometric mean) | expansions |
|---|---|---|---|
| scan-comb gbfs-ff | 38 | 24 s → 0.30 s (79×) | 5411 → 32 |
| scan-comb gbfs-cea | 36 | 126 s → 0.69 s (184×) | |
| scan-comb lama-first | 14 | 14 s → 0.25 s (56×) | |
| scan-comb lazy-astar-hmax-tb | 31 | 14 s → 0.39 s (35×) | |
| scan-comb lazy-astar-blind | | 2× | |
| scan-sep gbfs-ff | 31 | 86 s → 0.74 s (116×) | 26k → 28 |
| scan-sep gbfs-cea | 10 | 174 s → 0.40 s (438×) | |
| scan-sep lazy-astar-hmax-tb | 4 | 24 s → 0.54 s (44×) | |
| scan-sep lazy-astar-blind | | 3× | |

FA does not reach fewer states. "Evaluated", which counts the forced intermediate states, is about the same as classic (scan-comb gbfs-ff: 7.0k vs 5.4k). The difference is that FA computes the heuristic only at agent decision states, which are 1 in 126 to 1 in 1251 of the states. That is why blind search gains only 2–3×.

**Optimal.**
- `lazy-astar-hmax-tb` is the FA optimal setting that scales: 34/40 large problems on scan-comb and orderfree-comb. The classic best is 31/40 on scan-comb (VM astar-hmax, and the same with classic hmax-tb on the M5 Pro) and 0/6 on order-free.
- The settings the fork's `tools/plan.py` uses today scale poorly:
  - `lazy_wastar` breaks f-ties in FIFO order and sweeps the whole f = C* layer (`lazy-astar-hmax` 19–20/40).
  - Blind solves 8/40.
- FA proves optima for all 41 problems classic proved, plus 3 more.
- On the separated models, every FA optimal config runs out of memory (at most 7–8/40).

**Satisficing quality** (cost / optimum) is essentially unchanged: mean 1.00–1.03 under FA, against 1.00–1.06 for classic. The exception is scan-sep gbfs-add and gbfs-cea at 1.09, because of one problem at 3.40.

**Order-free models under FA.**
- The interleaving blow-up is gone.
- orderfree-comb has the same coverage as scan-comb and is the fastest model: 0.47–0.75× of scan-comb's search time on the same tasks, for every config.
- orderfree-sep is the weakest: 2–6× slower than scan-comb for the satisficing configs, with more memouts.

**What limits FA: memory.**
- 477 FA runs hit the memory limit, against 83 timeouts (plus 100 exhausted runs on the no-plan problems).
- The fork's `apply_forced_actions` registers every intermediate forced state, at about 1–1.3 KB each. Per expansion that is 126 states for orderfree-comb, 225 for scan-comb, 611 for orderfree-sep and 1251 for scan-sep.
- Fork branch `claude/lazy-forced-fixpoints` (52938c8b5, from 28c32a9, local, not pushed) registers only the end state of each forced chain. On group B (gbfs-ff and lazy-astar-hmax-tb):
  - No coverage was lost; hmax-tb went from 17 to 18 solved.
  - Peak memory per run is at most 191 MB instead of 3 GB.
  - Search was 3.5–4.5× faster on commonly solved tasks.
  - Plans are byte-identical on all 336 small-level runs.
  - The former memouts now hit the 300 s time limit instead.
  - The full re-sweep (all groups) is in the section above: 477 memouts → 2, no lost solves, 41 more large-problem solves.
