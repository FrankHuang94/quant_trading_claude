# Quiz: Start here

> **TL;DR**
>
> - Twelve questions on module 00: firm types, the two coordinates (horizon and edge source), the pipeline, who pays, and the cheat sheet's formulas and misused terms.
> - About half are conceptual, a third are small calculations and the rest are judgment calls. Each is marked basic, informed or sharp.
> - Answer out loud or on paper before you open the answer. Every answer links to the page that explains it.

**Level:** Core · **Read time:** ~10 min · **Last verified:** 2026-11

## Firm types and who pays

### Q1 (basic). Which two coordinates does this KB use to place any quant trading business, and what do they predict?

<details markdown="1">
<summary>Answer</summary>

**Holding horizon** (microseconds to months) and **edge source** (speed, liquidity provision, structural/regulatory, informational, behavioral or risk premium). Together they predict the capital source, capacity, Sharpe ratio and how the strategy dies. Firm type, the third axis, describes the business model and whose capital is at risk. → [The big picture](../00-start-here/the-big-picture.md)

</details>

### Q2 (basic). Name the pipeline stages every quant strategy runs. How does the pipeline differ between an electronic market maker and a factor manager?

<details markdown="1">
<summary>Answer</summary>

Data → signals → forecast → portfolio → orders → fills → P&L, with P&L feeding back into signal research. A market maker closes the loop in microseconds, and "portfolio" shrinks to inventory skew. A factor manager closes it monthly, and the optimizer dominates. The stages are the same; only the clock speed changes. → [The big picture](../00-start-here/the-big-picture.md) · [There is no single algorithm](../03-algorithms/there-is-no-single-algorithm.md)

</details>

### Q3 (basic). "Who pays you, and why do they accept it?" Answer it for a market maker, a latency arbitrageur, a factor manager and an agency execution desk.

<details markdown="1">
<summary>Answer</summary>

