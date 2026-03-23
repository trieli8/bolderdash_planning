#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


def safe_float(value: str) -> Optional[float]:
    v = (value or "").strip()
    if not v:
        return None
    v = v.replace(",", "")
    try:
        return float(v)
    except Exception:
        return None


def safe_int(value: str) -> Optional[int]:
    f = safe_float(value)
    if f is None:
        return None
    try:
        return int(round(f))
    except Exception:
        return None


def percentile(sorted_values: Sequence[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_values[lo]
    frac = pos - lo
    return sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac


def nice_max(value: float) -> float:
    if value <= 0:
        return 1.0
    exponent = math.floor(math.log10(value))
    frac = value / (10 ** exponent)
    if frac <= 1:
        nice = 1
    elif frac <= 2:
        nice = 2
    elif frac <= 5:
        nice = 5
    else:
        nice = 10
    return nice * (10 ** exponent)


def lin_map(v: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if src_max <= src_min:
        return (dst_min + dst_max) / 2.0
    frac = (v - src_min) / (src_max - src_min)
    return dst_min + frac * (dst_max - dst_min)


def log_map(v: float, src_min: float, src_max: float, dst_min: float, dst_max: float) -> float:
    if v <= 0 or src_min <= 0 or src_max <= 0:
        return (dst_min + dst_max) / 2.0
    log_min = math.log10(src_min)
    log_max = math.log10(src_max)
    if log_max <= log_min:
        return (dst_min + dst_max) / 2.0
    frac = (math.log10(v) - log_min) / (log_max - log_min)
    return dst_min + frac * (dst_max - dst_min)


def power_of_ten_ticks(min_value: float, max_value: float) -> List[float]:
    if min_value <= 0 or max_value <= 0:
        return []
    lo = int(math.floor(math.log10(min_value)))
    hi = int(math.ceil(math.log10(max_value)))
    return [10.0 ** exponent for exponent in range(lo, hi + 1)]


def format_log_tick(value: float) -> str:
    if value <= 0:
        return "0"
    if value >= 1000 and abs(value - round(value)) <= 1e-9:
        return f"{int(round(value))}"
    if value >= 1:
        return f"{value:g}"
    return f"{value:.3g}"


def color_palette() -> List[str]:
    return [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
        "#4e79a7",
        "#f28e2b",
        "#59a14f",
        "#e15759",
        "#76b7b2",
        "#edc948",
    ]


def color_for_categories(cats: Sequence[str]) -> Dict[str, str]:
    pal = color_palette()
    mapping: Dict[str, str] = {}
    for idx, cat in enumerate(cats):
        mapping[cat] = pal[idx % len(pal)]
    return mapping


DOMAIN_FAMILY_ORDER = ("classic", "fa", "plus")
DOMAIN_SCANNER_ORDER = ("non-scanner", "scanner")
DOMAIN_LAYOUT_ORDER = ("combined", "separated")
DOMAIN_VARIANT_ORDER = tuple(
    f"{scanner}|{layout}"
    for scanner in DOMAIN_SCANNER_ORDER
    for layout in DOMAIN_LAYOUT_ORDER
)
DOMAIN_FAMILY_COMPARE_COLORS = {
    "classic": "#4e79a7",
    "fa": "#f28e2b",
    "plus": "#59a14f",
}
DOMAIN_VARIANT_RE = re.compile(
    r"^domain_(?:(classic|fa|plus)_)?(scanner|non-scanner)_(combined|separated)"
    r"(?:_(actions|events(?:_fluents)?))?$",
    flags=re.IGNORECASE,
)


def normalize_domain_family(value: str) -> str:
    lowered = (value or "").strip().lower()
    if lowered in {"classic", "pddl"}:
        return "classic"
    if lowered == "fa":
        return "fa"
    if lowered in {"plus", "pddl+", "pddlplus"}:
        return "plus"
    return lowered or "unknown"


def domain_family_compare_label(family: str) -> str:
    fam = normalize_domain_family(family)
    if fam == "classic":
        return "PDDL"
    if fam == "fa":
        return "FA"
    if fam == "plus":
        return "PLUS"
    return fam or "Unknown"


def domain_scanner_label(scanner: str) -> str:
    value = (scanner or "").strip().lower()
    if value == "non-scanner":
        return "Non-scanner"
    if value == "scanner":
        return "Scanner"
    return value or "Unknown"


def domain_layout_label(layout: str) -> str:
    value = (layout or "").strip().lower()
    if value == "combined":
        return "Combined"
    if value == "separated":
        return "Separated"
    return value or "Unknown"


def domain_variant_key(scanner: str, layout: str) -> str:
    scanner_value = (scanner or "").strip().lower()
    layout_value = (layout or "").strip().lower()
    if scanner_value not in DOMAIN_SCANNER_ORDER or layout_value not in DOMAIN_LAYOUT_ORDER:
        return "unknown"
    return f"{scanner_value}|{layout_value}"


def domain_variant_label(variant: str) -> str:
    value = (variant or "").strip().lower()
    if "|" not in value:
        return value or "Unknown"
    scanner, layout = value.split("|", 1)
    return f"{domain_scanner_label(scanner)} / {domain_layout_label(layout)}"


def domain_compare_label(domain: str) -> str:
    family, scanner, layout, encoding = parse_domain_variant(domain)
    if family == "unknown" or scanner == "unknown" or layout == "unknown":
        return domain or "Unknown"
    parts = [
        domain_family_compare_label(family),
        domain_scanner_label(scanner),
        domain_layout_label(layout),
    ]
    if encoding not in {"", "plain"}:
        parts.append(encoding.replace("_", " ").title())
    return " / ".join(parts)


def parse_domain_variant(domain_stem: str) -> Tuple[str, str, str, str]:
    match = DOMAIN_VARIANT_RE.match((domain_stem or "").strip())
    if not match:
        return "unknown", "unknown", "unknown", "unknown"
    family = normalize_domain_family(match.group(1) or "classic")
    scanner = ((match.group(2) or "").strip().lower() or "unknown")
    layout = ((match.group(3) or "").strip().lower() or "unknown")
    encoding = ((match.group(4) or "").strip().lower() or "plain")
    if scanner not in DOMAIN_SCANNER_ORDER:
        scanner = "unknown"
    if layout not in DOMAIN_LAYOUT_ORDER:
        layout = "unknown"
    return family, scanner, layout, encoding


def ordered_present_categories(
    rows: Sequence[Dict[str, str]],
    key: str,
    preferred: Sequence[str],
) -> List[str]:
    preferred_set = set(preferred)
    present = set()
    for row in rows:
        value = (row.get(key, "") or "").strip().lower()
        if not value or value == "unknown":
            continue
        present.add(value)
    ordered = [value for value in preferred if value in present]
    ordered.extend(sorted(value for value in present if value not in preferred_set))
    return ordered


def domain_family_compare_colors(families: Sequence[str]) -> Dict[str, str]:
    colors = color_for_categories(families)
    for family, color in DOMAIN_FAMILY_COMPARE_COLORS.items():
        if family in colors:
            colors[family] = color
    return colors


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader]
    if not rows:
        raise ValueError(f"CSV has no rows: {csv_path}")
    return rows


def annotate_row(row: Dict[str, str]) -> None:
    row["_setting"] = row.get("planner_setting", "") or "unknown"
    row["_family"] = (row.get("planner_family", "") or "").strip().lower() or "unknown"
    row["_domain"] = Path(row.get("domain", "")).stem or "unknown"
    row["_map"] = Path(row.get("level", "")).stem or "unknown"
    row["_status"] = (row.get("status", "") or "").strip().lower()
    row["_phase"] = (row.get("phase", "") or "").strip().lower()
    row["_runtime"] = str(safe_float(row.get("measured_total_sec", "")) or 0.0)
    row["_cells"] = str(safe_int(row.get("cells", "")) or 0)
    row["_run_id"] = str(safe_int(row.get("run_id", "")) or 0)
    parsed_family, scanner_mode, layout_mode, encoding = parse_domain_variant(row["_domain"])
    domain_kind = normalize_domain_family(row.get("domain_kind", ""))
    if domain_kind != "unknown":
        parsed_family = domain_kind
    elif parsed_family == "unknown":
        parsed_family = normalize_domain_family(row.get("planner_family", ""))
    row["_domain_family"] = parsed_family
    row["_domain_scanner"] = scanner_mode
    row["_domain_layout"] = layout_mode
    row["_domain_variant"] = domain_variant_key(scanner_mode, layout_mode)
    row["_domain_encoding"] = encoding


def svg_start(width: int, height: int, title: str, subtitle: str) -> List[str]:
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect x="0" y="0" width="100%" height="100%" fill="white"/>',
        f'<text x="24" y="32" font-size="22" font-family="Arial, sans-serif" fill="#111">{html.escape(title)}</text>',
        f'<text x="24" y="52" font-size="12" font-family="Arial, sans-serif" fill="#555">{html.escape(subtitle)}</text>',
    ]
    return out


def svg_finish(lines: List[str], out_path: Path) -> None:
    lines.append("</svg>")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_no_data_plot(out_path: Path, title: str, subtitle: str, message: str = "No data for this section.") -> None:
    width = 980
    height = 260
    lines = svg_start(width, height, title, subtitle)
    lines.append(
        f'<text x="24" y="120" font-size="16" font-family="Arial, sans-serif" fill="#444">{html.escape(message)}</text>'
    )
    svg_finish(lines, out_path)


def draw_legend(
    lines: List[str],
    *,
    items: Sequence[Tuple[str, str]],
    x: float,
    y: float,
    title: str,
    marker: str = "rect",
) -> None:
    lines.append(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" font-family="Arial, sans-serif" fill="#111">{html.escape(title)}</text>'
    )
    cy = y + 18
    for label, color in items:
        if marker == "circle":
            lines.append(
                f'<circle cx="{x+7:.1f}" cy="{cy-4:.1f}" r="5" fill="{color}" stroke="#111" stroke-width="1"/>'
            )
        else:
            lines.append(
                f'<rect x="{x:.1f}" y="{cy-10:.1f}" width="12" height="12" fill="{color}" stroke="#111" stroke-width="1"/>'
            )
        lines.append(
            f'<text x="{x+18:.1f}" y="{cy:.1f}" font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(label)}</text>'
        )
        cy += 16


def family_label(family: str) -> str:
    fam = (family or "").strip().lower()
    if fam == "fa":
        return "FA"
    if fam == "plus":
        return "PDDL+"
    if fam == "classic":
        return "Classic"
    return fam or "Unknown"


def draw_family_shape_legend(
    lines: List[str],
    *,
    families: Sequence[str],
    x: float,
    y: float,
) -> None:
    if not families:
        return
    lines.append(
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="13" font-family="Arial, sans-serif" fill="#111">Family (dot shape)</text>'
    )
    cy = y + 18
    for fam in families:
        draw_point_marker(
            lines,
            x=x + 7,
            y=cy - 4,
            marker=marker_for_family(fam),
            size=5.0,
            fill="#666",
            stroke="#111",
            stroke_width=0.9,
        )
        lines.append(
            f'<text x="{x+18:.1f}" y="{cy:.1f}" font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(family_label(fam))}</text>'
        )
        cy += 16


def family_by_setting(rows: Sequence[Dict[str, str]]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for r in rows:
        setting = r.get("_setting", "") or "unknown"
        family = (r.get("_family", "") or "unknown").strip().lower() or "unknown"
        if setting not in mapping:
            mapping[setting] = family
    return mapping


def is_attempt_status(status: str) -> bool:
    return status not in {"dry-run", "skipped_after_timeout", ""}


def include_line_scatter_point(status: str) -> bool:
    s = (status or "").strip().lower()
    return s not in {"timeout", "error"}


def marker_for_family(family: str) -> str:
    fam = (family or "").strip().lower()
    if fam == "classic":
        return "circle"
    if fam == "fa":
        return "square"
    if fam == "plus":
        return "diamond"
    return "triangle"


def draw_point_marker(
    lines: List[str],
    *,
    x: float,
    y: float,
    marker: str,
    size: float,
    fill: str,
    stroke: str = "#111",
    stroke_width: float = 0.8,
    fill_opacity: Optional[float] = None,
) -> None:
    style = f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width:.2f}"'
    if fill_opacity is not None:
        style += f' fill-opacity="{fill_opacity:.3f}"'
    if marker == "square":
        lines.append(
            f'<rect x="{x-size:.1f}" y="{y-size:.1f}" width="{2*size:.1f}" height="{2*size:.1f}" {style}/>'
        )
        return
    if marker == "diamond":
        points = [
            (x, y - size),
            (x + size, y),
            (x, y + size),
            (x - size, y),
        ]
        lines.append(
            f'<polygon points="{" ".join(f"{px:.1f},{py:.1f}" for px, py in points)}" {style}/>'
        )
        return
    if marker == "triangle":
        h = size * 1.15
        points = [
            (x, y - h),
            (x + size, y + size * 0.8),
            (x - size, y + size * 0.8),
        ]
        lines.append(
            f'<polygon points="{" ".join(f"{px:.1f},{py:.1f}" for px, py in points)}" {style}/>'
        )
        return
    lines.append(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size:.1f}" {style}/>'
    )


