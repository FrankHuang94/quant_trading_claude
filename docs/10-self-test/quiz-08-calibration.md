# Quiz: Calibration

> **TL;DR**
>
> - 14 questions on module 08: myths, contested debates and the back-of-envelope checks for claims and backtests.
> - About half are numeric. Do them on paper first; every formula you need is on [sanity-checking claims](../08-calibration/sanity-checking-claims.md).
> - Difficulty: **basic** (you read the page), **informed** (you can apply it), **sharp** (you could challenge a pitch with it). Each answer links to the page that explains it.

**Level:** Core · **Read time:** ~10 min · **Last verified:** 2026-11

## Myths vs reality

### Q1 (basic). Most myths about quant trading take a true mechanism and drop one ingredient. Name the five ingredients that usually go missing.

<details markdown="1">
<summary>Answer</summary>

The costs, the number of trials, the tail, the counterparty, and capacity and crowding. A gross Sharpe without costs, a backtest without its trial count, a smooth return stream without its crash, a profit without anyone named who pays it, or a result without its size is each half a claim. The fix is to ask for the missing ingredient. → [Myths vs reality](../08-calibration/myths-vs-reality.md)

</details>

### Q2 (basic). A colleague says published anomalies are a reliable source of returns. What does the evidence say, and what haircut is sensible?

<details markdown="1">
<summary>Answer</summary>

Across 97 predictors, McLean and Pontiff (2016) found returns 26% lower out of sample and 58% lower after publication. Part of that is statistical bias in the original papers and part is investors trading the signal away. The KB's rule of thumb is to haircut academic gross returns by a third to a half before costs. → [Myths vs reality](../08-calibration/myths-vs-reality.md)

</details>

### Q3 (informed). An execution report says an order "beat VWAP". Why is that weak evidence of good execution, and what benchmark should you ask for?

<details markdown="1">
<summary>Answer</summary>

VWAP is easy to beat because your own trades are part of the average. In Lab 17 an order that cost 12.8 bps against the arrival price looked like 8.2 bps against interval VWAP (synthetic lab result). Ask for implementation shortfall against the arrival price, which measures what the decision to trade actually cost. → [Myths vs reality](../08-calibration/myths-vs-reality.md)

</details>

### Q4 (informed). Is a market-neutral stat-arb book close to riskless? Use the August 2007 numbers.

<details markdown="1">
<summary>Answer</summary>

No. Market neutrality removes beta, not the risk that many funds hold the same positions and unwind together. Khandani and Lo's simple contrarian strategy lost 6.85% unlevered over three days of August 2007; at the roughly 9:1 leverage it by then needed to match its 1998 return, that is about 62% of equity. Stat arb has positive expectation and a fat crowding tail. → [Sanity-checking claims](../08-calibration/sanity-checking-claims.md)

</details>

### Q5 (basic). A market maker cancels 95% of its orders. Is that spoofing?

<details markdown="1">
<summary>Answer</summary>

Not by itself. Market makers cancel most orders because their quotes must follow fair value as it moves. US commodities law defines spoofing as bidding or offering with intent to cancel before execution, so intent is the line, not the cancel rate; the 2015 Sarao case turned on layered orders he allegedly never meant to fill. → [Myths vs reality](../08-calibration/myths-vs-reality.md)

</details>

### Q6 (informed). Someone calls S&P 500 index inclusion a "free 5–8% pop". What has happened to the effect?

<details markdown="1">
<summary>Answer</summary>

Greenwood and Sammon (2025) measure the inclusion effect at 7.4% in the 1990s and under 1% in the 2010s. Announcements are public and heavily traded, so what remains is mostly pay for supplying liquidity to index funds at the close. It is now a liquidity-provision trade, not an information edge. → [Myths vs reality](../08-calibration/myths-vs-reality.md)

</details>

## Back-of-envelope checks

### Q7 (informed). A strategy shows an annual Sharpe ratio of 1.0 over five years of daily data. Roughly what are its standard error and t-statistic?

<details markdown="1">
<summary>Answer</summary>

Using Lo's approximation, SE ≈ √((1 + S²/2) / T) = √(1.5 / 5) ≈ 0.55, and t ≈ S × √T = 1.0 × √5 ≈ 2.2. A five-year Sharpe of 1.0 is only just distinguishable from zero, and serial correlation or fat tails widen the error further. → [Sanity-checking claims](../08-calibration/sanity-checking-claims.md)

</details>

### Q8 (informed). A researcher tried 100 zero-skill variants on five years of data and kept the best. What Sharpe should the winner show by luck alone?

<details markdown="1">
<summary>Answer</summary>

