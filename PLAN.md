# PLAN: build tracker

Living tracker for the build described in `BUILD_SPEC.md`, with conventions in `CLAUDE.md`.
**Resume rule:** read BUILD_SPEC.md, CLAUDE.md and this file; run `git log --oneline -20` and
`make wordcount`; resume at the first unchecked item. Modules 02 and 03 (with their labs and
walkthroughs) take priority until the Phase 6 gate passes.

## Phase status

- [x] **Phase 0: Setup**: repo confirmed, BUILD_SPEC.md saved, tree + stubs, CLAUDE.md, PLAN.md, mkdocs.yml, requirements, Makefile, scripts, CI.
- [ ] **Phase 1: Spine**: big picture, strategy map, how-quants-evaluate, there-is-no-single-algorithm, algorithm map; glossary seed (150); `labs/common/simulate.py`.
- [ ] **Phase 2: Market structure essentials (01)**
- [ ] **Phase 3: Strategies (02 a–g)** with interleaved labs
- [ ] **Phase 4: Algorithms (03 a–g)** with interleaved labs
- [ ] **Phase 5: Walkthroughs + cross-cutting**
- [ ] **Phase 6: PRIORITY GATE**: reader re-read, template checks, 40-claim fact-check, labs embedded, tag `v0.9-strategies-algorithms`
- [ ] **Phase 7: Industry & firms (04), infrastructure (05), risk & regulation (06)**
- [ ] **Phase 8: Conversation playbook (07) + calibration (08)**
- [ ] **Phase 9: Reference (09) + self-test (10)**
- [ ] **Phase 10: Final QA**: tag `v1.0`, GitHub Pages, README site URL

## Build approach (decisions log)

- 2026-11-12: The build is orchestrated by one session that delegates page-writing and lab-building to
  helper agents with disjoint file assignments; only the orchestrator commits and pushes.
- 2026-11-12: **Labs are built before the pages that cite them** (rather than strictly page-then-lab)
  so that parallel writers can read the finished `lab.py`, quote `results.json` numbers and embed the
  committed plots. This preserves the spec's intent (pseudocode matches the lab; plots embedded).
- 2026-11-12: Word counts exclude code blocks, Mermaid, URLs and `## Sources` sections (see
  `scripts/kb.py:prose_words`), so the totals measure what a reader actually reads.
- 2026-11-12: MkDocs anchor validation is set to `info` during the build because glossary anchors are
  verified by `scripts/check_glossary_links.py`; flip to `warn` in Phase 10.
- 2026-11-12: Lab links in pages use absolute GitHub URLs (labs live outside `docs/`); lab plots are
  committed under `docs/assets/labs/` so the site can embed them.

## Word count vs budget

_Updated after each phase from `make wordcount`._

| Module | Budget | Words | Status |
|---|---|---|---|
| 00 Start here | 2,500 | 0 | stub |
| 01 Market structure | 8,000 | 0 | stub |
| 02 Strategies | 35,000 | 0 | stub |
| 03 Algorithms | 42,000 | 0 | stub |
| 04 Industry & firms | 5,000 | 0 | stub |
| 05 Infrastructure | 3,500 | 0 | stub |
| 06 Risk & regulation | 2,500 | 0 | stub |
| 07 Conversation playbook | 5,000 | 0 | stub |
| 08 Calibration | 2,500 | 0 | stub |
| 09 Reference | 5,500 | 0 | stub |
| **Total** | **110,000** | **0** | |

## Labs

