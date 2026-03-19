(define (domain mine-tick-gravity-plus-scanner-separated-int-state)
  (:requirements :strips :negative-preconditions :disjunctive-preconditions :universal-preconditions :conditional-effects :action-costs :processes :events :numeric-fluents)

  ;; HiddenCellType IDs from stonesandgem/src/definitions.h:
  ;; 0  agent
  ;; 1  empty
  ;; 2  dirt
  ;; 3  stone
  ;; 4  stone_falling
  ;; 5  diamond
  ;; 6  diamond_falling
  ;; 7/8/18/19/20/21/22 are treated as solid

  (:predicates
    ;; layout / topology
    (up ?from ?to)
    (down ?from ?to)
    (right-of ?from ?to)

    (border-cell ?c)
    (real-cell ?c)

    ;; linear scan order (top-left -> bottom-right)
    (first-cell ?c)
    (last-cell ?c)
    (next-cell ?c1 ?c2)

    ;; scan pointer for this tick
    (scan-at ?c)
    (scan-required)
    (scan-complete)
    (scan-active)

    ;; high-level state
    (agent-alive)
    (got-gem)
    (crushed)

    ;; scanner-local control
    (can_fall)
    (can_roll_left)
    (can_roll_right)
    (check_fall)
    (check_roll_left)
    (check_roll_right)
    (ready_to_move)
  )

  (:functions
    (total-cost)
    (sim-time)
    (tick)
    (cell-state ?c)
    (last-updated-tick ?c)
  )

  ;; Keep a running clock while scan is active (PDDL+ process).
  (:process scan-clock
    :parameters ()
    :precondition (scan-active)
    :effect (increase (sim-time) #t)
  )

  ;; ======================================================
  ;; AGENT MOVEMENT
  ;; ======================================================
  (:action move_noop
    :parameters (?start)
    :precondition (and
      (agent-alive)
      (first-cell ?start)
      (scan-complete)
    )
    :effect (and
      (scan-required)
      (not (scan-complete))
      (increase (tick) 1)
      (increase (total-cost) 1)
    )
  )

  (:action move_empty
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (= (cell-state ?from) 0)
      (or
        (up ?from ?to)
        (down ?from ?to)
        (right-of ?to ?from)
        (right-of ?from ?to)
      )
      (= (cell-state ?to) 1)
      (scan-complete)
    )
    :effect (and
      (assign (cell-state ?from) 1)
      (assign (cell-state ?to) 0)
      (scan-required)
      (not (scan-complete))
      (increase (tick) 1)
      (increase (total-cost) 1)
    )
  )

  (:action move_into_dirt
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (= (cell-state ?from) 0)
      (or
        (up ?from ?to)
        (down ?from ?to)
        (right-of ?to ?from)
        (right-of ?from ?to)
      )
      (= (cell-state ?to) 2)
      (scan-complete)
    )
    :effect (and
      (assign (cell-state ?from) 1)
      (assign (cell-state ?to) 0)
      (scan-required)
      (not (scan-complete))
      (increase (tick) 1)
      (increase (total-cost) 1)
    )
  )

  (:action move_into_gem
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (= (cell-state ?from) 0)
      (or
        (up ?from ?to)
        (down ?from ?to)
        (right-of ?to ?from)
        (right-of ?from ?to)
      )
      (or
        (= (cell-state ?to) 5)
        (= (cell-state ?to) 6)
      )
      (scan-complete)
    )
    :effect (and
      (assign (cell-state ?from) 1)
      (assign (cell-state ?to) 0)
      (got-gem)
      (scan-required)
      (not (scan-complete))
      (increase (tick) 1)
      (increase (total-cost) 1)
    )
  )

  (:action move_push_rock
    :parameters (?from ?to ?stone_dest)
    :precondition (and
      (agent-alive)
      (= (cell-state ?from) 0)
      (or
        (and (right-of ?to ?from) (right-of ?stone_dest ?to))
        (and (right-of ?from ?to) (right-of ?to ?stone_dest))
      )
        (= (cell-state ?to) 3)
      (= (cell-state ?stone_dest) 1)
      (scan-complete)
    )
    :effect (and
      (assign (cell-state ?from) 1)
      (assign (cell-state ?to) 0)
      (assign (cell-state ?stone_dest) 3)
      ;; preserve prior behavior where pushed-through cell is already updated
      (assign (last-updated-tick ?to) (+ (tick) 1))
      (scan-required)
      (not (scan-complete))
      (increase (tick) 1)
      (increase (total-cost) 1)
    )
  )

  ;; ======================================================
  ;; SCANNER MOVEMENT
  ;; ======================================================
  (:action forced-start_tick
    :parameters (?start)
    :precondition (and
      (agent-alive)
      (first-cell ?start)
      (scan-required)
      (not (scan-active))
    )
    :effect (and
      (scan-at ?start)
      (scan-active)
      (assign (sim-time) 0)

      (not (can_fall))
      (not (can_roll_left))
      (not (can_roll_right))
      (not (check_roll_left))
      (not (check_roll_right))
      (not (ready_to_move))
      (check_fall)
    )
  )

  (:action forced-advance_scan_no_update
    :parameters (?c ?next)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (next-cell ?c ?next)
      (or
        (= (last-updated-tick ?c) (tick))
        (= (cell-state ?c) 0)
        (= (cell-state ?c) 1)
        (= (cell-state ?c) 2)
        (= (cell-state ?c) 7)
        (= (cell-state ?c) 8)
        (= (cell-state ?c) 18)
        (= (cell-state ?c) 19)
        (= (cell-state ?c) 20)
        (= (cell-state ?c) 21)
        (= (cell-state ?c) 22)
      )
    )
    :effect (and
      (not (scan-at ?c))
      (scan-at ?next)

      (not (can_fall))
      (not (can_roll_left))
      (not (can_roll_right))
      (not (check_roll_left))
      (not (check_roll_right))
      (not (ready_to_move))
      (check_fall)
    )
  )

  (:action forced-advance_scan
    :parameters (?c ?next)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (next-cell ?c ?next)
      (ready_to_move)
      (= (last-updated-tick ?c) (tick))
    )
    :effect (and
      (not (scan-at ?c))
      (scan-at ?next)

      (not (can_fall))
      (not (can_roll_left))
      (not (can_roll_right))
      (not (check_roll_left))
      (not (check_roll_right))
      (not (ready_to_move))
      (check_fall)
    )
  )

  (:action forced-end_tick
    :parameters (?c)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (last-cell ?c)
    )
    :effect (and
      (not (scan-at ?c))
      (not (scan-required))
      (scan-complete)
      (not (scan-active))

      (not (can_fall))
      (not (can_roll_left))
      (not (can_roll_right))
      (not (check_roll_left))
      (not (check_roll_right))
      (not (ready_to_move))
      (check_fall)
    )
  )

  ;; ======================================================
  ;; SCANNER CHECKS
  ;; ======================================================
  (:action forced-can_fall
    :parameters (?c ?down)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_fall)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (down ?c ?down)
      (= (cell-state ?down) 1)
    )
    :effect (and
      (can_fall)
      (not (check_fall))
      (ready_to_move)
    )
  )

  (:action forced-not_fall
    :parameters (?c ?down)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_fall)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (down ?c ?down)
      (not (= (cell-state ?down) 1))
    )
    :effect (and
      (not (can_fall))
      (not (check_fall))
      (check_roll_left)
    )
  )

  (:action forced-not_fall_no_down
    :parameters (?c)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_fall)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (forall (?d - object) (not (down ?c ?d)))
    )
    :effect (and
      (not (can_fall))
      (not (check_fall))
      (check_roll_left)
    )
  )

  (:action forced-can_roll_left
    :parameters (?c ?left ?down_left ?down)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_roll_left)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (right-of ?left ?c)
      (down ?left ?down_left)
      (down ?c ?down)

      (not (= (cell-state ?down) 0))
      (or
        (= (cell-state ?down) 3)
        (= (cell-state ?down) 4)
        (= (cell-state ?down) 5)
        (= (cell-state ?down) 6)
        (= (cell-state ?down) 7)
        (= (cell-state ?down) 8)
        (= (cell-state ?down) 18)
        (= (cell-state ?down) 19)
        (= (cell-state ?down) 20)
        (= (cell-state ?down) 21)
        (= (cell-state ?down) 22)
        (= (last-updated-tick ?down) (tick))
      )
      (not (= (cell-state ?down) 4))
      (not (= (cell-state ?down) 6))

      (= (cell-state ?left) 1)
      (= (cell-state ?down_left) 1)
    )
    :effect (and
      (can_roll_left)
      (not (check_roll_left))
      (ready_to_move)
    )
  )

  (:action forced-not_roll_left
    :parameters (?c ?left ?down_left ?down)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_roll_left)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (right-of ?left ?c)
      (down ?left ?down_left)
      (down ?c ?down)

      (or
        (= (cell-state ?down) 0)
        (and
          (not (= (cell-state ?down) 3))
          (not (= (cell-state ?down) 4))
          (not (= (cell-state ?down) 5))
          (not (= (cell-state ?down) 6))
          (not (= (cell-state ?down) 7))
          (not (= (cell-state ?down) 8))
          (not (= (cell-state ?down) 18))
          (not (= (cell-state ?down) 19))
          (not (= (cell-state ?down) 20))
          (not (= (cell-state ?down) 21))
          (not (= (cell-state ?down) 22))
          (not (= (last-updated-tick ?down) (tick)))
        )
        (= (cell-state ?down) 4)
        (= (cell-state ?down) 6)
        (not (= (cell-state ?left) 1))
        (not (= (cell-state ?down_left) 1))
      )
    )
    :effect (and
      (not (can_roll_left))
      (not (check_roll_left))
      (check_roll_right)
    )
  )

  (:action forced-not_roll_left_default
    :parameters (?c)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_roll_left)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
    )
    :effect (and
      (not (can_roll_left))
      (not (check_roll_left))
      (check_roll_right)
    )
  )

  (:action forced-can_roll_right
    :parameters (?c ?right ?down_right ?down)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_roll_right)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (right-of ?c ?right)
      (down ?right ?down_right)
      (down ?c ?down)

      (not (= (cell-state ?down) 0))
      (or
        (= (cell-state ?down) 3)
        (= (cell-state ?down) 4)
        (= (cell-state ?down) 5)
        (= (cell-state ?down) 6)
        (= (cell-state ?down) 7)
        (= (cell-state ?down) 8)
        (= (cell-state ?down) 18)
        (= (cell-state ?down) 19)
        (= (cell-state ?down) 20)
        (= (cell-state ?down) 21)
        (= (cell-state ?down) 22)
        (= (last-updated-tick ?down) (tick))
      )
      (not (= (cell-state ?down) 4))
      (not (= (cell-state ?down) 6))

      (= (cell-state ?right) 1)
      (= (cell-state ?down_right) 1)
    )
    :effect (and
      (can_roll_right)
      (not (check_roll_right))
      (ready_to_move)
    )
  )

  (:action forced-not_roll_right
    :parameters (?c ?right ?down_right ?down)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_roll_right)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (right-of ?c ?right)
      (down ?right ?down_right)
      (down ?c ?down)

      (or
        (= (cell-state ?down) 0)
        (and
          (not (= (cell-state ?down) 3))
          (not (= (cell-state ?down) 4))
          (not (= (cell-state ?down) 5))
          (not (= (cell-state ?down) 6))
          (not (= (cell-state ?down) 7))
          (not (= (cell-state ?down) 8))
          (not (= (cell-state ?down) 18))
          (not (= (cell-state ?down) 19))
          (not (= (cell-state ?down) 20))
          (not (= (cell-state ?down) 21))
          (not (= (cell-state ?down) 22))
          (not (= (last-updated-tick ?down) (tick)))
        )
        (= (cell-state ?down) 4)
        (= (cell-state ?down) 6)
        (not (= (cell-state ?right) 1))
        (not (= (cell-state ?down_right) 1))
      )
    )
    :effect (and
      (not (can_roll_right))
      (not (check_roll_right))
      (ready_to_move)
    )
  )

  (:action forced-not_roll_right_default
    :parameters (?c)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (check_roll_right)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
    )
    :effect (and
      (not (can_roll_right))
      (not (check_roll_right))
      (ready_to_move)
    )
  )

  ;; ======================================================
  ;; STONE/GEM MOVEMENT
  ;; ======================================================
  (:action forced-stone_fall
    :parameters (?c ?down)
    :precondition (and
      (ready_to_move)
      (scan-required)
      (scan-at ?c)
      (< (last-updated-tick ?c) (tick))
      (down ?c ?down)
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
      )
      (can_fall)
    )
    :effect (and
      (assign (cell-state ?c) 1)
      (assign (cell-state ?down) 4)
      (assign (last-updated-tick ?down) (tick))
      (assign (last-updated-tick ?c) (tick))
    )
  )

  (:action forced-gem_fall
    :parameters (?c ?down)
    :precondition (and
      (ready_to_move)
      (scan-required)
      (scan-at ?c)
      (< (last-updated-tick ?c) (tick))
      (down ?c ?down)
      (or
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (can_fall)
    )
    :effect (and
      (assign (cell-state ?c) 1)
      (assign (cell-state ?down) 6)
      (assign (last-updated-tick ?down) (tick))
      (assign (last-updated-tick ?c) (tick))
    )
  )

  (:action forced-stone_roll_left
    :parameters (?c ?left)
    :precondition (and
      (ready_to_move)
      (scan-required)
      (scan-at ?c)
      (< (last-updated-tick ?c) (tick))
      (right-of ?left ?c)
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
      )
      (can_roll_left)
      (not (can_fall))
    )
    :effect (and
      (assign (cell-state ?c) 1)
      (assign (cell-state ?left) 4)
      (assign (last-updated-tick ?c) (tick))
      (assign (last-updated-tick ?left) (tick))
    )
  )

  (:action forced-gem_roll_left
    :parameters (?c ?left)
    :precondition (and
      (ready_to_move)
      (scan-required)
      (scan-at ?c)
      (< (last-updated-tick ?c) (tick))
      (right-of ?left ?c)
      (or
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (can_roll_left)
      (not (can_fall))
    )
    :effect (and
      (assign (cell-state ?c) 1)
      (assign (cell-state ?left) 6)
      (assign (last-updated-tick ?c) (tick))
      (assign (last-updated-tick ?left) (tick))
    )
  )

  (:action forced-stone_roll_right
    :parameters (?c ?right)
    :precondition (and
      (ready_to_move)
      (scan-required)
      (scan-at ?c)
      (< (last-updated-tick ?c) (tick))
      (right-of ?c ?right)
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
      )
      (can_roll_right)
      (not (can_fall))
      (not (can_roll_left))
    )
    :effect (and
      (assign (cell-state ?c) 1)
      (assign (cell-state ?right) 4)
      (assign (last-updated-tick ?c) (tick))
      (assign (last-updated-tick ?right) (tick))
    )
  )

  (:action forced-gem_roll_right
    :parameters (?c ?right)
    :precondition (and
      (ready_to_move)
      (scan-required)
      (scan-at ?c)
      (< (last-updated-tick ?c) (tick))
      (right-of ?c ?right)
      (or
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (can_roll_right)
      (not (can_fall))
      (not (can_roll_left))
    )
    :effect (and
      (assign (cell-state ?c) 1)
      (assign (cell-state ?right) 6)
      (assign (last-updated-tick ?c) (tick))
      (assign (last-updated-tick ?right) (tick))
    )
  )

  (:action forced-stone_gem_noop
    :parameters (?c)
    :precondition (and
      (ready_to_move)
      (scan-required)
      (scan-at ?c)
      (< (last-updated-tick ?c) (tick))
      (or
        (= (cell-state ?c) 3)
        (= (cell-state ?c) 4)
        (= (cell-state ?c) 5)
        (= (cell-state ?c) 6)
      )
      (not (can_fall))
      (not (can_roll_left))
      (not (can_roll_right))
    )
    :effect (and
      (assign (last-updated-tick ?c) (tick))
      (when (= (cell-state ?c) 4) (assign (cell-state ?c) 3))
      (when (= (cell-state ?c) 6) (assign (cell-state ?c) 5))
    )
  )
)
