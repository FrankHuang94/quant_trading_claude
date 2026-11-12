# quant_trading_claude

**A knowledge base on how quantitative trading firms trade US equities, with strategies and algorithms first.**

**Site:** <https://frankhuang94.github.io/quant_trading_claude/> (published from the `gh-pages` branch by
`.github/workflows/pages.yml`; GitHub Pages must be enabled once in the repository settings, see
"Publishing" below).

This repository is a GitHub-hosted, MkDocs-published knowledge base for a finance professional who wants a
medium-deep, accurate mental model of quant trading: what quant firms actually trade, why each strategy
makes money, who is on the other side, and the concrete algorithms inside the research-and-trading
pipeline, from signal construction to execution and market-making quoting logic. It has about 250,000
words, 218 diagrams, 20 runnable labs and 1,058 cited sources.

## Start with strategies & algorithms

Two modules carry the knowledge base. They hold about 129,000 of its words, every lab and the
strictest QA:

| Module | What's inside |
|---|---|
| [02 · Strategies](docs/02-strategies/index.md) ★ | 30 strategy dossiers (market making, speed/structural, stat arb, mid-frequency alpha, factors, volatility, futures), a strategy map, how quants evaluate a strategy, comparison matrix, strategy × algorithm matrix, a failure gallery of 9 episodes (1998–2024) |
| [03 · Algorithms](docs/03-algorithms/index.md) ★ | 39 algorithm cards (data & signals, forecasting, validation, portfolio construction, execution, market making & HFT, live trading), "there is no single algorithm" (5 canonical pipelines), algorithm map, **4 end-to-end walkthroughs** |

Every dossier states its edge source, counterparty, horizon, capacity and Sharpe range (gross/net,
period, source type, confidence tag). Every card has intuition, ≤ 40-line pseudocode that matches its
lab, a worked numeric example and a sourced "textbook vs practice" section.

## Learning paths

See [Learning paths](docs/00-start-here/learning-paths.md):

- **90-minute sprint:** the big picture, the strategy map, "there is no single algorithm", one
  market-making and one stat-arb dossier, a walkthrough skim and the cheat sheet.
- **4-hour Core Path:** 14 pages, about 24,700 words, 85% of them from modules 02–03
  (`scripts/core_path.txt`).
- **2-week Deep Path:** all of modules 02 and 03 with their labs and walkthroughs, then the supporting
  modules, quizzes and flashcards.

## Module map

| # | Module | Pages | Words | Highlights |
|---|---|---|---|---|
| 00 | [Start here](docs/00-start-here/the-big-picture.md) | 3 | 3.2k | big picture, learning paths, one-page cheat sheet |
| 01 | [Market structure essentials](docs/01-market-structure/life-of-a-stock-order.md) | 9 | 10.9k | order life, LOB and queue value, auctions, venues and PFOF, NBBO/SIP, fees and ticks, linkages, shorting/T+1, recent changes as of 2026-11 |
| **02** | [**Strategies**](docs/02-strategies/index.md) | 37 | 65.8k | 30 dossiers + 7 overview/cross-cutting pages |
| **03** | [**Algorithms**](docs/03-algorithms/index.md) | 46 | 63.4k | 39 cards + 3 overviews + 4 walkthroughs |
| 04 | [Industry & firms](docs/04-industry-and-firms/taxonomy-of-quant-firms.md) | 23 | 11.7k | taxonomy, economics, roles, competitive dynamics & M&A, 18 firm profiles |
| 05 | [Infrastructure](docs/05-infrastructure/how-infrastructure-constrains-algorithms.md) | 4 | 3.8k | latency budgets, colocation and the speed of light, tech stacks, a semiconductor lens |
| 06 | [Risk & regulation](docs/06-risk-and-regulation/risk-management-at-quant-firms.md) | 2 | 2.6k | firm risk practice; rules that shape strategies |
| 07 | [Conversation playbook](docs/07-conversation-playbook/how-to-talk-to-a-quant.md) | 5 | 26.9k | 74 elevator explanations, 139 questions to ask, 6 mock conversations, faux pas |
| 08 | [Calibration](docs/08-calibration/myths-vs-reality.md) | 3 | 4.5k | 28 myths, 8 contested debates, a sanity-check checklist |
| 09 | [Reference](docs/09-reference/glossary.md) | 6 | 36.8k | 444-term glossary, 194 acronyms, books, 120 papers, talks, datasets & tools |
| 10 | [Self-test](docs/10-self-test/index.md) | 11 | 18.8k | 10 quizzes (174 questions), 425 Anki-ready flashcards |
| | [Labs](docs/labs.md) | | | 20 Python labs on synthetic data, plus walkthrough helpers |

