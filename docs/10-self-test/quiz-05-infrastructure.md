# Quiz: Infrastructure

> **TL;DR**
>
> - 14 questions on module 05: latency budgets, what runs on FPGA, CPU and GPU, the speed-of-light arithmetic between data centers, the two tech stacks, and the semiconductor angle.
> - The numeric ones need only two constants: 3.34 µs per km in air or vacuum and 4.9 µs per km in glass fiber.
> - Difficulty: **basic** (you read the page), **informed** (you can apply it), **sharp** (you could use it with an engineer or in diligence). Each answer links to the page that explains it.

**Level:** Core · **Read time:** ~9 min · **Last verified:** 2026-11

## Latency budgets and hardware

### Q1 (basic). What is a strategy's "decision budget", and how wide is the range across strategies?

<details markdown="1">
<summary>Answer</summary>

It is the time a strategy can spend between seeing information and acting on it before the opportunity is gone or a rival has acted. It runs from tens of nanoseconds for latency arbitrage on FPGAs to a whole night for daily factor books, each rung roughly a thousand times slower than the last. The budget decides which algorithms are allowed at all. → [How infrastructure constrains algorithms](../05-infrastructure/how-infrastructure-constrains-algorithms.md)

</details>

### Q2 (basic). Assign each job to an FPGA, a CPU core or a GPU: parsing an exchange feed, training a neural net, the main quoting loop across many symbols, a pre-trade risk check, an overnight Monte Carlo.

<details markdown="1">
<summary>Answer</summary>

FPGA: feed parsing and pre-trade risk checks, which are fixed pipelines that need deterministic, tens-of-nanoseconds timing. CPU: the main quoting loop, because it needs branchy logic over many symbols and fast iteration. GPU: training neural nets and overnight Monte Carlo, which are large batched math. → [How infrastructure constrains algorithms](../05-infrastructure/how-infrastructure-constrains-algorithms.md)

</details>

### Q3 (informed). GPUs are the fastest chips for math. Why do they stay out of the HFT hot path?

<details markdown="1">
<summary>Answer</summary>

A PCIe round trip plus a kernel launch costs several to tens of microseconds before any math happens. The hot path handles one event at a time, so there is no batch to spread that overhead over, and a few microseconds lose the race against a ~2.5 µs software or tens-of-ns FPGA rival. GPUs earn their keep upstream, training the models whose outputs the hot path uses. → [How infrastructure constrains algorithms](../05-infrastructure/how-infrastructure-constrains-algorithms.md)

</details>

### Q4 (informed). Explain "slow models arm fast triggers", and say what it implies for which model types live in the fast path.

<details markdown="1">
<summary>Answer</summary>

A large model, refit offline or every few seconds, writes thresholds and lookup tables; the hot path only compares one number with a threshold, such as "if the future ticks up, pull these quotes". So the fast path favors linear or distilled models (a microprice plus a few order-book signals is a dot product), while large networks are distilled or moved to a slower horizon. → [How infrastructure constrains algorithms](../05-infrastructure/how-infrastructure-constrains-algorithms.md)

</details>

### Q5 (informed). For an options market maker, what binds first: single-message latency or something else? Give the number that shows why.

<details markdown="1">
<summary>Answer</summary>

Throughput and exchange message caps bind first, because one tick in the underlying reprices hundreds to thousands of series. OPRA planned for a peak of 13.575M messages per 100 ms by July 2026. Market makers move a few volatility-surface parameters per event and reprice the most exposed series first. → [How infrastructure constrains algorithms](../05-infrastructure/how-infrastructure-constrains-algorithms.md)

</details>

### Q6 (informed). Why do speed businesses concentrate in a handful of firms?

<details markdown="1">
<summary>Answer</summary>

Speed is mostly fixed cost (links, colocation, FPGA engineers, GPU clusters), which creates operating leverage: in the KB's illustrative latency-arbitrage book, doubling the win rate more than quadruples net profit. Cutting Chicago–New York latency cost over \$500M in build-out plus five years of operations (Laughlin et al.). Only firms with volume across many strategies can carry that bill. → [How infrastructure constrains algorithms](../05-infrastructure/how-infrastructure-constrains-algorithms.md)

</details>

## Colocation and the speed of light

### Q7 (basic). Where are the matching engines for NYSE, Nasdaq, Cboe US equities and CME equity-index futures, and why does a firm's rack position inside a colocation hall not matter?

<details markdown="1">
<summary>Answer</summary>

