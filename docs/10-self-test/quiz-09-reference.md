# Quiz: Reference

> **TL;DR**
>
> - 14 questions on module 09: glossary terms you should be able to define precisely, which book, paper, talk or blog to reach for, and the caveats that come with each source.
> - The point is not memorizing citations. It is knowing where to look and what a source can and cannot prove.
> - Difficulty: **basic** (you read the page), **informed** (you can apply it), **sharp** (you could defend the choice to a quant). Each answer links to the page that explains it.

**Level:** Core · **Read time:** ~9 min · **Last verified:** 2026-11

## Glossary

### Q1 (basic). Define a markout, and say at what horizons market makers usually measure it.

<details markdown="1">
<summary>Answer</summary>

A markout is the P&L of a fill marked to a later reference price: for a buy at P, the mid at time t + h minus P (sign-flipped for sells), usually in basis points or ticks. Horizons run from about 100 milliseconds to five minutes. Markout curves by venue, counterparty and order type are the main diagnostic of adverse selection. → [Glossary: markout](../09-reference/glossary.md#markout)

</details>

### Q2 (informed). Purging and embargo both protect cross-validation. What does each one remove, and why are both needed?

<details markdown="1">
<summary>Answer</summary>

Purging removes training observations whose label intervals overlap the test fold's labels, for example 20-day forward returns that straddle the fold boundary. The embargo drops a buffer of observations just after each test fold, because features built on serially correlated data can still carry test information; López de Prado suggests about 1% of the sample. Without them, out-of-sample scores are inflated. → [Glossary: purged cross-validation](../09-reference/glossary.md#purged-cross-validation)

</details>

### Q3 (informed). Using the square-root law with Y = 1, what does buying 10% of a day's volume cost in a stock with 2% daily volatility? What happens to cost per share if you double the order?

<details markdown="1">
<summary>Answer</summary>

Impact ≈ Y × σ × √(Q/V) = 1 × 2% × √0.1 ≈ 0.6% (illustrative). Doubling the order multiplies cost per share by √2, about 41% more, so total cost rises about 2.8×. This concavity is why capacity is finite and why large orders are spread over days. → [Glossary: square-root law](../09-reference/glossary.md#square-root-law)

</details>

### Q4 (informed). In the Avellaneda-Stoikov model, what is the reservation price, and what happens to a market maker's quotes when it is long inventory?

<details markdown="1">
<summary>Answer</summary>

It is the price at which the market maker is indifferent between keeping its inventory and trading one more unit: r = s − qγσ²(T − t), with inventory q, risk aversion γ and volatility σ. Long inventory lowers r, so both quotes shift down (quote skew), making a sale more likely and a further purchase less likely. Production quoters apply the same idea with empirically tuned skew per unit of inventory. → [Glossary: reservation price](../09-reference/glossary.md#reservation-price)

</details>

### Q5 (informed). Why is breadth in the Fundamental Law usually overstated?

<details markdown="1">
<summary>Answer</summary>

Breadth counts independent bets per year, and real bets are correlated: 500 stocks that load on one sector are not 500 bets, and a slow signal rebalanced daily is not 252 bets a year. Overstated breadth is the main reason Fundamental Law information ratios come out too optimistic. → [Glossary: breadth](../09-reference/glossary.md#breadth)

</details>

## Books

### Q6 (basic). A colleague new to the field wants three books. Which does the KB recommend, and what does each give them?

<details markdown="1">
<summary>Answer</summary>

Narang's *Inside the Black Box* for the map of a systematic firm, written without math; Grinold and Kahn's *Active Portfolio Management* for the logic of a cross-sectional book (IC, breadth, the Fundamental Law); and Harris's *Trading and Exchanges* for who is on the other side of every trade. Harris predates Reg NMS, so its venue details are dated, but its economics hold. → [Books](../09-reference/books.md)

</details>

### Q7 (informed). You want one book that walks the stat-arb pipeline from market data through forecasting, combining, risk, costs and portfolio construction to simulation. Which, and what is the catch?

<details markdown="1">
<summary>Answer</summary>

Isichenko's *Quantitative Portfolio Management* (2021), the closest thing to a stat-arb operator's manual; its chapters follow the same pipeline as this KB. The catch is difficulty: it is ★★★, written by a physicist and dense. → [Books](../09-reference/books.md)

</details>

### Q8 (informed). Which chapters of López de Prado's *Advances in Financial Machine Learning* matter most for validating a strategy?

<details markdown="1">
<summary>Answer</summary>

Chapter 7 (cross-validation in finance: purging and embargo) and chapters 11–14 (backtesting, combinatorial purged cross-validation and backtest statistics), plus chapter 3 (labeling), chapter 4 (sample weights), chapter 10 (bet sizing) and chapter 16 (hierarchical risk parity). Its validation chapters are much more widely used than its feature recipes `[Lore]`. → [Books](../09-reference/books.md)

</details>

### Q9 (sharp). Someone cites *The Man Who Solved the Market* as proof of Medallion's returns. What is the right way to use that book, and what should an options-desk new hire read instead for their own job?

<details markdown="1">
<summary>Answer</summary>

Zuckerman's book is good history and culture, but every firm detail in it is journalism, not disclosure, so treat its figures as `[Reported]` at best. An options new hire starts with Natenberg's *Option Volatility and Pricing* (★), then Sinclair's *Volatility Trading* (★★) and Gatheral's *The Volatility Surface* (★★★). → [Books](../09-reference/books.md)

</details>

## Papers

### Q10 (informed). What does VPIN measure, and what is the caveat?

<details markdown="1">
<summary>Answer</summary>

VPIN (Easley, López de Prado and O'Hara 2012) is a volume-clock measure of flow toxicity (how informed order flow is, and so how likely it is to move prices against a liquidity provider), and its authors argued it rose before the 2010 Flash Crash. Andersen and Bondarenko (2014) found its apparent warning depends on trade-classification and volume-bucket choices and has little incremental predictive power. The debate is unresolved, so cite VPIN as a contested measure, not a proven early-warning signal. → [Papers](../09-reference/papers.md)

</details>

### Q11 (informed). Glosten-Milgrom and Kyle are both 1985 papers on informed trading. What does each contribute to how a market maker thinks?

<details markdown="1">
<summary>Answer</summary>

Glosten and Milgrom show a spread can exist from adverse selection alone: the bid and ask are the expected value conditional on a sell or a buy, which is the theory behind every markout. Kyle shows an informed trader hiding in noise flow, with prices moving linearly in net order flow at slope λ ("Kyle's lambda"), the root of linear impact and order-flow signals. → [Papers](../09-reference/papers.md)

</details>

### Q12 (sharp). On the factor-replication debate, which two papers anchor the opposing sides, and why do they disagree?

<details markdown="1">
<summary>Answer</summary>

Hou, Xue and Zhang (2020) find most of 452 anomalies lose significance with NYSE breakpoints and value weights, which keep microcaps from dominating. Chen and Zimmermann (2022) replicate over 300 predictors with open code and find most reproduce. They differ mainly on definitions (value or equal weights, microcaps in or out, whether a redundant factor counts as false), not on the data. → [Papers](../09-reference/papers.md)

</details>

## Talks, podcasts and blogs

### Q13 (basic). You are meeting a low-latency engineer next week. Which talk and which podcast episode should you watch or hear first?

<details markdown="1">
<summary>Answer</summary>

Carl Cook's CppCon 2017 talk "When a Microsecond Is an Eternity" (Optiver), the classic on the hot path, cache warming, measuring tick-to-trade and "if in doubt, pull your orders"; David Gross's CppCon 2024 talk is the modern companion. On audio, Jane Street's *Signals and Threads* episode 1, "Programmable Hardware", covers where a trading firm puts logic on FPGAs. → [Talks, podcasts and blogs](../09-reference/talks-podcasts-blogs.md)

</details>

### Q14 (informed). How should you weigh a chart from an AQR, Man Group or Two Sigma research note, or a backtest on Quantpedia?

<details markdown="1">
<summary>Answer</summary>

Firm research blogs are high quality but written by asset managers with products to sell: read them as well-argued advocacy and look for the paper behind each chart. Firm-produced content is evidence about that firm's views and technology, not evidence that a technique works and never evidence about other firms. Quantpedia is a useful index of published strategies, but its backtests are not evidence. → [Talks, podcasts and blogs](../09-reference/talks-podcasts-blogs.md)

</details>

## Datasets and tools

### Q15 (informed). An intern backtests a value strategy on free daily prices for today's S&P 500 members and gets a great Sharpe ratio. Name two dataset problems before you look at the strategy, and the kind of data that fixes them.

<details markdown="1">
<summary>Answer</summary>

First, survivorship bias: a universe of today's members leaves out the delisted and dropped losers, which flatters value and small-cap backtests. Second, look-ahead in membership and fundamentals: index membership and restated accounting data were not known at the time. The fix is a survivorship-free security master with delisting returns (for example CRSP) and point-in-time fundamentals and index membership. → [Datasets and tools](../09-reference/datasets-and-tools.md) · [Point-in-time data](../03-algorithms/a-data-and-signals/point-in-time-data-and-cleaning.md)

</details>

## Related pages

- [Glossary](../09-reference/glossary.md)
- [Acronyms](../09-reference/acronyms.md)
- [Books](../09-reference/books.md)
- [Papers](../09-reference/papers.md)
- [Talks, podcasts and blogs](../09-reference/talks-podcasts-blogs.md)
- [Datasets and tools](../09-reference/datasets-and-tools.md)
- [Contested debates](../08-calibration/contested-debates.md)
