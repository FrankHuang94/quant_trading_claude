"""Lab 12: alpha combination and purged cross-validation.

What it demonstrates
  * Combining 14 signals into one forecast of the 5-day residual return: the three planted
    alphas (known ICs), a noisier near-duplicate of alpha_fast (correlation ~0.85, as when two
    researchers build similar reversal signals) and 10 pure-noise signals. Combiners:
    (i) equal weight, (ii) IC-weighted, (iii) ridge regression, (iv) gradient-boosted trees
    (LightGBM if installed, else scikit-learn HistGradientBoostingRegressor).
  * Three ways to estimate out-of-sample (OOS) skill: (a) naive shuffled K-fold over
    (date, stock) rows, (b) walk-forward (expanding window, purged), (c) purged K-fold with an
    embargo (Lopez de Prado 2018, ch. 7). The target is a 5-day forward return sampled daily,
    so neighboring labels share 4 of 5 days: shuffled K-fold puts near-copies of every test
    label in the training set.
  * Findings to look for: shuffled K-fold flatters the flexible model (GBDT) and ranks it
    first; walk-forward and purged K-fold agree with each other and show it is the worst of the
    fitted combiners. Linear combiners barely leak. IC weighting double-counts the duplicate.
    All are compared with an "oracle" combination that uses the planted ICs.

Supports: docs/03-algorithms/b-forecasting-models/alpha-combination-and-ensembling.md (F5),
          docs/03-algorithms/c-validation-and-backtesting/time-series-cross-validation.md (V1),
          docs/03-algorithms/b-forecasting-models/linear-models-and-regularization.md,
          docs/03-algorithms/b-forecasting-models/tree-ensembles.md

Run: python labs/12-alpha-combination-purged-cv/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import simulate, utils  # noqa: E402

try:                                         # optional dependency
    import lightgbm as lgb
except ImportError:                          # pragma: no cover - exercised when lightgbm is absent
    lgb = None
    from sklearn.ensemble import HistGradientBoostingRegressor
    from threadpoolctl import threadpool_limits   # installed with scikit-learn

C_BLUE, C_ORANGE, C_AQUA, C_GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"
INK, INK2 = "#0b0b0b", "#52514e"


# =====================================================================================
# === CORE ALGORITHM ===
# Data layout: one row per (date, stock). X: rows x K signals (z-scored per date), y: target,
# dates: integer date index of each row. Label of date t = return over t+1..t+horizon.
# =====================================================================================

def purged_kfold_splits(n_dates, n_folds=5, horizon=5, embargo=10):
    """Purged K-fold with embargo (Lopez de Prado 2018, ch. 7) over time-ordered dates.

    Yields (train_dates, test_dates). Each test fold is a contiguous block of dates. A training
    date t is PURGED if its label window t+1..t+horizon overlaps any test label window, and the
    `embargo` dates after the block are also dropped (serial correlation leaks backwards).
    Training dates after the test block are kept: the sample is assumed stationary.
    """
    dates = np.arange(n_dates)
    for test in np.array_split(dates, n_folds):
        first, last = test[0], test[-1]
        keep = (dates + horizon <= first) | (dates >= last + horizon + embargo)
        yield dates[keep], test


def walk_forward_splits(n_dates, n_folds=5, horizon=5):
    """Expanding-window walk-forward: the sample is cut into n_folds + 1 blocks; fold k trains on
    every date whose label is fully known before block k starts (t + horizon <= first test date)."""
    blocks = np.array_split(np.arange(n_dates), n_folds + 1)
    for test in blocks[1:]:
        yield np.arange(0, test[0] - horizon + 1), test


def rank_target(ret, dates):
    """Per-date percentile rank of the forward return, mapped to [-0.5, 0.5]: removes outliers,
    the day's average move and differences in volatility between stocks."""
    g = pd.Series(ret).groupby(dates)
    return ((g.rank() - 1) / (g.transform("count") - 1) - 0.5).to_numpy()


