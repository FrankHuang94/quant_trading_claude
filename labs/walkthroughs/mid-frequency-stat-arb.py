"""Walkthrough helper: a toy mid-frequency US equity stat-arb book, built from the finished labs.

Builds every number quoted in
docs/03-algorithms/h-end-to-end-walkthroughs/walkthrough-mid-frequency-stat-arb.md by running ONE
pipeline on the synthetic market of labs/common (simulate_equity_market, seed 7: 500 stocks x
1,260 days, three planted alphas) and importing the labs' core functions:

  * universe   point-in-time liquidity screen (price, 20-day ADV) on each date
  * alphas     Lab 11 `make_raw_signal`: the three planted alphas made "dirty" (beta tilt, drifting
               sector tilt, rare huge outliers, arbitrary units), as research signals arrive
  * transforms Lab 11 `winsorize` + `zscore` + `neutralize` (estimated beta + sector dummies),
               scored with Lab 11 `ic_series`
  * combine    Lab 12 `combine_ic_weighted`, weights = trailing mean 5-day IC (no look-ahead)
  * risk       Lab 14 `pca_factor_cov` (16 statistical factors + diagonal specific variance)
  * optimize   Lab 14 `optimize_portfolio` (dollar, beta and sector neutral, per-name caps,
               gross cap, linear cost penalty)
  * execute    Lab 17 `vwap_schedule` + `child_order_costs_bps` (spread, temporary and
               permanent impact of a one-day VWAP including the closing auction)
  * attribute  next-day P&L = market + sector + style factor P&L + specific P&L (split into the
               oracle-expected part and noise) - spread - impact

Conventions: weights are fractions of CAPITAL ($50M); max gross 2.0 -> $100M GMV. Signals are
known at the close of day t; the new target is executed by VWAP over day t+1, so day t+1's return
is earned on the average of the old and new weights (fills land mid-day on average). Bookends
(trade at the close of t; full one-day delay) are reported as a sensitivity. The backtest is the
last 504 days (two years, daily rebalance, about 0.07 s per cvxpy solve); the first three years
are history for the IC weights, betas and risk model. Commissions, borrow and financing are left
out (the page estimates them separately).

Run:  python labs/walkthroughs/mid-frequency-stat-arb.py          (about 45 s)
Out:  labs/walkthroughs/mid-frequency-stat-arb.json
      docs/assets/labs/walkthrough-stat-arb-pnl.png
"""
from __future__ import annotations

import os

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")          # small dense matrices: one BLAS thread is fastest

import importlib.util  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

LABS = Path(__file__).resolve().parents[1]
REPO = LABS.parent
sys.path.insert(0, str(LABS))
from common import simulate, utils  # noqa: E402

utils.set_style()
import matplotlib.pyplot as plt  # noqa: E402


