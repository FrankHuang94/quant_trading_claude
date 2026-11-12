# PLAN: build tracker

Living tracker for the build described in `BUILD_SPEC.md`, with conventions in `CLAUDE.md`.
**Resume rule:** read BUILD_SPEC.md, CLAUDE.md and this file; run `git log --oneline -20` and
`make wordcount`; resume at the first unchecked item. Modules 02 and 03 (with their labs and
walkthroughs) take priority until the Phase 6 gate passes.

## Phase status

- [x] **Phase 0: Setup**: repo confirmed, BUILD_SPEC.md saved, tree + stubs, CLAUDE.md, PLAN.md, mkdocs.yml, requirements, Makefile, scripts, CI.
- [x] **Phase 1: Spine** (pages ✓, glossary seed 150 ✓, simulate.py ✓ selftest 43/43): big picture, strategy map, how-quants-evaluate, there-is-no-single-algorithm, algorithm map; glossary seed (150); `labs/common/simulate.py`.
- [x] **Phase 2: Market structure essentials (01)**: 9/9 pages, ~10.7k words, 20 Mermaid (2026-11-12)
- [x] **Phase 3: Strategies (02 a–g)**: 30 dossiers, labs built first then pages (see decisions log)
- [x] **Phase 4: Algorithms (03 a–g)**: 39 cards; all 20 labs built, run in 246 s, plots embedded
- [x] **Phase 5: Walkthroughs + cross-cutting**: 4 walkthroughs (with `labs/walkthroughs/` helpers), comparison matrix, strategy × algorithm matrix, failure gallery, evolution, how firms combine
- [x] **Phase 6: PRIORITY GATE**: 7 reviewers re-read all 02–03 pages; check_template 82/82; 49-claim fact-check logged below; all lab plots embedded; Mermaid 170/170 parse; tag `v0.9-strategies-algorithms`
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

| Module | Budget | Words | Pages written | Mermaid |
|---|---|---|---|---|
| 00 Start here | 2,500 | 1,357 | 1/3 | 2 |
| 01 Market structure essentials | 8,000 | 10,858 | 9/9 | 20 |
| 02 Strategies | 35,000 | 65,765 | 37/37 | 68 |
| 03 Algorithms & the trading pipeline | 42,000 | 63,399 | 46/46 | 78 |
| 04 Industry & firms | 5,000 | 0 | 0/23 | 0 |
| 05 Infrastructure | 3,500 | 0 | 0/4 | 0 |
| 06 Risk & regulation | 2,500 | 0 | 0/2 | 0 |
| 07 Conversation playbook | 5,000 | 0 | 0/5 | 0 |
| 08 Calibration & skepticism | 2,500 | 0 | 0/3 | 0 |
| 09 Reference | 5,500 | 10,456 | 1/6 | 0 |
| 10 Self-test | 0 | 0 | 0/11 | 0 |
| **Total** | **110,000** | **154,206** | | **170** |

Modules 02+03: 129,164 words (84% of total; target ≥ 75,000 and ≈ 70%). Mermaid in 02–03: 146 (target ≥ 100). TODO(verify) markers: 0.

## Labs

- [x] `labs/common/` (utils.py, simulate.py, orderbook.py, options.py; `python labs/common/simulate.py --selftest`)
- [x] 01 matching engine & order book
- [x] 02 microprice & imbalance fair value
- [x] 03 order-flow imbalance → short-horizon returns
- [x] 04 markout analysis
- [x] 05 Avellaneda–Stoikov & GLFT vs naive quoting
- [x] 06 options MM toy (delta hedging, gamma/theta, implied vs realized)
- [x] 07 ETF NAV arbitrage & creation/redemption
- [x] 08 pairs trading with cointegration
- [x] 09 PCA / factor-residual stat arb
- [x] 10 reversal & momentum with costs
- [x] 11 signal transforms + IC
- [x] 12 alpha combination under purged CV
- [x] 13 backtest overfitting: DSR & PBO
- [x] 14 risk model & constrained MVO
- [x] 15 trading toward the aim
- [x] 16 Almgren–Chriss frontier
- [x] 17 VWAP / TWAP / POV simulation
- [x] 18 smart order router toy
- [x] 19 trend following with vol targeting
- [x] 20 index-reconstitution event study

## Priority-gate fact-check (40 claims)

Completed 2026-11-12 by seven reviewers (49 claims, 20 corrected, downgraded or reworded; the rest confirmed). Each reviewer also re-read their pages as the target reader and made clarity, consistency and pseudocode-vs-lab fixes. The arithmetic errors they found were fixed in place: ES tick 0.42 bp, not 4.2; the AQR Style Premia fund was −22.0% in 2020; the NYSE MOC/LOC cancel cutoff is 3:50 p.m.).

