"""Lab 10: short-term reversal vs 12-1 momentum, and what trading costs do to each.

What it demonstrates
  * Two classic cross-sectional books on a simulated 500-stock market in which BOTH effects are
    planted with known strength (simulate_equity_market with reversal_strength > 0 and
    momentum_strength > 0):
      (a) 1-week reversal: buy last week's losers, sell last week's winners (Lehmann 1990;
          Lo & MacKinlay 1990 linear "contrarian" weights, plus the usual decile version),
          rebalanced weekly;
      (b) 12-1 momentum: buy the past year's winners, sell the losers, skipping the most recent
          month (Jegadeesh & Titman 1993), decile long-short rebalanced monthly.
  * Realistic costs: half the quoted spread + square-root market impact (a coefficient times
    daily vol times sqrt(trade / ADV)) + a general-collateral borrow fee on the shorts.
  * The punchline: reversal has the higher GROSS Sharpe but trades ~14x more, so costs eat it;
    momentum's lower gross Sharpe survives. Shown three ways: gross vs net P&L at a $100M book,
    net Sharpe vs a flat cost assumption (break-even cost per trade), and net Sharpe vs book size
    (capacity).
  * Truth check: how well each signal recovers the planted IC.
  * Pitfall: momentum's worst month. After a bear market the momentum book is short the
    losers, which carry high beta and sit in the beaten-down sectors; when the market rebounds
    the book loses (the Daniel & Moskowitz 2016 "momentum crash" mechanism). The lab splits that
    loss into market beta, sector/style tilts and specific returns using the TRUE exposures. The
    simulator's version is mild (about -3 sd), far smaller than the historical crashes D&M document.

Supports: docs/02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md,
          docs/02-strategies/e-risk-premia-and-factors/momentum.md,
          docs/03-algorithms/d-portfolio-construction/transaction-cost-and-impact-models.md (cost model)

Run: python labs/10-reversal-momentum-costs/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import utils, simulate  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Planted effects (stylized but plausible): measured daily IC vs next-day specific return.
REVERSAL_STRENGTH = 0.03      # IC of -(5-day specific return), the simulator's reversal input
MOMENTUM_STRENGTH = 0.01      # IC of 12-1 month specific momentum
BASE_BOOK_USD = 100e6         # gross book (long $ + short $) for the headline net numbers
IMPACT_COEF = 0.5             # square-root-law coefficient Y (stylized; same as Labs 09 and 16)
BORROW_BPS_PER_YEAR = 35.0    # general-collateral borrow fee on short notional (stylized)
BOOK_SIZES_USD = [1e7, 3e7, 1e8, 3e8, 1e9, 3e9, 1e10]
FLAT_COSTS_BPS = np.arange(0.0, 40.5, 0.5)
COLORS = {"reversal": "#2a78d6", "momentum": "#eb6834", "lm": "#1baf7a", "hedged": "#eda100"}


# =====================================================================================
# === CORE ALGORITHM ===
# Signals are computed from returns known at the CLOSE of day t; the book set at close t
# earns the return of day t+1. Weights are fractions of the gross book (sum |w| = 1).
# =====================================================================================

def reversal_signal(returns: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """1-week reversal score (Lo & MacKinlay 1990 contrarian weighting).

    score_i,t = -(r_i - r_mkt) over the last `lookback` days, where r_mkt is the equal-weighted
    cross-sectional average. Positive score = past loser = BUY. Used as raw weights it is the
    Lo-MacKinlay portfolio w_i = -(1/N)(r_i - r_mkt) (dollar neutral by construction).
    """
    past = returns.rolling(lookback).sum()                 # past-week return per stock
    return -past.sub(past.mean(axis=1), axis=0)            # minus deviation from the market


def momentum_signal(returns: pd.DataFrame, lookback: int = 252, skip: int = 21) -> pd.DataFrame:
    """12-1 momentum (Jegadeesh & Titman 1993): return from t-lookback to t-skip.

    The most recent month is skipped because 1-month returns REVERSE (the effect above); mixing
    the two would make the momentum score partly a bet against itself.
    """
    log_ret = np.log1p(returns)
    return log_ret.rolling(lookback - skip).sum().shift(skip)   # sum of days t-251 .. t-21


def apply_costs(weights: pd.DataFrame, returns: pd.DataFrame, book_usd: float,
                spread_bps: pd.Series, adv_usd: pd.DataFrame, daily_vol: pd.DataFrame,
                impact_coef: float = 0.5, borrow_bps_per_year: float = 35.0) -> pd.DataFrame:
    """Daily gross and net P&L (fractions of the gross book) of a target-weight book.

    cost of trading q dollars of stock i = q * ( spread_i / 2  +  impact_coef * vol_i * sqrt(q / ADV_i) )
    i.e. pay half the quoted spread plus square-root market impact; plus a borrow fee on shorts.
    """
    traded = weights.diff().abs().fillna(weights.abs())     # fraction of book traded at close t
    trade_usd = traded * book_usd
    cost_rate = (spread_bps / 2e4) + impact_coef * daily_vol * np.sqrt(trade_usd / adv_usd)
    trading_cost = (traded * cost_rate).sum(axis=1)          # fraction of book, paid at close t
    shorts = weights.shift(1).clip(upper=0).abs().sum(axis=1)      # short book held over day t
    borrow_cost = shorts * borrow_bps_per_year / 1e4 / 252
    gross = (weights.shift(1) * returns).sum(axis=1)        # earn day-t return on w set at t-1
    out = pd.DataFrame({"gross": gross, "trading_cost": trading_cost, "borrow_cost": borrow_cost,
                        "turnover": traded.sum(axis=1)})
    out["net"] = out["gross"] - out["trading_cost"] - out["borrow_cost"]
    return out


# === END CORE ALGORITHM ===
# =====================================================================================


def decile_weights(signal: pd.DataFrame, q: float = 0.1) -> pd.DataFrame:
    """Equal-weight long top-q / short bottom-q book, +0.5 long and -0.5 short (gross 1)."""
    rank = signal.rank(axis=1, pct=True)
    top, bottom = (rank > 1 - q), (rank <= q)
    w = top.div(top.sum(axis=1), axis=0) * 0.5 - bottom.div(bottom.sum(axis=1), axis=0) * 0.5
    return w.fillna(0.0)


def lm_weights(signal: pd.DataFrame) -> pd.DataFrame:
    """Lo-MacKinlay linear weights, scaled to gross 1 (they are already dollar neutral)."""
    s = signal.sub(signal.mean(axis=1), axis=0)
    return s.div(s.abs().sum(axis=1), axis=0).fillna(0.0)


def rebalance_every(weights: pd.DataFrame, every: int, start: int) -> pd.DataFrame:
    """Hold target weights fixed between rebalance days (drift between rebalances ignored)."""
    w = weights.copy()
    keep = np.zeros(len(w), dtype=bool)
    keep[start::every] = True
    w.iloc[~keep] = np.nan
    w = w.ffill().fillna(0.0)
    w.iloc[:start] = 0.0
    return w


def beta_hedge(weights: pd.DataFrame, beta: pd.Series) -> pd.DataFrame:
    """Add an equal-weighted universe basket so the book's beta (sum w_i beta_i) is zero."""
    book_beta = weights.mul(beta, axis=1).sum(axis=1)
    basket = pd.Series(1.0 / len(beta), index=beta.index)
    hedge = -book_beta / float(beta.mean())                 # $ of basket per $ of gross book
    return weights + np.outer(hedge.to_numpy(), basket.to_numpy())


