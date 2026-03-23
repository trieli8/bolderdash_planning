#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_ROOT="$SCRIPT_DIR/tools/benchmarking/results"
PLAN_PY="$SCRIPT_DIR/tools/plan.py"

usage() {
    cat <<EOF
Usage:
  $0 [selector] [run_dir]
  $0 --list [run_dir]

Examples:
  $0
  $0 level_custom
  $0 generated_006x006_growth tools/benchmarking/results/config-matrix_20260320_232944_big_boy
  $0 --list

Behavior:
  - Uses the latest config-matrix run when run_dir is omitted.
  - Lists playable selectors from benchmark_matrix.csv.
  - If selector is omitted and the run has exactly one playable selector, it is used automatically.
EOF
}

latest_run_dir() {
    shopt -s nullglob
    local candidates=("$RESULTS_ROOT"/config-matrix_*)
    shopt -u nullglob

    if [ ${#candidates[@]} -eq 0 ]; then
        echo "No config-matrix runs found under $RESULTS_ROOT" >&2
        exit 1
    fi

    ls -1dt "${candidates[@]}" | head -n 1
}

resolve_run_dir() {
    local raw="${1:-}"
    if [ -z "$raw" ]; then
        latest_run_dir
        return
    fi

    if [ -d "$raw" ]; then
        cd "$raw" >/dev/null 2>&1 && pwd
        return
    fi

    if [ -d "$SCRIPT_DIR/$raw" ]; then
        cd "$SCRIPT_DIR/$raw" >/dev/null 2>&1 && pwd
        return
    fi

    echo "Run directory not found: $raw" >&2
    exit 1
}

selector_data() {
    local run_dir="$1"
    local selector="${2:-}"
    local mode="$3"

    python3 - "$run_dir" "$selector" "$mode" <<'PY'
import csv
import re
import sys
from pathlib import Path

run_dir = Path(sys.argv[1]).resolve()
selector_arg = sys.argv[2]
mode = sys.argv[3]
csv_path = run_dir / "benchmark_matrix.csv"

if not csv_path.exists():
    print(f"Missing benchmark_matrix.csv: {csv_path}", file=sys.stderr)
    sys.exit(1)

selectors = {}
with csv_path.open(newline="", encoding="utf-8") as handle:
    reader = csv.DictReader(handle)
    for row in reader:
        plan_path = (row.get("plan_file") or "").strip()
        level_path = (row.get("level") or "").strip()
        if not plan_path.endswith(".plan") or plan_path.endswith(".timed.plan"):
            continue

        play_plan_path = Path(f"{plan_path[:-5]}.play.plan")
        if not play_plan_path.exists():
            continue

        name = play_plan_path.name
        match = re.search(r"_l_(.+?)(?:_rep\d+)?\.play\.plan$", name)
        if not match:
            continue

        selector = match.group(1)
        entry = selectors.setdefault(selector, {"level": level_path, "plans": set()})

        if level_path:
            if entry["level"] and entry["level"] != level_path:
                print(
                    f"Conflicting level paths for selector {selector}: "
                    f"{entry['level']} vs {level_path}",
                    file=sys.stderr,
                )
                sys.exit(1)
            entry["level"] = level_path

        entry["plans"].add(str(play_plan_path))

if not selectors:
    print(f"No playable .play.plan entries found in {csv_path}", file=sys.stderr)
    sys.exit(1)

if mode == "list":
    for selector in sorted(selectors):
        entry = selectors[selector]
        print(f"{selector}\t{len(entry['plans'])}\t{entry['level']}")
    sys.exit(0)

if selector_arg:
    chosen = selector_arg
    if chosen not in selectors:
        available = ", ".join(sorted(selectors))
        print(
            f"Selector not found: {chosen}\nAvailable selectors: {available}",
            file=sys.stderr,
        )
        sys.exit(1)
else:
    if len(selectors) != 1:
        print("Multiple playable selectors found:", file=sys.stderr)
        for selector in sorted(selectors):
            entry = selectors[selector]
            print(
                f"  {selector} ({len(entry['plans'])} plans) -> {entry['level']}",
                file=sys.stderr,
            )
        sys.exit(2)
    chosen = next(iter(selectors))

entry = selectors[chosen]
if not entry["level"]:
    print(f"Could not resolve level file for selector {chosen}", file=sys.stderr)
    sys.exit(1)

print(chosen)
print(entry["level"])
for plan_path in sorted(entry["plans"]):
    print(plan_path)
PY
}

MODE="view"
SELECTOR=""
RUN_DIR_ARG=""

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    --list)
        MODE="list"
        RUN_DIR_ARG="${2:-}"
        if [ $# -gt 2 ]; then
            usage
            exit 1
        fi
        ;;
    "")
        ;;
    *)
        SELECTOR="${1:-}"
        RUN_DIR_ARG="${2:-}"
        if [ $# -gt 2 ]; then
            usage
            exit 1
        fi
        ;;
esac

RUN_DIR="$(resolve_run_dir "$RUN_DIR_ARG")"

if [ ! -f "$PLAN_PY" ]; then
    echo "Plan viewer wrapper not found: $PLAN_PY" >&2
    exit 1
fi

if [ "$MODE" = "list" ]; then
    echo "Run directory: $RUN_DIR"
    echo "Available playable selectors:"
    while IFS=$'\t' read -r selector plan_count level_path; do
        printf '  %s (%s plans) -> %s\n' "$selector" "$plan_count" "$level_path"
    done < <(selector_data "$RUN_DIR" "" list)
    exit 0
fi

resolved=()
selector_output="$(selector_data "$RUN_DIR" "$SELECTOR" view)"
while IFS= read -r line; do
    resolved+=("$line")
done <<EOF
$selector_output
EOF

if [ ${#resolved[@]} -lt 3 ]; then
    echo "Failed to resolve selector data for run: $RUN_DIR" >&2
    exit 1
fi

SELECTOR="${resolved[0]}"
LEVEL_FILE="${resolved[1]}"
PLAN_FILES=("${resolved[@]:2}")

if [ ! -f "$LEVEL_FILE" ]; then
    echo "Level file not found: $LEVEL_FILE" >&2
    exit 1
fi

echo "Run directory: $RUN_DIR"
echo "Selector: $SELECTOR"
echo "Level file: $LEVEL_FILE"
echo "Plans: ${#PLAN_FILES[@]}"

for plan_file in "${PLAN_FILES[@]}"; do
    echo
    echo "Running plan viewer for $plan_file"
    echo "Plan content:"
    cat "$plan_file"
    echo
    python3 "$PLAN_PY" --play-plan "$plan_file" --play-level "$LEVEL_FILE"
    echo "Press Enter to continue to next plan..."
    read -r
done

echo
echo "Batch processing complete for selector $SELECTOR."
