; Generated test domain variant
; variant: domain_non-scanner_combined.pddl
; source: pddl/domain_orderfree_combined.pddl
; regenerate with: python pddl/make_target_variants.py
; Boulder Dash (stonesngems engine) - order-free physics with pending flags,
; one combined action per outcome (stones and gems share the physics actions).
;
; Reproduces stonesandgem/src/stonesngems_base.cpp (RNDGameState::apply_action)
; exactly for agent / empty / dirt / stone / gem / walls:
;   * the agent acts first; then every stone/gem that was there at the start
;     of the tick is updated once (an object that moved this tick, or a stone
;     the agent just pushed, is not: engine has_updated);
;   * a falling stone OR gem landing on the agent kills it;
;   * only resting stones/gems and brick walls (id 18) are rounded; steel
;     walls, exits and the level border are not, and the agent is not;
;   * pushed stones are falling iff the cell below their destination is empty;
;   * the target-gem marker travels with its gem.
;
; Only objects that can move are updated: a change to a cell marks the objects
; that read it dirty (vacated cell: the cell, above, left, right, up-left,
; up-right; a support that stopped falling: the object above; a moved object:
; itself), and start_tick makes the dirty stones/gems pending.  Every other
; object provably stays put: within a tick an update can only block objects
; later in the engine's scan, never enable them (see
; pddl/test_domains_target/README.md).
;
; Order-free: there is no scan pointer.  After an agent move, start_tick marks
; the dirty stones/gems pending; any pending object may be updated next,
; provided no pending object is left in its conflict window
;
;        k-2 k-1  k  k+1 k+2
;   r-1   x   x   x   x   x         (?ul2 ?ul ?u ?ur ?ur2)
;   r     x   x   c                 (?l2 ?l)
;
; i.e. the earlier cells (row-major) whose update can read a cell that c's
; update writes, or write a cell that c's update reads (c reads its cell, the
; cells below, left, down-left, right, down-right; it writes its cell and the
; one it moves to).  Every interleaving therefore yields the engine's
; row-major result: the end-of-tick state is unique, although several physics
; actions (for independent objects) are usually applicable at the same time.
;
; Per pending object exactly one of the physics_* actions is applicable.
; Physics does not depend on agent-alive, so a tick in which the agent dies
; still ends in a unique state (the agent can no longer move).
;
; The test-domain variants
; (pddl/test_domains_target/domain_{classic,FA}_non-scanner_combined.pddl)
; are generated with
;   python pddl/make_target_variants.py
;
; Problems: pddl/problem_gen_orderfree.py
; Differential test against the engine: tools/sim_check/fuzz.py
(define (domain mine-tick-gravity)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :universal-preconditions :conditional-effects :action-costs)

  (:types
    real-cell border-cell - cell
  )

  (:functions
    (total-cost)
  )

  (:predicates
    ;; ---- static ----
    (up ?from ?to - cell)              ; ?to is directly above ?from
    (down ?from ?to - cell)            ; ?to is directly below ?from
    (right-of ?from ?to - cell)        ; ?to is directly right of ?from
    (brick ?c - cell)                  ; any wall inside the level
    (rounded-wall ?c - cell)           ; brick wall (id 18): things roll off it
    (flat-wall ?c - cell)              ; steel wall / exit / level border

    ;; ---- cell contents (exactly one per cell inside the level) ----
    (agent-at ?c - cell)
    (empty ?c - cell)
    (dirt ?c - cell)
    (stone ?c - cell)
    (gem ?c - cell)
    (target-gem ?c - cell)
    (falling ?c - cell)                ; stone/gem state; resting otherwise

    ;; ---- tick bookkeeping ----
    (update-required)                  ; a tick is in progress
    (tick-start)                       ; agent has moved, objects not marked yet
    (pushed ?c - cell)                 ; stone pushed by the agent this tick
    (pending ?c - cell)                ; stone/gem not yet updated this tick
    (dirty ?c - cell)                  ; a cell it reads changed: update it next tick

    ;; ---- high level ----
    (agent-alive)
    (got-gem)
  )

  ;; ======================================================================
  ;; AGENT MOVEMENT (between ticks; starts a tick)
  ;; ======================================================================

  (:action move_noop
    :parameters ()
    :precondition (and (agent-alive) (not (update-required)))
    :effect (and
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  (:action move_empty
    :parameters (?from ?to - real-cell ?fu ?fl ?fr ?ful ?fur - cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (up ?from ?fu) (right-of ?fl ?from) (right-of ?from ?fr) (right-of ?ful ?fu) (right-of ?fu ?fur)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (empty ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (empty ?to)) (agent-at ?to)
      (dirty ?fu) (dirty ?fl) (dirty ?fr) (dirty ?ful) (dirty ?fur)
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  ;; Move into dirt (mines it).
  (:action move_into_dirt
    :parameters (?from ?to - real-cell ?fu ?fl ?fr ?ful ?fur - cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (up ?from ?fu) (right-of ?fl ?from) (right-of ?from ?fr) (right-of ?ful ?fu) (right-of ?fu ?fur)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (dirt ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (dirt ?to)) (agent-at ?to)
      (dirty ?fu) (dirty ?fl) (dirty ?fr) (dirty ?ful) (dirty ?fur)
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  ;; Collect a gem (resting or falling); the target gem sets got-gem.
  (:action move_into_gem
    :parameters (?from ?to - real-cell ?fu ?fl ?fr ?ful ?fur - cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (up ?from ?fu) (right-of ?fl ?from) (right-of ?from ?fr) (right-of ?ful ?fu) (right-of ?fu ?fur)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (gem ?to))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (gem ?to)) (not (falling ?to))
      (when (target-gem ?to) (and (not (target-gem ?to)) (got-gem))) (agent-at ?to)
      (dirty ?fu) (dirty ?fl) (dirty ?fr) (dirty ?ful) (dirty ?fur)
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )


  ;; Horizontal push of a resting stone into an empty cell.  The pushed stone
  ;; is not updated again this tick (start_tick does not mark it pending) and
  ;; is falling iff the cell below its destination is empty.
  (:action move_push_rock
    :parameters (?from ?to ?stone_dest - real-cell ?below ?fu ?fl ?fr ?ful ?fur - cell)
    :precondition (and
      (agent-alive) (not (update-required))
      (agent-at ?from)
      (up ?from ?fu) (right-of ?fl ?from) (right-of ?from ?fr) (right-of ?ful ?fu) (right-of ?fu ?fur)
      (or (and (right-of ?from ?to) (right-of ?to ?stone_dest))
          (and (right-of ?to ?from) (right-of ?stone_dest ?to)))
      (stone ?to) (not (falling ?to))
      (empty ?stone_dest)
      (down ?stone_dest ?below))
    :effect (and
      (not (agent-at ?from)) (empty ?from)
      (not (stone ?to)) (agent-at ?to)
      (not (empty ?stone_dest)) (stone ?stone_dest) (pushed ?stone_dest) (dirty ?stone_dest)
      (when (empty ?below) (falling ?stone_dest))
      (dirty ?fu) (dirty ?fl) (dirty ?fr) (dirty ?ful) (dirty ?fur)
      (update-required) (tick-start)
      (increase (total-cost) 1))
  )

  ;; ======================================================================
  ;; PHYSICS: one action per pending stone/gem.  Every action carries the
  ;; conflict window ?l ?l2 ?u ?ul ?ul2 ?ur ?ur2 (see the header), which must
  ;; hold no pending object.
  ;; ======================================================================

  ;; Cell below is empty: move down, falling.
  (:action physics_fall
    :parameters (?c - real-cell ?down ?r ?l ?l2 ?u ?ul ?ul2 ?ur ?ur2 - cell)
    :precondition (and
      (pending ?c)
      (right-of ?l ?c) (right-of ?l2 ?l)
      (up ?c ?u) (right-of ?ul ?u) (right-of ?ul2 ?ul) (right-of ?u ?ur) (right-of ?ur ?ur2)
      (not (pending ?l)) (not (pending ?l2))
      (not (pending ?u)) (not (pending ?ul)) (not (pending ?ul2)) (not (pending ?ur)) (not (pending ?ur2))
      (down ?c ?down) (empty ?down) (right-of ?c ?r))
    :effect (and
      (not (pending ?c)) (dirty ?u) (dirty ?ul) (dirty ?ur) (dirty ?l) (dirty ?r) (dirty ?down)
      (not (stone ?c)) (not (gem ?c)) (not (target-gem ?c)) (not (falling ?c)) (empty ?c)
      (when (stone ?c) (stone ?down))
      (when (gem ?c) (gem ?down))
      (when (target-gem ?c) (target-gem ?down))
      (not (empty ?down)) (falling ?down))
  )

  ;; Falling stone or gem lands on the agent: explosion, agent dies.
  (:action physics_fall_on_agent
    :parameters (?c - real-cell ?down ?l ?l2 ?u ?ul ?ul2 ?ur ?ur2 - cell)
    :precondition (and
      (pending ?c)
      (right-of ?l ?c) (right-of ?l2 ?l)
      (up ?c ?u) (right-of ?ul ?u) (right-of ?ul2 ?ul) (right-of ?u ?ur) (right-of ?ur ?ur2)
      (not (pending ?l)) (not (pending ?l2))
      (not (pending ?u)) (not (pending ?ul)) (not (pending ?ul2)) (not (pending ?ur)) (not (pending ?ur2))
      (falling ?c) (down ?c ?down) (agent-at ?down))
    :effect (and (not (pending ?c)) (not (agent-alive)))
  )

  ;; Rounded support (resting stone/gem or brick wall), left and down-left
  ;; empty: roll left (engine: CanRollLeft has priority).
  (:action physics_roll_left
    :parameters (?c - real-cell ?down ?down_left ?r ?l ?l2 ?u ?ul ?ul2 ?ur ?ur2 - cell)
    :precondition (and
      (pending ?c)
      (right-of ?l ?c) (right-of ?l2 ?l)
      (up ?c ?u) (right-of ?ul ?u) (right-of ?ul2 ?ul) (right-of ?u ?ur) (right-of ?ur ?ur2)
      (not (pending ?l)) (not (pending ?l2))
      (not (pending ?u)) (not (pending ?ul)) (not (pending ?ul2)) (not (pending ?ur)) (not (pending ?ur2))
      (down ?c ?down) (down ?l ?down_left)
      (or (rounded-wall ?down) (and (or (stone ?down) (gem ?down)) (not (falling ?down))))
      (empty ?l) (empty ?down_left) (right-of ?c ?r))
    :effect (and
      (not (pending ?c)) (dirty ?u) (dirty ?ul) (dirty ?ur) (dirty ?l) (dirty ?r)
      (not (stone ?c)) (not (gem ?c)) (not (target-gem ?c)) (not (falling ?c)) (empty ?c)
      (when (stone ?c) (stone ?l))
      (when (gem ?c) (gem ?l))
      (when (target-gem ?c) (target-gem ?l))
      (not (empty ?l)) (falling ?l))
  )

  ;; Rounded support, roll left blocked, right and down-right empty: roll right.
  (:action physics_roll_right
    :parameters (?c - real-cell ?down ?down_left ?right ?down_right ?l ?l2 ?u ?ul ?ul2 ?ur ?ur2 - cell)
    :precondition (and
      (pending ?c)
      (right-of ?l ?c) (right-of ?l2 ?l)
      (up ?c ?u) (right-of ?ul ?u) (right-of ?ul2 ?ul) (right-of ?u ?ur) (right-of ?ur ?ur2)
      (not (pending ?l)) (not (pending ?l2))
      (not (pending ?u)) (not (pending ?ul)) (not (pending ?ul2)) (not (pending ?ur)) (not (pending ?ur2))
      (down ?c ?down) (down ?l ?down_left) (right-of ?c ?right) (down ?right ?down_right)
      (or (rounded-wall ?down) (and (or (stone ?down) (gem ?down)) (not (falling ?down))))
      (or (not (empty ?l)) (not (empty ?down_left)))
      (empty ?right) (empty ?down_right))
    :effect (and
      (not (pending ?c)) (dirty ?u) (dirty ?ul) (dirty ?ur) (dirty ?l) (dirty ?right)
      (not (stone ?c)) (not (gem ?c)) (not (target-gem ?c)) (not (falling ?c)) (empty ?c)
      (when (stone ?c) (stone ?right))
      (when (gem ?c) (gem ?right))
      (when (target-gem ?c) (target-gem ?right))
      (not (empty ?right)) (falling ?right))
  )

  ;; Support is not rounded: dirt, a flat wall / the border, a falling
  ;; stone/gem, or the agent under a resting object (a falling one crushes
  ;; it).  The object stays; a falling one comes to rest.
  (:action physics_settle
    :parameters (?c - real-cell ?down ?l ?l2 ?u ?ul ?ul2 ?ur ?ur2 - cell)
    :precondition (and
      (pending ?c)
      (right-of ?l ?c) (right-of ?l2 ?l)
      (up ?c ?u) (right-of ?ul ?u) (right-of ?ul2 ?ul) (right-of ?u ?ur) (right-of ?ur ?ur2)
      (not (pending ?l)) (not (pending ?l2))
      (not (pending ?u)) (not (pending ?ul)) (not (pending ?ul2)) (not (pending ?ur)) (not (pending ?ur2))
      (down ?c ?down)
      (or (dirt ?down) (flat-wall ?down)
          (and (or (stone ?down) (gem ?down)) (falling ?down))
          (and (agent-at ?down) (not (falling ?c)))))
    :effect (and (not (pending ?c)) (not (falling ?c)) (when (falling ?c) (dirty ?u)))
  )

  ;; Rounded support, but both rolls are blocked.
  (:action physics_settle_blocked
    :parameters (?c - real-cell ?down ?down_left ?right ?down_right ?l ?l2 ?u ?ul ?ul2 ?ur ?ur2 - cell)
    :precondition (and
      (pending ?c)
      (right-of ?l ?c) (right-of ?l2 ?l)
      (up ?c ?u) (right-of ?ul ?u) (right-of ?ul2 ?ul) (right-of ?u ?ur) (right-of ?ur ?ur2)
      (not (pending ?l)) (not (pending ?l2))
      (not (pending ?u)) (not (pending ?ul)) (not (pending ?ul2)) (not (pending ?ur)) (not (pending ?ur2))
      (down ?c ?down) (down ?l ?down_left) (right-of ?c ?right) (down ?right ?down_right)
      (or (rounded-wall ?down) (and (or (stone ?down) (gem ?down)) (not (falling ?down))))
      (or (not (empty ?l)) (not (empty ?down_left)))
      (or (not (empty ?right)) (not (empty ?down_right))))
    :effect (and (not (pending ?c)) (not (falling ?c)) (when (falling ?c) (dirty ?u)))
  )

  ;; Mark the dirty stones/gems pending (all others provably stay put this
  ;; tick), except a stone the agent just pushed: it stays dirty for the next
  ;; tick.
  (:action start_tick
    :parameters ()
    :precondition (tick-start)
    :effect (and
      (not (tick-start))
      (forall (?cc - cell)
        (and (when (and (dirty ?cc) (or (stone ?cc) (gem ?cc)) (not (pushed ?cc))) (pending ?cc))
             (when (not (pushed ?cc)) (not (dirty ?cc)))
             (not (pushed ?cc)))))
  )

  ;; Every stone/gem has been updated: the tick is over.
  (:action end_tick
    :parameters ()
    :precondition (and
      (update-required) (not (tick-start))
      (forall (?c - real-cell) (not (pending ?c))))
    :effect (not (update-required))
  )
)