def stats(pnl: pd.DataFrame) -> dict:
    """Annualized Sharpe (gross, net), returns, turnover and average cost per $ traded."""
    traded = pnl["turnover"].sum()
    return {
        "sharpe_gross": utils.annualized_sharpe(pnl["gross"].to_numpy()),
        "sharpe_net": utils.annualized_sharpe(pnl["net"].to_numpy()),
        "ann_return_gross_pct": 100 * 252 * pnl["gross"].mean(),
        "ann_return_net_pct": 100 * 252 * pnl["net"].mean(),
        "ann_vol_pct": 100 * np.sqrt(252) * pnl["gross"].std(),
        "annual_turnover_x_gross": 252 * pnl["turnover"].mean(),
        "avg_cost_bps_per_dollar_traded": 1e4 * pnl["trading_cost"].sum() / traded if traded else 0.0,
        "trading_cost_pct_per_year": 100 * 252 * pnl["trading_cost"].mean(),
        "borrow_cost_pct_per_year": 100 * 252 * pnl["borrow_cost"].mean(),
        "max_drawdown_net_pct": 100 * utils.max_drawdown(pnl["net"].cumsum().to_numpy()),
    }


def flat_cost_sharpe(pnl: pd.DataFrame, cost_bps: float) -> float:
    """Net Sharpe if every $ traded cost `cost_bps` (one way), borrow fee included."""
    net = pnl["gross"] - pnl["turnover"] * cost_bps / 1e4 - pnl["borrow_cost"]
    return utils.annualized_sharpe(net.to_numpy())


