# BUILD PROMPT — Quant Trading Knowledge Base (strategies & algorithms first)

## 0. Setup context (read first)
- The GitHub repo for this project **already exists** and you are running inside its local clone. Do **not** create a new repo. Run `git remote -v` and `git status` to identify it, then `git pull`. If this folder is not a git clone of a GitHub repo, stop and ask me for the repo URL. That is the only question you may ask before starting.
- If the repo already has files (e.g., a README or LICENSE created on GitHub), keep and extend them rather than overwriting them blindly.
- **First action:** save this entire prompt verbatim as `BUILD_SPEC.md` at the repo root and commit it. Future sessions will resume from it.

Defaults:
- Primary market: **US equities** (other markets only as comparison)
- Target size: **~110,000 words**, of which **~70% go to two priority modules: 02-strategies and 03-algorithms**
- Labs: **20 Python labs on synthetic data**
- Site: **MkDocs Material, published via GitHub Pages**

---

## 1. Role and mission

You are acting as a **senior quant practitioner plus a technical writer**: someone who has been a quantitative researcher and trader at both an electronic market maker and a systematic equity hedge fund, and who writes well for smart non-specialists. Research, write and publish a **GitHub-hosted knowledge base** on how quantitative trading firms trade stocks.

**Two topics carry this KB, and they get most of the words, the best writing, the most labs and the strictest QA:**
1. **Strategies:** what quant firms actually trade, why each strategy makes money, who is on the other side, how it is implemented, how it fails.
2. **Algorithms:** the concrete methods inside the research-and-trading pipeline: signal construction, forecasting models, alpha combination, validation and backtesting, risk models and portfolio optimization, execution algorithms, and market-making/HFT quoting and hedging logic. Each one is explained with intuition, pseudocode, a worked example and a lab.

Everything else (market structure, firms, infrastructure, regulation, history) is **supporting context**: written leaner, and present mainly so the strategies and algorithms make sense.

**Goal: a medium-deep, accurate mental model**, enough that the reader can:
- Discuss any major strategy family with a quant trader or researcher: its edge, mechanics, horizon, capacity, risks, and how practice differs from the textbook.
- Follow how an idea goes from signal → forecast → portfolio → orders → fills → P&L attribution, and ask sharp questions at each step.
- Read pseudocode or short Python for the core algorithms and understand what it does and where it breaks.
- Tell real insight from marketing, folklore and retail "algo trading" noise.

Execute the whole build **autonomously in a single agent session**. Do not stop for approval between phases. Stop only if truly blocked. Track progress in `PLAN.md` so a later session can resume.

---

## 2. The reader (calibrate everything to this person)

- A finance professional: **CFA charterholder with a corporate development / M&A background** in semiconductors and AI infrastructure; former capital-markets lawyer. Strong on valuation, accounting, capital markets, reading filings.
- Statistics at CFA level. Knows ML concepts conceptually. **Reads Python comfortably**; not a production engineer.
- Familiar with chips and datacenter hardware.

