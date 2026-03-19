#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence


def benchmarking_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_latest_csv() -> Path:
    results_root = benchmarking_root() / "results"
    candidates = [p for p in results_root.glob("*/level_growth.csv") if p.is_file()]
    if not candidates:
        candidates = [p for p in results_root.glob("*/level_growth*.csv") if p.is_file()]
    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No level_growth*.csv found in {results_root}")
    return candidates[0]


def safe_float(value: str) -> Optional[float]:
    v = (value or "").strip()
    if not v:
        return None
    try:
        return float(v)
    except Exception:
        return None


def marker_svg(shape: str, x: float, y: float, size: float, color: str) -> str:
    if shape == "square":
        h = size
        return f'<rect x="{x-h:.2f}" y="{y-h:.2f}" width="{2*h:.2f}" height="{2*h:.2f}" fill="{color}" stroke="#111" stroke-width="1"/>'
    return f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{size:.2f}" fill="{color}" stroke="#111" stroke-width="1"/>'


def distinct(values: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def choose_out_path(csv_path: Path, explicit: Optional[Path]) -> Path:
    if explicit:
        return explicit.resolve()
    return csv_path.with_suffix(".growth.svg")


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = [r for r in reader]
    if not rows:
        raise ValueError(f"CSV has no rows: {csv_path}")
    return rows


def metric_value(row: Dict[str, str], key: str) -> Optional[float]:
    return safe_float(row.get(key, ""))


def x_pos(cell_count: int, min_cells: int, max_cells: int, left: float, width: float) -> float:
    if max_cells <= min_cells:
        return left + width / 2.0
    frac = (cell_count - min_cells) / float(max_cells - min_cells)
    return left + frac * width


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Plot level growth benchmark CSV (runtime/grounding/heuristic/search/action-set) as SVG."
    )
    ap.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Path to level_growth CSV (default: latest in tools/benchmarking/results/*/).",
    )
    ap.add_argument("--out", type=Path, default=None, help="Output SVG path (default: <csv>.growth.svg).")
    ap.add_argument("--title", default="Level Growth Metrics", help="Chart title.")
    ap.add_argument(
        "--include-skipped",
        action="store_true",
        help="Include rows with status=skipped_after_timeout.",
    )
    ap.add_argument(
        "--include-dry-run",
        action="store_true",
        help="Include rows with status=dry-run.",
    )
    args = ap.parse_args()

    csv_path = args.csv.resolve() if args.csv else find_latest_csv()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    out_path = choose_out_path(csv_path, args.out)
    rows = load_rows(csv_path)

    filtered: List[Dict[str, str]] = []
    for r in rows:
        status = (r.get("status") or "").strip().lower()
        if not args.include_skipped and status == "skipped_after_timeout":
            continue
        if not args.include_dry_run and status == "dry-run":
            continue
        filtered.append(r)

    if not filtered:
        raise ValueError("No rows left after filtering.")

    for r in filtered:
        r["_domain"] = Path(r.get("domain", "")).stem or "unknown"
        kind = (r.get("domain_kind") or "").strip().lower()
        if not kind:
            kind = "plus" if "plus" in r["_domain"].lower() else "classic"
        r["_kind"] = kind
        cells = int(float(r.get("cells", "0") or "0"))
        r["_cells"] = str(cells)

    domains = sorted(distinct([r["_domain"] for r in filtered]))
    cells_values = sorted({int(r["_cells"]) for r in filtered})
    if not cells_values:
        raise ValueError("No valid cell counts in CSV.")

    min_cells = min(cells_values)
    max_cells = max(cells_values)

    metrics = [
        ("runtime_sec", "Runtime (s)"),
        ("grounding_sec", "Grounding (s)"),
        ("heuristic_sec", "Heuristic (s)"),
        ("search_sec", "Search (s)"),
        ("action_set_size", "Action Set Size"),
    ]

    width = 1300
    left = 90
    right = 290
    top = 80
    panel_h = 145
    panel_gap = 58
    chart_w = width - left - right
    chart_h_total = len(metrics) * panel_h + (len(metrics) - 1) * panel_gap
    bottom = 100
    height = top + chart_h_total + bottom

    palette = [
        "#1f77b4",
        "#d62728",
        "#2ca02c",
        "#ff7f0e",
        "#9467bd",
        "#17becf",
        "#8c564b",
        "#e377c2",
        "#bcbd22",
        "#7f7f7f",
    ]
    d_color = {d: palette[i % len(palette)] for i, d in enumerate(domains)}

    grouped: Dict[str, List[Dict[str, str]]] = {d: [] for d in domains}
    for r in filtered:
        grouped[r["_domain"]].append(r)
    for d in domains:
        grouped[d].sort(key=lambda r: int(r["_cells"]))

    svg: List[str] = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    svg.append('<rect x="0" y="0" width="100%" height="100%" fill="white"/>')
    svg.append(f'<text x="{left}" y="36" font-size="23" font-family="Arial, sans-serif" fill="#111">{html.escape(args.title)}</text>')
    svg.append(f'<text x="{left}" y="58" font-size="13" font-family="Arial, sans-serif" fill="#555">{html.escape(str(csv_path))}</text>')

    for mi, (metric_key, metric_label) in enumerate(metrics):
        panel_top = top + mi * (panel_h + panel_gap)
        panel_bottom = panel_top + panel_h

        metric_vals: List[float] = []
        for r in filtered:
            v = metric_value(r, metric_key)
            if v is not None:
                metric_vals.append(v)
        y_max = max(metric_vals) if metric_vals else 1.0
        if y_max <= 0:
            y_max = 1.0
        y_max *= 1.1

        # Grid
        y_ticks = 4
        for i in range(y_ticks + 1):
            frac = i / y_ticks
            y = panel_bottom - frac * panel_h
            val = frac * y_max
            svg.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left+chart_w}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1"/>')
            fmt = f"{val:.0f}" if metric_key == "action_set_size" else f"{val:.2f}"
            svg.append(f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{fmt}</text>')

        # Axes
        svg.append(f'<line x1="{left}" y1="{panel_top}" x2="{left}" y2="{panel_bottom}" stroke="#111" stroke-width="1.4"/>')
        svg.append(f'<line x1="{left}" y1="{panel_bottom}" x2="{left+chart_w}" y2="{panel_bottom}" stroke="#111" stroke-width="1.4"/>')
        svg.append(f'<text x="{left}" y="{panel_top-10}" font-size="13" font-family="Arial, sans-serif" fill="#111">{html.escape(metric_label)}</text>')

        # Domain lines + points
        for domain in domains:
            series = grouped[domain]
            pts: List[tuple[float, float]] = []
            for r in series:
                v = metric_value(r, metric_key)
                if v is None:
                    continue
                cx = x_pos(int(r["_cells"]), min_cells, max_cells, left, chart_w)
                cy = panel_bottom - (v / y_max) * panel_h
                pts.append((cx, cy))
            if len(pts) >= 2:
                poly = " ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
                svg.append(f'<polyline points="{poly}" fill="none" stroke="{d_color[domain]}" stroke-width="1.8" opacity="0.9"/>')

            for r in series:
                v = metric_value(r, metric_key)
                if v is None:
                    continue
                cx = x_pos(int(r["_cells"]), min_cells, max_cells, left, chart_w)
                cy = panel_bottom - (v / y_max) * panel_h
                shape = "circle" if r["_kind"] == "plus" else "square"
                marker = marker_svg(shape, cx, cy, 4.2, d_color[domain])
                tip = (
                    f"{domain} [{r['_kind']}] | cells={r['_cells']} | {metric_key}={v:.6g} | "
                    f"status={r.get('status','')}"
                )
                svg.append(f'<g><title>{html.escape(tip)}</title>{marker}</g>')

        # X ticks only on the last panel.
        if mi == len(metrics) - 1:
            tick_cells = cells_values
            if len(tick_cells) > 12:
                # Downsample labels for readability.
                step = math.ceil(len(tick_cells) / 12)
                tick_cells = [tick_cells[i] for i in range(0, len(tick_cells), step)]
                if tick_cells[-1] != cells_values[-1]:
                    tick_cells.append(cells_values[-1])

            for c in tick_cells:
                cx = x_pos(c, min_cells, max_cells, left, chart_w)
                svg.append(f'<line x1="{cx:.2f}" y1="{panel_bottom}" x2="{cx:.2f}" y2="{panel_bottom+6}" stroke="#111" stroke-width="1"/>')
                svg.append(f'<text x="{cx:.2f}" y="{panel_bottom+22}" text-anchor="middle" font-size="11" font-family="Arial, sans-serif" fill="#111">{c}</text>')
            svg.append(f'<text x="{left + chart_w/2:.2f}" y="{panel_bottom+48}" text-anchor="middle" font-size="13" font-family="Arial, sans-serif" fill="#111">Cells (rows × cols)</text>')

    # Legend
    legend_x = left + chart_w + 26
    legend_y = top + 10
    svg.append(f'<text x="{legend_x}" y="{legend_y}" font-size="15" font-family="Arial, sans-serif" fill="#111">Domains</text>')
    cursor = legend_y + 22
    for domain in domains:
        color = d_color[domain]
        svg.append(f'<line x1="{legend_x}" y1="{cursor-4}" x2="{legend_x+16}" y2="{cursor-4}" stroke="{color}" stroke-width="2"/>')
        svg.append(marker_svg("circle", legend_x + 8, cursor - 4, 3.4, color))
        svg.append(f'<text x="{legend_x+24}" y="{cursor}" font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(domain)}</text>')
        cursor += 18

    cursor += 8
    svg.append(f'<text x="{legend_x}" y="{cursor}" font-size="15" font-family="Arial, sans-serif" fill="#111">Marker</text>')
    cursor += 20
    svg.append(marker_svg("circle", legend_x + 8, cursor - 4, 4.0, "#666"))
    svg.append(f'<text x="{legend_x+24}" y="{cursor}" font-size="12" font-family="Arial, sans-serif" fill="#111">plus</text>')
    cursor += 18
    svg.append(marker_svg("square", legend_x + 8, cursor - 4, 4.0, "#666"))
    svg.append(f'<text x="{legend_x+24}" y="{cursor}" font-size="12" font-family="Arial, sans-serif" fill="#111">classic</text>')

    svg.append("</svg>")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(f"[OK] Wrote plot: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
