#!/usr/bin/env python3
"""Write the classic / forced-action test-domain variants from their sources.

  source                               -> pddl/test_domains_target/
  pddl/domain_rowscan.pddl             -> domain_{classic,FA}_scanner_combined.pddl
  pddl/domain_cellscan_separated.pddl  -> domain_{classic,FA}_scanner_separated.pddl
  pddl/domain_orderfree_combined.pddl  -> domain_{classic,FA}_non-scanner_combined.pddl
  pddl/domain_orderfree_separated.pddl -> domain_{classic,FA}_non-scanner_separated.pddl

The classic variant is the source unchanged; the FA variant prefixes every
physics action (every action that is not an agent move_* action) with
__FORCED__.  Both carry the `; variant:` / `; source:` headers that the
problem-generator wrappers (problem_gen_common.py), tools/plan.py and the
benchmark scripts use to pick the matching problem generator.

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


def build(text: str, forced: bool) -> str:
    if not forced:
        return text
    # every action that is not an agent move_* action is physics
    return re.sub(r"\(:action (?!move_)([A-Za-z0-9_\-]+)", r"(:action __FORCED__\1", text)


def main() -> None:
    for source, cell in SOURCES.items():
        body = (HERE / source).read_text(encoding="utf-8")
        for prefix, variant, forced in (("classic", f"domain_{cell}.pddl", False),
                                        ("FA", f"domain_FA_{cell}.pddl", True)):
            header = (
                "; Generated test domain variant\n"
                f"; variant: {variant}\n"
                f"; source: pddl/{source}\n"
                "; regenerate with: python pddl/make_target_variants.py\n"
            )
            out = OUT_DIR / f"domain_{prefix}_{cell}.pddl"
            out.write_text(header + build(body, forced), encoding="utf-8")
            print(f"wrote {out}")


if __name__ == "__main__":
    main()
