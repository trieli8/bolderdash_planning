#!/usr/bin/env python3
"""
remove_when_by_splitting_actions.py

Converts a PDDL domain using conditional effects (when) into a domain without (when)
by generating additional actions.

Strategy:
  For each (:action A ... :effect E):
    - Keep a copy A-base with all unconditional effects only.
    - For each (when C CE) inside E:
        create A-wi with precondition (and PRE C) and effect (and UNCOND CE)
"""

from __future__ import annotations
import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Any, Union


Token = str
SExpr = Union[str, List["SExpr"]]


def tokenize(s: str) -> List[Token]:
    # Remove ; comments
    s = re.sub(r";[^\n]*", "", s)
    # Split parentheses and symbols
    return re.findall(r"\(|\)|[^\s()]+", s)


def parse_sexpr(tokens: List[Token]) -> SExpr:
    if not tokens:
        raise ValueError("Empty token stream")
    tok = tokens.pop(0)
    if tok == "(":
        out: List[SExpr] = []
        while tokens and tokens[0] != ")":
            out.append(parse_sexpr(tokens))
        if not tokens:
            raise ValueError("Unbalanced parentheses")
        tokens.pop(0)  # ')'
        return out
    elif tok == ")":
        raise ValueError("Unexpected ')'")
    else:
        return tok


def dumps(x: SExpr, indent: int = 0) -> str:
    if isinstance(x, str):
        return x
    # pretty print lists
    if not x:
        return "()"
    head = x[0]
    if isinstance(head, str):
        head_l = head.lower()
        if head_l == "and":
            if len(x) == 1:
                return "(and)"
            # break lines between each conjunct for readability
            indent_str = "  " * indent
            child_indent = indent + 1
            parts = ["(and"]
            for item in x[1:]:
                parts.append("\n" + "  " * child_indent + dumps(item, child_indent))
            parts.append("\n" + indent_str + ")")
            return "".join(parts)
        if head_l in {":predicates", ":types", ":requirements", ":action", ":parameters", ":precondition", ":effect"}:
            # keep "keyword blocks" a bit more readable
            pieces = ["(" + dumps(head)]
            for item in x[1:]:
                pieces.append("\n" + "  " * (indent + 1) + dumps(item, indent + 1))
            pieces.append("\n" + "  " * indent + ")")
            return "".join(pieces)

    inner = " ".join(dumps(i, indent) for i in x)
    return f"({inner})"


@dataclass
class PddlAction:
    name: str
    sexpr: List[SExpr]


def is_list(x: SExpr) -> bool:
    return isinstance(x, list)


def find_actions(domain: SExpr) -> List[PddlAction]:
    if not is_list(domain):
        raise ValueError("Domain is not a list")
    actions: List[PddlAction] = []

    def walk(node: SExpr):
        if is_list(node) and node:
            if isinstance(node[0], str) and node[0].lower() == ":action":
                name = str(node[1])
                actions.append(PddlAction(name=name, sexpr=node))  # type: ignore
            for child in node:
                walk(child)

    walk(domain)
    return actions


def get_field(action: List[SExpr], key: str) -> SExpr | None:
    key_l = key.lower()
    for i in range(len(action) - 1):
        if isinstance(action[i], str) and action[i].lower() == key_l:
            return action[i + 1]
    return None


def set_field(action: List[SExpr], key: str, value: SExpr) -> None:
    key_l = key.lower()
    for i in range(len(action) - 1):
        if isinstance(action[i], str) and action[i].lower() == key_l:
            action[i + 1] = value
            return
    action.append(key)
    action.append(value)


def ensure_and(expr: SExpr) -> List[SExpr]:
    # Returns a list-form (and ...)
    if is_list(expr) and expr and isinstance(expr[0], str) and expr[0].lower() == "and":
        return expr  # type: ignore
    return ["and", expr]  # type: ignore


def negate(expr: SExpr) -> SExpr:
    """Return logical negation with basic De Morgan pushdown."""
    if is_list(expr) and expr:
        head = expr[0]
        if isinstance(head, str):
            h = head.lower()
            if h == "and":
                return ["or", *[negate(e) for e in expr[1:]]]
            if h == "or":
                return ["and", *[negate(e) for e in expr[1:]]]
            if h == "not" and len(expr) == 2:
                return expr[1]
    return ["not", expr]