def combine_ic_weighted(X, ic):
    """Forecast = sum_k w_k * X[:, k] with w_k proportional to max(IC_k, 0), weights summing to 1.

    ic: each signal's mean daily IC measured on the TRAINING sample only. Ignores correlations
    between signals: two copies of the same alpha get double weight.
    """
    w = np.clip(np.asarray(ic, dtype=float), 0.0, None)
    w = w / w.sum() if w.sum() > 0 else np.full(len(w), 1.0 / len(w))
    return X @ w, w


def fit_ridge(X, y, lam):
    """Ridge regression without intercept (X z-scored and y ranked per date, so both have mean 0):
    beta = (X'X + lam I)^-1 X'y. Shrinkage spreads weight across correlated signals."""
    return np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ y)


# === END CORE ALGORITHM ===
# =====================================================================================


# ----------------------------------------------------------------------------- helpers
def mean_daily_ic(x, y, dates):
    """Mean over dates of the cross-sectional Pearson correlation of x and y (long format)."""
    codes = np.unique(dates, return_inverse=True)[1]
    cnt = np.bincount(codes)

    def demean(v):
        return v - (np.bincount(codes, v) / cnt)[codes]

    xc, yc = demean(x), demean(y)
    num = np.bincount(codes, xc * yc)
    den = np.sqrt(np.bincount(codes, xc * xc) * np.bincount(codes, yc * yc))
    with np.errstate(invalid="ignore", divide="ignore"):
        return float(np.nanmean(num / den))


def rank_rows(a):
    """Row-wise ranks of a T x N array (average ties)."""
    return pd.DataFrame(a).rank(axis=1).to_numpy()


def daily_rank_ic(pred, ret):
    """Spearman IC per date (row) between a T x N forecast and T x N realized returns."""
    p, r = rank_rows(pred), rank_rows(ret)
    p -= p.mean(axis=1, keepdims=True)
    r -= r.mean(axis=1, keepdims=True)
    return (p * r).sum(axis=1) / np.sqrt((p * p).sum(axis=1) * (r * r).sum(axis=1))


GBDT_PARAMS = dict(learning_rate=0.05, num_leaves=31, min_data_in_leaf=50, feature_fraction=0.8,
                   bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0)


def fit_gbdt(X, y, n_rounds, seed):
    """Gradient-boosted trees (LightGBM if available, else sklearn HistGradientBoosting).
    Deliberately loose regularization (31 leaves, 50 rows per leaf): typical of a first attempt."""
    if lgb is not None:
        params = dict(GBDT_PARAMS, objective="regression", verbose=-1, num_threads=2, seed=seed,
                      deterministic=True, force_col_wise=True)
        return lgb.train(params, lgb.Dataset(X, y), num_boost_round=n_rounds)
    model = HistGradientBoostingRegressor(
        learning_rate=GBDT_PARAMS["learning_rate"], max_iter=n_rounds,
        max_leaf_nodes=GBDT_PARAMS["num_leaves"], min_samples_leaf=GBDT_PARAMS["min_data_in_leaf"],
        l2_regularization=GBDT_PARAMS["lambda_l2"], early_stopping=False, random_state=seed)
    with threadpool_limits(limits=2):            # small data: more threads only add overhead
        return model.fit(X, y)


def long_short_pnl(forecast, ret1, cost_bps):
    """Daily dollar-neutral book with weights proportional to the demeaned forecast rank,
    scaled to $1 gross; P&L on the next day's return, cost = sum |trade| x cost_bps."""
    r = rank_rows(forecast)
    w = r - r.mean(axis=1, keepdims=True)
    w /= np.abs(w).sum(axis=1, keepdims=True)
    gross = (w * np.nan_to_num(ret1)).sum(axis=1)[:-1]
    traded = np.abs(np.diff(w, axis=0))
    cost = np.r_[0.0, (traded * cost_bps[None, :]).sum(axis=1)[:-1]] / 1e4
    return gross, gross - cost, float(traded.sum(axis=1).mean())


