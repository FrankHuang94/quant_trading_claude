# Glossary

> **TL;DR**: 150 terms (a seed that will grow to 400+), 72% on strategies and algorithms. Each entry: a one- to three-sentence practitioner definition and a link to the page that explains it.

**Jump to:** [A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [F](#f) · [G](#g) · [H](#h) · [I](#i) · [K](#k) · [L](#l) · [M](#m) · [N](#n) · [O](#o) · [P](#p) · [Q](#q) · [R](#r) · [S](#s) · [T](#t) · [V](#v) · [W](#w) · [Z](#z)

Confidence tags follow the KB convention: `[Verified]` primary source · `[Reported]` credible secondary source · `[Estimate]` derived · `[Lore]` widely repeated, unverified. Regulatory status is as of 2026-11.

<!--
Maintainer notes (keep this structure when growing the glossary to 400+ terms):
- One "### Term" heading per term, under "## <Letter>" sections, alphabetical within each letter.
- Headings are plain ASCII, singular, no en dashes; acronym in parentheses where natural.
  The anchor is the Python-Markdown slug of the heading, e.g. "Order-flow imbalance (OFI)" -> order-flow-imbalance-ofi.
  Renaming a heading breaks inbound links: run `python scripts/check_glossary_links.py --missing` after any rename.
- Every entry ends with "**See:**" and at least one relative link to the explaining page.
  Strategy and algorithm terms must link a page in 02-strategies or 03-algorithms first.
- Keep the Jump-to line in sync with the letters that exist.
- Avoid "-$" or "($" before a dollar amount in a paragraph that contains another "$": arithmatex will read it as math.
- Regulatory statuses come from the build's shared facts register; update them in one pass when rules change.
-->

## A

### Access fee

The fee an exchange charges to execute against a resting quote, capped by Reg NMS Rule 610(c) for protected quotations at $0.003 per share (30 mils) for stocks priced at $1 or more since 2005. The September 2024 amendments cut the cap to $0.001 (10 mils), but compliance has been postponed twice, most recently to the first business day of November 2027 (SEC order of 2026-06-11), and the SEC chairman has said staff will review Rule 610(c), so the 30-mil cap still applies as of 2026-11 `[Verified]`. Because maker rebates are funded from take fees, the cap also bounds rebates and the whole maker-taker economy. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

### Adverse selection

The loss a liquidity provider suffers because the counterparties who choose to trade against its quotes are, on average, better informed about the next price move, so fills are systematically followed by prices moving against it. Market makers measure it with markouts and manage it by skewing, widening or pulling quotes when short-horizon signals turn against them; in liquid large caps it typically consumes most of the gross half-spread `[Lore]`. **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Almgren-Chriss model

The canonical optimal-execution model (Almgren and Chriss, 2001): choose the trading trajectory that minimizes expected cost plus $\lambda$ times the variance of cost, given linear temporary and permanent impact. The solution front-loads trading more the higher the risk aversion, $x(t) = X\,\sinh(\kappa(T-t))/\sinh(\kappa T)$ with $\kappa \approx \sqrt{\lambda\sigma^2/\eta}$, and traces a cost-versus-risk efficient frontier that underlies most implementation-shortfall algorithms. **See:** [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Alpha combination

The step that merges many individual signals into one expected-return forecast per stock, by equal or IC-weighted averaging, regression on forward returns (usually ridge-regularized) or tree and neural ensembles. The hard parts are correlated signals, unstable weights and leakage in the combination step itself, which is why combination weights are fit with purged, walk-forward validation like any other model. **See:** [Alpha combination and ensembling](../03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md)

### Alpha decay

Two related meanings: (1) how fast a signal's predictive power fades with horizon after it is formed (its information half-life), and (2) the erosion of a strategy's edge over calendar time as competitors find it. On the second, McLean and Pontiff (2016) found anomaly returns about 26% lower out of sample and 58% lower after publication `[Reported]`. **See:** [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

### Alternative data

Non-traditional datasets used to forecast fundamentals or flows before they reach prices or filings: card-transaction panels, web traffic and app usage, satellite and geolocation data, job postings, shipping and supply-chain records. The edge is usually nowcasting a reported metric (revenue, same-store sales) a few weeks early; the costs are licensing, short histories, panel drift and legal review of how the data was collected. **See:** [Alternative data](../02-strategies/d-mid-frequency-alpha/alternative-data.md)

### Alternative trading system (ATS)

A broker-dealer-operated venue registered under Regulation ATS rather than as an exchange. NMS-stock ATSs, most of them dark pools, file public Form ATS-N disclosures on order types, segmentation and who can interact with whom, and their quotes are not protected under Reg NMS. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

### Alternative uptick rule

Reg SHO Rule 201 (adopted 2010): once a stock falls 10% or more from the prior day's close, short sales may be executed only at a price above the current national best bid for the rest of that day and the whole next day `[Reported]`. Short-side strategies and hedges must switch to passive, above-the-bid execution while the restriction is on, which changes both fill rates and adverse selection. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### Arrival price

The midquote at the moment a parent order reaches the trader or algorithm, used as the benchmark for implementation shortfall. Slippage versus arrival captures delay, spread, impact and opportunity cost in one number and cannot be gamed by trading with the crowd, which is why buy-side TCA has largely moved from VWAP to arrival-price benchmarks. **See:** [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Auction imbalance

The excess of buy over sell interest (or the reverse) at the indicative clearing price of an opening or closing auction, published by the listing exchange in the minutes before the cross (from 3:50 pm ET for the NYSE and Nasdaq closes `[Reported]`). Liquidity providers trade against published imbalances with offsetting closing orders and unwind later, earning a premium for warehousing overnight gap risk. **See:** [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Authorized participant

A broker-dealer (AP) with a contractual agreement with an ETF issuer that lets it create and redeem ETF shares in creation-unit size, usually in kind against a basket of the underlying securities. APs are the conduit for ETF arbitrage; market makers that are not APs arbitrage through one. **See:** [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md) · [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md)

### Avellaneda-Stoikov model

The 2008 market-making model in which a dealer with exponential utility quotes around a reservation price $r = s - q\gamma\sigma^2(T-t)$ that shifts against inventory $q$, with total spread $\gamma\sigma^2(T-t) + \tfrac{2}{\gamma}\ln(1+\gamma/k)$, where $k$ describes how fast fill intensity decays with distance from the mid. In practice it is the template for inventory skew rather than a production quoter; the GLFT model removes its finite-horizon artifacts. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

## B

### Basis

The difference between a futures (or other derivative) price and the price of its underlying, $F - S$; the fair basis for an equity index future is the net carry, roughly $S\,(e^{(r-q)T} - 1)$ with financing rate $r$ and dividend yield $q$. Index arbitrageurs trade deviations of the actual basis from fair value net of financing, dividend uncertainty and execution costs; in liquid index futures such deviations are small and short-lived `[Lore]`. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md)

### Best execution

A broker's duty to seek the most favorable terms reasonably available for a customer order, codified for FINRA members in Rule 5310 with a "regular and rigorous" review of execution quality across venues. It is what makes routing, PFOF and internalization decisions reviewable and why brokers buy TCA. The SEC's December 2022 proposal for its own Regulation Best Execution was withdrawn on 2025-06-12 `[Reported]`, so FINRA's rule remains the operative standard. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

### Beta neutral

A long-short portfolio whose net exposure to the market factor (the sum of position value times beta) is zero, as opposed to dollar neutral (equal long and short dollars). A dollar-neutral book long low-beta utilities and short high-beta tech is net short the market; most equity market-neutral books target both, plus near-zero sector and style exposures, via neutralization or optimizer constraints. **See:** [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

### Bid-ask bounce

Spurious negative autocorrelation in trade-price returns caused by consecutive trades alternating between the bid and the ask (Roll, 1984). A short-term reversal backtest on last-trade or closing prices harvests this bounce on paper; using midquotes, lagging execution by a bar and charging the spread removes it. **See:** [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Short-term cross-sectional reversal](../02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md)

### Breadth

In the fundamental law of active management, the number of independent forecasts (bets) a strategy makes per year. Breadth is overstated whenever bets are correlated: 500 stocks that load on one sector, or a slow signal rebalanced daily, are not 500 or 252 independent bets, which is the main reason fundamental-law IRs are too optimistic. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

## C

### Capacity

The capital a strategy can run before market impact and crowding erode its net returns unacceptably; working definitions include the AUM at which net Sharpe halves or at which the marginal dollar earns zero net alpha. Capacity scales roughly with the liquidity of the names traded times the holding period `[Estimate]` (impact cost grows with trade size relative to volume), which is why HFT is high-Sharpe but small and factor investing low-Sharpe but large. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

### Carry

The return an asset earns if its price does not change: roll yield for futures, the interest differential for currencies, dividend yield net of financing for equities (Koijen, Moskowitz, Pedersen and Vrugt, 2018). Carry strategies go long high-carry and short low-carry assets within or across asset classes; the premium comes with left-skewed, crash-prone returns. **See:** [Carry and cross-asset risk premia](../02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md)

### Closing auction

The single-price cross at 4:00 pm ET on each listing exchange that sets the official close used for index valuation, fund NAVs and benchmarks; MOC and LOC orders feed it and imbalances are published from 3:50 pm `[Reported]`. Its share has grown with indexing, from about 3% of dollar volume in 2010 to a record of about 9.4% of notional in Q2 2024, and is far higher on index-rebalance days `[Reported]`. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md)

### Cointegration

Two or more non-stationary price series are cointegrated if some linear combination of them (the spread $y - \beta x$) is stationary, so deviations tend to close. It is tested with Engle-Granger (regress, then run an ADF test on the residuals with adjusted critical values) or Johansen; it is a more useful property for pairs trading than high return correlation, but estimated relationships break often out of sample. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Colocation

Renting rack space for one's servers inside an exchange's matching-engine data center (NYSE in Mahwah, Nasdaq in Carteret and Cboe in Secaucus, all in New Jersey `[Reported]`) so that market data and orders travel meters rather than kilometers. Exchanges equalize cable lengths inside the facility; colocation is table stakes for market making and latency-sensitive strategies, not an edge by itself. **See:** [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

### Combinatorial purged cross-validation (CPCV)

López de Prado's (2018) extension of purged k-fold cross-validation: split the sample into N groups, use every combination of k groups as the test set (with purging and embargo), and stitch the test predictions into many complete backtest paths (N = 6, k = 2 gives 15 splits and 5 paths). Instead of one walk-forward Sharpe ratio you get a distribution of them, which feeds overfitting diagnostics such as PBO. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md) · [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Commodity trading advisor (CTA)

A US regulatory category (registered with the CFTC, member of the NFA) for managers advising on futures, and in practice the industry label for systematic, mostly trend-following futures funds. CTAs matter to equity quants because their de-risking in sharp selloffs flows into index futures and, through index arbitrage, into the underlying stocks. **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Conditional order

A dark-pool order type that rests as a non-binding indication; when the venue finds a potential match it invites the sender to "firm up" with a real order within a short window. Conditionals let a large order sit in many dark pools at once without overfill risk; venues track firm-up rates and penalize participants who use conditionals to fish for information. **See:** [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Creation and redemption

The primary-market mechanism by which an AP creates ETF shares (delivering a basket of securities or cash and receiving new shares) or redeems them (the reverse), in creation units typically of tens of thousands of shares `[Reported]`. It anchors the ETF price to NAV: when the ETF trades rich, arbitrageurs sell the ETF, buy the basket and create shares to close the position. **See:** [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md) · [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md)

### Crowding

Many funds holding the same positions because they run similar signals on similar data, so their exits are correlated. Crowding is measured with short-interest and 13F holdings overlap, borrow costs, factor-return correlations and days-to-cover; it costs little until a deleveraging shock, then produces fast, correlated drawdowns such as the August 2007 quant quake. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

## D

### Dark pool

A venue that does not publish quotes, almost always an ATS or a broker's internal crossing engine; orders typically match at or within the NBBO (often at the midpoint) and trades are reported to the consolidated tape through a FINRA trade reporting facility after execution. Off-exchange trading passed half of US equity volume in 2025 (50.6%), but ATSs are only about a fifth of that, the rest being principal dealers such as wholesalers `[Reported]`; who is allowed into a pool and how flow is segmented determine how toxic it is. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Deflated Sharpe ratio

Bailey and López de Prado's (2014) test of a Sharpe ratio that corrects for selection across N trials, non-normal returns and track-record length: the probability that the true Sharpe exceeds the maximum Sharpe expected from N skill-less trials. The more configurations tried, the higher the hurdle, so a backtest Sharpe that clears it after 10 trials can fail after 1,000. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Delta hedging

Neutralizing an option position's first-order exposure to the underlying by trading $-\Delta$ units of the stock, ETF or future. Market makers re-hedge at discrete times or when delta drifts outside a band, trading hedge costs against tracking error; what remains is gamma, theta and vega P&L. **See:** [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md) · [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md)

### Designated market maker (DMM)

The NYSE successor to the specialist: a firm assigned to each listed stock with obligations to maintain quotes, provide liquidity and run the open, close and reopenings (including manual price setting), in return for parity allocations and fee benefits. A small number of firms hold the assignments, e.g., Citadel Securities, GTS and Virtu `[Reported]`. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md)

### Direct feed

An exchange's proprietary market-data feed (e.g., Nasdaq TotalView-ITCH, NYSE Integrated, Cboe PITCH) carrying full depth and order-by-order events with lower latency than the SIP. Latency-sensitive firms build their own book and NBBO from direct feeds; the gap between the direct-feed view and the SIP view is the window that latency-arbitrage debates are about. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Dispersion trading

Selling index volatility and buying volatility on the index constituents (or the reverse), with options or variance swaps, to trade the gap between implied and realized correlation. Because index implied correlation has historically exceeded realized `[Reported]`, the short-correlation side earns a premium on average but loses heavily in market-wide selloffs, when correlations jump toward one. **See:** [Dispersion and correlation trading](../02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md)

## E

### Effective spread

Twice the signed distance between the execution price and the midpoint prevailing at order arrival, $2q(P - M)$ with $q = +1$ for buys: the cost actually paid, net of any price improvement. Split into realized spread (what the liquidity provider kept) and price impact (what it lost to adverse selection), it is the standard decomposition in Rule 605 reports and microstructure research. **See:** [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md) · [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Embargo

A buffer of observations dropped from the training set immediately after each test fold in cross-validation, so that features built on serially correlated data just after the test period cannot leak test information into training. López de Prado (2018) suggests an embargo of about 1% of the sample; it complements purging, which handles overlapping label horizons. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### ETF arbitrage

Trading an ETF against its underlying basket (or against correlated futures and ETFs) when the ETF price deviates from its intraday fair value, closing through creation/redemption or by unwinding both legs. In large US equity ETFs the deviations are a few basis points or less and are captured by a handful of market makers within milliseconds `[Lore]`; the economics are in hedge precision and execution cost rather than the raw mispricing. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md)

## F

### Factor model

A model that explains each stock's return as exposures to a small number of common factors plus an idiosyncratic residual, $r = Bf + \varepsilon$, so the covariance matrix becomes $BFB^\top + D$. Factors can be fundamental (industry, size, value, momentum: exposures observed, factor returns estimated by cross-sectional regression), macroeconomic or statistical (PCA); quants use them to forecast risk, neutralize unwanted exposures and attribute P&L. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Factor timing

Varying exposure to factors (value, momentum, low volatility and so on) based on forecasts of their returns from valuation spreads, factor momentum, volatility or macro regimes. The evidence is contested: proponents point to predictable factor volatility and factor momentum, skeptics (e.g., Asness, 2016) to weak out-of-sample results and the turnover cost of timing. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

### Fair value

In market making and HFT, the firm's real-time estimate of where the price "really" is: the mid adjusted for book imbalance (microprice), recent trade flow, lead-lag signals from futures and ETFs, and sometimes its own inventory. Quotes are placed relative to fair value rather than the displayed mid, and small accuracy gains, fractions of a tick, are much of the edge `[Lore]`. **See:** [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

### Fama-MacBeth regression

The two-pass procedure (Fama and MacBeth, 1973) that runs a cross-sectional regression of returns on characteristics or exposures each period, then averages the per-period slopes and uses their time-series standard error for inference. It is the workhorse for asking whether a characteristic carries a return premium controlling for others; each period's slope is also the return of a characteristic-mimicking portfolio. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Fill probability

The probability that a passive limit order executes within a given horizon, as a function of its queue position, the size ahead of it, order-arrival and cancellation rates, and price moves. Fill-probability models decide whether to post or take, at which price and on which venue; fills that do happen are adverse-selected relative to those that do not, so fill probability and markouts are always modeled together. **See:** [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Flow toxicity

The degree to which order flow is informed, i.e., likely to move prices against the liquidity provider after the trade. Market makers estimate it per counterparty, venue and order type from historical markouts; VPIN (Easley, López de Prado and O'Hara, 2012) is a published volume-bucket measure whose predictive power is disputed (Andersen and Bondarenko, 2014). **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

### FPGA

Field-programmable gate array: a reconfigurable chip on which trading logic (feed parsing, book building, simple decision rules, order encoding) runs directly in hardware. FPGA paths are used where tick-to-trade must be well under a microsecond `[Reported]`; the cost is long development cycles and limited logic, so firms split strategies between fast, simple hardware paths and slower, richer software. **See:** [A semiconductor lens](../05-infrastructure/semiconductor-lens.md) · [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)

### Frequent batch auction

A market design proposed by Budish, Cramton and Shim (2015) that replaces continuous trading with uniform-price sealed-bid auctions held every fraction of a second (e.g., every 100 ms), so speed advantages smaller than the batch interval stop winning races. It is the leading academic remedy for latency arbitrage; US equity markets have not adopted it. **See:** [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Fundamental law of active management

Grinold's (1989) approximation $IR \approx IC \times \sqrt{BR}$: the information ratio of an optimally run active strategy is forecast skill times the square root of breadth, later scaled by a transfer coefficient for constraints (Clarke, de Silva and Thorley, 2002). Its message is that a tiny IC (say 0.02) across thousands of independent bets can give a high IR, but only if the bets really are independent and before costs. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

## G

### Gamma scalping

Holding long options (positive gamma) and repeatedly delta-hedging, which mechanically sells after rises and buys after falls; the hedged P&L over a short interval is about $\tfrac{1}{2}\Gamma S^2(\sigma_{\text{realized}}^2 - \sigma_{\text{implied}}^2)\Delta t$. It profits when realized volatility exceeds the implied volatility paid; the short-gamma side of the same trade is how the variance risk premium is harvested. **See:** [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md) · [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md)

### GLFT model

The Guéant-Lehalle-Fernandez-Tapia (2013) market-making model, which solves the Avellaneda-Stoikov problem with inventory limits and gives closed-form asymptotic quotes whose skew is linear in inventory and no longer depends on time to a terminal date. It is the usual starting point for production quote-skew logic. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

## H

### Half-life

The expected time for a deviation to decay halfway back to its mean: $\ln 2/\kappa$ for an Ornstein-Uhlenbeck spread with speed $\kappa$, or $-\ln 2/\ln b$ periods for an AR(1) with coefficient $b$. Stat-arb traders use it to filter spreads (keeping those that revert within days to weeks), to set holding periods and to size stop-outs; signal half-life applies the same idea to how fast predictive power fades. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md) · [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md)

### Hard-to-borrow

A stock whose lendable supply is scarce relative to short demand, so the borrow fee rises far above general-collateral rates (tens of basis points a year for easy names, double- or triple-digit percentages in squeezes `[Reported]`) and locates may be unavailable or recalled. Borrow cost and recall risk belong in the backtest of any strategy with a short leg; many anomaly returns concentrate in hard-to-borrow names. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### Hedge ratio

The number of units of one instrument held per unit of another to neutralize a common exposure; in pairs trading, the $\beta$ in the spread $y - \beta x$, estimated by OLS, total least squares or adaptively with a Kalman filter. The choice matters: OLS ratios are asymmetric (regressing y on x differs from x on y) and a stale ratio turns a mean-reverting spread into a directional bet. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md) · [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md)

### High-frequency trading (HFT)

Automated proprietary trading with holding periods from microseconds to minutes, near-flat positions at day end and P&L driven by speed, queue position and microstructure signals rather than fundamental forecasts. Most US equity HFT is market making; the rest is short-horizon directional and arbitrage trading (latency, lead-lag, ETF and index). US equity rules have no formal definition of HFT. **See:** [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md) · [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)

## I

### Implementation shortfall

The difference between the return of a paper portfolio traded at decision prices and the actual portfolio return (Perold, 1988), decomposed into delay, spread, market impact, fees and the opportunity cost of unfilled shares. As an algorithm, "IS" means minimizing expected shortfall plus a risk penalty, which front-loads execution relative to VWAP; Almgren-Chriss is the textbook model. **See:** [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Implied correlation

The average pairwise correlation that reconciles index implied volatility with constituent implied volatilities, $\rho \approx \dfrac{\sigma_I^2 - \sum_i w_i^2\sigma_i^2}{\sum_{i \neq j} w_i w_j \sigma_i \sigma_j}$. It is the price that dispersion traders sell or buy; Cboe publishes implied correlation indexes for the S&P 500. **See:** [Dispersion and correlation trading](../02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md)

### Index arbitrage

Trading index futures against the cash basket (or ETFs) when the futures price deviates from fair value, i.e., spot plus financing minus expected dividends. Today it is an HFT business executed with partial baskets and ETFs; its economic role is to transmit futures-led price discovery into the stocks. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [Lead-lag and cross-asset arbitrage](../02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md)

### Index reconstitution

The periodic change of an index's membership and weights (S&P 500 quarterly rebalances plus ad hoc changes; Russell US indexes annually in June, moving to semi-annual from 2026 `[Reported]`), which forces index funds to trade, mostly in the closing auction of the effective date. Flow-driven strategies pre-position for the predictable demand and supply liquidity on the day; the pure inclusion effect has shrunk sharply since the 1990s (Greenwood and Sammon) `[Reported]`. **See:** [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md) · [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md)

### Information coefficient (IC)

The correlation between a signal's forecasts and subsequent realized returns (IC), usually computed cross-sectionally each period and averaged; Pearson IC uses raw values, rank IC uses ranks. For daily-to-monthly equity signals a mean IC of 0.02-0.05 is useful and anything above 0.10 deserves suspicion of leakage `[Lore]`; IC stability (mean over standard deviation, the "IC IR") matters as much as its level. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

### Information leakage

Other participants inferring the presence of a large order from its footprint (child-order patterns, venue choices, dark-pool pings, conditional firm-ups) and trading ahead of it, raising the parent order's cost. Execution algorithms randomize, cap participation and choose venues to limit it; TCA detects it as adverse price drift during the order beyond what the impact model predicts. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Intermarket sweep order (ISO)

A limit order flagged as exempt from the receiving venue's Reg NMS order-protection checks because the sender has simultaneously routed orders to take out all better-priced protected quotes elsewhere. HFTs and routers use ISOs to execute or post at a new price immediately instead of waiting for the venue to route, which makes ISO usage central to queue-priority and latency debates. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Internalization

A broker-dealer executing customer orders against its own inventory instead of routing them to an exchange; in US equities it mostly means wholesalers filling retail marketable orders at or better than the NBBO. Retail flow is valuable to internalize because it is, on average, uninformed over short horizons, so the internalizer can give price improvement and still earn positive markouts. **See:** [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md) · [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

### Inventory risk

The price risk a market maker bears on positions accumulated through fills until it can offload them; the P&L variance is roughly $q^2\sigma^2\tau$ for inventory $q$ held for time $\tau$. It is controlled by skewing quotes away from the side that would grow inventory, widening, hedging with correlated instruments and hard position limits; with adverse selection it sets the minimum viable spread. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Inverted venue

An exchange with taker-maker pricing: it pays a rebate to liquidity takers and charges liquidity providers, e.g., Cboe BYX and Nasdaq BX `[Reported]`. Posting there costs money but buys priority, because routers that need to take liquidity prefer the venue that pays them; in tick-constrained names inverted venues act as a de facto sub-tick price. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

## K

### Kelly criterion

The position size that maximizes the expected logarithm of wealth; for a continuous strategy with excess return $\mu$ and variance $\sigma^2$ the optimal leverage is $f^* = \mu/\sigma^2$, the Sharpe ratio divided by volatility. Full Kelly implies a 50% chance of halving capital at some point, so practitioners size at a quarter to half Kelly (half Kelly keeps 75% of the growth rate with half the volatility) and treat it as an upper bound given estimation error in $\mu$. **See:** [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md)

### Kill switch

An automated or manual control that immediately cancels a firm's or strategy's open orders and blocks new ones when a limit is breached: position, loss, message rate, or a mismatch between expected and actual positions. Knight Capital's August 2012 malfunction, which lost about $460 million in roughly 45 minutes and led to SEC charges under the Market Access Rule, is the standard case for why it must exist `[Reported]`. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md) · [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

## L

### Latency arbitrage

Profiting from reacting first to public information, typically by picking off stale quotes on one venue after a price move elsewhere (another exchange, or futures) before the quoting firm can cancel. Aquilina, Budish and O'Neill (2022) estimate that such races account for about a fifth of London Stock Exchange volume and act as a tax of roughly 0.4 bp on traded value `[Reported]`. **See:** [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md) · [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

### Lead-lag

A predictable delay between price moves in related instruments, e.g., index futures leading ETFs and constituent stocks, or industry leaders leading followers. At millisecond horizons it drives fair-value updates and latency strategies; at daily horizons (customer-supplier links, industry momentum) it is a slower alpha signal. **See:** [Lead-lag and cross-asset arbitrage](../02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md)

### Ledoit-Wolf shrinkage

A covariance estimator that blends the sample covariance $S$ with a structured target $F$ (scaled identity, constant correlation or a factor model), $\hat\Sigma = \delta F + (1-\delta)S$, with the intensity $\delta$ chosen analytically to minimize expected estimation error (Ledoit and Wolf, 2004). It keeps the matrix well conditioned when stocks outnumber observations and tames the error-maximizing behavior of mean-variance optimizers; their later nonlinear shrinkage adjusts each eigenvalue separately. **See:** [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

### Limit Up-Limit Down (LULD)

The single-stock volatility mechanism, a national market system plan in effect since 2013 `[Reported]`, that blocks trades outside price bands around a rolling five-minute reference price: 5% for Tier 1 stocks (S&P 500, Russell 1000, selected ETPs) and 10% for Tier 2 stocks above $3, wider for low-priced stocks `[Reported]`. If quotes sit at a band for 15 seconds the stock enters a five-minute trading pause and reopens by auction; market-wide circuit breakers (7%, 13% and 20% S&P 500 declines) are a separate mechanism. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [Order types and auctions](../01-market-structure/order-types-and-auctions.md)

### Locate

The Reg SHO Rule 203(b)(1) requirement that, before accepting or effecting a short sale, a broker-dealer have reasonable grounds to believe the shares can be borrowed for delivery, typically from its stock-loan desk or a daily easy-to-borrow list. Bona fide market making is excepted, which matters for market makers' ability to quote two-sided in hard-to-borrow names. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### Look-ahead bias

Using information in a backtest that was not available at decision time: restated fundamentals, index membership known only later, a closing price used to trade at that same close, or features normalized with full-sample statistics. It is the most common reason backtests fail live; the fixes are point-in-time data, explicit timestamps with publication lags, and a lag between signal and execution. **See:** [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Low-volatility anomaly

The finding that low-volatility and low-beta stocks have earned risk-adjusted returns as high as or higher than high-volatility stocks, contrary to the CAPM (Ang, Hodrick, Xing and Zhang, 2006; Frazzini and Pedersen, 2014). Leading explanations are leverage constraints (investors who cannot borrow buy high-beta stocks instead) and lottery preferences; low-volatility portfolios carry large interest-rate and sector exposures. **See:** [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md)

## M

### Maker-taker

The dominant US exchange pricing model: the venue pays a rebate to the order that adds (makes) liquidity and charges a fee to the order that removes (takes) it, keeping the difference. Top-tier rebates have run around $0.002-0.003 per share against take fees at the $0.003 cap `[Reported]`, a meaningful fraction of a one-cent spread in tick-constrained stocks; the 10-mil cap adopted in 2024 would compress this range, but its compliance date is now November 2027 `[Verified]`. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

### Market Access Rule

SEC Rule 15c3-5 (adopted 2010): a broker-dealer that provides market access, including to itself, must run pre-trade risk controls under its direct and exclusive control, covering credit and capital thresholds, erroneous-order checks (price collars, size limits, duplicates) and regulatory requirements, which ended "naked" sponsored access. It is the legal backbone of the risk checks every HFT and execution system applies before an order leaves the building. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Market impact

The price move caused by one's own trading, split into temporary impact (which decays after trading stops) and permanent impact (the information the market infers from the trade). Empirically, the impact of a metaorder grows roughly with the square root of its size relative to daily volume; for institutional-size trades impact, not commissions or spread, is the dominant cost. **See:** [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Market making

Continuously quoting a bid and an offer and earning the spread from counterparties who demand immediacy, while managing inventory and adverse selection. Read as an income statement, revenue is spread capture plus rebates, cost of goods sold is adverse selection and hedging, and operating costs are fees, technology and people. **See:** [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md) · [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Market-on-close (MOC)

An order to buy or sell at the official closing auction price, entered before the exchange's cutoff (3:50 pm ET on the NYSE and Nasdaq, with cancellation restricted afterward `[Reported]`). Index funds and benchmarked managers concentrate rebalancing in MOC orders; limit-on-close orders and imbalance-only order types let liquidity providers join the cross with price protection. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md)

### Markout

The P&L of a fill marked to a later reference price: for a buy at $P$, the markout at horizon $h$ is $M_{t+h} - P$ (sign-flipped for sells), usually in basis points or ticks at horizons from about 100 milliseconds to five minutes. Markout curves by venue, counterparty and order type are the main diagnostic of adverse selection and of whether a flow is worth trading against. **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Mean reversion

The tendency of a price, spread or residual to move back toward an equilibrium after a deviation. In equities it is mainly a property of relative prices (pairs, residuals after removing factor exposure, short-term reversal) rather than of single stock prices, which are close to random walks; the economic source is usually liquidity provision to overreacting or forced traders. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Mean-variance optimization (MVO)

Choosing portfolio weights to maximize expected return minus a risk-aversion penalty on variance, $\max_w\, w^\top\alpha - \tfrac{\lambda}{2} w^\top\Sigma w$, in practice with transaction-cost terms and constraints on factor exposures, positions and turnover. Unconstrained MVO amplifies estimation error (Michaud's "error maximization"), so practitioners shrink alphas and covariances, add constraints and penalties, and solve it as a convex program. **See:** [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md)

### Microprice

An estimate of the efficient price that moves the mid toward the side with less displayed size; the simplest version is the size-weighted mid $\frac{P_b Q_a + P_a Q_b}{Q_a + Q_b}$, while Stoikov's (2018) micro-price is the limit of expected future mids conditional on the current imbalance and spread. It predicts short-horizon mid changes better than the mid and is a standard input to fair value. **See:** [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

### Microwave network

Point-to-point radio links (microwave, and millimeter wave for short hops) between trading centers such as the Chicago futures data center and the New Jersey equity data centers. Signals travel through air at close to the speed of light versus about two-thirds of it in glass fiber, and tower routes can be straighter, cutting one-way latency by roughly a third or more `[Estimate]` (from the propagation-speed ratio alone); rain fade means firms keep fiber backup. **See:** [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

### Midpoint peg

A usually non-displayed order whose price tracks the NBBO midpoint, used to trade inside the spread on exchanges and in dark pools. Mid-peg orders let institutions and algorithms save half the spread without displaying size, but they can be picked off at a stale midpoint when the NBBO moves faster than the venue updates. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Momentum

The tendency of assets that outperformed over the past 3-12 months to keep outperforming over the next few months. In equities the standard signal is the 12-1 month return (skipping the latest month to avoid short-term reversal); Jegadeesh and Titman (1993) reported about 1% a month for 1965-1989 `[Reported]`, with weaker but still positive results in later US data `[Reported]`. **See:** [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Momentum crash

A sudden, severe loss to long-short momentum portfolios, typically when markets rebound sharply after a bear market and the shorted losers (high-beta, beaten-down stocks) rally hardest, as in 1932 and spring 2009 (Daniel and Moskowitz, 2016). Crash risk is partly predictable from bear-market states and high volatility, which motivates volatility-scaled momentum. **See:** [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Multiple testing

The problem that when many signals or strategies are tested, some look significant by chance, so the best of N backtests is biased upward. Corrections include Bonferroni and Holm (family-wise error), Benjamini-Hochberg (false discovery rate), the deflated Sharpe ratio, and the t-statistic hurdle of about 3.0 for new factors proposed by Harvey, Liu and Zhu (2016). **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

## N

### NBBO

National best bid and offer: the highest bid and lowest offer across all exchanges' protected (displayed, round-lot) quotations, disseminated by the SIPs and computed independently by firms from direct feeds. It is the reference for order protection, best execution and price-improvement statistics; since the round-lot redefinition took effect on 2025-11-03, smaller quotes in high-priced stocks count toward it `[Reported]`, while odd-lot and non-displayed liquidity still does not. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md)

### Neutralization

Removing unwanted exposures from a signal or portfolio, e.g., demeaning within industries or regressing out market beta, size and other risk-model factors, so that what remains is the stock-specific (residual) bet. Neutralizing the signal before optimization and constraining exposures inside the optimizer give different portfolios; most mid-frequency books do both. **See:** [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

## O

### Odd lot

An order or trade for fewer shares than a round lot. Odd lots have been around half or more of US equity trades by count in recent years `[Reported]`, especially in high-priced stocks, yet they do not set the NBBO. Under the 2024 Reg NMS amendments the SIPs have disseminated a best odd-lot quote since late April 2026, with odd-lot depth deferred to May 2028 `[Reported]`. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Recent changes (as of 2026-11)](../01-market-structure/recent-changes.md)

### Order-book imbalance

The relative size of resting bid and ask depth at the top of the book (or over several levels), commonly $I = \frac{Q_b - Q_a}{Q_b + Q_a}$ in $[-1, 1]$. It is one of the strongest very-short-horizon predictors of the next mid-price move, especially in tick-constrained stocks, and the input to the microprice; it is a state, whereas order-flow imbalance measures changes. **See:** [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md) · [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

### Order-flow imbalance (OFI)

The net signed change in best-level liquidity over an interval: bid-size increases and ask-size decreases (from new limit orders, cancels and trades) minus the opposite (Cont, Kukanov and Stoikov, 2014). Over short intervals mid-price changes are roughly linear in OFI with a slope inversely proportional to depth, which makes it a staple feature for HFT fair value and short-horizon alpha. **See:** [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

### Ornstein-Uhlenbeck process

The continuous-time mean-reverting process $dX_t = \kappa(\theta - X_t)\,dt + \sigma\,dW_t$, with equilibrium $\theta$, reversion speed $\kappa$ and stationary standard deviation $\sigma/\sqrt{2\kappa}$. Stat-arb models fit it (as a discrete AR(1)) to spreads or cumulative residuals to obtain the half-life and the s-score used for entries and exits. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

## P

### P&L attribution

Decomposing realized profit and loss into its sources: factor versus specific return for a neutral book; alpha capture versus spread, impact, fees and borrow for a mid-frequency strategy; spread capture, rebates, adverse selection, inventory and hedging for a market maker. Daily attribution is how firms catch decaying signals, broken hedges and cost overruns before they show up as drawdowns. **See:** [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md)

### Pairs trading

Trading two related stocks against each other when their spread deviates from its usual level: short the rich leg, buy the cheap one, unwind when the spread reverts. Gatev, Goetzmann and Rouwenhorst (2006) report excess returns of up to about 11% a year for a simple distance method over 1962-2002, declining over time `[Reported]`; modern versions use cointegration, factor-residual spreads and baskets rather than single pairs. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Parent order

The full order a portfolio manager or optimizer wants executed (e.g., buy 400,000 shares by the close), which an execution algorithm slices into many child orders sent to venues over time. TCA is measured at the parent level; child-level fills, venues and prices are the inputs to routing and impact models. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md)

### Participation rate

The fraction of market volume an execution algorithm accounts for while it trades; at 10% it buys one share for every nine traded by others. Percentage-of-volume (POV) algorithms hold the rate constant, typical institutional settings are 5-20% `[Lore]`, and impact models express cost as a function of participation rate and of total size relative to ADV. **See:** [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md) · [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

### Pass-through fees

An arrangement, common at multi-manager hedge funds, in which investors bear the fund's operating costs, including portfolio-manager compensation, data and technology, directly instead of out of a fixed management fee. At the largest platforms these expenses have been reported at several percent of AUM a year `[Reported]`; they fund the talent competition that drives pod-shop economics. **See:** [Economics and revenue pools](../04-industry-and-firms/economics-and-revenue-pools.md)

### Payment for order flow (PFOF)

Compensation a wholesaler pays a retail broker for routing customer orders to it, typically per share or per contract and larger in options than in equities. It is legal in the US subject to Rule 606 routing disclosure and best-execution duties; critics see a conflict of interest, defenders point to price improvement and zero-commission trading. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

### Pod

A semi-independent portfolio-management team at a multi-manager hedge fund (a "pod shop"), which allocates capital to many pods under central risk management, with tight factor-exposure limits and hard drawdown stops, often a capital cut at around a 5% loss and termination at around 7-10% `[Lore]`. Systematic pods running mid-frequency equity strategies are a major employer of quants and a major source of crowding. **See:** [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md) · [Millennium (quant pods)](../04-industry-and-firms/firm-profiles/millennium.md)

### Point-in-time data

Data stored as it was known at each historical moment: original (pre-restatement) fundamentals with their actual release timestamps, historical index constituents, delisted securities and as-of corporate-action adjustments. It is the main defense against look-ahead and survivorship bias; vendors sell point-in-time versions of fundamentals precisely because restated databases inflate backtests. **See:** [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Post-earnings announcement drift (PEAD)

The tendency of prices to keep drifting in the direction of an earnings surprise for weeks after the announcement (Ball and Brown, 1968; Bernard and Thomas, 1989). Surprise is measured as standardized unexpected earnings, surprise versus analyst consensus, or the announcement-window return; the effect has weakened considerably in large US stocks in recent decades `[Reported]`. **See:** [Earnings and event-driven](../02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md)

### Post-only order

A limit order that may only rest on the book: if it would execute on arrival, the venue rejects or reprices it instead. Market makers use post-only to guarantee maker economics (rebate, not fee) and to avoid crossing the spread by accident when their view of the book is stale. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Price improvement

Execution at a better price than the NBBO prevailing when the order arrived, e.g., a retail buy filled at $10.004 against a $10.01 offer. Wholesalers compete for broker flow on price-improvement statistics reported under Rules 605 and 606; its value depends on the benchmark, since the NBBO omits odd-lot and hidden liquidity that was often already better. **See:** [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md) · [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

### Price-time priority

The matching rule used by US equity exchanges: better-priced orders execute first and, at the same price, earlier orders execute first (with displayed orders ahead of non-displayed ones on most venues). It makes queue position a valuable asset in tick-constrained stocks and is why speed of order entry right after a price level forms matters. **See:** [The limit order book](../01-market-structure/the-limit-order-book.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Principal component analysis (PCA)

Decomposing the correlation matrix of returns into orthogonal eigenvectors (eigenportfolios) ranked by the variance they explain; the first is close to the market. In stat arb, the top components serve as statistical factors and the residuals from regressing each stock on them are traded for mean reversion (Avellaneda and Lee, 2010); in risk modeling they complement fundamental factors. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Probability of backtest overfitting (PBO)

The probability that the configuration ranked best in sample ranks below the median out of sample, estimated by combinatorially symmetric cross-validation across all the configurations tried (Bailey, Borwein, López de Prado and Zhu, 2017). A PBO near or above 0.5 means the in-sample winner is no better than a random pick. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Proprietary trading firm

A firm that trades only its own (partners') capital, with no outside investors, e.g., Jane Street, Hudson River Trading, Jump Trading and Tower Research Capital `[Reported]`. Most are market makers and HFTs registered as broker-dealers and exchange members; they keep all profits and disclose little, and their size is bounded by partner capital and clearing-bank leverage. **See:** [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)

### Purged cross-validation

K-fold cross-validation adapted to labels that span time: any training observation whose label interval overlaps the test fold's label intervals is removed ("purged"), usually together with an embargo after the test fold (López de Prado, 2018). Without purging, overlapping labels such as 20-day forward returns leak test information into training and inflate out-of-sample scores. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

## Q

### Quant quake

The August 6-9, 2007 episode in which many quantitative long-short equity funds lost heavily at once with no obvious market-wide trigger; the leading explanation is the rapid unwind of one or more large, crowded quant books, which hit everyone holding similar positions (Khandani and Lo, 2011). It is the reference case for crowding risk in stat arb; the weak factor returns of 2018-2020 are called the "quant winter". **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md) · [Stat arb: overview and history](../02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md)

### Queue position

Where a resting limit order sits among same-priced orders at its level; under price-time priority all shares ahead of it must trade or cancel before it fills. Front-of-queue orders fill more often and with less adverse selection than back-of-queue ones, so in tick-constrained stocks a queue spot has measurable value and market makers model it when deciding to keep, cancel or re-post. **See:** [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

## R

### Rank IC

The Spearman rank correlation between a signal and subsequent returns, computed cross-sectionally each period. It is the default IC in equity research because it is robust to outliers and to the signal's scale and matches how many strategies trade (by rank or quantile); a large gap between Pearson IC and rank IC usually means a few extreme names drive the result. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

### Realized spread

The part of the effective spread a liquidity provider keeps after prices move, $2q(P - M_{t+h})$, with $M_{t+h}$ the midpoint a fixed interval after the trade and $q = +1$ for buyer-initiated trades. Effective minus realized spread is price impact (adverse selection); Rule 605 historically used a five-minute horizon and its amended version, in force since 2026-08-01, uses much shorter ones `[Reported]`. **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Rebate capture

Strategies whose expected profit comes mainly from exchange maker rebates rather than from spread or alpha, e.g., posting passively in low-priced, tick-constrained names where a rebate of a few tenths of a cent is large relative to typical price moves. Their margin is directly exposed to fee-schedule changes and to the pending access-fee cap cut; most firms treat rebates as one line of market-making P&L rather than a strategy in itself. **See:** [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

### Regulation NMS

Regulation National Market System (adopted 2005 `[Reported]`), the SEC framework linking US equity venues: Rule 611 order protection (no trade-throughs of protected quotes), Rule 610 access and fee caps, Rule 612 minimum pricing increments, and the market-data rules behind the SIPs. It created the fragmented, fee-driven, speed-sensitive market that US equity HFT is built around. Its 2024 amendments redefined round lots (in effect since 2025-11-03 `[Reported]`) but their half-cent tick and 10-mil fee cap are delayed to November 2027, and on 2026-06-11 the SEC proposed repealing Rule 611 `[Verified]`. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [NBBO and market data](../01-market-structure/nbbo-and-market-data.md)

### Regulation SHO

The SEC's short-sale regulation (compliance from 2005 `[Reported]`): the locate requirement (Rule 203(b)(1)), mandatory close-out of fails to deliver (Rule 204), threshold-security lists, and the alternative uptick rule (Rule 201, adopted 2010). It sets the costs and constraints of every short leg, from stat-arb shorts to market makers' hedges. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md) · [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

### Reservation price

The price at which a market maker is indifferent between keeping its current inventory and trading one more unit; in the Avellaneda-Stoikov model $r = s - q\gamma\sigma^2(T-t)$. Long inventory lowers it, so both quotes shift down (quote skew), making a sale more likely and a further purchase less likely; production quoters apply the same idea with empirically tuned skew per unit of inventory. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Residual return

The part of a stock's return not explained by its exposures to common factors, $\varepsilon_i = r_i - \beta_i^\top f$; also called idiosyncratic or specific return. Market-neutral strategies aim to forecast and hold only residual return, and a risk model's specific-risk forecast is the variance of this term. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Risk model

A model that forecasts the covariance of returns across thousands of stocks, almost always as a factor model: factor exposures, a factor covariance matrix and specific variances. Commercial models (e.g., MSCI Barra, Axioma, Northfield) and in-house ones feed optimization, neutralization, risk limits and attribution; short-horizon and long-horizon versions can disagree materially about the same book. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Risk parity

Allocating so that each asset or strategy contributes equally to portfolio risk, $w_i(\Sigma w)_i = \tfrac{1}{N}\, w^\top \Sigma w$, rather than equally to capital; with uncorrelated assets it reduces to inverse-volatility weighting. It needs no return forecasts, which makes it robust, but usually requires leverage on low-volatility assets such as bonds. **See:** [Alternatives to MVO](../03-algorithms/d-portfolio-construction/alternatives-to-mvo.md)

### Round lot

The standard trading unit, historically 100 shares for almost all NMS stocks; only round-lot quotes count toward the NBBO and protected quotations. Since 2025-11-03 it has been defined by price tier, 100 shares up to $250, 40 up to $1,000, 10 up to $10,000 and 1 share above `[Reported]`, which brings smaller quotes in high-priced stocks into the NBBO. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Recent changes (as of 2026-11)](../01-market-structure/recent-changes.md)

### Rule 605

The SEC rule requiring monthly public execution-quality reports (effective spread, price improvement, fill rates, speed) for covered orders. The March 2024 amendments, with compliance from 2026-08-01 `[Reported]`, extend it to larger broker-dealers (100,000 or more customers), widen covered orders (including odd lots, fractional shares and more limit orders), add summary reports and shorten the measurement horizons. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

## S

### S-score

The standardized distance of a stock's cumulative residual (after regressing its returns on factors or sector ETFs and fitting an Ornstein-Uhlenbeck process) from its equilibrium, $s = (X - m)/\sigma_{eq}$, used for entries and exits (Avellaneda and Lee, 2010). Their rules open a position beyond about 1.25 and close inside about 0.5-0.75, trading only residuals with fast mean reversion `[Reported]`. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md)

### Sharpe ratio

Mean excess return divided by its standard deviation, usually annualized by multiplying a daily ratio by $\sqrt{252}$, which assumes independent returns; autocorrelated returns (smoothed marks, slow signals) make that scaling wrong (Lo, 2002). Always ask gross or net, backtest or live, and over what period: net figures of 0.5-1.0 for factor strategies and well above 3 for HFT market making are commonly cited `[Lore]`. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Short-term reversal

The tendency of stocks with extreme returns over the past day to month to partly reverse relative to peers over the following days to weeks (Lehmann, 1990; Jegadeesh, 1990). It is compensation for supplying liquidity to traders who demand immediacy, so it is strong gross and fragile net: turnover is high and costs, bid-ask bounce and execution assumptions decide whether it survives. **See:** [Short-term cross-sectional reversal](../02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md)

### SIP

Securities information processor: the consolidator that collects quotes and trades from every exchange and FINRA's trade reporting facilities and disseminates the NBBO and the consolidated tape (the CTA/CQ plans for NYSE- and other-listed Tapes A and B, the UTP plan for Nasdaq-listed Tape C). It is slower than direct feeds because of extra network hops and processing, so latency-sensitive firms build their own consolidated view. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md)

### Smart order routing (SOR)

The logic that decides where, how and in what size to send child orders across 18 registered exchanges, about 33 NMS-stock ATSs and the wholesalers (as of 2026-10 `[Reported]`), using real-time quotes, fees and rebates, historical fill probabilities, latency and venue toxicity. The main design choices are spraying simultaneously versus routing sequentially, posting versus taking, and dark-first versus lit-first. **See:** [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Speed bump

A deliberate delay applied to incoming orders or messages, e.g., IEX's 350-microsecond delay implemented with coiled fiber, which gives the venue time to reprice pegged orders before latency arbitrageurs can pick them off `[Reported]`. Speed bumps protect resting liquidity on that venue; critics argue delayed quotes should not enjoy Reg NMS protection. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Spoofing

Placing orders with intent to cancel them before execution, to create a false impression of supply or demand and move the price toward one's genuine orders; layering is the multi-level variant. It is expressly prohibited in futures by the Dodd-Frank amendment to the Commodity Exchange Act and prosecuted in securities as manipulation under the Exchange Act; surveillance looks at order-to-trade ratios, cancel timing and the side of subsequent fills. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Spread capture

The part of the quoted spread a market maker earns per round trip before adverse selection and hedging, i.e., the half-spread earned on each passive fill. In tick-constrained large caps the quoted spread is one cent, so gross capture is at most about half a cent per share plus the rebate; profit depends on how much survives the markout. **See:** [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md) · [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Square-root law

The empirical regularity that a metaorder's price impact grows with the square root of its size, $\Delta P/P \approx Y\,\sigma_d\sqrt{Q/V_d}$, with daily volatility $\sigma_d$, daily volume $V_d$ and $Y$ of order one (Tóth et al., 2011; Bouchaud et al., 2018) `[Reported]`. Illustratively, buying 10% of ADV in a stock with 2% daily volatility costs about 0.6% with Y = 1. **See:** [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

### Statistical arbitrage

Market-neutral trading of many small, statistically motivated relative-value bets (pairs, factor residuals, short-term reversal, ML forecasts) held from minutes to weeks, relying on diversification across hundreds or thousands of positions rather than on any single convergence. It originated at Morgan Stanley in the mid-1980s `[Reported]` and is now the generic label for mid-frequency equity market-neutral quant trading. **See:** [Stat arb: overview and history](../02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md)

### Survivorship bias

Overstating backtest performance by using a universe of securities that still exist today, omitting those that were delisted, acquired or went bankrupt. For equities the fix is a point-in-time universe including delisted names and their delisting returns (Shumway, 1997), which matters most for small-cap, value and distress-related signals. **See:** [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

## T

### T+1 settlement

The standard US settlement cycle for most broker-dealer securities trades since 2024-05-28, shortened from T+2 by amendments to SEC Rule 15c6-1 `[Verified]`. It compresses the timelines for allocations and affirmations, stock-loan recalls and FX funding by non-US investors, and moves Reg SHO close-out deadlines earlier. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### Tick size

The minimum price increment for quotes and orders. For US stocks priced at $1 or more it has been one cent since decimalization (2001), codified in Rule 612 (2005). The 2024 amendments add a half-cent increment for tick-constrained stocks (time-weighted average quoted spread of $0.015 or less), but compliance has been postponed to the first business day of November 2027 and the rule is under staff review `[Verified]`. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Tick-constrained stock

A stock whose quoted spread sits at the minimum tick most of the time, typically a liquid, low-to-mid-priced name. Because price cannot improve by less than a tick, competition moves to queue position, fee schedules (inverted venues) and speed; these are the stocks the 2024 half-cent tick targets, which is not in effect as of 2026-11 `[Verified]`. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Tick-to-trade

The time from a market-data packet arriving at a firm's network interface to the resulting order leaving it, the standard internal latency metric for HFT systems. Tuned software systems are typically in the single-digit microseconds and FPGA paths below one microsecond `[Reported]`; the network trip to and from the venue is a separate budget. **See:** [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md) · [Trading and research tech stacks](../05-infrastructure/trading-and-research-tech-stacks.md)

### Time-series momentum

Going long assets whose own past return (typically over 12 months) is positive and short those whose return is negative, regardless of other assets; Moskowitz, Ooi and Pedersen (2012) document it across 58 liquid futures and forward markets. It is the formal name for what trend-following CTAs do, and differs from cross-sectional momentum, which ranks assets against each other. **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md) · [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Trade-through rule

Reg NMS Rule 611, the Order Protection Rule: trading centers must maintain policies that prevent trade-throughs, i.e., executions at a price inferior to a protected quotation displayed on another venue, such as buying at $10.02 while $10.01 is displayed elsewhere. Exceptions such as ISOs let a sender clear better prices itself; it is the rule that forces routing and makes the NBBO binding, and on 2026-06-11 the SEC proposed repealing it `[Verified]`. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

### Trading toward the aim

Gârleanu and Pedersen's (2013) result that, with quadratic trading costs and predictable returns, the optimal policy trades each period only part of the way from the current portfolio toward an "aim" portfolio, itself a weighted average of today's and expected future Markowitz portfolios. It formalizes why persistent signals deserve more weight than fast-decaying ones of equal strength and underlies multi-period construction in many stat-arb books. **See:** [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### Transaction cost analysis (TCA)

Measuring and attributing trading costs: pre-trade (forecast cost and risk of a planned trade), intra-trade (real-time slippage) and post-trade (shortfall versus arrival, VWAP or close, split into spread, impact, timing and fees). Quant firms run TCA to calibrate impact models and choose algorithms and brokers; for the buy side it also documents best execution. **See:** [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Trend following

Systematic strategies that buy assets in uptrends and sell those in downtrends, using moving-average crossovers or breakouts over weeks to a year, mostly in futures across equity indexes, rates, currencies and commodities, with positions scaled by volatility. Returns are positively skewed, concentrated in sustained moves such as 2008 and 2022 `[Reported]`, with long flat or losing stretches in between. **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Turnover

How much of the portfolio is traded per period, usually one-way: half the sum of absolute weight changes, or traded value over gross book, per day or annualized (some firms quote two-way, so ask). Turnover times cost per unit traded is the cost drag: illustratively, 50% daily one-way turnover at 5 bp per trade costs 2.5 bp a day, about 6% a year on gross book. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### TWAP

Time-weighted average price: an execution schedule that trades equal quantities in equal time slices regardless of volume, and the corresponding benchmark. It is simple and predictable, hence easy to detect unless randomized, and is used where volume forecasts are unreliable, e.g., in illiquid names. **See:** [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md)

## V

### Variance risk premium

The difference between risk-neutral (implied) and expected realized variance, $E^Q[\sigma^2] - E^P[\sigma^2]$, which has been persistently positive for equity indexes: implied volatility has usually exceeded subsequently realized volatility (Carr and Wu, 2009) `[Reported]`. Option sellers and short-variance strategies earn it as compensation for crash losses; it is the main structural P&L source of short-volatility and dispersion books. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md)

### Volatility arbitrage

Trading options or variance swaps on a view that implied volatility is mispriced relative to forecast realized volatility, or relative to other points on the surface, while hedging delta so that P&L comes from the volatility difference. In practice it ranges from systematic short-VRP books to relative-value trades along the skew and term structure. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md) · [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md)

### Volatility surface

Implied volatility as a function of strike (or delta) and maturity for one underlying, showing the equity skew (downside puts richer) and the term structure. Options market makers fit a smooth, arbitrage-free parametric surface (e.g., SVI) to quotes and price every option off it; the fitted surface, not individual Black-Scholes prices, is their real fair value. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md) · [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md)

### Volatility targeting

Scaling position size inversely to forecast volatility so the portfolio runs at a constant ex-ante volatility (say 10% a year), $w_t = \sigma^{*}/\hat\sigma_t$. Because volatility is persistent and not matched by higher subsequent returns, it tends to raise Sharpe ratios and cut tail losses for equity and momentum portfolios (Moreira and Muir, 2017), though the out-of-sample benefit is debated (Cederburg et al., 2020). **See:** [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md) · [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### VWAP

Volume-weighted average price: the volume-weighted mean of all trade prices over a period, used both as a benchmark and as an execution algorithm that trades in proportion to a forecast intraday volume curve (U-shaped, with a large share in the close). Because a VWAP benchmark can be matched simply by trading with the crowd, alpha-driven orders are now usually judged against arrival price instead. **See:** [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

## W

### Walk-forward analysis

Repeatedly fitting a model on a historical window and testing it on the next unseen period, rolling or expanding forward, so every out-of-sample point uses only information available at the time. It mimics live deployment and is the standard validation scheme, but it yields a single path and still overfits if many walk-forward variants are tried and only the best is reported. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Wholesaler

An off-exchange market maker that buys retail marketable order flow from brokers and executes it as principal, e.g., Citadel Securities, Virtu, Jane Street and Susquehanna's G1 `[Reported]`. Wholesalers segment retail from institutional flow, offer price improvement and pay PFOF; a handful of them handle the large majority of US retail marketable orders `[Reported]`. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

### Winsorization

Capping extreme values of a signal or return at chosen percentiles (e.g., 1st and 99th) or at a number of standard deviations (e.g., 3) instead of deleting them. It is applied before z-scoring and combining signals so that a few data errors or extreme names do not dominate cross-sectional rankings or regression fits. **See:** [Signal transforms](../03-algorithms/a-data-and-signals/signal-transforms.md)

## Z

### Z-score

A value standardized by subtracting a mean and dividing by a standard deviation; for equity signals usually computed cross-sectionally (each day across stocks, often within industries) after winsorization. Z-scoring puts heterogeneous signals on a common scale before combination; time-series z-scores (against an instrument's own history) are the basis of mean-reversion entry rules such as the s-score. **See:** [Signal transforms](../03-algorithms/a-data-and-signals/signal-transforms.md)

## Sources

<!-- Regulatory statuses (2024 Reg NMS amendment delays, Rule 611 repeal proposal, round lots, odd-lot data, Rule 605,
T+1, best execution, closing-auction and off-exchange shares, venue counts) come from the build's shared facts register.
All journal DOIs below were checked against the Crossref API (2026-11). The SEC, OUP and Wiley URLs could not be fetched
from this session; re-check them with lychee in Phase 9. -->

- [Verified] U.S. Securities and Exchange Commission (2005). "Regulation NMS." Final rule, Release No. 34-51808. <https://www.sec.gov/rules/final/34-51808.pdf> (accessed 2026-11)
- [Verified] U.S. Securities and Exchange Commission (2024). "Regulation NMS: Minimum Pricing Increments, Access Fees, and Transparency of Better Priced Orders." Final rule, Release No. 34-101070. <https://www.sec.gov/files/rules/final/2024/34-101070.pdf> (accessed 2026-11)
- [Verified] U.S. Securities and Exchange Commission (2026-06-11). Temporary exemptive order extending the compliance date for the Rule 610 and 612 amendments, Release No. 34-105656. <https://www.sec.gov/files/rules/exorders/2026/34-105656.pdf> (accessed 2026-11)
- [Verified] U.S. Securities and Exchange Commission (2026-06-11). Proposed rescission of the Rule 611 order protection rule, Federal Register public-inspection document 2026-11997. <https://public-inspection.federalregister.gov/2026-11997.pdf> (accessed 2026-11)
- [Verified] U.S. Securities and Exchange Commission (2023). "Shortening the Securities Transaction Settlement Cycle." Final rule, Release No. 34-96930. <https://www.sec.gov/files/rules/final/2023/34-96930.pdf> (accessed 2026-11)
- [Reported] Harris, L. (2003). *Trading and Exchanges: Market Microstructure for Practitioners.* Oxford University Press. <https://global.oup.com/academic/product/trading-and-exchanges-9780195144703> (accessed 2026-11)
- [Reported] López de Prado, M. (2018). *Advances in Financial Machine Learning.* Wiley. <https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086> (accessed 2026-11)
- [Verified] Grinold, R. (1989). "The fundamental law of active management." *Journal of Portfolio Management* 15(3), 30–37. <https://doi.org/10.3905/jpm.1989.409211> (accessed 2026-11)
- [Verified] Avellaneda, M. & Stoikov, S. (2008). "High-frequency trading in a limit order book." *Quantitative Finance* 8(3), 217–224. <https://doi.org/10.1080/14697680701381228> (accessed 2026-11)
- [Verified] Almgren, R. & Chriss, N. (2001). "Optimal execution of portfolio transactions." *Journal of Risk* 3(2), 5–39. <https://doi.org/10.21314/JOR.2001.041> (accessed 2026-11)
- [Verified] Cont, R., Kukanov, A. & Stoikov, S. (2014). "The price impact of order book events." *Journal of Financial Econometrics* 12(1), 47–88. <https://doi.org/10.1093/jjfinec/nbt003> (accessed 2026-11)
- [Verified] Bailey, D. H. & López de Prado, M. (2014). "The deflated Sharpe ratio: correcting for selection bias, backtest overfitting and non-normality." *Journal of Portfolio Management* 40(5), 94–107. <https://doi.org/10.3905/jpm.2014.40.5.094> (accessed 2026-11)
- [Verified] McLean, R. D. & Pontiff, J. (2016). "Does academic research destroy stock return predictability?" *Journal of Finance* 71(1), 5–32. <https://doi.org/10.1111/jofi.12365> (accessed 2026-11)
- [Verified] Harvey, C. R., Liu, Y. & Zhu, H. (2016). "... and the cross-section of expected returns." *Review of Financial Studies* 29(1), 5–68. <https://doi.org/10.1093/rfs/hhv059> (accessed 2026-11)
- [Verified] Gatev, E., Goetzmann, W. N. & Rouwenhorst, K. G. (2006). "Pairs trading: performance of a relative-value arbitrage rule." *Review of Financial Studies* 19(3), 797–827. <https://doi.org/10.1093/rfs/hhj020> (accessed 2026-11)
- [Verified] Budish, E., Cramton, P. & Shim, J. (2015). "The high-frequency trading arms race: frequent batch auctions as a market design response." *Quarterly Journal of Economics* 130(4), 1547–1621. <https://doi.org/10.1093/qje/qjv027> (accessed 2026-11)
- [Verified] Aquilina, M., Budish, E. & O'Neill, P. (2022). "Quantifying the high-frequency trading 'arms race'." *Quarterly Journal of Economics* 137(1), 493–564. <https://doi.org/10.1093/qje/qjab032> (accessed 2026-11)
- [Verified] Moskowitz, T. J., Ooi, Y. H. & Pedersen, L. H. (2012). "Time series momentum." *Journal of Financial Economics* 104(2), 228–250. <https://doi.org/10.1016/j.jfineco.2011.11.003> (accessed 2026-11)
- [Verified] Gârleanu, N. & Pedersen, L. H. (2013). "Dynamic trading with predictable returns and transaction costs." *Journal of Finance* 68(6), 2309–2340. <https://doi.org/10.1111/jofi.12080> (accessed 2026-11)
- [Verified] Ledoit, O. & Wolf, M. (2004). "Honey, I shrunk the sample covariance matrix." *Journal of Portfolio Management* 30(4), 110–119. <https://doi.org/10.3905/jpm.2004.110> (accessed 2026-11)
