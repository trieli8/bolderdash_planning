#!/usr/bin/env python3
"""Draw comparison diagrams for scanner/non-scanner and combined/separated models.

The script emits two SVGs:

* a map comparison for scanner vs non-scanner, using the level in
  ``pddl/problem_exsample.txt`` by default
* a 2x2 flow-chart comparison for scanner/non-scanner x combined/separated
* a combined overview that stacks the two diagrams into one SVG

Both diagrams are intentionally high-level. They are meant to communicate the
per-tick control-flow differences between the current domain variants rather
than reproduce every grounded action.
"""

from __future__ import annotations

import argparse
import base64
import html
import math
import sys
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path

PDDL_DIR = Path(__file__).resolve().parents[1] / "pddl"
TILE_DIR = Path(__file__).resolve().parents[1] / "stonesandgem" / "tiles"
sys.path.insert(0, str(PDDL_DIR))

import problem_gen as base  # type: ignore  # noqa: E402


@dataclass(frozen=True)
class CellInfo:
    row: int
    col: int
    cell_id: int
    kind: str
    label: str = ""
    is_target: bool = False


def read_level_text(level_arg: str) -> str:
    path = Path(level_arg)
    if path.exists() and path.suffix == ".txt":
        raw = path.read_text(encoding="utf-8")
    else:
        raw = level_arg
    return "".join(part.strip() for part in raw.splitlines() if part.strip())


def classify_kind(cell_id: int) -> str:
    if cell_id in base.AGENT_IDS:
        return "agent"
    if cell_id in base.EMPTY_IDS:
        return "empty"
    if cell_id in base.DIRT_IDS:
        return "dirt"
    if cell_id in base.STONE_IDS:
        return "stone"
    if cell_id in base.GEM_IDS:
        return "gem"
    return "brick"


def build_cells(level_text: str) -> tuple[base.PreparedLevel, list[list[CellInfo]]]:
    prepared = base.prepare_level(level_text)
    rows, cols = prepared.rows, prepared.cols
    cell_grid: list[list[CellInfo]] = []

    gem_index = 0
    stone_index = 0
    dirt_index = 0
    for r in range(rows):
        row_cells: list[CellInfo] = []
        for c in range(cols):
            idx = r * cols + c
            cell_id = prepared.cell_ids[idx]
            kind = classify_kind(cell_id)
            label = ""
            is_target = False
            if kind == "agent":
                label = "A"
            elif kind == "gem":
                gem_index += 1
                label = f"G{gem_index}"
                if prepared.target_gem_pos == (r, c):
                    label = "T"
                    is_target = True
            elif kind == "stone":
                stone_index += 1
                label = f"S{stone_index}"
            elif kind == "dirt":
                dirt_index += 1
                label = f"D{dirt_index}"
            row_cells.append(CellInfo(r, c, cell_id, kind, label, is_target))
        cell_grid.append(row_cells)
    return prepared, cell_grid


def escape(text: str) -> str:
    return html.escape(text, quote=True)


def wrap_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def svg_header(width: int, height: int, title: str, subtitle: str) -> list[str]:
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#334155"/>',
        "</marker>",
        '<marker id="arrow-soft" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b"/>',
        "</marker>",
        "</defs>",
        '<rect x="0" y="0" width="100%" height="100%" fill="#fbfbf7"/>',
        f'<text x="40" y="38" font-size="24" font-family="Arial, Helvetica, sans-serif" font-weight="700" fill="#111827">{escape(title)}</text>',
    ]
    if subtitle:
        lines.append(
            f'<text x="40" y="62" font-size="13" font-family="Arial, Helvetica, sans-serif" fill="#475569">{escape(subtitle)}</text>'
        )
    return lines


def svg_footer() -> list[str]:
    return ["</svg>"]


def nest_svg(svg_text: str, x: float, y: float) -> str:
    lines = svg_text.splitlines()
    if not lines:
        return svg_text
    first = lines[0]
    if first.startswith("<svg "):
        first = first.replace("<svg ", f'<svg x="{x:.2f}" y="{y:.2f}" ', 1)
    return "\n".join([first, *lines[1:]])


