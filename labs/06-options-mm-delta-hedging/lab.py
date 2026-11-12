"""Lab 06: options market making -- smile fitting, delta hedging and Greeks P&L attribution.

What it demonstrates
  (a) Fitting a smile per expiry to a synthetic option chain (Heston world with a variance risk
      premium, labs/common/simulate.py): quadratic in log-moneyness vs raw SVI. In-sample both fit
      to a fraction of a vol point; fitted on the inner strikes and extrapolated to the wings, the
      parabola misses by far more than SVI (pitfall: a local fit is not a surface).
  (b) A market maker sells a 30-day at-the-money straddle once a week at its fitted ATM vol plus
      0.5 vol points of edge and delta-hedges it to expiry: every 15 minutes, hourly, daily, weekly,
      or only when net delta leaves a band. Hedge trades pay 1 bp.
  (c) Greeks P&L attribution on the 15-minute grid:
          quoted edge + theta + gamma + vega + vanna + volga + delta-hedge residual
          + hedging costs + unexplained (Taylor remainder) = total P&L.
      With r = 0, theta + gamma is exactly sum 1/2 Gamma S^2 (sigma_impl^2 - sigma_real^2) dt:
      the short straddle earns the gap between implied and realized variance, weighted by dollar
      gamma. Hedge frequency changes the VARIANCE of P&L (through the delta-hedge residual), not
      its mean (to first order, before costs); costs make frequent hedging expensive.
  (d) Implied vs subsequently realized vol over time: the variance risk premium (VRP) the seller
      harvests, compared with the premium planted in the simulator.

Supports: docs/02-strategies/a-liquidity-provision/options-market-making.md,
          docs/03-algorithms/f-market-making-and-hft-algorithms/options-pricing-and-vol-surfaces-for-mm.md,
          docs/03-algorithms/f-market-making-and-hft-algorithms/hedging-algorithms.md

Run: python labs/06-options-mm-delta-hedging/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import options, simulate, utils  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.optimize import least_squares  # noqa: E402

TENOR_DAYS = 30          # straddle maturity, trading days
EDGE_VOL = 0.005         # quoted edge: sell at fitted vol + 0.5 vol points (stylized)
COST_BPS = 1.0           # cost per $ of stock traded when hedging (half-spread + fees, stylized)
MULT = 100               # contract multiplier: one straddle = 1 call + 1 put on 100 shares
DELTA_BANDS = (0.05, 0.10)   # move-based hedging: rebalance when |net delta| > band (per straddle share)
TIME_POLICIES = [("15 min", 1), ("hourly", 4), ("daily", 26), ("weekly", 130)]   # steps (26/day)
COLORS = {"15 min": "#2a78d6", "daily": "#eb6834", "gross": "#2a78d6", "net": "#eb6834",
          "iv": "#2a78d6", "rv": "#eb6834", "pos": "#1baf7a", "neg": "#d6452a", "grey": "#7a7a7a"}


# =====================================================================================
# === CORE ALGORITHM ===
# Units: spot and option values in $ per share of underlying; vol in decimals (0.20 = 20%);
# time in years (trading-day convention, 252 days); position Greeks are for the WHOLE
# position (a short straddle has negative gamma and vega and positive theta).
# =====================================================================================

def fit_smile(log_moneyness, implied_vol, T, method="svi"):
    """Fit one expiry's implied-vol smile; return a function k -> implied vol.

    log_moneyness: k = ln(K / F) for each quoted strike; implied_vol: decimals; T: years.
    "quadratic": sigma(k) = a + b k + c k^2 by least squares. Fast and fine near the money,
                 but a local fit: the parabola bends the wrong way or explodes in the wings.
    "svi":       raw SVI (Gatheral 2004) for total implied variance w = sigma^2 T:
                     w(k) = a + b (rho (k - m) + sqrt((k - m)^2 + s^2)),
                 bounded least squares (b >= 0, |rho| < 1, s > 0); wings are linear in k.
    NaN vols (no time value) are ignored.
    """
    k, iv = np.asarray(log_moneyness, float), np.asarray(implied_vol, float)
    ok = np.isfinite(iv)
    k, iv = k[ok], iv[ok]
    if method == "quadratic":
        c2, c1, c0 = np.polyfit(k, iv, 2)
        return lambda x: c0 + c1 * np.asarray(x, float) + c2 * np.asarray(x, float) ** 2

    def svi_w(p, x):                                  # total variance and its parameter gradient
        a, b, rho, m, s = p
        root = np.sqrt((x - m) ** 2 + s * s)
        w = a + b * (rho * (x - m) + root)
        grad = np.stack([np.ones_like(x), rho * (x - m) + root, b * (x - m),
                         -b * (rho + (x - m) / root), b * s / root], axis=-1)
        return np.maximum(w, 1e-10), grad

    # start: match a parabola in total variance near the money (SVI with m = 0, s = 0.1)
    q2, q1, q0 = np.polyfit(k, iv ** 2 * T, 2)
    s0 = 0.1
    b0 = max(2 * s0 * q2, abs(q1) / 0.9, 1e-4)
    x0 = [q0 - b0 * s0, b0, np.clip(q1 / b0, -0.9, 0.9), 0.0, s0]
    lo, hi = [-1.0, 0.0, -0.999, -1.0, 1e-3], [1.0, 5.0, 0.999, 1.0, 2.0]
    resid = lambda p: np.sqrt(svi_w(p, k)[0] / T) - iv                           # noqa: E731
    jac = lambda p: svi_w(p, k)[1] / (2 * T * np.sqrt(svi_w(p, k)[0] / T))[:, None]  # noqa: E731
    p = least_squares(resid, x0, jac=jac, bounds=(lo, hi)).x
    return lambda x: np.sqrt(svi_w(p, np.asarray(x, float))[0] / T)


def delta_hedge_pnl(spot, position_delta, rebalance_every=1, band=None, cost_bps=COST_BPS):
    """Delta-hedge an option position along a price path with the underlying.

    spot, position_delta: arrays (..., n + 1) on one time grid (last axis = time; leading axes
        = independent trades); position_delta[..., i] is the option position's delta at step i.
    rebalance_every: time-based hedging, back to zero net delta every k steps; or
    band: move-based hedging, checked every step, rebalance only when |net delta| > band.
    cost_bps: cost per $ of underlying traded (half-spread + fees). Hedge unwound at the end.
    Returns dict: shares held over each step (..., n), hedge_pnl, costs, n_rebalances.
    """
    spot, pos_delta = np.asarray(spot, float), np.asarray(position_delta, float)
    n = spot.shape[-1] - 1
    held = np.zeros(spot.shape[:-1])
    shares = np.zeros(spot.shape[:-1] + (n,))
    traded_usd = np.zeros_like(held)
    n_reb = np.zeros_like(held)
    for i in range(n):
        net_delta = held + pos_delta[..., i]
        if band is None:
            rebalance = np.full(held.shape, i % rebalance_every == 0)
        else:
            rebalance = (np.abs(net_delta) > band) | (i == 0)
        target = np.where(rebalance, -pos_delta[..., i], held)   # flatten net delta
        traded_usd += np.abs(target - held) * spot[..., i]
        n_reb += rebalance
        held = target
        shares[..., i] = held
    traded_usd += np.abs(held) * spot[..., n]                    # unwind at expiry
    hedge_pnl = (shares * np.diff(spot, axis=-1)).sum(-1)
    return {"shares": shares, "hedge_pnl": hedge_pnl,
            "costs": traded_usd * cost_bps / 1e4, "n_rebalances": n_reb}


def greeks_attribution(value, spot, vol, greeks, hedge_shares, dt, premium, costs=0.0):
    """Explain a delta-hedged option position's P&L step by step with its Greeks.

    value: mark-to-market value of the option position at steps 0..n (negative when short);
    spot, vol: underlying price and the option's own implied vol at steps 0..n;
    greeks: dict of the POSITION's delta, gamma, vega (per 1.00 vol), theta (per year) at 0..n,
        optionally vanna (d2V/dS dvol) and volga (d2V/dvol2) for the cross/convexity terms;
    hedge_shares: shares held over each step (..., n); dt: years per step;
    premium: cash received (+) or paid (-) at the trade; costs: hedging costs (positive $).
    Per step, value change ~ theta dt + delta dS + 1/2 gamma dS^2 + vega dvol
                             + vanna dS dvol + 1/2 volga dvol^2.
    Returns a dict whose components sum EXACTLY to total; "unexplained" is the Taylor
    remainder (speed, charm, ...) and should be small.
    """
    dS, dvol = np.diff(spot, axis=-1), np.diff(vol, axis=-1)
    g = {name: np.asarray(x)[..., :-1] for name, x in greeks.items()}     # Greeks at step start
    out = {
        "quoted_edge": premium + value[..., 0],             # traded price vs fair mark
        "theta": (g["theta"] * dt).sum(-1),
        "gamma": (0.5 * g["gamma"] * dS ** 2).sum(-1),
        "vega": (g["vega"] * dvol).sum(-1),
    }
    if "vanna" in g:
        out["vanna"] = (g["vanna"] * dS * dvol).sum(-1)
        out["volga"] = (0.5 * g["volga"] * dvol ** 2).sum(-1)
    out["delta_hedge_residual"] = ((hedge_shares + g["delta"]) * dS).sum(-1)   # stale hedge
    out["hedging_costs"] = -np.asarray(costs, float)
    total = premium + value[..., -1] + (hedge_shares * dS).sum(-1) - costs
    out["unexplained"] = total - sum(out.values())
    out["total"] = total
    return out


# === END CORE ALGORITHM ===
# =====================================================================================


def forward_fill(x: np.ndarray) -> np.ndarray:
    """Forward-fill NaNs along the last axis (implied vol is undefined with no time value)."""
    idx = np.where(np.isfinite(x), np.arange(x.shape[-1]), 0)
    np.maximum.accumulate(idx, axis=-1, out=idx)
    return np.take_along_axis(x, idx, axis=-1)


def bs_vanna_volga(S, K, T, sigma):
    """Black-Scholes vanna (d2V/dS dsigma) and volga (d2V/dsigma2), r = 0; same for calls and puts."""
    with np.errstate(divide="ignore", invalid="ignore"):
        sqT = np.sqrt(T)
        d1 = (np.log(S / K) + 0.5 * sigma ** 2 * T) / (sigma * sqT)
        d2 = d1 - sigma * sqT
        pdf = np.exp(-0.5 * d1 ** 2) / np.sqrt(2 * np.pi)
        vanna = -pdf * d2 / sigma
        volga = S * pdf * sqT * d1 * d2 / sigma
    ok = (T > 0) & np.isfinite(vanna) & np.isfinite(volga)
    return np.where(ok, vanna, 0.0), np.where(ok, volga, 0.0)


def heston_price_bucketed(S, K, T, v, om, call=True, v_edges=(1e-4, 1e-3, 4e-3, 1e-2)):
    """options.heston_price called separately per variance bucket.

    Workaround for speed: heston_price sizes its Fourier grid for the smallest variance in each
    batch, so a few near-zero-variance states (common here: this Heston calibration violates the
    Feller condition) make every option in the batch slow. Results are identical.
    """
    S, K, T, v = (np.asarray(a, float) for a in np.broadcast_arrays(S, K, T, v))
    q, out = om.q_params, np.empty(S.shape)
    bucket = np.digitize(v, v_edges)
    for b in np.unique(bucket):
        m = bucket == b
        out[m] = options.heston_price(S[m], K[m], T[m], om.cfg.r, v[m], q["kappa"], q["theta"],
                                      q["xi"], q["rho"], call)
    return out


# ----------------------------------------------------------------------------- (a) smiles
def smile_study(om, sample_days):
    """In-sample RMSE and wing-extrapolation error (vol points) of quadratic vs SVI fits."""
    c = om.chain[om.chain.call & om.chain.day.isin(sample_days)]
    insample = {"quadratic": [], "svi": []}
    wing = {"quadratic": [], "svi": []}
    by_expiry = {}
    for (day, exp_days), g in c.groupby(["day", "expiry_days"]):
        k, iv, T = np.log(g.moneyness.to_numpy()), g.implied_vol.to_numpy(), g["T"].iloc[0]
        inner = (g.moneyness >= 0.849).to_numpy() & (g.moneyness <= 1.151).to_numpy()
        outer = ~inner & np.isfinite(iv)
        if np.isfinite(iv).sum() < 6 or np.isfinite(iv[inner]).sum() < 6:
            continue
        for meth in ("quadratic", "svi"):
            f = fit_smile(k, iv, T, meth)
            err = (f(k) - iv)[np.isfinite(iv)] * 100
            insample[meth].append(np.sqrt(np.mean(err ** 2)))
            by_expiry.setdefault((meth, exp_days), []).append(np.sqrt(np.mean(err ** 2)))
            if outer.any():
                f_in = fit_smile(k[inner], iv[inner], T, meth)
                wing[meth].extend(np.abs(f_in(k[outer]) - iv[outer]) * 100)
    return {
        "rmse_volpts": {m: float(np.mean(v)) for m, v in insample.items()},
        "wing_abs_err_volpts": {m: float(np.mean(v)) for m, v in wing.items()},
        "wing_max_err_volpts": {m: float(np.max(v)) for m, v in wing.items()},
        "rmse_by_expiry_volpts": {f"{m}_{e}d": float(np.mean(v)) for (m, e), v in sorted(by_expiry.items())},
    }


def atm_quote_vols(om, trade_days):
    """Fitted (SVI) 30-day ATM vol on each trade day: the desk's mid before adding edge."""
    c = om.chain[om.chain.call & (om.chain.expiry_days == TENOR_DAYS) & om.chain.day.isin(trade_days)]
    out = {}
    for day, g in c.groupby("day"):
        f = fit_smile(np.log(g.moneyness.to_numpy()), g.implied_vol.to_numpy(), g["T"].iloc[0], "svi")
        out[day] = float(f(0.0))
    return np.array([out[d] for d in trade_days])