- [ ] `labs/common/` (utils.py ✓, simulate.py, orderbook.py, options.py)
- [ ] 01 matching engine & order book
- [ ] 02 microprice & imbalance fair value
- [ ] 03 order-flow imbalance → short-horizon returns
- [ ] 04 markout analysis
- [ ] 05 Avellaneda–Stoikov & GLFT vs naive quoting
- [ ] 06 options MM toy (delta hedging, gamma/theta, implied vs realized)
- [ ] 07 ETF NAV arbitrage & creation/redemption
- [ ] 08 pairs trading with cointegration
- [ ] 09 PCA / factor-residual stat arb
- [ ] 10 reversal & momentum with costs
- [ ] 11 signal transforms + IC
- [ ] 12 alpha combination under purged CV
- [ ] 13 backtest overfitting: DSR & PBO
- [ ] 14 risk model & constrained MVO
- [ ] 15 trading toward the aim
- [ ] 16 Almgren–Chriss frontier
- [ ] 17 VWAP / TWAP / POV simulation
- [ ] 18 smart order router toy
- [ ] 19 trend following with vol targeting
- [ ] 20 index-reconstitution event study

## Priority-gate fact-check (40 claims)

_To be filled in Phase 6: claim · page · source(s) · result (confirmed / corrected / downgraded tag)._

## Open TODO(verify) items

_Collected from pages by `grep -rn "TODO(verify)" docs/`; updated after each phase._

## Page checklist

### (root pages)

- [ ] `index.md` — Home (P1)
- [ ] `labs.md` — Labs (P3)

### 00-start-here

- [ ] `00-start-here/the-big-picture.md` — The big picture (P1)
- [ ] `00-start-here/learning-paths.md` — Learning paths (P5)
- [ ] `00-start-here/one-page-cheat-sheet.md` — One-page cheat sheet (P5)

### 01-market-structure

- [ ] `01-market-structure/life-of-a-stock-order.md` — Life of a stock order (P2)
- [ ] `01-market-structure/the-limit-order-book.md` — The limit order book (P2)
- [ ] `01-market-structure/order-types-and-auctions.md` — Order types and auctions (P2)
- [ ] `01-market-structure/venues-and-retail-flow.md` — Venues and retail flow (P2)
- [ ] `01-market-structure/nbbo-and-market-data.md` — NBBO and market data (P2)
- [ ] `01-market-structure/fees-rebates-and-ticks.md` — Fees, rebates and ticks (P2)
- [ ] `01-market-structure/etf-futures-options-linkages.md` — ETF, futures and options linkages (P2)
- [ ] `01-market-structure/shorting-financing-and-settlement.md` — Shorting, financing and settlement (P2)
- [ ] `01-market-structure/recent-changes.md` — Recent changes (as of 2026-11) (P2)

### 02-strategies