@lru_cache(maxsize=None)
def tile_data_uri(filename: str) -> str:
    data = (TILE_DIR / filename).read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def tile_asset_name(cell_id: int) -> str:
    if cell_id in base.AGENT_IDS:
        return "agent_in_exit.png" if cell_id == 9 else "agent.png"
    if cell_id in base.EMPTY_IDS:
        return "empty.png"
    if cell_id in base.DIRT_IDS:
        return "dirt.png"
    if cell_id in base.STONE_IDS:
        if cell_id == 48:
            return "stone_in_dirt.png"
        if cell_id == 47:
            return "pebble_in_dirt.png"
        return "stone.png"
    if cell_id in base.GEM_IDS:
        return "diamond.png"
    if cell_id == 7:
        return "exit_closed.png"
    if cell_id == 8:
        return "exit_open.png"
    if cell_id == 18:
        return "wall_brick.png"
    if cell_id == 19:
        return "wall_steel.png"
    if cell_id in {20, 22}:
        return "wall_magic_off.png"
    if cell_id == 21:
        return "wall_magic_on.png"
    if cell_id == 23:
        return "blob.png"
    if cell_id in {10, 11, 12, 13}:
        return "firefly.png"
    if cell_id in {14, 15, 16, 17}:
        return "butterfly.png"
    if cell_id == 24:
        return "explosion.png"
    if cell_id == 39:
        return "nut.png"
    if cell_id in {40, 41}:
        return "bomb.png"
    if cell_id in {43, 44, 45, 46}:
        return "orange.png"
    if cell_id == 27:
        return "gate_red_closed.png"
    if cell_id == 28:
        return "gate_red_open.png"
    if cell_id == 29:
        return "key_red.png"
    if cell_id == 30:
        return "gate_blue_closed.png"
    if cell_id == 31:
        return "gate_blue_open.png"
    if cell_id == 32:
        return "key_blue.png"
    if cell_id == 33:
        return "gate_green_closed.png"
    if cell_id == 34:
        return "gate_green_open.png"
    if cell_id == 35:
        return "key_green.png"
    if cell_id == 36:
        return "gate_yellow_closed.png"
    if cell_id == 37:
        return "gate_yellow_open.png"
    if cell_id == 38:
        return "key_yellow.png"
    if cell_id == 42:
        return "bomb.png"
    if cell_id == 49:
        return "void_in_dirt.png"
    return "empty.png"


def draw_image(lines: list[str], x: float, y: float, size: float, filename: str) -> None:
    uri = tile_data_uri(filename)
    lines.append(
        f'<image href="{uri}" x="{x:.2f}" y="{y:.2f}" width="{size:.2f}" height="{size:.2f}" '
        f'preserveAspectRatio="none"/>'
    )


def draw_tile_cell(
    lines: list[str],
    x: float,
    y: float,
    size: float,
    cell_id: int,
    *,
    highlight: str | None = None,
    role_label: str | None = None,
    label_fill: str = "#ffffff",
    label_text_fill: str = "#0f172a",
) -> None:
    draw_color = {
        None: ("#f8fafc", "#cbd5e1", 1.0),
        "first": ("#dcfce7", "#16a34a", 3.0),
        "current": ("#dbeafe", "#2563eb", 3.2),
        "next": ("#ffedd5", "#d97706", 3.0),
        "last": ("#ede9fe", "#7c3aed", 3.2),
        "danger": ("#fee2e2", "#dc2626", 3.2),
    }[highlight]
    fill, stroke, stroke_width = draw_color
    rect(lines, x, y, size, size, fill=fill, stroke=stroke, stroke_width=stroke_width, rx=6, opacity=0.9 if highlight else 1.0)
    inner = 3.0
    draw_image(lines, x + inner, y + inner, size - inner * 2, tile_asset_name(cell_id))
    if role_label:
        tag_w = 18.0 if len(role_label) <= 2 else min(size - 8.0, 108.0)
        tag_h = 16.0
        tag_x = x + 4.0
        tag_y = y + 4.0
        rect(
            lines,
            tag_x,
            tag_y,
            tag_w,
            tag_h,
            fill=label_fill,
            stroke=stroke,
            stroke_width=1.0,
            rx=6,
            opacity=0.92,
        )
        draw_text(
            lines,
            tag_x + tag_w / 2,
            tag_y + 12.0,
            role_label,
            size=9,
            fill=label_text_fill,
            weight="700",
        )


