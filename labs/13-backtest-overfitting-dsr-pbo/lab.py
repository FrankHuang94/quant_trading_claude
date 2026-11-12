"""Lab 13: backtest overfitting, the Deflated Sharpe Ratio and the Probability of Backtest Overfitting.

What it demonstrates
  * Selection bias: 500 strategies built on pure-noise signals (true Sharpe exactly 0) are
    backtested on a synthetic 100-stock market next to one strategy built on a genuinely
    planted alpha (true gross Sharpe ~2). Pick the best of the 500 on the first half of the
    sample (in-sample, IS) and watch its second-half (out-of-sample, OOS) Sharpe collapse to
    noise; across all 500 the IS and OOS Sharpes are uncorrelated.
  * Expected maximum Sharpe vs number of trials: with N independent zero-skill trials the best
    IS Sharpe grows like sqrt(2 ln N) times the Sharpe's standard error. The lab compares the
    closed form (Bailey & Lopez de Prado 2014) with the simulated maximum.
  * Deflated Sharpe Ratio (DSR, Bailey & Lopez de Prado 2014): the probability that the true
    Sharpe beats the best Sharpe expected from N noise trials, corrected for track-record
    length, skewness and fat tails. Shown for the best noise strategy and for the planted alpha
    at several assumed trial counts.
  * Probability of Backtest Overfitting (PBO) by combinatorially symmetric cross-validation
    (CSCV, Bailey, Borwein, Lopez de Prado & Zhu 2017): ~50% for a noise-only search, low when
    the search set contains a real alpha.

Supports: docs/03-algorithms/c-validation-and-backtesting/overfitting-and-multiple-testing.md

Run: python labs/13-backtest-overfitting-dsr-pbo/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import itertools
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.stats import norm  # noqa: E402

from common import simulate, utils  # noqa: E402
from common.simulate import PlantedAlpha  # noqa: E402

C_BLUE, C_ORANGE, C_GRAY = "#2a78d6", "#eb6834", "#8a8984"
INK2 = "#52514e"
ANN = np.sqrt(252.0)


# =====================================================================================
# === CORE ALGORITHM ===
# Sharpe ratios inside these functions are PER PERIOD (daily), not annualized.
# =====================================================================================
EULER_GAMMA = 0.5772156649


def expected_max_sharpe(n_trials, sr_std):
    """Expected maximum Sharpe of n_trials independent strategies whose true Sharpe is 0
    (Bailey & Lopez de Prado 2014): sr_std * ((1-g) Z^-1(1 - 1/N) + g Z^-1(1 - 1/(N e))),
    g = Euler-Mascheroni constant, sr_std = standard deviation of the trials' Sharpe estimates."""
    if n_trials <= 1:
        return 0.0
    g = EULER_GAMMA
    return sr_std * ((1 - g) * norm.ppf(1 - 1 / n_trials) + g * norm.ppf(1 - 1 / (n_trials * np.e)))


