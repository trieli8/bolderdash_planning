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
    (right-of ?from ?to - cell)

    (border-cell ?c - border-cell)
    (real-cell ?c - real-cell)

    ;; linear scan order (top-left -> bottom-right)
    (first-cell ?c - real-cell)
    (last-cell ?c - real-cell)
    (next-cell ?c1 ?c2 - real-cell)

    ;; scan pointer for this tick
    (scan-at ?c - real-cell)
    (scan-required)

    ;; updated-in-this-tick flags
    (updated ?c - cell)

    ;; cell contents
    (agent-at ?c - cell)
    (empty ?c - cell)
    (dirt ?c - cell)
    (stone ?c - cell)
    (gem ?c - cell)
    (falling ?c - cell)
    (brick ?c - cell)

    ;; high-level state
    (agent-alive)
    (got-gem)
    (crushed)
    ;; kept for compatibility with existing problem files
    (update-required)
  )

  ;; ======================================================
  ;; AGENT MOVEMENT
  ;; Each move starts a new game tick by setting scan-at to
  ;; the first cell in the English-reading order.
  ;; ======================================================

  (:action move_noop
    :parameters (?start - real-cell)
    :precondition (and
      (agent-alive)
      (first-cell ?start)
      (not (scan-required))
    )
    :effect (and
      (scan-at ?start)
      (scan-required)
      (increase (total-cost) 1)
    )
  )

  (:action move_empty
    :parameters (?from ?to ?start - real-cell)
    :precondition (and
      (agent-alive)
      (agent-at ?from)
        (or (up ?from ?to)
          (down ?from ?to)
          (right-of ?to ?from)
          (right-of ?from ?to))
      (empty ?to)
      (first-cell ?start)
      (not (scan-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (empty ?from)
      (not (empty ?to))

      (scan-at ?start)
      (scan-required)
      (increase (total-cost) 1)
    )
  )

  ;; Move into dirt (mines it to empty)
  (:action move_into_dirt
    :parameters (?from ?to ?start - real-cell)
    :precondition (and
      (agent-alive)
      (agent-at ?from)
        (or (up ?from ?to)
          (down ?from ?to)
          (right-of ?to ?from)
          (right-of ?from ?to))
      (dirt ?to)
      (first-cell ?start)
      (not (scan-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (not (dirt ?to))

      (empty ?from)
      (not (empty ?to))

      (scan-at ?start)
      (scan-required)
      (increase (total-cost) 1)
    )
  )

  ;; Move into gem (collect it -> got-gem)
  (:action move_into_gem
    :parameters (?from ?to ?start - real-cell)
    :precondition (and
      (agent-alive)
      (agent-at ?from)
        (or (up ?from ?to)
          (down ?from ?to)
          (right-of ?to ?from)
          (right-of ?from ?to))
      (gem ?to)
      (first-cell ?start)
      (not (scan-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (empty ?from)
      (not (empty ?to))

      (not (gem ?to))
      (not (falling ?to))

      (got-gem)

      (scan-at ?start)
      (scan-required)
      (increase (total-cost) 1)
    )
  )

  (:action move_push_rock
    :parameters (?from ?to ?stone_dest ?start - real-cell)
    :precondition (and
      (agent-alive)
      (agent-at ?from)
      (or
        (and (right-of ?to ?from) (right-of ?stone_dest ?to))
        (and (right-of ?from ?to) (right-of ?to ?stone_dest)))
      (stone ?to)
      (empty ?stone_dest)
      (not (falling ?to))
      (first-cell ?start)
      (not (scan-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (not (empty ?to))
      (empty ?from)

      (not (stone ?to))
      (stone ?stone_dest)

      (not (empty ?stone_dest))
      (not (falling ?stone_dest))

      ;; match the updated domain behavior
      (updated ?to)

      (scan-at ?start)
      (scan-required)
      (increase (total-cost) 1)
    )
  )

  ;; ======================================================
  ;; AGENT DEATH
  ;; ======================================================

  (:action __forced__physics_fall_on_agent
    :parameters (?c ?down ?next - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (down ?c ?down)

      (stone ?c)
      (falling ?c)

      (agent-at ?down)

      (not (updated ?c))
    )
    :effect (and
      (not (agent-alive))
      (crushed)

      (updated ?c)
      (not (falling ?c))


      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  ;; ======================================================
  ;; FORCED ACTIONS: ONE-TICK CELL UPDATE IN SCAN ORDER
  ;; ======================================================

  (:action __forced__physics_stone_fall
    :parameters (?c ?down ?next - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))

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


      (stone ?down)
      (falling ?down)
      (not (empty ?down))


      (updated ?down)
      (updated ?c)

      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_gem_fall
    :parameters (?c ?down ?next - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))

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


      (gem ?down)
      (falling ?down)
      (not (empty ?down))


      (updated ?down)
      (updated ?c)

      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_stone_on_dirt
    :parameters (?c ?down ?next - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (down ?c ?down)
      (stone ?c)
      (dirt ?down)

      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))


      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_gem_on_dirt
    :parameters (?c ?down ?next - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (down ?c ?down)
      (gem ?c)
      (dirt ?down)

      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))


      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_on_bottom
    :parameters (?c ?next - real-cell ?down - border-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (down ?c ?down)

      (or (stone ?c) (gem ?c))
      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))


      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  ;; ------------------------------------------------------
  ;; ROLLING
  ;; ------------------------------------------------------

  (:action __forced__physics_stone_roll_left
    :parameters (?c ?next - real-cell ?left ?down_left ?down ?up_left)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (not (updated ?c))

      (right-of ?left ?c)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)

      ;; above
      (up ?left ?up_left)

      (stone ?c)

      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))


      (or (and (not (stone ?up_left)) (not (gem ?up_left))) (updated ?up_left))

      (empty ?left)
      (not (updated ?left))

      (empty ?down_left)

    )
    :effect (and
      (not (stone ?c))
      (not (falling ?c))

      (empty ?c)

      (stone ?left)
      (falling ?left)
      (not (empty ?left))


      (updated ?c)
      (updated ?left)

      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_gem_roll_left
    :parameters (?c ?next - real-cell ?left ?down_left ?down ?up_left)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (not (updated ?c))

      (right-of ?left ?c)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)

      ;; above
      (up ?left ?up_left)

      (gem ?c)

      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))


      (or (and (not (stone ?up_left)) (not (gem ?up_left))) (updated ?up_left))

      (empty ?left)
      (not (updated ?left))

      (empty ?down_left)

    )
    :effect (and
      (not (gem ?c))
      (not (falling ?c))

      (empty ?c)

      (gem ?left)
      (falling ?left)
      (not (empty ?left))


      (updated ?c)
      (updated ?left)

      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_stone_roll_right
    :parameters (?c ?next - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (not (updated ?c))

      (right-of ?left ?c)
      (right-of ?c ?right)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)

      ;; above
      (up ?left ?up_left)
      (up ?c ?up)
      (up ?right ?up_right)

      (stone ?c)

      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))


      (or (and (not (stone ?up_right)) (not (gem ?up_right))) (updated ?up_right))

      (empty ?right)
      (not (updated ?right))

      (empty ?down_right)

      ;; no roll left
      (or
        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (and (stone ?up_left) (not (updated ?up_left)))
        (and (gem ?up_left) (not (updated ?up_left))))

    )
    :effect (and
      (not (stone ?c))
      (not (falling ?c))

      (empty ?c)

      (stone ?right)
      (falling ?right)
      (not (empty ?right))


      (updated ?c)
      (updated ?right)

      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_gem_roll_right
    :parameters (?c ?next - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (not (updated ?c))

      (right-of ?left ?c)
      (right-of ?c ?right)

      ;; below
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)

      ;; above
      (up ?left ?up_left)
      (up ?c ?up)
      (up ?right ?up_right)

      (gem ?c)

      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))


      (or (and (not (stone ?up_right)) (not (gem ?up_right))) (updated ?up_right))

      (empty ?right)
      (not (updated ?right))

      (empty ?down_right)

      ;; no roll left
      (or
        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (and (stone ?up_left) (not (updated ?up_left)))
        (and (gem ?up_left) (not (updated ?up_left))))

    )
    :effect (and
      (not (gem ?c))
      (not (falling ?c))

      (empty ?c)

      (gem ?right)
      (falling ?right)
      (not (empty ?right))


      (updated ?c)
      (updated ?right)

      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_stone_noop
    :parameters (?c ?next - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (stone ?c)

      (right-of ?left ?c)
      (right-of ?c ?right)

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

        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (and (stone ?up_left) (not (updated ?up_left)))
        (and (gem ?up_left) (not (updated ?up_left)))
      )

      ;; no roll right
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)) (not (updated ?down)))
        (falling ?down)

        (not (empty ?right))
        (updated ?right)
        (not (empty ?down_right))
        (and (stone ?up_right) (not (updated ?up_right)))
        (and (gem ?up_right) (not (updated ?up_right))))


      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))


      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_on_falling_noop
    :parameters (?c ?next - real-cell ?down - cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (down ?c ?down)

      (or (stone ?c) (gem ?c))

      (falling ?down)


      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))


      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_gem_noop
    :parameters (?c ?next - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (gem ?c)

      (right-of ?left ?c)
      (right-of ?c ?right)

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

        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (and (stone ?up_left) (not (updated ?up_left)))
        (and (gem ?up_left) (not (updated ?up_left)))
      )

      ;; no roll right
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)) (not (updated ?down)))
        (falling ?down)

        (not (empty ?right))
        (updated ?right)
        (not (empty ?down_right))
        (and (stone ?up_right) (not (updated ?up_right)))
        (and (gem ?up_right) (not (updated ?up_right))))


      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))


      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_agent_noop
    :parameters (?c ?next - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (agent-at ?c)
      (not (updated ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))


      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  (:action __forced__physics_other_noop
    :parameters (?c ?next - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (or (last-cell ?c) (next-cell ?c ?next))
      (not (updated ?c))
      (not (stone ?c))
      (not (gem ?c))
    )
    :effect (and
      (updated ?c)

      (when (next-cell ?c ?next)
        (and
          (not (scan-at ?c))
          (scan-at ?next)))
    )
  )

  ;; -------- Skip already-updated cells --------

  (:action __forced__advance_scan
    :parameters (?c ?next - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (updated ?c)
      (next-cell ?c ?next)
    )
    :effect (and
      (not (scan-at ?c))
      (scan-at ?next)
    )
  )

  ;; -------- End-of-tick: at last cell, updated, clear flags --------

  (:action __forced__end_tick
    :parameters (?c - real-cell)
    :precondition (and
      (scan-required)
      (scan-at ?c)
      (last-cell ?c)
      (updated ?c)
    )
    :effect (and
      (not (scan-at ?c))
      (not (scan-required))
      (forall (?rc - real-cell)
        (not (updated ?rc)))
    )
  )
)