The expected maximum of 100 standard normals is about 2.5, so the best variant shows roughly 2.5 ÷ √5 ≈ 1.1. That is why a backtest Sharpe means little without its trial count. The deflated Sharpe ratio formalizes this hurdle and adjusts for skew and kurtosis. → [Sanity-checking claims](../08-calibration/sanity-checking-claims.md)

</details>

### Q9 (informed). A manager claims "never a down year". What does that imply about the Sharpe ratio, assuming roughly normal annual returns?

<details markdown="1">
<summary>Answer</summary>

The chance of a losing year is about Φ(−S): 31% at a Sharpe of 0.5, 16% at 1.0 and 2% at 2.0. A long run of positive years therefore implies a high Sharpe, or something else: short volatility, stale marks or a short sample. It is a prompt to ask for the worst month and the skew, not proof of skill. → [Sanity-checking claims](../08-calibration/sanity-checking-claims.md)

</details>

### Q10 (informed). A book makes 8% gross alpha a year and turns over 40 times a year. What is its breakeven cost, and is it safe if the modeled cost is 12 bps per dollar traded?

<details markdown="1">
<summary>Answer</summary>

Breakeven cost is gross alpha ÷ turnover = 8% ÷ 40 = 0.2%, or 20 bps per dollar traded (illustrative numbers). The modeled 12 bps sits within 2× of breakeven, which the checklist treats as a red flag: a modest underestimate of impact would erase most of the net alpha. → [Sanity-checking claims](../08-calibration/sanity-checking-claims.md)

</details>

### Q11 (sharp). A pitch claims net Sharpe 2.5 from a monthly-rebalanced book of 500 US large caps over 2010–2024, with a transfer coefficient of 0.5. What IC does the Fundamental Law require, and what is your verdict?

<details markdown="1">
<summary>Answer</summary>

Breadth is at most 500 × 12 = 6,000 bets a year, so √BR ≈ 77 and IC = 2.5 ÷ (0.5 × 77) ≈ 0.065, or about 0.13 if correlation cuts effective breadth to 1,500. An IC near 0.05 on a broad monthly composite is usually called good, so the claim needs two to three times that, every month, after costs. Luck does not explain it (t ≈ 9.7 over 15 years), so suspect look-ahead, survivorship or an unpriced tail, and ask for point-in-time data lineage, delisting returns and net Sharpe at the target size. → [Sanity-checking claims](../08-calibration/sanity-checking-claims.md)

</details>

## Contested debates

### Q12 (informed). Why can't a decade of data settle whether the value premium is dead? Give the arithmetic.

<details markdown="1">
<summary>Answer</summary>

At a true Sharpe of 0.3, reaching t = 2 takes about (2 ÷ 0.3)² ≈ 44 years of data. HML's gross Sharpe was −0.06 over 2010–2026, yet Fama and French cannot reject equal expected premiums across the two halves of their sample because monthly premiums are so volatile. The "cyclical" camp also points to HML's 68% rebound from October 2020 to December 2022. → [Contested debates](../08-calibration/contested-debates.md#4-value-dead-or-cyclical)

</details>

### Q13 (sharp). Give the strongest evidence on each side of "machine learning beats linear models for stock returns", and say why it stays open.

<details markdown="1">
<summary>Answer</summary>

For ML: Gu, Kelly and Xiu (2020) found trees and neural nets doubled monthly out-of-sample R² (0.33–0.40% against 0.16%). Against: Avramov, Cheng and Metzker (2023) show much of the deep-learning profit comes from microcaps, distressed stocks and volatile periods, and fades with exclusions or reasonable costs. It stays open because the advantage is a few tenths of a percent of R², concentrated where costs are highest, and studies differ in universe, horizon and costs. → [Contested debates](../08-calibration/contested-debates.md#5-machine-learning-versus-linear-models)

</details>

### Q14 (sharp). A journalist asks whether payment for order flow hurts retail investors. How do you answer without claiming more than the evidence supports?

<details markdown="1">
<summary>Answer</summary>

Give both sides. Dyhrberg, Shkilko and Werner estimate wholesaler price improvement saves retail close to \$1B a month versus exchange execution; Schwarz et al. (2025) found round-trip costs from 0.07% to 0.46% across six accounts placing simultaneous orders, unexplained by PFOF levels. Every study needs a counterfactual (an NBBO that odd lots beat, an auction that does not exist), which is why the question stays open. → [Contested debates](../08-calibration/contested-debates.md#2-payment-for-order-flow)

</details>

## Related pages

- [Myths vs reality](../08-calibration/myths-vs-reality.md)
- [Contested debates](../08-calibration/contested-debates.md)
- [Sanity-checking claims](../08-calibration/sanity-checking-claims.md)
- [Overfitting and multiple testing](../03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md)
- [Evaluating signals](../03-algorithms/a-data-and-signals/evaluating-signals.md)
- [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)
