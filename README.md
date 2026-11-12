# quant_trading_claude

**A knowledge base on how quantitative trading firms trade US equities, with strategies and algorithms first.**

> Status: **under construction**. See [`PLAN.md`](PLAN.md) for live progress against the build spec.

This repository is a GitHub-hosted, MkDocs-published knowledge base for a finance professional who wants a
medium-deep, accurate mental model of quant trading: what quant firms actually trade, why each strategy
makes money, who is on the other side, and the concrete algorithms inside the research-and-trading
pipeline, from signal construction to execution and market-making quoting logic.

## Start with strategies & algorithms

Two modules carry this knowledge base and get most of the words, labs and QA:

| Module | What's inside |
|---|---|
| [02 · Strategies](docs/02-strategies/index.md) ★ | 30 strategy dossiers (market making, stat arb, mid-frequency alpha, factors, vol, trend) + comparison and failure gallery |
| [03 · Algorithms](docs/03-algorithms/index.md) ★ | 39 algorithm cards (signals, forecasting, validation, risk models, optimization, execution, market making) + 4 end-to-end walkthroughs |

Supporting modules: [00 Start here](docs/00-start-here/the-big-picture.md) ·
[01 Market structure](docs/01-market-structure/life-of-a-stock-order.md) ·
[04 Industry & firms](docs/04-industry-and-firms/taxonomy-of-quant-firms.md) ·
[05 Infrastructure](docs/05-infrastructure/how-infrastructure-constrains-algorithms.md) ·
[06 Risk & regulation](docs/06-risk-and-regulation/risk-management-at-quant-firms.md) ·
[07 Conversation playbook](docs/07-conversation-playbook/how-to-talk-to-a-quant.md) ·
[08 Calibration](docs/08-calibration/myths-vs-reality.md) ·
[09 Reference](docs/09-reference/glossary.md) ·
[10 Self-test](docs/10-self-test/index.md) ·
[Labs](docs/labs.md)

## Repository layout

```
docs/        the knowledge base (MkDocs Material site)
labs/        20 Python labs on synthetic data (labs/common/simulate.py is the market simulator)
scripts/     content checks: templates, word counts, glossary links, strategy x algorithm matrix
references/  master bibliography (generated)
```

## Build locally

```bash
python -m venv .venv && . .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
make site        # mkdocs build --strict
make labs-smoke  # every lab with a tiny parameter set
make check       # template, matrix, glossary and word-count checks + strict build
```

## License

Prose is licensed under CC BY 4.0; code (labs, scripts) under MIT. See [LICENSE](LICENSE).
