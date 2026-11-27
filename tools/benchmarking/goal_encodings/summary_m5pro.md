# Goal encodings on m5pro: "any n gems" (count) vs "these n gems" (named)

Rows: [goal_encodings_m5pro.csv](goal_encodings_m5pro.csv), from
`tools/benchmarking/compare_goal_encodings.py` on host m5pro (Apple M5 Pro, 48 GB, macOS).

- Domains: `pddl/test_domains_target/domain_FA_scanner_combined_{gemcount,multigem}.pddl` @ 868a67c (clean).
- Planner: `planners/fast-downward` @ 28c32a9fa (eager search `forced_actions=true`) plus the local
  `FD_STATE_DUMP` gate in `state_dump.{cc,h}`. The harness sets `FD_STATE_DUMP=0`.
- Limits: satisficing search 300 s (`lazy_greedy([ff()], preferred=[ff()])`), optimal search 600 s.
  Memory is capped at 16 GB by the RSS watchdog, with no FD memory flags. The highest peak was 10.1 GB,
  so nothing hit the cap.
- Optimal configs:
  - `astar-hmax-fa` = `astar(hmax(), forced_actions=true)`
  - `lazy-astar-hmax-tb` = `let(h, hmax(), lazy(tiebreaking([sum([g(), h]), h]), reopen_closed=true))`
- Named targets are the gems that the count satisficing plan collected (row-major ordinals).
  "Any n" is therefore <= "these n", and the two problems can have different optima.
- Lazy search prints no initial h and no f layers. FD prints no expansion count on a timeout. For a
  timed-out A* run, last f is the best lower bound it proved.

Levels:
- `bd_levels.txt` line 1: 22x40, 18 gems, nearest gem at cost 8.
- `bd_levels.txt` line 3: 22x40, 24 gems, nearest gem at cost 4.
- Line 11 was skipped: it is relaxed-unsolvable with the target-gem goal.

## Line 1

count (any n):

| n | sat cost | h0 | A* hmax-fa | last f | A* time | lazy hmax-tb | lazy time |
|---|---------:|---:|------------|-------:|--------:|--------------|----------:|
| 1 | 8  | 8  | 8 (9 exp) | 8  | 1.6 s | 8 (12 exp) | 1.5 s |
| 2 | 30 | 9  | timeout   | 17 | 604 s | timeout    | 603 s |
| 3 | 52 | 10 | timeout   | 17 | 602 s | timeout    | 602 s |
| 4 | 56 | 11 | timeout   | 18 | 602 s | timeout    | 602 s |
| 5 | 60 | 12 | timeout   | 19 | 602 s | timeout    | 603 s |

named (these n):

| n | target gems | sat cost | h0 | A* hmax-fa | last f | A* time | lazy hmax-tb | lazy time |
|---|-------------|---------:|---:|------------|-------:|--------:|--------------|----------:|
| 1 | 1          | 8  | 8  | 8 (9 exp)    | 8  | 1.7 s | 8 (12 exp)    | 1.6 s |
| 2 | 1+2        | 28 | 24 | 26 (306 exp) | 26 | 6.5 s | 26 (1023 exp) | 7.3 s |
| 3 | 1+2+5      | 48 | 35 | timeout      | 40 | 602 s | timeout       | 602 s |
| 4 | 1+2+4+5    | 52 | 40 | timeout      | 43 | 602 s | timeout       | 602 s |
| 5 | 1+2+5+7+12 | 56 | 40 | timeout      | 44 | 602 s | timeout       | 603 s |

## Line 3

count (any n):

| n | sat cost | h0 | A* hmax-fa     | last f | A* time | lazy hmax-tb   | lazy time |
|---|---------:|---:|----------------|-------:|--------:|----------------|----------:|
| 1 | 4  | 4 | 4 (5 exp)      | 4  | 0.9 s   | 4 (6 exp)      | 0.9 s   |
| 2 | 20 | 5 | 16 (3247 exp)  | 16 | 23.3 s  | 16 (6503 exp)  | 18.9 s  |
| 3 | 27 | 6 | 18 (6231 exp)  | 18 | 41.5 s  | 18 (13473 exp) | 34.9 s  |
| 4 | 28 | 7 | 22 (24650 exp) | 22 | 175.9 s | 22 (57175 exp) | 142.8 s |
| 5 | 32 | 8 | timeout        | 24 | 603 s   | timeout        | 602 s   |

named (these n):

| n | target gems | sat cost | h0 | A* hmax-fa     | last f | A* time | lazy hmax-tb   | lazy time |
|---|-------------|---------:|---:|----------------|-------:|--------:|----------------|----------:|
| 1 | 4           | 4  | 4  | 4 (5 exp)      | 4  | 0.9 s   | 4 (6 exp)      | 0.9 s  |
| 2 | 4+7         | 16 | 10 | 16 (602 exp)   | 16 | 4.0 s   | 16 (1155 exp)  | 3.8 s  |
| 3 | 4+7+8       | 25 | 17 | 23 (2396 exp)  | 23 | 17.0 s  | 23 (5760 exp)  | 14.4 s |
| 4 | 4+7+8+10    | 27 | 18 | 24 (4005 exp)  | 24 | 30.4 s  | 24 (10061 exp) | 25.9 s |
| 5 | 4+7+8+10+12 | 32 | 22 | 28 (11386 exp) | 28 | 103.5 s | 28 (29877 exp) | 85.5 s |

