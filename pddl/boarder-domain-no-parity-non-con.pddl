(define (domain mine-tick-gravity)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :conditional-effects)

  (:types
    cell agent
    real-cell border-cell - cell
  )

  (:predicates
    ;; layout / topology
    (up ?from ?to - cell)
    (down ?from ?to - cell)
    (left-of ?from ?to - cell)
    (right-of ?from ?to - cell)
    (real-cell ?c - cell)
    (border-cell ?c - cell)

    ;; linear scan order (top-left -> bottom-right)
    (first-cell ?c - cell)
    (last-cell ?c - cell)
    (next-cell ?c1 ?c2 - cell)

    ;; scan pointer for this tick
    (scan-at ?c - cell)
    (scan-required)

    ;; updated-in-this-tick flags (interpreted via parity)
    (updated ?c - cell)

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
  )

  ;; ======================================================
  ;; AGENT MOVEMENT
  ;; Each move starts a new game tick by setting scan-at to
  ;; the first cell in the English-reading order.
  ;; ======================================================

  (:action move-empty
    :parameters (?a - agent ?from ?to ?start - real-cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (empty ?to)
      (first-cell ?start)
      (not (scan-required))
      )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      ;; start a new tick scan
      (scan-at ?start)
      (scan-required)
      )
    
  )

  ;; Move into dirt (mines it to empty)
  (:action move-into-dirt
    :parameters (?a - agent ?from ?to ?start - real-cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (dirt ?to)
      (first-cell ?start)
      (not (scan-required))
      )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (not (dirt ?to))
      (empty ?to)
      (scan-at ?start)
      (scan-required)
      )
  )

  ;; Move into gem (collect it -> got-gem)
  (:action move-into-gem
    :parameters (?a - agent ?from ?to ?start - real-cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (gem ?to)
      (first-cell ?start)
      (not (scan-required))
      )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (not (gem ?to))
      (empty ?to)
      (got-gem)
      (scan-at ?start)
      (scan-required)
      )
  )

  (:action move-push-rock
    :parameters (?a - agent ?from ?to ?stone_dest ?start - real-cell)
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
      (first-cell ?start)
      (not (scan-required))
      )
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (not (stone ?to))
      (empty ?to)
      (not (empty ?stone_dest))
      (stone ?stone_dest)
      ;; start a new tick scan
      (scan-at ?start)
      (scan-required)
      )
  )

  ;; ======================================================
  ;; FORCED ACTIONS: ONE-TICK CELL UPDATE IN SCAN ORDER
  ;; ======================================================


  (:action fa-physics-stone-fall
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      ;; is the scanner here
      (scan-at ?c)
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
      (empty ?down)
    )

    :effect (and
      (not (stone ?c))
      (empty ?c)

      (stone ?down)
      (not (empty ?down))

      (updated ?c)
      (updated ?down)
    
    )
  )

  (:action fa-physics-gem-fall
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      ;; is the scanner here
      (scan-at ?c)
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
      (empty ?down)
    )

    :effect (and
      (not (gem ?c))
      (empty ?c)

      (gem ?down)
      (not (empty ?down))

      (updated ?c)
      (updated ?down)
    
    )
  )

  (:action fa-physics-stone-roll-left
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      ;; is the scanner here
      (scan-at ?c)
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

      ;;can't fall down
      ; (not (empty ?down)) All ready accounted for below

      ;; Stone and rollable object below
      (stone ?c)
      (or (stone ?down) (gem ?down) (brick ?down))

      ;; we don't caer about up left cause it's already updated
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
          (updated ?left)
    
    )
  )

  (:action fa-physics-gem-roll-left
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      ;; is the scanner here
      (scan-at ?c)
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

      ;;can't fall down
      ; (not (empty ?down)) All ready accounted for below

      ;; Stone and rollable object below
      (gem ?c)
      (or (stone ?down) (gem ?down) (brick ?down))

      ;; we don't caer about up left cause it's already updated
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
          (updated ?left)
    
    )
  )

  (:action fa-physics-stone-roll-right
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      ;; is the scanner here
      (scan-at ?c)
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

      ;;can't fall down
      ; (not (empty ?down)) All ready accounted for below

      ;; Stone and rollable object below
      (stone ?c)
      (or (stone ?down) (gem ?down) (brick ?down))

      ;; we don't caer about up right cause it's already updated
      (empty ?right)
      (not (updated ?right))
      (empty ?down_right)
      (not (updated ?down_right))

      ;; can't roll left
      (or
        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (updated ?down_left)
      )
    )

    :effect (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))

          (updated ?c)
          (updated ?right)
    )
  )

  (:action fa-physics-gem-roll-right
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      ;; is the scanner here
      (scan-at ?c)
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

      ;;can't fall down
      ; (not (empty ?down)) All ready accounted for below

      ;; Stone and rollable object below
      (gem ?c)
      (or (stone ?down) (gem ?down) (brick ?down))

      ;; we don't caer about up right cause it's already updated
      (empty ?right)
      (not (updated ?right))
      (empty ?down_right)
      (not (updated ?down_right))

      (or
        (not (empty ?left))
        (updated ?left)
        (not (empty ?down_left))
        (updated ?down_left)
      )
    )

    :effect (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))

          (updated ?c)
          (updated ?right)
    
    )
  )
  
  ;; No-op cases split by content to avoid DNF blow-up
  (:action fa-physics-stone-noop
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
    :precondition (and
      (scan-at ?c)
      (not (updated ?c))
      (stone ?c)

      (right-of ?left ?c)
      (right-of ?c ?right)
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)
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
    :effect (and (updated ?c))
  )

  (:action fa-physics-gem-noop
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
    :precondition (and
      (scan-at ?c)
      (not (updated ?c))
      (gem ?c)

      (right-of ?left ?c)
      (right-of ?c ?right)
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)
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
    :effect (and (updated ?c))
  )

  (:action fa-physics-other-noop
    :parameters (?c - real-cell ?left ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
    :precondition (and
      (scan-at ?c)
      (not (updated ?c))
      (not (stone ?c))
      (not (gem ?c))

      (right-of ?left ?c)
      (right-of ?c ?right)
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)
      (up ?left ?up_left)
      (up ?c ?up)
      (up ?right ?up_right)
    )
    :effect (and (updated ?c))
  )

  ;; -------- Advance scan pointer to next cell --------

  (:action fa-advance-scan
    :parameters (?c ?next - real-cell)
    :precondition (and
      (scan-at ?c)
      (next-cell ?c ?next)
      (updated ?c)
    )
    :effect (and
      (not (updated ?c))
      (not (scan-at ?c))
      (scan-at ?next)
    )
  )

  ;; -------- End-of-tick: at last cell, updated, flip parity --------

  (:action fa-end-tick
    :parameters (?c - real-cell)
    :precondition (and
      (scan-at ?c)
      (last-cell ?c)
    )
    :effect (and
      ;; remove scan pointer: tick finished
      (not (scan-at ?c))
      (not (scan-required))
      (not (updated ?c))
    )
  )
)
