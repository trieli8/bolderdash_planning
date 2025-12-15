#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class PlanResult:
    planner: str
    domain: str
    problem: str
    status: str  # "solved" | "unsolved" | "error"
    actions: List[Tuple[str, List[str]]]  # [("move", ["a","c1","c2"]), ...]
    raw_stdout: str
    raw_stderr: str
    metrics: dict


def repo_root() -> Path:
    # Assumes tools/ is at repo_root/tools/
    return Path(__file__).resolve().parents[1]


def ensure_executable(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    if os.name != "nt" and not os.access(path, os.X_OK):
        raise PermissionError(f"Not executable: {path} (try: chmod +x {path})")


def run_cmd(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_sec: Optional[int] = None,
) -> Tuple[int, str, str]:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec,
    )
    return p.returncode, p.stdout, p.stderr


def parse_sexp_action(line: str) -> Optional[Tuple[str, List[str]]]:
    """
    Accepts lines like:
      (move a c1 c2)
      0: (move a c1 c2)
    Returns ("move", ["a","c1","c2"])
    """
    line = line.strip()
    m = re.search(r"\(\s*([^\s()]+)\s*([^()]*)\)", line)
    if not m:
        return None
    name = m.group(1).strip()
    rest = m.group(2).strip()
    args = [tok for tok in rest.split() if tok]
    return name, args


def write_plan_outputs(out_dir: Path, result: PlanResult) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # Plain text: one action per line in sexp form
    txt_path = out_dir / "plan.txt"
    with txt_path.open("w", encoding="utf-8") as f:
        f.write(f"; planner={result.planner}\n")
        f.write(f"; domain={result.domain}\n")
        f.write(f"; problem={result.problem}\n")
        f.write(f"; status={result.status}\n")
        for (name, args) in result.actions:
            f.write("(" + " ".join([name] + args) + ")\n")

    # JSON
    json_path = out_dir / "plan.json"
    payload = {
        "planner": result.planner,
        "domain": result.domain,
        "problem": result.problem,
        "status": result.status,
        "actions": [{"name": n, "args": a} for (n, a) in result.actions],
        "metrics": result.metrics,
    }
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Raw logs
    (out_dir / "raw_stdout.log").write_text(result.raw_stdout or "", encoding="utf-8")
    (out_dir / "raw_stderr.log").write_text(result.raw_stderr or "", encoding="utf-8")
