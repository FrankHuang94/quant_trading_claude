"""Lab 14: risk models, covariance shrinkage and constrained mean-variance optimization.

What it demonstrates
  * Four covariance estimators for 500 stocks from a 252-day window (so N > T and the sample
    covariance is singular): (i) the sample covariance, (ii) Ledoit-Wolf (2004) shrinkage toward
    a scaled identity (scikit-learn), (iii) a statistical PCA factor model (k factors + diagonal
    specific variance), (iv) the TRUE covariance of the simulator (oracle).
  * Out-of-sample risk-forecast accuracy: predicted vs realized volatility and the bias statistic
    (std of return / predicted vol; 1 = unbiased) for random portfolios and for portfolios chosen
    by an optimizer that uses each estimate.
  * A cvxpy mean-variance optimizer: maximize alpha'w - risk_aversion * w'Sigma w - costs * |w - w_prev|
    subject to dollar, beta and sector neutrality, position caps and a gross leverage cap.
  * Pitfall: error maximization. The sample covariance is unbiased for any FIXED portfolio, but
    the optimizer seeks out exactly the directions where it underestimates risk, so optimized
    portfolios are far riskier than predicted; the efficient frontier it reports is a mirage.
  * Pitfall: costs. Without a turnover penalty a biweekly-rebalanced book overtrades; with too
    large a penalty it gives up alpha. A penalty well below 1 (the cost amortized over the
    signal's ~20-day life) keeps the most net alpha.

The alpha is a planted signal (daily IC 0.01, half-life 20 days) and the optimizer gets its TRUE
conditional expected return, so differences between runs come from the risk model and costs.

Supports: docs/03-algorithms/d-portfolio-construction/risk-models.md,
          docs/03-algorithms/d-portfolio-construction/covariance-estimation-and-shrinkage.md,
          docs/03-algorithms/d-portfolio-construction/mean-variance-optimization.md

Run: python labs/14-risk-model-mvo/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Small dense matrices: multi-threaded BLAS is slower than one thread (and can be 100x slower
# when several processes share the CPU). Must be set before numpy is imported.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cvxpy as cp  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.covariance import LedoitWolf  # noqa: E402

from common import simulate, utils  # noqa: E402
from common.simulate import PlantedAlpha  # noqa: E402


# =====================================================================================
# === CORE ALGORITHM ===
# Every risk model is stored in factor form:  Sigma = L' L + diag(specific_var)
#   L: (k x N) "square-root loadings" (k factors, or k = T observations for the sample
#   covariance), specific_var: (N,). This keeps the optimizer fast for N = 500.
# =====================================================================================

@dataclass
class FactorCov:
    L: np.ndarray             # (k, N): Sigma = L.T @ L + diag(specific_var)
    specific_var: np.ndarray  # (N,)

    def variance(self, W):
        """Daily variance of each portfolio in W (P x N, or a single N-vector)."""
        W = np.atleast_2d(W)
        return ((W @ self.L.T) ** 2).sum(axis=1) + (W ** 2) @ self.specific_var


def pca_factor_cov(returns, n_factors=16, min_specific_var=1e-6):
    """Statistical factor model from a (T x N) window of daily returns.

    Top-n_factors principal components of the sample covariance are the factors; whatever
    variance they leave on the diagonal is the stock's specific variance (floored). All
    off-diagonal noise beyond the k factors is thrown away, which is the point.
    """
    X = returns - returns.mean(axis=0)
    S = X.T @ X / (len(X) - 1)                          # sample covariance (N x N)
    eigval, eigvec = np.linalg.eigh(S)                  # ascending order
    top = np.argsort(eigval)[::-1][:n_factors]
    L = (eigvec[:, top] * np.sqrt(eigval[top])).T       # (k, N): B F^(1/2), factors orthogonal
    specific = np.maximum(np.diag(S) - (L ** 2).sum(axis=0), min_specific_var)
    return FactorCov(L, specific)


def optimize_portfolio(alpha, cov, w_prev=None, risk_aversion=50.0, cost=None, beta=None,
                       sectors=None, max_weight=0.01, max_gross=2.0):
    """Constrained mean-variance optimizer (weights as fractions of capital).

    maximize   alpha'w - risk_aversion * w'Sigma w - sum_i cost_i * |w_i - w_prev_i|
    subject to sum(w) = 0 (dollar neutral), beta'w = 0, sectors'w = 0 (each sector nets to 0),
               |w_i| <= max_weight, sum|w_i| <= max_gross.
    alpha and Sigma must cover the same horizon (e.g. both 21-day); risk_aversion is then
    horizon-free. cost_i = cost per unit of weight traded (half-spread + impact, as a fraction).
    """
    n = len(alpha)
    w_prev = np.zeros(n) if w_prev is None else w_prev
    w = cp.Variable(n)
    y = cp.Variable(cov.L.shape[0])                      # factor exposures y = L w
    risk = cp.sum_squares(y) + cp.sum_squares(cp.multiply(np.sqrt(cov.specific_var), w))
    objective = alpha @ w - risk_aversion * risk
    if cost is not None:
        objective -= cost @ cp.abs(w - w_prev)
    cons = [y == cov.L @ w, cp.sum(w) == 0, cp.abs(w) <= max_weight, cp.norm1(w) <= max_gross]
    if beta is not None:
        cons.append(beta @ w == 0)
    if sectors is not None:
        cons.append(sectors.T @ w == 0)                  # sectors: (N x n_sectors) 0/1 dummies
    prob = cp.Problem(cp.Maximize(objective), cons)
    prob.solve(solver="SCS", eps_abs=1e-6, eps_rel=1e-6)  # first-order; fast on dense sample cov
    if prob.status != "optimal":
        prob.solve(solver="CLARABEL")                     # interior-point fallback
    return np.asarray(w.value).ravel()


def bias_statistic(realized_returns, predicted_vol):
    """Std of standardized returns r / sigma_pred. 1 = unbiased; > 1 = risk underpredicted."""
    z = np.asarray(realized_returns) / np.asarray(predicted_vol)
    return float(np.std(z, ddof=1))


# === END CORE ALGORITHM ===
# =====================================================================================


def sample_cov(returns):
    """Sample covariance in factor form: Sigma = X'X/(T-1) -> L = X / sqrt(T-1), no specific part."""
    X = returns - returns.mean(axis=0)
    return FactorCov(X / np.sqrt(len(X) - 1), np.zeros(X.shape[1]))


