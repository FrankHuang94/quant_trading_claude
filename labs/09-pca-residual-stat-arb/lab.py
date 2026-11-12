"""Lab 09: PCA-residual statistical arbitrage (Avellaneda & Lee 2010 style).

What it demonstrates
  * The Avellaneda & Lee (2010) recipe on a simulated 500-stock market that has a real,
    known short-term reversal planted in its specific returns (reversal_strength > 0):
      1. rolling PCA of the 252-day correlation matrix -> 15 "eigenportfolios" (statistical factors);
      2. regress each stock's last 60 daily returns on the eigenportfolio returns -> residuals;
      3. model the cumulative residual as an Ornstein-Uhlenbeck (OU) process, fitted as an AR(1),
         and compute the s-score = (X - m) / sigma_eq (how many equilibrium standard deviations
         the stock is away from its fitted mean);
      4. trade bands: open long below -1.25, open short above +1.25, close longs above -0.50,
         close shorts below +0.75; only stocks whose fitted mean-reversion time is < 30 days;
      5. equal-size positions, net dollar exposure hedged with an index basket (dollar-neutral).
  * The same s-score machinery on two other residual definitions: sector "ETF" residuals (one
    regression on the stock's cap-weighted sector index, as in the paper's ETF variant) and an
    ORACLE factor model that uses the simulator's true exposures.
  * Truth check: how well PCA residuals match the true specific returns, and the IC of the
    s-score vs the planted reversal IC.
  * Pitfalls: (1) the gross Sharpe is high but the strategy holds positions for days and turns
    the book over many times a year, so costs take most of it and capacity is limited;
    (2) more factors are not automatically better (sensitivity to the number of PCA factors).

Supports: docs/02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md
          (also: risk-models, short-term-cross-sectional-reversal)

Run: python labs/09-pca-residual-stat-arb/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Single-threaded BLAS: the matrices are small, and multi-threading only slows things down
# when several labs run at once. Must be set before numpy is imported.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import utils, simulate  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

REVERSAL_STRENGTH = 0.04       # planted IC of -(5-day specific return) for the next day (stylized, strong)
N_FACTORS = 15                 # number of PCA eigenportfolios (statistical factors)
CORR_WINDOW = 252              # days for the correlation matrix
RESID_WINDOW = 60              # days for the residual regression and the OU fit
PCA_REFIT_EVERY = 5            # re-estimate the eigenportfolios weekly (saves time)
BOOK_USD = 10e6                # capital of the headline book; each open position is POSITION_SIZE of it
POSITION_SIZE = 0.01           # 1% of capital per open position (gross varies with # positions)
IMPACT_COEF = 0.5              # square-root impact coefficient Y (stylized; same as Lab 16)
BORROW_BPS_PER_YEAR = 35.0     # general-collateral borrow fee on shorts (stylized)
BOOK_SIZES_USD = [3e6, 1e7, 3e7, 1e8, 3e8, 1e9]
FLAT_COSTS_BPS = [0.0, 2.0, 5.0, 10.0]
COLORS = {"pca": "#2a78d6", "etf": "#eb6834", "oracle": "#1baf7a", "grey": "0.45"}


# =====================================================================================
# === CORE ALGORITHM ===
# Arrays are (days x stocks), oldest row first, last row = today (close of day t).
# =====================================================================================

def pca_residuals(returns: np.ndarray, n_factors: int = 15, resid_window: int = 60,
                  eigenportfolios: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Residual returns of each stock vs the top PCA eigenportfolios (Avellaneda & Lee 2010).

    returns: (corr_window x N), e.g. the last 252 days. Steps:
      1. correlation matrix of standardized returns -> top `n_factors` eigenvectors v_j;
      2. eigenportfolio weights Q_ij = v_ij / sigma_i  (inverse-vol weights along each eigenvector);
      3. factor returns F = R Q over the last `resid_window` days; regress each stock on F with an
         intercept (the stock's drift); residual = what the factors and drift do not explain.
    Pass `eigenportfolios` (a Q from an earlier call) to skip steps 1-2 between PCA refits.
    Returns ((resid_window x N) residuals, each column summing to zero; Q).
    """
    Q = eigenportfolios
    if Q is None:
        sigma = returns.std(axis=0, ddof=1)
        Y = (returns - returns.mean(axis=0)) / sigma         # standardized returns
        eigval, U = np.linalg.eigh(Y @ Y.T)                  # days x days Gram matrix: cheaper than N x N
        top = np.argsort(eigval)[::-1][:n_factors]
        V = Y.T @ U[:, top] / np.sqrt(eigval[top])           # = top eigenvectors of the correlation matrix
        Q = V / sigma[:, None]                               # eigenportfolio weights (N x k)
    R = returns[-resid_window:]
    X = np.column_stack([np.ones(resid_window), R @ Q])      # intercept + factor returns
    coef = np.linalg.solve(X.T @ X, X.T @ R)                 # OLS for all stocks at once
    return R - X @ coef, Q


