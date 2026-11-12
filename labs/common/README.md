# labs/common: API cheat sheet

Shared code for all labs. Read this instead of the source; the full reference is the docstring
at the top of `simulate.py` (`python labs/common/simulate.py` prints it). Everything is
deterministic given `seed`. Check the calibration with:

```bash
python labs/common/simulate.py --selftest     # ~40 PASS/FAIL lines, ~7 s, exit 1 on failure
```

| Module | What it gives you |
|---|---|
| `utils.py` | `setup()`, `save_fig()`, `write_results()`, `annualized_sharpe()`, `max_drawdown()` |
| `simulate.py` | synthetic markets: equity cross-section with planted alphas, order book flow, options, futures, intraday session |
| `orderbook.py` | `OrderBook`: price-time-priority limit order book and matching engine |
| `options.py` | Black-Scholes price / greeks / implied vol, Heston price |

Every lab starts like this (CLAUDE.md section 5.2):

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import utils, simulate   # noqa: E402

def main():
    ctx = utils.setup(__file__, "Lab NN: title")   # parses --smoke / --seed; ctx.smoke, ctx.seed
    ...
    utils.save_fig(ctx, fig, "name")               # -> docs/assets/labs/labNN-name.png (smoke: labs/_smoke/)
    utils.write_results(ctx, {"key": value})       # -> labs/NN-name/results.json
```

Pass `seed=ctx.seed` to every simulator so `--seed` works.

## Contents

- [Equity cross-section and planted alphas](#equity-cross-section-and-planted-alphas)
- [Order book flow (simulate_lob)](#order-book-flow-simulate_lob)
- [Matching engine (orderbook.OrderBook)](#matching-engine-orderbookorderbook)
- [Options (simulate_option_market and options.py)](#options-simulate_option_market-and-optionspy)
- [Futures for trend following](#futures-for-trend-following)
- [Intraday session for execution](#intraday-session-for-execution)
- [Pitfalls](#pitfalls)

## Equity cross-section and planted alphas

```python
from common import simulate
m = simulate.simulate_equity_market(seed=7)                    # 500 stocks x 1260 days, ~0.3 s
small = simulate.simulate_equity_market(n_stocks=200, n_days=500, seed=7)   # smoke size
```

Config `EquityMarketConfig` (all are keyword overrides): `n_stocks=500, n_days=1260,
n_sectors=11, start="2019-01-02", seed=7, market_vol=0.16, style_factors=("size", "value",
"momentum", "low_vol"), idio_vol_range=(0.15, 0.45), beta_range=(0.6, 1.5),
vol_clustering=True, fat_tails_df=5.0, reversal_strength=0.0, momentum_strength=0.0,
alphas=DEFAULT_ALPHAS`; extras `market_drift=0.06, stress_per_year=0.5`.

Fields of the returned `EquityMarket` (DataFrames are dates x tickers unless noted):

| Field | Meaning |
|---|---|
| `dates`, `tickers` | business days from `start`; tickers `S0000`..`S0499` |
| `returns` | total simple daily returns (factor part + specific part) |
| `specific_returns` | the residual (specific) part; planted alphas live here |
| `factor_returns` | dates x factors: `market`, `size`, `value`, `momentum`, `low_vol`, `sec_<Sector>` |
| `exposures` | tickers x factors: market = beta, styles = z-scores, sectors = 0/1 dummies (constant over time) |
| `sector`, `beta`, `spread_bps` | Series by ticker; spreads 2-30 bps, tighter for liquid names |
| `prices`, `volume` (shares), `adv_usd` (trailing 20-day $ volume incl. day t), `market_cap` | liquidity data |
| `specific_vol` | true daily specific vol on each day |
| `alphas` | dict name -> observable signal known at the CLOSE of day t (daily z-score) |
| `alpha_specs` | dict name -> `PlantedAlpha` |
| extras: `expected_specific_return` | oracle E_t[specific return of day t+1], aligned at t |
| extras: `vol_regime`, `stress_dates`, `factor_vol`, `alpha_loadings` | regime multiplier h[t] (mean h^2 = 1), stress-episode start dates, base daily factor vols, calibrated loadings |

Methods and helpers:

```python
fwd1 = m.forward_returns(1, specific=True)     # sum of specific returns t+1..t+h, aligned at t
fwd5 = m.forward_returns(5)                    # total returns t+1..t+5
ic = simulate.cross_sectional_ic(m.alphas["alpha_med"], fwd1)               # daily IC Series
ric = simulate.cross_sectional_ic(m.alphas["alpha_med"], fwd1, rank=True)   # rank IC
print(round(ic.mean(), 4), round(ric.mean(), 4))     # ~0.030, ~0.033
cov = m.true_covariance(100)                   # tickers x tickers daily covariance on day index 100
noise = simulate.noise_signals(m, n=5, seed=1)       # {"noise_000": DataFrame, ...}, true IC = 0
for name, sig in simulate.iter_noise_signals(m, n=3, seed=2):   # generator: use for n in the 100s+
    pass
