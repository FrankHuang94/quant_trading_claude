# Quiz: Strategies

> **TL;DR**
>
> - Thirty questions on module 02: the evaluation lens, every strategy family (A. liquidity provision to G. futures and macro) and the five cross-cutting pages (comparison matrix, strategy × algorithm matrix, failure gallery, evolution, how firms combine strategies).
> - About half are conceptual ("why does it pay?", "what breaks it?"), a third are small calculations (breakeven cost, IC × √breadth, hedge ratios, P&L lines) and a fifth are judgment calls. Each is marked basic, informed or sharp.
> - For each strategy, first try to name who pays and why they accept it; most answers start there. Every answer links to the dossier or page that explains it.

**Level:** Core · **Read time:** ~35 min · **Last verified:** 2026-11

## The evaluation lens

### Q1 (basic). Name the six edge sources. Which does the KB expect to be most durable, which least, and why?

<details markdown="1">
<summary>Answer</summary>

Risk premium, behavioral, structural/regulatory, informational, liquidity provision and speed. Edges where the counterparty has a lasting reason to pay (risk premia, liquidity provision, rules and mandates) should last longest. Informational and behavioral signals at days-to-weeks horizons should decay fastest, because they are the easiest to copy (the KB's view, `[Estimate]`). → [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Strategies: the map](../02-strategies/index.md)

</details>

### Q2 (informed). Your book runs at Sharpe 2.0. Candidate C has a standalone Sharpe of 0.6 and correlation −0.3 to the book; candidate D has Sharpe 1.5 and correlation 0.8. Which improves the book?

<details markdown="1">
<summary>Answer</summary>

A small allocation helps only if the candidate's Sharpe exceeds ρ × the book's Sharpe. C's hurdle is −0.3 × 2.0 = −0.6, which 0.6 clears easily; at the optimal mix the book's Sharpe rises to about **2.36**. D's hurdle is 0.8 × 2.0 = 1.6, above its 1.5, so its optimal weight is zero and the book stays at 2.00 (illustrative). The weakest standalone strategy adds the most. → [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

</details>

### Q3 (sharp). A researcher pitches a 1–3 day residual-reversal strategy: 12-year backtest, 200 variants tried, gross Sharpe 3.0, net 1.8 (12% gross alpha, 60× turnover, 8 bp cost), correlation 0.3 to a Sharpe-2.0 book. Do you fund it?

<details markdown="1">
<summary>Answer</summary>

Not as designed. Noise is not the problem: the best of 200 zero-alpha variants would show about 0.8 by luck, below 1.8. The problem is decay, which hits gross alpha while costs stay put. A 30–50% haircut leaves 6.0–8.4% gross against 4.8% of costs, so net Sharpe is 0.3–0.9, straddling the hurdle of 0.3 × 2.0 = 0.6 (a 50% gross haircut is an 83% net haircut). Cut turnover with a no-trade band and trading toward the aim, then fund small capital with kill criteria written before the first trade. → [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

</details>

## A. Liquidity provision

### Q4 (informed). A market maker's benign round trip (600 shares) earns +\$4.50 in spread and rebates; a toxic one, where an informed seller hits its bid, loses \$3.05. If 40% of round trips are toxic, what does it earn per share, and at what toxic share does it break even?

<details markdown="1">
<summary>Answer</summary>

Expected P&L = 0.6 × 4.50 − 0.4 × 3.05 = 2.70 − 1.22 = **\$1.48 per 600 shares, about 0.25¢ a share**, before hedging, clearing and technology. Break-even toxic share p solves (1 − p) × 4.50 = p × 3.05, so p = 4.50 ÷ 7.55 ≈ **60%** (illustrative). The edge is less the quoting formula than fair value and speed: cancelling stale quotes before the informed trader arrives. → [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)

</details>

### Q5 (sharp). In March 2020 the bond ETF LQD closed at a 5.0% discount to its NAV `[Reported]`. A colleague says the ETF "broke". What are the two readings, and how does an ETF market maker price in that situation?

<details markdown="1">
<summary>Answer</summary>

One reading, held by issuers such as Invesco: NAV was built from stale bond marks, the ETF was the true price, and its discount was price discovery. The other, from Haddad, Moreira and Muir (2021): a real dislocation driven by forced selling, larger for safer bonds and erased once the Fed said it could buy bond ETFs. Either way, when the basket is stale or shut the ETF becomes the price: the market maker prices the fund, not its stale NAV. The dossier presents both readings without a verdict. → [ETF market making](../02-strategies/a-liquidity-provision/etf-market-making.md)

</details>

### Q6 (informed). Read an options market maker's P&L as an income statement. Which line is revenue, which is insurance, and why is the daily breakeven move of a short at-the-money position (stock \$100, 25% implied vol) about \$1.57?

<details markdown="1">
<summary>Answer</summary>

Edge (price minus theoretical value) is revenue. Theta minus gamma is the insurance line: implied versus realized volatility. Vega is a mark, and hedging, fees and PFOF are costs. Theta pays for the gamma of a move of one implied daily standard deviation: \$100 × 25% ÷ √252 ≈ **\$1.57**, the move at which ½ × gamma × ΔS² equals one day's theta. In the dossier's illustration one +5% gap with a vol jump costs about 13 days of theta. → [Options market making](../02-strategies/a-liquidity-provision/options-market-making.md)

</details>

### Q7 (basic). What is a retail wholesaler's edge, and what happened to it in the GameStop week of January 2021?

<details markdown="1">
<summary>Answer</summary>

Segmentation: an exchange prices for its average anonymous counterparty, while a wholesaler knows the broker and prices low-toxicity retail flow, so it can improve on the NBBO, pay PFOF and keep a fraction of a cent. The model fails when retail flow turns correlated and informed-looking. GameStop's off-exchange share of dollar volume fell from 62.6% to 32.8% within a week, consistent with wholesalers internalizing less `[Verified]`. → [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

</details>

## B. Speed and structural

### Q8 (basic). Why is latency arbitrage "a race, not a forecast"? Who pays for it, and why do speed bumps only partly help?

<details markdown="1">
<summary>Answer</summary>

Public news (a futures tick, a sweep elsewhere) has already moved fair value; the only question is who reaches the stale quote first. In London data the winner beat the first loser by a modal 5–10 µs `[Verified]`. Sniped quoters pay first and investors pay last, through wider spreads: about 0.5 bp of trading volume, roughly \$5B a year in global equities `[Verified]`. A speed bump such as IEX's protects quotes on one venue only. → [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)

</details>

### Q9 (informed). E-mini S&P futures at 6,000 jump 2.5 points. A \$200 stock (mid \$199.99) has a 100-ms beta of 1.3, which you shrink by half. A stale offer sits at \$200.00 and the take fee is 0.3¢. What is your edge per share?

<details markdown="1">
<summary>Answer</summary>

Leader return = 2.5 ÷ 6,000 = 4.17 bps. Implied move = 0.5 × 1.3 × 4.17 bps × \$200 ≈ \$0.054, so fair value ≈ \$200.044. Lifting the \$200.00 offer earns 4.4¢ − 0.3¢ = **4.1¢ a share**, or \$20.50 on 500 shares; you hedge by selling about four Micro E-minis (illustrative). → [Lead-lag and cross-asset arbitrage](../02-strategies/b-speed-and-structural/lead-lag-and-cross-asset-arbitrage.md)

</details>

### Q10 (sharp). Index arbitrage is said to "belong to the cheapest balance sheet". Why, and what happens to an arbitrageur who trades inside its own no-arbitrage band?

<details markdown="1">
<summary>Answer</summary>

Selling rich futures against a long basket earns the futures' implied financing rate. In the dossier's illustration that rate is 4.33%, so a desk funding at 4.00% nets about 1.5 bps over 60 days, while a desk funding at 4.33% earns nothing. The no-arbitrage band is the cheapest arbitrageur's all-in cost (spreads, impact, fees, financing). Trade inside your own band and you lose: in Lab 07 a fixed trigger at 0 bps lost \$0.53M a year, while a cost-aware rule earned \$0.21M (synthetic lab result). → [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md)

</details>

## C. Statistical arbitrage

### Q11 (informed). A pairs trade's winners net +\$38,833 and its stopped-out losers −\$51,000. What win rate breaks even, and why is a false pair a losing bet?

<details markdown="1">
<summary>Answer</summary>

Break-even win rate = 51,000 ÷ (38,833 + 51,000) ≈ **57%**. If the spread has no leash (a random walk), the chance of reaching the z = −0.5 exit before the z = −4 stop from an entry at −2.2 is only (4 − 2.2) ÷ (4 − 0.5) ≈ 51% (illustrative). A false pair is a coin flip that pays less than it costs. False pairs are common: in Lab 08 about 94% of same-sector pairs passing a 5% cointegration test were false (synthetic lab result). → [Pairs trading and cointegration](../02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md)

</details>

### Q12 (informed). A stock's residual fits an AR(1) with b = 0.90 and innovation sd 1.2%; its centered residual is +4.0% above equilibrium. Compute the mean-reversion time and the s-score. Trade?

<details markdown="1">
<summary>Answer</summary>

Mean-reversion time = 1 ÷ (−ln 0.90) ≈ **9.5 days**, short enough to trade. Equilibrium sd = 1.2% ÷ √(1 − 0.81) ≈ 2.75%, so s = −4.0% ÷ 2.75% ≈ **−1.45**. That is beyond Avellaneda and Lee's 1.25 entry threshold: buy and hedge the factors (illustrative). Expect far less than the model's ~2% gain: in Lab 09 the s-score's IC was 0.013, and the market paid about a tenth of the model's expectation (synthetic lab result). → [Factor-residual mean reversion](../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md)

</details>

### Q13 (informed). Short-term reversal has the highest gross Sharpe of the classic anomalies and the thinnest net. Why, and what keeps it alive?

<details markdown="1">
<summary>Answer</summary>

It is a fee for absorbing temporary price pressure, earned at 50–100× annual turnover, so costs decide everything. The plain French reversal factor's Sharpe fell from 0.92 (1963–1991) to 0.01 (2010–2026) `[Verified]`. In the dossier's illustrative \$500M book a naive weekly rebalance nets −\$0.22M a week. Buffering trades and executing patiently turns that into +\$0.34M, a Sharpe near 1: only the trading changed. Residualized, news-filtered versions inside multi-signal books survive. → [Short-term cross-sectional reversal](../02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md)

</details>

### Q14 (sharp). An ML team's 30-minute forecast has a rank IC of 0.03, better than its 1-day forecast's 0.02. They want to trade the 30-minute signal on its own. What do you tell them?

<details markdown="1">
<summary>Answer</summary>

Expected return per leg is IC × residual σ × 1.4 for the top quintile: 0.03 × 0.40% × 1.4 ≈ 1.7 bps at 30 minutes, against 0.02 × 1.50% × 1.4 ≈ 4.2 bps at one day (illustrative). Round trips cost 5.4 bps aggressive and 2.5 bps passive, so the faster signal nets −0.8 bps at best while the slower one nets +1.7. The 30-minute forecast is more accurate but loses on its own. Use it to time the slower forecasts' trades, with costs inside the optimizer's objective. → [ML-driven short-horizon alpha](../02-strategies/c-statistical-arbitrage/ml-driven-short-horizon-alpha.md)

</details>

## D. Mid-frequency alpha

### Q15 (informed). A sector-neutral book holds A +\$20.8M (beta 1.4) and C +\$29.2M (beta 1.1), and is short B −\$20.8M (beta 1.3) and D −\$29.2M (beta 0.9). What is its net beta exposure, and what does a 2% market drop cost?

<details markdown="1">
<summary>Answer</summary>

Net beta dollars = 20.8 × 1.4 + 29.2 × 1.1 − 20.8 × 1.3 − 29.2 × 0.9 ≈ **+\$7.9M**, so a 2% drop costs about **\$158k** (illustrative). Sector-neutral is not beta-neutral. Add beta to the neutralization regression or hedge with about \$7.9M of index futures. → [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

</details>

### Q16 (sharp). A PM wants to run post-earnings announcement drift in large caps, citing Bernard and Thomas's 4.2% over 60 days. What do you say?

<details markdown="1">
<summary>Answer</summary>

That result covers 1974–1985. Martineau (2022) finds the drift gone outside microcaps since 2006; 2025 papers dispute that, so the question is open. Execution costs are certain either way: on a \$5M position, entering on event days (10 bps spread, 15 bps impact) and exiting at 10 bps costs \$17,500. So a trade that nets +\$82,500 if a 2% drift exists loses \$17,500 if it does not (illustrative). Test it on recent large-cap data with event-day costs before committing capital. → [Earnings and event-driven](../02-strategies/d-mid-frequency-alpha/earnings-and-event-driven.md)

</details>

### Q17 (basic). Who pays a flow-driven trader around index additions, and why has the S&P 500 inclusion effect shrunk?

<details markdown="1">
<summary>Answer</summary>

Index funds must buy on the effective date whatever the price; their "index turnover cost" was at least 21–28 bp a year for the S&P 500 over 1990–2005 (Petajisto) `[Verified]`. The rules are public, so crowding shrinks the effect and pulls it earlier. Additions averaged +7.4% in the 1990s but under 1% in the 2010s (Greenwood and Sammon 2025) `[Verified]`. Trading announced changes is not front-running: no client order is involved. → [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md)

</details>

### Q18 (sharp). What is the signature backtest trap for LLM-based text signals, and why does fast news have little capacity?

<details markdown="1">
<summary>Answer</summary>

Pretraining look-ahead: a model trained on text through year Y has effectively read what happened next, so only backtests on data after its training cutoff are clean. Time-stamped models suggest the bias is modest but real, and the edge shrinks as adoption rises (Lopez-Lira and Tang, *JFE* 2026). Fast news is a latency race: in the dossier's illustrative ladder, the same correct reading is worth six times more acted on in one second than in one hour. Slow text has more capacity but is crowded. → [NLP and LLM signals](../02-strategies/d-mid-frequency-alpha/nlp-and-llm-signals.md)

</details>

## E. Risk premia and factors

### Q19 (basic). A manager earns 9.0% a year over cash with market beta 0.9. Its loadings are 0.3 on value, 0.4 on profitability and 0.2 on momentum; the premia are market 7.2%, value 3.5%, profitability 3.0% and momentum 7.3%. What is its alpha?

<details markdown="1">
<summary>Answer</summary>

CAPM alpha = 9.0 − 0.9 × 7.2 = **+2.5%**. Subtract factor exposures of 0.3 × 3.5 = 1.05, 0.4 × 3.0 = 1.20 and 0.2 × 7.3 = 1.46: multi-factor alpha = **−1.2%** (illustrative). The "alpha" was factor beta, available from a style-premia fund for a fraction of the fee; allocators run exactly this regression. → [Factor investing fundamentals](../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md)

</details>

### Q20 (informed). Why does momentum crash in sharp market rebounds, and what is the standard defense?

<details markdown="1">
<summary>Answer</summary>

After a fall, past losers are high-beta stocks, so a dollar-neutral momentum book is net short the market. With winners at beta 0.6 and losers at 1.8, \$1B a side carries −\$1.2B of beta; a 15% rebound costs \$180M, about 30 months of premium (illustrative). Daniel and Moskowitz find loser betas above 3 after major declines `[Verified]`. Defenses: hedge the beta and scale by volatility, which roughly doubled momentum's Sharpe in the KB's 1927–2026 replication. → [Momentum](../02-strategies/e-risk-premia-and-factors/momentum.md)

</details>

### Q21 (sharp). A factor fund runs \$1,000M of NAV at 8× gross under an 8× prime-broker cap. Its spread loses 3%, then 2%, then rebounds 5%. Compare holding with de-levering to the cap. What should the fund have done differently?

<details markdown="1">
<summary>Answer</summary>

Holding without trading ends flat (−\$120M − \$80M + \$200M). De-levering to the cap forces \$960M of selling after day 1 and \$563M after day 2, so the rebound is earned on a smaller book. After \$5M of costs NAV ends at \$967M: **−3.3%** (illustrative). Selling at the bottom locks in losses the unlevered trade recovers. The defense comes beforehand: lower leverage, de-grossing rules agreed in advance, diversification and volatility targeting, not heroic factor timing. → [Factor timing, crowding and quant winters](../02-strategies/e-risk-premia-and-factors/factor-timing-crowding-and-quant-winters.md)

</details>

## F. Volatility and derivatives

### Q22 (informed). You are short a one-month S&P 500 variance swap with \$100,000 of vega notional at a strike of 18. What do you make if realized volatility is 14, and lose if it is 30?

<details markdown="1">
<summary>Answer</summary>

Variance notional = 100,000 ÷ (2 × 18) ≈ \$2,778 per variance point; P&L = 2,778 × (18² − realized²). At 14: 2,778 × (324 − 196) ≈ **+\$356K**. At 30: 2,778 × (324 − 900) ≈ **−\$1.60M** (illustrative). With a 2.5× cap a crash month costs about \$4.73M and erases 13 calm months. That is the shape of selling insurance. → [Volatility risk premium and vol arb](../02-strategies/f-volatility-and-derivatives/volatility-risk-premium-and-vol-arb.md)

</details>

### Q23 (informed). What is a dispersion trade really short, and why can an equal-vega book that is net long volatility still lose heavily in a crash?

<details markdown="1">
<summary>Answer</summary>

Index variance is roughly average stock variance times average correlation. Selling index volatility and buying constituent volatility is therefore a bet that stocks move together less than options imply: a short position in implied correlation. In a crash correlation jumps, and the index leg's loss outruns the stock legs' gain. In the dossier's illustration a crash with correlation at 0.70 nets −\$17.9M. One-month implied correlation went from 2.9 to 39.6 between 12 July and 5 August 2024 `[Verified]`. → [Dispersion and correlation trading](../02-strategies/f-volatility-and-derivatives/dispersion-and-correlation-trading.md)

</details>

## G. Futures and macro context

### Q24 (informed). A trend follower sizes each market to 2.5% of NAV in standalone volatility. Why does it hold 125% of NAV in 2-year Treasury futures but only 5% in S&P 500 futures, and what does that imply on a reversal day?

<details markdown="1">
<summary>Answer</summary>

Volatility targeting: notional = risk budget ÷ volatility (× signal). At 2% volatility the 2-year note needs 2.5 ÷ 2 = 125% of NAV; the S&P future at 16% volatility and a weak +1/3 signal needs only 1/3 × 2.5 ÷ 16 ≈ 5.2%. Low-volatility rate futures carry the most notional, so when bonds rally 1.0% and 1.5% against short positions, the book loses about 1.9% of NAV in a day (illustrative). → [Trend following and CTAs](../02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md)

</details>

### Q25 (informed). What does carry pay for, and why should a US equity quant care about yen carry?

<details markdown="1">
<summary>Answer</summary>

Largely crash risk: carry earns a steady coupon and loses in every asset class at once in global recessions. AUD/JPY fell 46% in about three months of 2008, roughly 11 years of carry `[Verified]`. For an equity quant, carry is a risk-on/risk-off input and a hidden correlation in multi-strategy books. The August 2024 yen-carry unwind hit equities, volatility sellers and dispersion books together. → [Carry and cross-asset risk premia](../02-strategies/g-futures-and-macro-context/carry-and-cross-asset-risk-premia.md) · [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)

</details>

## H. Cross-cutting

### Q26 (basic). On a chart of capacity against Sharpe, the high-capacity, high-Sharpe corner is nearly empty. Why? And which numbers in the comparison matrix are the most reliable?

<details markdown="1">
<summary>Answer</summary>

Market impact. Under the square-root law, cost per dollar traded rises with the square root of size, so total cost grows like size^1.5 while gross alpha grows like size; profit peaks at 4/9 of the break-even size. Fast strategies trade their books 50–250 times a year and hit that wall early. The most reliable numbers are the lowest: slow factor Sharpe ratios are `[Verified]` from decades of public data, while most market-making and speed figures are `[Lore]`. → [Strategy comparison matrix](../02-strategies/h-cross-cutting/strategy-comparison-matrix.md)

</details>

### Q27 (informed). In the strategy × algorithm matrix, which card do the most strategies use, and why are execution and validation cards rarely "core" yet nearly everywhere?

<details markdown="1">
<summary>Answer</summary>

P5, the transaction cost and impact model: 18 dossiers, 11 of them core, and the only card that reaches six of the seven families. Anything that trades enough to move prices needs a cost forecast. Execution, validation and live-monitoring cards fill 99 cells but only 5 core: they are where a strategy leaks money, not where it earns it. Slippage and overfitting decide how much of the signal's edge survives. → [Strategy × algorithm matrix](../02-strategies/h-cross-cutting/strategy-x-algorithm-matrix.md)

</details>

### Q28 (sharp). It is the close on 9 August 2007. Your stat-arb book, levered 8:1, is down about a quarter of its capital in three days, and risk wants to halve gross overnight. What does the record say, and what was the real mistake?

<details markdown="1">
<summary>Answer</summary>

Khandani and Lo's base strategy lost 6.85% unlevered over 7–9 August, about −25% at 8:1, then made 5.92% on 10 August and ended the week −0.43% `[Verified]`. Funds that de-grossed at the bottom handed the rebound to buyers with balance sheet. But nobody knew on 9 August that it would reverse, and a 12-sigma loss means the model was wrong. The real mistake came earlier. The strategy's daily return had decayed from 1.38% (1995) to 0.13% (2007), so matching old returns took about 9:1 leverage, in crowded positions, with no pre-agreed de-grossing rules. → [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md) · [Stat arb: overview and history](../02-strategies/c-statistical-arbitrage/stat-arb-overview-and-history.md)

</details>

### Q29 (informed). A signal's alpha halves every three years. What fraction does it lose each year, and how should a firm account for that?

<details markdown="1">
<summary>Answer</summary>

Annual loss = 1 − 0.5^(1/3) ≈ **21%**; with a two-year half-life, 1 − 0.5^(1/2) ≈ 29% (illustrative). The book needs that much new alpha every year just to stand still. Treat a signal as an amortizing intangible and research as maintenance capex. Haircut backtests by 30–60% `[Lore]`, bracketing McLean and Pontiff's −26% out of sample and −58% after publication `[Verified]`. → [Evolution of quant strategies](../02-strategies/h-cross-cutting/evolution-of-quant-strategies.md)

</details>

### Q30 (sharp). A multi-manager platform hires pods with Sharpe 0.8 each and average pairwise correlation 0.05. What is the book's Sharpe with 10 pods, what is the ceiling, and what is the platform's central risk?

<details markdown="1">
<summary>Answer</summary>

Book Sharpe = S × √(N ÷ (1 + (N − 1)ρ)) = 0.8 × √(10 ÷ 1.45) ≈ **2.10**. As N grows it approaches S ÷ √ρ = 0.8 ÷ 0.224 ≈ **3.58** (illustrative). If crowding lifts ρ to 0.20, the ceiling falls to 1.79. So the central risk is correlation: pods hire from the same talent pool, buy the same data and hedge the same factors. → [How firms combine strategies](../02-strategies/h-cross-cutting/how-firms-combine-strategies.md)

</details>

## Related pages

- [Strategies: the map](../02-strategies/index.md)
- [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)
- [Strategy comparison matrix](../02-strategies/h-cross-cutting/strategy-comparison-matrix.md)
- [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)
- [Quiz: Algorithms](quiz-03-algorithms.md)
- [Quiz: Market structure](quiz-01-market-structure.md)