NYSE is in Mahwah, Nasdaq in Carteret and Cboe in Secaucus (NY5), all in New Jersey; CME Globex is in Aurora, Illinois. Inside the building a meter of fiber adds about 4.9 ns, so exchanges equalize cable lengths (Cboe engineers every cross-connect to the same latency). Colocated firms race on their own hardware, not on rack position. → [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

</details>

### Q8 (informed). Aurora to Carteret is about 1,178 km. Compute the one-way time at the speed of light and in straight-line fiber, and compare them with the best microwave and fiber routes.

<details markdown="1">
<summary>Answer</summary>

In vacuum or air, 1,178 × 3.336 µs ≈ 3.93 ms; in fiber with refractive index 1.47, 1,178 × 4.90 µs ≈ 5.78 ms. The best microwave was estimated at about 4.03 ms in 2012, while Spread Networks' 2010 fiber took 6.65 ms. Radio wins by more than 2.5 ms because light in glass is about 47% slower and fiber follows roads and rail. → [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

</details>

### Q9 (informed). Spread Networks' fiber took 6.65 ms one way. How much glass does that imply, and what does that say about the route?

<details markdown="1">
<summary>Answer</summary>

6.65 ms ÷ 4.90 µs per km ≈ 1,357 km of fiber, roughly 15% longer than the 1,178 km great circle. Even a route built for speed detours, because fiber follows rights-of-way. By contrast, McKay's 4.056 ms radio route to Secaucus sits only 2.4% above the vacuum bound. → [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

</details>

### Q10 (sharp). A heavy storm knocks out the Chicago–New Jersey microwave links for an afternoon. What happens to equity market makers in New Jersey, and why?

<details markdown="1">
<summary>Answer</summary>

Their adverse selection falls and liquidity improves (Shkilko and Sokolov 2020). With radio down, traffic falls back to fiber, so the fastest traders lose most of their head start on futures moves (about 4 ms by microwave against 6.65 ms on the best fiber) and stale New Jersey quotes are picked off less often. That is why weather counts as a risk factor for speed strategies. → [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)

</details>

## Tech stacks

### Q11 (informed). Describe the two stacks a quant firm runs and the narrow interface between them. What is the best-documented exception to "C++ everywhere"?

<details markdown="1">
<summary>Answer</summary>

Production is small, fast and deterministic: C++ (or OCaml, or FPGA logic), kernel-bypass networking and pinned cores. Research is large and flexible: Python, columnar stores such as kdb+, GPU clusters. Research ships parameters, weights and limits; production ships back logs of every packet, order and fill. Jane Street is the exception: OCaml is its primary language, with Python second for data analysis and ML. → [Trading and research tech stacks](../05-infrastructure/trading-and-research-tech-stacks.md)

</details>

### Q12 (sharp). Where is money most often lost between research and production, and how do firms defend against it?

<details markdown="1">
<summary>Answer</summary>

At the seam: a model that looked good in Python but is reimplemented in C++ can differ in rounding, feature timing or missing-data handling, and simulators that ignore queues and latency overstate fills. Firms use shared libraries across both stacks (Jane Street's single-language approach is one answer), replay tests that must match production byte for byte, and staged capital ramps for new models. → [Trading and research tech stacks](../05-infrastructure/trading-and-research-tech-stacks.md)

</details>

## A semiconductor lens

### Q13 (informed). Who supplies the latency stack, and what does a decade of consolidation mean for a trading-firm customer?

<details markdown="1">
<summary>Answer</summary>

FPGAs come from AMD (Xilinx, acquired 2022) and Altera (51% sold to Silver Lake in 2025); low-latency NICs from AMD Solarflare (bought by Xilinx in 2019) and NVIDIA (Mellanox, 2020). The acquirers wanted data-center networking; trading is a small, demanding reference account. For the trading firm, consolidation means fewer independent roadmaps and real lock-in, since FPGA designs, toolchains and kernel-bypass APIs do not port cleanly. → [A semiconductor lens](../05-infrastructure/semiconductor-lens.md)

</details>

### Q14 (sharp). A chip company's strategy deck calls trading "a fast-growing silicon market". What would you push back on, and which part of trading demand does scale?

<details markdown="1">
<summary>Answer</summary>

No credible public figure sizes "trading silicon"; production buys small volumes of the lowest-latency parts (FPGAs, NICs, switches, clocks), a high-margin showcase niche rather than a volume driver. What scales is research compute, which grows with model size: XTX reports over 25,000 GPUs, High-Flyer's Fire-Flyer 2 held 10,000 A100s, and HRT leases NVIDIA Vera Rubin systems on CoreWeave. Ask whether trading revenue is disclosed, whether customers use vendor IP, and whether GPU demand is bought, leased or self-built. → [A semiconductor lens](../05-infrastructure/semiconductor-lens.md)

</details>

## Related pages

- [How infrastructure constrains algorithms](../05-infrastructure/how-infrastructure-constrains-algorithms.md)
- [Colocation, networks and the speed of light](../05-infrastructure/colocation-networks-and-the-speed-of-light.md)
- [Trading and research tech stacks](../05-infrastructure/trading-and-research-tech-stacks.md)
- [A semiconductor lens](../05-infrastructure/semiconductor-lens.md)
- [Anatomy of an HFT trading loop](../03-algorithms/f-market-making-and-hft-algorithms/anatomy-of-an-hft-trading-loop.md)
- [Latency arbitrage](../02-strategies/b-speed-and-structural/latency-arbitrage.md)
- [ML-driven short-horizon alpha](../02-strategies/c-statistical-arbitrage/ml-driven-short-horizon-alpha.md)
