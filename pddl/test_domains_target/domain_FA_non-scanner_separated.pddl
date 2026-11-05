; Generated test domain variant
; variant: domain_FA_non-scanner_separated.pddl
; source: pddl/domain_orderfree_separated.pddl
; regenerate with: python pddl/make_target_variants.py
; Boulder Dash (stonesngems engine) - order-free physics with pending flags,
; separated check / act actions.
;
; Reproduces stonesandgem/src/stonesngems_base.cpp (RNDGameState::apply_action)
; exactly for agent / empty / dirt / stone / gem / walls:
;   * the agent acts first; then every stone/gem that was there at the start
;     of the tick is updated once (an object that moved this tick, or a stone
;     the agent just pushed, is not: engine has_updated);
;   * a falling stone OR gem landing on the agent kills it;
;   * only resting stones/gems and brick walls (id 18) are rounded; steel
;     walls, exits and the level border are not, and the agent is not;
;   * pushed stones are falling iff the cell below their destination is empty;
;   * the target-gem marker travels with its gem.
;
; Order-free: there is no scan pointer.  After an agent move, start_tick marks
; every stone/gem pending.  select_object picks any pending object whose
; conflict window
;
;        k-2 k-1  k  k+1 k+2
;   r-1   x   x   x   x   x         (?ul2 ?ul ?u ?ur ?ur2)
;   r     x   x   c                 (?l2 ?l)
;
; holds no pending object (the earlier cells, row-major, whose update can read
; a cell that c's update writes or write a cell that c's update reads), so
; every selection order yields the engine's row-major result: the
; end-of-tick state is unique, although several objects are usually
; selectable at the same time.  The selected object is then decided by
; separate check actions
;   check_fall       -> can_fall | not_fall | fall_on_agent
;   check_roll_left  -> can_roll_left | not_roll_left
;   check_roll_right -> can_roll_right | not_roll_right
; and moved by one act action (stone_/gem_ fall / roll, or stone_gem_settle),
; which releases it.  Between selection and release exactly one physics
; action is applicable.  Physics does not depend on agent-alive, so a tick in
; which the agent dies still ends in a unique state.
;
; The test-domain variants
; (pddl/test_domains_target/domain_{classic,FA}_non-scanner_separated.pddl)
; are generated with
;   python pddl/make_target_variants.py
;
; Problems: pddl/problem_gen_orderfree.py
; Differential test against the engine: tools/sim_check/fuzz.py
(define (domain mine-tick-gravity)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :universal-preconditions :conditional-effects :action-costs)

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

    ;; ---- cell contents (exactly one per cell inside the level) ----
    (agent-at ?c - cell)
    (empty ?c - cell)
    (dirt ?c - cell)
    (stone ?c - cell)
    (gem ?c - cell)
    (target-gem ?c - cell)
    (falling ?c - cell)                ; stone/gem state; resting otherwise

    ;; ---- tick bookkeeping ----
    (update-required)                  ; a tick is in progress
    (tick-start)                       ; agent has moved, objects not marked yet
    (pushed ?c - cell)                 ; stone pushed by the agent this tick
    (pending ?c - cell)                ; stone/gem not yet updated this tick
    (busy)                             ; an object is selected
    (active ?c - cell)                 ; the selected object

    ;; ---- decision phases of the selected object ----
    (check_fall)
    (check_roll_left)
    (check_roll_right)
    (ready_to_move)
    (can_fall)
    (can_roll_left)
    (can_roll_right)

    ;; ---- high level ----
    (agent-alive)
    (got-gem)
  )

  ;; ======================================================================
  ;; AGENT MOVEMENT (between ticks; starts a tick)
  ;; ======================================================================

  (:action move_noop
    :parameters ()
    :precondition (and (agent-alive) (not (update-required)))
    :effect (and
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  (:action move_empty
    :parameters (?from ?to - real-cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (empty ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (empty ?to)) (agent-at ?to)
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  ;; Move into dirt (mines it).
  (:action move_into_dirt
    :parameters (?from ?to - real-cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (dirt ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (dirt ?to)) (agent-at ?to)
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  ;; Collect an ordinary gem (resting or falling).
  (:action move_into_gem
    :parameters (?from ?to - real-cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (gem ?to) (not (target-gem ?to)))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (gem ?to)) (not (falling ?to)) (agent-at ?to)
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  ;; Collect the distinguished target gem.
  (:action move_into_target_gem
    :parameters (?from ?to - real-cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (gem ?to) (target-gem ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (gem ?to)) (not (target-gem ?to)) (not (falling ?to)) (agent-at ?to)
      (got-gem)
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  ;; Horizontal push of a resting stone into an empty cell.  The pushed stone
  ;; is not updated again this tick (start_tick does not mark it pending) and
  ;; is falling iff the cell below its destination is empty.
  (:action move_push_rock
    :parameters (?from ?to ?stone_dest - real-cell ?below - cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (or (and (right-of ?from ?to) (right-of ?to ?stone_dest))
          (and (right-of ?to ?from) (right-of ?stone_dest ?to)))
      (stone ?to) (not (falling ?to))
      (empty ?stone_dest)
      (down ?stone_dest ?below))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (stone ?to)) (agent-at ?to)
      (not (empty ?stone_dest)) (stone ?stone_dest) (pushed ?stone_dest)
      (when (empty ?below) (falling ?stone_dest))
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  ;; ======================================================================
  ;; SELECTION (order-free)
  ;; ======================================================================

  (:action __FORCED__select_object
    :parameters (?c - real-cell ?l ?l2 ?u ?ul ?ul2 ?ur ?ur2 - cell)
    :precondition (and
      (not (busy)) (pending ?c)
      (right-of ?l ?c) (right-of ?l2 ?l)
      (up ?c ?u) (right-of ?ul ?u) (right-of ?ul2 ?ul) (right-of ?u ?ur) (right-of ?ur ?ur2)
      (not (pending ?l)) (not (pending ?l2))
      (not (pending ?u)) (not (pending ?ul)) (not (pending ?ul2)) (not (pending ?ur)) (not (pending ?ur2)))
    :effect (and (busy) (active ?c) (check_fall))
  )

  ;; Mark every stone/gem pending, except a stone the agent just pushed.
  (:action __FORCED__start_tick
    :parameters ()
    :precondition (tick-start)
    :effect (and
      (not (tick-start))
      (forall (?cc - real-cell)
        (and (when (and (or (stone ?cc) (gem ?cc)) (not (pushed ?cc))) (pending ?cc))
             (not (pushed ?cc)))))
  )

  ;; Every stone/gem has been updated: the tick is over.
  (:action __FORCED__end_tick
    :parameters ()
    :precondition (and
      (update-required) (not (tick-start))
      (forall (?c - real-cell) (not (pending ?c))))
    :effect (not (update-required))
  )

  ;; ======================================================================
  ;; CHECKS (on the selected object)
  ;; ======================================================================

  (:action __FORCED__can_fall
    :parameters (?c - real-cell ?down - cell)
    :precondition (and (active ?c) (check_fall) (down ?c ?down) (empty ?down))
    :effect (and (not (check_fall)) (can_fall) (ready_to_move))
  )

  ;; Falling stone or gem lands on the agent: explosion, agent dies.
  (:action __FORCED__fall_on_agent
    :parameters (?c - real-cell ?down - cell)
    :precondition (and (active ?c) (check_fall) (falling ?c) (down ?c ?down) (agent-at ?down))
    :effect (and
      (not (check_fall)) (not (agent-alive))
      (not (active ?c)) (not (busy)) (not (pending ?c)))
  )

  (:action __FORCED__not_fall
    :parameters (?c - real-cell ?down - cell)
    :precondition (and
      (active ?c) (check_fall)
      (down ?c ?down) (not (empty ?down))
      (or (not (falling ?c)) (not (agent-at ?down))))
    :effect (and (not (check_fall)) (check_roll_left))
  )

  ;; Roll left needs a rounded support (resting stone/gem or brick wall) and
  ;; empty left and down-left cells (engine: CanRollLeft, tried first).
  (:action __FORCED__can_roll_left
    :parameters (?c - real-cell ?down ?left ?down_left - cell)
    :precondition (and
      (active ?c) (check_roll_left)
      (down ?c ?down) (right-of ?left ?c) (down ?left ?down_left)
      (or (rounded-wall ?down) (and (or (stone ?down) (gem ?down)) (not (falling ?down))))
      (empty ?left) (empty ?down_left))
    :effect (and (not (check_roll_left)) (can_roll_left) (ready_to_move))
  )

  (:action __FORCED__not_roll_left
    :parameters (?c - real-cell ?down ?left ?down_left - cell)
    :precondition (and
      (active ?c) (check_roll_left)
      (down ?c ?down) (right-of ?left ?c) (down ?left ?down_left)
      (or (and (not (rounded-wall ?down))
               (or (falling ?down) (and (not (stone ?down)) (not (gem ?down)))))
          (not (empty ?left))
          (not (empty ?down_left))))
    :effect (and (not (check_roll_left)) (check_roll_right))
  )

  (:action __FORCED__can_roll_right
    :parameters (?c - real-cell ?down ?right ?down_right - cell)
    :precondition (and
      (active ?c) (check_roll_right)
      (down ?c ?down) (right-of ?c ?right) (down ?right ?down_right)
      (or (rounded-wall ?down) (and (or (stone ?down) (gem ?down)) (not (falling ?down))))
      (empty ?right) (empty ?down_right))
    :effect (and (not (check_roll_right)) (can_roll_right) (ready_to_move))
  )

  (:action __FORCED__not_roll_right
    :parameters (?c - real-cell ?down ?right ?down_right - cell)
    :precondition (and
      (active ?c) (check_roll_right)
      (down ?c ?down) (right-of ?c ?right) (down ?right ?down_right)
      (or (and (not (rounded-wall ?down))
               (or (falling ?down) (and (not (stone ?down)) (not (gem ?down)))))
          (not (empty ?right))
          (not (empty ?down_right))))
    :effect (and (not (check_roll_right)) (ready_to_move))
  )

  ;; ======================================================================
  ;; ACTS (move the selected object and release it)
  ;; ======================================================================

  (:action __FORCED__stone_fall
    :parameters (?c ?down - real-cell)
    :precondition (and (active ?c) (ready_to_move) (can_fall) (stone ?c) (down ?c ?down))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?down)) (stone ?down) (falling ?down)
      (not (ready_to_move)) (not (can_fall))
      (not (active ?c)) (not (busy)) (not (pending ?c)))
  )

  (:action __FORCED__gem_fall
    :parameters (?c ?down - real-cell)
    :precondition (and (active ?c) (ready_to_move) (can_fall) (gem ?c) (down ?c ?down))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?down)))
      (not (empty ?down)) (gem ?down) (falling ?down)
      (not (ready_to_move)) (not (can_fall))
      (not (active ?c)) (not (busy)) (not (pending ?c)))
  )

  (:action __FORCED__stone_roll_left
    :parameters (?c ?left - real-cell)
    :precondition (and (active ?c) (ready_to_move) (can_roll_left) (stone ?c) (right-of ?left ?c))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?left)) (stone ?left) (falling ?left)
      (not (ready_to_move)) (not (can_roll_left))
      (not (active ?c)) (not (busy)) (not (pending ?c)))
  )

  (:action __FORCED__gem_roll_left
    :parameters (?c ?left - real-cell)
    :precondition (and (active ?c) (ready_to_move) (can_roll_left) (gem ?c) (right-of ?left ?c))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?left)))
      (not (empty ?left)) (gem ?left) (falling ?left)
      (not (ready_to_move)) (not (can_roll_left))
      (not (active ?c)) (not (busy)) (not (pending ?c)))
  )

  (:action __FORCED__stone_roll_right
    :parameters (?c ?right - real-cell)
    :precondition (and (active ?c) (ready_to_move) (can_roll_right) (stone ?c) (right-of ?c ?right))
    :effect (and
      (not (stone ?c)) (not (falling ?c)) (empty ?c)
      (not (empty ?right)) (stone ?right) (falling ?right)
      (not (ready_to_move)) (not (can_roll_right))
      (not (active ?c)) (not (busy)) (not (pending ?c)))
  )

  (:action __FORCED__gem_roll_right
    :parameters (?c ?right - real-cell)
    :precondition (and (active ?c) (ready_to_move) (can_roll_right) (gem ?c) (right-of ?c ?right))
    :effect (and
      (not (gem ?c)) (not (falling ?c)) (empty ?c)
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?right)))
      (not (empty ?right)) (gem ?right) (falling ?right)
      (not (ready_to_move)) (not (can_roll_right))
      (not (active ?c)) (not (busy)) (not (pending ?c)))
  )

  ;; Cannot move: a falling object comes to rest, a resting one stays.
  (:action __FORCED__stone_gem_settle
    :parameters (?c - real-cell)
    :precondition (and
      (active ?c) (ready_to_move)
      (not (can_fall)) (not (can_roll_left)) (not (can_roll_right)))
    :effect (and
      (not (falling ?c)) (not (ready_to_move))
      (not (active ?c)) (not (busy)) (not (pending ?c)))
  )
)
