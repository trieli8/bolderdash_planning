"""
Convert a stonesngems_cpp level string into a PDDL problem
for the mine-tick-gravity domain.

Level string format (from stonesngems_cpp README):

    rows|cols|max_time|required_gems|cell_0|cell_1|...|cell_{rows*cols-1}

where each cell_i is an integer HiddenCellType ID.
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

# ----------------------------------------------------------------------
# Mapping from HiddenCellType IDs to our simplified PDDL 

# ----------------------------------------------------------------------

# These values are taken from stonesngems_cpp/definitions.h
# (enum class HiddenCellType). We only handle a subset here.
STONE_IDS   = {3, 4, 48}        # Stone, StoneFalling, StoneInDirt
STONE_FALLING_IDS = {4}         # StoneFalling
GEM_IDS     = {5, 6}            # Diamond, DiamondFalling
GEM_FALLING_IDS = {6}           # DiamondFalling
EMPTY_IDS   = {1}               # Empty
DIRT_IDS    = {2}               # Dirt
AGENT_IDS   = {0, 9}            # Agent, AgentInExit
BRICK_IDS   = {
    7, 8,                      # ExitClosed, ExitOpen
    10, 11, 12, 13,            # Fireflies (unmodeled hazards -> solid blockers)
    14, 15, 16, 17,            # Butterflies (unmodeled hazards -> solid blockers)
    18, 19,                    # WallBrick, WallSteel
    20, 21, 22,                # Magic walls (treat as solid)
    23,                        # Blob (unmodeled growth -> solid blocker)
}


@dataclass(frozen=True)
class LevelMetadata:
    start_gem_ordinal: int | None = None
    target_gem_ordinal: int | None = None


@dataclass(frozen=True)
class PreparedLevel:
    rows: int
    cols: int
    max_time: int
    required_gems: int
    cell_ids: tuple[int, ...]
    agent_pos: tuple[int, int]
    target_gem_pos: tuple[int, int] | None
    initial_got_gem: bool

def classify_cell_id(cell_id: int):
    """
    Map a HiddenCellType ID to a simple content kind understood by the PDDL domain.

    Returns one of: "agent", "empty", "dirt", "stone", "gem", "brick".

    Raises ValueError if the ID is not recognised. Extend the sets above
    if you want to support more elements.
    """
    if cell_id in AGENT_IDS:
        return "agent"
    if cell_id in EMPTY_IDS:
        return "empty"
    if cell_id in DIRT_IDS:
        return "dirt"
    if cell_id in STONE_IDS:
        return "stone"
    if cell_id in GEM_IDS:
        return "gem"
    if cell_id in BRICK_IDS:
        return "brick"
    raise ValueError(
        f"Unsupported cell ID {cell_id}; extend the mapping in classify_cell_id()."
    )

# ----------------------------------------------------------------------
# Level parsing and PDDL generation
# ----------------------------------------------------------------------

def parse_level_string(level_str: str):
    """
    Parse a |-delimited stonesngems level string.

    Returns (rows, cols, max_time, required_gems, cell_ids).
    """
    parts = [p for p in level_str.strip().split("|") if p != ""]
    if len(parts) < 4:
        raise ValueError(
            "Level string must have at least 4 fields: "
            "rows|cols|max_time|required_gems|..."
        )

    rows = int(parts[0])
    cols = int(parts[1])
    max_time = int(parts[2])
    required_gems = int(parts[3])

    cell_strs = parts[4:]
    expected = rows * cols
    if len(cell_strs) != expected:
        raise ValueError(f"Expected {expected} cell IDs, got {len(cell_strs)}")

    cell_ids = [int(s) for s in cell_strs]
    return rows, cols, max_time, required_gems, cell_ids


def parse_level_text(level_text: str) -> tuple[str, LevelMetadata]:
    metadata: dict[str, int] = {}
    level_lines: list[str] = []

    for raw_line in level_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith((";", "#")):
            body = stripped[1:].strip()
            if ":" in body:
                key, value = body.split(":", 1)
                norm_key = key.strip().lower().replace("_", "-")
                if norm_key in {"start-gem-ordinal", "target-gem-ordinal"}:
                    metadata[norm_key] = int(value.strip())
            continue
        level_lines.append(raw_line.strip())

    if not level_lines:
        raise ValueError("Level input did not contain a level string.")

    return "\n".join(level_lines), LevelMetadata(
        start_gem_ordinal=metadata.get("start-gem-ordinal"),
        target_gem_ordinal=metadata.get("target-gem-ordinal"),
    )


def _pick_gem_position(gem_positions, ordinal: int, field_name: str):
    if ordinal < 1 or ordinal > len(gem_positions):
        raise ValueError(
            f"{field_name}={ordinal} is out of range for {len(gem_positions)} gems."
        )
    return gem_positions[ordinal - 1]


def prepare_level(level_text: str, level_metadata: LevelMetadata | None = None) -> PreparedLevel:
    parsed_level_text, inline_metadata = parse_level_text(level_text)
    if level_metadata is None:
        level_metadata = inline_metadata
    else:
        level_metadata = LevelMetadata(
            start_gem_ordinal=(
                level_metadata.start_gem_ordinal
                if level_metadata.start_gem_ordinal is not None
                else inline_metadata.start_gem_ordinal
            ),
            target_gem_ordinal=(
                level_metadata.target_gem_ordinal
                if level_metadata.target_gem_ordinal is not None
                else inline_metadata.target_gem_ordinal
            ),
        )

    rows, cols, max_time, required_gems, parsed_cell_ids = parse_level_string(parsed_level_text)
    cell_ids = list(parsed_cell_ids)

    agent_pos = None
    gem_positions = []
    for idx, cell_id in enumerate(cell_ids):
        r = idx // cols
        c = idx % cols
        kind = classify_cell_id(cell_id)
        if kind == "agent":
            if agent_pos is not None:
                raise ValueError("Multiple agent cells found; this script expects exactly one.")
            agent_pos = (r, c)
        elif kind == "gem":
            gem_positions.append((r, c))

    if agent_pos is None:
        raise ValueError("No agent found in level (no cell with ID in AGENT_IDS).")

    initial_got_gem = False
    if level_metadata.start_gem_ordinal is not None:
        start_pos = _pick_gem_position(
            gem_positions,
            level_metadata.start_gem_ordinal,
            "start-gem-ordinal",
        )
        old_agent_idx = agent_pos[0] * cols + agent_pos[1]
        start_idx = start_pos[0] * cols + start_pos[1]
        cell_ids[old_agent_idx] = next(iter(EMPTY_IDS))
        cell_ids[start_idx] = next(iter(AGENT_IDS))
        agent_pos = start_pos

    if level_metadata.target_gem_ordinal is not None:
        target_gem_pos = _pick_gem_position(
            gem_positions,
            level_metadata.target_gem_ordinal,
            "target-gem-ordinal",
        )
        if target_gem_pos == agent_pos:
            initial_got_gem = True
    else:
        current_gem_positions = []
        for idx, cell_id in enumerate(cell_ids):
            if classify_cell_id(cell_id) == "gem":
                current_gem_positions.append((idx // cols, idx % cols))
        target_gem_pos = select_target_gem_position(agent_pos, current_gem_positions)

    return PreparedLevel(
        rows=rows,
        cols=cols,
        max_time=max_time,
        required_gems=required_gems,
        cell_ids=tuple(cell_ids),
        agent_pos=agent_pos,
        target_gem_pos=target_gem_pos,
        initial_got_gem=initial_got_gem,
    )

def cell_name(r: int, c: int) -> str:
    """Name for a cell object in PDDL."""
    return f"c_{r}_{c}"

def interior_cell_name(r: int, c: int) -> str:
    """
    Name for an interior cell once we pad the grid with a 1-cell border.
    Interior coords are 0-based in the level string; we shift by +1 to
    leave room for the border.
    """
    return cell_name(r + 1, c + 1)


def select_target_gem_position(agent_pos, gem_positions):
    """
    Pick one distinguished gem to represent the goal gem.

    We use the gem farthest from the start so generated benchmark levels keep
    treating the "main" gem as the goal even when extra gems are present.
    """
    if not gem_positions:
        return None
    return max(
        gem_positions,
        key=lambda pos: (
            abs(pos[0] - agent_pos[0]) + abs(pos[1] - agent_pos[1]),
            -pos[0],
            -pos[1],
        ),
    )

def generate_pddl_problem(
    level_str: str,
    problem_name: str = "level-1",
    domain_name: str = "mine-tick-gravity",
    agent_name: str = "player",
) -> str:
    """
    Generate a full PDDL problem text from a level string.
    """
    prepared = prepare_level(level_str)
    rows = prepared.rows
    cols = prepared.cols
    max_time = prepared.max_time
    required_gems = prepared.required_gems
    cell_ids = list(prepared.cell_ids)
    target_gem_pos = prepared.target_gem_pos

    # Pad with a 1-cell brick border so physics never steps outside.
    padded_rows = rows + 2
    padded_cols = cols + 2

    # Build grid of object names (includes border)
    cells = [[cell_name(r, c) for c in range(padded_cols)] for r in range(padded_rows)]
    interior_cells = [interior_cell_name(r, c) for r in range(rows) for c in range(cols)]
    border_cells = [
        cell_name(r, c)
        for r in range(padded_rows)
        for c in range(padded_cols)
        if r == 0 or r == padded_rows - 1 or c == 0 or c == padded_cols - 1
    ]
    left_void = "left_void"
    border_cells.append(left_void)

    # Find agent and classify contents
    contents = {}  # (r, c) -> kind
    falling_cells = set()

    for idx, cell_id in enumerate(cell_ids):
        r = idx // cols
        c = idx % cols
        kind = classify_cell_id(cell_id)
        contents[(r, c)] = kind
        if cell_id in STONE_FALLING_IDS or cell_id in GEM_FALLING_IDS:
            falling_cells.add((r, c))
    agent_pos = prepared.agent_pos

    # Shift agent into padded coordinates
    padded_agent_pos = (agent_pos[0] + 1, agent_pos[1] + 1)

    # ------------------------------------------------------------------
    # :objects
    # ------------------------------------------------------------------
    obj_lines = []
    obj_lines.append(f"    {' '.join(interior_cells)} - real-cell")
    obj_lines.append(f"    {' '.join(border_cells)} - border-cell")

    # ------------------------------------------------------------------
    # :init
    # ------------------------------------------------------------------
    init_lines = []

    # High-level flags
    init_lines.append("    (agent-alive)")
    if prepared.initial_got_gem:
        init_lines.append("    (got-gem)")


    # Agent position
    ar, ac = padded_agent_pos
    init_lines.append(f"    (agent-at {cell_name(ar, ac)})")


    # Cell contents
    for r in range(padded_rows):
        for c in range(padded_cols):
            cname = cell_name(r, c)
            is_border = (
                r == 0 or r == padded_rows - 1 or c == 0 or c == padded_cols - 1
            )
            if is_border:
                init_lines.append(f"    (border-cell {cname})")
                init_lines.append(f"    (not (empty {cname}))")

                continue

            init_lines.append(f"    (real-cell {cname})")
            inner_kind = contents[(r - 1, c - 1)]
            if inner_kind == "agent":
                # Treat underlying cell as empty for physics
                init_lines.append(f"    (not (empty {cname}))")
            elif inner_kind == "empty":
                init_lines.append(f"    (empty {cname})")
            elif inner_kind == "dirt":
                init_lines.append(f"    (dirt {cname})")
            elif inner_kind == "stone":
                init_lines.append(f"    (stone {cname})")
            elif inner_kind == "gem":
                init_lines.append(f"    (gem {cname})")
                if (r - 1, c - 1) == target_gem_pos and not prepared.initial_got_gem:
                    init_lines.append(f"    (target-gem {cname})")
            elif inner_kind == "brick":
                init_lines.append(f"    (brick {cname})")
            if (r - 1, c - 1) in falling_cells:
                init_lines.append(f"    (falling {cname})")

    init_lines.append(f"    (border-cell {left_void})")
    init_lines.append(f"    (not (empty {left_void}))")


    # Adjacency predicates: up, down, right-of (left via reverse right-of).
    for r in range(padded_rows):
        for c in range(padded_cols):
            cname = cell_name(r, c)
            # up: from this cell to the one above (this -> above)
            if r > 0:
                above = cell_name(r - 1, c)
                init_lines.append(f"    (up {cname} {above})")
            # down: from this to below (this -> below)
            if r < padded_rows - 1:
                below = cell_name(r + 1, c)
                init_lines.append(f"    (down {cname} {below})")
            # right-of: left -> right
            if c == 0:
                init_lines.append(f"    (right-of {left_void} {cname})")
            else:
                left = cell_name(r, c - 1)
                init_lines.append(f"    (right-of {left} {cname})")

    # Scan order: top-left to bottom-right over interior cells only
    order = [interior_cell_name(r, c) for r in range(rows) for c in range(cols)]
    first = order[0]
    last = order[-1]
    init_lines.append(f"    (first-cell {first})")
    init_lines.append(f"    (last-cell {last})")

    for i in range(len(order) - 1):
        init_lines.append(f"    (next-cell {order[i]} {order[i+1]})")

    # Note: no scan-at in the initial state; a move-* action will start a tick.

    # ------------------------------------------------------------------
    # :goal
    # ------------------------------------------------------------------
    # Simple default: eventually get a gem
    goal_lines = ["    (got-gem)", 
                  "    (not (update-required))", 
                  "    (not (crushed))", 
                  "    (agent-alive)"]

    # Assemble full PDDL
    pddl = f"""\
