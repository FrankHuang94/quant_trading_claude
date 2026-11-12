# Quiz: Risk and regulation

> **TL;DR**
>
> - 14 questions on module 06: the limit stack, factor limits, pod drawdown rules, stress tests, kill switches and model risk, then the rules that shape strategy design (Reg NMS, Reg SHO, 15c3-5, manipulation cases, Rules 605 and 606, MiFID II, SEBI).
> - Several are diligence scenarios: what control would have caught a failure, or which strategies a rule change hits.
> - Difficulty: **basic** (you read the page), **informed** (you can apply it), **sharp** (you could use it in diligence or with a risk manager). Each answer links to the page that explains it.

**Level:** Core · **Read time:** ~9 min · **Last verified:** 2026-11

## Risk management at quant firms

### Q1 (basic). List the layers of a quant firm's limit stack from the order up, and say what design principle links them.

<details markdown="1">
<summary>Answer</summary>

Per-order checks (price collar, size, notional, message rate), per-name position or inventory limits, gross and net notional, factor exposures, risk budget, liquidity, loss limits, and finally a kill switch. Each layer assumes the one above it has failed. In accounting terms, limits are preventive controls, monitors and P&L attribution are detective controls, and kill switches and capital cuts are corrective ones. → [Risk management at quant firms](../06-risk-and-regulation/risk-management-at-quant-firms.md)

</details>

### Q2 (informed). Why are factor-exposure limits described as the quant-specific layer, and what are illustrative settings for a market-neutral book?

<details markdown="1">
<summary>Answer</summary>

Quant books are built to be neutral, so factor limits cap what the strategy did not mean to own: a stat-arb book that is accidentally long momentum is a factor bet in disguise, and crowded books with similar exposures lost together in August 2007. Illustrative settings: beta within ±0.05–0.1, sector net within ±1–3% of gross market value, style tilts under about 0.25 standard deviations (practitioner ranges, not published firm limits). → [Risk management at quant firms](../06-risk-and-regulation/risk-management-at-quant-firms.md)

</details>

### Q3 (sharp). A platform halves a PM's capital at a 5% loss on allocated capital. At 4% annual volatility, how often does that stop fire within a year for a zero-skill pod and for a Sharpe-1 pod, and what does that tell you about the rule?

<details markdown="1">
<summary>Answer</summary>

The KB's simulation puts it at about 20% of zero-skill pods and about 4% of Sharpe-1 pods (an estimate; the Millennium rule itself is reported, not published). The stop caps damage cheaply but detects skill poorly. It also pushes PMs toward low volatility and tight factor neutrality, because a factor drawdown counts the same as a stock-picking one. → [Risk management at quant firms](../06-risk-and-regulation/risk-management-at-quant-firms.md)

</details>

### Q4 (informed). Match each stress scenario to the books it hits hardest: 24 August 2015; 5 February 2018; 5 August 2024; August 2007.

<details markdown="1">
<summary>Answer</summary>

24 August 2015 (1,278 LULD halts, 1,058 of them in ETPs) hits ETF arbitrage and ETF market making. 5 February 2018 (VIX from 17.31 to 37.32 in a day) hits short volatility. 5 August 2024 (the yen-carry unwind) hits carry, short volatility and crowded momentum. August 2007 hits stat arb and multi-factor books through crowded long-short unwinds. → [Risk management at quant firms](../06-risk-and-regulation/risk-management-at-quant-firms.md)

</details>

### Q5 (informed). What does a well-designed kill switch do, and who should be able to operate it?

<details markdown="1">
<summary>Answer</summary>

It cancels working orders and blocks new ones, often still allowing risk-reducing orders, and it is a last resort behind layered pre-trade controls. FIA's 2024 best practice recommends granular switches per trading system that the risk owner can operate and the trader cannot override; MiFID II's RTS 6 requires the ability to cancel any or all unexecuted orders immediately. Good designs fail safe: on lost connectivity, stale data or a breached loss limit, quotes come down first. → [Risk management at quant firms](../06-risk-and-regulation/risk-management-at-quant-firms.md)

</details>

### Q6 (sharp). Knight Capital lost over \$460M in about 45 minutes in 2012. What went wrong mechanically, and which missing control would have caught it?

<details markdown="1">
<summary>Answer</summary>

New code reached seven of eight servers, and a repurposed flag woke dead logic on the eighth, which built roughly \$3.5B of unintended longs and \$3.15B of shorts. It was code risk, a form of model risk, not a market move. No check compared orders going out with fills coming in; staged deployment (new code on one server first), position and loss limits enforced inline, and a tested kill switch are the standard defenses. → [Risk management at quant firms](../06-risk-and-regulation/risk-management-at-quant-firms.md)

</details>

### Q7 (basic). Who owns risk at a quant firm, and how does the market access rule formalize that at a broker-dealer?

<details markdown="1">
<summary>Answer</summary>