**Calibration rules:**
- **Skip** finance basics (stocks, shorting, options basics, what a hedge fund is). One-line reminders at most.
- **Teach from first principles:** microstructure, stat-arb math, finance-specific time-series and ML pitfalls, optimization, execution theory, market-making models.
- In the priority modules, go **one level deeper than a typical overview**: real formulas (collapsible), real pseudocode, realistic parameter values, and the practical tweaks practitioners make. Always lead with intuition.
- Use accounting-native framing where it helps (e.g., a market maker's P&L as a P&L statement: spread revenue, rebates, adverse-selection cost, inventory gains and losses, fees).
- Never put personal data about the reader in the repo.

---

## 3. Deliverables and word budget

| # | Module | Priority | Target words | Notes |
|---|---|---|---|---|
| 00 | Start here | Support | 2,500 | big picture, learning paths, cheat sheet |
| 01 | Market structure essentials | Support (prerequisite) | 8,000 | only what strategies & algorithms depend on |
| **02** | **Strategies** | **TOP** | **35,000** | 30 strategy dossiers + 7 overview/cross-cutting pages |
| **03** | **Algorithms & the trading pipeline** | **TOP** | **42,000** | 39 algorithm cards + 3 overview pages + 4 end-to-end walkthroughs |
| 04 | Industry & firms | Support | 5,000 | taxonomy, economics, ~18 short firm profiles |
| 05 | Infrastructure (as it constrains algorithms) | Support | 3,500 | 4 compact pages |
| 06 | Risk & regulation | Support | 2,500 | strategy-relevant rules only |
| 07 | Conversation playbook | High | 5,000 | tilted to strategies & algorithms |
| 08 | Calibration & skepticism | Medium | 2,500 | myths, debates, sanity checks |
| 09 | Reference: glossary, acronyms, resources | Support | 5,500 | glossary 400+ terms |
| 10 | Self-test | Support | n/a | quizzes + 300+ flashcards |

Plus: 20 Python labs, a master bibliography (150+ sources), a Strategy × Algorithm matrix, a MkDocs site, and CI.

**Cut order if time or context runs short** (cut from the top first): number of firm profiles → infrastructure depth → risk & regulation depth → resources annotations → calibration length. **Never cut modules 02 and 03, their labs, or the four walkthroughs.**

---

## 4. Repository structure

```
<repo root>/
├── README.md                 # what this is; Core Path; module map; "start with strategies & algorithms"
├── BUILD_SPEC.md             # this prompt, verbatim
├── CLAUDE.md                 # conventions for future sessions (see §9)
├── PLAN.md                   # living tracker: phases, checklist, word counts vs budget, open TODOs
├── CHANGELOG.md
├── LICENSE                   # CC BY 4.0 for prose; MIT for code (keep any existing license file in mind)
├── mkdocs.yml                # Material, search, Mermaid (superfences), admonitions, details, arithmatex
├── requirements.txt          # pinned: mkdocs stack + numpy pandas scipy statsmodels scikit-learn cvxpy matplotlib (+ optional lightgbm, numba)
├── Makefile                  # make site | make labs | make labs-smoke | make check | make wordcount
├── .github/workflows/{ci.yml,pages.yml}
├── docs/
│   ├── index.md
│   ├── 00-start-here/
│   │   ├── the-big-picture.md            # master map: firm types × horizon × alpha source
│   │   ├── learning-paths.md             # 90-min sprint · 4-hour Core Path · 2-week Deep Path
│   │   └── one-page-cheat-sheet.md
│   ├── 01-market-structure/              # lean; written to serve modules 02–03
│   │   ├── life-of-a-stock-order.md
│   │   ├── the-limit-order-book.md
│   │   ├── order-types-and-auctions.md
│   │   ├── venues-and-retail-flow.md
│   │   ├── nbbo-and-market-data.md
│   │   ├── fees-rebates-and-ticks.md
│   │   ├── etf-futures-options-linkages.md
│   │   ├── shorting-financing-and-settlement.md
│   │   └── recent-changes.md
│   ├── 02-strategies/                    # ★ TOP PRIORITY
│   │   ├── index.md                      # strategy map + how to read a dossier
│   │   ├── how-quants-evaluate-a-strategy.md
│   │   ├── a-liquidity-provision/
│   │   │   ├── equity-market-making.md
│   │   │   ├── etf-market-making.md
│   │   │   ├── options-market-making.md
│   │   │   ├── retail-flow-internalization.md
│   │   │   └── auctions-and-closing-liquidity.md
│   │   ├── b-speed-and-structural/
│   │   │   ├── latency-arbitrage.md
│   │   │   ├── lead-lag-and-cross-asset-arbitrage.md
│   │   │   ├── etf-and-index-arbitrage.md
│   │   │   └── fee-and-microstructure-driven-strategies.md
│   │   ├── c-statistical-arbitrage/
│   │   │   ├── stat-arb-overview-and-history.md
│   │   │   ├── pairs-trading-and-cointegration.md
│   │   │   ├── factor-residual-mean-reversion.md
│   │   │   ├── short-term-cross-sectional-reversal.md
│   │   │   ├── intraday-patterns-and-seasonality.md
│   │   │   └── ml-driven-short-horizon-alpha.md
│   │   ├── d-mid-frequency-alpha/
│   │   │   ├── cross-sectional-alpha-and-neutralization.md
│   │   │   ├── fundamental-quant-signals.md
│   │   │   ├── earnings-and-event-driven.md
│   │   │   ├── analyst-revisions-and-sentiment.md
│   │   │   ├── flow-driven-strategies.md
│   │   │   ├── alternative-data.md
│   │   │   └── nlp-and-llm-signals.md
│   │   ├── e-risk-premia-and-factors/
│   │   │   ├── factor-investing-fundamentals.md
│   │   │   ├── momentum.md
│   │   │   ├── value-quality-low-vol.md
│   │   │   └── factor-timing-crowding-and-quant-winters.md
│   │   ├── f-volatility-and-derivatives/
│   │   │   ├── volatility-risk-premium-and-vol-arb.md
│   │   │   └── dispersion-and-correlation-trading.md
│   │   ├── g-futures-and-macro-context/
│   │   │   ├── trend-following-and-ctas.md
│   │   │   └── carry-and-cross-asset-risk-premia.md
│   │   └── h-cross-cutting/
│   │       ├── strategy-comparison-matrix.md
│   │       ├── strategy-x-algorithm-matrix.md
│   │       ├── strategy-failure-gallery.md
│   │       ├── evolution-of-quant-strategies.md
│   │       └── how-firms-combine-strategies.md
│   ├── 03-algorithms/                    # ★ TOP PRIORITY
│   │   ├── index.md
│   │   ├── there-is-no-single-algorithm.md
│   │   ├── algorithm-map.md
│   │   ├── a-data-and-signals/
│   │   │   ├── point-in-time-data-and-cleaning.md
│   │   │   ├── feature-engineering.md
│   │   │   ├── signal-transforms.md
│   │   │   └── evaluating-signals.md
│   │   ├── b-forecasting-models/
│   │   │   ├── linear-models-and-regularization.md
│   │   │   ├── tree-ensembles.md
│   │   │   ├── neural-nets-and-sequence-models.md
│   │   │   ├── llms-and-foundation-models-in-quant.md
│   │   │   ├── alpha-combination-and-ensembling.md
│   │   │   └── regime-detection.md
│   │   ├── c-validation-and-backtesting/
│   │   │   ├── time-series-cross-validation.md
│   │   │   ├── backtesting-engines.md
│   │   │   ├── backtest-pitfalls.md
│   │   │   └── overfitting-and-multiple-testing.md
│   │   ├── d-portfolio-construction/
│   │   │   ├── risk-models.md
│   │   │   ├── covariance-estimation-and-shrinkage.md
│   │   │   ├── mean-variance-optimization.md
│   │   │   ├── alternatives-to-mvo.md
│   │   │   ├── transaction-cost-and-impact-models.md
│   │   │   ├── multi-period-and-trading-toward-aim.md
│   │   │   └── position-sizing-and-risk-budgeting.md
│   │   ├── e-execution-algorithms/
│   │   │   ├── execution-algorithms-overview.md
│   │   │   ├── vwap-twap-pov.md
│   │   │   ├── implementation-shortfall-and-almgren-chriss.md
│   │   │   ├── smart-order-routing.md
│   │   │   ├── auction-close-and-dark-liquidity-algos.md
│   │   │   └── transaction-cost-analysis.md
│   │   ├── f-market-making-and-hft-algorithms/
│   │   │   ├── anatomy-of-an-hft-trading-loop.md
│   │   │   ├── fair-value-and-microprice.md
│   │   │   ├── order-book-and-trade-flow-signals.md
│   │   │   ├── quoting-and-inventory-control.md
│   │   │   ├── adverse-selection-and-markouts.md
│   │   │   ├── queue-position-and-order-placement.md
│   │   │   ├── hedging-algorithms.md
│   │   │   ├── options-pricing-and-vol-surfaces-for-mm.md
│   │   │   └── algorithmic-risk-controls.md
│   │   ├── g-live-trading/
│   │   │   ├── live-monitoring-and-pnl-attribution.md
│   │   │   ├── alpha-decay-detection-and-model-retirement.md
│   │   │   └── reinforcement-learning-in-trading.md
│   │   └── h-end-to-end-walkthroughs/
│   │       ├── walkthrough-mid-frequency-stat-arb.md
│   │       ├── walkthrough-etf-market-maker.md
│   │       ├── walkthrough-options-market-maker.md
│   │       └── walkthrough-institutional-execution.md
│   ├── 04-industry-and-firms/
│   │   ├── taxonomy-of-quant-firms.md
│   │   ├── economics-and-revenue-pools.md
│   │   ├── roles-teams-and-careers.md
│   │   ├── competitive-dynamics-and-ma.md
│   │   └── firm-profiles/
│   ├── 05-infrastructure/
│   │   ├── how-infrastructure-constrains-algorithms.md
│   │   ├── colocation-networks-and-the-speed-of-light.md
│   │   ├── trading-and-research-tech-stacks.md
│   │   └── semiconductor-lens.md
│   ├── 06-risk-and-regulation/
│   │   ├── risk-management-at-quant-firms.md
│   │   └── rules-that-shape-strategies.md
│   ├── 07-conversation-playbook/
│   │   ├── how-to-talk-to-a-quant.md
│   │   ├── elevator-explanations.md
│   │   ├── questions-to-ask.md
│   │   ├── mock-conversations.md
│   │   └── faux-pas-and-naive-questions.md
│   ├── 08-calibration/
│   │   ├── myths-vs-reality.md
│   │   ├── contested-debates.md
│   │   └── sanity-checking-claims.md
│   ├── 09-reference/
│   │   ├── glossary.md
│   │   ├── acronyms.md
│   │   ├── books.md
│   │   ├── papers.md
│   │   ├── talks-podcasts-blogs.md
│   │   └── datasets-and-tools.md
│   └── 10-self-test/
│       ├── quiz-<module>.md
│       └── flashcards.csv            # front,back,tags
├── labs/                             # see §5.6
├── references/sources.md
└── scripts/{wordcount.py,check_template.py,check_glossary_links.py,check_matrix.py}
```

---

## 5. Content specification

### 5.1 Strategy dossier template (every page in `02-strategies/a–g`)

Length: **900–1,500 words** each (longer for market making, stat arb, cross-sectional alpha, momentum).

```markdown
# <Strategy>

> **TL;DR**: 3–5 bullets you could repeat in conversation.

**Level:** Core | Deep dive · **Read time:** ~N min · **Last verified:** YYYY-MM

| Field | Value |
|---|---|
| Family | liquidity provision / speed & structural / stat arb / mid-freq alpha / risk premia / vol / futures |
| Edge source | risk premium · behavioral · structural/regulatory · informational · liquidity provision · speed |
| Holding period | |
| Counterparty: who pays and why they accept it | |
| Universe & instruments | |
| Data required | |
| Core algorithms used | links to 03-algorithms cards |
| Infra intensity | latency sensitivity, compute |
| Capacity (rough $ range) | with confidence tag |
| Typical Sharpe (gross vs net) | range, confidence tag |
| Turnover | |
| Main risks / failure modes | |
| Crowding risk | |
| Firm types that run it | (specific firms only if sourced) |
| Lab | link |

## Intuition (the story in plain English)
## Economic rationale: why should this make money at all?
## The trade, step by step
## Worked example with numbers (P&L math shown; label illustrative numbers)
## Signals and algorithms under the hood (link each algorithm card; 10–25 lines of pseudocode for the core logic)
## Implementation choices that matter (universe, rebalance frequency, neutralization, sizing, execution, financing/borrow)
## P&L decomposition (where the money comes from and leaks out)
## Evidence (academic results, post-publication decay, practitioner reports; confidence-tagged)
## Capacity, crowding and decay
## How it fails (mechanisms + historical episodes)
## Textbook vs how it's done today
## Variants and neighbours
## Diagram (≥1 Mermaid)
## How practitioners talk about it (6–10 sentences with glosses)
## Myths vs reality
## Questions you could ask a quant about this (basic → sharp; flag proprietary territory)
## Go deeper (<details>: math, derivations)
## Related pages · Sources
```

**Overview and cross-cutting strategy pages:**
- `index.md`: master strategy map (Mermaid): horizon (µs → months) × edge source, with every dossier placed on it.
- `how-quants-evaluate-a-strategy.md`: the edge-source taxonomy, plus the evaluation checklist: economic rationale, counterparty, Sharpe/IR, capacity, turnover and cost sensitivity, correlation to the existing book, tail risk, decay, crowding, data/infra cost. Also how a PM decides whether to fund a strategy.
- `strategy-comparison-matrix.md`: one table across all dossiers.
- `strategy-x-algorithm-matrix.md`: rows = strategies, columns = algorithm cards, cells = core / supporting / n/a. Must be consistent with dossier headers; `check_matrix.py` verifies this.
- `strategy-failure-gallery.md`: 8–10 mini case studies (~500 words each), each covering the strategy involved, the loss mechanism and what changed afterwards. At minimum: the 2007 quant quake, the 2010 Flash Crash, Knight Capital in 2012, the 2016–2020 value "quant winter", the Feb 2018 short-vol unwind, the March 2020 quant drawdowns, the 2021 meme-stock squeezes, and one recent episode verified at build time.
- `evolution-of-quant-strategies.md`: how strategies are born, crowded, arbitraged away and migrate.
- `how-firms-combine-strategies.md`: multi-strategy books, capital allocation, correlation management, internal netting.

### 5.2 Algorithm card template (every page in `03-algorithms/a–g`)

Length: **700–1,200 words** each (longer for MVO, risk models, quoting & inventory, alpha combination, cross-validation).

```markdown
# <Algorithm / method>

> **TL;DR**: 3–5 bullets.

**Level:** Core | Deep dive · **Pipeline stage:** data | signal | forecast | validation | portfolio | execution | market making | live · **Last verified:** YYYY-MM

| Field | Value |
|---|---|
| Purpose (the question it answers) | |
| Inputs → Outputs | |
| Used by strategies | links to dossiers |
| Latency / compute regime | ns · µs · ms · overnight batch |
| Key parameters | and typical ranges |
| Main failure modes | |
| Lab | link |

## Intuition
## Where it sits in the pipeline (Mermaid diagram)
## The algorithm
   - Plain-English steps
   - **Pseudocode**: readable Python, ≤ 40 lines, commented, consistent with the lab implementation
## Worked example with numbers
## Key parameters and how practitioners tune them
## Textbook version vs what firms actually do (sourced or tagged)
## How to tell if it's working (metrics, diagnostics, plots)
## Failure modes and pitfalls
## How practitioners talk about it (sentences with glosses)
## Questions you could ask a quant about this
## Go deeper (<details>: formulas, derivations, complexity)
## Related pages · Sources
```

**Pipeline overview pages:**
- `there-is-no-single-algorithm.md`: answer "what is their algorithm?" directly. Firms run a **pipeline** of many algorithms. Give annotated pseudocode and a diagram for **five canonical pipelines**:
  1. HFT / electronic market maker loop: market data → book build → fair value → quote & skew → pre-trade risk → order → fill → hedge → inventory update.
  2. Short-horizon stat arb (minutes–days): features → ML forecast → combination → optimizer with cost model → execution.
  3. Mid-frequency cross-sectional equity (days–weeks): data → alphas → transforms → combination → risk model → optimizer → trade list → execution algos → attribution.
  4. Systematic factor manager (monthly): factor scores → constrained portfolio construction → rebalance.
  5. Agency execution: parent order → schedule (IS/VWAP/POV) → child orders → smart order routing → TCA.
- `algorithm-map.md`: every algorithm card placed on one master pipeline diagram.

**End-to-end walkthroughs** (1,800–2,500 words each; the capstone of the KB; narrative and numeric, reusing lab outputs):
- **Mid-frequency stat arb:** a toy US equity book from scratch: universe → three alphas → transforms → IC-weighted combination → risk model → optimizer with costs → trade list → VWAP/IS execution → next-day P&L attribution.
- **ETF market maker:** one trading day: fair value from basket and futures, quoting, inventory, creation/redemption, hedging, markouts, end-of-day P&L decomposition.
- **Options market maker:** vol surface fit → theoretical values → quoting → delta/vega hedging → Greeks P&L attribution (theta vs gamma vs vega vs edge).
- **Institutional execution:** a $500M pension-fund buy order: schedule choice, child orders, venues, dark vs lit, the close, TCA report, and the counterparties along the way.

### 5.3 Module 01: market structure essentials (lean prerequisite)
Write only what strategies and algorithms need. End every page with **"Why this matters for strategies & algorithms"**, linking forward. Cover:
- the life of an order;
- the limit order book and price-time priority (queue value);
- order types and auctions, including closing-auction share;
- venues, wholesalers and PFOF (flow toxicity);
- SIP vs direct feeds;
- maker-taker vs inverted venues, ticks and odd lots;
- ETF/futures/options linkages;
- borrow costs, Reg SHO and T+1 as inputs to strategy P&L.

`recent-changes.md`: verify the status of items as of the build date and keep only those that affect strategies. Examples: the SEC's 2024 tick-size, access-fee and round-lot amendments; extended/overnight trading initiatives; 0DTE options growth. **Do not state any of these from memory.**

### 5.4 Module 04: industry & firms (support)
- **Taxonomy:** market makers/PTFs, HFT prop, quant hedge funds, multi-manager quant pods, systematic asset managers, CTAs, agency execution, the ecosystem. For each: capital source, incentives, horizon, edge, and **which strategy families from module 02 they run** (linked).
- **Economics:** revenue pools, prop vs fund economics, capacity limits. Use public filings (e.g., Virtu 10-K, Flow Traders annual report) and tag press figures `[Reported]`.
- **Roles & teams:** QR vs QT vs QD vs SWE; how strategy and signal teams are organized at a market maker vs a pod shop vs a centralized quant fund.
- **Competitive dynamics & M&A** (corp-dev lens): moats, consolidation, notable deals (verify each one).
- **~18 short firm profiles** (300–500 words each) emphasizing **known strategy focus and approach**: Citadel Securities, Virtu, Jane Street, Hudson River Trading, Jump, Tower, Optiver, IMC, SIG, XTX Markets, Renaissance, D.E. Shaw, Two Sigma, Millennium (quant pods), Cubist, AQR, Man Group (AHL/Numeric), High-Flyer. Each gets a snapshot table (type, scale, horizon, known strategies, tech signals, confidence, sources) plus a "fact vs lore" section. Verify each firm is current; replace it and log the change if not.

### 5.5 Modules 05–10 (support)
- **05 Infrastructure (4 pages)**, written as "how infrastructure constrains algorithms":
  - latency budgets by strategy, and what runs on FPGA vs CPU vs GPU and why;
  - colocation and microwave networks, with a speed-of-light table;
  - production vs research tech stacks (C++, kernel bypass, OCaml at Jane Street, kdb+/Python research, GPU clusters; verified);
  - a short semiconductor-lens page for a chip-industry reader.
- **06 Risk & regulation (2 pages):**
  - firm risk practice: limits, factor exposure caps, pod drawdown rules, kill switches;
  - rules that shape strategy design, each with "which strategies this affects": Reg NMS, Reg SHO, 15c3-5, spoofing/layering/marking-the-close enforcement, MiFID II algo rules, SEBI F&O rules.
- **07 Conversation playbook (high value):**
  - `elevator-explanations.md`: 70+ concepts, each in a 30-second and a 2-minute spoken version; ≥ 50 are strategies or algorithms.
  - `questions-to-ask.md`: organized **by strategy family and by pipeline stage first**, then by role. Mark each question basic / informed / sharp, and flag proprietary territory.
  - `mock-conversations.md`: 6 annotated dialogues (800–1,200 words each) with an ETF market maker, a stat-arb PM at a pod shop, an ML researcher on a short-horizon team, a factor PM during a drawdown, an execution quant at a bank, and a low-latency engineer. Margin notes explain the jargon and why each question landed.
  - `how-to-talk-to-a-quant.md`: ask about *approach*, not *alpha*.
  - `faux-pas-and-naive-questions.md`: with better alternatives.
- **08 Calibration:**
  - 25+ myths, ≥ 15 of them about strategies or algorithms (e.g., "high backtest Sharpe means it works", "ML/LLMs make prediction easy", "HFT = front-running", "quants have one secret formula", "more features always help");
  - contested debates, giving each side's strongest evidence;
  - a sanity-check checklist for claims and backtests.
- **09 Reference:**
  - glossary of 400+ terms (≥ 60% on strategies/algorithms), each linked to its explaining page;
  - 150+ acronyms;
  - annotated resources (list below);
  - datasets and tools, with honest caveats.
- **10 Self-test:** 10–15 questions per support module and 25–30 per priority module; `flashcards.csv` with ≥ 300 cards, ≥ 60% tagged strategies/algorithms.

**Must-include resources** (verify editions; annotate each with who it's for, which chapters, and difficulty):
- *Strategies & portfolio:* Narang *Inside the Black Box*; Grinold & Kahn *Active Portfolio Management*; Isichenko *Quantitative Portfolio Management*; Pedersen *Efficiently Inefficient*; Ilmanen *Expected Returns*; Chan *Quantitative Trading* / *Algorithmic Trading*; Tulchinsky et al. *Finding Alphas*; López de Prado *Advances in Financial Machine Learning*.
- *Microstructure, MM & execution:* Harris *Trading and Exchanges*; Cartea, Jaimungal & Penalva *Algorithmic and High-Frequency Trading*; Bouchaud et al. *Trades, Quotes and Prices*; Lehalle & Laruelle *Market Microstructure in Practice*; Johnson *Algorithmic Trading and DMA*; Kissell *The Science of Algorithmic Trading and Portfolio Management*.
- *Options/vol:* Natenberg *Option Volatility and Pricing*; Gatheral *The Volatility Surface*; Sinclair *Volatility Trading*.
- *Context:* MacKenzie *Trading at the Speed of Light*; Zuckerman *The Man Who Solved the Market*; Patterson *The Quants*.
- *Papers, organized by family:*
  - **Market making & microstructure:** Kyle (1985); Glosten & Milgrom (1985); Avellaneda & Stoikov (2008); Guéant, Lehalle & Fernandez-Tapia (2013); Cont, Kukanov & Stoikov (2014); Stoikov (microprice, 2018); Easley, López de Prado & O'Hara (VPIN, 2012); Menkveld (2013); Budish, Cramton & Shim (2015); Aquilina, Budish & O'Neill (2022).
  - **Stat arb:** Gatev, Goetzmann & Rouwenhorst (2006); Avellaneda & Lee (2010); Khandani & Lo (2007/2011); Lehmann (1990); Jegadeesh (1990); Lo & MacKinlay (1990).
  - **Factors & anomalies:** Jegadeesh & Titman (1993); Fama & French (1993, 2015); Asness, Moskowitz & Pedersen (2013); Daniel & Moskowitz (2016); Moskowitz, Ooi & Pedersen (2012); Frazzini & Pedersen (2014); Novy-Marx (2013); Bernard & Thomas (1989); McLean & Pontiff (2016); Harvey, Liu & Zhu (2016); Kakushadze (2016).
  - **ML & validation:** Gu, Kelly & Xiu (2020); Bailey & López de Prado (2014); Bailey, Borwein, López de Prado & Zhu (PBO).
  - **Portfolio & costs:** Grinold (1989); Ledoit & Wolf (2004); López de Prado (HRP, 2016); Gârleanu & Pedersen (2013); Almgren & Chriss (2000); Frazzini, Israel & Moskowitz (trading costs); Tóth et al. (square-root impact).
  - **Volatility:** Carr & Wu (variance risk premia).
  - **Official reports:** CFTC-SEC Flash Crash report; SEC Knight Capital order; SEC staff report on early-2021 market events.
- *Talks/podcasts/blogs:* Jane Street *Signals and Threads*; CppCon low-latency trading talks; firm research/engineering blogs; *Flirting with Models*; Quantocracy; Alpha Architect; the Chen & Zimmermann open-source asset-pricing replication project.

### 5.6 Labs (20, nearly all serving modules 02–03)

Python 3.11 with `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `cvxpy`, `matplotlib`; optional `lightgbm`, `numba`.

**Build the synthetic data engine first** (`labs/common/simulate.py`). It is a configurable market with:
- (a) a factor-structured cross-section of ~500 stocks with realistic volatility, beta and sector structure;
- (b) **planted alphas of known strength and decay**, so labs can show whether methods recover the truth and how often noise fools them;
- (c) a simple limit-order-book/trade-flow generator for microstructure labs;
- (d) synthetic option prices from a stochastic-vol model.

Real data is only a clearly optional extra, with survivorship and look-ahead warnings.

Each lab contains:
- a `README.md`: what it demonstrates, which dossier/card it supports, how to run it, expected output, and **"what this toy misses vs the real world"**;
- a runnable `.py` script;
- a smoke-test parameter set (CI < 60 s per lab);
- 1–2 committed output plots, embedded in the linked KB page.

| # | Lab | Supports |
|---|---|---|
| 01 | Matching engine & order book (price-time priority, queues) | order book, queue position |
| 02 | Microprice & imbalance-based fair value | fair value card |
| 03 | Order-flow imbalance → short-horizon returns | OB signals card |
| 04 | Markout analysis: measuring adverse selection | markouts card, equity MM |
| 05 | Avellaneda–Stoikov & GLFT vs naive quoting, with P&L decomposition | quoting card, equity MM |
| 06 | Options MM toy: delta hedging, gamma/theta P&L, implied vs realized vol | options MM, vol surface card |
| 07 | ETF NAV arbitrage & creation/redemption | ETF MM, ETF arb |
| 08 | Pairs trading with cointegration (and regime breaks) | pairs dossier |
| 09 | PCA / factor-residual stat arb | factor-residual dossier |
| 10 | Cross-sectional reversal & momentum with realistic costs | reversal, momentum dossiers |
| 11 | Signal transforms + IC, rank IC, IC decay, quantile spreads | signal cards |
| 12 | Alpha combination (equal, IC-weighted, ridge, GBDT) under purged CV | combination, CV cards |
| 13 | Backtest overfitting: deflated Sharpe & PBO on many random strategies | overfitting card |
| 14 | Risk model (statistical + shrinkage) & constrained MVO with cvxpy | risk model, MVO cards |
| 15 | Trading toward the aim vs full rebalancing under costs | multi-period card |
| 16 | Almgren–Chriss efficient frontier | IS card |
| 17 | VWAP / TWAP / POV simulation and implementation shortfall | execution cards |
| 18 | Smart order router toy: fees, rebates, fill probability, toxicity | SOR card |
| 19 | Trend following with volatility targeting on synthetic futures | trend dossier, sizing card |
| 20 | Index-reconstitution event study (synthetic) | flow-driven dossier |

`make labs` runs everything in < 15 minutes on a laptop; `make labs-smoke` is what CI runs.

---

## 6. Writing standards
- Practitioner voice: plain English, precise, concrete numbers, no hype. US English.
- Order of explanation: intuition → mechanics → numbers → pseudocode → math (math collapsible, `$…$` / `$$…$$`).
- **Pseudocode is mandatory** in every algorithm card and in every dossier's "under the hood" section, and must match the lab code.
- Define terms on first use and link them to the glossary. Each page links to 3+ related pages; no orphan pages.
- Mermaid diagrams: ≥ 1 per page in modules 01–03; **140+ overall, with ≥ 100 in modules 02–03.**
- Use tables for comparisons; date-stamp anything time-sensitive.
- "Textbook vs practice" sections must say how each claim is known (practitioner source, firm talk or blog, paper, or `[Lore]`). Never present invented "insider" detail as fact.
- On contested topics, give each side's strongest evidence; give no verdict where the evidence is mixed.

---

## 7. Research protocol and integrity rules (non-negotiable)
1. Research every module with web search and fetch. Do not write time-sensitive facts, figures, firm details or regulatory status from memory.
2. **Source hierarchy:** primary sources (regulators' rules and orders, exchange specs and fee schedules, filings, papers, firm blogs and talks) → reputable financial press → practitioner books → anything else (flagged). Avoid SEO and retail "algo trading" content farms.
3. **Confidence tags** on every number and firm-specific claim:
   - `[Verified]`: primary source;
   - `[Reported]`: credible secondary source;
   - `[Estimate]`: derived (show the reasoning);
   - `[Lore]`: widely repeated, unverified.

   Cross-check key numbers against 2+ sources, and show ranges when they conflict.
4. **Sharpe, capacity and return figures** must state: gross or net, period, source type (academic backtest / fund disclosure / practitioner estimate), and known post-publication decay.
5. **Never invent** firm-specific strategies, revenue figures, people, quotes, or paper titles. If you can't verify something, write `TODO(verify): …` and log it in PLAN.md.
6. **Copyright:** paraphrase. Keep quotes rare and under ~15 words. Never reproduce book passages or paywalled text; link instead.
7. `references/sources.md`: a deduplicated master bibliography (150+), grouped by strategy family / algorithm area / other, each entry with URL, date, accessed date and confidence tag.

---

## 8. Execution plan (phases)

After each phase: update PLAN.md (checklist, words vs budget, TODOs), run `make check`, commit (`module-XX: <what>`), and `git push` to the existing remote.

- **Phase 0: Setup.** Confirm the repo (`git remote -v`, `git pull`). Save this prompt as `BUILD_SPEC.md`. Create the directory tree and stubs, README, LICENSE (if none exists), CLAUDE.md, PLAN.md (listing every page and lab as a checkbox), mkdocs.yml, requirements.txt, Makefile, scripts and CI workflows. Commit and push. If the push fails on authentication, stop and tell me the exact fix (e.g., `gh auth login`).
- **Phase 1: Spine.**
  - Pages: `the-big-picture.md`, `02-strategies/index.md`, `how-quants-evaluate-a-strategy.md`, `there-is-no-single-algorithm.md`, `algorithm-map.md`.
  - Seed the glossary with 150 terms.
  - Build `labs/common/simulate.py`.
- **Phase 2: Market structure essentials (01).** Keep it lean; forward-link everything to 02–03.
- **Phase 3: Strategies (02).** Work family by family (a → g). **Interleave labs:** when a dossier has a lab, build the lab right after the page, embed its plot, and make the pseudocode match.
- **Phase 4: Algorithms (03).** Sections a → g, with labs interleaved the same way.
- **Phase 5: Walkthroughs + cross-cutting.** The four walkthroughs, the comparison matrix, the strategy × algorithm matrix (`check_matrix.py` passes), the failure gallery, the evolution page, and the how-firms-combine page.
- **Phase 6: PRIORITY GATE (do not skip).** Before any lower-priority module:
  - re-read modules 02–03 as the target reader and fix anything confusing, thin, redundant or unsourced;
  - `check_template.py` passes for every dossier and card, and word counts meet the budget;
  - fact-check the **40 highest-stakes claims** in 02–03 and log the results in PLAN.md;
  - all labs run, and their plots are embedded;
  - commit, push, and tag `v0.9-strategies-algorithms`.
- **Phase 7: Industry & firms (04), infrastructure (05), risk & regulation (06).** Lean.
- **Phase 8: Conversation playbook (07) + calibration (08).**
- **Phase 9: Reference (09) + self-test (10).**
- **Phase 10: Final QA (§10).** Tag `v1.0`, enable GitHub Pages, and add the site URL to README.

**Context management:** write pages to disk as you go; never hold large drafts in context. Re-read CLAUDE.md and PLAN.md at the start of each phase. If context is getting tight: commit, push, write exact next steps into PLAN.md, and tell me to start a new session with this resume prompt:
> *"Continue building the knowledge base in this repo. Read BUILD_SPEC.md, CLAUDE.md and PLAN.md fully, run `git log --oneline -20` and `make wordcount`, then resume at the first unchecked item in PLAN.md. Modules 02 and 03 (with their labs and walkthroughs) take priority until the Phase 6 gate passes."*

If you must trim scope, follow the cut order in §3.

---

## 9. CLAUDE.md contents (create in Phase 0)
Include:
- purpose and an anonymized reader profile;
- the **priority statement (modules 02–03 first, never cut)** and the word budget table;
- the dossier, algorithm card and firm profile templates;
- pseudocode and lab-consistency rules;
- confidence tags and the source hierarchy;
- writing standards and kebab-case file naming;
- the commit convention and how to run the checks;
- the definition of done.

---

## 10. Definition of done

**Priority modules (02–03): all must pass**
- [ ] ≥ 30 strategy dossiers and ≥ 39 algorithm cards, each passing `check_template.py` and within its length range.
- [ ] Modules 02 + 03 total ≥ 75,000 words (≈ 70% of the KB).
- [ ] Every card and dossier has pseudocode, a worked numeric example, ≥ 1 Mermaid diagram, and a sourced or tagged "textbook vs practice" section.
- [ ] Every strategy states counterparty, edge source, horizon, capacity and Sharpe ranges (gross/net, period, source type, confidence).
- [ ] The four walkthroughs are complete and numerically consistent with the labs.
- [ ] The strategy × algorithm matrix is complete and consistent (`check_matrix.py` passes).
- [ ] All 20 labs run (`make labs` < 15 min), each linked from and embedded in its pages.
- [ ] The priority-gate fact-check of 40 claims is logged in PLAN.md.

**Whole KB**
- [ ] Total ≥ 110,000 words. The Core Path is ≤ ~25k words, with ≥ 60% of it drawn from modules 02–03.
- [ ] ≥ 140 Mermaid diagrams; `mkdocs build --strict` passes.
- [ ] Glossary ≥ 400 terms (`check_glossary_links.py` passes); acronyms ≥ 150.
- [ ] Elevator explanations ≥ 70; questions-to-ask organized by strategy and pipeline stage; 6 mock conversations.
- [ ] Myths ≥ 25 (≥ 15 on strategies/algorithms).
- [ ] references/sources.md has ≥ 150 unique sources; every number has a source or confidence tag; no `TODO(verify)` left in Core Path pages.
- [ ] Quizzes for every module (priority modules 2× longer); flashcards.csv has ≥ 300 cards.
- [ ] Lychee link check, markdownlint and CI all pass; GitHub Pages site is live.
- [ ] README has the module map, learning paths ("start with strategies & algorithms"), the site link, and a "How this was built / limitations" section.

When finished, report:
- the repo URL and site URL;
- words per module vs budget, and counts against each target;
- the remaining `TODO(verify)` items;
- the **10 pages to read first**: at least 7 from modules 02–03, including one walkthrough.