## Repository layout

```text
docs/        the knowledge base (MkDocs Material site)
labs/        20 Python labs on synthetic data (labs/common/simulate.py is the market simulator)
             labs/walkthroughs/ holds the scripts behind the four end-to-end walkthroughs
scripts/     checks and generators: templates, word counts, glossary links, strategy x algorithm matrix,
             Mermaid validation, dollar-sign escaping, bibliography, labs page, plan tracker
references/  master bibliography (generated: references/sources.md)
BUILD_SPEC.md, CLAUDE.md, PLAN.md   the original brief, the writing conventions and the build log
```

## Build locally

```bash
python -m venv .venv && . .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
make site          # mkdocs build --strict
make labs          # run all 20 labs (about 4 minutes on a laptop)
make labs-smoke    # every lab with a tiny parameter set (what CI runs)
make walkthroughs  # regenerate the numbers behind the four walkthroughs
make check         # templates, matrix, glossary, dollar escaping, word counts + strict build
make lint          # markdownlint
```

`node scripts/check_mermaid.mjs` validates every Mermaid diagram with the real parser (needs Node,
Playwright and `npm install --no-save mermaid@11.4.1`).

## Publishing

`.github/workflows/pages.yml` builds the site and pushes it to the `gh-pages` branch on every push to
`main`. To serve it, enable GitHub Pages once: **Settings → Pages → Build and deployment → Source:
Deploy from a branch → Branch: `gh-pages` / `(root)` → Save**. The site then appears at the URL above.

## How this was built / limitations

- **How:** the knowledge base was researched and written with AI assistance (Claude) from public
  sources: regulators' rules and orders, exchange documents, company filings, peer-reviewed papers,
  firm blogs and talks, and reputable press. The build followed [`BUILD_SPEC.md`](BUILD_SPEC.md) and the
  conventions in [`CLAUDE.md`](CLAUDE.md). Progress, decisions and the priority-gate fact-check are logged
  in [`PLAN.md`](PLAN.md).
- **Verification:** every number and firm-specific claim carries a confidence tag (`[Verified]`
  primary source, `[Reported]` credible secondary source, `[Estimate]` derived, `[Lore]` unverified).
  Seven reviewers re-read modules 02–03 and fact-checked 49 high-stakes claims; 20 of them were corrected
  or downgraded. Automated checks cover templates, the strategy × algorithm matrix, glossary anchors,
  Mermaid syntax, internal links (lychee) and Markdown lint.
- **Limitations:**
  - Firm details are public-source only; nothing here is insider information. Where a claim is widely
    repeated but unverified, it is tagged `[Lore]`.
  - Time-sensitive facts are dated (the build date is 2026-11). Regulatory status in particular changes
    often: the 2024 Reg NMS tick and access-fee amendments, for example, were delayed to November 2027.
  - The labs run on **synthetic data**. The simulator plants effects of known strength, so lab Sharpe
    ratios and P&Ls show mechanisms and comparisons, not real-world levels. Each lab README lists what
    the toy misses.
  - Some publishers and regulators block automated fetching, so a minority of sources were checked
    through abstracts, Crossref metadata or reputable summaries rather than full text; those claims are
    tagged accordingly.
  - Word budget: the knowledge base is about 250k words against a 110k target. Modules 02–03 are 129k
    words (52% of the total). The spec's required counts for the support modules (70+ two-version
    elevator explanations, 400+ glossary terms, 150+ annotated sources, quizzes) exceed their nominal
    budgets.
  - Not investment advice.

## License

Prose is licensed under CC BY 4.0; code (labs, scripts) under MIT. See [LICENSE](LICENSE).
