# Quiz: Market structure

> **TL;DR**
>
> - Fifteen questions on module 01: an order's path, the book and queue value, order types and the close, venues and retail flow, the NBBO and data feeds, fees and ticks, cross-asset linkages, shorting and financing, and the rule changes in force or pending as of 2026-11.
> - About half are conceptual, a third are small calculations and the rest are judgment calls. Each is marked basic, informed or sharp.
> - Answer before you open the answer. Every answer links to the page that explains it, and most point forward to the strategy or algorithm that depends on it.

**Level:** Core · **Read time:** ~15 min · **Last verified:** 2026-11

## The order's path and the book

### Q1 (basic). A retail app's 100-share market buy and a pension fund's 2-million-share order take different routes to the tape. Describe each.

<details markdown="1">
<summary>Answer</summary>

**Retail:** the broker routes marketable orders to a wholesaler, which fills them as principal at or better than the NBBO, usually with price improvement, and reports them to a FINRA TRF. When the SEC proposed its Order Competition Rule in 2022, it found that more than 90% of individual investors' marketable orders went to six wholesalers `[Verified]`. **Institutional:** OMS → execution algo (VWAP, implementation shortfall) → smart order router, which slices child orders across exchanges, ATSs and the closing auction. Both trades are novated and netted at NSCC and settle at DTC on T+1. → [Life of a stock order](../01-market-structure/life-of-a-stock-order.md)

</details>

### Q2 (basic). The asks are 400 shares at \$100.01, 500 at \$100.02 and 300 at \$100.03; the best bid is \$100.00. A market buy for 1,000 shares arrives. What is the average price, and what does the trade cost against the mid?

<details markdown="1">
<summary>Answer</summary>

It fills 400 at 100.01, 500 at 100.02 and 100 at 100.03. Average = (40,004 + 50,010 + 10,003) ÷ 1,000 = **\$100.017**. Against the \$100.005 mid that is 1.2 cents a share, about 1.2 bps, or \$12 on a \$100k order. The book is left at 100.00 × 100.03; how fast it refills is its resilience. → [The limit order book](../01-market-structure/the-limit-order-book.md)

</details>

### Q3 (informed). Two identical bids rest at the same price: one at the front of a 10,000-share queue, one at the back. Why is the front worth more, and which effect dominates?

<details markdown="1">
<summary>Answer</summary>

The front fills on ordinary small sell orders. The back fills mainly when a large or informed seller sweeps the whole level, just before the price drops, so its fills carry worse adverse selection. In the page's illustrative numbers the front is worth +0.45¢ per share posted and the back −0.06¢; most of the gap is adverse selection, not fill rate. Lab 01 puts priority at about \$0.56 per 100 shares (synthetic lab result). → [The limit order book](../01-market-structure/the-limit-order-book.md) · [Queue position and order placement](../03-algorithms/f-market-making-and-hft-algorithms/queue-position-and-order-placement.md)

</details>

### Q4 (informed). What does an intermarket sweep order (ISO) let a router do, why does it exist, and what could change its role?

<details markdown="1">
<summary>Answer</summary>

The sender certifies that it is also taking out better-priced protected quotes elsewhere, so each venue may fill at once without checking away markets. Routers use ISOs to sweep several venues in the same microseconds. The order type exists because of the trade-through rule, Rule 611 of Regulation NMS. The SEC proposed rescinding Rule 611 and the locked/crossed-market ban on 11 June 2026, and the proposal was still pending as of 2026-11 `[Verified]`. → [Order types and auctions](../01-market-structure/order-types-and-auctions.md)

</details>

### Q5 (informed). At the closing cutoff XYZ has 1.2M shares of MOC buys and 0.9M of MOC sells. Other sell interest: 100,000 at \$50.02, 150,000 at \$50.05 and 200,000 at \$50.10. The last trade was \$50.00. Where does the close print, and who earns the concession?

<details markdown="1">
<summary>Answer</summary>

The auction picks the price that maximizes matched volume. At \$50.00 only 0.9M shares match, at \$50.02 1.0M, at \$50.05 1.15M; only at \$50.10 (1.35M offered) are all 1.2M bought shares matched. The close prints **\$50.10**, 20 bps above the last trade, and MOC buyers pay about \$120,000 more than at \$50.00 (illustrative). Auction liquidity providers who offset the published imbalance earn that concession. In practice the imbalance message attracts more sellers before 4:00 p.m. and shrinks the move. → [Order types and auctions](../01-market-structure/order-types-and-auctions.md) · [Auctions and closing liquidity](../02-strategies/a-liquidity-provision/auctions-and-closing-liquidity.md)