def pick_reference_cells(prepared: base.PreparedLevel) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
    rows, cols = prepared.rows, prepared.cols
    current = (1, 1)
    if current[0] >= rows:
        current = (max(0, rows // 2), max(0, cols // 2))
    if current[1] >= cols:
        current = (current[0], max(0, cols // 2))
    next_cell = (current[0], min(cols - 1, current[1] + 1))
    if next_cell == current and current[0] + 1 < rows:
        next_cell = (current[0] + 1, 0)
    first_cell = (0, 0)
    last_cell = (rows - 1, cols - 1)
    danger = (current[0], max(0, current[1] - 2))
    return current, next_cell, first_cell, last_cell, danger


def draw_text(lines: list[str], x: float, y: float, text: str, *, size: int = 14, fill: str = "#111827",
              anchor: str = "middle", weight: str = "400", family: str = "Arial, Helvetica, sans-serif") -> None:
    lines.append(
        f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" font-size="{size}" '
        f'font-family="{family}" font-weight="{weight}" fill="{fill}">{escape(text)}</text>'
    )


def draw_multiline_text(
    lines: list[str],
    x: float,
    y: float,
    text: str,
    *,
    size: int = 14,
    fill: str = "#111827",
    anchor: str = "middle",
    weight: str = "400",
    line_height: int | None = None,
) -> None:
    split = text.split("\n")
    lh = line_height or int(size * 1.25)
    offset = -(len(split) - 1) * lh / 2
    for idx, part in enumerate(split):
        draw_text(
            lines,
            x,
            y + offset + idx * lh,
            part,
            size=size,
            fill=fill,
            anchor=anchor,
            weight=weight,
        )


def rect(lines: list[str], x: float, y: float, w: float, h: float, *, fill: str, stroke: str = "#111827",
         stroke_width: float = 1.0, rx: float = 10.0, opacity: float = 1.0) -> None:
    lines.append(
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx:.2f}" ry="{rx:.2f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width:.2f}" opacity="{opacity:.3f}"/>'
    )


def line(
    lines: list[str],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str = "#334155",
    stroke_width: float = 2.0,
    dash: str | None = None,
    marker_end: str | None = "url(#arrow)",
    opacity: float = 1.0,
) -> None:
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    marker_attr = f' marker-end="{marker_end}"' if marker_end else ""
    lines.append(
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
        f'stroke="{stroke}" stroke-width="{stroke_width:.2f}"{dash_attr}{marker_attr} opacity="{opacity:.3f}"/>'
    )


def rounded_box(
    lines: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str,
    stroke: str,
    title: str,
    subtitle: str = "",
    title_size: int = 15,
    subtitle_size: int = 12,
    title_color: str = "#0f172a",
    subtitle_color: str = "#475569",
) -> None:
    rect(lines, x, y, w, h, fill=fill, stroke=stroke, stroke_width=1.6, rx=16)
    title_lines = title.split("\n")
    title_y = y + 26
    draw_multiline_text(lines, x + w / 2, title_y, "\n".join(title_lines), size=title_size, fill=title_color, weight="700")
    if subtitle:
        draw_multiline_text(
            lines,
            x + w / 2,
            y + h / 2 + 16,
            "\n".join(wrap_text(subtitle, 38)),
            size=subtitle_size,
            fill=subtitle_color,
        )


def panel_frame(lines: list[str], x: float, y: float, w: float, h: float, title: str, subtitle: str) -> None:
    rect(lines, x, y, w, h, fill="#ffffff", stroke="#cbd5e1", stroke_width=1.2, rx=18)
    draw_text(lines, x + 18, y + 28, title, size=18, fill="#0f172a", anchor="start", weight="700")
    if subtitle:
        draw_text(lines, x + 18, y + 50, subtitle, size=12, fill="#475569", anchor="start")


def draw_map_panel(
    lines: list[str],
    prepared: base.PreparedLevel,
    grid: list[list[CellInfo]],
    *,
    x0: float,
    y0: float,
    cell: float,
    title: str,
    subtitle: str,
    scanner_mode: bool,
) -> None:
    rows, cols = prepared.rows, prepared.cols
    panel_w = cols * cell + 40
    panel_h = rows * cell + 120
    panel_frame(lines, x0, y0, panel_w, panel_h, title, subtitle)

    gx = x0 + 20
    gy = y0 + 72

    if scanner_mode:
        note = "Row-major scan order"
    else:
        note = "Direct neighbor checks"
    draw_text(lines, x0 + panel_w - 18, y0 + 28, note, size=11, fill="#64748b", anchor="end")

    current_pos, next_pos, first_pos, last_pos, danger_pos = pick_reference_cells(prepared)
    if scanner_mode:
        current_pos = current_pos
        danger_pos = None
    else:
        current_pos = (1, 3) if rows > 1 and cols > 3 else current_pos
        danger_pos = (1, 1) if rows > 1 and cols > 1 else danger_pos

    for r in range(rows):
        for c in range(cols):
            info = grid[r][c]
            cx = gx + c * cell
            cy = gy + r * cell
            highlight = None
            role_label = None
            label_fill = "#ffffff"
            label_text_fill = "#ffffff"
            if scanner_mode and (r, c) == first_pos:
                highlight = "first"
                role_label = "F"
                label_fill = "#16a34a"
            elif scanner_mode and (r, c) == next_pos:
                highlight = "next"
                role_label = "N"
                label_fill = "#d97706"
            elif scanner_mode and (r, c) == last_pos:
                highlight = "last"
                role_label = "L"
                label_fill = "#7c3aed"
            elif (r, c) == current_pos:
                highlight = "current"
                role_label = "C"
                label_fill = "#2563eb"
            elif not scanner_mode and danger_pos is not None and (r, c) == danger_pos:
                highlight = "danger"
                role_label = "D"
                label_fill = "#dc2626"
            draw_tile_cell(
                lines,
                cx,
                cy,
                cell,
                info.cell_id,
                highlight=highlight,
                role_label=role_label,
                label_fill=label_fill,
                label_text_fill=label_text_fill,
            )

    # Legend is shared across both panels.


def draw_shared_map_legend(lines: list[str], x: float, y: float, w: float) -> None:
    items = [
        ("#16a34a", "F", "first-cell"),
        ("#2563eb", "C", "current-cell"),
        ("#d97706", "N", "next-cell"),
        ("#7c3aed", "L", "last-cell"),
        ("#dc2626", "D", "danger-cell"),
    ]
    box_h = 64
    rect(lines, x, y, w, box_h, fill="#ffffff", stroke="#cbd5e1", stroke_width=1.2, rx=18)
    item_y = y + 42
    item_gap = 160
    item_w = 142
    total_width = len(items) * item_gap - (item_gap - item_w)
    cursor = x + max(0.0, (w - total_width) / 2)
    for fill, symbol, label in items:
        rect(lines, cursor, item_y - 14, 18, 18, fill=fill, stroke=fill, stroke_width=1.2, rx=6, opacity=0.95)
        draw_text(lines, cursor + 9, item_y - 1, symbol, size=10, fill="#ffffff", weight="700")
        draw_text(lines, cursor + 26, item_y - 1, label, size=11, fill="#334155", anchor="start")
        cursor += item_gap


def map_legend_svg() -> str:
    width = 760
    height = 120
    lines = svg_header(width, height, "Map Legend", "")
    draw_shared_map_legend(lines, 20, 36, width - 40)
    lines.extend(svg_footer())
    return "\n".join(lines) + "\n"


def map_comparison_svg(level_text: str) -> str:
    prepared, grid = build_cells(level_text)
    rows, cols = prepared.rows, prepared.cols
    cell = 48.0
    panel_w = cols * cell + 40
    panel_h = rows * cell + 88
    gap = 24.0
    width = int(40 + panel_w * 2 + gap)
    legend_w = width - 120
    legend_x = 60
    legend_y = 80 + panel_h + 20
    height = int(legend_y + 84)

    lines = svg_header(
        width,
        height,
        "Scanner vs Non-scanner Map",
        "",
    )

    draw_map_panel(
        lines,
        prepared,
        grid,
        x0=20,
        y0=80,
        cell=cell,
        title="Scanner model",
        subtitle="",
        scanner_mode=True,
    )
    draw_map_panel(
        lines,
        prepared,
        grid,
        x0=20 + panel_w + gap,
        y0=80,
        cell=cell,
        title="Non-scanner model",
        subtitle="",
        scanner_mode=False,
    )
    draw_shared_map_legend(lines, legend_x, legend_y, legend_w)

    lines.extend(svg_footer())
    return "\n".join(lines) + "\n"


def flow_box(
    lines: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str,
    *,
    fill: str,
    stroke: str,
    title_size: int = 14,
) -> None:
    rounded_box(lines, x, y, w, h, fill=fill, stroke=stroke, title=title, subtitle=subtitle, title_size=title_size)


def step_box(
    lines: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str = "",
    *,
    fill: str,
    stroke: str,
    title_size: int = 13,
    subtitle_size: int = 10,
) -> None:
    rounded_box(
        lines,
        x,
        y,
        w,
        h,
        fill=fill,
        stroke=stroke,
        title=title,
        subtitle=subtitle,
        title_size=title_size,
        subtitle_size=subtitle_size,
    )


def action_grid_height(count: int, cols: int = 3, *, title_lines: int = 1, subtitle_lines: int = 1) -> float:
    rows = math.ceil(count / cols)
    header = 18 + title_lines * 14 + (subtitle_lines * 12 if subtitle_lines else 0)
    chips = rows * 26 + max(0, rows - 1) * 8
    return header + chips + 20


def action_grid(
    lines: list[str],
    x: float,
    y: float,
    w: float,
    *,
    title: str,
    subtitle: str,
    labels: list[str],
    fill: str,
    stroke: str,
    chip_fill: str,
    chip_stroke: str,
    title_fill: str,
    subtitle_fill: str,
    chip_text_fill: str,
    cols: int = 3,
) -> None:
    rows = math.ceil(len(labels) / cols)
    box_h = action_grid_height(len(labels), cols)
    rect(lines, x, y, w, box_h, fill=fill, stroke=stroke, stroke_width=1.6, rx=16)
    draw_text(lines, x + w / 2, y + 24, title, size=13, fill=title_fill, weight="700")
    if subtitle:
        draw_multiline_text(lines, x + w / 2, y + 40, subtitle, size=10, fill=subtitle_fill)
    chip_gap_x = 10
    chip_gap_y = 8
    inner_w = w - 36
    chip_w = (inner_w - (cols - 1) * chip_gap_x) / cols
    chip_start_x = x + 18
    chip_start_y = y + 56
    for idx, label in enumerate(labels):
        row = idx // cols
        col = idx % cols
        cx = chip_start_x + col * (chip_w + chip_gap_x)
        cy = chip_start_y + row * (26 + chip_gap_y)
        rect(lines, cx, cy, chip_w, 26, fill=chip_fill, stroke=chip_stroke, stroke_width=1.1, rx=9)
        draw_text(lines, cx + chip_w / 2, cy + 17, label, size=8, fill=chip_text_fill, weight="700")


def action_grid_bottom(y: float, labels: list[str], cols: int = 3) -> float:
    return y + action_grid_height(len(labels), cols)


def draw_vertical_flow(lines: list[str], x: float, y: float, w: float, boxes: list[tuple[str, str, str, str]]) -> None:
    box_h = 66
    gap = 18
    for idx, (title, subtitle, fill, stroke) in enumerate(boxes):
        by = y + idx * (box_h + gap)
        flow_box(lines, x, by, w, box_h, title, subtitle, fill=fill, stroke=stroke)
        if idx < len(boxes) - 1:
            line(lines, x + w / 2, by + box_h, x + w / 2, by + box_h + gap, stroke="#475569", stroke_width=2.2, marker_end="url(#arrow)")


def draw_horizontal_flow(lines: list[str], x: float, y: float, w: float, boxes: list[tuple[str, str, str, str]]) -> None:
    box_w = 168
    gap = 20
    total = len(boxes) * box_w + (len(boxes) - 1) * gap
    start_x = x + max(0.0, (w - total) / 2)
    box_h = 82
    for idx, (title, subtitle, fill, stroke) in enumerate(boxes):
        bx = start_x + idx * (box_w + gap)
        flow_box(lines, bx, y, box_w, box_h, title, subtitle, fill=fill, stroke=stroke)
        if idx < len(boxes) - 1:
            line(
                lines,
                bx + box_w,
                y + box_h / 2,
                bx + box_w + gap,
                y + box_h / 2,
                stroke="#475569",
                stroke_width=2.2,
                marker_end="url(#arrow)",
            )


def flow_svg() -> str:
    width = 1110
    height = 820
    lines = svg_header(
        width,
        height,
        "Combined vs Separated Physics",
        "Combined starts with a free choice of updater functions; separated walks the checks in a fixed order first.",
    )

    panel_w = 500
    panel_h = 620
    left_x = 30
    right_x = 560
    top_y = 92
    fill_move = "#dbeafe"
    fill_phase = "#ede9fe"
    fill_phys = "#fff7ed"
    fill_end = "#e2e8f0"
    stroke_move = "#2563eb"
    stroke_phase = "#7c3aed"
    stroke_phys = "#d97706"
    stroke_end = "#475569"

    panel_frame(lines, left_x, top_y, panel_w, panel_h, "Combined", "Any updater can be chosen as soon as the tick starts.")
    panel_frame(lines, right_x, top_y, panel_w, panel_h, "Separated", "The available updater narrows as the tick advances.")

    start_h = 46
    gap = 12
    inner_x = 60
    inner_w = panel_w - 120

    # Combined: a single choice set is available immediately after the tick starts.
    start_y = top_y + 84
    step_box(lines, left_x + inner_x, start_y, inner_w, start_h, "start_tick", "opens the tick", fill=fill_move, stroke=stroke_move)
    line(lines, left_x + panel_w / 2, start_y + start_h, left_x + panel_w / 2, start_y + start_h + gap, stroke="#2563eb", stroke_width=2.2)
    combined_labels = [
        "fall",
        "roll left",
        "roll right",
        "noop",
    ]
    combined_grid_y = start_y + start_h + gap
    action_grid(
        lines,
        left_x + 40,
        combined_grid_y,
        panel_w - 80,
        title="choose any updater",
        subtitle="fall, roll left, roll right, or noop",
        labels=combined_labels,
        fill=fill_phys,
        stroke=stroke_phys,
        chip_fill="#fed7aa",
        chip_stroke="#ea580c",
        title_fill="#9a3412",
        subtitle_fill="#7c2d12",
        chip_text_fill="#9a3412",
        cols=4,
    )
    combined_end_y = combined_grid_y + action_grid_height(len(combined_labels), 4) + gap
    step_box(lines, left_x + inner_x, combined_end_y, inner_w, start_h, "end_tick", "tick closes after one choice resolves", fill=fill_end, stroke=stroke_end)

    # Separated: explicit linear checks before the updater set.
    sep_start_y = top_y + 84
    step_box(lines, right_x + inner_x, sep_start_y, inner_w, start_h, "start_tick", "opens the tick", fill=fill_move, stroke=stroke_move)
    line(lines, right_x + panel_w / 2, sep_start_y + start_h, right_x + panel_w / 2, sep_start_y + start_h + gap, stroke="#2563eb", stroke_width=2.2)

    decision_w = 252
    result_w = 132
    result_x = right_x + 44
    decision_x = result_x + result_w + 10
    branch_gap = 12

    def branch_row(y: float, decision_title: str, decision_subtitle: str, result_title: str, result_subtitle: str) -> None:
        step_box(lines, result_x, y, result_w, start_h, result_title, result_subtitle, fill=fill_phys, stroke=stroke_phys, title_size=12, subtitle_size=10)
        step_box(lines, decision_x, y, decision_w, start_h, decision_title, decision_subtitle, fill=fill_phase, stroke=stroke_phase, title_size=12, subtitle_size=10)
        line(lines, decision_x, y + start_h / 2, result_x + result_w, y + start_h / 2, stroke="#7c3aed", stroke_width=2.0, marker_end="url(#arrow)")

    row1_y = sep_start_y + start_h + gap
    branch_row(row1_y, "can fall", "if possible, open the fall branch", "fall", "take the fall branch")
    line(lines, decision_x + decision_w / 2, row1_y + start_h, decision_x + decision_w / 2, row1_y + start_h + branch_gap, stroke="#7c3aed", stroke_width=2.2, marker_end="url(#arrow)")

    row2_y = row1_y + start_h + branch_gap
    branch_row(row2_y, "can roll left", "if fall is not taken, open the left roll branch", "roll left", "take the left roll branch")
    line(lines, decision_x + decision_w / 2, row2_y + start_h, decision_x + decision_w / 2, row2_y + start_h + branch_gap, stroke="#7c3aed", stroke_width=2.2, marker_end="url(#arrow)")

    row3_y = row2_y + start_h + branch_gap
    branch_row(row3_y, "can roll right", "if left roll is not taken, open the right roll branch", "roll right", "take the right roll branch")
    line(lines, decision_x + decision_w / 2, row3_y + start_h, decision_x + decision_w / 2, row3_y + start_h + branch_gap, stroke="#7c3aed", stroke_width=2.2, marker_end="url(#arrow)")

    row4_y = row3_y + start_h + branch_gap
    step_box(lines, right_x + inner_x, row4_y, inner_w, start_h, "noop", "fallback if no roll branch applies", fill=fill_phys, stroke=stroke_phys, title_size=12, subtitle_size=10)
    line(lines, right_x + panel_w / 2, row4_y + start_h, right_x + panel_w / 2, row4_y + start_h + gap, stroke="#d97706", stroke_width=2.2, marker_end="url(#arrow)")
    step_box(lines, right_x + inner_x, row4_y + start_h + gap, inner_w, start_h, "end_tick", "tick closes after the fallback resolves", fill=fill_end, stroke=stroke_end, title_size=12, subtitle_size=10)

    lines.extend(svg_footer())
    return "\n".join(lines) + "\n"


def overview_svg(level_text: str) -> str:
    map_svg = map_comparison_svg(level_text)
    flow_svg_text = flow_svg()
    width = 1300
    map_y = 48
    map_x = int((width - 816) / 2)
    flow_y = 676
    height = 1524

    lines = svg_header(width, height, "Model Comparison Overview", "")
    lines.append(nest_svg(map_svg, map_x, map_y))
    lines.append(nest_svg(flow_svg_text, 20, flow_y))
    lines.extend(svg_footer())
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate SVG diagrams comparing scanner/non-scanner and combined/separated models.")
    ap.add_argument(
        "--level",
        default=str(PDDL_DIR / "problem_exsample.txt"),
        help="Level string or path to a .txt file (default: pddl/problem_exsample.txt)",
    )
    ap.add_argument(
        "--out-dir",
        default=str(Path("tools") / "diagram_outputs"),
        help="Directory to write SVGs into (default: tools/diagram_outputs)",
    )
    ap.add_argument(
        "--map-out",
        default="scanner_non_scanner_map.svg",
        help="Filename for the map comparison SVG.",
    )
    ap.add_argument(
        "--flow-out",
        default="combined_separated_flows.svg",
        help="Filename for the flow-chart SVG.",
    )
    ap.add_argument(
        "--overview-out",
        default="model_comparison_overview.svg",
        help="Filename for the combined overview SVG.",
    )
    ap.add_argument(
        "--legend-out",
        default="map_legend.svg",
        help="Filename for the standalone map legend SVG.",
    )
    args = ap.parse_args()

    try:
        level_text = read_level_text(args.level)
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        map_path = out_dir / args.map_out
        flow_path = out_dir / args.flow_out
        overview_path = out_dir / args.overview_out
        legend_path = out_dir / args.legend_out
        map_path.write_text(map_comparison_svg(level_text), encoding="utf-8")
        flow_path.write_text(flow_svg(), encoding="utf-8")
        overview_path.write_text(overview_svg(level_text), encoding="utf-8")
        legend_path.write_text(map_legend_svg(), encoding="utf-8")
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    sys.stdout.write(f"Wrote {map_path}\nWrote {flow_path}\n")
    sys.stdout.write(f"Wrote {overview_path}\n")
    sys.stdout.write(f"Wrote {legend_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