```

Planted alphas. Each one is a latent AR(1) score whose effect on next-day specific returns is
calibrated so that the measured mean daily Pearson IC of the observable signal against
next-day specific returns equals `ic` (+-0.003 typical on the default size), and the IC at lag
k (signal at t vs specific return of day t+1+k) is about `ic * horizon_decay**k`:

```python
from common.simulate import PlantedAlpha, DEFAULT_ALPHAS
# DEFAULT_ALPHAS: alpha_fast (ic 0.04, half_life 2), alpha_med (0.03, 10), alpha_slow (0.02, 60),
#                 each with horizon_decay = 0.5 ** (1 / half_life)  (IC decays like the signal)
a = PlantedAlpha("my_alpha", ic=0.03, half_life=5.0, horizon_decay=0.5 ** (1 / 5.0),
                 noise=0.0,               # extra observation noise (IC target already accounts for it)
                 ic_halflife_years=None,  # e.g. 2.0: loading halves every 2 years (alpha decay)
                 start_day=0)             # no predictive power before this day index
m2 = simulate.simulate_equity_market(n_days=750, alphas=DEFAULT_ALPHAS + (a,), seed=7)
decaying = PlantedAlpha("published", ic=0.04, half_life=20, horizon_decay=0.5 ** (1 / 20), ic_halflife_years=1.5)
```

Endogenous effects for lab 10 (they are functions of past specific returns, generated
sequentially, so they behave like real reversal and momentum):

```python
mr = simulate.simulate_equity_market(reversal_strength=0.04, momentum_strength=0.02, seed=7)
rev_signal = -simulate.reversal_signal(mr)      # -(5-day specific return), z-scored: IC ~0.04
mom_signal = simulate.momentum_signal(mr)       # 12-1 month specific return, z-scored: IC ~0.02
```

Calibration on the default config (selftest): realized market vol ~16.6%, average pairwise
stock correlation ~0.26 (0.38 within sector), daily specific vol 1-2.3% (5th-95th
percentile), betas 0.60-1.49, mean ADV $7M-$540M, 2-3 stress episodes in 5 years. Planting or
removing alphas does not change the factor returns or the specific noise for a given seed.

## Order book flow (simulate_lob)

```python
sim = simulate.simulate_lob(seed=7)                    # one 6.5 h day, ~270k events, ~2-3 s
sim = simulate.simulate_lob(n_seconds=1800, seed=7)    # smoke size, ~0.2 s
q, tr, ev = sim.quotes, sim.trades, sim.events
```

Config `LOBConfig`: `n_seconds=23400, tick=0.01, start_price=50.0, daily_vol=0.02,
limit_rate=6.0` (limit orders/s), `cancel_rate=0.05` (per-second hazard of EACH resting order,
not a total), `market_rate=1.0` (market orders/s), `informed_share=0.25,
jump_rate_per_hour=2.0, depth_levels=10, seed=7`; extras `jump_size_bps=10, stale_cancel_prob=0.3,
lp_edge_ticks=0.5, placement_decay=0.7, lp_fv_lag=20.0` (s), `flow_impact_ticks=0.3,
mean_limit_lots=2.0, mean_market_lots=2.5`.

| Output | Columns |
|---|---|
| `quotes` | one row per event, state AFTER it: `time` (s), `bid`, `ask`, `bid_size`, `ask_size`, `mid`, `spread` ($), `imbalance` = (bid_size - ask_size) / (bid_size + ask_size), `bid_size_2`, `ask_size_2`, `bid_size_3`, `ask_size_3` |
| `events` | same index as `quotes`: `time`, `type` (`limit`/`cancel`/`market`), `side` (+1 bid/buy, -1 ask/sell), `price` (limit price; VWAP for market orders), `size`, `order_id`, `owner` (`lp`/`noise`/`informed`/`agent`) |
| `trades` | one row per fill: `time`, `price`, `size`, `side` (+1 buyer-initiated), `informed` (bool); extras `maker_id`, `maker_owner`, `taker_owner`, `event_idx` |
| `fair_value` | latent efficient price, Series aligned with `quotes` rows |
| `book` | final `OrderBook` |

The book just before a trade is `quotes.iloc[trade.event_idx - 1]`. Mid at an arbitrary time:

```python
import numpy as np
t_query = tr["time"].to_numpy() + 10.0                       # 10 s after each trade
j = np.searchsorted(q["time"].to_numpy(), t_query, side="right") - 1
mid_later = q["mid"].ffill().to_numpy()[j]
lp_markout_ticks = -tr["side"].to_numpy() * (mid_later - tr["price"].to_numpy()) / sim.cfg.tick
print(simulate.lob_markouts(sim, horizon=10.0))   # {'informed': ~-0.35, 'noise': ~+0.85, 'all': ...}
print(simulate.lob_imbalance_predictiveness(sim)) # (corr(imbalance, sign of next mid change) ~0.2, n)
```

How the market works (for interpreting results): informed traders see the true fair value;
liquidity providers quote around a lagged belief (an EMA of fair value with a 20 s time
constant, nudged by each market order). Hence: spread 1 tick ~50% of the time and 1-3 ticks
~96%; median touch size ~500 shares; imbalance predicts the next mid move; informed trades
are adversely selecting (LP markout turns negative within ~10 s) while noise trades are profitable
for LPs; mid realized vol ~= `daily_vol`.

Agent hook (for labs that quote or post orders inside the simulated market):

```python
def my_agent(ctx):              # called every agent_interval simulated seconds
    # ctx.t, ctx.fair_value (true; do not "cheat" with it unless that is the point), ctx.book
    # ctx.new_fills: fills involving the agent since the last call
    if ctx.book.best_bid() is not None and int(ctx.t) % 30 == 0:
        oid = ctx.add_limit(+1, ctx.book.best_bid(), 100)    # owner "agent", recorded in events
        # ctx.cancel(oid) / ctx.market(-1, 100) also exist

