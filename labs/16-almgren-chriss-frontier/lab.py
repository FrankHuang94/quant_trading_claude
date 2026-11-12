"""Lab 16: Almgren-Chriss optimal liquidation and the cost-vs-risk efficient frontier.

What it demonstrates
  * The closed-form Almgren & Chriss (2000) optimal liquidation trajectory for a given risk
    aversion lambda (linear temporary + permanent impact, arithmetic Brownian price).
  * The efficient frontier of expected implementation shortfall vs its standard deviation, traced
    by sweeping lambda; TWAP is the risk-neutral end point (lambda = 0).
  * A Monte Carlo of realized shortfall for TWAP, AC at several lambdas and a front-loaded
    heuristic, checking that the closed-form mean/variance are recovered and that the heuristic
    sits inside (is dominated by) the frontier.
  * Pitfalls: (1) a single order's realized shortfall is mostly price noise, so "AC beat TWAP"
    on one trade proves nothing; (2) the linear impact model misprices fast schedules when true
    temporary impact is concave (square-root-like), and very risk-averse schedules demand
    participation rates no desk would accept.

Illustrative calibration: a $500M sell order (10M shares at $50) in a stock trading $1B/day
(20M shares/day), over 5 trading days in 50 intervals. Parameters are stylized; see README.

Supports: docs/03-algorithms/e-execution-algorithms/implementation-shortfall-and-almgren-chriss.md
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from common import utils  # noqa: E402


# =====================================================================================
# === CORE ALGORITHM ===
# Units: shares, dollars, trading days. sigma is in $/share/sqrt(day).
#   temporary impact: execution price = S - epsilon - eta * (shares per day)    [linear]
#   permanent impact: S drops by gamma per share sold
#   objective:        minimize E[shortfall] + lam * Var[shortfall]   (lam in 1/$)
# =====================================================================================

def ac_trajectory(X, T, n, sigma, eta, gamma, lam):
    """Almgren-Chriss (2000) optimal holdings x_0..x_n for selling X shares over T days.

    X: shares to sell; T: horizon (days); n: number of trading intervals (tau = T/n);
    sigma: price vol ($/share/sqrt(day)); eta: temporary impact ($/share per share/day);
    gamma: permanent impact ($/share per share); lam: risk aversion (1/$).
    Returns an array of n+1 holdings, x_0 = X ... x_n = 0.
    """
    tau = T / n
    t = np.arange(n + 1) * tau
    eta_tilde = eta - 0.5 * gamma * tau          # discrete-time correction from the paper
    if eta_tilde <= 0:
        raise ValueError("eta - gamma*tau/2 must be > 0 (refine the time grid)")
    if lam <= 0:
        return X * (1.0 - t / T)                 # risk-neutral: straight line = TWAP
    kappa_tilde_sq = lam * sigma**2 / eta_tilde  # continuous-time urgency squared
    kappa = np.arccosh(0.5 * kappa_tilde_sq * tau**2 + 1.0) / tau   # urgency (1/day)
    # holdings decay like sinh: half-life ~ ln(2)/kappa days when kappa*T >> 1
    return X * np.sinh(kappa * (T - t)) / np.sinh(kappa * T)


def ac_cost_variance(holdings, T, sigma, eta, gamma, epsilon=0.0):
    """Expected shortfall E and variance V ($, $^2) of ANY sell schedule under the AC model.

    holdings: x_0..x_n (shares still to sell at each interval boundary), x_n = 0.
    E = 1/2 gamma X^2 + epsilon * sum|n_k| + (eta_tilde / tau) * sum n_k^2
    V = sigma^2 * tau * sum_{k=1..n} x_k^2
    where n_k = x_{k-1} - x_k is the number of shares sold in interval k.
    """
    x = np.asarray(holdings, dtype=float)
    n = len(x) - 1
    tau = T / n
    trades = -np.diff(x)
    eta_tilde = eta - 0.5 * gamma * tau
    expected = (0.5 * gamma * x[0] ** 2 + epsilon * np.abs(trades).sum()
                + eta_tilde / tau * np.sum(trades**2))
    variance = sigma**2 * tau * np.sum(x[1:] ** 2)
    return expected, variance


# === END CORE ALGORITHM ===
# =====================================================================================


def urgency(T, n, sigma, eta, gamma, lam):
    """kappa (1/day) used by ac_trajectory, for reporting half-lives."""
    tau = T / n
    if lam <= 0:
        return 0.0
    k2 = lam * sigma**2 / (eta - 0.5 * gamma * tau)
    return float(np.arccosh(0.5 * k2 * tau**2 + 1.0) / tau)


def front_loaded_schedule(X, T, n, first_day_fraction=0.5):
    """Heuristic: sell `first_day_fraction` of X evenly on day 1, the rest evenly afterwards."""
    tau = T / n
    per_day = int(round(1.0 / tau))
    trades = np.empty(n)
    trades[:per_day] = first_day_fraction * X / per_day
    trades[per_day:] = (1.0 - first_day_fraction) * X / (n - per_day)
    return np.concatenate([[X], X - np.cumsum(trades)])


def simulate_shortfall(holdings, T, S0, sigma, eta, gamma, epsilon, z, impact="linear", v_ref=None):
    """Realized implementation shortfall ($) per path for a sell schedule.

    z: (paths, n) standard normals (pass the same z to every strategy = common random numbers).
    impact="linear": temporary cost epsilon + eta*v (the AC model, should match ac_cost_variance);
    impact="sqrt":   temporary cost epsilon + eta*v_ref*sqrt(v/v_ref), i.e. equal to the linear
                     model at the reference rate v_ref but concave (square-root-law-like).
    """
    x = np.asarray(holdings, dtype=float)
    n = len(x) - 1
    tau = T / n
    trades = -np.diff(x)
    rate = trades / tau                                         # shares/day in each interval
    diffusion = sigma * np.sqrt(tau) * np.cumsum(z, axis=1)    # random part of S after interval k
    diffusion_before = np.hstack([np.zeros((z.shape[0], 1)), diffusion[:, :-1]])
    S_before = S0 + diffusion_before - gamma * (x[0] - x[:-1])  # price when interval k starts
    if impact == "linear":
        temp = epsilon * np.sign(trades) + eta * rate
    else:
        temp = epsilon * np.sign(trades) + eta * v_ref * np.sign(rate) * np.sqrt(np.abs(rate) / v_ref)
    proceeds = (trades * (S_before - temp)).sum(axis=1)
    return x[0] * S0 - proceeds


def lam_for_variance(target_var, X, T, n, sigma, eta, gamma, epsilon):
    """Bisection (in log lambda) for the AC lambda whose variance equals target_var."""
    lo, hi = -14.0, -3.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        _, v = ac_cost_variance(ac_trajectory(X, T, n, sigma, eta, gamma, 10**mid), T, sigma, eta,
                                gamma, epsilon)
        lo, hi = (mid, hi) if v > target_var else (lo, mid)
    return 10 ** (0.5 * (lo + hi))


def main():
    ctx = utils.setup(__file__, "Lab 16: Almgren-Chriss optimal execution frontier")
    rng = np.random.default_rng(ctx.seed)

    # ---- illustrative calibration (see README "Key parameters") ----------------------
    S0 = 50.0                      # $/share
    adv_shares = 20e6              # 20M shares/day  -> $1B ADV
    X = 10e6                       # 10M shares      -> $500M order = 50% of ADV
    T, n = 5.0, 50                 # 5 trading days, 10 intervals/day (~39 min each)
    sigma = 0.02 * S0              # 2% daily vol -> $1.00/share/sqrt(day)
    epsilon = 0.00015 * S0         # half-spread 1.5 bps -> $0.0075/share
    v_ref = X / T                  # TWAP rate: 2M shares/day = 10% of ADV
    eta = 0.0020 * S0 / v_ref      # temporary impact 20 bps at 10% of ADV  -> 5e-8
    gamma = 0.0050 * S0 / X        # permanent drop 50 bps after selling the whole order -> 2.5e-8
    notional = X * S0
    to_bps = 1e4 / notional

    n_paths = 2_000 if ctx.smoke else 40_000
    lam_grid = np.concatenate([[0.0], np.logspace(-10, -5.5, 15 if ctx.smoke else 80)])

    strategies = {"TWAP (lambda=0)": ac_trajectory(X, T, n, sigma, eta, gamma, 0.0)}
    for lam in (1e-9, 1e-8, 1e-7, 1e-6):
        strategies[f"AC lambda={lam:.0e}"] = ac_trajectory(X, T, n, sigma, eta, gamma, lam)
    strategies["Front-loaded (50% day 1)"] = front_loaded_schedule(X, T, n, 0.5)

    # ---- closed form vs Monte Carlo (linear world) and the sqrt-impact world ---------
    z = rng.standard_normal((n_paths, n))           # common random numbers for all strategies
    rows, shortfalls = {}, {}
    for name, hold in strategies.items():
        E, V = ac_cost_variance(hold, T, sigma, eta, gamma, epsilon)
        sf = simulate_shortfall(hold, T, S0, sigma, eta, gamma, epsilon, z) * to_bps
        sf_sqrt = simulate_shortfall(hold, T, S0, sigma, eta, gamma, epsilon, z, "sqrt", v_ref) * to_bps
        shortfalls[name] = sf
        rows[name] = dict(E_bps=E * to_bps, sd_bps=np.sqrt(V) * to_bps, mc_mean=sf.mean(),
                          mc_sd=sf.std(ddof=1), mc_p95=np.percentile(sf, 95),
                          sqrt_mean=sf_sqrt.mean(),
                          max_participation=float(np.max(-np.diff(hold)) / (T / n) / adv_shares))

    frontier = np.array([ac_cost_variance(ac_trajectory(X, T, n, sigma, eta, gamma, lam), T, sigma,
                                          eta, gamma, epsilon) for lam in lam_grid])
    front_E, front_sd = frontier[:, 0] * to_bps, np.sqrt(frontier[:, 1]) * to_bps

    # front-loaded heuristic vs the AC schedule with the same variance
    fl = rows["Front-loaded (50% day 1)"]
    lam_match = lam_for_variance((fl["sd_bps"] / to_bps) ** 2, X, T, n, sigma, eta, gamma, epsilon)
    E_match, _ = ac_cost_variance(ac_trajectory(X, T, n, sigma, eta, gamma, lam_match), T, sigma, eta,
                                  gamma, epsilon)
    fl_excess = fl["E_bps"] - E_match * to_bps

    mc_err_mean = max(abs(r["mc_mean"] - r["E_bps"]) / r["sd_bps"] * np.sqrt(n_paths) for r in rows.values())
    mc_err_sd = max(abs(r["mc_sd"] / r["sd_bps"] - 1) for r in rows.values())
    key_ac = "AC lambda=1e-07"
    p_twap_beats = float(np.mean(shortfalls["TWAP (lambda=0)"] < shortfalls[key_ac]))

    # ---- plot 1: trajectories --------------------------------------------------------
    t_grid = np.arange(n + 1) * T / n
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = plt.cm.viridis(np.linspace(0, 0.85, 5))
    for (name, hold), c in zip(list(strategies.items())[:5], colors):
        lam = 0.0 if name.startswith("TWAP") else float(name.split("=")[1])
        kappa = urgency(T, n, sigma, eta, gamma, lam)
        hl = f", half-life {np.log(2) / kappa:.2f} d" if kappa > 0 else ""
        ax.plot(t_grid, 100 * hold / X, color=c, lw=2, label=f"{name}{hl}")
    ax.plot(t_grid, 100 * strategies["Front-loaded (50% day 1)"] / X, "k--", lw=1.5,
            label="Front-loaded heuristic (50% on day 1)")
    ax.set_xlabel("time (trading days)")
    ax.set_ylabel("shares still to sell (% of order)")
    ax.set_title("Almgren-Chriss optimal liquidation: \\$500M order, \\$1B ADV, 5 days\n"
                 "(synthetic data, stylized parameters; lambda in 1/\\$)")
    ax.legend(loc="upper right", fontsize=8.5)
    ax.set_xlim(0, T)
    ax.set_ylim(0, 102)
    utils.save_fig(ctx, fig, "trajectories")

    # ---- plot 2: frontier with MC points + realized shortfall distributions -----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.15, 1]})
    ax1.plot(front_sd, front_E, color="0.3", lw=2, label="AC efficient frontier (closed form)")
    marker_colors = list(colors) + ["k"]
    for (name, r), c in zip(rows.items(), marker_colors):
        ax1.errorbar(r["mc_sd"], r["mc_mean"], yerr=1.96 * r["mc_sd"] / np.sqrt(n_paths), fmt="o",
                     color=c, ms=8, label=f"{name}: MC")
        ax1.plot(r["mc_sd"], r["sqrt_mean"], marker="o", mfc="none", mec=c, ms=8, ls="none")
    ax1.plot([], [], marker="o", mfc="none", mec="0.3", ls="none",
             label="same schedule, square-root temporary impact")
    ax1.annotate(f"front-loaded heuristic:\n{fl_excess:.1f} bps above the frontier",
                 xy=(fl["mc_sd"], fl["mc_mean"]), xytext=(fl["mc_sd"] - 60, fl["mc_mean"] + 90),
                 fontsize=8, arrowprops=dict(arrowstyle="->", color="0.3"))
    ax1.set_xlabel("std of implementation shortfall (bps of order notional)")
    ax1.set_ylabel("expected implementation shortfall (bps)")
    ax1.set_title("Cost-risk efficient frontier (synthetic)")
    ax1.legend(fontsize=7.5, loc="upper right")
    bins = np.linspace(-700, 900, 81)
    for name, c in (("TWAP (lambda=0)", colors[0]), (key_ac, colors[3]),
                    ("Front-loaded (50% day 1)", "k")):
        ax2.hist(shortfalls[name], bins=bins, histtype="step", lw=1.8, color=c, density=True,
                 label=f"{name}: mean {rows[name]['mc_mean']:.0f}, sd {rows[name]['mc_sd']:.0f}")
    ax2.set_xlabel("realized implementation shortfall (bps, + = cost)")
    ax2.set_ylabel("density")
    ax2.set_title(f"Realized shortfall, {n_paths:,} simulated orders (synthetic)")
    ax2.legend(fontsize=8, loc="upper right")
    utils.save_fig(ctx, fig, "frontier")

    # ---- results ---------------------------------------------------------------------
    tw, ac, fast = rows["TWAP (lambda=0)"], rows[key_ac], rows["AC lambda=1e-06"]
    results = {
        "order_notional_usd": notional, "order_pct_adv": 100 * X / adv_shares,
        "twap_expected_cost_bps": tw["E_bps"], "twap_sd_bps": tw["sd_bps"],
        "ac_lam1e-7_expected_cost_bps": ac["E_bps"], "ac_lam1e-7_sd_bps": ac["sd_bps"],
        "ac_lam1e-7_half_life_days": np.log(2) / urgency(T, n, sigma, eta, gamma, 1e-7),
        "ac_lam1e-6_expected_cost_bps": fast["E_bps"], "ac_lam1e-6_sd_bps": fast["sd_bps"],
        "front_loaded_expected_cost_bps": fl["E_bps"], "front_loaded_sd_bps": fl["sd_bps"],
        "front_loaded_excess_cost_vs_frontier_bps": fl_excess,
        "mc_mean_max_error_in_standard_errors": mc_err_mean,
        "mc_sd_max_relative_error": mc_err_sd,
        "p95_shortfall_bps_twap": tw["mc_p95"], "p95_shortfall_bps_ac_lam1e-7": ac["mc_p95"],
        "prob_twap_beats_ac_lam1e-7_on_one_order": p_twap_beats,
        "sqrt_impact_cost_bps_twap": tw["sqrt_mean"], "sqrt_impact_cost_bps_ac_lam1e-6": fast["sqrt_mean"],
        "ac_lam1e-6_max_participation_pct_adv": 100 * fast["max_participation"],
    }
    utils.write_results(ctx, results)

    print(f"\nOrder: ${notional/1e6:.0f}M = {100*X/adv_shares:.0f}% of ADV, {T:.0f} days, {n} intervals")
    print(f"{'strategy':<27}{'E[IS] bps':>10}{'sd bps':>8}{'MC mean':>9}{'MC sd':>7}{'p95':>6}"
          f"{'sqrt-impact E':>14}{'max %ADV/day':>13}")
    for name, r in rows.items():
        print(f"{name:<27}{r['E_bps']:>10.1f}{r['sd_bps']:>8.1f}{r['mc_mean']:>9.1f}{r['mc_sd']:>7.1f}"
              f"{r['mc_p95']:>6.0f}{r['sqrt_mean']:>14.1f}{100*r['max_participation']:>13.0f}")
    print(f"Front-loaded heuristic costs {fl_excess:.1f} bps more than the AC schedule with equal risk.")
    print(f"P(TWAP beats AC lambda=1e-7 on a single order) = {p_twap_beats:.2f}")


if __name__ == "__main__":
    main()