# ----------------------------------------------------------------------------- (b) trades
def price_straddles(om, trade_days):
    """Market (Heston) value, implied vol and BS Greeks of each straddle on the 15-min grid."""
    spd = om.cfg.steps_per_day
    n = TENOR_DAYS * spd
    gidx = trade_days[:, None] * spd + np.arange(n + 1)[None, :]       # global step indices
    S = om.path["S"].to_numpy()[gidx]
    vQ = om.path["v"].to_numpy()[gidx] * (1 + om.cfg.vrp)               # risk-neutral variance
    K = S[:, :1] * np.ones_like(S)                                     # ATM strike = spot at sale
    T = np.broadcast_to((n - np.arange(n + 1)) / (252.0 * spd), S.shape)
    call = heston_price_bucketed(S, K, T, vQ, om, True)
    put = call - S + K                                                 # parity, r = 0
    otm_call = K >= S
    iv = options.implied_vol(np.where(otm_call, call, put), S, K, T, om.cfg.r, otm_call)
    iv = forward_fill(iv)                                              # near expiry, deep OTM
    gc = options.bs_greeks(S, K, T, om.cfg.r, iv, True)
    gp = options.bs_greeks(S, K, T, om.cfg.r, iv, False)
    straddle_greeks = {g: gc[g] + gp[g] for g in ("delta", "gamma", "vega", "theta")}
    vanna, volga = bs_vanna_volga(S, K, T, iv)
    straddle_greeks["vanna"], straddle_greeks["volga"] = 2 * vanna, 2 * volga   # call + put
    return {"S": S, "K": K, "T": T, "value": call + put, "iv": iv, "greeks": straddle_greeks,
            "dt": 1.0 / (252.0 * spd)}


