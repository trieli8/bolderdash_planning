#!/usr/bin/env python3
"""Generate compact PDDL problems for domain_plus_scanner_separated.pddl.

ENHSP is much more stable on the compact untyped encoding used by
problem_gen_plus_from_domain.py, so this scanner-separated plus generator
reuses that layout while targeting the scanner-plus domain name.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from problem_gen_plus_from_domain import generate_compact_problem  # type: ignore  # noqa: E402


def _read_level(level_input: str) -> str:
    if level_input.endswith('.txt'):
        return Path(level_input).read_text(encoding='utf-8').strip()
    return level_input


def main() -> int:
    ap = argparse.ArgumentParser(description='Convert a Stones & Gems level into a compact PDDL+ scanner-separated problem.')
    ap.add_argument('level_input', help='Level string or .txt path')
    ap.add_argument('-p', '--problem-name', default='')
    ap.add_argument('-d', '--domain-name', default='mine-tick-gravity-plus-scanner')
    args = ap.parse_args()

    if not args.problem_name:
        args.problem_name = args.level_input.rsplit('.', 1)[0] if args.level_input.endswith('.txt') else 'level_plus_scanner'

    try:
        level_str = _read_level(args.level_input)
        pddl = generate_compact_problem(level_str, args.problem_name, args.domain_name)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    sys.stdout.write(pddl)

    try:
        Path(f"{args.problem_name}.pddl").write_text(pddl, encoding='utf-8')
    except Exception as exc:
        sys.stderr.write(f"Warning: failed to write {args.problem_name}.pddl: {exc}\n")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
