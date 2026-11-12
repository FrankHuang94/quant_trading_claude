"""Lab 20: index reconstitution -- an event study of index adds and deletes, and how crowding
shrinks the trade.

What it demonstrates
  * A synthetic, Russell-style annual reconstitution on top of labs/common
    simulate_equity_market (800 stocks, 10 years): on each rank day R the stocks are ranked by
    market cap; the index holds the top 400 with a +-10-rank band (a non-member joins if it ranks
    in the top 390, a member leaves if it falls below 410). The add and delete lists are announced
    on day A = R + 20 and take effect at the close of day E = A + 20 (trading days).
  * A STYLIZED price-pressure model planted on top of the simulated returns (parameters below,
    not calibrated to any index): a total effect that shrinks as arbitrage capital grows, part of
    it realized early (anticipation from R, a jump on A), the rest drifting up into E, then a partial
    reversal after E; plus a closing-auction volume spike on E from index-fund demand.
  * An event study (market-model abnormal returns, CARs with 95% bands) around A and E for adds
    and deletes, checked against the planted truth.
  * A strategy that buys adds (shorts deletes) at the close of A and sells (covers) into the
    closing auction at E, beta-hedged, net of costs; and its P&L as crowding (arbitrage capital
    relative to index demand) rises: per-trade returns fall towards zero and total arbitrage
    profit is hump-shaped (capacity).
  * Pitfalls: (1) selection -- stocks are added BECAUSE they rose, so their pre-event CAR is huge
    and says nothing about the index effect; (2) a market-model intercept estimated over that
    pre-event year turns the run-up into a fake negative alpha and biases the CAR; (3) events
    cluster in calendar time, so naive cross-sectional standard errors are too small; (4) holding
    past E gives back the reversal.

Supports: docs/02-strategies/d-mid-frequency-alpha/flow-driven-strategies.md

Run: python labs/20-index-reconstitution-event-study/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import simulate, utils  # noqa: E402

# ---- calendar and index rules (Russell-style, stylized) --------------------------------------
FIRST_RANK_DAY = 260        # trading-day index of the first rank day (one year of history first)
RANK_TO_ANNOUNCE = 20       # A = R + 20 trading days
ANNOUNCE_TO_EFFECTIVE = 20  # E = A + 20 trading days (effective at the close of E)
BAND = 10                   # rank band around the cutoff that limits turnover
WINDOW = (-20, 40)          # event window relative to A: from R to E + 20
EST_WINDOW = (-270, -21)    # estimation window for the market model: the year before R

# ---- STYLIZED price-pressure model (not calibrated to any index) ------------------------------
P0 = 0.05                   # total price effect at E with no arbitrage capital (5%)
C_HALF = 0.5                # crowding at which the total effect halves
EARLY_SHARE_0 = 0.20        # share of the effect realized by the close of A with no arbitrageurs
E_DAY_SHARE = 0.25          # share of the A->E drift that lands on day E (closing-auction pressure)
REVERSAL = 0.50             # share of the total effect that reverses over the 10 days after E
REVERSAL_DAYS = 10
PASSIVE_SHARE = 0.04        # index funds must buy/sell 4% of shares outstanding at the close of E
BASE_CROWDING = 0.25        # arbitrage capital / index demand in the base-case event study
CROWDING_GRID = (0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0)

# ---- stylized strategy costs ------------------------------------------------------------------
IMPACT_BPS = 10.0           # entry impact at the close of A (small arbitrageur), bps
BORROW_BPS_PER_YEAR = 100.0 # stock-borrow fee for shorting deletes
COLORS = {"add": "#2a78d6", "delete": "#eb6834", "truth": "#3a3a3a", "net": "#1baf7a", "agg": "#eda100"}


# =====================================================================================
# === CORE ALGORITHM ===
# Event time: day 0 = announcement day A. Abnormal return (AR) = what the stock did beyond
# what its market exposure explains. CAR = cumulative AR. Returns are simple daily returns.
# =====================================================================================

def abnormal_returns(returns, market, events, window=(-20, 40), est_window=(-270, -21),
                     intercept=False):
    """Market-model abnormal returns for each event over `window` (event x relative-day array).

    returns: (days x stocks) array; market: (days,) array of index returns;
    events: DataFrame with integer columns `stock` (column) and `day0` (row of day 0).
    For each event, fit r = alpha + beta * r_m by OLS over est_window (relative days), then
    AR = r - beta * r_m      (default: drop alpha, which mostly reflects past luck), or
    AR = r - alpha - beta * r_m  if intercept=True (the textbook market model).
    Also returns the ARs over the estimation window (for the standard errors).
    """
    rel = np.arange(window[0], window[1] + 1)
    est = np.arange(est_window[0], est_window[1] + 1)
    ar, ar_est = [], []
    for stock, d0 in zip(events["stock"], events["day0"]):
        r_e, m_e = returns[d0 + est, stock], market[d0 + est]
        beta = np.cov(r_e, m_e)[0, 1] / np.var(m_e, ddof=1)
        alpha = (r_e.mean() - beta * m_e.mean()) if intercept else 0.0
        ar.append(returns[d0 + rel, stock] - alpha - beta * market[d0 + rel])
        ar_est.append(r_e - alpha - beta * m_e)
    return np.array(ar), np.array(ar_est)


def event_study(ar, ar_est, window=(-20, 40)):
    """Mean CAR per relative day with two standard errors and a 95% band.

    ar: (events x window days) ARs; ar_est: (events x estimation days) ARs.
    CAR(k) = sum of ARs on days window[0]+1 .. k, so the CAR is 0 on the first window day.
    se_cross: cross-sectional std of the events' CARs / sqrt(n); assumes independent events.
    se_dependence: Brown & Warner (1985) "crude dependence adjustment": the daily std of the
    equal-weighted AR portfolio over the estimation window x sqrt(days cumulated). It absorbs
    the cross-correlation of events that share calendar dates. The band uses the larger one.
    """
    n = ar.shape[0]
    car_i = np.cumsum(np.c_[np.zeros(n), ar[:, 1:]], axis=1)          # CAR of each event
    car = car_i.mean(axis=0)
    days = np.arange(ar.shape[1])                                    # days cumulated so far
    se_cross = car_i.std(axis=0, ddof=1) / np.sqrt(n)
    se_dep = ar_est.mean(axis=0).std(ddof=1) * np.sqrt(days)
    se = np.maximum(se_cross, se_dep)                                # conservative band
    rel = np.arange(window[0], window[1] + 1)
    return pd.DataFrame({"car": car, "se_cross": se_cross, "se_dependence": se_dep,
                         "lo": car - 1.96 * se, "hi": car + 1.96 * se}, index=pd.Index(rel, name="rel_day"))


# === END CORE ALGORITHM ===
# =====================================================================================


def reconstitution_events(mcap: np.ndarray, n_index: int, band: int, rank_days: list[int]) -> pd.DataFrame:
    """Adds (side +1) and deletes (side -1) at each annual rank day; membership starts as the
    top n_index stocks by market cap on day 0."""
    members = set(np.argsort(-mcap[0])[:n_index])
    rows = []
    for k, R in enumerate(rank_days):
        rank = np.empty(mcap.shape[1], dtype=int)
        rank[np.argsort(-mcap[R])] = np.arange(1, mcap.shape[1] + 1)          # 1 = largest
        adds = [j for j in range(mcap.shape[1]) if j not in members and rank[j] <= n_index - band]
        dels = [j for j in members if rank[j] > n_index + band]
        for j, side in [(j, 1) for j in adds] + [(j, -1) for j in dels]:
            rows.append({"recon": k, "stock": j, "side": side, "R": R, "day0": R + RANK_TO_ANNOUNCE,
                         "E": R + RANK_TO_ANNOUNCE + ANNOUNCE_TO_EFFECTIVE, "rank": rank[j]})
        members = (members - set(dels)) | set(adds)
    return pd.DataFrame(rows)


def pressure_path(crowding: float, window=WINDOW) -> np.ndarray:
    """STYLIZED cumulative abnormal return path (per unit of P0, for an add) over the window.

    total(c)  = 1 / (1 + c / C_HALF)                  : arbitrage capital absorbs the demand shock
    early(c)  = EARLY_SHARE_0 + (1 - EARLY_SHARE_0) * c / (c + C_HALF)
                                                       : competition moves the effect earlier
    The early part beyond EARLY_SHARE_0 is split between anticipation (R+1..A-1) and the A-day
    jump; the rest drifts up from A+1 to E (E_DAY_SHARE of it on E); REVERSAL of the total
    reverses linearly over the REVERSAL_DAYS after E.
    """
    rel = np.arange(window[0], window[1] + 1)
    total = 1.0 / (1.0 + crowding / C_HALF)
    early = EARLY_SHARE_0 + (1.0 - EARLY_SHARE_0) * crowding / (crowding + C_HALF)
    anticip, jump = 0.5 * (early - EARLY_SHARE_0), EARLY_SHARE_0 + 0.5 * (early - EARLY_SHARE_0)
    late = 1.0 - early
    e_day = ANNOUNCE_TO_EFFECTIVE
    daily = np.zeros(len(rel))
    pre = (rel > window[0]) & (rel < 0)
    daily[pre] = anticip / pre.sum()
    daily[rel == 0] = jump
    run = (rel > 0) & (rel < e_day)
    daily[run] = late * (1 - E_DAY_SHARE) / run.sum()
    daily[rel == e_day] = late * E_DAY_SHARE
    rev = (rel > e_day) & (rel <= e_day + REVERSAL_DAYS)
    daily[rev] = -REVERSAL / rev.sum()
    return total * np.cumsum(daily)


def plant_effects(base_returns: np.ndarray, events: pd.DataFrame, size: np.ndarray, crowding: float) -> np.ndarray:
    """Add the stylized abnormal-return path of every event to a copy of the simulated returns."""
    r = base_returns.copy()
    rel = np.arange(WINDOW[0], WINDOW[1] + 1)
    daily = np.diff(np.r_[0.0, pressure_path(crowding)])
    for (stock, d0, side), s in zip(events[["stock", "day0", "side"]].to_numpy(), size):
        r[d0 + rel, stock] += side * P0 * s * daily
    return r


def cap_weighted_market(returns: np.ndarray, mcap: np.ndarray) -> np.ndarray:
    w = np.vstack([mcap[:1], mcap[:-1]])                   # yesterday's caps
    return (returns * w).sum(axis=1) / w.sum(axis=1)


def strategy_pnl(ar: np.ndarray, events: pd.DataFrame, spread_bps: np.ndarray, exit_day: int = ANNOUNCE_TO_EFFECTIVE):
    """Per-event return of: buy adds / short deletes at the close of A, exit at the close of
    `exit_day`, hedged with beta x index. Returns (gross, net) arrays in decimal."""
    rel = np.arange(WINDOW[0], WINDOW[1] + 1)
    held = (rel >= 1) & (rel <= exit_day)
    gross = events["side"].to_numpy() * ar[:, held].sum(axis=1)
    return gross, gross - trade_costs(events, spread_bps, exit_day)


def trade_costs(events: pd.DataFrame, spread_bps: np.ndarray, exit_day: int = ANNOUNCE_TO_EFFECTIVE) -> np.ndarray:
    """Stylized round-trip cost per event (decimal): half-spread in + half-spread out + entry
    impact, plus stock-borrow fees on shorts (deletes)."""
    borrow = np.where(events["side"].to_numpy() < 0, BORROW_BPS_PER_YEAR * 1e-4 * exit_day / 252, 0.0)
    return (spread_bps + IMPACT_BPS) * 1e-4 + borrow


def clustered_mean_ci(x: np.ndarray, clusters: np.ndarray) -> tuple[float, float]:
    """Mean of x and a 95% half-width from cluster (reconstitution) means."""
    means = pd.Series(x).groupby(clusters).mean()
    if len(means) < 2:
        return float(np.mean(x)), float("nan")
    return float(np.mean(x)), float(1.96 * means.std(ddof=1) / np.sqrt(len(means)))


def main():
    ctx = utils.setup(__file__, "Lab 20: index reconstitution event study")
    n_stocks, n_days = (300, 800) if ctx.smoke else (800, 2520)
    n_index, band = n_stocks // 2, (5 if ctx.smoke else BAND)
    # alphas=(): no planted stock-specific alphas, so the index effect is the ONLY predictable
    # part of specific returns (adds are past winners; any momentum-like alpha would confound it)
    m = simulate.simulate_equity_market(n_stocks=n_stocks, n_days=n_days, seed=ctx.seed, alphas=())
    base = m.returns.to_numpy()
    mcap = m.market_cap.to_numpy()
    volume = m.volume.to_numpy()
    rank_days = list(range(FIRST_RANK_DAY, n_days - RANK_TO_ANNOUNCE - WINDOW[1] - 1, 252))
    ev = reconstitution_events(mcap, n_index, band, rank_days)
    adds, dels = ev.side.to_numpy() > 0, ev.side.to_numpy() < 0

    # index demand per event, in days of ADV: drives the E-day volume and the size of the effect
    adv_shares = pd.DataFrame(volume).rolling(60).mean().to_numpy()
    shares_out = mcap[0] / m.prices.to_numpy()[0]
    demand_days = PASSIVE_SHARE * shares_out[ev.stock] / adv_shares[ev.R, ev.stock]
    size = np.clip(np.sqrt(demand_days / np.median(demand_days)), 0.5, 2.0)   # square-root scaling
    spread = m.spread_bps.to_numpy()[ev.stock]

    # ---- base case: plant effects at moderate crowding, then run the event study --------------
    r_base = plant_effects(base, ev, size, BASE_CROWDING)
    mkt = cap_weighted_market(r_base, mcap)
    ar, ar_est = abnormal_returns(r_base, mkt, ev, WINDOW, EST_WINDOW)
    groups = (("add", adds), ("delete", dels))
    studies = {g: event_study(ar[mask], ar_est[mask], WINDOW) for g, mask in groups}
    truth_path = pressure_path(BASE_CROWDING) * P0
    truth = {"add": truth_path * size[adds].mean(), "delete": -truth_path * size[dels].mean()}
    rel = studies["add"].index.to_numpy()

    def window_car(g, k0, k1, table=None):
        """CAR from the close of day k0 to the close of day k1 (sum of ARs on k0+1..k1)."""
        t = studies[g] if table is None else table
        return t.car.loc[k1] - t.car.loc[k0]

    E = ANNOUNCE_TO_EFFECTIVE
    win = {"anticipation_R_to_A": (WINDOW[0], -1), "announcement_day_A": (-1, 0), "run_up_A_to_E": (0, E),
           "effective_day_E": (E - 1, E), "reversal_E_to_E20": (E, E + 20), "total_R_to_E20": (WINDOW[0], E + 20)}
    car_windows = {g: {k: window_car(g, *v) for k, v in win.items()} for g in studies}
    truth_windows = {g: {k: truth[g][list(rel).index(v[1])] - truth[g][list(rel).index(v[0])]
                         for k, v in win.items()} for g in studies}
    coverage = {g: float(((studies[g].lo <= truth[g]) & (truth[g] <= studies[g].hi)).mean()) for g in studies}
    # naive band: cross-sectional standard errors only (assumes independent events)
    naive_cov = {g: float((np.abs(studies[g].car - truth[g]) <= 1.96 * studies[g].se_cross).mean()) for g in studies}
    se_ratio = float(np.median((studies["add"].se_dependence / studies["add"].se_cross).iloc[5:]))

    # ---- pitfalls: selection run-up and the market-model intercept ---------------------------
    # beta-adjusted CAR over the year before R (beta estimated over that same year, no alpha)
    ar_pre, _ = abnormal_returns(r_base, mkt, ev, (-270, -20), (-270, -21))
    selection_car = {g: float(ar_pre[mask, 1:].sum(axis=1).mean()) for g, mask in groups}
    ar_int, ar_int_est = abnormal_returns(r_base, mkt, ev, WINDOW, EST_WINDOW, intercept=True)
    with_intercept = {g: event_study(ar_int[mask], ar_int_est[mask], WINDOW) for g, mask in groups}
    intercept_bias = {g: float(window_car(g, WINDOW[0], E + 20, with_intercept[g]) - car_windows[g]["total_R_to_E20"])
                      for g in studies}

    # ---- the strategy at base crowding, and holding past E ----------------------------------
    gross, net = strategy_pnl(ar, ev, spread)
    _, net_hold = strategy_pnl(ar, ev, spread, exit_day=E + 20)
    recon = ev.recon.to_numpy()
    base_net, base_ci = clustered_mean_ci(net, recon)
    n_years = len(rank_days)

    # ---- E-day volume spike ------------------------------------------------------------------
    vol_planted = volume.astype(float).copy()
    vol_planted[ev.E, ev.stock] += PASSIVE_SHARE * shares_out[ev.stock]
    vol_rel = np.arange(-10, E + 11)
    base_vol = np.array([np.median(volume[d0 - 60:d0 - 20, s]) for s, d0 in zip(ev.stock, ev.day0)])
    vol_ratio = np.array([vol_planted[d0 + vol_rel, s] for s, d0 in zip(ev.stock, ev.day0)]) / base_vol[:, None]
    e_day_volume_mult = float(np.median(vol_ratio[:, list(vol_rel).index(E)]))

    # ---- crowding sweep -------------------------------------------------------------------------
    demand_usd = PASSIVE_SHARE * mcap[ev.R, ev.stock]
    costs = trade_costs(ev, spread)
    sweep = []
    for c in CROWDING_GRID:
        r_c = plant_effects(base, ev, size, c)
        ar_c, _ = abnormal_returns(r_c, cap_weighted_market(r_c, mcap), ev, WINDOW, EST_WINDOW)
        g_c, n_c = strategy_pnl(ar_c, ev, spread)
        path = pressure_path(c)
        gm, gci = clustered_mean_ci(g_c, recon)
        nm, nci = clustered_mean_ci(n_c, recon)
        rel_l = list(np.arange(WINDOW[0], WINDOW[1] + 1))
        sweep.append({"crowding": c, "gross_bps": 1e4 * gm, "gross_ci_bps": 1e4 * gci, "net_bps": 1e4 * nm,
                      "net_ci_bps": 1e4 * nci,
                      "planted_gross_bps": 1e4 * P0 * size.mean() * (path[rel_l.index(E)] - path[rel_l.index(0)]),
                      "planted_total_effect_bps": 1e4 * P0 * size.mean() * path[rel_l.index(E)],
                      "arb_profit_musd_per_year": c * np.sum(demand_usd * n_c) / n_years / 1e6,
                      "planted_arb_profit_musd_per_year": c * np.sum(demand_usd * (
                          P0 * size * (path[rel_l.index(E)] - path[rel_l.index(0)]) - costs)) / n_years / 1e6})
    sweep = pd.DataFrame(sweep)
    best = sweep.loc[sweep.planted_arb_profit_musd_per_year.idxmax()]

    # ---- plot 1: CARs and volume ----------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.4, 1]})
    for (g, mask), lab in zip(groups, ("adds", "deletes")):
        t = studies[g]
        ax1.plot(rel, t.car * 100, color=COLORS[g], lw=2, label=f"{lab} (n = {mask.sum()}), mean CAR")
        ax1.fill_between(rel, t.lo * 100, t.hi * 100, color=COLORS[g], alpha=0.18, lw=0)
        ax1.plot(rel, truth[g] * 100, color=COLORS[g], lw=1.2, ls="--")
    ax1.plot([], [], color="0.4", ls="--", label="planted (true) path")
    for x, lab in ((WINDOW[0], "R: rank day"), (0, "A: announcement"), (E, "E: effective (close)")):
        ax1.axvline(x, color="k", lw=0.8, ls=":")
        ax1.text(x + 0.4, ax1.get_ylim()[1] * 0.92 if x != WINDOW[0] else ax1.get_ylim()[1] * 0.80, lab, fontsize=8)
    ax1.axhline(0, color="k", lw=0.6)
    ax1.set_xlabel("trading days relative to announcement day A")
    ax1.set_ylabel("cumulative abnormal return (%)")
    ax1.set_title(f"Index adds and deletes: CAR around A and E\n(synthetic data, stylized price pressure, "
                  f"crowding {BASE_CROWDING})")
    handles, _ = ax1.get_legend_handles_labels()
    handles.append(Patch(color="0.6", alpha=0.35, label="95% band (dependence-adjusted)"))
    ax1.legend(handles=handles, fontsize=8, loc="lower left")
    for g, lab in (("add", "adds"), ("delete", "deletes")):
        mask = adds if g == "add" else dels
        ax2.plot(vol_rel, np.median(vol_ratio[mask], axis=0), color=COLORS[g], lw=1.8, marker="o", ms=3,
                 label=f"{lab}: median volume / normal")
    ax2.axvline(E, color="k", lw=0.8, ls=":")
    ax2.set_ylim(0, None)
    ax2.set_xlabel("trading days relative to announcement day A")
    ax2.set_ylabel("daily volume / pre-event median volume (x)")
    ax2.set_title(f"Index funds trade at the close of E:\nvolume about {e_day_volume_mult:.0f}x normal (synthetic)")
    ax2.legend(fontsize=8.5, loc="upper left")
    utils.save_fig(ctx, fig, "car")

    # ---- plot 2: P&L vs crowding --------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(sweep))
    ax1.plot(x, sweep.planted_total_effect_bps, color=COLORS["truth"], lw=1.2, ls=":", marker="s", ms=4,
             label="planted total price effect at E")
    ax1.plot(x, sweep.planted_gross_bps, color=COLORS["truth"], lw=1.2, ls="--",
             label="planted A->E move (what the trade can capture)")
    ax1.plot(x, sweep.planted_gross_bps - 1e4 * costs.mean(), color=COLORS["net"], lw=1.2, ls="--",
             label="planted A->E move minus average costs")
    ax1.errorbar(x - 0.06, sweep.gross_bps, yerr=sweep.gross_ci_bps, fmt="o", color=COLORS["add"], capsize=3,
                 label="measured gross return per trade, 95% CI")
    ax1.errorbar(x + 0.06, sweep.net_bps, yerr=sweep.net_ci_bps, fmt="o", color=COLORS["net"], capsize=3,
                 label="measured net return per trade, 95% CI")
    ax1.axhline(0, color="k", lw=0.6)
    ax1.set_xticks(x, [f"{c:g}" for c in sweep.crowding])
    ax1.set_xlabel("crowding: arbitrage capital / index demand")
    ax1.set_ylabel("return per trade, beta-hedged (bps)")
    ax1.set_title("Buy adds / short deletes at A, exit at the close of E\n(synthetic data, stylized model)")
    ax1.legend(fontsize=8, loc="upper right")
    ax2.plot(x, sweep.planted_arb_profit_musd_per_year, color=COLORS["truth"], lw=1.2, ls="--",
             label="expected under the planted model")
    ax2.plot(x, sweep.arb_profit_musd_per_year, color=COLORS["agg"], lw=2, marker="o",
             label="measured in this sample")
    ax2.legend(fontsize=8.5, loc="lower left")
    ax2.set_xticks(x, [f"{c:g}" for c in sweep.crowding])
    ax2.axhline(0, color="k", lw=0.6)
    ax2.set_xlabel("crowding: arbitrage capital / index demand")
    ax2.set_ylabel("total arbitrage profit, net (\\$M per year)")
    ax2.set_title(f"Capacity: total arbitrage profit is hump-shaped\n(synthetic data, stylized model; index "
                  f"demand \\${demand_usd.sum() / n_years / 1e9:.0f}B per year)")
    utils.save_fig(ctx, fig, "crowding")

    # ---- results ---------------------------------------------------------------------------------
    results = {
        "n_adds": int(adds.sum()), "n_deletes": int(dels.sum()), "n_reconstitutions": n_years,
        "car_adds_pct": {k: 100 * v for k, v in car_windows["add"].items()},
        "car_deletes_pct": {k: 100 * v for k, v in car_windows["delete"].items()},
        "planted_car_adds_pct": {k: 100 * v for k, v in truth_windows["add"].items()},
        "band_coverage_of_truth_adds_deletes": [coverage["add"], coverage["delete"]],
        "naive_cross_sectional_band_coverage_adds_deletes": [naive_cov["add"], naive_cov["delete"]],
        "se_dependence_over_se_cross_median": se_ratio,
        "e_day_volume_multiple_median": e_day_volume_mult,
        "strategy_net_bps_per_trade_base": 1e4 * base_net, "strategy_net_ci95_bps": 1e4 * base_ci,
        "strategy_gross_bps_per_trade_base": 1e4 * gross.mean(),
        "strategy_hit_rate": float((net > 0).mean()),
        "hold_to_E_plus_20_net_bps_per_trade": 1e4 * net_hold.mean(),
        "net_bps_by_crowding": dict(zip([f"{c:g}" for c in sweep.crowding], sweep.net_bps)),
        "arb_profit_musd_per_year_by_crowding": dict(zip([f"{c:g}" for c in sweep.crowding],
                                                         sweep.arb_profit_musd_per_year)),
        "planted_arb_profit_musd_per_year_by_crowding": dict(zip([f"{c:g}" for c in sweep.crowding],
                                                                 sweep.planted_arb_profit_musd_per_year)),
        "crowding_at_max_expected_total_arb_profit": float(best.crowding),
        "index_demand_usd_bn_per_year": demand_usd.sum() / n_years / 1e9,
        "mean_round_trip_cost_bps": 1e4 * costs.mean(),
        "pitfall_selection_car_year_before_rank_day_pct": {k: 100 * v for k, v in selection_car.items()},
        "pitfall_intercept_bias_total_car_pct": {k: 100 * v for k, v in intercept_bias.items()},
    }
    utils.write_results(ctx, results)

    print(f"\n{n_stocks} stocks x {n_days} days; index = top {n_index} by market cap, band +-{band}; "
          f"{n_years} reconstitutions: {adds.sum()} adds, {dels.sum()} deletes")
    print(f"base crowding {BASE_CROWDING}: CAR (%), measured vs planted [95% band coverage of the truth: "
          f"adds {coverage['add']:.0%}, deletes {coverage['delete']:.0%}]")
    for k in win:
        print(f"  {k:<22} adds {100 * car_windows['add'][k]:+6.2f} (true {100 * truth_windows['add'][k]:+6.2f})"
              f"   deletes {100 * car_windows['delete'][k]:+6.2f} (true {100 * truth_windows['delete'][k]:+6.2f})")
    print(f"dependence-adjusted SE / cross-sectional SE (median): {se_ratio:.2f}")
    print(f"naive (cross-sectional SE only) band coverage of the truth: adds {naive_cov['add']:.0%}, "
          f"deletes {naive_cov['delete']:.0%}")
    print(f"E-day volume: {e_day_volume_mult:.1f}x normal (median)")
    print(f"strategy (buy adds / short deletes at A, exit at E close): gross {1e4 * gross.mean():.0f} bps, "
          f"net {1e4 * base_net:.0f} +- {1e4 * base_ci:.0f} bps per trade, hit rate {(net > 0).mean():.0%}; "
          f"holding to E+20 instead: net {1e4 * net_hold.mean():.0f} bps")
    print("crowding sweep (net bps per trade; total arb profit $M/yr):")
    for _, row in sweep.iterrows():
        print(f"  c = {row.crowding:<4g} planted total {row.planted_total_effect_bps:5.0f}  capturable "
              f"{row.planted_gross_bps:5.0f}  measured gross {row.gross_bps:6.0f}  net {row.net_bps:6.0f} "
              f"+- {row.net_ci_bps:4.0f}   arb profit {row.arb_profit_musd_per_year:7.1f} "
              f"(expected {row.planted_arb_profit_musd_per_year:7.1f})")
    print(f"pitfall, selection: CAR over the year before R: adds {100 * selection_car['add']:+.1f}%, "
          f"deletes {100 * selection_car['delete']:+.1f}% (no planted effect there)")
    print(f"pitfall, intercept: total CAR (R..E+20) changes by adds {100 * intercept_bias['add']:+.2f} pp, "
          f"deletes {100 * intercept_bias['delete']:+.2f} pp with an estimated alpha")


if __name__ == "__main__":
    main()
