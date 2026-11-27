#!/usr/bin/env python3
"""Write the classic / forced-action test-domain variants from their sources.

  source                               -> pddl/test_domains_target/
  pddl/domain_rowscan.pddl             -> domain_{classic,FA}_scanner_combined[_multigem].pddl
  pddl/domain_cellscan_separated.pddl  -> domain_{classic,FA}_scanner_separated[_multigem].pddl
  pddl/domain_orderfree_combined.pddl  -> domain_{classic,FA}_non-scanner_combined[_multigem].pddl
  pddl/domain_orderfree_separated.pddl -> domain_{classic,FA}_non-scanner_separated[_multigem].pddl

The classic variant is the source unchanged; the FA variant prefixes every
physics action (every action that is not an agent move_* action) with
__FORCED__.  All variants carry the `; variant:` / `; source:` headers that the
problem-generator wrappers (problem_gen_common.py), tools/plan.py and the
benchmark scripts use to pick the matching problem generator.

The _multigem variants have any number of target gems, each a `target`
object: (target-gem ?c ?t) is target ?t's marker, it travels with its gem
exactly like the single marker does, and collecting the gem makes
(collected ?t) true.  The goal is (collected ?t) for every target.  With one
target this is the single-target model with its atoms renamed.  The physics
are untouched: every rule that moves or clears the marker becomes a forall over
the targets.  problem_gen_common.py writes the target objects and goal.

Usage:
  python pddl/make_target_variants.py
"""

from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "test_domains_target"

# source file -> matrix cell name used in the output file names and headers
SOURCES = {
    "domain_rowscan.pddl": "scanner_combined",
    "domain_cellscan_separated.pddl": "scanner_separated",
    "domain_orderfree_combined.pddl": "non-scanner_combined",
    "domain_orderfree_separated.pddl": "non-scanner_separated",
}

V = r"(\?[A-Za-z0-9_\-]+)"
FA = "(forall (?tg - target) "
# (pattern, replacement) applied in order to the code (not the comments) of each line
MULTIGEM_RULES = [
    # the marker travels: delete at the old cell, add at the new one
    (rf"\(when \(target-gem {V}\) \(and \(not \(target-gem \1\)\) \(target-gem {V}\)\)\)",
     FA + r"(when (target-gem \1 ?tg) (and (not (target-gem \1 ?tg)) (target-gem \2 ?tg))))"),
    # collecting the gem
    (rf"\(when \(target-gem {V}\) \(and \(not \(target-gem \1\)\) \(got-gem\)\)\)",
     FA + r"(when (target-gem \1 ?tg) (and (not (target-gem \1 ?tg)) (collected ?tg))))"),
    # order-free combined: unconditional delete plus a conditional add
    (rf"\(when \(target-gem {V}\) \(target-gem {V}\)\)",
     FA + r"(when (target-gem \1 ?tg) (target-gem \2 ?tg)))"),
    (rf"\(not \(target-gem {V}\)\)", FA + r"(not (target-gem \1 ?tg)))"),
    # declarations
    (r"\(target-gem \?c - cell\)", "(target-gem ?c - cell ?t - target)"),
    (r"\(got-gem\)", "(collected ?t - target)"),
    (r"\(define \(domain ([A-Za-z0-9_\-]+)\)", r"(define (domain \1-multigem)"),
]


def multigem(text: str) -> str:
    lines = []
    for line in text.splitlines(keepends=True):
        code, sep, comment = line.partition(";")
        for pat, rep in MULTIGEM_RULES:
            code = re.sub(pat, rep, code)
        lines.append(code + sep + comment)
    out = "".join(lines)
    out = re.sub(r"\(:types\s*\n", "(:types\n    target - object\n", out, count=1)
    # every marker / goal atom must have been rewritten
    code_only = "\n".join(l.partition(";")[0] for l in out.splitlines())
    left = re.findall(r"\(target-gem \?[A-Za-z0-9_\-]+\)|\(got-gem\)", code_only)
    if left or "target - object" not in out:
        raise SystemExit(f"multigem: unhandled target-gem / got-gem uses {sorted(set(left))}")
    return out


def gemcount(text: str) -> str:
    """Any-n-gems goal, as on main (85adeaa): a gem-count counter gems_0 -> ... ->
    gems_n that move_into_gem steps (gems_n loops to itself), goal
    (gems-collected gems_n).  The target-gem atoms stay, unused."""
    start = text.index("(:action move_into_gem")
    end = text.index("(:action", start + 1)
    block = text[start:end]
    for pat, rep in (
        (r"(:parameters \([^)]*)\)", r"\1 ?n ?m - gem-count)"),
        (r":precondition \(and\n", ":precondition (and\n      (gems-collected ?n) (gem-count-next ?n ?m)\n"),
        (r":effect \(and\n", ":effect (and\n      (not (gems-collected ?n)) (gems-collected ?m)\n"),
    ):
        block, k = re.subn(pat, rep, block, count=1)
        if k != 1:
            raise SystemExit(f"gemcount: no match for {pat} in move_into_gem")
    out = text[:start] + block + text[end:]
    out, k1 = re.subn(r"\(:types\s*\n", "(:types\n    gem-count - object\n", out, count=1)
    out, k2 = re.subn(r"^(\s*)\(got-gem\)(.*)$",
                      r"\1(got-gem)\2\n\1(gems-collected ?n - gem-count)    ; gems collected so far (exactly one true)"
                      r"\n\1(gem-count-next ?n ?m - gem-count) ; static successor; gems_n -> gems_n (saturates)",
                      out, count=1, flags=re.MULTILINE)
    out, k3 = re.subn(r"\(define \(domain ([A-Za-z0-9_\-]+)\)", r"(define (domain \1-gemcount)", out, count=1)
    if not (k1 and k2 and k3):
        raise SystemExit("gemcount: types / predicates / domain name not found")
    return out


def build(text: str, forced: bool, multi: bool = False, count: bool = False) -> str:
    if multi:
        text = multigem(text)
    if count:
        text = gemcount(text)
    if not forced:
        return text
    # every action that is not an agent move_* action is physics
    return re.sub(r"\(:action (?!move_)([A-Za-z0-9_\-]+)", r"(:action __FORCED__\1", text)


def main() -> None:
    for source, cell in SOURCES.items():
        body = (HERE / source).read_text(encoding="utf-8")
        for suffix, multi, count in (("", False, False), ("_multigem", True, False), ("_gemcount", False, True)):
            for prefix, variant, forced in (("classic", f"domain_{cell}{suffix}.pddl", False),
                                            ("FA", f"domain_FA_{cell}{suffix}.pddl", True)):
                header = (
                    "; Generated test domain variant\n"
                    f"; variant: {variant}\n"
                    f"; source: pddl/{source}\n"
                    + ("; multigem: target gems are `target` objects, (target-gem ?c ?t) travels with\n"
                       ";   the gem, collecting it sets (collected ?t); comments below describe the\n"
                       ";   single-target source (target-gem ?c) / (got-gem)\n" if multi else "")
                    + ("; gemcount: goal (gems-collected gems_n) = any n gems; move_into_gem steps the\n"
                       ";   counter gems_0 -> ... -> gems_n (saturating), as on main (85adeaa)\n" if count else "")
                    + "; regenerate with: python pddl/make_target_variants.py\n"
                )
                out = OUT_DIR / f"domain_{prefix}_{cell}{suffix}.pddl"
                out.write_text(header + build(body, forced, multi, count), encoding="utf-8")
                print(f"wrote {out}")


if __name__ == "__main__":
    main()
