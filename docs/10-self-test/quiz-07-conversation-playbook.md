# Quiz: Conversation playbook

> **TL;DR**
>
> - 15 questions on module 07: the "approach, not alpha" rule, what quants will and will not discuss, how to repair a naive question, moves from the mock conversations, and the 30-second explanation.
> - Most are scenarios: a question you are about to ask, or an answer you just got. Decide what you would say next before opening the answer.
> - Difficulty: **basic** (you read the page), **informed** (you can apply it), **sharp** (you could do it live). Each answer links to the page that explains it.

**Level:** Core · **Read time:** ~10 min · **Last verified:** 2026-11

## Ground rules

### Q1 (basic). What is the one-line rule for talking to a quant, and how do you convert a "what", a "how much" and a "does it work" question to follow it?

<details markdown="1">
<summary>Answer</summary>

Ask about approach, not alpha: how they decide, measure and fail, never what the signal is. Turn "what" into "how do you decide", "how much" into "how do you measure", and "does it work" into "when did it stop working". The reframed versions are answerable and show you know which part matters. → [How to talk to a quant](../07-conversation-playbook/how-to-talk-to-a-quant.md)

</details>

### Q2 (basic). Sort these into usually open versus off-limits: cross-validation scheme, latency rank, lessons from August 2007, live positions, FPGA versus CPU split, PFOF rates paid.

<details markdown="1">
<summary>Answer</summary>

Open: the cross-validation scheme (a method), lessons from August 2007 (a failure everyone lived through) and the FPGA versus CPU split (infrastructure in general terms). Off-limits: latency rank (the rank is the edge), live positions (they are the strategy, and discussing them raises compliance flags) and PFOF rates (commercial terms). → [How to talk to a quant](../07-conversation-playbook/how-to-talk-to-a-quant.md)

</details>

### Q3 (informed). Why are a firm's risk limits and stop levels on the locked list, even though they reveal no signal?

<details markdown="1">
<summary>Answer</summary>

They tell rivals when the firm becomes a forced seller, which is exactly when others can trade against it. Ask instead how limits are set and reviewed. The same logic locks capacity by strategy: it shows rivals how much room is left. → [Questions to ask](../07-conversation-playbook/questions-to-ask.md)

</details>

### Q4 (informed). Naive questions fail in three ways. Name them and the repair for each.

<details markdown="1">
<summary>Answer</summary>

They fish for the secret (signals, positions, P&L), so ask for the method instead. They assert a myth ("HFT front-runs", "AI predicts stocks"), so ask about the evidence. They ask for one number stripped of its conditions (Sharpe, hit rate, speed), so ask for the conditions: gross or net, period, capacity. → [Faux pas and naive questions](../07-conversation-playbook/faux-pas-and-naive-questions.md)

</details>

### Q5 (basic). What do the **Basic**, **Informed** and **Sharp** labels and the 🔒 mark mean on the question bank, and when should you climb a level?

<details markdown="1">
<summary>Answer</summary>

Basic questions are safe openers, informed ones show you know the mechanics, and sharp ones probe a failure the quant lived through; 🔒 marks proprietary territory nobody will answer. Climb only when the answer earns it: units and a horizon move you from basic to informed, and the quant citing their own tests or failures moves you to sharp. A vague answer means drop back and ask for one example. → [Questions to ask](../07-conversation-playbook/questions-to-ask.md)

</details>

## Repairing naive questions

### Q6 (informed). You are about to say "Market making is free money: you just collect the spread." What do the numbers say, and what should you ask instead?

<details markdown="1">
<summary>Answer</summary>

Adverse selection eats much of the spread. In Menkveld's (2013) data an HFT market maker earned €1.55 of spread per trade, lost €0.68 on positions and netted €0.88. Ask "What share of spread capture goes to adverse selection?", which shows you know where market-making P&L leaks. → [Faux pas and naive questions](../07-conversation-playbook/faux-pas-and-naive-questions.md)

</details>

### Q7 (informed). A PM mentions a losing month, and you are tempted to ask whether the model is broken. Why is that naive? Give the arithmetic.

<details markdown="1">
<summary>Answer</summary>

A strategy with an annual Sharpe of 1 has a monthly Sharpe of about 1 ÷ √12 ≈ 0.29, so it loses in roughly 39% of months, assuming normal returns. One bad month says almost nothing. Ask instead whether the drawdown was inside what the risk model expected. → [Faux pas and naive questions](../07-conversation-playbook/faux-pas-and-naive-questions.md)

</details>

### Q8 (informed). In a live-trading conversation, how many years of data does it take before a Sharpe of 0.75 reaches t = 2?

<details markdown="1">
<summary>Answer</summary>

Since t ≈ Sharpe × √years, you need √years = 2 ÷ 0.75 ≈ 2.7, or about seven years. A quant who knows this will be cautious about declaring a signal dead or alive from one or two years of live data. → [Questions to ask](../07-conversation-playbook/questions-to-ask.md)

</details>

