#!/usr/bin/env python3
"""Check strategy dossiers, algorithm cards, walkthroughs, firm profiles and module-01 pages
against the templates in CLAUDE.md.

Usage:
  python scripts/check_template.py            # stubs are skipped (reported as a count)
  python scripts/check_template.py --strict   # stubs count as failures (final QA)
  python scripts/check_template.py path/to/page.md [...]   # check specific pages
Exit code 1 if any page has errors. Warnings never fail the run.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from kb import (DOCS, LONG_CARDS, LONG_DOSSIERS, TAG_RE, all_pages, find_section, get_field, is_stub,
                links, mermaid_count, page_kind, prose_words, read, resolve, sections, split_code,
                table_fields)

DOSSIER_FIELDS = ["Family", "Edge source", "Holding period", "Counterparty", "Universe",
                  "Data required", "Core algorithms used", "Infra intensity", "Capacity",
                  "Typical Sharpe", "Turnover", "Main risks", "Crowding risk", "Firm types", "Lab"]
DOSSIER_H2 = ["Intuition", "Economic rationale", "The trade, step by step", "Worked example",
              "Signals and algorithms under the hood", "Implementation choices", "P&L decomposition",
              "Evidence", "Capacity, crowding and decay", "How it fails", "Textbook vs how it",
              "Variants and neighbo", "Diagram", "How practitioners talk", "Myths vs reality",
              "Questions you could ask", "Go deeper", "Related pages", "Sources"]
CARD_FIELDS = ["Purpose", "Inputs", "Used by strategies", "Latency", "Key parameters",
               "Main failure modes", "Lab"]
CARD_H2 = ["Intuition", "Where it sits in the pipeline", "The algorithm", "Worked example",
           "Key parameters", "Textbook version vs what firms actually do", "How to tell if it",
           "Failure modes", "How practitioners talk", "Questions you could ask", "Go deeper",
           "Related pages", "Sources"]
FIRM_FIELDS = ["Type", "Scale", "Horizon", "Known strategies", "Tech signals", "Confidence", "Sources"]
FIRM_H2 = ["What they do", "Strategy focus", "Fact vs lore", "Related pages", "Sources"]

RANGES = {
    "dossier": (900, 1500, 2200),   # min, normal max, max for LONG_DOSSIERS
    "card": (700, 1200, 1700),
    "walkthrough": (1800, 2500, 2500),
    "firm": (250, 650, 650),
    "ms": (500, 1600, 1600),
}


def check(path: Path, strict: bool) -> tuple[list[str], list[str]]:
    errs: list[str] = []
    warns: list[str] = []
    text = read(path)
    kind = page_kind(path)
    if is_stub(text):
        if strict:
            errs.append("page is still a stub")
        return errs, warns

    words = prose_words(text)
    lo, hi, hi_long = RANGES.get(kind, (0, 10**9, 10**9))
    long_ok = path.stem in (LONG_DOSSIERS | LONG_CARDS)
    upper = hi_long if long_ok else hi
    if words < lo:
        errs.append(f"too short: {words} words (min {lo})")
    elif words > upper:
        errs.append(f"too long: {words} words (max {upper})")

    if not text.lstrip().startswith("# "):
        errs.append("first line must be the H1 title")
    secs = sections(text, 2)
    n_mermaid = mermaid_count(text)

    if kind in ("dossier", "card", "walkthrough", "ms") and n_mermaid < 1:
        errs.append("needs >= 1 Mermaid diagram")

    if kind == "ms":
        if not find_section(secs, "Why this matters for strategies"):
            errs.append("missing '## Why this matters for strategies & algorithms'")
        return errs, warns

    if kind == "walkthrough":
        if not re.search(r"(?m)^> \*\*TL;DR\*\*", text):
            errs.append("missing TL;DR blockquote")
        if len(links(text)) < 8:
            warns.append("walkthrough links to fewer than 8 pages")
        return errs, warns

    if kind not in ("dossier", "card", "firm"):
        return errs, warns

    if not re.search(r"(?m)^> \*\*TL;DR\*\*", text):
        errs.append("missing '> **TL;DR**' blockquote")

    fields = table_fields(text)
    want_fields = {"dossier": DOSSIER_FIELDS, "card": CARD_FIELDS, "firm": FIRM_FIELDS}[kind]
    for f in want_fields:
        if get_field(fields, f) is None:
            errs.append(f"metadata table missing field '{f}'")
    want_h2 = {"dossier": DOSSIER_H2, "card": CARD_H2, "firm": FIRM_H2}[kind]
    for h in want_h2:
        if not find_section(secs, h):
            errs.append(f"missing section '## {h}...'")

    if kind == "firm":
        if not TAG_RE.search(text):
            errs.append("no confidence tags ([Verified]/[Reported]/[Estimate]/[Lore])")
        return errs, warns

    level = re.search(r"(?m)^\*\*Level:\*\*.*$", text)
    if not level:
        errs.append("missing '**Level:** ...' metadata line")
    else:
        line = level.group(0)
        need = ["Read time", "Last verified"] if kind == "dossier" else ["Pipeline stage", "Last verified"]
        for n in need:
            if n not in line:
                errs.append(f"metadata line missing '{n}'")

    # pseudocode
    pseudo_sec = find_section(secs, "Signals and algorithms under the hood" if kind == "dossier"
                              else "The algorithm")
    if pseudo_sec:
        _, blocks = split_code(pseudo_sec[1])
        py = [b for lang, b, _ in blocks if lang == "python"]
        if not py:
            errs.append(f"no ```python pseudocode block in '{pseudo_sec[0]}'")
        else:
            n = max(len([ln for ln in b.splitlines() if ln.strip()]) for b in py)
            if kind == "card" and n > 40:
                errs.append(f"pseudocode is {n} non-blank lines (max 40)")
            if kind == "dossier" and not (8 <= n <= 30):
                warns.append(f"pseudocode is {n} non-blank lines (target 10-25)")

    # worked example must contain numbers
    we = find_section(secs, "Worked example")
    if we and len(re.findall(r"\d", we[1])) < 10:
        errs.append("worked example has too few numbers")

    # go deeper uses <details>
    gd = find_section(secs, "Go deeper")
    if gd and "<details" not in gd[1]:
        errs.append("'Go deeper' must use a <details> block")

    # textbook vs practice must be sourced or tagged
    tv = find_section(secs, "Textbook vs how it" if kind == "dossier" else "Textbook version")
    if tv and not (TAG_RE.search(tv[1]) or re.search(r"\]\(", tv[1])):
        errs.append("'Textbook vs practice' section has no confidence tag or source link")

    # related pages >= 3 internal links that resolve
    rp = find_section(secs, "Related pages")
    if rp:
        internal = [h for _, h in links(rp[1]) if not h.startswith("http")]
        if len(internal) < 3:
            errs.append("'Related pages' needs >= 3 internal links")

    # sources section non-empty
    so = find_section(secs, "Sources")
    if so and len(re.findall(r"(?m)^\s*[-*] ", so[1])) < 3:
        warns.append("fewer than 3 sources listed")

    # confidence tags on capacity / sharpe
    if kind == "dossier":
        for f in ("Capacity", "Typical Sharpe"):
            v = get_field(fields, f) or ""
            if not TAG_RE.search(v):
                errs.append(f"'{f}' field needs a confidence tag")
        core = get_field(fields, "Core algorithms used") or ""
        n_core = sum(1 for _, h in links(core) if "03-algorithms/" in h)
        if n_core < 2:
            errs.append("'Core algorithms used' should link >= 2 algorithm cards")
    if kind == "card":
        used = get_field(fields, "Used by strategies") or ""
        if not any("02-strategies/" in h for _, h in links(used)):
            errs.append("'Used by strategies' must link >= 1 strategy dossier")

    # broken relative links (cheap pre-check; mkdocs --strict is authoritative)
    for _, href in links(text):
        tgt, _ = resolve(path, href)
        if tgt is not None and not tgt.exists():
            errs.append(f"broken link: {href}")
    if not TAG_RE.search(text):
        errs.append("no confidence tags anywhere on the page")
    return errs, warns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="only print failing pages")
    args = ap.parse_args()
    pages = [Path(p).resolve() for p in args.paths] if args.paths else all_pages()
    pages = [p for p in pages if page_kind(p) in ("dossier", "card", "walkthrough", "firm", "ms")]
    n_err = n_stub = n_ok = 0
    for p in pages:
        text = read(p)
        if is_stub(text) and not args.strict:
            n_stub += 1
            continue
        errs, warns = check(p, args.strict)
        rel = p.relative_to(DOCS).as_posix()
        if errs:
            n_err += 1
            print(f"FAIL {rel}")
            for e in errs:
                print(f"     - {e}")
        else:
            n_ok += 1
        if warns and not args.quiet:
            print(f"warn {rel}: " + "; ".join(warns))
    print(f"\ncheck_template: {n_ok} ok, {n_err} failing, {n_stub} stubs skipped")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
