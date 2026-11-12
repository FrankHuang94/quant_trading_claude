"""Walkthrough helper: a book-level options market maker on Lab 06's synthetic market.

Supports docs/03-algorithms/h-end-to-end-walkthroughs/walkthrough-options-market-maker.md.

Lab 06 sells one straddle a week. This script runs a whole (toy) book for N five-day weeks on the
same Heston market (simulate_option_market, seed 7) and reuses Lab 06's CORE ALGORITHM:
  1. Surface: every hour, refit one raw-SVI smile per expiry (fit_smile) to NOISY screen mids
     (true implied vol + 0.5 vol pt noise, calls and puts quoted separately).
  2. Theo: Black-Scholes at the fitted vol, sticky strike between refits.
  3. Quotes: theo +/- half-width (0.5 vol pt x vega x (1 + 3|k|)), leaned against the book's vega
     in that expiry; one side pulled when an expiry's vega limit is hit.
  4. Fills: three customer types (retail, put-buying institutions, call overwriters) pick the
     better of our quote and a competitor quoting around the true value.
  5. Delta hedge: delta_hedge_pnl on the book's share delta (band, checked every 15 min, 1 bp).
  6. Attribution: greeks_attribution per fill (padded before the fill), summed to the book,
     per day and per week. Components sum exactly to the mark-to-market P&L.
All marks are the true (risk-neutral Heston) values, as in Lab 06; the desk's own fit error
therefore shows up as edge lost to "winner's curse" selection.

Run: python labs/walkthroughs/options-market-maker.py [--seed 7] [--weeks 12]   (~50 s; SVI refits dominate)
Writes labs/walkthroughs/options-market-maker.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common import options, simulate, utils  # noqa: E402

_spec = importlib.util.spec_from_file_location("lab06", ROOT / "06-options-mm-delta-hedging" / "lab.py")
lab06 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lab06)
fit_smile, delta_hedge_pnl, greeks_attribution = lab06.fit_smile, lab06.delta_hedge_pnl, lab06.greeks_attribution

SPD = 26                                   # 15-minute steps per day (Lab 06 grid)
DAYS = 5                                   # one trading week
EXPIRIES = (10, 30, 60)                    # trading days to expiry at Monday's open
MONEYNESS = np.round(np.arange(0.80, 1.2001, 0.025), 3)   # 17 listed strikes per expiry
MULT = 100
QUOTE_NOISE = 0.005                        # sd of screen-mid implied-vol noise (0.5 vol pt)
REFIT_EVERY = 4                            # steps: refit the surface hourly
HW_VOL = 0.005                             # ATM half-width 0.5 vol pt (= Lab 06 EDGE_VOL)
HW_WING = 3.0                              # half-width x (1 + 3 |ln K/S|): wider in the wings
MIN_HALF = 0.01                            # $ per share
LEAN_VOL_PER_1K = 0.0005                   # lean 0.05 vol pt per $1,000/vol pt of expiry vega
LEAN_CAP = 0.005                           # lean capped at 0.5 vol pt
VEGA_LIMIT = 5_000.0                       # $ per vol pt per expiry: pull the side that adds risk
BAND_SHARES = 1_500                        # hedge when |book delta| > 1,500 shares
COST_BPS = 1.0                             # Lab 06 hedge cost
# customer flow: orders per day, expiry probabilities, option type, |K/S - 1| range, P(buy), size
FLOW = {
    "retail": dict(rate=300, exp_p=(0.75, 0.25, 0.0), call_p=0.6, otm=(0.0, 0.10), buy_p=0.75, size=(1, 10)),
    "institution": dict(rate=2, exp_p=(0.0, 0.5, 0.5), call_p=0.0, otm=(0.05, 0.15), buy_p=1.0, size=(50, 250)),
    "overwriter": dict(rate=2, exp_p=(0.0, 1.0, 0.0), call_p=1.0, otm=(0.05, 0.10), buy_p=0.0, size=(50, 250)),
}
COMPONENTS = ["quoted_edge", "theta", "gamma", "vega", "vanna", "volga", "delta_hedge_residual",
              "hedging_costs", "unexplained", "total"]


def price_grid(om, n_weeks):
    """True marks, implied vols and Greeks for every listed series, every 15 minutes, every week."""
    n = DAYS * SPD
    gidx = (np.arange(n_weeks) * DAYS)[:, None] * SPD + np.arange(n + 1)[None, :]       # (W, n+1)
    S = om.path["S"].to_numpy()[gidx]
    vQ = om.path["v"].to_numpy()[gidx] * (1 + om.cfg.vrp)
    K = np.round(S[:, :1] * MONEYNESS[None, :] * 2) / 2                                # $0.50 strikes
    T = (np.array(EXPIRIES)[:, None] * SPD - np.arange(n + 1)[None, :]) / (252.0 * SPD)  # (E, n+1)
    shp = (n_weeks, len(EXPIRIES), len(MONEYNESS), n + 1)
    Sb, Kb = np.broadcast_to(S[:, None, None, :], shp), np.broadcast_to(K[:, None, :, None], shp)
    Tb, vb = np.broadcast_to(T[None, :, None, :], shp), np.broadcast_to(vQ[:, None, None, :], shp)
    call = lab06.heston_price_bucketed(Sb, Kb, Tb, vb, om, True)
    put = call - Sb + Kb                                                                # parity, r = 0
    otm = Kb >= Sb
    iv = options.implied_vol(np.where(otm, call, put), Sb, Kb, Tb, 0.0, otm)
    iv = lab06.forward_fill(iv)
    iv = lab06.forward_fill(iv[..., ::-1])[..., ::-1]                                   # leading NaNs
    ok = np.isfinite(iv).all(-1)                                                        # quotable series
    iv = np.where(np.isfinite(iv), iv, 0.2)
    gc, gp = options.bs_greeks(Sb, Kb, Tb, 0.0, iv, True), options.bs_greeks(Sb, Kb, Tb, 0.0, iv, False)
    vanna, volga = lab06.bs_vanna_volga(Sb, Kb, Tb, iv)
    return dict(S=S, K=K, T=T, call=call, put=put, iv=iv, ok=ok, gc=gc, gp=gp, vanna=vanna, volga=volga,
                dt=1.0 / (252.0 * SPD), n=n)


def draw_orders(rng, n):
    """Pre-drawn customer orders per step (common random numbers across runs)."""
    orders = []
    for typ, f in FLOW.items():
        counts = rng.poisson(f["rate"] / SPD, n)
        for s in np.flatnonzero(counts):
            for _ in range(counts[s]):
                orders.append(dict(step=int(s), type=typ, e=int(rng.choice(3, p=f["exp_p"])),
                                   is_call=bool(rng.random() < f["call_p"]), otm=rng.uniform(*f["otm"]),
                                   buy=bool(rng.random() < f["buy_p"]),
                                   size=int(rng.integers(f["size"][0], f["size"][1] + 1)), u=rng.random()))
    orders.sort(key=lambda o: o["step"])
    return orders


def fit_surfaces(g, w, noise):
    """1. Every hour, fit one raw-SVI smile per expiry to noisy call and put mids (Lab 06 fit_smile)."""
    n, S, K, T, iv, ok = g["n"], g["S"][w], g["K"][w], g["T"], g["iv"][w], g["ok"][w]
    fits = np.full((n // REFIT_EVERY + 1, len(EXPIRIES), len(MONEYNESS)), np.nan)
    fit_err, raw_err = [], []
    for r, s in enumerate(range(0, n, REFIT_EVERY)):
        k = np.log(K / S[s])
        for e in range(len(EXPIRIES)):
            m = ok[e]
            nz = noise[r, e]                                                   # (2, M): call and put mids
            q_iv = np.concatenate([iv[e, m, s] + nz[0, m], iv[e, m, s] + nz[1, m]])
            fits[r, e] = fit_smile(np.concatenate([k[m], k[m]]), q_iv, T[e, s], "svi")(k)
            fit_err.append(np.c_[k[m], (fits[r, e, m] - iv[e, m, s]) * 100])
            raw_err.append(np.abs(nz[:, m]).ravel() * 100)
    return fits, np.vstack(fit_err), np.concatenate(raw_err)


def run_week(g, w, orders, fits, lean_on=True):
    """Quote, fill and hedge one week; return fills, book delta path, limit hits."""
    n, S, K, T = g["n"], g["S"][w], g["K"][w], g["T"]
    iv, ok = g["iv"][w], g["ok"][w]
    vega = g["gc"]["vega"][w]                           # per share per 1.00 vol = $ per vol pt per contract
    dC, dP = g["gc"]["delta"][w], g["gp"]["delta"][w]
    mark = {True: g["call"][w], False: g["put"][w]}
    pos = np.zeros((len(EXPIRIES), len(MONEYNESS), 2))   # net contracts [expiry, strike, call?]
    fills, book_delta, limit_hits = [], np.zeros(n + 1), 0
    oi = 0
    for s in range(n + 1):
        sig_fit = fits[min(s, n - 1) // REFIT_EVERY]                         # sticky strike between refits
        V = np.einsum("emc,em->e", pos, vega[:, :, s])                       # book vega by expiry, $/vol pt
        while oi < len(orders) and orders[oi]["step"] == s and s < n:
            o = orders[oi]; oi += 1
            e, c = o["e"], o["is_call"]
            target = S[s] * (1 + o["otm"]) if c else S[s] * (1 - o["otm"])
            j = int(np.argmin(np.abs(K - target) + 1e9 * ~ok[e]))
            kk = np.log(K[j] / S[s])
            theo_g = options.bs_greeks(S[s], K[j], T[e, s], 0.0, sig_fit[e, j], c)
            theo = options.bs_price(S[s], K[j], T[e, s], 0.0, sig_fit[e, j], c)   # 2. theo
            hw_v = HW_VOL * (1 + HW_WING * abs(kk))                                # 3. width
            half = max(MIN_HALF, hw_v * theo_g["vega"])
            lean_v = np.clip(-V[e] / 1000 * LEAN_VOL_PER_1K, -LEAN_CAP, LEAN_CAP) if lean_on else 0.0
            lean = lean_v * theo_g["vega"]                                         # short vega -> raise
            fair = mark[c][e, j, s]
            half_c = max(MIN_HALF, hw_v * vega[e, j, s])                           # competitor, true value
            if o["buy"]:                                                           # customer buys: we sell
                if V[e] < -VEGA_LIMIT:
                    limit_hits += 1
                    continue
                px = theo + half + lean
                p = np.clip(0.5 + (fair + half_c - px) / (2 * half_c), 0.02, 0.98)
                q = -o["size"]
            else:
                if V[e] > VEGA_LIMIT:
                    limit_hits += 1
                    continue
                px = theo - half + lean
                p = np.clip(0.5 + (px - (fair - half_c)) / (2 * half_c), 0.02, 0.98)
                q = o["size"]
            if o["u"] < p:                                                         # 4. fill
                pos[e, j, int(c)] += q
                V[e] += q * vega[e, j, s]
                fills.append(dict(step=s, e=e, j=j, call=c, q=q, px=float(px), type=o["type"],
                                  theo=float(theo), fair=float(fair),
                                  vol_err=float(sig_fit[e, j] - iv[e, j, s]) * 100))
        book_delta[s] = MULT * (np.sum(pos[:, :, 1] * dC[:, :, s]) + np.sum(pos[:, :, 0] * dP[:, :, s]))
    return fills, book_delta, limit_hits


def fill_arrays(g, w, fills):
    """Per-fill position paths (value, vol, Greeks), constant/zero before the fill step."""
    n = g["n"]
    t = np.arange(n + 1)
    rows = {k: [] for k in ("value", "vol", "delta", "gamma", "vega", "theta", "vanna", "volga")}
    premium = []
    for f in fills:
        e, j, c, s, q = f["e"], f["j"], f["call"], f["step"], f["q"]
        gr = g["gc"] if c else g["gp"]
        live = t >= s
        scale = q * MULT
        val = scale * (g["call"] if c else g["put"])[w, e, j]
        rows["value"].append(np.where(live, val, val[s]))
        rows["vol"].append(np.where(live, g["iv"][w, e, j], g["iv"][w, e, j, s]))
        for name in ("delta", "gamma", "vega", "theta"):
            rows[name].append(np.where(live, scale * gr[name][w, e, j], 0.0))
        rows["vanna"].append(np.where(live, scale * g["vanna"][w, e, j], 0.0))
        rows["volga"].append(np.where(live, scale * g["volga"][w, e, j], 0.0))
        premium.append(-q * MULT * f["px"])                     # cash: + when we sell
    return {k: np.array(v) for k, v in rows.items()}, np.array(premium)


def hedge_costs_by_step(S, shares, bps=COST_BPS):
    """Lab 06 cost formula, but per step: |trade| x price x bps (+ unwind at the end)."""
    prev = np.concatenate([[0.0], shares[:-1]])
    c = np.abs(shares - prev) * S[:-1] * bps / 1e4
    c[-1] += abs(shares[-1]) * S[-1] * bps / 1e4
    return c


def attribute(g, w, arr, premium, fill_steps, shares, step_costs, lo, hi):
    """greeks_attribution over steps lo..hi for every fill opened before hi; summed to the book."""
    sel = fill_steps < hi
    if not sel.any():
        return {k: 0.0 for k in COMPONENTS}
    sl = slice(lo, hi + 1)
    a = {k: v[sel][:, sl] for k, v in arr.items()}
    prem = np.where(fill_steps[sel] < lo, -a["value"][:, 0], premium[sel])      # carried at the open mark
    m = sel.sum()
    S = np.broadcast_to(g["S"][w, sl], a["value"].shape)
    greeks = {k: a[k] for k in ("delta", "gamma", "vega", "theta", "vanna", "volga")}
    h = np.broadcast_to(shares[lo:hi] / m, (m, hi - lo))                       # book hedge, pro rata
    out = greeks_attribution(a["value"], S, a["vol"], greeks, h, g["dt"], prem,
                             costs=np.full(m, step_costs[lo:hi].sum() / m))
    return {k: float(np.sum(out[k])) for k in COMPONENTS}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--weeks", type=int, default=12)
    args = ap.parse_args()
    t0 = time.time()
    W = args.weeks
    om = simulate.simulate_option_market(n_days=W * DAYS + 1, seed=args.seed)
    assert om.cfg.steps_per_day == SPD
    g = price_grid(om, W)
    n = g["n"]
    rng = np.random.default_rng(args.seed + 1000)
    weeks = {True: [], False: []}
    for w in range(W):
        orders = draw_orders(rng, n)
        noise = rng.normal(0, QUOTE_NOISE, (n // REFIT_EVERY + 1, len(EXPIRIES), 2, len(MONEYNESS)))
        fits, fit_err, raw_err = fit_surfaces(g, w, noise)
        for lean_on in (True, False):
            fills, bdelta, hits = run_week(g, w, orders, fits, lean_on)
            arr, prem = fill_arrays(g, w, fills)
            steps = np.array([f["step"] for f in fills])
            S = g["S"][w]
            h = delta_hedge_pnl(S, bdelta, band=BAND_SHARES, cost_bps=COST_BPS)
            sc = hedge_costs_by_step(S, h["shares"])
            assert abs(sc.sum() - h["costs"]) < 1e-6
            days = [attribute(g, w, arr, prem, steps, h["shares"], sc, d * SPD, (d + 1) * SPD) for d in range(DAYS)]
            week = attribute(g, w, arr, prem, steps, h["shares"], sc, 0, n)
            assert all(abs(sum(d[k] for d in days) - week[k]) < 1e-6 * max(1, abs(week[k]))
                       for k in ("quoted_edge", "theta", "gamma", "vega", "total"))
            # what the desk thinks it earned (vs its own theo) vs edge against the fair mark
            edge_theo = sum(-f["q"] * MULT * (f["px"] - f["theo"]) for f in fills)
            contracts = {t: sum(abs(f["q"]) for f in fills if f["type"] == t) for t in FLOW}
            edge_by = {t: sum(-f["q"] * MULT * (f["px"] - f["fair"]) for f in fills if f["type"] == t) for t in FLOW}
            vega_by = {t: sum(f["q"] * g["gc"]["vega"][w, f["e"], f["j"], f["step"]] for f in fills
                              if f["type"] == t) for t in FLOW}
            eod = np.arange(1, DAYS + 1) * SPD
            close_vega = {}
            for e in range(len(EXPIRIES)):
                v = np.zeros(DAYS)
                for f in fills:
                    if f["e"] == e:
                        v += np.where(f["step"] < eod, f["q"] * g["gc"]["vega"][w, e, f["j"], eod], 0.0)
                close_vega[f"{EXPIRIES[e]}d"] = v
            book_gamma = np.zeros(DAYS)
            for f in fills:
                gr = g["gc"] if f["call"] else g["gp"]
                book_gamma += np.where(f["step"] < eod, f["q"] * MULT * gr["gamma"][w, f["e"], f["j"], eod], 0.0)
            # hedge-policy comparison on the same book delta path (only residual and costs change)
            dS = np.diff(S)
            pol = {}
            for lbl, kw in (("15 min", {"rebalance_every": 1}), ("hourly", {"rebalance_every": 4}),
                            ("daily", {"rebalance_every": SPD}), (f"band {BAND_SHARES}", {"band": BAND_SHARES})):
                hh = delta_hedge_pnl(S, bdelta, cost_bps=COST_BPS, **kw)
                pol[lbl] = dict(costs=float(hh["costs"]), rebalances=float(hh["n_rebalances"]),
                                residual=float(np.sum((hh["shares"] + bdelta[:-1]) * dS)))
            weeks[lean_on].append(dict(
                week=w, days=days, week_total=week, n_fills=len(fills), contracts=contracts,
                edge_by_type=edge_by, vega_by_type=vega_by, edge_vs_own_theo=edge_theo,
                close_vega=close_vega, close_gamma_shares_per_usd=book_gamma, hedge=pol,
                hedge_rebalances=float(h["n_rebalances"]), hedge_shares_traded=float(np.abs(np.diff(
                    np.concatenate([[0], h["shares"], [0]]))).sum()),
                limit_hits=hits, spot_open=float(S[0]), spot_close=float(S[-1]),
                atm30_iv_open=float(np.interp(0, np.log(g["K"][w] / S[0]), g["iv"][w, 1, :, 0])),
                atm30_iv_close=float(np.interp(0, np.log(g["K"][w] / S[-1]), g["iv"][w, 1, :, -1])),
                rv_week=float(np.sqrt(252 * SPD * np.mean(np.diff(np.log(S)) ** 2))),      # from 15-min returns
                close_spot=S[SPD::SPD], close_atm30_iv=[float(np.interp(0, np.log(g["K"][w] / S[t]), g["iv"][w, 1, :, t]))
                                                       for t in range(SPD, n + 1, SPD)],
                fit_abs_err=float(np.mean(np.abs(fit_err[:, 1]))),
                fit_abs_err_wings=float(np.mean(np.abs(fit_err[np.abs(fit_err[:, 0]) > 0.15, 1]))),
                raw_abs_err=float(np.mean(raw_err)),
                fill_vol_abs_err=float(np.mean([abs(f["vol_err"]) for f in fills]))))

    on, off = weeks[True], weeks[False]
    tot = np.array([x["week_total"]["total"] for x in on])
    feat = on[int(np.argsort(tot)[len(tot) // 2])]                     # the median week
    mean = lambda lst, k: float(np.mean([x["week_total"][k] for x in lst]))  # noqa: E731
    sd = lambda lst, k: float(np.std([x["week_total"][k] for x in lst], ddof=1))  # noqa: E731
    ctr = lambda x: sum(x["contracts"].values())  # noqa: E731
    res = {
        "script": "labs/walkthroughs/options-market-maker.py", "seed": args.seed, "weeks": W,
        "units": "$ for the whole book unless stated; vega $ per vol point; gamma shares per $1",
        "setup": dict(expiries_days=EXPIRIES, n_strikes=len(MONEYNESS), quote_noise_volpts=QUOTE_NOISE * 100,
                      refit_every_min=REFIT_EVERY * 15, half_width_atm_volpts=HW_VOL * 100, wing_mult=HW_WING,
                      lean_volpts_per_1k_vega=LEAN_VOL_PER_1K * 100, lean_cap_volpts=LEAN_CAP * 100,
                      vega_limit_per_expiry=VEGA_LIMIT, hedge_band_shares=BAND_SHARES, cost_bps=COST_BPS,
                      flow={k: {kk: vv for kk, vv in v.items()} for k, v in FLOW.items()}),
        "fit": dict(raw_quote_abs_err_volpts=float(np.mean([x["raw_abs_err"] for x in on])),
                    svi_fit_abs_err_volpts=float(np.mean([x["fit_abs_err"] for x in on])),
                    svi_fit_abs_err_wings_volpts=float(np.mean([x["fit_abs_err_wings"] for x in on])),
                    theo_vol_abs_err_at_fill_volpts=float(np.mean([x["fill_vol_abs_err"] for x in on]))),
        "featured_week": dict(
            rule="median weekly P&L of the lean-on runs", week_index=feat["week"],
            spot_open=feat["spot_open"], spot_close=feat["spot_close"],
            atm30_iv_open=feat["atm30_iv_open"], atm30_iv_close=feat["atm30_iv_close"], rv_week_15min=feat["rv_week"],
            close_spot=[round(float(x), 2) for x in feat["close_spot"]],
            close_atm30_iv=[round(x, 4) for x in feat["close_atm30_iv"]],
            days={f"day{d + 1}": {k: round(v, 1) for k, v in feat["days"][d].items()} for d in range(DAYS)},
            week={k: round(v, 1) for k, v in feat["week_total"].items()},
            n_fills=feat["n_fills"], contracts=feat["contracts"],
            edge_by_type={k: round(v, 1) for k, v in feat["edge_by_type"].items()},
            vega_by_type={k: round(v, 1) for k, v in feat["vega_by_type"].items()},
            edge_vs_own_theo=round(feat["edge_vs_own_theo"], 1),
            close_vega={k: [round(x, 0) for x in v] for k, v in feat["close_vega"].items()},
            close_gamma_shares_per_usd=[round(x, 0) for x in feat["close_gamma_shares_per_usd"]],
            hedge_rebalances=feat["hedge_rebalances"], hedge_shares_traded=feat["hedge_shares_traded"],
            hedge_policies=feat["hedge"], limit_hits=feat["limit_hits"]),
        "all_weeks_lean_on": dict(
            mean={k: round(mean(on, k), 1) for k in COMPONENTS}, sd={k: round(sd(on, k), 1) for k in COMPONENTS},
            mean_contracts=float(np.mean([ctr(x) for x in on])),
            contracts_by_type={t: float(np.mean([x["contracts"][t] for x in on])) for t in FLOW},
            edge_by_type={t: float(np.mean([x["edge_by_type"][t] for x in on])) for t in FLOW},
            edge_per_contract_by_type={t: float(np.sum([x["edge_by_type"][t] for x in on])
                                                / max(1, np.sum([x["contracts"][t] for x in on]))) for t in FLOW},
            vega_by_type={t: float(np.mean([x["vega_by_type"][t] for x in on])) for t in FLOW},
            edge_vs_own_theo=float(np.mean([x["edge_vs_own_theo"] for x in on])),
            weekly_totals=[round(float(x), 0) for x in tot],
            share_weeks_losing=float(np.mean(tot < 0)), worst_week=float(tot.min()), best_week=float(tot.max()),
            mean_abs_close_vega={k: float(np.mean([np.abs(x["close_vega"][k]).mean() for x in on]))
                                 for k in on[0]["close_vega"]},
            limit_hits=float(np.mean([x["limit_hits"] for x in on])),
            hedge_policies={p: {m: float(np.mean([x["hedge"][p][m] for x in on])) for m in ("costs", "rebalances")}
                            | {"residual_sd": float(np.std([x["hedge"][p]["residual"] for x in on], ddof=1))}
                            for p in on[0]["hedge"]}),
        "all_weeks_lean_off": dict(
            mean={k: round(mean(off, k), 1) for k in COMPONENTS}, sd={k: round(sd(off, k), 1) for k in COMPONENTS},
            mean_contracts=float(np.mean([ctr(x) for x in off])),
            mean_abs_close_vega={k: float(np.mean([np.abs(x["close_vega"][k]).mean() for x in off]))
                                 for k in off[0]["close_vega"]},
            limit_hits=float(np.mean([x["limit_hits"] for x in off]))),
    }
    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(utils._jsonable(res), indent=2) + "\n", encoding="utf-8")
    fw = res["featured_week"]
    print(f"{W} weeks, featured week {fw['week_index']}: spot {fw['spot_open']:.2f} -> {fw['spot_close']:.2f}, "
          f"30d ATM IV {fw['atm30_iv_open']:.1%} -> {fw['atm30_iv_close']:.1%}, RV (15-min) {fw['rv_week_15min']:.1%}")
    print("  closes", fw["close_spot"], fw["close_atm30_iv"])
    print("  featured week:", {k: v for k, v in fw["week"].items()})
    for d, v in fw["days"].items():
        print(f"  {d}:", v)
    print("  contracts", fw["contracts"], "edge", fw["edge_by_type"], "vega", fw["vega_by_type"])
    print("  close vega", fw["close_vega"], "gamma", fw["close_gamma_shares_per_usd"])
    print("  hedge", fw["hedge_policies"], "rebal", fw["hedge_rebalances"], "limit hits", fw["limit_hits"])
    print("  fit", res["fit"])
    for lbl in ("all_weeks_lean_on", "all_weeks_lean_off"):
        print(lbl, json.dumps(utils._jsonable(res[lbl]), indent=None))
    print(f"done in {time.time() - t0:.1f} s -> {out.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