def lerp_channel(a: int, b: int, t: float) -> int:
    t = max(0.0, min(1.0, t))
    return int(round(a + (b - a) * t))


def red_yellow_green(rate: float) -> str:
    # 0.0 -> red, 0.5 -> yellow, 1.0 -> green
    rate = max(0.0, min(1.0, rate))
    if rate <= 0.5:
        t = rate / 0.5
        r = lerp_channel(220, 242, t)
        g = lerp_channel(70, 197, t)
        b = lerp_channel(70, 66, t)
    else:
        t = (rate - 0.5) / 0.5
        r = lerp_channel(242, 46, t)
        g = lerp_channel(197, 159, t)
        b = lerp_channel(66, 85, t)
    return f"rgb({r},{g},{b})"


def plot_status_by_setting(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    status_order = ["solved", "no-path", "timeout", "error", "unsolved", "dry-run", "skipped_after_timeout"]
    other_status = sorted(set(r["_status"] for r in rows if r["_status"] not in status_order))
    statuses = status_order + other_status
    statuses = [s for s in statuses if any(r["_status"] == s for r in rows)]
    status_colors = color_for_categories(statuses)

    width = max(1150, 260 + 110 * len(settings))
    height = 620
    left = 80
    top = 90
    right = 320
    bottom = 200
    cw = width - left - right
    ch = height - top - bottom

    counts: Dict[str, Dict[str, int]] = {s: {st: 0 for st in statuses} for s in settings}
    max_total = 1
    for r in rows:
        counts[r["_setting"]][r["_status"]] += 1
    for s in settings:
        total = sum(counts[s].values())
        max_total = max(max_total, total)
    y_max = max_total
    y_step = max(1, int(math.ceil(y_max / 6)))
    y_max = int(math.ceil(y_max / y_step) * y_step)

    lines = svg_start(width, height, "Status Counts By Setting", subtitle)
    for i in range(7):
        v = (y_max / 6.0) * i
        y = top + ch - (v / y_max) * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{int(round(v))}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')

    bar_step = cw / max(1, len(settings))
    bar_w = min(56.0, bar_step * 0.68)
    for i, setting in enumerate(settings):
        x = left + (i + 0.5) * bar_step - bar_w / 2.0
        cum = 0
        for st in statuses:
            v = counts[setting][st]
            if v <= 0:
                continue
            y_top = top + ch - ((cum + v) / y_max) * ch
            h = (v / y_max) * ch
            lines.append(
                f'<rect x="{x:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" height="{h:.1f}" '
                f'fill="{status_colors[st]}" stroke="#111" stroke-width="0.6"/>'
            )
            cum += v
        cx = x + bar_w / 2.0
        lines.append(
            f'<text x="{cx:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" transform="rotate(55 {cx:.1f} {top+ch+18:.1f})" '
            f'font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(setting)}</text>'
        )

    draw_legend(
        lines,
        items=[(s, status_colors[s]) for s in statuses],
        x=left + cw + 24,
        y=top + 8,
        title="Status",
        marker="rect",
    )
    svg_finish(lines, out_path)


def plot_success_rate(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    solved = Counter()
    totals = Counter()
    for r in rows:
        totals[r["_setting"]] += 1
        if r["_status"] == "solved":
            solved[r["_setting"]] += 1

    width = max(1100, 240 + 105 * len(settings))
    height = 560
    left = 80
    top = 90
    right = 120
    bottom = 180
    cw = width - left - right
    ch = height - top - bottom
    colors = color_for_categories(settings)

    lines = svg_start(width, height, "Solve Rate By Setting", subtitle)
    for i in range(6):
        v = i * 20
        y = top + ch - (v / 100.0) * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{v}%</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')

    step = cw / max(1, len(settings))
    bw = min(56.0, step * 0.68)
    for i, s in enumerate(settings):
        rate = (100.0 * solved[s] / totals[s]) if totals[s] > 0 else 0.0
        h = (rate / 100.0) * ch
        x = left + (i + 0.5) * step - bw / 2.0
        y = top + ch - h
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{colors[s]}" stroke="#111" stroke-width="0.7"/>')
        lines.append(
            f'<text x="{x+bw/2:.1f}" y="{y-5:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#111">{rate:.1f}%</text>'
        )
        lines.append(
            f'<text x="{x+bw/2:.1f}" y="{top+ch+16:.1f}" text-anchor="middle" transform="rotate(55 {x+bw/2:.1f} {top+ch+16:.1f})" '
            f'font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(s)}</text>'
        )
    svg_finish(lines, out_path)


def plot_status_by_domain(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    domains = sorted(set(r["_domain"] for r in rows))
    status_order = ["solved", "no-path", "timeout", "error", "unsolved", "dry-run", "skipped_after_timeout"]
    statuses = [s for s in status_order if any(r["_status"] == s for r in rows)]
    extras = sorted(set(r["_status"] for r in rows if r["_status"] not in statuses))
    statuses.extend(extras)
    status_colors = color_for_categories(statuses)

    width = max(1200, 320 + 26 * len(domains))
    height = 680
    left = 90
    top = 90
    right = 320
    bottom = 150
    cw = width - left - right
    ch = height - top - bottom

    counts: Dict[str, Dict[str, int]] = {d: {s: 0 for s in statuses} for d in domains}
    max_total = 1
    for r in rows:
        counts[r["_domain"]][r["_status"]] += 1
    for d in domains:
        max_total = max(max_total, sum(counts[d].values()))
    y_max = int(math.ceil(max_total / 6) * 6) if max_total > 6 else max_total
    y_max = max(y_max, 1)

    lines = svg_start(width, height, "Status Counts By Domain", subtitle)
    for i in range(7):
        v = (y_max / 6.0) * i
        y = top + ch - (v / y_max) * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{int(round(v))}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')

    step = cw / max(1, len(domains))
    bw = min(26.0, step * 0.72)
    for i, d in enumerate(domains):
        x = left + (i + 0.5) * step - bw / 2.0
        cum = 0
        for st in statuses:
            v = counts[d][st]
            if v <= 0:
                continue
            y_top = top + ch - ((cum + v) / y_max) * ch
            h = (v / y_max) * ch
            lines.append(
                f'<rect x="{x:.1f}" y="{y_top:.1f}" width="{bw:.1f}" height="{h:.1f}" '
                f'fill="{status_colors[st]}" stroke="#111" stroke-width="0.4"/>'
            )
            cum += v
        lines.append(
            f'<text x="{x+bw/2:.1f}" y="{top+ch+16:.1f}" text-anchor="middle" transform="rotate(65 {x+bw/2:.1f} {top+ch+16:.1f})" '
            f'font-size="8.5" font-family="Arial, sans-serif" fill="#111">{html.escape(d)}</text>'
        )
    draw_legend(
        lines,
        items=[(s, status_colors[s]) for s in statuses],
        x=left + cw + 18,
        y=top + 8,
        title="Status",
        marker="rect",
    )
    svg_finish(lines, out_path)


def plot_success_rate_by_domain(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    domains = sorted(set(r["_domain"] for r in rows))
    totals = Counter()
    solved = Counter()
    for r in rows:
        if not is_attempt_status(r["_status"]):
            continue
        totals[r["_domain"]] += 1
        if r["_status"] == "solved":
            solved[r["_domain"]] += 1
    domains = [d for d in domains if totals[d] > 0]
    if not domains:
        return
    colors = color_for_categories(domains)

    width = max(1180, 320 + 26 * len(domains))
    height = 620
    left = 90
    top = 90
    right = 120
    bottom = 150
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, "Solve Rate By Domain", subtitle)
    for i in range(6):
        v = i * 20
        y = top + ch - (v / 100.0) * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{v}%</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')

    step = cw / max(1, len(domains))
    bw = min(26.0, step * 0.72)
    for i, d in enumerate(domains):
        rate = 100.0 * solved[d] / totals[d]
        h = (rate / 100.0) * ch
        x = left + (i + 0.5) * step - bw / 2.0
        y = top + ch - h
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{colors[d]}" stroke="#111" stroke-width="0.5"/>')
        lines.append(
            f'<text x="{x+bw/2:.1f}" y="{y-4:.1f}" text-anchor="middle" font-size="8.5" font-family="Arial, sans-serif" fill="#111">{rate:.0f}%</text>'
        )
        lines.append(
            f'<text x="{x+bw/2:.1f}" y="{top+ch+16:.1f}" text-anchor="middle" transform="rotate(65 {x+bw/2:.1f} {top+ch+16:.1f})" '
            f'font-size="8.5" font-family="Arial, sans-serif" fill="#111">{html.escape(d)}</text>'
        )
    svg_finish(lines, out_path)


def plot_success_rate_by_category(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
    *,
    title: str,
    category_key: str,
    category_order: Sequence[str],
    label_fn: Callable[[str], str],
) -> None:
    categories = ordered_present_categories(rows, category_key, category_order)
    totals = Counter()
    solved = Counter()
    for row in rows:
        category = (row.get(category_key, "") or "").strip().lower()
        if category not in categories or not is_attempt_status(row["_status"]):
            continue
        totals[category] += 1
        if row["_status"] == "solved":
            solved[category] += 1
    categories = [category for category in categories if totals[category] > 0]
    if not categories:
        return

    if category_key == "_domain_family":
        colors = domain_family_compare_colors(categories)
    else:
        colors = color_for_categories(categories)

    width = max(820, 240 + 140 * len(categories))
    height = 540
    left = 80
    top = 90
    right = 120
    bottom = 110
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, title, subtitle)
    for i in range(6):
        value = i * 20
        y = top + ch - (value / 100.0) * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{value}%</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')

    step = cw / max(1, len(categories))
    bar_width = min(78.0, step * 0.62)
    for i, category in enumerate(categories):
        rate = 100.0 * solved[category] / totals[category]
        height_value = (rate / 100.0) * ch
        x = left + (i + 0.5) * step - bar_width / 2.0
        y = top + ch - height_value
        lines.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{height_value:.1f}" '
            f'fill="{colors[category]}" stroke="#111" stroke-width="0.8"/>'
        )
        lines.append(
            f'<text x="{x+bar_width/2:.1f}" y="{y-6:.1f}" text-anchor="middle" font-size="10" '
            f'font-family="Arial, sans-serif" fill="#111">{rate:.1f}%</text>'
        )
        lines.append(
            f'<text x="{x+bar_width/2:.1f}" y="{top+ch+20:.1f}" text-anchor="middle" font-size="11" '
            f'font-family="Arial, sans-serif" fill="#111">{html.escape(label_fn(category))}</text>'
        )
    svg_finish(lines, out_path)


def plot_box_by_category(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
    *,
    title: str,
    category_key: str,
    category_order: Sequence[str],
    label_fn: Callable[[str], str],
    value_fn: Callable[[Dict[str, str]], Optional[float]],
    y_label: str,
) -> None:
    categories = ordered_present_categories(rows, category_key, category_order)
    grouped: Dict[str, List[float]] = {category: [] for category in categories}
    for row in rows:
        category = (row.get(category_key, "") or "").strip().lower()
        if category not in grouped:
            continue
        value = value_fn(row)
        if value is None or value < 0:
            continue
        grouped[category].append(value)
    categories = [category for category in categories if grouped[category]]
    if not categories:
        return

    ymax = max(max(values) for values in grouped.values())
    ymax = nice_max(ymax * 1.1 if ymax > 0 else 1.0)
    if category_key == "_domain_family":
        colors = domain_family_compare_colors(categories)
    else:
        colors = color_for_categories(categories)

    width = max(860, 250 + 140 * len(categories))
    height = 580
    left = 90
    top = 92
    right = 120
    bottom = 110
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, title, subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        value = frac * ymax
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{value:.1f}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left-62}" y="{top + ch/2:.1f}" transform="rotate(-90 {left-62} {top + ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(y_label)}</text>'
    )

    step = cw / max(1, len(categories))
    box_width = min(64.0, step * 0.52)
    for i, category in enumerate(categories):
        mn, q1, median, q3, mx = box_stats(grouped[category])
        cx = left + (i + 0.5) * step
        x = cx - box_width / 2.0
        y_mn = top + ch - (mn / ymax) * ch
        y_q1 = top + ch - (q1 / ymax) * ch
        y_median = top + ch - (median / ymax) * ch
        y_q3 = top + ch - (q3 / ymax) * ch
        y_mx = top + ch - (mx / ymax) * ch
        lines.append(f'<line x1="{cx:.1f}" y1="{y_mx:.1f}" x2="{cx:.1f}" y2="{y_q3:.1f}" stroke="#111" stroke-width="1.1"/>')
        lines.append(f'<line x1="{cx:.1f}" y1="{y_q1:.1f}" x2="{cx:.1f}" y2="{y_mn:.1f}" stroke="#111" stroke-width="1.1"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{y_mx:.1f}" x2="{x+box_width:.1f}" y2="{y_mx:.1f}" stroke="#111" stroke-width="1.1"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{y_mn:.1f}" x2="{x+box_width:.1f}" y2="{y_mn:.1f}" stroke="#111" stroke-width="1.1"/>')
        lines.append(
            f'<rect x="{x:.1f}" y="{y_q3:.1f}" width="{box_width:.1f}" height="{max(1.0, y_q1-y_q3):.1f}" '
            f'fill="{colors[category]}" stroke="#111" stroke-width="0.9"/>'
        )
        lines.append(f'<line x1="{x:.1f}" y1="{y_median:.1f}" x2="{x+box_width:.1f}" y2="{y_median:.1f}" stroke="#111" stroke-width="1.5"/>')
        lines.append(
            f'<text x="{cx:.1f}" y="{top+ch+20:.1f}" text-anchor="middle" font-size="11" '
            f'font-family="Arial, sans-serif" fill="#111">{html.escape(label_fn(category))}</text>'
        )
    svg_finish(lines, out_path)