sim = simulate.simulate_lob(n_seconds=600, seed=7, agent=my_agent, agent_interval=1.0)
agent_fills = sim.trades[(sim.trades.maker_owner == "agent") | (sim.trades.taker_owner == "agent")]
```

To see every fill the moment it happens, call `ctx.book.subscribe(callback)` once (Lab 01's
`QueueProbeAgent` does this to track virtual orders).

## Matching engine (orderbook.OrderBook)

```python
from common.orderbook import OrderBook, BUY, SELL    # BUY = BID = +1, SELL = ASK = -1
book = OrderBook(tick=0.01)
a = book.add_limit(BUY, 10.00, 300, owner="A")      # returns order id; marketable limits cross first
b = book.add_limit(BUY, 10.00, 200, owner="B")
book.add_limit(SELL, 10.02, 400, owner="C")
book.queue_ahead(b)                 # 300 shares ahead (A)
fills = book.market(SELL, 400, owner="T")    # list[Fill]: A 300 @ 10.00, then B 100 @ 10.00
book.order(b)                       # OrderInfo(id, side, price, size=100 remaining, orig_size, owner, time)
book.cancel(b)                      # True; cancel(id, size=50) reduces size and keeps priority
book.best_bid(), book.best_ask(), book.mid(), book.spread()   # floats, or None if a side is empty
book.depth(BUY, 5)                  # [(price, total size), ...] best first
book.snapshot(5)                    # dict: time, best_bid, best_ask, mid, spread, imbalance, bids, asks
book.level_orders(BUY, 10.00)       # resting orders at a price, front of the queue first
print(book.to_string())             # ladder with each queue as owner:size
```

`Fill(price, size, maker_id, taker_side, maker_owner, taker_owner, time, taker_id)`: price is
the maker's price; `taker_side` +1 = buyer-initiated. Set `book.time = t` before calls to stamp
fills. `book.last_fills` holds the fills of the most recent `add_limit`/`market` call.
Extras: `best_bid_size()`, `best_ask_size()`, `imbalance(levels)`, `spread_ticks()`,
`n_orders`, `is_resting(id)`, `subscribe(cb)`. Speed: ~300k events in 1-2 s.

## Options (simulate_option_market and options.py)

```python
om = simulate.simulate_option_market(seed=7)   # 252 days, ~0.2 s, chain of 18,216 rows
c = om.chain
atm30 = c[(c.expiry_days == 30) & (c.moneyness == 1.0) & c.call].set_index("day")["implied_vol"]
rv_fwd = om.realized_vol(30, forward=True)     # realized vol over days d+1..d+30, aligned at d
print(round((atm30 - rv_fwd).mean(), 3))       # ~ +0.012: the variance risk premium
p = om.price(day=10, strike=100.0, T=20 / 252, call=True)   # revalue any fixed contract on any day
```

Config `OptionMarketConfig`: `n_days=252, steps_per_day=26, s0=100, r=0.0, v0=0.04, kappa=2.0,
theta=0.04, xi=0.6, rho=-0.7` (physical Heston), `vrp=0.25, expiries_days=(7, 30, 60, 91),
moneyness=(0.8, ..., 1.2), seed=7`; extra `mu=0.05` (physical drift).

- `path`: one row per intraday step: `t` (years), `S`, `v` (instantaneous variance), `day`, `step`.
- `daily`: end-of-day `S`, `v` indexed by `day` (0..n_days).
- `chain`: `day, expiry_days, T, strike, moneyness, spot, call, price, implied_vol, delta, gamma,
  vega` (Black-Scholes greeks at the row's implied vol; vega per 1.00 of vol). Constant maturity:
  every day lists fresh 7/30/60/91-day options at strikes = moneyness x that day's spot. About
  1.6% of rows (deep OTM 7-day calls) have NaN implied vol because their price is ~0.
- Day counts are trading days: T = expiry_days / 252.
- Options are priced under a risk-neutral Heston with v_Q = v (1 + vrp), theta_Q = theta (1 + vrp)
  (`om.q_params`). Results: negative skew (30-day IV ~31% at 80% moneyness vs ~19% at 120%) and
  implied vol above subsequent realized vol by ~1-2 vol points on average.

```python
from common import options
options.bs_price(100, 105, 0.5, 0.03, 0.25, call=True)          # vectorized: arrays broadcast
g = options.bs_greeks(100, 105, 0.5, 0.03, 0.25, call=True)     # dict delta, gamma, vega, theta
# units: vega per 1.00 vol (/100 per vol point); theta per year (/252 per trading day here)
options.implied_vol(7.9656, 100, 100, 1.0, 0.0, call=True)       # ~0.20; NaN if out of bounds
options.heston_price(100, [90, 100, 110], 30 / 252, 0.0, 0.04, 2.0, 0.05, 0.6, -0.7, call=True)
```

## Futures for trend following

```python
fm = simulate.simulate_futures(seed=7)    # 24 assets x 5040 days (20 years), ~0.05 s
fm.returns            # daily excess returns (dates x assets)
fm.asset_class        # Series: equity / rates / fx / commodity (6 each)
fm.true_drift         # the latent daily expected return (for "oracle" comparisons)
fm.vol                # true daily vol per asset and day (vol clustering)
print(round(simulate.tsmom_sharpe(fm), 2))   # 12-month TSMOM, inverse-vol weights: ~0.78 gross
```

Config `FuturesConfig`: `n_assets=24, n_days=5040, trend_strength=0.045, seed=7`; extras
`regime_days=250, class_trend_share=0.3, fat_tails_df=5.0, start="2005-01-03"`.
`trend_strength` = std of the daily drift in units of daily vol (0.045 means a typical drift
regime has an annual Sharpe of about +-0.7). The diversified 12-month TSMOM Sharpe averages
~0.75 across seeds (0.3-1.2 per 20-year sample); single assets only ~0.1-0.2. Names are
synthetic but descriptive (`EQ_US_LARGE`, `UST_10Y`, `EURUSD`, `CRUDE`, ...), with realistic vols
(2% for 2-year notes to ~45% for natural gas).

## Intraday session for execution

```python
prof = simulate.intraday_volume_profile(390)   # U-shape, sums to 1 (continuous session only)
bars = simulate.simulate_intraday_session(seed=7)
bars.columns       # minute, volume, mid, spread ($), spread_bps, high, low, vwap
bars.attrs["close_auction_volume"], bars.attrs["close_price"]   # also open_price, continuous_volume
```

Config `IntradayConfig`: `n_bins=390, price=50.0, daily_vol=0.02, adv_shares=5e6,
spread_bps=3.0, close_auction_share=0.10, seed=7`; extras `volume_noise=0.35,
day_volume_noise=0.25`. The first minute trades ~3.7x the average minute and the last ~3.1x;
intraday variance follows the volume profile; spreads are ~2.5x wider at the open. Minute 0 is
9:30-9:31; `mid` is the end-of-minute mid. Simulate several days with different seeds.

## Pitfalls

- **Alignment.** Signals (`m.alphas`) are known at the close of day t; trade them on day t+1's
  return: `m.forward_returns(1)` is already aligned at t. Never correlate a signal with the
  same-day return.
- **IC is defined vs specific returns.** Against total returns the IC is ~15% lower, because
  factor moves add cross-sectional noise. Rank IC runs ~10% above Pearson IC (ranking removes
  the dilution from heteroskedastic volatility).
- **horizon_decay vs half_life.** If you set `horizon_decay` far from `0.5 ** (1 / half_life)`,
  a smoothed or differenced version of the signal predicts better than the signal itself (by
  construction). Keep them equal unless that is what the lab is about. The class default
  `horizon_decay=0.5` is a fast decay; `DEFAULT_ALPHAS` set it explicitly.
- **Memory.** Each 1260 x 500 DataFrame is ~5 MB. For hundreds of noise signals use
  `iter_noise_signals` or a smaller market.
- **Endogenous effects interact.** With `reversal_strength`/`momentum_strength` on, the planted
  alphas' measured ICs shift by ~0.001-0.002 (past returns contain alpha).
- **LOB cancel_rate is per order**, not a total rate: total cancels/s = cancel_rate x resting orders.
- **No holidays** in equity dates (business days); option and intraday time is in trading days.
