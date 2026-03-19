#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


def benchmarking_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_latest_csv() -> Path:
    results_root = benchmarking_root() / "results"
    candidates: List[Path] = []
    for pattern in ("*/plus_sweep.csv", "*/classic_sweep.csv", "*/*.csv"):
        candidates.extend([p for p in results_root.glob(pattern) if p.is_file()])
        if candidates:
            break
    candidates = sorted(set(candidates), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No benchmark CSV found in {results_root}")
    return candidates[0]


def safe_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def marker_svg(
    shape: str,
    x: float,
    y: float,
    size: float,
    fill: str,
    stroke: str,
    stroke_width: float = 1.2,
) -> str:
    if shape == "square":
        h = size
        return f'<rect x="{x-h}" y="{y-h}" width="{2*h}" height="{2*h}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    if shape == "triangle":
        h = size * 1.2
        points = f"{x},{y-h} {x-h},{y+h} {x+h},{y+h}"
        return f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    if shape == "diamond":
        h = size * 1.2
        points = f"{x},{y-h} {x-h},{y} {x},{y+h} {x+h},{y}"
        return f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    if shape == "cross":
        h = size * 1.1
        return (
            f'<line x1="{x-h}" y1="{y-h}" x2="{x+h}" y2="{y+h}" stroke="{stroke}" stroke-width="{max(1.6, stroke_width)}"/>'
            f'<line x1="{x-h}" y1="{y+h}" x2="{x+h}" y2="{y-h}" stroke="{stroke}" stroke-width="{max(1.6, stroke_width)}"/>'
        )
    return f'<circle cx="{x}" cy="{y}" r="{size}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'


def choose_out_path(csv_path: Path, explicit: Path | None) -> Path:
    if explicit:
        return explicit.resolve()
    return csv_path.with_suffix(".runtime.svg")


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = [r for r in reader]
    if not rows:
        raise ValueError(f"CSV has no data rows: {csv_path}")
    return rows


def problem_name(row: Dict[str, str]) -> str:
    raw = row.get("input_problem", "").strip()
    if not raw:
        return "unknown"
    return Path(raw).stem


def domain_name(row: Dict[str, str]) -> str:
    raw = row.get("domain", "").strip()
    if not raw:
        return "unknown"
    return Path(raw).stem


def distinct(values: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Plot runtime from ENHSP benchmark CSV as SVG (x=problem, y=runtime, fill=h, marker=s, outline=domain)."
    )
    ap.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Benchmark CSV path. Defaults to latest CSV in tools/benchmarking/results/*/.",
    )
    ap.add_argument("--out", type=Path, default=None, help="Output SVG path. Default: <csv>.runtime.svg")
    ap.add_argument("--title", default="ENHSP Runtime Sweep", help="Chart title.")
    ap.add_argument(
        "--x-axis",
        choices=["problem", "domain_problem"],
        default="problem",
        help="X-axis grouping key (default: problem).",
    )
    ap.add_argument(
        "--include-failures",
        action="store_true",
        help="Include timeout/error rows in the plot. By default they are excluded.",
    )
    args = ap.parse_args()

    csv_path = args.csv.resolve() if args.csv else find_latest_csv()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    out_path = choose_out_path(csv_path, args.out)

    rows = load_rows(csv_path)
    if not args.include_failures:
        rows = [r for r in rows if r.get("status", "").strip().lower() not in {"timeout", "error"}]
        if not rows:
            raise ValueError(
                "No rows left after filtering timeout/error. "
                "Use --include-failures to plot all rows."
            )
    for r in rows:
        r["_problem"] = problem_name(r)
        r["_domain"] = domain_name(r)
        r["_time"] = str(safe_float(r.get("time_sec", "0")))
        r["_x"] = r["_problem"] if args.x_axis == "problem" else f"{r['_domain']}::{r['_problem']}"

    problems = distinct([r["_x"] for r in rows])
    domains = sorted(distinct([r["_domain"] for r in rows]))
    heuristics = sorted(distinct([r.get("heuristic", "unknown") for r in rows]))
    searches = sorted(distinct([r.get("search", "unknown") for r in rows]))

    if not problems:
        raise ValueError(f"No problems found in {csv_path}")

    width = max(980, 180 + 140 * len(problems))
    height = 700
    left = 90
    right = 340
    top = 70
    bottom = 170
    chart_w = width - left - right
    chart_h = height - top - bottom

    y_max = max(safe_float(r["_time"]) for r in rows)
    if y_max <= 0:
        y_max = 1.0
    y_max = math.ceil(y_max * 1.1)

    x_step = chart_w / max(1, len(problems))
    x_centers = {p: left + (i + 0.5) * x_step for i, p in enumerate(problems)}

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
    h_color = {h: palette[i % len(palette)] for i, h in enumerate(heuristics)}
    d_color = {d: palette[i % len(palette)] for i, d in enumerate(domains)}

    marker_order = ["circle", "square", "triangle", "diamond", "cross"]
    s_marker = {s: marker_order[i % len(marker_order)] for i, s in enumerate(searches)}

    per_problem: Dict[str, List[Dict[str, str]]] = {p: [] for p in problems}
    for r in rows:
        per_problem[r["_x"]].append(r)

    svg: List[str] = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    svg.append('<rect x="0" y="0" width="100%" height="100%" fill="white"/>')
    svg.append(f'<text x="{left}" y="36" font-size="22" font-family="Arial, sans-serif" fill="#111">{html.escape(args.title)}</text>')
    svg.append(f'<text x="{left}" y="58" font-size="13" font-family="Arial, sans-serif" fill="#555">{html.escape(str(csv_path))}</text>')

    # Grid + y-axis ticks
    y_ticks = 6
    for i in range(y_ticks + 1):
        frac = i / y_ticks
        y = top + chart_h - frac * chart_h
        val = frac * y_max
        svg.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left+chart_w}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1"/>')
        svg.append(f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" font-size="12" font-family="Arial, sans-serif" fill="#444">{val:.0f}</text>')

    # Axes
    svg.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+chart_h}" stroke="#111" stroke-width="1.5"/>')
    svg.append(f'<line x1="{left}" y1="{top+chart_h}" x2="{left+chart_w}" y2="{top+chart_h}" stroke="#111" stroke-width="1.5"/>')
    svg.append(f'<text x="{left-60}" y="{top + chart_h/2}" transform="rotate(-90 {left-60} {top + chart_h/2})" font-size="14" font-family="Arial, sans-serif" fill="#111">Runtime (sec)</text>')
    x_label = "Problem" if args.x_axis == "problem" else "Domain::Problem"
    svg.append(f'<text x="{left + chart_w/2}" y="{top + chart_h + 130}" text-anchor="middle" font-size="14" font-family="Arial, sans-serif" fill="#111">{x_label}</text>')

    # X ticks + labels
    for p in problems:
        x = x_centers[p]
        svg.append(f'<line x1="{x:.2f}" y1="{top+chart_h}" x2="{x:.2f}" y2="{top+chart_h+6}" stroke="#111" stroke-width="1"/>')
        svg.append(
            f'<text x="{x:.2f}" y="{top+chart_h+22}" transform="rotate(28 {x:.2f} {top+chart_h+22})" '
            f'text-anchor="start" font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(p)}</text>'
        )

    # Points
    for p in problems:
        items = per_problem[p]
        n = len(items)
        jitter_span = min(0.65 * x_step, 60)
        for idx, r in enumerate(items):
            x = x_centers[p]
            if n > 1:
                offset = (idx - (n - 1) / 2.0) * (jitter_span / (n - 1))
                x += offset
            t = safe_float(r["_time"])
            y = top + chart_h - (t / y_max) * chart_h
            heuristic = r.get("heuristic", "unknown")
            search = r.get("search", "unknown")
            status = r.get("status", "unknown")
            domain = r.get("_domain", "unknown")
            fill = h_color.get(heuristic, "#666")
            stroke = d_color.get(domain, "#222")
            shape = s_marker.get(search, "circle")
            marker = marker_svg(shape, x, y, 5.5, fill, stroke, stroke_width=1.4)
            tip = f"{domain} | {r['_problem']} | h={heuristic} | s={search} | status={status} | time={t:.3f}s"
            svg.append(f'<g><title>{html.escape(tip)}</title>{marker}</g>')

    # Legends
    legend_x = left + chart_w + 30
    legend_y = top + 20
    svg.append(f'<text x="{legend_x}" y="{legend_y}" font-size="15" font-family="Arial, sans-serif" fill="#111">Heuristic (color)</text>')
    y_cursor = legend_y + 22
    for h in heuristics:
        svg.append(marker_svg("circle", legend_x + 8, y_cursor - 5, 5.2, h_color[h], "#222"))
        svg.append(f'<text x="{legend_x + 22}" y="{y_cursor}" font-size="13" font-family="Arial, sans-serif" fill="#111">{html.escape(h)}</text>')
        y_cursor += 20

    y_cursor += 14
    svg.append(f'<text x="{legend_x}" y="{y_cursor}" font-size="15" font-family="Arial, sans-serif" fill="#111">Search (marker)</text>')
    y_cursor += 22
    for s in searches:
        svg.append(marker_svg(s_marker[s], legend_x + 8, y_cursor - 5, 5.2, "#f8fafc", "#111"))
        svg.append(f'<text x="{legend_x + 22}" y="{y_cursor}" font-size="13" font-family="Arial, sans-serif" fill="#111">{html.escape(s)}</text>')
        y_cursor += 20

    if len(domains) > 1:
        y_cursor += 14
        svg.append(f'<text x="{legend_x}" y="{y_cursor}" font-size="15" font-family="Arial, sans-serif" fill="#111">Domain (outline)</text>')
        y_cursor += 22
        for d in domains:
            svg.append(marker_svg("circle", legend_x + 8, y_cursor - 5, 5.2, "#ffffff", d_color[d], stroke_width=1.8))
            svg.append(f'<text x="{legend_x + 22}" y="{y_cursor}" font-size="13" font-family="Arial, sans-serif" fill="#111">{html.escape(d)}</text>')
            y_cursor += 20

    svg.append("</svg>")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(f"[OK] Wrote runtime plot: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