- [ ] `02-strategies/index.md` — Strategies: the map (P1)
- [ ] `02-strategies/how-quants-evaluate-a-strategy.md` — How quants evaluate a strategy (P1)
- [ ] `02-strategies/a-liquidity-provision/equity-market-making.md` — Equity market making (P3)
- [ ] `02-strategies/a-liquidity-provision/etf-market-making.md` — ETF market making (P3)
- [ ] `02-strategies/a-liquidity-provision/options-market-making.md` — Options market making (P3)
- [ ] `02-strategies/a-liquidity-provision/retail-flow-internalization.md` — Retail flow internalization (P3)
- [ ] `02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md` — Auctions and closing liquidity (P3)
- [ ] `02-strategies/b-speed-and-structural/latency-arbitrage.md` — Latency arbitrage (P3)
- [ ] `02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md` — Lead-lag and cross-asset arbitrage (P3)
- [ ] `02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md` — ETF and index arbitrage (P3)
- [ ] `02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md` — Fee- and microstructure-driven strategies (P3)
- [ ] `02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md` — Stat arb: overview and history (P3)
- [ ] `02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md` — Pairs trading and cointegration (P3)
- [ ] `02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md` — Factor-residual mean reversion (P3)
- [ ] `02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md` — Short-term cross-sectional reversal (P3)
- [ ] `02-strategies/c-statistical-arbitrage/intraday-patterns-and-seasonality.md` — Intraday patterns and seasonality (P3)
- [ ] `02-strategies/c-statistical-arbitrage/ml-driven-short-horizon-alpha.md` — ML-driven short-horizon alpha (P3)
- [ ] `02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md` — Cross-sectional alpha and neutralization (P3)
- [ ] `02-strategies/d-mid-frequency-alpha/fundamental-quant-signals.md` — Fundamental quant signals (P3)
- [ ] `02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md` — Earnings and event-driven (P3)
- [ ] `02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md` — Analyst revisions and sentiment (P3)
- [ ] `02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md` — Flow-driven strategies (P3)
- [ ] `02-strategies/d-mid-frequency-alpha/alternative-data.md` — Alternative data (P3)
- [ ] `02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md` — NLP and LLM signals (P3)
- [ ] `02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md` — Factor investing fundamentals (P3)
- [ ] `02-strategies/e-risk-premia-and-factors/momentum.md` — Momentum (P3)
- [ ] `02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md` — Value, quality and low volatility (P3)
- [ ] `02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md` — Factor timing, crowding and quant winters (P3)
- [ ] `02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md` — Volatility risk premium and vol arb (P3)
- [ ] `02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md` — Dispersion and correlation trading (P3)
- [ ] `02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md` — Trend following and CTAs (P3)
- [ ] `02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md` — Carry and cross-asset risk premia (P3)
- [ ] `02-strategies/h-cross-cutting/strategy-comparison-matrix.md` — Strategy comparison matrix (P5)
- [ ] `02-strategies/h-cross-cutting/strategy-x-algorithm-matrix.md` — Strategy x algorithm matrix (P5)
- [ ] `02-strategies/h-cross-cutting/strategy-failure-gallery.md` — Strategy failure gallery (P5)
- [ ] `02-strategies/h-cross-cutting/evolution-of-quant-strategies.md` — Evolution of quant strategies (P5)
- [ ] `02-strategies/h-cross-cutting/how-firms-combine-strategies.md` — How firms combine strategies (P5)

### 03-algorithms