### Q9 (sharp). A fund pitches "AI-driven, uncorrelated to everything, Sharpe 2.5 on \$5B, monthly rebalancing, no losing years since 2015". List the red flags.

<details markdown="1">
<summary>Answer</summary>

"AI-driven" with no method (the SEC brought its first AI-washing cases in March 2024); "uncorrelated" never tested in 2007, 2020 or August 2024; a Sharpe above 2 on billions at a monthly horizon, which contradicts the comparison matrix; no gross or net, period or capacity attached; and smooth returns with no losing stretch, which usually means short volatility, stale marks or a short sample. Run it through the sanity-checking checklist next. → [How to talk to a quant](../07-conversation-playbook/how-to-talk-to-a-quant.md)

</details>

## Moves from the mock conversations

### Q10 (sharp). You ask an ETF market maker for the weights in her Japan ETF fair-value model while Tokyo is shut, and she declines. What is the right next move?

<details markdown="1">
<summary>Answer</summary>

Accept the no in a few words, with no second push, and move one level up to structure. In the dialogue: "Without numbers, which error costs you more there, the level of fair value or how fast it updates?" She can answer that (speed, because a stale quote gets picked off) without giving anything away. → [Mock conversations](../07-conversation-playbook/mock-conversations.md#1-the-etf-market-maker)

</details>

### Q11 (informed). Why does an ETF market maker judge a client block by its hedge-adjusted markout rather than its raw markout?

<details markdown="1">
<summary>Answer</summary>

After a hedged sale, a market rally makes the raw markout look terrible while saying nothing about the client. Net of the futures hedge, it shows whether the client knew something about that fund. In the KB's walkthrough the raw markout swung from +20 bps at 60 seconds to −34 bps at the close, while the hedge-adjusted markout stayed at +8 to +11 bps. → [Mock conversations](../07-conversation-playbook/mock-conversations.md#1-the-etf-market-maker)

</details>

### Q12 (sharp). You cite press reports that a pod platform halves capital at a 5% loss and exits near 7.5%; the PM won't confirm his thresholds. What do you ask next, and what answer should you expect?

<details markdown="1">
<summary>Answer</summary>

Ask how the stop changes the way he runs the book. Expect: lower volatility than he would run with his own money, a cushion above the line, and a quicker trigger on misbehaving signals. The KB's simulation explains the cushion: at 4% annual volatility a zero-skill pod hits a 5% peak-to-trough drawdown within a year about 37% of the time, and a Sharpe-1 pod about 13%, so even skilled PMs trip the stop. → [Mock conversations](../07-conversation-playbook/mock-conversations.md#2-the-stat-arb-pm-at-a-pod-shop)

</details>

### Q13 (informed). A client wants to know whether one bank's algorithm beats another's. Why can't a few orders tell, and what do desks use instead?

<details markdown="1">
<summary>Answer</summary>

A single order's shortfall has a standard deviation of 50–150 bps, while the gap between brokers is a few bps, so it takes hundreds to thousands of comparable, market-adjusted orders. Desks use algo wheels, which randomize orders across brokers within a bucket so the league table compares like with like. → [Mock conversations](../07-conversation-playbook/mock-conversations.md#5-the-execution-quant-at-a-bank)

</details>

### Q14 (sharp). A low-latency engineer won't give you his p99 tick-to-trade. What can you ask instead, and what burst arithmetic explains why the tail matters?

<details markdown="1">
<summary>Answer</summary>

Ask what they measure and where tail latency comes from: page faults, interrupts, cache misses, bursts at the open. If one core must requote 500 symbols at 1 µs each, the last quote leaves 500 µs late; sharded across 16 cores, about 31 µs. Averages hide this, so asking about the tail shows you understand the problem. → [Mock conversations](../07-conversation-playbook/mock-conversations.md#6-the-low-latency-engineer)

</details>

## Elevator explanations

### Q15 (informed). Your CFO asks what statistical arbitrage is, and you have 30 seconds. Which three questions must the answer cover, and what would you say?

<details markdown="1">
<summary>Answer</summary>

What it is, who pays for it, and how it breaks. For example: stat arb holds thousands of small long and short positions in stocks that look temporarily mispriced against their peers, neutral to market, sectors and styles, for hours to about ten days; it is mostly paid for absorbing other investors' temporary price pressure; and because edges are thin, leverage turns crowding into forced selling, as in August 2007. Save the mechanism and sourced numbers for the 2-minute version. → [Elevator explanations](../07-conversation-playbook/elevator-explanations.md#statistical-arbitrage)

</details>

## Related pages

- [How to talk to a quant](../07-conversation-playbook/how-to-talk-to-a-quant.md)
- [Questions to ask](../07-conversation-playbook/questions-to-ask.md)
- [Mock conversations](../07-conversation-playbook/mock-conversations.md)
- [Faux pas and naive questions](../07-conversation-playbook/faux-pas-and-naive-questions.md)
- [Elevator explanations](../07-conversation-playbook/elevator-explanations.md)
- [Adverse selection and markouts](../03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md)
- [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)
