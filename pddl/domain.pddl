(define (domain mine-tick-gravity)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :conditional-effects)

  (:types
    cell agent
  )

  (:predicates
    ;; layout / topology
    (up ?from ?to - cell)
    (down ?from ?to - cell)
    (left-of ?from ?to - cell)
    (right-of ?from ?to - cell)

    ;; linear scan order (top-left -> bottom-right)
    (first-cell ?c - cell)
    (last-cell ?c - cell)
    (next-cell ?c1 ?c2 - cell)

    ;; scan pointer for this tick
    (scan-at ?c - cell)

    ;; tick parity (exactly one true at a time)
    (parity)

    ;; updated-in-this-tick flags (interpreted via parity)
    (updated ?c - cell)

    ;; cell contents
    (agent-at ?c - cell)
    (empty ?c - cell)
    (dirt ?c - cell)
    (stone ?c - cell)
    (gem ?c - cell)
    (brick ?c - cell)

    ;; grid edge info
    (bottom ?c - cell)
    (top ?c - cell)
    (left-edge ?c - cell)
    (right-edge ?c - cell)
    

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
    :parameters (?a - agent ?from ?to ?start - cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (empty ?to)
      (first-cell ?start))
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      ;; start a new tick scan
      (scan-at ?start))
  )

  ;; Move into dirt (mines it to empty)
  (:action move-into-dirt
    :parameters (?a - agent ?from ?to ?start - cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (dirt ?to)
      (first-cell ?start))
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (not (dirt ?to))
      (empty ?to)
      (scan-at ?start))
  )

  ;; Move into gem (collect it -> got-gem)
  (:action move-into-gem
    :parameters (?a - agent ?from ?to ?start - cell)
    :precondition (and (agent-alive)
      (agent-at ?from)
      (or (up ?from ?to)
        (down ?from ?to)
        (left-of ?from ?to)
        (right-of ?from ?to))
      (gem ?to)
      (first-cell ?start))
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (not (gem ?to))
      (empty ?to)
      (got-gem)
      (scan-at ?start))
  )

  (:action move-push-rock
    :parameters (?a - agent ?from ?to ?stone_dest ?start - cell)
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
      (first-cell ?start))
    :effect (and
      (not (agent-at ?from))
      (agent-at ?to)
      (not (stone ?to))
      (empty ?to)
      (not (empty ?stone_dest))
      (stone ?stone_dest)
      ;; start a new tick scan
      (scan-at ?start))
  )

  ;; ======================================================
  ;; FORCED ACTIONS: ONE-TICK CELL UPDATE IN SCAN ORDER
  ;; ======================================================

  ;; TODO deal with edge cases (at the edges of the grid)
  (:action fa-physics-even
    :parameters (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      ;; is the scanner here
      (scan-at ?c)

      ;; is it even parity
      (parity)
      (not (updated ?c))

      ;; Center stone (3rd column)
      (or (stone ?c) (gem ?c))

      ;; Horizontal layout (middle row)
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
    )

    :effect (and

      ;; mark source cell updated in this tick 
      (updated ?c)

      ;; ========== STONE FALLING ==========

      ;; stone falls down
      (when
        (and
          (stone ?c)
          (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; gem falls down
      (when
        (and
          (gem ?c)
          (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; stone rolls left
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; not (stone or gem) at up_left
          (and (not (stone ?up_left))
               (not (gem ?up_left)))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?left)
          (not (empty ?left))
          (updated ?left)))

      ;; gem rolls left
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; not (stone or gem) at up_left
          (and (not (stone ?up_left))
               (not (gem ?up_left)))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?left)
          (not (empty ?left))
          (updated ?left)))

      ;; stone rolls right
      (when
        (and
          ;; check it can't roll left (NNF):
          (or (stone ?up_left)
              (gem ?up_left)
              (not (empty ?left))
              (not (empty ?down_left)))

          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; not (stone or gem) at up_right
          (and (not (stone ?up_right))
               (not (gem ?up_right)))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))
          (updated ?right)))

      ;; gem rolls right
      (when
        (and
          ;; check it can't roll left (NNF):
          (or (stone ?up_left)
              (gem ?up_left)
              (not (empty ?left))
              (not (empty ?down_left)))

          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; not (stone or gem) at up_right
          (and (not (stone ?up_right))
               (not (gem ?up_right)))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))
          (updated ?right)))
    )
  )

  (:action fa-physics-odd
    :parameters (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)

    :precondition (and
      ;; is the scanner here
      (scan-at ?c)

      ;; is it odd parity
      (not (parity))
      (updated ?c)

      ;; Center stone (3rd column)
      (or (stone ?c) (gem ?c))

      ;; Horizontal layout (middle row)
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
    )

    :effect (and
      ;; mark source cell updated in this tick (odd parity ⇒ set updated false)
      (not (updated ?c))

      ;; ========== STONE FALLING ==========

      ;; stone falls down
      (when
        (and (stone ?c)
             (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; gem falls down
      (when
        (and (gem ?c)
             (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; stone rolls left
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; not (stone or gem) at up_left
          (and (not (stone ?up_left))
               (not (gem ?up_left)))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?left)
          (not (empty ?left))
          (not (updated ?left))))

      ;; gem rolls left
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; not (stone or gem) at up_left
          (and (not (stone ?up_left))
               (not (gem ?up_left)))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?left)
          (not (empty ?left))
          (not (updated ?left))))

      ;; stone rolls right
      (when
        (and
          ;; check it can't roll left (NNF, same as even case)
          (or (stone ?up_left)
              (gem ?up_left)
              (not (empty ?left))
              (not (empty ?down_left)))

          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; not (stone or gem) at up_right
          (and (not (stone ?up_right))
               (not (gem ?up_right)))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))
          (not (updated ?right))))

      ;; gem rolls right
      (when
        (and
          ;; check it can't roll left (NNF, same as even case)
          (or (stone ?up_left)
              (gem ?up_left)
              (not (empty ?left))
              (not (empty ?down_left)))

          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; not (stone or gem) at up_right
          (and (not (stone ?up_right))
               (not (gem ?up_right)))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))
          (not (updated ?right))))
      )
  )

  (:action fa-physics-bottom
    :parameters (?c - cell)
    :precondition (and
      (scan-at ?c)
      (bottom ?c)
      ;; Must NOT yet be marked updated for this parity
      (or (and (parity) (not (updated ?c)))
          (and (not (parity)) (updated ?c))))
    :effect (and
      ;; simply enforce the correct updated polarity for this parity
      (when (parity) (updated ?c))
      (when (not (parity)) (not (updated ?c))))
  )

  (:action fa-physics-top-even
    :parameters (?left ?c ?right ?down_left ?down ?down_right - cell)
    :precondition (and
      (scan-at ?c)
      (parity)
      (not (updated ?c))

      ;; top row, but not corners
      (top ?c)
      (not (left-edge ?c))
      (not (right-edge ?c))

      ;; centre has a stone or gem
      (or (stone ?c) (gem ?c))

      ;; horizontal neighbours
      (right-of ?left ?c)
      (right-of ?c ?right)

      ;; below row
      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)
    )
    :effect (and
      ;; mark source as updated for this (even) tick
      (updated ?c)

      ;; ---- STONE FALL DOWN ----
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; ---- GEM FALL DOWN ----
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; ---- STONE ROLL LEFT ----
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?left)
          (not (empty ?left))
          (updated ?left)))

      ;; ---- GEM ROLL LEFT ----
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?left)
          (not (empty ?left))
          (updated ?left)))

      ;; ---- STONE ROLL RIGHT ----
      (when
        (and
          ;; "can't roll left" here = left or down_left not both empty
          (or (not (empty ?left))
              (not (empty ?down_left)))
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))
          (updated ?right)))

      ;; ---- GEM ROLL RIGHT ----
      (when
        (and
          ;; "can't roll left" here = left or down_left not both empty
          (or (not (empty ?left))
              (not (empty ?down_left)))
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))
          (updated ?right)))
    )
  )

  (:action fa-physics-top-odd
    :parameters (?left ?c ?right ?down_left ?down ?down_right - cell)
    :precondition (and
      (scan-at ?c)
      (not (parity))
      (updated ?c)

      (top ?c)
      (not (left-edge ?c))
      (not (right-edge ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?left ?c)
      (right-of ?c ?right)

      (down ?left ?down_left)
      (down ?c ?down)
      (down ?right ?down_right)
    )
    :effect (and
      ;; odd tick ⇒ updated must end up false
      (not (updated ?c))

      ;; ---- STONE FALL DOWN ----
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; ---- GEM FALL DOWN ----
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; ---- STONE ROLL LEFT ----
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?left)
          (not (empty ?left))
          (not (updated ?left))))

      ;; ---- GEM ROLL LEFT ----
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?left)
          (not (empty ?left))
          (not (updated ?left))))

      ;; ---- STONE ROLL RIGHT ----
      (when
        (and
          (or (not (empty ?left))
              (not (empty ?down_left)))
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))
          (not (updated ?right))))

      ;; ---- GEM ROLL RIGHT ----
      (when
        (and
          (or (not (empty ?left))
              (not (empty ?down_left)))
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))
          (not (updated ?right))))
    )
  )

  (:action fa-physics-left-even
    :parameters (?c ?right ?down ?down_right ?up ?up_right - cell)
    :precondition (and
      (scan-at ?c)
      (parity)
      (not (updated ?c))

      (left-edge ?c)
      (not (top ?c))
      (not (bottom ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?c ?right)

      (down ?c ?down)
      (down ?right ?down_right)

      (up ?c ?up)
      (up ?right ?up_right)
    )
    :effect (and
      (updated ?c)

      ;; fall down
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; gem falls down
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; roll right (same pattern as interior, but no left side)
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; nothing resting above-right
          (and (not (stone ?up_right))
              (not (gem ?up_right)))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))
          (updated ?right)))

      ;; gem rolls right (same pattern as interior, but no left side)
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          ;; nothing resting above-right
          (and (not (stone ?up_right))
              (not (gem ?up_right)))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))
          (updated ?right)))
    )
  )

  (:action fa-physics-left-odd
    :parameters (?c ?right ?down ?down_right ?up ?up_right - cell)
    :precondition (and
      (scan-at ?c)
      (not (parity))
      (updated ?c)

      (left-edge ?c)
      (not (top ?c))
      (not (bottom ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?c ?right)

      (down ?c ?down)
      (down ?right ?down_right)

      (up ?c ?up)
      (up ?right ?up_right)
    )
    :effect (and
      (not (updated ?c))

      ;; fall down
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; gem falls down
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; roll right
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (and (not (stone ?up_right))
              (not (gem ?up_right)))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))
          (not (updated ?right))))

      ;; gem rolls right
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (and (not (stone ?up_right))
              (not (gem ?up_right)))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))
          (not (updated ?right))))
    )
  )

  (:action fa-physics-right-even
    :parameters (?left ?c ?down_left ?down ?up_left ?up - cell)
    :precondition (and
      (scan-at ?c)
      (parity)
      (not (updated ?c))

      (right-edge ?c)
      (not (top ?c))
      (not (bottom ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?left ?c)

      (down ?left ?down_left)
      (down ?c ?down)

      (up ?left ?up_left)
      (up ?c ?up)
    )
    :effect (and
      (updated ?c)

      ;; fall down
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; gem falls down
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; roll left
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (and (not (stone ?up_left))
              (not (gem ?up_left)))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?left)
          (not (empty ?left))
          (updated ?left)))

      ;; gem rolls left
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (and (not (stone ?up_left))
              (not (gem ?up_left)))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?left)
          (not (empty ?left))
          (updated ?left)))
    )
  )

  (:action fa-physics-right-odd
    :parameters (?left ?c ?down_left ?down ?up_left ?up - cell)
    :precondition (and
      (scan-at ?c)
      (not (parity))
      (updated ?c)

      (right-edge ?c)
      (not (top ?c))
      (not (bottom ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?left ?c)

      (down ?left ?down_left)
      (down ?c ?down)

      (up ?left ?up_left)
      (up ?c ?up)
    )
    :effect (and
      (not (updated ?c))

      ;; fall down
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; gem falls down
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; roll left
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (and (not (stone ?up_left))
              (not (gem ?up_left)))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?left)
          (not (empty ?left))
          (not (updated ?left))))

      ;; gem rolls left
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (and (not (stone ?up_left))
              (not (gem ?up_left)))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?left)
          (not (empty ?left))
          (not (updated ?left))))
    )
  )

  (:action fa-physics-top-left-corner-even
    :parameters (?c ?right ?down ?down_right - cell)
    :precondition (and
      (scan-at ?c)
      (parity)
      (not (updated ?c))

      (top ?c)
      (left-edge ?c)
      (not (bottom ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?c ?right)
      (down ?c ?down)
      (down ?right ?down_right)
    )
    :effect (and
      ;; mark source updated this tick (even ⇒ updated = true)
      (updated ?c)

      ;; ---- FALL DOWN ----
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; ---- GEM FALL DOWN ----
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; ---- ROLL RIGHT ----
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))
          (updated ?right)))

      ;; ---- GEM ROLL RIGHT ----
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))
          (updated ?right)))
    )
  )

  (:action fa-physics-top-left-corner-odd
    :parameters (?c ?right ?down ?down_right - cell)
    :precondition (and
      (scan-at ?c)
      (not (parity))
      (updated ?c)

      (top ?c)
      (left-edge ?c)
      (not (bottom ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?c ?right)
      (down ?c ?down)
      (down ?right ?down_right)
    )
    :effect (and
      ;; odd parity ⇒ updated = false
      (not (updated ?c))

      ;; ---- FALL DOWN ----
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; ---- GEM FALL DOWN ----
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; ---- ROLL RIGHT ----
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?right)
          (not (empty ?right))
          (not (updated ?right))))

      ;; ---- GEM ROLL RIGHT ----
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?right)
          (empty ?down_right))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?right)
          (not (empty ?right))
          (not (updated ?right))))
    )
  )

  (:action fa-physics-top-right-corner-even
    :parameters (?left ?c ?down_left ?down - cell)
    :precondition (and
      (scan-at ?c)
      (parity)
      (not (updated ?c))

      (top ?c)
      (right-edge ?c)
      (not (bottom ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?left ?c)
      (down ?c ?down)
      (down ?left ?down_left)
    )
    :effect (and
      (updated ?c)

      ;; ---- FALL DOWN ----
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; ---- GEM FALL DOWN ----
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (updated ?down)))

      ;; ---- ROLL LEFT ----
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?left)
          (not (empty ?left))
          (updated ?left)))

      ;; ---- GEM ROLL LEFT ----
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?left)
          (not (empty ?left))
          (updated ?left)))
    )
  )

  (:action fa-physics-top-right-corner-odd
    :parameters (?left ?c ?down_left ?down - cell)
    :precondition (and
      (scan-at ?c)
      (not (parity))
      (updated ?c)

      (top ?c)
      (right-edge ?c)
      (not (bottom ?c))

      (or (stone ?c) (gem ?c))

      (right-of ?left ?c)
      (down ?c ?down)
      (down ?left ?down_left)
    )
    :effect (and
      (not (updated ?c))

      ;; ---- FALL DOWN ----
      (when
        (and (stone ?c)
            (empty ?down))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; ---- GEM FALL DOWN ----
      (when
        (and (gem ?c)
            (empty ?down))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?down)
          (not (empty ?down))
          (not (updated ?down))))

      ;; ---- ROLL LEFT ----
      (when
        (and
          (stone ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (stone ?c))
          (empty ?c)
          (stone ?left)
          (not (empty ?left))
          (not (updated ?left))))

      ;; ---- GEM ROLL LEFT ----
      (when
        (and
          (gem ?c)
          (or (stone ?down) (gem ?down) (brick ?down))
          (empty ?left)
          (empty ?down_left))
        (and
          (not (gem ?c))
          (empty ?c)
          (gem ?left)
          (not (empty ?left))
          (not (updated ?left))))
    )
  )

  ;; -------- Advance scan pointer to next cell --------

  (:action fa-advance-scan
    :parameters (?c ?next - cell)
    :precondition (and
      (scan-at ?c)
      (next-cell ?c ?next)
      ;; current cell already updated this tick
      (or (and (parity) (updated ?c))
          (and (not (parity)) (not (updated ?c))))
    )
    :effect (and
      (not (scan-at ?c))
      (scan-at ?next)
    )
  )

  ;; -------- End-of-tick: at last cell, updated, flip parity --------

  (:action fa-end-tick
    :parameters (?c - cell)
    :precondition (and
      (scan-at ?c)
      (last-cell ?c)
      (or (and (parity) (updated ?c))
          (and (not (parity)) (not (updated ?c))))
    )
    :effect (and
      ;; remove scan pointer: tick finished
      (not (scan-at ?c))

      ;; flip parity
      (when (parity) (not (parity)))
      (when (not (parity)) (parity))
    )
  )
)