</details>

## Venues, data and fees

### Q6 (basic). Why can a wholesaler fill a retail order at a better price than the NBBO and still pay the broker for the order?

<details markdown="1">
<summary>Answer</summary>

Retail marketable orders are small, uncorrelated across accounts and rarely timed on short-horizon information, so their markouts are small. The wholesaler knows which broker sent the order (segmentation) and prices it as retail; an exchange sees anonymous orders and must price for its average counterparty. Whether that helps retail overall is contested: better fills and zero commissions on one side, an SEC-estimated \$1.5B-a-year "competitive shortfall" `[Verified]` and wider lit spreads on the other. → [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md)

</details>

### Q7 (sharp). A wholesaler's per-share income statement on a retail buy is +0.60¢ spread captured, −0.10¢ adverse selection, −0.15¢ PFOF and −0.10¢ other costs. One broker's flow starts marking out at 1.5¢ a share after one minute. What happens to the economics, and what can the wholesaler do?

<details markdown="1">
<summary>Answer</summary>

Normal flow nets +0.60 − 0.10 − 0.15 − 0.10 = **+0.25¢** a share. At a 1.5¢ markout it is +0.60 − 1.50 − 0.15 − 0.10 = **−1.15¢** (illustrative). The business rests on telling those counterparties apart. The wholesaler can segment more finely (broker, order type, stock), cut price improvement or PFOF for that segment, or stop internalizing it and route it to an exchange. → [Venues and retail flow](../01-market-structure/venues-and-retail-flow.md) · [Retail flow internalization](../02-strategies/a-liquidity-provision/retail-flow-internalization.md)

</details>

### Q8 (informed). Direct exchange feeds beat the SIP by roughly 0.2–0.5 ms. Why, and why would a faster SIP computer not close the gap?

<details markdown="1">
<summary>Answer</summary>

The gap comes from geography and an extra hop. A quote must travel to the SIP processor and then on to the trader, while a direct feed goes straight from the exchange's data center. In the page's sketch the direct microwave path takes about 190 μs and the SIP path about 400 μs `[Estimate]`. SIP processing is only tens of μs, so faster hardware barely helps. The gap is the raw material of latency arbitrage against SIP-priced midpoint pegs. → [NBBO and market data](../01-market-structure/nbbo-and-market-data.md)

</details>

### Q9 (informed). Since 3 November 2025 a \$900 stock has a different round lot. What is it, and what does the change do to the NBBO and to strategy data?

<details markdown="1">
<summary>Answer</summary>

Round lots now depend on price: 100 shares up to \$250, 40 shares from \$250.01 to \$1,000, 10 shares up to \$10,000 and 1 share above that `[Verified]`. A \$900 stock's protected quote can now be set by 40-share orders, so the NBBO is tighter and thinner; in the page's illustration it narrows from 40 cents to 10. Signals and TCA built on NBBO size or spread shift level on that date, so treat it as a break in any history. → [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Recent changes](../01-market-structure/recent-changes.md)

</details>

### Q10 (informed). Why would a market maker pay a fee to post a bid on an inverted venue when it could earn a rebate for the same displayed price on a maker-taker venue?

<details markdown="1">
<summary>Answer</summary>

Fee-adjusted, the inverted venue's bid is the better price for sellers. With illustrative schedules, a seller hitting a \$10.00 bid nets \$9.9970 on the maker-taker venue (30-mil take fee) but \$10.0002 on the inverted venue (2-mil taker rebate). Sellers and routers therefore hit the inverted venue first. The maker gives up a 0.29¢ rebate and pays a 0.15¢ fee, a 0.44¢ swing, to buy a short queue, where fills are more frequent and less adversely selected. → [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md) · [Fee- and microstructure-driven strategies](../02-strategies/b-speed-and-structural/fee-and-microstructure-driven-strategies.md)

</details>

### Q11 (sharp). A passive market maker in a tick-constrained \$40 stock earns a 0.50¢ half-spread and a 0.29¢ rebate per share. It loses 0.45¢ to adverse selection, 0.16¢ on aggressive exits and 0.02¢ to clearing. What is its net, what share of gross revenue is the rebate, and why do the 2024 SEC amendments matter?

