(define (domain mine-tick-gravity)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :universal-preconditions :conditional-effects :action-costs)

  (:types
    cell agent real-cell border-cell - cell
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
    (brick ?c - cell)

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

  (:action move-empty
    :parameters (?a - agent ?from ?to - real-cell)
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

      (updated ?to)
      (update-required)
      (increase (total-cost) 1)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))

    )
  )
  ;; Move into dirt (mines it to empty)
  (:action move-into-dirt
    :parameters (?a - agent ?from ?to - real-cell)
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
      (empty ?to)

      (empty ?from)
      (not (empty ?to))

      (updated ?to)
      (update-required)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))
      (increase (total-cost) 1)
    )
  )

  ;; Move into gem (collect it -> got-gem)
  (:action move-into-gem
    :parameters (?a - agent ?from ?to - real-cell)
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
      (empty ?to)

      (got-gem)
      (updated ?to)
      (update-required)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))
      (increase (total-cost) 1)

    )
  )

  (:action move-push-rock
    :parameters (?a - agent ?from ?to ?stone_dest - real-cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or
        (and (up ?from ?to) (up ?to ?stone_dest))
        (and (left-of ?from ?to) (left-of ?to ?stone_dest))
        (and (right-of ?from ?to) (right-of ?to ?stone_dest))
        (and (down ?from ?to) (down ?to ?stone_dest))
      )
      (stone ?to)
      (empty ?stone_dest)
      (not (update-required))
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)

      (not (stone ?to))
      (empty ?to)

      (not (empty ?stone_dest))
      (stone ?stone_dest)

      (updated ?to)
      (update-required)
      (forall (?cc - real-cell) (when (or (stone ?cc) (gem ?cc)) (and (pending ?cc))))
      (increase (total-cost) 1)

    )
  )

  ;; ======================================================
  ;; PHYSICS: ONE-TICK CELL UPDATE (PARALLEL)
  ;; ======================================================

  (:action __forced__physics_basics_stone-fall
    :parameters (?c ?down - real-cell)
    :precondition (and
      (update-required)
      (down ?c ?down)
      (stone ?c)
      (empty ?down)
    )
    :effect (and
      (not (stone ?c))
      (empty ?c)
      (stone ?down)
      (not (empty ?down))
      (updated ?down)
      (updated ?c)
      (not (pending ?c))

    )
  )

  (:action __forced__physics_basics_gem-fall
    :parameters (?c ?down - real-cell)
    :precondition (and
      (update-required)
      (down ?c ?down)
      (gem ?c)
      (empty ?down)
    )
    :effect (and
      (not (gem ?c))
      (empty ?c)
      (gem ?down)
      (not (empty ?down))
      (updated ?down)
      (updated ?c)
      (not (pending ?c))
    )
  )

  (:action __forced__physics_basics_stone-on-dirt
    :parameters (?c ?down - real-cell)
    :precondition (and
      (update-required)
      (down ?c ?down)
      (stone ?c)
      (dirt ?down)
    )
    :effect (and
      (updated ?c)
      (not (pending ?c))
    )
  )

  (:action __forced__physics_basics_gem-on-dirt
    :parameters (?c ?down - real-cell)
    :precondition (and
      (update-required)
      (down ?c ?down)
      (gem ?c)
      (dirt ?down)
    )
    :effect (and
      (updated ?c)
      (not (pending ?c))
    )
  )

  (:action __forced__physics-stone-roll-left
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      (update-required)
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
      (or (stone ?down) (gem ?down) (brick ?down))
      (empty ?left)
      (not (updated ?left))
      (empty ?down_left)
      (not (updated ?down_left))
    )

    :effect (and
      (not (stone ?c))
      (empty ?c)
      (stone ?left)
      (not (empty ?left))
      (updated ?c)
      (not (pending ?c))

    )
  )

  (:action __forced__physics-gem-roll-left
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      (update-required)
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
      (or (stone ?down) (gem ?down) (brick ?down))
      (empty ?left)
      (not (updated ?left))
      (empty ?down_left)
      (not (updated ?down_left))
    )

    :effect (and
      (not (gem ?c))
      (empty ?c)
      (gem ?left)
      (not (empty ?left))
      (updated ?c)
      (not (pending ?c))

    )
  )

  (:action __forced__physics-stone-roll-right
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      (update-required)
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
      (or (stone ?down) (gem ?down) (brick ?down))
      (empty ?right)
      (not (updated ?right))
      (empty ?down_right)
      (not (updated ?down_right))
      (or
        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (updated ?down_left))
    )

    :effect (and
      (not (stone ?c))
      (empty ?c)
      (stone ?right)
      (not (empty ?right))
      (updated ?c)
      (updated ?right)
      (not (pending ?c))
    )
  )

  (:action __forced__physics-gem-roll-right
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      (update-required)
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
      (or (stone ?down) (gem ?down) (brick ?down))
      (empty ?right)
      (not (updated ?right))
      (empty ?down_right)
      (not (updated ?down_right))
      (or
        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (updated ?down_left))
    )

    :effect (and
      (not (gem ?c))
      (empty ?c)
      (gem ?right)
      (not (empty ?right))
      (updated ?c)
      (not (pending ?c))
      (updated ?right)
    )
  )

  (:action __forced__physics-stone-noop
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
    :precondition (and
      (update-required)
      (not (updated ?c))
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
      (not (empty ?down))

      ;; no roll left
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)))
        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (updated ?down_left))

      ;; no roll right
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)))
        (not (empty ?right))
        (updated ?right)
        (not (empty ?down_right))
        (updated ?down_right))
    )
    :effect (and (updated ?c) (not (pending ?c)))
  )

  (:action __forced__physics-gem-noop
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
    :precondition (and
      (update-required)
      (not (updated ?c))
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
      (not (empty ?down))

      ;; no roll left
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)))
        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (updated ?down_left))

      ;; no roll right
      (or
        (and (not (stone ?down)) (not (gem ?down)) (not (brick ?down)))
        (not (empty ?right))
        (updated ?right)
        (not (empty ?down_right))
        (updated ?down_right))
    )
    :effect (and (updated ?c) (not (pending ?c)))
  )

  ;; -------- End-of-tick: at last cell, updated, flip parity --------

  (:action __forced__end-tick
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
        (and (not (updated ?c)) (not (pending ?c))))
      (not (update-required))
    )
  )
)