def ou_sscore(residuals: np.ndarray, max_reversion_days: float = 30.0, center: bool = True) -> np.ndarray:
    """s-score of each stock from its residual returns (L x N), via an OU process fitted as AR(1).

    X_t = cumulative residual;  X_{t+1} = a + b X_t + zeta  (OLS per stock)
    kappa = -ln(b) * 252 (speed),  m = a / (1 - b) (equilibrium level),
    sigma_eq = sqrt(var(zeta) / (1 - b^2)) (equilibrium std),  s = (X_today - m) / sigma_eq.
    Stocks whose mean-reversion time 252/kappa exceeds `max_reversion_days` get NaN (not traded).
    center: subtract the cross-sectional mean of m (a common refinement that keeps longs and
    shorts balanced when all residuals drift the same way).
    """
    X = np.cumsum(residuals, axis=0)
    x0, x1 = X[:-1], X[1:]
    d0, d1 = x0 - x0.mean(axis=0), x1 - x1.mean(axis=0)
    b = (d0 * d1).sum(axis=0) / (d0 ** 2).sum(axis=0)       # AR(1) slope per stock
    a = x1.mean(axis=0) - b * x0.mean(axis=0)
    zeta = x1 - (a + b * x0)
    ok = (b > 0) & (b < 1)
    b_ok = np.where(ok, b, 0.5)                               # placeholder for invalid fits
    m = a / (1 - b_ok)
    sigma_eq = np.sqrt(zeta.var(axis=0, ddof=1) / (1 - b_ok ** 2))
    if center:
        m = m - np.mean(m[ok]) if ok.any() else m
    s = (X[-1] - m) / sigma_eq
    reversion_days = 252.0 / (-np.log(b_ok) * 252.0)          # = 1 / kappa, in trading days
    return np.where(ok & (reversion_days < max_reversion_days), s, np.nan)


def sscore_positions(s: np.ndarray, prev: np.ndarray, s_open: float = 1.25,
                     s_close_long: float = 0.50, s_close_short: float = 0.75) -> np.ndarray:
    """Avellaneda-Lee bang-bang rule: today's position (+1 long, -1 short, 0 flat) per stock.

    open long if s < -s_open; open short if s > +s_open;
    close a long once s > -s_close_long; close a short once s < +s_close_short.
    A stock whose s-score is NaN (no valid OU fit) is closed.
    """
    pos = prev.copy()
    pos[(prev == 0) & (s < -s_open)] = 1
    pos[(prev == 0) & (s > s_open)] = -1
    pos[(prev == 1) & (s > -s_close_long)] = 0
    pos[(prev == -1) & (s < s_close_short)] = 0
    pos[np.isnan(s)] = 0
    return pos


# === END CORE ALGORITHM ===
# =====================================================================================


def etf_residuals(returns: np.ndarray, sector_index: np.ndarray, resid_window: int = 60) -> np.ndarray:
    """A&L 'ETF' variant: regress each stock on its own sector index (with intercept)."""
    R, E = returns[-resid_window:], sector_index[-resid_window:]
    Rc, Ec = R - R.mean(axis=0), E - E.mean(axis=0)
    beta = (Rc * Ec).sum(axis=0) / (Ec ** 2).sum(axis=0)
    return Rc - beta * Ec


def factor_model_residuals(returns: np.ndarray, exposures: np.ndarray) -> np.ndarray:
    """Daily cross-sectional regression on KNOWN exposures (the oracle factor model)."""
    pinv = np.linalg.pinv(exposures)                          # (k x N), exposures are constant here
    factor_ret = returns @ pinv.T                             # (days x k) estimated factor returns
    return returns - factor_ret @ exposures.T