def run_policies(px, premium_per_share):
    """Delta-hedge the SHORT straddles under each policy and attribute the P&L ($ per contract)."""
    pos_value = -px["value"]                                           # short one straddle
    pos_greeks = {g: -v for g, v in px["greeks"].items()}
    policies = [(lbl, {"rebalance_every": k}) for lbl, k in TIME_POLICIES]
    policies += [(f"band {b:.2f}", {"band": b}) for b in DELTA_BANDS]
    res = {}
    for label, kw in policies:
        h = delta_hedge_pnl(px["S"], pos_greeks["delta"], cost_bps=COST_BPS, **kw)
        att = greeks_attribution(pos_value, px["S"], px["iv"], pos_greeks, h["shares"], px["dt"],
                                 premium_per_share, h["costs"])
        res[label] = {k: v * MULT for k, v in att.items()}
        res[label]["rebalances_per_day"] = h["n_rebalances"] / TENOR_DAYS
    return res


def summarize(x, overlap):
    """Mean, sd and an overlap-adjusted standard error of the mean."""
    x = np.asarray(x, float)
    n_eff = max(len(x) / overlap, 2.0)
    return float(x.mean()), float(x.std(ddof=1)), float(x.std(ddof=1) / np.sqrt(n_eff))


# ----------------------------------------------------------------------------- plots
COMPONENTS = ["quoted_edge", "theta", "gamma", "vega", "vanna", "volga", "delta_hedge_residual",
              "hedging_costs", "unexplained", "total"]
