# Quiz: Industry and firms

> **TL;DR**
>
> - 15 questions on module 04: firm types, revenue pools and business models, roles and org design, moats and M&A, and what the firm profiles can and cannot tell you.
> - Several are corp-dev exercises: read an income statement, value a market maker through the volatility cycle, spot the gross-versus-net trap in a Form ADV.
> - Difficulty: **basic** (you read the page), **informed** (you can apply it), **sharp** (you could use it in diligence). Each answer links to the page that explains it.

**Level:** Core · **Read time:** ~11 min · **Last verified:** 2026-11

## Firm types

### Q1 (basic). The math at different quant firms overlaps a lot. What actually separates the firm types, and what chain of cause and effect follows from it?

<details markdown="1">
<summary>Answer</summary>

Whose capital is at risk and how the decision-makers are paid. Capital source sets the horizon, the horizon sets the edge, and pay structure sets behavior. That is why own-capital market makers sit at microseconds to minutes and fee-earning asset managers at weeks to months. → [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)

</details>

### Q2 (informed). Why do electronic market makers rarely take outside investors, while for quant funds capacity becomes a negotiation with investors?

<details markdown="1">
<summary>Answer</summary>

A market maker's revenue is capped by volume and spread, not by equity: Jane Street reported about \$29.9B of members' equity at end-2024 against \$20.5B of net trading revenue that year. It turns its balance sheet over many times a day, so more capital adds little, and owners keep all the upside. A fund earns fees on assets, so its revenue can keep growing with capital even as market impact cuts the return on each dollar. → [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)

</details>

### Q3 (informed). Match each threat to the firm type it most typically kills: a three-year factor drought; losing the latency race; a faulty software deployment; several "independent" PMs drawing down at once.

<details markdown="1">
<summary>Answer</summary>

A long factor drought hits systematic asset managers (HML fell 51% from January 2017 to September 2020). Losing the race kills HFT prop, where second place earns almost nothing. A deployment error is the market maker's operational risk: Knight Capital lost over \$460M in about 45 minutes in 2012. Correlated PM drawdowns, or investors balking at pass-through costs, are how pods fail. → [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)

</details>

### Q4 (basic). Give two examples of the lines between firm types blurring.

<details markdown="1">
<summary>Answer</summary>

Market makers take directional risk: Coalition Greenwich put non-bank liquidity providers' 2025 trading revenue at about \$114B, of which \$84.3B came from proprietary trading and only \$30.2B from market making. Citadel (the hedge fund) and Citadel Securities (the market maker) are separate companies under one brand. Man Group runs both a trend-following CTA (AHL) and a systematic equity manager (Numeric). → [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)

</details>

## Economics

### Q5 (informed). Virtu's adjusted net trading income was \$3.9M a day in 2019 (average VIX 15.4) and about \$6.4M a day in 2024 (VIX 15.6). Why did revenue rise 1.6× at the same volatility?

<details markdown="1">
<summary>Answer</summary>

Revenue tracks volatility *and* volume, plus structural share, and the base had moved. Virtu bought ITG's agency business in 2019, and listed options volume set a record every year from 2020 through 2025. Volatility alone explains the 2019 to 2020 jump (\$3.9M to \$9.0M a day as VIX nearly doubled), not the 2019 to 2024 one. → [Economics and revenue pools](../04-industry-and-firms/economics-and-revenue-pools.md)

</details>

### Q6 (informed). A pass-through pod platform earns 15% gross, charges 6% of pass-through costs, then takes a 20% performance fee. What do investors keep, and what share of gross P&L goes to the platform and its PMs?

<details markdown="1">
<summary>Answer</summary>

After pass-through, 15% − 6% = 9%; the 20% fee takes 1.8%, leaving investors 7.2% (illustrative numbers). The platform and its PMs keep 7.8% of the 15% gross, about half. Balyasny's flagship reportedly made 15.2% gross and 2.8% net in 2023. → [Economics and revenue pools](../04-industry-and-firms/economics-and-revenue-pools.md)

</details>

### Q7 (sharp). A strategy earns 6% gross alpha minus impact of 1.5% × √(assets ÷ \$1B), and charges a 1.5% management fee. At what size do investors' dollar profits peak, and what does the manager earn at \$9B?

<details markdown="1">
<summary>Answer</summary>

At \$4B the net return is 6% − 3% − 1.5% = 1.5%, or \$60M, the peak in the KB's table (\$1B gives \$30M; \$9B gives 0%). At \$9B investors earn nothing while management fees reach \$135M. This is the Berk and Green (2004) equilibrium: money flows in until investors' net alpha is competed to zero, which is why return-focused firms close funds or, like Medallion, expel outside money. → [Economics and revenue pools](../04-industry-and-firms/economics-and-revenue-pools.md)

</details>

## Roles and organization

### Q8 (basic). One person builds simulators and turns a team's research into production strategy code; another builds feed handlers and order gateways used by every desk. Which roles are these, and what single question places anyone quickly?

<details markdown="1">
<summary>Answer</summary>

The first is a quant developer (QD), who owns the team's code; the second is a software engineer (SWE), who owns shared infrastructure. Titles vary by firm, so ask: "Who owns the P&L you work on?" A QR at a centralized fund may never see a dollar figure for their signal, while a pod PM knows theirs to the basis point. → [Roles, teams and careers](../04-industry-and-firms/roles-teams-and-careers.md)