def simplify(expr: SExpr) -> SExpr:
    """Simplify boolean connectives: flatten, drop singletons, dedup, remove double not."""
    if not is_list(expr) or not expr:
        return expr
    head = expr[0]
    if not isinstance(head, str):
        return [simplify(e) for e in expr]  # type: ignore
    h = head.lower()
    if h in {"and", "or"}:
        items = [simplify(e) for e in expr[1:]]
        flat: List[SExpr] = []
        for it in items:
            if is_list(it) and it and isinstance(it[0], str) and it[0].lower() == h:
                flat.extend(it[1:])  # flatten nested same connective
            else:
                flat.append(it)
        # dedup while preserving order
        dedup: List[SExpr] = []
        for item in flat:
            if item not in dedup:
                dedup.append(item)
        if not dedup:
            return [head]
        if len(dedup) == 1:
            return dedup[0]
        return [head, *dedup]
    if h == "not" and len(expr) == 2:
        inner = simplify(expr[1])
        if is_list(inner) and inner and isinstance(inner[0], str) and inner[0].lower() == "not" and len(inner) == 2:
            return simplify(inner[1])
        return ["not", inner]
    # default: simplify children
    return [head, *(simplify(e) for e in expr[1:])]


def split_effect(effect: SExpr) -> Tuple[List[SExpr], List[Tuple[SExpr, SExpr]]]:
    """
    Returns (unconditional_effects, conditional_effects)
    unconditional_effects: list of effect s-exprs (no 'when')
    conditional_effects: list of (cond, eff) pairs from (when cond eff)
    """
    uncond: List[SExpr] = []
    whens: List[Tuple[SExpr, SExpr]] = []

    eff_and = ensure_and(effect)
    for item in eff_and[1:]:
        if is_list(item) and item and isinstance(item[0], str) and item[0].lower() == "when":
            if len(item) != 3:
                raise ValueError("Expected (when <cond> <eff>)")
            whens.append((item[1], item[2]))
        else:
            uncond.append(item)

    return uncond, whens


def replace_action_name(action: List[SExpr], new_name: str) -> List[SExpr]:
    out = list(action)
    out[1] = new_name
    return out


def rebuild_domain_with_actions(domain: List[SExpr], new_actions: List[List[SExpr]]) -> List[SExpr]:
    """
    Removes all existing :action blocks and appends new ones at the end.
    """
    def is_action(node: SExpr) -> bool:
        return is_list(node) and node and isinstance(node[0], str) and node[0].lower() == ":action"

    stripped = [x for x in domain if not is_action(x)]
    # keep them near end, but still inside (define ...)
    return stripped + new_actions


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_domain", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    args = ap.parse_args()

    text = args.input_domain.read_text(encoding="utf-8")
    tokens = tokenize(text)
    dom = parse_sexpr(tokens)
    if tokens:
        raise ValueError("Trailing tokens after parse (input may contain multiple top-level forms).")
    if not is_list(dom) or not dom or not (isinstance(dom[0], str) and dom[0].lower() == "define"):
        raise ValueError("Expected a single (define ...) domain.")

    actions = find_actions(dom)
    new_action_blocks: List[List[SExpr]] = []

    for a in actions:
        pre = get_field(a.sexpr, ":precondition")
        eff = get_field(a.sexpr, ":effect")
        if pre is None or eff is None:
            new_action_blocks.append(a.sexpr)
            continue

        uncond, whens = split_effect(eff)
        pre_and = ensure_and(pre)
        neg_whens = [negate(cond) for cond, _ in whens]

        # Base action: unconditional only
        base = replace_action_name(a.sexpr, f"{a.name}-base")
        base_pre = ["and", *pre_and[1:], *neg_whens] if neg_whens else pre_and
        set_field(base, ":precondition", simplify(base_pre))
        set_field(base, ":effect", ["and", *uncond] if uncond else ["and"])
        new_action_blocks.append(base)

        # One action per when
        for i, (cond, ceff) in enumerate(whens, start=1):
            ai = replace_action_name(a.sexpr, f"{a.name}-w{i}")
            neg_others = [negate(c) for j, (c, _) in enumerate(whens) if j != i - 1]
            ai_pre = ["and", *pre_and[1:], cond, *neg_others]
            set_field(ai, ":precondition", simplify(ai_pre))
            set_field(ai, ":effect", ["and", *uncond, ceff] if uncond else ["and", ceff])
            new_action_blocks.append(ai)

    dom2 = rebuild_domain_with_actions(dom, new_action_blocks)  # type: ignore
    out_text = dumps(dom2) + "\n"
    args.output.write_text(out_text, encoding="utf-8")
    print(f"Wrote: {args.output} (actions: {len(new_action_blocks)})")


if __name__ == "__main__":
    main()
