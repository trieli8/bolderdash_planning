#!/usr/bin/env python3
"""Write the scanner-combined test-domain variants from pddl/domain_rowscan.pddl.

  pddl/test_domains_target/domain_classic_scanner_combined.pddl  (plain names)
  pddl/test_domains_target/domain_FA_scanner_combined.pddl       (physics actions
                                                                   prefixed __FORCED__)

Both keep the `; variant:` / `; source:` headers that the problem-generator
wrappers (problem_gen_common.py) and the benchmark scripts use to pick
pddl/problem_gen_rowscan.py.
"""

from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "domain_rowscan.pddl"
OUT_DIR = HERE / "test_domains_target"

VARIANTS = {
    "domain_classic_scanner_combined.pddl": ("domain_scanner_combined.pddl", False),
    "domain_FA_scanner_combined.pddl": ("domain_FA_scanner_combined.pddl", True),
}


def build(text: str, forced: bool) -> str:
    if not forced:
        return text
    # every action that is not an agent move_* action is physics
    return re.sub(r"\(:action (?!move_)([A-Za-z0-9_\-]+)", r"(:action __FORCED__\1", text)


def main() -> None:
    body = SOURCE.read_text(encoding="utf-8")
    for out_name, (variant, forced) in VARIANTS.items():
        header = (
            "; Generated test domain variant\n"
            f"; variant: {variant}\n"
            f"; source: pddl/{SOURCE.name}\n"
            "; regenerate with: python pddl/make_rowscan_variants.py\n"
        )
        (OUT_DIR / out_name).write_text(header + build(body, forced), encoding="utf-8")
        print(f"wrote {OUT_DIR / out_name}")


if __name__ == "__main__":
    main()
