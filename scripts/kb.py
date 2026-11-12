"""Shared helpers for the knowledge-base check scripts.

Every script in scripts/ imports from here so that "what counts as a word",
"what is a dossier" and "what is an algorithm card" are defined exactly once.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STUB_MARK = "<!-- STUB -->"
GITHUB_URL = "https://github.com/FrankHuang94/quant_trading_claude"

# module folder -> (title, target words)
MODULES: dict[str, tuple[str, int]] = {
    "00-start-here": ("Start here", 2500),
    "01-market-structure": ("Market structure essentials", 8000),
    "02-strategies": ("Strategies", 35000),
    "03-algorithms": ("Algorithms & the trading pipeline", 42000),
    "04-industry-and-firms": ("Industry & firms", 5000),
    "05-infrastructure": ("Infrastructure", 3500),
    "06-risk-and-regulation": ("Risk & regulation", 2500),
    "07-conversation-playbook": ("Conversation playbook", 5000),
    "08-calibration": ("Calibration & skepticism", 2500),
    "09-reference": ("Reference", 5500),
    "10-self-test": ("Self-test", 0),
}

# Stable short IDs for the 39 algorithm cards (used by the strategy x algorithm matrix
# and the algorithm map). Never renumber; append if a card is added.
CARD_IDS: dict[str, str] = {
    "D1": "a-data-and-signals/point-in-time-data-and-cleaning",
    "D2": "a-data-and-signals/feature-engineering",
    "D3": "a-data-and-signals/signal-transforms",
    "D4": "a-data-and-signals/evaluating-signals",
    "F1": "b-forecasting-models/linear-models-and-regularization",
    "F2": "b-forecasting-models/tree-ensembles",
    "F3": "b-forecasting-models/neural-nets-and-sequence-models",
    "F4": "b-forecasting-models/llms-and-foundation-models-in-quant",
    "F5": "b-forecasting-models/alpha-combination-and-ensembling",
    "F6": "b-forecasting-models/regime-detection",
    "V1": "c-validation-and-backtesting/time-series-cross-validation",
    "V2": "c-validation-and-backtesting/backtesting-engines",
    "V3": "c-validation-and-backtesting/backtest-pitfalls",
    "V4": "c-validation-and-backtesting/overfitting-and-multiple-testing",
    "P1": "d-portfolio-construction/risk-models",
    "P2": "d-portfolio-construction/covariance-estimation-and-shrinkage",
    "P3": "d-portfolio-construction/mean-variance-optimization",
    "P4": "d-portfolio-construction/alternatives-to-mvo",
    "P5": "d-portfolio-construction/transaction-cost-and-impact-models",
    "P6": "d-portfolio-construction/multi-period-and-trading-toward-aim",
    "P7": "d-portfolio-construction/position-sizing-and-risk-budgeting",
    "E1": "e-execution-algorithms/execution-algorithms-overview",
    "E2": "e-execution-algorithms/vwap-twap-pov",
    "E3": "e-execution-algorithms/implementation-shortfall-and-almgren-chriss",
    "E4": "e-execution-algorithms/smart-order-routing",
    "E5": "e-execution-algorithms/auction-close-and-dark-liquidity-algos",
    "E6": "e-execution-algorithms/transaction-cost-analysis",
    "M1": "f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop",
    "M2": "f-market-making-and-hft-algorithms/fair-value-and-microprice",
    "M3": "f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals",
    "M4": "f-market-making-and-hft-algorithms/quoting-and-inventory-control",
    "M5": "f-market-making-and-hft-algorithms/adverse-selection-and-markouts",
    "M6": "f-market-making-and-hft-algorithms/queue-position-and-order-placement",
    "M7": "f-market-making-and-hft-algorithms/hedging-algorithms",
    "M8": "f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm",
    "M9": "f-market-making-and-hft-algorithms/algorithmic-risk-controls",
    "L1": "g-live-trading/live-monitoring-and-pnl-attribution",
    "L2": "g-live-trading/alpha-decay-detection-and-model-retirement",
    "L3": "g-live-trading/reinforcement-learning-in-trading",
}
CARD_ID_BY_PATH = {v: k for k, v in CARD_IDS.items()}

LONG_DOSSIERS = {
    "equity-market-making", "etf-market-making", "options-market-making",
    "stat-arb-overview-and-history", "pairs-trading-and-cointegration",
    "factor-residual-mean-reversion", "cross-sectional-alpha-and-neutralization",
    "momentum",
}
LONG_CARDS = {
    "mean-variance-optimization", "risk-models", "quoting-and-inventory-control",
    "alpha-combination-and-ensembling", "time-series-cross-validation",
}

FENCE_OPEN = re.compile(r"^(`{3,}|~{3,})\s*([\w+-]*)")
TAG_RE = re.compile(r"\[(Verified|Reported|Estimate|Lore)\]")
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def all_pages() -> list[Path]:
    return sorted(p for p in DOCS.rglob("*.md"))


def module_of(path: Path) -> str | None:
    rel = path.relative_to(DOCS).parts
    return rel[0] if rel and rel[0] in MODULES else None


def is_stub(text: str) -> bool:
    return STUB_MARK in text


def page_kind(path: Path) -> str:
    """dossier | card | walkthrough | firm | ms (module 01) | other"""
    rel = path.relative_to(DOCS).as_posix()
    parts = rel.split("/")
    if parts[0] == "02-strategies" and len(parts) == 3 and re.match(r"[a-g]-", parts[1]):
        return "dossier"
    if parts[0] == "03-algorithms" and len(parts) == 3 and re.match(r"[a-g]-", parts[1]):
        return "card"
    if parts[0] == "03-algorithms" and len(parts) == 3 and parts[1].startswith("h-"):
        return "walkthrough"
    if parts[0] == "04-industry-and-firms" and len(parts) == 3 and parts[1] == "firm-profiles" \
            and parts[2] != "index.md":
        return "firm"
    if parts[0] == "01-market-structure":
        return "ms"
    return "other"


def split_code(text: str) -> tuple[list[str], list[tuple[str, str, int]]]:
    """Split markdown into prose lines and fenced code blocks.

    Returns (prose_lines, blocks) where each block is (lang, body, start_line_index).
    Handles fences indented inside lists / <details>.
    """
    prose: list[str] = []
    blocks: list[tuple[str, str, int]] = []
    in_code = False
    fence = ""
    lang = ""
    buf: list[str] = []
    start = 0
    for i, line in enumerate(text.splitlines()):
        s = line.strip()
        if not in_code:
            m = FENCE_OPEN.match(s)
            if m:
                in_code, fence, lang, buf, start = True, m.group(1), m.group(2).lower(), [], i
                continue
            prose.append(line)
        else:
            if s.startswith(fence[0] * 3) and set(s) <= set(fence[0]) and len(s) >= len(fence):
                blocks.append((lang, "\n".join(buf), start))
                in_code = False
            else:
                buf.append(line)
    return prose, blocks


def sections(text: str, level: int = 2) -> dict[str, str]:
    """Map heading text -> section body (code blocks included) for one heading level."""
    out: dict[str, str] = {}
    current = None
    buf: list[str] = []
    in_code = False
    fence = ""
    prefix = "#" * level + " "
    for line in text.splitlines():
        s = line.strip()
        if not in_code:
            m = FENCE_OPEN.match(s)
            if m:
                in_code, fence = True, m.group(1)
            elif line.startswith(prefix):
                if current is not None:
                    out[current] = "\n".join(buf)
                current = line[len(prefix):].strip()
                buf = []
                continue
        elif s.startswith(fence[0] * 3) and set(s) <= set(fence[0]) and len(s) >= len(fence):
            in_code = False
        if current is not None:
            buf.append(line)
    if current is not None:
        out[current] = "\n".join(buf)
    return out


def find_section(secs: dict[str, str], prefix: str) -> tuple[str, str] | None:
    p = prefix.lower()
    for k, v in secs.items():
        if k.lower().startswith(p):
            return k, v
    return None


def _strip_sources(text: str) -> str:
    return re.sub(r"(?ms)^## Sources\s*$.*?(?=^## |\Z)", "", text)


def prose_words(text: str, drop_sources: bool = True) -> int:
    """Words a reader reads: excludes fenced code (incl. Mermaid), HTML comments,
    URLs, front matter and (by default) the bibliography section '## Sources'."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            text = text[end + 4:]
    if drop_sources:
        text = _strip_sources(text)
    prose, _ = split_code(text)
    t = "\n".join(prose)
    t = re.sub(r"(?s)<!--.*?-->", " ", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"<https?://[^>]+>", " ", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[#>*_|`]", " ", t)
    return sum(1 for w in t.split() if re.search(r"[A-Za-z0-9]", w))


def mermaid_count(text: str) -> int:
    _, blocks = split_code(text)
    return sum(1 for lang, _, _ in blocks if lang == "mermaid")


def links(text: str) -> list[tuple[str, str]]:
    prose, _ = split_code(text)
    return LINK_RE.findall("\n".join(prose))


def resolve(page: Path, href: str) -> tuple[Path | None, str]:
    """Resolve a relative markdown link from `page` -> (absolute path or None, anchor)."""
    if href.startswith(("http://", "https://", "mailto:")):
        return None, ""
    target, _, anchor = href.partition("#")
    if not target:
        return page, anchor
    return (page.parent / target).resolve(), anchor


def table_fields(text: str) -> dict[str, str]:
    """First markdown table whose header is 'Field | Value' -> {field: value}."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() == "field" and cells[1].lower() == "value":
            out: dict[str, str] = {}
            for row in lines[i + 2:]:
                if not row.strip().startswith("|"):
                    break
                parts = [c.strip() for c in row.strip().strip("|").split("|")]
                if len(parts) >= 2:
                    out[parts[0].strip("* ")] = " | ".join(parts[1:])
            return out
    return {}


def get_field(fields: dict[str, str], prefix: str) -> str | None:
    for k, v in fields.items():
        if k.lower().startswith(prefix.lower()):
            return v
    return None


def slugify(heading: str) -> str:
    """Same rule as Python-Markdown's default toc slugify."""
    import unicodedata
    value = unicodedata.normalize("NFKD", heading).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def card_rel(path: Path) -> str | None:
    """'b-forecasting-models/tree-ensembles' for a card path, else None."""
    try:
        rel = path.relative_to(DOCS / "03-algorithms").as_posix()
    except ValueError:
        return None
    rel = rel[:-3] if rel.endswith(".md") else rel
    return rel if rel in CARD_ID_BY_PATH else None


def dossier_rel(path: Path) -> str | None:
    try:
        rel = path.relative_to(DOCS / "02-strategies").as_posix()
    except ValueError:
        return None
    if not re.match(r"[a-g]-[^/]+/[^/]+\.md$", rel):
        return None
    return rel[:-3]
