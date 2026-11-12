# Walkthrough helper scripts

These scripts produce the numbers quoted in the four end-to-end walkthroughs in
`docs/03-algorithms/h-end-to-end-walkthroughs/`. Each one runs a single coherent scenario by
importing the **core functions of the finished labs** (via `importlib`, since lab folder names
contain hyphens) plus `labs/common`, and writes every number the page quotes to a JSON file next to
the script. They are deterministic (seed 7) and are not part of the 20 numbered labs.

| Script | Walkthrough page | Labs reused | Output |
|---|---|---|---|
| `mid-frequency-stat-arb.py` | [A mid-frequency stat-arb book](../../docs/03-algorithms/h-end-to-end-walkthroughs/walkthrough-mid-frequency-stat-arb.md) | 11, 12, 14, 17 | `mid-frequency-stat-arb.json` |
| `etf-market-maker.py` | [A day at an ETF market maker](../../docs/03-algorithms/h-end-to-end-walkthroughs/walkthrough-etf-market-maker.md) | 02, 04, 05, 07 | `etf-market-maker.json` |
| `options-market-maker.py` | [An options market maker](../../docs/03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md) | 06 | `options-market-maker.json` |
| `institutional-execution.py` | [Executing a \$500M buy order](../../docs/03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md) | 16, 17, 18 | `institutional-execution.json` |

## How to run

```bash
python scripts/run_labs.py --walkthroughs
```

or one script at a time, e.g. `python labs/walkthroughs/etf-market-maker.py`. Runtimes: about
1–2 s each, except the options book (~50 s, dominated by refitting smiles).

## Caveats

The scenarios inherit every simplification of the labs they reuse (see each lab's "What this toy
misses vs the real world"). Sharpe ratios and P&L levels are stylized; the walkthrough pages label
them as synthetic lab results and set realistic ranges beside them.