def ledoit_wolf_cov(returns):
    """Ledoit-Wolf (2004) shrinkage toward mu*I, via scikit-learn, in factor form.

    sklearn: Sigma = (1 - delta) * S_mle + delta * mu * I, with S_mle = X'X / T, mu = tr(S)/N.
    """
    lw = LedoitWolf(store_precision=False).fit(returns)
    X = returns - returns.mean(axis=0)
    delta = lw.shrinkage_
    mu = np.trace(X.T @ X / len(X)) / X.shape[1]
    fc = FactorCov(np.sqrt((1 - delta) / len(X)) * X, np.full(X.shape[1], delta * mu))
    return fc, float(delta)


def oracle_cov(m, day):
    """True covariance of the generating model for returns on `day` (known at the prior close)."""
    h = float(m.vol_regime.iloc[day])
    L = (m.exposures.to_numpy() * (m.factor_vol.to_numpy() * h)).T
    return FactorCov(L, m.specific_vol.iloc[day].to_numpy() ** 2)


def alpha_forecast(m, name, day, horizon):
    """TRUE expected specific return over days day+1..day+horizon given the planted signal.

    E[s_{t+1+k}] = loading * sigma_i * score_i * decay**k  (simulator model), summed over k;
    today's specific vol stands in for future vols (the vol regime moves slowly).
    """
    spec = m.alpha_specs[name]
    hd = spec.horizon_decay
    mult = (1 - hd ** horizon) / (1 - hd)
    score = m.alphas[name].iloc[day].to_numpy()
    sigma = m.specific_vol.iloc[day].to_numpy()
    return m.alpha_loadings[name] * sigma * np.nan_to_num(score) * mult


