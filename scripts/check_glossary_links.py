#!/usr/bin/env python3
"""Glossary integrity:
  1. every link into glossary.md#anchor from any page points at an existing term;
  2. every glossary term links to at least one explaining page outside the glossary;
  3. counts terms (target >= 400) and the share explained by modules 02-03 (target >= 60%);
  4. counts acronyms (table rows in acronyms.md, target >= 150).

Glossary format (docs/09-reference/glossary.md): one '### Term' heading per term, grouped under
'## A', '## B', ... Term headings use ASCII only so anchors are predictable (see CLAUDE.md).

Usage: python scripts/check_glossary_links.py [--missing]   (--missing lists anchors to add)
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter

from kb import DOCS, all_pages, is_stub, links, read, resolve, slugify

GLOSSARY = DOCS / "09-reference" / "glossary.md"
ACRONYMS = DOCS / "09-reference" / "acronyms.md"


def glossary_terms() -> dict[str, str]:
    """slug -> body text of the entry."""
    text = read(GLOSSARY)
    out: dict[str, str] = {}
    cur = None
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("### "):
            if cur:
                out[cur] = "\n".join(buf)
            heading = re.sub(r"\s*\{#([^}]+)\}\s*$", "", line[4:].strip())
            m = re.search(r"\{#([^}]+)\}\s*$", line)
            cur = m.group(1) if m else slugify(heading)
            buf = []
        elif line.startswith("## "):
            if cur:
                out[cur] = "\n".join(buf)
            cur = None
            buf = []
        elif cur:
            buf.append(line)
    if cur:
        out[cur] = "\n".join(buf)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--missing", action="store_true")
    ap.add_argument("--strict", action="store_true", help="fail if counts are below target")
    args = ap.parse_args()
    terms = glossary_terms()
    errs: list[str] = []

    # 1. inbound anchors
    wanted: Counter[str] = Counter()
    where: dict[str, str] = {}
    for p in all_pages():
        if p == GLOSSARY:
            continue
        for _, href in links(read(p)):
            tgt, anchor = resolve(p, href)
            if tgt is not None and tgt == GLOSSARY.resolve() and anchor:
                wanted[anchor] += 1
                where.setdefault(anchor, p.relative_to(DOCS).as_posix())
    missing = sorted(a for a in wanted if a not in terms)
    for a in missing:
        errs.append(f"glossary anchor '#{a}' linked from {where[a]} does not exist")

    # 2. each term links to an explaining page; 3. share explained by 02-03
    n_prio = 0
    no_link = []
    for slug, body in terms.items():
        targets = []
        for _, href in links(body):
            tgt, _ = resolve(GLOSSARY, href)
            if tgt is not None and tgt != GLOSSARY.resolve():
                targets.append(tgt.relative_to(DOCS.resolve()).as_posix() if tgt.is_relative_to(DOCS.resolve()) else str(tgt))
        if not targets:
            no_link.append(slug)
        elif any(t.startswith(("02-", "03-")) for t in targets):
            n_prio += 1
    for s in no_link:
        errs.append(f"glossary term '{s}' has no link to an explaining page")

    n_acr = 0
    if ACRONYMS.exists() and not is_stub(read(ACRONYMS)):
        n_acr = sum(1 for ln in read(ACRONYMS).splitlines()
                    if ln.startswith("|") and not re.match(r"^\|\s*(-|:)", ln)) - 1
        n_acr = max(n_acr, 0)

    if args.missing:
        print("\n".join(f"{a}  ({wanted[a]} links, e.g. {where[a]})" for a in missing))
        return 0
    for e in errs[:200]:
        print("FAIL", e)
    if len(errs) > 200:
        print(f"... and {len(errs) - 200} more")
    share = n_prio / len(terms) if terms else 0
    print(f"\ncheck_glossary_links: {len(terms)} terms (target >= 400), {share:.0%} explained in 02-03 "
          f"(target >= 60%), {len(wanted)} distinct anchors linked, {len(missing)} missing; "
          f"acronyms: {n_acr} (target >= 150)")
    if args.strict and (len(terms) < 400 or share < 0.6 or n_acr < 150):
        errs.append("counts below target")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