def compute_sscores(R: np.ndarray, kind: str, start: int, n_factors: int = N_FACTORS,
                    sector_index: np.ndarray | None = None, oracle_resid: np.ndarray | None = None,
                    keep_resid: bool = False):
    """Rolling s-scores for days start..T-1 (NaN before). Optionally the latest-day PCA residual."""
    T, N = R.shape
    S = np.full((T, N), np.nan)
    last_resid = np.full((T, N), np.nan) if keep_resid else None
    for t in range(start, T):
        if kind == "pca":
            refit = (t - start) % PCA_REFIT_EVERY == 0          # re-estimate eigenportfolios weekly
            resid, Q = pca_residuals(R[t - CORR_WINDOW + 1:t + 1], n_factors, RESID_WINDOW,
                                     eigenportfolios=None if refit else Q)
        elif kind == "etf":
            resid = etf_residuals(R[t - RESID_WINDOW + 1:t + 1], sector_index[t - RESID_WINDOW + 1:t + 1])
        else:                                                   # oracle factor model, drift removed
            u = oracle_resid[t - RESID_WINDOW + 1:t + 1]
            resid = u - u.mean(axis=0)
        S[t] = ou_sscore(resid)
        if keep_resid:
            last_resid[t] = resid[-1]
    return S, last_resid


def run_positions(S: np.ndarray) -> np.ndarray:
    """Apply sscore_positions day by day."""
    P = np.zeros_like(S)
    for t in range(1, len(S)):
        P[t] = sscore_positions(S[t], P[t - 1])
    return P


def book_weights(P: np.ndarray, position_size: float = POSITION_SIZE) -> np.ndarray:
    """Each open position = position_size of capital; net $ hedged with an equal-weight basket."""
    W = P * position_size
    return W - W.sum(axis=1, keepdims=True) / W.shape[1]     # dollar neutral


def pnl_with_costs(W: np.ndarray, R: np.ndarray, book_usd: float, spread_bps: np.ndarray,
                   adv_usd: np.ndarray, daily_vol: np.ndarray) -> dict:
    """Gross/net daily P&L (fraction of capital): half-spread + sqrt impact + borrow."""
    traded = np.abs(np.diff(W, axis=0, prepend=0.0))
    cost_rate = spread_bps / 2e4 + IMPACT_COEF * daily_vol * np.sqrt(traded * book_usd / adv_usd)
    tcost = (traded * cost_rate).sum(axis=1)
    held = np.vstack([np.zeros((1, W.shape[1])), W[:-1]])
    borrow = np.clip(-held, 0, None).sum(axis=1) * BORROW_BPS_PER_YEAR / 1e4 / 252
    gross = (held * R).sum(axis=1)
    return {"gross": gross, "tcost": tcost, "borrow": borrow, "net": gross - tcost - borrow,
            "turnover": traded.sum(axis=1), "gross_exposure": np.abs(W).sum(axis=1)}


def summarize(p: dict, sl: slice, P: np.ndarray) -> dict:
    g, n = p["gross"][sl], p["net"][sl]
    turn = p["turnover"][sl]
    opens = int(((P[1:] != 0) & (P[1:] != P[:-1])).sum())
    held_days = float((P != 0).sum() / max(opens, 1))
    return {
        "sharpe_gross": utils.annualized_sharpe(g), "sharpe_net": utils.annualized_sharpe(n),
        "ann_return_gross_pct": 100 * 252 * g.mean(), "ann_return_net_pct": 100 * 252 * n.mean(),
        "ann_vol_pct": 100 * np.sqrt(252) * g.std(),
        "avg_gross_exposure_x_capital": float(p["gross_exposure"][sl].mean()),
        "annual_turnover_x_capital": 252 * float(turn.mean()),
        "annual_turnover_x_gross": 252 * float(turn.mean()) / float(p["gross_exposure"][sl].mean()),
        "avg_cost_bps_per_dollar_traded": 1e4 * p["tcost"][sl].sum() / turn.sum(),
        "trading_cost_pct_per_year": 100 * 252 * p["tcost"][sl].mean(),
        "borrow_cost_pct_per_year": 100 * 252 * p["borrow"][sl].mean(),
        "avg_open_positions": float((P[sl] != 0).sum(axis=1).mean()),
        "avg_holding_days": held_days,
        "max_drawdown_net_pct": 100 * utils.max_drawdown(np.cumsum(n)),
    }


