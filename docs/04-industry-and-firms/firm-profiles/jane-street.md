# Jane Street

> **TL;DR**
>
> - Private trading firm founded in 2000. It made its name in ETFs and is now a major player in equities, bonds and options on more than 200 venues `[Verified]`.
> - Reported 2025 net trading revenue was \$39.6B, helped by gains on private stakes such as Anthropic, and Q1 2026 brought \$16.1B `[Reported]`.
> - It writes its software in OCaml and uses neural nets heavily. Its India manipulation case was unresolved as of 2026-11.

**Type:** proprietary trading firm and market maker · **Last verified:** 2026-11

| Field | Value |
|---|---|
| Type | Proprietary trading firm; US broker-dealers Jane Street Capital and Jane Street Execution Services `[Verified]` |
| Scale | ~\$39.6B net trading revenue in 2025, private-stake gains included `[Reported]`; ~24% of US ETF primary-market and ~16% of secondary activity in 2024 `[Reported]` |
| Horizon | Sub-second quoting to multi-day ETF and bond inventory `[Estimate]` |
| Known strategies | [ETF market making](../../02-strategies/a-liquidity-provision/etf-market-making.md) · [ETF and index arbitrage](../../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [Options market making](../../02-strategies/a-liquidity-provision/options-market-making.md) · [Equity market making](../../02-strategies/a-liquidity-provision/equity-market-making.md) |
| Tech signals | OCaml as its primary language; in-house hardware design; neural nets fed by an event-driven feature system (2026 blog) `[Verified]` |
| Confidence | Medium: technology from the firm; revenue from press |
| Sources | Firm site and blog, Reuters, Global Trading, Indian press (below) |

## What they do

Jane Street quotes ETFs, stocks, bonds and options for its own account. It is a large [authorized participant](../../09-reference/glossary.md#authorized-participant) that creates and redeems ETF shares with issuers `[Reported]`. In 2024 it handled about 10% of US equity volume `[Reported]`.

## Strategy focus and approach

The franchise is [ETF market making](../../02-strategies/a-liquidity-provision/etf-market-making.md). The firm values the basket, quotes the ETF around that value, hedges fills with baskets or futures, and nets leftover inventory through [creation and redemption](../../09-reference/glossary.md#creation-and-redemption). For bond and foreign-stock ETFs, the hard part is pricing underlyings that trade rarely or are shut. Underneath sit [feature engineering](../../03-algorithms/a-data-and-signals/feature-engineering.md) and [neural nets](../../03-algorithms/b-forecasting-models/neural-nets-and-sequence-models.md). Its Flex Model framework turns raw market events into the hundreds or thousands of features a model consumes `[Verified]`.

```mermaid
flowchart LR
    U["Underlying basket<br/>stocks, bonds, futures"] --> FV["Basket fair value"]
    FV --> Q["Quote the ETF"]
    Q --> H["Hedge fills"]
    H --> CR["Create or redeem<br/>with the issuer"]
```

## Fact vs lore

- **Lore:** "OCaml is the edge." **Fact:** OCaml is the firm's primary development platform `[Verified]`. Its P&L contribution is unknowable `[Lore]`.
- **India.** SEBI's 2025-07-03 interim order barred four Jane Street entities and impounded ₹4,843.57 crore, about \$566M at ₹85.5 per dollar `[Estimate]`. It alleged Bank Nifty manipulation around weekly expiries `[Reported]`. Jane Street paid the sum into escrow and regained access in July 2025. It disputes the findings and appealed to the Securities Appellate Tribunal, which reserved an order on document disclosure in October 2026 `[Reported]`. These are allegations, not final findings.

## Related pages

- [ETF market making](../../02-strategies/a-liquidity-provision/etf-market-making.md) · [ETF and index arbitrage](../../02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md) · [ETF market maker walkthrough](../../03-algorithms/h-end-to-end-walkthroughs/walkthrough-etf-market-maker.md)
- [Taxonomy of quant firms](../taxonomy-of-quant-firms.md) · [Optiver](optiver.md)

## Sources

- [Verified] Jane Street (n.d.). "Overview" (founding, venues, products). <https://www.janestreet.com/what-we-do/overview/> (accessed 2026-11)
- [Verified] Jane Street (n.d.). "Technology" (OCaml as primary development platform). <https://www.janestreet.com/technology/> (accessed 2026-11)
- [Verified] Maczka, S. (2026-10-13). "Flex Model: an event-driven feature engineering system." *Jane Street Blog*. <https://blog.janestreet.com/flex-model-an-event-driven-feature-engineering-system/> (accessed 2026-11)
- [Verified] Ray, A. (2020-06-01). "Using ASCII waveforms to test hardware designs." *Jane Street Blog*. <https://blog.janestreet.com/using-ascii-waveforms-to-test-hardware-designs/> (accessed 2026-11)
- [Reported] Reuters via MarketScreener (2026-04-24). "Jane Street's \$40 billion trading haul tops rivals, sources say." <https://www.marketscreener.com/news/jane-street-s-40-billion-trading-haul-tops-rivals-sources-say-ce7f59dfdf8ff52d> (accessed 2026-11)
- [Reported] Reuters via MarketScreener (2026). "Jane Street rakes in record first-quarter trading haul of \$16.1 billion, sources say." <https://uk.marketscreener.com/news/jane-street-rakes-in-record-first-quarter-trading-haul-of-16-1-billion-sources-say-ce7f5bdbdf8af521> (accessed 2026-11)
- [Reported] Global Trading (2025). "Jane Street took 10% of US equity market in 2024." <https://www.globaltrading.net/?p=38181> (accessed 2026-11)
- [Reported] Mondaq (2025-07). "SEBI Update: Interim Order Against Jane Street Group For Alleged Index Manipulation." <https://www.mondaq.com/india/securities/1648508/sebi-update-%7c-interim-order-against-jane-street-group-for-alleged-index-manipulation> (accessed 2026-11)
- [Reported] The Week (2025-07-14). "Jane Street folds to Sebi order on market manipulation, deposits over ₹4,800 crore in escrow accounts." <https://www.theweek.in/news/biz-tech/2025/07/14/jane-street-folds-to-sebi-order-on-market-manipulation-deposits-over-4800-crore-rupees-in-escrow-accounts.amp.html> (accessed 2026-11)
- [Reported] Business Today (2026-10-06). "Sebi tells SAT that Jane Street has enough data to respond to market manipulation charges." <https://www.businesstoday.in/markets/story/sebi-tells-sat-that-jane-street-has-enough-data-to-respond-to-market-manipulation-charges-559953-2026-10-06> (accessed 2026-11)
- [Reported] NewsBytes (2026-10). "SAT reserves order in Jane Street document disclosure case." <https://www.newsbytesapp.com/news/business/sat-reserves-order-in-jane-street-document-disclosure-case/story> (accessed 2026-11)
