"""Lab 03: order-flow imbalance (OFI) vs trade imbalance vs queue imbalance.

What it demonstrates
  * Cont, Kukanov & Stoikov (2014) order-flow imbalance: every change of the best bid/ask
    (a new order, a cancel or a trade at the touch) adds or removes demand or supply; OFI sums
    these signed queue changes over fixed time intervals.
  * Contemporaneous regressions of the mid change on OFI and on trade imbalance (signed market
    order volume) for intervals of 1 s to 60 s: R^2 and betas.
  * The planted mechanics: CKS's stylized model says delta mid = OFI / (2 x depth) ticks. The lab
    estimates the price-impact coefficient in each half-hour, regresses log(beta) on log(depth)
    (CKS's test: slope -1) and compares thin, normal and thick books.
  * Prediction: the NEXT interval's mid change regressed on OFI, trade imbalance and queue
    imbalance (bid size - ask size) / (bid size + ask size), fitted on two days, evaluated on a
    third (out-of-sample R^2), and how that predictive power decays with the interval length.
  * Pitfalls: contemporaneous R^2 (~70%) is not a forecast (~5%); and a taker that trades the
    forecast loses money because the predicted move is smaller than the half-spread it pays.

Data: labs/common/simulate.py `simulate_lob` (synthetic $50 stock, 1-cent tick, 6.5-hour days).

Supports: docs/03-algorithms/f-market-making-and-hft-algorithms/order-book-and-trade-flow-signals.md
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import statsmodels.api as sm  # noqa: E402

from common import simulate, utils  # noqa: E402

TICK = 0.01
INTERVALS_S = [1, 2, 5, 10, 30, 60]          # interval lengths, seconds
MAIN_INTERVAL = 10                           # CKS used 10-second intervals
HALF_HOUR = 1800
COLORS = {"OFI": "#2a78d6", "trade imbalance": "#eb6834", "queue imbalance": "#1baf7a",
          "all three": "#6250d6", "CKS model": "#52514e"}


# =====================================================================================
# === CORE ALGORITHM ===
# Sign convention: positive OFI = net buying pressure (bid queue grows / ask queue shrinks).
# =====================================================================================

def ofi_contributions(bid, ask, bid_size, ask_size):
    """CKS (2014) contribution e_n of each top-of-book update n (vs update n-1), in shares.

    e_n = 1{bid_n >= bid_{n-1}} q^b_n - 1{bid_n <= bid_{n-1}} q^b_{n-1}
        - 1{ask_n <= ask_{n-1}} q^a_n + 1{ask_n >= ask_{n-1}} q^a_{n-1}
    Same bid price: e = change in bid size. Bid moves up: e = the whole new bid queue. Bid moves
    down: e = minus the whole old queue. Mirror-image (with opposite sign) on the ask side.
    """
    b0, b1, a0, a1 = bid[:-1], bid[1:], ask[:-1], ask[1:]
    qb0, qb1, qa0, qa1 = bid_size[:-1], bid_size[1:], ask_size[:-1], ask_size[1:]
    e = (b1 >= b0) * qb1 - (b1 <= b0) * qb0 - (a1 <= a0) * qa1 + (a1 >= a0) * qa0
    return np.concatenate([[0.0], e])                 # first update has no predecessor


def compute_ofi(quotes, interval, tick=TICK):
    """Order-flow imbalance per fixed time interval, CKS (2014).

    quotes: DataFrame with time (s), bid, ask, bid_size, ask_size, mid (one row per book update).
    Returns a DataFrame indexed by interval start (s) with
      ofi         sum of e_n over the updates in the interval (shares)
      mid_change  mid at the end of the interval minus mid at the end of the previous one (ticks)
      avg_depth   average of (bid_size + ask_size) / 2 over the updates (CKS's depth AD)
    """
    q = quotes.ffill()                                # carry quotes over a momentarily empty side
    e = ofi_contributions(*(q[c].to_numpy() for c in ("bid", "ask", "bid_size", "ask_size")))
    times = q["time"].to_numpy()
    n = int(np.ceil(times[-1] / interval))
    k = np.minimum((times // interval).astype(int), n - 1)          # interval of each update
    ofi = np.bincount(k, weights=e, minlength=n)
    depth = np.bincount(k, weights=0.5 * (q["bid_size"] + q["ask_size"]).to_numpy(), minlength=n)
    depth /= np.maximum(np.bincount(k, minlength=n), 1)
    last = np.searchsorted(times, np.arange(n + 1) * interval, side="right") - 1
    mid_at_edges = q["mid"].to_numpy()[np.maximum(last, 0)] / tick  # mid at each interval boundary
    return pd.DataFrame({"ofi": ofi, "mid_change": np.diff(mid_at_edges), "avg_depth": depth},
                        index=pd.Index(np.arange(n) * interval, name="start_s"))


def trade_imbalance(trades, interval, n_intervals):
    """Signed market-order volume per interval: buyer-initiated minus seller-initiated shares."""
    k = np.minimum((trades["time"].to_numpy() // interval).astype(int), n_intervals - 1)
    return np.bincount(k, weights=(trades["size"] * trades["side"]).to_numpy(), minlength=n_intervals)


# === END CORE ALGORITHM ===
# =====================================================================================


def interval_table(sim, interval):
    """OFI, trade imbalance, queue imbalance and spread per interval for one simulated day."""
    df = compute_ofi(sim.quotes, interval)
    df["trade_imb"] = trade_imbalance(sim.trades, interval, len(df))
    times = sim.quotes["time"].to_numpy()
    end = np.searchsorted(times, df.index.to_numpy() + interval, side="right") - 1
    df["queue_imb_end"] = sim.quotes["imbalance"].to_numpy()[end]           # state at interval end
    df["half_spread_end"] = sim.quotes["spread"].ffill().to_numpy()[end] / TICK / 2
    df["next_mid_change"] = df["mid_change"].shift(-1)                      # the forecast target
    df["next_half_spread"] = df["half_spread_end"].shift(-1)
    return df


def ols(y, X, robust=True):
    model = sm.OLS(np.asarray(y, float), sm.add_constant(np.asarray(X, float)))
    return model.fit(cov_type="HC1") if robust else model.fit()


def oos_r2(y_test, pred, y_train_mean):
    return float(1 - np.mean((y_test - pred) ** 2) / np.mean((y_test - y_train_mean) ** 2))


def main() -> None:
    ctx = utils.setup(__file__, "Lab 03: order-flow imbalance")
    n_seconds = 3600 if ctx.smoke else 23400
    seeds = [ctx.seed, ctx.seed + 1, ctx.seed + 2]               # days 1-2 train, day 3 test
    print("Lab 03: order-flow imbalance (Cont, Kukanov & Stoikov 2014)")
    print(f"  simulating {len(seeds)} days of {n_seconds:,} s (2 to fit forecasts, 1 held out) ...")
    sims = [simulate.simulate_lob(n_seconds=n_seconds, seed=s) for s in seeds]
    tables = {dt: [interval_table(s, dt) for s in sims] for dt in INTERVALS_S}

    # ---- 1) contemporaneous: delta mid on OFI and on trade imbalance, all days pooled
    contemp = {}
    for dt in INTERVALS_S:
        d = pd.concat(tables[dt])
        f_ofi, f_ti = ols(d["mid_change"], d["ofi"]), ols(d["mid_change"], d["trade_imb"])
        f_both = ols(d["mid_change"], d[["ofi", "trade_imb"]])
        contemp[dt] = {"n": len(d), "r2_ofi": f_ofi.rsquared, "r2_trade_imb": f_ti.rsquared,
                       "r2_both": f_both.rsquared,
                       "beta_ofi_ticks_per_100sh": 100 * f_ofi.params[1], "t_ofi": f_ofi.tvalues[1],
                       "beta_trade_imb_ticks_per_100sh": 100 * f_ti.params[1], "t_trade_imb": f_ti.tvalues[1],
                       "t_ofi_joint": f_both.tvalues[1], "t_trade_imb_joint": f_both.tvalues[2]}
    print("\n  Contemporaneous regressions, delta mid (ticks) on flow (pooled):")
    print("  interval   R2 OFI   R2 trades   R2 both   beta OFI (ticks/100 sh)   beta trades")
    for dt, r in contemp.items():
        print(f"  {dt:>5} s   {r['r2_ofi']:6.2f}   {r['r2_trade_imb']:9.2f}   {r['r2_both']:7.2f}"
              f"   {r['beta_ofi_ticks_per_100sh']:22.3f}   {r['beta_trade_imb_ticks_per_100sh']:11.3f}")
    c10 = contemp[MAIN_INTERVAL]
    print(f"  at {MAIN_INTERVAL} s, both in one regression: t(OFI) = {c10['t_ofi_joint']:.0f}, "
          f"t(trades) = {c10['t_trade_imb_joint']:.0f}")

    # ---- 2) the planted mechanics: beta ~ c / depth (CKS: log beta = a - lambda log AD, lambda ~ 1)
    d10 = pd.concat(tables[MAIN_INTERVAL])
    per_half_hour = []
    for day, t in enumerate(tables[MAIN_INTERVAL]):
        for h, g in t.groupby(t.index // HALF_HOUR):
            fit = ols(g["mid_change"], g["ofi"], robust=False)
            per_half_hour.append({"day": day, "half_hour": h, "beta": fit.params[1], "avg_depth": g["avg_depth"].mean()})
    hh = pd.DataFrame(per_half_hour)
    loglog = ols(np.log(hh["beta"]), np.log(hh["avg_depth"]), robust=False)
    lam, lam_se = -loglog.params[1], loglog.bse[1]
    c_hat = float((hh["beta"] * hh["avg_depth"]).mean())        # c in beta = c / AD (CKS model: 1/2)
    mean_depth = float(d10["avg_depth"].mean())
    print(f"\n  CKS check over {len(hh)} half-hours: log(beta) on log(depth) slope = {-lam:.2f} "
          f"(s.e. {lam_se:.2f}; CKS model: -1); c = beta x depth = {c_hat:.2f} (stylized model: 0.50)")
    books = []
    for label, lr in (("thin book", 3.0), ("default book", 6.0), ("thick book", 12.0)):
        s = sims[0] if lr == 6.0 else simulate.simulate_lob(n_seconds=n_seconds, seed=ctx.seed + 20, limit_rate=lr)
        t = compute_ofi(s.quotes, MAIN_INTERVAL)
        fit = ols(t["mid_change"], t["ofi"], robust=False)
        ad = float(t["avg_depth"].mean())
        books.append({"book": label, "limit_rate_per_s": lr, "avg_depth_shares": ad,
                      "beta_ticks_per_100sh": 100 * fit.params[1], "cks_model_ticks_per_100sh": 100 / (2 * ad),
                      "r2": fit.rsquared})
    print("  " + "; ".join(f"{b['book']}: depth {b['avg_depth_shares']:.0f} sh, beta {b['beta_ticks_per_100sh']:.3f} "
                           f"vs 1/(2 depth) {b['cks_model_ticks_per_100sh']:.3f} ticks/100 sh" for b in books))

    # ---- 3) prediction: next interval's mid change, fitted on days 1-2, tested on day 3
    predictive = {}
    signals = {"OFI": ["ofi"], "trade imbalance": ["trade_imb"], "queue imbalance": ["queue_imb_end"],
               "all three": ["ofi", "trade_imb", "queue_imb_end"]}
    for dt in INTERVALS_S:
        train = pd.concat(tables[dt][:2]).dropna()
        test = tables[dt][2].dropna()
        row = {}
        for name, cols in signals.items():
            fit = ols(train["next_mid_change"], train[cols], robust=False)
            pred = fit.predict(sm.add_constant(test[cols].to_numpy(), has_constant="add"))
            row[name] = oos_r2(test["next_mid_change"].to_numpy(), pred, train["next_mid_change"].mean())
            if name == "all three":
                row["_pred"], row["_test"] = pred, test
        predictive[dt] = row
    print("\n  Predicting the NEXT interval's mid change, out-of-sample R^2 (day 3):")
    print("  interval      OFI   trades   queue imb.   all three")
    for dt, r in predictive.items():
        print(f"  {dt:>5} s   {r['OFI']:6.3f}   {r['trade imbalance']:6.3f}   {r['queue imbalance']:10.3f}   {r['all three']:9.3f}")

    # ---- 4) pitfall: trade the forecast as a taker (buy at the ask / sell at the bid)
    taker = []
    for dt in (5, MAIN_INTERVAL):
        pred, test = predictive[dt]["_pred"], predictive[dt]["_test"]
        for thr in (0.0, 0.25, 0.5, 1.0):
            sel = np.abs(pred) > thr
            if sel.sum() == 0:
                continue
            gross = np.sign(pred[sel]) * test["next_mid_change"].to_numpy()[sel]     # mid to mid, ticks
            cost_in = test["half_spread_end"].to_numpy()[sel]
            cost_out = test["next_half_spread"].to_numpy()[sel]
            taker.append({"interval_s": dt, "threshold_ticks": thr, "n_trades": int(sel.sum()),
                          "share_of_intervals": float(sel.mean()),
                          "mean_abs_forecast_ticks": float(np.abs(pred[sel]).mean()),
                          "gross_ticks": float(gross.mean()), "half_spread_paid_ticks": float(cost_in.mean()),
                          "net_enter_taker_exit_mid_ticks": float((gross - cost_in).mean()),
                          "net_round_trip_ticks": float((gross - cost_in - cost_out).mean())})
    print("\n  Taker trading the 'all three' forecast (ticks per trade; held one interval):")
    for t in taker:
        print(f"  {t['interval_s']:>3} s, |forecast| > {t['threshold_ticks']:.2f}: {t['n_trades']:5d} trades, "
              f"gross {t['gross_ticks']:+.2f}, half-spread paid {t['half_spread_paid_ticks']:.2f}, "
              f"net (exit at mid) {t['net_enter_taker_exit_mid_ticks']:+.2f}, net round trip {t['net_round_trip_ticks']:+.2f}")

    # ---------------------------------------------------------------- plots
    rng = np.random.default_rng(ctx.seed)
    fit_ofi = ols(d10["mid_change"], d10["ofi"], robust=False)
    fit_ti = ols(d10["mid_change"], d10["trade_imb"], robust=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
    for ax, col, fit, name, xlab in ((axes[0], "ofi", fit_ofi, "OFI", "Order-flow imbalance over the interval (shares)"),
                                     (axes[1], "trade_imb", fit_ti, "trade imbalance", "Trade imbalance: buy minus sell market volume (shares)")):
        x, y = d10[col].to_numpy(), d10["mid_change"].to_numpy()
        ax.scatter(x, y + rng.uniform(-0.12, 0.12, y.size), s=4, alpha=0.12, color=COLORS[name], lw=0,
                   label="10-s intervals (jittered)")
        xs = np.linspace(np.percentile(x, 0.5), np.percentile(x, 99.5), 50)
        ax.plot(xs, fit.params[0] + fit.params[1] * xs, color="0.1", lw=2,
                label=f"OLS fit: {100 * fit.params[1]:.3f} ticks per 100 sh, R² = {fit.rsquared:.2f}")
        if col == "ofi":
            ax.plot(xs, xs / (2 * mean_depth), color=COLORS["CKS model"], lw=1.8, ls="--",
                    label=f"CKS model: OFI / (2 x depth), depth = {mean_depth:.0f} sh")
        ax.set_xlim(xs[0], xs[-1])
        ax.set_xlabel(xlab)
        ax.axhline(0, color="0.3", lw=0.8)
        ax.legend(fontsize=8, loc="upper left", markerscale=3)
    axes[0].set_ylabel("Mid-price change over the interval (ticks, 1 tick = $0.01)")
    axes[0].set_ylim(-8, 8)
    axes[0].set_title("Order-flow imbalance (OFI)", fontsize=10)
    axes[1].set_title("Trade imbalance", fontsize=10)
    fig.suptitle(f"Lab 03: mid change vs order flow, {MAIN_INTERVAL}-second intervals (synthetic data)", fontweight="bold")
    fig.text(0.5, -0.03, f"{len(d10):,} intervals from {len(seeds)} simulated days of a $50 stock with a 1-cent tick; "
             "x-axes trimmed to the 0.5-99.5 percentiles.", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "ofi-scatter")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
    xs = np.array(INTERVALS_S)
    for name, key, marker in (("OFI", "r2_ofi", "o"), ("trade imbalance", "r2_trade_imb", "s")):
        axes[0].plot(xs, [100 * contemp[dt][key] for dt in INTERVALS_S], marker=marker, ms=7, lw=2, color=COLORS[name], label=name)
    axes[0].set_ylim(0, 100)
    axes[0].set_ylabel("R² of the same interval's mid change (%)")
    axes[0].set_title("Same interval (explains, cannot trade)", fontsize=10)
    for name, marker in (("OFI", "o"), ("trade imbalance", "s"), ("queue imbalance", "^"), ("all three", "D")):
        axes[1].plot(xs, [100 * predictive[dt][name] for dt in INTERVALS_S], marker=marker, ms=7, lw=2,
                     color=COLORS[name], label=name)
    axes[1].axhline(0, color="0.3", lw=0.8)
    axes[1].set_ylabel("Out-of-sample R² of the next interval's mid change (%)")
    axes[1].set_title("Next interval (forecast, held-out day)", fontsize=10)
    for ax in axes:
        ax.set_xscale("log")
        ax.set_xticks(xs, [str(x) for x in xs])
        ax.set_xlabel("Interval length (seconds)")
        ax.legend(fontsize=8)
    fig.suptitle("Lab 03: explanatory vs predictive power by interval length (synthetic data)", fontweight="bold")
    fig.text(0.5, -0.03, "Left: pooled OLS on 3 simulated days. Right: fitted on days 1-2, evaluated on day 3. "
             "Note the different y-scales.", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "r2-by-horizon")

    # ---------------------------------------------------------------- results
    best = max(INTERVALS_S, key=lambda dt: predictive[dt]["all three"])
    t10 = [t for t in taker if t["interval_s"] == MAIN_INTERVAL]
    results = {
        "n_days": len(seeds), "seconds_per_day": n_seconds, "main_interval_s": MAIN_INTERVAL,
        "r2_contemporaneous_10s_ofi": c10["r2_ofi"], "r2_contemporaneous_10s_trade_imbalance": c10["r2_trade_imb"],
        "r2_contemporaneous_10s_both": c10["r2_both"],
        "beta_ofi_10s_ticks_per_100_shares": c10["beta_ofi_ticks_per_100sh"],
        "beta_trade_imbalance_10s_ticks_per_100_shares": c10["beta_trade_imb_ticks_per_100sh"],
        "t_stats_joint_regression_10s": {"ofi": c10["t_ofi_joint"], "trade_imbalance": c10["t_trade_imb_joint"]},
        "cks_model_beta_ticks_per_100_shares": 100 / (2 * mean_depth), "avg_touch_depth_shares": mean_depth,
        "cks_loglog_depth_exponent_lambda": lam, "cks_loglog_lambda_se": lam_se, "cks_c_hat": c_hat,
        "n_half_hour_subsamples": len(hh),
        "beta_vs_book_thickness": books,
        "r2_contemporaneous_by_interval": {f"{dt}s": {k: contemp[dt][k] for k in ("r2_ofi", "r2_trade_imb", "r2_both")} for dt in INTERVALS_S},
        "oos_r2_next_interval_by_interval": {f"{dt}s": {k: v for k, v in predictive[dt].items() if not k.startswith("_")} for dt in INTERVALS_S},
        "oos_r2_next_interval_10s_ofi": predictive[MAIN_INTERVAL]["OFI"],
        "oos_r2_next_interval_10s_all_three": predictive[MAIN_INTERVAL]["all three"],
        "best_forecast_interval_s": best, "best_oos_r2_all_three": predictive[best]["all three"],
        "taker_strategy": taker,
        "taker_10s_all_signals_net_round_trip_ticks": t10[0]["net_round_trip_ticks"],
        "taker_10s_all_signals_gross_ticks": t10[0]["gross_ticks"],
    }
    utils.write_results(ctx, results)
    print(f"\nSummary: at {MAIN_INTERVAL} s, OFI explains {c10['r2_ofi']:.0%} of same-interval mid changes and its beta is "
          f"{c10['beta_ofi_ticks_per_100sh'] / (100 / (2 * mean_depth)):.2f}x the CKS value 1/(2 x depth); depth exponent "
          f"{lam:.2f} (CKS: 1). As a forecast of the NEXT interval it explains {predictive[MAIN_INTERVAL]['OFI']:.1%} "
          f"(best: {predictive[best]['all three']:.1%} at {best} s, all three signals), and a taker trading it loses "
          f"{-t10[0]['net_round_trip_ticks']:.2f} ticks per round trip.")


if __name__ == "__main__":
    main()