def deflated_sharpe(returns, n_trials, sr_std_trials):
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014) of the SELECTED strategy.

    returns: its per-period returns; n_trials: how many strategies were tried;
    sr_std_trials: std of the per-period Sharpe estimates across those trials.
    Returns (DSR, SR0): DSR = Prob[true Sharpe > SR0], SR0 = expected max Sharpe of n_trials
    noise strategies. With n_trials = 1, SR0 = 0 and DSR is the Probabilistic Sharpe Ratio.
    """
    r = np.asarray(returns, dtype=float)
    n = r.size
    sr = r.mean() / r.std(ddof=1)
    z = (r - r.mean()) / r.std()
    skew, kurt = np.mean(z ** 3), np.mean(z ** 4)          # kurtosis = 3 for a normal
    sr0 = expected_max_sharpe(n_trials, sr_std_trials)
    stat = (sr - sr0) * np.sqrt(n - 1) / np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    return float(norm.cdf(stat)), float(sr0)


def pbo_cscv(R, n_blocks=16):
    """Probability of Backtest Overfitting by CSCV (Bailey, Borwein, Lopez de Prado & Zhu 2017).

    R: T x N matrix of per-period returns of the N strategy variants tried.
    Cut time into n_blocks blocks; for every way of choosing half of them as in-sample (IS),
    the rest out-of-sample (OOS): pick the best IS Sharpe, find its relative rank w in (0, 1)
    among the N OOS Sharpes, logit = ln(w / (1 - w)). PBO = share of splits with logit <= 0,
    i.e. the IS winner lands at or below the OOS median.
    """
    T, N = R.shape
    blocks = np.array_split(np.arange(T), n_blocks)
    s1 = np.array([R[b].sum(axis=0) for b in blocks])              # block sums, S x N
    s2 = np.array([(R[b] ** 2).sum(axis=0) for b in blocks])
    nb = np.array([len(b) for b in blocks], dtype=float)
    combos = np.array(list(itertools.combinations(range(n_blocks), n_blocks // 2)))
    is_mask = np.zeros((len(combos), n_blocks))
    is_mask[np.arange(len(combos))[:, None], combos] = 1.0

    def sharpe(mask):                                              # Sharpe of the chosen blocks
        n = (mask @ nb)[:, None]
        mu = mask @ s1 / n
        return mu / np.sqrt(mask @ s2 / n - mu ** 2)

    sr_is, sr_oos = sharpe(is_mask), sharpe(1.0 - is_mask)
    best = sr_is.argmax(axis=1)
    oos_best = sr_oos[np.arange(len(combos)), best]
    rank = (sr_oos < oos_best[:, None]).sum(axis=1) + 1            # 1 = worst ... N = best OOS
    w = rank / (N + 1.0)
    logits = np.log(w / (1 - w))
    return dict(pbo=float(np.mean(logits <= 0)), logits=logits, n_splits=len(combos),
                is_sharpe_best=sr_is[np.arange(len(combos)), best], oos_sharpe_best=oos_best)


# === END CORE ALGORITHM ===
# =====================================================================================


def strategy_returns(signal, ret):
    """Daily dollar-neutral book: weights = demeaned signal / sum |.| ($1 gross); P&L on t+1."""
    w = signal - signal.mean(axis=1, keepdims=True)
    w /= np.abs(w).sum(axis=1, keepdims=True)
    return (w[:-1] * ret[1:]).sum(axis=1)


def split_sharpes(R, n_blocks, n_splits, rng):
    """Annualized Sharpe of every column of R on random IS/OOS splits: each split puts a random
    half of the n_blocks time blocks in-sample and the rest out-of-sample. Returns two
    n_splits x N arrays (IS, OOS)."""
    blocks = np.array_split(np.arange(R.shape[0]), n_blocks)
    s1 = np.array([R[b].sum(axis=0) for b in blocks])
    s2 = np.array([(R[b] ** 2).sum(axis=0) for b in blocks])
    nb = np.array([len(b) for b in blocks], dtype=float)
    mask = np.zeros((n_splits, n_blocks))
    for k in range(n_splits):
        mask[k, rng.choice(n_blocks, n_blocks // 2, replace=False)] = 1.0

    def sr(mk):
        n = (mk @ nb)[:, None]
        mu = mk @ s1 / n
        return ANN * mu / np.sqrt(mk @ s2 / n - mu ** 2)

    return sr(mask), sr(1.0 - mask)


def sharpe(x, axis=0):
    """Annualized Sharpe along an axis (gross of costs)."""
    return ANN * x.mean(axis=axis) / x.std(axis=axis, ddof=1)


# ----------------------------------------------------------------------------- experiment
def main():
    t_start = time.time()
    ctx = utils.setup(__file__, "Lab 13: backtest overfitting, DSR and PBO")
    n_stocks, n_days = (100, 504) if ctx.smoke else (100, 1260)
    n_trials = 60 if ctx.smoke else 500
    n_blocks = 8 if ctx.smoke else 16
    rng = np.random.default_rng(ctx.seed)

    real = PlantedAlpha("alpha_real", ic=0.015, half_life=20.0, horizon_decay=0.5 ** (1 / 20.0))
    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, alphas=(real,), seed=ctx.seed)
    R = m.returns.to_numpy()                                    # total returns: a plain backtest
    r_real = strategy_returns(m.alphas["alpha_real"].to_numpy(), R)
    P = np.column_stack([strategy_returns(s.to_numpy(), R)
                         for _, s in simulate.iter_noise_signals(m, n_trials, seed=ctx.seed + 1)])
    T = P.shape[0]
    half = T // 2
    print(f"\nSynthetic market: {n_stocks} stocks x {n_days} days. {n_trials} noise strategies (true Sharpe 0) "
          f"+ 1 planted alpha (IC {real.ic}, half-life {real.half_life:g} d). Gross of costs.")

    # ---- (A) pick the best in-sample, look out-of-sample ------------------------------------
    sr_is, sr_oos = sharpe(P[:half]), sharpe(P[half:])
    best = int(np.argmax(sr_is))
    real_is, real_oos, real_full = sharpe(r_real[:half]), sharpe(r_real[half:]), sharpe(r_real)
    slope = np.polyfit(sr_is, sr_oos, 1)[0]
    rank_real_is = int((sr_is > real_is).sum())
    print("\n[A] Best of the noise strategies on the first half vs the planted alpha")
    print(f"    best noise   IS Sharpe {sr_is[best]:5.2f}  ->  OOS {sr_oos[best]:5.2f}")
    print(f"    planted alpha IS Sharpe {real_is:5.2f}  ->  OOS {real_oos:5.2f}   "
          f"({rank_real_is} noise strategies beat it in-sample)")
    print(f"    across noise: corr(IS, OOS) = {np.corrcoef(sr_is, sr_oos)[0, 1]:+.3f}, slope {slope:+.3f}; "
          f"IS Sharpe sd {sr_is.std():.2f} vs theory {np.sqrt(252 / half):.2f} = sqrt(252/T_IS)")

    # ---- (B) expected max Sharpe vs number of trials -----------------------------------------
    # Many random IS/OOS splits (half of the time blocks in-sample, as in CSCV) x random subsets of
    # N strategies, so that no single lucky strategy dominates the average.
    is_split, oos_split = split_sharpes(P, n_blocks, n_splits=200 if ctx.smoke else 400, rng=rng)
    real_is_split, _ = split_sharpes(r_real[:, None], n_blocks, n_splits=is_split.shape[0],
                                     rng=np.random.default_rng(ctx.seed))
    sr_std_is = float(np.mean(is_split.std(axis=1))) / ANN          # per-period sd across trials
    real_is_avg = float(real_is_split.mean())
    n_grid = np.array([n for n in (1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000) if n <= n_trials])
    emp_max, emp_oos = [], []
    for n in n_grid:
        mx, oo = [], []
        for k in range(is_split.shape[0]):
            for _ in range(10):
                idx = rng.choice(n_trials, size=n, replace=False)
                j = idx[np.argmax(is_split[k, idx])]
                mx.append(is_split[k, j])
                oo.append(oos_split[k, j])
        emp_max.append(np.mean(mx))
        emp_oos.append(np.mean(oo))
    n_theory = np.unique(np.logspace(0, 4, 200).astype(int))
    th_max = np.array([ANN * expected_max_sharpe(n, sr_std_is) for n in n_theory])
    n_cross = int(n_theory[np.argmax(th_max >= real_is_avg)]) if (th_max >= real_is_avg).any() else None
    print("\n[B] Max IS Sharpe of N noise trials (annualized, half-sample windows): theory vs simulated")
    for n, e, o in zip(n_grid, emp_max, emp_oos):
        print(f"    N={n:5d}  theory {ANN * expected_max_sharpe(n, sr_std_is):5.2f}   simulated {e:5.2f}"
              f"   OOS Sharpe of that winner {o:+.2f}")
    print(f"    planted alpha's average IS Sharpe {real_is_avg:.2f}: the luckiest noise strategy is expected "
          f"to beat it once N >= {n_cross}")

    # ---- (C) deflated Sharpe ratio on the full sample ----------------------------------------
    sr_full = sharpe(P)
    best_full = int(np.argmax(sr_full))
    sr_std_full = (sr_full / ANN).std()
    psr_noise, _ = deflated_sharpe(P[:, best_full], 1, sr_std_full)
    dsr_noise, sr0 = deflated_sharpe(P[:, best_full], n_trials, sr_std_full)
    dsr_real = {n: deflated_sharpe(r_real, n, sr_std_full) for n in sorted({1, 10, 100, n_trials})}
    print(f"\n[C] Deflated Sharpe ratio (full {T}-day sample; SR0 = expected max Sharpe of N noise trials)")
    print(f"    best noise strategy: Sharpe {sr_full[best_full]:.2f};  PSR (N=1) {psr_noise:.3f};  "
          f"DSR (N={n_trials}) {dsr_noise:.3f}  [SR0 = {ANN * sr0:.2f}]")
    for n, (d, s0) in dsr_real.items():
        print(f"    planted alpha:       Sharpe {real_full:.2f};  N={n:4d}: SR0 {ANN * s0:4.2f}, DSR {d:.3f}")

    # ---- (D) probability of backtest overfitting by CSCV --------------------------------------
    pbo_noise = pbo_cscv(P, n_blocks)
    pbo_mixed = pbo_cscv(np.column_stack([P, r_real]), n_blocks)
    group = 100 if not ctx.smoke else 20
    pbo_groups = [pbo_cscv(P[:, g:g + group], n_blocks)["pbo"] for g in range(0, n_trials - group + 1, group)]
    print(f"\n[D] PBO by CSCV ({n_blocks} blocks -> {pbo_noise['n_splits']} IS/OOS splits)")
    for label, d in (("noise only", pbo_noise), ("noise + planted alpha", pbo_mixed)):
        print(f"    {label:<22} PBO {d['pbo']:.2f};  IS winner's Sharpe: IS {ANN * d['is_sharpe_best'].mean():.2f}, "
              f"OOS {ANN * d['oos_sharpe_best'].mean():+.2f} (mean over splits); "
              f"OOS < 0 in {100 * np.mean(d['oos_sharpe_best'] < 0):.0f}% of splits")
    print(f"    noise only, {len(pbo_groups)} disjoint groups of {group}: PBO "
          + ", ".join(f"{x:.2f}" for x in pbo_groups) + f" (mean {np.mean(pbo_groups):.2f})")

    # ---- plot 1: IS vs OOS scatter -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.4))
    ax.scatter(sr_is, sr_oos, s=14, color=C_GRAY, alpha=0.6, lw=0, label=f"{n_trials} noise strategies (true Sharpe 0)")
    xs = np.linspace(sr_is.min(), max(sr_is.max(), real_is) + 0.2, 10)
    b1, b0 = np.polyfit(sr_is, sr_oos, 1)
    ax.plot(xs, b0 + b1 * xs, color=INK2, lw=1.2, label=f"OLS fit across noise: slope {b1:+.2f}")
    ax.plot(xs, xs, color=INK2, lw=1, ls=":", label="OOS = IS (no decay)")
    ax.scatter([sr_is[best]], [sr_oos[best]], s=110, color=C_ORANGE, edgecolor="white", lw=1.5, zorder=5,
               label=f"best IS noise strategy: {sr_is[best]:.2f} IS -> {sr_oos[best]:.2f} OOS")
    ax.scatter([real_is], [real_oos], s=220, marker="*", color=C_BLUE, edgecolor="white", lw=1.2, zorder=6,
               label=f"planted alpha: {real_is:.2f} IS -> {real_oos:.2f} OOS")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_xlabel(f"in-sample Sharpe, first {half} days (annualized)")
    ax.set_ylabel(f"out-of-sample Sharpe, last {T - half} days (annualized)")
    ax.set_title("Selection bias: the in-sample winner of a noise search does not persist\n"
                 f"(synthetic data, {n_stocks} stocks, gross of costs)")
    ax.legend(fontsize=8, loc="upper left")
    utils.save_fig(ctx, fig, "is-vs-oos-sharpe")

    # ---- plot 2: expected max Sharpe vs number of trials ----------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(n_theory, th_max, color=C_ORANGE, lw=2, label="expected max IS Sharpe of N noise trials (closed form)")
    ax.plot(n_grid, emp_max, "o", ms=8, color=C_ORANGE, mfc="white", mew=1.8, label="simulated: max IS Sharpe (mean over random splits and subsets)")
    ax.plot(n_grid, emp_oos, "s", ms=7, color=C_GRAY, label="simulated: OOS Sharpe of that IS winner (other half)")
    ax.axhline(real_is_avg, color=C_BLUE, lw=1.5, ls="--",
               label=f"planted alpha, average IS Sharpe {real_is_avg:.2f}")
    if n_cross:
        ax.axvline(n_cross, color=INK2, lw=0.8, ls=":")
        ax.text(n_cross * 1.1, 0.15, f"N = {n_cross}: luck catches up\nwith the real alpha", fontsize=8, color=INK2)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("number of strategies tried, N (log scale)")
    ax.set_ylabel(f"annualized Sharpe (in-sample = random half of the {T} days)")
    ax.set_title("The more you try, the better the best backtest looks\n(synthetic data; noise strategies have zero true Sharpe)")
    ax.legend(fontsize=8, loc="upper left")
    utils.save_fig(ctx, fig, "expected-max-sharpe")

    res = {
        "n_stocks": n_stocks, "n_days": n_days, "n_noise_trials": n_trials,
        "best_noise_is_sharpe": sr_is[best], "best_noise_oos_sharpe": sr_oos[best],
        "planted_alpha_is_sharpe": real_is, "planted_alpha_oos_sharpe": real_oos,
        "planted_alpha_full_sharpe": real_full, "noise_beating_planted_alpha_is": rank_real_is,
        "corr_is_oos_noise": float(np.corrcoef(sr_is, sr_oos)[0, 1]),
        "expected_max_is_sharpe_theory": ANN * expected_max_sharpe(n_trials, sr_std_is),
        "max_is_sharpe_simulated": emp_max[-1], "oos_sharpe_of_is_winner_simulated": emp_oos[-1],
        "planted_alpha_avg_is_sharpe_random_halves": real_is_avg,
        "n_trials_where_luck_beats_planted_alpha": n_cross,
        "best_noise_full_sharpe": sr_full[best_full],
        "best_noise_psr": psr_noise, "best_noise_dsr": dsr_noise, "sr0_annualized": ANN * sr0,
        "planted_alpha_dsr_by_n_trials": {str(n): d for n, (d, _) in dsr_real.items()},
        "pbo_noise_only": pbo_noise["pbo"], "pbo_with_planted_alpha": pbo_mixed["pbo"],
        "cscv_splits": pbo_noise["n_splits"],
        "pbo_noise_disjoint_groups_of_100_mean": float(np.mean(pbo_groups)),
        "pbo_noise_disjoint_groups_range": [float(min(pbo_groups)), float(max(pbo_groups))],
        "cscv_noise_mean_oos_sharpe_of_is_winner": ANN * pbo_noise["oos_sharpe_best"].mean(),
    }
    utils.write_results(ctx, res)
    print(f"\nDone in {time.time() - t_start:.1f} s.")


if __name__ == "__main__":
    main()