COMPONENT_LABELS = ["quoted\nedge", "theta", "gamma", "vega", "vanna", "volga", "delta-hedge\nresidual",
                    "hedging\ncosts", "unexpl-\nained", "TOTAL"]


def plot_vol(days, atm_iv, rv_fwd, smile_day, om):
    fig = plt.figure(figsize=(10, 7.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1], hspace=0.4, wspace=0.27)
    ax = fig.add_subplot(gs[0, :])
    ax.plot(days, atm_iv * 100, color=COLORS["iv"], lw=1.1, label="30-day ATM implied vol on day d")
    ax.plot(days, rv_fwd * 100, color=COLORS["rv"], lw=0.9, label="realized vol over days d+1..d+30")
    ax.fill_between(days, atm_iv * 100, rv_fwd * 100, where=atm_iv >= rv_fwd, color=COLORS["pos"],
                    alpha=0.3, lw=0, label="implied > realized (option seller wins)")
    ax.fill_between(days, atm_iv * 100, rv_fwd * 100, where=atm_iv < rv_fwd, color=COLORS["neg"],
                    alpha=0.3, lw=0, label="implied < realized (option seller loses)")
    ax.set_xlabel("trading day")
    ax.set_ylabel("annualized vol (%)")
    ax.set_title("Implied vs subsequently realized vol (synthetic Heston market with a variance risk premium)")
    ax.legend(loc="upper left", ncol=2, fontsize=8)

    ax = fig.add_subplot(gs[1, 0])
    c = om.chain[(om.chain.day == smile_day) & om.chain.call & (om.chain.expiry_days == TENOR_DAYS)]
    k, iv, T = np.log(c.moneyness.to_numpy()), c.implied_vol.to_numpy(), c["T"].iloc[0]
    inner = (c.moneyness >= 0.849).to_numpy() & (c.moneyness <= 1.151).to_numpy()
    grid = np.linspace(np.log(0.75), np.log(1.25), 200)
    ax.plot(c.moneyness, iv * 100, "o", color="k", ms=5, label="market implied vol", zorder=3)
    ax.plot(np.exp(grid), fit_smile(k[inner], iv[inner], T, "svi")(grid) * 100, color=COLORS["iv"],
            label="SVI, fitted on 0.85-1.15")
    ax.plot(np.exp(grid), fit_smile(k[inner], iv[inner], T, "quadratic")(grid) * 100, "--",
            color=COLORS["rv"], label="quadratic, fitted on 0.85-1.15")
    for lo, hi in ((0.75, 0.849), (1.151, 1.25)):
        ax.axvspan(lo, hi, color=COLORS["grey"], alpha=0.12, lw=0)
    ax.set_xlabel("strike / spot")
    ax.set_ylabel("implied vol (%)")
    ax.set_title(f"30-day smile on day {smile_day}: wings (shaded) extrapolated", fontsize=10)
    ax.legend(fontsize=8)

    ax = fig.add_subplot(gs[1, 1])
    gap = (atm_iv - rv_fwd)[np.isfinite(rv_fwd)] * 100
    bins = np.linspace(np.floor(gap.min()), np.ceil(gap.max()), 40)
    ax.hist(gap[gap >= 0], bins=bins, color=COLORS["pos"], alpha=0.7, label=f"IV > RV: {np.mean(gap >= 0):.0%} of days")
    ax.hist(gap[gap < 0], bins=bins, color=COLORS["neg"], alpha=0.7, label=f"IV < RV: {np.mean(gap < 0):.0%} of days")
    ax.axvline(gap.mean(), color="k", lw=1.2, label=f"mean {gap.mean():+.1f} vol pts")
    ax.set_xlabel("implied minus subsequently realized vol (vol pts)")
    ax.set_ylabel("number of days")
    ax.set_title("Variance risk premium: small gain, fat left tail", fontsize=10)
    ax.legend(fontsize=8)
    fig.text(0.01, 0.005, "Synthetic data: simulate_option_market (Heston; risk-neutral variance = 1.25 x physical). "
             "RV = close-to-close, annualized.", fontsize=7.5, color="#555555")
    return fig


