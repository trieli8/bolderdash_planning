#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

LEVEL_INPUT="${1:-pddl/level_5_5.txt}"
RESULTS_INPUT="${2:-}"

PYTHON_BIN="${PYTHON_BIN:-python3}"
TIMEOUT="${TIMEOUT:-120}"
CLASSIC_PLANNER="${CLASSIC_PLANNER:-fd}"   # ff | fd | both
PLUS_PLANNER="${PLUS_PLANNER:-auto}"       # auto | enhsp | optic | cmd
DRY_RUN="${DRY_RUN:-0}"                    # 1 to print commands without running

if [[ "$LEVEL_INPUT" = /* ]]; then
  LEVEL_PATH="$LEVEL_INPUT"
else
  LEVEL_PATH="$REPO_ROOT/$LEVEL_INPUT"
fi

if [[ ! -f "$LEVEL_PATH" ]]; then
  echo "[ERR] Level file not found: $LEVEL_PATH" >&2
  exit 2
fi

if [[ ! "$TIMEOUT" =~ ^[0-9]+$ ]]; then
  echo "[ERR] TIMEOUT must be an integer number of seconds. Got: $TIMEOUT" >&2
  exit 2
fi

if [[ ! "$CLASSIC_PLANNER" =~ ^(ff|fd|both)$ ]]; then
  echo "[ERR] CLASSIC_PLANNER must be one of: ff, fd, both. Got: $CLASSIC_PLANNER" >&2
  exit 2
fi

if [[ ! "$PLUS_PLANNER" =~ ^(auto|enhsp|optic|cmd)$ ]]; then
  echo "[ERR] PLUS_PLANNER must be one of: auto, enhsp, optic, cmd. Got: $PLUS_PLANNER" >&2
  exit 2
fi

now_epoch() {
  "$PYTHON_BIN" -c 'import time; print(time.time())'
}

elapsed_sec() {
  "$PYTHON_BIN" - "$1" "$2" <<'PY'
import sys
start = float(sys.argv[1])
end = float(sys.argv[2])
print(f"{max(0.0, end - start):.3f}")
PY
}

stamp="$(date +%Y%m%d_%H%M%S)"
if [[ -n "$RESULTS_INPUT" ]]; then
  if [[ "$RESULTS_INPUT" = /* ]]; then
    RESULTS_DIR="$RESULTS_INPUT"
  else
    RESULTS_DIR="$REPO_ROOT/$RESULTS_INPUT"
  fi
else
  RESULTS_DIR="$REPO_ROOT/results/all-domains-level-reduce/run_$stamp"
fi

mkdir -p "$RESULTS_DIR"

DOMAINS=()
while IFS= read -r rel_domain; do
  DOMAINS+=("$rel_domain")
done < <(cd "$REPO_ROOT" && ls pddl/domain*.pddl 2>/dev/null | sort)
if [[ "${#DOMAINS[@]}" -eq 0 ]]; then
  echo "[ERR] No domain files matched pddl/domain*.pddl" >&2
  exit 2
fi

SUMMARY_CSV="$RESULTS_DIR/summary.csv"
echo "domain,runner,planner,runtime_sec,exit_code,stdout,stderr" > "$SUMMARY_CSV"

echo "Level: $LEVEL_PATH"
echo "Domains: ${#DOMAINS[@]}"
echo "Timeout: ${TIMEOUT}s"
echo "Results: $RESULTS_DIR"
echo

failures=0
index=0
total="${#DOMAINS[@]}"

for rel_domain in "${DOMAINS[@]}"; do
  index=$((index + 1))
  domain_path="$REPO_ROOT/$rel_domain"
  domain_name="$(basename "$domain_path")"
  domain_stem="${domain_name%.pddl}"

  stdout_file="$RESULTS_DIR/${domain_stem}.stdout.txt"
  stderr_file="$RESULTS_DIR/${domain_stem}.stderr.txt"

  if [[ "$domain_name" == *plus* ]]; then
    runner="plan_plus.py"
    planner="$PLUS_PLANNER"
    cmd=(
      "$PYTHON_BIN" "$REPO_ROOT/tools/plan_plus.py"
      --domain "$domain_path"
      --problem "$LEVEL_PATH"
      --planner "$PLUS_PLANNER"
      --timeout "$TIMEOUT"
    )
  else
    runner="plan.py"
    planner="$CLASSIC_PLANNER"
    cmd=(
      "$PYTHON_BIN" "$REPO_ROOT/tools/plan.py"
      --planner "$CLASSIC_PLANNER"
      --domain "$domain_path"
      --problem "$LEVEL_PATH"
      --timeout "$TIMEOUT"
    )
  fi

  echo "[$index/$total] $domain_name"
  echo "  runner: $runner ($planner)"

  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  DRY_RUN=1 -> ${cmd[*]}"
    rc=0
    runtime_sec="0.000"
    : > "$stdout_file"
    : > "$stderr_file"
  else
    start_ts="$(now_epoch)"
    if "${cmd[@]}" >"$stdout_file" 2>"$stderr_file"; then
      rc=0
    else
      rc=$?
      failures=$((failures + 1))
    fi
    end_ts="$(now_epoch)"
    runtime_sec="$(elapsed_sec "$start_ts" "$end_ts")"
  fi

  echo "  runtime: ${runtime_sec}s"
  echo "  exit: $rc"
  printf "%s,%s,%s,%s,%d,%s,%s\n" \
    "$domain_name" \
    "$runner" \
    "$planner" \
    "$runtime_sec" \
    "$rc" \
    "$stdout_file" \
    "$stderr_file" >> "$SUMMARY_CSV"
done

echo
echo "Batch run complete."
echo "Summary CSV: $SUMMARY_CSV"
echo "Failed runs: $failures/$total"

if [[ "$failures" -gt 0 ]]; then
  exit 1
fi

exit 0