</details>

### Q9 (informed). What behavior does each pay structure reward: a market maker's firm-wide pool, a pod PM's formula payout, and a centralized fund's attribution-based bonus?

<details markdown="1">
<summary>Answer</summary>

A shared pool rewards sharing models across desks, which matters because desks depend on each other (the ETF desk uses the equity desk's fair values). A pod payout rewards guarding ideas and hedging every factor, because the PM shares in gains but not losses. Attribution rewards signals that are uncorrelated with what the combined model already has. → [Roles, teams and careers](../04-industry-and-firms/roles-teams-and-careers.md)

</details>

## Competitive dynamics and M&A

### Q10 (informed). Which market-maker moat is least durable and which are most durable? Describe the flywheel that makes the durable ones compound.

<details markdown="1">
<summary>Answer</summary>

Speed is the least durable: every upgrade gets copied. Proprietary flow data and balance sheet are the most durable. More order flow gives more fills and markout data, which give better fair-value and toxicity models, tighter quotes and more flow, while higher P&L funds pay, hardware and payments for order flow. → [Competitive dynamics and M&A](../04-industry-and-firms/competitive-dynamics-and-ma.md)

</details>

### Q11 (informed). Read the market-maker deal table as a corp-dev analyst. What three lessons does it teach?

<details markdown="1">
<summary>Answer</summary>

Flow and franchises transfer, code does not: buyers paid for retail order flow, DMM books and client lists. Sellers sell at the cyclical bottom: Knight after its 2012 loss, KCG in low-volatility 2017 for a 12.7% premium. The winners stay private, raising minority equity (Citadel Securities in 2022) or bonds (Jane Street) instead. → [Competitive dynamics and M&A](../04-industry-and-firms/competitive-dynamics-and-ma.md)

</details>

### Q12 (sharp). A market maker earns \$7.0M a day at VIX 15 plus \$0.35M a day per VIX point, over 252 days, with costs of 30% of revenue plus \$500M fixed. Compare EBITDA at VIX 15 and VIX 30, and say which year you would value.

<details markdown="1">
<summary>Answer</summary>

At VIX 30, revenue is 7.0 + 0.35 × 15 = \$12.25M a day, or \$3.09B a year; costs are \$1.43B, so EBITDA is \$1.66B against \$0.73B at VIX 15 (illustrative numbers). Volatility doubles and EBITDA rises 2.3× through operating leverage. Value the normal year (VIX about 19, EBITDA \$0.98B) and treat stressed years as an option on volatility, not a run rate. → [Competitive dynamics and M&A](../04-industry-and-firms/competitive-dynamics-and-ma.md)

</details>

## Firm profiles

### Q13 (informed). Millennium's Form ADV shows \$720.8B of regulatory AUM, yet press reports put its assets near \$79B. Why the gap, and where else in the profiles does the same trap appear?

<details markdown="1">
<summary>Answer</summary>

Form ADV counts gross, levered assets, so regulatory AUM runs about nine times reported capital. Renaissance's Medallion shows \$61.2B of gross assets, while Bloomberg reported its equity capped at \$9–10B, and Point72's \$274.1B regulatory AUM covers the whole firm gross of leverage. Always ask whether a size figure is equity or gross exposure. → [Millennium profile](../04-industry-and-firms/firm-profiles/millennium.md)

</details>

### Q14 (informed). What is wrong with repeating "Medallion made 66% a year" as a hard fact?

<details markdown="1">
<summary>Answer</summary>

The figure (about 66% gross and 39% net, 1988–2018) comes from Zuckerman's book, not audited disclosure. It is an arithmetic average; Guo and Liu (2024, preprint) estimate compounded gross returns below 35%. Medallion has also been closed to outside investors since 2005, and Renaissance's outside funds have ordinary results: RIEF lost 19% in 2020 while Medallion reportedly gained 76%. → [Renaissance Technologies profile](../04-industry-and-firms/firm-profiles/renaissance-technologies.md)

</details>

### Q15 (sharp). Two Sigma paid a \$90M SEC penalty in 2025. What happened, and what is the lesson for anyone diligencing a systematic manager?

<details markdown="1">
<summary>Answer</summary>

Models read parameters from a shared database, and one researcher's unreviewed edits to 14 models from November 2021 to August 2023 moved funds' returns in opposite directions: some gained over \$400M, others lost about \$165M, which the firm repaid. Staff had flagged the unrestricted write access since March 2019. The lesson is model governance: ask who can change production parameters, how changes are reviewed, and how live monitoring would catch it. → [Two Sigma profile](../04-industry-and-firms/firm-profiles/two-sigma.md)

</details>

## Related pages

- [Taxonomy of quant firms](../04-industry-and-firms/taxonomy-of-quant-firms.md)
- [Economics and revenue pools](../04-industry-and-firms/economics-and-revenue-pools.md)
- [Roles, teams and careers](../04-industry-and-firms/roles-teams-and-careers.md)
- [Competitive dynamics and M&A](../04-industry-and-firms/competitive-dynamics-and-ma.md)
- [Firm profiles](../04-industry-and-firms/firm-profiles/index.md)
- [How firms combine strategies](../02-strategies/h-cross-cutting/how-firms-combine-strategies.md)
- [Equity market making](../02-strategies/a-liquidity-provision/equity-market-making.md)
