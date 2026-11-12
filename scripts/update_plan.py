#!/usr/bin/env python3
"""Refresh PLAN.md from the repository state:
  * ticks '- [ ] `path`' page checkboxes whose docs page is written (no STUB marker);
  * ticks lab checkboxes whose labs/NN-*/results.json exists;
  * rewrites the 'Word count vs budget' table from scripts/wordcount.py.

Usage: python scripts/update_plan.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

from kb import DOCS, MODULES, ROOT, is_stub, read

PLAN = ROOT / "PLAN.md"


def main() -> int:
    text = read(PLAN)

    def tick_page(m: re.Match) -> str:
        path = DOCS / m.group(2)
        done = path.exists() and not is_stub(read(path))
        return f"- [{'x' if done else ' '}] `{m.group(2)}`"

    text = re.sub(r"- \[( |x)\] `([^`]+\.md)`", tick_page, text)

    def tick_lab(m: re.Match) -> str:
        nn = m.group(2)
        done = any(ROOT.glob(f"labs/{nn}-*/results.json"))
        return f"- [{'x' if done else ' '}] {nn} "

    text = re.sub(r"- \[( |x)\] (\d\d) ", tick_lab, text)

    wc = json.loads(subprocess.run([sys.executable, str(ROOT / "scripts" / "wordcount.py"), "--json"],
                                   capture_output=True, text=True, check=True).stdout)
    rows = ["| Module | Budget | Words | Pages written | Mermaid |", "|---|---|---|---|---|"]
    for m, (title, budget) in MODULES.items():
        v = wc["modules"][m]
        rows.append(f"| {m[:2]} {title} | {budget:,} | {v['words']:,} | {v['pages'] - v['stubs']}/{v['pages']} "
                    f"| {v['mermaid']} |")
    rows.append(f"| **Total** | **110,000** | **{wc['total_words']:,}** | | **{wc['mermaid_total']}** |")
    rows.append("")
    rows.append(f"Modules 02+03: {wc['priority_words']:,} words ({wc['priority_share']:.0%} of total; target "
                f"≥ 75,000 and ≈ 70%). Mermaid in 02–03: {wc['mermaid_02_03']} (target ≥ 100). "
                f"TODO(verify) markers: {wc['todo_verify']}.")
    table = "\n".join(rows)
    text = re.sub(r"(## Word count vs budget\n\n_Updated[^\n]*_\n\n)(.*?)(\n## )",
                  lambda m: m.group(1) + table + "\n" + m.group(3), text, flags=re.S)
    PLAN.write_text(text, encoding="utf-8")
    n_done = len(re.findall(r"- \[x\] `", text))
    n_all = len(re.findall(r"- \[[ x]\] `", text))
    print(f"PLAN.md updated: {n_done}/{n_all} pages written; total words {wc['total_words']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
