# Multi-gem pilot: classic Fast Downward, scan-comb

First runs of the `_multigem` domains (several target gems, all must be
collected).

**Setup**

- Machine and limits: the VM (4 cores, 2.10 GHz Xeon), 300 s / 3 GB per run, 4 jobs at a time.
- Planner: upstream Fast Downward 24.06.1, translator `inv0`.
- Model: classic scan-comb only. It's the classic model that scales; the others time out on level 1.
- Configs: lama-first (satisficing), astar-hmax and astar-lmcp (optimal).
- Problems (`fd_sweep.py --multigem --groups A`):
  - `n1`: the 24 level-1 problems of the main sweep.
  - `n2`, `n3`: the same problems with one or two extra target gems.

Full tables are in `report_classic.md`.

## Coverage (solved / 24)

| config | 1 target | 2 targets | 3 targets |
|---|---|---|---|
| lama-first | 24 | 17 (7 TO) | 14 (10 TO) |
| astar-hmax | 22 (2 TO) | 8 (16 TO) | 5 (19 TO) |
| astar-lmcp | 7 (17 MO) | 0 (24 MO) | 0 (24 MO) |

One extra target cuts optimal coverage from 22 to 8.

## Consistency

- **One target:** runs with one target match the single-target sweep
  (`../sweep_results_v2`) in status, cost and expansions on 68 of 72 runs.
  The other 4 differ only in which limit a failing run hit first, near the
  300 s boundary:
  - 3 astar-lmcp runs ran out of memory instead of time.
  - 1 astar-hmax run solved within the limit instead of timing out.
- **More targets never make a plan cheaper:** no optimum gets cheaper when a
  target is added.
- **lama-first is never below the optimum.**

## What still solves optimally with 2–3 targets

These are mostly problems where the extra targets lie on or near the route to
the first one.

Optimal cost for 1 → 2 → 3 targets:

| start → first target | 1 target | 2 targets | 3 targets |
|---|---|---|---|
| s003 → t016 | 33 | 33 | 34 |
| s007 → t004 | 8 | 35 | 35 |
| s011 → t010 | 14 | 17 | 41 |
| s009 → t010 | 3 | 14 | 44 |

On level 1, gem 13 sits on the row the route to gem 16 crosses, and gem 17 is
directly below gem 16. So "targets 13, 16, 17" costs 34, exactly like
"target 17" alone, with the same search.

astar-hmax expansions grow fast when the targets are apart:

| start → first target | 1 target | more targets |
|---|---|---|
| s012 → t010 | 2.3k | 77k (2 targets) |
| s017 → t013 | 2.6k | 66k (2 targets) |
| s011 → t010 | 3.4k | 99k (3 targets) |

Classic search manages about 450 expansions per second here. Each expansion
is one physics step, about 117 per move on this model. So 300 s covers only
about 1–2k agent decisions.

## Reading

- **hmax** gives the cost of the farthest target, not of the whole tour. The
  optimal search has to close the gap between that and the true optimum
  without guidance. It works only while that gap is small, as on the
  one-target problems with blind search (at most cost 10–15).
- **Landmark cost partitioning** (astar-lmcp) could in principle add the
  targets up. It already ran out of memory on 17 of 24 one-target problems,
  and on every problem with more.
- **Forced actions** (fork, fixpoint build, `lazy-astar-hmax-tb`) evaluate
  only agent decision states. With one target that was 35/40 on large
  problems, against 31 for classic. Per second they cover roughly 50–100×
  more agent decisions than classic does here, so they should get further
  with 2–3 targets. Run on the M5 Pro:

  ```bash
  python3 tools/benchmarking/fd_sweep.py --fd <fixpoint build> --fa --multigem --groups A,C --jobs 12 --host m5pro
  ```