def plot_runtime_vs_cells_by_category(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
    *,
    title: str,
    category_key: str,
    category_order: Sequence[str],
    label_fn: Callable[[str], str],
    marker_fn: Optional[Callable[[str], str]] = None,
) -> None:
    categories = ordered_present_categories(rows, category_key, category_order)
    grouped: Dict[str, Dict[int, List[float]]] = {category: defaultdict(list) for category in categories}
    all_cells = set()
    for row in rows:
        if not include_line_scatter_point(row["_status"]):
            continue
        category = (row.get(category_key, "") or "").strip().lower()
        if category not in grouped:
            continue
        cells = safe_int(row.get("cells", ""))
        runtime = safe_float(row.get("measured_total_sec", ""))
        if cells is None or runtime is None or runtime < 0:
            continue
        grouped[category][cells].append(runtime)
        all_cells.add(cells)
    categories = [category for category in categories if grouped[category]]
    cells_sorted = sorted(all_cells)
    if not categories or not cells_sorted:
        return

    max_y = max(
        percentile(sorted(values), 0.5)
        for category in categories
        for values in grouped[category].values()
        if values
    )
    y_max = nice_max(max_y * 1.25 if max_y > 0 else 1.0)
    x_min = min(cells_sorted)
    x_max = max(cells_sorted)
    if category_key == "_domain_family":
        colors = domain_family_compare_colors(categories)
    else:
        colors = color_for_categories(categories)

    width = 1120
    height = 620
    left = 90
    top = 92
    right = 240
    bottom = 90
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, title, subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        value = frac * y_max
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{value:.1f}</text>'
        )
    for cells in cells_sorted:
        x = lin_map(cells, x_min, x_max, left, left + cw)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{cells}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" '
        f'font-family="Arial, sans-serif" fill="#111">Cells (rows × cols)</text>'
    )
    lines.append(
        f'<text x="{left-58}" y="{top + ch/2:.1f}" transform="rotate(-90 {left-58} {top + ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">Median Measured Runtime (sec)</text>'
    )

    for category in categories:
        points: List[Tuple[float, float]] = []
        for cells in cells_sorted:
            values = grouped[category].get(cells, [])
            if not values:
                continue
            median = percentile(sorted(values), 0.5)
            x = lin_map(cells, x_min, x_max, left, left + cw)
            y = lin_map(median, 0, y_max, top + ch, top)
            points.append((x, y))
        if len(points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" '
                f'fill="none" stroke="{colors[category]}" stroke-width="2.0"/>'
            )
        marker = marker_fn(category) if marker_fn is not None else "circle"
        for x, y in points:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker=marker,
                size=3.6,
                fill=colors[category],
                stroke="#111",
                stroke_width=0.8,
            )

    draw_legend(
        lines,
        items=[(label_fn(category), colors[category]) for category in categories],
        x=left + cw + 18,
        y=top + 8,
        title="Category",
        marker="rect",
    )
    svg_finish(lines, out_path)


