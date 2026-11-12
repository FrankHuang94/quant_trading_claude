# Glossary

> **TL;DR**: 444 terms, 94% of them explained on a strategy or algorithm page. Each entry: a short practitioner definition and a link to the page that explains it. Acronyms are expanded on the [acronyms](acronyms.md) page.

**Jump to:** [0-9](#0-9) · [A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [F](#f) · [G](#g) · [H](#h) · [I](#i) · [J](#j) · [K](#k) · [L](#l) · [M](#m) · [N](#n) · [O](#o) · [P](#p) · [Q](#q) · [R](#r) · [S](#s) · [T](#t) · [U](#u) · [V](#v) · [W](#w) · [Z](#z)

Confidence tags follow the KB convention: `[Verified]` primary source · `[Reported]` credible secondary source · `[Estimate]` derived · `[Lore]` widely repeated, unverified. Regulatory status is as of 2026-11.

<!--
Maintainer notes (keep this structure when growing the glossary to 400+ terms):
- One "### Term" heading per term, under "## <Letter>" sections ("## 0-9" for terms starting with a digit), alphabetical within each letter.
  New entries: 20-40 words plus the See line. If a heading cannot produce a linked anchor, append an explicit id: "### Term {#anchor}".
- Headings are plain ASCII, singular, no en dashes; acronym in parentheses where natural.
  The anchor is the Python-Markdown slug of the heading, e.g. "Order-flow imbalance (OFI)" -> order-flow-imbalance-ofi.
  Renaming a heading breaks inbound links: run `python scripts/check_glossary_links.py --missing` after any rename.
- Every entry ends with "**See:**" and at least one relative link to the explaining page.
  Strategy and algorithm terms must link a page in 02-strategies or 03-algorithms first.
- Keep the Jump-to line in sync with the letters that exist.
- Avoid "-$" or "($" before a dollar amount in a paragraph that contains another "$": arithmatex will read it as math.
- Regulatory statuses come from the build's shared facts register; update them in one pass when rules change.
-->

## 0-9

### 0DTE

Options that expire on the day they trade, mostly S&P 500 index options now listed for every weekday. They were a record 66.2% of SPX volume in July 2026 `[Verified]`; whether dealers' same-day gamma hedging amplifies intraday moves is debated. **See:** [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md) · [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md) · [Intraday patterns and seasonality](../02-strategies/c-statistical-arbitrage/intraday-patterns-and-seasonality.md)

## A

### Access fee

The fee an exchange charges to execute against a resting quote. Reg NMS Rule 610(c) has capped it at \$0.003 per share (30 mils) for protected quotes in stocks at \$1 or more since 2005. The 2024 amendments cut the cap to \$0.001, but compliance is postponed to the first business day of November 2027 (SEC order of 2026-06-11) and staff will review Rule 610(c), so 30 mils still applies as of 2026-11 `[Verified]`. Because rebates are funded from take fees, the cap bounds the whole maker-taker economy. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

### Accruals

The non-cash part of earnings: net income minus operating cash flow. Sloan (1996) found high-accrual firms subsequently underperform because investors overweight the accrual component; a staple earnings-quality signal. **See:** [Fundamental quant signals](../02-strategies/d-mid-frequency-alpha/fundamental-quant-signals.md) · [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md)

### Ack latency

The time between sending an order and receiving the exchange's acknowledgment. It determines how quickly a firm knows its queue position and limits how fast it can safely react. **See:** [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md) · [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)

### ADR

American depositary receipt: a US-listed certificate for shares of a foreign company, convertible through a depositary bank. Its fair value is the home-market price times the exchange rate, so ADR-versus-home gaps are a classic lead-lag and arbitrage trade. **See:** [Lead-lag and cross-asset arbitrage](../02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md) · [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md)

### Adverse selection

The loss a liquidity provider suffers because the counterparties who choose to trade against its quotes are, on average, better informed about the next price move, so fills are systematically followed by prices moving against it. Market makers measure it with markouts and manage it by skewing, widening or pulling quotes when short-horizon signals turn against them; in liquid large caps it typically consumes most of the gross half-spread `[Lore]`. **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Aim portfolio

In Gârleanu-Pedersen, the target a trader moves toward: a weighted average of the current and expected future cost-free optimal portfolios. Trading goes partway toward it each period. **See:** [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### Alert fatigue

When monitoring raises so many alerts that real ones get ignored. Countered with calibrated alert bands, severity tiers and pruning of alerts nobody acts on. **See:** [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md)

### Algo wheel

A broker-allocation system that assigns orders randomly or by rule among competing broker algorithms, so their performance can be compared fairly in transaction cost analysis. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Almgren-Chriss model

The canonical optimal-execution model (Almgren and Chriss, 2001): choose the trading trajectory that minimizes expected cost plus $\lambda$ times the variance of cost, given linear temporary and permanent impact. The solution front-loads trading more the higher the risk aversion, $x(t) = X\,\sinh(\kappa(T-t))/\sinh(\kappa T)$ with $\kappa \approx \sqrt{\lambda\sigma^2/\eta}$, and traces a cost-versus-risk efficient frontier that underlies most implementation-shortfall algorithms. **See:** [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Alpha

Return beyond what a portfolio's factor exposures explain: the intercept of a factor regression, so it shrinks as the model adds factors. To a quant, "an alpha" is also a single signal that forecasts residual return. **See:** [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md) · [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md)

### Alpha combination

The step that merges many individual signals into one expected-return forecast per stock, by equal or IC-weighted averaging, regression on forward returns (usually ridge-regularized) or tree and neural ensembles. The hard parts are correlated signals, unstable weights and leakage in the combination step itself, which is why combination weights are fit with purged, walk-forward validation like any other model. **See:** [Alpha combination and ensembling](../03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md)

### Alpha decay

Two related meanings: (1) how fast a signal's predictive power fades with horizon after it is formed (its information half-life), and (2) the erosion of a strategy's edge over calendar time as competitors find it. On the second, McLean and Pontiff (2016) found anomaly returns about 26% lower out of sample and 58% lower after publication `[Reported]`. **See:** [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

### Alpha scaling

Turning a standardized signal into an expected return, alpha = IC × volatility × score (Grinold), so the optimizer weighs returns of the right size against risk and costs. **See:** [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md) · [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

### Alternative data

Non-traditional datasets used to forecast fundamentals or flows before they reach prices or filings: card-transaction panels, web traffic and app usage, satellite and geolocation data, job postings, shipping and supply-chain records. The edge is usually nowcasting a reported metric (revenue, same-store sales) a few weeks early; the costs are licensing, short histories, panel drift and legal review of how the data was collected. **See:** [Alternative data](../02-strategies/d-mid-frequency-alpha/alternative-data.md)

### Alternative trading system (ATS)

A broker-dealer-operated venue registered under Regulation ATS rather than as an exchange. NMS-stock ATSs, most of them dark pools, file public Form ATS-N disclosures on order types, segmentation and who can interact with whom, and their quotes are not protected under Reg NMS. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

### Alternative uptick rule

Reg SHO Rule 201 (adopted 2010): once a stock falls 10% or more from the prior day's close, short sales may be executed only at a price above the current national best bid for the rest of that day and the whole next day `[Reported]`. Short-side strategies and hedges must switch to passive, above-the-bid execution while the restriction is on, which changes both fill rates and adverse selection. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### Amihud illiquidity

Amihud's (2002) price-impact proxy: the average of absolute daily return divided by dollar volume over a window. Higher values mean thinner trading; it serves as a liquidity feature, a universe filter and a rough cost-model input. **See:** [Feature engineering](../03-algorithms/a-data-and-signals/feature-engineering.md)

### Arrival price

The midquote at the moment a parent order reaches the trader or algorithm, used as the benchmark for implementation shortfall. Slippage versus arrival captures delay, spread, impact and opportunity cost in one number and cannot be gamed by trading with the crowd, which is why buy-side TCA has largely moved from VWAP to arrival-price benchmarks. **See:** [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### As-of join

Attaching to each decision time the latest record known at that time, keyed on knowledge timestamps rather than period dates (pandas `merge_asof`). The basic operation for building point-in-time datasets without look-ahead. **See:** [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Auction imbalance

The excess of buy over sell interest (or the reverse) at the indicative clearing price of an opening or closing auction, published by the listing exchange in the minutes before the cross (from 3:50 pm ET for the NYSE and Nasdaq closes `[Reported]`). Liquidity providers trade against published imbalances with offsetting closing orders and unwind later, earning a premium for warehousing overnight gap risk. **See:** [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Augmented Dickey-Fuller test

A unit-root test that regresses a series' changes on its lagged level and lagged changes. Rejecting the unit root means the series is stationary, the property spread traders need; for cointegration residuals the critical values are more negative. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Authorized participant

A broker-dealer (AP) with a contractual agreement with an ETF issuer that lets it create and redeem ETF shares in creation-unit size, usually in kind against a basket of the underlying securities. APs are the conduit for ETF arbitrage; market makers that are not APs arbitrage through one. **See:** [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md) · [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md)

### Autoencoder

A neural network trained to compress inputs into a small latent code and reconstruct them. Conditional autoencoder models (Gu, Kelly and Xiu, 2021) learn latent factors and betas from stock characteristics. **See:** [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md)

### Avellaneda-Stoikov model

The 2008 market-making model in which a dealer with exponential utility quotes around a reservation price $r = s - q\gamma\sigma^2(T-t)$ that shifts against inventory $q$, with total spread $\gamma\sigma^2(T-t) + \tfrac{2}{\gamma}\ln(1+\gamma/k)$, where $k$ describes how fast fill intensity decays with distance from the mid. In practice it is the template for inventory skew rather than a production quoter; the GLFT model removes its finite-horizon artifacts. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Average daily volume (ADV)

Mean shares or dollars traded per day over a trailing window, often 20 days. The basic liquidity yardstick: order sizes, participation caps, impact models and universe filters are all stated as fractions of ADV. **See:** [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md) · [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md) · [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md)

## B

### Backfill bias

Inflated history from data added after the fact: a vendor reconstructing pre-launch history with today's knowledge, or funds joining a database only after a good start. The fix is to use data exactly as originally delivered. **See:** [Alternative data](../02-strategies/d-mid-frequency-alpha/alternative-data.md) · [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Backtest

A simulation of a strategy on historical data, applying its signals, portfolio construction, costs and fills as of each date. Always optimistic; its value depends on the realism of fills, costs and data timing. **See:** [Backtesting engines](../03-algorithms/c-validation-and-backtesting/backtesting-engines.md) · [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md)

### Backwardation

A futures curve in which nearer contracts trade above later ones, so a long position earns positive roll yield if the curve does not change. The opposite of contango; common in commodities when current supply is tight. **See:** [Carry and cross-asset risk premia](../02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md)

### Basis

The difference between a futures (or other derivative) price and the price of its underlying, $F - S$; the fair basis for an equity index future is the net carry, roughly $S\,(e^{(r-q)T} - 1)$ with financing rate $r$ and dividend yield $q$. Index arbitrageurs trade deviations of the actual basis from fair value net of financing, dividend uncertainty and execution costs; in liquid index futures such deviations are small and short-lived `[Lore]`. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md)

### Bayesian Sharpe ratio

An estimate of a strategy's true Sharpe that combines its live record with a prior, typically a backtest Sharpe haircut for overfitting, updated as live data arrive. **See:** [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md)

### Best execution

A broker's duty to seek the most favorable terms reasonably available for a customer order, codified for FINRA members in Rule 5310 with a "regular and rigorous" review of execution quality across venues. It is what makes routing, PFOF and internalization decisions reviewable and why brokers buy TCA. The SEC's December 2022 proposal for its own Regulation Best Execution was withdrawn on 2025-06-12 `[Reported]`, so FINRA's rule remains the operative standard. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

### Beta

The sensitivity of an asset's return to a factor, usually the market: the slope of a regression of stock on index returns. Beta 0.9 implies a 0.9% expected move per 1% market move; market-neutral books target net beta near zero. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md) · [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

### Beta neutral

A long-short portfolio whose net exposure to the market factor (the sum of position value times beta) is zero, as opposed to dollar neutral (equal long and short dollars). A dollar-neutral book long low-beta utilities and short high-beta tech is net short the market; most equity market-neutral books target both, plus near-zero sector and style exposures, via neutralization or optimizer constraints. **See:** [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

### Betting against beta (BAB)

Frazzini and Pedersen's (2014) factor: long low-beta stocks levered to beta 1, short high-beta stocks delevered to beta 1. Its premium is explained by leverage-constrained investors overpaying for high-beta stocks instead of borrowing. **See:** [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md)

### Bias statistic

A risk-model check: the standard deviation of realized return divided by forecast volatility, across portfolios or over time. Values near 1 mean unbiased forecasts; above 1 means risk was underpredicted, typical in crises and for optimized books. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md) · [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

### Bid-ask bounce

Spurious negative autocorrelation in trade-price returns caused by consecutive trades alternating between the bid and the ask (Roll, 1984). A short-term reversal backtest on last-trade or closing prices harvests this bounce on paper; using midquotes, lagging execution by a bar and charging the spread removes it. **See:** [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Short-term cross-sectional reversal](../02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md)

### Black-Litterman model

A Bayesian method that blends market-implied equilibrium returns with an investor's views, weighted by confidence, to produce stable expected returns for mean-variance optimization. **See:** [Alternatives to MVO](../03-algorithms/d-portfolio-construction/alternatives-to-mvo.md)

### Black-Scholes model

The 1973 option-pricing model that assumes lognormal prices with constant volatility. Traders use it as a quoting convention, translating prices into implied volatility, not as a true description of markets. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md)

### Block trade

A single trade far larger than displayed liquidity, usually negotiated or crossed in a block venue or conditional-order book to avoid leaving footprints in lit markets. **See:** [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md) · [Walkthrough: executing a \$500M buy order](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md)

### Bonferroni correction

The simplest multiple-testing adjustment: divide the significance level by the number of tests. Too conservative when the tests are correlated, as backtest variants usually are. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Borrow fee

The annualized rate a short seller pays to borrow stock, deducted from the interest rebate on its cash collateral. Easy names cost a fraction of a percent; hard-to-borrow names can cost tens of percent `[Lore]`, a cost many backtests omit. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md) · [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

### Breadth

In the fundamental law of active management, the number of independent forecasts (bets) a strategy makes per year. Breadth is overstated whenever bets are correlated: 500 stocks that load on one sector, or a slow signal rebalanced daily, are not 500 or 252 independent bets, which is the main reason fundamental-law IRs are too optimistic. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

### Breakeven cost

The all-in cost per dollar traded at which a strategy's net alpha reaches zero: gross alpha divided by turnover. A quick feasibility and capacity test. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md)

## C

### Cancel-on-disconnect

An exchange session setting that automatically cancels all of a firm's open orders if its connection drops. It stops quotes going stale while a market maker cannot manage them; a standard layer of algorithmic risk controls. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Capacity

The capital a strategy can run before market impact and crowding erode its net returns unacceptably; working definitions include the AUM at which net Sharpe halves or at which the marginal dollar earns zero net alpha. Capacity scales roughly with the liquidity of the names traded times the holding period `[Estimate]` (impact cost grows with trade size relative to volume), which is why HFT is high-Sharpe but small and factor investing low-Sharpe but large. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

### Carry

The return an asset earns if its price does not change: roll yield for futures, the interest differential for currencies, dividend yield net of financing for equities (Koijen, Moskowitz, Pedersen and Vrugt, 2018). Carry strategies go long high-carry and short low-carry assets within or across asset classes; the premium comes with left-skewed, crash-prone returns. **See:** [Carry and cross-asset risk premia](../02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md)

### Central counterparty (CCP)

A clearinghouse that becomes buyer to every seller and seller to every buyer through novation, guaranteeing trades if a member defaults. For US equities it is NSCC, a DTCC subsidiary; members post margin sized to unsettled exposure. **See:** [Life of a stock order](../01-market-structure/life-of-a-stock-order.md)

### Change-point detection

Methods that test whether a series' distribution shifted at some time, such as CUSUM or Bayesian online change-point detection (Adams and MacKay, 2007). Used to flag regime breaks and signal decay. **See:** [Regime detection](../03-algorithms/b-forecasting-models/regime-detection.md) · [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md)

### Child order

One of the many small orders an execution algorithm carves from a parent order and sends to venues over time. Child sizing, pricing and venue choice decide most of an order's market impact and information leakage. **See:** [There is no single algorithm](../03-algorithms/there-is-no-single-algorithm.md) · [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md) · [Life of a stock order](../01-market-structure/life-of-a-stock-order.md)

### Clearly erroneous execution

A trade at a price so far from the market that an exchange may cancel it. Under FINRA Rule 11892, regular-hours trades inside LULD bands are generally not reviewable `[Reported]`, so firms keep their mistakes. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Closing auction

The single-price cross at 4:00 pm ET on each listing exchange that sets the official close used for index valuation, fund NAVs and benchmarks; MOC and LOC orders feed it and imbalances are published from 3:50 pm `[Reported]`. Its share has grown with indexing, from about 3% of dollar volume in 2010 to a record of about 9.4% of notional in Q2 2024, and is far higher on index-rebalance days `[Reported]`. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md)

### Cointegration

Two or more non-stationary price series are cointegrated if some linear combination of them (the spread $y - \beta x$) is stationary, so deviations tend to close. It is tested with Engle-Granger (regress, then run an ADF test on the residuals with adjusted critical values) or Johansen; it is a more useful property for pairs trading than high return correlation, but estimated relationships break often out of sample. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Colocation

Renting rack space for one's servers inside an exchange's matching-engine data center (NYSE in Mahwah, Nasdaq in Carteret and Cboe in Secaucus, all in New Jersey `[Reported]`) so that market data and orders travel meters rather than kilometers. Exchanges equalize cable lengths inside the facility; colocation is table stakes for market making and latency-sensitive strategies, not an edge by itself. **See:** [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

### Combinatorial purged cross-validation (CPCV)

López de Prado's (2018) extension of purged k-fold cross-validation: split the sample into N groups, use every combination of k groups as the test set (with purging and embargo), and stitch the test predictions into many complete backtest paths (N = 6, k = 2 gives 15 splits and 5 paths). Instead of one walk-forward Sharpe ratio you get a distribution of them, which feeds overfitting diagnostics such as PBO. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md) · [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Combinatorially symmetric cross-validation (CSCV)

The procedure behind PBO: split a performance matrix into S time blocks, form every half-and-half train and test combination, and count how often the in-sample winner ranks below median out of sample. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Commodity trading advisor (CTA)

A US regulatory category (registered with the CFTC, member of the NFA) for managers advising on futures, and in practice the industry label for systematic, mostly trend-following futures funds. CTAs matter to equity quants because their de-risking in sharp selloffs flows into index futures and, through index arbitrage, into the underlying stocks. **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Comomentum

Lou and Polk's measure of momentum crowding: the average excess correlation of residual returns among stocks in the winner (or loser) decile. High comomentum flags crowded momentum trading and weaker, more crash-prone subsequent momentum returns. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md) · [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Complex order

A multi-leg options order, such as a spread, straddle or buy-write, executed as one package at a net price on an exchange's complex order book. Market makers use them to quote spreads and to trade risk out without legging risk. **See:** [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

### Condition number

The ratio of a covariance matrix's largest to smallest eigenvalue. A high value means the matrix is nearly singular, so inverting it, as mean-variance optimization does, amplifies noise; shrinkage lowers it. **See:** [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

### Conditional order

A dark-pool order type that rests as a non-binding indication; when the venue finds a potential match it invites the sender to "firm up" with a real order within a short window. Conditionals let a large order sit in many dark pools at once without overfill risk; venues track firm-up rates and penalize participants who use conditionals to fish for information. **See:** [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Consensus estimate

The mean or median of sell-side analysts' forecasts for a metric such as quarterly EPS or revenue. Earnings surprises, revisions and alternative-data nowcasts are all measured against it, so point-in-time consensus history matters. **See:** [Alternative data](../02-strategies/d-mid-frequency-alpha/alternative-data.md) · [Analyst revisions and sentiment](../02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md) · [Earnings and event-driven](../02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md)

### Consolidated Audit Trail (CAT)

The SEC-mandated regulatory database recording every US equity and options order, route, modification and execution with customer identifiers. The SEC issued a concept release on overhauling its cost and scope on 2026-04-16 `[Verified]`. **See:** [Recent changes (as of 2026-11)](../01-market-structure/recent-changes.md) · [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

### Contango

A futures curve in which later contracts trade above nearer ones, so a long rolling position loses if the curve does not change. The normal state of VIX futures, which is why long VIX futures positions bleed. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md) · [Carry and cross-asset risk premia](../02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md)

### Continuous net settlement (CNS)

NSCC's system that nets each member's buys and sells in each security into one delivery or receipt per settlement date, with NSCC as counterparty. Netting shrinks the shares and cash that actually move at DTC. **See:** [Life of a stock order](../01-market-structure/life-of-a-stock-order.md)

### Contrarian strategy

Buying recent losers and selling recent winners. Lo and MacKinlay (1990) showed much of its profit comes from lead-lag effects across stocks rather than from overreaction alone. **See:** [Stat arb: overview and history](../02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md) · [Short-term cross-sectional reversal](../02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md)

### Convolutional neural network (CNN)

A neural network whose filters scan for local patterns across an input grid. In trading it is applied to order-book levels near the touch and, less convincingly, to price-chart images. **See:** [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md)

### Copula

A function that joins marginal distributions into a joint distribution with a chosen dependence structure. Copula pairs rules trade on conditional probabilities instead of spread z-scores. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Corporate action

An event that changes a security's shares or price without a trading decision: splits, dividends, spin-offs, mergers, identifier changes. Pipelines adjust for them through total returns; unadjusted data breaks signals and backtests. **See:** [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Correlation risk premium

The excess of index-option implied correlation over subsequently realized correlation. Dispersion trades earn it by selling index volatility and buying single-stock volatility. **See:** [Dispersion and correlation trading](../02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md)

### Creation and redemption

The primary-market mechanism by which an AP creates ETF shares (delivering a basket of securities or cash and receiving new shares) or redeems them (the reverse), in creation units typically of tens of thousands of shares `[Reported]`. It anchors the ETF price to NAV: when the ETF trades rich, arbitrageurs sell the ETF, buy the basket and create shares to close the position. **See:** [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md) · [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md)

### Creation unit

The fixed block of ETF shares, set by each fund, that an authorized participant creates or redeems against the published basket plus a cash component. Primary-market arbitrage and creation fees work in creation-unit increments. **See:** [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md) · [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md) · [Walkthrough: a day at an ETF market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-etf-market-maker.md)

### Crisis alpha

Trend following's tendency to profit in prolonged crises such as 2008 and 2022, because sustained moves create trends. It fails in sudden V-shaped crashes and reversals. **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Cross-hedge

Hedging a position with a correlated but different instrument, such as an index future against a stock basket. Cheaper and more liquid, it leaves basis risk. **See:** [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md)

### Crowding

Many funds holding the same positions because they run similar signals on similar data, so their exits are correlated. Crowding is measured with short-interest and 13F holdings overlap, borrow costs, factor-return correlations and days-to-cover; it costs little until a deleveraging shock, then produces fast, correlated drawdowns such as the August 2007 quant quake. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

### Custom basket

A creation or redemption basket that differs from the ETF's standard pro-rata basket, allowed under the SEC's 2019 ETF rule with written policies. It lets funds and APs tailor baskets, for example to manage tax lots. **See:** [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md) · [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md)

### CUSUM

Page's (1954) cumulative-sum change detector: add up standardized shortfalls each period, floor the sum at zero, and alarm when it crosses a threshold. It flags persistent decay or regime change faster than rolling averages. **See:** [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md) · [Regime detection](../03-algorithms/b-forecasting-models/regime-detection.md)

## D

### Dark pool

A venue that does not publish quotes, almost always an ATS or a broker's internal crossing engine; orders match at or within the NBBO, often at the midpoint, and print to the tape through a FINRA trade reporting facility. Off-exchange trading passed half of US equity volume in 2025 (50.6%), but ATSs are only about a fifth of it, the rest principal dealers such as wholesalers `[Reported]`. Access rules and segmentation determine how toxic a pool is. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Data snooping

Finding spurious patterns by testing many ideas or variants on the same data and keeping the best. Its symptom is good in-sample results that vanish live; remedies are counting trials, haircutting Sharpe ratios and true holdout data. **See:** [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Days-to-cover

Short interest divided by average daily volume: how many days of normal trading short sellers would need to buy back their positions. A short-crowding gauge used both as a return signal and as a squeeze-risk warning. **See:** [Analyst revisions and sentiment](../02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md)

### Decision price

The price at the moment the portfolio manager decided to trade, the starting benchmark for full implementation shortfall, which then splits into delay, execution and opportunity costs. **See:** [Walkthrough: executing a \$500M buy order](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Deflated Sharpe ratio

Bailey and López de Prado's (2014) test of a Sharpe ratio that corrects for selection across N trials, non-normal returns and track-record length: the probability that the true Sharpe exceeds the maximum Sharpe expected from N skill-less trials. The more configurations tried, the higher the hurdle, so a backtest Sharpe that clears it after 10 trials can fail after 1,000. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Delay cost

The price move between the investment decision and the order's arrival at the trading desk or algorithm. Part of implementation shortfall when it is measured from the decision price. **See:** [Walkthrough: executing a \$500M buy order](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Deleveraging

Cutting gross exposure, voluntarily or because a prime broker or risk limit forces it. When many funds holding similar positions deleverage at once, their selling moves prices against everyone still in the trade, as in August 2007. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md) · [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)

### Delisting return

The return on a stock's final move out of a database through merger, bankruptcy or exchange removal. Missing values bias backtests upward; standard imputation uses −30% for NYSE/Amex (Shumway 1997) and −55% for Nasdaq (Shumway and Warther 1999). **See:** [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Delta

The change in an option's value per unit change in the underlying price, and so the hedge ratio in shares. Options market makers delta-hedge to isolate their volatility exposure. **See:** [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md) · [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md)

### Delta hedging

Neutralizing an option position's first-order exposure to the underlying by trading $-\Delta$ units of the stock, ETF or future. Market makers re-hedge at discrete times or when delta drifts outside a band, trading hedge costs against tracking error; what remains is gamma, theta and vega P&L. **See:** [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md) · [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md)

### Depth of book

Resting orders beyond the best bid and offer, by price level or order by order. Exchanges sell it on direct feeds while the SIP carries only top of book; it feeds microprice, imbalance and queue-position models. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

### Designated market maker (DMM)

The NYSE successor to the specialist: a firm assigned to each listed stock with obligations to maintain quotes, provide liquidity and run the open, close and reopenings (including manual price setting), in return for parity allocations and fee benefits. A small number of firms hold the assignments, e.g., Citadel Securities, GTS and Virtu `[Reported]`. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md)

### Direct feed

An exchange's proprietary market-data feed (e.g., Nasdaq TotalView-ITCH, NYSE Integrated, Cboe PITCH) carrying full depth and order-by-order events with lower latency than the SIP. Latency-sensitive firms build their own book and NBBO from direct feeds; the gap between the direct-feed view and the SIP view is the window that latency-arbitrage debates are about. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Dispersion trading

Selling index volatility and buying volatility on the index constituents (or the reverse), with options or variance swaps, to trade the gap between implied and realized correlation. Because index implied correlation has historically exceeded realized `[Reported]`, the short-correlation side earns a premium on average but loses heavily in market-wide selloffs, when correlations jump toward one. **See:** [Dispersion and correlation trading](../02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md)

### Distance method

Gatev, Goetzmann and Rouwenhorst's (2006) pairs rule: choose pairs whose normalized prices tracked most closely in a 12-month formation period, then trade divergences of two standard deviations. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Dollar neutral

A long-short book with equal dollar value long and short, so net dollar exposure is zero. Not the same as beta neutral if the legs' betas differ. **See:** [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

### Drawdown

The decline in cumulative P&L or NAV from its running peak; maximum drawdown is the largest such decline. Funds and pods set drawdown limits that cut risk automatically when breached. **See:** [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

### Dropout

Randomly zeroing a share of a neural network's units during training, so it cannot rely on any single path. A standard regularizer, important when the signal in returns is weak. **See:** [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md)

## E

### Early exercise

Exercising an American option before expiry. Calls are typically exercised just before an ex-dividend date when the dividend exceeds the remaining time value, so option writers face early assignment. **See:** [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

### Early stopping

Halting iterative training, such as boosting rounds or neural-net epochs, when validation error stops improving. In finance the validation set must be a later, purged period; a random split leaks the future. **See:** [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md) · [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Earnings revision

A change in analysts' forecast of a company's earnings. Revisions trend because analysts update gradually and herd, and prices drift after them, so net revision breadth is a standard mid-frequency signal. **See:** [Analyst revisions and sentiment](../02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md)

### Earnings surprise

Reported earnings minus expectations, usually the consensus estimate; scaled versions such as SUE drive post-earnings drift. Revenue and guidance surprises add information beyond EPS. **See:** [Earnings and event-driven](../02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md) · [Analyst revisions and sentiment](../02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md)

### Edge source

The economic reason a strategy should make money: speed, liquidity provision, structural or regulatory, informational, behavioral or risk premium. It predicts a strategy's capacity, decay and failure modes. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Strategies: the map](../02-strategies/index.md)

### Effective number of trials

The number of independent strategies equivalent to a set of correlated backtest variants, estimated by clustering their returns. It is the trial count that multiple-testing corrections such as the deflated Sharpe ratio need. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Effective spread

Twice the signed distance between the execution price and the midpoint prevailing at order arrival, $2q(P - M)$ with $q = +1$ for buys: the cost actually paid, net of any price improvement. Split into realized spread (what the liquidity provider kept) and price impact (what it lost to adverse selection), it is the standard decomposition in Rule 605 reports and microstructure research. **See:** [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md) · [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Eigenportfolio

A portfolio whose weights come from an eigenvector of the stock correlation matrix; the first is roughly the market. Avellaneda and Lee (2010) use the top eigenportfolios as the factors in residual stat arb. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Stat arb: overview and history](../02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md)

### Elastic net

A regression penalty mixing ridge (squared) and lasso (absolute) terms. It combines shrinkage with feature selection and handles groups of correlated features better than lasso alone. **See:** [Linear models and regularization](../03-algorithms/b-forecasting-models/linear-models-and-regularization.md)

### Embargo

A buffer of observations dropped from the training set immediately after each test fold in cross-validation, so that features built on serially correlated data just after the test period cannot leak test information into training. López de Prado (2018) suggests an embargo of about 1% of the sample; it complements purging, which handles overlapping label horizons. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Embedding

A dense numeric vector that a model produces to represent text or another input, placing similar meanings close together. Quants embed filings or news and let their own ridge or tree model learn which directions predict returns. **See:** [LLMs and foundation models in quant](../03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md) · [NLP and LLM signals](../02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md)

### Engle-Granger test

A two-step cointegration test: regress one price on the other, then run an augmented Dickey-Fuller test on the residuals using adjusted critical values. Results depend on which series is the regressand. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Entity resolution

Mapping names, merchants, domains or locations in raw data to the right listed company and security identifier over time. Often the most labor-intensive step in an alternative-data pipeline. **See:** [Alternative data](../02-strategies/d-mid-frequency-alpha/alternative-data.md)

### Epps effect

The fall in measured correlation between assets as the sampling interval shrinks (Epps, 1979), caused mainly by asynchronous trading and stale prices. Lead-lag estimators sample in event time to avoid it. **See:** [Lead-lag and cross-asset arbitrage](../02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md)

### Equal risk contribution (ERC)

Weights chosen so each asset or strategy contributes the same share of portfolio variance; the general form of risk parity, accounting for correlations. **See:** [Alternatives to MVO](../03-algorithms/d-portfolio-construction/alternatives-to-mvo.md) · [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md)

### Error maximization

Michaud's critique that mean-variance optimizers overweight assets whose returns are overestimated and risks underestimated, amplifying estimation error. Shrinkage, constraints and robust methods counter it. **See:** [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### ETF arbitrage

Trading an ETF against its underlying basket (or against correlated futures and ETFs) when the ETF price deviates from its intraday fair value, closing through creation/redemption or by unwinding both legs. In large US equity ETFs the deviations are a few basis points or less and are captured by a handful of market makers within milliseconds `[Lore]`; the economics are in hedge precision and execution cost rather than the raw mispricing. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md)

### ETF premium and discount

The amount by which an ETF trades above (premium) or below (discount) its NAV or fair value. Arbitrage keeps it inside a cost band, but bond ETFs such as LQD hit about a 5% discount in March 2020 `[Reported]`. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md)

### Event-driven backtester

A backtest engine that replays market events in time order through the same code path used live, handling orders, fills and latency. Slower than a vectorized backtest but far more realistic for intraday strategies. **See:** [Backtesting engines](../03-algorithms/c-validation-and-backtesting/backtesting-engines.md)

### Execution algorithm

Software that turns a parent order into child orders across time and venues to minimize cost against a benchmark: schedule-based (VWAP, TWAP, POV), cost-optimizing (implementation shortfall), liquidity-seeking or close-targeting. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md)

### Expanding window

A walk-forward scheme that retrains on all history up to each refit date; a rolling window keeps only the latest N periods. Expanding windows are more stable, rolling ones adapt faster to change. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md) · [Linear models and regularization](../03-algorithms/b-forecasting-models/linear-models-and-regularization.md)

### Exponentially weighted moving average (EWMA)

An average whose weights decay geometrically with the age of each observation, set by a half-life. Used to smooth signals and to estimate volatility and covariance that respond faster than equal-weighted windows. **See:** [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md) · [Signal transforms](../03-algorithms/a-data-and-signals/signal-transforms.md)

## F

### Factor

A common driver of returns shared by many stocks, such as market, industry, size, value or momentum, usually represented by a long-short spread portfolio. Factor models split each return into exposures times factor returns plus a residual. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Factor covariance matrix

The estimated covariance of factor returns in a risk model, usually exponentially weighted with Newey-West adjustments. Combined with exposures and specific risk it gives the risk of any portfolio. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Factor exposure

How much a stock or portfolio loads on a factor: a beta or standardized characteristic per stock, and the holdings-weighted sum for a book. Dollar exposure times the factor's return gives that factor's P&L. **See:** [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Factor model

A model that explains each stock's return as exposures to a small number of common factors plus an idiosyncratic residual, $r = Bf + \varepsilon$, so the covariance matrix becomes $BFB^\top + D$. Factors can be fundamental (industry, size, value, momentum: exposures observed, factor returns estimated by cross-sectional regression), macroeconomic or statistical (PCA); quants use them to forecast risk, neutralize unwanted exposures and attribute P&L. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Factor momentum

The tendency of factors that did well recently to keep doing well. Ehsani and Linnainmaa (2022): the average factor earned 51 bps a month after a winning year versus 6 bps after a losing one `[Verified]`. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

### Factor return

The return attributed to a factor on a date, estimated in fundamental models by a cross-sectional regression of stock returns on exposures. Its time series feeds the factor covariance matrix and P&L attribution. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md) · [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md)

### Factor timing

Varying exposure to factors (value, momentum, low volatility and so on) based on forecasts of their returns from valuation spreads, factor momentum, volatility or macro regimes. The evidence is contested: proponents point to predictable factor volatility and factor momentum, skeptics (e.g., Asness, 2016) to weak out-of-sample results and the turnover cost of timing. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

### Factor zoo

Cochrane's (2011) name for the hundreds of published return predictors. Harvey, Liu and Zhu (2016) argue most are false discoveries and propose t-statistic hurdles near 3; others find most replicate but are redundant. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md) · [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Fair value

In market making and HFT, the firm's real-time estimate of where the price "really" is: the mid adjusted for book imbalance (microprice), recent trade flow, lead-lag signals from futures and ETFs, and sometimes its own inventory. Quotes are placed relative to fair value rather than the displayed mid, and small accuracy gains, fractions of a tick, are much of the edge `[Lore]`. **See:** [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

### False discovery rate

The expected share of false positives among results declared significant. Controlling it, as with the Benjamini-Hochberg-Yekutieli procedure, is less strict than avoiding any false positive and suits screening many signals. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Fama-French factors

Fama and French's factor portfolios: market, size (SMB) and value (HML) in 1993, plus profitability (RMW) and investment (CMA) in 2015, with data in Kenneth French's online library. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md)

### Fama-MacBeth regression

The two-pass procedure (Fama and MacBeth, 1973) that runs a cross-sectional regression of returns on characteristics or exposures each period, then averages the per-period slopes and uses their time-series standard error for inference. It is the workhorse for asking whether a characteristic carries a return premium controlling for others; each period's slope is also the return of a characteristic-mimicking portfolio. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Fat-finger check

A pre-trade control that rejects orders with abnormal size, notional or price relative to recent trading, catching typos and runaway algorithms. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Feature engineering

Turning raw data into model inputs that are scale-free, relative across stocks, robust to outliers and lagged correctly: returns over windows, volatility, liquidity, fundamental ratios. In finance it often matters more than the model choice `[Lore]`. **See:** [Feature engineering](../03-algorithms/a-data-and-signals/feature-engineering.md)

### Feature importance

A ranking of how much each input contributes to a model, by split gain, permutation or SHAP. Correlated substitutes split the credit and can each look unimportant while the pair matters. **See:** [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md)

### Fee tier

Volume-based pricing levels at which exchanges pay higher rebates or charge lower fees. Top tiers reward the largest liquidity providers and shape routing decisions. **See:** [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Feed handler

The component that decodes exchange market-data messages, detects and recovers sequence gaps, and builds order books for the trading logic. In HFT it often runs in FPGA or tuned C++. **See:** [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)

### Fill intensity

The arrival rate of fills as a function of a quote's distance from the mid, typically modeled as $A e^{-k\delta}$. Its parameters set optimal spreads in the Avellaneda-Stoikov and GLFT models. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Fill model

The rules a backtester or simulator uses to decide whether, when and at what price an order executes. Optimistic passive fills that ignore queue position and adverse selection are the classic way market-making backtests mislead. **See:** [Backtesting engines](../03-algorithms/c-validation-and-backtesting/backtesting-engines.md) · [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Fill probability

The probability that a passive limit order executes within a given horizon, as a function of its queue position, the size ahead of it, order-arrival and cancellation rates, and price moves. Fill-probability models decide whether to post or take, at which price and on which venue; fills that do happen are adverse-selected relative to those that do not, so fill probability and markouts are always modeled together. **See:** [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Fire sale

Forced selling by funds facing redemptions or margin calls at prices below fundamental value. The selling is predictable from fund flows and holdings, and prices tend to recover afterward, which flow-driven strategies exploit. **See:** [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md)

### Flash crash

The 2010-05-06 crash and rebound in US stocks and futures, in which some stocks briefly traded at a penny. It led to single-stock circuit breakers and then the LULD bands. **See:** [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md) · [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Flow toxicity

The degree to which order flow is informed, i.e., likely to move prices against the liquidity provider after the trade. Market makers estimate it per counterparty, venue and order type from historical markouts; VPIN (Easley, López de Prado and O'Hara, 2012) is a published volume-bucket measure whose predictive power is disputed (Andersen and Bondarenko, 2014). **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

### Formulaic alpha

A short expression on prices and volumes, such as a rank of 5-day return times volume, used as a trading signal. Kakushadze's (2016) "101 Formulaic Alphas" made the term standard for mass-produced, short-horizon signals. **See:** [Feature engineering](../03-algorithms/a-data-and-signals/feature-engineering.md) · [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

### Foundation model

A large model pretrained on broad data and adapted to many tasks; in quant work, LLMs for text and time-series models pretrained on many series for zero-shot forecasts. Their training data and cutoffs are hard to audit for look-ahead. **See:** [LLMs and foundation models in quant](../03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md)

### FPGA

Field-programmable gate array: a reconfigurable chip on which trading logic (feed parsing, book building, simple decision rules, order encoding) runs directly in hardware. FPGA paths are used where tick-to-trade must be well under a microsecond `[Reported]`; the cost is long development cycles and limited logic, so firms split strategies between fast, simple hardware paths and slower, richer software. **See:** [A semiconductor lens](../05-infrastructure/semiconductor-lens.md) · [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)

### Fractional Kelly

Betting a fraction, often half, of the Kelly-optimal size. It gives up a little growth for a large cut in variance and drawdowns and protects against an overestimated edge. **See:** [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md)

### Frequent batch auction

A market design proposed by Budish, Cramton and Shim (2015) that replaces continuous trading with uniform-price sealed-bid auctions held every fraction of a second (e.g., every 100 ms), so speed advantages smaller than the batch interval stop winning races. It is the leading academic remedy for latency arbitrage; US equity markets have not adopted it. **See:** [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Front-running

Trading ahead of a known pending client order to profit from its impact, which FINRA Rule 5270 prohibits for imminent blocks `[Verified]`. Often misapplied to trading ahead of public, predictable flows such as index rebalances, which is legal. **See:** [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md) · [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md)

### Fundamental factor model

A risk model with observed exposures, such as industry, size, value, momentum and volatility, and factor returns from daily cross-sectional regressions, as in MSCI Barra and Axioma models. Contrast statistical factor models. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Fundamental law of active management

Grinold's (1989) approximation $IR \approx IC \times \sqrt{BR}$: the information ratio of an optimally run active strategy is forecast skill times the square root of breadth, later scaled by a transfer coefficient for constraints (Clarke, de Silva and Thorley, 2002). Its message is that a tiny IC (say 0.02) across thousands of independent bets can give a high IR, but only if the bets really are independent and before costs. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

### FX carry trade

Borrowing in a low-interest currency to invest in a high-interest one, earning the rate differential with crash risk in risk-off episodes such as August 2024. **See:** [Carry and cross-asset risk premia](../02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md)

## G

### Gamma

The rate at which an option's delta changes with the underlying price. A delta-hedged long-gamma position profits from large moves; short gamma earns theta but pays when the stock moves, and its hedging trades with the move. **See:** [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md) · [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md) · [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md)

### Gamma scalping

Holding long options (positive gamma) and repeatedly delta-hedging, which mechanically sells after rises and buys after falls; the hedged P&L over a short interval is about $\tfrac{1}{2}\Gamma S^2(\sigma_{\text{realized}}^2 - \sigma_{\text{implied}}^2)\Delta t$. It profits when realized volatility exceeds the implied volatility paid; the short-gamma side of the same trade is how the variance risk premium is harvested. **See:** [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md) · [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md)

### Garleanu-Pedersen model

Gârleanu and Pedersen's (2013) dynamic trading model with quadratic costs: trade a constant fraction toward an aim portfolio that blends today's optimum with expected future ones, weighting slow-decaying signals more. **See:** [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### General collateral

Stocks that are easy to borrow and lend at the lowest standard fee, covering most large and mid caps; the opposite of hard-to-borrow or "special" names. Fees run about 0.25–0.50% a year `[Lore]`. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### GLFT model

The Guéant-Lehalle-Fernandez-Tapia (2013) market-making model, which solves the Avellaneda-Stoikov problem with inventory limits and gives closed-form asymptotic quotes whose skew is linear in inventory and no longer depends on time to a terminal date. It is the usual starting point for production quote-skew logic. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Gradient boosting

An ensemble that adds shallow decision trees one at a time, each fit to the errors the ensemble still makes and scaled by a small learning rate. LightGBM and XGBoost are the workhorse nonlinear models for tabular return prediction. **See:** [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md)

### Greeks

An option's sensitivities: delta, gamma, vega, theta and rho. Options desks manage risk and explain daily P&L greek by greek. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

### Gross market value (GMV)

The sum of the absolute values of long and short positions, the standard size measure of a long-short book. Turnover, capacity, costs and gross leverage (GMV divided by capital) are quoted against it. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Alternative data](../02-strategies/d-mid-frequency-alpha/alternative-data.md)

### Gross profitability

Revenue minus cost of goods sold, divided by total assets. Novy-Marx (2013) showed it predicts returns about as strongly as book-to-market and is negatively correlated with value, so the two combine well. **See:** [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md) · [Fundamental quant signals](../02-strategies/d-mid-frequency-alpha/fundamental-quant-signals.md)

## H

### Haircut Sharpe ratio

A backtest Sharpe ratio reduced for the number of strategies tried. Harvey and Liu (2015): a Sharpe of 1.0 over 120 months, chosen from 100 tests, falls to 0.438 after a BHY multiple-testing adjustment `[Verified]`. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md) · [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md)

### Half-life

The expected time for a deviation to decay halfway back to its mean: $\ln 2/\kappa$ for an Ornstein-Uhlenbeck spread with speed $\kappa$, or $-\ln 2/\ln b$ periods for an AR(1) with coefficient $b$. Stat-arb traders use it to filter spreads (keeping those that revert within days to weeks), to set holding periods and to size stop-outs; signal half-life applies the same idea to how fast predictive power fades. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md) · [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md)

### Half-spread

Half the quoted bid-ask spread: the cost of crossing from the mid to the far side with a marketable order, and a market maker's gross revenue per share before adverse selection. **See:** [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md) · [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)

### Hallucination

A fluent but false LLM output, such as a misread figure or an invented fact in a filing extraction. Production pipelines validate extracted numbers against structured data before they reach a signal. **See:** [LLMs and foundation models in quant](../03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md)

### Hard-to-borrow

A stock whose lendable supply is scarce relative to short demand, so the borrow fee rises far above general-collateral rates (tens of basis points a year for easy names, double- or triple-digit percentages in squeezes `[Reported]`) and locates may be unavailable or recalled. Borrow cost and recall risk belong in the backtest of any strategy with a short leg; many anomaly returns concentrate in hard-to-borrow names. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### Hedge ratio

The number of units of one instrument held per unit of another to neutralize a common exposure; in pairs trading, the $\beta$ in the spread $y - \beta x$, estimated by OLS, total least squares or adaptively with a Kalman filter. The choice matters: OLS ratios are asymmetric (regressing y on x differs from x on y) and a stale ratio turns a mean-reverting spread into a directional bet. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md) · [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md)

### Hedging band

A no-trade band around the target delta: rehedge only when delta drifts outside it, trading hedge costs against hedging error (Whalley and Wilmott). Bands widen with transaction costs and narrow with risk aversion. **See:** [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

### Hidden Markov model (HMM)

A model in which an unobserved state, such as calm or stressed, switches by a Markov chain and each state draws returns from its own distribution. Filtering gives each day's state probability, used for regime-based risk scaling. **See:** [Regime detection](../03-algorithms/b-forecasting-models/regime-detection.md)

### Hierarchical risk parity (HRP)

López de Prado's (2016) allocation: cluster assets by correlation, order them, then split capital top-down between clusters by inverse variance. It never inverts the covariance matrix. **See:** [Alternatives to MVO](../03-algorithms/d-portfolio-construction/alternatives-to-mvo.md)

### High-frequency trading (HFT)

Automated proprietary trading with holding periods from microseconds to minutes, near-flat positions at day end and P&L driven by speed, queue position and microstructure signals rather than fundamental forecasts. Most US equity HFT is market making; the rest is short-horizon directional and arbitrage trading (latency, lead-lag, ETF and index). US equity rules have no formal definition of HFT. **See:** [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md) · [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)

### Holding P&L

The P&L from positions held at the start of the day, valued as if no trading occurred. Total P&L minus holding P&L is trading P&L, which splits into slippage versus arrival and the later move of traded shares. **See:** [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md)

### Horizon blending

Combining fast and slow signals into one forecast by scaling each to its expected return over the portfolio's trading horizon, so signals with different decay rates are weighted consistently. **See:** [Alpha combination and ensembling](../03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md) · [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### Hot path

The latency-critical code from market-data arrival to order send, kept free of memory allocation, locks, logging and slow models, which run off the path and feed it precomputed values. **See:** [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)

## I

### IC decay

How a signal's information coefficient falls as the forecast horizon lengthens. Its shape sets the natural holding period and how fast the portfolio should trade toward new forecasts. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md) · [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### IC-weighted combination

Weighting signals in a composite by their historical information coefficients, sometimes adjusted for correlation between signals. Simple and robust, it is often competitive with regression-based weights. **See:** [Alpha combination and ensembling](../03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md)

### Iceberg order

A reserve order that displays a small portion and refills from a hidden quantity as the displayed part fills. Each refill usually takes a new timestamp and loses time priority, and repeated refills at one price reveal the order. **See:** [The limit order book](../01-market-structure/the-limit-order-book.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### ICIR

Mean information coefficient divided by the standard deviation of the IC over time, a measure of a signal's consistency. Multiplied by the square root of periods per year, it approximates the annualized IR of a pure signal portfolio. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

### Idiosyncratic volatility

The volatility of a stock's residual return after removing factor exposures. Stocks with high idiosyncratic volatility have earned low subsequent returns (Ang, Hodrick, Xing and Zhang, 2006), part of the low-volatility anomaly. **See:** [Feature engineering](../03-algorithms/a-data-and-signals/feature-engineering.md) · [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md)

### Immediate-or-cancel (IOC)

An order instruction to execute whatever is available at once and cancel the rest, so it never rests on the book. Routers probe dark pools with IOCs; latency arbitrageurs use them to hit stale quotes. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Implementation shortfall

The difference between the return of a paper portfolio traded at decision prices and the actual portfolio return (Perold, 1988), decomposed into delay, spread, market impact, fees and the opportunity cost of unfilled shares. As an algorithm, "IS" means minimizing expected shortfall plus a risk penalty, which front-loads execution relative to VWAP; Almgren-Chriss is the textbook model. **See:** [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Implied correlation

The average pairwise correlation that reconciles index implied volatility with constituent implied volatilities, $\rho \approx \dfrac{\sigma_I^2 - \sum_i w_i^2\sigma_i^2}{\sum_{i \neq j} w_i w_j \sigma_i \sigma_j}$. It is the price that dispersion traders sell or buy; Cboe publishes implied correlation indexes for the S&P 500. **See:** [Dispersion and correlation trading](../02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md)

### Implied volatility

The volatility that, entered into an option-pricing model such as Black-Scholes, reproduces an option's market price. Traders quote and hedge in implied-vol terms because it is comparable across strikes, expiries and underlyings. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

### Index arbitrage

Trading index futures against the cash basket (or ETFs) when the futures price deviates from fair value, i.e., spot plus financing minus expected dividends. Today it is an HFT business executed with partial baskets and ETFs; its economic role is to transmit futures-led price discovery into the stocks. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [Lead-lag and cross-asset arbitrage](../02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md)

### Index inclusion effect

The price rise of a stock added to a major index, driven by index funds' buying around the effective date. Greenwood and Sammon (2025) put the S&P 500 effect at 7.4% in the 1990s and find it has since faded `[Verified]`. **See:** [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md)

### Index reconstitution

The periodic change of an index's membership and weights (S&P 500 quarterly rebalances plus ad hoc changes; Russell US indexes annually in June, moving to semi-annual from 2026 `[Reported]`), which forces index funds to trade, mostly in the closing auction of the effective date. Flow-driven strategies pre-position for the predictable demand and supply liquidity on the day; the pure inclusion effect has shrunk sharply since the 1990s (Greenwood and Sammon) `[Reported]`. **See:** [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md) · [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md)

### Indicative NAV (iNAV)

An intraday estimate of an ETF's per-share basket value disseminated during trading; Rule 6c-11 does not require it `[Verified]`. It is slow, so market makers compute their own fair value from constituent prices, futures and FX. **See:** [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md) · [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md)

### Industry momentum

The tendency of past winning industries to keep outperforming past losers (Moskowitz and Grinblatt, 1999). It accounts for much of individual-stock momentum, so momentum books must decide whether to hedge industry exposure. **See:** [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Information coefficient (IC)

The correlation between a signal's forecasts and subsequent realized returns (IC), usually computed cross-sectionally each period and averaged; Pearson IC uses raw values, rank IC uses ranks. For daily-to-monthly equity signals a mean IC of 0.02-0.05 is useful and anything above 0.10 deserves suspicion of leakage `[Lore]`; IC stability (mean over standard deviation, the "IC IR") matters as much as its level. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

### Information leakage

Other participants inferring the presence of a large order from its footprint (child-order patterns, venue choices, dark-pool pings, conditional firm-ups) and trading ahead of it, raising the parent order's cost. Execution algorithms randomize, cap participation and choose venues to limit it; TCA detects it as adverse price drift during the order beyond what the impact model predicts. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Information ratio

Active or residual return divided by its volatility, annualized: a Sharpe ratio measured against a benchmark. The fundamental law expresses it as IC times the square root of breadth, scaled by the transfer coefficient. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

### Information share

Hasbrouck's (1995) measure of how much of the common efficient-price innovation each market contributes. It identifies which instrument or venue leads price discovery; lead-lag traders use the leader to price the followers. **See:** [Lead-lag and cross-asset arbitrage](../02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md)

### Intermarket sweep order (ISO)

A limit order flagged as exempt from the receiving venue's Reg NMS order-protection checks because the sender has simultaneously routed orders to take out all better-priced protected quotes elsewhere. HFTs and routers use ISOs to execute or post at a new price immediately instead of waiting for the venue to route, which makes ISO usage central to queue-priority and latency debates. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Internalization

A broker-dealer executing customer orders against its own inventory instead of routing them to an exchange; in US equities it mostly means wholesalers filling retail marketable orders at or better than the NBBO. Retail flow is valuable to internalize because it is, on average, uninformed over short horizons, so the internalizer can give price improvement and still earn positive markouts. **See:** [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md) · [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

### Intraday momentum

The tendency of the first half-hour's market return to predict the last half-hour's (Gao, Han, Li and Zhou, 2018); futures traders act on it in the last half-hour. **See:** [Intraday patterns and seasonality](../02-strategies/c-statistical-arbitrage/intraday-patterns-and-seasonality.md)

### Inventory risk

The price risk a market maker bears on positions accumulated through fills until it can offload them; the P&L variance is roughly $q^2\sigma^2\tau$ for inventory $q$ held for time $\tau$. It is controlled by skewing quotes away from the side that would grow inventory, widening, hedging with correlated instruments and hard position limits; with adverse selection it sets the minimum viable spread. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Inventory skew

Shifting both bid and ask against the inventory a market maker holds, lower when long and higher when short, so the next fill is more likely to reduce the position. The practical form of the reservation price. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md) · [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)

### Inverse volatility weighting

Sizing each asset in inverse proportion to its volatility while ignoring correlations; a simple, robust approximation to risk parity used widely by trend followers. **See:** [Alternatives to MVO](../03-algorithms/d-portfolio-construction/alternatives-to-mvo.md) · [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Inverted venue

An exchange with taker-maker pricing: it pays a rebate to liquidity takers and charges liquidity providers, e.g., Cboe BYX and Nasdaq BX `[Reported]`. Posting there costs money but buys priority, because routers that need to take liquidity prefer the venue that pays them; in tick-constrained names inverted venues act as a de facto sub-tick price. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

### Investment factor

Long firms with low asset growth, short firms with high asset growth (CMA in the Fama-French five-factor model). Firms that invest aggressively have subsequently earned lower returns. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md) · [Fundamental quant signals](../02-strategies/d-mid-frequency-alpha/fundamental-quant-signals.md)

## J

### Johansen test

A multivariate cointegration test based on a vector error-correction model. It finds how many cointegrating relationships exist among several series and treats them symmetrically. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Junk rally

A sharp rally led by low-quality, high-beta, heavily shorted stocks, typically after a market bottom. It hurts quality, low-volatility and momentum strategies at the same time. **See:** [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md) · [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

## K

### Kalman filter

A recursive estimator that updates hidden quantities, such as a time-varying hedge ratio or fair value, by blending the prior estimate with each new observation in proportion to their noise. Pairs traders use it for adaptive hedge ratios. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Kelly criterion

The position size that maximizes the expected logarithm of wealth; for a continuous strategy with excess return $\mu$ and variance $\sigma^2$ the optimal leverage is $f^* = \mu/\sigma^2$, the Sharpe ratio divided by volatility. Full Kelly implies a 50% chance of halving capital at some point, so practitioners size at a quarter to half Kelly (half Kelly keeps 75% of the growth rate with half the volatility) and treat it as an upper bound given estimation error in $\mu$. **See:** [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md)

### Kernel bypass

Networking that moves packets directly between the network card and a user-space program, skipping the operating system's kernel stack and the microseconds and jitter it adds. Solarflare Onload and DPDK are common examples; standard in latency-sensitive market making. **See:** [Trading and research tech stacks](../05-infrastructure/trading-and-research-tech-stacks.md) · [How infrastructure constrains algorithms](../05-infrastructure/how-infrastructure-constrains-algorithms.md) · [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)

### Kill criteria

Conditions, written before launch, under which a strategy will be cut or shut down, such as a drawdown or live Sharpe below a threshold. They prevent sunk-cost reasoning. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md)

### Kill switch

An automated or manual control that immediately cancels a firm's or strategy's open orders and blocks new ones when a limit is breached: position, loss, message rate, or a mismatch between expected and actual positions. Knight Capital's August 2012 malfunction, which lost more than \$460 million in roughly 45 minutes and led to SEC charges under the Market Access Rule, is the standard case for why it must exist `[Verified]`. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md) · [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

### Knight Capital incident

On 2012-08-01 a botched deployment woke dead code in Knight's order router, turning 212 retail orders into over 4 million executions in 154 stocks within about 45 minutes and a loss above \$460M `[Verified]`. The template market-access case. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md) · [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)

### Kyle's lambda

The price-impact coefficient in Kyle's (1985) model: how far the price moves per unit of net order flow. Estimated as the slope of price changes on signed flow; thinner books have larger lambda. **See:** [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

## L

### Large language model (LLM)

A transformer neural network trained on vast text to predict the next token, able to read filings, news and transcripts in context. In quant work it scores or embeds text; pretraining look-ahead makes its backtests suspect. **See:** [LLMs and foundation models in quant](../03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md) · [NLP and LLM signals](../02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md)

### Lasso

Linear regression with a penalty on the sum of absolute coefficients, which sets weak coefficients exactly to zero and so selects features. Unstable when features are correlated, where it picks one arbitrarily. **See:** [Linear models and regularization](../03-algorithms/b-forecasting-models/linear-models-and-regularization.md)

### Latency arbitrage

Profiting from reacting first to public information, typically by picking off stale quotes on one venue after a price move elsewhere (another exchange, or futures) before the quoting firm can cancel. Aquilina, Budish and O'Neill (2022) estimate that such races account for about a fifth of London Stock Exchange volume and act as a tax of roughly 0.4 bp on traded value `[Reported]`. **See:** [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md) · [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

### Layering

A form of spoofing: placing several non-bona-fide orders at multiple price levels on one side to fake depth, trading on the other side, then cancelling. Prohibited as manipulation; firms run self-surveillance to catch it. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Lazy prices

Cohen, Malloy and Nguyen's (2020) finding that firms whose 10-K or 10-Q language changes substantially underperform, because investors overlook filing changes. The basis of filing-similarity signals. **See:** [NLP and LLM signals](../02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md)

### Lead market maker (LMM)

The designated liquidity provider for an exchange-listed product, typically an ETF, that accepts quoting obligations in return for exchange fee credits. FINRA Rule 5250 generally bars issuers from paying market makers directly `[Reported]`. **See:** [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md)

### Lead-lag

A predictable delay between price moves in related instruments, e.g., index futures leading ETFs and constituent stocks, or industry leaders leading followers. At millisecond horizons it drives fair-value updates and latency strategies; at daily horizons (customer-supplier links, industry momentum) it is a slower alpha signal. **See:** [Lead-lag and cross-asset arbitrage](../02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md)

### Leakage

Information from the test period or the future entering training or features: overlapping labels, full-sample normalization, revised data, random splits. The most common reason a backtest beats live trading. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Learning rate

The step size by which each boosting round or gradient update changes a model. Smaller rates with more rounds usually generalize better on noisy return data, at higher compute cost. **See:** [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md)

### Ledoit-Wolf shrinkage

A covariance estimator that blends the sample covariance $S$ with a structured target $F$ (scaled identity, constant correlation or a factor model), $\hat\Sigma = \delta F + (1-\delta)S$, with the intensity $\delta$ chosen analytically to minimize expected estimation error (Ledoit and Wolf, 2004). It keeps the matrix well conditioned when stocks outnumber observations and tames the error-maximizing behavior of mean-variance optimizers; their later nonlinear shrinkage adjusts each eigenvalue separately. **See:** [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

### Lee-Ready algorithm

Lee and Ready's (1991) trade classification: a trade above the mid is a buy, below the mid a sell, and at the mid it is signed by the tick rule (direction of the last price change). **See:** [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

### Leveraged ETF rebalancing

Daily leveraged and inverse ETFs must buy after up days and sell after down days, near the close, to reset leverage. The flow is predictable and proportional to the day's move, so it shapes closing auctions and late-day patterns. **See:** [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md) · [Intraday patterns and seasonality](../02-strategies/c-statistical-arbitrage/intraday-patterns-and-seasonality.md)

### Limit order book

A venue's record of all resting buy and sell limit orders, ranked by price and then, on most US venues, by time. Marketable orders consume it from the best price; adds, cancels and trades are the events that change it. **See:** [The limit order book](../01-market-structure/the-limit-order-book.md) · [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md) · [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

### Limit Up-Limit Down (LULD)

The single-stock volatility mechanism, a national market system plan in effect since 2013 `[Reported]`, that blocks trades outside bands around a rolling five-minute reference price: 5% for Tier 1 stocks (S&P 500, Russell 1000, selected ETPs) and 10% for Tier 2 stocks above \$3, wider for low-priced stocks `[Reported]`. Quotes stuck at a band for 15 seconds trigger a five-minute pause and a reopening auction. Market-wide circuit breakers are a separate mechanism. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [Order types and auctions](../01-market-structure/order-types-and-auctions.md)

### Limit-on-close (LOC)

An order to trade in the closing auction only at its limit price or better. Unlike a market-on-close order it cannot be forced through at any price, so it may go unfilled; imbalance traders use LOCs to offset published imbalances. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Limits to arbitrage

Frictions such as capital constraints, noise-trader risk, short-sale costs and leverage limits that let mispricings persist because arbitrageurs cannot bet enough against them (Shleifer and Vishny, 1997). **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md) · [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md)

### Liquidity spiral

A feedback loop in which losses force deleveraging, selling widens prices and raises margins, and that forces more selling (Brunnermeier and Pedersen, 2009). **See:** [Stat arb: overview and history](../02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md) · [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

### Liquidity-seeking algorithm

An execution algorithm that waits for and sweeps block liquidity across dark and lit venues when it appears, rather than following a fixed schedule. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md)

### Locate

The Reg SHO Rule 203(b)(1) requirement that, before accepting or effecting a short sale, a broker-dealer have reasonable grounds to believe the shares can be borrowed for delivery, typically from its stock-loan desk or a daily easy-to-borrow list. Bona fide market making is excepted, which matters for market makers' ability to quote two-sided in hard-to-borrow names. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### Long short-term memory (LSTM)

A recurrent neural network with gates that decide what to keep, forget and output, so it can carry information across many time steps. Applied to order-book event streams and return histories, usually beside simpler baselines. **See:** [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md)

### Look-ahead bias

Using information in a backtest that was not available at decision time: restated fundamentals, index membership known only later, a closing price used to trade at that same close, or features normalized with full-sample statistics. It is the most common reason backtests fail live; the fixes are point-in-time data, explicit timestamps with publication lags, and a lag between signal and execution. **See:** [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Loughran-McDonald dictionary

A finance-specific word list (2011) that classifies words in filings as negative, positive, uncertain or litigious, built because general dictionaries misread terms like "liability". The classic pre-LLM text signal. **See:** [NLP and LLM signals](../02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md) · [LLMs and foundation models in quant](../03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md)

### Low-volatility anomaly

The finding that low-volatility and low-beta stocks have earned risk-adjusted returns as high as or higher than high-volatility stocks, contrary to the CAPM (Ang, Hodrick, Xing and Zhang, 2006; Frazzini and Pedersen, 2014). Leading explanations are leverage constraints (investors who cannot borrow buy high-beta stocks instead) and lottery preferences; low-volatility portfolios carry large interest-rate and sector exposures. **See:** [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md)

## M

### Maker-taker

The dominant US exchange pricing model: the venue pays a rebate to the order that adds (makes) liquidity and charges a fee to the order that removes (takes) it, keeping the difference. Top-tier rebates have run around \$0.002-0.003 per share against take fees at the \$0.003 cap `[Reported]`, a meaningful fraction of a one-cent spread in tick-constrained stocks; the 10-mil cap adopted in 2024 would compress this range, but its compliance date is now November 2027 `[Verified]`. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

### Managed futures

Funds, run by CTAs, that trade futures across asset classes mainly with trend-following signals. Industry assets were about \$354B in Q2 2026 `[Reported]` (BarclayHedge). **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Market Access Rule

SEC Rule 15c3-5 (adopted 2010): a broker-dealer that provides market access, including to itself, must run pre-trade risk controls under its direct and exclusive control, covering credit and capital thresholds, erroneous-order checks (price collars, size limits, duplicates) and regulatory requirements, which ended "naked" sponsored access. It is the legal backbone of the risk checks every HFT and execution system applies before an order leaves the building. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Market depth

How much can trade within a given distance of the mid, for example the shares displayed within k ticks. Large-tick stocks have deep queues at a one-tick spread; small-tick stocks have thin, spread-out books. **See:** [The limit order book](../01-market-structure/the-limit-order-book.md) · [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

### Market impact

The price move caused by one's own trading, split into temporary impact (which decays after trading stops) and permanent impact (the information the market infers from the trade). Empirically, the impact of a metaorder grows roughly with the square root of its size relative to daily volume; for institutional-size trades impact, not commissions or spread, is the dominant cost. **See:** [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Market maker

A firm that continuously posts bids and offers, earning the spread from impatient traders while managing inventory and adverse selection. Electronic market makers do this in thousands of symbols with automated quoting. **See:** [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md) · [There is no single algorithm](../03-algorithms/there-is-no-single-algorithm.md) · [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Market making

Continuously quoting a bid and an offer and earning the spread from counterparties who demand immediacy, while managing inventory and adverse selection. Read as an income statement, revenue is spread capture plus rebates, cost of goods sold is adverse selection and hedging, and operating costs are fees, technology and people. **See:** [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md) · [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Market-on-close (MOC)

An order to buy or sell at the official closing auction price, entered before the exchange's cutoff (3:50 pm ET on the NYSE and Nasdaq, with cancellation restricted afterward `[Reported]`). Index funds and benchmarked managers concentrate rebalancing in MOC orders; limit-on-close orders and imbalance-only order types let liquidity providers join the cross with price protection. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md)

### Market-wide circuit breaker

Halts all US stock trading for 15 minutes when the S&P 500 falls 7% or 13% from the prior close before 3:25 p.m., and for the rest of the day at 20%. Level 1 fired four times in March 2020 `[Verified]`. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md) · [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)

### Markout

The P&L of a fill marked to a later reference price: for a buy at $P$, the markout at horizon $h$ is $M_{t+h} - P$ (sign-flipped for sells), usually in basis points or ticks at horizons from about 100 milliseconds to five minutes. Markout curves by venue, counterparty and order type are the main diagnostic of adverse selection and of whether a flow is worth trading against. **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Markout curve

Average markout plotted against the horizon after fills, from milliseconds to minutes. Its shape separates instant adverse selection from slower information and shows when a fill's P&L should be judged. **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md) · [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)

### Markov decision process (MDP)

The framework for sequential decisions in reinforcement learning: states, actions, transition probabilities and rewards, with the next state depending only on the current state and action. Execution and market making can be cast as MDPs. **See:** [Reinforcement learning in trading](../03-algorithms/g-live-trading/reinforcement-learning-in-trading.md)

### Markov-switching model

Hamilton's (1989) regression or volatility model whose parameters switch between unobserved states that follow a Markov chain. The econometric basis of regime detection. **See:** [Regime detection](../03-algorithms/b-forecasting-models/regime-detection.md)

### Mean reversion

The tendency of a price, spread or residual to move back toward an equilibrium after a deviation. In equities it is mainly a property of relative prices (pairs, residuals after removing factor exposure, short-term reversal) rather than of single stock prices, which are close to random walks; the economic source is usually liquidity provision to overreacting or forced traders. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Mean-variance optimization (MVO)

Choosing portfolio weights to maximize expected return minus a risk-aversion penalty on variance, $\max_w\, w^\top\alpha - \tfrac{\lambda}{2} w^\top\Sigma w$, in practice with transaction-cost terms and constraints on factor exposures, positions and turnover. Unconstrained MVO amplifies estimation error (Michaud's "error maximization"), so practitioners shrink alphas and covariances, add constraints and penalties, and solve it as a convex program. **See:** [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md)

### Merger arbitrage

Buying the target of an announced acquisition, and shorting the acquirer in stock deals, to earn the spread to the deal price. Returns are small and steady until a deal breaks, a payoff resembling a short put. **See:** [Earnings and event-driven](../02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md)

### Microprice

An estimate of the efficient price that moves the mid toward the side with less displayed size; the simplest version is the size-weighted mid $\frac{P_b Q_a + P_a Q_b}{Q_a + Q_b}$, while Stoikov's (2018) micro-price is the limit of expected future mids conditional on the current imbalance and spread. It predicts short-horizon mid changes better than the mid and is a standard input to fair value. **See:** [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

### Microwave network

Point-to-point radio links (microwave, and millimeter wave for short hops) between trading centers such as the Chicago futures data center and the New Jersey equity data centers. Signals travel through air at close to the speed of light versus about two-thirds of it in glass fiber, and tower routes can be straighter, cutting one-way latency by roughly a third or more `[Estimate]` (from the propagation-speed ratio alone); rain fade means firms keep fiber backup. **See:** [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

### Midpoint peg

A usually non-displayed order whose price tracks the NBBO midpoint, used to trade inside the spread on exchanges and in dark pools. Mid-peg orders let institutions and algorithms save half the spread without displaying size, but they can be picked off at a stale midpoint when the NBBO moves faster than the venue updates. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Minimum backtest length

Bailey, Borwein, López de Prado and Zhu's bound on how many years of data are needed before the best of N variants is unlikely to show a given Sharpe ratio by luck. It grows with the number of trials. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Minimum fill quantity

An order condition that executes only against contra orders of at least a set size, protecting block orders from pinging and from many small informed fills. **See:** [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md)

### Minimum variance portfolio

The fully invested portfolio with the lowest forecast variance, needing no return forecasts. Because it depends only on the covariance estimate, it is the standard test of covariance quality. **See:** [Alternatives to MVO](../03-algorithms/d-portfolio-construction/alternatives-to-mvo.md) · [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

### Model retirement

Turning off a signal or model when evidence shows decay, based on rolling IC t-statistics, CUSUM alarms and a diagnosis of the cause, such as crowding, regime or data. **See:** [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md)

### Model-predictive control

Re-solving a multi-period optimization each period with updated forecasts and executing only the first step. A practical way to trade toward a moving target portfolio. **See:** [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### Momentum

The tendency of assets that outperformed over the past 3-12 months to keep outperforming over the next few months. In equities the standard signal is the 12-1 month return (skipping the latest month to avoid short-term reversal); Jegadeesh and Titman (1993) reported about 1% a month for 1965-1989 `[Reported]`, with weaker but still positive results in later US data `[Reported]`. **See:** [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Momentum crash

A sudden, severe loss to long-short momentum portfolios, typically when markets rebound sharply after a bear market and the shorted losers (high-beta, beaten-down stocks) rally hardest, as in 1932 and spring 2009 (Daniel and Moskowitz, 2016). Crash risk is partly predictable from bear-market states and high volatility, which motivates volatility-scaled momentum. **See:** [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Monotone constraint

A restriction forcing a tree model's prediction to rise, or fall, with a feature, encoding economic priors such as "cheaper is better". It reduces overfitting and makes the model easier to defend. **See:** [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md)

### Multi-manager platform

A hedge fund that allocates capital to many independent teams (pods) under central risk limits and tight drawdown stops, netting positions and hedging factor exposure centrally. **See:** [How firms combine strategies](../02-strategies/h-cross-cutting/how-firms-combine-strategies.md) · [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)

### Multilayer perceptron (MLP)

A feed-forward neural network: stacked linear layers with nonlinear activations such as ReLU between them. It learns feature interactions without hand-crafting; cross-sectional MLPs are the standard neural benchmark for stock returns. **See:** [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md)

### Multiple testing

The problem that when many signals or strategies are tested, some look significant by chance, so the best of N backtests is biased upward. Corrections include Bonferroni and Holm (family-wise error), Benjamini-Hochberg (false discovery rate), the deflated Sharpe ratio, and the t-statistic hurdle of about 3.0 for new factors proposed by Harvey, Liu and Zhu (2016). **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

## N

### NBBO

National best bid and offer: the highest bid and lowest offer across all exchanges' protected (displayed, round-lot) quotations, disseminated by the SIPs and computed independently by firms from direct feeds. It is the reference for order protection, best execution and price-improvement statistics; since the round-lot redefinition took effect on 2025-11-03, smaller quotes in high-priced stocks count toward it `[Reported]`, while odd-lot and non-displayed liquidity still does not. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md)

### Nested cross-validation

An outer loop that estimates performance and an inner loop that tunes hyperparameters only on each outer fold's training data, so tuning never touches the test period. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Net asset value (NAV)

The per-share value of a fund's holdings; for ETFs, struck at the close. ETF prices trade around it within an arbitrage band. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md)

### Net trading income

A market maker's top line: trading gains and losses net of hedges, often shown with rebates, fees and interest. Virtu reported \$2,436.7M for 2025 `[Reported]`. **See:** [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md) · [Economics and revenue pools](../04-industry-and-firms/economics-and-revenue-pools.md)

### Netting

Offsetting long and short positions or trades across strategies within one firm, so it trades only the net and saves costs. A main argument for combining signals into one book. **See:** [How firms combine strategies](../02-strategies/h-cross-cutting/how-firms-combine-strategies.md)

### Neutralization

Removing unwanted exposures from a signal or portfolio, e.g., demeaning within industries or regressing out market beta, size and other risk-model factors, so that what remains is the stock-specific (residual) bet. Neutralizing the signal before optimization and constraining exposures inside the optimizer give different portfolios; most mid-frequency books do both. **See:** [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

### Newey-West standard error

A standard error robust to autocorrelation and heteroskedasticity, needed when overlapping returns or persistent signals make observations dependent. Without it, t-statistics on multi-day IC series are badly overstated. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md) · [Linear models and regularization](../03-algorithms/b-forecasting-models/linear-models-and-regularization.md)

### News sentiment

A score of the tone of news about a stock, from dictionaries, vendors or LLMs, usually weighted by relevance and novelty. It predicts returns over roughly a day to a week. **See:** [Analyst revisions and sentiment](../02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md) · [NLP and LLM signals](../02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md)

### No-arbitrage band

The price range around fair value within which arbitrage between an ETF or future and its basket does not pay after fees, spreads, financing and hedging costs. Prices outside it trigger creation, redemption or basket trades. **See:** [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md)

### No-trade region

A band around the target portfolio inside which holding is cheaper than trading, created by proportional costs. It widens with costs and narrows with risk; trades move only to the band's edge. **See:** [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md) · [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md)

### Nonlinear shrinkage

Ledoit and Wolf's method of shrinking each sample eigenvalue by its own amount, instead of pulling the whole matrix toward a single target. It performs better for large universes than linear shrinkage. **See:** [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

### Nonstationarity

Change over time in a series' statistical properties: mean, volatility, correlations. In markets, patterns also change once traded, so models fit on the past degrade; the core reason finance ML needs time-aware validation. **See:** [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md) · [Regime detection](../03-algorithms/b-forecasting-models/regime-detection.md) · [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Nowcasting

Estimating a current-period metric, such as quarterly revenue, before it is reported, from high-frequency data like card spending, web traffic or foot traffic. The core use of alternative data in equities. **See:** [Alternative data](../02-strategies/d-mid-frequency-alpha/alternative-data.md)

## O

### Odd lot

An order or trade for fewer shares than a round lot. Odd lots have been around half or more of US equity trades by count in recent years `[Reported]`, especially in high-priced stocks, yet they do not set the NBBO. Under the 2024 Reg NMS amendments the SIPs have disseminated a best odd-lot quote since late April 2026, with odd-lot depth deferred to May 2028 `[Reported]`. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Recent changes (as of 2026-11)](../01-market-structure/recent-changes.md)

### Opportunity cost

Alpha lost on shares not traded or traded late, one component of implementation shortfall. Trading slowly to cut impact raises it. **See:** [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md) · [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

### Order-book imbalance

The relative size of resting bid and ask depth at the top of the book (or over several levels), commonly $I = \frac{Q_b - Q_a}{Q_b + Q_a}$ in $[-1, 1]$. It is one of the strongest very-short-horizon predictors of the next mid-price move, especially in tick-constrained stocks, and the input to the microprice; it is a state, whereas order-flow imbalance measures changes. **See:** [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md) · [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

### Order-flow imbalance (OFI)

The net signed change in best-level liquidity over an interval: bid-size increases and ask-size decreases (from new limit orders, cancels and trades) minus the opposite (Cont, Kukanov and Stoikov, 2014). Over short intervals mid-price changes are roughly linear in OFI with a slope inversely proportional to depth, which makes it a staple feature for HFT fair value and short-horizon alpha. **See:** [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

### Order-to-trade ratio

The number of orders, modifications and cancels a participant sends per execution. Exchanges cap it or charge for excess messaging, which constrains how often market makers can requote. **See:** [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md) · [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Ornstein-Uhlenbeck process

The continuous-time mean-reverting process $dX_t = \kappa(\theta - X_t)\,dt + \sigma\,dW_t$, with equilibrium $\theta$, reversion speed $\kappa$ and stationary standard deviation $\sigma/\sqrt{2\kappa}$. Stat-arb models fit it (as a discrete AR(1)) to spreads or cumulative residuals to obtain the half-life and the s-score used for entries and exits. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Overlapping returns

Multi-day forward returns sampled every day, so neighboring observations share most of their days. They inflate the apparent sample size and t-statistics; remedies are non-overlapping samples, Newey-West errors and purging. **See:** [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

### Overnight return

The close-to-open return. Lou, Polk and Skouras (2019) find momentum profits accrue overnight while other strategies earn theirs intraday, a "tug of war" between investor clienteles. **See:** [Intraday patterns and seasonality](../02-strategies/c-statistical-arbitrage/intraday-patterns-and-seasonality.md)

## P

### P&L attribution

Decomposing realized profit and loss into its sources: factor versus specific return for a neutral book; alpha capture versus spread, impact, fees and borrow for a mid-frequency strategy; spread capture, rebates, adverse selection, inventory and hedging for a market maker. Daily attribution is how firms catch decaying signals, broken hedges and cost overruns before they show up as drawdowns. **See:** [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md)

### P&L explain

Daily attribution of an options book's P&L to delta, gamma, theta and vega plus a residual. A large unexplained residual signals model, data or booking errors. **See:** [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md) · [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md)

### Pairs trading

Trading two related stocks against each other when their spread deviates from its usual level: short the rich leg, buy the cheap one, unwind when the spread reverts. Gatev, Goetzmann and Rouwenhorst (2006) report excess returns of up to about 11% a year for a simple distance method over 1962-2002, declining over time `[Reported]`; modern versions use cointegration, factor-residual spreads and baskets rather than single pairs. **See:** [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Panel drift

Change over time in who is in an alternative-data sample, such as the users of a card or app, which shifts measured metrics with no change at the company. Panels must be reweighted before nowcasting. **See:** [Alternative data](../02-strategies/d-mid-frequency-alpha/alternative-data.md)

### Paper trading

Running a strategy in real time on live data with simulated orders before committing capital. It exposes data-timing and operational problems a backtest cannot, though not market impact. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Parent order

The full order a portfolio manager or optimizer wants executed (e.g., buy 400,000 shares by the close), which an execution algorithm slices into many child orders sent to venues over time. TCA is measured at the parent level; child-level fills, venues and prices are the inputs to routing and impact models. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md)

### Participation rate

The fraction of market volume an execution algorithm accounts for while it trades; at 10% it buys one share for every nine traded by others. Percentage-of-volume (POV) algorithms hold the rate constant, typical institutional settings are 5-20% `[Lore]`, and impact models express cost as a function of participation rate and of total size relative to ADV. **See:** [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md) · [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

### Pass-through fees

An arrangement, common at multi-manager hedge funds, in which investors bear the fund's operating costs, including portfolio-manager compensation, data and technology, directly instead of out of a fixed management fee. At the largest platforms these expenses have been reported at several percent of AUM a year `[Reported]`; they fund the talent competition that drives pod-shop economics. **See:** [Economics and revenue pools](../04-industry-and-firms/economics-and-revenue-pools.md)

### Payment for order flow (PFOF)

Compensation a wholesaler pays a retail broker for routing customer orders to it, typically per share or per contract and larger in options than in equities. It is legal in the US subject to Rule 606 routing disclosure and best-execution duties; critics see a conflict of interest, defenders point to price improvement and zero-commission trading. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

### Percentage of volume (POV)

An execution algorithm that trades a fixed fraction of market volume as it prints, commonly 5–20% `[Lore]`, so it speeds up when the market is busy. Completion time is uncertain, and it can chase volume its own trading creates. **See:** [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md) · [There is no single algorithm](../03-algorithms/there-is-no-single-algorithm.md)

### Permanent impact

The part of trading's price move that remains after trading ends, read as the information the market infers from the flow. In Almgren-Chriss it is linear in total shares and independent of the schedule. **See:** [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Pin risk

The risk at expiry that the underlying closes near a strike, leaving an option writer unsure whether it will be assigned and what stock position it will hold after the weekend. Desks close or hedge such positions before expiry. **See:** [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md) · [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

### Pinging

Sending small immediate-or-cancel orders to dark venues to detect hidden liquidity. Routers use it to find blocks and predatory traders to find large orders; venues defend with minimum fill sizes. **See:** [Auction, close and dark-liquidity algos](../03-algorithms/e-execution-algorithms/auction-close-and-dark-liquidity-algos.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Pod

A semi-independent portfolio-management team at a multi-manager hedge fund (a "pod shop"), which allocates capital to many pods under central risk management, with tight factor-exposure limits and hard drawdown stops, often a capital cut at around a 5% loss and termination at around 7-10% `[Lore]`. Systematic pods running mid-frequency equity strategies are a major employer of quants and a major source of crowding. **See:** [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md) · [Millennium (quant pods)](../04-industry-and-firms/firm-profiles/millennium.md)

### Point-in-time data

Data stored as it was known at each historical moment: original (pre-restatement) fundamentals with their actual release timestamps, historical index constituents, delisted securities and as-of corporate-action adjustments. It is the main defense against look-ahead and survivorship bias; vendors sell point-in-time versions of fundamentals precisely because restated databases inflate backtests. **See:** [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Policy

In reinforcement learning, the rule that maps each state to an action, or to probabilities over actions, learned to maximize expected cumulative reward. In execution, a policy picks child-order size and price from time and shares left. **See:** [Reinforcement learning in trading](../03-algorithms/g-live-trading/reinforcement-learning-in-trading.md)

### Post-earnings announcement drift (PEAD)

The tendency of prices to keep drifting in the direction of an earnings surprise for weeks after the announcement (Ball and Brown, 1968; Bernard and Thomas, 1989). Surprise is measured as standardized unexpected earnings, surprise versus analyst consensus, or the announcement-window return; the effect has weakened considerably in large US stocks in recent decades `[Reported]`. **See:** [Earnings and event-driven](../02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md)

### Post-only order

A limit order that may only rest on the book: if it would execute on arrival, the venue rejects or reprices it instead. Market makers use post-only to guarantee maker economics (rebate, not fee) and to avoid crossing the spread by accident when their view of the book is stale. **See:** [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Pre-trade cost estimate

A forecast of an order's spread, impact and timing-risk costs before trading, used to choose strategy and horizon and later as a TCA benchmark. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Pre-trade risk check

A test every order must pass before it leaves the firm: size, price collar, notional, position and credit limits, duplicate and message-rate checks. The SEC Market Access Rule requires such controls for broker-dealers with market access. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md) · [Algorithm map](../03-algorithms/algorithm-map.md)

### Pretraining look-ahead

Bias when an LLM used in a backtest was trained on text published after the backtest date, so it may already know the outcomes. Remedies include models with dated training cutoffs and testing only after the cutoff. **See:** [LLMs and foundation models in quant](../03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md) · [NLP and LLM signals](../02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md)

### Price collar

A pre-trade check that rejects orders priced too far from a reference price, such as the NBBO or last trade, keeping an algorithm from sweeping through a thin book. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Price improvement

Execution at a better price than the NBBO prevailing when the order arrived, e.g., a retail buy filled at \$10.004 against a \$10.01 offer. Wholesalers compete for broker flow on price-improvement statistics reported under Rules 605 and 606; its value depends on the benchmark, since the NBBO omits odd-lot and hidden liquidity that was often already better. **See:** [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md) · [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

### Price pressure

Temporary price moves caused by uninformed demand for liquidity, such as index rebalances, fund flows or forced selling, that reverse once the flow ends. Liquidity providers and reversal strategies are paid to absorb it. **See:** [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md) · [Short-term cross-sectional reversal](../02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md)

### Price-time priority

The matching rule used by US equity exchanges: better-priced orders execute first and, at the same price, earlier orders execute first (with displayed orders ahead of non-displayed ones on most venues). It makes queue position a valuable asset in tick-constrained stocks and is why speed of order entry right after a price level forms matters. **See:** [The limit order book](../01-market-structure/the-limit-order-book.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Prime broker

A bank or broker that gives hedge funds financing for longs, stock loan for shorts, custody, clearing and cross-margining. Its margin terms cap leverage, and its crowding reports show how many peers hold the same positions. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md) · [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

### Principal component analysis (PCA)

Decomposing the correlation matrix of returns into orthogonal eigenvectors (eigenportfolios) ranked by the variance they explain; the first is close to the market. In stat arb, the top components serve as statistical factors and the residuals from regressing each stock on them are traded for mean reversion (Avellaneda and Lee, 2010); in risk modeling they complement fundamental factors. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Principal risk bid

A broker's price to take a client's entire block onto its own book at once, transferring execution risk to the broker for a fee. The alternative to working the order as agent through algorithms. **See:** [Walkthrough: executing a \$500M buy order](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md)

### Principal trading firm (PTF)

A firm that trades only its own capital, with no outside clients, such as most electronic market makers and HFT firms. Contrast hedge funds, which manage investors' money, and agency brokers, which execute for clients. **See:** [The big picture](../00-start-here/the-big-picture.md) · [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)

### Pro-rata matching

An allocation rule that splits each incoming order among resting orders at a price in proportion to their size rather than by time. Used in some futures and options markets, it rewards posting size over speed. **See:** [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Probability of backtest overfitting (PBO)

The probability that the configuration ranked best in sample ranks below the median out of sample, estimated by combinatorially symmetric cross-validation across all the configurations tried (Bailey, Borwein, López de Prado and Zhu, 2017). A PBO near or above 0.5 means the in-sample winner is no better than a random pick. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Proprietary trading firm

A firm that trades only its own (partners') capital, with no outside investors, e.g., Jane Street, Hudson River Trading, Jump Trading and Tower Research Capital `[Reported]`. Most are market makers and HFTs registered as broker-dealers and exchange members; they keep all profits and disclose little, and their size is bounded by partner capital and clearing-bank leverage. **See:** [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)

### Protected quote

Under Reg NMS, an automated, displayed, round-lot best bid or offer on a registered exchange that other venues may not trade through. Only protected quotes form the NBBO; hidden orders, odd lots and ATS quotes are unprotected. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Publication decay

The fall in an anomaly's returns after academic publication; McLean and Pontiff (2016) estimate returns about 58% lower post-publication `[Verified]`. **See:** [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md) · [Evolution of quant strategies](../02-strategies/h-cross-cutting/evolution-of-quant-strategies.md)

### Purged cross-validation

K-fold cross-validation adapted to labels that span time: any training observation whose label interval overlaps the test fold's label intervals is removed ("purged"), usually together with an embargo after the test fold (López de Prado, 2018). Without purging, overlapping labels such as 20-day forward returns leak test information into training and inflate out-of-sample scores. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Put-call parity

The no-arbitrage identity for European options: call minus put equals the discounted forward minus the discounted strike, $C - P = Se^{-qT} - Ke^{-rT}$. Market makers invert it to extract the implied forward, which absorbs dividends and borrow. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md) · [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md)

## Q

### Q-learning

A reinforcement-learning method that learns the value Q(s, a) of taking action a in state s and acting optimally afterward, moving each estimate toward reward plus the discounted best next value. Tabular versions suit toy liquidation problems. **See:** [Reinforcement learning in trading](../03-algorithms/g-live-trading/reinforcement-learning-in-trading.md)

### Quality factor

Long profitable, stable, conservatively financed firms and short the reverse, measured by gross profitability, ROE, accruals or leverage (Novy-Marx 2013; Asness, Frazzini and Pedersen 2019). It tends to do well when value suffers. **See:** [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md) · [Fundamental quant signals](../02-strategies/d-mid-frequency-alpha/fundamental-quant-signals.md)

### Quant quake

The August 6-9, 2007 episode in which many quantitative long-short equity funds lost heavily at once with no obvious market-wide trigger; the leading explanation is the rapid unwind of one or more large, crowded quant books, which hit everyone holding similar positions (Khandani and Lo, 2011). It is the reference case for crowding risk in stat arb; the weak factor returns of 2018-2020 are called the "quant winter". **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md) · [Stat arb: overview and history](../02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md)

### Quant winter

A multi-year stretch in which systematic factor strategies, especially value, underperform, as in 2018–2020; assets shrink and some firms close. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

### Quantile portfolio

A portfolio of the stocks in one slice, such as a decile or quintile, of a signal's ranking. A monotonic return pattern across quantiles and the top-minus-bottom spread are standard signal diagnostics. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

### Queue position

Where a resting limit order sits among same-priced orders at its level; under price-time priority all shares ahead of it must trade or cancel before it fills. Front-of-queue orders fill more often and with less adverse selection than back-of-queue ones, so in tick-constrained stocks a queue spot has measurable value and market makers model it when deciding to keep, cancel or re-post. **See:** [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Quote fade

Displayed liquidity disappearing before an order reaches it, because faster traders cancel after seeing related trades elsewhere. Routers time multi-venue sweeps to arrive simultaneously to reduce it. **See:** [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md) · [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Quoted spread

The difference between the best offer and best bid at a moment. Contrast the effective spread, measured on trades against the mid, and the realized spread, measured against a later price. **See:** [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)

## R

### Random forest

An ensemble of deep decision trees, each fit to a bootstrap sample using random subsets of features, whose predictions are averaged to cut variance. A robust baseline beside gradient boosting for tabular return prediction. **See:** [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md)

### Random matrix theory

Results on the eigenvalues of pure-noise correlation matrices, notably the Marchenko-Pastur law. Used to separate signal eigenvalues from noise and to clip the noisy ones when cleaning covariance estimates. **See:** [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

### Rank IC

The Spearman rank correlation between a signal and subsequent returns, computed cross-sectionally each period. It is the default IC in equity research because it is robust to outliers and to the signal's scale and matches how many strategies trade (by rank or quantile); a large gap between Pearson IC and rank IC usually means a few extreme names drive the result. **See:** [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

### Rank transform

Replacing a signal's raw values with their cross-sectional percentile ranks on each date, often mapped to a uniform or normal score. It neutralizes outliers and scale differences but discards information in the magnitudes. **See:** [Signal transforms](../03-algorithms/a-data-and-signals/signal-transforms.md) · [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

### Realized spread

The part of the effective spread a liquidity provider keeps after prices move, $2q(P - M_{t+h})$, with $M_{t+h}$ the midpoint a fixed interval after the trade and $q = +1$ for buyer-initiated trades. Effective minus realized spread is price impact (adverse selection); Rule 605 historically used a five-minute horizon and its amended version, in force since 2026-08-01, uses much shorter ones `[Reported]`. **See:** [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Realized volatility

The volatility actually observed in returns over a period, measured from daily or intraday data. Volatility strategies bet on the gap between implied volatility and subsequent realized volatility. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md) · [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md)

### Rebate capture

Strategies whose expected profit comes mainly from exchange maker rebates rather than from spread or alpha, e.g., posting passively in low-priced, tick-constrained names where a rebate of a few tenths of a cent is large relative to typical price moves. Their margin is directly exposed to fee-schedule changes and to the pending access-fee cap cut; most firms treat rebates as one line of market-making P&L rather than a strategy in itself. **See:** [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

### Reconciliation

Matching a firm's internal positions and P&L daily against broker, clearing and exchange records. Breaks reveal booking errors, missed fills or bad marks. **See:** [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md)

### Regime

A persistent market state, such as calm or stressed, trending or mean-reverting, in which returns, volatility and correlations behave differently. Firms mostly use regime estimates defensively, to scale risk or gate strategies. **See:** [Regime detection](../03-algorithms/b-forecasting-models/regime-detection.md)

### Regularization

Constraining a model to reduce overfitting, through penalties, early stopping, depth limits, dropout or optimizer constraints. Essential in finance, where signal-to-noise is low and independent samples are few. **See:** [Linear models and regularization](../03-algorithms/b-forecasting-models/linear-models-and-regularization.md) · [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md)

### Regulation NMS

Regulation National Market System (adopted 2005 `[Reported]`), the SEC framework linking US equity venues: Rule 611 order protection (no trade-throughs), Rule 610 access and fee caps, Rule 612 minimum ticks, and the market-data rules behind the SIPs. It created the fragmented, fee-driven, speed-sensitive market that HFT is built around. Its 2024 amendments redefined round lots (in effect since 2025-11-03 `[Reported]`), but the half-cent tick and 10-mil fee cap are delayed to November 2027; on 2026-06-11 the SEC proposed repealing Rule 611 `[Verified]`. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [NBBO and market data](../01-market-structure/nbbo-and-market-data.md)

### Regulation SHO

The SEC's short-sale regulation (compliance from 2005 `[Reported]`): the locate requirement (Rule 203(b)(1)), mandatory close-out of fails to deliver (Rule 204), threshold-security lists, and the alternative uptick rule (Rule 201, adopted 2010). It sets the costs and constraints of every short leg, from stat-arb shorts to market makers' hedges. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md) · [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

### Reinforcement learning

Machine learning in which an agent learns a policy by trial and error to maximize cumulative reward instead of predicting labels. Applied to execution, hedging and market making, usually in simulators whose fidelity limits live results. **See:** [Reinforcement learning in trading](../03-algorithms/g-live-trading/reinforcement-learning-in-trading.md)

### Request for quote (RFQ)

A client asks one or more dealers to price a specific size, common for ETF and bond blocks. The winning dealer prices its hedging and inventory cost into the quote. **See:** [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md) · [Walkthrough: a day at an ETF market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-etf-market-maker.md)

### Requote threshold

The minimum change in fair value that makes a market maker cancel and replace its quotes. Too small burns messages and queue position; too large leaves quotes stale to faster traders. **See:** [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md) · [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Reservation price

The price at which a market maker is indifferent between keeping its current inventory and trading one more unit; in the Avellaneda-Stoikov model $r = s - q\gamma\sigma^2(T-t)$. Long inventory lowers it, so both quotes shift down (quote skew), making a sale more likely and a further purchase less likely; production quoters apply the same idea with empirically tuned skew per unit of inventory. **See:** [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

### Residual momentum

Ranking stocks on residual returns after removing factor exposures, rather than on raw returns. Blitz, Huij and Martens (2011) find it about doubles momentum's risk-adjusted profit `[Verified]`, with smaller crashes. **See:** [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Residual return

The part of a stock's return not explained by its exposures to common factors, $\varepsilon_i = r_i - \beta_i^\top f$; also called idiosyncratic or specific return. Market-neutral strategies aim to forecast and hold only residual return, and a risk model's specific-risk forecast is the variance of this term. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Restatement

A company's revision of previously reported financials. A backtest using restated figures trades on numbers nobody had at the time, so point-in-time databases append restatements and keep the originally reported values. **See:** [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md) · [Fundamental quant signals](../02-strategies/d-mid-frequency-alpha/fundamental-quant-signals.md)

### Reward hacking

A reinforcement-learning agent exploiting quirks of its simulator or reward design, such as an unrealistic fill model, instead of learning a real edge. **See:** [Reinforcement learning in trading](../03-algorithms/g-live-trading/reinforcement-learning-in-trading.md)

### Ridge regression

Linear regression with a penalty on the sum of squared coefficients, shrinking them all toward zero. In noisy return data it trades a little bias for a large cut in variance, and amounts to shrinking signal weights toward equal weights. **See:** [Linear models and regularization](../03-algorithms/b-forecasting-models/linear-models-and-regularization.md) · [Alpha combination and ensembling](../03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md)

### Risk aversion

The parameter, usually lambda, that trades off expected return against variance in a portfolio optimizer or execution model. Higher values give smaller, more diversified books, or faster, front-loaded execution schedules. **See:** [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Risk budget

An allocation of total risk, as volatility or VaR, to strategies, pods, factors or positions, each of which is then sized to its budget. **See:** [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md) · [How firms combine strategies](../02-strategies/h-cross-cutting/how-firms-combine-strategies.md)

### Risk model

A model that forecasts the covariance of returns across thousands of stocks, almost always as a factor model: factor exposures, a factor covariance matrix and specific variances. Commercial models (e.g., MSCI Barra, Axioma, Northfield) and in-house ones feed optimization, neutralization, risk limits and attribution; short-horizon and long-horizon versions can disagree materially about the same book. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Risk parity

Allocating so that each asset or strategy contributes equally to portfolio risk, $w_i(\Sigma w)_i = \tfrac{1}{N}\, w^\top \Sigma w$, rather than equally to capital; with uncorrelated assets it reduces to inverse-volatility weighting. It needs no return forecasts, which makes it robust, but usually requires leverage on low-volatility assets such as bonds. **See:** [Alternatives to MVO](../03-algorithms/d-portfolio-construction/alternatives-to-mvo.md)

### Risk premium

Expected return paid for bearing a risk that hurts in bad times, such as equity, value, carry or short-volatility risk. Unlike a mispricing, it should survive publication, because holders still demand pay for the losses. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md) · [The big picture](../00-start-here/the-big-picture.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

### Roll yield

The return from rolling a futures position into the next contract as prices converge toward spot: positive in backwardation, negative in contango. **See:** [Carry and cross-asset risk premia](../02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md) · [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Roll-down

The return a bond or bond-futures position earns as it ages toward a shorter maturity and is revalued on an unchanged, upward-sloping yield curve. With the yield-minus-repo spread, it makes up bond carry. **See:** [Carry and cross-asset risk premia](../02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md)

### Round lot

The standard trading unit, historically 100 shares for almost all NMS stocks; only round-lot quotes count toward the NBBO and protected quotations. Since 2025-11-03 it has been defined by price tier, 100 shares up to \$250, 40 up to \$1,000, 10 up to \$10,000 and 1 share above `[Reported]`, which brings smaller quotes in high-priced stocks into the NBBO. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Recent changes (as of 2026-11)](../01-market-structure/recent-changes.md)

### Rule 605

The SEC rule requiring monthly public execution-quality reports (effective spread, price improvement, fill rates, speed) for covered orders. The March 2024 amendments, with compliance from 2026-08-01 `[Reported]`, extend it to larger broker-dealers (100,000 or more customers), widen covered orders (including odd lots, fractional shares and more limit orders), add summary reports and shorten the measurement horizons. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

### Rule 606

The SEC rule requiring brokers to publish quarterly reports on where they route customer orders and the payment for order flow received per 100 shares. With Rule 605, it lets outsiders audit routing and PFOF. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

## S

### S-score

The standardized distance of a stock's cumulative residual (after regressing its returns on factors or sector ETFs and fitting an Ornstein-Uhlenbeck process) from its equilibrium, $s = (X - m)/\sigma_{eq}$, used for entries and exits (Avellaneda and Lee, 2010). Their rules open a position beyond about 1.25 and close inside about 0.5-0.75, trading only residuals with fast mean reversion `[Reported]`. **See:** [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md)

### Sample covariance matrix

The covariance estimated directly from historical returns. For 3,000 stocks it has about 4.5 million free parameters and is singular unless there are more periods than stocks, so it is never used raw in an optimizer. **See:** [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

### Sector neutral

Zero net exposure to each sector or industry, imposed by demeaning signals within sectors or with optimizer constraints. Sector neutral is not beta neutral. **See:** [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md) · [Signal transforms](../03-algorithms/a-data-and-signals/signal-transforms.md)

### Securities information processor (SIP)

The consolidated-tape processor that collects every exchange's top-of-book quotes and all trades, computes the NBBO and disseminates them under the CTA/CQ and UTP plans. Slower and thinner than exchanges' direct feeds. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Security master

The reference database mapping each security's identifiers (ticker, CUSIP, permanent ID), listing history, share classes and corporate actions over time. Errors such as reused tickers silently corrupt every downstream signal. **See:** [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Seed ensembling

Averaging several neural networks trained identically except for their random seeds. It cuts the large run-to-run variance that noisy financial data produces. **See:** [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md)

### Segmentation

Sorting order flow by expected toxicity, by broker, client type or order size, so each segment can be priced separately. Wholesalers' economics rest on segmenting retail flow. **See:** [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md) · [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Selection bias

Distortion from reporting the best of many tried strategies, parameters or samples as if it were the only one tried. The deflated Sharpe ratio and the probability of backtest overfitting correct for it. **See:** [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Self-trade prevention

An exchange order option that stops a firm's buy and sell orders from executing against each other by cancelling the resting order, the incoming one or both. It avoids wash trades and wasted fees when many strategies share an account. **See:** [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Shadow price

The change in an optimizer's objective from relaxing a constraint by one unit, read from the dual solution. It shows which constraint costs the most expected return. **See:** [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md)

### SHAP

Shapley additive explanations (Lundberg and Lee, 2017): splits a model's individual prediction among its input features using game-theoretic Shapley values. Popular for explaining tree models; it measures attribution, not P&L contribution. **See:** [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md)

### Sharpe ratio

Mean excess return divided by its standard deviation, usually annualized by multiplying a daily ratio by $\sqrt{252}$, which assumes independent returns; autocorrelated returns (smoothed marks, slow signals) make that scaling wrong (Lo, 2002). Always ask gross or net, backtest or live, and over what period: net figures of 0.5-1.0 for factor strategies and well above 3 for HFT market making are commonly cited `[Lore]`. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

### Short interest

Shares sold short and not yet covered, published by FINRA from member reports. High short interest relative to float or volume predicts low returns but also raises squeeze risk. **See:** [Analyst revisions and sentiment](../02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md) · [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

### Short squeeze

A rapid price rise that forces short sellers to buy back, which pushes the price higher still. Risk concentrates in names with high short interest and borrow fees, as in January 2021. **See:** [Analyst revisions and sentiment](../02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md) · [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)

### Short volatility

Positions that collect premium while volatility stays low and lose when it spikes: short options, short variance swaps, short VIX futures. They earn the variance risk premium at the cost of crash risk. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md) · [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)

### Short-term reversal

The tendency of stocks with extreme returns over the past day to month to partly reverse relative to peers over the following days to weeks (Lehmann, 1990; Jegadeesh, 1990). It is compensation for supplying liquidity to traders who demand immediacy, so it is strong gross and fragile net: turnover is high and costs, bid-ask bounce and execution assumptions decide whether it survives. **See:** [Short-term cross-sectional reversal](../02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md)

### Signal smoothing

Averaging a fast signal over recent days, typically with an EWMA, to cut turnover. It trades a little predictive power for much lower costs, and the smoothed signal must be re-neutralized because averaging reintroduces factor exposure. **See:** [Signal transforms](../03-algorithms/a-data-and-signals/signal-transforms.md) · [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### Signal-to-noise ratio

The ratio of predictable to unpredictable variation in a target. Stock returns have very low signal-to-noise, with out-of-sample R² well below 1%, which favors heavily regularized, simple models over flexible ones. **See:** [Linear models and regularization](../03-algorithms/b-forecasting-models/linear-models-and-regularization.md) · [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md)

### Simulator fidelity

How faithfully a market simulator reproduces fills, impact and other traders' reactions. An RL agent learns the simulator, so low fidelity means strategies that fail live. **See:** [Reinforcement learning in trading](../03-algorithms/g-live-trading/reinforcement-learning-in-trading.md) · [Backtesting engines](../03-algorithms/c-validation-and-backtesting/backtesting-engines.md)

### SIP

Securities information processor: the consolidator that collects quotes and trades from every exchange and FINRA's trade reporting facilities and disseminates the NBBO and the consolidated tape (the CTA/CQ plans for NYSE- and other-listed Tapes A and B, the UTP plan for Nasdaq-listed Tape C). It is slower than direct feeds because of extra network hops and processing, so latency-sensitive firms build their own consolidated view. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md)

### Size factor

SMB, small minus big: long small caps, short large caps, split at the NYSE median market cap. A Fama-French factor since 1993; imputing missing delisting returns erases the Nasdaq size effect. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md) · [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### Skip month

Leaving out the latest month when measuring momentum (the "12-1" signal: return from 12 months to 1 month ago), because one-month returns tend to reverse and would offset the momentum effect. **See:** [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md) · [Feature engineering](../03-algorithms/a-data-and-signals/feature-engineering.md)

### Slippage

The difference between an execution price and a benchmark price, typically the arrival mid or the price assumed in a backtest. Measured in basis points per dollar traded. **See:** [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Smart beta

Long-only, rules-based index products that tilt toward factors such as value, quality, low volatility or momentum at low fees. They harvest factor premia with tracking error to the cap-weighted index and no shorting. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md)

### Smart order routing (SOR)

The logic that decides where, how and in what size to send child orders across 18 registered exchanges, about 33 NMS-stock ATSs and the wholesalers (as of 2026-10 `[Reported]`), using real-time quotes, fees and rebates, historical fill probabilities, latency and venue toxicity. The main design choices are spraying simultaneously versus routing sequentially, posting versus taking, and dark-first versus lit-first. **See:** [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### Sniping

Latency arbitrage against stale quotes: sending a marketable order to hit a quote before its owner can cancel it. Budish, Cramton and Shim (2015) treat it as a tax on liquidity provision. **See:** [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Specific return

The part of a stock's return not explained by the risk model's factors, the residual $u_i$. Stock-selection alpha lives here; in attribution, a market-neutral book's specific P&L should be positive on average. **See:** [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md) · [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md) · [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md)

### Specific risk

The variance of a stock's specific (idiosyncratic) return, which a factor risk model assumes is uncorrelated across stocks. It diversifies away as the number of positions grows, so concentrated books are dominated by it. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

### Speed bump

A deliberate delay applied to incoming orders or messages, e.g., IEX's 350-microsecond delay implemented with coiled fiber, which gives the venue time to reprice pegged orders before latency arbitrageurs can pick them off `[Reported]`. Speed bumps protect resting liquidity on that venue; critics argue delayed quotes should not enjoy Reg NMS protection. **See:** [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Spoofing

Placing orders with intent to cancel them before execution, to create a false impression of supply or demand and move the price toward one's genuine orders; layering is the multi-level variant. It is expressly prohibited in futures by the Dodd-Frank amendment to the Commodity Exchange Act and prosecuted in securities as manipulation under the Exchange Act; surveillance looks at order-to-trade ratios, cancel timing and the side of subsequent fills. **See:** [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md) · [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)

### Spread capture

The part of the quoted spread a market maker earns per round trip before adverse selection and hedging, i.e., the half-spread earned on each passive fill. In tick-constrained large caps the quoted spread is one cent, so gross capture is at most about half a cent per share plus the rebate; profit depends on how much survives the markout. **See:** [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md) · [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

### Square-root law

The empirical regularity that a metaorder's price impact grows with the square root of its size, $\Delta P/P \approx Y\,\sigma_d\sqrt{Q/V_d}$, with daily volatility $\sigma_d$, daily volume $V_d$ and $Y$ of order one (Tóth et al., 2011; Bouchaud et al., 2018) `[Reported]`. Illustratively, buying 10% of ADV in a stock with 2% daily volatility costs about 0.6% with Y = 1. **See:** [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

### Stacking

Combining models by training a second-level model on their predictions. Unless those predictions are themselves out of sample and purged, stacking leaks and overweights the most overfit models. **See:** [Alpha combination and ensembling](../03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md)

### Stale quote

A quote not yet updated after a price-relevant event, so faster traders can hit it at an outdated price. Picking off stale quotes is the core of latency arbitrage. **See:** [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

### Standardized unexpected earnings (SUE)

An earnings surprise scaled by its typical size: actual minus expected EPS, from a seasonal random walk or consensus, divided by the standard deviation of past surprises. The classic sort variable for post-earnings drift. **See:** [Earnings and event-driven](../02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md)

### Stationarity

A series is stationary if its distribution does not change over time. Models need stationary inputs, so price levels become returns, ratios or ranks, and spreads are tested for stationarity before mean-reversion trades. **See:** [Feature engineering](../03-algorithms/a-data-and-signals/feature-engineering.md) · [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Statistical arbitrage

Market-neutral trading of many small, statistically motivated relative-value bets (pairs, factor residuals, short-term reversal, ML forecasts) held from minutes to weeks, relying on diversification across hundreds or thousands of positions rather than on any single convergence. It originated at Morgan Stanley in the mid-1980s `[Reported]` and is now the generic label for mid-frequency equity market-neutral quant trading. **See:** [Stat arb: overview and history](../02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md)

### Statistical factor model

A risk model whose factors are extracted from the return covariance by PCA or a similar method, without predefined characteristics. It adapts quickly and catches unnamed themes, but its factors are hard to interpret. **See:** [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md) · [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md)

### Sticky strike

A spot-vol rule assuming each strike's implied volatility stays fixed as spot moves; under sticky delta the smile moves with spot instead. The choice changes the delta used for hedging. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md)

### Stop-loss

A rule that cuts or exits a position or strategy after a set loss. It helps when losses persist, as in trends or broken pairs, and hurts strategies whose P&L mean-reverts. **See:** [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md) · [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

### Straddle

A call and a put at the same strike and expiry. Delta-neutral at inception, a long straddle profits from large moves either way; Coval and Shumway (2001) found zero-beta index straddles lost about 3% a week `[Verified]`. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md)

### Strategy life cycle

The arc of a strategy: discovery, early profits, publication and diffusion, crowding, then decay or a crowded crash. Firms budget research as maintenance capex to replace decaying edges. **See:** [Evolution of quant strategies](../02-strategies/h-cross-cutting/evolution-of-quant-strategies.md)

### Survivorship bias

Overstating backtest performance by using a universe of securities that still exist today, omitting those that were delisted, acquired or went bankrupt. For equities the fix is a point-in-time universe including delisted names and their delisting returns (Shumway, 1997), which matters most for small-cap, value and distress-related signals. **See:** [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

### SVI parameterization

Gatheral's "stochastic volatility inspired" formula for one expiry's implied-variance smile: five parameters, linear in the wings, fitted with constraints that avoid arbitrage (Gatheral and Jacquier, 2014). **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

## T

### T+1 settlement

The standard US settlement cycle for most broker-dealer securities trades since 2024-05-28, shortened from T+2 by amendments to SEC Rule 15c6-1 `[Verified]`. It compresses the timelines for allocations and affirmations, stock-loan recalls and FX funding by non-US investors, and moves Reg SHO close-out deadlines earlier. **See:** [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

### Tail latency

The slowest percentiles of a system's response time, such as the 99.9th. In HFT the tail matters more than the average, because the slow moments arrive when markets move. **See:** [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)

### Temporary impact

The price concession that lasts only while you trade and fades afterward, a function of trading rate. Almgren-Chriss treats it as linear in rate; measured impact is concave. **See:** [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Theta

The rate at which an option's value decays as time passes, all else equal. Short-option books earn theta daily and pay it back through gamma losses when the underlying moves; for a hedged option the two balance at implied volatility. **See:** [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md) · [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md)

### Tick size

The minimum price increment for quotes and orders. For US stocks priced at \$1 or more it has been one cent since decimalization (2001), codified in Rule 612 (2005). The 2024 amendments add a half-cent increment for tick-constrained stocks (time-weighted average quoted spread of \$0.015 or less), but compliance has been postponed to the first business day of November 2027 and the rule is under staff review `[Verified]`. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Tick-constrained stock

A stock whose quoted spread sits at the minimum tick most of the time, typically a liquid, low-to-mid-priced name. Because price cannot improve by less than a tick, competition moves to queue position, fee schedules (inverted venues) and speed; these are the stocks the 2024 half-cent tick targets, which is not in effect as of 2026-11 `[Verified]`. **See:** [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

### Tick-to-trade

The time from a market-data packet arriving at a firm's network interface to the resulting order leaving it, the standard internal latency metric for HFT systems. Tuned software systems are typically in the single-digit microseconds and FPGA paths below one microsecond `[Reported]`; the network trip to and from the venue is a separate budget. **See:** [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md) · [Trading and research tech stacks](../05-infrastructure/trading-and-research-tech-stacks.md)

### Time-series momentum

Going long assets whose own past return (typically over 12 months) is positive and short those whose return is negative, regardless of other assets; Moskowitz, Ooi and Pedersen (2012) document it across 58 liquid futures and forward markets. It is the formal name for what trend-following CTAs do, and differs from cross-sectional momentum, which ranks assets against each other. **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md) · [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

### Top of book

The best bid and best offer, with sizes, on a venue; across protected venues they form the NBBO. The SIP carries each exchange's top of book, while deeper levels need direct feeds. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

### Tracking error

The annualized standard deviation of a portfolio's return relative to its benchmark. Long-only quant and smart-beta products set tracking-error budgets, often a few percent, within which they maximize factor exposure. **See:** [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md) · [There is no single algorithm](../03-algorithms/there-is-no-single-algorithm.md)

### Trade reporting facility (TRF)

A FINRA facility, operated with Nasdaq or NYSE, where off-exchange trades by ATSs and wholesalers are reported for the consolidated tape. TRF prints were 50.6% of US equity volume in 2025 `[Verified]`. **See:** [Life of a stock order](../01-market-structure/life-of-a-stock-order.md) · [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

### Trade sign

Whether a trade was buyer- or seller-initiated. When the data do not flag it, it is inferred with the Lee-Ready (quote) or tick rule; signed volume feeds trade-flow imbalance signals. **See:** [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

### Trade-through rule

Reg NMS Rule 611, the Order Protection Rule: trading centers must maintain policies that prevent trade-throughs, i.e., executions at a price inferior to a protected quotation displayed on another venue, such as buying at \$10.02 while \$10.01 is displayed elsewhere. Exceptions such as ISOs let a sender clear better prices itself; it is the rule that forces routing and makes the NBBO binding, and on 2026-06-11 the SEC proposed repealing it `[Verified]`. **See:** [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

### Trading toward the aim

Gârleanu and Pedersen's (2013) result that, with quadratic trading costs and predictable returns, the optimal policy trades each period only part of the way from the current portfolio toward an "aim" portfolio, itself a weighted average of today's and expected future Markowitz portfolios. It formalizes why persistent signals deserve more weight than fast-decaying ones of equal strength and underlies multi-period construction in many stat-arb books. **See:** [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### Transaction cost analysis (TCA)

Measuring and attributing trading costs: pre-trade (forecast cost and risk of a planned trade), intra-trade (real-time slippage) and post-trade (shortfall versus arrival, VWAP or close, split into spread, impact, timing and fees). Quant firms run TCA to calibrate impact models and choose algorithms and brokers; for the buy side it also documents best execution. **See:** [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

### Transfer coefficient

The correlation between the risk-adjusted weights an unconstrained optimizer would hold and those actually held (Clarke, de Silva and Thorley, 2002). It scales the fundamental law, IR ≈ TC × IC × √breadth; constraints often hold it to 0.3–0.7 `[Estimate]`. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md) · [How firms combine strategies](../02-strategies/h-cross-cutting/how-firms-combine-strategies.md)

### Transformer

The neural-network architecture behind LLMs: self-attention layers let each element of a sequence weigh every other element. Applied to text and, with mixed results, to order-book and return sequences. **See:** [Neural nets and sequence models](../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md) · [LLMs and foundation models in quant](../03-algorithms/b-forecasting-models/llms-and-foundation-models-in-quant.md)

### Transient impact

Impact that decays gradually after each trade, modeled with a decay kernel rather than split into temporary and permanent parts. It matters when trading over several days, because today's impact raises tomorrow's starting price. **See:** [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

### Trend following

Systematic strategies that buy assets in uptrends and sell those in downtrends, using moving-average crossovers or breakouts over weeks to a year, mostly in futures across equity indexes, rates, currencies and commodities, with positions scaled by volatility. Returns are positively skewed, concentrated in sustained moves such as 2008 and 2022 `[Reported]`, with long flat or losing stretches in between. **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Turnover

How much of the portfolio is traded per period, usually one-way: half the sum of absolute weight changes, or traded value over gross book, per day or annualized (some firms quote two-way, so ask). Turnover times cost per unit traded is the cost drag: illustratively, 50% daily one-way turnover at 5 bp per trade costs 2.5 bp a day, about 6% a year on gross book. **See:** [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### Turnover penalty

A cost term in an optimizer's objective, linear or quadratic in trade size, that blocks trades whose forecast gain does not cover their expected cost. Its multiplier is tuned so realized costs match the model. **See:** [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md) · [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

### TWAP

Time-weighted average price: an execution schedule that trades equal quantities in equal time slices regardless of volume, and the corresponding benchmark. It is simple and predictable, hence easy to detect unless randomized, and is used where volume forecasts are unreliable, e.g., in illiquid names. **See:** [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md)

## U

### Urgency

How fast an execution should finish, expressed as a risk-aversion or participation setting. High urgency front-loads trading, cutting timing risk at the price of higher impact. **See:** [Execution algorithms: overview](../03-algorithms/e-execution-algorithms/execution-algorithms-overview.md) · [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

## V

### Value factor

Long cheap stocks and short expensive ones on book-to-market, earnings or cash-flow yield (HML in Fama-French). Explained as distress risk or as overpaying for glamour; HML fell about 51% from January 2017 to September 2020 `[Verified]`. **See:** [Value, quality and low volatility](../02-strategies/e-risk-premia-and-factors/value-quality-low-vol.md) · [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md)

### Value spread

The valuation gap between a factor's cheap and expensive legs, for example the ratio of their book-to-market. A wide spread implies higher expected factor returns and is the main input to factor timing, but spreads can widen for years. **See:** [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md) · [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)

### Variance risk premium

The difference between risk-neutral (implied) and expected realized variance, $E^Q[\sigma^2] - E^P[\sigma^2]$, which has been persistently positive for equity indexes: implied volatility has usually exceeded subsequently realized volatility (Carr and Wu, 2009) `[Reported]`. Option sellers and short-variance strategies earn it as compensation for crash losses; it is the main structural P&L source of short-volatility and dispersion books. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md)

### Variance swap

A swap that pays the difference between realized variance over its life and a strike fixed at inception. The fair strike is replicated by a strip of options across strikes, as in the VIX calculation, isolating the variance risk premium. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md) · [Dispersion and correlation trading](../02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md)

### Vectorized backtest

A backtest computed with array operations over a whole panel of signals and returns at once. Fast for daily research, but it easily hides look-ahead and ignores fills, queues and latency. **See:** [Backtesting engines](../03-algorithms/c-validation-and-backtesting/backtesting-engines.md)

### Vega

An option's sensitivity to a change in implied volatility, usually per volatility point. Options market makers manage vega by expiry and strike bucket, because quoting flow accumulates it and stock hedges cannot remove it. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md) · [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md) · [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

### Venue scorecard

A router's per-venue statistics: fill rates, fees, latency and the markouts of fills. Used to rank venues net of adverse selection rather than by fees alone. **See:** [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

### VIX

Cboe's 30-day implied-volatility index for the S&P 500, computed from a strip of SPX options. Over 1990–2026 it averaged 19.4 versus 15.3 subsequently realized, and exceeded realized on 86% of days `[Verified]`. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md)

### Volatility arbitrage

Trading options or variance swaps on a view that implied volatility is mispriced relative to forecast realized volatility, or relative to other points on the surface, while hedging delta so that P&L comes from the volatility difference. In practice it ranges from systematic short-VRP books to relative-value trades along the skew and term structure. **See:** [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md) · [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md)

### Volatility skew

How implied volatility varies across strikes for one expiry. Equity-index skew slopes down: since 1987, out-of-the-money puts have carried higher implied vols than calls. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md) · [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md)

### Volatility surface

Implied volatility as a function of strike (or delta) and maturity for one underlying, showing the equity skew (downside puts richer) and the term structure. Options market makers fit a smooth, arbitrage-free parametric surface (e.g., SVI) to quotes and price every option off it; the fitted surface, not individual Black-Scholes prices, is their real fair value. **See:** [Options pricing and vol surfaces for market making](../03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md) · [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md)

### Volatility targeting

Scaling position size inversely to forecast volatility so the portfolio runs at a constant ex-ante volatility (say 10% a year), $w_t = \sigma^{*}/\hat\sigma_t$. Because volatility is persistent and not matched by higher subsequent returns, it tends to raise Sharpe ratios and cut tail losses for equity and momentum portfolios (Moreira and Muir, 2017), though the out-of-sample benefit is debated (Cederburg et al., 2020). **See:** [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md) · [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

### Volmageddon

The 2018-02-05 volatility spike, VIX from 17.31 to 37.32 (+115.6%) `[Verified]`, which wiped out inverse-VIX exchange-traded products whose own end-of-day hedging fed the move. **See:** [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md) · [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md)

### Volume curve

The expected share of daily volume traded in each interval of the day, typically U-shaped with a spike at the close. VWAP algorithms schedule against a forecast of it. **See:** [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md) · [Intraday patterns and seasonality](../02-strategies/c-statistical-arbitrage/intraday-patterns-and-seasonality.md)

### VPIN

Volume-synchronized probability of informed trading (Easley, López de Prado and O'Hara, 2012): order imbalance across equal-volume buckets, proposed as a flow-toxicity gauge. Its predictive claims, including for the 2010 flash crash, are contested. **See:** [Order-book and trade-flow signals](../03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md)

### VWAP

Volume-weighted average price: the volume-weighted mean of all trade prices over a period, used both as a benchmark and as an execution algorithm that trades in proportion to a forecast intraday volume curve (U-shaped, with a large share in the close). Because a VWAP benchmark can be matched simply by trading with the crowd, alpha-driven orders are now usually judged against arrival price instead. **See:** [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

## W

### Walk-forward analysis

Repeatedly fitting a model on a historical window and testing it on the next unseen period, rolling or expanding forward, so every out-of-sample point uses only information available at the time. It mimics live deployment and is the standard validation scheme, but it yields a single path and still overfits if many walk-forward variants are tried and only the best is reported. **See:** [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

### Weighted mid

The midpoint shifted toward the side with less displayed size, using top-of-book imbalance; a simple fair-value estimate that the microprice refines. **See:** [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

### Whipsaw

Losses from a rule that flips position repeatedly as a signal oscillates around its threshold, paying costs on every flip. Trend followers and regime filters suffer it in choppy markets; bands and hysteresis reduce it. **See:** [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md) · [Regime detection](../03-algorithms/b-forecasting-models/regime-detection.md)

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
- [Verified] Cboe (2026-08). "Market Metrics That Matter: Derivatives July 2026 Volume Highlights." <https://www.cboe.com/insights/posts/market-metrics-that-matter-derivatives-july-2026-volume-highlights> (accessed 2026-11)
- [Verified] SEC (2013-10-16). In the Matter of Knight Capital Americas LLC, Release No. 34-70694. <https://www.sec.gov/litigation/admin/2013/34-70694.pdf> (accessed 2026-11)
- [Verified] SEC (2026-04-16). "Concept Release on the Consolidated Audit Trail and Other Audit Trails and Data Sources." Release No. 34-105251. <https://www.govinfo.gov/content/pkg/FR-2026-04-20/html/2026-07651.htm> (accessed 2026-11)
- [Verified] French, K. R. "Data Library: Fama/French 3 and 5 factors, momentum," monthly through 2026-09 (statistics in this glossary are the KB's computations). <https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html> (accessed 2026-11)
- [Verified] Harvey, C. R. & Liu, Y. (2015). "Backtesting." *Journal of Portfolio Management* 42(1), 13–28. <https://doi.org/10.3905/jpm.2015.42.1.013> (accessed 2026-11)
- [Verified] Greenwood, R. & Sammon, M. (2025). "The Disappearing Index Effect." *Journal of Finance* 80(2), 657–698. <https://doi.org/10.1111/jofi.13410> (accessed 2026-11)
- [Verified] Ehsani, S. & Linnainmaa, J. T. (2022). "Factor Momentum and the Momentum Factor." *Journal of Finance* 77(3), 1877–1919. <https://doi.org/10.1111/jofi.13131> (accessed 2026-11)
- [Verified] Lou, D. & Polk, C. (2022). "Comomentum: Inferring Arbitrage Activity from Return Correlations." *Review of Financial Studies* 35(7), 3272–3302. <https://doi.org/10.1093/rfs/hhab117> (accessed 2026-11)
- [Verified] Blitz, D., Huij, J. & Martens, M. (2011). "Residual momentum." *Journal of Empirical Finance* 18(3), 506–521. <https://doi.org/10.1016/j.jempfin.2011.01.003> (accessed 2026-11)
- [Verified] Coval, J. D. & Shumway, T. (2001). "Expected Option Returns." *Journal of Finance* 56(3), 983–1009. <https://doi.org/10.1111/0022-1082.00352> (accessed 2026-11)
- [Verified] Shumway, T. (1997). "The Delisting Bias in CRSP Data." *Journal of Finance* 52(1), 327–340. <https://doi.org/10.1111/j.1540-6261.1997.tb03818.x> (accessed 2026-11)
- [Verified] Lee, C. M. C. & Ready, M. J. (1991). "Inferring Trade Direction from Intraday Data." *Journal of Finance* 46(2), 733–746. <https://doi.org/10.1111/j.1540-6261.1991.tb02683.x> (accessed 2026-11)
- [Verified] Easley, D., López de Prado, M. & O'Hara, M. (2012). "Flow Toxicity and Liquidity in a High-frequency World." *Review of Financial Studies* 25(5), 1457–1493. <https://doi.org/10.1093/rfs/hhs053> (accessed 2026-11)
- [Verified] Gao, L., Han, Y., Li, S. Z. & Zhou, G. (2018). "Market intraday momentum." *Journal of Financial Economics* 129(2), 394–414. <https://doi.org/10.1016/j.jfineco.2018.05.009> (accessed 2026-11)
- [Verified] Lundberg, S. M. & Lee, S.-I. (2017). "A Unified Approach to Interpreting Model Predictions." *NeurIPS 30*. <https://arxiv.org/abs/1705.07874> (accessed 2026-11)
