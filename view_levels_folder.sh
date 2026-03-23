#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VIEWER_BIN="$SCRIPT_DIR/stonesandgem/build/bin/level_folder_viewer"
VIEWER_SRC="$SCRIPT_DIR/stonesandgem/src/level_folder_viewer.cpp"
VIEWER_CMAKE="$SCRIPT_DIR/stonesandgem/CMakeLists.txt"

if [ ! -x "$VIEWER_BIN" ] || [ "$VIEWER_SRC" -nt "$VIEWER_BIN" ] || [ "$VIEWER_CMAKE" -nt "$VIEWER_BIN" ]; then
    make -C "$SCRIPT_DIR" game >/dev/null
fi

exec "$VIEWER_BIN" "$@"