## Reading

- **Count's initial hmax equals the nearest-gem cost + n − 1 exactly on both levels:** 8..12 on
  line 1 and 4..8 on line 3. Under delete relaxation the nearest gem never disappears, so every
  further counter step costs one more move into the same cell.
- **Named's initial hmax is 2.0–3.6x count's for n ≥ 2:** 24/35/40/40 vs 9..12 on line 1, and
  10/17/18/22 vs 5..8 on line 3. hmax of a conjunction is the maximum over its atoms, so this is
  the relaxed cost of the hardest single target, not a sum. That is why it stays at 40 from n=4 to
  n=5 on line 1.
- At n=4 on line 3, h0 is 32% of the optimum for count (7/22) and 75% for named (18/24).

Where the data disagrees with the expectation:

- **"Count stalls for n ≥ 2" holds on line 1 only.**
  - On line 1, every count run with n ≥ 2 times out with last f 17–19, against plans of cost 30–60.
  - On line 3, count proves the optimum for n = 2, 3, 4 (16, 18, 22) and stalls only at n=5
    (last f 24).
  - Where it does solve, it needs 2.6–6.2x more A* expansions than named (3247 vs 602,
    6231 vs 2396, 24650 vs 4005), even though named has an equal or higher optimum (16 vs 16,
    23 vs 18, 24 vs 22).
- **"Named proves at least n=2" holds, but on line 1 it proves only n ≤ 2.**
  - On line 1, n = 3..5 time out with last f 40/43/44 against satisficing costs 48/52/56.
  - On line 3, named proves every n up to 5.

## Cross-check: main's counter on the older encoding (step 4)

Setup:
- Line 1, n=2, using main's `pddl/test_domains_target/domain_FA_scanner_combined.pddl` (85adeaa).
- `tools/plan.py` has no write-only option, so I ran the generator it selects with the same
  command: `problem_gen_domain_FA_scanner_combined.py LEVEL -p NAME --collect-gems 2`.
- Search: `astar(hmax(), forced_actions=true)`, `--overall-time-limit 600s`, no memory limit,
  `FD_STATE_DUMP=0`.
- Main's working tree has an uncommitted edit to that domain: it folds `move_into_target_gem` into
  `move_into_gem`. I ran both that version and the committed version.

| main domain     | operators (forced) | h0 hmax | last f        | result  | peak RSS |
|-----------------|-------------------:|--------:|---------------|---------|---------:|
| working tree    | 23250 (9823)       | 9       | 16 (at 560 s) | timeout | 4.4 GB   |
| committed (HEAD)| 23250 (9823)       | 9       | 15 (at 99 s)  | timeout | 2.9 GB   |
| this branch's gemcount port | 23438  | 9       | 17            | timeout | 6.2 GB   |

The same h0 of 9 and the same stall happen on main's own counter. The weak count heuristic comes
from the counter itself, not from the port.

These two runs overlapped with the harness's line 1 n=2–3 rows. FD is single-threaded on an
18-core machine, but times and last f near the 600 s limit may be slightly affected.

## Checks

**Equivalence (step 2):** `tools/sim_check/multigem_check.py --cases 100`.
- multigem vs `domain_FA_scanner_combined`: 100 pass, 0 fail. By target count: 59 with 1,
  27 with 2, 14 with 3. 35 runs collected at least one target.
- gemcount vs multigem with every gem a target: 100 pass, 0 fail. 32 runs reached N gems.

**Native simulator (step 5):** main's `tools/validate_pddl.py`, with absolute paths and the level
`.txt` next to each problem. Each plan was rerun with `$FD/fast-downward.py` on the problem from the
matching generator. The target objects and forall effects caused no problems.

| plan                                              | cost | result               |
|---------------------------------------------------|-----:|----------------------|
| line 1 n=2 named (1+2), A* optimal                | 26   | `[OK] traces match`  |
| line 1 n=2 count, optimal                         | –    | not solved (both configs timed out) |
| line 1 n=2 count, satisficing plan instead        | 31*  | `[OK] traces match`  |
| line 3 n=5 named (4+7+8+10+12), largest solved n  | 28   | `[OK] traces match`  |
| line 3 n=2 count, A* optimal (extra)              | 16   | `[OK] traces match`  |
| line 1 n=1 count and named, A* optimal (extra)    | 8    | `[OK] traces match`  |

\* The harness's count n=2 satisficing plan cost 30. My rerun used FD's default translator options,
and the harness passes `--invariant-generation-max-candidates 0`. The line 3 reruns used the
harness's options and reproduce its cost, h0 and expansions exactly.
