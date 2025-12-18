(define (domain mine-tick-gravity) (:requirements
  :strips
  :typing
  :negative-preconditions
  :disjunctive-preconditions
  :conditional-effects
) (:types
  cell
  agent
) (:predicates
  (up ?from ?to - cell)
  (down ?from ?to - cell)
  (left-of ?from ?to - cell)
  (right-of ?from ?to - cell)
  (first-cell ?c - cell)
  (last-cell ?c - cell)
  (next-cell ?c1 ?c2 - cell)
  (scan-at ?c - cell)
  (scan-required)
  (parity)
  (updated ?c - cell)
  (agent-at ?c - cell)
  (empty ?c - cell)
  (dirt ?c - cell)
  (stone ?c - cell)
  (gem ?c - cell)
  (brick ?c - cell)
  (bottom ?c - cell)
  (top ?c - cell)
  (left-edge ?c - cell)
  (right-edge ?c - cell)
  (agent-alive)
  (got-gem)
  (crushed)
) (:action
  move-empty-base
  :parameters
  (?a - agent ?from ?to ?start - cell)
  :precondition
  (and
    (agent-alive)
    (agent-at ?from)
    (or (up ?from ?to) (down ?from ?to) (left-of ?from ?to) (right-of ?from ?to))
    (empty ?to)
    (first-cell ?start)
    (not (scan-required))
  )
  :effect
  (and
    (not (agent-at ?from))
    (agent-at ?to)
    (scan-at ?start)
    (scan-required)
  )
) (:action
  move-into-dirt-base
  :parameters
  (?a - agent ?from ?to ?start - cell)
  :precondition
  (and
    (agent-alive)
    (agent-at ?from)
    (or (up ?from ?to) (down ?from ?to) (left-of ?from ?to) (right-of ?from ?to))
    (dirt ?to)
    (first-cell ?start)
    (not (scan-required))
  )
  :effect
  (and
    (not (agent-at ?from))
    (agent-at ?to)
    (not (dirt ?to))
    (empty ?to)
    (scan-at ?start)
    (scan-required)
  )
) (:action
  move-into-gem-base
  :parameters
  (?a - agent ?from ?to ?start - cell)
  :precondition
  (and
    (agent-alive)
    (agent-at ?from)
    (or (up ?from ?to) (down ?from ?to) (left-of ?from ?to) (right-of ?from ?to))
    (gem ?to)
    (first-cell ?start)
    (not (scan-required))
  )
  :effect
  (and
    (not (agent-at ?from))
    (agent-at ?to)
    (not (gem ?to))
    (empty ?to)
    (got-gem)
    (scan-at ?start)
    (scan-required)
  )
) (:action
  move-push-rock-base
  :parameters
  (?a - agent ?from ?to ?stone_dest ?start - cell)
  :precondition
  (and
    (agent-alive)
    (agent-at ?from)
    (or (and
      (up ?from ?to)
      (up ?to ?stone_dest)
    ) (and
      (left-of ?from ?to)
      (left-of ?to ?stone_dest)
    ) (and
      (right-of ?from ?to)
      (right-of ?to ?stone_dest)
    ) (and
      (down ?from ?to)
      (down ?to ?stone_dest)
    ))
    (stone ?to)
    (empty ?stone_dest)
    (first-cell ?start)
    (not (scan-required))
  )
  :effect
  (and
    (not (agent-at ?from))
    (agent-at ?to)
    (not (stone ?to))
    (empty ?to)
    (not (empty ?stone_dest))
    (stone ?stone_dest)
    (scan-at ?start)
    (scan-required)
  )
) (:action
  fa-physics-even-base
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (parity)
    (not (updated ?c))
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (updated ?c)
  )
) (:action
  fa-physics-even-w1
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (parity)
    (not (updated ?c))
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (stone ?c)
    (empty ?down)
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (updated ?c)
    (and
      (not (stone ?c))
      (empty ?c)
      (stone ?down)
      (not (empty ?down))
      (updated ?down)
    )
  )
) (:action
  fa-physics-even-w2
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (parity)
    (not (updated ?c))
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (gem ?c)
    (empty ?down)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (updated ?c)
    (and
      (not (gem ?c))
      (empty ?c)
      (gem ?down)
      (not (empty ?down))
      (updated ?down)
    )
  )
) (:action
  fa-physics-even-w3
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (parity)
    (not (updated ?c))
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (stone ?c)
    (or (stone ?down) (gem ?down) (brick ?down))
    (not (stone ?up_left))
    (not (gem ?up_left))
    (empty ?left)
    (empty ?down_left)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (updated ?c)
    (and
      (not (stone ?c))
      (empty ?c)
      (stone ?left)
      (not (empty ?left))
      (updated ?left)
    )
  )
) (:action
  fa-physics-even-w4
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (parity)
    (not (updated ?c))
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (gem ?c)
    (or (stone ?down) (gem ?down) (brick ?down))
    (not (stone ?up_left))
    (not (gem ?up_left))
    (empty ?left)
    (empty ?down_left)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (updated ?c)
    (and
      (not (gem ?c))
      (empty ?c)
      (gem ?left)
      (not (empty ?left))
      (updated ?left)
    )
  )
) (:action
  fa-physics-even-w5
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (parity)
    (not (updated ?c))
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (or (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (stone ?c)
    (or (stone ?down) (gem ?down) (brick ?down))
    (not (stone ?up_right))
    (not (gem ?up_right))
    (empty ?right)
    (empty ?down_right)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (updated ?c)
    (and
      (not (stone ?c))
      (empty ?c)
      (stone ?right)
      (not (empty ?right))
      (updated ?right)
    )
  )
) (:action
  fa-physics-even-w6
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (parity)
    (not (updated ?c))
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (or (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (gem ?c)
    (or (stone ?down) (gem ?down) (brick ?down))
    (not (stone ?up_right))
    (not (gem ?up_right))
    (empty ?right)
    (empty ?down_right)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (updated ?c)
    (and
      (not (gem ?c))
      (empty ?c)
      (gem ?right)
      (not (empty ?right))
      (updated ?right)
    )
  )
) (:action
  fa-physics-odd-base
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (not (parity))
    (updated ?c)
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (not (updated ?c))
  )
) (:action
  fa-physics-odd-w1
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (not (parity))
    (updated ?c)
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (stone ?c)
    (empty ?down)
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (not (updated ?c))
    (and
      (not (stone ?c))
      (empty ?c)
      (stone ?down)
      (not (empty ?down))
      (not (updated ?down))
    )
  )
) (:action
  fa-physics-odd-w2
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (not (parity))
    (updated ?c)
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (gem ?c)
    (empty ?down)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (not (updated ?c))
    (and
      (not (gem ?c))
      (empty ?c)
      (gem ?down)
      (not (empty ?down))
      (not (updated ?down))
    )
  )
) (:action
  fa-physics-odd-w3
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (not (parity))
    (updated ?c)
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (stone ?c)
    (or (stone ?down) (gem ?down) (brick ?down))
    (not (stone ?up_left))
    (not (gem ?up_left))
    (empty ?left)
    (empty ?down_left)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (not (updated ?c))
    (and
      (not (stone ?c))
      (empty ?c)
      (stone ?left)
      (not (empty ?left))
      (not (updated ?left))
    )
  )
) (:action
  fa-physics-odd-w4
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (not (parity))
    (updated ?c)
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (gem ?c)
    (or (stone ?down) (gem ?down) (brick ?down))
    (not (stone ?up_left))
    (not (gem ?up_left))
    (empty ?left)
    (empty ?down_left)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (not (updated ?c))
    (and
      (not (gem ?c))
      (empty ?c)
      (gem ?left)
      (not (empty ?left))
      (not (updated ?left))
    )
  )
) (:action
  fa-physics-odd-w5
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (not (parity))
    (updated ?c)
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (or (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (stone ?c)
    (or (stone ?down) (gem ?down) (brick ?down))
    (not (stone ?up_right))
    (not (gem ?up_right))
    (empty ?right)
    (empty ?down_right)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (not (updated ?c))
    (and
      (not (stone ?c))
      (empty ?c)
      (stone ?right)
      (not (empty ?right))
      (not (updated ?right))
    )
  )
) (:action
  fa-physics-odd-w6
  :parameters
  (?left ?c ?right ?down_left ?down ?down_right ?up_left ?up ?up_right - cell)
  :precondition
  (and
    (scan-at ?c)
    (not (parity))
    (updated ?c)
    (right-of ?left ?c)
    (right-of ?c ?right)
    (down ?left ?down_left)
    (down ?c ?down)
    (down ?right ?down_right)
    (up ?left ?up_left)
    (up ?c ?up)
    (up ?right ?up_right)
    (or (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (gem ?c)
    (or (stone ?down) (gem ?down) (brick ?down))
    (not (stone ?up_right))
    (not (gem ?up_right))
    (empty ?right)
    (empty ?down_right)
    (or (not (stone ?c)) (not (empty ?down)))
    (or (not (gem ?c)) (not (empty ?down)))
    (or (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (not (gem ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_left) (gem ?up_left) (not (empty ?left)) (not (empty ?down_left)))
    (or (and
      (not (stone ?up_left))
      (not (gem ?up_left))
      (empty ?left)
      (empty ?down_left)
    ) (not (stone ?c)) (and
      (not (stone ?down))
      (not (gem ?down))
      (not (brick ?down))
    ) (stone ?up_right) (gem ?up_right) (not (empty ?right)) (not (empty ?down_right)))
  )
  :effect
  (and
    (not (updated ?c))
    (and
      (not (gem ?c))
      (empty ?c)
      (gem ?right)
      (not (empty ?right))
      (not (updated ?right))
    )
  )
) (:action
  fa-advance-scan-base
  :parameters
  (?c ?next - cell)
  :precondition
  (and
    (scan-at ?c)
    (next-cell ?c ?next)
    (or (and
      (parity)
      (updated ?c)
    ) (and
      (not (parity))
      (not (updated ?c))
    ))
  )
  :effect
  (and
    (not (scan-at ?c))
    (scan-at ?next)
  )
) (:action
  fa-end-tick-base
  :parameters
  (?c - cell)
  :precondition
  (and
    (scan-at ?c)
    (last-cell ?c)
    (not (parity))
    (parity)
  )
  :effect
  (and
    (not (scan-at ?c))
    (not (scan-required))
  )
) (:action
  fa-end-tick-w1
  :parameters
  (?c - cell)
  :precondition
  (and
    (scan-at ?c)
    (last-cell ?c)
    (parity)
  )
  :effect
  (and
    (not (scan-at ?c))
    (not (scan-required))
    (not (parity))
  )
) (:action
  fa-end-tick-w2
  :parameters
  (?c - cell)
  :precondition
  (and
    (scan-at ?c)
    (last-cell ?c)
    (not (parity))
  )
  :effect
  (and
    (not (scan-at ?c))
    (not (scan-required))
    (parity)
  )
))
