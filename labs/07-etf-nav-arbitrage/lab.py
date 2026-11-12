"""Lab 07: ETF NAV arbitrage -- creation/redemption, the no-arbitrage band and the AP's P&L.

What it demonstrates
  * An ETF on a 50-stock cap-weighted basket (the 50 largest names of a simulated 200-stock
    market, labs/common simulate_equity_market). The creation unit is 50,000 ETF shares holding a
    fixed number of shares of each stock plus a small cash component; NAV per ETF share is
    (basket value + cash) / 50,000.
  * The ETF's closing price = NAV x (1 + premium). The premium is driven by flow shocks: net
    demand for ETF shares that the secondary market has not absorbed (stylized AR(1) model,
    shocks larger in high-vol regimes and correlated with the market's move).
  * An authorized participant (AP) creates units (buys the basket, delivers it, sells new ETF
    shares) when the premium exceeds its all-in cost, and redeems (buys ETF shares, receives and
    sells the basket, borrowing the stocks until settlement) when the discount does. Costs:
    ETF half-spread, basket half-spreads, square-root market impact, a fixed fee per order and
    borrow for redemptions. These costs define the NO-ARBITRAGE BAND [-redeem cost, +create cost].
    Rival arbitrageurs (4 bps costlier) take any premium beyond their own band; both have a
    daily balance-sheet capacity.
  * Results: premium statistics with and without AP activity (sd, |premium| percentiles, days
    outside the band, half-life vs the planted persistence), the AP's P&L vs its trigger
    threshold (trading inside the band loses money), and a stress pitfall: when basket spreads
    widen and the AP hits its balance-sheet limit, discounts break out of the normal band.
Daily steps (the AP acts at the close, when creations and redemptions are struck at NAV).

Supports: docs/02-strategies/a-liquidity-provision/etf-market-making.md,
          docs/02-strategies/b-speed-and-structural/etf-and-index-arbitrage.md

Run: python labs/07-etf-nav-arbitrage/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import simulate, utils  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# ETF and AP parameters: all STYLIZED (round numbers of a realistic order of magnitude)
N_BASKET = 50               # stocks in the basket (largest by market cap on day 0)
CU_SIZE = 50_000            # ETF shares per creation unit
NAV0 = 50.0                 # initial NAV per ETF share -> creation unit worth $2.5M
ETF_HALF_SPREAD_BPS = 1.5   # ETF quoted spread 3 bps in calm markets
FEE_USD = 500.0             # creation or redemption fee per order (fixed, paid to the issuer)
BORROW_BPS_PER_YEAR = 25.0  # stock-borrow fee for the basket shorted during a redemption
SETTLE_DAYS = 1             # days the AP is short the basket before redeemed shares arrive
IMPACT_COEF = 0.5           # square-root law: impact = coef x daily vol x sqrt(order / ADV)
MAX_UNITS = 10              # our AP's balance-sheet limit: creation units per day ($25M)
RIVAL_EXTRA_BPS = 4.0       # rival arbitrageurs' all-in cost exceeds ours by 4 bps
RIVAL_MAX_UNITS = 15        # rivals' combined capacity, units per day ($37.5M)
# premium model (flow shocks), stylized
PREMIUM_PER_UNIT_BPS = 2.0  # premium moves 2 bps per creation unit of unabsorbed net demand
FLOW_SD_UNITS = 8.0         # daily net-demand shock sd in calm markets (units = $20M)
FLOW_PERSISTENCE = 0.95     # share of unabsorbed demand left the next day (half-life 13.5 days)
FLOW_MARKET_CORR = 0.4      # investors buy the ETF on up days and dump it on down days
COLORS = {"noap": "#8c8c8c", "ap": "#2a78d6", "band": "#1baf7a", "create": "#eb6834",
          "redeem": "#7b3fbf", "pnl": "#2a78d6", "sd": "#eb6834", "stress": "#d6452a"}


# =====================================================================================
# === CORE ALGORITHM ===
# Units: prices in $, costs and premiums in basis points of the creation unit's value.
# Premium = ETF price / NAV - 1 (positive = ETF rich -> create; negative = cheap -> redeem).
# =====================================================================================

def nav(prices, basket_shares, cash_per_unit, cu_size=CU_SIZE):
    """Net asset value per ETF share.

    prices: (..., n_stocks) stock prices; basket_shares: (n_stocks,) shares of each stock in
    ONE creation unit; cash_per_unit: cash component per unit ($, absorbs whole-share rounding);
    cu_size: ETF shares per creation unit. NAV = (sum_i shares_i x price_i + cash) / cu_size.
    """
    return (np.asarray(prices) @ np.asarray(basket_shares) + cash_per_unit) / cu_size


def no_arbitrage_band(weights, half_spread_bps, daily_vol, adv_usd, unit_value, n_units=1,
                      etf_half_spread_bps=ETF_HALF_SPREAD_BPS, fee_usd=FEE_USD,
                      borrow_bps_per_year=BORROW_BPS_PER_YEAR, settle_days=SETTLE_DAYS,
                      impact_coef=IMPACT_COEF):
    """All-in cost (bps of unit value, per unit) of creating and of redeeming n_units.

    weights, half_spread_bps, daily_vol (decimal), adv_usd: per basket stock.
    Create: buy basket (half-spread + impact) + sell ETF (half-spread) + fixed fee.
    Redeem: buy ETF + sell basket + fee + borrow the basket until the redemption settles.
    Returns (create_cost_bps, redeem_cost_bps): the band is [-redeem_cost, +create_cost].
    """
    w = np.asarray(weights)
    order_usd = w * unit_value * n_units                                   # $ traded per stock
    impact_bps = impact_coef * np.asarray(daily_vol) * np.sqrt(order_usd / np.asarray(adv_usd)) * 1e4
    basket_bps = np.sum(w * (np.asarray(half_spread_bps) + impact_bps))
    fee_bps = fee_usd / (unit_value * n_units) * 1e4                       # fixed per order
    create = etf_half_spread_bps + basket_bps + fee_bps
    borrow_bps = borrow_bps_per_year * settle_days / 360.0                 # basket shorted until delivery
    return create, create + borrow_bps


def arb_decision(premium_bps, create_cost_bps, redeem_cost_bps, impact_bps_per_unit,
                 max_units=MAX_UNITS, buffer_bps=0.0):
    """Authorized participant's end-of-day decision. Returns signed creation units.

    Act only outside the band widened by buffer_bps (the trigger). Each unit created and sold
    (redeemed and bought) moves the premium down (up) by impact_bps_per_unit, so trade the
    units whose AVERAGE premium still exceeds the trigger: n = floor((|p| - trigger) / impact
    + 1/2), at most max_units (balance-sheet limit). +n = create, -n = redeem, 0 = no trade.
    Vectorized over arrays of premiums / costs / buffers.
    """
    p = np.asarray(premium_bps, float)
    up = np.asarray(create_cost_bps) + buffer_bps                          # create trigger
    dn = np.asarray(redeem_cost_bps) + buffer_bps                          # redeem trigger
    n_create = np.floor((p - up) / impact_bps_per_unit + 0.5)
    n_redeem = np.floor((-p - dn) / impact_bps_per_unit + 0.5)
    units = np.where(n_create > 0, n_create, np.where(n_redeem > 0, -n_redeem, 0.0))
    return np.clip(units, -max_units, max_units)


# === END CORE ALGORITHM ===
# =====================================================================================


def build_etf(m):
    """Pick the basket, fix share counts per creation unit and compute daily NAV and inputs."""
    cap0 = m.market_cap.iloc[0]
    names = cap0.sort_values(ascending=False).index[:N_BASKET]
    w0 = cap0[names] / cap0[names].sum()
    unit_value0 = NAV0 * CU_SIZE
    p0 = m.prices[names].iloc[0]
    shares = np.floor(w0 * unit_value0 / p0).to_numpy()                   # whole shares per unit
    cash = unit_value0 - float(shares @ p0.to_numpy())                     # cash component
    prices = m.prices[names].to_numpy()
    nav_ps = nav(prices, shares, cash)
    weights_t = prices * shares / (nav_ps[:, None] * CU_SIZE)              # drift with prices (cap-weighted)
    vol = m.returns[names].rolling(20, min_periods=5).std().bfill().to_numpy()
    return {"names": names, "shares": shares, "cash": cash, "nav": nav_ps, "weights": weights_t,
            "daily_vol": vol, "adv": m.adv_usd[names].to_numpy(),
            "half_spread": m.spread_bps[names].to_numpy() / 2.0}


def daily_bands(etf, h):
    """No-arbitrage band (1-unit order) each day; spreads widen with the vol regime squared."""
    T = len(etf["nav"])
    create, redeem, comp = np.empty(T), np.empty(T), None
    for t in range(T):
        stress = h[t] ** 2                                                  # stylized spread widening
        unit_value = etf["nav"][t] * CU_SIZE
        create[t], redeem[t] = no_arbitrage_band(etf["weights"][t], etf["half_spread"] * stress,
                                                 etf["daily_vol"][t], etf["adv"][t], unit_value,
                                                 etf_half_spread_bps=ETF_HALF_SPREAD_BPS * stress)
        if t == 0:
            w = etf["weights"][0]
            imp = IMPACT_COEF * etf["daily_vol"][0] * np.sqrt(w * unit_value / etf["adv"][0]) * 1e4
            comp = {"etf_half_spread": ETF_HALF_SPREAD_BPS * stress,
                    "basket_half_spread": float(np.sum(w * etf["half_spread"]) * stress),
                    "basket_impact": float(np.sum(w * imp)), "fee": FEE_USD / unit_value * 1e4,
                    "borrow_redeem_only": BORROW_BPS_PER_YEAR * SETTLE_DAYS / 360.0}
    return create, redeem, comp


def unit_cost_bps(etf, t, n_units, h_t, redeem):
    """True all-in cost per unit (bps) of an n-unit order on day t (impact grows with size)."""
    stress = h_t ** 2
    c, r = no_arbitrage_band(etf["weights"][t], etf["half_spread"] * stress, etf["daily_vol"][t],
                             etf["adv"][t], etf["nav"][t] * CU_SIZE, n_units=n_units,
                             etf_half_spread_bps=ETF_HALF_SPREAD_BPS * stress)
    return r if redeem else c


def simulate_premium(flow, create_band, redeem_band, triggers, ap=True, rivals=True, fixed=False):
    """Run the premium model for one or several AP triggers (vectorized over triggers).

    flow: daily net-demand shocks in units. State: unabsorbed demand I (units);
    premium = PREMIUM_PER_UNIT_BPS x I. Each day: I = FLOW_PERSISTENCE x I + flow. At the
    close, rival arbitrageurs (other APs and ETF market makers, cost = band + RIVAL_EXTRA_BPS)
    take any premium beyond their cost; then our AP trades what is left beyond its trigger
    (triggers: bps added to its cost band, or absolute bps if fixed=True). I -= units traded.
    Returns the premium our AP faces, the closing premium, our AP's units and the rivals'
    units, each (T, K).
    """
    triggers = np.atleast_1d(np.asarray(triggers, float))
    T, K = len(flow), len(triggers)
    faced, post, units, rival_units = (np.zeros((T, K)) for _ in range(4))
    imbalance = np.zeros(K)
    for t in range(T):
        imbalance = FLOW_PERSISTENCE * imbalance + flow[t]
        if rivals:
            rival_units[t] = arb_decision(PREMIUM_PER_UNIT_BPS * imbalance, create_band[t] + RIVAL_EXTRA_BPS,
                                          redeem_band[t] + RIVAL_EXTRA_BPS, PREMIUM_PER_UNIT_BPS, RIVAL_MAX_UNITS)
            imbalance = imbalance - rival_units[t]
        faced[t] = PREMIUM_PER_UNIT_BPS * imbalance
        if ap:
            base_c, base_r = (0.0, 0.0) if fixed else (create_band[t], redeem_band[t])
            units[t] = arb_decision(faced[t], base_c, base_r, PREMIUM_PER_UNIT_BPS, MAX_UNITS, triggers)
        imbalance = imbalance - units[t]
        post[t] = PREMIUM_PER_UNIT_BPS * imbalance
    return faced, post, units, rival_units


def ap_pnl_usd(etf, pre, units, h, cost_cache):
    """AP P&L per day ($): units x average premium captured minus true all-in costs."""
    pnl = np.zeros_like(pre)
    lam = PREMIUM_PER_UNIT_BPS
    for t, k in zip(*np.nonzero(units)):
        n = abs(units[t, k])
        side = np.sign(units[t, k])
        captured = n * side * pre[t, k] - lam * n * n / 2.0                # bps x units
        key = (t, int(n), side < 0)
        if key not in cost_cache:
            cost_cache[key] = unit_cost_bps(etf, t, int(n), h[t], side < 0)
        pnl[t, k] = (captured - n * cost_cache[key]) * etf["nav"][t] * CU_SIZE / 1e4
    return pnl


def premium_stats(p, create_band, redeem_band, tol=0.0, mask=None):
    """Summary statistics of a closing premium series (bps); outside = beyond the band + tol."""
    if mask is not None:
        p, create_band, redeem_band = p[mask], create_band[mask], redeem_band[mask]
    a = np.abs(p)
    phi = float(np.polyfit(p[:-1], p[1:], 1)[0]) if len(p) > 3 else float("nan")
    return {"mean_bps": float(p.mean()), "sd_bps": float(p.std()),
            "mean_abs_bps": float(a.mean()), "p95_abs_bps": float(np.percentile(a, 95)),
            "max_discount_bps": float(p.min()), "max_premium_bps": float(p.max()),
            "share_days_outside_band": float(np.mean((p > create_band + tol + 1e-9) | (p < -redeem_band - tol - 1e-9))),
            "ar1": phi, "half_life_days": float(np.log(0.5) / np.log(phi)) if 0 < phi < 1 else float("nan")}


# ----------------------------------------------------------------------------- plots
def plot_premium(dates, p_noap, p_ap, create_band, redeem_band, units, stress_mask, zoom):
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.2), gridspec_kw={"height_ratios": [1, 1.1], "hspace": 0.35})
    ax = axes[0]
    ax.plot(dates, p_noap, color=COLORS["noap"], lw=0.9, label="no AP: creations/redemptions switched off")
    ax.plot(dates, p_ap, color=COLORS["ap"], lw=0.9, label="with AP arbitrage")
    ax.fill_between(dates, -redeem_band, create_band, color=COLORS["band"], alpha=0.35, lw=0,
                    label="no-arbitrage band (cost of creating / redeeming 1 unit)")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel("closing premium to NAV (bps)")
    ax.set_title("ETF premium/discount to NAV with and without authorized-participant arbitrage")
    ax.legend(fontsize=8, loc="upper left", ncol=1)

    ax = axes[1]
    sl = slice(*zoom)
    d = dates[sl]
    ax.fill_between(d, -redeem_band[sl], create_band[sl], color=COLORS["band"], alpha=0.35, lw=0,
                    label="no-arbitrage band")
    ax.plot(d, p_ap[sl], color=COLORS["ap"], lw=1.1, label="closing premium, with AP")
    cr, rd = units[sl] > 0, units[sl] < 0
    ax.scatter(d[cr], p_ap[sl][cr], s=12 + 2 * units[sl][cr], color=COLORS["create"], zorder=3,
               label="creation (marker size ~ units)")
    ax.scatter(d[rd], p_ap[sl][rd], s=12 - 2 * units[sl][rd], color=COLORS["redeem"], zorder=3,
               label="redemption")
    st = stress_mask[sl]
    if st.any():
        ax.fill_between(d, 0, 1, where=st, transform=ax.get_xaxis_transform(), color=COLORS["stress"],
                        alpha=0.08, lw=0, label="stress episode (vol regime > 1.4)")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel("closing premium to NAV (bps)")
    ax.set_title("Zoom: arbitrage pins the premium to the band edges; it breaks out when flows exceed "
                 "arbitrage capacity", fontsize=10)
    lo, hi = ax.get_ylim()
    ax.set_ylim(lo, hi + 0.35 * (hi - lo))                                 # room for the legend
    ax.legend(fontsize=7.5, loc="upper left", ncol=3)
    fig.text(0.01, 0.005, "Synthetic data: 50-stock cap-weighted basket from simulate_equity_market; stylized flow "
             "model, costs and fees (see README).", fontsize=7.5, color="#555555")
    return fig


def plot_threshold(thresholds, pnl_musd, sd_bps, mean_band, best, rival_band):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(thresholds, pnl_musd, "o-", color=COLORS["pnl"], ms=4, label="AP P&L after all costs ($M per year)")
    ax.axhline(0, color="k", lw=0.6)
    ax.axvline(mean_band, color=COLORS["band"], lw=1.5, ls="--",
               label=f"average cost of a 1-unit creation ({mean_band:.1f} bps)")
    ax.axvline(rival_band, color=COLORS["stress"], lw=1.2, ls=":",
               label=f"rivals' average cost ({rival_band:.1f} bps): they take anything beyond")
    ax.plot([best[0]], [best[1]], "*", color="k", ms=12, label=f"best trigger: {best[0]:.0f} bps")
    ax.set_xlabel("AP trigger: act when |premium| exceeds this many bps")
    ax.set_ylabel("AP net P&L ($M per year)", color=COLORS["pnl"])
    ax2 = ax.twinx()
    ax2.plot(thresholds, sd_bps, "s--", color=COLORS["sd"], ms=3.5, label="sd of closing premium (bps, right axis)")
    ax2.set_ylabel("sd of closing premium (bps)", color=COLORS["sd"])
    ax2.spines["right"].set_visible(True)
    ax2.grid(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")
    ax.set_title("AP P&L vs trigger: inside your cost band you lose, beyond rivals' you get nothing")
    fig.text(0.01, -0.02, "Synthetic data. Fixed symmetric trigger; true costs include basket spreads, square-root "
             "impact (grows with units), $500 fee per order, borrow on redemptions.", fontsize=7.5, color="#555555")
    return fig


# ----------------------------------------------------------------------------- main
def main():
    ctx = utils.setup(__file__, "Lab 07: ETF NAV arbitrage and the no-arbitrage band")
    t0 = time.time()
    n_days = 500 if ctx.smoke else 1260
    m = simulate.simulate_equity_market(n_stocks=200, n_days=n_days, seed=ctx.seed)
    etf = build_etf(m)
    h = m.vol_regime.to_numpy()
    create_band, redeem_band, band_parts = daily_bands(etf, h)

    # flow shocks: fat-tailed, scaled by the vol regime, correlated with the market factor move
    rng = np.random.default_rng(ctx.seed + 707)
    mkt = m.factor_returns["market"].to_numpy()
    mkt_z = (mkt - mkt.mean()) / mkt.std()
    eps = rng.standard_t(5, n_days) / np.sqrt(5 / 3)
    # (the market move already scales with the vol regime h, so both parts are ~ h)
    flow = FLOW_SD_UNITS * (FLOW_MARKET_CORR * mkt_z + np.sqrt(1 - FLOW_MARKET_CORR ** 2) * h * eps)

    # (1) no arbitrage vs arbitrage: our AP triggers at its cost band, rivals at band + 4 bps
    _, p_noap, _, _ = simulate_premium(flow, create_band, redeem_band, [0.0], ap=False, rivals=False)
    faced_ap, p_ap, units_ap, units_rival = simulate_premium(flow, create_band, redeem_band, [0.0])
    p_noap, p_ap, faced_ap, units_ap, units_rival = (x[:, 0] for x in (p_noap, p_ap, faced_ap, units_ap, units_rival))
    all_units = units_ap + units_rival
    stress_mask = h > 1.4
    tol = PREMIUM_PER_UNIT_BPS / 2                       # one unit cannot be split: +-half a step
    stats = {
        "no_ap": premium_stats(p_noap, create_band, redeem_band, tol),
        "with_ap": premium_stats(p_ap, create_band, redeem_band, tol),
        "with_ap_calm": premium_stats(p_ap, create_band, redeem_band, tol, ~stress_mask),
        "with_ap_stress": premium_stats(p_ap, create_band, redeem_band, tol, stress_mask),
    }
    calm_band = float(np.median(create_band))
    stress_beyond_calm_band = (float(np.mean(np.abs(p_ap[stress_mask]) > calm_band + tol))
                               if stress_mask.any() else float("nan"))
    cap_days = int(np.sum((np.abs(units_ap) >= MAX_UNITS) & (np.abs(units_rival) >= RIVAL_MAX_UNITS)))
    nav_ret = np.diff(np.log(etf["nav"]))
    te = {name: float(np.std(np.diff(np.log(etf["nav"] * (1 + p / 1e4))) - nav_ret) * 1e4)
          for name, p in (("no_ap", p_noap), ("with_ap", p_ap))}

    # (2) our AP's P&L vs a fixed symmetric trigger (rivals unchanged)
    thresholds = np.arange(0.0, 21.0, 1.0) if not ctx.smoke else np.arange(0.0, 21.0, 2.0)
    faced_k, post_k, units_k, _ = simulate_premium(flow, create_band, redeem_band, thresholds, fixed=True)
    cache = {}
    pnl_k = ap_pnl_usd(etf, faced_k, units_k, h, cache)
    years = n_days / 252.0
    pnl_per_year = pnl_k.sum(0) / years / 1e6
    sd_k = post_k.std(0)
    ib = int(np.argmax(pnl_per_year))
    pnl_band = ap_pnl_usd(etf, faced_ap[:, None], units_ap[:, None], h, cache)[:, 0]

    # plots
    dates = m.dates.to_numpy()
    excess = np.abs(p_ap - np.clip(p_ap, -redeem_band, create_band))    # bps beyond the band
    mid = int(np.argmax(excess))                                          # biggest breakout
    zoom = (max(0, mid - 120), min(n_days, mid + 60))
    fig = plot_premium(dates, p_noap, p_ap, create_band, redeem_band, all_units, stress_mask, zoom)
    utils.save_fig(ctx, fig, "premium-band")
    fig = plot_threshold(thresholds, pnl_per_year, sd_k, float(np.mean(create_band)),
                         (thresholds[ib], pnl_per_year[ib]), float(np.mean(create_band)) + RIVAL_EXTRA_BPS)
    utils.save_fig(ctx, fig, "arb-pnl-vs-threshold")

    n_orders = int(np.sum(units_ap != 0))
    results = {
        "n_days": n_days, "basket_stocks": N_BASKET, "creation_unit_shares": CU_SIZE,
        "creation_unit_value_usd_day0": NAV0 * CU_SIZE,
        "band_components_bps_day0": band_parts,
        "create_cost_bps_mean": float(np.mean(create_band)), "redeem_cost_bps_mean": float(np.mean(redeem_band)),
        "create_cost_bps_max_stress": float(np.max(create_band)),
        "rival_extra_cost_bps": RIVAL_EXTRA_BPS,
        "stress_days": int(stress_mask.sum()),
        "share_stress_days_beyond_median_band": stress_beyond_calm_band,
        "premium_stats_no_ap": stats["no_ap"], "premium_stats_with_ap": stats["with_ap"],
        "premium_stats_with_ap_calm": stats["with_ap_calm"], "premium_stats_with_ap_stress": stats["with_ap_stress"],
        "planted_flow_persistence": FLOW_PERSISTENCE,
        "tracking_error_etf_vs_nav_bps_per_day": te,
        "ap_orders_per_year": n_orders / years,
        "ap_units_created_per_year": float(units_ap[units_ap > 0].sum() / years),
        "ap_units_redeemed_per_year": float(-units_ap[units_ap < 0].sum() / years),
        "all_arbs_units_created_per_year": float(all_units[all_units > 0].sum() / years),
        "all_arbs_units_redeemed_per_year": float(-all_units[all_units < 0].sum() / years),
        "all_arbs_capacity_binding_days": cap_days,
        "ap_pnl_musd_per_year_cost_aware": float(pnl_band.sum() / years / 1e6),
        "ap_pnl_bps_per_unit_cost_aware": float(pnl_band.sum() / (np.abs(units_ap).sum() * NAV0 * CU_SIZE) * 1e4),
        "max_breakout_beyond_band_bps": float(excess.max()),
        "ap_pnl_musd_per_year_by_trigger_bps": {f"{t:g}": round(float(v), 4) for t, v in zip(thresholds, pnl_per_year)},
        "best_trigger_bps": float(thresholds[ib]), "best_trigger_pnl_musd_per_year": float(pnl_per_year[ib]),
        "pnl_trigger_0bps_musd_per_year": float(pnl_per_year[0]),
    }
    utils.write_results(ctx, results)

    # summary
    s0, s1 = stats["no_ap"], stats["with_ap"]
    print(f"\nETF on the {N_BASKET} largest of 200 simulated stocks, {n_days} days; unit = {CU_SIZE:,} shares "
          f"(${NAV0 * CU_SIZE / 1e6:.1f}M).")
    print("  1-unit cost components on day 0 (bps): " + ", ".join(f"{k} {v:.2f}" for k, v in band_parts.items()))
    print(f"  no-arbitrage band: create {np.mean(create_band):.1f} bps, redeem {np.mean(redeem_band):.1f} bps on "
          f"average (create up to {np.max(create_band):.1f} bps in stress)")
    print("  closing premium        sd   mean|p|  p95|p|  max disc  outside band  AR(1)  half-life")
    for name, s in (("no AP", s0), ("with AP", s1), ("with AP, calm", stats["with_ap_calm"]),
                    ("with AP, stress", stats["with_ap_stress"])):
        print(f"  {name:<18} {s['sd_bps']:7.1f} {s['mean_abs_bps']:8.1f} {s['p95_abs_bps']:7.1f} "
              f"{s['max_discount_bps']:9.1f} {s['share_days_outside_band']:12.1%} {s['ar1']:6.3f} "
              f"{s['half_life_days']:8.1f}")
    print(f"  planted persistence {FLOW_PERSISTENCE} (half-life {np.log(0.5) / np.log(FLOW_PERSISTENCE):.1f} d); "
          f"tracking error ETF vs NAV: {te['no_ap']:.1f} -> {te['with_ap']:.1f} bps/day")
    print(f"  AP: {n_orders / years:.0f} orders/yr, {results['ap_units_created_per_year']:.0f} units created and "
          f"{results['ap_units_redeemed_per_year']:.0f} redeemed per year (all arbitrageurs: "
          f"{results['all_arbs_units_created_per_year']:.0f} / {results['all_arbs_units_redeemed_per_year']:.0f}); "
          f"all capacity used on {cap_days} days; our P&L ${results['ap_pnl_musd_per_year_cost_aware']:.2f}M/yr "
          f"(cost-aware trigger)")
    print(f"  fixed trigger: 0 bps -> ${pnl_per_year[0]:.2f}M/yr; best {thresholds[ib]:.0f} bps -> "
          f"${pnl_per_year[ib]:.2f}M/yr; {thresholds[-1]:.0f} bps -> ${pnl_per_year[-1]:.2f}M/yr")
    print(f"  stress (vol regime > 1.4, {int(stress_mask.sum())} days): |premium| beyond the median band on "
          f"{stress_beyond_calm_band:.0%} of them")
    print(f"  done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
