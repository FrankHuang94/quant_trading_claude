"""Walkthrough helper: one trading day at an ETF market maker that is also an authorized participant.

Chains the CORE ALGORITHM functions of four labs on one simulated day:
  * Lab 07 (07-etf-nav-arbitrage): nav, no_arbitrage_band, arb_decision, build_etf, daily_bands
  * Lab 05 (05-avellaneda-stoikov-glft-quoting): glft_quotes, step_pnl
  * Lab 04 (04-markout-analysis): markouts, markout_curve
  * Lab 02 (02-microprice-fair-value): book_state, weighted_mid, plus the fitted microprice table
    from its results.json

The world: Lab 07's synthetic market (200 stocks, 5 years, seed 7) and its ETF on the 50 largest
names (creation unit 50,000 shares). "Today" is the first calm, modestly rising day after day 300
whose ETF-vs-index basis move is under 5 bps (see pick_day). Intraday,
every factor and every stock's specific return follows a Brownian path (plus market-wide news
jumps about once a minute) bridged so that each stock closes exactly at the simulator's closing
price. Fair value = NAV of the live basket each second; the "future" is on the cap-weighted
index of all 200 names (an S&P 500 stand-in); the "peer ETF" holds the 100 largest names.

The market maker quotes the ETF with GLFT quotes (inventory skew from the basis risk left after
the futures hedge), floored at hedge cost plus expected adverse selection and capped by the
creation/redemption band. Fills: uninformed clients (Poisson, net buyers today), fast
arbitrageurs who pick off stale quotes when news moves fair value, and one RFQ block. It hedges
with futures, creates whole units at the close and carries the fraction overnight. Output: an
income statement that reconciles to cash plus positions at the close.

All parameters are STYLIZED (illustrative orders of magnitude, not any real fund or firm).
Run: python labs/walkthroughs/etf-market-maker.py   (~5 s, deterministic, seed 7)
Writes labs/walkthroughs/etf-market-maker.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LABS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LABS))
from common import simulate  # noqa: E402


def load_lab(dirname):
    """Import labs/<dirname>/lab.py as a module (every lab file is called lab.py)."""
    spec = importlib.util.spec_from_file_location("lab_" + dirname[:2], LABS / dirname / "lab.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod          # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


lab07 = load_lab("07-etf-nav-arbitrage")
lab05 = load_lab("05-avellaneda-stoikov-glft-quoting")
lab04 = load_lab("04-markout-analysis")
lab02 = load_lab("02-microprice-fair-value")

SEED = 7
T = 23_400                      # seconds in the 9:30-16:00 session (1-second steps)
CU = lab07.CU_SIZE              # 50,000 ETF shares per creation unit
LOT = 500                       # shares per screen fill
LOTS_PER_UNIT = CU // LOT       # 100 lots = 1 creation unit
Q_MAX = lab07.MAX_UNITS * LOTS_PER_UNIT   # inventory limit: 10 units (Lab 07's balance-sheet limit)
# quoting (GLFT in bps of fair value and 500-share lots)
A_PER_S = 0.07                  # fill rate of a quote AT fair value, each side (fills/s)
K_PER_BP = 0.67                 # fill rate falls by e^-0.67 per bp of distance -> base half-spread ~1.5 bps
GAMMA = 2.5e-6                  # risk aversion per (bp x lot): lean ~0.1 bp per unit of hedged inventory
AS_PRIOR_BPS = 0.5              # expected adverse selection per share used in the quote floor
BUY_BIAS = 0.20                 # today clients buy at 1.2x and sell at 0.8x the base rate
# news and fast arbitrageurs (Lab 05 world-B mechanism)
NEWS_PER_S = 1 / 60             # market-wide news about once a minute
JUMP_MEAN_BPS = 1.5             # mean |jump| of the market factor (exponential)
P_CANCEL = 0.5                  # share of stale quotes we cancel before the arbitrageur arrives
DISPLAY_LOTS = 4                # displayed size the arbitrageur takes (2,000 shares)
# block RFQ
BLOCK_T = 5_400                 # 11:00:00
BLOCK_UNITS = 5                 # client buys 250,000 shares
RFQ_MARGIN_BPS = 1.5
# hedge instruments and fees (stylized; see the walkthrough page)
F0, FUT_MULT, FUT_TICK, FUT_FEE = 6_000.0, 50.0, 0.25, 1.00    # E-mini-like; $ fee per contract
PEER_PX, PEER_HALF_SPREAD, PEER_TAKE_FEE = 100.0, 0.005, 0.0030  # top-100 ETF; $ per share
N_PEER = 100                    # peer ETF: 100 largest names (by day-0 cap), cap-weighted
REBATE = 0.0020                 # maker rebate per passive ETF share filled ($)
MOC_FEE = 0.0010                # closing-auction fee per basket share ($)
SEC_FEE = 20.60e-6              # SEC Section 31 fee per $ of sales (from 2026-04-04)
ETF_BORROW_BPS_YR = 30.0        # borrow on an ETF short carried overnight
CLOSE_SHARE = 0.10              # closing auction share of each stock's daily volume
HISTORY = 250                   # days of daily history for hedge ratios
HORIZONS = [0, 1, 10, 60, 300]


def index_returns(m, cols=None):
    """Daily returns of a cap-weighted index (all names, or the columns in cols); [k] = day k."""
    cap, ret = m.market_cap.to_numpy(), m.returns.to_numpy()
    if cols is not None:
        cap, ret = cap[:, cols], ret[:, cols]
    out = np.zeros(len(ret))
    out[1:] = (cap[:-1] * ret[1:]).sum(1) / cap[:-1].sum(1)
    return out


def pick_day(m, nav, idx_ret):
    """First 'ordinary' day after day 300: calm vol regime (0.95-1.05), the index up 0.2-0.8%, and
    an ETF-vs-index basis move under 5 bps (hedge ratio from the prior 250 days). Chosen so the
    income statement shows the economics of the business rather than one lucky basis move."""
    h = m.vol_regime.to_numpy()
    nav_r = np.zeros(len(nav))
    nav_r[1:] = np.diff(nav) / nav[:-1]
    for t in range(300, len(h)):
        x, y = idx_ret[t - HISTORY:t], nav_r[t - HISTORY:t]
        beta = np.cov(y, x)[0, 1] / np.var(x, ddof=1)
        if 0.95 <= h[t] <= 1.05 and 0.002 <= idx_ret[t] <= 0.008 and abs(nav_r[t] - beta * idx_ret[t]) < 5e-4:
            return t
    raise RuntimeError("no suitable day")


def intraday_paths(m, d, rng):
    """Cumulative intraday simple returns (stocks x T+1), bridged to day d's closes.

    Each factor and each specific return is a Brownian path with that day's vol; the market factor
    also gets news jumps. A linear drift correction makes every path end at the simulator's daily
    value, so every stock closes exactly at m.prices on day d.
    """
    h = m.vol_regime.to_numpy()[d]
    fac = m.factor_returns.columns
    n_f = len(fac)
    sd_f = (m.factor_vol[fac].to_numpy() * h)[:, None] / np.sqrt(T)
    inc = rng.standard_normal((n_f, T)) * sd_f
    # news jumps in the market factor; diffusion variance reduced so total daily variance is kept
    news = rng.random(T) < NEWS_PER_S
    jump = np.where(news, rng.exponential(JUMP_MEAN_BPS, T) * rng.choice([-1.0, 1.0], T), 0.0) / 1e4
    i_m = list(fac).index("market")
    var_m = (m.factor_vol["market"] * h) ** 2
    var_j = 2 * (JUMP_MEAN_BPS / 1e4) ** 2 * NEWS_PER_S * T
    inc[i_m] *= np.sqrt(max(var_m - var_j, 0.2 * var_m) / var_m)
    inc[i_m] += jump
    f_path = np.concatenate([np.zeros((n_f, 1)), np.cumsum(inc, axis=1)], axis=1)
    s = np.linspace(0, 1, T + 1)
    f_path += (m.factor_returns.iloc[d].to_numpy() - f_path[:, -1])[:, None] * s
    sv = m.specific_vol.iloc[d].to_numpy()[:, None] / np.sqrt(T)
    e_path = np.concatenate([np.zeros((len(sv), 1)),
                             np.cumsum(rng.standard_normal((len(sv), T)) * sv, axis=1)], axis=1)
    e_path += (m.specific_returns.iloc[d].to_numpy() - e_path[:, -1])[:, None] * s
    r_path = m.exposures[fac].to_numpy() @ f_path + e_path                # stocks x (T+1)
    return r_path, f_path[i_m], jump


def band_parts(etf, t, n_units=1, h_t=1.0):
    """Split Lab 07's no_arbitrage_band into its components by switching parts off."""
    st = h_t ** 2
    args = (etf["weights"][t], etf["half_spread"] * st, etf["daily_vol"][t], etf["adv"][t],
            etf["nav"][t] * CU, n_units)
    full_c, full_r = lab07.no_arbitrage_band(*args, etf_half_spread_bps=lab07.ETF_HALF_SPREAD_BPS * st)
    no_etf, _ = lab07.no_arbitrage_band(*args, etf_half_spread_bps=0.0)
    no_imp, _ = lab07.no_arbitrage_band(*args, etf_half_spread_bps=0.0, impact_coef=0.0)
    no_fee, _ = lab07.no_arbitrage_band(*args, etf_half_spread_bps=0.0, impact_coef=0.0, fee_usd=0.0)
    return {"create_bps": full_c, "redeem_bps": full_r, "etf_half_spread": full_c - no_etf,
            "basket_impact": no_etf - no_imp, "fee": no_imp - no_fee, "basket_half_spread": no_fee,
            "borrow_redeem_only": full_r - full_c, "create_ex_etf_half_spread": no_etf}


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    out = {"script": "labs/walkthroughs/etf-market-maker.py", "seed": SEED}

    # ------------------------------------------------------------------ 1. pre-open
    m = simulate.simulate_equity_market(n_stocks=200, n_days=1260, seed=SEED)   # Lab 07's world
    etf = lab07.build_etf(m)
    h = m.vol_regime.to_numpy()
    idx200_ret = index_returns(m)                                   # the futures' index
    top = np.argsort(-m.market_cap.to_numpy()[0])[:N_PEER]
    peer100_ret = index_returns(m, top)                              # the peer ETF's index
    d = pick_day(m, etf["nav"], idx200_ret)
    names = etf["names"]
    shares, cash = etf["shares"], etf["cash"]
    nav_prev = float(etf["nav"][d - 1])
    pre = band_parts(etf, d - 1, 1, h[d - 1])          # yesterday's close data: today's pre-open band
    w = etf["weights"][d - 1]
    out["preopen"] = {
        "day_index": d, "vol_regime": float(h[d]), "nav_prev_close": nav_prev,
        "unit_value_usd": nav_prev * CU, "cash_component_usd": float(cash),
        "top5_weights": [float(x) for x in np.sort(w)[::-1][:5]], "top10_weight": float(np.sort(w)[::-1][:10].sum()),
        "band_1unit": {k: float(v) for k, v in pre.items()},
        "lab07_mean_create_cost_bps": 7.379123,
    }

    # hedge ratios from daily history (days d-HISTORY .. d-1): ETF NAV vs the futures' index and vs peer ETF
    hist = slice(d - HISTORY, d)
    nav_ret = np.diff(etf["nav"])[d - HISTORY - 1:d - 1] / etf["nav"][d - HISTORY - 1:d - 1]
    mkt_ret = idx200_ret[hist]
    cap = m.market_cap.to_numpy()
    peer_ret = peer100_ret[hist]

    def hedge_stats(y, x):
        beta = np.cov(y, x)[0, 1] / np.var(x, ddof=1)
        resid = y - beta * x
        return float(beta), float(np.std(resid, ddof=1) * 1e4), float(np.corrcoef(y, x)[0, 1])

    b_fut, res_fut, rho_fut = hedge_stats(nav_ret, mkt_ret)
    b_peer, res_peer, rho_peer = hedge_stats(nav_ret, peer_ret)
    etf_vol_bps = float(np.std(nav_ret, ddof=1) * 1e4)

    # ------------------------------------------------------------------ 2. intraday world and fair value
    r_path, _, jump_mkt = intraday_paths(m, d, rng)
    p_prev = m.prices.iloc[d - 1].to_numpy()
    idx = [list(m.tickers).index(n) for n in names]
    px_basket = p_prev[idx][:, None] * (1 + r_path[idx])              # 50 x (T+1)
    fv = lab07.nav(px_basket.T, shares, cash)                          # NAV each second ($)
    assert abs(fv[-1] - etf["nav"][d]) < 1e-9, "bridge must hit Lab 07's closing NAV"
    beta_true = m.beta.to_numpy()[idx]
    jump_fv = (shares * p_prev[idx] * beta_true).sum() / CU * jump_mkt   # FV move caused by news ($)
    cap_prev = cap[d - 1]
    fut = F0 * (cap_prev[:, None] * (1 + r_path)).sum(0) / cap_prev.sum()
    peer = PEER_PX * (cap_prev[top, None] * (1 + r_path[top])).sum(0) / cap_prev[top].sum()
    jump_fut = F0 * (cap_prev * m.beta.to_numpy()).sum() / cap_prev.sum() * jump_mkt
    # intraday realized (1-minute) check of the hedge ratios
    mi = np.arange(0, T + 1, 60)
    r_e, r_f, r_p = (np.diff(np.log(x[mi])) for x in (fv, fut, peer))
    intr = {"beta_fut": float(np.cov(r_e, r_f)[0, 1] / np.var(r_f, ddof=1)), "rho_fut": float(np.corrcoef(r_e, r_f)[0, 1]),
            "rho_peer": float(np.corrcoef(r_e, r_p)[0, 1])}

    # hedge choice: cost of laying off q and holding it for tau (Lab 07 band for the basket)
    q_usd = BLOCK_UNITS * nav_prev * CU
    tau_days = (T - BLOCK_T) / T
    gamma_usd = GAMMA / (LOT * nav_prev / 1e4)    # GLFT's gamma per (bp x lot) restated per $
    basket_cost = band_parts(etf, d - 1, BLOCK_UNITS, h[d - 1])
    fut_cost_bps = (FUT_TICK / 2) / F0 * 1e4 + FUT_FEE / (F0 * FUT_MULT) * 1e4
    peer_cost_bps = (PEER_HALF_SPREAD + PEER_TAKE_FEE) / PEER_PX * 1e4
    choice = {}
    for name, c_bps, res_bps in (("futures", fut_cost_bps, res_fut), ("peer_etf", peer_cost_bps, res_peer),
                                 ("basket", basket_cost["basket_half_spread"] + basket_cost["basket_impact"], 0.0)):
        trade = 2 * c_bps if name != "basket" else c_bps        # in and out (basket: bought once, created)
        risk_sd = q_usd * res_bps / 1e4 * np.sqrt(tau_days)
        choice[name] = {"cost_bps_round_trip": float(trade), "cost_usd": float(trade / 1e4 * q_usd),
                        "residual_vol_bps_per_day": float(res_bps), "basis_sd_usd_to_close": float(risk_sd),
                        "objective_usd": float(trade / 1e4 * q_usd + 0.5 * gamma_usd * risk_sd ** 2)}

    # Lab 02 overlay: constituent microprices vs mids (tick $0.01, 1-tick spreads)
    g_table = np.array(json.loads((LABS / "02-microprice-fair-value" / "results.json").read_text())
                       ["microprice_adjustment_ticks_spread1"])
    def nav_shift_bps(imb):
        state = lab02.book_state(imb, np.ones_like(imb))          # spread 1 tick -> states 0..10
        adj = g_table[state] * 0.01                               # $ per share
        return float((shares * adj).sum() / CU / fv[0] * 1e4)
    all_up = nav_shift_bps(np.full(len(names), 0.6))
    rnd = [nav_shift_bps(rng.uniform(-1, 1, len(names))) for _ in range(2000)]
    wm_etf = lab02.weighted_mid(50.00, 50.01, 8000.0, 2000.0)        # ETF's own book, illustrative
    out["fair_value"] = {
        "beta_fut_daily": b_fut, "resid_vol_fut_bps_day": res_fut, "rho_fut_daily": rho_fut,
        "beta_peer_daily": b_peer, "resid_vol_peer_bps_day": res_peer, "rho_peer_daily": rho_peer,
        "etf_vol_bps_day": etf_vol_bps, "intraday_1min": intr,
        "news_events": int((jump_mkt != 0).sum()),
        "largest_news_jump_fv_bps": float(np.max(np.abs(jump_fv / fv[:-1])) * 1e4),
        "largest_news_jump_fut_bps": float(np.max(np.abs(jump_fut / fut[:-1])) * 1e4),
        "mean_abs_news_jump_fv_bps": float(np.mean(np.abs(jump_fv[jump_fv != 0] / fv[:-1][jump_fv != 0])) * 1e4),
        "nav_open": float(fv[0]), "nav_close": float(fv[-1]), "nav_return_bps": float((fv[-1] / fv[0] - 1) * 1e4),
        "fut_return_bps": float((fut[-1] / fut[0] - 1) * 1e4), "peer_return_bps": float((peer[-1] / peer[0] - 1) * 1e4),
        "microprice_all_names_imb0.6_nav_shift_bps": all_up,
        "microprice_random_imb_nav_shift_sd_bps": float(np.std(rnd)),
        "etf_own_book_weighted_mid_8000x2000": float(wm_etf),
        "etf_own_book_microprice_adj_ticks_imb0.6": float(g_table[lab02.book_state(np.array([0.6]), np.array([1]))[0]]),
    }
    out["hedge_choice_block"] = {"units": BLOCK_UNITS, "usd": q_usd, "hold_hours": tau_days * 6.5,
                                 "gamma_per_usd": gamma_usd, "instruments": choice}

    # ------------------------------------------------------------------ 3. quoting parameters
    sigma_b = res_fut / np.sqrt(T)                       # basis vol after the futures hedge, bps/sqrt(s)
    sigma_u = etf_vol_bps / np.sqrt(T)                   # unhedged ETF vol, bps/sqrt(s)
    d0_bid, _ = lab05.glft_quotes(0, GAMMA, sigma_b, A_PER_S, K_PER_BP, Q_MAX)
    c_hedged = float(lab05.glft_quotes(1, GAMMA, sigma_b, A_PER_S, K_PER_BP)[0] - d0_bid)
    c_unhedged = float(lab05.glft_quotes(1, GAMMA, sigma_u, A_PER_S, K_PER_BP)[0]
                       - lab05.glft_quotes(0, GAMMA, sigma_u, A_PER_S, K_PER_BP)[0])
    hedge_floor = 2 * fut_cost_bps                       # futures in and out per share hedged
    floor_bps = hedge_floor + AS_PRIOR_BPS
    band_c, band_r = pre["create_bps"], pre["redeem_bps"]
    rfq_bps = hedge_floor + basket_cost["create_ex_etf_half_spread"] + RFQ_MARGIN_BPS
    out["quoting"] = {
        "A_per_s": A_PER_S, "k_per_bp": K_PER_BP, "gamma": GAMMA, "lot_shares": LOT, "q_max_units": Q_MAX // LOTS_PER_UNIT,
        "sigma_basis_bps_per_sqrt_s": float(sigma_b), "sigma_etf_bps_per_sqrt_s": float(sigma_u),
        "half_spread_q0_bps": float(d0_bid), "lean_bps_per_unit_hedged": c_hedged * LOTS_PER_UNIT,
        "lean_bps_per_unit_unhedged": c_unhedged * LOTS_PER_UNIT, "floor_bps": float(floor_bps),
        "floor_hedge_part_bps": float(hedge_floor), "band_cap_create_bps": float(band_c), "band_cap_redeem_bps": float(band_r),
        "rfq": {"hedge_futures_bps": float(hedge_floor),
                "basket_and_fee_bps": float(basket_cost["create_ex_etf_half_spread"]),
                "basket_half_spread_bps": float(basket_cost["basket_half_spread"]),
                "basket_impact_bps": float(basket_cost["basket_impact"]), "fee_bps": float(basket_cost["fee"]),
                "margin_bps": RFQ_MARGIN_BPS, "quote_bps": float(rfq_bps)},
    }

    # ------------------------------------------------------------------ 4. the trading day
    q = 0                                         # ETF inventory in lots (negative = short)
    nfut = 0                                      # futures contracts held
    lines = {"spread_screen": 0.0, "spread_block": 0.0, "adverse": 0.0, "inv_etf": 0.0}
    cash_etf = 0.0
    fills = []                                    # time, price, side (+1 we bought), lots, segment
    fut_trades = []                               # time, contracts, mid
    q_path, skew_path, hb_path = np.zeros(T + 1), np.zeros(T + 1), np.zeros(T + 1)
    passive_shares = 0
    for t in range(1, T + 1):
        f_ref = fv[t - 1]
        db, da = lab05.glft_quotes(q, GAMMA, sigma_b, A_PER_S, K_PER_BP, Q_MAX)
        db, da = float(db), float(da)
        # floor: never quote inside hedge cost + expected adverse selection; cap: the creation band
        db = min(max(db, floor_bps), band_r) if np.isfinite(db) else db
        da = min(max(da, floor_bps), band_c) if np.isfinite(da) else da
        skew_path[t - 1] = (da - db) / 2                                  # center above fair value (bps)
        hb_path[t - 1] = (da + db) / 2
        if t == BLOCK_T:                                                   # RFQ block: client buys 5 units
            lots = BLOCK_UNITS * LOTS_PER_UNIT
            d_usd = rfq_bps * f_ref / 1e4
            sp, _, _ = lab05.step_pnl(q, 0, lots, 0.0, d_usd, 0.0, 0.0)
            lines["spread_block"] += sp * LOT
            cash_etf += lots * LOT * (f_ref + d_usd)
            fills.append((t - 0.5, f_ref + d_usd, -1, lots, "rfq_block"))
            q -= lots
            db, da = (float(x) for x in lab05.glft_quotes(q, GAMMA, sigma_b, A_PER_S, K_PER_BP, Q_MAX))
            db = min(max(db, floor_bps), band_r) if np.isfinite(db) else db
            da = min(max(da, floor_bps), band_c) if np.isfinite(da) else da
        db_usd, da_usd = db * f_ref / 1e4, da * f_ref / 1e4
        j_bps = jump_fv[t - 1] / f_ref * 1e4
        bought = sold = 0
        # fast arbitrageurs pick off the stale side when news moves fair value through our quote
        if j_bps > da and rng.random() > P_CANCEL:
            n = min(DISPLAY_LOTS, q + Q_MAX)
            if n > 0:
                sold += n
                fills.append((t - 0.5, f_ref + da_usd, -1, n, "fast_arb"))
        elif -j_bps > db and rng.random() > P_CANCEL:
            n = min(DISPLAY_LOTS, Q_MAX - q)
            if n > 0:
                bought += n
                fills.append((t - 0.5, f_ref - db_usd, +1, n, "fast_arb"))
        # uninformed clients: Poisson at A exp(-k delta); net buyers today
        if np.isfinite(da):
            n = min(rng.poisson(A_PER_S * (1 + BUY_BIAS) * np.exp(-K_PER_BP * da)), q - sold + bought + Q_MAX)
            if n > 0:
                sold += n
                fills.append((t - 0.5, f_ref + da_usd, -1, n, "client"))
        if np.isfinite(db):
            n = min(rng.poisson(A_PER_S * (1 - BUY_BIAS) * np.exp(-K_PER_BP * db)), Q_MAX - q - bought + sold)
            if n > 0:
                bought += n
                fills.append((t - 0.5, f_ref - db_usd, +1, n, "client"))
        diff_usd = fv[t] - fv[t - 1] - jump_fv[t - 1]
        sp, adv, inv = lab05.step_pnl(q, bought, sold, db_usd if bought else 0.0, da_usd if sold else 0.0,
                                      jump_fv[t - 1], diff_usd)
        lines["spread_screen"] += sp * LOT
        lines["adverse"] += adv * LOT
        lines["inv_etf"] += inv * LOT
        cash_etf += LOT * (sold * (f_ref + da_usd if sold else 0) - bought * (f_ref - db_usd if bought else 0))
        passive_shares += (bought + sold) * LOT
        q += bought - sold
        q_path[t] = q
        # hedge: target futures = -beta x ETF dollars / contract notional; trade when 1+ contract off
        target = int(np.round(-b_fut * q * LOT * fv[t] / (fut[t] * FUT_MULT)))
        if target != nfut:
            fut_trades.append((t, target - nfut, fut[t]))
            nfut = target
    skew_path[T], hb_path[T] = skew_path[T - 1], hb_path[T - 1]

    # ------------------------------------------------------------------ 5. close: create, unwind, carry
    q_shares = q * LOT
    units_short = -q_shares / CU
    n_create = int(np.floor(units_short)) if units_short > 0 else 0          # whole units only
    close_cost = band_parts(etf, d, max(n_create, 1), h[d])                  # today's closing data
    buyback_bps = close_cost["create_bps"] if n_create else 0.0              # rivals' offers for size ~ their band
    carry_units = units_short - n_create
    premium_close_bps = float(skew_path[T])                                  # ETF mid vs NAV (our skew)
    band_close = band_parts(etf, d, 1, h[d])                                # 1-unit band, as Lab 07's AP uses
    arb_extra = float(lab07.arb_decision(premium_close_bps, band_close["create_bps"], band_close["redeem_bps"],
                                         lab07.PREMIUM_PER_UNIT_BPS, lab07.MAX_UNITS))
    unit_value = fv[T] * CU
    basket_exec_usd = -(close_cost["basket_half_spread"] + close_cost["basket_impact"]) / 1e4 * unit_value * n_create
    fee_usd = -lab07.FEE_USD if n_create else 0.0
    basket_shares = shares * n_create
    moc_fee_usd = -MOC_FEE * basket_shares.sum()
    close_px = m.prices.iloc[d].to_numpy()[idx]
    auction_vol = m.volume.iloc[d].to_numpy()[idx] * CLOSE_SHARE
    part = basket_shares / auction_vol
    # futures: keep the hedge for the carried fraction, sell the rest at the close (half a tick)
    target_close = int(np.round(-b_fut * (q_shares + n_create * CU) * fv[T] / (fut[T] * FUT_MULT)))
    if target_close != nfut:
        fut_trades.append((T, target_close - nfut, fut[T]))
        nfut = target_close
    ft = np.array([(n, mid) for _, n, mid in fut_trades])
    fut_mtm = float((ft[:, 0] * (fut[T] - ft[:, 1])).sum() * FUT_MULT)
    fut_slip = float(-np.abs(ft[:, 0]).sum() * FUT_TICK / 2 * FUT_MULT)
    fut_fees = float(-np.abs(ft[:, 0]).sum() * FUT_FEE)
    carry_shares = q_shares + n_create * CU
    borrow_usd = -abs(carry_shares) * fv[T] * ETF_BORROW_BPS_YR / 1e4 / 360 if carry_shares < 0 else 0.0
    rebates = REBATE * passive_shares
    etf_sold_usd = sum(n * LOT * p for _, p, sd, n, _ in fills if sd < 0)
    sec_fee_usd = -SEC_FEE * etf_sold_usd

    inc = {
        "spread_capture_screen": lines["spread_screen"], "spread_capture_rfq_block": lines["spread_block"],
        "rebates_net_of_fees": rebates + fut_fees + moc_fee_usd + sec_fee_usd,
        "adverse_selection": lines["adverse"],
        "inventory_pnl_net_of_hedge": lines["inv_etf"] + fut_mtm,
        "hedge_slippage_futures": fut_slip,
        "basket_execution_at_close": basket_exec_usd,
        "creation_fee": fee_usd,
        "financing_and_borrow": borrow_usd,
    }
    total = float(sum(inc.values()))
    # reconcile: ETF cash + inventory marked at NAV, futures P&L, creation and carry costs
    direct = (cash_etf + q_shares * fv[T]) + (fut_mtm + fut_slip + fut_fees) + basket_exec_usd + fee_usd \
        + moc_fee_usd + borrow_usd + rebates + sec_fee_usd
    assert abs(direct - total) < 1e-6, (direct, total)
    etf_traded_usd = sum(abs(n) * LOT * p for _, p, _, n, _ in fills)
    gross_traded = etf_traded_usd + n_create * unit_value + np.abs(ft[:, 0]).sum() * F0 * FUT_MULT

    # ------------------------------------------------------------------ 6. markouts by counterparty (Lab 04)
    fdf = pd.DataFrame(fills, columns=["time", "price", "side", "lots", "segment"])
    fdf["shares"] = fdf["lots"] * LOT
    mid = pd.Series(fv, index=np.arange(T + 1, dtype=float))
    ok = fdf["time"] + max(HORIZONS) <= T
    mo = lab04.markouts(fdf[ok], mid, HORIZONS)
    mk = {}
    for seg in ("client", "fast_arb", "rfq_block", "all_screen"):
        sel = (fdf.loc[ok, "segment"] != "rfq_block") if seg == "all_screen" else (fdf.loc[ok, "segment"] == seg)
        sub = mo[sel.to_numpy()]
        wts = fdf.loc[ok, "shares"][sel.to_numpy()]
        blocks = (fdf.loc[ok, "time"][sel.to_numpy()] // 600).to_numpy()
        mean, se = lab04.markout_curve(sub, wts, blocks)
        mk[seg] = {"shares": int(wts.sum()), "fills": len(sub),
                   "markout_bps": {f"{k}s": float(v) for k, v in mean.items()},
                   "se_bps": {f"{k}s": float(v) for k, v in se.items()}}
    blk = fdf[fdf.segment == "rfq_block"].iloc[0]
    mk["rfq_block"]["markout_to_close_bps"] = float(blk.side * (fv[T] - blk.price) / blk.price * 1e4)
    mk["rfq_block"]["fv_move_after_block_to_close_bps"] = float((fv[T] / fv[BLOCK_T - 1] - 1) * 1e4)
    # hedged markout: the block's markout minus beta x the futures move (what the hedged desk keeps)
    t_b = BLOCK_T - 1
    hm = {}
    for hh in HORIZONS[1:] + [T - t_b]:
        e_mv = fv[min(t_b + hh, T)] / fv[t_b] - 1
        f_mv = fut[min(t_b + hh, T)] / fut[t_b] - 1
        key = "close" if hh == T - t_b else f"{hh}s"
        hm[key] = float(mk["rfq_block"]["markout_bps"]["0s"] + blk.side * (e_mv - b_fut * f_mv) * 1e4)
    mk["rfq_block"]["hedged_markout_bps"] = hm

    # ------------------------------------------------------------------ outputs
    seg_shares = fdf.groupby("segment")["shares"].sum().to_dict()
    seg_side = fdf.assign(signed=fdf.side * fdf.shares).groupby("segment")["signed"].sum().to_dict()
    out["day"] = {
        "fills": {k: int(v) for k, v in fdf.segment.value_counts().items()},
        "shares_by_segment": {k: int(v) for k, v in seg_shares.items()},
        "net_shares_we_bought_by_segment": {k: int(v) for k, v in seg_side.items()},
        "etf_shares_traded": int(fdf.shares.sum()), "etf_usd_traded": float(etf_traded_usd),
        "inventory_close_shares": int(q_shares), "inventory_close_units": float(-units_short),
        "inventory_min_units": float(q_path.min() / LOTS_PER_UNIT), "inventory_max_units": float(q_path.max() / LOTS_PER_UNIT),
        "inventory_just_after_block_units": float(q_path[BLOCK_T] / LOTS_PER_UNIT),
        "inventory_at_1300_units": float(q_path[12_600] / LOTS_PER_UNIT),
        "mean_quoted_half_spread_bps": float(hb_path.mean()), "mean_abs_skew_bps": float(np.abs(skew_path).mean()),
        "skew_at_close_bps": premium_close_bps, "max_skew_bps": float(skew_path.max()),
        "futures_trades": len(fut_trades), "futures_contracts_traded": int(np.abs(ft[:, 0]).sum()),
        "futures_max_position": int(max(abs(n) for n in np.cumsum(ft[:, 0]))), "futures_close_position": int(nfut),
        "futures_notional_per_contract_open": F0 * FUT_MULT,
    }
    # unhedged dollar delta after the hedge (integer contracts), per second
    pos_f = np.zeros(T + 1)
    for tt, n, _ in fut_trades:
        pos_f[int(tt):] += n
    resid = q_path * LOT * fv * b_fut + pos_f * fut * FUT_MULT
    out["day"]["max_residual_delta_usd_after_hedge"] = float(np.max(np.abs(resid[1:T])))
    clock = {"09:30": 0, "10:30": 3600, "11:00 after block": BLOCK_T, "13:00": 12_600, "15:00": 19_800,
             "15:50 MOC cutoff": 22_800, "16:00": T}
    out["timeline"] = {k: {"inventory_units": float(q_path[v] / LOTS_PER_UNIT), "futures": int(pos_f[v]),
                           "skew_bps": float(skew_path[v]), "fv": float(fv[v])} for k, v in clock.items()}
    out["close"] = {
        "units_short": float(units_short), "n_create": n_create, "carry_units": float(carry_units),
        "carry_shares": int(-carry_shares),
        "create_cost_per_unit_bps": float(close_cost["create_ex_etf_half_spread"]),
        "create_cost_parts_bps": {k: float(close_cost[k]) for k in ("basket_half_spread", "basket_impact", "fee")},
        "buyback_cost_per_unit_bps_rivals_band": float(buyback_bps),
        "carry_borrow_bps_per_day": ETF_BORROW_BPS_YR / 360,
        "closing_premium_bps": premium_close_bps, "arb_decision_extra_units": arb_extra,
        "band_today_1unit_create_redeem_bps": [float(band_close["create_bps"]), float(band_close["redeem_bps"])],
        "basket_shares_bought": int(basket_shares.sum()), "basket_usd": float((basket_shares * close_px).sum()),
        "moc_participation_max": float(part.max()), "moc_participation_capweighted": float((w * part).sum()),
        "futures_sold_at_close": int(-fut_trades[-1][1]) if fut_trades[-1][0] == T else 0,
    }
    out["income_statement_usd"] = {k: round(float(v), 2) for k, v in inc.items()}
    out["income_statement_usd"]["net_trading_income"] = round(total, 2)
    out["income_statement_detail_usd"] = {
        "inventory_etf_mtm": round(lines["inv_etf"], 2), "inventory_futures_mtm": round(fut_mtm, 2),
        "rebates": round(rebates, 2), "futures_fees": round(fut_fees, 2), "moc_fees": round(moc_fee_usd, 2),
        "sec_section31_fee": round(sec_fee_usd, 2), "etf_sold_usd": round(etf_sold_usd, 2)}
    out["income_statement_bps_of_etf_traded"] = {k: round(float(v) / etf_traded_usd * 1e4, 3) for k, v in
                                                 {**inc, "net_trading_income": total}.items()}
    out["gross_usd_traded_all_legs"] = float(gross_traded)
    out["markouts"] = mk
    out["horizons_s"] = HORIZONS
    path = Path(__file__).with_suffix(".json")
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ("preopen", "quoting", "day", "close", "income_statement_usd",
                                          "income_statement_bps_of_etf_traded")}, indent=1))
    print("markouts:", json.dumps({k: v["markout_bps"] for k, v in mk.items()}, indent=1))
    print(f"done in {time.time() - t0:.1f} s -> {path}")


if __name__ == "__main__":
    main()
