#!/usr/bin/env python3
"""Shared no-write problem generator wrappers for pddl/test_domains domains."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
PDDL_DIR = THIS_DIR.parent
sys.path.insert(0, str(PDDL_DIR))

import problem_gen as classic_gen  # type: ignore  # noqa: E402
import problem_gen_scanner_separated as scanner_sep_gen  # type: ignore  # noqa: E402
import problem_gen_plus_from_domain as plus_from_gen  # type: ignore  # noqa: E402
import problem_gen_plus_scanner_separated as plus_scanner_gen  # type: ignore  # noqa: E402
import problem_gen_plus_scanner_separated_events_fluents as plus_events_fluent_gen  # type: ignore  # noqa: E402


SOURCE_TO_KIND = {
    "domain.pddl": "classic",
    "domain_merged.pddl": "classic",
    "domain_scanner_combined.pddl": "classic",
    "domain_scanner_separated.pddl": "scanner_separated",
    "domain_plus_from_domain.pddl": "plus_from_domain",
    "domain_plus_scanner_separated.pddl": "plus_scanner",
    "domain_plus_scanner_separated_events.pddl": "plus_scanner",
    "domain_plus_scanner_separated_events_fluents.pddl": "plus_scanner_events_fluents",
}

SCANNER_CHAIN_PREDICATES = ("first-cell", "next-cell", "last-cell")


def _read_level(level_input: str) -> str:
    if level_input.endswith(".txt"):
        return Path(level_input).read_text(encoding="utf-8").strip()
    return level_input


def _default_problem_name(level_input: str) -> str:
    if level_input.endswith(".txt"):
        return Path(level_input).stem
    return "level"


def _extract_domain_name(domain_path: Path) -> str:
    text = domain_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"\(define\s*\(domain\s+([^\s\)]+)\)", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not find domain name in {domain_path}")
    return match.group(1)


def _extract_source(domain_path: Path) -> str:
    text = domain_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^;\s*source:\s*(.+)$", text, flags=re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find '; source:' header in {domain_path}")
    return Path(match.group(1).strip()).name


def _domain_declares_predicate(domain_text: str, predicate: str) -> bool:
    return re.search(rf"\(\s*{re.escape(predicate)}(\s|\))", domain_text) is not None


def _strip_scanner_chain_facts(problem_pddl: str) -> str:
    out_lines = []
    for line in problem_pddl.splitlines():
        if re.search(r"\(\s*(first-cell|next-cell|last-cell)\b", line):
            continue
        out_lines.append(line)
    if not out_lines:
        return ""
    return "\n".join(out_lines) + "\n"


def _generate(kind: str, level_str: str, problem_name: str, domain_name: str, agent_name: str) -> str:
    if kind == "classic":
        return classic_gen.generate_pddl_problem(
            level_str,
            problem_name=problem_name,
            domain_name=domain_name,
            agent_name=agent_name,
        )
    if kind == "scanner_separated":
        return scanner_sep_gen.generate_pddl_problem(
            level_str,
            problem_name=problem_name,
            domain_name=domain_name,
            agent_name=agent_name,
        )
    if kind == "plus_from_domain":
        return plus_from_gen.generate_compact_problem(level_str, problem_name, domain_name)
    if kind == "plus_scanner":
        return plus_scanner_gen.generate_compact_problem(level_str, problem_name, domain_name)
    if kind == "plus_scanner_events_fluents":
        return plus_events_fluent_gen.generate_compact_problem(level_str, problem_name, domain_name)
    raise ValueError(f"Unsupported generator kind: {kind}")


def main_for_domain_file(domain_filename: str) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Generate a problem for a pddl/test_domains domain variant and print to stdout only "
            "(does not write files)."
        )
    )
    ap.add_argument("level_input", help="Level string or .txt path")
    ap.add_argument("-p", "--problem-name", default="", help="Problem name (default: derived from level input)")
    ap.add_argument("-d", "--domain-name", default="", help="Override domain name in the generated problem")
    ap.add_argument("-a", "--agent-name", default="player", help="Agent object name for classic generators")
    args = ap.parse_args()

    domain_path = THIS_DIR / domain_filename
    if not domain_path.exists():
        sys.stderr.write(f"Error: missing domain file {domain_path}\n")
        return 1

    if not args.problem_name:
        args.problem_name = _default_problem_name(args.level_input)

    try:
        level_str = _read_level(args.level_input)
        domain_text = domain_path.read_text(encoding="utf-8", errors="replace")
        source_name = _extract_source(domain_path)
        kind = SOURCE_TO_KIND.get(source_name)
        if kind is None:
            raise ValueError(
                f"No generator mapping for source '{source_name}' in {domain_path.name}. "
                "Update SOURCE_TO_KIND in problem_gen_common.py."
            )

        domain_name = args.domain_name or _extract_domain_name(domain_path)
        pddl = _generate(kind, level_str, args.problem_name, domain_name, args.agent_name)

        # Classic generators currently emit scanner-chain init facts unconditionally.
        # Remove them when the domain variant does not declare these predicates.
        if any(
            not _domain_declares_predicate(domain_text, pred)
            for pred in SCANNER_CHAIN_PREDICATES
        ):
            pddl = _strip_scanner_chain_facts(pddl)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    sys.stdout.write(pddl)
    return 0
