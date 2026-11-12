"""Lab 15: multi-period portfolio choice -- trade partially toward the aim (Garleanu-Pedersen).

What it demonstrates
  * Garleanu & Pedersen (2013): with predictable returns whose signals decay at known rates and
    QUADRATIC transaction costs (cost = 1/2 * lam * dx' Sigma dx), the optimal policy is
        x_t = x_{t-1} + (a / lam) * (aim_t - x_{t-1})
    i.e. trade a fixed fraction a/lam of the way toward an "aim" portfolio each day. The rate a/lam
    depends on costs (lam) and risk aversion (gamma) only; signal persistence enters through the
    aim, which down-weights fast-decaying signals relative to the Markowitz portfolio.
  * On a simulated 300-stock market with planted alphas of equal IC but half-lives of 1, 5, 20 and
    60 days, a grid search over the trade rate recovers the closed-form rate, and full daily
    rebalancing to the Markowitz portfolio is destroyed by costs for fast signals.
  * If you instead trade toward the plain Markowitz portfolio (a common shortcut), the best rate
    DOES depend on the half-life and the best achievable result is worse.
  * Pitfall: single-period ("myopic") cost-aware optimization trades far too slowly, because it
    charges the full cost of a trade against one day of alpha.

The book is assumed factor-hedged (P&L = positions x specific returns) and the trader is given the
TRUE signal model, so differences between rules come from trading alone.

Supports: docs/03-algorithms/d-portfolio-construction/multi-period-and-trading-toward-aim.md

Run: python labs/15-trading-toward-aim/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")   # small arrays: avoid BLAS thread oversubscription

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common import simulate, utils  # noqa: E402
from common.simulate import PlantedAlpha  # noqa: E402


# =====================================================================================
# === CORE ALGORITHM ===
# Garleanu & Pedersen (2013), "Dynamic Trading with Predictable Returns and Transaction Costs".
# Model (per day): expected return of asset i tomorrow = sum_k B_ik f_k,t ; each signal f_k
# mean-reverts, f_k,t+1 = (1 - phi_k) f_k,t + noise ; risk penalty gamma/2 x'Sigma x ;
# trading cost 1/2 dx' Lambda dx with Lambda = lam * Sigma. Positions x in dollars.
# =====================================================================================

def gp_trade_rate(gamma, lam, rho=0.0):
    """Optimal fraction of the gap to the aim to close each period: a / lam.

    gamma: risk aversion (1/$); lam: cost multiplier (Lambda = lam * Sigma, 1/$);
    rho: per-period discount rate. Closed form from Garleanu & Pedersen (2013).
    Higher costs -> slower trading; higher risk aversion -> faster trading.
    """
    g = gamma * (1 - rho) + lam * rho
    a = (-g + np.sqrt(g ** 2 + 4 * gamma * lam * (1 - rho) ** 2)) / (2 * (1 - rho))
    return a / lam


def aim_portfolio(signal_alphas, decay_rates, sigma2, gamma, lam, rho=0.0):
    """GP aim: the Markowitz portfolio of each signal, shrunk by 1 / (1 + a * phi / gamma).

    signal_alphas: list of (N,) expected next-day returns, one per signal (alpha_k = B_k f_k);
    decay_rates:   list of phi_k = 1 - per-day persistence (phi = 1 - 0.5**(1/half_life));
    sigma2: (N,) variances (diagonal Sigma). Persistent signals (small phi) keep almost full
    weight; fast signals are scaled down because they will be gone before you finish trading.
    """
    a = gp_trade_rate(gamma, lam, rho) * lam
    aim = 0.0
    for alpha_k, phi_k in zip(signal_alphas, decay_rates):
        markowitz_k = alpha_k / (gamma * sigma2)          # (gamma Sigma)^-1 alpha_k
        aim = aim + markowitz_k / (1 + a * phi_k / gamma)
    return aim


def trade_toward_aim(current, aim, rate):
    """Move a fraction `rate` of the way from the current portfolio to the aim.

    rate = 1 is full rebalancing; GP's optimal rate is gp_trade_rate(gamma, lam).
    """
    return current + rate * (aim - current)


# === END CORE ALGORITHM ===
# =====================================================================================


def run_books(targets, sig2, alpha, s_next, rates, gamma, lam, burn):
    """Simulate x_t = trade_toward_aim(x_{t-1}, target_t, rate) for a vector of rates at once.

    targets, sig2, alpha, s_next: (T, N) arrays aligned at the decision day t (s_next[t] is the
    specific return of day t+1). Returns dict of (n_rates, T - burn) daily series ($).
    """
    T, N = targets.shape
    r = np.asarray(rates, dtype=float)[:, None]
    x = np.zeros((len(r), N))
    out = {k: np.empty((len(r), T)) for k in ("pnl", "cost", "exp", "var", "traded", "gross")}
    for t in range(T):
        x_new = trade_toward_aim(x, targets[t], r)
        dx = x_new - x
        x = x_new
        out["cost"][:, t] = 0.5 * lam * (dx ** 2 * sig2[t]).sum(axis=1)   # 1/2 dx' Lambda dx
        out["pnl"][:, t] = x @ s_next[t]
        out["exp"][:, t] = x @ alpha[t]                                  # expected P&L (true model)
        out["var"][:, t] = (x ** 2 * sig2[t]).sum(axis=1)
        out["traded"][:, t] = np.abs(dx).sum(axis=1)
        out["gross"][:, t] = np.abs(x).sum(axis=1)
    return {k: v[:, burn:] for k, v in out.items()}


def summarize(book, gamma):
    """Per-rate metrics: realized gross/net Sharpe, ex-ante utility, turnover, costs ($/yr)."""
    net = book["pnl"] - book["cost"]
    sd = lambda x: x.std(axis=1, ddof=1)                                 # noqa: E731
    return {
        "sharpe_gross": np.sqrt(252) * book["pnl"].mean(axis=1) / sd(book["pnl"]),
        "sharpe_net": np.sqrt(252) * net.mean(axis=1) / sd(net),
        # GP objective per day, using the true expected returns and risk (no sampling noise)
        "utility": 252 * (book["exp"] - 0.5 * gamma * book["var"] - book["cost"]).mean(axis=1),
        "exp_net": 252 * (book["exp"] - book["cost"]).mean(axis=1),
        "cost": 252 * book["cost"].mean(axis=1),
        "turnover": 252 * book["traded"].mean(axis=1) / book["gross"].mean(axis=1),
        "gross": book["gross"].mean(axis=1),
    }


def best_rate(rates, values):
    """Arg-max of a curve on a log grid, refined by a parabola through the top 3 points."""
    i = int(np.argmax(values))
    if 0 < i < len(rates) - 1:
        lr, v = np.log(rates[i - 1:i + 2]), values[i - 1:i + 2]
        c = np.polyfit(lr, v, 2)
        if c[0] < 0:
            return float(np.exp(-c[1] / (2 * c[0])))
    return float(rates[i])


def main():
    ctx = utils.setup(__file__, "Lab 15: trading toward the aim (Garleanu-Pedersen)")
    n_stocks, n_days, n_rates = (100, 500, 12) if ctx.smoke else (200, 2520, 25)
    half_lives = [1, 5, 20, 60]                 # days
    ic = 0.01                                   # same daily IC for every signal
    burn = 120                                  # days dropped before measuring (positions start at 0)
    gamma = 2e-7                                # risk aversion, 1/$ (gives a ~$0.5B gross book)
    # cost: price impact lam * sigma^2 * dx; lam chosen so that trading $1M of a stock with 1.7%
    # daily specific vol moves it ~10 bps (cost ~5 bps). Stylized; see README.
    lam = 1e-3 / (0.017 ** 2 * 1e6)
    rates = np.logspace(-2, 0, n_rates)

    alphas = tuple(PlantedAlpha(f"hl{h}", ic=ic, half_life=h, horizon_decay=0.5 ** (1 / h))
                   for h in half_lives)
    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, alphas=alphas, seed=ctx.seed)
    S = m.specific_returns.to_numpy()
    s_next = np.vstack([S[1:], np.zeros((1, n_stocks))])           # return of day t+1, at t
    vol = m.specific_vol.to_numpy()
    vol_next = np.vstack([vol[1:], vol[-1:]])                      # tomorrow's vol: known at t
    sig2 = vol_next ** 2
    phis = {h: 1 - 0.5 ** (1 / h) for h in half_lives}
    sig_alpha = {h: m.alpha_loadings[f"hl{h}"] * vol_next * np.nan_to_num(m.alphas[f"hl{h}"].to_numpy())
                 for h in half_lives}                              # TRUE E_t[s_{t+1}] per signal
    measured_ic = {h: float(simulate.cross_sectional_ic(m.alphas[f"hl{h}"],
                                                        m.forward_returns(1, specific=True)).mean())
                   for h in half_lives}
    r_gp = gp_trade_rate(gamma, lam)

    # ------------------------------------------------ E1: trade-rate sweep for each half-life
    curves = {}
    for h in half_lives:
        alpha = sig_alpha[h]
        markowitz = alpha / (gamma * sig2)
        aim = aim_portfolio([alpha], [phis[h]], sig2, gamma, lam)
        for target_name, target in (("aim", aim), ("markowitz", markowitz)):
            curves[(h, target_name)] = summarize(run_books(target, sig2, alpha, s_next, rates, gamma,
                                                           lam, burn), gamma)
        full = summarize(run_books(markowitz, sig2, alpha, s_next, [1.0], gamma, lam, burn), gamma)
        curves[(h, "full")] = full

    # ------------------------------------------------ E2: optimal rate vs cost level
    cost_mults = [0.25, 1.0, 4.0] if ctx.smoke else [0.0625, 0.25, 1.0, 4.0, 16.0]
    cost_sweep = []
    for cm in cost_mults:
        lam_c = lam * cm
        for h in half_lives:
            aim = aim_portfolio([sig_alpha[h]], [phis[h]], sig2, gamma, lam_c)
            s = summarize(run_books(aim, sig2, sig_alpha[h], s_next, rates, gamma, lam_c, burn), gamma)
            cost_sweep.append(dict(cost_mult=cm, half_life=h, gp_rate=gp_trade_rate(gamma, lam_c),
                                   grid_best_rate=best_rate(rates, s["utility"])))

    # ------------------------------------------------ E3: combined fast + slow signal
    combo = [5, 60]
    alpha_c = sig_alpha[combo[0]] + sig_alpha[combo[1]]
    markowitz_c = alpha_c / (gamma * sig2)
    aim_c = aim_portfolio([sig_alpha[h] for h in combo], [phis[h] for h in combo], sig2, gamma, lam)
    r_myopic = gamma / (gamma + lam)            # one-period optimum: x = argmax of today's utility
    rules = {
        "Full rebalance to Markowitz": (markowitz_c, 1.0),
        "Myopic cost-aware (rate g/(g+lam))": (markowitz_c, r_myopic),
        "Toward Markowitz at GP rate": (markowitz_c, r_gp),
        "Garleanu-Pedersen (aim, GP rate)": (aim_c, r_gp),
    }
    combo_res, paths = {}, {}
    for name, (target, rate) in rules.items():
        book = run_books(target, sig2, alpha_c, s_next, [rate], gamma, lam, burn)
        combo_res[name] = {k: float(v[0]) for k, v in summarize(book, gamma).items()}
    # position path of one stock with a strong slow signal (re-run the rule for that one name)
    stock = int(np.argmax(np.abs(m.alphas[f"hl{combo[1]}"].to_numpy()[burn:burn + 200]).mean(axis=0)))
    window = slice(burn, burn + (120 if not ctx.smoke else 80))
    for name, (target, rate) in rules.items():
        x, path = 0.0, []
        for t in range(window.stop):
            x = trade_toward_aim(x, target[t, stock], rate)
            path.append(x)
        paths[name] = np.array(path)[window]
    paths["Markowitz target"] = markowitz_c[window, stock]
    paths["GP aim"] = aim_c[window, stock]

    # ------------------------------------------------ plot 1: net Sharpe vs trade rate
    hl_colors = {1: "#eb6834", 5: "#eda100", 20: "#1baf7a", 60: "#2a78d6"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    best_sr = max(curves[(h, t)]["sharpe_net"].max() for h in half_lives for t in ("aim", "markowitz"))
    y_floor = -4.0
    for ax, target_name, title in ((axes[0], "aim", "Trading toward the GP aim"),
                                   (axes[1], "markowitz", "Trading toward the Markowitz portfolio")):
        for h in half_lives:
            c = curves[(h, target_name)]
            ax.plot(rates, c["sharpe_net"], color=hl_colors[h], lw=2, label=f"half-life {h} d")
            i = int(np.argmax(c["sharpe_net"]))
            ax.plot(rates[i], c["sharpe_net"][i], "o", color=hl_colors[h], ms=8, mec="white", mew=1.5)
        ax.axvline(r_gp, color="0.3", ls="--", lw=1.2)
        ax.text(r_gp * 0.93, y_floor + 0.2, f"GP rate a/lam = {r_gp:.2f}", fontsize=8.5, color="0.3",
                rotation=90, va="bottom", ha="right")
        worst = min(curves[(h, target_name)]["sharpe_net"][-1] for h in half_lives)
        if worst < y_floor:
            ax.annotate(f"rate 1 (jump to target), half-life 1 d:\nnet Sharpe {worst:.1f} (off scale)",
                        xy=(1.0, y_floor), xytext=(0.011, y_floor + 1.1), fontsize=8.5,
                        arrowprops=dict(arrowstyle="->", color="0.3"))
        ax.set_xscale("log")
        ax.set_xlabel("trade rate: fraction of the gap closed per day (log scale)")
        ax.set_title(title, fontsize=11)
        ax.axhline(0, color="0.5", lw=0.8)
    axes[0].set_ylabel("net Sharpe ratio (annualized, after quadratic costs)")
    axes[0].set_ylim(y_floor, best_sr + 0.8)
    axes[0].legend(loc="lower left", fontsize=9, bbox_to_anchor=(0.0, 0.22))
    fig.suptitle(f"Net Sharpe vs trade rate, {n_stocks} stocks, IC {ic} for every signal; dots = best rate "
                 "(synthetic data)", fontweight="bold")
    fig.subplots_adjust(top=0.86, wspace=0.06)
    utils.save_fig(ctx, fig, "net-sharpe-vs-rate")

    # ------------------------------------------------ plot 2: position paths + rate vs cost
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.5, 1]})
    days = np.arange(len(paths["GP aim"]))
    ax1.plot(days, paths["Markowitz target"] / 1e6, color="0.7", lw=1, label="Markowitz target (full rebalance)")
    ax1.plot(days, paths["GP aim"] / 1e6, color="#eda100", lw=1.5, label="GP aim")
    ax1.plot(days, paths["Garleanu-Pedersen (aim, GP rate)"] / 1e6, color="#2a78d6", lw=2.2,
             label=f"GP position (rate {r_gp:.2f}/day)")
    ax1.plot(days, paths["Myopic cost-aware (rate g/(g+lam))"] / 1e6, color="#eb6834", lw=2, ls="--",
             label=f"myopic cost-aware (rate {r_myopic:.3f}/day)")
    ax1.axhline(0, color="0.5", lw=0.8)
    ax1.set_xlabel("trading day")
    ax1.set_ylabel("position in one stock ($M)")
    ax1.set_title(f"Position paths, signal = half-life {combo[0]} d + {combo[1]} d", fontsize=11)
    ax1.legend(fontsize=8, loc="best")
    cs = cost_sweep
    lam_rel = np.array(cost_mults)
    ax2.plot(lam_rel, [gp_trade_rate(gamma, lam * c) for c in lam_rel], "k-", lw=2,
             label="closed form a/lam")
    for j, h in enumerate(half_lives):          # small horizontal offsets so the dots do not hide
        pts = [(d["cost_mult"] * 1.13 ** (j - 1.5), d["grid_best_rate"]) for d in cs if d["half_life"] == h]
        ax2.plot(*zip(*pts), "o", color=hl_colors[h], ms=7, mec="white", label=f"grid search, half-life {h} d")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_yticks([0.05, 0.1, 0.2, 0.5], ["0.05", "0.1", "0.2", "0.5"])
    ax2.minorticks_off()
    ax2.set_xlabel("cost multiplier (1 = base: ~10 bps impact per $1M)")
    ax2.set_ylabel("utility-maximizing trade rate per day")
    ax2.set_title("Optimal rate depends on costs, not half-life", fontsize=11)
    ax2.legend(fontsize=8)
    fig.suptitle("Trading toward the aim (synthetic data, quadratic costs)", fontweight="bold")
    fig.subplots_adjust(top=0.86, wspace=0.28)
    utils.save_fig(ctx, fig, "position-paths")

    # ------------------------------------------------ results
    res = {"n_stocks": n_stocks, "n_days": n_days,
           "gamma_per_million_usd": gamma * 1e6, "lam_per_million_usd": lam * 1e6,
           "gp_trade_rate": r_gp, "myopic_trade_rate": r_myopic,
           "measured_ic": {f"hl{h}": measured_ic[h] for h in half_lives}}
    for h in half_lives:
        ca, cmk, cf = curves[(h, "aim")], curves[(h, "markowitz")], curves[(h, "full")]
        i_gp = int(np.argmin(np.abs(np.log(rates / r_gp))))
        res[f"hl{h}"] = {
            "sharpe_gross_full_rebalance": float(cf["sharpe_gross"][0]),
            "sharpe_net_full_rebalance": float(cf["sharpe_net"][0]),
            "sharpe_net_gp": float(ca["sharpe_net"][i_gp]),
            "sharpe_net_best_toward_markowitz": float(cmk["sharpe_net"].max()),
            "best_rate_utility_aim": best_rate(rates, ca["utility"]),
            "best_rate_utility_markowitz": best_rate(rates, cmk["utility"]),
            "best_rate_sharpe_aim": float(rates[np.argmax(ca["sharpe_net"])]),
            "best_rate_sharpe_markowitz": float(rates[np.argmax(cmk["sharpe_net"])]),
            "utility_musd_gp": float(ca["utility"][i_gp] / 1e6),
            "utility_musd_best_toward_markowitz": float(cmk["utility"].max() / 1e6),
            "utility_musd_full_rebalance": float(cf["utility"][0] / 1e6),
        }
    res["cost_sweep"] = cost_sweep
    res["combined_signal_half_lives"] = combo
    res["combined_signal"] = {
        name: {"sharpe_gross": r["sharpe_gross"], "sharpe_net": r["sharpe_net"],
               "utility_musd_per_year": r["utility"] / 1e6, "expected_net_pnl_musd_per_year": r["exp_net"] / 1e6,
               "cost_musd_per_year": r["cost"] / 1e6, "turnover_x_per_year": r["turnover"],
               "avg_gross_book_musd": r["gross"] / 1e6}
        for name, r in combo_res.items()}
    utils.write_results(ctx, res)

    print(f"\n{n_stocks} stocks x {n_days} days; gamma {gamma:.1e}/$, lam {lam:.2e}/$ -> GP rate "
          f"a/lam = {r_gp:.3f}/day (myopic {r_myopic:.3f})")
    print(f"{'half-life':>9}{'IC':>7}{'net SR full':>12}{'net SR GP':>10}{'best SR->Mkw':>13}"
          f"{'rate*(aim)':>11}{'rate*(Mkw)':>11}")
    for h in half_lives:
        r = res[f"hl{h}"]
        print(f"{h:>8}d{measured_ic[h]:>7.4f}{r['sharpe_net_full_rebalance']:>12.2f}{r['sharpe_net_gp']:>10.2f}"
              f"{r['sharpe_net_best_toward_markowitz']:>13.2f}{r['best_rate_utility_aim']:>11.3f}"
              f"{r['best_rate_utility_markowitz']:>11.3f}")
    print("(rate* = utility-maximizing rate found by grid search; GP theory says rate*(aim) = "
          f"{r_gp:.3f} for every half-life)")
    print("\nCost sweep: GP rate vs grid-search rate (aim), averaged over half-lives")
    for cm in cost_mults:
        rows = [d for d in cost_sweep if d["cost_mult"] == cm]
        print(f"  cost x{cm:<6g} GP {rows[0]['gp_rate']:.3f}   grid "
              + " ".join(f"{d['grid_best_rate']:.3f}" for d in rows))
    print(f"\nCombined signal (half-lives {combo}):")
    for name, r in combo_res.items():
        print(f"  {name:<37} net SR {r['sharpe_net']:>6.2f}  gross SR {r['sharpe_gross']:>5.2f}  "
              f"utility ${r['utility'] / 1e6:>6.1f}M/yr  costs ${r['cost'] / 1e6:>5.1f}M/yr  "
              f"turnover {r['turnover']:>5.1f}x/yr")


if __name__ == "__main__":
    main()