def main() -> None:
    ctx = utils.setup(__file__, "Lab 09: PCA-residual stat arb (Avellaneda-Lee)")
    n_stocks, n_days = (120, 420) if ctx.smoke else (500, 1260)
    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, seed=ctx.seed,
                                        reversal_strength=REVERSAL_STRENGTH)
    R = m.returns.to_numpy()
    T, N = R.shape
    start = CORR_WINDOW                                         # first day with a full window
    sl = slice(start + 1, T)
    print(f"Market: {N} stocks x {T} days (synthetic), planted reversal IC {REVERSAL_STRENGTH}; "
          f"trading days {T - start - 1}")

    # sector indices (cap-weighted, yesterday's caps) for the ETF variant, oracle residuals
    caps = m.market_cap.shift(1).bfill().to_numpy()
    sec = m.sector.to_numpy()
    sector_ret = np.zeros_like(R)
    for s_name in np.unique(sec):
        cols = sec == s_name
        idx = (R[:, cols] * caps[:, cols]).sum(axis=1) / caps[:, cols].sum(axis=1)
        sector_ret[:, cols] = idx[:, None]
    oracle_resid = factor_model_residuals(R, m.exposures.to_numpy())

    k_grid = [1, 5, 15, 30] if not ctx.smoke else [5, 15]
    if N_FACTORS not in k_grid:
        k_grid.append(N_FACTORS)
    S = {}
    S["pca"], pca_last = compute_sscores(R, "pca", start, keep_resid=True)
    S["etf"], etf_last = compute_sscores(R, "etf", start, sector_index=sector_ret, keep_resid=True)
    S["oracle"], oracle_last = compute_sscores(R, "oracle", start, oracle_resid=oracle_resid, keep_resid=True)
    S_k = {k: (S["pca"] if k == N_FACTORS else compute_sscores(R, "pca", start, n_factors=k)[0])
           for k in k_grid}

    # ------------------------------------------------------------ truth checks
    spec = m.specific_returns.to_numpy()
    fwd_spec = m.forward_returns(1, specific=True)

    def ic(sig: np.ndarray) -> float:
        df = pd.DataFrame(sig, index=m.dates, columns=m.tickers)
        return float(simulate.cross_sectional_ic(df, fwd_spec).iloc[sl].mean())

    def row_corr(a: np.ndarray, b: np.ndarray) -> float:
        a = a - a.mean(axis=1, keepdims=True)
        b = b - b.mean(axis=1, keepdims=True)
        return float(np.nanmean((a * b).sum(axis=1) / np.sqrt((a ** 2).sum(axis=1) * (b ** 2).sum(axis=1))))

    truth = {
        "planted_reversal_ic": REVERSAL_STRENGTH,
        "ic_oracle_5d_reversal_signal": ic(-simulate.reversal_signal(m).to_numpy()),
        "ic_minus_sscore_pca": ic(-S["pca"]),
        "ic_minus_sscore_etf": ic(-S["etf"]),
        "ic_minus_sscore_oracle": ic(-S["oracle"]),
        "corr_pca_residual_vs_true_specific": row_corr(pca_last[sl], spec[sl]),
        "corr_oracle_residual_vs_true_specific": row_corr(oracle_last[sl], spec[sl]),
        "corr_etf_residual_vs_true_specific": row_corr(etf_last[sl], spec[sl]),
        "share_of_stocks_tradeable_pca": float(np.isfinite(S["pca"][sl]).mean()),
    }

    # ------------------------------------------------------------ backtests
    daily_vol = m.returns.rolling(60, min_periods=20).std().bfill().to_numpy()
    adv = m.adv_usd.shift(1).bfill().to_numpy()
    spread = m.spread_bps.to_numpy()[None, :]
    P = {k: run_positions(v) for k, v in S.items()}
    W = {k: book_weights(v) for k, v in P.items()}
    pnl = {k: pnl_with_costs(W[k], R, BOOK_USD, spread, adv, daily_vol) for k in W}
    summary = {k: summarize(pnl[k], sl, P[k]) for k in pnl}
    by_size = {k: {b: utils.annualized_sharpe(pnl_with_costs(W[k], R, b, spread, adv, daily_vol)["net"][sl])
                   for b in BOOK_SIZES_USD} for k in W}
    by_k = {}
    for k, Sk in S_k.items():
        Pk = run_positions(Sk)
        pk = pnl_with_costs(book_weights(Pk), R, BOOK_USD, spread, adv, daily_vol)
        by_k[k] = {"sharpe_gross": utils.annualized_sharpe(pk["gross"][sl]),
                   "sharpe_net": utils.annualized_sharpe(pk["net"][sl]),
                   "ic_minus_sscore": ic(-Sk)}
    p = pnl["pca"]
    breakeven_bps = {k: 1e4 * (v["gross"][sl] - v["borrow"][sl]).mean() / v["turnover"][sl].mean()
                     for k, v in pnl.items()}
    flat_sharpe = {f"{c:g}bps": utils.annualized_sharpe((p["gross"] - p["borrow"] - c / 1e4 * p["turnover"])[sl])
                   for c in FLAT_COSTS_BPS}

    # ------------------------------------------------------------ print
    print("\nTruth checks:")
    print(f"  corr(residual, true specific return): PCA-{N_FACTORS} {truth['corr_pca_residual_vs_true_specific']:.3f}, "
          f"sector ETF {truth['corr_etf_residual_vs_true_specific']:.3f}, "
          f"oracle factor model {truth['corr_oracle_residual_vs_true_specific']:.3f}")
    print(f"  IC of -s-score vs next-day specific return: PCA {truth['ic_minus_sscore_pca']:.4f}, "
          f"ETF {truth['ic_minus_sscore_etf']:.4f}, oracle {truth['ic_minus_sscore_oracle']:.4f}; "
          f"planted 5-day reversal {REVERSAL_STRENGTH} (oracle 5-day signal {truth['ic_oracle_5d_reversal_signal']:.4f})")
    print(f"\nBacktests: ${BOOK_USD / 1e6:.0f}M capital, {POSITION_SIZE:.0%} per position, impact coef "
          f"{IMPACT_COEF}, borrow {BORROW_BPS_PER_YEAR:.0f} bps/yr")
    print(f"  {'residuals':<10}{'SR gross':>9}{'SR net':>8}{'ret g%':>8}{'ret n%':>8}{'gross x':>8}"
          f"{'turn x/yr':>10}{'hold d':>7}{'cost bps':>9}")
    for k, s in summary.items():
        print(f"  {k:<10}{s['sharpe_gross']:9.2f}{s['sharpe_net']:8.2f}{s['ann_return_gross_pct']:8.1f}"
              f"{s['ann_return_net_pct']:8.1f}{s['avg_gross_exposure_x_capital']:8.2f}"
              f"{s['annual_turnover_x_capital']:10.1f}{s['avg_holding_days']:7.1f}"
              f"{s['avg_cost_bps_per_dollar_traded']:9.1f}")
    print("  break-even flat cost (bps per $ traded): " + ", ".join(f"{k} {v:.1f}" for k, v in breakeven_bps.items()))
    print("  PCA net Sharpe at a flat cost per $ traded: " + ", ".join(f"{k} {v:.2f}" for k, v in flat_sharpe.items()))
    for k, v in by_size.items():
        print(f"  {k} net Sharpe by capital: " + ", ".join(f"${b / 1e6:,.0f}M {x:.2f}" for b, x in v.items()))
    print("  PCA by number of factors (gross / net Sharpe): "
          + ", ".join(f"k={k}: {v['sharpe_gross']:.2f}/{v['sharpe_net']:.2f}" for k, v in sorted(by_k.items())))

    # ------------------------------------------------------------ plots
    # (1) s-score of one actively traded stock with its positions, over ~1 year
    trades_per_stock = (np.diff(P["pca"], axis=0) != 0).sum(axis=0)
    j = int(np.argsort(trades_per_stock)[len(trades_per_stock) // 2 + len(trades_per_stock) // 4])
    lo = max(start + 1, T - 260)
    d = m.dates[lo:]
    sj, pj = S["pca"][lo:, j], P["pca"][lo:, j]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.fill_between(d, -3.5, 3.5, where=pj > 0, color=COLORS["pca"], alpha=0.12, lw=0, label="long position")
    ax.fill_between(d, -3.5, 3.5, where=pj < 0, color=COLORS["etf"], alpha=0.14, lw=0, label="short position")
    ax.plot(d, sj, color="0.15", lw=1.4, label="s-score (PCA-15 residual, OU fit)")
    for lvl, ls, lab in ((1.25, "--", "open short / long at +/-1.25"), (-1.25, "--", None),
                         (0.75, ":", "close short at +0.75, close long at -0.50"), (-0.50, ":", None)):
        ax.axhline(lvl, color="0.35", lw=1.0, ls=ls, label=lab)
    ax.set_ylim(-3.5, 3.5)
    ax.set_ylabel("s-score (equilibrium std devs)")
    ax.set_title(f"Avellaneda-Lee s-score and positions for one stock ({m.tickers[j]}, {m.sector.iloc[j]}), "
                 f"last year of the sample\nsynthetic data; gaps in the line = fitted mean reversion slower than "
                 "30 days, not traded", fontsize=10)
    ax.legend(loc="upper left", ncol=3, fontsize=8)
    fig.tight_layout()
    utils.save_fig(ctx, fig, "sscore")

    # (2) cumulative P&L gross vs net for the three residual models + capacity
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.6, 1]})
    dd = m.dates[sl]
    labels = {"pca": f"PCA ({N_FACTORS} factors)", "etf": "sector ETF", "oracle": "oracle factor model"}
    for k, lab in labels.items():
        s = summary[k]
        ax.plot(dd, 100 * np.cumsum(pnl[k]["gross"][sl]), color=COLORS[k], lw=1.3, ls="--",
                label=f"{lab}: gross (Sharpe {s['sharpe_gross']:.2f})")
        ax.plot(dd, 100 * np.cumsum(pnl[k]["net"][sl]), color=COLORS[k], lw=2.0,
                label=f"{lab}: net (Sharpe {s['sharpe_net']:.2f})")
        ax2.plot(np.array(BOOK_SIZES_USD) / 1e6, list(by_size[k].values()), "o-", color=COLORS[k], lw=2,
                 ms=6, label=lab)
    ax.axhline(0, color="0.3", lw=0.8)
    ax.set_ylabel("cumulative P&L, % of capital")
    ax.set_title(f"Gross vs net of half-spread + sqrt impact + borrow, ${BOOK_USD / 1e6:.0f}M capital,\n"
                 f"{POSITION_SIZE:.0%} of capital per position, dollar neutral", fontsize=10)
    ax.legend(loc="upper left", fontsize=8.2)
    ax2.set_xscale("log")
    ax2.axhline(0, color="0.3", lw=0.8)
    ax2.set_xlabel("capital, $M (log scale)")
    ax2.set_ylabel("annualized net Sharpe")
    ax2.set_title("Capacity: net Sharpe vs capital", fontsize=10)
    ax2.legend(loc="lower left", fontsize=8.5)
    fig.suptitle(f"Residual mean-reversion (Avellaneda-Lee): synthetic data, planted 5-day reversal IC "
                 f"{REVERSAL_STRENGTH}", fontsize=11, fontweight="bold")
    fig.tight_layout()
    utils.save_fig(ctx, fig, "pnl-gross-vs-net")

    # ------------------------------------------------------------ results
    keep = ("sharpe_gross", "sharpe_net", "ann_return_gross_pct", "ann_return_net_pct",
            "avg_gross_exposure_x_capital", "annual_turnover_x_capital", "annual_turnover_x_gross",
            "avg_holding_days", "avg_open_positions", "avg_cost_bps_per_dollar_traded",
            "trading_cost_pct_per_year", "borrow_cost_pct_per_year", "max_drawdown_net_pct")
    utils.write_results(ctx, {
        "n_stocks": N, "n_days": T, "trading_days": T - start - 1,
        "capital_usd": BOOK_USD, "position_size_of_capital": POSITION_SIZE,
        "impact_coef": IMPACT_COEF, "borrow_bps_per_year": BORROW_BPS_PER_YEAR,
        "n_factors": N_FACTORS, "corr_window": CORR_WINDOW, "resid_window": RESID_WINDOW,
        "truth": truth,
        "pca_sharpe_gross": summary["pca"]["sharpe_gross"],
        "pca_sharpe_net_10m": summary["pca"]["sharpe_net"],
        "pca_sharpe_net_100m": by_size["pca"][1e8],
        "oracle_sharpe_gross": summary["oracle"]["sharpe_gross"],
        "oracle_sharpe_net_10m": summary["oracle"]["sharpe_net"],
        "etf_sharpe_gross": summary["etf"]["sharpe_gross"],
        "etf_sharpe_net_10m": summary["etf"]["sharpe_net"],
        "pca_annual_turnover_x_gross": summary["pca"]["annual_turnover_x_gross"],
        "pca_avg_holding_days": summary["pca"]["avg_holding_days"],
        "breakeven_flat_cost_bps": breakeven_bps,
        "pca_net_sharpe_at_flat_cost": flat_sharpe,
        "models": {k: {kk: s[kk] for kk in keep} for k, s in summary.items()},
        "net_sharpe_by_capital_usd": {k: {f"{b:.0e}": x for b, x in v.items()} for k, v in by_size.items()},
        "pca_by_n_factors": {str(k): v for k, v in sorted(by_k.items())},
        "plot_stock": m.tickers[j],
    })


if __name__ == "__main__":
    main()