def plot_success_rate_by_domain_family(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    plot_success_rate_by_category(
        rows,
        out_path,
        subtitle,
        title="Solve Rate By Domain Family (PDDL / FA / PLUS)",
        category_key="_domain_family",
        category_order=DOMAIN_FAMILY_ORDER,
        label_fn=domain_family_compare_label,
    )


def plot_runtime_box_by_domain_family(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    plot_box_by_category(
        rows,
        out_path,
        subtitle,
        title="Measured Runtime Distribution By Domain Family",
        category_key="_domain_family",
        category_order=DOMAIN_FAMILY_ORDER,
        label_fn=domain_family_compare_label,
        value_fn=lambda row: safe_float(row.get("measured_total_sec", "")),
        y_label="Measured Runtime (sec)",
    )


def plot_runtime_vs_cells_by_domain_family(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    plot_runtime_vs_cells_by_category(
        rows,
        out_path,
        subtitle,
        title="Median Runtime vs Level Size By Domain Family",
        category_key="_domain_family",
        category_order=DOMAIN_FAMILY_ORDER,
        label_fn=domain_family_compare_label,
        marker_fn=marker_for_family,
    )


def plot_success_rate_by_domain_scanner(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    plot_success_rate_by_category(
        rows,
        out_path,
        subtitle,
        title="Solve Rate By Scanner vs Non-scanner Domain Variant",
        category_key="_domain_scanner",
        category_order=DOMAIN_SCANNER_ORDER,
        label_fn=domain_scanner_label,
    )


def plot_success_rate_by_domain_layout(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    plot_success_rate_by_category(
        rows,
        out_path,
        subtitle,
        title="Solve Rate By Combined vs Separated Domain Variant",
        category_key="_domain_layout",
        category_order=DOMAIN_LAYOUT_ORDER,
        label_fn=domain_layout_label,
    )


def plot_success_rate_heatmap_domain_family_x_variant(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
) -> None:
    families = ordered_present_categories(rows, "_domain_family", DOMAIN_FAMILY_ORDER)
    variants = ordered_present_categories(rows, "_domain_variant", DOMAIN_VARIANT_ORDER)
    if not families or not variants:
        return

    totals: Dict[Tuple[str, str], int] = Counter()
    solved: Dict[Tuple[str, str], int] = Counter()
    for row in rows:
        family = (row.get("_domain_family", "") or "").strip().lower()
        variant = (row.get("_domain_variant", "") or "").strip().lower()
        if family not in families or variant not in variants or not is_attempt_status(row["_status"]):
            continue
        key = (family, variant)
        totals[key] += 1
        if row["_status"] == "solved":
            solved[key] += 1
    if not any(totals.values()):
        return

    width = max(1020, 360 + 160 * len(variants))
    height = max(420, 220 + 56 * len(families))
    left = 260
    top = 100
    right = 180
    bottom = 120
    cw = width - left - right
    ch = height - top - bottom
    cell_w = cw / max(1, len(variants))
    cell_h = ch / max(1, len(families))

    lines = svg_start(width, height, "Solve Rate Heatmap (PDDL / FA / PLUS x Domain Variant)", subtitle)
    for ri, family in enumerate(families):
        y = top + ri * cell_h
        lines.append(
            f'<text x="{left-12:.1f}" y="{y+cell_h*0.64:.1f}" text-anchor="end" font-size="11" '
            f'font-family="Arial, sans-serif" fill="#111">{html.escape(domain_family_compare_label(family))}</text>'
        )
        for ci, variant in enumerate(variants):
            x = left + ci * cell_w
            key = (family, variant)
            total = totals[key]
            if total <= 0:
                fill = "rgb(232,232,232)"
                text = "NA"
            else:
                rate = solved[key] / total
                fill = red_yellow_green(rate)
                text = f"{rate*100:.0f}%"
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" '
                f'fill="{fill}" stroke="#ddd" stroke-width="0.8"/>'
            )
            lines.append(
                f'<text x="{x+cell_w/2:.1f}" y="{y+cell_h*0.64:.1f}" text-anchor="middle" font-size="10" '
                f'font-family="Arial, sans-serif" fill="#1f2937">{text}</text>'
            )
    lines.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{cw:.1f}" height="{ch:.1f}" fill="none" stroke="#111" stroke-width="1"/>')
    for ci, variant in enumerate(variants):
        x = left + (ci + 0.5) * cell_w
        lines.append(
            f'<text x="{x:.1f}" y="{top-8:.1f}" text-anchor="end" transform="rotate(-30 {x:.1f} {top-8:.1f})" '
            f'font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(domain_variant_label(variant))}</text>'
        )
    draw_legend(
        lines,
        items=[
            ("100% solved", red_yellow_green(1.0)),
            ("50% solved", red_yellow_green(0.5)),
            ("0% solved", red_yellow_green(0.0)),
            ("No data", "rgb(232,232,232)"),
        ],
        x=left + cw + 18,
        y=top + 8,
        title="Cell Meaning",
        marker="rect",
    )
    svg_finish(lines, out_path)


def plot_runtime_heatmap_domain_family_x_variant(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
) -> None:
    families = ordered_present_categories(rows, "_domain_family", DOMAIN_FAMILY_ORDER)
    variants = ordered_present_categories(rows, "_domain_variant", DOMAIN_VARIANT_ORDER)
    if not families or not variants:
        return

    grouped: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for row in rows:
        family = (row.get("_domain_family", "") or "").strip().lower()
        variant = (row.get("_domain_variant", "") or "").strip().lower()
        if family not in families or variant not in variants:
            continue
        runtime = safe_float(row.get("measured_total_sec", ""))
        if runtime is None or runtime < 0:
            continue
        grouped[(family, variant)].append(runtime)

    medians: Dict[Tuple[str, str], Optional[float]] = {}
    all_medians: List[float] = []
    for family in families:
        for variant in variants:
            values = grouped.get((family, variant), [])
            if values:
                median = percentile(sorted(values), 0.5)
                medians[(family, variant)] = median
                all_medians.append(median)
            else:
                medians[(family, variant)] = None
    if not all_medians:
        return

    vmin = min(all_medians)
    vmax = max(all_medians)
    if vmax <= vmin:
        vmax = vmin + 1.0

    width = max(1020, 360 + 160 * len(variants))
    height = max(420, 220 + 56 * len(families))
    left = 260
    top = 100
    right = 180
    bottom = 120
    cw = width - left - right
    ch = height - top - bottom
    cell_w = cw / max(1, len(variants))
    cell_h = ch / max(1, len(families))

    lines = svg_start(width, height, "Median Runtime Heatmap (PDDL / FA / PLUS x Domain Variant)", subtitle)
    for ri, family in enumerate(families):
        y = top + ri * cell_h
        lines.append(
            f'<text x="{left-12:.1f}" y="{y+cell_h*0.64:.1f}" text-anchor="end" font-size="11" '
            f'font-family="Arial, sans-serif" fill="#111">{html.escape(domain_family_compare_label(family))}</text>'
        )
        for ci, variant in enumerate(variants):
            x = left + ci * cell_w
            median = medians[(family, variant)]
            if median is None:
                fill = "rgb(232,232,232)"
                text = "NA"
            else:
                frac = (median - vmin) / (vmax - vmin)
                fill = red_yellow_green(1.0 - frac)
                text = f"{median:.1f}s"
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" '
                f'fill="{fill}" stroke="#ddd" stroke-width="0.8"/>'
            )
            lines.append(
                f'<text x="{x+cell_w/2:.1f}" y="{y+cell_h*0.64:.1f}" text-anchor="middle" font-size="10" '
                f'font-family="Arial, sans-serif" fill="#1f2937">{text}</text>'
            )
    lines.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{cw:.1f}" height="{ch:.1f}" fill="none" stroke="#111" stroke-width="1"/>')
    for ci, variant in enumerate(variants):
        x = left + (ci + 0.5) * cell_w
        lines.append(
            f'<text x="{x:.1f}" y="{top-8:.1f}" text-anchor="end" transform="rotate(-30 {x:.1f} {top-8:.1f})" '
            f'font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(domain_variant_label(variant))}</text>'
        )
    draw_legend(
        lines,
        items=[
            ("Faster median", red_yellow_green(1.0)),
            ("Slower median", red_yellow_green(0.0)),
            ("No data", "rgb(232,232,232)"),
        ],
        x=left + cw + 18,
        y=top + 8,
        title="Cell Meaning",
        marker="rect",
    )
    lines.append(
        f'<text x="{left+cw+18:.1f}" y="{top+82:.1f}" font-size="11" font-family="Arial, sans-serif" fill="#444">'
        f'Range: {vmin:.2f}s to {vmax:.2f}s</text>'
    )
    svg_finish(lines, out_path)


def plot_box_by_domain(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
    *,
    title: str,
    value_fn: Callable[[Dict[str, str]], Optional[float]],
    y_label: str,
) -> None:
    domains = sorted(set(r["_domain"] for r in rows))
    grouped: Dict[str, List[float]] = {d: [] for d in domains}
    for r in rows:
        v = value_fn(r)
        if v is None or v < 0:
            continue
        grouped[r["_domain"]].append(v)
    domains = [d for d in domains if grouped[d]]
    if not domains:
        return
    ymax = max(max(vals) for vals in grouped.values())
    ymax = nice_max(ymax * 1.1 if ymax > 0 else 1.0)
    colors = color_for_categories(domains)

    width = max(1220, 330 + 28 * len(domains))
    height = 620
    left = 95
    top = 92
    right = 140
    bottom = 160
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, title, subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        v = frac * ymax
        label = f"{v:.1f}" if ymax >= 10 else f"{v:.2f}"
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{label}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left-62}" y="{top + ch/2:.1f}" transform="rotate(-90 {left-62} {top + ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(y_label)}</text>'
    )

    step = cw / max(1, len(domains))
    bw = min(18.0, step * 0.7)
    for i, d in enumerate(domains):
        mn, q1, md, q3, mx = box_stats(grouped[d])
        cx = left + (i + 0.5) * step
        x = cx - bw / 2.0
        y_mn = top + ch - (mn / ymax) * ch
        y_q1 = top + ch - (q1 / ymax) * ch
        y_md = top + ch - (md / ymax) * ch
        y_q3 = top + ch - (q3 / ymax) * ch
        y_mx = top + ch - (mx / ymax) * ch
        lines.append(f'<line x1="{cx:.1f}" y1="{y_mx:.1f}" x2="{cx:.1f}" y2="{y_q3:.1f}" stroke="#111" stroke-width="1.0"/>')
        lines.append(f'<line x1="{cx:.1f}" y1="{y_q1:.1f}" x2="{cx:.1f}" y2="{y_mn:.1f}" stroke="#111" stroke-width="1.0"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{y_mx:.1f}" x2="{x+bw:.1f}" y2="{y_mx:.1f}" stroke="#111" stroke-width="1.0"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{y_mn:.1f}" x2="{x+bw:.1f}" y2="{y_mn:.1f}" stroke="#111" stroke-width="1.0"/>')
        lines.append(f'<rect x="{x:.1f}" y="{y_q3:.1f}" width="{bw:.1f}" height="{max(1.0, y_q1-y_q3):.1f}" fill="{colors[d]}" stroke="#111" stroke-width="0.6"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{y_md:.1f}" x2="{x+bw:.1f}" y2="{y_md:.1f}" stroke="#111" stroke-width="1.2"/>')
        lines.append(
            f'<text x="{cx:.1f}" y="{top+ch+14:.1f}" text-anchor="middle" transform="rotate(65 {cx:.1f} {top+ch+14:.1f})" '
            f'font-size="8.5" font-family="Arial, sans-serif" fill="#111">{html.escape(d)}</text>'
        )
    svg_finish(lines, out_path)


def plot_runtime_heatmap_domain_x_setting(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    domains = sorted(set(r["_domain"] for r in rows))
    if not settings or not domains:
        return

    grouped: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for r in rows:
        v = safe_float(r.get("measured_total_sec", ""))
        if v is None or v < 0:
            continue
        grouped[(r["_domain"], r["_setting"])].append(v)

    medians: Dict[Tuple[str, str], Optional[float]] = {}
    vals_all: List[float] = []
    for d in domains:
        for s in settings:
            vals = grouped.get((d, s), [])
            if vals:
                med = percentile(sorted(vals), 0.5)
                medians[(d, s)] = med
                vals_all.append(med)
            else:
                medians[(d, s)] = None
    if not vals_all:
        return

    vmin = min(vals_all)
    vmax = max(vals_all)
    if vmax <= vmin:
        vmax = vmin + 1.0

    width = max(1220, 260 + 130 * len(settings))
    height = max(780, 220 + 26 * len(domains))
    left = 320
    top = 100
    right = 140
    bottom = 120
    cw = width - left - right
    ch = height - top - bottom
    cell_w = cw / max(1, len(settings))
    cell_h = ch / max(1, len(domains))

    lines = svg_start(width, height, "Median Runtime Heatmap (Domain x Setting)", subtitle)
    for di, d in enumerate(domains):
        y = top + di * cell_h
        lines.append(
            f'<text x="{left-8:.1f}" y="{y+cell_h*0.68:.1f}" text-anchor="end" font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(d)}</text>'
        )
        for si, s in enumerate(settings):
            x = left + si * cell_w
            med = medians[(d, s)]
            if med is None:
                fill = "rgb(232,232,232)"
                txt = "NA"
            else:
                frac = (med - vmin) / (vmax - vmin)
                # Low runtime=green, high runtime=red
                fill = red_yellow_green(1.0 - frac)
                txt = f"{med:.1f}"
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" fill="{fill}" stroke="#ddd" stroke-width="0.6"/>'
            )
            lines.append(
                f'<text x="{x+cell_w/2:.1f}" y="{y+cell_h*0.64:.1f}" text-anchor="middle" font-size="9" font-family="Arial, sans-serif" fill="#222">{txt}</text>'
            )
    lines.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{cw:.1f}" height="{ch:.1f}" fill="none" stroke="#111" stroke-width="1"/>')
    for si, s in enumerate(settings):
        x = left + (si + 0.5) * cell_w
        lines.append(
            f'<text x="{x:.1f}" y="{top-8:.1f}" text-anchor="end" transform="rotate(-40 {x:.1f} {top-8:.1f})" '
            f'font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(s)}</text>'
        )
    svg_finish(lines, out_path)


def box_stats(values: Sequence[float]) -> Tuple[float, float, float, float, float]:
    vals = sorted(values)
    return (
        vals[0],
        percentile(vals, 0.25),
        percentile(vals, 0.50),
        percentile(vals, 0.75),
        vals[-1],
    )


def plot_box_by_setting(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
    *,
    title: str,
    value_fn: Callable[[Dict[str, str]], Optional[float]],
    y_label: str,
) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    grouped: Dict[str, List[float]] = {s: [] for s in settings}
    for r in rows:
        v = value_fn(r)
        if v is not None and v >= 0:
            grouped[r["_setting"]].append(v)

    settings = [s for s in settings if grouped[s]]
    if not settings:
        return
    ymax = max(max(vals) for vals in grouped.values())
    ymax = nice_max(ymax * 1.1 if ymax > 0 else 1.0)

    width = max(1100, 250 + 110 * len(settings))
    height = 580
    left = 90
    top = 92
    right = 130
    bottom = 180
    cw = width - left - right
    ch = height - top - bottom
    colors = color_for_categories(settings)

    lines = svg_start(width, height, title, subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        v = frac * ymax
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#e6e6e6"/>')
        label = f"{v:.2f}" if ymax < 100 else f"{v:.1f}"
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{label}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left-62}" y="{top + ch/2:.1f}" transform="rotate(-90 {left-62} {top + ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(y_label)}</text>'
    )

    step = cw / max(1, len(settings))
    bw = min(50.0, step * 0.55)
    for i, s in enumerate(settings):
        stats = box_stats(grouped[s])
        mn, q1, med, q3, mx = stats
        cx = left + (i + 0.5) * step
        x = cx - bw / 2.0
        y_mn = top + ch - (mn / ymax) * ch
        y_q1 = top + ch - (q1 / ymax) * ch
        y_md = top + ch - (med / ymax) * ch
        y_q3 = top + ch - (q3 / ymax) * ch
        y_mx = top + ch - (mx / ymax) * ch
        lines.append(f'<line x1="{cx:.1f}" y1="{y_mx:.1f}" x2="{cx:.1f}" y2="{y_q3:.1f}" stroke="#111" stroke-width="1.1"/>')
        lines.append(f'<line x1="{cx:.1f}" y1="{y_q1:.1f}" x2="{cx:.1f}" y2="{y_mn:.1f}" stroke="#111" stroke-width="1.1"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{y_mx:.1f}" x2="{x+bw:.1f}" y2="{y_mx:.1f}" stroke="#111" stroke-width="1.1"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{y_mn:.1f}" x2="{x+bw:.1f}" y2="{y_mn:.1f}" stroke="#111" stroke-width="1.1"/>')
        lines.append(f'<rect x="{x:.1f}" y="{y_q3:.1f}" width="{bw:.1f}" height="{max(1.0, y_q1-y_q3):.1f}" fill="{colors[s]}" stroke="#111" stroke-width="0.9"/>')
        lines.append(f'<line x1="{x:.1f}" y1="{y_md:.1f}" x2="{x+bw:.1f}" y2="{y_md:.1f}" stroke="#111" stroke-width="1.5"/>')
        lines.append(
            f'<text x="{cx:.1f}" y="{top+ch+16:.1f}" text-anchor="middle" transform="rotate(55 {cx:.1f} {top+ch+16:.1f})" '
            f'font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(s)}</text>'
        )
    svg_finish(lines, out_path)


def plot_runtime_cdf(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    values: Dict[str, List[float]] = {s: [] for s in settings}
    for r in rows:
        v = safe_float(r.get("measured_total_sec", ""))
        if v is not None and v >= 0:
            values[r["_setting"]].append(v)
    settings = [s for s in settings if values[s]]
    if not settings:
        return
    xmax = max(max(vs) for vs in values.values())
    xmax = nice_max(xmax * 1.05 if xmax > 0 else 1.0)
    colors = color_for_categories(settings)

    width = 1120
    height = 620
    left = 90
    top = 92
    right = 280
    bottom = 90
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, "Runtime CDF By Setting", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#efefef"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{frac:.1f}</text>'
        )
    for i in range(6):
        frac = i / 5.0
        x = left + frac * cw
        xv = frac * xmax
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f3f3f3"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="11" font-family="Arial, sans-serif" fill="#444">{xv:.1f}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" font-family="Arial, sans-serif" fill="#111">Measured Runtime (sec)</text>')
    lines.append(
        f'<text x="{left-58}" y="{top + ch/2:.1f}" transform="rotate(-90 {left-58} {top + ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">Cumulative Fraction</text>'
    )

    for s in settings:
        vals = sorted(values[s])
        points: List[str] = []
        for i, v in enumerate(vals, start=1):
            x = lin_map(v, 0, xmax, left, left + cw)
            y = lin_map(i / len(vals), 0, 1, top + ch, top)
            points.append(f"{x:.2f},{y:.2f}")
        lines.append(
            f'<polyline points="{" ".join(points)}" fill="none" stroke="{colors[s]}" stroke-width="1.8"/>'
        )
    draw_legend(
        lines,
        items=[(s, colors[s]) for s in settings],
        x=left + cw + 18,
        y=top + 8,
        title="Setting",
        marker="rect",
    )
    svg_finish(lines, out_path)


def plot_runtime_vs_cells(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    setting_family = family_by_setting(rows)
    grouped: Dict[str, Dict[int, List[float]]] = {s: defaultdict(list) for s in settings}
    all_cells = set()
    for r in rows:
        if not include_line_scatter_point(r["_status"]):
            continue
        cells = safe_int(r.get("cells", ""))
        rt = safe_float(r.get("measured_total_sec", ""))
        if cells is None or rt is None or rt < 0:
            continue
        grouped[r["_setting"]][cells].append(rt)
        all_cells.add(cells)
    cells_sorted = sorted(all_cells)
    settings = [s for s in settings if grouped[s]]
    if not settings or not cells_sorted:
        return
    max_y = max(
        percentile(sorted(vals), 0.5)
        for s in settings
        for vals in grouped[s].values()
        if vals
    )
    y_max = nice_max(max_y * 1.25 if max_y > 0 else 1.0)
    colors = color_for_categories(settings)

    width = 1220
    height = 640
    left = 90
    top = 92
    right = 300
    bottom = 100
    cw = width - left - right
    ch = height - top - bottom

    x_min = min(cells_sorted)
    x_max = max(cells_sorted)
    lines = svg_start(width, height, "Median Runtime vs Level Size", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        val = frac * y_max
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{val:.1f}</text>'
        )
    for c in cells_sorted:
        x = lin_map(c, x_min, x_max, left, left + cw)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{c}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" font-family="Arial, sans-serif" fill="#111">Cells (rows × cols)</text>')
    lines.append(
        f'<text x="{left-58}" y="{top + ch/2:.1f}" transform="rotate(-90 {left-58} {top + ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">Median Measured Runtime (sec)</text>'
    )

    for s in settings:
        points: List[Tuple[float, float]] = []
        for c in cells_sorted:
            vals = grouped[s].get(c, [])
            if not vals:
                continue
            med = percentile(sorted(vals), 0.5)
            x = lin_map(c, x_min, x_max, left, left + cw)
            y = lin_map(med, 0, y_max, top + ch, top)
            points.append((x, y))
        if len(points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="none" stroke="{colors[s]}" stroke-width="1.8"/>'
            )
        marker = marker_for_family(setting_family.get(s, "unknown"))
        for x, y in points:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker=marker,
                size=3.2,
                fill=colors[s],
                stroke="#111",
                stroke_width=0.7,
            )
    draw_legend(
        lines,
        items=[(s, colors[s]) for s in settings],
        x=left + cw + 18,
        y=top + 8,
        title="Setting",
        marker="rect",
    )
    families_present = sorted(set(setting_family.get(s, "unknown") for s in settings))
    draw_family_shape_legend(
        lines,
        families=families_present,
        x=left + cw + 18,
        y=top + 8 + 18 + 16 * len(settings) + 10,
    )
    svg_finish(lines, out_path)


def plot_runtime_vs_cells_by_domain(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    domains = sorted(set(r["_domain"] for r in rows))
    domain_family: Dict[str, str] = {}
    grouped: Dict[str, Dict[int, List[float]]] = {domain: defaultdict(list) for domain in domains}
    all_cells = set()
    for row in rows:
        if not include_line_scatter_point(row["_status"]):
            continue
        domain = row["_domain"]
        cells = safe_int(row.get("cells", ""))
        runtime = safe_float(row.get("measured_total_sec", ""))
        if cells is None or runtime is None or runtime < 0:
            continue
        grouped[domain][cells].append(runtime)
        domain_family.setdefault(domain, (row.get("_domain_family", "") or "unknown").strip().lower() or "unknown")
        all_cells.add(cells)
    domains = [domain for domain in domains if grouped[domain]]
    cells_sorted = sorted(all_cells)
    if not domains or not cells_sorted:
        return

    max_y = max(
        percentile(sorted(values), 0.5)
        for domain in domains
        for values in grouped[domain].values()
        if values
    )
    y_max = nice_max(max_y * 1.25 if max_y > 0 else 1.0)
    colors = color_for_categories(domains)

    width = 1560
    height = 700
    left = 90
    top = 92
    right = 460
    bottom = 100
    cw = width - left - right
    ch = height - top - bottom

    x_min = min(cells_sorted)
    x_max = max(cells_sorted)
    lines = svg_start(width, height, "Median Runtime vs Level Size By Domain", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        value = frac * y_max
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{value:.1f}</text>'
        )
    for cells in cells_sorted:
        x = lin_map(cells, x_min, x_max, left, left + cw)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{cells}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" '
        f'font-family="Arial, sans-serif" fill="#111">Cells (rows × cols)</text>'
    )
    lines.append(
        f'<text x="{left-58}" y="{top + ch/2:.1f}" transform="rotate(-90 {left-58} {top + ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">Median Measured Runtime (sec)</text>'
    )

    for domain in domains:
        points: List[Tuple[float, float]] = []
        for cells in cells_sorted:
            values = grouped[domain].get(cells, [])
            if not values:
                continue
            median = percentile(sorted(values), 0.5)
            x = lin_map(cells, x_min, x_max, left, left + cw)
            y = lin_map(median, 0, y_max, top + ch, top)
            points.append((x, y))
        if len(points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" '
                f'fill="none" stroke="{colors[domain]}" stroke-width="1.8"/>'
            )
        marker = marker_for_family(domain_family.get(domain, "unknown"))
        for x, y in points:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker=marker,
                size=3.2,
                fill=colors[domain],
                stroke="#111",
                stroke_width=0.7,
            )
    draw_legend(
        lines,
        items=[(domain_compare_label(domain), colors[domain]) for domain in domains],
        x=left + cw + 18,
        y=top + 8,
        title="Domain",
        marker="rect",
    )
    families_present = sorted(set(domain_family.get(domain, "unknown") for domain in domains))
    draw_family_shape_legend(
        lines,
        families=families_present,
        x=left + cw + 18,
        y=top + 8 + 18 + 16 * len(domains) + 10,
    )
    svg_finish(lines, out_path)


def plot_action_literals_vs_cells(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    grouped_actions: Dict[int, List[float]] = defaultdict(list)
    grouped_literals: Dict[int, List[float]] = defaultdict(list)
    all_cells: set[int] = set()

    for r in rows:
        cells = safe_int(r.get("cells", ""))
        if cells is None or cells <= 0:
            continue
        action_count = safe_float(r.get("action_set_size", ""))
        literal_count = safe_float(r.get("facts_count", ""))
        if action_count is not None and action_count >= 0:
            grouped_actions[cells].append(action_count)
            all_cells.add(cells)
        if literal_count is not None and literal_count >= 0:
            grouped_literals[cells].append(literal_count)
            all_cells.add(cells)

    cells_sorted = sorted(all_cells)
    action_medians = {c: percentile(sorted(v), 0.5) for c, v in grouped_actions.items() if v}
    literal_medians = {c: percentile(sorted(v), 0.5) for c, v in grouped_literals.items() if v}
    if not cells_sorted or (not action_medians and not literal_medians):
        return

    y_values = list(action_medians.values()) + list(literal_medians.values())
    y_max = nice_max(max(y_values) * 1.2 if y_values and max(y_values) > 0 else 1.0)
    x_min, x_max = min(cells_sorted), max(cells_sorted)

    width = 1080
    height = 560
    left = 90
    top = 92
    right = 250
    bottom = 90
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, "Action Set / Literal Count vs Map Size", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        val = frac * y_max
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{val:.0f}</text>'
        )

    for c in cells_sorted:
        x = lin_map(c, x_min, x_max, left, left + cw)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{c}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" font-family="Arial, sans-serif" fill="#111">Cells (rows × cols)</text>'
    )
    lines.append(
        f'<text x="{left-62}" y="{top+ch/2:.1f}" transform="rotate(-90 {left-62} {top+ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">Count (median)</text>'
    )

    series: List[Tuple[str, Dict[int, float], str, str]] = [
        ("Action set size", action_medians, "#1f77b4", "circle"),
        ("Literal count", literal_medians, "#d62728", "square"),
    ]
    legend_items: List[Tuple[str, str]] = []
    for label, values, color, marker in series:
        if not values:
            continue
        pts: List[Tuple[float, float]] = []
        for c in cells_sorted:
            yv = values.get(c)
            if yv is None:
                continue
            x = lin_map(c, x_min, x_max, left, left + cw)
            y = lin_map(yv, 0, y_max, top + ch, top)
            pts.append((x, y))
        if len(pts) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{color}" stroke-width="2.0"/>'
            )
        for x, y in pts:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker=marker,
                size=3.4,
                fill=color,
                stroke="#111",
                stroke_width=0.8,
            )
        legend_items.append((label, color))

    draw_legend(
        lines,
        items=legend_items,
        x=left + cw + 18,
        y=top + 8,
        title="Metric",
        marker="rect",
    )
    svg_finish(lines, out_path)


