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
import problem_gen_rowscan as rowscan_gen  # type: ignore  # noqa: E402
import problem_gen_cellscan as cellscan_gen  # type: ignore  # noqa: E402
import problem_gen_orderfree as orderfree_gen  # type: ignore  # noqa: E402


SOURCE_TO_KIND = {
    "domain.pddl": "classic",
    "domain_merged.pddl": "classic",
    "domain_scanner_combined.pddl": "classic",
    "domain_scanner_separated.pddl": "scanner_separated",
    "domain_plus_from_domain.pddl": "plus_from_domain",
    "domain_plus_scanner_separated.pddl": "plus_scanner",
    "domain_plus_scanner_separated_events.pddl": "plus_scanner",
    "domain_plus_scanner_separated_events_fluents.pddl": "plus_scanner_events_fluents",
    "domain_rowscan.pddl": "rowscan",
    "domain_cellscan_separated.pddl": "cellscan",
    "domain_orderfree_combined.pddl": "orderfree",
    "domain_orderfree_separated.pddl": "orderfree",
}

SCANNER_CHAIN_PREDICATES = ("first-cell", "next-cell", "last-cell")
OPTIONAL_DOMAIN_PREDICATES = ("update-required", "crushed")
PREDICATE_COMPAT_RENAMES = (
    ("update-required", "tick-active"),
    ("crushed", "agent-crushed"),
)


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


def _resolve_domain_path(domain_filename: str) -> Path:
    domain_path = THIS_DIR / domain_filename
    if domain_path.exists():
        return domain_path

    # Classic matrix files on disk are named domain_classic_*, while the
    # generated wrapper names and `; variant:` headers omit the classic marker.
    if (
        domain_filename.startswith("domain_")
        and not domain_filename.startswith(("domain_classic_", "domain_FA_", "domain_plus_"))
    ):
        classic_alias = THIS_DIR / f"domain_classic_{domain_filename[len('domain_'):]}"
        if classic_alias.exists():
            return classic_alias

    return domain_path


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


def _strip_predicate_facts(problem_pddl: str, predicate: str) -> str:
    out_lines = []
    # Remove both positive and negated literals, e.g.:
    #   (update-required)
    #   (not (update-required))
    pattern = re.compile(rf"\(\s*(?:not\s+\(\s*)?{re.escape(predicate)}\b")
    for line in problem_pddl.splitlines():
        if pattern.search(line):
            continue
        out_lines.append(line)
    if not out_lines:
        return ""
    return "\n".join(out_lines) + "\n"


def _rename_predicate_facts(problem_pddl: str, src_predicate: str, dst_predicate: str) -> str:
    # Handles both positive and negated atoms by replacing predicate heads.
    pattern = re.compile(rf"(\(\s*(?:not\s+\(\s*)?){re.escape(src_predicate)}(\b)")
    return pattern.sub(rf"\1{dst_predicate}\2", problem_pddl)


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
    if kind == "rowscan":
        return rowscan_gen.generate_problem(level_str, problem_name, domain_name)
    if kind == "cellscan":
        return cellscan_gen.generate_problem(level_str, problem_name, domain_name)
    if kind == "orderfree":
        return orderfree_gen.generate_problem(level_str, problem_name, domain_name)
    raise ValueError(f"Unsupported generator kind: {kind}")


# ---------------------------------------------------------------------------
# multi-gem variants (domain_*_multigem.pddl, written by make_target_variants.py)
# ---------------------------------------------------------------------------

MULTIGEM_KINDS = {"rowscan", "cellscan", "orderfree"}
UNMARK = {classic_gen.TARGET_GEM_STATIC_ID: 5, classic_gen.TARGET_GEM_FALLING_ID: 6}


