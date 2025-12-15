from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple


def run_cmd(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_sec: Optional[int] = None,
) -> Tuple[int, str, str]:
    """Run a command and capture stdout/stderr (no live streaming)."""
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout_sec,
    )
    return p.returncode, p.stdout, p.stderr


def run_cmd_streaming(
    cmd: List[str],
    cwd: Optional[Path] = None,
    timeout_sec: Optional[int] = None,
    prefix: str = "",
    live: bool = True,
) -> Tuple[int, str, str]:
    """
    Run a command and (optionally) stream stdout/stderr live to terminal.
    Always returns (returncode, full_stdout, full_stderr).

    If live=False, behaves like run_cmd but still uses Popen.
    Timeout returns code 124.
    """
    start = time.time()
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line buffered
        universal_newlines=True,
    )

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    try:
        # Stream stdout
        while True:
            line = proc.stdout.readline() if proc.stdout else ""
            if line:
                stdout_lines.append(line)
                if live:
                    print(f"{prefix}{line}", end="")
            elif proc.poll() is not None:
                break

            if timeout_sec and (time.time() - start) > timeout_sec:
                proc.kill()
                # Drain anything available quickly
                try:
                    out_rest, err_rest = proc.communicate(timeout=1)
                    if out_rest:
                        stdout_lines.append(out_rest)
                        if live:
                            print(f"{prefix}{out_rest}", end="")
                    if err_rest:
                        stderr_lines.append(err_rest)
                        if live:
                            print(f"{prefix}{err_rest}", end="")
                except Exception:
                    pass
                return 124, "".join(stdout_lines), "".join(stderr_lines)

        # Drain remaining stdout
        if proc.stdout:
            rest = proc.stdout.read()
            if rest:
                stdout_lines.append(rest)
                if live:
                    print(f"{prefix}{rest}", end="")

        # Drain stderr
        if proc.stderr:
            for line in proc.stderr:
                stderr_lines.append(line)
                if live:
                    print(f"{prefix}{line}", end="")

        return proc.returncode, "".join(stdout_lines), "".join(stderr_lines)

    except KeyboardInterrupt:
        proc.kill()
        raise
