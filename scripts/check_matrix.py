#!/usr/bin/env python3
"""Verify (or regenerate) the strategy x algorithm matrix.

Source of truth:
  * core links      = algorithm cards linked in each dossier's 'Core algorithms used' field  -> ●
  * supporting links = dossiers linked in each card's 'Used by strategies' field that are not core -> ○
  * extra supporting pairs may be listed in scripts/matrix_supporting.txt ("dossier-slug CARD_ID")

The matrix lives in docs/02-strategies/h-cross-cutting/strategy-x-algorithm-matrix.md between
<!-- MATRIX:START --> and <!-- MATRIX:END -->.

Usage: python scripts/check_matrix.py [--write]
"""
from __future__ import annotations

import argparse
import re
import sys

from kb import (CARD_ID_BY_PATH, CARD_IDS, DOCS, ROOT, all_pages, card_rel, dossier_rel, get_field,
                is_stub, links, page_kind, read, resolve, table_fields)

MATRIX = DOCS / "02-strategies" / "h-cross-cutting" / "strategy-x-algorithm-matrix.md"
EXTRA = ROOT / "scripts" / "matrix_supporting.txt"
START, END = "<!-- MATRIX:START -->", "<!-- MATRIX:END -->"
CORE, SUP, NA = "●", "○", "·"


def gather():
    dossiers: dict[str, dict] = {}
    used_by: dict[str, set[str]] = {}
    for p in all_pages():
        kind = page_kind(p)
        text = read(p)
        if kind == "dossier":
            rel = dossier_rel(p)
            title = text.splitlines()[0].lstrip("# ").strip() if text.strip() else rel
            core: set[str] = set()
            if not is_stub(text):
                field = get_field(table_fields(text), "Core algorithms used") or ""
                for _, href in links(field):
                    tgt, _ = resolve(p, href)
                    cr = card_rel(tgt) if tgt else None
                    if cr:
                        core.add(CARD_ID_BY_PATH[cr])
            dossiers[rel] = {"title": title, "core": core, "stub": is_stub(text)}
        elif kind == "card" and not is_stub(text):
            cid = CARD_ID_BY_PATH.get(card_rel(p) or "")
            if not cid:
                continue
            field = get_field(table_fields(text), "Used by strategies") or ""
            for _, href in links(field):
                tgt, _ = resolve(p, href)
                dr = dossier_rel(tgt) if tgt else None
                if dr:
                    used_by.setdefault(cid, set()).add(dr)
    extra: set[tuple[str, str]] = set()
    if EXTRA.exists():
        for line in EXTRA.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                slug, cid = line.split()
                extra.add((slug, cid))
    return dossiers, used_by, extra


def expected(dossiers, used_by, extra) -> dict[str, dict[str, str]]:
    exp = {d: {cid: NA for cid in CARD_IDS} for d in dossiers}
    for cid, ds in used_by.items():
        for d in ds:
            if d in exp:
                exp[d][cid] = SUP
    for slug, cid in extra:
        for d in exp:
            if d.split("/")[-1] == slug and exp[d][cid] == NA:
                exp[d][cid] = SUP
    for d, info in dossiers.items():
        for cid in info["core"]:
            exp[d][cid] = CORE
    return exp


def render(dossiers, exp) -> str:
    ids = list(CARD_IDS)
    head = "| Strategy | " + " | ".join(ids) + " |"
    sep = "|---|" + "|".join([":-:"] * len(ids)) + "|"
    rows = [head, sep]
    for d in sorted(dossiers):
        link = f"[{dossiers[d]['title']}](../{d}.md)"
        rows.append(f"| {link} | " + " | ".join(exp[d][c] for c in ids) + " |")
    return "\n".join(rows)


def parse_matrix(text: str) -> dict[str, dict[str, str]]:
    if START not in text or END not in text:
        return {}
    body = text.split(START, 1)[1].split(END, 1)[0]
    lines = [ln for ln in body.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return {}
    ids = [c.strip() for c in lines[0].strip().strip("|").split("|")][1:]
    out = {}
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        m = re.search(r"\(\.\./([^)]+)\.md\)", cells[0])
        if m:
            out[m.group(1)] = dict(zip(ids, cells[1:]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="regenerate the matrix table in place")
    args = ap.parse_args()
    dossiers, used_by, extra = gather()
    exp = expected(dossiers, used_by, extra)
    text = read(MATRIX)
    if args.write:
        table = render(dossiers, exp)
        if START in text:
            pre, rest = text.split(START, 1)
            post = rest.split(END, 1)[1] if END in rest else ""
            text = f"{pre}{START}\n{table}\n{END}{post}"
        else:
            text = text.rstrip() + f"\n\n{START}\n{table}\n{END}\n"
        MATRIX.write_text(text, encoding="utf-8")
        print(f"matrix written: {len(dossiers)} strategies x {len(CARD_IDS)} cards")
        return 0

    errs = []
    written = [d for d, i in dossiers.items() if not i["stub"]]
    for d in written:
        if not dossiers[d]["core"]:
            errs.append(f"{d}: no algorithm cards linked in 'Core algorithms used'")
    have = parse_matrix(text)
    if not have:
        errs.append("matrix table not found between markers (run with --write)")
    else:
        for d in dossiers:
            if d not in have:
                errs.append(f"matrix missing row for {d}")
                continue
            for cid in CARD_IDS:
                got = have[d].get(cid, "?")
                if got != exp[d][cid]:
                    errs.append(f"{d} x {cid}: matrix has '{got}', dossier/card headers imply '{exp[d][cid]}'")
    unused = [cid for cid in CARD_IDS if all(exp[d][cid] == NA for d in exp)]
    for e in errs:
        print("FAIL", e)
    if unused:
        print("warn: cards not used by any strategy:", ", ".join(unused))
    print(f"\ncheck_matrix: {len(written)} written dossiers, {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
