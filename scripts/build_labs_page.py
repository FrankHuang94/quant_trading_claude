#!/usr/bin/env python3
"""Generate docs/labs.md (the lab catalog) from each lab's README.md, plots and results.json.

Usage: python scripts/build_labs_page.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "labs.md"
GH = "https://github.com/FrankHuang94/quant_trading_claude/tree/main/labs"

GROUPS = [
    ("Market microstructure and market making", ["01", "02", "03", "04", "05"]),
    ("Options, ETFs and arbitrage", ["06", "07"]),
    ("Statistical arbitrage and factors", ["08", "09", "10", "19", "20"]),
    ("Signals, combination and validation", ["11", "12", "13"]),
    ("Portfolio construction", ["14", "15"]),
    ("Execution", ["16", "17", "18"]),
]


def section(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^## {re.escape(name)}\s*$(.*?)(?=^## |\Z)", text)
    return m.group(1).strip() if m else ""


def first_paragraph(body: str, max_words: int = 70) -> str:
    para = []
    for line in body.splitlines():
        if not line.strip():
            if para:
                break
            continue
        para.append(line.strip())
    text = " ".join(para)
    text = re.sub(r"^\d+\.\s+", "", text)
    words = text.split()
    if len(words) > max_words:
        cut = " ".join(words[:max_words])
        dot = cut.rfind(". ")
        text = cut[: dot + 1] if dot > 80 else cut + " …"
    return text


def supports(body: str) -> list[str]:
    out = []
    for label, href in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", body):
        if "docs/" in href:
            rel = href.split("docs/", 1)[1]
            if (ROOT / "docs" / rel.split("#")[0]).exists():
                out.append(f"[{label}]({rel})")
    seen = []
    for x in out:
        if x not in seen:
            seen.append(x)
    return seen


def main() -> int:
    labs = {p.name[:2]: p for p in sorted(ROOT.glob("labs/[0-9][0-9]-*")) if (p / "README.md").exists()}
    lines = [
        "# Labs",
        "",
        "> **TL;DR**",
        ">",
        "> - 20 runnable Python labs on **synthetic data**, each backing specific strategy dossiers and algorithm cards.",
        "> - The simulator (`labs/common/simulate.py`) plants effects of *known* strength, so every lab can show "
        "whether a method recovers the truth, and how often noise fools it.",
        "> - Lab Sharpe ratios and P&Ls are **stylized**: they illustrate mechanisms and comparisons, not "
        "real-world levels. Each lab README lists what the toy misses.",
        "",
        "**Level:** Core · **Last verified:** 2026-11",
        "",
        "Run everything with `make labs` (about 4 minutes) or one lab with "
        "`python labs/NN-name/lab.py`; `--smoke` runs a tiny version (what CI runs). Plots below are "
        "from the committed full runs (seed 7).",
        "",
        "```mermaid",
        "flowchart LR",
        "  sim[\"labs/common/simulate.py<br/>synthetic market engine\"]",
        "  sim --> eq[\"Equity cross-section<br/>with planted alphas\"]",
        "  sim --> lob[\"Limit-order-book<br/>and trade flow\"]",
        "  sim --> opt[\"Heston option chains<br/>with a variance risk premium\"]",
        "  sim --> fut[\"Futures panel<br/>with trends\"]",
        "  sim --> intr[\"Intraday volume<br/>and price session\"]",
        "  lob --> L1[\"Labs 01-05<br/>microstructure, market making\"]",
        "  opt --> L6[\"Lab 06<br/>options MM\"]",
        "  eq --> L7[\"Labs 07-15, 20<br/>ETF arb, stat arb, signals, portfolio\"]",
        "  fut --> L19[\"Lab 19<br/>trend following\"]",
        "  intr --> L17[\"Labs 16-18<br/>execution\"]",
        "```",
        "",
    ]
    for title, ids in GROUPS:
        lines += [f"## {title}", ""]
        for nn in ids:
            p = labs.get(nn)
            if not p:
                continue
            readme = (p / "README.md").read_text(encoding="utf-8")
            h1 = readme.splitlines()[0].lstrip("# ").strip()
            demo = first_paragraph(section(readme, "What it demonstrates"))
            sup = supports(section(readme, "Supports"))
            plots = sorted((ROOT / "docs" / "assets" / "labs").glob(f"lab{nn}-*.png"))
            lines += [f"### {h1}", ""]
            if demo:
                lines += [demo, ""]
            if sup:
                lines += ["**Supports:** " + " · ".join(sup), ""]
            lines += [f"**Code:** [`labs/{p.name}/`]({GH}/{p.name}) · run `python labs/{p.name}/lab.py`", ""]
            if plots:
                lines += [f"![{h1}](assets/labs/{plots[0].name})", ""]
    lines += [
        "## Related pages",
        "",
        "- [Algorithms: overview](03-algorithms/index.md)",
        "- [Strategies: the map](02-strategies/index.md)",
        "- [There is no single algorithm](03-algorithms/there-is-no-single-algorithm.md)",
        "",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"labs.md written: {len(labs)} labs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
