"""Walkthrough helper: executing a $500M buy order.

Builds every number quoted in
docs/03-algorithms/h-end-to-end-walkthroughs/walkthrough-institutional-execution.md
from the finished labs, so the page stays consistent with them:

  * Lab 16 (Almgren-Chriss): calibration, `ac_trajectory`, `ac_cost_variance` and the same 40,000
    Monte Carlo price paths (seed 7). Lab 16 simulates a SELL; this script MIRRORS it for a BUY:
    fills are at S + epsilon + eta * rate and each share bought lifts S by gamma. Expected cost and
    variance are identical, and a buy on price path z costs exactly what the lab's sell costs on -z
    (asserted below).
  * Lab 17 (VWAP/TWAP/POV) and Lab 18 (smart order router): read from their results.json and
    rescaled to this order (arithmetic shown in the page).
  * Close sizing: the E5 card's rule (cap MOC/LOC at 15% of the forecast closing print).

Run:  python labs/walkthroughs/institutional-execution.py   (about 2 s)
Out:  labs/walkthroughs/institutional-execution.json
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

LABS = Path(__file__).resolve().parents[1]
SEED = 7


def load_lab(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, LABS / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lab16 = load_lab("lab16", "16-almgren-chriss-frontier/lab.py")
lab17 = json.loads((LABS / "17-vwap-twap-pov/results.json").read_text())
lab18 = json.loads((LABS / "18-smart-order-router/results.json").read_text())

# ---- Lab 16 calibration (identical values; see labs/16-almgren-chriss-frontier/README.md) ----
S0 = 50.0                      # arrival price, $/share
ADV = 20e6                     # shares/day -> $1B ADV
X = 10e6                       # shares to BUY -> $500M, 50% of ADV
T, N = 5.0, 50                 # 5 days, 10 intervals/day (~39 min each)
TAU = T / N
SIGMA = 0.02 * S0              # $1.00/share/sqrt(day)
EPS = 0.00015 * S0             # half-spread 1.5 bps
V_REF = X / T                  # TWAP rate, 10% of ADV/day
ETA = 0.0020 * S0 / V_REF      # 5e-8
GAMMA = 0.0050 * S0 / X        # 2.5e-8
NOTIONAL = X * S0
BPS = 1e4 / NOTIONAL           # $ -> bps of order notional (1 bp = $50,000)

# ---- walkthrough assumptions (illustrative) ----
PARTICIPATION_CAP = 0.25       # desk cap on any interval's rate, share of ADV per day
LAMBDAS = [0.0, 1e-9, 1e-8, 1e-7, 1e-6]
AUCTION_SHARE = 0.10           # closing auction = 10% of daily volume (Lab 17 default)
CLOSE_FRAC = 0.10              # VWAP-within-day puts the auction's slice of volume in the close
MAX_AUCTION_PCT = 0.15         # E5 rule: never more than 15% of the forecast print
COMMISSION = 0.01              # $/share, illustrative; [Lore] range 0.5-2 cents
DELAY_DAYS = 0.1               # decision -> algo start: one interval, ~39 min
PATH_PERCENTILE = 75           # the simulated week used for the TCA report
SQRT_Y = 0.5                   # square-root law prefactor used to calibrate Lab 16


def buy_fills(holdings, z_path):
    """Mirror of lab16.simulate_shortfall for ONE buy path. Returns per-interval arrays."""
    x = np.asarray(holdings, float)
    trades = -np.diff(x)                               # shares bought in interval k
    rate = trades / TAU                                # shares/day
    dW = SIGMA * np.sqrt(TAU) * z_path                 # random price increments
    d_before = np.concatenate([[0.0], np.cumsum(dW)[:-1]])
    bought_before = X - x[:-1]
    s_before = S0 + d_before + GAMMA * bought_before   # buying lifts the price
    fill = s_before + EPS + ETA * rate                 # pay half-spread + temporary impact
    return dict(trades=trades, rate=rate, dW=dW, d_before=d_before, s_before=s_before,
                fill=fill, bought_before=bought_before)


def buy_shortfall_bps(holdings, z):
    """Realized buy shortfall (bps, + = cost) for many paths z (paths, N)."""
    x = np.asarray(holdings, float)
    trades = -np.diff(x)
    rate = trades / TAU
    d = SIGMA * np.sqrt(TAU) * np.cumsum(z, axis=1)
    d_before = np.hstack([np.zeros((z.shape[0], 1)), d[:, :-1]])
    s_before = S0 + d_before + GAMMA * (X - x[:-1])
    paid = (trades * (s_before + EPS + ETA * rate)).sum(axis=1)
    return (paid - X * S0) * BPS


def main():
    rng = np.random.default_rng(SEED)
    z_all = rng.standard_normal((40_000, N))          # the same draws as Lab 16's Monte Carlo
    z_delay = rng.standard_normal()                    # next draw in the stream: the delay move

    out: dict = {"seed": SEED, "order_usd": NOTIONAL, "order_shares": X, "pct_adv": 100 * X / ADV}

    # ---- 1. pre-trade: square-root law -------------------------------------------------
    peak = 1e4 * SQRT_Y * 0.02 * np.sqrt(X / ADV)
    out["pretrade_sqrt"] = dict(Y=SQRT_Y, peak_impact_bps=peak, avg_fill_impact_bps=2 / 3 * peak,
                                peak_impact_bps_Y1=2 * peak, avg_fill_impact_bps_Y1=4 / 3 * peak,
                                one_day_10pct_peak_bps=1e4 * SQRT_Y * 0.02 * np.sqrt(0.10),
                                one_day_10pct_avg_bps=2 / 3 * 1e4 * SQRT_Y * 0.02 * np.sqrt(0.10))

    # ---- 2. frontier, mirrored for a buy -------------------------------------------------
    sched, frontier = {}, {}
    for lam in LAMBDAS:
        hold = lab16.ac_trajectory(X, T, N, SIGMA, ETA, GAMMA, lam)
        E, V = lab16.ac_cost_variance(hold, T, SIGMA, ETA, GAMMA, EPS)
        trades = -np.diff(hold)
        daily = trades.reshape(int(T), -1).sum(axis=1)
        sqrt_mean = lab16.simulate_shortfall(hold, T, S0, SIGMA, ETA, GAMMA, EPS, z_all, "sqrt",
                                             V_REF).mean() * BPS
        kappa = lab16.urgency(T, N, SIGMA, ETA, GAMMA, lam)
        perm = 0.5 * GAMMA * X**2 * BPS
        spread = EPS * X * BPS
        frontier[f"{lam:g}"] = dict(
            expected_bps=E * BPS, expected_usd=E, sd_bps=np.sqrt(V) * BPS, sd_usd=np.sqrt(V),
            permanent_bps=perm, spread_bps=spread, temporary_bps=E * BPS - perm - spread,
            peak_pct_adv=100 * trades.max() / TAU / ADV, sqrt_impact_expected_bps=sqrt_mean,
            certainty_equivalent_bps=(E + lam * V) * BPS,      # the AC objective E + lambda * Var
            half_life_days=(np.log(2) / kappa) if kappa > 0 else None,
            daily_shares=daily, daily_pct_adv=100 * daily / ADV)
        sched[lam] = hold

    # decision rule: the most risk-averse lambda whose peak rate respects the cap
    ok = [lam for lam in LAMBDAS if frontier[f"{lam:g}"]["peak_pct_adv"] <= 100 * PARTICIPATION_CAP]
    lam_star = max(ok)
    out["frontier"] = frontier
    out["chosen_lambda"] = lam_star
    f_star, f_twap = frontier[f"{lam_star:g}"], frontier["0"]
    out["chosen_vs_twap"] = dict(extra_cost_bps=f_star["expected_bps"] - f_twap["expected_bps"],
                                 extra_cost_usd=f_star["expected_usd"] - f_twap["expected_usd"],
                                 sd_cut_usd=f_twap["sd_usd"] - f_star["sd_usd"])

    # multi-day reconciliation (TWAP): permanent impact carried from earlier days
    per_day_perm_bps = 1e4 * GAMMA * (X / T) / S0                   # 10 bps per day of buying
    carried = [d * per_day_perm_bps for d in range(int(T))]
    out["twap_permanent_split"] = dict(per_day_bps=per_day_perm_bps, carried_by_day=carried,
                                       carried_avg_bps=float(np.mean(carried)),
                                       within_day_bps=per_day_perm_bps / 2)
    out["lab16_one_day_10pct_linear_bps"] = dict(
        temporary=1e4 * ETA * V_REF / S0, permanent=per_day_perm_bps / 2, spread=1e4 * EPS / S0)

    # ---- 3. close sizing per day (E5 rule) ------------------------------------------------
    auction_print = AUCTION_SHARE * ADV
    daily = np.array(f_star["daily_shares"])
    moc = np.minimum(CLOSE_FRAC * daily, MAX_AUCTION_PCT * auction_print)
    out["close_plan"] = dict(auction_print_shares=auction_print, cap_shares=MAX_AUCTION_PCT * auction_print,
                             moc_shares=moc, moc_total_shares=moc.sum(), moc_total_usd=moc.sum() * S0,
                             moc_pct_of_order=100 * moc.sum() / X,
                             close_heavy_day1_pct_of_auction=100 * 0.30 * daily[0] / auction_print)

    # ---- 4. child orders --------------------------------------------------------------------
    first_interval = -np.diff(sched[lam_star])[0]
    out["child_orders"] = dict(first_interval_shares=first_interval, first_interval_usd=first_interval * S0,
                               avg_child_shares=250, n_children_total=X / 250,
                               n_children_first_interval=first_interval / 250)

    # ---- 5. one simulated week for the TCA report -------------------------------------------
    hold = sched[lam_star]
    sf_all = buy_shortfall_bps(hold, z_all)
    # check the mirror: buy on z == the lab's sell on -z
    sell_mirror = lab16.simulate_shortfall(hold, T, S0, SIGMA, ETA, GAMMA, EPS, -z_all[:200]) * BPS
    assert np.allclose(sell_mirror, sf_all[:200]), "buy/sell mirror check failed"
    idx = int(np.argsort(sf_all)[int(PATH_PERCENTILE / 100 * len(sf_all))])
    z = z_all[idx]
    f = buy_fills(hold, z)
    q, fill = f["trades"], f["fill"]
    spread_usd = EPS * X
    perm_usd = 0.5 * GAMMA * X**2                      # Lab 16's closed-form split
    temp_usd = ETA * (q * f["rate"]).sum() + GAMMA * (q * f["bought_before"]).sum() - perm_usd
    timing_usd = (q * f["d_before"]).sum()
    is_arrival = (q * fill).sum() - X * S0
    assert abs(is_arrival - (spread_usd + perm_usd + temp_usd + timing_usd)) < 1.0
    decision_px = S0 - SIGMA * np.sqrt(DELAY_DAYS) * z_delay
    delay_usd = X * (S0 - decision_px)
    commission_usd = COMMISSION * X
    opportunity_usd = (X - q.sum()) * (S0 + f["dW"].sum() + GAMMA * X - decision_px)  # 0: order completes
    total_usd = delay_usd + is_arrival + opportunity_usd + commission_usd
    avg_fill = (q * fill).sum() / X
    # interval VWAP: everyone else trades ADV*TAU per interval around the moving mid, plus our prints
    v_other = ADV * TAU
    p_other = f["s_before"] + 0.5 * f["dW"] + 0.5 * GAMMA * q
    vwap = (v_other * p_other.sum() + (q * fill).sum()) / (v_other * N + X)
    close_day5 = S0 + f["dW"].sum() + GAMMA * X
    day_close = S0 + np.cumsum(f["dW"]).reshape(int(T), -1)[:, -1] + GAMMA * (X - hold[10::10])
    same_path = {f"{lam:g}": float(buy_shortfall_bps(sched[lam], z[None, :])[0]) for lam in (0.0, 1e-8, 1e-7)}
    to_bps = lambda v: 1e4 * v / (X * decision_px)    # TCA reports in bps of DECISION notional
    out["tca"] = dict(
        path_index=idx, path_percentile=PATH_PERCENTILE, z_delay=z_delay,
        decision_px=decision_px, arrival_px=S0, avg_fill_px=avg_fill, interval_vwap=vwap,
        close_day5=close_day5, day_closes=day_close, max_fill_px=fill.max(),
        usd=dict(delay=delay_usd, spread=spread_usd, permanent=perm_usd, temporary=temp_usd,
                 timing=timing_usd, opportunity=opportunity_usd, commission=commission_usd,
                 total=total_usd, is_vs_arrival=is_arrival),
        bps_of_decision=dict(delay=to_bps(delay_usd), spread=to_bps(spread_usd),
                             permanent=to_bps(perm_usd), temporary=to_bps(temp_usd),
                             timing=to_bps(timing_usd), opportunity=to_bps(opportunity_usd),
                             commission=to_bps(commission_usd), total=to_bps(total_usd)),
        is_vs_arrival_bps=is_arrival * BPS,
        slippage_vs_vwap_bps=1e4 * (avg_fill - vwap) / vwap,
        slippage_vs_close_bps=1e4 * (avg_fill - close_day5) / close_day5,
        pretrade_expected_bps=f_star["expected_bps"], pretrade_sd_bps=f_star["sd_bps"],
        same_path_is_vs_arrival_bps=same_path,
        mc_mean_bps=sf_all.mean(), mc_sd_bps=sf_all.std(ddof=1))

    # ---- 6. Lab 17 and Lab 18 rescaled to this order ---------------------------------------
    out["lab17"] = {k: lab17[k]["expected_cost"] for k in ("twap", "vwap", "pov10", "close_heavy")}
    out["lab17"]["pov10_pct_days_complete"] = lab17["pov10"]["pct_days_complete"]
    out["lab17"]["vwap_minus_twap_bps"] = lab17["vwap_minus_twap_expected_cost_bps"]
    out["lab17"]["close_heavy_minus_vwap_bps"] = lab17["close_heavy"]["expected_cost"] - lab17["vwap"]["expected_cost"]
    pas, agg = "passive_all_in_bps_", "aggressive_all_in_bps_"
    out["lab18_usd_on_order"] = {
        "fee_greedy_minus_bandit_passive": (lab18[pas + "fee_greedy"] - lab18[pas + "net_of_toxicity"]) * NOTIONAL / 1e4,
        "fee_greedy_minus_bandit_aggressive": (lab18[agg + "fee_greedy"] - lab18[agg + "net_of_toxicity"]) * NOTIONAL / 1e4,
        "fill_weighted_minus_bandit_passive": (lab18[pas + "fill_weighted"] - lab18[pas + "net_of_toxicity"]) * NOTIONAL / 1e4,
        "fill_weighted_minus_bandit_aggressive": (lab18[agg + "fill_weighted"] - lab18[agg + "net_of_toxicity"]) * NOTIONAL / 1e4,
    }

    path = Path(__file__).with_suffix(".json")
    path.write_text(json.dumps(_round(out), indent=2) + "\n", encoding="utf-8")

    t = out["tca"]
    print(f"Chosen lambda {lam_star:g}: E {f_star['expected_bps']:.1f} bps, sd {f_star['sd_bps']:.1f} bps, "
          f"peak {f_star['peak_pct_adv']:.1f}% ADV, daily % ADV {np.round(f_star['daily_pct_adv'], 1)}")
    print(f"TCA week (p{PATH_PERCENTILE}): decision {t['decision_px']:.3f}, avg fill {t['avg_fill_px']:.3f}, "
          f"VWAP {t['interval_vwap']:.3f}, close {t['close_day5']:.3f}")
    for k, v in t["bps_of_decision"].items():
        print(f"  {k:<11}{v:8.1f} bps  ${t['usd'][k]:>13,.0f}")
    print(f"  vs arrival {t['is_vs_arrival_bps']:.1f}, vs VWAP {t['slippage_vs_vwap_bps']:.1f}, "
          f"vs close {t['slippage_vs_close_bps']:.1f} bps; same path {t['same_path_is_vs_arrival_bps']}")
    print(f"wrote {path.relative_to(LABS.parent)}")


def _round(x):
    if isinstance(x, dict):
        return {str(k): _round(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, np.ndarray)):
        return [_round(v) for v in np.asarray(x).tolist()] if isinstance(x, np.ndarray) else [_round(v) for v in x]
    if isinstance(x, (float, np.floating)):
        return float(f"{float(x):.6g}")
    if isinstance(x, np.integer):
        return int(x)
    return x


if __name__ == "__main__":
    main()
