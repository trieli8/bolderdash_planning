#!/bin/bash

# Batch script to run plan viewer for all plans of a specified level
# Usage: ./view_plans_batch.sh <level>  e.g., ./view_plans_batch.sh 006x006

if [ $# -ne 1 ]; then
    echo "Usage: $0 <level>  (e.g., 006x006)"
    exit 1
fi

LEVEL=$1
RESULTS_DIR="/Users/elijahlewis/dev/boulderdash_planner/tools/benchmarking/results/config-matrix_20260320_232944_big_boy"
PLANS_DIR="$RESULTS_DIR/plans"
LEVELS_DIR="$RESULTS_DIR/generated-levels"
PLAN_PY="/Users/elijahlewis/dev/boulderdash_planner/tools/plan.py"

LEVEL_FILE="$LEVELS_DIR/generated_${LEVEL}.txt"

if [ ! -f "$LEVEL_FILE" ]; then
    echo "Level file not found: $LEVEL_FILE"
    exit 1
fi

echo "Viewing all plans for level: $LEVEL"

# Find all .play.plan files for this level
# Plan names contain _l_generated_${LEVEL}_
plan_files=$(ls "$PLANS_DIR"/*_l_generated_${LEVEL}_*.play.plan 2>/dev/null)

if [ -z "$plan_files" ]; then
    echo "No plan files found for level $LEVEL"
    exit 1
fi

for plan_file in $plan_files; do
    echo "Running plan viewer for $plan_file with level $LEVEL_FILE"

    # Print the plan file content
    echo "Plan content:"
    cat "$plan_file"
    echo ""

    # Run the plan viewer
    python3 "$PLAN_PY" --play-plan "$plan_file" --play-level "$LEVEL_FILE"

    # Optional: Add a delay or prompt between runs
    echo "Press Enter to continue to next plan..."
    read
done

echo "Batch processing complete for level $LEVEL."