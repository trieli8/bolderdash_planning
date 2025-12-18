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
