; Generated test domain variant
; variant: domain_scanner_separated.pddl
; source: pddl/domain_cellscan_separated.pddl
; regenerate with: python pddl/make_target_variants.py
; Boulder Dash (stonesngems engine) - cell-by-cell scanner, separated check/act actions.
;
; Mirrors stonesandgem/src/stonesngems_base.cpp (RNDGameState::apply_action)
; exactly for agent / empty / dirt / stone / gem / walls:
;   * each tick the agent acts first, then every cell is visited in row-major
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
; Style: the scan pointer visits one cell at a time.  For a stone/gem the
; engine's decision is taken by separate check actions
;   check_fall       -> can_fall | not_fall | fall_on_agent
;   check_roll_left  -> can_roll_left | not_roll_left
;   check_roll_right -> can_roll_right | not_roll_right
; followed by one act action (stone_/gem_ fall / roll, or stone_gem_settle),
; and advance_scan.  Cells without a pending object are passed by skip_cell.
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
    (first-cell ?c - real-cell)        ; scan order: top-left ...
    (next-cell ?c1 - real-cell ?c2 - cell)
    (last-cell ?c - border-cell)       ; ... -> end-of-scan sentinel

    ;; ---- cell contents (exactly one per cell inside the level) ----
    (agent-at ?c - cell)
    (empty ?c - cell)
    (dirt ?c - cell)
    (stone ?c - cell)
    (gem ?c - cell)
    (target-gem ?c - cell)
    (falling ?c - cell)                ; stone/gem state; resting otherwise

    ;; ---- scan bookkeeping ----
    (scan-required)                    ; agent moved, tick not started
    (scan-complete)                    ; between ticks
    (scan-at ?c - cell)
    (updated ?c - cell)                ; object moved here this tick (ahead of the scan)

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
  ;; AGENT MOVEMENT (only between ticks)
  ;; ======================================================================

  (:action move_noop
    :parameters ()
    :precondition (and (agent-alive) (scan-complete))
    :effect (and
      (not (scan-complete)) (scan-required)
      (increase (total-cost) 1))
  )

  (:action move_empty
    :parameters (?from ?to - real-cell)
    :precondition (and
      (agent-alive) (scan-complete)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (empty ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (empty ?to)) (agent-at ?to)
      (not (scan-complete)) (scan-required)
      (increase (total-cost) 1))
  )

  ;; Move into dirt (mines it).
  (:action move_into_dirt
    :parameters (?from ?to - real-cell)
    :precondition (and
      (agent-alive) (scan-complete)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (dirt ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (dirt ?to)) (agent-at ?to)
      (not (scan-complete)) (scan-required)
      (increase (total-cost) 1))
  )

  ;; Collect an ordinary gem (resting or falling).
  (:action move_into_gem
    :parameters (?from ?to - real-cell)
    :precondition (and
      (agent-alive) (scan-complete)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (gem ?to) (not (target-gem ?to)))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (gem ?to)) (not (falling ?to)) (agent-at ?to)
      (not (scan-complete)) (scan-required)
      (increase (total-cost) 1))
  )

  ;; Collect the distinguished target gem.
  (:action move_into_target_gem
    :parameters (?from ?to - real-cell)
    :precondition (and
      (agent-alive) (scan-complete)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (gem ?to) (target-gem ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (gem ?to)) (not (target-gem ?to)) (not (falling ?to)) (agent-at ?to)
      (got-gem)
      (not (scan-complete)) (scan-required)
      (increase (total-cost) 1))
  )

  ;; Horizontal push of a resting stone into an empty cell.  The engine marks
  ;; the pushed stone updated (it does not move again this tick) and makes it
  ;; falling iff the cell below its destination is empty.
  (:action move_push_rock
    :parameters (?from ?to ?stone_dest - real-cell ?below - cell)
    :precondition (and
      (agent-alive) (scan-complete)
      (agent-at ?from)
      (or (and (right-of ?from ?to) (right-of ?to ?stone_dest))
          (and (right-of ?to ?from) (right-of ?stone_dest ?to)))
      (stone ?to) (not (falling ?to))
      (empty ?stone_dest)
      (down ?stone_dest ?below))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (stone ?to)) (agent-at ?to)
      (not (empty ?stone_dest)) (stone ?stone_dest) (updated ?stone_dest)
      (when (empty ?below) (falling ?stone_dest))
      (not (scan-complete)) (scan-required)
      (increase (total-cost) 1))
  )

  ;; ======================================================================
  ;; SCANNER MOVEMENT
  ;; ======================================================================

  (:action start_tick
    :parameters (?start - real-cell)
    :precondition (and (scan-required) (first-cell ?start))
    :effect (and (not (scan-required)) (scan-at ?start) (check_fall))
  )

  ;; Nothing to do here: no stone/gem, or an object that already moved this tick.
  (:action skip_cell
    :parameters (?c - real-cell ?next - cell)
    :precondition (and
      (scan-at ?c) (next-cell ?c ?next) (check_fall)
      (or (updated ?c) (empty ?c) (dirt ?c) (agent-at ?c) (brick ?c)))
    :effect (and (not (updated ?c)) (not (scan-at ?c)) (scan-at ?next))
  )

  ;; The stone/gem of this cell has been handled.
  (:action advance_scan
    :parameters (?c - real-cell ?next - cell)
    :precondition (and (scan-at ?c) (next-cell ?c ?next) (acted))
    :effect (and (not (acted)) (check_fall) (not (scan-at ?c)) (scan-at ?next))
  )

  (:action end_tick
    :parameters (?c - border-cell)
    :precondition (and (scan-at ?c) (last-cell ?c))
    :effect (and (not (scan-at ?c)) (not (check_fall)) (scan-complete))
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
      (down ?c ?down) (not (empty ?down))
      (or (not (falling ?c)) (not (agent-at ?down))))
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
      (or (and (not (rounded-wall ?down))
               (or (falling ?down) (and (not (stone ?down)) (not (gem ?down)))))
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
      (or (and (not (rounded-wall ?down))
               (or (falling ?down) (and (not (stone ?down)) (not (gem ?down)))))
          (not (empty ?right))
          (not (empty ?down_right))))
    :effect (and (not (check_roll_right)) (ready_to_move))
  )

  ;; ======================================================================
  ;; STONE / GEM ACTS
  ;; ======================================================================

  ;; Fall one cell (the object below the scan is skipped when reached).
  (:action stone_fall
    :parameters (?c ?down - real-cell)
    :precondition (and (scan-at ?c) (ready_to_move) (can_fall) (stone ?c) (down ?c ?down))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?down)) (stone ?down) (falling ?down) (updated ?down)
      (not (ready_to_move)) (not (can_fall)) (acted))
  )

  (:action gem_fall
    :parameters (?c ?down - real-cell)
    :precondition (and (scan-at ?c) (ready_to_move) (can_fall) (gem ?c) (down ?c ?down))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?down)))
      (not (empty ?down)) (gem ?down) (falling ?down) (updated ?down)
      (not (ready_to_move)) (not (can_fall)) (acted))
  )

  ;; Roll left: the destination is behind the scan, so it needs no updated flag.
  (:action stone_roll_left
    :parameters (?c ?left - real-cell)
    :precondition (and (scan-at ?c) (ready_to_move) (can_roll_left) (stone ?c) (right-of ?left ?c))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?left)) (stone ?left) (falling ?left)
      (not (ready_to_move)) (not (can_roll_left)) (acted))
  )

  (:action gem_roll_left
    :parameters (?c ?left - real-cell)
    :precondition (and (scan-at ?c) (ready_to_move) (can_roll_left) (gem ?c) (right-of ?left ?c))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?left)))
      (not (empty ?left)) (gem ?left) (falling ?left)
      (not (ready_to_move)) (not (can_roll_left)) (acted))
  )

  ;; Roll right: the destination is the next cell of the scan, skipped there.
  (:action stone_roll_right
    :parameters (?c ?right - real-cell)
    :precondition (and (scan-at ?c) (ready_to_move) (can_roll_right) (stone ?c) (right-of ?c ?right))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?right)) (stone ?right) (falling ?right) (updated ?right)
      (not (ready_to_move)) (not (can_roll_right)) (acted))
  )

  (:action gem_roll_right
    :parameters (?c ?right - real-cell)
    :precondition (and (scan-at ?c) (ready_to_move) (can_roll_right) (gem ?c) (right-of ?c ?right))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?right)))
      (not (empty ?right)) (gem ?right) (falling ?right) (updated ?right)
      (not (ready_to_move)) (not (can_roll_right)) (acted))
  )

  ;; Cannot move: a falling object comes to rest, a resting one stays.
  (:action stone_gem_settle
    :parameters (?c - real-cell)
    :precondition (and
      (scan-at ?c) (ready_to_move)
      (not (can_fall)) (not (can_roll_left)) (not (can_roll_right)))
    :effect (and (not (falling ?c)) (not (ready_to_move)) (acted))
  )
)
