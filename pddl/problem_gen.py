"""
Convert a stonesngems_cpp level string into a PDDL problem
for the mine-tick-gravity domain.

Level string format (from stonesngems_cpp README):

    rows|cols|max_time|required_gems|cell_0|cell_1|...|cell_{rows*cols-1}

where each cell_i is an integer HiddenCellType ID.
"""

import argparse
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Mapping from HiddenCellType IDs to our simplified PDDL predicates
# ----------------------------------------------------------------------

# These values are taken from stonesngems_cpp/definitions.h
# (enum class HiddenCellType). We only handle a subset here.
STONE_IDS   = {3, 4, 48}        # Stone, StoneFalling, StoneInDirt
GEM_IDS     = {5, 6}            # Diamond, DiamondFalling
EMPTY_IDS   = {1}               # Empty
DIRT_IDS    = {2}               # Dirt
AGENT_IDS   = {0, 9}            # Agent, AgentInExit
BRICK_IDS   = {
    7, 8,                      # ExitClosed, ExitOpen
    18, 19,                    # WallBrick, WallSteel
    20, 21, 22,                # Magic walls (treat as solid)
}

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

def generate_pddl_problem(
    level_str: str,
    problem_name: str = "level-1",
    domain_name: str = "mine-tick-gravity",
    agent_name: str = "player",
) -> str:
    """
    Generate a full PDDL problem text from a level string.
    """
    rows, cols, max_time, required_gems, cell_ids = parse_level_string(level_str)

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

    # Find agent and classify contents
    agent_pos = None
    contents = {}  # (r, c) -> kind

    for idx, cell_id in enumerate(cell_ids):
        r = idx // cols
        c = idx % cols
        kind = classify_cell_id(cell_id)
        contents[(r, c)] = kind
        if kind == "agent":
            if agent_pos is not None:
                raise ValueError(
                    "Multiple agent cells found; this script expects exactly one."
                )
            agent_pos = (r, c)

    if agent_pos is None:
        raise ValueError(
            "No agent found in level (no cell with ID in AGENT_IDS)."
        )

    # Shift agent into padded coordinates
    padded_agent_pos = (agent_pos[0] + 1, agent_pos[1] + 1)

    # ------------------------------------------------------------------
    # :objects
    # ------------------------------------------------------------------
    obj_lines = [f"    {agent_name} - agent"]
    obj_lines.append(f"    {' '.join(interior_cells)} - real-cell")
    obj_lines.append(f"    {' '.join(border_cells)} - border-cell")

    # ------------------------------------------------------------------
    # :init
    # ------------------------------------------------------------------
    init_lines = []

    # High-level flags
    init_lines.append("    (agent-alive)")


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
            elif inner_kind == "brick":
                init_lines.append(f"    (brick {cname})")


    # Adjacency predicates: up, down, left-of, right-of
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
            if c > 0:
                left = cell_name(r, c - 1)
                init_lines.append(f"    (right-of {left} {cname})")
            # left-of: this -> right
            if c < padded_cols - 1:
                right = cell_name(r, c + 1)
                init_lines.append(f"    (left-of {cname} {right})")

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
    goal_lines = ["    (got-gem)"]

    # Assemble full PDDL
    pddl = f"""\
(define (problem {problem_name})
  (:domain {domain_name})
  (:objects
{chr(10).join(obj_lines)}
  )
  (:init
{chr(10).join(init_lines)}
  )
  (:goal
  (and
{chr(10).join(goal_lines)}
  ))
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
                level_str = f.read().strip()
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
