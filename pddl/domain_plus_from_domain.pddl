(define (domain mine-tick-gravity-plus-from-domain)
  (:requirements
    :strips
    :negative-preconditions
    :disjunctive-preconditions
    :conditional-effects
    :numeric-fluents
    :action-costs
    :events
  )

  (:predicates
    (up ?from ?to)
    (down ?from ?to)
    (right-of ?from ?to)

    ;; Scan ordering / tick control
    (first-cell ?c)
    (last-cell ?c)
    (next-cell ?c1 ?c2)
    (bottom ?c)

    (scan-at ?c)
    (scan-required)
    (scan-complete)
    (scan-active)
    (updated ?c)

    ;; World state
    (agent-at ?c)
    (empty ?c)
    (dirt ?c)
    (stone ?c)
    (gem ?c)
    (falling ?c)
    (brick ?c)

    (agent-alive)
    (got-gem)
    (crushed)
  )

  (:functions
    (total-cost)
    (sim-time)
  )

  ;; Keep time flowing while scan is active so autonomous events progress
  ;; scan advancement without planner choices.
  (:process scan-clock
    :parameters ()
    :precondition (scan-active)
    :effect (increase (sim-time) #t)
  )

  ;; ======================================================
  ;; AGENT MOVEMENT
  ;; ======================================================

  (:action move_noop
    :parameters ()
    :precondition (and
      (agent-alive)
      (scan-complete)
    )
    :effect (and
      (scan-required)
      (not (scan-complete))
      (increase (total-cost) 1)
    )
  )

  (:action move_empty
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (scan-complete)
      (agent-at ?from)
      (or
        (up ?from ?to)
        (down ?from ?to)
        (right-of ?to ?from)
        (right-of ?from ?to)
      )
      (empty ?to)
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (empty ?from)
      (not (empty ?to))
      (scan-required)
      (not (scan-complete))
      (increase (total-cost) 1)
    )
  )

  (:action move_into_dirt
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (scan-complete)
      (agent-at ?from)
      (or
        (up ?from ?to)
        (down ?from ?to)
        (right-of ?to ?from)
        (right-of ?from ?to)
      )
      (dirt ?to)
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (not (dirt ?to))
      (empty ?from)
      (not (empty ?to))
      (scan-required)
      (not (scan-complete))
      (increase (total-cost) 1)
    )
  )

  (:action move_into_gem
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (scan-complete)
      (agent-at ?from)
      (or
        (up ?from ?to)
        (down ?from ?to)
        (right-of ?to ?from)
        (right-of ?from ?to)
      )
      (gem ?to)
    )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (empty ?from)
      (not (empty ?to))
      (not (gem ?to))
      (not (falling ?to))
      (got-gem)
      (scan-required)
      (not (scan-complete))
      (increase (total-cost) 1)
    )
  )

  (:action move_push_rock
    :parameters (?from ?to ?stone_dest)
    :precondition (and
      (agent-alive)
      (scan-complete)
      (agent-at ?from)
      (or
        (and (right-of ?to ?from) (right-of ?stone_dest ?to))
        (and (right-of ?from ?to) (right-of ?to ?stone_dest))
      )
      (stone ?to)
      (empty ?stone_dest)
      (not (falling ?to))
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
      (scan-required)
      (not (scan-complete))
      (increase (total-cost) 1)
    )
  )

  ;; ======================================================
  ;; TICK PROGRESSION
  ;; Every cell must be consumed before movement can happen again.
  ;; ======================================================

  (:action start_scan
    :parameters (?start)
    :precondition (and
      (scan-required)
      (not (scan-active))
      (first-cell ?start)
    )
    :effect (and
      (scan-at ?start)
      (scan-active)
    )
  )

  (:action advance_scan
    :parameters (?c ?next)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (updated ?c)
      (next-cell ?c ?next)
    )
    :effect (and
      (not (scan-at ?c))
      (scan-at ?next)
      (not (updated ?c))
    )
  )

  (:action end_scan
    :parameters (?c)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (updated ?c)
      (last-cell ?c)
    )
    :effect (and
      (not (scan-at ?c))
      (not (updated ?c))
      (not (scan-required))
      (scan-complete)
      (not (scan-active))
    )
  )

  ;; ======================================================
  ;; PHYSICS EVENTS (AUTOMATIC)
  ;; roll/fall/crush mechanics are events, not planner actions.
  ;; ======================================================

  (:event ev_mark_passive_cell
    :parameters (?c)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (or (empty ?c) (dirt ?c) (brick ?c) (agent-at ?c))
    )
    :effect (updated ?c)
  )

  (:event ev_stone_fall
    :parameters (?c ?d)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (stone ?c)
      (down ?c ?d)
      (empty ?d)
      (not (updated ?d))
    )
    :effect (and
      (not (stone ?c))
      (not (falling ?c))
      (empty ?c)
      (stone ?d)
      (falling ?d)
      (not (empty ?d))
      (updated ?c)
      (updated ?d)
    )
  )

  (:event ev_gem_fall
    :parameters (?c ?d)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (gem ?c)
      (down ?c ?d)
      (empty ?d)
      (not (updated ?d))
    )
    :effect (and
      (not (gem ?c))
      (not (falling ?c))
      (empty ?c)
      (gem ?d)
      (falling ?d)
      (not (empty ?d))
      (updated ?c)
      (updated ?d)
    )
  )

  (:event ev_stone_roll_left
    :parameters (?c ?left ?down ?down_left)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (stone ?c)
      (right-of ?left ?c)
      (down ?c ?down)
      (down ?left ?down_left)
      (empty ?left)
      (empty ?down_left)
      (not (agent-at ?down))
      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
    )
    :effect (and
      (not (stone ?c))
      (not (falling ?c))
      (empty ?c)
      (stone ?left)
      (falling ?left)
      (not (empty ?left))
      (updated ?c)
    )
  )

  (:event ev_gem_roll_left
    :parameters (?c ?left ?down ?down_left)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (gem ?c)
      (right-of ?left ?c)
      (down ?c ?down)
      (down ?left ?down_left)
      (empty ?left)
      (empty ?down_left)
      (not (agent-at ?down))
      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
    )
    :effect (and
      (not (gem ?c))
      (not (falling ?c))
      (empty ?c)
      (gem ?left)
      (falling ?left)
      (not (empty ?left))
      (updated ?c)
    )
  )

  (:event ev_stone_roll_right
    :parameters (?c ?left ?right ?down ?down_left ?down_right)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (not (updated ?right))
      (stone ?c)
      (right-of ?left ?c)
      (right-of ?c ?right)
      (down ?c ?down)
      (down ?left ?down_left)
      (down ?right ?down_right)
      (empty ?right)
      (empty ?down_right)
      (not (agent-at ?down))
      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
      (or
        (not (empty ?left))
        (not (empty ?down_left))
        (updated ?left)
      )
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
    )
  )

  (:event ev_gem_roll_right
    :parameters (?c ?left ?right ?down ?down_left ?down_right)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (not (updated ?right))
      (gem ?c)
      (right-of ?left ?c)
      (right-of ?c ?right)
      (down ?c ?down)
      (down ?left ?down_left)
      (down ?right ?down_right)
      (empty ?right)
      (empty ?down_right)
      (not (agent-at ?down))
      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
      (or
        (not (empty ?left))
        (not (empty ?down_left))
        (updated ?left)
      )
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
    )
  )

  (:event ev_crush_by_stone
    :parameters (?c ?d)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (stone ?c)
      (falling ?c)
      (down ?c ?d)
      (agent-at ?d)
    )
    :effect (and
      (not (agent-alive))
      (crushed)
      (not (falling ?c))
      (updated ?c)
    )
  )

  (:event ev_crush_by_gem
    :parameters (?c ?d)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (gem ?c)
      (falling ?c)
      (down ?c ?d)
      (agent-at ?d)
    )
    :effect (and
      (not (agent-alive))
      (crushed)
      (not (falling ?c))
      (updated ?c)
    )
  )

  (:event ev_stone_settle
    :parameters (?c ?d)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (stone ?c)
      (down ?c ?d)
      (not (empty ?d))
    )
    :effect (and
      (not (falling ?c))
      (updated ?c)
    )
  )

  (:event ev_gem_settle
    :parameters (?c ?d)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (gem ?c)
      (down ?c ?d)
      (not (empty ?d))
    )
    :effect (and
      (not (falling ?c))
      (updated ?c)
    )
  )

  (:event ev_stone_settle_bottom
    :parameters (?c)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (stone ?c)
      (bottom ?c)
    )
    :effect (and
      (not (falling ?c))
      (updated ?c)
    )
  )

  (:event ev_gem_settle_bottom
    :parameters (?c)
    :precondition (and
      (scan-required)
      (scan-active)
      (scan-at ?c)
      (not (updated ?c))
      (gem ?c)
      (bottom ?c)
    )
    :effect (and
      (not (falling ?c))
      (updated ?c)
    )
  )
)