def plot_runtime_grounding_vs_cells(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    grouped_runtime: Dict[int, List[float]] = defaultdict(list)
    grouped_grounding: Dict[int, List[float]] = defaultdict(list)
    all_cells: set[int] = set()

    for row in rows:
        if not include_line_scatter_point(row["_status"]):
            continue
        cells = safe_int(row.get("cells", ""))
        if cells is None or cells <= 0:
            continue
        runtime = safe_float(row.get("measured_total_sec", ""))
        grounding = safe_float(row.get("reported_grounding_sec", ""))
        if runtime is not None and runtime >= 0:
            grouped_runtime[cells].append(runtime)
            all_cells.add(cells)
        if grounding is not None and grounding >= 0:
            grouped_grounding[cells].append(grounding)
            all_cells.add(cells)

    cells_sorted = sorted(all_cells)
    runtime_medians = {cells: percentile(sorted(values), 0.5) for cells, values in grouped_runtime.items() if values}
    grounding_medians = {cells: percentile(sorted(values), 0.5) for cells, values in grouped_grounding.items() if values}
    if not cells_sorted or (not runtime_medians and not grounding_medians):
        return

    y_values = list(runtime_medians.values()) + list(grounding_medians.values())
    y_max = nice_max(max(y_values) * 1.2 if y_values and max(y_values) > 0 else 1.0)
    x_min = min(cells_sorted)
    x_max = max(cells_sorted)

    width = 1080
    height = 560
    left = 90
    top = 92
    right = 260
    bottom = 90
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, "Measured Runtime / Grounding Time vs Level Size", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        value = frac * y_max
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{value:.1f}</text>'
        )

    for cells in cells_sorted:
        x = lin_map(cells, x_min, x_max, left, left + cw)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{cells}</text>'
        )

    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" font-family="Arial, sans-serif" fill="#111">Cells (rows × cols)</text>'
    )
    lines.append(
        f'<text x="{left-62}" y="{top+ch/2:.1f}" transform="rotate(-90 {left-62} {top+ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">Time (sec, median)</text>'
    )

    series: List[Tuple[str, Dict[int, float], str, str]] = [
        ("Measured runtime", runtime_medians, "#1f77b4", "circle"),
        ("Reported grounding time", grounding_medians, "#ff7f0e", "square"),
    ]
    legend_items: List[Tuple[str, str]] = []
    for label, values, color, marker in series:
        if not values:
            continue
        points: List[Tuple[float, float]] = []
        for cells in cells_sorted:
            y_value = values.get(cells)
            if y_value is None:
                continue
            x = lin_map(cells, x_min, x_max, left, left + cw)
            y = lin_map(y_value, 0, y_max, top + ch, top)
            points.append((x, y))
        if len(points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in points)}" fill="none" stroke="{color}" stroke-width="2.0"/>'
            )
        for x, y in points:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker=marker,
                size=3.4,
                fill=color,
                stroke="#111",
                stroke_width=0.8,
            )
        legend_items.append((label, color))

    draw_legend(
        lines,
        items=legend_items,
        x=left + cw + 18,
        y=top + 8,
        title="Metric",
        marker="rect",
    )
    svg_finish(lines, out_path)


