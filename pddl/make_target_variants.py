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


def build(text: str, forced: bool, multi: bool = False) -> str:
    if multi:
        text = multigem(text)
    if not forced:
        return text
    # every action that is not an agent move_* action is physics
    return re.sub(r"\(:action (?!move_)([A-Za-z0-9_\-]+)", r"(:action __FORCED__\1", text)


def main() -> None:
    for source, cell in SOURCES.items():
        body = (HERE / source).read_text(encoding="utf-8")
        for suffix, multi in (("", False), ("_multigem", True)):
            for prefix, variant, forced in (("classic", f"domain_{cell}{suffix}.pddl", False),
                                            ("FA", f"domain_FA_{cell}{suffix}.pddl", True)):
                header = (
                    "; Generated test domain variant\n"
                    f"; variant: {variant}\n"
                    f"; source: pddl/{source}\n"
                    + ("; multigem: target gems are `target` objects, (target-gem ?c ?t) travels with\n"
                       ";   the gem, collecting it sets (collected ?t); comments below describe the\n"
                       ";   single-target source (target-gem ?c) / (got-gem)\n" if multi else "")
                    + "; regenerate with: python pddl/make_target_variants.py\n"
                )
                out = OUT_DIR / f"domain_{prefix}_{cell}{suffix}.pddl"
                out.write_text(header + build(body, forced, multi), encoding="utf-8")
                print(f"wrote {out}")


if __name__ == "__main__":
    main()
