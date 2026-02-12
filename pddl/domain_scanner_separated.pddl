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
    (last-cell ?c - border-cell)
    (next-cell ?c1 - real-cell ?c2 - cell)

    ;; scan pointer for this tick
    (scan-at ?c - cell)
    (scan-required)
    (scan-complete)
    (scan-active)

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

    (can_fall)
    (can_roll_left)
    (can_roll_right)
    (check_fall)
    (check_roll_left)
    (check_roll_right)
    (ready_to_move)
  )

  ;; ======================================================
  ;; AGENT MOVEMENT
  ;; ======================================================
    (:action move_noop
        :parameters (?start - real-cell)
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
        :parameters (?from ?to - real-cell)
        :precondition (and
            (agent-alive)
            (agent-at ?from)
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

            (empty ?from)
            (not (empty ?to))

            (scan-required)
            (not (scan-complete))
            (increase (total-cost) 1)
        )
    )

    ;; Move into dirt (mines it to empty)
    (:action move_into_dirt
        :parameters (?from ?to - real-cell)
        :precondition (and
            (agent-alive)
            (agent-at ?from)
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
        :parameters (?from ?to - real-cell)
        :precondition (and
            (agent-alive)
            (agent-at ?from)
                (or (up ?from ?to)
                (down ?from ?to)
                (right-of ?to ?from)
                (right-of ?from ?to))
            (gem ?to)
            (scan-complete)
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
        :parameters (?from ?to ?stone_dest - real-cell)
        :precondition (and
            (agent-alive)
            (agent-at ?from)
            (or
                (and (right-of ?to ?from) (right-of ?stone_dest ?to))
                (and (right-of ?from ?to) (right-of ?to ?stone_dest)))
        (stone ?to)
        (empty ?stone_dest)
        (not (falling ?to))
        (scan-complete)
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

            (scan-required)
            (not (scan-complete))
            (increase (total-cost) 1)
        )
    )

  ;; ======================================================
  ;; SCANNER MOVEMENT
  ;; ======================================================
    (:action __forced__start_tick
        :parameters (?start - real-cell)
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
    
    (:action __forced__advance_scan_no_update
        :parameters (?c - real-cell ?next - cell)
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

    (:action __forced__advance_scan
        :parameters (?c - real-cell ?next - cell)
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

    (:action __forced__end_tick
        :parameters (?c - border-cell)
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
    (:action __forced__can_fall
        :parameters (?c - real-cell ?down - cell)
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

    (:action __forced__not_fall
        :parameters (?c - real-cell ?down - cell)
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

    (:action __forced__can_roll_left
        :parameters (?c - real-cell ?left ?down_left ?down ?up_left - cell)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_left)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (right-of ?left ?c)
            (down ?left ?down_left)
            (down ?c ?down)
            (up ?left ?up_left)

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

    (:action __forced__not_roll_left
        :parameters (?c - real-cell ?left ?down_left ?down ?up_left - cell)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_left)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (right-of ?left ?c)
            (down ?left ?down_left)
            (down ?c ?down)
            (up ?left ?up_left)

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

    (:action __forced__can_roll_right
        :parameters (?c - real-cell ?right ?down_right ?down ?up_right - cell)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_right)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (right-of ?c ?right)
            (down ?right ?down_right)
            (down ?c ?down)
            (up ?right ?up_right)

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

    (:action __forced__not_roll_right
        :parameters (?c - real-cell ?right ?down_right ?down ?up_right - cell)
        :precondition (and
            (scan-required)
            (scan-at ?c)
            (check_roll_right)
            (not (updated ?c))
            (or (stone ?c) (gem ?c))
            
            (right-of ?c ?right)
            (down ?right ?down_right)
            (down ?c ?down)
            (up ?right ?up_right)

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

  ;; ======================================================
  ;; STONE/GEM MOVEMENT
  ;; ======================================================
    (:action __forced__stone_fall
        :parameters (?c ?down - real-cell)
        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))

            (down ?c ?down)
            (stone ?c)

            (can_fall)
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
        )
    )

    (:action __forced__gem_fall
        :parameters (?c ?down - real-cell)
        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))

            (down ?c ?down)
            (gem ?c)

            (can_fall)
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
        )
    )

    (:action __forced__stone_roll_left
        :parameters (?c ?left - real-cell )

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))

            (right-of ?left ?c)
            (stone ?c)
            
            (can_roll_left)
            (not (can_fall))
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
        )
    )
    
    (:action __forced__gem_roll_left
        :parameters (?c ?left - real-cell )

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))

            (right-of ?left ?c)
            (gem ?c)
            
            (can_roll_left)
            (not (can_fall))
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
        )
    )


    (:action __forced__stone_roll_right
        :parameters (?c ?right - real-cell )

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))

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

            (stone ?right)
            (falling ?right)
            (not (empty ?right))

            (updated ?c)
            (updated ?right)
        )
    )
    
    (:action __forced__gem_roll_right
        :parameters (?c ?right - real-cell )

        :precondition (and
            (ready_to_move)
            (scan-required)
            (scan-at ?c)
            (not (updated ?c))

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

            (gem ?right)
            (falling ?right)
            (not (empty ?right))

            (updated ?c)
            (updated ?right)
        )
    )

    (:action __forced__stone_gem_noop
        :parameters (?c - real-cell )

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
