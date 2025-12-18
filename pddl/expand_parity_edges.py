#!/usr/bin/env python3
"""
expand_parity_edges_multi.py

Expands selected PDDL actions into even/odd parity copies (and optional edge variants).

Selection:
  --name-regex REGEX     Expand actions whose names match REGEX
  --contains SUBSTRING   Expand actions whose raw action text contains SUBSTRING
  --all-actions          Expand all actions

Parity rule:
  - Template action is assumed "EVEN".
  - ODD copy flips (updated X) <-> (not (updated X)) everywhere in the action.
  - EVEN gets (parity) added to preconditions.
  - ODD gets (not (parity)) added to preconditions.

Edge variants (optional):
  If action contains (right-of ?left ?c)  -> generates -leftedge
  If action contains (right-of ?c ?right) -> generates -rightedge
  If it contains both -> also generates -both-edges
  (The variant is created by removing the literal from preconditions/effects wherever it appears.)
"""

from __future__ import annotations
import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class ActionBlock:
    name: str
    text: str
    start: int
    end: int


def _find_matching_paren(s: str, open_index: int) -> int:
    depth = 0
    for i in range(open_index, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("Unbalanced parentheses while locating action block.")


def extract_all_actions(domain_text: str) -> List[ActionBlock]:
    actions: List[ActionBlock] = []
    for m in re.finditer(r"\(\s*:action\s+([^\s\)]+)", domain_text, flags=re.IGNORECASE):
        start = m.start()
        end = _find_matching_paren(domain_text, start) + 1
        name = m.group(1)
        text = domain_text[start:end]
        actions.append(ActionBlock(name=name, text=text, start=start, end=end))
    return actions


def rename_action(action_text: str, new_name: str) -> str:
    return re.sub(
        r"(\(\s*:action\s+)([^\s\)]+)",
        r"\1" + new_name,
        action_text,
        count=1,
        flags=re.IGNORECASE,
    )


def _inject_parity_precond(action_text: str, parity_literal: str) -> str:
    m = re.search(r"(:precondition\s*)(\()", action_text, flags=re.IGNORECASE)
    if not m:
        raise ValueError("Action has no :precondition.")
    precond_start = m.start(2)
    precond_end = _find_matching_paren(action_text, precond_start) + 1
    precond_expr = action_text[precond_start:precond_end]

    and_m = re.match(r"\(\s*and\b", precond_expr, flags=re.IGNORECASE)
    if and_m:
        insert_at = and_m.end()
        new_precond = precond_expr[:insert_at] + "\n      " + parity_literal + precond_expr[insert_at:]
    else:
        new_precond = f"(and\n      {parity_literal}\n      {precond_expr}\n    )"

    return action_text[:precond_start] + new_precond + action_text[precond_end:]


def flip_updated_literals(action_text: str) -> str:
    placeholder = "__UPDATED_PLACEHOLDER__"

    action_text = re.sub(
        r"\(\s*not\s*\(\s*updated\b([^\)]*)\)\s*\)",
        lambda m: f"({placeholder}{m.group(1)})",
        action_text,
        flags=re.IGNORECASE,
    )

    action_text = re.sub(
        r"\(\s*updated\b([^\)]*)\)",
        lambda m: f"(not (updated{m.group(1)}))",
        action_text,
        flags=re.IGNORECASE,
    )

    action_text = re.sub(
        r"\(" + re.escape(placeholder) + r"([^\)]*)\)",
        lambda m: f"(updated{m.group(1)})",
        action_text,
        flags=re.IGNORECASE,
    )

    return action_text


def drop_literal_everywhere(action_text: str, literal_regex: str) -> str:
    return re.sub(literal_regex, "", action_text, flags=re.IGNORECASE)


def normalize_spacing(s: str) -> str:
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n[ \t]*\n[ \t]*\n+", "\n\n", s)
    return s


def build_variants(template: ActionBlock, make_edges: bool) -> List[str]:
    base = template.text
    base_name = template.name

    # EVEN
    even = rename_action(base, f"{base_name}-even")
    even = _inject_parity_precond(even, "(parity)")

    # ODD
    odd = rename_action(base, f"{base_name}-odd")
    odd = _inject_parity_precond(odd, "(not (parity))")
    odd = flip_updated_literals(odd)

    variants = [even, odd]

    if make_edges:
        has_left = re.search(r"\(\s*right-of\s+\?left\s+\?c\s*\)", base, flags=re.IGNORECASE)
        has_right = re.search(r"\(\s*right-of\s+\?c\s+\?right\s*\)", base, flags=re.IGNORECASE)

        def suffix_current_name(action_text: str, suffix: str) -> str:
            m = re.search(r"\(\s*:action\s+([^\s\)]+)", action_text, flags=re.IGNORECASE)
            assert m
            return rename_action(action_text, m.group(1) + suffix)

        def edgeify(action_text: str, edge_tag: str, drop_left: bool, drop_right: bool) -> str:
            t = action_text
            if drop_left:
                t = drop_literal_everywhere(t, r"\(\s*right-of\s+\?left\s+\?c\s*\)")
            if drop_right:
                t = drop_literal_everywhere(t, r"\(\s*right-of\s+\?c\s+\?right\s*\)")
            t = suffix_current_name(t, f"-{edge_tag}")
            return normalize_spacing(t)

        extra: List[str] = []
        for v in variants:
            if has_left:
                extra.append(edgeify(v, "leftedge", drop_left=True, drop_right=False))
            if has_right:
                extra.append(edgeify(v, "rightedge", drop_left=False, drop_right=True))
            if has_left and has_right:
                extra.append(edgeify(v, "both-edges", drop_left=True, drop_right=True))
        variants.extend(extra)

    return [normalize_spacing(v) for v in variants]


def action_matches(a: ActionBlock, name_re: Optional[re.Pattern], contains: List[str], all_actions: bool) -> bool:
    if all_actions:
        return True
    ok = False
    if name_re is not None and name_re.search(a.name):
        ok = True
    if contains:
        if any(sub in a.text for sub in contains):
            ok = True
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_domain", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--name-regex", type=str, default=None,
                    help="Regex for action names to expand (e.g. '^tick-' or 'move|fall').")
    ap.add_argument("--contains", action="append", default=[],
                    help="Only expand actions whose text contains this substring. Can be repeated.")
    ap.add_argument("--all-actions", action="store_true",
                    help="Expand every action in the domain.")
    ap.add_argument("--no-edges", action="store_true",
                    help="Do not generate edge variants.")
    args = ap.parse_args()

    dom = args.input_domain.read_text(encoding="utf-8")
    actions = extract_all_actions(dom)
    if not actions:
        raise ValueError("No (:action ...) blocks found.")

    name_re = re.compile(args.name_regex) if args.name_regex else None
    make_edges = not args.no_edges

    # Build output by walking through the source text and replacing selected action blocks
    out_parts: List[str] = []
    cursor = 0
    expanded_count = 0
    generated_actions = 0

    for a in actions:
        out_parts.append(dom[cursor:a.start])

        if action_matches(a, name_re, args.contains, args.all_actions):
            variants = build_variants(a, make_edges=make_edges)
            out_parts.append("\n\n" + "\n\n".join(variants) + "\n\n")
            expanded_count += 1
            generated_actions += len(variants)
        else:
            out_parts.append(dom[a.start:a.end])

        cursor = a.end

    out_parts.append(dom[cursor:])
    out = "".join(out_parts)

    args.output.write_text(out, encoding="utf-8")
    print(f"Wrote: {args.output}")
    print(f"Expanded {expanded_count} actions -> generated {generated_actions} actions total (including even/odd + edges).")


if __name__ == "__main__":
    main()