def plot_runtime_grounding_vs_cells_by_domain(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
) -> None:
    domains = sorted(set(r["_domain"] for r in rows))
    grouped_runtime: Dict[str, Dict[int, List[float]]] = {domain: defaultdict(list) for domain in domains}
    grouped_grounding: Dict[str, Dict[int, List[float]]] = {domain: defaultdict(list) for domain in domains}
    all_cells: set[int] = set()

    for row in rows:
        if not include_line_scatter_point(row["_status"]):
            continue
        domain = row["_domain"]
        cells = safe_int(row.get("cells", ""))
        if cells is None or cells <= 0:
            continue
        runtime = safe_float(row.get("measured_total_sec", ""))
        grounding = safe_float(row.get("reported_grounding_sec", ""))
        if runtime is not None and runtime >= 0:
            grouped_runtime[domain][cells].append(runtime)
            all_cells.add(cells)
        if grounding is not None and grounding >= 0:
            grouped_grounding[domain][cells].append(grounding)
            all_cells.add(cells)

    domains = [domain for domain in domains if grouped_runtime[domain] or grouped_grounding[domain]]
    cells_sorted = sorted(all_cells)
    if not domains or not cells_sorted:
        return

    runtime_medians: Dict[str, Dict[int, float]] = {}
    grounding_medians: Dict[str, Dict[int, float]] = {}
    y_values: List[float] = []
    for domain in domains:
        runtime_medians[domain] = {
            cells: percentile(sorted(values), 0.5)
            for cells, values in grouped_runtime[domain].items()
            if values
        }
        grounding_medians[domain] = {
            cells: percentile(sorted(values), 0.5)
            for cells, values in grouped_grounding[domain].items()
            if values
        }
        y_values.extend(runtime_medians[domain].values())
        y_values.extend(grounding_medians[domain].values())
    if not y_values:
        return

    y_max = nice_max(max(y_values) * 1.2 if max(y_values) > 0 else 1.0)
    x_min = min(cells_sorted)
    x_max = max(cells_sorted)
    colors = color_for_categories(domains)

    width = 1760
    height = 760
    left = 90
    top = 92
    right = 560
    bottom = 100
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, "Measured Runtime / Grounding Time vs Level Size By Domain", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        value = frac * y_max
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{value:.1f}</text>'
        )
    for cells in cells_sorted:
        x = lin_map(cells, x_min, x_max, left, left + cw)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{cells}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" '
        f'font-family="Arial, sans-serif" fill="#111">Cells (rows × cols)</text>'
    )
    lines.append(
        f'<text x="{left-62}" y="{top+ch/2:.1f}" transform="rotate(-90 {left-62} {top+ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">Time (sec, median)</text>'
    )

    for domain in domains:
        runtime_points: List[Tuple[float, float]] = []
        for cells in cells_sorted:
            value = runtime_medians[domain].get(cells)
            if value is None:
                continue
            x = lin_map(cells, x_min, x_max, left, left + cw)
            y = lin_map(value, 0, y_max, top + ch, top)
            runtime_points.append((x, y))
        if len(runtime_points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in runtime_points)}" '
                f'fill="none" stroke="{colors[domain]}" stroke-width="1.9"/>'
            )
        for x, y in runtime_points:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker="circle",
                size=3.1,
                fill=colors[domain],
                stroke="#111",
                stroke_width=0.7,
            )

        grounding_points: List[Tuple[float, float]] = []
        for cells in cells_sorted:
            value = grounding_medians[domain].get(cells)
            if value is None:
                continue
            x = lin_map(cells, x_min, x_max, left, left + cw)
            y = lin_map(value, 0, y_max, top + ch, top)
            grounding_points.append((x, y))
        if len(grounding_points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in grounding_points)}" '
                f'fill="none" stroke="{colors[domain]}" stroke-width="1.7" stroke-dasharray="6,4"/>'
            )
        for x, y in grounding_points:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker="square",
                size=3.0,
                fill=colors[domain],
                stroke="#111",
                stroke_width=0.7,
            )

    draw_legend(
        lines,
        items=[(domain_compare_label(domain), colors[domain]) for domain in domains],
        x=left + cw + 18,
        y=top + 8,
        title="Domain",
        marker="rect",
    )

    metric_x = left + cw + 18
    metric_y = top + 8 + 18 + 16 * len(domains) + 12
    lines.append(
        f'<text x="{metric_x:.1f}" y="{metric_y:.1f}" font-size="13" font-family="Arial, sans-serif" fill="#111">Metric</text>'
    )
    runtime_y = metric_y + 18
    lines.append(
        f'<line x1="{metric_x:.1f}" y1="{runtime_y-4:.1f}" x2="{metric_x+28:.1f}" y2="{runtime_y-4:.1f}" stroke="#444" stroke-width="1.9"/>'
    )
    draw_point_marker(
        lines,
        x=metric_x + 14,
        y=runtime_y - 4,
        marker="circle",
        size=3.1,
        fill="#444",
        stroke="#111",
        stroke_width=0.7,
    )
    lines.append(
        f'<text x="{metric_x+38:.1f}" y="{runtime_y:.1f}" font-size="12" font-family="Arial, sans-serif" fill="#111">Measured runtime</text>'
    )
    grounding_y = runtime_y + 18
    lines.append(
        f'<line x1="{metric_x:.1f}" y1="{grounding_y-4:.1f}" x2="{metric_x+28:.1f}" y2="{grounding_y-4:.1f}" stroke="#444" stroke-width="1.7" stroke-dasharray="6,4"/>'
    )
    draw_point_marker(
        lines,
        x=metric_x + 14,
        y=grounding_y - 4,
        marker="square",
        size=3.0,
        fill="#444",
        stroke="#111",
        stroke_width=0.7,
    )
    lines.append(
        f'<text x="{metric_x+38:.1f}" y="{grounding_y:.1f}" font-size="12" font-family="Arial, sans-serif" fill="#111">Reported grounding time</text>'
    )
    svg_finish(lines, out_path)


def plot_runtime_grounding_vs_cells_by_domain_loglog(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
) -> None:
    domains = sorted(set(r["_domain"] for r in rows))
    grouped_runtime: Dict[str, Dict[int, List[float]]] = {domain: defaultdict(list) for domain in domains}
    grouped_grounding: Dict[str, Dict[int, List[float]]] = {domain: defaultdict(list) for domain in domains}
    all_cells: set[int] = set()

    for row in rows:
        if not include_line_scatter_point(row["_status"]):
            continue
        domain = row["_domain"]
        cells = safe_int(row.get("cells", ""))
        if cells is None or cells <= 0:
            continue
        runtime = safe_float(row.get("measured_total_sec", ""))
        grounding = safe_float(row.get("reported_grounding_sec", ""))
        if runtime is not None and runtime > 0:
            grouped_runtime[domain][cells].append(runtime)
            all_cells.add(cells)
        if grounding is not None and grounding > 0:
            grouped_grounding[domain][cells].append(grounding)
            all_cells.add(cells)

    domains = [domain for domain in domains if grouped_runtime[domain] or grouped_grounding[domain]]
    cells_sorted = sorted(cells for cells in all_cells if cells > 0)
    if not domains or not cells_sorted:
        return

    runtime_medians: Dict[str, Dict[int, float]] = {}
    grounding_medians: Dict[str, Dict[int, float]] = {}
    y_values: List[float] = []
    for domain in domains:
        runtime_medians[domain] = {
            cells: percentile(sorted(values), 0.5)
            for cells, values in grouped_runtime[domain].items()
            if values and percentile(sorted(values), 0.5) > 0
        }
        grounding_medians[domain] = {
            cells: percentile(sorted(values), 0.5)
            for cells, values in grouped_grounding[domain].items()
            if values and percentile(sorted(values), 0.5) > 0
        }
        y_values.extend(runtime_medians[domain].values())
        y_values.extend(grounding_medians[domain].values())
    if not y_values:
        return

    x_min = min(cells_sorted)
    x_max = max(cells_sorted)
    y_min = min(y_values)
    y_max = max(y_values)
    if x_max <= x_min or y_max <= y_min:
        return

    colors = color_for_categories(domains)

    width = 1760
    height = 760
    left = 90
    top = 92
    right = 560
    bottom = 100
    cw = width - left - right
    ch = height - top - bottom

    x_ticks = power_of_ten_ticks(x_min, x_max)
    y_ticks = power_of_ten_ticks(y_min, y_max)
    lines = svg_start(width, height, "Measured Runtime / Grounding Time vs Level Size By Domain (Log-Log)", subtitle)
    for value in y_ticks:
        y = log_map(value, y_min, y_max, top + ch, top)
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{html.escape(format_log_tick(value))}</text>'
        )
    for value in x_ticks:
        x = log_map(value, x_min, x_max, left, left + cw)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{html.escape(format_log_tick(value))}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(
        f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" '
        f'font-family="Arial, sans-serif" fill="#111">Cells (rows × cols, log scale)</text>'
    )
    lines.append(
        f'<text x="{left-62}" y="{top+ch/2:.1f}" transform="rotate(-90 {left-62} {top+ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">Time (sec, median, log scale)</text>'
    )

    for domain in domains:
        runtime_points: List[Tuple[float, float]] = []
        for cells in cells_sorted:
            value = runtime_medians[domain].get(cells)
            if value is None or value <= 0:
                continue
            x = log_map(cells, x_min, x_max, left, left + cw)
            y = log_map(value, y_min, y_max, top + ch, top)
            runtime_points.append((x, y))
        if len(runtime_points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in runtime_points)}" '
                f'fill="none" stroke="{colors[domain]}" stroke-width="1.9"/>'
            )
        for x, y in runtime_points:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker="circle",
                size=3.1,
                fill=colors[domain],
                stroke="#111",
                stroke_width=0.7,
            )

        grounding_points: List[Tuple[float, float]] = []
        for cells in cells_sorted:
            value = grounding_medians[domain].get(cells)
            if value is None or value <= 0:
                continue
            x = log_map(cells, x_min, x_max, left, left + cw)
            y = log_map(value, y_min, y_max, top + ch, top)
            grounding_points.append((x, y))
        if len(grounding_points) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in grounding_points)}" '
                f'fill="none" stroke="{colors[domain]}" stroke-width="1.7" stroke-dasharray="6,4"/>'
            )
        for x, y in grounding_points:
            draw_point_marker(
                lines,
                x=x,
                y=y,
                marker="square",
                size=3.0,
                fill=colors[domain],
                stroke="#111",
                stroke_width=0.7,
            )

    draw_legend(
        lines,
        items=[(domain_compare_label(domain), colors[domain]) for domain in domains],
        x=left + cw + 18,
        y=top + 8,
        title="Domain",
        marker="rect",
    )

    metric_x = left + cw + 18
    metric_y = top + 8 + 18 + 16 * len(domains) + 12
    lines.append(
        f'<text x="{metric_x:.1f}" y="{metric_y:.1f}" font-size="13" font-family="Arial, sans-serif" fill="#111">Metric</text>'
    )
    runtime_y = metric_y + 18
    lines.append(
        f'<line x1="{metric_x:.1f}" y1="{runtime_y-4:.1f}" x2="{metric_x+28:.1f}" y2="{runtime_y-4:.1f}" stroke="#444" stroke-width="1.9"/>'
    )
    draw_point_marker(
        lines,
        x=metric_x + 14,
        y=runtime_y - 4,
        marker="circle",
        size=3.1,
        fill="#444",
        stroke="#111",
        stroke_width=0.7,
    )
    lines.append(
        f'<text x="{metric_x+38:.1f}" y="{runtime_y:.1f}" font-size="12" font-family="Arial, sans-serif" fill="#111">Measured runtime</text>'
    )
    grounding_y = runtime_y + 18
    lines.append(
        f'<line x1="{metric_x:.1f}" y1="{grounding_y-4:.1f}" x2="{metric_x+28:.1f}" y2="{grounding_y-4:.1f}" stroke="#444" stroke-width="1.7" stroke-dasharray="6,4"/>'
    )
    draw_point_marker(
        lines,
        x=metric_x + 14,
        y=grounding_y - 4,
        marker="square",
        size=3.0,
        fill="#444",
        stroke="#111",
        stroke_width=0.7,
    )
    lines.append(
        f'<text x="{metric_x+38:.1f}" y="{grounding_y:.1f}" font-size="12" font-family="Arial, sans-serif" fill="#111">Reported grounding time</text>'
    )
    svg_finish(lines, out_path)


def plot_runtime_vs_cells_by_phase(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    observed = sorted(set(r["_phase"] for r in rows if r.get("_phase")))
    preferred_order = ["custom", "random-repeat", "growth"]
    phase_names = [p for p in preferred_order if p in observed] + [p for p in observed if p not in preferred_order]
    if not phase_names:
        return

    base_colors = {
        "custom": "#1f77b4",
        "random-repeat": "#2ca02c",
        "growth": "#d62728",
    }
    fallback = color_for_categories(phase_names)
    colors = {p: base_colors.get(p, fallback[p]) for p in phase_names}
    grouped: Dict[str, Dict[int, List[float]]] = {p: defaultdict(list) for p in phase_names}
    all_cells = set()
    for r in rows:
        if not include_line_scatter_point(r["_status"]):
            continue
        phase = r["_phase"]
        if phase not in grouped:
            continue
        cells = safe_int(r.get("cells", ""))
        rt = safe_float(r.get("measured_total_sec", ""))
        if cells is None or rt is None or rt < 0:
            continue
        grouped[phase][cells].append(rt)
        all_cells.add(cells)
    if not all_cells:
        return
    cells_sorted = sorted(all_cells)
    x_min, x_max = min(cells_sorted), max(cells_sorted)
    max_y = 1.0
    for p in phase_names:
        for vals in grouped[p].values():
            if vals:
                max_y = max(max_y, percentile(sorted(vals), 0.5))
    y_max = nice_max(max_y * 1.25)

    width = 1080
    height = 560
    left = 90
    top = 92
    right = 220
    bottom = 90
    cw = width - left - right
    ch = height - top - bottom
    lines = svg_start(width, height, "Runtime vs Level Size By Phase", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{(frac*y_max):.1f}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    for c in cells_sorted:
        x = lin_map(c, x_min, x_max, left, left + cw)
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{c}</text>'
        )
    for p in phase_names:
        pts: List[Tuple[float, float]] = []
        for c in cells_sorted:
            vals = grouped[p].get(c, [])
            if not vals:
                continue
            med = percentile(sorted(vals), 0.5)
            x = lin_map(c, x_min, x_max, left, left + cw)
            y = lin_map(med, 0, y_max, top + ch, top)
            pts.append((x, y))
        if len(pts) >= 2:
            lines.append(
                f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{colors[p]}" stroke-width="2.0"/>'
            )
        for x, y in pts:
            lines.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.3" fill="{colors[p]}" stroke="#111" stroke-width="0.8"/>'
            )
    draw_legend(
        lines,
        items=[(p, colors[p]) for p in phase_names],
        x=left + cw + 18,
        y=top + 8,
        title="Phase",
        marker="circle",
    )
    svg_finish(lines, out_path)