<details markdown="1">
<summary>Answer</summary>

Net = 0.50 + 0.29 − 0.45 − 0.16 − 0.02 = **+0.16¢** a share. The rebate is 0.29 ÷ 0.79 = **37%** of gross revenue; without it the book loses 0.13¢ a share (illustrative). The half-penny tick and the 10-mil access-fee cap would shrink both the tick rent and the rebate; the page's estimate turns the net to −0.06¢. Compliance with both is deferred to the first business day of November 2027 and under staff review `[Verified]`. → [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md)

</details>

### Q12 (informed). The S&P 500 is at 6,000, financing costs 4.30%, the dividend yield is 1.30% and expiry is three months away. What is the futures fair value, and what do you do if the E-mini trades at 6,052?

<details markdown="1">
<summary>Answer</summary>

F = S × e^((r − q)T) = 6,000 × e^(0.03 × 0.25) ≈ **6,045.2**. At 6,052 the future is about 6.8 points rich, an implied financing rate near 4.75% `[Estimate]`. Sell futures and buy the basket: ten contracts capture 6.8 × \$50 × 10 = **\$3,400** before roughly \$600–\$1,200 of basket trading costs (illustrative). → [ETF, futures and options linkages](../01-market-structure/etf-futures-options-linkages.md) · [ETF and index arbitrage](../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md)

</details>

## Shorting and recent changes

### Q13 (sharp). A dollar-neutral book has \$250M of capital, \$500M long and \$500M short. Long financing costs 0.40% over benchmark; 90% of the shorts are general collateral at 0.30%, and 10% are hard to borrow at 8%. What is the annual drag, and what is the lesson?

<details markdown="1">
<summary>Answer</summary>

Long spread 0.40% × \$500M = \$2.00M; GC borrow 0.30% × \$450M = \$1.35M; hard-to-borrow 8% × \$50M = \$4.00M. The total is **\$7.35M, 2.9% of capital**, about 29% of a 10% gross alpha (illustrative). The 10% of shorts that are hard to borrow cost more than everything else combined. That is why production systems treat borrow as a per-name negative expected return and cap or exclude hard-to-borrow names: the "alpha" of many short signals sits exactly there. → [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

</details>

### Q14 (sharp). Your mean-reversion model wants to short a stock that has fallen 12% today. Which rule bites, and what does it do to the trade?

<details markdown="1">
<summary>Answer</summary>

Rule 201, the short-sale circuit breaker. After a 10% drop from the prior close, short sales for the rest of that day and all of the next may only be priced above the national best bid `[Verified]`. The short leg cannot hit the bid; it must rest passively and may not fill, so a backtest that assumed it traded at the bid overstates the strategy. The broker still needs a locate under Rule 203; bona fide market makers are exempt. → [Shorting, financing and settlement](../01-market-structure/shorting-financing-and-settlement.md)

</details>

### Q15 (sharp). A colleague backtests a market-making signal on 2019–2026 data built from SIP quotes, using NBBO size and spread as features. Name two market-structure reasons to distrust the result.

<details markdown="1">
<summary>Answer</summary>

First, price-tiered round lots went live on 3 November 2025, so NBBO size and spread in stocks above \$250 shift level on that date. Late April 2026 brought another break when the SIP began showing the best odd-lot order. Neither is alpha. Second, SIP timestamps understate how stale quotes were against direct feeds, so the backtest misses the fills on which the quoter was picked off. The deferred tick and fee-cap changes would add a third break if adopted. → [Recent changes](../01-market-structure/recent-changes.md) · [NBBO and market data](../01-market-structure/nbbo-and-market-data.md) · [Backtesting engines](../03-algorithms/c-validation-and-backtesting/backtesting-engines.md)

</details>

## Related pages

- [Life of a stock order](../01-market-structure/life-of-a-stock-order.md)
- [The limit order book](../01-market-structure/the-limit-order-book.md)
- [Fees, rebates and ticks](../01-market-structure/fees-rebates-and-ticks.md)
- [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)
- [Smart order routing](../03-algorithms/e-execution-algorithms/smart-order-routing.md)
- [Quiz: Strategies](quiz-02-strategies.md)
