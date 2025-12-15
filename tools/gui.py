#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from common import repo_root


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Stones & Gems GUI.")
    ap.add_argument("--level", type=Path, default=None, help="path to level file (optional)")
    ap.add_argument("--gui-bin", type=Path, default=repo_root() / "stonesandgem" / "build" / "bin" / "gui")
    ap.add_argument("--cwd", type=Path, default=repo_root())
    args = ap.parse_args()

    gui_bin = args.gui_bin.resolve()
    if not gui_bin.exists():
        print(f"[ERR] GUI binary not found: {gui_bin}")
        print("      Build your game first (e.g. via your Makefile) so ./stonesandgem/build/bin/gui exists.")
        return 1

    cmd = [str(gui_bin)]
    if args.level:
        cmd.append(str(args.level.resolve()))

    # Run interactively, inheriting stdin/out/err
    p = subprocess.run(cmd, cwd=str(args.cwd.resolve()))
    return p.returncode


if __name__ == "__main__":
    raise SystemExit(main())