- **Market maker:** impatient traders pay the half-spread for immediacy (Grossman and Miller's framing).
- **Latency arbitrageur:** slow quoters whose stale quotes get sniped pay first; investors pay in the end, through wider spreads.
- **Factor manager:** investors who want to shed risks they dislike (crashes, distress, leverage constraints) pay a premium.
- **Agency desk:** institutions pay commissions to have orders worked. No alpha is sought.

→ [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md) · [The big picture](../00-start-here/the-big-picture.md)

</details>

### Q4 (informed). Why do the largest market makers rarely take outside money, while factor managers compete on fees?

<details markdown="1">
<summary>Answer</summary>

Liquidity and speed businesses earn tens of billions on balance sheets of a few billion each, because they recycle capital many times a day. Their limit is capacity, not capital, so outside money adds little. Forecasting and premia businesses earn single-digit to low-teens percent on hundreds of billions, so scale and fees are the business `[Estimate]`. → [The big picture](../00-start-here/the-big-picture.md) · [Strategy comparison matrix](../02-strategies/h-cross-cutting/strategy-comparison-matrix.md)

</details>

### Q5 (informed). A friend says HFT firms "front-run" index funds by buying stocks before an announced index addition takes effect. Is that front-running?

<details markdown="1">
<summary>Answer</summary>

Not as a quant or regulator uses the term. Front-running means trading ahead of a known client order; FINRA Rule 5270 covers imminent block transactions `[Verified]`. Trading ahead of public, predictable flows such as announced index changes is flow-driven trading. The index funds' cost is the price of following a public rule. → [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md) · [Flow-driven strategies](../02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md)

</details>

### Q6 (informed). A market maker is short options and delta-hedges them. What is the position betting on, and how does a day's P&L behave?

<details markdown="1">
<summary>Answer</summary>

It earns theta and pays gamma: P&L per step ≈ ½ × Γ × S² × (implied variance − realized variance) × dt. So it is a bet that implied variance exceeds realized variance. Quiet days pay a little theta; a large move costs gamma, which grows with the square of the move. A long, delta-hedged option position has the opposite sign. → [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md) · [Hedging algorithms](../03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md)

</details>

## Formulas and numbers

### Q7 (informed). A signal has a daily IC of 0.01, and the book makes about 50,000 independent bets a year. What information ratio does the Fundamental Law predict, and what happens with a transfer coefficient of 0.5?

<details markdown="1">
<summary>Answer</summary>

IR ≈ IC × √breadth = 0.01 × √50,000 ≈ 0.01 × 224 ≈ **2.2** before costs. With a transfer coefficient of 0.5, constraints let half the forecast through: IR ≈ **1.1**. Breadth counts independent bets, not trades; correlated bets cut it further. → [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

</details>

### Q8 (informed). A strategy earns 12% gross alpha a year on its gross market value and turns over 60 times a year. What is its breakeven cost per dollar traded, and what does each extra basis point of cost cost you?

<details markdown="1">
<summary>Answer</summary>

Breakeven c* = α ÷ T = 12% ÷ 60 = **20 bp** per dollar traded. Net alpha is α − T × c, so each extra basis point of cost subtracts 60 bp, or **0.6% a year**. At a modeled 8 bp the net is 12% − 4.8% = 7.2%. → [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

</details>

### Q9 (informed). A strategy's true Sharpe ratio is 0.75. Roughly how many years of daily data do you need before its t-statistic reaches 2?

<details markdown="1">
<summary>Answer</summary>

t ≈ Sharpe × √years, so √years = 2 ÷ 0.75 = 2.67 and years ≈ **7**. That is why a few months of live P&L cannot prove an alpha; they can only show that the implementation works. → [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)

</details>

### Q10 (sharp). A strategy earns 7% excess return at 10% volatility. What leverage does the Kelly criterion give, why do practitioners run half Kelly or less, and what happens if the true Sharpe is half the estimate?

<details markdown="1">
<summary>Answer</summary>

Kelly leverage is μ ÷ σ² = 0.07 ÷ 0.01 = **7×**. Growth is fμ − f²σ²/2, so half Kelly (3.5×) earns 18.4% a year against 24.5% at full Kelly: 75% of the growth at half the volatility. If the true Sharpe is 0.35, true Kelly is 3.5×, so running 7× means running twice true Kelly. Expected growth is then zero, and in the page's model a 50% drawdown becomes certain (illustrative). → [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md) · [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md)

</details>

## Judgment

### Q11 (sharp). A PM describes her book as "market neutral: \$500M long, \$500M short." What do you ask, and what could go wrong?

<details markdown="1">
<summary>Answer</summary>

Dollar-neutral is not market-neutral. If the longs have beta 0.8 and the shorts 1.2, the book carries −\$200M of beta, and a +1% market day loses about \$2M (illustrative). Ask whether the book is also beta-neutral and factor-neutral (sector, style), and how the betas are estimated. Dollar-neutral books can hide factor bets. → [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md) · [Cross-sectional alpha and neutralization](../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

</details>

### Q12 (sharp). An HFT market maker and a monthly factor fund each claim "Sharpe 3". Which claim is more plausible, and what facts do you need before either number means anything?

<details markdown="1">
<summary>Answer</summary>

The market maker's. Annualized Sharpe scales with the square root of independent bets per year: a daily Sharpe of 0.2 already annualizes to 0.2 × √252 ≈ 3.2. The price is small capacity. A monthly factor book at 3 would be far above the net 0.3–0.7 that risk-premia books show. For either claim, ask whether it is gross or net, over what period, backtest or live, and how many variants were tried. → [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md) · [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md) · [Strategy comparison matrix](../02-strategies/h-cross-cutting/strategy-comparison-matrix.md)

</details>

## Related pages

- [The big picture](../00-start-here/the-big-picture.md)
- [Learning paths](../00-start-here/learning-paths.md)
- [One-page cheat sheet](../00-start-here/one-page-cheat-sheet.md)
- [How quants evaluate a strategy](../02-strategies/how-quants-evaluate-a-strategy.md)
- [There is no single algorithm](../03-algorithms/there-is-no-single-algorithm.md)
- [Quiz: Market structure](quiz-01-market-structure.md)
