# CLAUDE.md: conventions for building this knowledge base

Read this file fully before writing anything. `BUILD_SPEC.md` is the original brief (source of truth
for scope); `PLAN.md` tracks progress. This file turns the brief into exact, checkable conventions.

## 1. Purpose and reader

A GitHub-hosted, MkDocs-published knowledge base on **how quantitative trading firms trade US
equities**, strategies and algorithms first. The goal is a medium-deep, accurate mental model: enough to
discuss any strategy family with a quant, follow signal → forecast → portfolio → orders → fills → P&L,
read short Python for core algorithms, and tell insight from marketing.

**Reader profile (anonymized):** an experienced finance professional (CFA charterholder; corporate
development / M&A in semiconductors and AI infrastructure; former capital-markets lawyer). Strong on
valuation, accounting, capital markets, filings. Statistics at CFA level; knows ML conceptually; reads
Python comfortably; not a production engineer. Familiar with chips and datacenter hardware.

Calibration: skip finance basics (one-line reminders at most). Teach from first principles:
microstructure, stat-arb math, finance-specific ML/time-series pitfalls, optimization, execution theory,
market-making models. In modules 02–03 go one level deeper than a typical overview: real formulas
(collapsible), real pseudocode, realistic parameter values, practitioner tweaks. Lead with intuition.
Use accounting-native framing where it helps (e.g. a market maker's P&L as an income statement).
**Never put personal data about the reader in the repo.**

## 2. Priority statement and budget

**Modules 02 (Strategies) and 03 (Algorithms) carry this KB. They get most of the words, the best
writing, the most labs and the strictest QA. They are never cut.** Everything else is supporting context.

| # | Module | Priority | Target words |
|---|---|---|---|
| 00 | Start here | Support | 2,500 |
| 01 | Market structure essentials | Support (prerequisite) | 8,000 |
| **02** | **Strategies** (30 dossiers + 7 overview pages) | **TOP** | **35,000+** |
| **03** | **Algorithms** (39 cards + 3 overviews + 4 walkthroughs) | **TOP** | **42,000+** |
| 04 | Industry & firms (~18 profiles) | Support | 5,000 |
| 05 | Infrastructure | Support | 3,500 |
| 06 | Risk & regulation | Support | 2,500 |
| 07 | Conversation playbook | High | 5,000 |
| 08 | Calibration & skepticism | Medium | 2,500 |
| 09 | Reference (glossary 400+, acronyms 150+) | Support | 5,500 |
| 10 | Self-test (quizzes, 300+ flashcards) | Support | n/a |

Totals: ≥ 110,000 words; modules 02+03 ≥ 75,000 words (≈ 70%). Cut order if forced (cut first →
last): number of firm profiles → infrastructure depth → risk & regulation depth → resources annotations
→ calibration length. Never cut 02, 03, their labs or the four walkthroughs.

**How words are counted** (`scripts/wordcount.py`, `scripts/kb.py:prose_words`): prose and tables only.
Fenced code (pseudocode, Mermaid), HTML comments, URLs and the `## Sources` section are excluded.

## 3. Files, naming, layout

- kebab-case file names, `.md`, US English. One H1 per page (the title), first line of the file.
- The page tree is fixed by `mkdocs.yml` `nav`. Do not add pages without adding them to `nav`.
- Unwritten pages are stubs containing `<!-- STUB -->`. **When you write a page, remove the stub
  marker and the "Not yet written" admonition.**
- Plots from labs live in `docs/assets/labs/labNN-<name>.png`. Lab code lives in `labs/NN-<name>/`.

### Relative link cheat sheet (MkDocs resolves `.md` links relative to the current file)

| From a page in… | to glossary | to a dossier | to an algorithm card | to a lab plot |
|---|---|---|---|---|
| `docs/0X-module/page.md` | `../09-reference/glossary.md#slug` | `../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md` | `../03-algorithms/d-portfolio-construction/risk-models.md` | `../assets/labs/lab14-frontier.png` |
| `docs/02-strategies/x-family/page.md` (and 03 cards, firm profiles) | `../../09-reference/glossary.md#slug` | `../c-statistical-arbitrage/pairs-trading-and-cointegration.md` (same module) | `../../03-algorithms/d-portfolio-construction/risk-models.md` | `../../assets/labs/lab14-frontier.png` |
| `docs/index.md`, `docs/labs.md` | `09-reference/glossary.md#slug` | `02-strategies/...` | `03-algorithms/...` | `assets/labs/...` |

**Glossary anchors:** link a term on first use per page as `[microprice](../../09-reference/glossary.md#microprice)`.
The anchor slug is the glossary heading lowercased, punctuation removed, spaces → hyphens
(Python-Markdown default): "Order-flow imbalance (OFI)" → `order-flow-imbalance-ofi`; "Implementation
shortfall" → `implementation-shortfall`; "VWAP" → `vwap`. Use singular, plain-ASCII term names. Glossary
headings must be ASCII (write "Avellaneda-Stoikov model", not an en dash). Missing anchors are listed by
`python scripts/check_glossary_links.py --missing` and are filled by the glossary pass; just link sensibly.

**Lab links:** link labs by absolute GitHub URL, e.g.
`[Lab 05](https://github.com/FrankHuang94/quant_trading_claude/tree/main/labs/05-avellaneda-stoikov-glft-quoting)`.
Embed the lab's committed plot with a relative image link and a caption line in italics.

### Algorithm card IDs (stable; used by the matrix and the algorithm map)

| ID | Card | ID | Card | ID | Card |
|---|---|---|---|---|---|
| D1 | point-in-time-data-and-cleaning | P1 | risk-models | M1 | anatomy-of-an-hft-trading-loop |
| D2 | feature-engineering | P2 | covariance-estimation-and-shrinkage | M2 | fair-value-and-microprice |
| D3 | signal-transforms | P3 | mean-variance-optimization | M3 | order-book-and-trade-flow-signals |
| D4 | evaluating-signals | P4 | alternatives-to-mvo | M4 | quoting-and-inventory-control |
| F1 | linear-models-and-regularization | P5 | transaction-cost-and-impact-models | M5 | adverse-selection-and-markouts |
| F2 | tree-ensembles | P6 | multi-period-and-trading-toward-aim | M6 | queue-position-and-order-placement |
| F3 | neural-nets-and-sequence-models | P7 | position-sizing-and-risk-budgeting | M7 | hedging-algorithms |
| F4 | llms-and-foundation-models-in-quant | E1 | execution-algorithms-overview | M8 | options-pricing-and-vol-surfaces-for-mm |
| F5 | alpha-combination-and-ensembling | E2 | vwap-twap-pov | M9 | algorithmic-risk-controls |
| F6 | regime-detection | E3 | implementation-shortfall-and-almgren-chriss | L1 | live-monitoring-and-pnl-attribution |
| V1 | time-series-cross-validation | E4 | smart-order-routing | L2 | alpha-decay-detection-and-model-retirement |
| V2 | backtesting-engines | E5 | auction-close-and-dark-liquidity-algos | L3 | reinforcement-learning-in-trading |
| V3 | backtest-pitfalls | E6 | transaction-cost-analysis | | |
| V4 | overfitting-and-multiple-testing | | | | |

Folders: D = `a-data-and-signals`, F = `b-forecasting-models`, V = `c-validation-and-backtesting`,
P = `d-portfolio-construction`, E = `e-execution-algorithms`, M = `f-market-making-and-hft-algorithms`,
L = `g-live-trading`.

### Strategy × algorithm consistency rule

`scripts/check_matrix.py` derives the matrix from page headers: an algorithm card linked in a dossier's
**Core algorithms used** field = core (●); a dossier linked in a card's **Used by strategies** field but
not core = supporting (○). So: put only the 2–6 truly central cards in "Core algorithms used"; list in a
card's "Used by strategies" every dossier that materially uses it. Regenerate with `make matrix`.

## 4. Templates

### 4.1 Strategy dossier (every page in `docs/02-strategies/a-…` to `g-…`)

Length (prose words): **900–1,500**; up to **2,200** for equity/ETF/options market making, stat-arb
overview, pairs, factor-residual, cross-sectional alpha, momentum. Aim ~1,200–1,450 (long ones ~1,800).
Every H2 below is required, in this order, with these exact leading words.

````markdown
# Pairs trading and cointegration

> **TL;DR**
>
> - 3–5 bullets you could repeat in conversation.

**Level:** Core · **Read time:** ~8 min · **Last verified:** 2026-11

| Field | Value |
|---|---|
| Family | stat arb |
| Edge source | behavioral · liquidity provision |
| Holding period | days to weeks |
| Counterparty: who pays and why they accept it | … |
| Universe & instruments | … |
| Data required | … |
| Core algorithms used | [D3 Signal transforms](../../03-algorithms/a-data-and-signals/signal-transforms.md) · [P5 …](…) |
| Infra intensity | low latency sensitivity; overnight batch compute |
| Capacity (rough $ range) | $100M–$1B per firm `[Estimate]` (reasoning: …) |
| Typical Sharpe (gross vs net) | gross 1.0–1.5, net 0.3–0.8; 1962–2002 academic backtest, decayed after publication `[Reported]` |
| Turnover | … |
| Main risks / failure modes | … |
| Crowding risk | … |
| Firm types that run it | … (specific firms only if sourced) |
| Lab | [Lab 08](https://github.com/FrankHuang94/quant_trading_claude/tree/main/labs/08-pairs-cointegration) or "—" |

## Intuition (the story in plain English)
## Economic rationale: why should this make money at all?
## The trade, step by step
## Worked example with numbers
(P&L math shown; label illustrative numbers as illustrative)
## Signals and algorithms under the hood
(link each algorithm card; one ```python block of 10–25 lines of pseudocode for the core logic,
consistent with the lab if there is one; embed the lab plot if there is one)
## Implementation choices that matter
## P&L decomposition
## Evidence
## Capacity, crowding and decay
## How it fails
## Textbook vs how it's done today
(each claim says how it is known: link, paper, firm talk/blog, or a tag such as `[Lore]`)
## Variants and neighbours
## Diagram
(≥ 1 Mermaid diagram here; more elsewhere are welcome)
## How practitioners talk about it
(6–10 example sentences, each followed by a gloss)
## Myths vs reality
## Questions you could ask a quant about this
(ordered basic → informed → sharp; mark proprietary territory with 🔒)
## Go deeper
<details markdown="1">
<summary>Math: …</summary>

$$ … $$

</details>

## Related pages
(≥ 3 internal links)
## Sources
(see §6 for the line format)
````

### 4.2 Algorithm card (every page in `docs/03-algorithms/a-…` to `g-…`)

Length: **700–1,200**; up to **1,700** for MVO, risk models, quoting & inventory, alpha combination,
time-series CV. Aim ~950–1,150 (long ones ~1,450).

````markdown
# Mean-variance optimization

> **TL;DR**
>
> - 3–5 bullets.

**Level:** Core · **Pipeline stage:** portfolio · **Last verified:** 2026-11

| Field | Value |
|---|---|
| Purpose (the question it answers) | … |
| Inputs → Outputs | … |
| Used by strategies | [Cross-sectional alpha](../../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md) · … |
| Latency / compute regime | overnight batch (seconds per solve for 3,000 names) |
| Key parameters | risk aversion λ 1–50; turnover penalty …; position caps 1–3% NAV |
| Main failure modes | … |
| Lab | [Lab 14](https://github.com/FrankHuang94/quant_trading_claude/tree/main/labs/14-risk-model-mvo) or "—" |

## Intuition
## Where it sits in the pipeline
(Mermaid diagram showing upstream inputs and downstream consumers; highlight this card's node)
## The algorithm
(plain-English numbered steps, then ONE ```python pseudocode block, ≤ 40 non-blank lines, commented,
consistent with the lab implementation: same function/variable names where possible)
## Worked example with numbers
## Key parameters and how practitioners tune them
## Textbook version vs what firms actually do
(sourced or tagged)
## How to tell if it's working
## Failure modes and pitfalls
## How practitioners talk about it
## Questions you could ask a quant about this
## Go deeper
<details markdown="1"> … </details>
## Related pages
## Sources
````

Pipeline stage is one of: data | signal | forecast | validation | portfolio | execution | market making | live.

### 4.3 End-to-end walkthrough (`docs/03-algorithms/h-end-to-end-walkthroughs/`)

1,800–2,500 words; narrative + numbers, **reusing lab outputs** (quote `labs/NN-*/results.json`
numbers and embed lab plots); starts with `> **TL;DR**`; ≥ 1 Mermaid; links to every card it uses.

### 4.4 Firm profile (`docs/04-industry-and-firms/firm-profiles/`)

300–500 words. Sections: `> **TL;DR**`, metadata line `**Type:** … · **Last verified:** YYYY-MM`,
a `| Field | Value |` table with **Type, Scale, Horizon, Known strategies, Tech signals, Confidence,
Sources**, then `## What they do`, `## Strategy focus and approach`, `## Fact vs lore`,
`## Related pages`, `## Sources`. Every number tagged. Never invent strategies, revenue, people or quotes.

### 4.5 Module 01 pages

500–1,600 words, ≥ 1 Mermaid, last H2 is `## Why this matters for strategies & algorithms` with
forward links into 02–03, then `## Related pages` and `## Sources`.

## 5. Pseudocode and labs

### 5.1 Pseudocode rules

- Mandatory in every card (`## The algorithm`) and every dossier (`## Signals and algorithms under the hood`).
- Readable Python, commented, no imports beyond numpy/pandas conventions (`np`, `pd`). Cards ≤ 40
  non-blank lines; dossiers 10–25 lines.
- **Must match the lab code** when a lab exists: same algorithm, same parameter names, same sign
  conventions. Read the lab's `lab.py` before writing pseudocode. If you simplify, say so in a comment.

### 5.2 Labs: layout and API

```text
labs/
  common/
    utils.py      # setup(), save_fig(), write_results(), annualized_sharpe(), max_drawdown()
    simulate.py   # the synthetic market engine (see docstring for the full API)
    orderbook.py  # price-time-priority limit order book / matching engine
    options.py    # Black-Scholes price, greeks, implied vol
  NN-name/
    lab.py        # runnable: python labs/NN-name/lab.py [--smoke] [--seed N]
    README.md     # what it demonstrates · supports (links) · how to run · expected output ·
                  # "What this toy misses vs the real world"
    results.json  # key numbers from the full run (committed; quoted by pages)
```

Every `lab.py` starts like this:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import utils, simulate   # noqa: E402

def main():
    ctx = utils.setup(__file__, "Lab 08: pairs trading with cointegration")
    n_days = 300 if ctx.smoke else 1500
    ...
    utils.save_fig(ctx, fig, "spread")          # -> docs/assets/labs/lab08-spread.png (full run)
    utils.write_results(ctx, {"sharpe_net": s}) # -> labs/08-pairs-cointegration/results.json
```

Rules: deterministic given `--seed`; full run of all labs < 15 min total (aim < 60 s each); smoke run
< 60 s each (aim < 15 s) and writes only to `labs/_smoke/`; 1–2 plots per lab, readable at 900 px
width, titled, axes labeled, illustrative units stated; optional deps (lightgbm) imported in
`try/except` with a sklearn fallback; print a short human-readable summary.

| # | Directory | Supports |
|---|---|---|
| 01 | `01-matching-engine-order-book` | the-limit-order-book (01), queue-position card |
| 02 | `02-microprice-fair-value` | fair-value-and-microprice |
| 03 | `03-order-flow-imbalance` | order-book-and-trade-flow-signals |
| 04 | `04-markout-analysis` | adverse-selection-and-markouts, equity-market-making |
| 05 | `05-avellaneda-stoikov-glft-quoting` | quoting-and-inventory-control, equity-market-making |
| 06 | `06-options-mm-delta-hedging` | options-market-making, options-pricing-and-vol-surfaces-for-mm, hedging-algorithms |
| 07 | `07-etf-nav-arbitrage` | etf-market-making, etf-and-index-arbitrage |
| 08 | `08-pairs-cointegration` | pairs-trading-and-cointegration |
| 09 | `09-pca-residual-stat-arb` | factor-residual-mean-reversion |
| 10 | `10-reversal-momentum-costs` | short-term-cross-sectional-reversal, momentum |
| 11 | `11-signal-transforms-ic` | signal-transforms, evaluating-signals |
| 12 | `12-alpha-combination-purged-cv` | alpha-combination-and-ensembling, time-series-cross-validation |
| 13 | `13-backtest-overfitting-dsr-pbo` | overfitting-and-multiple-testing |
| 14 | `14-risk-model-mvo` | risk-models, covariance-estimation-and-shrinkage, mean-variance-optimization |
| 15 | `15-trading-toward-aim` | multi-period-and-trading-toward-aim |
| 16 | `16-almgren-chriss-frontier` | implementation-shortfall-and-almgren-chriss |
| 17 | `17-vwap-twap-pov` | vwap-twap-pov, execution-algorithms-overview |
| 18 | `18-smart-order-router` | smart-order-routing |
| 19 | `19-trend-following-vol-targeting` | trend-following-and-ctas, position-sizing-and-risk-budgeting |
| 20 | `20-index-reconstitution-event-study` | flow-driven-strategies |

Each lab README must include the section **"What this toy misses vs the real world"**.

## 6. Research, confidence tags and sources

1. Research with web search/fetch. **Do not write time-sensitive facts, figures, firm details or
   regulatory status from memory.** Verify; if you cannot, write `TODO(verify): …` inline.
2. Source hierarchy: primary (regulators' rules/orders, exchange specs and fee schedules, filings,
   papers, firm blogs/talks) → reputable financial press → practitioner books → anything else (flag it).
   Avoid SEO/retail "algo trading" content farms.
3. Confidence tags on **every number and firm-specific claim**: `[Verified]` primary source ·
   `[Reported]` credible secondary · `[Estimate]` derived (show the reasoning) · `[Lore]` widely
   repeated, unverified. Write tags in backticks or plain brackets; both count. Show ranges when
   sources conflict.
4. Sharpe / capacity / return figures state: gross or net, period, source type (academic backtest /
   fund disclosure / practitioner estimate), and known post-publication decay.
5. Never invent firm-specific strategies, revenue figures, people, quotes or paper titles.
   Illustrative numbers in worked examples are fine **if labeled illustrative**.
6. Copyright: paraphrase; quotes rare and under ~15 words; never reproduce book passages; link instead.
7. **`## Sources` line format** (compiled into `references/sources.md` by `make sources`; one per line):

```markdown
- [Verified] Avellaneda, M. & Stoikov, S. (2008). "High-frequency trading in a limit order book." *Quantitative Finance* 8(3), 217–224. <https://doi.org/10.1080/14697680701381228> (accessed 2026-11)
- [Reported] Financial Times (2025-01-15). "Headline here." <https://www.ft.com/...> (accessed 2026-11)
```

Tag first, then author/org, (date), title, venue, `<URL>`, `(accessed YYYY-MM)`. Prefer DOI or the
publisher/regulator URL; SSRN/arXiv are fine for papers.

## 7. Writing standards

- Practitioner voice: plain English, precise, concrete numbers, no hype. US English.
- Order: intuition → mechanics → numbers → pseudocode → math (math collapsible in `<details markdown="1">`).
- Math: `$…$` inline and `$$…$$` display (arithmatex). Leave a blank line before and after `$$` blocks.
- **Currency: write dollar amounts as `\$500M`, `\$0.0030`** (backslash-escaped). Unescaped `$50M–$200M` is parsed as inline math and garbles the page. `python scripts/fix_dollars.py` escapes them automatically; `--check` reports any left.
- Define terms on first use and link them to the glossary. Each page links to ≥ 3 related pages.
- Tables for comparisons; date-stamp anything time-sensitive ("as of 2026-11").
- Contested topics: each side's strongest evidence; no verdict where evidence is mixed.
- **Mermaid** (≥ 1 per page in 01–03; 140+ overall): use `flowchart LR`/`TD`, `sequenceDiagram`,
  `quadrantChart`, `timeline`, `stateDiagram-v2`. Keep node IDs alphanumeric (`A1`, `fv`), put labels in
  double quotes when they contain punctuation, e.g. `fv["Fair value (microprice)"]`; never use double
  quotes inside a label; use `<br/>` for line breaks; don't name a node `end`; avoid `&` and `;` in
  labels (write "and"). Validate with `node scripts/check_mermaid.mjs <files>` if available.
- Admonitions (`!!! note`, `!!! warning`) are fine; use them sparingly.

## 8. Checks, commits and workflow

```bash
export PATH=/home/user/venv-qt/bin:$PATH          # local venv used by the build session
python scripts/check_template.py docs/02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md
python scripts/check_template.py --quiet          # all written dossiers/cards/firms/01 pages
python scripts/check_matrix.py [--write]          # strategy x algorithm matrix
python scripts/check_glossary_links.py [--missing]
python scripts/wordcount.py [--pages]
mkdocs build --strict --site-dir "$(mktemp -d)"   # authoritative link check
python scripts/run_labs.py [--smoke] [--only 05]  # labs
make check                                        # all of the above (site dir = site/)
```

- Commit convention: `module-XX: <what>` (e.g. `module-02: stat-arb dossiers`, `labs: 08-10`).
  Only the orchestrating session commits and pushes; helper agents never run `git commit`/`git push`.
- Phase order and status live in `PLAN.md`; update it after each phase with word counts vs budget.

## 9. Definition of done (summary of BUILD_SPEC §10)

Priority (02–03): ≥ 30 dossiers and ≥ 39 cards passing `check_template.py` within length; 02+03 ≥
75,000 words; every card/dossier has pseudocode, worked numeric example, ≥ 1 Mermaid, sourced/tagged
textbook-vs-practice; every strategy states counterparty, edge source, horizon, capacity and Sharpe
(gross/net, period, source type, confidence); 4 walkthroughs consistent with labs; matrix passes;
all 20 labs run (`make labs` < 15 min) and are embedded; 40-claim fact-check logged in PLAN.md.

Whole KB: ≥ 110,000 words; Core Path ≤ ~25k words with ≥ 60% from 02–03 (`scripts/core_path.txt`);
≥ 140 Mermaid; `mkdocs build --strict` passes; glossary ≥ 400 terms; acronyms ≥ 150; elevator
explanations ≥ 70; questions-to-ask by strategy and pipeline stage; 6 mock conversations; myths ≥ 25
(≥ 15 strategies/algorithms); `references/sources.md` ≥ 150 unique sources; no `TODO(verify)` in Core
Path pages; quizzes for every module (priority modules 2× longer); flashcards ≥ 300; lychee,
markdownlint and CI pass; GitHub Pages live; README has module map, learning paths, site link and
"How this was built / limitations".
