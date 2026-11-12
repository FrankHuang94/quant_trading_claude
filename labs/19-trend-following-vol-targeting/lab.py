"""Lab 19: trend following (time-series momentum) with volatility targeting and risk budgeting.

What it demonstrates
  * Time-series momentum (TSMOM; Moskowitz, Ooi & Pedersen 2012) on a synthetic panel of 24
    futures (6 equity index, 6 government bond, 6 FX, 6 commodity; 20 years of daily excess
    returns from labs/common simulate_futures). The simulator plants persistent drift regimes
    (mean length 250 days) and nothing else: no carry, no equity premium.
  * The forecast: the average of the signs of the past 1-, 3- and 12-month returns.
  * Position sizing, three ways, on the same forecast:
      (a) equal notional per market;
      (b) inverse volatility per market (MOP 2012 style: each market sized to 40% ex-ante vol, 1/N);
      (c) the vol-targeted book: equal risk budget per asset class (risk parity across classes),
          inverse vol within class, the whole book scaled to a 10% ex-ante portfolio vol with an
          EWMA covariance, a per-market cap, and a no-trade buffer to cut turnover.
  * Costs: slippage of 0.5-2 bps of notional per trade plus roll costs (stylized, by asset class).
  * "Crisis alpha": quarterly trend returns vs the equity-index future form a smile (convex payoff).
  * Truth: an oracle that knows the sign of the planted drift, and how often TSMOM agrees with it.
  * Pitfalls: the fast 1-month signal loses a third of its Sharpe to costs; equal notional lets
    commodities and equities dominate the risk and lets realized vol swing; one 20-year backtest
    is a noisy estimate (12 independent synthetic worlds give a wide range of Sharpe ratios).

Supports: docs/02-strategies/g-futures-and-macro-context/trend-following-and-ctas.md,
          docs/03-algorithms/d-portfolio-construction/position-sizing-and-risk-budgeting.md

Run: python labs/19-trend-following-vol-targeting/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import simulate, utils  # noqa: E402

# Stylized costs, bps of notional per one-way trade (half-spread + slippage), and contract rolls
# per year. A roll is traded as a calendar spread and is charged one slippage unit.
SLIPPAGE_BPS = {"equity": 1.0, "rates": 0.5, "fx": 0.5, "commodity": 2.0}
ROLLS_PER_YEAR = {"equity": 4, "rates": 4, "fx": 4, "commodity": 8}
LOOKBACKS = (21, 63, 252)          # 1, 3 and 12 months in trading days
TARGET_VOL = 0.10                  # annualized portfolio vol target
ASSET_CAP = 0.40                   # max standalone vol of one market, as a fraction of TARGET_VOL
BUFFER = 0.25                      # no-trade band, fraction of the market's typical position
VOL_COM = 60                       # EWMA center of mass for vol, days (as in MOP 2012)
CORR_SPAN = 250                    # EWMA span for the correlation matrix, days
MOP_ASSET_VOL = 0.40               # per-market ex-ante vol in the MOP-style book
COLORS = {"vt": "#2a78d6", "en": "#eb6834", "iv": "#1baf7a", "eq": "#6b6b6b", "fit": "#eda100"}


# =====================================================================================
# === CORE ALGORITHM ===
# Positions are notional exposure as a fraction of capital (NAV): +0.8 = long futures worth
# 80% of NAV. Everything is computed at the close of day t and earns day t+1's return.
# =====================================================================================

def tsmom_signal(returns, lookbacks=(21, 63, 252)):
    """Time-series momentum forecast in [-1, +1] for every market and day.

    returns: DataFrame (dates x markets) of daily excess returns.
    For each lookback L (trading days) take the sign of the market's OWN past L-day return
    (+1 = it went up, so be long; -1 = short), then average the votes across lookbacks.
    With (21, 63, 252) the forecast is -1, -1/3, +1/3 or +1. Known at the close of day t.
    """
    votes = [np.sign(returns.rolling(L).sum()) for L in lookbacks]
    return sum(votes) / len(lookbacks)


def vol_target_positions(signal, ann_vol, corr, asset_class, target_vol=0.10, asset_cap=0.40):
    """One day's positions (notional / NAV) for a vol-targeted, risk-budgeted trend book.

    signal: forecast per market in [-1, 1]; ann_vol: ex-ante annualized vol per market;
    corr: ex-ante correlation matrix; asset_class: class label per market (numpy arrays).
    1. Risk budget: each asset class gets an equal share of risk, split equally inside the class.
    2. Inverse vol: weight = signal x budget / vol, so a 2%-vol bond future gets ~20x the
       notional of a 40%-vol gas future for the same risk.
    3. Vol target: scale the whole book so its ex-ante vol sqrt(w' C w) equals target_vol.
    4. Cap: no single market may carry standalone vol above asset_cap x target_vol.
    """
    classes, counts = np.unique(asset_class, return_counts=True)
    n_in_class = dict(zip(classes, counts))
    budget = np.array([1.0 / (len(classes) * n_in_class[c]) for c in asset_class])
    w = signal * budget / ann_vol                       # step 1 + 2
    cov = corr * np.outer(ann_vol, ann_vol)             # annualized covariance
    port_vol = np.sqrt(w @ cov @ w)
    if port_vol > 0:
        w = w * target_vol / port_vol                   # step 3
    cap = asset_cap * target_vol / ann_vol              # step 4 (in notional units)
    return np.clip(w, -cap, cap)


def trade_with_buffer(target, current, band):
    """No-trade zone: keep the current position unless the target moves more than `band` away,
    and then trade only to the edge of the band (not all the way). Cuts turnover from noise in
    the vol estimates at little cost in tracking."""
    gap = target - current
    return np.where(np.abs(gap) > band, target - np.sign(gap) * band, current)


# === END CORE ALGORITHM ===
# =====================================================================================


def ewma_vol(returns: pd.DataFrame, com: float = VOL_COM) -> pd.DataFrame:
    """Ex-ante annualized vol from an EWMA of squared daily returns (known at the close of t)."""
    return np.sqrt((returns ** 2).ewm(com=com, min_periods=60).mean() * 252)


def ewma_corr(R: np.ndarray, span: int = CORR_SPAN) -> np.ndarray:
    """EWMA correlation matrices (days x N x N), each using returns up to and including day t."""
    lam = 1.0 - 2.0 / (span + 1.0)
    T, N = R.shape
    out = np.empty((T, N, N))
    c = np.cov(R[:60].T)                  # initial guess; forgotten long before trading starts
    for t in range(T):
        c = lam * c + (1.0 - lam) * np.outer(R[t], R[t])
        d = np.sqrt(np.diag(c))
        out[t] = c / np.outer(d, d)
    return out


def build_book(signal: np.ndarray, vol: np.ndarray, corr: np.ndarray, classes: np.ndarray,
               start: int, buffer: float = BUFFER) -> np.ndarray:
    """Daily vol-targeted positions with an optional no-trade buffer (days x markets)."""
    T, N = signal.shape
    W = np.zeros((T, N))
    current = np.zeros(N)
    typical = None                         # EWMA of |target|: the market's typical position size
    for t in range(start, T):
        if not (np.all(np.isfinite(signal[t])) and np.all(np.isfinite(vol[t]))):
            continue
        target = vol_target_positions(signal[t], vol[t], corr[t], classes, TARGET_VOL, ASSET_CAP)
        typical = np.abs(target) if typical is None else 0.99 * typical + 0.01 * np.abs(target)
        current = trade_with_buffer(target, current, buffer * typical) if buffer > 0 else target
        W[t] = current
    return W


def cap_binding_share(signal: np.ndarray, vol: np.ndarray, corr: np.ndarray, classes: np.ndarray,
                      start: int) -> float:
    """Share of market-days on which the per-market cap in vol_target_positions binds."""
    hits = total = 0
    for t in range(start, len(signal)):
        if np.all(np.isfinite(signal[t])) and np.all(np.isfinite(vol[t])):
            free = vol_target_positions(signal[t], vol[t], corr[t], classes, TARGET_VOL, np.inf)
            hits += int(np.sum(np.abs(free) > ASSET_CAP * TARGET_VOL / vol[t]))
            total += len(free)
    return hits / max(total, 1)


def backtest(W: np.ndarray, R: np.ndarray, classes: np.ndarray, start: int,
             cost_mult: float = 1.0) -> dict:
    """Gross and net daily returns of positions W (held from close t to close t+1)."""
    slip = np.array([SLIPPAGE_BPS[c] for c in classes]) * 1e-4 * cost_mult
    rolls = np.array([ROLLS_PER_YEAR[c] for c in classes])
    gross = np.r_[0.0, np.sum(W[:-1] * R[1:], axis=1)]
    trades = np.abs(np.diff(np.vstack([np.zeros(W.shape[1]), W]), axis=0))
    trade_cost = trades @ slip
    roll_cost = np.abs(W) @ (slip * rolls) / 252.0
    keep = slice(start + 1, len(R))
    net = gross - trade_cost - roll_cost
    return {"gross": gross[keep], "net": net[keep], "turnover": trades[keep].sum(axis=1),
            "trade_cost": trade_cost[keep], "roll_cost": roll_cost[keep],
            "gross_leverage": np.abs(W[keep]).sum(axis=1), "pnl_by_market": W[:-1][start:] * R[start + 1:]}


def sharpe(x) -> float:
    return utils.annualized_sharpe(np.asarray(x))


def rolling_vol(x: np.ndarray, window: int = 63) -> np.ndarray:
    return pd.Series(x).rolling(window).std().dropna().to_numpy() * np.sqrt(252)


def risk_share_by_class(pnl_by_market: np.ndarray, classes: np.ndarray) -> dict:
    """Euler share of realized variance: cov(class P&L, total P&L) / var(total P&L)."""
    total = pnl_by_market.sum(axis=1)
    return {c: float(np.cov(pnl_by_market[:, classes == c].sum(axis=1), total)[0, 1] / total.var(ddof=1))
            for c in np.unique(classes)}


def smile_fit(trend_q: np.ndarray, equity_q: np.ndarray) -> dict:
    """OLS of quarterly trend return on equity return and its square: y = a + b x + c x^2."""
    X = np.column_stack([np.ones_like(equity_q), equity_q, equity_q ** 2])
    coef, *_ = np.linalg.lstsq(X, trend_q, rcond=None)
    resid = trend_q - X @ coef
    cov = resid.var(ddof=3) * np.linalg.inv(X.T @ X)
    worst = equity_q <= np.quantile(equity_q, 0.10)
    return {"a": coef[0], "b": coef[1], "c": coef[2], "t_c": coef[2] / np.sqrt(cov[2, 2]),
            "worst_decile_equity": equity_q[worst].mean(), "worst_decile_trend": trend_q[worst].mean(),
            "corr": float(np.corrcoef(trend_q, equity_q)[0, 1])}


def quarterly(x: np.ndarray, dates: pd.DatetimeIndex) -> np.ndarray:
    return pd.Series(x, index=dates).resample("QE").sum().to_numpy()


def run_world(seed: int, n_days: int) -> dict:
    """Main strategy (and equal notional) on one more synthetic world, for the robustness check."""
    fm = simulate.simulate_futures(n_days=n_days, seed=seed)
    R, classes = fm.returns.to_numpy(), fm.asset_class.to_numpy()
    start = max(LOOKBACKS) + 5
    sig = tsmom_signal(fm.returns, LOOKBACKS).to_numpy()
    W = build_book(sig, ewma_vol(fm.returns).to_numpy(), ewma_corr(R), classes, start)
    bt = backtest(W, R, classes, start)
    bt_en = backtest(np.nan_to_num(sig) / R.shape[1], R, classes, start)
    dates = fm.returns.index[start + 1:]
    trend_q, eq_q = quarterly(bt["net"], dates), quarterly(R[start + 1:, 0], dates)
    sm = smile_fit(trend_q, eq_q)
    return {"sharpe_net": sharpe(bt["net"]), "sharpe_net_en": sharpe(bt_en["net"]), "curvature": sm["c"],
            "worst_decile_trend": sm["worst_decile_trend"], "trend_q": trend_q, "eq_q": eq_q}


def main():
    ctx = utils.setup(__file__, "Lab 19: trend following with vol targeting")
    n_days = 252 * 8 if ctx.smoke else 252 * 20
    n_worlds = 2 if ctx.smoke else 12

    fm = simulate.simulate_futures(n_days=n_days, seed=ctx.seed)
    rets, classes = fm.returns, fm.asset_class.to_numpy()
    R, names = rets.to_numpy(), list(rets.columns)
    T, N = R.shape
    start = max(LOOKBACKS) + 5               # first day with a full 12-month lookback
    dates = rets.index[start + 1:]
    eq_col = names.index("EQ_US_LARGE")

    vol = ewma_vol(rets).to_numpy()
    corr = ewma_corr(R)
    signal = tsmom_signal(rets, LOOKBACKS).to_numpy()

    # ---- the three sizing schemes on the same forecast ----------------------------------------
    W_vt = build_book(signal, vol, corr, classes, start, buffer=BUFFER)
    W_vt_nobuf = build_book(signal, vol, corr, classes, start, buffer=0.0)
    sig0 = np.nan_to_num(signal)
    W_en = sig0 / N                                               # equal notional, 1/N each
    W_iv = sig0 * MOP_ASSET_VOL / np.nan_to_num(vol, nan=np.inf) / N   # MOP-style inverse vol
    W_en[:start] = W_iv[:start] = 0.0
    # equal notional and inverse vol have no portfolio-level target: scale them ex post (with
    # hindsight) to the same 10% realized vol, so curves and costs are comparable
    for W in (W_en, W_iv):
        W *= TARGET_VOL / (np.std(backtest(W, R, classes, start)["gross"]) * np.sqrt(252))
    cap_share = cap_binding_share(signal, vol, corr, classes, start)
    books = {"vt": W_vt, "vt_nobuf": W_vt_nobuf, "en": W_en, "iv": W_iv}
    bts = {k: backtest(W, R, classes, start) for k, W in books.items()}

    # ---- truth: oracle that knows the sign of the planted drift --------------------------------
    true_sign = np.sign(fm.true_drift.to_numpy())
    W_or = build_book(true_sign, vol, corr, classes, start, buffer=BUFFER)
    bt_or = backtest(W_or, R, classes, start)
    agree = float(np.mean(np.sign(signal[start:]) == true_sign[start:]))
    single_asset_sharpes = [sharpe(bts["iv"]["pnl_by_market"][:, j]) for j in range(N)]

    # ---- one lookback at a time (same sizing): speed vs costs ----------------------------------
    by_lookback = {}
    for L in (21, 63, 126, 252):
        W_L = build_book(tsmom_signal(rets, (L,)).to_numpy(), vol, corr, classes, start, buffer=BUFFER)
        b = backtest(W_L, R, classes, start)
        by_lookback[L] = {"gross": sharpe(b["gross"]), "net": sharpe(b["net"]),
                          "turnover": b["turnover"].mean() * 252}
    cost_sens = {m: sharpe(backtest(W_vt, R, classes, start, cost_mult=m)["net"]) for m in (0, 1, 2, 4)}

    # ---- crisis alpha: quarterly trend vs equity-index future ----------------------------------
    trend_q = quarterly(bts["vt"]["net"], dates)
    eq_q = quarterly(R[start + 1:, eq_col], dates)
    smile = smile_fit(trend_q, eq_q)

    # ---- robustness: independent synthetic worlds ----------------------------------------------
    worlds = pd.DataFrame([run_world(ctx.seed + 1000 + k, n_days) for k in range(n_worlds)])
    pooled_trend = np.concatenate([trend_q] + list(worlds.trend_q))
    pooled_eq = np.concatenate([eq_q] + list(worlds.eq_q))

    # ---- summaries -----------------------------------------------------------------------------
    vt, en, iv = bts["vt"], bts["en"], bts["iv"]
    rv = {k: rolling_vol(bts[k]["net"]) for k in ("vt", "en", "iv")}
    share_vt = risk_share_by_class(vt["pnl_by_market"], classes)
    share_en = risk_share_by_class(en["pnl_by_market"], classes)
    cost_drag = (vt["trade_cost"].mean() + vt["roll_cost"].mean()) * 252
    cum = {k: np.cumsum(bts[k][kind]) * 100 for k, kind in (("vt", "net"), ("en", "net"), ("iv", "net"))}
    cum_vt_gross = np.cumsum(vt["gross"]) * 100
    eq_scaled = R[start + 1:, eq_col] * TARGET_VOL / (R[start + 1:, eq_col].std() * np.sqrt(252))

    # ---- plot 1: cumulative returns and rolling vol --------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.35, 1]})
    ax1.plot(dates, cum["vt"], color=COLORS["vt"], lw=2,
             label=f"Vol-targeted, risk parity by class, net (Sharpe {sharpe(vt['net']):.2f})")
    ax1.plot(dates, cum_vt_gross, color=COLORS["vt"], lw=1, ls="--",
             label=f"same, gross of costs (Sharpe {sharpe(vt['gross']):.2f})")
    ax1.plot(dates, cum["iv"], color=COLORS["iv"], lw=1.4,
             label=f"Inverse vol per market (MOP style), net ({sharpe(iv['net']):.2f})*")
    ax1.plot(dates, cum["en"], color=COLORS["en"], lw=1.4,
             label=f"Equal notional, net ({sharpe(en['net']):.2f})*")
    ax1.plot(dates, np.cumsum(eq_scaled) * 100, color=COLORS["eq"], lw=1, alpha=0.8,
             label=f"Long equity-index future EQ_US_LARGE ({sharpe(eq_scaled):.2f})*")
    ax1.set_ylabel("cumulative return (% of NAV, not compounded)")
    ax1.set_xlabel("year (synthetic calendar)")
    ax1.set_title("24-market TSMOM (1/3/12-month signs), 10% vol\n(synthetic data; * scaled ex post to 10% vol)")
    ax1.legend(fontsize=7.8, loc="upper left")
    for k, lab in (("en", "Equal notional"), ("iv", "Inverse vol (MOP style)"), ("vt", "Vol-targeted book")):
        ax2.plot(dates[62:], rv[k] * 100, color=COLORS[k], lw=1.6 if k == "vt" else 1.1,
                 label=f"{lab}: 5th-95th pct {np.percentile(rv[k], 5) * 100:.1f}-"
                       f"{np.percentile(rv[k], 95) * 100:.1f}%")
    ax2.axhline(TARGET_VOL * 100, color="k", lw=0.8, ls=":")
    ax2.set_ylabel("rolling 3-month realized vol (% per year)")
    ax2.set_xlabel("year (synthetic calendar)")
    ax2.set_title("Vol targeting keeps risk near 10%\n(synthetic data)")
    ax2.legend(fontsize=8, loc="upper left")
    ax2.set_ylim(0, max(25, np.percentile(rv["en"], 99.5) * 110))
    utils.save_fig(ctx, fig, "cumulative")

    # ---- plot 2: crisis-alpha smile --------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.3, 1]})
    ax1.scatter(eq_q * 100, trend_q * 100, s=22, color=COLORS["vt"], alpha=0.75, label="one quarter")
    xs = np.linspace(eq_q.min(), eq_q.max(), 200)
    ax1.plot(xs * 100, (smile["a"] + smile["b"] * xs + smile["c"] * xs ** 2) * 100, color=COLORS["fit"],
             lw=2.2, label=f"quadratic fit: curvature {smile['c']:.2f} (t = {smile['t_c']:.1f})")
    ax1.axhline(0, color="k", lw=0.6)
    ax1.axvline(0, color="k", lw=0.6)
    ax1.set_xlabel("equity-index future (EQ_US_LARGE) quarterly return (%)")
    ax1.set_ylabel("trend book quarterly return, net (%)")
    ax1.set_title("Crisis alpha: trend vs equities is a smile\n"
                  f"(synthetic data, seed {ctx.seed}, quarterly, 10% vol book)")
    ax1.legend(fontsize=8.5, loc="upper center")
    edges = np.quantile(pooled_eq, [0, 0.2, 0.4, 0.6, 0.8, 1.0])
    bucket = np.clip(np.searchsorted(edges, pooled_eq, side="right") - 1, 0, 4)
    means = np.array([pooled_trend[bucket == k].mean() for k in range(5)]) * 100
    ses = np.array([pooled_trend[bucket == k].std(ddof=1) / np.sqrt((bucket == k).sum())
                    for k in range(5)]) * 100
    eq_means = np.array([pooled_eq[bucket == k].mean() for k in range(5)]) * 100
    xpos = np.arange(5)
    ax2.bar(xpos, means, yerr=1.96 * ses, color=COLORS["vt"], alpha=0.85, capsize=4,
            label="trend book, mean +- 95% CI")
    ax2.set_xticks(xpos, [f"Q{k + 1}\nequity {m:+.1f}%" for k, m in enumerate(eq_means)], fontsize=8.5)
    ax2.axhline(0, color="k", lw=0.6)
    ax2.set_xlabel("equity quarters sorted into quintiles (Q1 = worst)")
    ax2.set_ylabel("average trend quarterly return, net (%)")
    ax2.set_title(f"Pooled over {n_worlds + 1} synthetic {n_days // 252}-year worlds\n"
                  f"({len(pooled_eq):,} quarters): trend return by equity quintile")
    ax2.legend(fontsize=8.5, loc="upper center")
    utils.save_fig(ctx, fig, "crisis-alpha")

    # ---- results ---------------------------------------------------------------------------------
    results = {
        "sharpe_gross_vol_target": sharpe(vt["gross"]),
        "sharpe_net_vol_target": sharpe(vt["net"]),
        "sharpe_net_vol_target_no_buffer": sharpe(bts["vt_nobuf"]["net"]),
        "sharpe_net_equal_notional": sharpe(en["net"]),
        "sharpe_net_inverse_vol_mop": sharpe(iv["net"]),
        "realized_vol_vol_target": np.std(vt["net"]) * np.sqrt(252),
        "rolling_3m_vol_p5_p95_vol_target": [np.percentile(rv["vt"], 5), np.percentile(rv["vt"], 95)],
        "rolling_3m_vol_p5_p95_equal_notional": [np.percentile(rv["en"], 5), np.percentile(rv["en"], 95)],
        "risk_share_commodity_equity_equal_notional": share_en["commodity"] + share_en["equity"],
        "risk_share_by_class_vol_target": share_vt,
        "annual_turnover_x_nav": vt["turnover"].mean() * 252,
        "annual_turnover_x_nav_no_buffer": bts["vt_nobuf"]["turnover"].mean() * 252,
        "annual_cost_drag_pct": 100 * cost_drag,
        "mean_gross_leverage_x_nav": vt["gross_leverage"].mean(),
        "asset_cap_binding_share_of_market_days": cap_share,
        "sharpe_by_lookback_gross_net": {f"{L}d": [v["gross"], v["net"]] for L, v in by_lookback.items()},
        "sharpe_net_by_cost_multiplier": {f"{m}x": v for m, v in cost_sens.items()},
        "oracle_sharpe_gross_true_drift_sign": sharpe(bt_or["gross"]),
        "signal_agrees_with_true_drift_sign": agree,
        "mean_single_market_sharpe_gross": float(np.mean(single_asset_sharpes)),
        "smile_curvature": smile["c"], "smile_curvature_t": smile["t_c"],
        "trend_vs_equity_quarterly_corr": smile["corr"],
        "worst_decile_equity_quarters_mean_equity_return": smile["worst_decile_equity"],
        "worst_decile_equity_quarters_mean_trend_return": smile["worst_decile_trend"],
        "n_worlds": n_worlds,
        "worlds_sharpe_net_mean_p10_p90": [worlds.sharpe_net.mean(), worlds.sharpe_net.quantile(0.1),
                                           worlds.sharpe_net.quantile(0.9)],
        "worlds_share_positive_curvature": float((worlds.curvature > 0).mean()),
        "worlds_share_positive_worst_decile_trend": float((worlds.worst_decile_trend > 0).mean()),
        "worlds_mean_sharpe_net_equal_notional": worlds.sharpe_net_en.mean(),
        "pooled_quintile_mean_trend_return_q1_to_q5": means / 100,
    }
    utils.write_results(ctx, results)

    print(f"\n{N} markets x {T} days; trading from day {start}; costs: slippage {SLIPPAGE_BPS} bps, "
          f"rolls/yr {ROLLS_PER_YEAR}")
    print(f"{'book':<42}{'Sharpe gross':>13}{'Sharpe net':>11}{'vol':>7}{'turnover x NAV/yr':>19}")
    for k, lab in (("vt", "vol-targeted, risk parity, 25% buffer"), ("vt_nobuf", "  same, no buffer"),
                   ("iv", "inverse vol per market (MOP style)*"), ("en", "equal notional*")):
        b = bts[k]
        print(f"{lab:<42}{sharpe(b['gross']):>13.2f}{sharpe(b['net']):>11.2f}"
              f"{np.std(b['net']) * np.sqrt(252):>7.1%}{b['turnover'].mean() * 252:>19.0f}")
    print("  * scaled ex post to 10% realized vol")
    print(f"cost drag {100 * cost_drag:.2f}%/yr; mean gross leverage {vt['gross_leverage'].mean():.1f}x NAV; "
          f"per-market cap binds on {cap_share:.2%} of market-days")
    print("risk share by class, vol-targeted: " + ", ".join(f"{c} {v:.0%}" for c, v in share_vt.items()))
    print("risk share by class, equal notional: " + ", ".join(f"{c} {v:.0%}" for c, v in share_en.items()))
    print("one lookback at a time (gross -> net Sharpe, turnover):")
    for L, v in by_lookback.items():
        print(f"  {L:>3}d: {v['gross']:.2f} -> {v['net']:.2f}  ({v['turnover']:.0f}x NAV/yr)")
    print(f"net Sharpe by cost multiplier: " + ", ".join(f"{m}x {v:.2f}" for m, v in cost_sens.items()))
    print(f"truth: oracle (sign of true drift) gross Sharpe {sharpe(bt_or['gross']):.2f}; TSMOM sign agrees with "
          f"the true drift sign on {agree:.0%} of market-days; mean single-market Sharpe "
          f"{np.mean(single_asset_sharpes):.2f}")
    print(f"smile: trend_q = {smile['a']:.3f} {smile['b']:+.2f} eq_q {smile['c']:+.2f} eq_q^2 "
          f"(t = {smile['t_c']:.1f}); worst 10% equity quarters: equity {smile['worst_decile_equity']:.1%}, "
          f"trend {smile['worst_decile_trend']:+.1%}")
    print(f"{n_worlds} independent worlds: net Sharpe mean {worlds.sharpe_net.mean():.2f} "
          f"(10th-90th pct {worlds.sharpe_net.quantile(0.1):.2f} to {worlds.sharpe_net.quantile(0.9):.2f}); "
          f"positive smile curvature in {(worlds.curvature > 0).mean():.0%}; equal notional mean "
          f"{worlds.sharpe_net_en.mean():.2f}")
    print("pooled trend return by equity quintile (Q1 worst): " + ", ".join(f"{m:+.1f}%" for m in means))


if __name__ == "__main__":
    main()