- [ ] `03-algorithms/index.md` — Algorithms: overview (P1)
- [ ] `03-algorithms/there-is-no-single-algorithm.md` — There is no single algorithm (P1)
- [ ] `03-algorithms/algorithm-map.md` — Algorithm map (P1)
- [ ] `03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md` — Point-in-time data and cleaning (P4)
- [ ] `03-algorithms/a-data-and-signals/feature-engineering.md` — Feature engineering (P4)
- [ ] `03-algorithms/a-data-and-signals/signal-transforms.md` — Signal transforms (P4)
- [ ] `03-algorithms/a-data-and-signals/evaluating-signals.md` — Evaluating signals (P4)
- [ ] `03-algorithms/b-forecasting-models/linear-models-and-regularization.md` — Linear models and regularization (P4)
- [ ] `03-algorithms/b-forecasting-models/tree-ensembles.md` — Tree ensembles (P4)
- [ ] `03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md` — Neural nets and sequence models (P4)
- [ ] `03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md` — LLMs and foundation models in quant (P4)
- [ ] `03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md` — Alpha combination and ensembling (P4)
- [ ] `03-algorithms/b-forecasting-models/regime-detection.md` — Regime detection (P4)
- [ ] `03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md` — Time-series cross-validation (P4)
- [ ] `03-algorithms/c-validation-and-backtesting/backtesting-engines.md` — Backtesting engines (P4)
- [ ] `03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md` — Backtest pitfalls (P4)
- [ ] `03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md` — Overfitting and multiple testing (P4)
- [ ] `03-algorithms/d-portfolio-construction/risk-models.md` — Risk models (P4)
- [ ] `03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md` — Covariance estimation and shrinkage (P4)
- [ ] `03-algorithms/d-portfolio-construction/mean-variance-optimization.md` — Mean-variance optimization (P4)
- [ ] `03-algorithms/d-portfolio-construction/alternatives-to-mvo.md` — Alternatives to MVO (P4)
- [ ] `03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md` — Transaction cost and impact models (P4)
- [ ] `03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md` — Multi-period optimization and trading toward the aim (P4)
- [ ] `03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md` — Position sizing and risk budgeting (P4)
- [ ] `03-algorithms/e-execution-algorithms/execution-algorithms-overview.md` — Execution algorithms: overview (P4)
- [ ] `03-algorithms/e-execution-algorithms/vwap-twap-pov.md` — VWAP, TWAP and POV (P4)
- [ ] `03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md` — Implementation shortfall and Almgren-Chriss (P4)
- [ ] `03-algorithms/e-execution-algorithms/smart-order-routing.md` — Smart order routing (P4)
- [ ] `03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md` — Auction, close and dark-liquidity algos (P4)
- [ ] `03-algorithms/e-execution-algorithms/transaction-cost-analysis.md` — Transaction cost analysis (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md` — Anatomy of an HFT trading loop (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md` — Fair value and microprice (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md` — Order-book and trade-flow signals (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md` — Quoting and inventory control (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md` — Adverse selection and markouts (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md` — Queue position and order placement (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md` — Hedging algorithms (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md` — Options pricing and vol surfaces for market making (P4)
- [ ] `03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md` — Algorithmic risk controls (P4)
- [ ] `03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md` — Live monitoring and P&L attribution (P4)
- [ ] `03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md` — Alpha decay detection and model retirement (P4)
- [ ] `03-algorithms/g-live-trading/reinforcement-learning-in-trading.md` — Reinforcement learning in trading (P4)
- [ ] `03-algorithms/h-end-to-end-walkthroughs/walkthrough-mid-frequency-stat-arb.md` — Walkthrough: a mid-frequency stat-arb book (P5)
- [ ] `03-algorithms/h-end-to-end-walkthroughs/walkthrough-etf-market-maker.md` — Walkthrough: a day at an ETF market maker (P5)
- [ ] `03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md` — Walkthrough: an options market maker (P5)
- [ ] `03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md` — Walkthrough: executing a $500M buy order (P5)

### 04-industry-and-firms

- [ ] `04-industry-and-firms/taxonomy-of-quant-firms.md` — Taxonomy of quant firms (P7)
- [ ] `04-industry-and-firms/economics-and-revenue-pools.md` — Economics and revenue pools (P7)
- [ ] `04-industry-and-firms/roles-teams-and-careers.md` — Roles, teams and careers (P7)
- [ ] `04-industry-and-firms/competitive-dynamics-and-ma.md` — Competitive dynamics and M&A (P7)
- [ ] `04-industry-and-firms/firm-profiles/index.md` — Firm profiles (P7)
- [ ] `04-industry-and-firms/firm-profiles/citadel-securities.md` — Citadel Securities (P7)
- [ ] `04-industry-and-firms/firm-profiles/virtu-financial.md` — Virtu Financial (P7)
- [ ] `04-industry-and-firms/firm-profiles/jane-street.md` — Jane Street (P7)
- [ ] `04-industry-and-firms/firm-profiles/hudson-river-trading.md` — Hudson River Trading (P7)
- [ ] `04-industry-and-firms/firm-profiles/jump-trading.md` — Jump Trading (P7)
- [ ] `04-industry-and-firms/firm-profiles/tower-research-capital.md` — Tower Research Capital (P7)
- [ ] `04-industry-and-firms/firm-profiles/optiver.md` — Optiver (P7)
- [ ] `04-industry-and-firms/firm-profiles/imc.md` — IMC Trading (P7)
- [ ] `04-industry-and-firms/firm-profiles/susquehanna-sig.md` — Susquehanna (SIG) (P7)
- [ ] `04-industry-and-firms/firm-profiles/xtx-markets.md` — XTX Markets (P7)
- [ ] `04-industry-and-firms/firm-profiles/renaissance-technologies.md` — Renaissance Technologies (P7)
- [ ] `04-industry-and-firms/firm-profiles/de-shaw.md` — D. E. Shaw (P7)
- [ ] `04-industry-and-firms/firm-profiles/two-sigma.md` — Two Sigma (P7)
- [ ] `04-industry-and-firms/firm-profiles/millennium.md` — Millennium (quant pods) (P7)
- [ ] `04-industry-and-firms/firm-profiles/cubist.md` — Cubist Systematic Strategies (P7)
- [ ] `04-industry-and-firms/firm-profiles/aqr.md` — AQR Capital Management (P7)
- [ ] `04-industry-and-firms/firm-profiles/man-group.md` — Man Group (AHL / Numeric) (P7)
- [ ] `04-industry-and-firms/firm-profiles/high-flyer.md` — High-Flyer (P7)

### 05-infrastructure

- [ ] `05-infrastructure/how-infrastructure-constrains-algorithms.md` — How infrastructure constrains algorithms (P7)
- [ ] `05-infrastructure/colocation-networks-and-the-speed-of-light.md` — Colocation, networks and the speed of light (P7)
- [ ] `05-infrastructure/trading-and-research-tech-stacks.md` — Trading and research tech stacks (P7)
- [ ] `05-infrastructure/semiconductor-lens.md` — A semiconductor lens (P7)

### 06-risk-and-regulation

- [ ] `06-risk-and-regulation/risk-management-at-quant-firms.md` — Risk management at quant firms (P7)
- [ ] `06-risk-and-regulation/rules-that-shape-strategies.md` — Rules that shape strategies (P7)

### 07-conversation-playbook

- [ ] `07-conversation-playbook/how-to-talk-to-a-quant.md` — How to talk to a quant (P8)
- [ ] `07-conversation-playbook/elevator-explanations.md` — Elevator explanations (P8)
- [ ] `07-conversation-playbook/questions-to-ask.md` — Questions to ask (P8)
- [ ] `07-conversation-playbook/mock-conversations.md` — Mock conversations (P8)
- [ ] `07-conversation-playbook/faux-pas-and-naive-questions.md` — Faux pas and naive questions (P8)

### 08-calibration

- [ ] `08-calibration/myths-vs-reality.md` — Myths vs reality (P8)
- [ ] `08-calibration/contested-debates.md` — Contested debates (P8)
- [ ] `08-calibration/sanity-checking-claims.md` — Sanity-checking claims (P8)

### 09-reference

- [ ] `09-reference/glossary.md` — Glossary (P9)
- [ ] `09-reference/acronyms.md` — Acronyms (P9)
- [ ] `09-reference/books.md` — Books (P9)
- [ ] `09-reference/papers.md` — Papers (P9)
- [ ] `09-reference/talks-podcasts-blogs.md` — Talks, podcasts and blogs (P9)
- [ ] `09-reference/datasets-and-tools.md` — Datasets and tools (P9)

### 10-self-test

- [ ] `10-self-test/index.md` — Self-test (P9)
- [ ] `10-self-test/quiz-00-start-here.md` — Quiz: Start here (P9)
- [ ] `10-self-test/quiz-01-market-structure.md` — Quiz: Market structure (P9)
- [ ] `10-self-test/quiz-02-strategies.md` — Quiz: Strategies (P9)
- [ ] `10-self-test/quiz-03-algorithms.md` — Quiz: Algorithms (P9)
- [ ] `10-self-test/quiz-04-industry-and-firms.md` — Quiz: Industry and firms (P9)
- [ ] `10-self-test/quiz-05-infrastructure.md` — Quiz: Infrastructure (P9)
- [ ] `10-self-test/quiz-06-risk-and-regulation.md` — Quiz: Risk and regulation (P9)
- [ ] `10-self-test/quiz-07-conversation-playbook.md` — Quiz: Conversation playbook (P9)
- [ ] `10-self-test/quiz-08-calibration.md` — Quiz: Calibration (P9)
- [ ] `10-self-test/quiz-09-reference.md` — Quiz: Reference (P9)