def _multigem_targets(level_text: str, ordinals: list[int]) -> tuple[str, list[tuple[int, int]]]:
    """Return the level with every target marker turned back into a plain gem,
    and the target positions (0-based row, col) in row-major order.

    Targets are the gems marked 90/91 in the level, the gem named by a
    `; target-gem-ordinal:` line, and the gems named by `ordinals` (row-major
    gem ordinals, counting from 1, as in the test-problem file names)."""
    level_str, meta = classic_gen.parse_level_text(level_text)
    rows, cols, max_time, required, ids = classic_gen.parse_level_string(level_str)
    gems = [i for i, cid in enumerate(ids) if classic_gen.classify_cell_id(cid) == "gem"]
    targets = {i for i in gems if ids[i] in classic_gen.TARGET_GEM_IDS}
    for o in ordinals + ([meta.target_gem_ordinal] if meta.target_gem_ordinal else []):
        if not 1 <= o <= len(gems):
            raise ValueError(f"target gem ordinal {o} is out of range for {len(gems)} gems")
        targets.add(gems[o - 1])
    if not targets:
        raise ValueError("no target gems: mark them 90/91 in the level or pass --targets")
    plain = [UNMARK.get(cid, cid) for cid in ids]
    level = "|".join([str(rows), str(cols), str(max_time), str(required)] + [f"{c:02d}" for c in plain])
    if meta.start_gem_ordinal:
        level = f"; start-gem-ordinal: {meta.start_gem_ordinal}\n{level}"
    return level, [divmod(i, cols) for i in sorted(targets)]


def _to_multigem(pddl: str, level: str, targets: list[tuple[int, int]]) -> str:
    """Rewrite a single-target problem for the multigem domain: one `target`
    object per target gem, (target-gem <cell> tK) instead of the generator's own
    (target-gem <cell>), and (collected tK) for every target in the goal."""
    prepared = classic_gen.prepare_level(level)
    names = [f"t{k + 1}" for k in range(len(targets))]
    head, kw, goal = pddl.partition("(:goal")
    if not kw or "(got-gem)" not in goal:
        raise ValueError("generator output has no (got-gem) goal")
    goal = goal.replace("(got-gem)", " ".join(f"(collected {n})" for n in names), 1)
    # drop the generator's own target marker / got-gem fact
    head = re.sub(r"^[ \t]*\((?:got-gem|target-gem [^()\s]+)\)[ \t]*\n", "", head, flags=re.MULTILINE)
    head = re.sub(r"\((?:got-gem|target-gem [^()\s]+)\)", "", head)
    init = []
    for n, (r, c) in zip(names, targets):
        if (r, c) == prepared.agent_pos:  # the agent starts on it (start-gem levels)
            init.append(f"(collected {n})")
            continue
        if classic_gen.classify_cell_id(prepared.cell_ids[r * prepared.cols + c]) != "gem":
            raise ValueError(f"target {n} at row {r}, column {c} is not a gem")
        cell = f"c_{r + 1}_{c + 1}"  # every generator pads the level by one cell
        if not re.search(rf"\(gem {cell}\)", head):
            raise ValueError(f"target {n}: no (gem {cell}) in the generated problem")
        init.append(f"(target-gem {cell} {n})")
    if "(:objects\n" not in head or "(:init\n" not in head:
        raise ValueError("unexpected generator output layout")
    head = head.replace("(:objects\n", f"(:objects\n    {' '.join(names)} - target\n", 1)
    head = head.replace("(:init\n", "(:init\n" + "".join(f"    {a}\n" for a in init), 1)
    return head + kw + goal


def _plain_level(level_text: str) -> str:
    """The level with every target marker turned back into a plain gem (keeps a start-gem line)."""
    level_str, meta = classic_gen.parse_level_text(level_text)
    rows, cols, max_time, required, ids = classic_gen.parse_level_string(level_str)
    plain = [UNMARK.get(cid, cid) for cid in ids]
    level = "|".join([str(rows), str(cols), str(max_time), str(required)] + [f"{c:02d}" for c in plain])
    if meta.start_gem_ordinal:
        level = f"; start-gem-ordinal: {meta.start_gem_ordinal}\n{level}"
    return level


