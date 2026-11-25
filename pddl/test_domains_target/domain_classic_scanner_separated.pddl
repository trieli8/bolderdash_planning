; Generated test domain variant
; variant: domain_scanner_separated.pddl
; source: pddl/domain_cellscan_separated.pddl
; regenerate with: python pddl/make_target_variants.py
; Boulder Dash (stonesngems engine) - row-gated scanner, separated check/act actions.
;
; Mirrors stonesandgem/src/stonesngems_base.cpp (RNDGameState::apply_action)
; exactly for agent / empty / dirt / stone / gem / walls:
;   * each tick the agent acts first, then cells are updated in row-major
;     order; an object that moved into a cell later in the scan (fall, roll
;     right, push) is marked updated and skipped for the rest of the tick
;     (engine: has_updated);
;   * a falling stone OR gem landing on the agent kills it;
;   * only resting stones/gems and brick walls (id 18) are rounded; steel
;     walls, exits and the level border are not, and the agent is not;
;   * pushed stones are skipped in the push tick and are falling iff the cell
;     below their destination is empty;
;   * the target-gem marker travels with its gem.
;
; Style: the scan pointer visits the open (non-wall) cells of a row one at a
; time.  For a stone/gem the engine's decision is taken by separate check
; actions
;   check_fall       -> can_fall | not_fall | fall_on_agent
;   check_roll_left  -> can_roll_left | not_roll_left
;   check_roll_right -> can_roll_right | not_roll_right
; followed by one act action (stone_/gem_ fall / roll, or stone_gem_settle)
; and advance_scan.  Cells without a pending object are passed by skip_cell /
; skip_updated.
;
; Speed: walls are not in the scan chain, and every row has a gate that skips
; the whole row in one step unless something in the row or the row below
; changed since the row was last scanned (then every object in it provably
; stays put); the same gating as pddl/domain_rowscan.pddl.
;
; Agent actions are the move_* actions; every other action is physics and is
; deterministic: while a tick is in progress exactly one of them is
; applicable and no move_* action is.  The test-domain variants
; (pddl/test_domains_target/domain_{classic,FA}_scanner_separated.pddl) are
; generated with
;   python pddl/make_target_variants.py
;
; Problems: pddl/problem_gen_cellscan.py
; Differential test against the engine: tools/sim_check/fuzz.py
(define (domain mine-tick-gravity)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :conditional-effects :action-costs)

  (:types
    pos - object
    cell row - pos
    real-cell border-cell - cell
  )

  (:functions
    (total-cost)
  )

  (:predicates
    ;; ---- static ----
    (up ?from ?to - cell)              ; ?to is directly above ?from
    (down ?from ?to - cell)            ; ?to is directly below ?from
    (right-of ?from ?to - cell)        ; ?to is directly right of ?from
    (brick ?c - cell)                  ; any wall inside the level
    (rounded-wall ?c - cell)           ; brick wall (id 18): things roll off it
    (flat-wall ?c - cell)              ; steel wall / exit / level border
    (cell-row ?c - cell ?r - row)
    (row-above ?r ?above - row)
    (first-row ?r - row)               ; first gate of the scan
    (next-row ?r ?next - row)          ; gate -> next gate (or done)
    (row-start ?r - row ?c - real-cell); gate -> first open cell of the row
    (next-pos ?c - real-cell ?next - pos) ; open cell -> next cell / next gate / done
    (scan-done ?r - row)               ; the idle sentinel

    ;; ---- cell contents (exactly one per cell inside the level) ----
    (agent-at ?c - cell)
    (empty ?c - cell)
    (dirt ?c - cell)
    (stone ?c - cell)
    (gem ?c - cell)
    (target-gem ?c - cell)
    (falling ?c - cell)                ; stone/gem state; resting otherwise

    ;; ---- scan bookkeeping ----
    (scan-at ?p - pos)
    (updated ?c - cell)                ; object moved here this tick (ahead of the scan)
    (row-dirty ?r - row)               ; row must be scanned next time

    ;; ---- per-cell decision phases (global: one cell at a time) ----
    (check_fall)
    (check_roll_left)
    (check_roll_right)
    (ready_to_move)
    (can_fall)
    (can_roll_left)
    (can_roll_right)
    (acted)

    ;; ---- high level ----
    (agent-alive)
    (got-gem)
  )

  ;; ======================================================================
  ;; AGENT MOVEMENT (only between ticks: the scan pointer rests on done)
  ;; The vacated cell can let objects in its row and the row above move.
  ;; ======================================================================

  (:action move_noop
    :parameters (?d ?r0 - row)
    :precondition (and (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0))
    :effect (and
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )

  (:action move_empty
    :parameters (?from ?to - real-cell ?d ?r0 ?rf ?rfa - row)
    :precondition (and
      (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (empty ?to)
      (cell-row ?from ?rf) (row-above ?rf ?rfa))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (empty ?to)) (agent-at ?to)
      (row-dirty ?rf) (row-dirty ?rfa)
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )

  ;; Move into dirt (mines it).
  (:action move_into_dirt
    :parameters (?from ?to - real-cell ?d ?r0 ?rf ?rfa - row)
    :precondition (and
      (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (dirt ?to)
      (cell-row ?from ?rf) (row-above ?rf ?rfa))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (dirt ?to)) (agent-at ?to)
      (row-dirty ?rf) (row-dirty ?rfa)
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )

  ;; Collect a gem (resting or falling); the target gem sets got-gem.
  (:action move_into_gem
    :parameters (?from ?to - real-cell ?d ?r0 ?rf ?rfa - row)
    :precondition (and
      (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (gem ?to)
      (cell-row ?from ?rf) (row-above ?rf ?rfa))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (gem ?to)) (not (falling ?to))
      (when (target-gem ?to) (and (not (target-gem ?to)) (got-gem))) (agent-at ?to)
      (row-dirty ?rf) (row-dirty ?rfa)
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )


  ;; Horizontal push of a resting stone into an empty cell.  The engine marks
  ;; the pushed stone updated (it does not move again this tick) and makes it
  ;; falling iff the cell below its destination is empty.
  (:action move_push_rock
    :parameters (?from ?to ?stone_dest - real-cell ?below - cell ?d ?r0 ?rf ?rfa - row)
    :precondition (and
      (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0)
      (agent-at ?from)
      (or (and (right-of ?from ?to) (right-of ?to ?stone_dest))
          (and (right-of ?to ?from) (right-of ?stone_dest ?to)))
      (stone ?to) (not (falling ?to))
      (empty ?stone_dest)
      (down ?stone_dest ?below)
      (cell-row ?from ?rf) (row-above ?rf ?rfa))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (stone ?to)) (agent-at ?to)
      (not (empty ?stone_dest)) (stone ?stone_dest) (updated ?stone_dest)
      (when (empty ?below) (falling ?stone_dest))
      (row-dirty ?rf) (row-dirty ?rfa)
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )

  ;; ======================================================================
  ;; ROW GATES
  ;; ======================================================================

  (:action row_enter
    :parameters (?r - row ?c - real-cell)
    :precondition (and (scan-at ?r) (row-dirty ?r) (row-start ?r ?c))
    :effect (and (not (scan-at ?r)) (not (row-dirty ?r)) (scan-at ?c) (check_fall))
  )

  (:action row_skip
    :parameters (?r ?next - row)
    :precondition (and (scan-at ?r) (not (row-dirty ?r)) (next-row ?r ?next))
    :effect (and (not (scan-at ?r)) (scan-at ?next))
  )

  ;; ======================================================================
  ;; SCANNER MOVEMENT
  ;; ======================================================================

  ;; Object that moved here earlier this tick: skip it, and make sure its row
  ;; is scanned again next tick.
  (:action skip_updated
    :parameters (?c - real-cell ?next - pos ?r - row)
    :precondition (and (scan-at ?c) (next-pos ?c ?next) (check_fall) (updated ?c) (cell-row ?c ?r))
    :effect (and (not (updated ?c)) (row-dirty ?r) (not (scan-at ?c)) (scan-at ?next))
  )

  ;; Nothing to do here: no stone/gem.
  (:action skip_cell
    :parameters (?c - real-cell ?next - pos)
    :precondition (and
      (scan-at ?c) (next-pos ?c ?next) (check_fall)
      (or (empty ?c) (dirt ?c) (agent-at ?c)))
    :effect (and (not (scan-at ?c)) (scan-at ?next))
  )

  ;; The stone/gem of this cell has been handled.
  (:action advance_scan
    :parameters (?c - real-cell ?next - pos)
    :precondition (and (scan-at ?c) (next-pos ?c ?next) (acted))
    :effect (and (not (acted)) (check_fall) (not (scan-at ?c)) (scan-at ?next))
  )

  ;; ======================================================================
  ;; SCANNER CHECKS (stone or gem that has not moved this tick)
  ;; ======================================================================

  (:action can_fall
    :parameters (?c - real-cell ?down - cell)
    :precondition (and
      (scan-at ?c) (check_fall)
      (or (stone ?c) (gem ?c)) (not (updated ?c))
      (down ?c ?down) (empty ?down))
    :effect (and (not (check_fall)) (can_fall) (ready_to_move))
  )

  ;; Falling stone or gem lands on the agent: explosion, agent dies.
  (:action fall_on_agent
    :parameters (?c - real-cell ?down - cell)
    :precondition (and
      (scan-at ?c) (check_fall)
      (or (stone ?c) (gem ?c)) (not (updated ?c)) (falling ?c)
      (down ?c ?down) (agent-at ?down))
    :effect (and (not (check_fall)) (not (agent-alive)) (acted))
  )

  (:action not_fall
    :parameters (?c - real-cell ?down - cell)
    :precondition (and
      (scan-at ?c) (check_fall)
      (or (stone ?c) (gem ?c)) (not (updated ?c))
      (down ?c ?down)
      ;; below is not empty, and not the agent under a falling object
      ;; (written without negating agent-at: Fast Downward makes the agent
      ;; position one multi-valued variable and would split the negation)
      (or (and (not (falling ?c)) (not (empty ?down)))
          (dirt ?down) (stone ?down) (gem ?down) (rounded-wall ?down) (flat-wall ?down)))
    :effect (and (not (check_fall)) (check_roll_left))
  )

  ;; Roll left needs a rounded support (resting stone/gem or brick wall) and
  ;; empty left and down-left cells (engine: CanRollLeft, tried first).
  (:action can_roll_left
    :parameters (?c - real-cell ?down ?left ?down_left - cell)
    :precondition (and
      (scan-at ?c) (check_roll_left)
      (down ?c ?down) (right-of ?left ?c) (down ?left ?down_left)
      (or (rounded-wall ?down) (and (or (stone ?down) (gem ?down)) (not (falling ?down))))
      (empty ?left) (empty ?down_left))
    :effect (and (not (check_roll_left)) (can_roll_left) (ready_to_move))
  )

  (:action not_roll_left
    :parameters (?c - real-cell ?down ?left ?down_left - cell)
    :precondition (and
      (scan-at ?c) (check_roll_left)
      (down ?c ?down) (right-of ?left ?c) (down ?left ?down_left)
      ;; support not rounded (it is not empty here), or left side blocked
      (or (dirt ?down) (agent-at ?down) (falling ?down) (flat-wall ?down)
          (not (empty ?left))
          (not (empty ?down_left))))
    :effect (and (not (check_roll_left)) (check_roll_right))
  )

  (:action can_roll_right
    :parameters (?c - real-cell ?down ?right ?down_right - cell)
    :precondition (and
      (scan-at ?c) (check_roll_right)
      (down ?c ?down) (right-of ?c ?right) (down ?right ?down_right)
      (or (rounded-wall ?down) (and (or (stone ?down) (gem ?down)) (not (falling ?down))))
      (empty ?right) (empty ?down_right))
    :effect (and (not (check_roll_right)) (can_roll_right) (ready_to_move))
  )

  (:action not_roll_right
    :parameters (?c - real-cell ?down ?right ?down_right - cell)
    :precondition (and
      (scan-at ?c) (check_roll_right)
      (down ?c ?down) (right-of ?c ?right) (down ?right ?down_right)
      ;; support not rounded (it is not empty here), or right side blocked
      (or (dirt ?down) (agent-at ?down) (falling ?down) (flat-wall ?down)
          (not (empty ?right))
          (not (empty ?down_right))))
    :effect (and (not (check_roll_right)) (ready_to_move))
  )

  ;; ======================================================================
  ;; STONE / GEM ACTS (moves mark the rows that may react next tick)
  ;; ======================================================================

  ;; Fall one cell (the object below the scan is skipped when reached).
  (:action stone_fall
    :parameters (?c ?down - real-cell ?rc ?ra ?rb - row)
    :precondition (and (scan-at ?c) (ready_to_move) (can_fall) (stone ?c) (down ?c ?down)
      (cell-row ?c ?rc) (row-above ?rc ?ra) (cell-row ?down ?rb))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?down)) (stone ?down) (falling ?down) (updated ?down)
      (row-dirty ?rc) (row-dirty ?ra) (row-dirty ?rb)
      (not (ready_to_move)) (not (can_fall)) (acted))
  )

  (:action gem_fall
    :parameters (?c ?down - real-cell ?rc ?ra ?rb - row)
    :precondition (and (scan-at ?c) (ready_to_move) (can_fall) (gem ?c) (down ?c ?down)
      (cell-row ?c ?rc) (row-above ?rc ?ra) (cell-row ?down ?rb))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?down)))
      (not (empty ?down)) (gem ?down) (falling ?down) (updated ?down)
      (row-dirty ?rc) (row-dirty ?ra) (row-dirty ?rb)
      (not (ready_to_move)) (not (can_fall)) (acted))
  )

  ;; Roll left: the destination is behind the scan, so it needs no updated flag.
  (:action stone_roll_left
    :parameters (?c ?left - real-cell ?rc ?ra - row)
    :precondition (and (scan-at ?c) (ready_to_move) (can_roll_left) (stone ?c) (right-of ?left ?c)
      (cell-row ?c ?rc) (row-above ?rc ?ra))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?left)) (stone ?left) (falling ?left)
      (row-dirty ?rc) (row-dirty ?ra)
      (not (ready_to_move)) (not (can_roll_left)) (acted))
  )

  (:action gem_roll_left
    :parameters (?c ?left - real-cell ?rc ?ra - row)
    :precondition (and (scan-at ?c) (ready_to_move) (can_roll_left) (gem ?c) (right-of ?left ?c)
      (cell-row ?c ?rc) (row-above ?rc ?ra))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?left)))
      (not (empty ?left)) (gem ?left) (falling ?left)
      (row-dirty ?rc) (row-dirty ?ra)
      (not (ready_to_move)) (not (can_roll_left)) (acted))
  )

  ;; Roll right: the destination is the next cell of the scan, skipped there.
  (:action stone_roll_right
    :parameters (?c ?right - real-cell ?rc ?ra - row)
    :precondition (and (scan-at ?c) (ready_to_move) (can_roll_right) (stone ?c) (right-of ?c ?right)
      (cell-row ?c ?rc) (row-above ?rc ?ra))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?right)) (stone ?right) (falling ?right) (updated ?right)
      (row-dirty ?rc) (row-dirty ?ra)
      (not (ready_to_move)) (not (can_roll_right)) (acted))
  )

  (:action gem_roll_right
    :parameters (?c ?right - real-cell ?rc ?ra - row)
    :precondition (and (scan-at ?c) (ready_to_move) (can_roll_right) (gem ?c) (right-of ?c ?right)
      (cell-row ?c ?rc) (row-above ?rc ?ra))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?right)))
      (not (empty ?right)) (gem ?right) (falling ?right) (updated ?right)
      (row-dirty ?rc) (row-dirty ?ra)
      (not (ready_to_move)) (not (can_roll_right)) (acted))
  )

  ;; Cannot move: a falling object comes to rest (the row above may now roll
  ;; off it), a resting one stays.
  (:action stone_gem_settle
    :parameters (?c - real-cell ?rc ?ra - row)
    :precondition (and
      (scan-at ?c) (ready_to_move)
      (not (can_fall)) (not (can_roll_left)) (not (can_roll_right))
      (cell-row ?c ?rc) (row-above ?rc ?ra))
    :effect (and
      (when (falling ?c) (and (not (falling ?c)) (row-dirty ?ra)))
      (not (ready_to_move)) (acted))
  )
)