def plot_attribution(res, pnl_rows, classic, gross_15m):
    fig = plt.figure(figsize=(10.5, 8.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.42, wspace=0.27)
    ax = fig.add_subplot(gs[0, :])
    x = np.arange(len(COMPONENTS))
    for j, (pol, lbl) in enumerate((("15 min", "hedged every 15 min"), ("daily", "hedged once a day"))):
        means = [np.mean(res[pol][c]) for c in COMPONENTS]
        sds = [np.std(res[pol][c], ddof=1) for c in COMPONENTS]
        ax.bar(x + (j - 0.5) * 0.38, means, 0.38, color=COLORS[pol], label=lbl, yerr=sds, capsize=2.5,
               error_kw={"elinewidth": 0.8, "ecolor": "#333333"})
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(x, COMPONENT_LABELS, fontsize=8.5)
    ax.set_ylabel("$ per contract (mean; whisker = 1 sd)")
    ax.set_title("Greeks P&L attribution of a short 30-day ATM straddle (1 contract = 100 shares)")
    ax.legend(fontsize=8.5, loc="upper right")

    ax = fig.add_subplot(gs[1, 0])
    reb = np.array([r["rebalances_per_day"] for r in pnl_rows])
    is_band = np.array([r["policy"].startswith("band") for r in pnl_rows])
    series = [("mean_gross", "o-", COLORS["gross"], "mean P&L before costs"),
              ("mean_net", "s-", COLORS["net"], f"mean P&L after {COST_BPS:g} bp hedge costs"),
              ("sd_gross", "^--", COLORS["grey"], "sd of P&L"),
              ("sd_delta_hedge_residual", "v:", "k", "sd of delta-hedge residual")]
    for key, style, col, lbl in series:
        y = np.array([r[key] for r in pnl_rows])
        ax.plot(reb[~is_band], y[~is_band], style, color=col, label=lbl, ms=5)
        ax.plot(reb[is_band], y[is_band], style[0], mfc="none", color=col, ms=9)
    for r in pnl_rows:
        if r["policy"].startswith("band"):
            ax.annotate(f"band\n{r['policy'][5:]}", (r["rebalances_per_day"], r["sd_gross"]),
                        textcoords="offset points", xytext=(0, 8), ha="center", fontsize=7.5)
    ax.set_xscale("log")
    ax.set_xticks(reb[~is_band], [r["policy"] for r in pnl_rows if not r["policy"].startswith("band")])
    ax.minorticks_off()
    ax.set_ylim(bottom=-5)
    ax.set_xlabel("hedge frequency (log scale of rebalances per day; hollow = delta band)")
    ax.set_ylabel("$ per contract")
    ax.set_title("Hedging more often cuts variance, not the mean", fontsize=10)
    ax.legend(fontsize=7.5, loc="upper right")

    ax = fig.add_subplot(gs[1, 1])
    ax.scatter(classic, gross_15m, s=9, alpha=0.55, color=COLORS["iv"], lw=0)
    lim = [min(classic.min(), gross_15m.min()), max(classic.max(), gross_15m.max())]
    ax.plot(lim, lim, color="k", lw=0.8, label="45-degree line")
    r2 = np.corrcoef(classic, gross_15m)[0, 1] ** 2
    ax.set_xlabel("sum of 1/2 Gamma S^2 (IV_sale^2 - RV^2) dt  ($)")
    ax.set_ylabel("actual P&L ex edge and costs ($)")
    ax.set_title(f"P&L = dollar-gamma-weighted IV^2 - RV^2 (R^2 {r2:.2f})", fontsize=10)
    ax.legend(fontsize=8, loc="upper left")
    fig.text(0.01, 0.005, "Synthetic data (Heston with variance risk premium). Sold at fitted ATM vol + "
             f"{EDGE_VOL * 100:.1f} vol pts; hedge trades cost {COST_BPS:g} bp; attribution on the 15-min grid.",
             fontsize=7.5, color="#555555")
    return fig


# ----------------------------------------------------------------------------- main
def main():
    ctx = utils.setup(__file__, "Lab 06: options market making, delta hedging and Greeks attribution")
    t0 = time.time()
    n_days = 252 if ctx.smoke else 2016          # 8 simulated years in the full run
    trade_every = 10 if ctx.smoke else 5         # sell a new straddle every week (overlapping)
    om = simulate.simulate_option_market(n_days=n_days, seed=ctx.seed)
    spd = om.cfg.steps_per_day
    assert spd == 26, "hedge policies assume 26 steps (15 min) per day"

    # (d) implied vs realized
    c = om.chain
    atm = c[(c.expiry_days == TENOR_DAYS) & (c.moneyness == 1.0) & c.call].set_index("day")["implied_vol"]
    rv_fwd = om.realized_vol(TENOR_DAYS, forward=True).reindex(atm.index)
    ok = rv_fwd.notna()
    gap = (atm - rv_fwd)[ok]
    # model variance-swap rate E_Q[average variance over 30 days] from the risk-neutral Heston params
    q, kap, Tq = om.q_params, om.q_params["kappa"], TENOR_DAYS / 252.0
    vq = om.daily["v"].reindex(atm.index) * (1 + om.cfg.vrp)
    var_swap = q["theta"] + (vq - q["theta"]) * (1 - np.exp(-kap * Tq)) / (kap * Tq)
    vrp_stats = {
        "mean_atm30_iv": float(atm[ok].mean()), "mean_rv30_fwd": float(rv_fwd[ok].mean()),
        "mean_iv_minus_rv_volpts": float(gap.mean() * 100),
        "share_days_iv_above_rv": float((gap > 0).mean()),
        "implied_over_realized_variance_atm": float((atm[ok] ** 2).mean() / (rv_fwd[ok] ** 2).mean()),
        "implied_over_realized_variance_varswap": float(var_swap[ok].mean() / (rv_fwd[ok] ** 2).mean()),
        "planted_variance_ratio": 1 + om.cfg.vrp,
    }

    # (a) smiles: diagnostics on one day a month, all expiries
    sample_days = np.arange(0, n_days + 1, 21 if not ctx.smoke else 42)
    smile = smile_study(om, sample_days)

    # (b) trades: sell a 30-day ATM straddle every `trade_every` days at fitted vol + edge
    trade_days = np.arange(0, n_days - TENOR_DAYS + 1, trade_every)
    fitted_atm = atm_quote_vols(om, trade_days)
    px = price_straddles(om, trade_days)
    S0, K0, T0 = px["S"][:, 0], px["K"][:, 0], px["T"][:, 0]
    quote_vol = fitted_atm + EDGE_VOL
    premium = (options.bs_price(S0, K0, T0, 0.0, quote_vol, True)
               + options.bs_price(S0, K0, T0, 0.0, quote_vol, False))
    res = run_policies(px, premium)
    overlap = TENOR_DAYS / trade_every
    vega0 = px["greeks"]["vega"][:, 0] / 100 * MULT                    # $ per vol point per contract

    # (c) attribution checks
    S, iv, dt = px["S"], px["iv"], px["dt"]
    ret2 = (np.diff(S, axis=-1) / S[:, :-1]) ** 2                         # squared simple returns
    # identity (r = 0): theta + gamma = sum 1/2 Gamma S^2 (IV_t^2 dt - (dS/S)^2), IV_t = current IV
    cash_gamma = 0.5 * px["greeks"]["gamma"][:, :-1] * S[:, :-1] ** 2
    vol_spread_current = (cash_gamma * (iv[:, :-1] ** 2 * dt - ret2)).sum(-1) * MULT
    gamma_theta = res["daily"]["gamma"] + res["daily"]["theta"]
    # classic hold-to-expiry formula: gamma at the SALE implied vol, P&L ~ sum 1/2 G S^2 (IV0^2 - RV^2) dt
    iv0 = np.broadcast_to(iv[:, :1], S.shape)
    gamma_sale = (options.bs_greeks(S, px["K"], px["T"], 0.0, iv0, True)["gamma"] * 2)[:, :-1]
    classic = (0.5 * gamma_sale * S[:, :-1] ** 2 * (iv0[:, :-1] ** 2 * dt - ret2)).sum(-1) * MULT
    gross_15m = res["15 min"]["total"] - res["15 min"]["hedging_costs"] - res["15 min"]["quoted_edge"]
    rv_life = np.sqrt(252.0 * (np.diff(np.log(S[:, ::spd]), axis=-1) ** 2).mean(-1))
    simple_vega_pnl = vega0 * (iv[:, 0] - rv_life) * 100                  # P&L ~ vega x (IV - RV)

    rows = []
    for pol, r in res.items():
        gross = r["total"] - r["hedging_costs"]
        m_g, sd_g, se_g = summarize(gross, overlap)
        m_n, sd_n, _ = summarize(r["total"], overlap)
        m_h, sd_h, se_h = summarize(r["delta_hedge_residual"], overlap)
        rows.append({"policy": pol, "rebalances_per_day": float(np.mean(r["rebalances_per_day"])),
                     "mean_gross": m_g, "se_mean_gross": se_g, "sd_gross": sd_g,
                     "mean_net": m_n, "sd_net": sd_n, "mean_costs": float(np.mean(r["hedging_costs"])),
                     "mean_delta_hedge_residual": m_h, "se_delta_hedge_residual": se_h,
                     "sd_delta_hedge_residual": sd_h})
    # the 15-min policy hedges on the attribution grid itself, so its residual is zero by construction
    time_rows = [r for r in rows if not r["policy"].startswith("band") and r["sd_delta_hedge_residual"] > 0]
    slope = np.polyfit(np.log([r["rebalances_per_day"] for r in time_rows]),
                       np.log([r["sd_delta_hedge_residual"] for r in time_rows]), 1)[0]

    comps = COMPONENTS
    attribution = {pol: {k: round(float(np.mean(res[pol][k])), 2) for k in comps}
                   for pol in ("15 min", "daily")}
    attribution_sd = {pol: {k: round(float(np.std(res[pol][k], ddof=1)), 2) for k in comps}
                      for pol in ("15 min", "daily")}

    # plots
    smile_day = int(sample_days[len(sample_days) // 2])
    fig = plot_vol(atm.index.to_numpy(), atm.to_numpy(), rv_fwd.to_numpy(), smile_day, om)
    utils.save_fig(ctx, fig, "implied-vs-realized")
    fig = plot_attribution(res, rows, classic, gross_15m)
    utils.save_fig(ctx, fig, "pnl-attribution")

    results = {
        "n_days": n_days, "n_trades": len(trade_days), "trade_every_days": trade_every,
        "units": "$ per short straddle contract (1 call + 1 put, 100 shares each)",
        "mean_premium_usd": float(premium.mean() * MULT), "mean_vega_usd_per_volpt": float(vega0.mean()),
        **{k: v for k, v in vrp_stats.items()},
        "smile_rmse_volpts": smile["rmse_volpts"],
        "smile_wing_extrapolation_abs_err_volpts": smile["wing_abs_err_volpts"],
        "attribution_mean_usd": attribution,
        "attribution_sd_usd": attribution_sd,
        "mean_pnl_gross_usd_by_policy": {r["policy"]: round(r["mean_gross"], 2) for r in rows},
        "mean_pnl_net_usd_by_policy": {r["policy"]: round(r["mean_net"], 2) for r in rows},
        "sd_pnl_usd_by_policy": {r["policy"]: round(r["sd_gross"], 2) for r in rows},
        "sd_delta_hedge_residual_usd_by_policy": {r["policy"]: round(r["sd_delta_hedge_residual"], 2) for r in rows},
        "mean_hedging_costs_usd_by_policy": {r["policy"]: round(r["mean_costs"], 2) for r in rows},
        "rebalances_per_day_by_policy": {r["policy"]: round(r["rebalances_per_day"], 2) for r in rows},
        "hedge_residual_sd_slope_vs_rebalances": float(slope),
        "max_abs_mean_delta_hedge_residual_in_se": float(max(abs(r["mean_delta_hedge_residual"])
                                                             / r["se_delta_hedge_residual"] for r in rows
                                                             if r["se_delta_hedge_residual"] > 0)),
        "theta_plus_gamma_minus_vol_spread_max_abs_usd": float(np.max(np.abs(gamma_theta - vol_spread_current))),
        "r2_pnl_vs_classic_gamma_weighted_formula": float(np.corrcoef(classic, gross_15m)[0, 1] ** 2),
        "r2_pnl_vs_vega_x_iv_minus_rv": float(np.corrcoef(simple_vega_pnl, gross_15m)[0, 1] ** 2),
        "mean_classic_formula_usd": float(classic.mean()), "mean_pnl_ex_edge_costs_15min_usd": float(gross_15m.mean()),
        "share_trades_losing_daily_hedge": float(np.mean(res["daily"]["total"] < 0)),
        "p05_trade_pnl_usd_daily_hedge": float(np.percentile(res["daily"]["total"], 5)),
        "unexplained_sd_usd_15min": float(np.std(res["15 min"]["unexplained"], ddof=1)),
        "unexplained_sd_usd_without_vanna_volga_15min": float(np.std(
            res["15 min"]["unexplained"] + res["15 min"]["vanna"] + res["15 min"]["volga"], ddof=1)),
    }
    utils.write_results(ctx, results)

    # summary
    print(f"\nSimulated {n_days} days; {len(trade_days)} short 30-day ATM straddles, one every "
          f"{trade_every} days (overlapping). Mean premium ${results['mean_premium_usd']:.0f}, "
          f"vega ${results['mean_vega_usd_per_volpt']:.1f}/vol pt per contract.")
    print(f"(d) VRP: mean 30d ATM IV {vrp_stats['mean_atm30_iv']:.1%} vs next-30d realized "
          f"{vrp_stats['mean_rv30_fwd']:.1%}: gap {vrp_stats['mean_iv_minus_rv_volpts']:+.2f} vol pts, IV > RV on "
          f"{vrp_stats['share_days_iv_above_rv']:.0%} of days. Implied/realized variance: var-swap "
          f"{vrp_stats['implied_over_realized_variance_varswap']:.2f}, "
          f"ATM {vrp_stats['implied_over_realized_variance_atm']:.2f} "
          f"(planted {vrp_stats['planted_variance_ratio']:.2f}).")
    print(f"(a) Smile RMSE (vol pts): quadratic {smile['rmse_volpts']['quadratic']:.3f}, SVI "
          f"{smile['rmse_volpts']['svi']:.3f}; wing extrapolation |error|: quadratic "
          f"{smile['wing_abs_err_volpts']['quadratic']:.2f}, SVI {smile['wing_abs_err_volpts']['svi']:.2f}.")
    print("(c) Attribution, mean $ per contract (sd):")
    for pol in ("15 min", "daily"):
        parts = ", ".join(f"{k} {attribution[pol][k]:+.1f} ({attribution_sd[pol][k]:.0f})" for k in comps)
        print(f"    {pol:>7}: {parts}")
    print("    policy       reb/day  mean gross (se)   mean net   sd total  sd hedge-resid")
    for r in rows:
        print(f"    {r['policy']:<11} {r['rebalances_per_day']:7.2f}  "
              f"{r['mean_gross']:8.1f} ({r['se_mean_gross']:4.1f})"
              f"  {r['mean_net']:8.1f}  {r['sd_gross']:8.1f}  {r['sd_delta_hedge_residual']:8.1f}")
    print(f"    sd(hedge residual) ~ rebalances^{slope:.2f} (theory -0.5). theta + gamma = cash-gamma-weighted "
          f"(IV^2 - RV^2) to ${results['theta_plus_gamma_minus_vol_spread_max_abs_usd']:.1e}.")
    print(f"    Hold-to-expiry formula sum 1/2 Gamma(IV_sale) S^2 (IV_sale^2 - RV^2) dt: mean ${classic.mean():.1f} vs "
          f"actual ${gross_15m.mean():.1f}, R^2 {results['r2_pnl_vs_classic_gamma_weighted_formula']:.2f} "
          f"(vega x (IV - RV): R^2 {results['r2_pnl_vs_vega_x_iv_minus_rv']:.2f}). Unexplained sd "
          f"${results['unexplained_sd_usd_15min']:.1f} (${results['unexplained_sd_usd_without_vanna_volga_15min']:.1f} "
          f"without vanna/volga terms).")
    print(f"  done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