def _to_gemcount(pddl: str, level: str, collect: str) -> str:
    """Rewrite a single-target problem for the gemcount domain (as on main, 85adeaa):
    counter objects gems_0..gems_n, (gem-count-next gems_n gems_n), goal
    (gems-collected gems_n); the generator's own target marker is dropped."""
    prepared = classic_gen.prepare_level(level)
    gems_on_map = sum(classic_gen.classify_cell_id(c) == "gem" for c in prepared.cell_ids)
    if collect == "level":
        n = prepared.required_gems
        if n < 1:
            raise ValueError(f"collect-gems=level, but the level's required_gems field is {n}")
    else:
        n = int(collect)
        if n < 1:
            raise ValueError(f"collect-gems must be at least 1, got {n}")
    if n > gems_on_map:
        raise ValueError(f"collect-gems={n}, but the level has only {gems_on_map} gems")
    names = [f"gems_{i}" for i in range(n + 1)]
    init = [f"(gems-collected {names[0]})"]
    init += [f"(gem-count-next {a} {b})" for a, b in zip(names, names[1:])]
    init.append(f"(gem-count-next {names[-1]} {names[-1]})")
    head, kw, goal = pddl.partition("(:goal")
    if not kw or "(got-gem)" not in goal:
        raise ValueError("generator output has no (got-gem) goal")
    goal = goal.replace("(got-gem)", f"(gems-collected {names[-1]})", 1)
    head = re.sub(r"^[ \t]*\((?:got-gem|target-gem [^()\s]+)\)[ \t]*\n", "", head, flags=re.MULTILINE)
    head = re.sub(r"\((?:got-gem|target-gem [^()\s]+)\)", "", head)
    if "(:objects\n" not in head or "(:init\n" not in head:
        raise ValueError("unexpected generator output layout")
    head = head.replace("(:objects\n", f"(:objects\n    {' '.join(names)} - gem-count\n", 1)
    head = head.replace("(:init\n", "(:init\n" + "".join(f"    {a}\n" for a in init), 1)
    return head + kw + goal


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
    ap.add_argument("--targets", default="",
                    help="multigem domains: comma-separated row-major gem ordinals (from 1) to make targets, "
                         "in addition to gems marked 90/91 in the level")
    ap.add_argument("--collect-gems", default="",
                    help="gemcount domains: goal is any N gems (N, or 'level' for the level's required_gems)")
    args = ap.parse_args()

    domain_path = _resolve_domain_path(domain_filename)
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
        multigem = _domain_declares_predicate(domain_text, "collected")
        ordinals = [int(x) for x in args.targets.split(",") if x.strip()]
        gemcount = _domain_declares_predicate(domain_text, "gems-collected")
        if gemcount:
            if kind not in MULTIGEM_KINDS:
                raise ValueError(f"gemcount problems are not supported for generator kind '{kind}'")
            if not args.collect_gems:
                raise ValueError("gemcount domain: pass --collect-gems N|level")
            level_str = _plain_level(level_str)
        elif args.collect_gems:
            raise ValueError("--collect-gems needs a gemcount domain (domain_*_gemcount.pddl)")
        if multigem:
            if kind not in MULTIGEM_KINDS:
                raise ValueError(f"multigem problems are not supported for generator kind '{kind}'")
            level_str, targets = _multigem_targets(level_str, ordinals)
        elif ordinals:
            raise ValueError("--targets needs a multigem domain (domain_*_multigem.pddl)")
        pddl = _generate(kind, level_str, args.problem_name, domain_name, args.agent_name)
        if multigem:
            pddl = _to_multigem(pddl, level_str, targets)
        if gemcount:
            pddl = _to_gemcount(pddl, level_str, args.collect_gems)

        # Classic generators currently emit scanner-chain init facts unconditionally.
        # Remove them when the domain variant does not declare these predicates.
        if any(
            not _domain_declares_predicate(domain_text, pred)
            for pred in SCANNER_CHAIN_PREDICATES
        ):
            pddl = _strip_scanner_chain_facts(pddl)
        for src_pred, dst_pred in PREDICATE_COMPAT_RENAMES:
            if (
                not _domain_declares_predicate(domain_text, src_pred)
                and _domain_declares_predicate(domain_text, dst_pred)
            ):
                pddl = _rename_predicate_facts(pddl, src_pred, dst_pred)
        for pred in OPTIONAL_DOMAIN_PREDICATES:
            if not _domain_declares_predicate(domain_text, pred):
                pddl = _strip_predicate_facts(pddl, pred)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1

    sys.stdout.write(pddl)
    return 0
