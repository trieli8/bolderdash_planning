; Generated test domain variant
; variant: domain_plus_non-scanner_combined_events.pddl
; source: pddl/domain_plus_from_domain.pddl
(define (domain mine-tick-gravity-plus-from-domain)
  (:requirements
    :strips
    :negative-preconditions
    :disjunctive-preconditions
    :conditional-effects
    :numeric-fluents
    :action-costs
    :processes
    :events
  )

  (:predicates
    ;; layout / topology
    (up ?from ?to)
    (down ?from ?to)
    (right-of ?from ?to)

    ;; cell tags
    (border-cell ?c)
    (real-cell ?c)

    ;; retained for compatibility with existing generated problems
    (first-cell ?c)
    (last-cell ?c)
    (next-cell ?c1 ?c2)
    (bottom ?c)
    (scan-at ?c)
    (scan-active)

    ;; cell contents
    (agent-at ?c)
    (empty ?c)
    (dirt ?c)
    (stone ?c)
    (gem ?c)
    (falling ?c)
    (brick ?c)

    ;; high-level state
    (agent-alive)
    (got-gem)
    (crushed)

    ;; tick control
    (scan-required)
    (scan-complete)
    (init-phase)

    ;; non-scanner per-cell update control
    (updated ?c)
    (pending ?c)

    ;; separated event checks (cell-scoped)
    (can_fall ?c)
    (can_roll_left ?c)
    (can_roll_right ?c)
    (check_fall ?c)
    (check_roll_left ?c)
    (check_roll_right ?c)
    (ready_to_move ?c)
  )

  (:functions
    (total-cost)
    (sim-time)
  )

  ;; Tick-local clock. Time only matters for phase boundaries/end-tick.
  (:process tick-clock
    :parameters ()
    :precondition (scan-required)
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
      (not (scan-required))
    )
    :effect (and
      (scan-required)
      (not (scan-complete))
      (init-phase)
      (assign (sim-time) 0)
      (increase (total-cost) 1)
    )
  )

  (:action move_empty
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (scan-complete)
      (not (scan-required))
      (real-cell ?from)
      (real-cell ?to)
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
      (init-phase)
      (assign (sim-time) 0)
      (increase (total-cost) 1)
    )
  )

  (:action move_into_dirt
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (scan-complete)
      (not (scan-required))
      (real-cell ?from)
      (real-cell ?to)
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
      (init-phase)
      (assign (sim-time) 0)
      (increase (total-cost) 1)
    )
  )

  (:action move_into_gem
    :parameters (?from ?to)
    :precondition (and
      (agent-alive)
      (scan-complete)
      (not (scan-required))
      (real-cell ?from)
      (real-cell ?to)
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
      (init-phase)
      (assign (sim-time) 0)
      (increase (total-cost) 1)
    )
  )

  (:action move_push_rock
    :parameters (?from ?to ?stone_dest)
    :precondition (and
      (agent-alive)
      (scan-complete)
      (not (scan-required))
      (real-cell ?from)
      (real-cell ?to)
      (real-cell ?stone_dest)
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
      (updated ?to)
      (scan-required)
      (not (scan-complete))
      (init-phase)
      (assign (sim-time) 0)
      (increase (total-cost) 1)
    )
  )

  ;; ======================================================
  ;; TICK PHASE MANAGEMENT
  ;; ======================================================

  ;; Clear stale per-cell control flags from previous tick.
  (:event ev_clear_cell_flags
    :parameters (?c)
    :precondition (and
      (scan-required)
      (init-phase)
      (or
        (updated ?c)
        (pending ?c)
        (can_fall ?c)
        (can_roll_left ?c)
        (can_roll_right ?c)
        (check_fall ?c)
        (check_roll_left ?c)
        (check_roll_right ?c)
        (ready_to_move ?c)
      )
    )
    :effect (and
      (not (updated ?c))
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  ;; Give one small time step for flag-cleanup, then enter physics phase.
  (:event ev_start_physics
    :parameters ()
    :precondition (and
      (scan-required)
      (init-phase)
      (>= (sim-time) 0.1)
    )
    :effect (and
      (not (init-phase))
      (assign (sim-time) 0)
    )
  )

  ;; ======================================================
  ;; SEPARATED PHYSICS CHECKS (NON-SCANNER)
  ;; ======================================================

  ;; Mark only active (stone/gem) cells; no full-grid scan.
  (:event ev_mark_active_cell
    :parameters (?c)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (or (stone ?c) (gem ?c))
      (not (updated ?c))
      (not (pending ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
    :effect (and
      (pending ?c)
      (check_fall ?c)
    )
  )

  (:event ev_can_fall
    :parameters (?c ?down)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (check_fall ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
      (down ?c ?down)
      (empty ?down)
    )
    :effect (and
      (can_fall ?c)
      (not (check_fall ?c))
      (ready_to_move ?c)
    )
  )

  (:event ev_not_fall
    :parameters (?c ?down)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (check_fall ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
      (down ?c ?down)
      (not (empty ?down))
    )
    :effect (and
      (not (can_fall ?c))
      (not (check_fall ?c))
      (check_roll_left ?c)
    )
  )

  (:event ev_can_roll_left
    :parameters (?c ?left ?down_left ?down)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (check_roll_left ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
      (right-of ?left ?c)
      (down ?left ?down_left)
      (down ?c ?down)
      (not (agent-at ?down))
      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
      (empty ?left)
      (or (empty ?down_left) (updated ?down_left))
    )
    :effect (and
      (can_roll_left ?c)
      (not (check_roll_left ?c))
      (ready_to_move ?c)
    )
  )

  (:event ev_not_roll_left
    :parameters (?c ?left ?down_left ?down)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (check_roll_left ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
      (right-of ?left ?c)
      (down ?left ?down_left)
      (down ?c ?down)
      (or
        (agent-at ?down)
        (and
          (not (stone ?down))
          (not (gem ?down))
          (not (brick ?down))
          (not (updated ?down))
        )
        (falling ?down)
        (not (empty ?left))
        (and (not (empty ?down_left)) (not (updated ?down_left)))
      )
    )
    :effect (and
      (not (can_roll_left ?c))
      (not (check_roll_left ?c))
      (check_roll_right ?c)
    )
  )

  (:event ev_not_roll_left_default
    :parameters (?c)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (check_roll_left ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
    )
    :effect (and
      (not (can_roll_left ?c))
      (not (check_roll_left ?c))
      (check_roll_right ?c)
    )
  )

  (:event ev_can_roll_right
    :parameters (?c ?right ?down_right ?down)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (check_roll_right ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
      (right-of ?c ?right)
      (down ?right ?down_right)
      (down ?c ?down)
      (not (agent-at ?down))
      (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
      (not (falling ?down))
      (empty ?right)
      (or (empty ?down_right) (updated ?down_right))
    )
    :effect (and
      (can_roll_right ?c)
      (not (check_roll_right ?c))
      (ready_to_move ?c)
    )
  )

  (:event ev_not_roll_right
    :parameters (?c ?right ?down_right ?down)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (check_roll_right ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
      (right-of ?c ?right)
      (down ?right ?down_right)
      (down ?c ?down)
      (or
        (agent-at ?down)
        (and
          (not (stone ?down))
          (not (gem ?down))
          (not (brick ?down))
          (not (updated ?down))
        )
        (falling ?down)
        (not (empty ?right))
        (and (not (empty ?down_right)) (not (updated ?down_right)))
      )
    )
    :effect (and
      (not (can_roll_right ?c))
      (not (check_roll_right ?c))
      (ready_to_move ?c)
    )
  )

  (:event ev_not_roll_right_default
    :parameters (?c)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (check_roll_right ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
    )
    :effect (and
      (not (can_roll_right ?c))
      (not (check_roll_right ?c))
      (ready_to_move ?c)
    )
  )

  ;; ======================================================
  ;; SEPARATED STONE/GEM MOVEMENT
  ;; ======================================================

  (:event ev_stone_fall
    :parameters (?c ?down)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (ready_to_move ?c)
      (pending ?c)
      (not (updated ?c))
      (stone ?c)
      (down ?c ?down)
      (can_fall ?c)
    )
    :effect (and
      (not (stone ?c))
      (not (falling ?c))
      (empty ?c)
      (stone ?down)
      (falling ?down)
      (not (empty ?down))
      (updated ?c)
      (updated ?down)
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  (:event ev_gem_fall
    :parameters (?c ?down)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (ready_to_move ?c)
      (pending ?c)
      (not (updated ?c))
      (gem ?c)
      (down ?c ?down)
      (can_fall ?c)
    )
    :effect (and
      (not (gem ?c))
      (not (falling ?c))
      (empty ?c)
      (gem ?down)
      (falling ?down)
      (not (empty ?down))
      (updated ?c)
      (updated ?down)
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  (:event ev_stone_roll_left
    :parameters (?c ?left)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (ready_to_move ?c)
      (pending ?c)
      (not (updated ?c))
      (right-of ?left ?c)
      (stone ?c)
      (can_roll_left ?c)
      (not (can_fall ?c))
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
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  (:event ev_gem_roll_left
    :parameters (?c ?left)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (ready_to_move ?c)
      (pending ?c)
      (not (updated ?c))
      (right-of ?left ?c)
      (gem ?c)
      (can_roll_left ?c)
      (not (can_fall ?c))
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
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  (:event ev_stone_roll_right
    :parameters (?c ?right)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (ready_to_move ?c)
      (pending ?c)
      (not (updated ?c))
      (right-of ?c ?right)
      (stone ?c)
      (can_roll_right ?c)
      (not (can_fall ?c))
      (not (can_roll_left ?c))
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
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  (:event ev_gem_roll_right
    :parameters (?c ?right)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (ready_to_move ?c)
      (pending ?c)
      (not (updated ?c))
      (right-of ?c ?right)
      (gem ?c)
      (can_roll_right ?c)
      (not (can_fall ?c))
      (not (can_roll_left ?c))
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
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  (:event ev_stone_gem_noop
    :parameters (?c)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (ready_to_move ?c)
      (pending ?c)
      (not (updated ?c))
      (or (stone ?c) (gem ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
    )
    :effect (and
      (updated ?c)
      (not (falling ?c))
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  ;; Agent can occupy a cell that was marked active.
  (:event ev_agent_noop
    :parameters (?c)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (agent-at ?c)
    )
    :effect (and
      (updated ?c)
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  (:event ev_crush_by_stone
    :parameters (?c ?d)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (not (updated ?c))
      (stone ?c)
      (falling ?c)
      (down ?c ?d)
      (agent-at ?d)
    )
    :effect (and
      (not (agent-alive))
      (crushed)
      (updated ?c)
      (not (falling ?c))
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  (:event ev_crush_by_gem
    :parameters (?c ?d)
    :precondition (and
      (scan-required)
      (not (init-phase))
      (pending ?c)
      (not (updated ?c))
      (gem ?c)
      (falling ?c)
      (down ?c ?d)
      (agent-at ?d)
    )
    :effect (and
      (not (agent-alive))
      (crushed)
      (updated ?c)
      (not (falling ?c))
      (not (pending ?c))
      (not (can_fall ?c))
      (not (can_roll_left ?c))
      (not (can_roll_right ?c))
      (not (check_fall ?c))
      (not (check_roll_left ?c))
      (not (check_roll_right ?c))
      (not (ready_to_move ?c))
    )
  )

  ;; End tick after one unit of autonomous physics-time.
  (:event ev_end_tick
    :parameters ()
    :precondition (and
      (scan-required)
      (not (init-phase))
      (>= (sim-time) 1)
    )
    :effect (and
      (not (scan-required))
      (not (init-phase))
      (scan-complete)
      (assign (sim-time) 0)
    )
  )
)
