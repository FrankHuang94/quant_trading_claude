# Quiz: Algorithms

> **TL;DR**
>
> - Thirty questions on module 03: the pipeline view, every card section (A. data and signals to G. live trading) and the four end-to-end walkthroughs.
> - About half are conceptual ("what breaks if…"), a third are small calculations (IC ratios, impact, a VWAP schedule, an Avellaneda-Stoikov reservation price, a markout's sign, P&L attribution) and a fifth are judgment calls about a backtest, a router report or a TCA report. Each is marked basic, informed or sharp.
> - Work the numbers on paper before you open the answer. Lab figures are labeled synthetic lab results: they show mechanisms and comparisons, not real-world levels.

**Level:** Core · **Read time:** ~35 min · **Last verified:** 2026-11

## The pipeline

### Q1 (basic). Why is "what is your algorithm?" the wrong question to ask a quant, and what is a better one?

<details markdown="1">
<summary>Answer</summary>

A trading business is a production line of dozens of algorithms, each answering one narrow question (fair price, relative return, risk, how to trade without moving the price). Losses compound like fab yield: if each of five stages keeps 85% of what it receives, only 0.85⁵ ≈ 44% of the alpha reaches P&L (illustrative). The edge usually lives in the joints between stages and in plumbing. A better question: which stage of your pipeline is the binding constraint? → [There is no single algorithm](../03-algorithms/there-is-no-single-algorithm.md) · [Algorithm map](../03-algorithms/algorithm-map.md)

</details>

## A. Data and signals

### Q2 (sharp). A small-cap value backtest uses the vendor's current company list and as-restated fundamentals. It looks strong. What two biases do you suspect, and how big can one of them be?

<details markdown="1">
<summary>Answer</summary>

**Survivorship:** dead stocks are missing. In the card's illustration 97 surviving Nasdaq small caps average +1.2%, while 3 delisted names lack returns. Imputing Shumway's −55% gives (97 × 1.2% − 3 × 55%) ÷ 100 ≈ **−0.49%**, not +1.2%. **Look-ahead from restatements:** EPS restated from \$2.00 to \$1.60 in August makes the stock look expensive in March, when only \$2.00 was public. The backtest then avoids or shorts it and banks the August drop. The fix is to key every value on the moment it became public, using an as-of join with a lag. → [Point-in-time data and cleaning](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

</details>

### Q3 (informed). Raw signal values for five stocks are −2, −1, 0, +1 and +20, and the +20 is a bad print. What goes wrong if you z-score first, and what is the fix?

<details markdown="1">
<summary>Answer</summary>

The bad print sets everyone's scale. The mean becomes 3.6 and the sd 8.26, so stock D (+1, above the median) gets a negative z of −0.31 and becomes a short. A ±3 clip afterward does nothing, because the bad print's own z is only 1.99. Winsorize first (median 0, MAD 1, clip at ±5), then z-score: D becomes +0.17, a long. Ranks get the order right but cannot see how extreme a value is. → [Signal transforms](../03-algorithms/a-data-and-signals/signal-transforms.md)

</details>

### Q4 (informed). A signal's daily rank IC averages 0.01 with a standard deviation of 0.10. What annual information ratio does that imply before costs, and how long until the mean IC reaches t = 3?

<details markdown="1">
<summary>Answer</summary>

IC ratio = 0.01 ÷ 0.10 × √252 ≈ **1.6 a year**, the Fundamental Law in disguise. The t-statistic after n days is 0.01 ÷ (0.10 ÷ √n), which reaches 3 at n = 900 days, about **3.6 years** (illustrative). On any single day, sampling noise alone is about 1/√N (0.045 at 500 names), so one day's IC tells you almost nothing. → [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)

</details>

## B. Forecasting models

### Q5 (informed). Two reversal signals are 0.8 correlated, with ICs of 0.030 and 0.026. Why does ridge regression beat OLS here?

<details markdown="1">
<summary>Answer</summary>

OLS gives coefficients of 0.0256 and 0.0056, and with ~10,000 effective observations each has a standard error of about 0.0167, larger than the second coefficient itself. Ridge (λ = 1) gives 0.0117 and 0.0083 with standard errors of about 0.0043, four times smaller, for a sliver of in-sample fit (0.091% vs 0.090% R²). Returns are mostly noise (the best monthly out-of-sample R² in Gu, Kelly and Xiu was 0.40%), so estimation variance dominates and shrinkage wins. Choose λ by purged walk-forward validation. → [Linear models and regularization](../03-algorithms/b-forecasting-models/linear-models-and-regularization.md)

</details>

### Q6 (sharp). A researcher IC-weights three signals: A (IC 0.040), A′ (a noisy copy of A, correlation 0.85, IC 0.034) and an unrelated B (IC 0.030). Then she adds ten pure-noise signals at equal weight "for diversification". What do you tell her?

<details markdown="1">
<summary>Answer</summary>

A′ adds nothing that A lacks. Mean-variance (OLS) weights give it zero and reach a composite IC of √(0.040² + 0.030²) = **0.050**, while IC weighting hands the A cluster 71% of the weight. OLS, ridge, equal weight and IC weighting all land within 6% of each other. The noise signals do the damage: equal weight across all thirteen falls to an IC of about **0.027**, losing 46%. Use ridge on the alpha correlation matrix and admit signals on out-of-sample evidence. → [Alpha combination and ensembling](../03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md)

</details>

### Q7 (basic). What do gradient-boosted trees find that a linear model misses, and why are their winning settings deliberately weak?

<details markdown="1">
<summary>Answer</summary>

Interactions and thresholds. In the card's example, reversal pays +6 / −5 bps in high-turnover names but only +1 / −1 in low-turnover ones. A linear fit misses every bucket by 2.25 bps, while a depth-2 tree recovers them exactly. Stock data have a very low signal-to-noise ratio, so flexible models fit noise. Winning settings are shallow trees, learning rates of 0.01–0.05, large leaves, subsampling and early stopping on time-ordered validation. → [Tree ensembles](../03-algorithms/b-forecasting-models/tree-ensembles.md)

</details>

### Q8 (sharp). A two-state regime model (calm vs stressed) jumps from a 5% to a 99% probability of stress after one −3% day. Is that a bug? And what is the classic way regime backtests cheat?

<details markdown="1">
<summary>Answer</summary>

Not a bug. A −3% day is 4.4 standard deviations for the calm state (0.7% volatility) but only 1.45 for the stressed state (2.0%), so Bayes' rule gives a posterior of about 0.991 (illustrative). A slow grind of three −1.5% days moves it only to 0.18, 0.43 and 0.70. The cheat is hindsight: smoothed probabilities and official recession dates use future data, so only filtered, same-day probabilities are honest. Firms mostly use regimes defensively, to scale risk, not to forecast returns. → [Regime detection](../03-algorithms/b-forecasting-models/regime-detection.md)

</details>

## C. Validation and backtesting

### Q9 (basic). Why does shuffled K-fold cross-validation leak on financial data, and what fixes it?

<details markdown="1">
<summary>Answer</summary>

Labels overlap: a daily-sampled 5-day return shares four days with its neighbor (correlation about 0.8), and features persist, so shuffling puts near-copies of test rows into training. The fixes are walk-forward splits, **purging** training dates whose labels overlap the test labels, and an **embargo** after each test block. The leak scales with model flexibility. In Lab 12 a GBDT scored an out-of-sample IC of 0.127 under shuffled K-fold, against 0.066 walk-forward and 0.076 purged; ridge leaked only 0.002 (synthetic lab result). → [Time-series cross-validation](../03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md)

</details>

### Q10 (informed). You test 100 zero-skill strategies on five years of daily data. Roughly what annualized Sharpe should the best one show by luck?

<details markdown="1">
<summary>Answer</summary>

A zero-skill annualized Sharpe has a standard error of about 1/√5 = 0.447. The expected best of N grows like √(2 ln N) standard errors; the card's more exact formula gives 2.53 for N = 100. So the luck hurdle is 0.447 × 2.53 ≈ **1.13** `[Estimate]`. Five years of data absorb only about 45 independent trials before the hurdle reaches 1.0. In Lab 13 the best of 500 noise strategies went from Sharpe 2.18 in sample to −0.90 out of sample (synthetic lab result). → [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

</details>

### Q11 (sharp). A PM shows you a 10-year backtest with Sharpe 1.0, the best of 100 variants. What is it worth, and what else do you ask?

<details markdown="1">
<summary>Answer</summary>

t = 1.0 × √10 = 3.16. A Bonferroni adjustment for 100 trials cuts the t-statistic to about 1.42, a Sharpe of **0.45**, a 55% haircut. Harvey and Liu's own example (with BHY and 0.4 average correlation) gives 0.44 `[Verified]`. Then ask for the honest trial count including abandoned ideas, point-in-time data, realistic costs and borrow, and an untouched out-of-sample period. Expect further decay: predictors lost 26% out of sample and 58% after publication (McLean and Pontiff) `[Verified]`. → [Backtest pitfalls](../03-algorithms/c-validation-and-backtesting/backtest-pitfalls.md) · [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)

</details>

## D. Portfolio construction

### Q12 (informed). Why must a risk model be graded on optimized portfolios rather than random ones?

<details markdown="1">
<summary>Answer</summary>

An optimizer seeks out the directions where forecast risk is lowest, and those are where the model underestimates risk. In Lab 14 the sample covariance scored a bias statistic (realized sd ÷ forecast sd) of 1.00 on random portfolios but 2.78 on optimized ones (synthetic lab result). The related alignment problem: alpha that the risk model cannot see looks diversifiable, so the optimizer overloads it. → [Risk models](../03-algorithms/d-portfolio-construction/risk-models.md)

</details>

### Q13 (informed). You estimate the covariance of 500 stocks from 252 days of returns. What is wrong with the sample matrix, and how much better is it with 1,000 days?

<details markdown="1">
<summary>Answer</summary>

With N > T it is singular: rank 251, leaving 249 zero-variance directions, "riskless" long-short books that carry ordinary risk. With T = 1,000 (N/T = 0.5), pure-noise eigenvalues still spread from (1 − √0.5)² ≈ 0.086 to (1 + √0.5)² ≈ 2.91. The safest-looking portfolio's volatility is then understated by up to 1/√0.086 ≈ 3.4×. Shrinking 33% toward the identity narrows that range to 0.39–2.28; factor models and nonlinear shrinkage are the other fixes. → [Covariance estimation and shrinkage](../03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md)

</details>

### Q14 (sharp). Why did Michaud call mean-variance optimization "error maximization"? Show it with a two-stock pair.

<details markdown="1">
<summary>Answer</summary>

The unconstrained solution is w* = Σ⁻¹α ÷ (2λ), a noisy inverse times noisy forecasts, so the optimizer bets hardest where estimates are most wrong. In the card's pair (20% residual vol each, true correlation 0.8), estimating 0.95 instead of 0.8 raises gross exposure from 25% to 100%. Realized volatility is then 1.98× the prediction, while the true information ratio barely moves. Fixes: scale alphas as IC × volatility × score, use a factor risk model with shrinkage, and add constraints and costs. → [Mean-variance optimization](../03-algorithms/d-portfolio-construction/mean-variance-optimization.md)

</details>

### Q15 (informed). You buy 5% of ADV (\$10M) in a \$50 stock with 2% daily volatility. Using the square-root law with Y between 0.5 and 1, what does impact cost, and what happens at four times the size?

<details markdown="1">
<summary>Answer</summary>

Peak impact = Y × 200 bps × √0.05 = **22.4–44.7 bps**. At a steady trading rate the average fill pays about two-thirds of the peak: 14.9–29.8 bps. Add a 2 bps half-spread and 1 bp of commission for a total of 18–33 bps, or \$18,000–\$33,000 (illustrative). At four times the size (20% of ADV) the cost per share doubles and the dollar cost rises eightfold. A linear model calibrated at 5% halves small-trade costs and doubles large ones. → [Transaction cost and impact models](../03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md)

</details>

### Q16 (informed). Gârleanu and Pedersen say "aim in front of the target, trade partially toward the aim." What does each half mean, and what sets the trading speed?

<details markdown="1">
<summary>Answer</summary>

The aim is a cost-aware target that shrinks fast-decaying signals: in Lab 15 a 60-day-half-life signal keeps 96% of its weight and a 1-day signal only 35% (synthetic lab result). You then trade a fixed fraction of the gap each day. That fraction depends on costs and risk aversion, not on alpha decay: 0.213 a day in the card's example. With quadratic costs a full rebalance would trade 6.2× as much and cost 38× as much (illustrative). → [Multi-period optimization and trading toward the aim](../03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md)

</details>

## E. Execution algorithms

### Q17 (informed). In Almgren-Chriss, what trades off against what? Compare TWAP with a risk-averse schedule for a \$500M sale over five days.

<details markdown="1">
<summary>Answer</summary>

Impact punishes speed and price risk punishes waiting; the model minimizes E[IS] + λ·Var[IS], and λ = 0 gives TWAP. In Lab 16, TWAP expects 46 bps with a 254 bps standard deviation, while λ = 10⁻⁷ expects 96 bps with a 110 bps standard deviation (synthetic lab result). That pays \$2.5M more expected cost to cut the standard deviation by \$7.2M, and whether that is worth it is the client's call. On single orders TWAP still beats that schedule 61% of the time. → [Implementation shortfall and Almgren-Chriss](../03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md)

</details>

### Q18 (informed). Buy 500,000 shares, 10% of a 5M-share ADV. The first half hour carries 11% of the day's volume (550,000 shares by others) and the 12:00 half hour 4.5% (225,000). How much do VWAP and TWAP each buy in those slots, and what does POV at 10% buy when others print 12,000 shares?

<details markdown="1">
<summary>Answer</summary>

VWAP follows the volume curve: 11% × 500,000 = **55,000** at the open and 22,500 at lunch, a steady 10 shares per 100 that others trade. TWAP buys 500,000 ÷ 13 ≈ **38,462** in every half hour: 7 per 100 at the open but 17 per 100 at lunch, so its temporary impact is 6.1 and 10.4 bps against VWAP's 7.5 (Lab 17's impact model). POV at 10% buys 0.10 ÷ 0.90 × 12,000 ≈ **1,333** shares, so it keeps the pace but not the deadline: on a day 25% light it fills only 83% (illustrative). → [VWAP, TWAP and POV](../03-algorithms/e-execution-algorithms/vwap-twap-pov.md)

</details>

### Q19 (sharp). Your router's venue report ranks a dark midpoint pool first: a 70% fill rate and the lowest cost it measures, 0.85 bps. Should you send it more passive flow?

<details markdown="1">
<summary>Answer</summary>

No. The report ignores markouts. That pool's fills mark out 3.0 bps against you, so its true all-in cost is 2.95 bps. All-in cost = P(fill) × (−half-spread ± fee or rebate + markout) + P(no fill) × cleanup. For the standard maker-taker venue: 0.40 × (−1.00 − 0.32 + 0.60) + 0.60 × 2.6 = **1.27 bps**, the best of the set (illustrative, Lab 18 parameters). High fill rates often signal toxicity: in Lab 18 a fill-chasing router cost 2.83 bps against 1.48 for a markout-aware bandit (synthetic lab result). → [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)

</details>

## F. Market making and HFT

### Q20 (basic). Describe a market maker's hot loop. Why does rank in the latency race matter more than absolute speed, and why do firms shard symbols across cores?

<details markdown="1">
<summary>Answer</summary>

Packet in → book update → fair value → quote decision → risk check → order out; models are fit offline and pushed in as parameters. Tick-to-trade is about 2.5 µs in very good software and tens of nanoseconds on FPGAs `[Verified]`, but every firm pays the same exchange round trip, so being first matters more than being fast. A futures tick can move fair value in 500 symbols at once: at 1 µs per symbol on one core, the last quote updates 500 µs later, long after rivals hit it. Across 16 cores it is about 31 µs (illustrative). → [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)

</details>

### Q21 (informed). The book is \$50.00 × \$50.02 with 4,500 shares bid and 500 offered. Compute the weighted mid. Why does a desk that quotes around it get picked off?

<details markdown="1">
<summary>Answer</summary>

Imbalance I = (4,500 − 500) ÷ 5,000 = 0.8, so the weighted mid = mid + I × half-spread = 50.010 + 0.8 × 0.010 = **\$50.018**. The fitted microprice is only \$50.0131. The weighted-mid desk thinks a new \$50.01 bid is 0.8 ticks cheap, the microprice says 0.31, and Lab 02's test days realized 0.16: a fivefold overstatement (synthetic lab result). The microprice learns how much of the imbalance lean actually comes true. → [Fair value and microprice](../03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md)

</details>

### Q22 (sharp). In Avellaneda-Stoikov the reservation price is r = s − qγσ²(T − t). With the card's parameters (γ = 0.01, σ² = 0.4274 cents² per second) a dealer is long 3 lots with an hour left. How far below the mid does AS center its quotes, and how does that compare with GLFT's lean of 0.254 cents per lot?

<details markdown="1">
<summary>Answer</summary>

γσ²(T − t) = 0.01 × 0.4274 × 3,600 ≈ **15.4 cents per lot**, so with q = +3 the reservation price sits about **46 cents** below the mid. A long dealer shades both quotes down and sells faster than it buys. GLFT's clock-free lean puts the center 3 × 0.254 ≈ 0.76 cents below the mid, sixty times less; the two agree only when about 59.5 seconds remain (illustrative). The AS lean hangs on an arbitrary end-of-horizon clock; GLFT's closed form drops the clock and adds inventory limits. → [Quoting and inventory control](../03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md)

</details>

### Q23 (basic). Your bid at \$50.00 is hit for 1,000 shares when the mid is \$50.005. Sixty seconds later the mid is \$49.985. What are the markouts at 0 and 60 seconds, and what do they say?

<details markdown="1">
<summary>Answer</summary>

Markout = side × (mid at t + h − fill price), with side +1 because you bought. At 0 s: 50.005 − 50.00 = **+0.5¢**, the spread captured, +\$5. At 60 s: 49.985 − 50.00 = **−1.5¢** (−3.0 bps), −\$15. Adverse selection was \$20 against \$5 of spread captured: this seller knew something. Segment markouts by counterparty and venue to set spreads and choose flow. → [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)

</details>

### Q24 (informed). An options desk hedges delta daily and considers hourly or every 15 minutes. What does more frequent hedging buy, and where do the returns diminish?

<details markdown="1">
<summary>Answer</summary>

It buys lower P&L variance, not higher expected P&L, and it costs trading. In Lab 06, going from daily to hourly hedging costs \$4.30 more per contract and cuts the P&L standard deviation by \$20.5, about \$4.8 of risk per dollar. Going from hourly to every 15 minutes costs \$6.96 more for a \$0.4 reduction, 6 cents per dollar (synthetic lab result). A band on net delta, rather than a clock, saved 16% of the edge for a small rise in risk. → [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md)

</details>

## G. Live trading

### Q25 (informed). A book is long \$10M of A (beta 1.2) and short \$10M of B (beta 0.8). The market returns −2.0%, A −1.5% and B −3.0%. Split the day's holding P&L into factor and specific.

<details markdown="1">
<summary>Answer</summary>

Dollar beta = 10 × 1.2 − 10 × 0.8 = +\$4M, so factor P&L = 4M × −2.0% = **−\$80,000**. Residuals: A = −1.5% + 1.2 × 2.0% = +0.9%, or +\$90,000; B = −3.0% + 0.8 × 2.0% = −1.4%, which the short earns as +\$140,000. Specific P&L = **+\$230,000**, and the total holding P&L is +\$150,000 (illustrative). The alpha worked; an unintended beta tilt cost \$80,000. Fix the hedge, not the alpha. → [Live monitoring and P&L attribution](../03-algorithms/g-live-trading/live-monitoring-and-pnl-attribution.md)

</details>

### Q26 (sharp). A strategy's Sharpe may have fallen from 1.0 to 0. With daily data, how long until the drop is two standard errors wide? Why does a market maker see decay so much faster?

<details markdown="1">
<summary>Answer</summary>

With daily data the standard error of an annual Sharpe is about 1/√years, so a two-standard-error gap needs years = (2 ÷ ΔSharpe)² = (2 ÷ 1)² = **4 years**. A market maker going from 8 to 4 needs (2 ÷ 4)² = 0.25 years, about three months: what matters is the absolute drop. That is why monitors stack weak evidence (rolling IC, CUSUM alarms, a Bayesian Sharpe posterior), retirement is staged, and alarms trigger a human review rather than an automatic kill. → [Alpha decay detection and model retirement](../03-algorithms/g-live-trading/alpha-decay-detection-and-model-retirement.md)

</details>

## H. End-to-end walkthroughs

### Q27 (sharp). The stat-arb walkthrough's book earns a two-year Sharpe of 12.5 gross and 10.3 net. A colleague wants to put that in a pitch deck. What do you say, and which lessons do survive?

<details markdown="1">
<summary>Answer</summary>

It is a synthetic lab result, explained by the Fundamental Law: an IC of 0.046 across 415 names a day gives 0.046 × √(415 × 252) ≈ 15 before constraints. The planted alphas never decay or crowd, and the toy charges no commissions or borrow; real books of this design net roughly 1–2 `[Lore]`. The lessons survive. Neutralize on the beta you actually trade (the book was neutral on estimated beta but carried \$3.6M of true beta). Judge the risk model on the optimized book, and let costs decide how far to trade. → [Walkthrough: a mid-frequency stat-arb book](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-mid-frequency-stat-arb.md)

</details>

### Q28 (informed). In the ETF market-maker walkthrough, the inventory lean is 0.10 bp per creation unit, not 0.70 bp. Why? And why mark a hedged block against its hedge?

<details markdown="1">
<summary>Answer</summary>

The desk hedges every fill with futures, so the inventory risk it carries is the leftover basis (18.7 bps a day), not the ETF's full volatility (126.5 bps). Leaning on the full volatility would push quotes 3.5 bps off NAV after a five-unit block for no reason: hedge first, then skew what is left. The block's raw markout swung from +20 bps at 60 seconds to −34 bps by the close, which is market noise. Net of the futures hedge it stayed at +8 to +11 bps, close to the spread charged (synthetic lab result). → [Walkthrough: a day at an ETF market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-etf-market-maker.md)

</details>

### Q29 (sharp). The options walkthrough's desk thought it had earned \$20,660 of edge in a week; measured against fair marks it earned \$13,191. Where did the difference go?

<details markdown="1">
<summary>Answer</summary>

To the winner's curse. Customers trade more when the desk's theoretical value is wrong in their favor. With theo error e and half-width h, the expected edge per order falls from h/2 to h/2 − e²/2h, a loss of (e/h)² of the edge. Theo was 0.33 vol points off when fills arrived, and over 12 weeks the desk lost 40% of its intended edge (synthetic lab result). Fast surface refits and spot-vol rules are edge protection, not engineering polish. → [Walkthrough: an options market maker](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md)

</details>

### Q30 (sharp). A broker reports that your \$500M buy "beat VWAP by 43 bps and the close by 131 bps". Implementation shortfall against the decision price says it cost 178.8 bps. Which is right, and what was controllable?

<details markdown="1">
<summary>Answer</summary>

All three are arithmetically right. Only implementation shortfall against the decision price measures the economic loss: a front-loaded buyer in a rising week naturally beats later prices. Of the 178.8 bps, 132.3 was timing (the market rose) and −6.7 was delay. The controllable cost (spread, temporary and permanent impact, commission) was 53.2 bps against a 53.3 bps budget (synthetic lab result, 75th-percentile week). One order cannot rank schedules: across all simulated weeks TWAP beat the risk-averse schedule on 61% of orders. → [Walkthrough: executing a \$500M buy order](../03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md) · [Transaction cost analysis](../03-algorithms/e-execution-algorithms/transaction-cost-analysis.md)

</details>

## Related pages

- [Algorithms: overview](../03-algorithms/index.md)
- [There is no single algorithm](../03-algorithms/there-is-no-single-algorithm.md)
- [Algorithm map](../03-algorithms/algorithm-map.md)
- [Strategy × algorithm matrix](../02-strategies/h-cross-cutting/strategy-x-algorithm-matrix.md)
- [Quiz: Strategies](quiz-02-strategies.md)
- [Labs](../labs.md)
