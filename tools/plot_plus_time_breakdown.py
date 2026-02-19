#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_latest_results_dir() -> Path:
    base = repo_root() / "results" / "plus-bench"
    runs = [p for p in base.glob("run_*") if p.is_dir()]
    if not runs:
        raise FileNotFoundError(f"No run_* folders found under {base}")
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return runs[0]


@dataclass
class TimeRow:
    label: str
    domain: str
    problem: str
    heuristic: str
    search: str
    grounding_sec: float
    planning_sec: float
    heuristic_sec: float
    search_sec: float
    source_file: str


def parse_ms(text: str, pattern: str) -> float:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return 0.0
    try:
        return float(m.group(1)) / 1000.0
    except Exception:
        return 0.0


def parse_stdout_file(path: Path) -> Optional[TimeRow]:
    txt = path.read_text(encoding="utf-8", errors="replace")

    grounding = parse_ms(txt, r"Grounding Time:\s*([0-9]+(?:\.[0-9]+)?)")
    planning = parse_ms(txt, r"Planning Time\s*\(msec\):\s*([0-9]+(?:\.[0-9]+)?)")
    heuristic = parse_ms(txt, r"Heuristic Time\s*\(msec\):\s*([0-9]+(?:\.[0-9]+)?)")
    search = parse_ms(txt, r"Search Time\s*\(msec\):\s*([0-9]+(?:\.[0-9]+)?)")

    if grounding == 0.0 and planning == 0.0 and heuristic == 0.0 and search == 0.0:
        return None

    # plus-enhsp-bench-d_<domain>-p_<problem>-h_<h>-s_<s>.stdout.txt
    m = re.match(
        r"^plus-enhsp-bench-d_(.+)-p_(.+)-h_(.+)-s_(.+)\.stdout\.txt$",
        path.name,
    )
    if m:
        domain, problem, h, s = m.groups()
    else:
        domain, problem, h, s = "unknown", path.stem, "unknown", "unknown"

    label = f"{problem}|{h}|{s}" if domain == "unknown" else f"{domain}:{problem}|{h}|{s}"
    return TimeRow(
        label=label,
        domain=domain,
        problem=problem,
        heuristic=h,
        search=s,
        grounding_sec=grounding,
        planning_sec=planning,
        heuristic_sec=heuristic,
        search_sec=search,
        source_file=str(path),
    )