| # | Reviewer | Claim | Page(s) | Source(s) checked | Result |
|---|---|---|---|---|---|
| 1 | R1 | ABO (2022): races ≈ 20% of FTSE 100 volume, modal race 5–10 µs, ~0.5 bp tax, top-6 firms > 80% of races, −17% cost of liquidity, ~\$5B/yr globally | latency-arbitrage; how-quants | BIS WP 955 abstract (bis.org/publ/work955.htm) | **Corrected** latency TL;DR "about 22%" → "about 20%" (now matches Evidence and 01 page). Other figures confirmed. how-quants \$5B tag upgraded `[Reported]` → `[Verified]` |
| 2 | R1 | Bryzgalova, Pavlova & Sikorskaya (JF 2023): retail > 60% of options volume; avg bid-ask spread 12.6%; ~90% of PFOF from 3 wholesalers | options-market-making | Crossref abstract, doi:10.1111/jofi.13285 (JF 78(6) 3465–3514) | Confirmed; added explicit `[Verified]` to the 60% figure in TL;DR |
| 3 | R1 | Virtu 2014 IPO filing: one losing day in 1,238 trading days | how-quants; equity-market-making | Press coverage of the S-1 (Business Insider, ForexLive, Themis Trading via search) | Confirmed (period 2009–2013, added to how-quants); stays `[Reported]` |
| 4 | R1 | McLean & Pontiff (JF 2016): 97 predictors; returns 26% lower out-of-sample, 58% lower post-publication | how-quants | Crossref abstract, doi:10.1111/jofi.12365 | Confirmed |
| 5 | R1 | Frazzini, Israel & Moskowitz break-even fund sizes for US size/value/momentum "\$52–103B" | how-quants | AQR working-paper page "Trading Costs of Asset Pricing Anomalies" (2012) via search | Confirmed: size \$103B, value \$83B, momentum \$52B (1998–2011 live costs). Text now gives all three; tag `[Reported]` → `[Verified]`; source line repointed to the AQR 2012 paper |
| 6 | R1 | SEC staff early-2021 report: NSCC \$6.9B intraday margin from 36 members on 2021-01-27; GME off-exchange share 62.6% → 32.8% | retail-flow-internalization | SEC staff report PDF (text extracted; dated October 14, 2021) | Figures confirmed (62.60% on Jan 21 → low 32.83% on Jan 28). **Corrected** causal overstatement "as wholesalers routed out" → "consistent with wholesalers internalizing less" (staff say it "may indicate"); How-it-fails line likewise; source date 2021-10-18 → "2021-10-14; released 2021-10-18" (matches facts register) |
| 7 | R1 | Schwarz, Barber, Huang, Jorion & Odean (JF 2025): round-trip costs 0.07%–0.46%; 85,000 simultaneous orders | retail-flow-internalization | Crossref abstract, doi:10.1111/jofi.13467 | Confirmed; wording "across brokers" → "across six brokerage accounts" (six accounts at five brokers) |
| 8 | R2 | Aug 2007: Goldman GEO lost >30% in a week; Highbridge Statistical Opportunities −18% to 8 Aug | stat-arb overview | Khandani & Lo (2007) SSRN/MIT PDF, which quotes WSJ 2007-08-10 and 2007-08-14 | Confirmed. Kept `[Reported]` and named the source in the text (WSJ, quoted by Khandani & Lo) |
| 9 | R2 | Khandani–Lo contrarian rule: 1.38%/day (1995) → 0.44% (2000) → 0.13% (2007); −1.16/−2.83/−2.86% on 7–9 Aug (−6.85%, 12 sd); +5.92% on 10 Aug; ~9:1 leverage needed; >25% loss at 8:1 | overview, pairs, factor-residual, reversal | Khandani & Lo (2007) full text | Confirmed. TL;DR reworded: 9:1 is the leverage needed in 2007 to match 1998 expected returns |
| 10 | R2 | Avellaneda & Lee: PCA net Sharpe 1.44 (1997–2007), 0.9 (2003–07); ETF 1.1 (1997–2007); ETF trading time 1.51 (2003–07); 10 bps round trip; 252-day correlation window; X₆₀ = 0 so s = −m/σ_eq, centered m | overview, factor-residual | A&L author version (2008), abstract and §§ on estimation | Figures confirmed. The method detail showed two inconsistencies, now fixed: the overview pseudocode used a 60-day correlation window and had no intercept or centering; the factor-residual worked example had a nonzero X today |
| 11 | R2 | Frazzini, Israel & Moskowitz: reversal break-even \$9B US / \$13B global; momentum \$52B US; optimized global reversal \$17B; live data 1998–2011 | short-term reversal | FIM NBER conference draft (2012-12) full text | Confirmed |
| 12 | R2 | Boehmer, Jones & Zhang (2008): heavily shorted stocks underperform by 1.16% over 20 days | analyst revisions | Crossref abstract (JF 63(2)) | Confirmed. Clarified that BJZ measure **short-selling flow** (NYSE order data, 2000–2004), not short interest. Tag `[Reported]`→`[Verified]` |
| 13 | R2 | Xing, Zhang & Zhao (2010): steepest smirk underperforms by 10.9% a year | analyst revisions | OpenAlex abstract (JFQA 45(3)) | Confirmed (risk-adjusted). Tags `[Reported]`→`[Verified]` (3 places) |
| 14 | R2 | Mitchell & Pulvino (2001): merger arb ~4% a year excess | earnings/event | OpenAlex abstract (JF 56(6)) | Confirmed: 4,750 mergers 1963–1998, 4% a year **after transaction costs**, payoff like a short index put. Wording sharpened. Tags `[Reported]`→`[Verified]` |
| 15 | R3 | AQR Style Premia Alternative fund "fell 19.2% in 2020" | factor-timing | AQR fund fact sheet SPAF.pdf (calendar-year returns as of 2026-09-30); QSPIX page (since-inception Sharpe 0.54); Institutional Investor 2021-04-28 (the 19.23% figure is from "a private database") | **Corrected:** −19.2% `[Reported]` → −12.4% / −8.2% / −22.0% in 2018–2020, +24.8% / +30.6% in 2021–2022 `[Verified]` (fact sheet added to Sources). Since-inception Sharpe 0.54 (factor-fundamentals, carry) confirmed. AQR RAUM \$248.9B→\$164.4B confirmed as reported by II; clarified "SEC-reported, including leverage". |
| 16 | R3 | French-library computations: HML −58% (Dec 2006–Sep 2020), −51% (Jan 2017–Sep 2020), +68% (Oct 2020–Dec 2022), −17% (2023–24), −13.8% Mar 2020; all Sharpe tables; UMD crashes (−74% Jul–Aug 1932, −49% Mar–May 2009), worst months, 2022–2026 annual returns (2023 −20.5%), Nov 2020 −12.6%, 9 Nov 2020 −14.4%, 2026 −17.9%; vol scaling 0.45→0.87; skew −3.0; UMD–HML corr −0.41/−0.19 | factor-fundamentals, momentum, value-quality, factor-timing | Fresh download of F-F 3-factor, 5-factor, momentum (monthly and daily) CSVs from mba.tuck.dartmouth.edu (202609 CRSP); recomputed independently | **Confirmed** all, two small corrections in momentum: UMD 1927–1962 Sharpe 0.40→0.41; bear-state "otherwise" mean +0.84%→+0.83%, and the state definition clarified (it is the *sum* of monthly excess returns over 24 months; the compounded definition gives 275 months, −0.11% vs +0.83%). TL;DR now says 0.45→0.87 is on the same months (full-sample raw Sharpe is 0.46). Cross-page consistency of value drawdowns (58% from Dec 2006 vs 51% from Jan 2017) and momentum 2023 −20.5% confirmed. |
| 17 | R3 | AQR BAB/QMJ statistics: Sharpe table (0.70/1.06/0.67/0.76; 0.48/0.68/0.40/0.25), QMJ −36% Oct 2023–Jun 2026 and −11% in 2025, BAB −55% May 1998–Feb 2000, correlations HML–BAB 0.31, RMW–QMJ 0.70, HML–RMW 0.10 | value-quality-low-vol | Fresh download of AQR "Betting Against Beta: Equity Factors, Monthly" and "Quality Minus Junk: Factors, Monthly" (USA, through 2026-08); recomputed | **Confirmed** (QMJ peak end-Oct 2023 to Jun 2026 −36.3%; BAB −54.6%) |
| 18 | R3 | Value-over-growth BE/ME spread at June formation: 10th pct in 2007, 86th in 2017, 99th in 2022, record in June 2026 (1951–2026) | factor-timing | French "6 Portfolios 2x3", value-weight average BE/ME table (Dec ME), log spread avg(small, big), June values; recomputed | **Confirmed** (11th/86th/99th/100th, max = 2026; rank-method differences explain 10 vs 11) |
| 19 | R3 | Khandani & Lo: 8:1 levered book-to-market portfolio lost 24% from 1 Aug to close of 7 Aug 2007; unwind began at the 6 Aug open; market makers withdrew from 8 Aug | factor-timing, factor-fundamentals | NBER WP 14465 (Khandani & Lo, "Evidence from Factors and Transactions Data") full text | **Confirmed** |
| 20 | R3 | Cboe correlation gauges: COR3M 11.8 on 2026-11-11, 2006–2026 median 41, record low 7.19 (2026-07-10), 90.3 (2020-03-16), 90.8 (2011-12-08); COR1M 96.6 (2008-10-24), 2.9→39.6 (Jul 12→Aug 5 2024); DSPX 38.1; 2024 COR3M "jumped nearly nine points in the week of August 5" | dispersion | Cboe COR3M, COR1M, DSPX daily CSVs (cdn.cboe.com, through 2026-11-11) | **Confirmed** the Cboe figures; DSPX value was undated → dated (2026-11-11). **Corrected** the 2024 press figure ("nearly nine points") to Cboe data: low 7.6 on 3 Jul 2024, 14.0 on 31 Jul → 35.7 on 5 Aug `[Verified]`. |
| 21 | R3 | BIS on 5 Feb 2018: 115,862 VIX futures in one minute; "about \$4B of inverse and leveraged VIX products"; XIV fell 96% `[Verified]` | flow-driven, VRP | BIS Quarterly Review March 2018 box (r_qt1803t.htm) | 115,862 contracts at 16:08 **confirmed**. \$4B is end-2017 assets of select products: **clarified**. BIS gives XIV −84%; −96% is the indicative-value figure: VRP tag **downgraded** to `[Reported]` with "(BIS: 84%)", matching the failure gallery. |
| 22 | R4 | Avellaneda & Lee PCA stat arb: Sharpe 1.44 (1997–2007) vs 0.9 (2003–2007); ETF volume-time 1.51 | there-is-no-single-algorithm; evolution | Working paper PDF (math.nyu.edu, 2008-07-11) abstract | **Corrected** on there-is-no-single-algorithm: old "1.44 in the working draft; the published version reports only 0.9" → both figures come from the same abstract (1.44 full period, 0.9 for 2003–2007). Evolution page already right. |
| 23 | R4 | Jane Street ~\$39.6B net trading revenue 2025; HRT ~\$12.3B; Citadel Securities ~\$12.2B | evolution | Reuters (2026-04-24) via KFGO/MarketScreener; Hedgeweek | **Confirmed** `[Reported]` (unnamed sources; private-stake gains incl. Anthropic boosted Jane Street) |
| 24 | R4 | 2025 listed options volume 15.26B, sixth straight record | evolution | OCC 2026-01-05 release (via search excerpt), OCC 2025 annual report, Cboe | **Corrected**: 15.26B is OCC's *total cleared* volume (options + futures); options were 15.21B. Text now says "OCC-cleared volume … 15.26B contracts, 15.21B of them options" |
| 25 | R4 | Khandani-Lo contrarian rule 1.38%/day (1995) → 0.44% (2000) → 0.13% (2007 YTD); ~9:1 leverage needed in 2007 vs 1998; \$160B L/S-EMN assets; Aug 7–9 −1.16/−2.83/−2.86, −6.85% = 12 sd; +5.92% on Aug 10; week −0.43%; 8:1 = base × 4 | evolution; failure gallery | Khandani & Lo (2007) working paper PDF (MIT), text and Tables 2, 3, 6, 7 | **Confirmed**. Clarified in gallery that the "base" strategy is 2:1 (Reg T convention), not "unlevered", and 8:1 = 4× base |
| 26 | R4 | Balyasny flagship 2023: 15.2% gross, 2.8% net, \$768M pass-through, 87% compensation; Goldman: >\$30B multi-manager outflows, first in 7 years | how-firms-combine | Hedgeweek (citing Bloomberg) 2025-02-12; Hedgeweek (citing FT/Goldman) 2024-09-10 | **Confirmed** `[Reported]`; named the fund (Atlas Enhanced). Also confirmed Millennium 5%/7.5% ladder is measured on the *initial allocation* (Business Insider/WSJ) |
| 27 | R4 | SEC proposed modernizing rule 17a-7 cross trading, published Oct 2026 | how-firms-combine | Federal Register API, doc 2026-21037 | **Confirmed** `[Verified]`: proposed rule, 91 FR 65622, published 2026-10-15, Release IC-36358, comments close 2026-12-14 (added to text and source line) |
| 28 | R4 | Kakushadze & Tulchinsky: 4,000 WorldQuant alphas, holding 0.7–19 days, median Sharpe 1.49 before costs, cost-per-share vs turnover | evaluating-signals | arXiv 1509.08110v2 abstract and Table 1 | **Confirmed with wording fix**: median 1.487 for 3,289 positive-Sharpe alphas (after outlier removal), before costs; abstract finds cents-per-share ∝ 1/turnover → text now "cents per share scaled as 1/turnover" |
| 29 | R5 | GKX (2020): monthly OOS R² 0.33–0.40% for trees and nets vs 0.16% OLS-3; NN long-short value-weighted Sharpe 1.35 vs linear about 0.6 | F1, F2, F3 | GKX paper PDF (dachxiu.chicagobooth.edu/download/ML.pdf); NBER w25398 abstract | Confirmed: 1.35 VW (2.45 EW) vs OLS-3 benchmark 0.61 (0.83 EW); R² 0.33–0.40%, OLS-3 0.16%, full OLS −3.46%. F2's "about 0.6 `[Reported]`" corrected to "0.61 `[Verified]`" and the Mirova secondary source dropped |
| 30 | R5 | Lopez-Lira & Tang: JFE 2026; GPT-4 "calls the direction of the same-day reaction about 90% of the time" | F4 | Crossref (JFE 184, 104335, Oct 2026); arXiv 2304.07619 v. 2025-10 abstract | Publication confirmed. Corrected: the figure is a **portfolio-day hit rate** (~90% of days) on the non-tradable initial reaction, not per-headline accuracy. Added that drift prediction is strongest in small stocks and after bad news, and that strategy returns fall as LLM adoption rises |
| 31 | R5 | F4 TODO(verify): named firms using in-house LLM tools | F4 | Hedgeweek 2023-07-25 (ManGPT); Hedgeweek 2025-07-11, citing Bloomberg 2025-07-10 (AlphaGPT) | Resolved: Man Group's ManGPT portal (2023) and AlphaGPT agent (2025; several dozen signals approved for live trading after human review) `[Reported]`. TODO removed |
| 32 | R5 | Rahimikia et al. (2026): foundation models trail CatBoost/LightGBM on daily returns, with "flat or declining" long-short returns and "do not trade profitably" | F2, F4 | arXiv:2511.18578 (Rahimikia, Ni & Wang, Nov 2025) full text | Corrected: zero-shot and fine-tuned TSFMs trail the boosted trees (zero-shot Chronos-large still earned 20% a year gross). Versions **pre-trained from scratch on financial data** came close on long-short Sharpe (gross, no costs) but not on R². "Do not trade profitably" removed. Citation changed to the arXiv version with the full author list; the FoFI URL did not resolve here |
| 33 | R5 | Cederburg et al. (2020): real-time vol-managed versions lose to the originals, "72 cases" | F6 | Paper PDF (JFE 138(1), 95–117) | Refined: managed versions had the higher Sharpe in only 53 of 103 direct comparisons, and real-time *combinations* earned lower CER than the original alone in 72 of 103 |
| 34 | R5 | VIX stats from 1990 to 2026-11: above 30 on 7.9% of days, stays above 30 the next day 87% of the time, above 25 on 17% | F6 | FRED VIXCLS CSV, 9,314 closes from 1990-01-02 to 2026-11-10, recomputed | Confirmed (7.89%, 87.2%, 17.2%). Tag upgraded `[Estimate]`→`[Verified]` (computed from FRED), matching facts.md |
| 35 | R5 | zipline-reloaded v3.2.1 in Oct 2026; backtrader's last PyPI release in Apr 2023 | V2 | PyPI JSON API | Confirmed (3.2.1 uploaded 2026-10-25; backtrader 1.9.78.123 uploaded 2023-04-19) |
| 36 | R6 | Almgren, Thum, Hauptmann & Li (2005) "Equity market impact", *Risk* 18(7) 57–62: impact exponent ≈ 0.6 on ~700,000 Citigroup US orders; CFM ~500,000 futures trades δ 0.5–0.6; Y "of order unity" | P5, E3 (Lab 16 README) | Tóth et al. 2011 full text (arXiv 1105.1694): "700,000 US stock trade orders executed by Citigroup Equity Trading… δ ≈ 0.6", "nearly 500,000 trades… δ ≈ 0.5 small tick, 0.6 large tick", "Y is of order unity", δ range 0.4–0.7; Risk.net and Wikipedia listing (Risk, July 2005, pp. 57–62; 3/5 power law) | Confirmed. Source tag stays [Reported] (article paywalled; details via Tóth et al.). The 0.142 / 0.314 coefficients are not quoted anywhere in the KB, so not needed. |
| 37 | R6 | Frazzini, Israel & Moskowitz (2018): \$1.7T of live AQR trades, 21 markets, 19 years; costs an order of magnitude below earlier studies; calibrated model wins out of sample | P5 | AQR working-paper page (abstract) | Confirmed verbatim. |
| 38 | R6 | "About 40% of US buy-side flow runs through algos; 36% of desks use algo wheels (2025)"; The TRADE 2025 algo-type shares (VWAP 81%, POV 74%, TWAP 38%, IS 51%, close 56%, dark liquidity-seeking 74%) | E1 (E2 for TRADE) | Web search on Coalition Greenwich 2025 US equity report (wheels 36%, +4 pts, 253 traders); Markets Media 2026-05-18 on Crisil Coalition Greenwich FY2025 report (algo + SOR = 43% of buy-side activity); The TRADE 2025 survey PDF, Figure 6 | Wheels and TRADE figures confirmed (TRADE caption tag upgraded to [Verified]). Algo share corrected: "about 40%" → "43% in FY2025", with the Markets Media source added. greenwich.com itself is blocked from this environment. |
| 39 | R6 | NYSE close: MOC/LOC cutoff 3:50 p.m.; contra-side LOC allowed after 3:50; "no NYSE cancels after 3:58 p.m." | E5 | NYSE Auctions Closing Process Fact Sheet (© 2024): MOC/LOC "after 3:50 p.m. cannot be modified or canceled"; after 3:50 entry only on the contra side of a significant imbalance; a 2022 NYSE memo (via search) removed the legitimate-error exception | Corrected: "no cancels after 3:58" → "no MOC/LOC cancels after 3:50 p.m., even for errors" (2 places). 3:50 cutoff and offsetting-LOC logic confirmed. |
| 40 | R6 | Dark-pool settlements: Barclays \$70M and Credit Suisse \$84.3M (2016); ITG \$20.3M (2015) | E5 | Press coverage of SEC/NYAG settlements (Wharton, Daily Star, Investment Executive, Finance Magnates) | Figures confirmed. Wording corrected: "regulators have fined… up to \$84.3M" → "one dark-pool operator paid \$84.3M to settle charges". The \$84.3M includes \$24.3M disgorgement and interest, so it is not all fines. |
| 41 | R6 | "Amended Rule 605 reports add realized spreads; compliance 2026-08-01" | E6 | Federal Register final rule 2024-05556 (89 FR 26428) abstract; FR 2025-19316 compliance extension | Corrected: realized spread was already in Rule 605. The amendments add larger brokers, odd-lot and fractional orders, millisecond timing, and **realized spreads at several horizons**. Compliance date 2026-08-01 confirmed. FR source line added. |
| 42 | R6 | Laloux et al. (1999): 406 S&P 500 stocks, 1,309 days; 94% of eigenvalues in the noise band; the top ~6% carry 26% of volatility | P2 | arXiv cond-mat/9810255 full text | Confirmed. Added the nuance that the band is fitted with σ² = 0.74 (the market mode's variance removed); TL;DR now says "fit such a band". |
| 43 | R7 | FPGA tick-to-trade 13.9 ns, 2024 STAC-T0, network I/O only (dead STAC URL) | M1 anatomy | AMD blog 2024-06-27 (amd.com, fetched): minimum 13.9 ns, STAC-T0 measures tick-to-trade network-I/O latency, testing commissioned by AMD and Exegy | Confirmed. Dead `stacresearch.com/node/48577` replaced by the AMD URL, the same source `there-is-no-single-algorithm.md` uses. Table now says "minimum" and "vendor-commissioned", matching that page |
| 44 | R7 | Software tick-to-trade ~2.5 µs (Cook 2017); hot path runs 0.01% of the time; "pull all orders, then ask questions" | M1 anatomy | Carl Cook's CppCon 2017 slides (CppCon2017 GitHub PDF): "a very good minimum time (wire to wire) for a software-based trading system is around 2.5us"; "hotpath is only exercised 0.01% of the time"; "Pull all orders, then start asking questions" | Confirmed. Wording made exact: "at best about 2.5 µs", "at best, wire to wire". Source line now points to the slides PDF, not the isocpp blog post |
| 45 | R7 | Knight 2012: 212 retail orders → over 4M executions in 154 stocks in 45 min; one of eight servers; 97 emails; \$12M penalty | M9 risk controls | SEC order 34-70694 as quoted verbatim (paras 15–16) by jrvarma.in; WilmerHale summary (97 emails, \$12M); facts.md (\$460M, 397M shares) | Confirmed (sec.gov blocks fetches, so the order was read via verbatim quotation) |
| 46 | R7 | CKS (2014): 50 NYSE stocks, 10-s intervals, OFI R² 65% vs trade imbalance 32%; R² 35–60% without price-changing events | M3 order-book signals | CKS arXiv:1011.6402v3 full text (abstract, §3.1–3.2 incl. footnote 3, Table 4) | Numbers confirmed (grand mean 65% vs 32%; 10-s grid; footnote 3 gives 35–60%). Corrected: the stocks were 50 randomly drawn **S&P 500** constituents measured with NYSE TAQ data, not "50 NYSE stocks" |
| 47 | R7 | Amended Rule 605 realized-spread horizons: 50 ms, 1 s, 15 s, 1 min, 5 min | M5 markouts | eCFR API, 17 CFR 242.605 current text (items O–X) | Confirmed. Tag `[Reported]` → `[Verified]`; eCFR source line added |
| 48 | R7 | Retail is over 60% of options volume (Bryzgalova, Pavlova & Sikorskaya 2023) | Options MM walkthrough | JF 2023 published abstract (via LBS repository and CEPR/EconPapers listings in search results) | Confirmed: "over 60% of total market volume" |
| 49 | R7 | Hendershott & Menkveld (2014): NYSE intermediary price pressure 0.49% average, 0.92-day half-life | M4 quoting | JFE abstract on RePEc/EconPapers (fetched) | Confirmed verbatim. Note: the 2010 working paper reports 0.28% per \$100K shock, with 0.49% as transitory volatility; the page correctly cites the journal version |

## Open TODO(verify) items

_Collected from pages by `grep -rn "TODO(verify)" docs/`; updated after each phase._

## Page checklist

### (root pages)

- [x] `index.md` — Home (P1)
- [x] `labs.md` — Labs (P3)

### 00-start-here

- [x] `00-start-here/the-big-picture.md` — The big picture (P1)
- [ ] `00-start-here/learning-paths.md` — Learning paths (P5)
- [ ] `00-start-here/one-page-cheat-sheet.md` — One-page cheat sheet (P5)

### 01-market-structure

- [x] `01-market-structure/life-of-a-stock-order.md` — Life of a stock order (P2)
- [x] `01-market-structure/the-limit-order-book.md` — The limit order book (P2)
- [x] `01-market-structure/order-types-and-auctions.md` — Order types and auctions (P2)
- [x] `01-market-structure/venues-and-retail-flow.md` — Venues and retail flow (P2)
- [x] `01-market-structure/nbbo-and-market-data.md` — NBBO and market data (P2)
- [x] `01-market-structure/fees-rebates-and-ticks.md` — Fees, rebates and ticks (P2)
- [x] `01-market-structure/etf-futures-options-linkages.md` — ETF, futures and options linkages (P2)
- [x] `01-market-structure/shorting-financing-and-settlement.md` — Shorting, financing and settlement (P2)
- [x] `01-market-structure/recent-changes.md` — Recent changes (as of 2026-11) (P2)

### 02-strategies

- [x] `02-strategies/index.md` — Strategies: the map (P1)
- [x] `02-strategies/how-quants-evaluate-a-strategy.md` — How quants evaluate a strategy (P1)
- [x] `02-strategies/a-liquidity-provision/equity-market-making.md` — Equity market making (P3)
- [x] `02-strategies/a-liquidity-provision/etf-market-making.md` — ETF market making (P3)
- [x] `02-strategies/a-liquidity-provision/options-market-making.md` — Options market making (P3)
- [x] `02-strategies/a-liquidity-provision/retail-flow-internalization.md` — Retail flow internalization (P3)
- [x] `02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md` — Auctions and closing liquidity (P3)
- [x] `02-strategies/b-speed-and-structural/latency-arbitrage.md` — Latency arbitrage (P3)
- [x] `02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md` — Lead-lag and cross-asset arbitrage (P3)
- [x] `02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md` — ETF and index arbitrage (P3)
- [x] `02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md` — Fee- and microstructure-driven strategies (P3)
- [x] `02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md` — Stat arb: overview and history (P3)
- [x] `02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md` — Pairs trading and cointegration (P3)
- [x] `02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md` — Factor-residual mean reversion (P3)
- [x] `02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md` — Short-term cross-sectional reversal (P3)
- [x] `02-strategies/c-statistical-arbitrage/intraday-patterns-and-seasonality.md` — Intraday patterns and seasonality (P3)
- [x] `02-strategies/c-statistical-arbitrage/ml-driven-short-horizon-alpha.md` — ML-driven short-horizon alpha (P3)
- [x] `02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md` — Cross-sectional alpha and neutralization (P3)
- [x] `02-strategies/d-mid-frequency-alpha/fundamental-quant-signals.md` — Fundamental quant signals (P3)
- [x] `02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md` — Earnings and event-driven (P3)
- [x] `02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md` — Analyst revisions and sentiment (P3)
- [x] `02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md` — Flow-driven strategies (P3)
- [x] `02-strategies/d-mid-frequency-alpha/alternative-data.md` — Alternative data (P3)
- [x] `02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md` — NLP and LLM signals (P3)
- [x] `02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md` — Factor investing fundamentals (P3)
- [x] `02-strategies/e-risk-premia-and-factors/momentum.md` — Momentum (P3)
- [x] `02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md` — Value, quality and low volatility (P3)
- [x] `02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md` — Factor timing, crowding and quant winters (P3)
- [x] `02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md` — Volatility risk premium and vol arb (P3)
- [x] `02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md` — Dispersion and correlation trading (P3)
- [x] `02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md` — Trend following and CTAs (P3)
- [x] `02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md` — Carry and cross-asset risk premia (P3)
- [x] `02-strategies/h-cross-cutting/strategy-comparison-matrix.md` — Strategy comparison matrix (P5)
- [x] `02-strategies/h-cross-cutting/strategy-x-algorithm-matrix.md` — Strategy x algorithm matrix (P5)
- [x] `02-strategies/h-cross-cutting/strategy-failure-gallery.md` — Strategy failure gallery (P5)
- [x] `02-strategies/h-cross-cutting/evolution-of-quant-strategies.md` — Evolution of quant strategies (P5)
- [x] `02-strategies/h-cross-cutting/how-firms-combine-strategies.md` — How firms combine strategies (P5)

### 03-algorithms

- [x] `03-algorithms/index.md` — Algorithms: overview (P1)
- [x] `03-algorithms/there-is-no-single-algorithm.md` — There is no single algorithm (P1)
- [x] `03-algorithms/algorithm-map.md` — Algorithm map (P1)
- [x] `03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md` — Point-in-time data and cleaning (P4)
- [x] `03-algorithms/a-data-and-signals/feature-engineering.md` — Feature engineering (P4)
- [x] `03-algorithms/a-data-and-signals/signal-transforms.md` — Signal transforms (P4)
- [x] `03-algorithms/a-data-and-signals/evaluating-signals.md` — Evaluating signals (P4)
- [x] `03-algorithms/b-forecasting-models/linear-models-and-regularization.md` — Linear models and regularization (P4)
- [x] `03-algorithms/b-forecasting-models/tree-ensembles.md` — Tree ensembles (P4)
- [x] `03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md` — Neural nets and sequence models (P4)
- [x] `03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md` — LLMs and foundation models in quant (P4)
- [x] `03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md` — Alpha combination and ensembling (P4)
- [x] `03-algorithms/b-forecasting-models/regime-detection.md` — Regime detection (P4)
- [x] `03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md` — Time-series cross-validation (P4)
- [x] `03-algorithms/c-validation-and-backtesting/backtesting-engines.md` — Backtesting engines (P4)
- [x] `03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md` — Backtest pitfalls (P4)
- [x] `03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md` — Overfitting and multiple testing (P4)
- [x] `03-algorithms/d-portfolio-construction/risk-models.md` — Risk models (P4)
- [x] `03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md` — Covariance estimation and shrinkage (P4)
- [x] `03-algorithms/d-portfolio-construction/mean-variance-optimization.md` — Mean-variance optimization (P4)
- [x] `03-algorithms/d-portfolio-construction/alternatives-to-mvo.md` — Alternatives to MVO (P4)
- [x] `03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md` — Transaction cost and impact models (P4)
- [x] `03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md` — Multi-period optimization and trading toward the aim (P4)
- [x] `03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md` — Position sizing and risk budgeting (P4)
- [x] `03-algorithms/e-execution-algorithms/execution-algorithms-overview.md` — Execution algorithms: overview (P4)
- [x] `03-algorithms/e-execution-algorithms/vwap-twap-pov.md` — VWAP, TWAP and POV (P4)
- [x] `03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md` — Implementation shortfall and Almgren-Chriss (P4)
- [x] `03-algorithms/e-execution-algorithms/smart-order-routing.md` — Smart order routing (P4)
- [x] `03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md` — Auction, close and dark-liquidity algos (P4)
- [x] `03-algorithms/e-execution-algorithms/transaction-cost-analysis.md` — Transaction cost analysis (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md` — Anatomy of an HFT trading loop (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md` — Fair value and microprice (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md` — Order-book and trade-flow signals (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md` — Quoting and inventory control (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md` — Adverse selection and markouts (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md` — Queue position and order placement (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md` — Hedging algorithms (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md` — Options pricing and vol surfaces for market making (P4)
- [x] `03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md` — Algorithmic risk controls (P4)
- [x] `03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md` — Live monitoring and P&L attribution (P4)
- [x] `03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md` — Alpha decay detection and model retirement (P4)
- [x] `03-algorithms/g-live-trading/reinforcement-learning-in-trading.md` — Reinforcement learning in trading (P4)
- [x] `03-algorithms/h-end-to-end-walkthroughs/walkthrough-mid-frequency-stat-arb.md` — Walkthrough: a mid-frequency stat-arb book (P5)
- [x] `03-algorithms/h-end-to-end-walkthroughs/walkthrough-etf-market-maker.md` — Walkthrough: a day at an ETF market maker (P5)
- [x] `03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md` — Walkthrough: an options market maker (P5)
- [x] `03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md` — Walkthrough: executing a $500M buy order (P5)

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

- [x] `09-reference/glossary.md` — Glossary (P9)
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
