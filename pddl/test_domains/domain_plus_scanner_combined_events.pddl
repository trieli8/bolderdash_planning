; Generated test domain variant
; variant: domain_plus_scanner_combined_events.pddl
; source: pddl/domain_plus_scanner_separated_events_fluents.pddl
(define (domain mine-tick-gravity-plus-scanner-separated-events-fluents)
  (:requirements :strips :negative-preconditions :disjunctive-preconditions :universal-preconditions :conditional-effects :action-costs :processes :events)


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

    ;; updated-in-this-tick flags
    (updated ?c)

    ;; entity identities and per-entity location mirrors
    (agent-entity ?a)
    (stone-entity ?s)
    (gem-entity ?g)
    (agent-at-obj ?a ?c)
    (stone-at ?s ?c)
    (gem-at ?g ?c)

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
    (x ?e)
    (y ?e)
    (cx ?c)
    (cy ?c)
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
            (increase (total-cost) 1)
        )
    )

    (:action move_empty
        :parameters (?from ?to ?a)
        :precondition (and
            (agent-alive)
            (agent-entity ?a)
            (agent-at ?from)
            (agent-at-obj ?a ?from)
                (or (up ?from ?to)
                (down ?from ?to)
                (right-of ?to ?from)
                (right-of ?from ?to))
            (empty ?to)
            (scan-complete)
        )
        :effect (and
            (not (agent-at ?from))
            (agent-at ?to)
            (not (agent-at-obj ?a ?from))
            (agent-at-obj ?a ?to)
            (assign (x ?a) (cx ?to))
            (assign (y ?a) (cy ?to))

            (empty ?from)
            (not (empty ?to))

            (scan-required)
            (not (scan-complete))
            (increase (total-cost) 1)
        )
    )

    ;; Move into dirt (mines it to empty)
    (:action move_into_dirt
        :parameters (?from ?to ?a)
        :precondition (and
            (agent-alive)
            (agent-entity ?a)
            (agent-at ?from)
            (agent-at-obj ?a ?from)
                (or (up ?from ?to)
                (down ?from ?to)
                (right-of ?to ?from)
                (right-of ?from ?to))
            (dirt ?to)
            (scan-complete)
        )
        :effect (and
            (not (agent-at ?from))
            (agent-at ?to)
            (not (agent-at-obj ?a ?from))
            (agent-at-obj ?a ?to)
            (assign (x ?a) (cx ?to))
            (assign (y ?a) (cy ?to))

            (not (dirt ?to))

            (empty ?from)
            (not (empty ?to))

            (scan-required)
            (not (scan-complete))
            (increase (total-cost) 1)
        )
    )

    ;; Move into gem (collect it -> got-gem)
    (:action move_into_gem
        :parameters (?from ?to ?a ?g)
        :precondition (and
            (agent-alive)
            (agent-entity ?a)
            (gem-entity ?g)
            (agent-at ?from)
            (agent-at-obj ?a ?from)
                (or (up ?from ?to)
                (down ?from ?to)
                (right-of ?to ?from)
                (right-of ?from ?to))
            (gem ?to)
            (gem-at ?g ?to)
            (scan-complete)
        )
        :effect (and
            (not (agent-at ?from))
            (agent-at ?to)
            (not (agent-at-obj ?a ?from))
            (agent-at-obj ?a ?to)
            (assign (x ?a) (cx ?to))
            (assign (y ?a) (cy ?to))

            (empty ?from)
            (not (empty ?to))

            (not (gem ?to))
            (not (gem-at ?g ?to))
            (assign (x ?g) -1)
            (assign (y ?g) -1)
            (not (falling ?to))

            (got-gem)

            (scan-required)
            (not (scan-complete))
            (increase (total-cost) 1)
        )
    )

    (:action move_push_rock
        :parameters (?from ?to ?stone_dest ?a ?s)
        :precondition (and
            (agent-alive)
            (agent-entity ?a)
            (stone-entity ?s)
            (agent-at ?from)
            (agent-at-obj ?a ?from)
            (or
                (and (right-of ?to ?from) (right-of ?stone_dest ?to))
                (and (right-of ?from ?to) (right-of ?to ?stone_dest)))
        (stone ?to)
        (stone-at ?s ?to)
        (empty ?stone_dest)
        (not (falling ?to))
        (scan-complete)
        )
        :effect (and
            (not (agent-at ?from))
            (agent-at ?to)
            (not (agent-at-obj ?a ?from))
            (agent-at-obj ?a ?to)
            (assign (x ?a) (cx ?to))
            (assign (y ?a) (cy ?to))

            (not (empty ?to))
            (empty ?from)

            (not (stone ?to))
            (stone ?stone_dest)
            (not (stone-at ?s ?to))
            (stone-at ?s ?stone_dest)
            (assign (x ?s) (cx ?stone_dest))
            (assign (y ?s) (cy ?stone_dest))

            (not (empty ?stone_dest))
            (not (falling ?stone_dest))

            ;; match the updated domain behavior
            (updated ?to)

            (scan-required)
            (not (scan-complete))
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

            (or (updated ?c) (brick ?c) (dirt ?c) (empty ?c) (agent-at ?c))
        )
        :effect (and
            (not (scan-at ?c))
            (not (updated ?c))
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

            (updated ?c)
        )
        :effect (and
            (not (scan-at ?c))
            (not (updated ?c))
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
    (:event forced-can_fall
        :parameters (?c ?down)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_fall)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (down ?c ?down)

            (empty ?down)
        )
        :effect (and
            (can_fall)
            (not (check_fall))
            (ready_to_move)
        )
    )

    (:event forced-not_fall
        :parameters (?c ?down)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_fall)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (down ?c ?down)

            (not (empty ?down))
        )
        :effect (and
            (not (can_fall))
            (not (check_fall))
            (check_roll_left)
        )
    )

    (:event forced-not_fall_no_down
        :parameters (?c)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_fall)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            (forall (?d - object) (not (down ?c ?d)))
        )
        :effect (and
            (not (can_fall))
            (not (check_fall))
            (check_roll_left)
        )
    )

    (:event forced-can_roll_left
        :parameters (?c ?left ?down_left ?down)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_left)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (right-of ?left ?c)
            (down ?left ?down_left)
            (down ?c ?down)

            (not (agent-at ?down))
            (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
            (not (falling ?down))

            (empty ?left)
            (empty ?down_left)
        )
        :effect (and
            (can_roll_left)
            (not (check_roll_left))
            (ready_to_move)
        )
    )

    (:event forced-not_roll_left
        :parameters (?c ?left ?down_left ?down)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_left)
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
                    (not (updated ?down)))
                (falling ?down)
                (not (empty ?left))
                (not (empty ?down_left))
            )

        )
        :effect (and
            (not (can_roll_left))
            (not (check_roll_left))
            (check_roll_right)
        )
    )

    (:event forced-not_roll_left_default
        :parameters (?c)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_left)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            (or
                (forall (?down - object) (not (down ?c ?down)))
                (forall (?left ?down_left - object)
                    (or
                        (not (right-of ?left ?c))
                        (not (down ?left ?down_left))
                    )
                )
            )
        )
        :effect (and
            (not (can_roll_left))
            (not (check_roll_left))
            (check_roll_right)
        )
    )

    (:event forced-can_roll_right
        :parameters (?c ?right ?down_right ?down)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_right)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (right-of ?c ?right)
            (down ?right ?down_right)
            (down ?c ?down)

            (not (agent-at ?down))
            (or (stone ?down) (gem ?down) (brick ?down) (updated ?down))
            (not (falling ?down))

            (empty ?right)
            (empty ?down_right)
        )
        :effect (and
            (can_roll_right)
            (not (check_roll_right))
            (ready_to_move)
        )
    )

    (:event forced-not_roll_right
        :parameters (?c ?right ?down_right ?down)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_right)
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
                    (not (updated ?down)))
                (falling ?down)
                (not (empty ?right))
                (not (empty ?down_right))
            )

        )
        :effect (and
            (not (can_roll_right))
            (not (check_roll_right))
            (ready_to_move)
        )
    )

    (:event forced-not_roll_right_default
        :parameters (?c)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_right)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            (or
                (forall (?down - object) (not (down ?c ?down)))
                (forall (?right ?down_right - object)
                    (or
                        (not (right-of ?c ?right))
                        (not (down ?right ?down_right))
                    )
                )
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
    (:event forced-stone_fall
        :parameters (?c ?down ?s)
        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))
            (stone-entity ?s)
            (stone-at ?s ?c)

            (down ?c ?down)
            (stone ?c)

            (can_fall)
        )
        :effect (and
            (not (stone ?c))
            (not (falling ?c))
            (empty ?c)
            (not (stone-at ?s ?c))

            (stone ?down)
            (falling ?down)
            (not (empty ?down))
            (stone-at ?s ?down)
            (assign (x ?s) (cx ?down))
            (assign (y ?s) (cy ?down))

            (updated ?down)
            (updated ?c)
        )
    )

    (:event forced-gem_fall
        :parameters (?c ?down ?g)
        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))
            (gem-entity ?g)
            (gem-at ?g ?c)

            (down ?c ?down)
            (gem ?c)

            (can_fall)
        )
        :effect (and
            (not (gem ?c))
            (not (falling ?c))
            (empty ?c)
            (not (gem-at ?g ?c))

            (gem ?down)
            (falling ?down)
            (not (empty ?down))
            (gem-at ?g ?down)
            (assign (x ?g) (cx ?down))
            (assign (y ?g) (cy ?down))

            (updated ?down)
            (updated ?c)
        )
    )

    (:event forced-stone_roll_left
        :parameters (?c ?left ?s)

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))
            (stone-entity ?s)
            (stone-at ?s ?c)

            (right-of ?left ?c)
            (stone ?c)
            
            (can_roll_left)
            (not (can_fall))
        )

        :effect (and
            (not (stone ?c))
            (not (falling ?c))
            (empty ?c)
            (not (stone-at ?s ?c))

            (stone ?left)
            (falling ?left)
            (not (empty ?left))
            (stone-at ?s ?left)
            (assign (x ?s) (cx ?left))
            (assign (y ?s) (cy ?left))

            (updated ?c)
            (updated ?left)
        )
    )
    
    (:event forced-gem_roll_left
        :parameters (?c ?left ?g)

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))
            (gem-entity ?g)
            (gem-at ?g ?c)

            (right-of ?left ?c)
            (gem ?c)
            
            (can_roll_left)
            (not (can_fall))
        )

        :effect (and
            (not (gem ?c))
            (not (falling ?c))
            (empty ?c)
            (not (gem-at ?g ?c))

            (gem ?left)
            (falling ?left)
            (not (empty ?left))
            (gem-at ?g ?left)
            (assign (x ?g) (cx ?left))
            (assign (y ?g) (cy ?left))

            (updated ?c)
            (updated ?left)
        )
    )


    (:event forced-stone_roll_right
        :parameters (?c ?right ?s)

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))
            (stone-entity ?s)
            (stone-at ?s ?c)

            (right-of ?c ?right)
            (stone ?c)
            
            (can_roll_right)
            (not (can_fall))
            (not (can_roll_left))

        )

        :effect (and
            (not (stone ?c))
            (not (falling ?c))
            (empty ?c)
            (not (stone-at ?s ?c))

            (stone ?right)
            (falling ?right)
            (not (empty ?right))
            (stone-at ?s ?right)
            (assign (x ?s) (cx ?right))
            (assign (y ?s) (cy ?right))

            (updated ?c)
            (updated ?right)
        )
    )
    
    (:event forced-gem_roll_right
        :parameters (?c ?right ?g)

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))
            (gem-entity ?g)
            (gem-at ?g ?c)

            (right-of ?c ?right)
            (gem ?c)
            
            (can_roll_right)
            (not (can_fall))
            (not (can_roll_left))
        )

        :effect (and
            (not (gem ?c))
            (not (falling ?c))
            (empty ?c)
            (not (gem-at ?g ?c))

            (gem ?right)
            (falling ?right)
            (not (empty ?right))
            (gem-at ?g ?right)
            (assign (x ?g) (cx ?right))
            (assign (y ?g) (cy ?right))

            (updated ?c)
            (updated ?right)
        )
    )

    (:event forced-stone_gem_noop
        :parameters (?c )

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (not (can_fall))
            (not (can_roll_left))
            (not (can_roll_right))
        )

        :effect (and
            (updated ?c)
            (not (falling ?c))
        )
    )


)