def load_lab(name: str, rel: str):
    """Import labs/NN-name/lab.py (directory names contain hyphens, so no plain import)."""
    spec = importlib.util.spec_from_file_location(name, LABS / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lab11 = load_lab("lab11", "11-signal-transforms-ic/lab.py")
lab12 = load_lab("lab12", "12-alpha-combination-purged-cv/lab.py")
lab14 = load_lab("lab14", "14-risk-model-mvo/lab.py")
lab17 = load_lab("lab17", "17-vwap-twap-pov/lab.py")

# ---------------------------------------------------------------- scenario (illustrative)
SEED = 7
CAPITAL = 50e6                 # weights are fractions of this; gross 2.0 = $100M GMV
MAX_GROSS = 2.0
MIN_PRICE, MIN_ADV = 5.0, 25e6          # liquidity screen, point in time
CAP_CAPITAL, CAP_ADV = 0.01, 0.01       # position cap: min(1% of capital = $500K, 1% of ADV)
H = 5                          # forecast and risk horizon (days)
IC_WINDOW = 252                # trailing days for IC weights
RISK_WINDOW, N_FACTORS, RISK_REFRESH = 252, 16, 21
RISK_AVERSION = 150.0          # utility = alpha'w - 150 w'Sigma_5d w - costs; GMV cap almost binds
COST_AVERSION = 1.0            # charge the full one-way cost estimate against the 5-day alpha
TYPICAL_TRADE = 100e3          # $ size at which the optimizer's linear cost is evaluated
ETA, GAMMA, EXPONENT = 0.15, 0.30, 0.6  # Lab 17 impact coefficients (stylized)
AUCTION_SHARE = 0.10           # Lab 17: closing auction = 10% of daily volume
N_BT_DAYS = 504                # daily rebalances in the backtest: the last two years (runtime)
DETAIL_DAY = 1200              # the rebalance shown step by step in the page
ALPHA_NAMES = {"alpha_fast": "A1 fast (reversal-like, half-life 2 d)",
               "alpha_med": "A2 medium (revisions-like, half-life 10 d)",
               "alpha_slow": "A3 slow (quality-like, half-life 60 d)"}

C_BLUE, C_ORANGE, C_AQUA, C_GRAY, C_PURPLE = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#6250d6"
INK = "#30302e"


def vwap_schedule_many(curve, qty):
    """Vectorized lab17.vwap_schedule: one row of child orders per name (same rounding rule)."""
    w = np.asarray(curve, float)
    cum = np.round(np.asarray(qty, float)[:, None] * np.cumsum(w)[None, :] / w.sum())
    return np.diff(np.concatenate([np.zeros((len(cum), 1)), cum], axis=1), axis=1)


def vwap_costs(qty_shares, price, day_volume_shares, half_spread_bps, daily_vol, adv_shares, curve):
    """Expected spread / temporary / permanent cost (in $) of one-day VWAP orders, per name.

    Child orders follow the volume curve (390 minutes + closing auction); each bin's cost comes
    from lab17.child_order_costs_bps (buy and sell are symmetric in that model).
    """
    q = vwap_schedule_many(curve, qty_shares)                        # names x 391
    others = day_volume_shares[:, None] * curve[None, :]             # others' volume per bin
    hs = np.repeat(half_spread_bps[:, None], len(curve), axis=1)
    hs[:, -1] = 0.0                                                  # no spread in the auction
    bought_before = np.cumsum(q, axis=1) - q
    s, t, p = lab17.child_order_costs_bps(q, others, hs, bought_before, adv_shares[:, None],
                                          daily_vol[:, None], ETA, GAMMA, EXPONENT)
    px = price[:, None] / 1e4
    return (q * px * s).sum(1), (q * px * t).sum(1), (q * px * p).sum(1)


def main():
    t0 = time.time()
    m = simulate.simulate_equity_market(seed=SEED)
    T, N = m.returns.shape
    dates, tickers = m.dates, m.tickers
    R = m.returns.to_numpy()
    S = m.specific_returns.to_numpy()
    price = m.prices.to_numpy()
    adv_usd = m.adv_usd.to_numpy()
    volume = m.volume.to_numpy()
    half_spread_bps = m.spread_bps.to_numpy() / 2
    sector_names = [c for c in m.exposures.columns if c.startswith("sec_")]
    sectors = m.exposures[sector_names].to_numpy()                  # N x 11 dummies (static)
    B = m.exposures.to_numpy()          # true exposures: market, 4 styles, 11 sectors (attribution)
    F = m.factor_returns[m.exposures.columns].to_numpy()             # T x K factor returns
    exp_spec = m.expected_specific_return.to_numpy()                 # oracle E_t[s_{t+1}]
    curve = np.r_[(1 - AUCTION_SHARE) * simulate.intraday_volume_profile(390), AUCTION_SHARE]

    # ---------------------------------------------------------------- 1. universe (point in time)
    in_univ = (price >= MIN_PRICE) & (adv_usd >= MIN_ADV)            # T x N, known at close t
    univ_count = in_univ.sum(axis=1)

    # cap-weighted index and trailing betas (re-estimated with the risk model, monthly)
    mcap = m.market_cap.to_numpy()
    idx_ret = np.r_[np.nan, (R[1:] * mcap[:-1]).sum(1) / mcap[:-1].sum(1)]
    bt_start = T - 1 - N_BT_DAYS                                     # first rebalance (signal day)
    refresh_days = list(range(bt_start, T - 1, RISK_REFRESH))
    beta_days = [d for d in range(RISK_REFRESH, T - 1) if (d - bt_start) % RISK_REFRESH == 0]
    beta_hat_at, risk_at = {}, {}
    for d in beta_days:
        lo = max(1, d - RISK_WINDOW + 1)
        x, Y = idx_ret[lo:d + 1], R[lo:d + 1]
        xc = x - x.mean()
        beta_hat_at[d] = (xc @ (Y - Y.mean(0))) / (xc @ xc)
    for d in refresh_days:
        risk_at[d] = lab14.pca_factor_cov(R[d - RISK_WINDOW + 1:d + 1], N_FACTORS)
    beta_days = np.array(beta_days)

    def beta_hat(t):
        return beta_hat_at[int(beta_days[beta_days <= t][-1])] if t >= beta_days[0] else np.ones(N)

    def risk_model(t):
        return risk_at[max(d for d in refresh_days if d <= t)]

    # ---------------------------------------------------------------- 2-3. alphas and transforms
    raw, wz, neut = {}, {}, {}
    for k, name in enumerate(ALPHA_NAMES):
        r_ = lab11.make_raw_signal(m, base=name, seed=SEED + 1 + k).to_numpy()
        r_ = np.where(in_univ, r_, np.nan)
        raw[name] = r_
        wz[name] = lab11.zscore(lab11.winsorize(r_, 0.01))          # per-date winsorize, z-score
        out = np.full((T, N), np.nan)
        for t in range(T):
            u = in_univ[t]
            E = np.column_stack([beta_hat(t)[u], sectors[u]])        # sector dummies span the mean
            out[t, u] = lab11.zscore(lab11.neutralize(wz[name][t, u], E))
        neut[name] = out

    fwd1 = m.forward_returns(1)                                      # total, aligned at t
    fwd1_s = m.forward_returns(1, specific=True)
    fwd5_s = m.forward_returns(H, specific=True)

    def df(x):
        return pd.DataFrame(x, index=dates, columns=tickers)

    def mean_ic(x, y, rows=slice(None)):
        return float(lab11.ic_series(df(x), y).iloc[rows].mean())

    def corr_with(x, v):
        """Mean over dates of the cross-sectional correlation of x[t] with a fixed vector v."""
        return float(df(x).corrwith(pd.Series(v, index=tickers), axis=1).mean())

    stage_ic = {}
    for name in ALPHA_NAMES:
        stage_ic[name] = {
            "raw_ic_total_1d": mean_ic(raw[name], fwd1),
            "winsor_z_ic_total_1d": mean_ic(wz[name], fwd1),
            "neutralized_ic_total_1d": mean_ic(neut[name], fwd1),
            "neutralized_ic_resid_1d": mean_ic(neut[name], fwd1_s),
            "neutralized_ic_resid_5d": mean_ic(neut[name], fwd5_s),
            "winsor_z_corr_with_true_beta": corr_with(wz[name], m.beta.to_numpy()),
            "neutralized_corr_with_true_beta": corr_with(neut[name], m.beta.to_numpy()),
        }

    # ---------------------------------------------------------------- 4. IC-weighted combination
    ic5 = pd.DataFrame({n: lab11.ic_series(df(neut[n]), fwd5_s) for n in ALPHA_NAMES})
    # weight on date t uses ICs whose 5-day label is complete by t: dates s <= t - H
    ic_trail = ic5.rolling(IC_WINDOW, min_periods=60).mean().shift(H)
    composite = np.full((T, N), np.nan)
    ic_weights = np.full((T, len(ALPHA_NAMES)), np.nan)
    for t in range(T):
        if np.isnan(ic_trail.iloc[t]).any():
            continue
        u = in_univ[t]
        X = np.column_stack([neut[n][t, u] for n in ALPHA_NAMES])
        comb, w = lab12.combine_ic_weighted(X, ic_trail.iloc[t].to_numpy())
        composite[t, u] = lab11.zscore(comb)
        ic_weights[t] = w
    comp_ic5 = lab11.ic_series(df(composite), fwd5_s)
    comp_ic_trail = comp_ic5.rolling(IC_WINDOW, min_periods=60).mean().shift(H).to_numpy()
    bt = slice(bt_start, T - 1)
    comp_ic1_mean = float(lab11.ic_series(df(composite), fwd1_s).iloc[bt].mean())
    comp_ic5_mean = float(comp_ic5.iloc[bt].mean())
    comp_autocorr = float(lab11.ic_series(df(composite), df(composite).shift(1)).iloc[bt].mean())
    t_prep = time.time() - t0

    # ---------------------------------------------------------------- 5-8. daily rebalance loop
    trailing_vol = pd.DataFrame(R).rolling(60, min_periods=20).std().to_numpy()
    w_prev = np.zeros(N)
    rows, detail = [], {}
    for t in range(bt_start, T - 1):
        cov = risk_model(t)
        u = in_univ[t]
        z = np.nan_to_num(composite[t])
        sigma_spec = np.sqrt(cov.specific_var)
        alpha = comp_ic_trail[t] * np.sqrt(H) * sigma_spec * z       # Grinold: IC x vol x score
        daily_vol = np.nan_to_num(trailing_vol[t], nan=0.02)
        adv_sh = adv_usd[t] / price[t]
        # optimizer's linear cost: half-spread + VWAP impact of a typical $100K trade, per $ traded
        need = u | (w_prev != 0)                                     # tradable or still held
        cost_unit = np.zeros(N)
        s_, t_, p_ = vwap_costs(np.round(TYPICAL_TRADE / price[t, need]), price[t, need], adv_sh[need],
                                half_spread_bps[need], daily_vol[need], adv_sh[need], curve)
        cost_unit[need] = (s_ + t_ + p_) / TYPICAL_TRADE
        cap = np.where(u, np.minimum(CAP_CAPITAL, CAP_ADV * adv_usd[t] / CAPITAL), 0.0)
        # optimize over today's universe; names that left it are sold to zero
        cov_u = lab14.FactorCov(cov.L[:, u] * np.sqrt(H), cov.specific_var[u] * H)
        w = np.zeros(N)
        w[u] = lab14.optimize_portfolio(alpha[u], cov_u, w_prev[u], RISK_AVERSION,
                                        COST_AVERSION * cost_unit[u], beta_hat(t)[u], sectors[u],
                                        cap[u], MAX_GROSS)
        w = np.where(np.abs(w) < 1e-7, 0.0, w)                       # solver dust
        trade = w - w_prev
        shares = np.round(np.abs(trade) * CAPITAL / price[t])
        cs, ct, cp_ = np.zeros(N), np.zeros(N), np.zeros(N)
        k = shares > 0                                               # realized day-(t+1) volume
        cs[k], ct[k], cp_[k] = vwap_costs(shares[k], price[t, k], volume[t + 1, k], half_spread_bps[k],
                                          daily_vol[k], adv_sh[k], curve)
        hold = 0.5 * (w_prev + w)                                    # VWAP over day t+1
        fpnl = CAPITAL * (hold @ B) * F[t + 1]                       # per factor
        spec = CAPITAL * hold @ S[t + 1]
        spec_exp = CAPITAL * hold @ exp_spec[t]
        total = CAPITAL * hold @ R[t + 1]
        assert abs(total - fpnl.sum() - spec) < 1e-6 * max(1.0, abs(total)) + 1e-3
        pred_vol = float(np.sqrt(cov.variance(w))[0]) * CAPITAL      # daily $ vol, PCA model
        rows.append(dict(
            t=t, date=dates[t + 1], gross_pnl=total, market=fpnl[0],
            styles=fpnl[1:5].sum(), sectors_pnl=fpnl[5:].sum(),
            specific=spec, specific_expected=spec_exp, specific_noise=spec - spec_exp,
            spread=cs.sum(), temporary=ct.sum(), permanent=cp_.sum(),
            pnl_close=CAPITAL * w @ R[t + 1], pnl_delay=CAPITAL * w_prev @ R[t + 1],
            traded=np.abs(trade).sum() * CAPITAL, gmv=np.abs(w).sum() * CAPITAL, shares=shares.sum(),
            net_exposure=w.sum() * CAPITAL, beta_hat_exp=float(beta_hat(t) @ w) * CAPITAL,
            beta_true_exp=float(m.beta.to_numpy() @ w) * CAPITAL,
            n_long=int((w > 1e-6).sum()), n_short=int((w < -1e-6).sum()),
            n_at_cap=int((np.abs(w) >= cap - 1e-6)[np.abs(w) > 1e-6].sum()),
            exp_alpha_5d=float(alpha @ w) * CAPITAL, pred_vol=pred_vol,
            exp_cost=float(cost_unit @ np.abs(trade)) * CAPITAL,
            true_exp_1d=CAPITAL * w @ exp_spec[t],
            universe=int(u.sum()),
        ))
        if t == DETAIL_DAY:
            true_cov = m.true_covariance(t + 1).to_numpy()
            fac_var = float(((w @ cov.L.T) ** 2).sum())
            spec_var = float((w ** 2) @ cov.specific_var)
            detail = dict(t=t, w_prev=w_prev.copy(), w=w.copy(), alpha=alpha, z=z, cap=cap,
                          cost_unit=cost_unit, cs=cs, ct=ct, cp=cp_, shares=shares, adv_usd=adv_usd[t],
                          price=price[t], daily_vol=daily_vol, cov=cov,
                          true_vol=float(np.sqrt(w @ true_cov @ w)) * CAPITAL,
                          factor_share=fac_var / (fac_var + spec_var), fpnl=fpnl, sigma_spec=sigma_spec,
                          pca_share_top1=float((cov.L[0] ** 2).sum() / ((cov.L ** 2).sum() + cov.specific_var.sum())),
                          pca_share_all=float((cov.L ** 2).sum() / ((cov.L ** 2).sum() + cov.specific_var.sum())))
        w_prev = w
    t_loop = time.time() - t0 - t_prep
    P = pd.DataFrame(rows).set_index("date")
    P["cost"] = P["spread"] + P["temporary"] + P["permanent"]
    P["net_pnl"] = P["gross_pnl"] - P["cost"]

    # ---------------------------------------------------------------- summary statistics
    ann = 252
    gmv = P["gmv"].mean()

    def sharpe(x):
        return float(utils.annualized_sharpe(np.asarray(x)))

    cum_net = P["net_pnl"].cumsum().to_numpy()
    dd = float((np.maximum.accumulate(cum_net) - cum_net).max())
    z_book = P["gross_pnl"] / P["pred_vol"]
    summary = dict(
        n_days=len(P), years=len(P) / ann, first_date=str(P.index[0].date()), last_date=str(P.index[-1].date()),
        avg_universe=float(P["universe"].mean()), avg_gmv_usd=gmv,
        avg_n_long=float(P["n_long"].mean()), avg_n_short=float(P["n_short"].mean()),
        avg_names_at_cap=float(P["n_at_cap"].mean()),
        turnover_pct_gmv_per_day=float((P["traded"] / P["gmv"]).iloc[1:].mean() * 100),
        annual_turnover_x_gmv=float((P["traded"] / P["gmv"]).iloc[1:].mean() * ann),
        gross_pnl_usd_per_year=float(P["gross_pnl"].mean() * ann),
        net_pnl_usd_per_year=float(P["net_pnl"].mean() * ann),
        gross_return_pct_gmv=float(P["gross_pnl"].mean() * ann / gmv * 100),
        net_return_pct_gmv=float(P["net_pnl"].mean() * ann / gmv * 100),
        vol_pct_gmv=float(P["net_pnl"].std() * np.sqrt(ann) / gmv * 100),
        predicted_vol_pct_gmv=float(P["pred_vol"].mean() * np.sqrt(ann) / gmv * 100),
        book_bias_statistic=float(z_book.std()),
        sharpe_gross=sharpe(P["gross_pnl"]), sharpe_net=sharpe(P["net_pnl"]),
        sharpe_gross_trade_at_close=sharpe(P["pnl_close"]),
        sharpe_gross_full_day_delay=sharpe(P["pnl_delay"]),
        gross_pnl_trade_at_close_usd_per_year=float(P["pnl_close"].mean() * ann),
        gross_pnl_full_day_delay_usd_per_year=float(P["pnl_delay"].mean() * ann),
        max_drawdown_usd=dd, max_drawdown_pct_gmv=dd / gmv * 100,
        pct_days_positive_net=float((P["net_pnl"] > 0).mean() * 100),
        cost_bps_per_dollar_traded=float(P["cost"].sum() / P["traded"].iloc[1:].sum() * 1e4),
        expected_cost_bps_per_dollar_traded=float(P["exp_cost"].iloc[1:].sum() / P["traded"].iloc[1:].sum() * 1e4),
        initial_build_cost_usd=float(P["cost"].iloc[0]),
        shares_traded_per_year=float(P["shares"].mean() * ann),
        commission_usd_per_year_at_half_cent=float(P["shares"].mean() * ann * 0.005),   # not in the toy
        borrow_usd_per_year_at_25_to_50_bps=[float(0.0025 * CAPITAL), float(0.005 * CAPITAL)],  # short side = capital
        fundamental_law_ir=float(comp_ic1_mean * np.sqrt(P["universe"].mean() * ann)),
        corr_pnl_with_index=float(np.corrcoef(P["gross_pnl"], idx_ret[P["t"].to_numpy() + 1])[0, 1]),
        avg_abs_true_beta_exposure_pct_gmv=float((P["beta_true_exp"].abs() / P["gmv"]).mean() * 100),
        composite_ic_1d=comp_ic1_mean, composite_ic_5d=comp_ic5_mean,
        composite_autocorr_1d=comp_autocorr,
    )
    lines = ["market", "sectors_pnl", "styles", "specific_expected", "specific_noise",
             "spread", "temporary", "permanent"]
    income = {k: float(P[k].mean() * ann) for k in lines}
    income["gross_pnl"] = float(P["gross_pnl"].mean() * ann)
    income["cost"] = float(P["cost"].mean() * ann)
    income["net_pnl"] = float(P["net_pnl"].mean() * ann)
    income_ex_build = {k: float(P[k].iloc[1:].mean() * ann) for k in ["spread", "temporary", "permanent", "cost"]}

    # ---------------------------------------------------------------- the detail day
    d = detail
    t = d["t"]
    row = P.loc[dates[t + 1]]
    w, wp = d["w"], d["w_prev"]
    trade = (w - wp) * CAPITAL
    adv_sh_all = d["adv_usd"] / d["price"]                           # ex-ante: ADV, not the realized day
    e_s, e_t, e_p = vwap_costs(d["shares"], d["price"], adv_sh_all, half_spread_bps, d["daily_vol"],
                               adv_sh_all, curve)
    cost_name = e_s + e_t + e_p
    tl = pd.DataFrame({
        "ticker": tickers, "sector": m.sector.to_numpy(), "z": d["z"],
        "alpha_5d_bps": d["alpha"] * 1e4, "old_usd": wp * CAPITAL, "new_usd": w * CAPITAL,
        "trade_usd": trade, "pct_adv": np.abs(trade) / d["adv_usd"] * 100,
        "exp_cost_bps": np.where(np.abs(trade) > 0, cost_name / np.maximum(np.abs(trade), 1) * 1e4, 0.0),
        "cap_usd": d["cap"] * CAPITAL, "price": d["price"], "shares": d["shares"] * np.sign(trade),
    })
    traded = tl[tl.trade_usd.abs() > 1]
    buys = traded.sort_values("trade_usd", ascending=False).head(5)
    sells = traded.sort_values("trade_usd").head(5)

    def recs(x):
        return [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
                for r in x.drop(columns=["cap_usd"]).to_dict("records")]

    big = traded.loc[traded.trade_usd.abs().idxmax()]
    i_big = list(tickers).index(big.ticker)
    q_big = vwap_schedule_many(curve, [abs(big.shares)])[0]
    q_check = lab17.vwap_schedule(curve, abs(big.shares))
    assert np.allclose(q_big, q_check)                               # vectorized == Lab 17
    adv_sh_big = d["adv_usd"][i_big] / d["price"][i_big]
    s1, t1, p1 = vwap_costs(np.array([abs(big.shares)]), d["price"][[i_big]], np.array([adv_sh_big]),
                            half_spread_bps[[i_big]], d["daily_vol"][[i_big]], np.array([adv_sh_big]), curve)
    notional_big = abs(big.shares) * d["price"][i_big]
    sector_net = (sectors.T @ w) * CAPITAL
    detail_out = dict(
        signal_date=str(dates[t].date()), trade_date=str(dates[t + 1].date()),
        universe=int(in_univ[t].sum()), universe_min_adv_musd=float(d["adv_usd"][in_univ[t]].min() / 1e6),
        excluded=int(N - in_univ[t].sum()),
        ic_weights=dict(zip(ALPHA_NAMES, np.round(ic_weights[t], 4).tolist())),
        trailing_ic5=dict(zip(ALPHA_NAMES, np.round(ic_trail.iloc[t].to_numpy(), 5).tolist())),
        composite_trailing_ic5=float(comp_ic_trail[t]),
        alpha_5d_bps_p5_p95=[float(np.percentile(d["alpha"][in_univ[t]] * 1e4, 5)),
                             float(np.percentile(d["alpha"][in_univ[t]] * 1e4, 95))],
        median_specific_vol_daily_pct=float(np.median(d["sigma_spec"][in_univ[t]]) * 100),
        gmv_usd=float(np.abs(w).sum() * CAPITAL), long_usd=float(w[w > 0].sum() * CAPITAL),
        short_usd=float(-w[w < 0].sum() * CAPITAL), net_usd=float(w.sum() * CAPITAL),
        n_long=int((w > 1e-6).sum()), n_short=int((w < -1e-6).sum()),
        n_at_cap=int(row.n_at_cap), max_position_usd=float(np.abs(w).max() * CAPITAL),
        beta_hat_exposure_usd=float(row.beta_hat_exp), beta_true_exposure_usd=float(row.beta_true_exp),
        max_abs_sector_net_usd=float(np.abs(sector_net).max()),
        predicted_vol_daily_usd=float(row.pred_vol), true_vol_daily_usd=float(d["true_vol"]),
        predicted_vol_annual_pct_gmv=float(row.pred_vol * np.sqrt(ann) / (np.abs(w).sum() * CAPITAL) * 100),
        factor_share_of_predicted_variance=float(d["factor_share"]),
        pca_variance_share_first_factor=d["pca_share_top1"], pca_variance_share_16_factors=d["pca_share_all"],
        expected_alpha_5d_usd=float(row.exp_alpha_5d), oracle_expected_alpha_1d_usd=float(row.true_exp_1d),
        traded_usd=float(row.traded), n_trades=int(len(traded)),
        expected_cost_usd=float(row.exp_cost), exante_vwap_cost_usd=float(cost_name.sum()),
        vwap_cost_usd=float(row.cost),
        vwap_cost_split_usd=dict(spread=float(row.spread), temporary=float(row.temporary),
                                 permanent=float(row.permanent)),
        median_trade_usd=float(traded.trade_usd.abs().median()),
        median_trade_pct_adv=float(traded.pct_adv.median()), max_trade_pct_adv=float(traded.pct_adv.max()),
        top_buys=recs(buys), top_sells=recs(sells),
        largest_trade=dict(ticker=big.ticker, sector=big.sector, side="buy" if big.trade_usd > 0 else "sell",
                           shares=float(abs(big.shares)), notional_usd=float(notional_big),
                           price=float(d["price"][i_big]), pct_adv=float(big.pct_adv),
                           daily_vol_pct=float(d["daily_vol"][i_big] * 100),
                           half_spread_bps=float(half_spread_bps[i_big]),
                           first_30min_shares=float(q_big[:30].sum()), auction_shares=float(q_big[-1]),
                           cost_bps=dict(spread=float(s1[0] / notional_big * 1e4),
                                         temporary=float(t1[0] / notional_big * 1e4),
                                         permanent=float(p1[0] / notional_big * 1e4))),
        next_day_pnl_usd=dict(market=float(row.market), sectors=float(row.sectors_pnl), styles=float(row.styles),
                              specific_expected=float(row.specific_expected),
                              specific_noise=float(row.specific_noise), gross=float(row.gross_pnl),
                              spread=float(-row.spread), temporary=float(-row.temporary),
                              permanent=float(-row.permanent), net=float(row.net_pnl)),
    )

    res = dict(
        walkthrough="mid-frequency-stat-arb", seed=SEED, n_stocks=N, n_days=T,
        params=dict(capital_usd=CAPITAL, max_gross=MAX_GROSS, gmv_usd=CAPITAL * MAX_GROSS,
                    min_price=MIN_PRICE, min_adv_usd=MIN_ADV, cap_pct_capital=CAP_CAPITAL * 100,
                    cap_pct_adv=CAP_ADV * 100, horizon_days=H, ic_window=IC_WINDOW,
                    risk_window=RISK_WINDOW, n_factors=N_FACTORS, risk_refresh_days=RISK_REFRESH,
                    risk_aversion=RISK_AVERSION, cost_aversion=COST_AVERSION,
                    typical_trade_usd=TYPICAL_TRADE, eta=ETA, gamma=GAMMA, exponent=EXPONENT,
                    auction_share=AUCTION_SHARE),
        avg_universe_all_days=float(univ_count.mean()),
        stage_ic=stage_ic, summary=summary, income_usd_per_year=income,
        costs_ex_initial_build_usd_per_year=income_ex_build, detail_day=detail_out,
        runtime_s=dict(prep=t_prep, loop=t_loop),
    )
    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(utils._jsonable(res), indent=2) + "\n")

    # ---------------------------------------------------------------- plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw={"width_ratios": [1.35, 1]})
    x = P.index
    ax1.plot(x, P["specific_expected"].cumsum() / 1e6, color=C_AQUA, lw=2, label="alpha captured (oracle-expected specific)")
    ax1.plot(x, P["specific"].cumsum() / 1e6, color=C_BLUE, lw=1.2, label="specific P&L (alpha + noise)")
    ax1.plot(x, (P["market"] + P["sectors_pnl"] + P["styles"]).cumsum() / 1e6, color=C_PURPLE, lw=1.5,
             label="factor P&L (market + sectors + styles)")
    ax1.plot(x, -P["cost"].cumsum() / 1e6, color=C_ORANGE, lw=1.5, label="trading costs (VWAP model)")
    ax1.plot(x, P["net_pnl"].cumsum() / 1e6, color=INK, lw=2.2, label="net P&L")
    ax1.axhline(0, color=C_GRAY, lw=0.8)
    ax1.set_ylabel("cumulative P&L (\\$ millions)")
    ax1.set_xlabel("date (synthetic)")
    ax1.set_title("Cumulative P&L by source, \\$100M GMV book", fontsize=11)
    ax1.legend(fontsize=8, loc="upper left")
    labels = ["alpha captured", "specific noise", "market", "sectors", "styles", "spread", "impact (temp.)",
              "impact (perm.)", "net"]
    vals = [income["specific_expected"], income["specific_noise"], income["market"], income["sectors_pnl"],
            income["styles"], -income["spread"], -income["temporary"], -income["permanent"], income["net_pnl"]]
    cols = [C_AQUA, C_BLUE, C_PURPLE, C_PURPLE, C_PURPLE, C_ORANGE, C_ORANGE, C_ORANGE, INK]
    y = np.arange(len(labels))[::-1]
    ax2.barh(y, np.array(vals) / 1e6, color=cols)
    for yi, v in zip(y, vals):
        ax2.text(v / 1e6 + (0.15 if v >= 0 else -0.15), yi, f"{v / 1e6:+.2f}", va="center",
                 ha="left" if v >= 0 else "right", fontsize=8, color=INK)
    ax2.set_yticks(y, labels)
    ax2.axvline(0, color=C_GRAY, lw=0.8)
    ax2.set_xlabel("\\$ millions per year (average)")
    ax2.set_title("Annual income statement", fontsize=11)
    lo_, hi_ = min(vals) / 1e6, max(vals) / 1e6
    ax2.set_xlim(lo_ - 0.25 * (hi_ - lo_) - 0.5, hi_ + 0.25 * (hi_ - lo_))
    ax2.grid(axis="y", alpha=0)
    fig.suptitle("Walkthrough: mid-frequency stat-arb book on the synthetic market (seed 7, stylized; "
                 "synthetic lab result)", fontweight="bold")
    fig.tight_layout()
    png = REPO / "docs" / "assets" / "labs" / "walkthrough-stat-arb-pnl.png"
    fig.savefig(png)
    plt.close(fig)

    # ---------------------------------------------------------------- print
    print(f"prep {t_prep:.1f}s, loop {t_loop:.1f}s ({len(P)} rebalances)")
    print(json.dumps(utils._jsonable({"stage_ic": stage_ic, "summary": summary, "income": income}), indent=1))
    print(json.dumps(utils._jsonable(detail_out), indent=1))
    print(f"wrote {out.relative_to(REPO)} and {png.relative_to(REPO)} in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    main()
