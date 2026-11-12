#!/usr/bin/env python3
"""Escape currency dollar signs so the math extension does not pair them as inline math.

`pymdownx.arithmatex` treats `$...$` as inline math. Prose such as "$50M–$200M" or
"(~$2.3M) vs (~$1.1M)" then renders the text between two dollar signs as math. Writing
currency as `\\$50M` fixes it (renders "$50M" on the site and on GitHub).

This script rewrites `$<number>` (followed by a unit letter, comma, whitespace or punctuation)
to `\\$<number>` outside code blocks, inline code and `$$` display math. Real inline math such as
`$0.5$`, `$2\\sigma$` or `$\\lambda$` is left alone. It is idempotent.

Usage: python scripts/fix_dollars.py [--check] [paths...]
  --check   report lines that would change and spans that still look like currency-in-math; exit 1 if any
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
CURRENCY = re.compile(
    r"(?<![\\$])\$(?=\d[\d,]*(?:\.\d+)?(?:[MBTKk]\b|bn\b|mm\b|tn\b|\s(?![\\+=\-−*^/])|[,;:)\]–—%|]|/(?:share|sh|yr|year|day|mo|month|contract|order|trade|hr|hour)\b|$))"
)
INLINE_CODE = re.compile(r"`[^`\n]*`")
SUSPICIOUS = re.compile(r"(?<![\\$])\$(?!\s)((?:\\.|[^\\$\n])+?)(?<!\s)\$(?!\$)")


def fix_line(line: str) -> str:
    # protect inline code
    keep: list[str] = []

    def stash(m: re.Match) -> str:
        keep.append(m.group(0))
        return f"\x00{len(keep) - 1}\x00"

    work = INLINE_CODE.sub(stash, line)
    work = CURRENCY.sub(r"\\$", work)
    return re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], work)


def process(path: Path, check: bool) -> tuple[int, list[str]]:
    text = path.read_text(encoding="utf-8")
    out: list[str] = []
    changed = 0
    warnings: list[str] = []
    in_code = False
    fence = ""
    in_display = False
    for i, line in enumerate(text.splitlines(keepends=True)):
        s = line.strip()
        m = FENCE.match(line)
        if not in_code and m:
            in_code, fence = True, m.group(1)
            out.append(line)
            continue
        if in_code:
            if s.startswith(fence[0] * 3) and set(s) <= set(fence[0]):
                in_code = False
            out.append(line)
            continue
        if s.startswith("$$") or s.endswith("$$"):
            if s.count("$$") == 1:
                in_display = not in_display
            out.append(line)
            continue
        if in_display:
            out.append(line)
            continue
        new = fix_line(line)
        if new != line:
            changed += 1
        # any remaining pair that still looks like prose between dollars?
        probe = INLINE_CODE.sub(" ", new)
        for sm in SUSPICIOUS.finditer(probe):
            c = sm.group(1)
            words = re.findall(r"[A-Za-z]{3,}", re.sub(r"\\[A-Za-z]+", "", c))
            if len(words) >= 3:
                warnings.append(f"{path.relative_to(ROOT)}:{i + 1}: ${c[:70]}$")
        out.append(new)
    if changed and not check:
        path.write_text("".join(out), encoding="utf-8")
    return changed, warnings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()
    paths = [Path(p).resolve() for p in args.paths] if args.paths else \
        sorted(ROOT.glob("docs/**/*.md")) + sorted(ROOT.glob("labs/**/README.md")) + [ROOT / "README.md"]
    total = 0
    warns: list[str] = []
    for p in paths:
        n, w = process(p, args.check)
        total += n
        warns += w
        if n and args.check:
            print(f"would fix {n:3d} lines: {p.relative_to(ROOT)}")
    for w in warns:
        print("suspicious math span:", w)
    verb = "would change" if args.check else "changed"
    print(f"fix_dollars: {verb} {total} lines; {len(warns)} suspicious spans remain")
    return 1 if args.check and (total or warns) else 0


if __name__ == "__main__":
    sys.exit(main())
