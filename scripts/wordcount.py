#!/usr/bin/env python3
"""Word counts per module vs budget, Mermaid counts, Core Path size and other KB totals.

Usage: python scripts/wordcount.py [--pages] [--json]
"""
from __future__ import annotations

import argparse
import csv
import json
import re

from kb import DOCS, MODULES, ROOT, all_pages, is_stub, mermaid_count, module_of, prose_words, read

CORE_PATH_FILE = ROOT / "scripts" / "core_path.txt"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", action="store_true", help="list every page with its count")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    per_module = {m: {"words": 0, "pages": 0, "stubs": 0, "mermaid": 0} for m in MODULES}
    other = {"words": 0, "pages": 0, "stubs": 0, "mermaid": 0}
    page_rows = []
    todo_verify = 0
    for p in all_pages():
        text = read(p)
        m = module_of(p)
        bucket = per_module[m] if m else other
        w = prose_words(text)
        mm = mermaid_count(text)
        stub = is_stub(text)
        bucket["pages"] += 1
        bucket["stubs"] += int(stub)
        bucket["words"] += 0 if stub else w
        bucket["mermaid"] += mm
        todo_verify += len(re.findall(r"TODO\(verify\)", text))
        page_rows.append((p.relative_to(DOCS).as_posix(), w, mm, stub))

    total = sum(v["words"] for v in per_module.values()) + other["words"]
    prio = per_module["02-strategies"]["words"] + per_module["03-algorithms"]["words"]
    mer_total = sum(v["mermaid"] for v in per_module.values()) + other["mermaid"]
    mer_prio = per_module["02-strategies"]["mermaid"] + per_module["03-algorithms"]["mermaid"]

    # Core Path
    core_words = core_prio = 0
    core_missing = []
    if CORE_PATH_FILE.exists():
        for line in CORE_PATH_FILE.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            fp = DOCS / line
            if not fp.exists():
                core_missing.append(line)
                continue
            w = prose_words(read(fp))
            core_words += w
            if line.startswith(("02-", "03-")):
                core_prio += w

    # Other artefacts
    flash = ROOT / "docs" / "10-self-test" / "flashcards.csv"
    n_cards = n_cards_prio = 0
    if flash.exists():
        with flash.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                n_cards += 1
                tags = (row.get("tags") or "").lower()
                if "strateg" in tags or "algorithm" in tags:
                    n_cards_prio += 1
    sources = ROOT / "references" / "sources.md"
    n_sources = len(re.findall(r"(?m)^- \[(?:Verified|Reported|Estimate|Lore)\]", read(sources))) \
        if sources.exists() else 0

    report = {
        "modules": per_module, "other": other, "total_words": total,
        "priority_words": prio, "priority_share": round(prio / total, 3) if total else 0,
        "mermaid_total": mer_total, "mermaid_02_03": mer_prio,
        "core_path_words": core_words,
        "core_path_share_02_03": round(core_prio / core_words, 3) if core_words else 0,
        "core_path_missing": core_missing, "todo_verify": todo_verify,
        "flashcards": n_cards, "flashcards_prio_share": round(n_cards_prio / n_cards, 3) if n_cards else 0,
        "sources_md_entries": n_sources,
    }
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"{'Module':<30}{'Words':>9}{'Budget':>9}{'%Bud':>7}{'Pages':>7}{'Stubs':>7}{'Mermaid':>9}")
    for m, (title, budget) in MODULES.items():
        v = per_module[m]
        pct = f"{100 * v['words'] / budget:.0f}%" if budget else "n/a"
        print(f"{m:<30}{v['words']:>9,}{budget:>9,}{pct:>7}{v['pages']:>7}{v['stubs']:>7}{v['mermaid']:>9}")
    if other["pages"]:
        print(f"{'(other pages)':<30}{other['words']:>9,}{'':>9}{'':>7}{other['pages']:>7}"
              f"{other['stubs']:>7}{other['mermaid']:>9}")
    print("-" * 78)
    print(f"Total words: {total:,} (target >= 110,000)")
    print(f"Modules 02+03: {prio:,} words = {report['priority_share']:.0%} of total (target >= 75,000, ~70%)")
    print(f"Mermaid diagrams: {mer_total} total (target >= 140), {mer_prio} in 02-03 (target >= 100)")
    print(f"Core Path: {core_words:,} words (target <= ~25,000), "
          f"{report['core_path_share_02_03']:.0%} from 02-03 (target >= 60%)")
    if core_missing:
        print(f"  Core Path entries missing: {core_missing}")
    print(f"TODO(verify) markers: {todo_verify}")
    print(f"Flashcards: {n_cards} (target >= 300), {report['flashcards_prio_share']:.0%} strategies/algorithms")
    print(f"references/sources.md entries: {n_sources} (target >= 150)")
    if args.pages:
        print()
        for rel, w, mm, stub in page_rows:
            print(f"{w:>6}  {mm:>2}  {'STUB ' if stub else ''}{rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