(define (problem {problem_name})
  (:domain {domain_name})
  (:requirements :typing :negative-preconditions :action-costs)
  (:objects
{chr(10).join(obj_lines)}
  )
  (:init
  (= (total-cost) 0)
{chr(10).join(init_lines)}
  )
  (:goal
  (and
{chr(10).join(goal_lines)}
  ))
  (:metric minimize (total-cost))

)
"""
    return pddl

def main():
    parser = argparse.ArgumentParser(
        description="Convert a stonesngems_cpp level string into a PDDL problem."
    )
    parser.add_argument(
        "level_input",
        help="Either a |-delimited level string, or a path to a .txt file containing it."
    )
    parser.add_argument(
        "-p", "--problem-name",
        default="",
        help="Name of the PDDL problem (default: level-1)."
    )
    parser.add_argument(
        "-d", "--domain-name",
        default="mine-tick-gravity",
        help="Name of the PDDL domain (default: mine-tick-gravity)."
    )
    parser.add_argument(
        "-a", "--agent-name",
        default="player",
        help="Name of the agent object (default: player)."
    )
    args = parser.parse_args()

    # --------------------------------------------------
    # Read level string
    # --------------------------------------------------
    level_input = args.level_input

    if level_input.endswith(".txt"):
        try:
            with open(level_input, "r", encoding="utf-8") as f:
                level_str = f.read()
        except OSError as e:
            sys.stderr.write(f"Error reading file '{level_input}': {e}\n")
            sys.exit(1)
    else:
        level_str = level_input

    if args.problem_name == "":
        args.problem_name = level_input.rsplit(".", 1)[0] if level_input.endswith(".txt") else "level"

    try:
        pddl = generate_pddl_problem(
            level_str,
            problem_name=args.problem_name,
            domain_name=args.domain_name,
            agent_name=args.agent_name,
        )
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    # Write to stdout
    sys.stdout.write(pddl)

    # Also persist to <problem_name>.pddl in the current working directory
    try:
        out_path = Path(f"{args.problem_name}.pddl")
        out_path.write_text(pddl, encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"Warning: failed to write {args.problem_name}.pddl: {e}\n")


if __name__ == "__main__":
    main()