Most firms separate the trader or PM, who owns P&L, from an independent risk team that sets and enforces limits. At broker-dealers with market access, Rule 15c3-5 requires automated pre-trade controls under the firm's direct and exclusive control and an annual CEO certification. The SEC's first case under the rule followed Knight's 2012 loss, with a \$12M penalty. → [Risk management at quant firms](../06-risk-and-regulation/risk-management-at-quant-firms.md)

</details>

## Rules that shape strategies

### Q8 (basic). Name the three Reg NMS rules that most shape equity strategies, what each does, and their status as of 2026-11.

<details markdown="1">
<summary>Answer</summary>

Rule 611 forbids trading through a better protected quote, so routers sweep with intermarket sweep orders; repeal was proposed in June 2026. Rule 610(c) caps access fees at 30 mils, which bounds maker-taker rebates; Rule 612 bans sub-penny quotes above \$1, which makes queues long in tick-constrained stocks. The 2024 amendments (a half-penny tick for tick-constrained stocks and a 10-mil cap) are delayed to the first business day of November 2027. → [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

</details>

### Q9 (sharp). The SEC finalizes the repeal of Rule 611. Which strategies and P&L lines would you expect to change?

<details markdown="1">
<summary>Answer</summary>

Smart order routing logic and ISO usage change first, because routers no longer must sweep every better protected quote. Latency arbitrage loses some triggers, since every sweep is a race trigger today, and venues that receive forced flow under the rule may lose it. Market makers' queue value and rebate capture shift with the routing. → [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

</details>

### Q10 (informed). A short-term reversal model wants to short a stock that has just fallen 12% on the day. What does Reg SHO allow, and what else constrains the short leg?

<details markdown="1">
<summary>Answer</summary>

After a 10% fall, Rule 201's circuit breaker allows short sales only above the national best bid for the rest of that day and the next, so the strategy cannot hit bids. Rule 203(b) also requires a locate before any short sale (with an exception for bona fide market making), and Rule 204 forces close-out of failed deliveries. Hard-to-borrow names add borrow fees and recall risk. → [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

</details>

### Q11 (informed). What did the SEC's 2014 Athena Capital case show about closing-auction algorithms, and what does it imply for index-rebalance traders?

<details markdown="1">
<summary>Answer</summary>

Athena's algorithm traded in the final seconds to move Nasdaq closing prices in 2009, at times over 70% of volume in those seconds; it settled for a \$1M penalty without admitting or denying. An algorithm built to win the close can itself be the violation. Closing-auction and index-rebalance traders need a non-price-setting reason for trading near the print, and market makers must log why each order was placed and cancelled. → [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

</details>

### Q12 (informed). Under MiFID II, when is a firm a high-frequency trader, and what obligations does running a market-making strategy trigger?

<details markdown="1">
<summary>Answer</summary>

A firm is an HFT if it averages at least 2 messages per second in one instrument, or 4 across all instruments on a venue. Under RTS 8, a firm running a market-making strategy on half the trading days in a month must sign a market-making agreement and quote firm two-sided prices for at least 50% of continuous trading hours. RTS 6 adds testing, kill functionality and annual stress tests at twice the past six months' peak volumes, and RTS 9 has venues police order-to-trade ratios. → [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

</details>

### Q13 (sharp). What did SEBI allege against Jane Street in July 2025, and what is the lesson for US index-arbitrage and closing-auction books?

<details markdown="1">
<summary>Answer</summary>

SEBI's interim order alleged that on expiry days between January 2023 and March 2025 the firm bought Bank Nifty constituents and futures in the morning while building bearish options positions, then sold in the afternoon; it impounded ₹4,843.57 crore. Jane Street disputes the findings and has appealed, and no final ruling on the merits had been reported as of 2026-11. The lesson: a regulator may treat ordinary cash trades as manipulation when they move a settlement price that a much larger derivatives position references. → [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

</details>

### Q14 (basic). How do Rules 605 and 606 move order flow?

<details markdown="1">
<summary>Answer</summary>

Rule 605 requires monthly execution-quality statistics; the amendments live since 2026-08-01 bring larger brokers in and add finer size buckets and time-to-execution measures, and wholesalers compete on these statistics for retail flow. Rule 606 requires quarterly routing reports, including payments and rebates by venue, plus order-level reports for institutional not-held orders on request, which buy-side desks use to audit brokers' algorithms. → [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)

</details>

## Related pages

- [Risk management at quant firms](../06-risk-and-regulation/risk-management-at-quant-firms.md)
- [Rules that shape strategies](../06-risk-and-regulation/rules-that-shape-strategies.md)
- [Algorithmic risk controls](../03-algorithms/f-market-making-and-hft-algorithms/algorithmic-risk-controls.md)
- [Position sizing and risk budgeting](../03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md)
- [How firms combine strategies](../02-strategies/h-cross-cutting/how-firms-combine-strategies.md)
- [Strategy failure gallery](../02-strategies/h-cross-cutting/strategy-failure-gallery.md)
