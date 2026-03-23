#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDDL_DIR = ROOT / "pddl"
sys.path.insert(0, str(PDDL_DIR))

import problem_gen as base  # type: ignore  # noqa: E402
import problem_gen_plus_from_domain as plus_gen  # type: ignore  # noqa: E402

SELECTED_LEVELS = (1, 2, 3, 6, 7, 8, 9, 11, 13, 14)
DEFAULT_DOMAIN_NAME = "mine-tick-gravity-plus-scanner-separated-events"
STEEL_WALL_ID = 19


def _load_level_strings(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _gem_positions(level_str: str) -> list[tuple[int, int]]:
    rows, cols, _max_time, _required_gems, cell_ids = base.parse_level_string(level_str)
    positions: list[tuple[int, int]] = []
    for idx, cell_id in enumerate(cell_ids):
        if base.classify_cell_id(cell_id) == "gem":
            positions.append((idx // cols, idx % cols))
    return positions


def _target_only_name(level_index: int, gem_ordinal: int) -> str:
    return f"bd_level_{level_index:02d}_target_gem_{gem_ordinal:03d}"


def _start_target_name(level_index: int, start_gem_ordinal: int, target_gem_ordinal: int) -> str:
    return (
        f"bd_level_{level_index:02d}_start_gem_{start_gem_ordinal:03d}"
        f"_target_gem_{target_gem_ordinal:03d}"
    )


def _render_level(
    rows: int,
    cols: int,
    max_time: int,
    required_gems: int,
    cell_ids: list[int],
) -> str:
    fields = [str(rows), str(cols), str(max_time), str(required_gems)]
    fields.extend(f"{cell_id:02d}" for cell_id in cell_ids)
    return "|".join(fields) + "|"


def _trim_outer_steel_border(
    rows: int,
    cols: int,
    cell_ids: list[int],
) -> tuple[int, int, list[int]]:
    grid = [cell_ids[row_start:row_start + cols] for row_start in range(0, len(cell_ids), cols)]

    while grid and all(cell_id == STEEL_WALL_ID for cell_id in grid[0]):
        grid.pop(0)
    while grid and all(cell_id == STEEL_WALL_ID for cell_id in grid[-1]):
        grid.pop()
    while grid and grid[0] and all(row[0] == STEEL_WALL_ID for row in grid):
        for row in grid:
            del row[0]
    while grid and grid[0] and all(row[-1] == STEEL_WALL_ID for row in grid):
        for row in grid:
            row.pop()

    if not grid or not grid[0]:
        raise ValueError("Trimming the outer steel border removed the entire level.")

    trimmed_rows = len(grid)
    trimmed_cols = len(grid[0])
    trimmed_cell_ids = [cell_id for row in grid for cell_id in row]
    return trimmed_rows, trimmed_cols, trimmed_cell_ids


def _marked_level_text(
    level_str: str,
    *,
    target_gem_ordinal: int,
    start_gem_ordinal: int | None = None,
) -> str:
    rows, cols, max_time, required_gems, cell_ids = base.parse_level_string(level_str)
    gem_positions = _gem_positions(level_str)
    target_pos = gem_positions[target_gem_ordinal - 1]
    target_idx = target_pos[0] * cols + target_pos[1]
    target_cell_id = cell_ids[target_idx]
    if target_cell_id in base.GEM_FALLING_IDS:
        cell_ids[target_idx] = base.TARGET_GEM_FALLING_ID
    else:
        cell_ids[target_idx] = base.TARGET_GEM_STATIC_ID

    if start_gem_ordinal is not None:
        if start_gem_ordinal == target_gem_ordinal:
            raise ValueError(
                "Self-contained txt test problems cannot encode start_gem == target_gem."
            )
        start_pos = gem_positions[start_gem_ordinal - 1]
        start_idx = start_pos[0] * cols + start_pos[1]
        agent_idx = next(
            idx for idx, cell_id in enumerate(cell_ids)
            if cell_id in base.AGENT_IDS
        )
        cell_ids[agent_idx] = next(iter(base.EMPTY_IDS))
        cell_ids[start_idx] = next(iter(base.AGENT_IDS))

    trimmed_rows, trimmed_cols, trimmed_cell_ids = _trim_outer_steel_border(rows, cols, cell_ids)
    return _render_level(trimmed_rows, trimmed_cols, max_time, required_gems, trimmed_cell_ids)


def _write_level_file(path: Path, level_str: str) -> None:
    path.write_text(f"{level_str.strip()}\n", encoding="utf-8")


def generate_selected_problems(
    levels_path: Path,
    output_dir: Path,
    domain_name: str,
) -> list[str]:
    level_strings = _load_level_strings(levels_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    for stale in output_dir.glob("bd_level_*.pddl"):
        stale.unlink()
    for stale in output_dir.glob("bd_level_*.txt"):
        stale.unlink()

    written: list[str] = []
    for level_index in SELECTED_LEVELS:
        try:
            level_str = level_strings[level_index - 1]
        except IndexError as exc:
            raise ValueError(f"Missing level {level_index} in {levels_path}.") from exc

        gem_positions = _gem_positions(level_str)
        gem_count = len(gem_positions)
        for gem_ordinal in range(1, gem_count + 1):
            stem = _target_only_name(level_index, gem_ordinal)
            out_path = output_dir / f"{stem}.txt"
            _write_level_file(
                out_path,
                _marked_level_text(level_str, target_gem_ordinal=gem_ordinal),
            )
            written.append(out_path.name)

        if level_index == 1:
            for start_gem_ordinal in range(1, gem_count + 1):
                for target_gem_ordinal in range(1, gem_count + 1):
                    if start_gem_ordinal == target_gem_ordinal:
                        continue
                    stem = _start_target_name(level_index, start_gem_ordinal, target_gem_ordinal)
                    out_path = output_dir / f"{stem}.txt"
                    _write_level_file(
                        out_path,
                        _marked_level_text(
                            level_str,
                            start_gem_ordinal=start_gem_ordinal,
                            target_gem_ordinal=target_gem_ordinal,
                        ),
                    )
                    written.append(out_path.name)

    return written


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Generate self-contained level-text test inputs with in-grid target-gem "
            "markers for selected Stones & Gems levels."
        )
    )
    ap.add_argument(
        "--levels-file",
        type=Path,
        default=ROOT / "stonesandgem" / "bd_levels" / "bd_levels.txt",
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "pddl" / "test_problems",
    )
    ap.add_argument(
        "--domain-name",
        default=DEFAULT_DOMAIN_NAME,
        help="Unused compatibility flag kept so existing invocations keep working.",
    )
    args = ap.parse_args()

    try:
        written = generate_selected_problems(args.levels_file, args.output_dir, args.domain_name)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    sys.stdout.write(f"Wrote {len(written)} level files to {args.output_dir}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