def plot_scatter(
    rows: Sequence[Dict[str, str]],
    out_path: Path,
    subtitle: str,
    *,
    title: str,
    x_fn: Callable[[Dict[str, str]], Optional[float]],
    y_fn: Callable[[Dict[str, str]], Optional[float]],
    x_label: str,
    y_label: str,
) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    setting_family = family_by_setting(rows)
    colors = color_for_categories(settings)
    pts: List[Tuple[str, float, float]] = []
    for r in rows:
        if not include_line_scatter_point(r["_status"]):
            continue
        xv = x_fn(r)
        yv = y_fn(r)
        if xv is None or yv is None:
            continue
        if xv < 0 or yv < 0:
            continue
        pts.append((r["_setting"], xv, yv))
    if not pts:
        return

    x_max = nice_max(max(p[1] for p in pts) * 1.1 if pts else 1.0)
    y_max = nice_max(max(p[2] for p in pts) * 1.1 if pts else 1.0)

    width = 1160
    height = 640
    left = 95
    top = 92
    right = 290
    bottom = 95
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, title, subtitle)
    for i in range(6):
        frac = i / 5.0
        x = left + frac * cw
        xv = frac * x_max
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f3f3f3"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{xv:.1f}</text>'
        )
        y = top + ch - frac * ch
        yv = frac * y_max
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#f3f3f3"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="10" font-family="Arial, sans-serif" fill="#444">{yv:.1f}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<text x="{left+cw/2:.1f}" y="{top+ch+40:.1f}" text-anchor="middle" font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(x_label)}</text>')
    lines.append(
        f'<text x="{left-62}" y="{top+ch/2:.1f}" transform="rotate(-90 {left-62} {top+ch/2:.1f})" '
        f'font-size="12" font-family="Arial, sans-serif" fill="#111">{html.escape(y_label)}</text>'
    )

    for setting, xv, yv in pts:
        x = lin_map(xv, 0, x_max, left, left + cw)
        y = lin_map(yv, 0, y_max, top + ch, top)
        draw_point_marker(
            lines,
            x=x,
            y=y,
            marker=marker_for_family(setting_family.get(setting, "unknown")),
            size=3.1,
            fill=colors[setting],
            stroke="#111",
            stroke_width=0.6,
            fill_opacity=0.72,
        )
    draw_legend(
        lines,
        items=[(s, colors[s]) for s in settings],
        x=left + cw + 18,
        y=top + 8,
        title="Setting",
        marker="rect",
    )
    families_present = sorted(set(setting_family.get(s, "unknown") for s in settings))
    draw_family_shape_legend(
        lines,
        families=families_present,
        x=left + cw + 18,
        y=top + 8 + 18 + 16 * len(settings) + 10,
    )
    svg_finish(lines, out_path)


def plot_timeout_heatmap(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    domains = sorted(set(r["_domain"] for r in rows))
    if not settings or not domains:
        return

    totals: Dict[Tuple[str, str], int] = Counter()
    timeouts: Dict[Tuple[str, str], int] = Counter()
    for r in rows:
        key = (r["_domain"], r["_setting"])
        totals[key] += 1
        if r["_status"] == "timeout":
            timeouts[key] += 1

    width = max(1180, 240 + 130 * len(settings))
    height = max(760, 220 + 26 * len(domains))
    left = 300
    top = 100
    right = 120
    bottom = 120
    cw = width - left - right
    ch = height - top - bottom

    cell_w = cw / max(1, len(settings))
    cell_h = ch / max(1, len(domains))

    lines = svg_start(width, height, "Timeout Rate Heatmap (Domain x Setting)", subtitle)
    for di, domain in enumerate(domains):
        y = top + di * cell_h
        lines.append(
            f'<text x="{left-8:.1f}" y="{y+cell_h*0.68:.1f}" text-anchor="end" font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(domain)}</text>'
        )
        for si, setting in enumerate(settings):
            x = left + si * cell_w
            key = (domain, setting)
            total = totals[key]
            rate = (timeouts[key] / total) if total > 0 else 0.0
            g = int(round(255 - 175 * rate))
            r = int(round(240 - 40 * rate))
            b = int(round(240 - 240 * rate))
            fill = f"rgb({r},{g},{b})"
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" fill="{fill}" stroke="#ddd" stroke-width="0.6"/>'
            )
            if total > 0:
                lines.append(
                    f'<text x="{x+cell_w/2:.1f}" y="{y+cell_h*0.64:.1f}" text-anchor="middle" font-size="9" font-family="Arial, sans-serif" fill="#222">{rate*100:.0f}%</text>'
                )
    lines.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{cw:.1f}" height="{ch:.1f}" fill="none" stroke="#111" stroke-width="1"/>')

    for si, setting in enumerate(settings):
        x = left + (si + 0.5) * cell_w
        lines.append(
            f'<text x="{x:.1f}" y="{top-8:.1f}" text-anchor="end" transform="rotate(-40 {x:.1f} {top-8:.1f})" '
            f'font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(setting)}</text>'
        )
    svg_finish(lines, out_path)


def plot_outcome_heatmap_domain_map_x_setting(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    domains = sorted(set(r["_domain"] for r in rows))
    if not domains:
        return

    maps = sorted(set(r["_map"] for r in rows))
    if not maps:
        return

    # Only include planner rows for planner-domain combinations that actually ran.
    settings_by_domain: Dict[str, List[str]] = {}
    for d in domains:
        domain_settings = sorted(set(r["_setting"] for r in rows if r["_domain"] == d))
        if domain_settings:
            settings_by_domain[d] = domain_settings
    domains = [d for d in domains if d in settings_by_domain]
    if not domains:
        return

    # Build row model with domain section headers + setting rows.
    row_entries: List[Tuple[str, str, str]] = []
    for d in domains:
        row_entries.append(("domain", d, ""))
        for s in settings_by_domain[d]:
            row_entries.append(("setting", d, s))

    outcomes: Dict[Tuple[str, str, str], Tuple[int, int, Optional[float]]] = {}
    for d in domains:
        for s in settings_by_domain[d]:
            for m in maps:
                attempts = 0
                solved = 0
                solved_runtimes: List[float] = []
                for r in rows:
                    if r["_domain"] != d or r["_setting"] != s or r["_map"] != m:
                        continue
                    st = r["_status"]
                    if not is_attempt_status(st):
                        continue
                    attempts += 1
                    if st == "solved":
                        solved += 1
                        rt = safe_float(r.get("measured_total_sec", ""))
                        if rt is None:
                            rt = safe_float(r.get("reported_total_sec", ""))
                        if rt is None:
                            rt = safe_float(r.get("reported_planning_sec", ""))
                        if rt is not None and rt >= 0:
                            solved_runtimes.append(rt)
                runtime_solved_median = percentile(sorted(solved_runtimes), 0.5) if solved_runtimes else None
                outcomes[(d, s, m)] = (solved, attempts, runtime_solved_median)

    # Fastest fully-solved runtime per level/map (ties are all highlighted).
    fastest_solved_runtime_by_map: Dict[str, Optional[float]] = {}
    for m in maps:
        solved_vals: List[float] = []
        for d in domains:
            for s in settings_by_domain[d]:
                solved, attempts, solved_runtime_sec = outcomes[(d, s, m)]
                if attempts > 0 and solved == attempts and solved_runtime_sec is not None:
                    solved_vals.append(solved_runtime_sec)
        fastest_solved_runtime_by_map[m] = min(solved_vals) if solved_vals else None

    width = max(1400, 440 + 86 * len(maps))
    height = max(860, 220 + 24 * len(row_entries))
    left = 440
    top = 100
    right = 150
    bottom = 130
    cw = width - left - right
    ch = height - top - bottom
    cell_w = cw / max(1, len(maps))
    cell_h = ch / max(1, len(row_entries))

    lines = svg_start(
        width,
        height,
        "Solved vs Unsolved Heatmap (Domain Sections + Setting Rows, Levels on X)",
        subtitle,
    )
    fastest_border_overlays: List[str] = []

    for ri, (kind, domain, setting_name) in enumerate(row_entries):
        y = top + ri * cell_h
        if kind == "domain":
            lines.append(
                f'<rect x="{left-6:.1f}" y="{y:.1f}" width="{cw+6:.1f}" height="{cell_h:.1f}" fill="#f0f4f8" stroke="#d7dee6" stroke-width="0.7"/>'
            )
            lines.append(
                f'<text x="{left-12:.1f}" y="{y+cell_h*0.67:.1f}" text-anchor="end" font-size="10.8" font-family="Arial, sans-serif" fill="#0f172a">{html.escape(domain)}</text>'
            )
            continue

        lines.append(
            f'<text x="{left-12:.1f}" y="{y+cell_h*0.68:.1f}" text-anchor="end" font-size="9.2" font-family="Arial, sans-serif" fill="#111">- {html.escape(setting_name)}</text>'
        )
        for mi, map_name in enumerate(maps):
            x = left + mi * cell_w
            solved, attempts, solved_runtime_sec = outcomes[(domain, setting_name, map_name)]
            if attempts == 0:
                fill = "rgb(232,232,232)"
                text = "NA"
            else:
                rate = solved / attempts
                fill = red_yellow_green(rate)
                if solved == attempts:
                    text = f"{solved_runtime_sec:.2f}s" if solved_runtime_sec is not None else "S"
                elif solved == 0:
                    text = "U"
                else:
                    text = f"{rate*100:.0f}%"

            is_fastest = (
                solved_runtime_sec is not None
                and solved == attempts
                and fastest_solved_runtime_by_map.get(map_name) is not None
                and abs(solved_runtime_sec - fastest_solved_runtime_by_map[map_name]) <= 1e-9
            )
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_w:.1f}" height="{cell_h:.1f}" fill="{fill}" stroke="#ddd" stroke-width="0.6"/>'
            )
            lines.append(
                f'<text x="{x+cell_w/2:.1f}" y="{y+cell_h*0.64:.1f}" text-anchor="middle" font-size="8.7" font-family="Arial, sans-serif" fill="#1f2937">{text}</text>'
            )
            if is_fastest:
                # Draw highlighted borders in a second pass so they are never overpainted by neighboring cell borders.
                fastest_border_overlays.append(
                    f'<rect x="{x+0.8:.1f}" y="{y+0.8:.1f}" width="{max(0.0, cell_w-1.6):.1f}" height="{max(0.0, cell_h-1.6):.1f}" '
                    f'fill="none" stroke="#0b5fff" stroke-width="2.0"/>'
                )

    lines.extend(fastest_border_overlays)

    lines.append(
        f'<rect x="{left:.1f}" y="{top:.1f}" width="{cw:.1f}" height="{ch:.1f}" fill="none" stroke="#111" stroke-width="1"/>'
    )

    for mi, map_name in enumerate(maps):
        x = left + (mi + 0.5) * cell_w
        lines.append(
            f'<text x="{x:.1f}" y="{top-8:.1f}" text-anchor="end" transform="rotate(-40 {x:.1f} {top-8:.1f})" '
            f'font-size="9.2" font-family="Arial, sans-serif" fill="#111">{html.escape(map_name)}</text>'
        )

    legend_items = [
        ("Solved", red_yellow_green(1.0)),
        ("Unsolved", red_yellow_green(0.0)),
        ("Mixed", red_yellow_green(0.5)),
        ("No data", "rgb(232,232,232)"),
    ]
    draw_legend(
        lines,
        items=legend_items,
        x=left + cw + 18,
        y=top + 8,
        title="Cell Meaning",
        marker="rect",
    )
    legend_x = left + cw + 18
    legend_y = top + 8 + 18 + 16 * len(legend_items) + 8
    lines.append(
        f'<rect x="{legend_x:.1f}" y="{legend_y-10:.1f}" width="12" height="12" fill="white" stroke="#0b5fff" stroke-width="2"/>'
    )
    lines.append(
        f'<text x="{legend_x+18:.1f}" y="{legend_y:.1f}" font-size="12" font-family="Arial, sans-serif" fill="#111">Fastest solved (per level)</text>'
    )

    svg_finish(lines, out_path)