def marker_rect(x: float, y: float, w: float, h: float, fill: str) -> str:
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}"/>'


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Plot stacked ENHSP timing breakdown from benchmark stdout files."
    )
    ap.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Directory containing plus benchmark *.stdout.txt files. Default: latest results/plus-bench/run_*/",
    )
    ap.add_argument(
        "--pattern",
        default="*.stdout.txt",
        help="Glob pattern for stdout files inside --results-dir (default: *.stdout.txt)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output SVG path. Default: <results-dir>/time_breakdown.svg",
    )
    ap.add_argument(
        "--title",
        default="ENHSP Time Breakdown (Stacked)",
        help="Chart title",
    )
    args = ap.parse_args()

    results_dir = args.results_dir.resolve() if args.results_dir else find_latest_results_dir()
    if not results_dir.exists():
        raise FileNotFoundError(f"Results dir not found: {results_dir}")

    files = sorted([p for p in results_dir.glob(args.pattern) if p.is_file()])
    if not files:
        raise FileNotFoundError(f"No files matched {args.pattern!r} in {results_dir}")

    rows: List[TimeRow] = []
    for f in files:
        parsed = parse_stdout_file(f)
        if parsed:
            rows.append(parsed)

    if not rows:
        raise ValueError("No timing rows parsed from stdout files.")

    # Grouped labels shorter when only one domain is present.
    domains = sorted({r.domain for r in rows})
    if len(domains) == 1:
        for r in rows:
            r.label = f"{r.problem}|{r.heuristic}|{r.search}"

    n = len(rows)
    width = max(1100, 200 + 75 * n)
    height = 760
    left = 90
    right = 320
    top = 80
    bottom = 260
    chart_w = width - left - right
    chart_h = height - top - bottom

    stack_totals = [
        r.grounding_sec + r.planning_sec + r.heuristic_sec + r.search_sec for r in rows
    ]
    y_max = max(stack_totals) if stack_totals else 1.0
    if y_max <= 0:
        y_max = 1.0
    y_max = math.ceil(y_max * 1.1)

    bar_step = chart_w / max(1, n)
    bar_w = min(42.0, bar_step * 0.72)

    colors = {
        "Grounding Time": "#4e79a7",
        "Planning Time": "#f28e2b",
        "Heuristic Time": "#59a14f",
        "Search Time": "#e15759",
    }

    svg: List[str] = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    svg.append('<rect x="0" y="0" width="100%" height="100%" fill="white"/>')
    svg.append(f'<text x="{left}" y="36" font-size="22" font-family="Arial, sans-serif" fill="#111">{html.escape(args.title)}</text>')
    svg.append(f'<text x="{left}" y="58" font-size="13" font-family="Arial, sans-serif" fill="#555">{html.escape(str(results_dir))}</text>')

    # Grid + y ticks
    y_ticks = 6
    for i in range(y_ticks + 1):
        frac = i / y_ticks
        y = top + chart_h - frac * chart_h
        val = frac * y_max
        svg.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left+chart_w}" y2="{y:.2f}" stroke="#e5e7eb" stroke-width="1"/>')
        svg.append(f'<text x="{left-10}" y="{y+4:.2f}" text-anchor="end" font-size="12" font-family="Arial, sans-serif" fill="#444">{val:.1f}</text>')

    svg.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+chart_h}" stroke="#111" stroke-width="1.5"/>')
    svg.append(f'<line x1="{left}" y1="{top+chart_h}" x2="{left+chart_w}" y2="{top+chart_h}" stroke="#111" stroke-width="1.5"/>')
    svg.append(f'<text x="{left-62}" y="{top + chart_h/2}" transform="rotate(-90 {left-62} {top + chart_h/2})" font-size="14" font-family="Arial, sans-serif" fill="#111">Time (sec, stacked)</text>')
    svg.append(f'<text x="{left + chart_w/2}" y="{top + chart_h + 185}" text-anchor="middle" font-size="14" font-family="Arial, sans-serif" fill="#111">Run (problem|h|s)</text>')

    for i, r in enumerate(rows):
        cx = left + (i + 0.5) * bar_step
        x = cx - bar_w / 2.0

        v_ground = r.grounding_sec
        v_plan = r.planning_sec
        v_heur = r.heuristic_sec
        v_search = r.search_sec
        segments = [
            ("Grounding Time", v_ground),
            ("Planning Time", v_plan),
            ("Heuristic Time", v_heur),
            ("Search Time", v_search),
        ]

        cum = 0.0
        for name, val in segments:
            if val <= 0:
                continue
            y_top = top + chart_h - ((cum + val) / y_max) * chart_h
            h_px = (val / y_max) * chart_h
            svg.append(marker_rect(x, y_top, bar_w, h_px, colors[name]))
            cum += val

        tip = (
            f"{r.label} | ground={v_ground:.3f}s "
            f"plan={v_plan:.3f}s heur={v_heur:.3f}s search={v_search:.3f}s"
        )
        svg.append(f'<title>{html.escape(tip)}</title>')

        svg.append(f'<line x1="{cx:.2f}" y1="{top+chart_h}" x2="{cx:.2f}" y2="{top+chart_h+6}" stroke="#111" stroke-width="1"/>')
        svg.append(
            f'<text x="{cx:.2f}" y="{top+chart_h+22}" transform="rotate(58 {cx:.2f} {top+chart_h+22})" '
            f'text-anchor="start" font-size="11" font-family="Arial, sans-serif" fill="#111">{html.escape(r.label)}</text>'
        )

    # Legend
    lx = left + chart_w + 28
    ly = top + 30
    svg.append(f'<text x="{lx}" y="{ly}" font-size="15" font-family="Arial, sans-serif" fill="#111">Stack Segments</text>')
    y_cursor = ly + 22
    for key in ["Grounding Time", "Planning Time", "Heuristic Time", "Search Time"]:
        svg.append(marker_rect(lx, y_cursor - 11, 14, 14, colors[key]))
        svg.append(f'<text x="{lx + 22}" y="{y_cursor}" font-size="13" font-family="Arial, sans-serif" fill="#111">{html.escape(key)}</text>')
        y_cursor += 22

    svg.append(
        f'<text x="{lx}" y="{y_cursor + 18}" font-size="11" font-family="Arial, sans-serif" fill="#666">'
        "Note: ENHSP 'Planning Time' may overlap with heuristic/search totals."
        "</text>"
    )

    svg.append("</svg>")

    out_path = args.out.resolve() if args.out else (results_dir / "time_breakdown.svg")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(svg) + "\n", encoding="utf-8")
    print(f"[OK] Wrote stacked timing chart: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
