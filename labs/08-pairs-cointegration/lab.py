"""Lab 08: pairs trading -- distance method vs Engle-Granger cointegration, with costs and breaks.

What it demonstrates
  * The two classic ways to pick pairs, run on a simulated 200-stock market with rolling
    12-month formation / 6-month trading periods (8 trading periods):
      - distance method (Gatev, Goetzmann & Rouwenhorst 2006): normalize each stock's total-return
        price to 1, pick the 20 pairs with the smallest sum of squared differences (SSD), trade the
        price gap (dollar neutral, hedge ratio 1);
      - cointegration (Engle & Granger 1987): among same-sector pairs, keep those whose OLS spread
        log P_A - beta log P_B passes an Engle-Granger test (statsmodels `coint`, p < 0.05), trade
        the 20 with the lowest p-values, with the estimated hedge ratio beta. Variants: trade
        EVERY pair with p < 0.05, and a two-step "SSD top 100, then test" screen.
    All trade the z-score of the spread: enter at |z| > 2.0, exit at |z| < 0.5, stop out at
    |z| > 4.0 (then sit out the rest of the period), and close everything at the period end.
  * The truth is known. In the base simulator, stocks in the same sector share factor exposures
    but their specific returns are independent, so NO natural pair is cointegrated. This lab
    PLANTS 8 cointegrated pairs on top of the simulated prices (stock B's log price is rebuilt as
    c + gamma * log P_A + an OU spread), and 4 of them BREAK partway (the spread drifts away
    for three months and never comes back: think merger, guidance shock, regulatory change).
  * Results and pitfalls: false discoveries when ~1,700 pairs are tested at 5%; low power (a
    10-day half-life spread often fails the test on one year of data); double-dipping (pre-
    screening by SSD and then testing on the same data inflates the pass rate far above 5%);
    the regime-break loss and what the stop-loss saves; gross vs net Sharpe with half-spread +
    square-root impact + borrow costs; and net Sharpe vs position size (capacity).

Supports: docs/02-strategies/c-statistical-arbitrage/pairs-trading-and-cointegration.md

Run: python labs/08-pairs-cointegration/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")          # small matrices: single-threaded BLAS is fastest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import utils, simulate  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from statsmodels.tsa.stattools import coint  # noqa: E402

FORMATION_DAYS = 252          # 12-month formation period (GGR)
TRADING_DAYS = 126            # 6-month trading period (GGR)
N_PAIRS = 20                  # pairs traded per period (GGR "top 20")
ENTRY_Z, EXIT_Z, STOP_Z = 2.0, 0.5, 4.0
P_VALUE = 0.05                # Engle-Granger screen
N_PLANTED, N_BREAKING = 8, 4  # planted cointegrated pairs; how many of them break partway
BREAK_DAYS, BREAK_DRIFT_SD = 60, 6.0   # a break = divergence of 6 equilibrium sd over 60 days
LEG_USD = 1e6                 # $ per leg at entry (headline); committed capital = N_PAIRS * 2 * LEG_USD
LEG_SIZES_USD = [2.5e5, 1e6, 4e6, 1.6e7]   # capacity sweep
IMPACT_COEF = 0.5             # square-root impact coefficient Y (stylized; same as Labs 09, 10, 16)
BORROW_BPS_PER_YEAR = 35.0    # general-collateral borrow fee on the short leg (stylized)
PRESCREEN = 100              # SSD pre-screen size for the two-step method
COLORS = {"distance": "#2a78d6", "coint_top20": "#eb6834", "coint_all": "#eda100",
          "two_step": "#e87ba4", "oracle": "#1baf7a"}
LABELS = {"distance": "distance (SSD top 20)", "coint_top20": "cointegration (top 20 by p-value)",
          "coint_all": "cointegration (every pair with p < 0.05)",
          "two_step": f"SSD top {PRESCREEN}, then cointegration p < 0.05", "oracle": "oracle (true pairs only)"}


# =====================================================================================
# === CORE ALGORITHM ===
# =====================================================================================

def ssd_distance(norm_prices: np.ndarray) -> np.ndarray:
    """Gatev-Goetzmann-Rouwenhorst distance: sum of squared differences between every pair of
    normalized price paths (days x N, each column starts at 1). Returns an N x N matrix."""
    sq = (norm_prices ** 2).sum(axis=0)
    ssd = sq[:, None] + sq[None, :] - 2.0 * norm_prices.T @ norm_prices   # sum_t (p_i - p_j)^2
    np.fill_diagonal(ssd, np.inf)
    return ssd


def hedge_ratio(log_a: np.ndarray, log_b: np.ndarray) -> tuple[float, float, np.ndarray]:
    """Engle-Granger step 1: OLS of log P_A on log P_B with an intercept.

    Returns (beta, alpha, spread) with spread = log_a - alpha - beta * log_b. Holding $1 of A
    against $beta of B earns (approximately) the change in this spread. Note the asymmetry:
    regressing B on A gives a different beta (not 1/beta) unless the fit is perfect.
    """
    X = np.column_stack([np.ones_like(log_b), log_b])
    (alpha, beta), *_ = np.linalg.lstsq(X, log_a, rcond=None)
    return float(beta), float(alpha), log_a - alpha - beta * log_b


def zscore_signals(z: np.ndarray, entry: float = 2.0, exit: float = 0.5, stop: float = 4.0) -> np.ndarray:
    """Daily position in the spread from its z-score (decided at each close).

    +1 = long the spread (long A, short B) when it is unusually LOW (z < -entry);
    -1 = short the spread when it is unusually HIGH (z > +entry);
    close when |z| < exit (converged); stop out when |z| > stop and stay flat for the rest of the
    trading period (the relationship may have broken). Flat on the last day.
    """
    pos = np.zeros(len(z), dtype=int)
    state, stopped = 0, False
    for t, zt in enumerate(z):
        if state == 0 and not stopped and entry < abs(zt) < stop:
            state = -1 if zt > 0 else 1                     # bet on convergence
        elif state != 0 and abs(zt) >= stop:
            state, stopped = 0, True                        # stop-loss
        elif (state == 1 and zt > -exit) or (state == -1 and zt < exit):
            state = 0                                       # converged: take profit
        pos[t] = state
    pos[-1] = 0
    return pos


# === END CORE ALGORITHM ===
# =====================================================================================


def plant_pairs(prices: np.ndarray, sector: np.ndarray, rng: np.random.Generator, n_days_min: int):
    """Rebuild stock B of N_PLANTED same-sector pairs so that log P_B = c + gamma log P_A + u_t.

    u is an OU spread (half-life 4-20 days, stationary sd 1.5-3.5%). For the first N_BREAKING pairs,
    from a random day on, the spread drifts away by BREAK_DRIFT_SD stationary sd over BREAK_DAYS
    days (a re-rating: one company's prospects change) and then wanders as a random walk (no more
    mean reversion). Returns (new prices, list of planted pair dicts). Stylized.
    """
    P = prices.copy()
    T, N = P.shape
    used: set[int] = set()
    planted = []
    sectors = np.unique(sector)
    while len(planted) < N_PLANTED:
        s = rng.choice(sectors)
        members = [i for i in np.flatnonzero(sector == s) if i not in used]
        if len(members) < 2:
            continue
        a, b = (int(x) for x in rng.choice(members, size=2, replace=False))
        used.update((a, b))
        gamma = rng.uniform(0.8, 1.2)
        half_life = rng.uniform(4, 20)
        sd_u = rng.uniform(0.015, 0.035)
        phi = 0.5 ** (1 / half_life)
        eps = rng.standard_normal(T) * sd_u * np.sqrt(1 - phi ** 2)
        breaks = len(planted) < N_BREAKING
        break_day = int(rng.integers(n_days_min, T - 40)) if breaks else T + 1
        drift = rng.choice([-1, 1]) * BREAK_DRIFT_SD * sd_u / BREAK_DAYS
        u = np.zeros(T)
        u[0] = rng.standard_normal() * sd_u
        for t in range(1, T):
            if t < break_day:
                u[t] = phi * u[t - 1] + eps[t]                           # OU: pulled back to 0
            elif t < break_day + BREAK_DAYS:
                u[t] = u[t - 1] + drift + eps[t]                         # steady divergence
            else:
                u[t] = u[t - 1] + eps[t]                                 # random walk: no anchor
        log_pb = np.log(P[0, b]) + gamma * (np.log(P[:, a]) - np.log(P[0, a])) + u - u[0]
        P[:, b] = np.exp(log_pb)
        planted.append({"a": a, "b": b, "gamma": gamma, "half_life": half_life, "sd_u": sd_u,
                        "break_day": break_day if breaks else None})
    return P, planted


def bh_count(pvals: np.ndarray, q: float = 0.05) -> np.ndarray:
    """Benjamini-Hochberg: boolean mask of discoveries at false discovery rate q."""
    n = len(pvals)
    order = np.argsort(pvals)
    ok = pvals[order] <= q * np.arange(1, n + 1) / n
    k = np.max(np.flatnonzero(ok)) + 1 if ok.any() else 0
    mask = np.zeros(n, dtype=bool)
    mask[order[:k]] = True
    return mask


def pair_window(P, logP, a, b, f0, f1, t1, method, stop=STOP_Z):
    """z-score path, hedge ratio and positions for one pair in one trading period."""
    days = np.arange(f1, t1)                                 # trading days (signals at each close)
    if method == "distance":
        form = P[f0:f1, [a, b]] / P[f0, [a, b]]
        sd = np.std(form[:, 0] - form[:, 1], ddof=1)
        norm = P[days][:, [a, b]] / P[f1 - 1, [a, b]]          # re-normalized at the period start
        z, beta = (norm[:, 0] - norm[:, 1]) / sd, 1.0
    else:
        beta, alpha, s_form = hedge_ratio(logP[f0:f1, a], logP[f0:f1, b])
        spread = logP[days, a] - alpha - beta * logP[days, b]
        z = (spread - s_form.mean()) / s_form.std(ddof=1)
    return days, z, beta, zscore_signals(z, ENTRY_Z, EXIT_Z, stop)


def pair_pnl(P, a, b, days, pos, beta, z, acc, trades, T):
    """Accumulate P&L of one pair-period into acc (units: $ per $1 of LEG size).

    At entry: $2/(1+beta) of A and $2*beta/(1+beta) of B (gross $2), shares then fixed until exit.
    """
    w_a, w_b = 2.0 / (1.0 + beta), 2.0 * beta / (1.0 + beta)
    n_a = n_b = 0.0
    res = {"gross": 0.0, "n_trades": 0, "n_stops": 0, "days_held": 0, "daily": np.zeros(T)}
    for k, d in enumerate(days):
        p = pos[k]
        prev = pos[k - 1] if k > 0 else 0
        if p != prev:
            if prev != 0:                                   # exit at today's close
                for i, n in ((a, n_a), (b, n_b)):
                    trades.append((d, abs(n) * P[d, i], i))
                res["n_stops"] += int(abs(z[k]) >= STOP_Z)
            if p != 0:                                      # enter at today's close
                n_a, n_b = p * w_a / P[d, a], -p * w_b / P[d, b]
                trades.append((d, w_a, a))
                trades.append((d, w_b, b))
                res["n_trades"] += 1
            else:
                n_a = n_b = 0.0
        if p != 0 and d + 1 < T:                            # hold over day d+1
            g = n_a * (P[d + 1, a] - P[d, a]) + n_b * (P[d + 1, b] - P[d, b])
            short_usd = -min(n_a * P[d, a], 0.0) - min(n_b * P[d, b], 0.0)
            acc["gross"][d + 1] += g
            acc["borrow"][d + 1] += short_usd * BORROW_BPS_PER_YEAR / 1e4 / 252
            res["gross"] += g
            res["daily"][d + 1] = g
            res["days_held"] += 1
    return res


def cost_series(trades: list, leg_usd: float, T: int, spread_bps, adv, vol) -> tuple[np.ndarray, float]:
    """Trading cost per day ($ per $1 of leg) at a given leg size; also total $ traded per $1."""
    out = np.zeros(T)
    traded = 0.0
    for d, unit, i in trades:
        usd = unit * leg_usd
        rate = spread_bps[i] / 2e4 + IMPACT_COEF * vol[d, i] * np.sqrt(usd / adv[d, i])
        out[d] += unit * rate
        traded += unit
    return out, traded


def main() -> None:
    ctx = utils.setup(__file__, "Lab 08: pairs trading, distance vs cointegration")
    n_stocks, n_days = (80, 504) if ctx.smoke else (200, 1260)
    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, seed=ctx.seed)
    rng = np.random.default_rng([ctx.seed, 8])
    sector = m.sector.to_numpy()
    P, planted = plant_pairs(m.prices.to_numpy(), sector, rng, n_days_min=FORMATION_DAYS + 40)
    logP = np.log(P)
    T, N = P.shape
    R = np.vstack([np.zeros((1, N)), P[1:] / P[:-1] - 1])
    vol = pd.DataFrame(R).rolling(60, min_periods=10).std().shift(1).fillna(0.02).to_numpy()  # known at t
    adv = m.adv_usd.shift(1).bfill().to_numpy()
    spread_bps = m.spread_bps.to_numpy()
    planted_key = {(p["a"], p["b"]): p for p in planted}
    planted_key.update({(p["b"], p["a"]): p for p in planted})
    print(f"Market: {N} stocks x {T} days (synthetic) + {N_PLANTED} planted cointegrated pairs "
          f"({N_BREAKING} break partway)")

    same_sector = [(i, j) for i in range(N) for j in range(i + 1, N) if sector[i] == sector[j]]
    windows = [(f0, f0 + FORMATION_DAYS, min(f0 + FORMATION_DAYS + TRADING_DAYS, T))
               for f0 in range(0, T - FORMATION_DAYS - 20, TRADING_DAYS)]
    methods = list(LABELS)
    acc = {k: {"gross": np.zeros(T), "borrow": np.zeros(T), "capital": np.full(T, np.nan)} for k in methods}
    trades = {k: [] for k in methods}
    records, screen_rows = [], []

    def truth(a, b, f1, t1):
        p = planted_key.get((a, b))
        if p is None:
            return "not cointegrated"
        bd = p["break_day"]
        if bd is not None and bd < f1:
            return "planted, broke earlier"
        return "planted, breaks this period" if bd is not None and bd < t1 else "planted, intact"

    for f0, f1, t1 in windows:
        # --- distance method: all pairs in the universe
        norm = P[f0:f1] / P[f0]
        ssd = ssd_distance(norm)
        iu = np.triu_indices(N, 1)
        top = np.argsort(ssd[iu])[:N_PAIRS]
        dist_pairs = [(int(iu[0][k]), int(iu[1][k])) for k in top]
        # --- two-step: distance pre-screen (fewer tests), then Engle-Granger
        pre = [(int(iu[0][k]), int(iu[1][k])) for k in np.argsort(ssd[iu])[:PRESCREEN]]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pv_pre = np.array([coint(logP[f0:f1, a], logP[f0:f1, b], trend="c", maxlag=1, autolag=None)[1]
                               for a, b in pre])
        beta_pre = np.array([hedge_ratio(logP[f0:f1, a], logP[f0:f1, b])[0] for a, b in pre])
        ok_pre = np.flatnonzero((pv_pre < P_VALUE) & (beta_pre > 0.25) & (beta_pre < 4.0))
        two_step = [pre[k] for k in ok_pre[np.argsort(pv_pre[ok_pre])][:N_PAIRS]]
        # --- Engle-Granger screen on same-sector pairs
        pv, betas = np.ones(len(same_sector)), np.zeros(len(same_sector))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for k, (a, b) in enumerate(same_sector):
                pv[k] = coint(logP[f0:f1, a], logP[f0:f1, b], trend="c", maxlag=1, autolag=None)[1]
                betas[k] = hedge_ratio(logP[f0:f1, a], logP[f0:f1, b])[0]
        sane = (betas > 0.25) & (betas < 4.0)                  # usable hedge ratios only
        passed = np.flatnonzero((pv < P_VALUE) & sane)
        bh = bh_count(pv) & sane
        coint_all = [same_sector[k] for k in passed]
        coint_top = [same_sector[k] for k in passed[np.argsort(pv[passed])][:N_PAIRS]]
        true_now = [(p["a"], p["b"]) for p in planted if p["break_day"] is None or p["break_day"] >= f1]
        is_true = np.array([truth(a, b, f1, t1).startswith("planted, intact") or
                            truth(a, b, f1, t1).startswith("planted, breaks") for a, b in same_sector])
        screen_rows.append({
            "formation_end": str(m.dates[f1 - 1].date()), "pairs_tested": len(same_sector),
            "pass_p05": int(len(passed)), "true_in_universe": len(true_now),
            "true_positives": int(is_true[passed].sum()), "false_positives": int((~is_true[passed]).sum()),
            "bh_discoveries": int(bh.sum()), "bh_true": int(is_true[bh].sum()),
            "distance_top20_true": int(sum(truth(a, b, f1, t1).startswith("planted, i") or
                                           truth(a, b, f1, t1).startswith("planted, b") for a, b in dist_pairs)),
        })
        is_true_pre = np.array([truth(a, b, f1, t1).startswith(("planted, intact", "planted, breaks"))
                                for a, b in pre])
        screen_rows[-1].update({"two_step_pass": int(len(ok_pre)), "two_step_true": int(is_true_pre[ok_pre].sum()),
                                "two_step_bh": int((bh_count(pv_pre) & (beta_pre > 0.25)).sum()),
                                "two_step_bh_true": int((bh_count(pv_pre) & is_true_pre).sum())})
        selections = {"distance": dist_pairs, "coint_top20": coint_top, "coint_all": coint_all,
                      "two_step": two_step, "oracle": true_now}
        for meth, pairs in selections.items():
            acc[meth]["capital"][f1 + 1:min(t1 + 1, T)] = 2.0 * max(len(pairs), 1)   # $ per $1 of leg
            for a, b in pairs:
                days, z, beta, pos = pair_window(P, logP, a, b, f0, f1, t1,
                                                 "distance" if meth == "distance" else "coint")
                res = pair_pnl(P, a, b, days, pos, beta, z, acc[meth], trades[meth], T)
                records.append({"method": meth, "window": str(m.dates[f1].date()), "a": a, "b": b,
                                "truth": truth(a, b, f1, t1), **res})

    # ------------------------------------------------------------ evaluate
    first = windows[0][1] + 1
    sl = slice(first, T)

    def evaluate(meth: str, leg_usd: float) -> dict:
        c, traded = cost_series(trades[meth], leg_usd, T, spread_bps, adv, vol)
        cap = acc[meth]["capital"]
        gross = np.nan_to_num(acc[meth]["gross"] / cap)
        net = np.nan_to_num((acc[meth]["gross"] - c - acc[meth]["borrow"]) / cap)
        return {"gross": gross, "net": net, "cost_total": float(c.sum()), "traded": traded}

    summary, series = {}, {}
    for meth in methods:
        e = evaluate(meth, LEG_USD)
        series[meth] = e
        recs = [r for r in records if r["method"] == meth]
        n_tr = sum(r["n_trades"] for r in recs)
        summary[meth] = {
            "sharpe_gross": utils.annualized_sharpe(e["gross"][sl]),
            "sharpe_net": utils.annualized_sharpe(e["net"][sl]),
            "ann_return_gross_pct": 100 * 252 * e["gross"][sl].mean(),
            "ann_return_net_pct": 100 * 252 * e["net"][sl].mean(),
            "avg_pairs_per_period": float(np.mean([len([r for r in recs if r["window"] == w])
                                                   for w in {r["window"] for r in recs}] or [0])),
            "round_trips": int(n_tr),
            "avg_holding_days": sum(r["days_held"] for r in recs) / max(n_tr, 1),
            "capital_in_use_share": sum(r["days_held"] for r in recs) / max(
                sum(len(range(f1, t1)) * len([r for r in recs if r["window"] == str(m.dates[f1].date())])
                    for f0, f1, t1 in windows), 1),
            "stop_outs": int(sum(r["n_stops"] for r in recs)),
            "avg_cost_bps_per_dollar_traded": 1e4 * e["cost_total"] / max(e["traded"], 1e-12),
            "annual_turnover_x_capital": e["traded"] / np.nanmean(acc[meth]["capital"]) / ((T - first) / 252),
            "max_drawdown_net_pct": 100 * utils.max_drawdown(np.cumsum(e["net"][sl])),
        }
        by_truth = {}
        for r in recs:
            by_truth[r["truth"]] = by_truth.get(r["truth"], 0.0) + r["gross"]
        mean_cap = float(np.nanmean(acc[meth]["capital"]))
        summary[meth]["gross_pnl_pct_of_capital_by_truth"] = {k: 100 * v / mean_cap for k, v in by_truth.items()}
        summary[meth]["pair_periods_by_truth"] = {k: sum(r["truth"] == k for r in recs) for k in by_truth}
    capacity = {meth: {f"{leg:.2e}": utils.annualized_sharpe(evaluate(meth, leg)["net"][sl])
                       for leg in LEG_SIZES_USD} for meth in ("distance", "coint_top20")}

    scr = {k: float(np.mean([r[k] for r in screen_rows])) for k in screen_rows[0] if k != "formation_end"}
    # regime breaks: P&L of the planted pairs (oracle selection) before vs after each break
    breaks = [r for r in records if r["method"] == "oracle" and r["truth"] == "planted, breaks this period"]
    intact = [r for r in records if r["method"] == "oracle" and r["truth"] == "planted, intact"]
    post = [float(r["daily"][planted_key[(r["a"], r["b"])]["break_day"]:].sum()) for r in breaks]
    post_no_stop = []                                       # same pair-periods without the stop-loss
    for r in breaks:
        w = next(w for w in windows if str(m.dates[w[1]].date()) == r["window"])
        days, z, beta, pos = pair_window(P, logP, r["a"], r["b"], *w, "coint", stop=np.inf)
        res = pair_pnl(P, r["a"], r["b"], days, pos, beta, z, {"gross": np.zeros(T), "borrow": np.zeros(T)}, [], T)
        post_no_stop.append(float(res["daily"][planted_key[(r["a"], r["b"])]["break_day"]:].sum()))
    pre = [float(r["daily"][:planted_key[(r["a"], r["b"])]["break_day"]].sum()) for r in breaks]
    regime = {
        "pair_periods_with_break": len(breaks),
        "post_break_gross_pnl_per_break_pct_of_leg": [100 * x for x in post],
        "post_break_gross_pnl_mean_pct_of_leg": 100 * float(np.mean(post)) if post else None,
        "post_break_gross_pnl_per_break_no_stop_pct_of_leg": [100 * x for x in post_no_stop],
        "post_break_gross_pnl_mean_no_stop_pct_of_leg": 100 * float(np.mean(post_no_stop)) if post else None,
        "pre_break_gross_pnl_mean_pct_of_leg": 100 * float(np.mean(pre)) if pre else None,
        "intact_pair_period_gross_pnl_mean_pct_of_leg": 100 * float(np.mean([r["gross"] for r in intact])) if intact else None,
        "stop_outs_in_break_periods": int(sum(r["n_stops"] for r in breaks)),
        "stop_outs_in_intact_pair_periods": int(sum(r["n_stops"] for r in intact)),
        "post_break_loss_as_pct_of_oracle_total_gross": 100 * float(np.sum(post)) / max(
            float(sum(r["gross"] for r in breaks + intact)), 1e-12),
    }

    # ------------------------------------------------------------ print
    print(f"\nScreening, averages over {len(windows)} formation periods (EG on {len(same_sector)} same-sector pairs):")
    print(f"  pass p<{P_VALUE}: {scr['pass_p05']:.1f}  -> true {scr['true_positives']:.1f} of "
          f"{scr['true_in_universe']:.1f} planted, false {scr['false_positives']:.1f} "
          f"(false discovery share {scr['false_positives'] / max(scr['pass_p05'], 1):.0%})")
    print(f"  Benjamini-Hochberg 5%: {scr['bh_discoveries']:.1f} discoveries, {scr['bh_true']:.1f} true")
    print(f"  distance method top {N_PAIRS}: {scr['distance_top20_true']:.1f} true pairs")
    print(f"  two-step (SSD top {PRESCREEN} -> EG): {scr['two_step_pass']:.1f} pass, {scr['two_step_true']:.1f} true; "
          f"BH: {scr['two_step_bh']:.1f} discoveries, {scr['two_step_bh_true']:.1f} true")
    print(f"\nBacktests (${LEG_USD / 1e6:.0f}M per leg, costs = half-spread + {IMPACT_COEF} x vol x sqrt(trade/ADV)"
          f" + {BORROW_BPS_PER_YEAR:.0f} bps/yr borrow):")
    print(f"  {'method':<44}{'SR gross':>9}{'SR net':>8}{'ret g%':>8}{'ret n%':>8}{'trips':>7}{'hold d':>7}{'stops':>6}")
    for meth, s in summary.items():
        print(f"  {LABELS[meth]:<44}{s['sharpe_gross']:9.2f}{s['sharpe_net']:8.2f}{s['ann_return_gross_pct']:8.2f}"
              f"{s['ann_return_net_pct']:8.2f}{s['round_trips']:7d}{s['avg_holding_days']:7.1f}{s['stop_outs']:6d}")
    for meth in methods:
        bt = ", ".join(f"{k}: {v:+.1f}%" for k, v in summary[meth]["gross_pnl_pct_of_capital_by_truth"].items())
        print(f"  gross P&L by pair type ({meth}), % of capital: {bt}")
    if breaks:
        print(f"  regime breaks (oracle selection): gross P&L after each break, % of one leg: "
              + ", ".join(f"{x:+.1f}" for x in regime["post_break_gross_pnl_per_break_pct_of_leg"])
              + " (without the stop-loss: " + ", ".join(f"{x:+.1f}" for x in regime["post_break_gross_pnl_per_break_no_stop_pct_of_leg"])
              + f"); intact pair-periods average {regime['intact_pair_period_gross_pnl_mean_pct_of_leg']:+.1f}%")
    print("  net Sharpe by leg size: " + "; ".join(
        f"{meth}: " + ", ".join(f"${float(k) / 1e6:g}M {v:.2f}" for k, v in capacity[meth].items())
        for meth in capacity))

    # ------------------------------------------------------------ plot 1: one planted pair that breaks
    cand = [r for r in records if r["method"] == "coint_top20" and r["truth"] == "planted, breaks this period"]
    if not cand:
        cand = [r for r in records if r["method"] == "oracle" and r["truth"] == "planted, breaks this period"]
    pick = min(cand, key=lambda r: r["gross"]) if cand else min(records, key=lambda r: r["gross"])
    pa, pb = pick["a"], pick["b"]
    pinfo = planted_key.get((pa, pb))
    meth_pick = pick["method"]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
    cum, cum_dates, cum_val = 0.0, [], []
    for f0, f1, t1 in windows:
        sel = [r for r in records if r["method"] == meth_pick and r["window"] == str(m.dates[f1].date())
               and (r["a"], r["b"]) == (pa, pb)]
        if not sel:
            continue
        days, z, beta, pos = pair_window(P, logP, pa, pb, f0, f1, t1,
                                         "distance" if meth_pick == "distance" else "coint")
        d = m.dates[days]
        ax.plot(d, z, color="0.15", lw=1.2)
        ax.axvspan(d[0], d[-1], color="0.5", alpha=0.06, lw=0)
        chg = np.flatnonzero(np.diff(np.r_[0, pos]) != 0)
        for k in chg:
            if pos[k] != 0:
                ax.plot(d[k], z[k], "^" if pos[k] > 0 else "v", ms=9, color=COLORS["coint_top20"],
                        mec="white", mew=1.0)
            else:
                stop = abs(z[k]) >= STOP_Z
                ax.plot(d[k], z[k], "X" if stop else "o", ms=9 if stop else 7,
                        color="#c0392b" if stop else COLORS["oracle"], mec="white", mew=1.0)
        acc1 = {"gross": np.zeros(T), "borrow": np.zeros(T)}
        pair_pnl(P, pa, pb, days, pos, beta, z, acc1, [], T)
        for k, dd in enumerate(days):
            cum += acc1["gross"][dd] * LEG_USD / 1e3
            cum_dates.append(m.dates[dd])
            cum_val.append(cum)
    for lvl, ls in ((ENTRY_Z, "--"), (-ENTRY_Z, "--"), (EXIT_Z, ":"), (-EXIT_Z, ":"), (STOP_Z, "-."), (-STOP_Z, "-.")):
        ax.axhline(lvl, color="0.4", lw=0.9, ls=ls)
    if pinfo and pinfo["break_day"] is not None:
        for a_ in (ax, ax2):
            a_.axvline(m.dates[pinfo["break_day"]], color="#c0392b", lw=1.5)
        ax.text(m.dates[pinfo["break_day"]], 5.4, "relationship breaks ", color="#c0392b", fontsize=9,
                va="center", ha="right")
    ax.plot([], [], "^", color=COLORS["coint_top20"], label="enter long spread")
    ax.plot([], [], "v", color=COLORS["coint_top20"], label="enter short spread")
    ax.plot([], [], "o", color=COLORS["oracle"], label="exit at |z| < 0.5")
    ax.plot([], [], "X", color="#c0392b", label="stop-loss at |z| > 4")
    ax.set_ylim(-6, 6)
    ax.set_ylabel("spread z-score (formation-period units)")
    ax.legend(loc="lower left", ncol=4, fontsize=8)
    ax.set_title(f"A planted cointegrated pair ({m.tickers[pa]} / {m.tickers[pb]}) traded by the cointegration "
                 f"method\nentry |z| > {ENTRY_Z}, exit |z| < {EXIT_Z}, stop |z| > {STOP_Z}; shaded = periods "
                 f"in which it was selected (synthetic data)", fontsize=10)
    ax2.plot(cum_dates, cum_val, color=COLORS["coint_top20"], lw=1.8)
    ax2.axhline(0, color="0.3", lw=0.8)
    ax2.set_ylabel(f"cum. gross P&L, $k\n(${LEG_USD / 1e6:.0f}M per leg)")
    fig.tight_layout()
    utils.save_fig(ctx, fig, "spread-zscore")

    # ------------------------------------------------------------ plot 2: P&L by method + screening
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.5, 1]})
    dts = m.dates[sl]
    for meth in methods:
        s = summary[meth]
        a1.plot(dts, 100 * np.cumsum(series[meth]["net"][sl]), color=COLORS[meth], lw=2.0,
                label=f"{LABELS[meth]}: net SR {s['sharpe_net']:.2f} (gross {s['sharpe_gross']:.2f})")
    a1.axhline(0, color="0.3", lw=0.8)
    a1.set_ylabel("cumulative P&L, % of committed capital")
    a1.set_title(f"Cumulative net P&L by selection method, ${LEG_USD / 1e6:.0f}M per leg\n"
                 "net of half-spread + square-root impact + borrow", fontsize=10)
    a1.legend(loc="upper left", fontsize=8)
    x = np.arange(len(screen_rows))
    tp = np.array([r["true_positives"] for r in screen_rows])
    fp = np.array([r["false_positives"] for r in screen_rows])
    a2.bar(x, tp, color=COLORS["oracle"], width=0.7, label="truly cointegrated (planted)")
    a2.bar(x, fp, bottom=tp, color="0.65", width=0.7, label="false discoveries")
    a2.set_xticks(x, [r["formation_end"][:7] for r in screen_rows], rotation=45, fontsize=8)
    a2.set_xlabel("formation period ending")
    a2.set_ylabel("pairs passing Engle-Granger p < 0.05")
    a2.set_title(f"Screening {len(same_sector):,} same-sector pairs per period:\nmost 'significant' pairs are noise",
                 fontsize=10)
    a2.legend(loc="upper right", fontsize=8.5)
    fig.suptitle("Pairs trading on a synthetic market with 8 planted cointegrated pairs (4 break partway)",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    utils.save_fig(ctx, fig, "pnl-by-method")

    # ------------------------------------------------------------ results
    keep = ("sharpe_gross", "sharpe_net", "ann_return_gross_pct", "ann_return_net_pct", "avg_pairs_per_period",
            "round_trips", "avg_holding_days", "capital_in_use_share", "stop_outs", "avg_cost_bps_per_dollar_traded",
            "annual_turnover_x_capital", "max_drawdown_net_pct", "gross_pnl_pct_of_capital_by_truth",
            "pair_periods_by_truth")
    utils.write_results(ctx, {
        "n_stocks": N, "n_days": T, "n_trading_periods": len(windows),
        "formation_days": FORMATION_DAYS, "trading_days": TRADING_DAYS,
        "entry_z": ENTRY_Z, "exit_z": EXIT_Z, "stop_z": STOP_Z,
        "leg_usd": LEG_USD, "committed_capital_usd_20_pairs": N_PAIRS * 2 * LEG_USD,
        "impact_coef": IMPACT_COEF, "borrow_bps_per_year": BORROW_BPS_PER_YEAR,
        "planted_pairs": [{**{k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items()},
                           "tickers": [m.tickers[p["a"]], m.tickers[p["b"]]],
                           "break_date": str(m.dates[p["break_day"]].date()) if p["break_day"] else None}
                          for p in planted],
        "screen_avg_per_period": scr,
        "screen_false_discovery_share": scr["false_positives"] / max(scr["pass_p05"], 1),
        "distance_sharpe_gross": summary["distance"]["sharpe_gross"],
        "distance_sharpe_net": summary["distance"]["sharpe_net"],
        "coint_top20_sharpe_gross": summary["coint_top20"]["sharpe_gross"],
        "coint_top20_sharpe_net": summary["coint_top20"]["sharpe_net"],
        "coint_all_sharpe_net": summary["coint_all"]["sharpe_net"],
        "oracle_sharpe_net": summary["oracle"]["sharpe_net"],
        "regime_break": regime,
        "methods": {k: {kk: s[kk] for kk in keep} for k, s in summary.items()},
        "net_sharpe_by_leg_usd": capacity,
        "plot_pair": [m.tickers[pa], m.tickers[pb]],
    })


if __name__ == "__main__":
    main()
