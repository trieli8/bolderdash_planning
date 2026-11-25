; Generated test domain variant
; variant: domain_scanner_combined.pddl
; source: pddl/domain_rowscan.pddl
; regenerate with: python pddl/make_target_variants.py
; Boulder Dash (stonesngems engine) - row-gated scanner model.
;
; Mirrors stonesandgem/src/stonesngems_base.cpp (RNDGameState::apply_action)
; exactly for agent / empty / dirt / stone / gem / walls:
;   * each tick the agent acts first, then cells are updated in row-major
;     order; an object that moved into a cell later in the scan (fall, roll
;     right, push) is marked updated and skipped for the rest of the tick
;     (engine: has_updated);
;   * a falling stone OR gem landing on the agent kills it;
;   * only resting stones/gems and brick walls (id 18) are rounded; steel
;     walls, exits and the level border are not;
;   * pushed stones are skipped in the push tick and are falling iff the cell
;     below their destination is empty;
;   * the target-gem marker travels with its gem.
;
; Speed: walls are not in the scan chain, and every row has a gate that skips
; the whole row in one step unless something in the row or the row below
; changed since the row was last scanned (in which case every object in it is
; provably stable); inside a scanned row, blocks of columns (8 by default, see
; pddl/problem_gen_rowscan.py) have their own gates, so only the blocks around
; a change are visited.  updated flags are cleared by the scan itself, so a tick
; ends without any forall reset.  Preconditions are positive except on the
; binary flags (updated, row-dirty, target-gem).
;
; Agent actions are the move_* actions; every other action is physics and is
; deterministic: in any state exactly one of them is applicable while a tick
; is in progress, and no move_* action is.  The forced-action variant
; (pddl/test_domains_target/domain_FA_scanner_combined.pddl) only prefixes the
; physics actions with __FORCED__; regenerate both variants with
;   python pddl/make_target_variants.py
;
; Problems: pddl/problem_gen_rowscan.py
; Differential test against the engine: tools/sim_check/fuzz.py
(define (domain mine-tick-gravity)
  (:requirements :strips :typing :negative-preconditions :disjunctive-preconditions :conditional-effects :action-costs)

  (:types
    pos - object
    cell row block - pos
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
    (rounded-wall ?c - cell)           ; brick wall: things roll off it
    (flat-wall ?c - cell)              ; steel wall / exit / level border
    (brick ?c - cell)                  ; any interior wall (kept for tools)
    (cell-row ?c - cell ?r - row)
    (row-above ?r ?above - row)
    (first-row ?r - row)               ; first gate of the scan
    (next-row ?r ?next - row)          ; gate -> next gate (or done)
    (row-first-block ?r - row ?b - block) ; row gate -> its first block gate
    (row-start ?r - row ?c - real-cell) ; row gate -> first open cell (rows with one block)
    (next-block ?b - block ?next - pos)  ; block gate -> next block gate / next row gate / done
    (block-start ?b - block ?c - real-cell) ; block gate -> first open cell of the block
    (next-pos ?c - real-cell ?next - pos) ; open cell -> next cell / next gate / done
    (block-of ?c - cell ?b - block)
    ;; blocks holding columns k-1 and k+1 of c's row (?b1 ?b2) and of the row
    ;; above (?a1 ?a2): the readers of cell c
    (marks ?c - cell ?b1 ?b2 ?a1 ?a2 - block)
    (scan-done ?r - row)               ; the idle sentinel

    ;; ---- cell contents (exactly one per open cell) ----
    (agent-at ?c - cell)
    (empty ?c - cell)
    (dirt ?c - cell)
    (obj ?c - cell)                    ; a stone or a gem
    ;; redundant complement of empty (also true on walls and the border)
    (full ?c - cell)
    ;; object details
    (stone ?c - cell)
    (gem ?c - cell)
    (target-gem ?c - cell)
    (falling ?c - cell)
    (resting ?c - cell)

    ;; ---- scan bookkeeping ----
    (scan-at ?p - pos)
    (updated ?c - cell)
    (row-dirty ?r - row)
    (block-dirty ?b - block)

    ;; ---- high level ----
    (agent-alive)
    (got-gem)
  )

  ;; ======================================================================
  ;; AGENT (only between ticks: the scan pointer rests on the done sentinel)
  ;; ======================================================================

  (:action move_noop
    :parameters (?d ?r0 - row)
    :precondition (and (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0))
    :effect (and
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )

  (:action move_empty
    :parameters (?from ?to - real-cell ?d ?r0 ?rf ?rfa - row ?m1 ?m2 ?m3 ?m4 - block)
    :precondition (and
      (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (empty ?to)
      (cell-row ?from ?rf) (row-above ?rf ?rfa) (marks ?from ?m1 ?m2 ?m3 ?m4))
    :effect (and
      (not (agent-at ?from)) (empty ?from) (not (full ?from))
      (not (empty ?to)) (full ?to) (agent-at ?to)
      (row-dirty ?rf) (row-dirty ?rfa) (block-dirty ?m1) (block-dirty ?m2) (block-dirty ?m3) (block-dirty ?m4)
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )

  (:action move_into_dirt
    :parameters (?from ?to - real-cell ?d ?r0 ?rf ?rfa - row ?m1 ?m2 ?m3 ?m4 - block)
    :precondition (and
      (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (dirt ?to)
      (cell-row ?from ?rf) (row-above ?rf ?rfa) (marks ?from ?m1 ?m2 ?m3 ?m4))
    :effect (and
      (not (agent-at ?from)) (empty ?from) (not (full ?from))
      (not (dirt ?to)) (agent-at ?to)
      (row-dirty ?rf) (row-dirty ?rfa) (block-dirty ?m1) (block-dirty ?m2) (block-dirty ?m3) (block-dirty ?m4)
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )

  ;; Collect a gem (resting or falling); the target gem sets got-gem.
  (:action move_into_gem
    :parameters (?from ?to - real-cell ?d ?r0 ?rf ?rfa - row ?m1 ?m2 ?m3 ?m4 - block)
    :precondition (and
      (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0)
      (agent-at ?from)
      (or (up ?from ?to) (down ?from ?to) (right-of ?from ?to) (right-of ?to ?from))
      (obj ?to) (gem ?to)
      (cell-row ?from ?rf) (row-above ?rf ?rfa) (marks ?from ?m1 ?m2 ?m3 ?m4))
    :effect (and
      (not (agent-at ?from)) (empty ?from) (not (full ?from))
      (not (obj ?to)) (not (gem ?to)) (not (falling ?to))
      (when (target-gem ?to) (and (not (target-gem ?to)) (got-gem))) (not (resting ?to)) (agent-at ?to)
      (row-dirty ?rf) (row-dirty ?rfa) (block-dirty ?m1) (block-dirty ?m2) (block-dirty ?m3) (block-dirty ?m4)
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )


  ;; Horizontal push of a resting stone into an empty cell.  The engine marks
  ;; the pushed stone updated (it does not move again this tick) and makes it
  ;; falling iff the cell below its destination is empty.
  (:action move_push_rock
    :parameters (?from ?to ?dest - real-cell ?below - cell ?d ?r0 ?rf ?rfa - row ?m1 ?m2 ?m3 ?m4 ?bd - block)
    :precondition (and
      (agent-alive) (scan-at ?d) (scan-done ?d) (first-row ?r0)
      (agent-at ?from)
      (or (and (right-of ?from ?to) (right-of ?to ?dest))
          (and (right-of ?to ?from) (right-of ?dest ?to)))
      (obj ?to) (stone ?to) (resting ?to)
      (empty ?dest)
      (down ?dest ?below)
      (cell-row ?from ?rf) (row-above ?rf ?rfa) (marks ?from ?m1 ?m2 ?m3 ?m4)
      (block-of ?dest ?bd))
    :effect (and
      (not (agent-at ?from)) (empty ?from) (not (full ?from))
      (not (obj ?to)) (not (stone ?to)) (not (resting ?to)) (agent-at ?to)
      (not (empty ?dest)) (full ?dest) (obj ?dest) (stone ?dest) (updated ?dest)
      (when (empty ?below) (falling ?dest))
      (when (full ?below) (resting ?dest))
      (row-dirty ?rf) (row-dirty ?rfa) (block-dirty ?m1) (block-dirty ?m2) (block-dirty ?m3) (block-dirty ?m4) (block-dirty ?bd)
      (not (scan-at ?d)) (scan-at ?r0)
      (increase (total-cost) 1))
  )

  ;; ======================================================================
  ;; ROW GATES
  ;; ======================================================================

  (:action row_enter
    :parameters (?r - row ?b - block)
    :precondition (and (scan-at ?r) (row-dirty ?r) (row-first-block ?r ?b))
    :effect (and (not (scan-at ?r)) (not (row-dirty ?r)) (scan-at ?b))
  )

  ;; A row whose open cells all lie in one block has no block gate.
  (:action row_enter_cell
    :parameters (?r - row ?c - real-cell)
    :precondition (and (scan-at ?r) (row-dirty ?r) (row-start ?r ?c))
    :effect (and (not (scan-at ?r)) (not (row-dirty ?r)) (scan-at ?c))
  )

  (:action row_skip
    :parameters (?r ?next - row)
    :precondition (and (scan-at ?r) (not (row-dirty ?r)) (next-row ?r ?next))
    :effect (and (not (scan-at ?r)) (scan-at ?next))
  )

  ;; Inside a row that is scanned, a block of columns is entered only if a
  ;; cell its objects read changed (block-dirty); every block mark also marks
  ;; the row, so a clean row has only clean blocks.
  (:action block_enter
    :parameters (?b - block ?c - real-cell)
    :precondition (and (scan-at ?b) (block-dirty ?b) (block-start ?b ?c))
    :effect (and (not (scan-at ?b)) (not (block-dirty ?b)) (scan-at ?c))
  )

  (:action block_skip
    :parameters (?b - block ?next - pos)
    :precondition (and (scan-at ?b) (not (block-dirty ?b)) (next-block ?b ?next))
    :effect (and (not (scan-at ?b)) (scan-at ?next))
  )

  ;; ======================================================================
  ;; CELLS WITHOUT A PENDING OBJECT
  ;; ======================================================================

  ;; Object that moved here earlier this tick: skip it, and make sure its row
  ;; is scanned again next tick.
  (:action scan_updated
    :parameters (?c - real-cell ?next - pos ?r - row ?bc - block)
    :precondition (and (scan-at ?c) (next-pos ?c ?next) (updated ?c) (cell-row ?c ?r) (block-of ?c ?bc))
    :effect (and (not (updated ?c)) (row-dirty ?r) (block-dirty ?bc) (not (scan-at ?c)) (scan-at ?next))
  )

  (:action scan_empty
    :parameters (?c - real-cell ?next - pos)
    :precondition (and (scan-at ?c) (next-pos ?c ?next) (empty ?c))
    :effect (and (not (scan-at ?c)) (scan-at ?next))
  )

  (:action scan_dirt
    :parameters (?c - real-cell ?next - pos)
    :precondition (and (scan-at ?c) (next-pos ?c ?next) (dirt ?c))
    :effect (and (not (scan-at ?c)) (scan-at ?next))
  )

  (:action scan_agent
    :parameters (?c - real-cell ?next - pos)
    :precondition (and (scan-at ?c) (next-pos ?c ?next) (agent-at ?c))
    :effect (and (not (scan-at ?c)) (scan-at ?next))
  )

  ;; ======================================================================
  ;; STONES AND GEMS (identical physics; kind and target marker travel along)
  ;; ======================================================================

  ;; Cell below is empty: move down, falling (engine: UpdateStone/UpdateStoneFalling).
  (:action physics_fall
    :parameters (?c - real-cell ?next - pos ?b - real-cell ?rc ?ra ?rb - row ?m1 ?m2 ?m3 ?m4 ?mb - block)
    :precondition (and
      (scan-at ?c) (next-pos ?c ?next)
      (obj ?c) (not (updated ?c))
      (down ?c ?b) (empty ?b)
      (cell-row ?c ?rc) (row-above ?rc ?ra) (cell-row ?b ?rb)
      (marks ?c ?m1 ?m2 ?m3 ?m4) (block-of ?b ?mb))
    :effect (and
      (not (obj ?c)) (not (falling ?c)) (not (resting ?c)) (empty ?c) (not (full ?c))
      (when (stone ?c) (and (not (stone ?c)) (stone ?b)))
      (when (gem ?c) (and (not (gem ?c)) (gem ?b)))
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?b)))
      (not (empty ?b)) (full ?b) (obj ?b) (falling ?b) (updated ?b)
      (row-dirty ?rc) (row-dirty ?ra) (row-dirty ?rb)
      (block-dirty ?m1) (block-dirty ?m2) (block-dirty ?m3) (block-dirty ?m4) (block-dirty ?mb)
      (not (scan-at ?c)) (scan-at ?next))
  )

  ;; Falling stone or gem lands on the agent: explosion, agent dies.
  (:action physics_crush_agent
    :parameters (?c - real-cell ?b - real-cell)
    :precondition (and
      (scan-at ?c)
      (obj ?c) (falling ?c) (not (updated ?c))
      (down ?c ?b) (agent-at ?b))
    :effect (and (not (agent-alive)) (not (scan-at ?c)))
  )

  ;; Roll left off a rounded object (engine: CanRollLeft has priority).
  (:action physics_roll_left
    :parameters (?c - real-cell ?next - pos ?b - cell ?l ?dl - real-cell ?rc ?ra - row ?m1 ?m2 ?m3 ?m4 - block)
    :precondition (and
      (scan-at ?c) (next-pos ?c ?next)
      (obj ?c) (not (updated ?c))
      (down ?c ?b) (or (resting ?b) (rounded-wall ?b))
      (right-of ?l ?c) (down ?l ?dl)
      (empty ?l) (empty ?dl)
      (cell-row ?c ?rc) (row-above ?rc ?ra) (marks ?c ?m1 ?m2 ?m3 ?m4))
    :effect (and
      (not (obj ?c)) (not (falling ?c)) (not (resting ?c)) (empty ?c) (not (full ?c))
      (when (stone ?c) (and (not (stone ?c)) (stone ?l)))
      (when (gem ?c) (and (not (gem ?c)) (gem ?l)))
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?l)))
      (not (empty ?l)) (full ?l) (obj ?l) (falling ?l)
      (row-dirty ?rc) (row-dirty ?ra)
      (block-dirty ?m1) (block-dirty ?m2) (block-dirty ?m3) (block-dirty ?m4)
      (not (scan-at ?c)) (scan-at ?next))
  )

  ;; Roll right when rolling left is impossible.
  (:action physics_roll_right
    :parameters (?c - real-cell ?next - pos ?b ?l ?dl - cell ?r ?dr - real-cell ?rc ?ra - row ?m1 ?m2 ?m3 ?m4 - block)
    :precondition (and
      (scan-at ?c) (next-pos ?c ?next)
      (obj ?c) (not (updated ?c))
      (down ?c ?b) (or (resting ?b) (rounded-wall ?b))
      (right-of ?l ?c) (down ?l ?dl)
      (or (full ?l) (and (empty ?l) (full ?dl)))
      (right-of ?c ?r) (down ?r ?dr)
      (empty ?r) (empty ?dr)
      (cell-row ?c ?rc) (row-above ?rc ?ra) (marks ?c ?m1 ?m2 ?m3 ?m4))
    :effect (and
      (not (obj ?c)) (not (falling ?c)) (not (resting ?c)) (empty ?c) (not (full ?c))
      (when (stone ?c) (and (not (stone ?c)) (stone ?r)))
      (when (gem ?c) (and (not (gem ?c)) (gem ?r)))
      (when (target-gem ?c) (and (not (target-gem ?c)) (target-gem ?r)))
      (not (empty ?r)) (full ?r) (obj ?r) (falling ?r) (updated ?r)
      (row-dirty ?rc) (row-dirty ?ra)
      (block-dirty ?m1) (block-dirty ?m2) (block-dirty ?m3) (block-dirty ?m4)
      (not (scan-at ?c)) (scan-at ?next))
  )

  ;; Cannot move and the support is not rounded: dirt, the agent (only for a
  ;; resting object; a falling one crushes it), a falling object, or a flat
  ;; wall / the border.  A falling object comes to rest; the row above may now
  ;; roll off it, so it is marked dirty.
  (:action physics_settle
    :parameters (?c - real-cell ?next - pos ?b - cell ?rc ?ra - row ?u - cell ?mu - block)
    :precondition (and
      (scan-at ?c) (next-pos ?c ?next)
      (obj ?c) (not (updated ?c))
      (down ?c ?b)
      (or (dirt ?b) (and (agent-at ?b) (resting ?c)) (falling ?b) (flat-wall ?b))
      (cell-row ?c ?rc) (row-above ?rc ?ra) (up ?c ?u) (block-of ?u ?mu))
    :effect (and
      (when (falling ?c) (and (not (falling ?c)) (resting ?c) (row-dirty ?ra) (block-dirty ?mu)))
      (not (scan-at ?c)) (scan-at ?next))
  )

  ;; Rounded support, but both rolls are blocked.
  (:action physics_settle_blocked
    :parameters (?c - real-cell ?next - pos ?b ?l ?dl ?r ?dr - cell ?rc ?ra - row ?u - cell ?mu - block)
    :precondition (and
      (scan-at ?c) (next-pos ?c ?next)
      (obj ?c) (not (updated ?c))
      (down ?c ?b) (or (resting ?b) (rounded-wall ?b))
      (right-of ?l ?c) (down ?l ?dl)
      (or (full ?l) (and (empty ?l) (full ?dl)))
      (right-of ?c ?r) (down ?r ?dr)
      (or (full ?r) (and (empty ?r) (full ?dr)))
      (cell-row ?c ?rc) (row-above ?rc ?ra) (up ?c ?u) (block-of ?u ?mu))
    :effect (and
      (when (falling ?c) (and (not (falling ?c)) (resting ?c) (row-dirty ?ra) (block-dirty ?mu)))
      (not (scan-at ?c)) (scan-at ?next))
  )
)