def random_portfolios(rng, n_assets, n_long_short, n_long_only):
    """Random dollar-neutral (gross 2) and long-only (sum 1) weight vectors."""
    ls = rng.standard_normal((n_long_short, n_assets))
    ls -= ls.mean(axis=1, keepdims=True)
    ls *= 2.0 / np.abs(ls).sum(axis=1, keepdims=True)
    lo = rng.exponential(1.0, (n_long_only, n_assets))
    lo /= lo.sum(axis=1, keepdims=True)
    return ls, lo


def main():
    ctx = utils.setup(__file__, "Lab 14: risk models, shrinkage and constrained MVO")
    t_start = time.time()
    rng = np.random.default_rng(ctx.seed)
    if ctx.smoke:
        n_stocks, n_days, window, step, opt_every, cost_years = 150, 420, 100, 42, 2, 0.4
    else:
        n_stocks, n_days, window, step, opt_every, cost_years = 500, 1260, 252, 21, 3, 2.0
    horizon = 21                       # holding period of the monthly test (days)
    n_factors = 16                     # PCA factors (the true model has 1 + 4 + 11 = 16)
    risk_aversion = 50.0               # utility = alpha'w - 50 w'Sigma w (any horizon); README
    max_weight, max_gross = 0.01, 2.0  # 1% name cap, 100/100 long-short book

    alpha_spec = PlantedAlpha("alpha", ic=0.01, half_life=20.0, horizon_decay=0.5 ** (1 / 20.0))
    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, alphas=(alpha_spec,),
                                        seed=ctx.seed)
    R = m.returns.to_numpy()
    beta = m.beta.to_numpy()
    sectors = m.exposures.filter(like="sec_").to_numpy()
    half_spread = m.spread_bps.to_numpy() / 2 / 1e4          # fraction per unit traded
    cost_unit = half_spread + 5e-4                           # + 5 bps stylized impact/commission
    names = ["Sample", "Ledoit-Wolf", f"PCA (k={n_factors})", "True (oracle)"]

    # sanity: the factor-form oracle equals the simulator's true_covariance()
    oc = oracle_cov(m, window)
    sub = slice(0, 5)
    full = (oc.L.T @ oc.L + np.diag(oc.specific_var))[sub, sub]
    assert np.allclose(full, m.true_covariance(window).to_numpy()[sub, sub])

    # ---------------------------------------------------------------- A: risk forecasts
    ls, lo = random_portfolios(rng, n_stocks, 200, 100)
    dates = list(range(window - 1, n_days - horizon - 1, step))
    pred = {k: {"ls": [], "lo": [], "opt": []} for k in names}
    real = {"ls": [], "lo": [], "opt": {k: [] for k in names}}
    w_prev = {k: np.zeros(n_stocks) for k in names}
    shrinkages = []
    for i, t in enumerate(dates):
        X = R[t - window + 1:t + 1]
        lw, delta = ledoit_wolf_cov(X)
        shrinkages.append(delta)
        models = dict(zip(names, [sample_cov(X), lw, pca_factor_cov(X, n_factors), oracle_cov(m, t + 1)]))
        fwd = R[t + 1:t + 1 + horizon]                              # (H x N) daily returns ahead
        real["ls"].append(fwd @ ls.T)
        real["lo"].append(fwd @ lo.T)
        do_opt = i % opt_every == 0
        alpha = alpha_forecast(m, "alpha", t, horizon)
        for k, cov in models.items():
            pred[k]["ls"].append(np.sqrt(cov.variance(ls)))
            pred[k]["lo"].append(np.sqrt(cov.variance(lo)))
            if do_opt:
                cov_h = FactorCov(cov.L * np.sqrt(horizon), cov.specific_var * horizon)
                w = optimize_portfolio(alpha, cov_h, w_prev[k], risk_aversion, cost_unit, beta,
                                       sectors, max_weight, max_gross)
                w_prev[k] = w
                pred[k]["opt"].append(float(np.sqrt(cov.variance(w))[0]))
                real["opt"][k].append(fwd @ w)
    t_risk = time.time() - t_start

    def stats(k):
        out = {}
        for typ in ("ls", "lo"):
            r = np.concatenate(real[typ])                                    # (dates*H, P)
            p = np.repeat(np.array(pred[k][typ]), horizon, axis=0)           # same shape
            out[f"bias_{typ}"] = float(np.mean([bias_statistic(r[:, j], p[:, j]) for j in range(r.shape[1])]))
        r = np.concatenate(real["opt"][k])
        p = np.repeat(np.array(pred[k]["opt"]), horizon)
        out["bias_opt"] = bias_statistic(r, p)
        out["opt_pred_vol"] = float(np.mean(pred[k]["opt"]) * np.sqrt(252))
        out["opt_real_vol"] = float(np.std(r, ddof=1) * np.sqrt(252))
        return out
    risk_stats = {k: stats(k) for k in names}

    # ---------------------------------------------------------------- B: efficient frontier
    t_f = dates[len(dates) // 2]
    X = R[t_f - window + 1:t_f + 1]
    models = dict(zip(names, [sample_cov(X), ledoit_wolf_cov(X)[0], pca_factor_cov(X, n_factors),
                              oracle_cov(m, t_f + 1)]))
    truth = models[names[-1]]
    alpha = alpha_forecast(m, "alpha", t_f, horizon)
    lam_grid = [3, 20, 50, 200, 1000] if ctx.smoke else [3, 10, 20, 50, 100, 200, 500, 1000]
    frontier = {k: [] for k in names}
    for k, cov in models.items():
        cov_h = FactorCov(cov.L * np.sqrt(horizon), cov.specific_var * horizon)
        for lam in lam_grid:
            w = optimize_portfolio(alpha, cov_h, None, lam, None, beta, sectors, max_weight, max_gross)
            ann = np.sqrt(252)
            frontier[k].append(dict(lam=lam, alpha=float(alpha @ w) * 252 / horizon,
                                    pred_vol=float(np.sqrt(cov.variance(w))[0]) * ann,
                                    true_vol=float(np.sqrt(truth.variance(w))[0]) * ann,
                                    gross=float(np.abs(w).sum())))
    t_frontier = time.time() - t_start - t_risk

    # ---------------------------------------------------------------- C: costs and turnover
    reb = 10                                                  # rebalance every 2 weeks
    n_cost_days = int(cost_years * 252)
    cost_dates = list(range(n_days - n_cost_days - 1, n_days - reb - 1, reb))
    cost_runs = {}
    for kappa in (0.0, 0.25, 1.0):
        w = np.zeros(n_stocks)
        gross_pnl, net_pnl, turnover, exp_alpha = [], [], [], []
        for t in cost_dates:
            X = R[t - window + 1:t + 1]
            cov = pca_factor_cov(X, n_factors)
            cov_h = FactorCov(cov.L * np.sqrt(reb), cov.specific_var * reb)
            a = alpha_forecast(m, "alpha", t, reb)
            w_new = optimize_portfolio(a, cov_h, w, risk_aversion, kappa * cost_unit,
                                       beta, sectors, max_weight, max_gross)
            trade = np.abs(w_new - w)
            w = w_new
            exp_alpha.append(float(a @ w))                    # TRUE expected 10-day return
            g = R[t + 1:t + 1 + reb] @ w
            c = np.zeros(reb)
            c[0] = trade @ cost_unit
            gross_pnl.append(g)
            net_pnl.append(g - c)
            turnover.append(trade.sum() / 2)          # (buys + sells) / 2, fraction of capital
        g, n_ = np.concatenate(gross_pnl), np.concatenate(net_pnl)
        cost_runs[kappa] = dict(sharpe_gross=utils.annualized_sharpe(g), sharpe_net=utils.annualized_sharpe(n_),
                                annual_turnover=float(np.sum(turnover) / (len(cost_dates) * reb) * 252),
                                cost_bps_per_year=float((g - n_).sum() / len(g) * 252 * 1e4),
                                gross_return_pct=float(g.mean() * 252 * 100),
                                expected_alpha_bps=float(np.mean(exp_alpha) * 252 / reb * 1e4))
    t_cost = time.time() - t_start - t_risk - t_frontier

    # ---------------------------------------------------------------- plot 1: predicted vs realized
    # categorical slots 2, 3, 1 of the KB palette; the oracle (truth) is drawn in neutral ink
    colors = {names[0]: "#eb6834", names[1]: "#1baf7a", names[2]: "#2a78d6", names[3]: "#30302e"}
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.4), sharex=True, sharey=True)
    ann = np.sqrt(252)
    for ax, k in zip(axes, names):
        p_ls = np.array(pred[k]["ls"])[:, :40].ravel() * ann
        r_ls = np.array([np.sqrt((x[:, :40] ** 2).mean(axis=0)) for x in real["ls"]]).ravel() * ann
        p_opt = np.array(pred[k]["opt"]) * ann
        r_opt = np.array([np.sqrt((x ** 2).mean()) for x in real["opt"][k]]) * ann
        ax.scatter(100 * p_ls, 100 * r_ls, s=4, color="0.65", alpha=0.35, label="random long-short")
        ax.scatter(100 * p_opt, 100 * r_opt, s=22, color=colors[k], edgecolor="k", lw=0.4,
                   label="optimized (MVO)")
        lim = (0.5, 10)
        ax.plot(lim, lim, "k--", lw=1)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(*lim)
        ax.set_ylim(*lim)
        s = risk_stats[k]
        ax.set_title(f"{k}\nbias: random {s['bias_ls']:.2f}, optimized {s['bias_opt']:.2f}", fontsize=9.5)
        ax.set_xlabel("predicted vol (% per year)")
        ax.set_xticks([1, 2, 5], ["1", "2", "5"])
        ax.set_yticks([1, 2, 5], ["1", "2", "5"])
        ax.minorticks_off()
    axes[0].set_ylabel("realized vol, next 21 days (% per year)")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle(f"Risk forecasts out of sample: {n_stocks} stocks, {window}-day estimation window; "
                 "dashed line = perfect forecast (synthetic data)", fontweight="bold", y=1.0)
    fig.subplots_adjust(top=0.80, wspace=0.08)
    utils.save_fig(ctx, fig, "risk-forecast")

    # ---------------------------------------------------------------- plot 2: frontier
    fig, ax = plt.subplots(figsize=(9, 5.4))
    for k in names:
        f = frontier[k]
        a_ = [100 * x["alpha"] for x in f]
        ax.plot([100 * x["true_vol"] for x in f], a_, "-o", color=colors[k], ms=4, lw=2,
                label=f"{k}: true risk")
        if k != names[-1]:
            ax.plot([100 * x["pred_vol"] for x in f], a_, "--", color=colors[k], lw=1.3,
                    label=f"{k}: predicted risk")
    ax.set_xlabel("portfolio volatility (% per year; true = oracle covariance)")
    ax.set_ylabel("expected alpha (% per year, ex ante)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.set_title("Efficient frontiers: what each risk model promises (dashed) vs delivers (solid)\n"
                 "dollar/beta/sector neutral, 1% name cap, gross <= 200% (synthetic data)")
    ax.legend(fontsize=8, loc="lower right", ncol=2)
    utils.save_fig(ctx, fig, "frontier")

    # ---------------------------------------------------------------- results
    mid_lam = lam_grid.index(risk_aversion)
    res = {
        "n_stocks": n_stocks, "window_days": window, "n_forecast_dates": len(dates),
        "n_optimized_dates": len(pred[names[0]]["opt"]),
        "sample_cov_rank": int(np.linalg.matrix_rank(sample_cov(X).L)),
        "ledoit_wolf_shrinkage_mean": float(np.mean(shrinkages)),
        "risk_aversion": risk_aversion,
    }
    short = {names[0]: "sample", names[1]: "ledoit_wolf", names[2]: "pca", names[3]: "oracle"}
    res["bias_statistic"] = {short[k]: {"random_long_short": s["bias_ls"], "random_long_only": s["bias_lo"],
                                        "optimized_mvo": s["bias_opt"]} for k, s in risk_stats.items()}
    res["optimized_vol_pct_predicted_vs_realized"] = {
        short[k]: [100 * s["opt_pred_vol"], 100 * s["opt_real_vol"]] for k, s in risk_stats.items()}
    res["frontier_true_over_predicted_vol_at_risk_aversion_50"] = {
        short[k]: frontier[k][mid_lam]["true_vol"] / frontier[k][mid_lam]["pred_vol"] for k in names}
    res["frontier_expected_alpha_per_true_vol_at_risk_aversion_50"] = {
        short[k]: frontier[k][mid_lam]["alpha"] / frontier[k][mid_lam]["true_vol"] for k in names}
    res["cost_test_pca_biweekly"] = {
        f"cost_aversion_{kappa:g}": {
            "sharpe_gross": r["sharpe_gross"], "sharpe_net": r["sharpe_net"],
            "annual_turnover_x_capital": r["annual_turnover"], "cost_bps_per_year": r["cost_bps_per_year"],
            "expected_alpha_bps_per_year": r["expected_alpha_bps"],
            "expected_net_alpha_bps_per_year": r["expected_alpha_bps"] - r["cost_bps_per_year"]}
        for kappa, r in cost_runs.items()}
    utils.write_results(ctx, res)

    print(f"\n{n_stocks} stocks, {window}-day estimation window, {len(dates)} forecast dates "
          f"(optimizer every {opt_every * step} days); mean LW shrinkage {np.mean(shrinkages):.2f}")
    print(f"{'estimator':<16}{'bias LS':>8}{'bias LO':>8}{'bias opt':>9}{'opt pred vol':>13}"
          f"{'opt real vol':>13}{'frontier true/pred':>19}")
    for k, s in risk_stats.items():
        f = frontier[k][mid_lam]
        print(f"{k:<16}{s['bias_ls']:>8.2f}{s['bias_lo']:>8.2f}{s['bias_opt']:>9.2f}"
              f"{100 * s['opt_pred_vol']:>12.1f}%{100 * s['opt_real_vol']:>12.1f}%"
              f"{f['true_vol'] / f['pred_vol']:>19.2f}")
    print(f"\nBiweekly MVO with PCA risk model, last {cost_years:g} years (costs = half-spread + 5 bps):")
    for kappa, r in cost_runs.items():
        print(f"  cost aversion {kappa:g}: turnover {r['annual_turnover']:.1f}x/yr, gross Sharpe "
              f"{r['sharpe_gross']:.2f}, net Sharpe {r['sharpe_net']:.2f}, expected alpha "
              f"{r['expected_alpha_bps']:.0f} - costs {r['cost_bps_per_year']:.0f} = "
              f"{r['expected_alpha_bps'] - r['cost_bps_per_year']:.0f} bps/yr")
    print(f"runtime: risk test {t_risk:.1f}s, frontier {t_frontier:.1f}s, cost test {t_cost:.1f}s")


if __name__ == "__main__":
    main()