# ----------------------------------------------------------------------------- experiment
def main():
    t_start = time.time()
    ctx = utils.setup(__file__, "Lab 12: alpha combination with purged cross-validation")
    n_stocks, n_days = (60, 400) if ctx.smoke else (150, 1260)
    n_rounds = 40 if ctx.smoke else 150
    horizon, n_folds, embargo = 5, 5, 10
    ridge_lam_per_row = 0.1                  # lam = 0.1 x rows: ~10% shrinkage of unit-variance signals
    impact_bps = 5.0                         # stylized impact + fees on top of the half-spread
    rng = np.random.default_rng(ctx.seed)

    # ---- data: planted alphas + a near-duplicate + noise -------------------------------------
    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, seed=ctx.seed)
    sig = {k: v.to_numpy() for k, v in m.alphas.items()}
    dup = sig["alpha_fast"] + 0.6 * rng.standard_normal(sig["alpha_fast"].shape)
    sig["alpha_fast_v2"] = (dup - dup.mean(1, keepdims=True)) / dup.std(1, keepdims=True)
    sig.update({k: v.to_numpy() for k, v in simulate.noise_signals(m, 10, seed=ctx.seed + 1).items()})
    names = list(sig)
    T_all, N = len(m.dates), len(m.tickers)
    T = T_all - horizon                                   # dates with a complete 5-day label
    X3 = np.stack([sig[k][:T] for k in names], axis=-1)   # T x N x K
    K = X3.shape[2]
    fwd = m.forward_returns(horizon, specific=True).to_numpy()[:T]
    ret1 = m.forward_returns(1, specific=True).to_numpy()[:T]
    date_of_row = np.repeat(np.arange(T), N)
    X = X3.reshape(-1, K)
    y = rank_target(fwd.reshape(-1), date_of_row)
    print(f"\nSynthetic market: {N} stocks x {T_all} days; {K} signals ({', '.join(names[:4])} + 10 noise); "
          f"target = ranked {horizon}-day residual return; GBDT = {'LightGBM' if lgb else 'sklearn HistGB'}")

    # ---- the four combiners: fit on training dates/rows, predict test rows --------------------
    def fit_predict(method, tr_rows, te_rows):
        Xtr, ytr, Xte = X[tr_rows], y[tr_rows], X[te_rows]
        if method == "equal weight":
            return Xte.mean(axis=1), None
        if method == "IC-weighted":
            ic = [mean_daily_ic(Xtr[:, k], ytr, date_of_row[tr_rows]) for k in range(K)]
            return combine_ic_weighted(Xte, ic)
        if method == "ridge":
            beta = fit_ridge(Xtr, ytr, ridge_lam_per_row * len(ytr))
            return Xte @ beta, beta
        model = fit_gbdt(Xtr, ytr, n_rounds, ctx.seed)
        return model.predict(Xte), model

    def rows_of(dates_idx):
        return (dates_idx[:, None] * N + np.arange(N)[None, :]).reshape(-1)

    schemes = {
        "shuffled K-fold (naive)": [(np.setdiff1d(np.arange(T * N), f), f) for f in
                                    np.array_split(rng.permutation(T * N), n_folds)],
        "walk-forward (purged)": [(rows_of(a), rows_of(b)) for a, b in walk_forward_splits(T, n_folds, horizon)],
        "purged K-fold + embargo": [(rows_of(a), rows_of(b)) for a, b in
                                    purged_kfold_splits(T, n_folds, horizon, embargo)],
    }
    methods = ["equal weight", "IC-weighted", "ridge", "GBDT"]
    common = np.arange(np.array_split(np.arange(T), n_folds + 1)[1][0], T)   # walk-forward test dates
    oos_ic, preds, last_fit = {}, {}, {}
    for scheme, folds in schemes.items():
        for meth in methods:
            p = np.full(T * N, np.nan)
            for tr, te in folds:
                p[te], fitted = fit_predict(meth, tr, te)
            p = p.reshape(T, N)
            preds[(scheme, meth)] = p
            oos_ic[(scheme, meth)] = float(np.mean(daily_rank_ic(p[common], fwd[common])))
            if scheme.startswith("walk"):
                last_fit[meth] = (fitted, tr)
        print(f"  {scheme:<26}" + "  ".join(f"{mm} {oos_ic[(scheme, mm)]:.4f}" for mm in methods)
              + f"   ({time.time() - t_start:.0f} s)")

    # oracle: planted alphas weighted by their true 5-day IC (no noise, no duplicate)
    true_ic5 = {k: s.ic * sum(s.horizon_decay ** j for j in range(horizon)) / np.sqrt(horizon)
                for k, s in m.alpha_specs.items()}
    oracle = sum(true_ic5[k] * sig[k][:T] for k in m.alpha_specs)
    oracle_ic = float(np.mean(daily_rank_ic(oracle[common], fwd[common])))
    best_single = max(m.alpha_specs, key=lambda k: np.mean(daily_rank_ic(sig[k][:T][common], fwd[common])))
    best_single_ic = float(np.mean(daily_rank_ic(sig[best_single][:T][common], fwd[common])))

    # in-sample vs out-of-sample (last walk-forward fold)
    gbdt_model, tr_rows = last_fit["GBDT"]
    tr_dates = np.unique(date_of_row[tr_rows])
    ins = gbdt_model.predict(X[tr_rows]).reshape(len(tr_dates), N)
    gbdt_is_ic = float(np.mean(daily_rank_ic(ins, fwd[tr_dates])))
    ridge_beta, _ = last_fit["ridge"]
    ridge_is_ic = float(np.mean(daily_rank_ic((X[tr_rows] @ ridge_beta).reshape(len(tr_dates), N),
                                              fwd[tr_dates])))
    _, ic_w = combine_ic_weighted(X[:1], [mean_daily_ic(X[tr_rows][:, k], y[tr_rows], date_of_row[tr_rows])
                                          for k in range(K)])

    # ---- P&L of the OOS forecasts on the walk-forward test period ----------------------------
    cost_bps = m.spread_bps.to_numpy() / 2.0 + impact_bps
    pnl = {}
    for key in [("walk-forward (purged)", mm) for mm in methods] + [("shuffled K-fold (naive)", "GBDT")]:
        g, n_, to = long_short_pnl(preds[key][common], ret1[common], cost_bps)
        pnl[key] = dict(gross=g, net=n_, turnover=to, sr_gross=utils.annualized_sharpe(g),
                        sr_net=utils.annualized_sharpe(n_))

    # ---- report ---------------------------------------------------------------------------------
    print(f"\nMean daily OOS rank IC vs the {horizon}-day residual return, on the same {len(common)} test dates")
    tab = pd.DataFrame({s: [oos_ic[(s, mm)] for mm in methods] for s in schemes}, index=methods)
    print(tab.round(4).to_string())
    print(f"  oracle (planted ICs as weights) {oracle_ic:.4f};  best single signal ({best_single}) {best_single_ic:.4f}")
    print(f"  GBDT in-sample IC {gbdt_is_ic:.4f} vs walk-forward OOS {oos_ic[('walk-forward (purged)', 'GBDT')]:.4f};"
          f"  ridge in-sample {ridge_is_ic:.4f} vs OOS {oos_ic[('walk-forward (purged)', 'ridge')]:.4f}")
    print("  last-fold weights: " + ", ".join(f"{n} IC-w {w:.2f}/ridge {b:+.3f}"
                                              for n, w, b in zip(names[:4], ic_w[:4], ridge_beta[:4] / np.abs(ridge_beta).sum())))
    print(f"  noise signals' share of |weight|: IC-weighted {ic_w[4:].sum():.2f}, "
          f"ridge {np.abs(ridge_beta[4:]).sum() / np.abs(ridge_beta).sum():.2f}")
    print("\nOOS long-short book on residual returns ($1 gross, daily, half-spread + 5 bps cost)")
    for (s, mm), d in pnl.items():
        print(f"  {mm:<13} {s:<26} Sharpe gross {d['sr_gross']:5.1f}  net {d['sr_net']:5.1f}  "
              f"turnover {100 * d['turnover']:.0f}%/day")

    # ---- plot 1: OOS IC by method x CV scheme --------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [C_GRAY, C_BLUE, C_ORANGE]
    width = 0.26
    for j, (s, c) in enumerate(zip(schemes, colors)):
        vals = [100 * oos_ic[(s, mm)] for mm in methods]
        bars = ax.bar(np.arange(len(methods)) + (j - 1) * width, vals, width * 0.92, color=c, label=s)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.12, f"{v:.1f}", ha="center", va="bottom", fontsize=8,
                    color=INK2, bbox=dict(boxstyle="square,pad=0.05", fc="white", ec="none"))
    ax.axhline(100 * oracle_ic, color=INK, ls="--", lw=1.2, label=f"oracle weights (planted ICs): {100 * oracle_ic:.1f}%")
    ax.set_xticks(range(len(methods)), methods)
    ax.set_ylabel(f"mean daily OOS rank IC (%), {horizon}-day residual return")
    ax.set_title(f"Shuffled K-fold flatters the flexible model; purged schemes do not\n"
                 f"(synthetic data: 3 planted alphas + 1 duplicate + 10 noise, {N} stocks x {T_all} days)")
    ax.legend(fontsize=8.5, loc="upper left")
    ax.set_ylim(0, 1.25 * max(100 * max(oos_ic.values()), 100 * oracle_ic))
    utils.save_fig(ctx, fig, "oos-ic-by-cv")

    # ---- plot 2: cumulative OOS P&L --------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    dates = m.dates[common][1:]
    for mm, c in zip(methods, [C_GRAY, C_BLUE, C_AQUA, C_ORANGE]):
        d = pnl[("walk-forward (purged)", mm)]
        ax.plot(dates, 100 * np.cumsum(d["gross"]), color=c, lw=2,
                label=f"{mm}, walk-forward (Sharpe {d['sr_gross']:.1f} gross, {d['sr_net']:.1f} net)")
    d = pnl[("shuffled K-fold (naive)", "GBDT")]
    ax.plot(dates, 100 * np.cumsum(d["gross"]), color=C_ORANGE, lw=2, ls="--",
            label=f"GBDT, shuffled K-fold: what naive CV promised (Sharpe {d['sr_gross']:.1f} gross)")
    ax.set_ylabel("cumulative P&L, % of gross book (before costs)")
    ax.set_xlabel("date (out-of-sample period)")
    ax.set_title("Out-of-sample P&L of each combiner (synthetic data)\n"
                 "daily dollar-neutral book on residual returns; net = after half-spread + 5 bps (stylized)",
                 fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    utils.save_fig(ctx, fig, "oos-pnl")

    res = {
        "n_stocks": N, "n_days": T_all, "n_signals": K, "label_horizon_days": horizon,
        "gbdt_backend": "lightgbm" if lgb else "sklearn.HistGradientBoostingRegressor",
        "oos_rank_ic": {f"{s} | {mm}": v for (s, mm), v in oos_ic.items()},
        "oracle_rank_ic": oracle_ic, "best_single_signal_rank_ic": best_single_ic,
        "gbdt_ic_shuffled_minus_walk_forward": oos_ic[("shuffled K-fold (naive)", "GBDT")]
        - oos_ic[("walk-forward (purged)", "GBDT")],
        "ridge_ic_shuffled_minus_walk_forward": oos_ic[("shuffled K-fold (naive)", "ridge")]
        - oos_ic[("walk-forward (purged)", "ridge")],
        "gbdt_in_sample_ic_last_fold": gbdt_is_ic, "ridge_in_sample_ic_last_fold": ridge_is_ic,
        "ic_weight_alpha_fast_plus_duplicate": float(ic_w[0] + ic_w[3]),
        "sharpe_gross_walk_forward": {mm: pnl[("walk-forward (purged)", mm)]["sr_gross"] for mm in methods},
        "sharpe_net_walk_forward": {mm: pnl[("walk-forward (purged)", mm)]["sr_net"] for mm in methods},
        "sharpe_gross_gbdt_shuffled_cv": pnl[("shuffled K-fold (naive)", "GBDT")]["sr_gross"],
        "turnover_per_day_ridge": pnl[("walk-forward (purged)", "ridge")]["turnover"],
    }
    utils.write_results(ctx, res)
    print(f"\nDone in {time.time() - t_start:.1f} s.")


if __name__ == "__main__":
    main()
