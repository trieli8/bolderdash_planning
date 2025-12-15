(define (problem mine-3x3-example)
  (:domain mine-tick-gravity)

  (:objects
    player - agent
    c00 c01 c02
    c10 c11 c12
    c20 c21 c22 - cell)

  (:init
    ;; --- topology: vertical adjacency ---
    (down c00 c10) (up c10 c00)
    (down c10 c20) (up c20 c10)
    (down c01 c11) (up c11 c01)
    (down c11 c21) (up c21 c11)
    (down c02 c12) (up c12 c02)
    (down c12 c22) (up c22 c12)

    ;; --- topology: horizontal adjacency ---
    (right-of c00 c01) (left-of c01 c00)
    (right-of c01 c02) (left-of c02 c01)
    (right-of c10 c11) (left-of c11 c10)
    (right-of c11 c12) (left-of c12 c11)
    (right-of c20 c21) (left-of c21 c20)
    (right-of c21 c22) (left-of c22 c21)

    ;; --- linear scan order (row-major, top-left to bottom-right) ---
    (first-cell c00)
    (next-cell c00 c01)
    (next-cell c01 c02)
    (next-cell c02 c10)
    (next-cell c10 c11)
    (next-cell c11 c12)
    (next-cell c12 c20)
    (next-cell c20 c21)
    (next-cell c21 c22)
    (last-cell c22)

    ;; --- initial parity ---
    (parity)             ; active parity
    ;; parity1 is false by default

    ;; --- contents ---
    (agent-alive)
    (at-agent c00)

    ;; row 0
    (empty c01)
    (empty c02)

    ;; row 1:
    (stone c10)
    (dirt c11)
    (empty c12)

    ;; row 2: 
    (gem c20)
    (gem c22)
    (empty c21)

  )

  ;; Goal: get any gem and still be alive (so crushed plans are not accepted)
  (:goal (and (got-gem)
              (agent-alive)))
)
