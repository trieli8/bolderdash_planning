(define (domain mine-tick-gravity)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :universal-preconditions :conditional-effects :action-costs)

  (:types
    cell real-cell border-cell - cell
  )

  (:functions
    (total-cost)
  )

  (:predicates
    ;; layout / topology
    (up ?from ?to - cell)
    (down ?from ?to - cell)
    (left-of ?from ?to - cell)
    (right-of ?from ?to - cell)

    (border-cell ?c - border-cell)
    (real-cell ?c - real-cell)

    ;; cell contents
    (agent-at ?c - cell)
    (empty ?c - cell)
    (dirt ?c - cell)
    (stone ?c - cell)
    (gem ?c - cell)
    (falling ?c - cell)
    (brick ?c - cell)
    (was_empty ?c - real-cell)
    (was_falling ?c - real-cell)

    ;; high-level state
    (agent-alive)
    (got-gem)
    (crushed)

    (update-required)
    (updated ?c - cell)
    (pending ?c - real-cell)

  )

  ;; ======================================================
  ;; AGENT MOVEMENT
  ;; ======================================================

  (:action move_noop
    :parameters ()
    :precondition (and (agent-alive)
      (not (update-required))
    )
    :effect (and
      (update-required)
      (increase (total-cost) 1)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))
    )
  )

  (:action move_empty
    :parameters (?from ?to - real-cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (empty ?to)
      (not (update-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (empty ?from)
      (not (empty ?to))

      (update-required)
      (increase (total-cost) 1)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))

    )
  )
  ;; Move into dirt (mines it to empty)
  (:action move_into_dirt
    :parameters (?from ?to - real-cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (dirt ?to)
      (not (update-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (not (dirt ?to))

      (empty ?from)
      (not (empty ?to))

      (update-required)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))
      (increase (total-cost) 1)
    )
  )

  ;; Move into gem (collect it -> got-gem)
  (:action move_into_gem
    :parameters (?from ?to - real-cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (gem ?to)
      (not (update-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (empty ?from)
      (not (empty ?to))

      (not (gem ?to))
      (not (falling ?to))

      (got-gem)
      (update-required)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))
      (increase (total-cost) 1)
    )
  )

  (:action move_push_rock
    :parameters (?from ?to ?stone_dest - real-cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or
        ; (and (up ?from ?to) (up ?to ?stone_dest))
        (and (left-of ?from ?to) (left-of ?to ?stone_dest))
        (and (right-of ?from ?to) (right-of ?to ?stone_dest))
        ; (and (down ?from ?to) (down ?to ?stone_dest))
      )
      (stone ?to)
      (empty ?stone_dest)
      (not (update-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (not (stone ?to))
      (not (falling ?to))
      (empty ?to)
      ; (was_empty ?to) TODO THINK ABOUT THIS

      (not (empty ?stone_dest))
      (stone ?stone_dest)
      (not (falling ?stone_dest))

      (updated ?to)
      (update-required)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))
      (increase (total-cost) 1)

    )
  )

  ;; ======================================================
  ;; PHYSICS: ONE-TICK CELL UPDATE (PARALLEL)
  ;; ======================================================

  (:action __forced__physics_stone_fall
    :parameters (?c ?down - real-cell)
    :precondition (and
      (update-required)

      (down ?c ?down)
      (stone ?c)
      (empty ?down)

      (not (updated ?c))
      (not (updated ?down))

    )
    :effect (and
      (not (stone ?c))
      (not (falling ?c))
      (empty ?c)
      (when (falling ?c) (was_falling ?c))

      (stone ?down)
      (falling ?down)
      (not (empty ?down))
      (was_empty ?down)

      (updated ?down)
      (updated ?c)
      (not (pending ?c))

    )
  )

  (:action __forced__physics_gem_fall
    :parameters (?c ?down - real-cell)
    :precondition (and
      (update-required)
      
      (down ?c ?down)
      (gem ?c)
      (empty ?down)

      (not (updated ?c))
      (not (updated ?down))
    )
    :effect (and
      (not (gem ?c))
      (not (falling ?c))
      (empty ?c)
      (when (falling ?c) (was_falling ?c))

      (gem ?down)
      (falling ?down)
      (not (empty ?down))
      (was_empty ?down)

      (updated ?down)
      (updated ?c)
      (not (pending ?c))
    )
  )

  (:action __forced__physics_stone_on_dirt
    :parameters (?c ?down - real-cell)
    :precondition (and
      (update-required)
      (down ?c ?down)
      (stone ?c)
      (or (dirt ?down))

      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (not (pending ?c))
    )
  )

  (:action __forced__physics_gem_on_dirt
    :parameters (?c ?down - real-cell)
    :precondition (and
      (update-required)
      (down ?c ?down)
      (gem ?c)
      (or (dirt ?down))


      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (not (pending ?c))
    )
  )

  (:action __forced__physics_on_bottom
    :parameters (?c - real-cell ?down - border-cell)
    :precondition (and
      (update-required)
      (down ?c ?down)

      (or (stone ?c) (gem ?c))
      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (not (pending ?c))
    )
  )

  ; ------------------------------------------------------
  ;; ROLLING
  ; ------------------------------------------------------

  (:action __forced__physics_stone_roll_left
    :parameters (?c - real-cell ?left ?down_left ?down ?up_left ?danger_cell - cell)

    :precondition (and
      (update-required)
      (right-of ?danger_cell ?left)
      (right-of ?left ?c)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)

      ;; above
      (up ?left ?up_left)

      (stone ?c)
      (not (updated ?c))

      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
      (not (was_falling ?down))

      (or (and (not (stone ?up_left)) (not (gem ?up_left))) (updated ?up_left))

      (empty ?left)
      (not (updated ?left))

      (or (empty ?down_left) (was_empty ?down_left))

      (or (and (not (stone ?danger_cell)) (not (gem ?danger_cell))) (updated ?danger_cell))
    )

    :effect (and
      (not (stone ?c))
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (empty ?c)

      (stone ?left)
      (falling ?left)
      (not (empty ?left))
      (was_empty ?left)

      (updated ?c)
      (updated ?left)
      (not (pending ?c))

    )
  )

  (:action __forced__physics_gem_roll_left
    :parameters (?c - real-cell ?left ?down_left ?down ?up_left ?danger_cell - cell)

    :precondition (and
      (update-required)
      (right-of ?danger_cell ?left)
      (right-of ?left ?c)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)

      ;; above
      (up ?left ?up_left)

      (gem ?c)
      (not (updated ?c))

      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
      (not (was_falling ?down))

      (or (and (not (stone ?up_left)) (not (gem ?up_left))) (updated ?up_left))

      (empty ?left)
      (not (updated ?left))

      (or (empty ?down_left) (was_empty ?down_left))

      (or (and (not (stone ?danger_cell)) (not (gem ?danger_cell))) (updated ?danger_cell))
    )

    :effect (and
      (not (gem ?c))
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (empty ?c)

      (gem ?left)
      (falling ?left)
      (not (empty ?left))
      (was_empty ?left)

      (updated ?c)
      (updated ?left)
      (not (pending ?c))
    )
  )

  (:action __forced__physics_stone_roll_right
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right ?left_danger - cell)

    :precondition (and
      (update-required)
      (right-of ?left ?c)
      (right-of ?c ?right)
      (right-of ?left_danger ?left)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)

      ;; above
      (up ?left ?up_left)
      (up ?c ?up)
      (up ?right ?up_right)

      (stone ?c)
      (not (updated ?c))

      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
      (not (was_falling ?down))

      (or (and (not (stone ?up_right)) (not (gem ?up_right))) (updated ?up_right))

      (empty ?right)
      (not (updated ?right))

      (or (empty ?down_right) (was_empty ?down_right))

      ;; no roll left
      (or
        (not (empty ?left))
        (updated ?left)
        (and (not (empty ?down_left)) (not (was_empty ?down_left)))
        (and (stone ?up_left) (not (updated ?up_left)))
        (and (gem ?up_left) (not (updated ?up_left)))
      )

      (or (and (not (stone ?left_danger)) (not (gem ?left_danger))) (updated ?left_danger))

    )

    :effect (and
      (not (stone ?c))
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (empty ?c)

      (stone ?right)
      (falling ?right)
      (not (empty ?right))
      (was_empty ?right)

      (updated ?c)
      (updated ?right)
      (not (pending ?c))
    )
  )

  (:action __forced__physics_gem_roll_right
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right ?left_danger - cell)

    :precondition (and
      (update-required)
      (right-of ?left ?c)
      (right-of ?c ?right)
      (right-of ?left_danger ?left)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)

      ;; above
      (up ?left ?up_left)
      (up ?c ?up)
      (up ?right ?up_right)

      (gem ?c)
      (not (updated ?c))

      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
      (not (was_falling ?down))

      (or (and (not (stone ?up_right)) (not (gem ?up_right))) (updated ?up_right))

      (empty ?right)
      (not (updated ?right))

      (or (empty ?down_right) (was_empty ?down_right))

      ;; no roll left
      (or
        (not (empty ?left))
        (updated ?left)
        (and (not (empty ?down_left)) (not (was_empty ?down_left)))
        (and (stone ?up_left) (not (updated ?up_left)))
        (and (gem ?up_left) (not (updated ?up_left)))
      )
      (or (and (not (stone ?left_danger)) (not (gem ?left_danger))) (updated ?left_danger))


    )

    :effect (and
      (not (gem ?c))
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (empty ?c)

      (gem ?right)
      (falling ?right)
      (not (empty ?right))
      (was_empty ?right)

      (updated ?c)
      (updated ?right)

      (not (pending ?c))
    )
  )

  (:action __forced__physics_stone_noop
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right ?left_danger - cell)
    :precondition (and
      (update-required)
      (stone ?c)

      (right-of ?left ?c)
      (right-of ?c ?right)
      (right-of ?left_danger ?left)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)

      ;; above
      (up ?left ?up_left)
      (up ?c ?up)
      (up ?right ?up_right)

      ;; no fall
      (or (not (empty ?down)) (updated ?down))

      ;; no roll left
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)) (not (updated ?down)))
        (falling ?down)
        (was_falling ?down)
        (not (empty ?left))
        (updated ?left)
        (and (not (empty ?down_left)) (not (was_empty ?down_left)))
        (and (stone ?up_left) (not (updated ?up_left)))
        (and (gem ?up_left) (not (updated ?up_left)))
        (and (stone ?left_danger) (not (updated ?left_danger)))
        (and (gem ?left_danger) (not (updated ?left_danger))))
      ;; no roll right
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)) (not (updated ?down)))
        (falling ?down)
        (was_falling ?down)
        (not (empty ?right))
        (updated ?right)
        (and (not (empty ?down_right)) (not (was_empty ?down_right)))
        (and (stone ?up_right) (not (updated ?up_right)))
        (and (gem ?up_right) (not (updated ?up_right))))

      (or (and (not (stone ?left_danger)) (not (gem ?left_danger))) (updated ?left_danger))
      
      (not (updated ?c))

    )

    :effect (and
      (updated ?c)
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (not (pending ?c))
    )
  )

  (:action __forced__physics_on_falling_noop
    :parameters (?c - real-cell ?down - cell)
    :precondition (and
      (update-required)
      (down ?c ?down)

      (or (stone ?c) (gem ?c))
      
      (falling ?down)
      (was_falling ?down)

      (not (updated ?c))
    )

    :effect (and
      (updated ?c)
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (not (pending ?c))
    )
  )

  (:action __forced__physics_gem_noop
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right ?left_danger - cell)
    :precondition (and
      (update-required)
      (gem ?c)

      (right-of ?left ?c)
      (right-of ?c ?right)
      (right-of ?left_danger ?left)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)

      ;; above
      (up ?left ?up_left)
      (up ?c ?up)
      (up ?right ?up_right)

      ;; no fall
      (or (not (empty ?down)) (updated ?down))

      ;; no roll left
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)) (not (updated ?down)))
        (falling ?down)
        (was_falling ?down)
        (not (empty ?left))
        (updated ?left)
        (and (not (empty ?down_left)) (not (was_empty ?down_left)))
        (and (stone ?up_left) (not (updated ?up_left)))
        (and (gem ?up_left) (not (updated ?up_left)))
        (and (stone ?left_danger) (not (updated ?left_danger)))
        (and (gem ?left_danger) (not (updated ?left_danger)))
      )

      ;; no roll right
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)) (not (updated ?down)))
        (falling ?down)
        (was_falling ?down)
        (not (empty ?right))
        (updated ?right)
        (and (not (empty ?down_right)) (not (was_empty ?down_right)))
        (and (stone ?up_right) (not (updated ?up_right)))
        (and (gem ?up_right) (not (updated ?up_right))))
      (or (and (not (stone ?left_danger)) (not (gem ?left_danger))) (updated ?left_danger))
      
      (not (updated ?c))

    )
    :effect (and
      (updated ?c)
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (not (pending ?c))
    )
  )

  (:action __forced__physics_agent_noop
    :parameters (?c - real-cell)
    :precondition (and
      (update-required)
      (agent-at ?c)
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))
      (when (falling ?c) (was_falling ?c))
      (not (pending ?c))
    )
  )

  ;; -------- End-of-tick: at last cell, updated, flip parity --------

  (:action __forced__end_tick
    :parameters ()
    :precondition (and
      (update-required)
      (forall
        (?c - real-cell)
        (and
          (not (pending ?c))
        ))
    )
    :effect (and
      ;; remove scan pointer: tick finished
      (forall
        (?c - real-cell)
        (and (not (updated ?c)) (not (pending ?c)) (not (was_empty ?c)) (not (was_falling ?c))))
      (not (update-required))
    )
  )
)
