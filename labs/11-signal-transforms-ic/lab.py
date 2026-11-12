"""Lab 11: signal transforms and information-coefficient (IC) diagnostics.

What it demonstrates
  * Transforms on a realistic "dirty" research signal: the planted alpha_med contaminated with a
    beta tilt, a slowly drifting sector tilt and rare huge outliers (bad prints, tiny
    denominators), in arbitrary raw units. Steps: raw, z-score (clipped at +-3), winsorize then
    z-score, cross-sectional rank, sector-neutralize, beta + sector neutralize (regression).
    Each step is scored by Pearson IC, rank IC and IC t-stat against next-day total and
    residual (specific) returns.
  * Evaluation of the three planted alphas (known IC, half-life and horizon decay): measured
    IC vs the planted truth, IC decay by horizon (1-20 days), cumulative h-day IC, half-life
    recovered from the decay curve, signal autocorrelation (turnover), quintile spread returns
    gross and net of a stylized cost.
  * Pitfalls: (1) a raw signal's IC against total returns is mostly a disguised beta/sector
    bet, with an IC volatility several times the residual one; (2) z-scoring without
    winsorizing first leaves outliers in charge; (3) overlapping multi-day ICs inflate a naive
    t-stat (Newey-West fixes it); (4) pure-noise signals clear |t| > 2 at the 5% rate;
    (5) the fastest alpha has the highest IC and loses the largest share of its spread to costs.

Supports: docs/03-algorithms/a-data-and-signals/signal-transforms.md (D3),
          docs/03-algorithms/a-data-and-signals/evaluating-signals.md (D4),
          docs/02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md

Run: python labs/11-signal-transforms-ic/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import curve_fit  # noqa: E402
from scipy.signal import lfilter  # noqa: E402

from common import simulate, utils  # noqa: E402

# categorical slots (validated, CVD-safe; same order as the other labs) + neutral gray
C_BLUE, C_ORANGE, C_AQUA, C_GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"
INK2 = "#52514e"
ALPHA_COLORS = {"alpha_fast": C_BLUE, "alpha_med": C_ORANGE, "alpha_slow": C_AQUA}


# =====================================================================================
# === CORE ALGORITHM ===
# Conventions: a signal is a dates x stocks table known at the CLOSE of date t; fwd_ret is the
# return realized after t (days t+1..t+h), aligned at t. One row = one cross-section.
# =====================================================================================

def zscore(x, clip=3.0):
    """Cross-sectional z-score along the last axis (one row = one date), clipped at +-clip sd.

    x: N-vector for one date or a T x N array. NaNs stay NaN and are ignored in the mean/sd.
    Clipping AFTER z-scoring does not stop one huge outlier from inflating the sd and squashing
    everyone else: winsorize first (see winsorize below) when the raw data has bad prints.
    """
    x = np.asarray(x, dtype=float)
    mu = np.nanmean(x, axis=-1, keepdims=True)
    sd = np.nanstd(x, axis=-1, keepdims=True)
    z = (x - mu) / np.where(sd > 0, sd, np.nan)
    return np.clip(z, -clip, clip) if clip else z


def neutralize(signal, exposures):
    """Residual of a least-squares regression of the signal on exposures, one regression per date.

    signal: N-vector (one date) or T x N array (the same exposures on every date; in production
            exposures change daily, so call this once per date).
    exposures: N x K, e.g. [beta, sector 0/1 dummies]; include a column of ones unless the
            dummies already span the intercept. No NaNs: drop or fill missing names first.
    Returns the part of the signal orthogonal to every exposure column (zero beta tilt, zero
    mean within each sector).
    """
    E = np.asarray(exposures, dtype=float)
    S = np.atleast_2d(np.asarray(signal, dtype=float))     # T x N
    coef, *_ = np.linalg.lstsq(E, S.T, rcond=None)         # K x T: the factor "tilts" of each date
    return (S - (E @ coef).T).reshape(np.shape(signal))


def ic_series(signal, fwd_ret, method="pearson"):
    """Daily information coefficient: cross-sectional correlation of signal(t) with fwd_ret(t).

    signal, fwd_ret: T x N DataFrames (dates x stocks), fwd_ret aligned at t.
    method: "pearson" (IC) or "spearman" (rank IC: correlation of the ranks).
    Names with a NaN on either side are dropped; dates with < 3 names give NaN.
    """
    s, r = signal.align(fwd_ret, join="inner")
    s, r = s.where(r.notna()), r.where(s.notna())          # same names on both sides
    if method == "spearman":
        s, r = s.rank(axis=1), r.rank(axis=1)
    s = s.sub(s.mean(axis=1), axis=0)
    r = r.sub(r.mean(axis=1), axis=0)
    ic = (s * r).sum(axis=1) / np.sqrt((s * s).sum(axis=1) * (r * r).sum(axis=1))
    return ic.where(s.notna().sum(axis=1) >= 3).rename("ic")


# === END CORE ALGORITHM ===
# =====================================================================================


# ----------------------------------------------------------------------------- helpers
def winsorize(x, pct=0.01):
    """Clip each row at its own pct and 1-pct quantiles (per-date winsorization)."""
    x = np.asarray(x, dtype=float)
    lo = np.nanquantile(x, pct, axis=-1, keepdims=True)
    hi = np.nanquantile(x, 1 - pct, axis=-1, keepdims=True)
    return np.clip(x, lo, hi)


def rank_score(x):
    """Per-row rank mapped to [-0.5, 0.5] (uniform scores; NaNs stay NaN)."""
    r = pd.DataFrame(np.atleast_2d(x)).rank(axis=1)
    n = r.notna().sum(axis=1).to_numpy()[:, None]
    return ((r.to_numpy() - 1) / np.maximum(n - 1, 1) - 0.5).reshape(np.shape(x))


def ic_tstat(ic, lags=0):
    """t-stat of the mean IC; lags > 0 uses a Newey-West (Bartlett) standard error, needed when
    the forward-return windows overlap (h-day returns sampled daily: use lags = h - 1)."""
    x = pd.Series(ic).dropna().to_numpy()
    n, e = x.size, x - x.mean()
    var = e @ e / n
    for k in range(1, lags + 1):
        var += 2 * (1 - k / (lags + 1)) * (e[k:] @ e[:-k]) / n
    return float(x.mean() / np.sqrt(var / n))


def quintile_book(signal, n_q=5):
    """Quintile labels (1 = lowest) and long-short weights: +1/n on the top, -1/n on the bottom."""
    pct = pd.DataFrame(signal).rank(axis=1, pct=True).to_numpy()
    q = np.clip(np.ceil(pct * n_q), 1, n_q)
    top, bot = (q == n_q).astype(float), (q == 1).astype(float)
    w = top / top.sum(axis=1, keepdims=True) - bot / bot.sum(axis=1, keepdims=True)
    return q, w


def make_raw_signal(m, base="alpha_med", seed=0, beta_tilt=0.6, sector_sd=0.6, sector_half_life=120.0,
                    outlier_prob=0.01, outlier_scale=15.0):
    """A 'dirty' research signal in arbitrary raw units: planted alpha + a static beta tilt + a
    slowly drifting sector tilt (AR(1) per sector) + rare huge Student-t outliers. Stylized."""
    rng = np.random.default_rng(seed)
    a = m.alphas[base].to_numpy()
    T, N = a.shape
    beta_z = zscore(m.beta.to_numpy(), clip=None)
    codes, uniq = pd.factorize(m.sector)
    phi = 0.5 ** (1.0 / sector_half_life)
    e = rng.standard_normal((T, len(uniq)))
    e[1:] *= np.sqrt(1 - phi ** 2)
    sector_level = sector_sd * lfilter([1.0], [1.0, -phi], e, axis=0)
    raw = a + beta_tilt * beta_z[None, :] + sector_level[:, codes]
    out = rng.random((T, N)) < outlier_prob
    raw[out] += outlier_scale * rng.standard_t(3, out.sum())
    return pd.DataFrame(1.0 + 0.4 * raw, index=m.dates, columns=m.tickers)   # arbitrary units


def row_corr(x, v):
    """Mean over dates of the cross-sectional correlation between rows of x and a fixed vector v."""
    x = np.asarray(x, float)
    xc = x - x.mean(axis=1, keepdims=True)
    vc = v - v.mean()
    return float(np.nanmean(xc @ vc / np.sqrt((xc * xc).sum(axis=1) * (vc @ vc))))


def fit_decay(lags, ics):
    """Least-squares fit IC_k = a * d**k; returns (a, d, implied half-life in days)."""
    (a, d), _ = curve_fit(lambda k, a, d: a * d ** k, lags, ics, p0=(ics[0], 0.9),
                          bounds=([-1, 0.01], [1, 0.9999]))
    return a, d, float(np.log(0.5) / np.log(d))


def long_short_stats(signal, fwd1, cost_bps):
    """Daily quintile long-short (top minus bottom) P&L, turnover and cost on the next day's return.

    The book is $1 long the top quintile and $1 short the bottom, equal-weighted, rebalanced daily.
    cost_bps: per-stock cost of trading $1 (one way), bps.
    """
    q, w = quintile_book(signal)
    r = np.nan_to_num(np.asarray(fwd1, float))
    gross = (w * r).sum(axis=1)[:-1]                       # last row has no forward return
    traded = np.abs(np.diff(w, axis=0, prepend=0.0))       # $ traded per stock per day
    traded[0] = 0.0                                        # ignore the initial build
    cost = (traded * cost_bps[None, :]).sum(axis=1)[:-1] / 1e4
    net = gross - cost
    return dict(q=q, gross=gross, net=net,
                turnover=float(traded[1:].sum(axis=1).mean() / 2.0),   # share of the $2 gross per day
                gross_bps=1e4 * gross.mean(), cost_bps=1e4 * cost.mean(), net_bps=1e4 * net.mean(),
                sharpe_gross=utils.annualized_sharpe(gross), sharpe_net=utils.annualized_sharpe(net))


# ----------------------------------------------------------------------------- experiment
def main():
    t_start = time.time()
    ctx = utils.setup(__file__, "Lab 11: signal transforms and IC diagnostics")
    n_stocks, n_days = (200, 500) if ctx.smoke else (500, 1260)
    n_noise = 6 if ctx.smoke else 20
    max_h = 10 if ctx.smoke else 20
    impact_bps = 5.0                       # stylized impact + fees per $ traded, on top of half-spread

    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, seed=ctx.seed)
    fwd1_total = m.forward_returns(1)
    fwd1_spec = m.forward_returns(1, specific=True)
    T, N = fwd1_total.shape
    print(f"\nSynthetic market: {N} stocks x {T} days; planted alphas "
          + ", ".join(f"{k} (IC {s.ic}, half-life {s.half_life:g} d)" for k, s in m.alpha_specs.items()))

    # ---- (A) transforms on a dirty signal ------------------------------------------------
    raw = make_raw_signal(m, seed=ctx.seed + 1)
    sector_dummies = m.exposures[[c for c in m.exposures.columns if c.startswith("sec_")]].to_numpy()
    beta = m.exposures["market"].to_numpy()
    wz = zscore(winsorize(raw.to_numpy(), 0.01))
    steps = {
        "raw": raw.to_numpy(),
        "z-score (clip 3)": zscore(raw.to_numpy()),
        "winsorize 1% + z": wz,
        "rank": rank_score(raw.to_numpy()),
        "+ sector-neutral": neutralize(wz, sector_dummies),
        "+ beta & sector-neutral": neutralize(wz, np.column_stack([beta, sector_dummies])),
        "clean alpha_med (truth)": m.alphas["alpha_med"].to_numpy(),
    }
    rows = {}
    for name, x in steps.items():
        sig = pd.DataFrame(x, index=m.dates, columns=m.tickers)
        ic_tot = ic_series(sig, fwd1_total)
        ic_sp = ic_series(sig, fwd1_spec)
        rows[name] = dict(
            ic_resid=ic_sp.mean(), ic_total=ic_tot.mean(),
            rank_ic_total=ic_series(sig, fwd1_total, "spearman").mean(),
            ic_sd_total=ic_tot.std(), t_total=ic_tstat(ic_tot), t_resid=ic_tstat(ic_sp),
            corr_beta=row_corr(x, beta))
    tbl = pd.DataFrame(rows).T
    print("\n[A] Transforms of a dirty signal (alpha_med + beta tilt + sector tilt + outliers)")
    print("    IC = mean daily cross-sectional correlation with the next-day return")
    with pd.option_context("display.float_format", "{:8.4f}".format, "display.width", 160, "display.max_columns", 20):
        print(tbl.rename(columns={"ic_resid": "IC resid", "ic_total": "IC total",
                                  "rank_ic_total": "rankIC tot", "ic_sd_total": "IC sd tot",
                                  "t_total": "t total", "t_resid": "t resid", "corr_beta": "corr beta"}))

    # ---- (B) planted alphas: IC vs truth, decay by horizon, half-life ----------------------
    lags = np.arange(max_h)
    decay, cum, truth_lag, truth_cum, fits, ic_se = {}, {}, {}, {}, {}, {}
    for name, spec in m.alpha_specs.items():
        sig = m.alphas[name]
        lag_ic = []
        for k in lags:                                     # IC with the return of day t+1+k
            ic_k = ic_series(sig, m.specific_returns.shift(-(1 + k)))
            lag_ic.append(ic_k.mean())
            if k == 0:
                ic_se[name] = ic_k.std() / np.sqrt(ic_k.notna().sum())
        decay[name] = np.array(lag_ic)
        truth_lag[name] = spec.ic * spec.horizon_decay ** lags
        cum[name] = np.array([ic_series(sig, m.forward_returns(h, specific=True)).mean()
                              for h in lags + 1])
        truth_cum[name] = np.cumsum(truth_lag[name]) / np.sqrt(lags + 1)   # sum of lag ICs / sqrt(h)
        fits[name] = fit_decay(lags, decay[name])
    print("\n[B] Planted alphas: measured vs true")
    print(f"    {'alpha':<11}{'IC true':>8}{'IC meas':>9}{'(2 se)':>8}{'rankIC':>8}{'HL true':>8}"
          f"{'HL fit':>8}{'autocorr':>9}{'phi true':>9}{f'IC {max_h}d cum':>12}")
    autocorr = {}
    for name, spec in m.alpha_specs.items():
        sig = m.alphas[name]
        autocorr[name] = ic_series(sig, sig.shift(1)).mean()    # day-over-day cross-sectional corr
        ric = ic_series(sig, fwd1_spec, "spearman").mean()
        print(f"    {name:<11}{spec.ic:8.3f}{decay[name][0]:9.4f}{2 * ic_se[name]:8.4f}{ric:8.4f}"
              f"{spec.half_life:8.0f}{fits[name][2]:8.1f}{autocorr[name]:9.3f}"
              f"{0.5 ** (1 / spec.half_life):9.3f}{cum[name][-1]:12.4f}")

    # overlapping horizons: naive vs Newey-West t-stat of the 5-day IC
    ic5 = ic_series(m.alphas["alpha_med"], m.forward_returns(5, specific=True))
    t5_naive, t5_nw = ic_tstat(ic5), ic_tstat(ic5, lags=4)
    print(f"\n    alpha_med 5-day IC {ic5.mean():.4f}: naive t = {t5_naive:.1f}, Newey-West(4) t = {t5_nw:.1f}")
    ic1_sd = ic_series(m.alphas["alpha_med"], fwd1_spec).std()
    print(f"    daily IC std {ic1_sd:.4f} vs 1/sqrt(N) = {1 / np.sqrt(N):.4f} (IC noise is mostly breadth)")

    # noise signals: how often does pure noise look significant?
    noise_t = {}
    for name, sig in simulate.iter_noise_signals(m, n_noise, seed=ctx.seed + 100):
        noise_t[name] = ic_tstat(ic_series(sig, fwd1_spec))
        if name.endswith("000"):
            noise0 = sig
    nt = np.array(list(noise_t.values()))
    print(f"    {n_noise} noise signals: IC t-stats mean {nt.mean():+.2f}, sd {nt.std():.2f}, "
          f"max |t| {np.abs(nt).max():.2f}, {int((np.abs(nt) > 2).sum())} with |t| > 2")

    # ---- (C) quintile spreads, turnover and costs --------------------------------------------
    cost_bps = (m.spread_bps.to_numpy() / 2.0 + impact_bps)        # half-spread + stylized impact
    ls = {name: long_short_stats(m.alphas[name].to_numpy(), fwd1_spec, cost_bps) for name in m.alpha_specs}
    ls["noise_000"] = long_short_stats(noise0.to_numpy(), fwd1_spec, cost_bps)
    qret = {}
    r1 = fwd1_spec.to_numpy()
    for name, d in ls.items():
        q = d["q"][:-1]
        qret[name] = [1e4 * np.nanmean(np.where(q == k, r1[:-1], np.nan)) for k in range(1, 6)]
    print("\n[C] Quintile long-short on next-day residual returns ($1 long top, $1 short bottom, daily)")
    print(f"    cost per $ traded = half-spread ({m.spread_bps.mean() / 2:.1f} bps avg) + {impact_bps:g} bps stylized impact")
    print(f"    {'signal':<11}{'Q1':>7}{'Q5':>7}{'gross':>8}{'turnover':>9}{'cost':>7}{'net':>7}"
          f"{'SR gross':>9}{'SR net':>8}   (bps/day; turnover = share of gross traded per day)")
    for name, d in ls.items():
        print(f"    {name:<11}{qret[name][0]:7.1f}{qret[name][4]:7.1f}{d['gross_bps']:8.1f}"
              f"{100 * d['turnover']:8.0f}%{d['cost_bps']:7.1f}{d['net_bps']:7.1f}"
              f"{d['sharpe_gross']:9.1f}{d['sharpe_net']:8.1f}")

    # ---- plot 1: IC decay curves -------------------------------------------------------------
    h = lags + 1
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
    for name in m.alpha_specs:
        c = ALPHA_COLORS.get(name, C_GRAY)
        hl = m.alpha_specs[name].half_life
        ax1.plot(h, 100 * truth_lag[name], color=c, lw=2, label=f"{name} (half-life {hl:g} d): planted truth")
        ax1.errorbar(h, 100 * decay[name], yerr=200 * ic_se[name], fmt="o", ms=5, color=c, mfc="white",
                     mew=1.5, elinewidth=1, label=f"{name}: measured (+-2 se)")
        ax2.plot(h, 100 * truth_cum[name], color=c, lw=2)
        ax2.plot(h, 100 * cum[name], "o", ms=5, color=c, mfc="white", mew=1.5)
    ax1.axhline(0, color=INK2, lw=0.8)
    for ax in (ax1, ax2):
        ax.set_xticks([1, 5, 10, 15, 20] if max_h >= 20 else list(range(1, max_h + 1)))
    ax1.set_xlabel("horizon h (days): IC with the return of day t+h")
    ax1.set_ylabel("mean daily IC (%)")
    ax1.set_title("Marginal IC decay")
    ax1.legend(fontsize=7.5, loc="upper right")
    ax2.set_xlabel("horizon h (days): IC with the cumulative return t+1..t+h")
    ax2.set_ylabel("mean daily IC (%)")
    ax2.set_title("Cumulative h-day IC (lines: theory, dots: measured)")
    ax2.set_ylim(bottom=0)
    fig.suptitle(f"IC decay by horizon: measured vs planted truth (synthetic data, {N} stocks x {T} days)",
                 fontweight="bold")
    fig.tight_layout()
    utils.save_fig(ctx, fig, "ic-decay")

    # ---- plot 2: transforms + quintile returns ----------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.15, 1]})
    names = list(tbl.index)
    y = np.arange(len(names))[::-1]
    ax1.barh(y + 0.2, tbl["t_total"], height=0.38, color=C_BLUE, label="vs next-day TOTAL return")
    ax1.barh(y - 0.2, tbl["t_resid"], height=0.38, color=C_ORANGE, label="vs next-day RESIDUAL return")
    for yi, row in zip(y, tbl.itertuples()):
        ax1.text(max(row.t_total, 0) + 0.3, yi + 0.2, f"IC {100 * row.ic_total:.1f}%", va="center",
                 fontsize=7.5, color=INK2)
        ax1.text(max(row.t_resid, 0) + 0.3, yi - 0.2, f"IC {100 * row.ic_resid:.1f}%", va="center",
                 fontsize=7.5, color=INK2)
    ax1.set_yticks(y, names)
    ax1.set_xlim(0, 1.18 * tbl[["t_total", "t_resid"]].to_numpy().max())
    ax1.set_xlabel("IC t-stat (mean IC / its standard error)")
    ax1.set_title("Transforms of a dirty alpha_med")
    ax1.legend(fontsize=8, loc="upper right")
    ax1.grid(axis="y", alpha=0)
    sig_names = list(qret)
    width = 0.8 / len(sig_names)
    for j, name in enumerate(sig_names):
        ax2.bar(np.arange(1, 6) + (j - (len(sig_names) - 1) / 2) * width, qret[name], width=width * 0.92,
                color=ALPHA_COLORS.get(name, C_GRAY), label=f"{name}: Q5-Q1 {ls[name]['gross_bps']:.1f} bps/d gross, "
                f"{ls[name]['net_bps']:.1f} net")
    ax2.axhline(0, color=INK2, lw=0.8)
    ax2.set_xticks(range(1, 6), ["Q1\n(low)", "Q2", "Q3", "Q4", "Q5\n(high)"])
    ax2.set_ylabel("mean next-day residual return (bps)")
    ax2.set_title("Quintile returns of the planted alphas")
    ax2.legend(fontsize=7.5, loc="upper left")
    fig.suptitle("Transforms and quintile spreads (synthetic data; costs = half-spread + 5 bps, stylized)",
                 fontweight="bold")
    fig.tight_layout()
    utils.save_fig(ctx, fig, "transforms-quintiles")

    # ---- results ----------------------------------------------------------------------------
    res = {
        "n_stocks": N, "n_days": T,
        "raw_pearson_ic_total": tbl.loc["raw", "ic_total"],
        "raw_rank_ic_total": tbl.loc["raw", "rank_ic_total"],
        "raw_ic_tstat_total": tbl.loc["raw", "t_total"],
        "zscore_only_ic_total": tbl.loc["z-score (clip 3)", "ic_total"],
        "winsor_z_ic_total": tbl.loc["winsorize 1% + z", "ic_total"],
        "winsor_z_ic_tstat_total": tbl.loc["winsorize 1% + z", "t_total"],
        "neutralized_ic_total": tbl.loc["+ beta & sector-neutral", "ic_total"],
        "neutralized_ic_tstat_total": tbl.loc["+ beta & sector-neutral", "t_total"],
        "neutralized_ic_resid": tbl.loc["+ beta & sector-neutral", "ic_resid"],
        "raw_ic_sd_total": tbl.loc["raw", "ic_sd_total"],
        "neutralized_ic_sd_total": tbl.loc["+ beta & sector-neutral", "ic_sd_total"],
        "raw_corr_with_beta": tbl.loc["raw", "corr_beta"],
        "measured_ic_1d": {k: v[0] for k, v in decay.items()},
        "true_ic_1d": {k: s.ic for k, s in m.alpha_specs.items()},
        "fitted_half_life_days": {k: v[2] for k, v in fits.items()},
        "true_half_life_days": {k: s.half_life for k, s in m.alpha_specs.items()},
        f"cumulative_ic_{max_h}d": {k: v[-1] for k, v in cum.items()},
        "signal_autocorr_1d": autocorr,
        "alpha_med_ic5d_tstat_naive": t5_naive, "alpha_med_ic5d_tstat_newey_west": t5_nw,
        "daily_ic_sd_alpha_med": ic1_sd, "one_over_sqrt_n": 1 / np.sqrt(N),
        "noise_signals_abs_t_gt_2": int((np.abs(nt) > 2).sum()), "noise_signals_n": n_noise,
        "q5_minus_q1_gross_bps_per_day": {k: v["gross_bps"] for k, v in ls.items()},
        "q5_minus_q1_net_bps_per_day": {k: v["net_bps"] for k, v in ls.items()},
        "turnover_per_day": {k: v["turnover"] for k, v in ls.items()},
        "sharpe_gross": {k: v["sharpe_gross"] for k, v in ls.items()},
        "sharpe_net": {k: v["sharpe_net"] for k, v in ls.items()},
    }
    utils.write_results(ctx, res)
    print(f"\nDone in {time.time() - t_start:.1f} s.")


if __name__ == "__main__":
    main()