def main() -> None:
    ctx = utils.setup(__file__, "Lab 10: reversal vs momentum, gross vs net of costs")
    n_stocks, n_days = (150, 600) if ctx.smoke else (500, 2520)
    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, seed=ctx.seed,
                                        reversal_strength=REVERSAL_STRENGTH,
                                        momentum_strength=MOMENTUM_STRENGTH)
    R = m.returns
    start = 252 + 21                                       # first day both signals exist
    print(f"Market: {n_stocks} stocks x {n_days} days (synthetic), stress episodes at "
          f"{[d.date().isoformat() for d in m.stress_dates]}")

    # ------------------------------------------------------------ signals and IC recovery
    rev = reversal_signal(R, lookback=5)
    mom = momentum_signal(R, lookback=252, skip=21)
    fwd_spec = m.forward_returns(1, specific=True)
    fwd_tot = m.forward_returns(1)
    ic = {
        "reversal_planted": REVERSAL_STRENGTH,
        "reversal_measured_vs_specific": simulate.cross_sectional_ic(rev, fwd_spec).iloc[start:].mean(),
        "reversal_measured_vs_total": simulate.cross_sectional_ic(rev, fwd_tot).iloc[start:].mean(),
        "reversal_oracle_signal_vs_specific": simulate.cross_sectional_ic(
            -simulate.reversal_signal(m), fwd_spec).iloc[start:].mean(),
        "momentum_planted": MOMENTUM_STRENGTH,
        "momentum_measured_vs_specific": simulate.cross_sectional_ic(mom, fwd_spec).iloc[start:].mean(),
        "momentum_measured_vs_total": simulate.cross_sectional_ic(mom, fwd_tot).iloc[start:].mean(),
        "momentum_oracle_signal_vs_specific": simulate.cross_sectional_ic(
            simulate.momentum_signal(m), fwd_spec).iloc[start:].mean(),
    }

    # ------------------------------------------------------------ books
    books = {
        "reversal": rebalance_every(decile_weights(rev), every=5, start=start),        # weekly
        "reversal_lm": rebalance_every(lm_weights(rev), every=5, start=start),
        "reversal_daily": rebalance_every(decile_weights(rev), every=1, start=start),
        "momentum": rebalance_every(decile_weights(mom), every=21, start=start),       # monthly
    }
    books["momentum_beta_hedged"] = beta_hedge(books["momentum"], m.beta)
    daily_vol = R.rolling(60, min_periods=20).std().bfill()      # trailing realized vol
    adv = m.adv_usd.shift(1).bfill()                             # ADV known before trading
    sl = slice(start + 1, None)                                  # evaluation window

    def run(name: str, book_usd: float) -> pd.DataFrame:
        return apply_costs(books[name], R, book_usd, m.spread_bps, adv, daily_vol,
                           IMPACT_COEF, BORROW_BPS_PER_YEAR).iloc[sl]

    pnl = {k: run(k, BASE_BOOK_USD) for k in books}
    summary = {k: stats(v) for k, v in pnl.items()}

    # ------------------------------------------------------------ cost sensitivity
    flat = {k: [flat_cost_sharpe(pnl[k], c) for c in FLAT_COSTS_BPS] for k in ("reversal", "momentum")}
    breakeven_bps = {k: 1e4 * (pnl[k]["gross"] - pnl[k]["borrow_cost"]).mean() / pnl[k]["turnover"].mean()
                     for k in ("reversal", "reversal_daily", "momentum")}
    by_size = {k: [utils.annualized_sharpe(run(k, b)["net"].to_numpy()) for b in BOOK_SIZES_USD]
               for k in ("reversal", "momentum")}

    # ------------------------------------------------------------ momentum crash check
    W = books["momentum"]
    book_beta = (W.mul(m.beta, axis=1).sum(axis=1) * 2).iloc[sl]   # per $1 long + $1 short
    mkt = m.factor_returns["market"]
    mkt_12m = mkt.rolling(252).sum().iloc[sl]
    mom_month = pnl["momentum"]["net"].rolling(21).sum()
    worst_end = mom_month.idxmin()
    i_end = m.dates.get_loc(worst_end)
    i_beg = i_end - 20
    # decompose the momentum book's gross P&L with the TRUE model: market beta / other factors
    # (sectors + styles) / specific returns
    W_held = W.shift(1)
    beta_pnl = W_held.mul(m.beta, axis=1).sum(axis=1) * mkt
    spec_pnl = (W_held * m.specific_returns).sum(axis=1)
    other_factor_pnl = (W_held * R).sum(axis=1) - beta_pnl - spec_pnl
    crash = {
        "worst_21d_end_date": worst_end.date().isoformat(),
        "worst_21d_return_pct": 100 * mom_month.min(),
        "worst_21d_in_sd_of_monthly_returns": mom_month.min() / (pnl["momentum"]["net"].std() * np.sqrt(21)),
        "market_return_same_21d_pct": 100 * mkt.iloc[i_beg:i_end + 1].sum(),
        "beta_component_same_21d_pct": 100 * beta_pnl.iloc[i_beg:i_end + 1].sum(),
        "sector_style_factor_component_same_21d_pct": 100 * other_factor_pnl.iloc[i_beg:i_end + 1].sum(),
        "specific_component_same_21d_pct": 100 * spec_pnl.iloc[i_beg:i_end + 1].sum(),
        "book_beta_entering_per_1usd_long_short": float(book_beta.loc[m.dates[i_beg - 1]]),
        "market_trailing_12m_return_entering_pct": 100 * float(mkt_12m.loc[m.dates[i_beg - 1]]),
        "corr_book_beta_vs_trailing_12m_market": float(np.corrcoef(book_beta, mkt_12m)[0, 1]),
        "beta_hedged_same_21d_return_pct": 100 * pnl["momentum_beta_hedged"]["net"].rolling(21).sum().loc[worst_end],
    }
    stress_rows = []
    for d in m.stress_dates:
        i = m.dates.get_loc(d)
        win = m.dates[i:min(i + 63, len(m.dates))]
        if i < start + 1:
            continue
        stress_rows.append({"stress_start": d.date().isoformat(),
                            "momentum_next_63d_pct": 100 * pnl["momentum"]["net"].reindex(win).sum(),
                            "reversal_next_63d_pct": 100 * pnl["reversal"]["net"].reindex(win).sum(),
                            "market_next_63d_pct": 100 * mkt.reindex(win).sum()})

    # ------------------------------------------------------------ print
    print("\nIC recovery (mean daily cross-sectional IC vs next-day SPECIFIC return):")
    print(f"  1-week reversal on total returns: {ic['reversal_measured_vs_specific']:.4f} "
          f"(planted {REVERSAL_STRENGTH}; oracle specific-return signal {ic['reversal_oracle_signal_vs_specific']:.4f})")
    print(f"  12-1 momentum on total returns:   {ic['momentum_measured_vs_specific']:.4f} "
          f"(planted {MOMENTUM_STRENGTH}; oracle {ic['momentum_oracle_signal_vs_specific']:.4f})")
    print(f"\nBooks at ${BASE_BOOK_USD / 1e6:.0f}M gross, impact coef {IMPACT_COEF}, borrow "
          f"{BORROW_BPS_PER_YEAR:.0f} bps/yr:")
    print(f"  {'book':<22}{'SR gross':>9}{'SR net':>8}{'ret g%':>8}{'ret n%':>8}{'turn x/yr':>10}{'cost bps':>9}")
    for k, s in summary.items():
        print(f"  {k:<22}{s['sharpe_gross']:9.2f}{s['sharpe_net']:8.2f}{s['ann_return_gross_pct']:8.2f}"
              f"{s['ann_return_net_pct']:8.2f}{s['annual_turnover_x_gross']:10.1f}"
              f"{s['avg_cost_bps_per_dollar_traded']:9.1f}")
    print("  break-even flat one-way cost (bps per $ traded): "
          + ", ".join(f"{k} {v:.1f}" for k, v in breakeven_bps.items()))
    print("  net Sharpe by gross book size: "
          + "; ".join(f"${b / 1e6:,.0f}M: rev {r:.2f} / mom {mo:.2f}"
                      for b, r, mo in zip(BOOK_SIZES_USD, by_size["reversal"], by_size["momentum"])))
    print(f"\nWorst 21-day momentum stretch (net) ending {crash['worst_21d_end_date']}: "
          f"{crash['worst_21d_return_pct']:.2f}% ({crash['worst_21d_in_sd_of_monthly_returns']:.1f} sd); market "
          f"{crash['market_return_same_21d_pct']:+.1f}% after a {crash['market_trailing_12m_return_entering_pct']:+.0f}% "
          f"trailing year; book beta entering {crash['book_beta_entering_per_1usd_long_short']:+.2f} "
          f"(loss split: market beta {crash['beta_component_same_21d_pct']:+.2f}%, sectors+styles "
          f"{crash['sector_style_factor_component_same_21d_pct']:+.2f}%, specific "
          f"{crash['specific_component_same_21d_pct']:+.2f}%); "
          f"beta-hedged book {crash['beta_hedged_same_21d_return_pct']:+.2f}%")
    print(f"  corr(momentum book beta, trailing 12m market return) = {crash['corr_book_beta_vs_trailing_12m_market']:.2f}")

    # ------------------------------------------------------------ plots
    dates = pnl["reversal"].index
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=False)
    for ax, k in zip(axes, ("reversal", "momentum")):
        c = COLORS[k]
        ax.plot(dates, 100 * pnl[k]["gross"].cumsum(), color=c, lw=1.6, ls="--", label="gross")
        ax.plot(dates, 100 * pnl[k]["net"].cumsum(), color=c, lw=2.0, label=f"net (${BASE_BOOK_USD / 1e6:.0f}M book)")
        for d in m.stress_dates:
            if d >= dates[0]:
                ax.axvspan(d, d + pd.Timedelta(days=60), color="0.5", alpha=0.15, lw=0)
        s = summary[k]
        ttl = "1-week reversal, decile L/S, weekly" if k == "reversal" else "12-1 momentum, decile L/S, monthly"
        ax.set_title(f"{ttl}\nSharpe gross {s['sharpe_gross']:.2f}, net {s['sharpe_net']:.2f}; "
                     f"turnover {s['annual_turnover_x_gross']:.0f}x/yr", fontsize=10)
        ax.axhline(0, color="0.3", lw=0.8)
        ax.set_ylabel("cumulative P&L, % of gross book")
        ax.legend(loc="upper left")
    axes[1].annotate(f"worst month ({crash['worst_21d_return_pct']:.1f}%): market\n"
                     f"{crash['market_return_same_21d_pct']:+.1f}% after a {crash['market_trailing_12m_return_entering_pct']:+.0f}% "
                     f"year; loss from sector/style\ntilts {crash['sector_style_factor_component_same_21d_pct']:+.1f}%, "
                     f"market beta {crash['beta_component_same_21d_pct']:+.1f}%",
                     xy=(worst_end, 100 * pnl["momentum"]["net"].cumsum().loc[worst_end]),
                     xytext=(0.40, 0.03), textcoords="axes fraction", fontsize=8.5, va="bottom",
                     arrowprops={"arrowstyle": "->", "color": "0.3"})
    fig.suptitle("Reversal vs momentum, gross vs net of spread + impact + borrow (synthetic data; "
                 "grey = stress episodes)", fontsize=11, fontweight="bold")
    fig.tight_layout()
    utils.save_fig(ctx, fig, "gross-vs-net")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
    for k, lbl in (("reversal", "1-week reversal (weekly)"), ("momentum", "12-1 momentum (monthly)")):
        a1.plot(FLAT_COSTS_BPS, flat[k], color=COLORS[k], lw=2, label=lbl)
        a1.plot(summary[k]["avg_cost_bps_per_dollar_traded"], summary[k]["sharpe_net"], "o", ms=8,
                color=COLORS[k], mec="white", mew=1.5)
        a2.plot(np.array(BOOK_SIZES_USD) / 1e6, by_size[k], "o-", color=COLORS[k], lw=2, ms=7, label=lbl)
    a1.axhline(0, color="0.3", lw=0.8)
    a1.set_xlabel("assumed flat one-way cost, bps per $ traded")
    a1.set_ylabel("annualized net Sharpe")
    a1.set_title("Net Sharpe vs cost assumption\n(dots: spread + impact model at $100M)", fontsize=10)
    a1.legend(loc="upper right")
    a2.set_xscale("log")
    a2.axhline(0, color="0.3", lw=0.8)
    a2.set_xlabel("gross book size, $M (log scale)")
    a2.set_ylabel("annualized net Sharpe")
    a2.set_title("Capacity: net Sharpe vs book size\n(half-spread + square-root impact + borrow)", fontsize=10)
    a2.legend(loc="lower left")
    fig.suptitle("Reversal's edge is thinner than its cost; momentum's survives (synthetic data)",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    utils.save_fig(ctx, fig, "sharpe-vs-costs")

    # ------------------------------------------------------------ results
    keep = ("sharpe_gross", "sharpe_net", "ann_return_gross_pct", "ann_return_net_pct", "annual_turnover_x_gross",
            "avg_cost_bps_per_dollar_traded", "trading_cost_pct_per_year", "max_drawdown_net_pct")
    utils.write_results(ctx, {
        "n_stocks": n_stocks, "n_days": n_days, "evaluation_days": len(dates),
        "universe_total_adv_usd_bn": float(m.adv_usd.iloc[sl].sum(axis=1).mean() / 1e9),
        "median_stock_adv_usd_m": float(m.adv_usd.iloc[sl].mean().median() / 1e6),
        "base_gross_book_usd": BASE_BOOK_USD, "impact_coef": IMPACT_COEF,
        "borrow_bps_per_year": BORROW_BPS_PER_YEAR,
        "ic": ic,
        "reversal_sharpe_gross": summary["reversal"]["sharpe_gross"],
        "reversal_sharpe_net_100m": summary["reversal"]["sharpe_net"],
        "momentum_sharpe_gross": summary["momentum"]["sharpe_gross"],
        "momentum_sharpe_net_100m": summary["momentum"]["sharpe_net"],
        "reversal_annual_turnover_x_gross": summary["reversal"]["annual_turnover_x_gross"],
        "momentum_annual_turnover_x_gross": summary["momentum"]["annual_turnover_x_gross"],
        "breakeven_flat_cost_bps": breakeven_bps,
        "books": {k: {kk: s[kk] for kk in keep} for k, s in summary.items()},
        "net_sharpe_by_book_usd": {f"{b:.0e}": {"reversal": r, "momentum": mo}
                                   for b, r, mo in zip(BOOK_SIZES_USD, by_size["reversal"], by_size["momentum"])},
        "momentum_crash": crash,
        "stress_episodes": stress_rows,
    })


if __name__ == "__main__":
    main()