def plot_time_breakdown(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    settings = sorted(set(r["_setting"] for r in rows))
    components = [
        ("reported_grounding_sec", "Grounding", "#4e79a7"),
        ("reported_heuristic_sec", "Heuristic", "#59a14f"),
        ("reported_search_sec", "Search", "#e15759"),
        ("reported_planning_sec", "Planning", "#f28e2b"),
    ]
    medians: Dict[str, Dict[str, float]] = {s: {} for s in settings}
    for s in settings:
        group = [r for r in rows if r["_setting"] == s]
        for key, _, _ in components:
            vals = [safe_float(r.get(key, "")) for r in group]
            vals = [v for v in vals if v is not None and v >= 0]
            medians[s][key] = percentile(sorted(vals), 0.5) if vals else 0.0
    settings = [s for s in settings if any(medians[s][k] > 0 for k, _, _ in components)]
    if not settings:
        return
    ymax = 1.0
    for s in settings:
        ymax = max(ymax, sum(medians[s][k] for k, _, _ in components))
    ymax = nice_max(ymax * 1.2)

    width = max(1120, 250 + 105 * len(settings))
    height = 600
    left = 90
    top = 92
    right = 260
    bottom = 170
    cw = width - left - right
    ch = height - top - bottom
    lines = svg_start(width, height, "Median Reported Time Breakdown By Setting", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#ececec"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{(frac*ymax):.1f}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    step = cw / max(1, len(settings))
    bw = min(56.0, step * 0.68)
    for i, s in enumerate(settings):
        x = left + (i + 0.5) * step - bw / 2.0
        cum = 0.0
        for key, _, color in components:
            v = medians[s][key]
            if v <= 0:
                continue
            y_top = top + ch - ((cum + v) / ymax) * ch
            h = (v / ymax) * ch
            lines.append(
                f'<rect x="{x:.1f}" y="{y_top:.1f}" width="{bw:.1f}" height="{h:.1f}" fill="{color}" stroke="#111" stroke-width="0.5"/>'
            )
            cum += v
        lines.append(
            f'<text x="{x+bw/2:.1f}" y="{top+ch+16:.1f}" text-anchor="middle" transform="rotate(55 {x+bw/2:.1f} {top+ch+16:.1f})" '
            f'font-size="10" font-family="Arial, sans-serif" fill="#111">{html.escape(s)}</text>'
        )
    draw_legend(
        lines,
        items=[(label, color) for _, label, color in components],
        x=left + cw + 20,
        y=top + 8,
        title="Time Components",
        marker="rect",
    )
    svg_finish(lines, out_path)


def plot_cumulative_status(rows: Sequence[Dict[str, str]], out_path: Path, subtitle: str) -> None:
    filtered = [r for r in rows if safe_int(r.get("run_id", "")) is not None]
    if not filtered:
        return
    ordered = sorted(filtered, key=lambda r: safe_int(r.get("run_id", "")) or 0)
    solved_cum: List[Tuple[int, int]] = []
    timeout_cum: List[Tuple[int, int]] = []
    error_cum: List[Tuple[int, int]] = []
    s = t = e = 0
    for idx, r in enumerate(ordered, start=1):
        st = r["_status"]
        if st == "solved":
            s += 1
        if st == "timeout":
            t += 1
        if st == "error":
            e += 1
        solved_cum.append((idx, s))
        timeout_cum.append((idx, t))
        error_cum.append((idx, e))
    x_max = len(ordered)
    y_max = nice_max(max(s, t, e, 1))

    width = 1100
    height = 580
    left = 90
    top = 92
    right = 220
    bottom = 90
    cw = width - left - right
    ch = height - top - bottom

    lines = svg_start(width, height, "Cumulative Status Over Run Order", subtitle)
    for i in range(6):
        frac = i / 5.0
        y = top + ch - frac * ch
        v = frac * y_max
        lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+cw}" y2="{y:.1f}" stroke="#efefef"/>')
        lines.append(
            f'<text x="{left-10}" y="{y+4:.1f}" text-anchor="end" font-size="11" font-family="Arial, sans-serif" fill="#444">{int(round(v))}</text>'
        )
    for i in range(6):
        frac = i / 5.0
        x = left + frac * cw
        v = frac * x_max
        lines.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+ch}" stroke="#f5f5f5"/>')
        lines.append(
            f'<text x="{x:.1f}" y="{top+ch+18:.1f}" text-anchor="middle" font-size="10" font-family="Arial, sans-serif" fill="#444">{int(round(v))}</text>'
        )
    lines.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')
    lines.append(f'<line x1="{left}" y1="{top+ch}" x2="{left+cw}" y2="{top+ch}" stroke="#111" stroke-width="1.4"/>')

    def draw_series(name: str, series: Sequence[Tuple[int, int]], color: str) -> None:
        pts = []
        for x_idx, yv in series:
            x = lin_map(x_idx, 1, x_max, left, left + cw)
            y = lin_map(yv, 0, y_max, top + ch, top)
            pts.append((x, y))
        lines.append(
            f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="none" stroke="{color}" stroke-width="2.0"/>'
        )

    draw_series("solved", solved_cum, "#2ca02c")
    draw_series("timeout", timeout_cum, "#d62728")
    draw_series("error", error_cum, "#8c564b")
    draw_legend(
        lines,
        items=[("solved", "#2ca02c"), ("timeout", "#d62728"), ("error", "#8c564b")],
        x=left + cw + 18,
        y=top + 8,
        title="Cumulative",
        marker="rect",
    )
    svg_finish(lines, out_path)


def write_plot_manifest(out_dir: Path, generated: Sequence[Path]) -> None:
    lines = ["Generated plots:"]
    for p in generated:
        lines.append(f"- {p.name}")
    (out_dir / "PLOTS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_chart_calls(rows: Sequence[Dict[str, str]], subtitle: str) -> List[Tuple[str, Callable[[Path], None]]]:
    return [
        ("status_by_setting.svg", lambda p: plot_status_by_setting(rows, p, subtitle)),
        ("success_rate_by_setting.svg", lambda p: plot_success_rate(rows, p, subtitle)),
        ("status_by_domain.svg", lambda p: plot_status_by_domain(rows, p, subtitle)),
        ("success_rate_by_domain.svg", lambda p: plot_success_rate_by_domain(rows, p, subtitle)),
        ("success_rate_by_domain_family.svg", lambda p: plot_success_rate_by_domain_family(rows, p, subtitle)),
        ("runtime_box_by_domain_family.svg", lambda p: plot_runtime_box_by_domain_family(rows, p, subtitle)),
        ("runtime_vs_cells_by_domain_family.svg", lambda p: plot_runtime_vs_cells_by_domain_family(rows, p, subtitle)),
        ("success_rate_by_scanner_mode.svg", lambda p: plot_success_rate_by_domain_scanner(rows, p, subtitle)),
        ("success_rate_by_layout_mode.svg", lambda p: plot_success_rate_by_domain_layout(rows, p, subtitle)),
        (
            "success_rate_heatmap_domain_family_x_variant.svg",
            lambda p: plot_success_rate_heatmap_domain_family_x_variant(rows, p, subtitle),
        ),
        (
            "runtime_heatmap_domain_family_x_variant.svg",
            lambda p: plot_runtime_heatmap_domain_family_x_variant(rows, p, subtitle),
        ),
        (
            "runtime_box_by_setting.svg",
            lambda p: plot_box_by_setting(
                rows,
                p,
                subtitle,
                title="Measured Runtime Distribution By Setting",
                value_fn=lambda r: safe_float(r.get("measured_total_sec", "")),
                y_label="Measured Runtime (sec)",
            ),
        ),
        (
            "runtime_box_by_domain.svg",
            lambda p: plot_box_by_domain(
                rows,
                p,
                subtitle,
                title="Measured Runtime Distribution By Domain",
                value_fn=lambda r: safe_float(r.get("measured_total_sec", "")),
                y_label="Measured Runtime (sec)",
            ),
        ),
        ("runtime_cdf_by_setting.svg", lambda p: plot_runtime_cdf(rows, p, subtitle)),
        ("runtime_vs_cells_by_setting.svg", lambda p: plot_runtime_vs_cells(rows, p, subtitle)),
        ("runtime_vs_cells_by_domain.svg", lambda p: plot_runtime_vs_cells_by_domain(rows, p, subtitle)),
        ("runtime_grounding_vs_cells.svg", lambda p: plot_runtime_grounding_vs_cells(rows, p, subtitle)),
        (
            "runtime_grounding_vs_cells_by_domain.svg",
            lambda p: plot_runtime_grounding_vs_cells_by_domain(rows, p, subtitle),
        ),
        (
            "runtime_grounding_vs_cells_by_domain_loglog.svg",
            lambda p: plot_runtime_grounding_vs_cells_by_domain_loglog(rows, p, subtitle),
        ),
        ("action_literals_vs_cells.svg", lambda p: plot_action_literals_vs_cells(rows, p, subtitle)),
        ("runtime_vs_cells_by_phase.svg", lambda p: plot_runtime_vs_cells_by_phase(rows, p, subtitle)),
        ("runtime_heatmap_domain_x_setting.svg", lambda p: plot_runtime_heatmap_domain_x_setting(rows, p, subtitle)),
        (
            "search_vs_grounding_scatter.svg",
            lambda p: plot_scatter(
                rows,
                p,
                subtitle,
                title="Reported Search vs Grounding Time",
                x_fn=lambda r: safe_float(r.get("reported_grounding_sec", "")),
                y_fn=lambda r: safe_float(r.get("reported_search_sec", "")),
                x_label="Reported Grounding Time (sec)",
                y_label="Reported Search Time (sec)",
            ),
        ),
        (
            "plan_length_vs_runtime_scatter.svg",
            lambda p: plot_scatter(
                [r for r in rows if r["_status"] == "solved"],
                p,
                subtitle,
                title="Plan Length vs Measured Runtime (Solved Runs)",
                x_fn=lambda r: safe_float(r.get("plan_action_count", "")),
                y_fn=lambda r: safe_float(r.get("measured_total_sec", "")),
                x_label="Plan Action Count",
                y_label="Measured Runtime (sec)",
            ),
        ),
        (
            "nodes_per_second_box_by_setting.svg",
            lambda p: plot_box_by_setting(
                rows,
                p,
                subtitle,
                title="Nodes/sec Distribution By Setting",
                value_fn=lambda r: safe_float(r.get("nodes_per_second", "")),
                y_label="Nodes per second",
            ),
        ),
        ("timeout_heatmap_domain_x_setting.svg", lambda p: plot_timeout_heatmap(rows, p, subtitle)),
        (
            "outcome_heatmap_domain_map_x_setting.svg",
            lambda p: plot_outcome_heatmap_domain_map_x_setting(rows, p, subtitle),
        ),
        ("time_breakdown_stacked_by_setting.svg", lambda p: plot_time_breakdown(rows, p, subtitle)),
        ("cumulative_status_by_run_order.svg", lambda p: plot_cumulative_status(rows, p, subtitle)),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate many SVG plots from config-matrix benchmark CSV.")
    ap.add_argument("--csv", type=Path, required=True, help="Path to benchmark_matrix.csv")
    ap.add_argument("--out-dir", type=Path, required=True, help="Output directory for SVG plots")
    ap.add_argument("--title-prefix", default="Config Matrix", help="Subtitle prefix")
    args = ap.parse_args()

    csv_path = args.csv.resolve()
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    rows = load_rows(csv_path)
    for r in rows:
        annotate_row(r)
    subtitle = f"{args.title_prefix} | {csv_path}"

    generated: List[Path] = []
    chart_calls = build_chart_calls(rows, subtitle)

    for filename, fn in chart_calls:
        out_path = out_dir / filename
        try:
            fn(out_path)
            if out_path.exists():
                generated.append(out_path)
        except Exception as exc:
            print(f"[WARN] Failed to generate {filename}: {exc}")

    section_specs: List[Tuple[str, str]] = [
        ("custom", "custom"),
        ("random-repeat", "repeats"),
        ("growth", "growth"),
    ]
    for phase_name, section_tag in section_specs:
        phase_rows = [r for r in rows if r["_phase"] == phase_name]
        if not phase_rows:
            continue
        section_subtitle = f"{subtitle} | section={phase_name}"
        for filename, fn in build_chart_calls(phase_rows, section_subtitle):
            out_path = out_dir / f"section_{section_tag}_{filename}"
            try:
                fn(out_path)
                if not out_path.exists():
                    write_no_data_plot(
                        out_path,
                        title=f"Section {phase_name}: {filename}",
                        subtitle=section_subtitle,
                    )
                generated.append(out_path)
            except Exception as exc:
                print(f"[WARN] Failed to generate {out_path.name}: {exc}")
                write_no_data_plot(
                    out_path,
                    title=f"Section {phase_name}: {filename}",
                    subtitle=section_subtitle,
                    message=f"Plot generation failed: {exc}",
                )
                generated.append(out_path)

    write_plot_manifest(out_dir, generated)
    print(f"[OK] Generated {len(generated)} plots in {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
