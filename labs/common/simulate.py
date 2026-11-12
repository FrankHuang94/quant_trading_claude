"""Synthetic market engine for the labs. THIS DOCSTRING IS THE API REFERENCE.

Every lab imports from here instead of downloading data, so results are reproducible
(deterministic given ``seed``) and every planted effect has a KNOWN true size: a lab can show
whether a method recovers the truth and how often noise fools it. Five generators:

  (a)+(b) simulate_equity_market  factor-structured US-equity-like cross-section + planted alphas
  (c)     simulate_lob            limit-order-book / trade-flow generator (uses orderbook.OrderBook)
  (d)     simulate_option_market  Heston stochastic-vol underlying + daily option chain with a VRP
          simulate_futures        diversified futures panel with persistent drift regimes (trend)
          simulate_intraday_session  one day of 1-minute bars + closing auction (execution labs)

All ``simulate_*`` functions take an optional config dataclass plus keyword overrides of its
fields, e.g. ``simulate_equity_market(n_stocks=200, n_days=500, seed=3)``. Run
``python labs/common/simulate.py --selftest`` to check every realism target below.

---------------------------------------------------------------------------------------------
(a)+(b) EQUITY CROSS-SECTION WITH PLANTED ALPHAS
---------------------------------------------------------------------------------------------
    m = simulate_equity_market()                       # 500 stocks x 1260 days, ~0.3 s
    m = simulate_equity_market(n_stocks=200, n_days=750, alphas=(PlantedAlpha("a", ic=0.05),))

Model (daily, simple returns; dates are business days from ``start``, no holidays):

    r[t, i] = sum_k B[i, k] f[t, k]  +  s[t, i]                    total = factor + specific
    f[t, market] = mu + sigma_m h[t] eps_t  (+ a crash drift in stress episodes)
    f[t, style or sector] = sigma_k h[t] eps_t
    s[t, i] = sigma_i m[t] * ( sum_a beta_a y_a[t-1, i]  + endogenous reversal/momentum terms
                              + sqrt(1 - P) eps[t, i] )

* Factors (``m.exposures`` columns, in order): ``market`` (exposure = beta, 0.6-1.5),
  ``size`` (z-score of log market cap), ``value``, ``momentum``, ``low_vol`` (static z-scores),
  then one dummy per sector, named ``sec_<Sector>`` (11 GICS-like sectors). Exposures are
  constant through time (a simplification). Factor vols (annual): market 16%, size 3%,
  value 4%, momentum 6%, low_vol 4%, sectors 8-16% (energy highest).
* Volatility regime ``h[t]`` (``m.vol_regime``): log-AR(1) stochastic vol (persistence 0.985)
  with a leverage effect (vol rises after down days) plus stress episodes (vol x2-3.5, decaying
  over weeks, with a 6-15% market drawdown); dates in ``m.stress_dates``. Normalized so that
  mean(h^2) = 1 over the sample, so realized market vol ~= ``market_vol``. All factors scale with
  h; specific vols scale with m[t] = sqrt(h[t]) (normalized), so correlations rise in stress.
* Shocks are Student-t (``fat_tails_df``, default 5), standardized to unit variance.
* ``sigma_i`` = annual specific vol drawn in ``idio_vol_range`` (smaller / high-beta stocks
  more volatile), i.e. 0.9%-2.8% daily. ``m.specific_vol`` = sigma_i m[t] (daily, true).
* Liquidity: market caps lognormal (median ~$15B, $1.5B-$600B); ADV ~ cap^0.7, roughly
  $5M-$1.5B; ``spread_bps`` 2-30 (tighter for liquid names); daily share volume is noisy,
  rises with |return| and with the vol regime; ``adv_usd`` = trailing 20-day mean of $ volume
  (including day t).

Realism targets (checked by the selftest on the default config):
  realized market vol ~16%/yr with stress spikes; average pairwise stock correlation 0.2-0.35,
  higher within sectors; daily specific vol 1-3%; betas 0.6-1.5.

PLANTED ALPHAS. Each ``PlantedAlpha(name, ic, half_life, horizon_decay, noise,
ic_halflife_years, start_day)`` creates a latent AR(1) score a[t, i] (unit variance,
phi = 0.5 ** (1 / half_life)). Its effect on returns is y[t] = hd*y[t-1] + (a[t] - phi*a[t-1])
(hd = horizon_decay): each innovation of the score is priced in over the following days with
geometric weights hd^k. If hd == phi (the DEFAULT_ALPHAS), y == a: the observable score is
itself the optimal predictor. The specific return on day t+1 gets sigma_i m[t+1] beta_a y[t];
beta_a is calibrated analytically so that

    mean_t corr_cross_section( m.alphas[name].iloc[t], m.specific_returns.iloc[t + 1] ) ~= ic
    corr( alphas[t], specific_returns[t + 1 + k] ) ~= ic * horizon_decay ** k    (IC decay)

``noise`` adds i.i.d. observation noise (the target IC already accounts for it: the noisy
score still has IC = ic, but higher turnover). ``ic_halflife_years`` makes beta_a decay
(post-publication decay); ``start_day`` zeroes it before that day index (the signal is
observable but has no power). ``m.alphas[name]`` is the observable score known at the CLOSE of
day t (cross-sectional z-score each day). Measured mean IC lands within ~+-0.003 of ``ic`` on
the default size (selftest: 0.0406 / 0.0300 / 0.0203 for the defaults). Rank IC runs ~10% above
Pearson IC (ranking removes the dilution from heteroskedastic specific vols).
WARNING: if horizon_decay is far from 0.5**(1/half_life), a smoothed or differenced version of
the score predicts better than the score itself (by design of the math, not a bug).

    DEFAULT_ALPHAS = alpha_fast (ic 0.04, half-life 2d), alpha_med (0.03, 10d),
                     alpha_slow (0.02, 60d), each with horizon_decay = 0.5 ** (1 / half_life)

IC is defined against SPECIFIC (residual) returns. Against total returns it is lower
(factor moves add cross-sectional noise): roughly ic * 0.85.

ENDOGENOUS REVERSAL / MOMENTUM (lab 10). ``reversal_strength`` is the target IC of
-(z-scored 5-day specific return ending at t) for day t+1's specific return; ``momentum_strength``
the target IC of the z-scored 12-1 month specific return (days t-251..t-21). They are generated
sequentially from realized past returns (so they are real features of the price history) and
calibrated net of their interaction with the planted alphas (selftest: 0.038 for 0.04, 0.018
for 0.02). Use ``reversal_signal(m)`` / ``momentum_signal(m)`` to build the matching signals.

``EquityMarket`` fields: cfg, dates, tickers, sector (Series), beta (Series), exposures
(tickers x factors), factor_returns (dates x factors), specific_returns, returns, prices,
volume (shares), adv_usd, market_cap, specific_vol (all dates x tickers), spread_bps (Series),
alphas (dict name -> dates x tickers), alpha_specs (dict name -> PlantedAlpha); extras:
factor_vol (Series, base daily vol per factor), vol_regime (Series h[t]), stress_dates,
alpha_loadings (dict name -> beta_a), expected_specific_return (dates x tickers: E_t of the
specific return of day t+1, known at close t: the "oracle" forecast).
Methods: ``forward_returns(h=1, specific=False)`` -> sum of returns t+1..t+h aligned at t (NaN
for the last h rows); ``true_covariance(day)`` -> tickers x tickers daily covariance of the
generating model on day index ``day`` (B F_t B' + diag(specific var)).

    noise_signals(m, n, seed=0) -> {"noise_000": DataFrame, ...}   # pure noise, AR(1) with random
                                   # half-lives 1-60 d, z-scored; ~5 MB each on the default size
    iter_noise_signals(m, n, seed=0)   # same, as a generator (memory-friendly for n in the 1000s)
    cross_sectional_ic(signal, fwd_returns, rank=False) -> Series of daily ICs (row-wise corr)
    reversal_signal(m) / momentum_signal(m) -> z-scored 5-day / 12-1 month specific return

---------------------------------------------------------------------------------------------
(c) LIMIT ORDER BOOK / TRADE FLOW
---------------------------------------------------------------------------------------------
    sim = simulate_lob()                       # one 6.5-hour day, ~270k events, ~2-3 s
    sim = simulate_lob(n_seconds=1800, seed=3) # smoke size, ~0.2 s

A continuous-time (Gillespie) simulation of one stock on one venue, using the real matching
engine in ``orderbook.py`` ($50 stock, 1-cent tick by default):
* a latent fair value FV (``sim.fair_value``) follows a random walk with ``daily_vol`` per
  6.5 h (0.65 ticks per second at the defaults) plus Poisson jumps (``jump_rate_per_hour``,
  size ~ N(0, ``jump_size_bps``));
* background liquidity providers ("lp") only know a lagged, flow-updated BELIEF of fair value:
  an EMA of FV with time constant ``lp_fv_lag`` (20 s), nudged by every market order by
  ``flow_impact_ticks`` x side x sqrt(size/100) (they learn from order flow, Glosten-Milgrom
  style). This lag is what lets informed traders adversely select them;
* lps submit limit orders at rate ``limit_rate`` (sizes 100 x geometric, mean 200), placed
  k = 1..depth_levels ticks behind the opposite best quote (P(k) ~ k^-0.7) but never at a price
  worse than their belief minus a small random edge (bids below it, asks above it);
* each resting lp order is cancelled at hazard ``cancel_rate`` per second (mean life 20 s);
  once a second, lp orders on the wrong side of the belief are cancelled with probability
  ``stale_cancel_prob`` (pulling stale quotes) and orders far from the touch are cleaned up;
* market orders arrive at ``market_rate`` (sizes 100 x geometric, mean 250); a share
  ``informed_share`` come from informed traders who see the TRUE fair value, buy if FV > mid
  (sell otherwise) and size up with the mispricing; the rest ("noise") pick a random side.
Emergent stylized facts (selftest, defaults): spread 1 tick ~50% of the time, 1-3 ticks ~96%;
median touch size ~500 shares; corr(top-of-book imbalance, sign of the next mid change) ~0.2;
liquidity-provider markout at 10 s ~ -0.35 ticks/share on informed trades vs ~ +0.85 on noise
trades (adverse selection builds over seconds); median |mid - FV| ~1.2 ticks; realized vol of
the mid ~= daily_vol.

Helpers: ``lob_markouts(sim, horizon)`` -> average LP markout (ticks/share) for informed / noise
/ all trades; ``lob_imbalance_predictiveness(sim)`` -> (corr(imbalance, sign of next mid
change), number of mid changes).

``LOBSimulation`` fields:
  quotes      one row per event, state AFTER the event: time, bid, ask, bid_size, ask_size, mid,
              spread, imbalance = (bid_size - ask_size) / (bid_size + ask_size), bid_size_2,
              ask_size_2, bid_size_3, ask_size_3 (sizes of the 2nd/3rd best levels)
  events      one row per event (same index as quotes): time, type ('limit'|'cancel'|'market'),
              side (+1 bid/buy, -1 ask/sell), price (limit price; cancelled order's price; VWAP
              for a market order, NaN if unfilled), size, order_id, owner ('lp'|'noise'|
              'informed'|'agent')
  trades      one row per fill: time, price, size, side (+1 buyer-initiated), informed (bool);
              extras: maker_id, maker_owner, taker_owner, event_idx (row of the market order in
              events/quotes: quotes.iloc[event_idx - 1] is the book just before the trade)
  fair_value  Series aligned with quotes rows;   book  the final OrderBook
Agent hook (extra): ``simulate_lob(..., agent=fn, agent_interval=1.0)`` calls ``fn(ctx)`` every
``agent_interval`` simulated seconds with an ``LOBAgentContext``: ctx.t, ctx.fair_value,
ctx.book (read it freely; the OrderBook API), ctx.add_limit(side, price, size) -> id,
ctx.cancel(id, size=None), ctx.market(side, size) -> fills, ctx.new_fills (fills involving the
agent since the last call). Agent orders are recorded in events/trades with owner 'agent'.
To observe every fill as it happens, call ctx.book.subscribe(callback) once.

---------------------------------------------------------------------------------------------
(d) OPTIONS UNDER STOCHASTIC VOLATILITY, WITH A VARIANCE RISK PREMIUM
---------------------------------------------------------------------------------------------
    om = simulate_option_market()              # 252 days, 26 steps/day, chain of 18k rows, ~1 s
The underlying follows Heston under the physical measure (drift ``mu``, extra field, default
5%/yr) on an intraday grid (full-truncation Euler). Each day's options are priced with
``options.heston_price`` under a risk-neutral measure with a reduced-form variance risk
premium: v_Q = v (1 + vrp), theta_Q = theta (1 + vrp), same kappa, xi, rho. (A pure Heston
change of measure cannot change today's variance; real short-dated VRPs come from jump and
dealer risk premia, which this toy folds into one markup.) Hence implied vol > subsequent
realized vol on average, and rho < 0 gives a negative skew. Day counts are TRADING days:
T = expiry_days / 252, volatility annualized with sqrt(252).
  path    one row per intraday step: t (years), S, v (instantaneous variance), day, step
  chain   one row per (day, expiry, strike, call/put), days 0..n_days: day, expiry_days, T,
          strike (= moneyness x spot that day), moneyness, spot, call (bool), price,
          implied_vol, delta, gamma, vega (Black-Scholes greeks at the implied vol; vega per
          1.00 vol). Constant-maturity: every day lists fresh expiries.
  daily   end-of-day spot and variance (index = day);  q_params  risk-neutral parameters
  realized_vol(window_days=21, forward=False) -> annualized realized vol of daily log returns
          (no demeaning); forward=True: over days d+1..d+window, aligned at d.
  price(day, strike, T, call=True) -> model price of any option on that day (e.g. to revalue
          a fixed-strike position as time passes).

---------------------------------------------------------------------------------------------
FUTURES (trend following) and INTRADAY (execution)
---------------------------------------------------------------------------------------------
    fm = simulate_futures()     # 24 assets x 5040 days: 6 equity index, 6 rates, 6 fx, 6 commodities
Daily excess returns r = true_drift + sigma_t * eps: realistic vols by asset (bond futures
2-12%, fx 7-11%, equity 15-23%, commodities 15-45%), vol clustering, fat tails, a factor-based
cross-asset correlation (risk-on/off, rates, USD, commodity blocks). true_drift = trend_strength
x sigma_t x z_t with z_t a persistent regime process (piecewise constant N(0,1) levels, mean
regime length ``regime_days`` = 250, 30% of the drift variance shared within an asset class).
trend_strength = std of the daily drift in units of daily vol: the default 0.045 means a typical
regime has an annual Sharpe of about +-0.7 (0.045 x sqrt(252)). A 12-month time-series-momentum
portfolio (sign of the 12-month return, inverse-vol weights) then earns a gross Sharpe of ~0.75
on average over 20-year samples (0.3-1.2 across seeds; 0.78 for seed 7; ``tsmom_sharpe(fm)``). Per asset the Sharpe
is only ~0.1-0.2: diversification across 24 markets does the work. Fields: returns (daily
excess returns), asset_class (Series), true_drift (daily expected return), vol (true daily vol).

    prof = intraday_volume_profile(390)        # U-shaped, sums to 1
    bars = simulate_intraday_session()         # 390 one-minute bars
Columns: minute (0 = 9:30-9:31), volume (shares), mid (end of minute), spread ($, wider at the
open), spread_bps, high, low, vwap (of the minute). attrs: close_auction_volume, close_price,
open_price, continuous_volume. Total daily volume ~ adv_shares (lognormal day-to-day noise),
of which ``close_auction_share`` trades in the closing auction. Intraday variance follows the
volume profile (more volatile at the open).
"""
from __future__ import annotations

import argparse
import dataclasses
import math
import sys
import time
import warnings
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Callable, Iterator

import numpy as np
import pandas as pd
from scipy.signal import lfilter
from scipy.special import ndtr

if __package__ in (None, ""):          # allow `python labs/common/simulate.py --selftest`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from common.orderbook import ASK, BID, BUY, SELL, Fill, OrderBook  # noqa: E402
    from common import options  # noqa: E402
else:
    from .orderbook import ASK, BID, BUY, SELL, Fill, OrderBook
    from . import options

__all__ = [
    "PlantedAlpha", "DEFAULT_ALPHAS", "EquityMarketConfig", "EquityMarket", "simulate_equity_market",
    "noise_signals", "iter_noise_signals", "cross_sectional_ic",
    "LOBConfig", "LOBSimulation", "LOBAgentContext", "simulate_lob",
    "OptionMarketConfig", "OptionMarket", "simulate_option_market",
    "FuturesConfig", "FuturesMarket", "simulate_futures",
    "IntradayConfig", "intraday_volume_profile", "simulate_intraday_session",
    "reversal_signal", "momentum_signal", "lob_markouts", "lob_imbalance_predictiveness", "tsmom_sharpe",
]


# =============================================================================================
# shared helpers
# =============================================================================================
def _make_cfg(cls, cfg, overrides: dict):
    """Config dataclass from (cfg or defaults) + keyword overrides (unknown names raise)."""
    cfg = cls() if cfg is None else cfg
    return dataclasses.replace(cfg, **overrides) if overrides else cfg


def _std_t(rng: np.random.Generator, df: float, size, clip: float = 12.0) -> np.ndarray:
    """Student-t shocks scaled to unit variance (normal if df is None/inf), clipped at +-clip."""
    if df is None or not np.isfinite(df) or df > 200:
        x = rng.standard_normal(size)
    else:
        x = rng.standard_t(df, size) / np.sqrt(df / (df - 2.0))
    return np.clip(x, -clip, clip)


def _zscore_rows(x: np.ndarray) -> np.ndarray:
    """Cross-sectional z-score of each row (NaN-safe; all-NaN rows stay NaN)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mu = np.nanmean(x, axis=1, keepdims=True)
        sd = np.nanstd(x, axis=1, keepdims=True)
    return (x - mu) / np.where(sd > 0, sd, 1.0)


def cross_sectional_ic(signal: pd.DataFrame, fwd_returns: pd.DataFrame, rank: bool = False) -> pd.Series:
    """Daily information coefficient: per-row correlation of signal and forward returns.

    Typical use: ``cross_sectional_ic(m.alphas["alpha_med"], m.forward_returns(1, specific=True))``.
    ``rank=True`` gives the Spearman (rank) IC. Pairs with a NaN on either side are dropped.
    """
    s, r = signal.align(fwd_returns, join="inner")
    S = s.to_numpy(dtype=float, copy=True)
    R = r.to_numpy(dtype=float, copy=True)
    bad = ~(np.isfinite(S) & np.isfinite(R))
    S[bad] = np.nan
    R[bad] = np.nan
    if rank:
        S = pd.DataFrame(S).rank(axis=1).to_numpy()
        R = pd.DataFrame(R).rank(axis=1).to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)            # all-NaN rows (e.g. last fwd rows)
        S = S - np.nanmean(S, axis=1, keepdims=True)
        R = R - np.nanmean(R, axis=1, keepdims=True)
        num = np.nansum(S * R, axis=1)
        den = np.sqrt(np.nansum(S * S, axis=1) * np.nansum(R * R, axis=1))
        ic = num / den
    ic[(~bad).sum(axis=1) < 3] = np.nan
    return pd.Series(ic, index=s.index, name="ic")


def _vol_regime(rng: np.random.Generator, n: int, burn: int, shock_lag: np.ndarray,
                stress_per_year: float, phi: float = 0.985, sd_log: float = 0.22,
                leverage: float = -0.4) -> tuple[np.ndarray, list[int], np.ndarray]:
    """Common volatility multiplier h[t]: log-AR(1) with leverage + stress episodes.

    Returns (h normalized to mean(h^2) = 1 over the sample part, stress start indices,
    crash drift array to add to the market return).
    """
    z = rng.standard_normal(n)
    innov = sd_log * np.sqrt(1 - phi ** 2) * (leverage * shock_lag + np.sqrt(1 - leverage ** 2) * z)
    log_h = lfilter([1.0], [1.0, -phi], innov)
    crash = np.zeros(n)
    sample_days = n - burn
    n_ep = rng.poisson(stress_per_year * sample_days / 252.0)
    if sample_days >= 500:
        n_ep = max(n_ep, 1)                      # at least one stress episode in a long sample
    starts: list[int] = []
    if n_ep and sample_days > 60:
        cand = np.arange(burn + 20, n - 20)
        starts = sorted(int(s) for s in rng.choice(cand, size=min(n_ep, cand.size), replace=False))
        for s in starts:
            mag = np.log(rng.uniform(2.0, 3.5))  # vol multiplier at the peak
            hl = rng.uniform(10.0, 30.0)         # half-life of the vol spike, days
            k = np.arange(n - s)
            log_h[s:] += mag * 0.5 ** (k / hl)
            dd = rng.uniform(0.06, 0.15)         # market drawdown spread over 5 days
            crash[s:s + 5] -= dd / 5.0
    h = np.exp(log_h)
    h /= np.sqrt(np.mean(h[burn:] ** 2))
    return h, starts, crash


# =============================================================================================
# (a)+(b) equity cross-section with planted alphas
# =============================================================================================
@dataclass
class PlantedAlpha:
    """A planted signal with known strength and decay (see module docstring)."""

    name: str
    ic: float = 0.03                    # target daily IC of the observable signal vs next-day SPECIFIC return
    half_life: float = 5.0              # persistence of the signal (AR(1) half-life, days) -> drives turnover
    horizon_decay: float = 0.5          # IC for day t+1+k scales ~ horizon_decay**k (IC decay curve)
    noise: float = 0.0                  # extra observation noise std (0 = researcher sees the true signal)
    ic_halflife_years: float | None = None   # structural decay: IC halves every N years
    start_day: int = 0                  # signal has no predictive power before this day index


DEFAULT_ALPHAS: tuple[PlantedAlpha, ...] = (
    PlantedAlpha("alpha_fast", ic=0.04, half_life=2.0, horizon_decay=0.5 ** (1 / 2.0)),
    PlantedAlpha("alpha_med", ic=0.03, half_life=10.0, horizon_decay=0.5 ** (1 / 10.0)),
    PlantedAlpha("alpha_slow", ic=0.02, half_life=60.0, horizon_decay=0.5 ** (1 / 60.0)),
)

SECTOR_NAMES = ("Communication", "ConsumerDisc", "ConsumerStaples", "Energy", "Financials",
                "HealthCare", "Industrials", "InfoTech", "Materials", "RealEstate", "Utilities")
# sector -> (shift of beta in probit space, annual vol of the sector factor)
_SECTOR_PARAMS = {
    "Communication": (0.10, 0.09), "ConsumerDisc": (0.35, 0.09), "ConsumerStaples": (-0.80, 0.08),
    "Energy": (0.20, 0.16), "Financials": (0.25, 0.11), "HealthCare": (-0.30, 0.09),
    "Industrials": (0.15, 0.08), "InfoTech": (0.55, 0.11), "Materials": (0.15, 0.10),
    "RealEstate": (-0.20, 0.12), "Utilities": (-1.10, 0.12),
}
_STYLE_VOL = {"size": 0.03, "value": 0.04, "momentum": 0.06, "low_vol": 0.04}


@dataclass
class EquityMarketConfig:
    n_stocks: int = 500
    n_days: int = 1260
    n_sectors: int = 11
    start: str = "2019-01-02"
    seed: int = 7
    market_vol: float = 0.16                       # annualized
    style_factors: tuple = ("size", "value", "momentum", "low_vol")
    idio_vol_range: tuple = (0.15, 0.45)           # annualized specific vol, cross-sectional range
    beta_range: tuple = (0.6, 1.5)
    vol_clustering: bool = True                    # stochastic common vol + stress episodes
    fat_tails_df: float = 5.0                      # Student-t df for shocks
    reversal_strength: float = 0.0                 # IC of (-5-day specific return) for next day
    momentum_strength: float = 0.0                 # IC of 12-1 month specific momentum for next day
    alphas: tuple = DEFAULT_ALPHAS
    # extras
    market_drift: float = 0.06                     # annual equity premium of the market factor
    stress_per_year: float = 0.5                   # expected stress episodes per year


@dataclass
class EquityMarket:
    cfg: EquityMarketConfig
    dates: pd.DatetimeIndex
    tickers: list
    sector: pd.Series
    beta: pd.Series
    exposures: pd.DataFrame
    factor_returns: pd.DataFrame
    specific_returns: pd.DataFrame
    returns: pd.DataFrame
    prices: pd.DataFrame
    volume: pd.DataFrame
    adv_usd: pd.DataFrame
    market_cap: pd.DataFrame
    spread_bps: pd.Series
    specific_vol: pd.DataFrame
    alphas: dict
    alpha_specs: dict
    # extras
    factor_vol: pd.Series = None
    vol_regime: pd.Series = None
    stress_dates: list = field(default_factory=list)
    alpha_loadings: dict = field(default_factory=dict)
    expected_specific_return: pd.DataFrame = None

    def forward_returns(self, h: int = 1, specific: bool = False) -> pd.DataFrame:
        """Sum of (specific) returns over days t+1..t+h, aligned at t (last h rows NaN)."""
        r = self.specific_returns if specific else self.returns
        return r.rolling(h).sum().shift(-h)

    def true_covariance(self, day) -> pd.DataFrame:
        """Daily covariance matrix of total returns implied by the generating model on ``day``.

        ``day`` is an integer row index (negative counts from the end) or a date.
        """
        if not isinstance(day, (int, np.integer)):
            day = self.dates.get_loc(pd.Timestamp(day))
        h = float(self.vol_regime.iloc[day])
        B = self.exposures.to_numpy()
        fvar = (self.factor_vol.to_numpy() * h) ** 2
        spec = self.specific_vol.iloc[day].to_numpy() ** 2
        cov = (B * fvar) @ B.T + np.diag(spec)
        return pd.DataFrame(cov, index=self.tickers, columns=self.tickers)


def _alpha_coeffs(spec: PlantedAlpha) -> tuple[float, float, float, float]:
    """phi, hd, Cov(a_t, y_t), Var(y_t) for a planted alpha (unit-variance latent score)."""
    phi = 0.5 ** (1.0 / max(spec.half_life, 1e-6))
    hd = float(spec.horizon_decay)
    if not 0.0 <= hd < 1.0:
        raise ValueError(f"{spec.name}: horizon_decay must be in [0, 1)")
    cov_ay = (1 - phi ** 2) / (1 - phi * hd)
    var_y = (1 - phi ** 2) / (1 - hd ** 2)
    return phi, hd, cov_ay, var_y


def simulate_equity_market(cfg: EquityMarketConfig | None = None, **overrides) -> EquityMarket:
    """Simulate the equity cross-section with planted alphas (see module docstring)."""
    cfg = _make_cfg(EquityMarketConfig, cfg, overrides)
    # Independent random streams per model component, so that e.g. adding a planted alpha or
    # switching on reversal does not change the factor returns or the specific noise.
    rng_static, rng_regime, rng_factor, rng_spec, rng_liq = (
        np.random.default_rng(s) for s in np.random.SeedSequence(cfg.seed).spawn(5))
    N, T = int(cfg.n_stocks), int(cfg.n_days)
    specs = tuple(cfg.alphas)
    names = [a.name for a in specs]
    if len(set(names)) != len(names):
        raise ValueError("planted alpha names must be unique")

    # 260-day burn-in so the vol regime and 12-1 month momentum start in steady state (planted
    # alphas get their own, longer burn-in below). Fixed, so the base market does not depend on
    # which alphas are planted.
    burn = 260
    TT = burn + T
    df = cfg.fat_tails_df

    # ---------------------------------------------------------------- static characteristics
    n_sec = int(cfg.n_sectors)
    sec_names = list(SECTOR_NAMES[:n_sec]) if n_sec <= len(SECTOR_NAMES) else \
        [f"Sector{j:02d}" for j in range(n_sec)]
    rng = rng_static
    sec_idx = rng.permutation(np.arange(N) % n_sec)
    sec_shift = np.array([_SECTOR_PARAMS.get(s, (0.0, 0.10))[0] for s in sec_names])
    sec_vol = np.array([_SECTOR_PARAMS.get(s, (0.0, 0.10))[1] for s in sec_names])

    log_cap = np.clip(rng.normal(np.log(15e9), 0.9, N), np.log(1.5e9), np.log(6e11))
    size_z = (log_cap - log_cap.mean()) / log_cap.std()
    lo_b, hi_b = cfg.beta_range
    beta = lo_b + (hi_b - lo_b) * ndtr(-0.15 + sec_shift[sec_idx] + rng.normal(0, 0.7, N))
    beta_z = (beta - beta.mean()) / beta.std()
    lo_v, hi_v = cfg.idio_vol_range
    idio_ann = lo_v + (hi_v - lo_v) * ndtr(-0.6 - 0.45 * size_z + 0.25 * beta_z + rng.normal(0, 0.6, N))
    sig_spec = idio_ann / np.sqrt(252.0)                     # daily specific vol (base)

    # exposures: market beta, style z-scores, sector dummies
    style_cols = list(cfg.style_factors)
    sty = {}
    for s in style_cols:
        if s == "size":
            x = size_z
        elif s == "value":
            x = rng.normal(0, 1, N) + 0.6 * np.array([0.5, -0.4, 0.3, 0.8, 0.9, -0.3, 0.2, -0.8, 0.5, 0.4, 0.6]
                                                      + [0.0] * max(0, n_sec - 11))[:n_sec][sec_idx]
        elif s == "low_vol":
            x = -(0.6 * beta_z + 0.8 * (idio_ann - idio_ann.mean()) / idio_ann.std()) + rng.normal(0, 0.5, N)
        else:                                                   # momentum and any custom style
            x = rng.normal(0, 1, N)
        sty[s] = (x - x.mean()) / x.std()
    sec_cols = [f"sec_{s}" for s in sec_names]
    dummies = np.zeros((N, n_sec))
    dummies[np.arange(N), sec_idx] = 1.0
    factor_names = ["market"] + style_cols + sec_cols
    B = np.column_stack([beta] + [sty[s] for s in style_cols] + [dummies])
    factor_vol_ann = np.array([cfg.market_vol] + [_STYLE_VOL.get(s, 0.04) for s in style_cols] + list(sec_vol))
    factor_vol = factor_vol_ann / np.sqrt(252.0)

    # ---------------------------------------------------------------- factor returns + regime
    eps_m = _std_t(rng_factor, df, TT)
    if cfg.vol_clustering:
        shock_lag = np.r_[0.0, eps_m[:-1]]
        h, stress_idx, crash = _vol_regime(rng_regime, TT, burn, shock_lag, cfg.stress_per_year)
    else:
        h, stress_idx, crash = np.ones(TT), [], np.zeros(TT)
    m_spec = np.sqrt(h) / np.sqrt(np.mean(h[burn:]))          # specific-vol multiplier, mean m^2 = 1
    K = len(factor_names)
    eps_f = _std_t(rng_factor, df, (TT, K))
    eps_f[:, 0] = eps_m
    F = factor_vol[None, :] * h[:, None] * eps_f
    F[:, 0] += cfg.market_drift / 252.0 + crash

    # ---------------------------------------------------------------- planted alphas
    kappa_sig = sig_spec.mean() / np.sqrt(np.mean(sig_spec ** 2))   # cross-sectional dilution
    day_idx = np.arange(TT) - burn                                   # sample day index (burn < 0)
    pred = np.zeros((TT, N))                                          # sum_a beta_a(t) y_a[t]
    P = np.zeros(TT)                                                  # predictable variance share
    obs_signals: dict[str, np.ndarray] = {}
    loadings: dict[str, float] = {}
    for a in specs:
        phi, hd, cov_ay, var_y = _alpha_coeffs(a)
        rng = np.random.default_rng([cfg.seed, zlib.crc32(a.name.encode())])   # stream per alpha name
        hd_half = math.log(0.5) / math.log(hd) if hd > 0 else 1.0
        extra = int(min(6 * max(a.half_life, hd_half, 10.0), 3000))  # own burn-in for y's transient
        innov = rng.standard_normal((extra + TT, N))
        innov[1:] *= np.sqrt(1 - phi ** 2)                          # a[0] ~ N(0,1): stationary start
        lat = lfilter([1.0], [1.0, -phi], innov, axis=0)            # latent score a[t]
        y = lat if abs(hd - phi) < 1e-12 else lfilter([1.0, -phi], [1.0, -hd], lat, axis=0)
        lat, y = lat[extra:], y[extra:]
        obs = lat + a.noise * rng.standard_normal((TT, N)) if a.noise > 0 else lat.copy()
        obs_signals[a.name] = _zscore_rows(obs)
        b0 = a.ic * np.sqrt(1 + a.noise ** 2) / (kappa_sig * cov_ay)
        prof = np.ones(TT)
        if a.ic_halflife_years:
            prof = 0.5 ** (np.maximum(day_idx, 0) / (252.0 * a.ic_halflife_years))
        prof = np.where(day_idx < a.start_day, 0.0, prof)
        bt = b0 * prof
        pred += bt[:, None] * y
        P += bt ** 2 * var_y
        loadings[a.name] = float(b0)
    # Endogenous reversal / momentum loadings. Past returns also contain the (persistent) planted
    # alphas, which leak into the measured reversal (-) and momentum (+) ICs; correct for that
    # interaction analytically: Cov(y[t-k], y[t]) = hd^k Var(y).
    leak_rev = leak_mom = 0.0
    for a in specs:
        _, hd, _, var_y = _alpha_coeffs(a)
        b2v = loadings[a.name] ** 2 * var_y
        leak_rev += b2v * sum(hd ** k for k in range(1, 6)) / math.sqrt(5.0)
        leak_mom += b2v * sum(hd ** k for k in range(22, 253)) / math.sqrt(231.0)
    b_rev = cfg.reversal_strength / kappa_sig + (leak_rev if cfg.reversal_strength else 0.0)
    b_mom = cfg.momentum_strength / kappa_sig - (leak_mom if cfg.momentum_strength else 0.0)
    P_end = P + b_rev ** 2 + b_mom ** 2
    if np.any(P_end >= 0.5):
        raise ValueError("planted effects explain >= 50% of specific variance; lower the ICs")

    # specific returns: s[t] = sigma_i m[t] (pred[t-1] + endogenous + sqrt(1 - P[t-1]) eps[t])
    eps_s = _std_t(rng_spec, df, (TT, N))
    scale = sig_spec[None, :] * m_spec[:, None]
    noise_w = np.sqrt(1.0 - np.r_[0.0, P_end[:-1]])
    S = np.empty((TT, N))
    S[0] = scale[0] * eps_s[0]
    S[1:] = scale[1:] * (pred[:-1] + noise_w[1:, None] * eps_s[1:])
    endo = np.zeros((TT, N))                                          # endogenous expected part
    if b_rev != 0.0 or b_mom != 0.0:
        Z = np.zeros((TT, N))
        cum = np.zeros((TT + 1, N))                                   # cum[t+1] = sum Z[0..t]
        Z[0] = S[0] / scale[0]
        cum[1] = Z[0]
        for t in range(1, TT):                                        # sequential: depends on past s
            extra = np.zeros(N)
            if b_rev != 0.0 and t >= 6:
                extra -= b_rev * _zscore_rows((cum[t] - cum[t - 5])[None, :])[0]   # days t-5..t-1
            if b_mom != 0.0 and t >= 253:
                extra += b_mom * _zscore_rows((cum[t - 21] - cum[t - 252])[None, :])[0]
            endo[t - 1] = extra
            S[t] += scale[t] * extra
            Z[t] = S[t] / scale[t]
            cum[t + 1] = cum[t] + Z[t]
    exp_spec = np.empty((TT, N))
    exp_spec[:-1] = scale[1:] * (pred[:-1] + endo[:-1])
    exp_spec[-1] = scale[-1] * pred[-1]                               # last day: use today's scale

    # ---------------------------------------------------------------- totals, prices, liquidity
    R = F @ B.T + S
    R = np.maximum(R, -0.95)
    sl = slice(burn, TT)
    R, S, F = R[sl], S[sl], F[sl]
    dates = pd.bdate_range(cfg.start, periods=T)
    tickers = [f"S{i:04d}" for i in range(N)]
    rng = rng_liq
    price0 = np.clip(np.exp(rng.normal(np.log(60.0), 0.7, N)), 8.0, 800.0)
    prices = price0[None, :] * np.cumprod(1.0 + R, axis=0)
    shares_out = np.exp(log_cap) / price0
    mcap = prices * shares_out[None, :]
    adv_target = np.clip(np.exp(1.51 + 0.7 * log_cap + rng.normal(0, 0.35, N)), 4e6, 1.5e9)
    zabs = np.abs(S / scale[sl])
    vmult = np.exp(0.25 * rng.standard_normal((T, N))) * (h[sl, None] ** 0.6) * (1.0 + 0.5 * zabs)
    vmult /= vmult.mean(axis=0, keepdims=True)
    dollar_vol = adv_target[None, :] * vmult
    volume = np.round(dollar_vol / prices)
    spread = 6.0 * (adv_target / 5e7) ** -0.55 * np.exp(rng.normal(0, 0.2, N))
    spread = np.clip(np.maximum(spread, 1e4 * 0.01 / price0), 2.0, 30.0)

    def frame(x: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(x, index=dates, columns=tickers)

    vol_df = frame(volume)
    adv_usd = (vol_df * frame(prices)).rolling(20, min_periods=1).mean()
    sector = pd.Series([sec_names[j] for j in sec_idx], index=tickers, name="sector")
    return EquityMarket(
        cfg=cfg, dates=dates, tickers=tickers, sector=sector,
        beta=pd.Series(beta, index=tickers, name="beta"),
        exposures=pd.DataFrame(B, index=tickers, columns=factor_names),
        factor_returns=pd.DataFrame(F, index=dates, columns=factor_names),
        specific_returns=frame(S), returns=frame(R), prices=frame(prices), volume=vol_df,
        adv_usd=adv_usd, market_cap=frame(mcap),
        spread_bps=pd.Series(spread, index=tickers, name="spread_bps"),
        specific_vol=frame(scale[sl]),
        alphas={k: frame(v[sl]) for k, v in obs_signals.items()},
        alpha_specs={a.name: a for a in specs},
        factor_vol=pd.Series(factor_vol, index=factor_names, name="daily_vol"),
        vol_regime=pd.Series(h[sl], index=dates, name="h"),
        stress_dates=[dates[s - burn] for s in stress_idx],
        alpha_loadings=loadings,
        expected_specific_return=frame(exp_spec[sl]),
    )


def iter_noise_signals(market: EquityMarket, n: int, seed: int = 0) -> Iterator[tuple[str, pd.DataFrame]]:
    """Yield (name, signal) for ``n`` pure-noise signals shaped like ``market.alphas``.

    Each is an AR(1) with a random half-life (log-uniform 1-60 days), z-scored daily, and
    independent of everything in the market: its true IC is exactly zero.
    """
    rng = np.random.default_rng(seed)
    T, N = len(market.dates), len(market.tickers)
    width = len(str(max(n - 1, 0))) if n > 1000 else 3
    for j in range(n):
        hl = float(np.exp(rng.uniform(np.log(1.0), np.log(60.0))))
        phi = 0.5 ** (1 / hl)
        e = rng.standard_normal((T, N))
        e[1:] *= np.sqrt(1 - phi ** 2)
        x = _zscore_rows(lfilter([1.0], [1.0, -phi], e, axis=0))
        yield f"noise_{j:0{width}d}", pd.DataFrame(x, index=market.dates, columns=market.tickers)


def noise_signals(market: EquityMarket, n: int, seed: int = 0) -> dict[str, pd.DataFrame]:
    """Dict of ``n`` pure-noise signals (see ``iter_noise_signals``). ~5 MB each at default size."""
    return dict(iter_noise_signals(market, n, seed))


# =============================================================================================
# (c) limit order book / trade flow
# =============================================================================================
@dataclass
class LOBConfig:
    n_seconds: int = 23400            # 6.5 hours
    tick: float = 0.01
    start_price: float = 50.0
    daily_vol: float = 0.02           # vol of the latent fair value per 6.5-hour day
    limit_rate: float = 6.0           # new background limit orders per second (both sides)
    cancel_rate: float = 0.05         # per-second cancellation hazard of EACH resting background order
    market_rate: float = 1.0          # market orders per second
    informed_share: float = 0.25      # share of market orders from informed traders
    jump_rate_per_hour: float = 2.0   # fair-value jumps (news)
    depth_levels: int = 10            # limit orders are placed up to this many ticks from the touch
    seed: int = 7
    # extras
    jump_size_bps: float = 10.0       # std of a jump, basis points of price
    stale_cancel_prob: float = 0.3    # per second: P(cancel) of an lp order on the wrong side of FV
    lp_edge_ticks: float = 0.5        # lp orders keep a random edge U(0, this) ticks vs fair value
    placement_decay: float = 0.7      # P(k ticks behind the opposite best) ~ k ** -placement_decay
    lp_fv_lag: float = 20.0           # lps' fair-value belief is an EMA of the true FV (time constant, s)
    flow_impact_ticks: float = 0.3    # lps shift their belief by this x side x sqrt(size/100) per market order
    mean_limit_lots: float = 2.0      # mean limit order size in 100-share lots
    mean_market_lots: float = 2.5     # mean noise market order size in 100-share lots


@dataclass
class LOBSimulation:
    cfg: LOBConfig
    quotes: pd.DataFrame
    trades: pd.DataFrame
    events: pd.DataFrame
    fair_value: pd.Series
    book: OrderBook


class LOBAgentContext:
    """Passed to the ``agent`` callback of ``simulate_lob`` (see module docstring)."""

    def __init__(self, sim_record: Callable, book: OrderBook) -> None:
        self._record = sim_record
        self.book = book
        self.t = 0.0
        self.fair_value = float("nan")
        self.new_fills: list[Fill] = []
        self._pending: list[Fill] = []

    def add_limit(self, side: int, price: float, size: float) -> int:
        oid = self.book.add_limit(side, price, size, owner="agent")
        self._record(0, side, self.book.to_price(self.book.to_ticks(price)), size, oid, "agent")
        return oid

    def cancel(self, order_id: int, size: float | None = None) -> bool:
        info = self.book.order(order_id)
        ok = self.book.cancel(order_id, size)
        if ok:
            self._record(1, info.side, info.price, info.size if size is None else size, order_id, "agent")
        return ok

    def market(self, side: int, size: float) -> list[Fill]:
        fills = self.book.market(side, size, owner="agent")
        filled = sum(f.size for f in fills)
        vwap = sum(f.price * f.size for f in fills) / filled if filled else float("nan")
        self._record(2, side, vwap, size, self.book._next_id - 1, "agent")
        return fills


class _Rand:
    """Block-buffered scalar random draws (much faster than one numpy call per event)."""

    def __init__(self, draw: Callable[[int], np.ndarray], block: int = 1 << 15) -> None:
        self.draw, self.block = draw, block
        self.buf: list = []
        self.i = 0

    def __call__(self):
        if self.i >= len(self.buf):
            self.buf = self.draw(self.block).tolist()
            self.i = 0
        v = self.buf[self.i]
        self.i += 1
        return v


_EVENT_TYPES = np.array(["limit", "cancel", "market"])
_OWNERS = ["lp", "noise", "informed", "agent"]


def simulate_lob(cfg: LOBConfig | None = None, agent: Callable[[LOBAgentContext], None] | None = None,
                 agent_interval: float = 1.0, **overrides) -> LOBSimulation:
    """Simulate one stock's order book and trade flow (see module docstring)."""
    cfg = _make_cfg(LOBConfig, cfg, overrides)
    rng = np.random.default_rng(cfg.seed)
    tick = cfg.tick
    book = OrderBook(tick)
    sig_s = cfg.start_price * cfg.daily_vol / math.sqrt(23400.0)   # fair-value $ vol per sqrt(second)
    lam_l, lam_m, theta = cfg.limit_rate, cfg.market_rate, cfg.cancel_rate
    depth = int(cfg.depth_levels)

    # random streams
    r_exp = _Rand(lambda n: rng.exponential(1.0, n))
    r_uni = _Rand(lambda n: rng.random(n))
    r_nrm = _Rand(lambda n: rng.standard_normal(n))
    pk = np.arange(1, depth + 1, dtype=float) ** (-cfg.placement_decay)
    pk /= pk.sum()
    r_k = _Rand(lambda n: rng.choice(np.arange(1, depth + 1), size=n, p=pk))
    p_lim = 1.0 / cfg.mean_limit_lots
    p_mkt = 1.0 / cfg.mean_market_lots
    r_lsz = _Rand(lambda n: 100 * rng.geometric(p_lim, n))
    r_msz = _Rand(lambda n: 100 * rng.geometric(p_mkt, n))
    # fair-value jumps (times and sizes)
    n_jumps = rng.poisson(cfg.jump_rate_per_hour * cfg.n_seconds / 3600.0)
    jump_t = np.sort(rng.uniform(0, cfg.n_seconds, n_jumps)).tolist()
    jump_x = (rng.standard_normal(n_jumps) * cfg.jump_size_bps / 1e4).tolist()   # relative size

    # ------------------------------------------------------------- event + quote recording
    ev_t, ev_type, ev_side, ev_px, ev_sz, ev_id, ev_own = [], [], [], [], [], [], []
    q_bid, q_ask, q_b1, q_b2, q_b3, q_a1, q_a2, q_a3, q_fv = [], [], [], [], [], [], [], [], []
    tr = []                                     # trade tuples
    state = {"t": 0.0, "fv": cfg.start_price}
    owner_code = {o: j for j, o in enumerate(_OWNERS)}
    top3 = book._top3

    def record(etype: int, side: int, price: float, size: float, oid: int, owner: str) -> None:
        ev_t.append(state["t"]); ev_type.append(etype); ev_side.append(side); ev_px.append(price)
        ev_sz.append(size); ev_id.append(oid); ev_own.append(owner_code[owner])
        b1, a1, bs1, bs2, bs3, as1, as2, as3 = top3()
        q_bid.append(b1); q_ask.append(a1)
        q_b1.append(bs1); q_b2.append(bs2); q_b3.append(bs3)
        q_a1.append(as1); q_a2.append(as2); q_a3.append(as3)
        q_fv.append(state["fv"])

    ctx = LOBAgentContext(record, book) if agent is not None else None

    def on_fill(f: Fill) -> None:
        tr.append((f.time, f.price, f.size, f.taker_side, f.maker_id, f.maker_owner, f.taker_owner,
                   len(ev_t)))
        if ctx is not None and (f.maker_owner == "agent" or f.taker_owner == "agent"):
            ctx._pending.append(f)

    book.subscribe(on_fill)

    lp_ids: list[int] = []                      # candidate lp order ids for random cancellation
    edge = cfg.lp_edge_ticks

    def place_lp(side: int, ticks: int, size: int) -> None:
        oid = book.add_limit(side, ticks * tick, size, owner="lp")
        lp_ids.append(oid)
        record(0, side, book.to_price(ticks), size, oid, "lp")

    # ------------------------------------------------------------- initial book
    book.time = 0.0
    fv_t0 = cfg.start_price / tick
    for lvl in range(depth):
        for side in (BID, ASK):
            base = math.floor(fv_t0 - 0.25) if side == BID else math.ceil(fv_t0 + 0.25)
            for _ in range(1 + int(r_uni() * 4)):
                place_lp(side, base - side * lvl, r_lsz())

    # ------------------------------------------------------------- main loop
    t = 0.0
    fv = cfg.start_price
    jpos = 0
    next_hk = 1.0                                # housekeeping once per simulated second
    next_agent = agent_interval if agent is not None else float("inf")
    horizon = float(cfg.n_seconds)
    p_stale = cfg.stale_cancel_prob
    keys, levels = book._keys, book._levels
    fv_lp = fv                                   # liquidity providers' (lagged) fair-value belief
    flow_imp = cfg.flow_impact_ticks * tick
    lp_alpha = 1.0 - math.exp(-1.0 / cfg.lp_fv_lag) if cfg.lp_fv_lag > 0 else 1.0

    def advance_fv(t_new: float) -> None:
        nonlocal fv, jpos
        fv += sig_s * math.sqrt(t_new - t) * r_nrm()
        while jpos < n_jumps and jump_t[jpos] <= t_new:
            fv *= 1.0 + jump_x[jpos]
            jpos += 1
        fv = max(fv, 10 * tick)
        state["fv"] = fv

    while True:
        rate = lam_l + lam_m + theta * len(lp_ids)
        t_next = t + r_exp() / rate
        t_hk = min(next_hk, next_agent)
        if t_next >= t_hk or t_next >= horizon:
            # ---- scheduled housekeeping / agent call (memoryless: redraw the next event after)
            t_new = min(t_hk, horizon)
            advance_fv(t_new)
            t = t_new
            state["t"] = t
            book.time = t
            if t >= horizon:
                break
            if t >= next_hk:
                next_hk += 1.0
                fv_lp += lp_alpha * (fv - fv_lp)         # lps update their belief once a second
                fv_ticks = fv_lp / tick
                # (1) fast lps pull quotes that are on the wrong side of fair value
                for side in (BID, ASK):
                    kk = keys[side]
                    j = len(kk) - 1
                    stale_levels = []
                    while j >= 0 and (side * kk[j] > fv_ticks if side == BID else -kk[j] < fv_ticks):
                        stale_levels.append(side * kk[j])
                        j -= 1
                    for lv_t in stale_levels:
                        lv = levels[side].get(lv_t)
                        if lv is None:
                            continue
                        for o in [o for o in lv.orders.values() if o.owner == "lp"]:
                            if r_uni() < p_stale:
                                sz = o.size
                                book.cancel(o.id)
                                record(1, side, o.price, sz, o.id, "lp")
                # (2) clean up lp orders far from the touch
                for side in (BID, ASK):
                    kk = keys[side]
                    if not kk:
                        continue
                    cutoff = kk[-1] - depth - 2              # keys are side*ticks; best is kk[-1]
                    far = [side * k for k in kk if k < cutoff]
                    for lv_t in far:
                        lv = levels[side].get(lv_t)
                        if lv is None:
                            continue
                        for o in [o for o in lv.orders.values() if o.owner == "lp"]:
                            sz = o.size
                            book.cancel(o.id)
                            record(1, side, o.price, sz, o.id, "lp")
            if t >= next_agent:
                next_agent += agent_interval
                ctx.t, ctx.fair_value = t, fv
                ctx.new_fills, ctx._pending = ctx._pending, []
                agent(ctx)
            continue

        advance_fv(t_next)
        t = t_next
        state["t"] = t
        book.time = t
        u = r_uni() * rate
        if u < lam_l:
            # ---------------- background limit order
            side = BID if r_uni() < 0.5 else ASK
            k = r_k()
            fv_ticks = fv_lp / tick
            kb, ka = keys[BID], keys[ASK]
            if side == BID:
                best_ok = math.floor(fv_ticks - edge * r_uni())          # highest bid lp accepts
                if ka:
                    best_ok = min(best_ok, -ka[-1] - 1)                  # stay non-marketable
                ticks = best_ok - (k - 1)
            else:
                best_ok = math.ceil(fv_ticks + edge * r_uni())
                if kb:
                    best_ok = max(best_ok, kb[-1] + 1)
                ticks = best_ok + (k - 1)
            place_lp(side, ticks, r_lsz())
        elif u < lam_l + lam_m:
            # ---------------- market order (noise or informed)
            kb, ka = keys[BID], keys[ASK]
            if kb and ka:
                mid_t = 0.5 * (kb[-1] - ka[-1])
            else:
                mid_t = fv / tick
            size = r_msz()
            if r_uni() < cfg.informed_share:
                owner = "informed"
                gap = fv / tick - mid_t
                side = BUY if gap > 0 else (SELL if gap < 0 else (BUY if r_uni() < 0.5 else SELL))
                size = int(100 * round(size / 100 * (1.0 + 0.5 * min(abs(gap), 4.0))))
            else:
                owner = "noise"
                side = BUY if r_uni() < 0.5 else SELL
            fills = book.market(side, size, owner=owner)
            filled = sum(f.size for f in fills)
            vwap = sum(f.price * f.size for f in fills) / filled if filled else float("nan")
            record(2, side, vwap, size, book._next_id - 1, owner)
            fv_lp += side * flow_imp * math.sqrt(size / 100.0)   # lps learn from order flow
        else:
            # ---------------- cancellation of a random resting lp order (thinning)
            j = int(r_uni() * len(lp_ids))
            oid = lp_ids[j]
            lp_ids[j] = lp_ids[-1]
            lp_ids.pop()
            o = book._orders.get(oid)
            if o is not None:
                side, px, sz = o.side, o.price, o.size
                book.cancel(oid)
                record(1, side, px, sz, oid, "lp")

    # ------------------------------------------------------------- assemble outputs
    n_ev = len(ev_t)
    bid = np.array([np.nan if x is None else x * tick for x in q_bid])
    ask = np.array([np.nan if x is None else x * tick for x in q_ask])
    bs1, as1 = np.array(q_b1, float), np.array(q_a1, float)
    with np.errstate(invalid="ignore", divide="ignore"):
        imb = (bs1 - as1) / (bs1 + as1)
    quotes = pd.DataFrame({
        "time": np.array(ev_t), "bid": np.round(bid, 8), "ask": np.round(ask, 8),
        "bid_size": bs1, "ask_size": as1, "mid": np.round(0.5 * (bid + ask), 8),
        "spread": np.round(ask - bid, 8), "imbalance": imb,
        "bid_size_2": np.array(q_b2, float), "ask_size_2": np.array(q_a2, float),
        "bid_size_3": np.array(q_b3, float), "ask_size_3": np.array(q_a3, float),
    })
    events = pd.DataFrame({
        "time": np.array(ev_t), "type": _EVENT_TYPES[np.array(ev_type, dtype=int)],
        "side": np.array(ev_side, dtype=int), "price": np.array(ev_px, dtype=float),
        "size": np.array(ev_sz, dtype=float), "order_id": np.array(ev_id, dtype=np.int64),
        "owner": np.array(_OWNERS, dtype=object)[np.array(ev_own, dtype=int)],
    })
    if tr:
        tt = list(zip(*tr))
        trades = pd.DataFrame({
            "time": np.array(tt[0], float), "price": np.array(tt[1], float),
            "size": np.array(tt[2], float), "side": np.array(tt[3], dtype=int),
            "informed": np.array([o == "informed" for o in tt[6]]),
            "maker_id": np.array(tt[4], dtype=np.int64),
            "maker_owner": np.array(tt[5], dtype=object), "taker_owner": np.array(tt[6], dtype=object),
            "event_idx": np.array(tt[7], dtype=np.int64),
        })
    else:
        trades = pd.DataFrame(columns=["time", "price", "size", "side", "informed", "maker_id",
                                       "maker_owner", "taker_owner", "event_idx"])
    fair = pd.Series(np.array(q_fv), index=quotes.index, name="fair_value")
    assert len(events) == n_ev == len(quotes)
    return LOBSimulation(cfg=cfg, quotes=quotes, trades=trades, events=events, fair_value=fair, book=book)



# =============================================================================================
# (d) options from a Heston model with a variance risk premium
# =============================================================================================
@dataclass
class OptionMarketConfig:
    n_days: int = 252
    steps_per_day: int = 26
    s0: float = 100.0
    r: float = 0.0
    v0: float = 0.04
    kappa: float = 2.0
    theta: float = 0.04
    xi: float = 0.6
    rho: float = -0.7                 # physical-measure Heston parameters
    vrp: float = 0.25                 # risk-neutral variance = physical x (1 + vrp)
    expiries_days: tuple = (7, 30, 60, 91)
    moneyness: tuple = (0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2)
    seed: int = 7
    # extras
    mu: float = 0.05                  # physical drift of the underlying (annual)


@dataclass
class OptionMarket:
    cfg: OptionMarketConfig
    path: pd.DataFrame
    chain: pd.DataFrame
    daily: pd.DataFrame = None
    q_params: dict = field(default_factory=dict)

    def realized_vol(self, window_days: int = 21, forward: bool = False) -> pd.Series:
        """Annualized realized vol of daily close-to-close log returns (not demeaned).

        Trailing (days d-window+1..d) by default; ``forward=True`` uses days d+1..d+window.
        """
        r2 = np.log(self.daily["S"]).diff() ** 2
        rv = np.sqrt(252.0 * r2.rolling(window_days).mean())
        if forward:
            rv = rv.shift(-window_days)
        return rv.rename(f"rv{window_days}{'_fwd' if forward else ''}")

    def price(self, day: int, strike, T, call=True):
        """Model (risk-neutral Heston) price of any option on ``day`` (vectorized)."""
        S = float(self.daily["S"].iloc[day])
        v = float(self.daily["v"].iloc[day])
        q = self.q_params
        return options.heston_price(S, strike, T, self.cfg.r, v * (1 + self.cfg.vrp),
                                    q["kappa"], q["theta"], q["xi"], q["rho"], call)


def simulate_option_market(cfg: OptionMarketConfig | None = None, **overrides) -> OptionMarket:
    """Heston underlying (physical measure) + a daily constant-maturity option chain."""
    cfg = _make_cfg(OptionMarketConfig, cfg, overrides)
    rng = np.random.default_rng(cfg.seed)
    spd = int(cfg.steps_per_day)
    n_steps = int(cfg.n_days) * spd
    dt = 1.0 / (252.0 * spd)
    z1 = rng.standard_normal(n_steps)
    z2 = cfg.rho * z1 + math.sqrt(1 - cfg.rho ** 2) * rng.standard_normal(n_steps)
    lnS = np.empty(n_steps + 1)
    v = np.empty(n_steps + 1)
    lnS[0], v[0] = math.log(cfg.s0), cfg.v0
    x, vv = lnS[0], cfg.v0
    sq_dt = math.sqrt(dt)
    kap, th, xi, mu = cfg.kappa, cfg.theta, cfg.xi, cfg.mu
    for i in range(n_steps):                       # full-truncation Euler (Lord et al. 2010)
        vp = vv if vv > 0.0 else 0.0
        sv = math.sqrt(vp) * sq_dt
        x += (mu - 0.5 * vp) * dt + sv * z1[i]
        vv += kap * (th - vp) * dt + xi * sv * z2[i]
        lnS[i + 1] = x
        v[i + 1] = vv if vv > 0.0 else 0.0
    steps = np.arange(n_steps + 1)
    path = pd.DataFrame({"t": steps * dt, "S": np.exp(lnS), "v": v,
                         "day": steps // spd, "step": steps})
    eod = steps[::spd]                              # day d close = step d * steps_per_day
    daily = pd.DataFrame({"S": np.exp(lnS[eod]), "v": v[eod]}, index=pd.RangeIndex(len(eod), name="day"))

    # risk-neutral parameters (reduced-form VRP)
    q = {"kappa": cfg.kappa, "theta": cfg.theta * (1 + cfg.vrp), "xi": cfg.xi, "rho": cfg.rho}
    days = daily.index.to_numpy()
    Sd = daily["S"].to_numpy()
    vQ = daily["v"].to_numpy() * (1 + cfg.vrp)
    exp_d = np.asarray(cfg.expiries_days, dtype=float)
    mny = np.asarray(cfg.moneyness, dtype=float)
    D, E, M = np.meshgrid(days, exp_d, mny, indexing="ij")          # (days, expiries, strikes)
    Sg, Vg = Sd[D], vQ[D]
    Tg = E / 252.0
    Kg = M * Sg
    calls = options.heston_price(Sg, Kg, Tg, cfg.r, Vg, q["kappa"], q["theta"], q["xi"], q["rho"], True)
    disc_k = Kg * np.exp(-cfg.r * Tg)
    puts = calls - Sg + disc_k
    otm_call = Kg >= Sg * np.exp(cfg.r * Tg)                       # invert the OTM option
    iv = options.implied_vol(np.where(otm_call, calls, puts), Sg, Kg, Tg, cfg.r, otm_call)
    rows = []
    for is_call, px in ((True, calls), (False, puts)):
        g = options.bs_greeks(Sg, Kg, Tg, cfg.r, np.where(np.isfinite(iv), iv, 0.2), is_call)
        rows.append(pd.DataFrame({
            "day": D.ravel(), "expiry_days": E.ravel().astype(int), "T": Tg.ravel(),
            "strike": Kg.ravel(), "moneyness": M.ravel(), "spot": Sg.ravel(),
            "call": is_call, "price": px.ravel(), "implied_vol": iv.ravel(),
            "delta": g["delta"].ravel(), "gamma": g["gamma"].ravel(), "vega": g["vega"].ravel(),
        }))
    chain = pd.concat(rows, ignore_index=True)
    chain = chain.sort_values(["day", "expiry_days", "call", "strike"], kind="stable").reset_index(drop=True)
    return OptionMarket(cfg=cfg, path=path, chain=chain, daily=daily, q_params=q)


# =============================================================================================
# futures panel for trend following
# =============================================================================================
_FUT_UNIVERSE = [
    # name, class, annual vol
    ("EQ_US_LARGE", "equity", 0.17), ("EQ_US_SMALL", "equity", 0.22), ("EQ_EUROPE", "equity", 0.19),
    ("EQ_JAPAN", "equity", 0.20), ("EQ_UK", "equity", 0.16), ("EQ_EM", "equity", 0.23),
    ("UST_2Y", "rates", 0.02), ("UST_10Y", "rates", 0.06), ("UST_30Y", "rates", 0.12),
    ("BUND_10Y", "rates", 0.06), ("GILT_10Y", "rates", 0.07), ("JGB_10Y", "rates", 0.03),
    ("EURUSD", "fx", 0.08), ("GBPUSD", "fx", 0.09), ("USDJPY", "fx", 0.09),
    ("AUDUSD", "fx", 0.11), ("USDCAD", "fx", 0.07), ("USDCHF", "fx", 0.08),
    ("CRUDE", "commodity", 0.35), ("NATGAS", "commodity", 0.45), ("GOLD", "commodity", 0.15),
    ("COPPER", "commodity", 0.24), ("CORN", "commodity", 0.25), ("SOYBEANS", "commodity", 0.21),
]
_FUT_CLASSES = ("equity", "rates", "fx", "commodity")


@dataclass
class FuturesConfig:
    n_assets: int = 24
    n_days: int = 252 * 20
    trend_strength: float = 0.045     # std of the daily drift in units of daily vol (see docstring)
    seed: int = 7
    # extras
    regime_days: float = 250.0        # mean length of a drift regime (trading days)
    class_trend_share: float = 0.3    # share of drift variance common within an asset class
    fat_tails_df: float = 5.0
    start: str = "2005-01-03"


@dataclass
class FuturesMarket:
    returns: pd.DataFrame
    asset_class: pd.Series
    true_drift: pd.DataFrame
    vol: pd.DataFrame = None          # true daily vol per asset and day
    cfg: FuturesConfig = None


def _regime_process(rng: np.random.Generator, n: int, k: int, mean_len: float) -> np.ndarray:
    """k independent piecewise-constant N(0,1) processes with geometric regime lengths."""
    switch = rng.random((n, k)) < 1.0 / mean_len
    switch[0] = True
    regime_id = np.cumsum(switch, axis=0)                     # regime counter per column
    levels = rng.standard_normal((int(regime_id.max()) + 1, k))
    return np.take_along_axis(levels, regime_id, axis=0)


def simulate_futures(cfg: FuturesConfig | None = None, **overrides) -> FuturesMarket:
    """Diversified futures panel with persistent drift regimes (see module docstring)."""
    cfg = _make_cfg(FuturesConfig, cfg, overrides)
    rng = np.random.default_rng(cfg.seed)
    n, T = int(cfg.n_assets), int(cfg.n_days)
    names, classes, vols = [], [], []
    for j in range(n):
        if j < len(_FUT_UNIVERSE):
            nm, cl, vo = _FUT_UNIVERSE[j]
        else:
            cl = _FUT_CLASSES[j % 4]
            nm, vo = f"{cl.upper()[:3]}_{j:02d}", {"equity": 0.19, "rates": 0.06, "fx": 0.09, "commodity": 0.27}[cl]
        names.append(nm); classes.append(cl); vols.append(vo)
    cls_idx = np.array([_FUT_CLASSES.index(c) for c in classes])
    vols = np.array(vols)

    # correlation via factors: risk-on/off, equity block, duration, USD, commodity block
    L = np.zeros((n, 5))
    for j, (nm, cl) in enumerate(zip(names, classes)):
        if cl == "equity":
            L[j] = [0.55, 0.65, 0, 0, 0]
        elif cl == "rates":
            L[j] = [-0.25, 0, 0.75 if nm not in ("UST_2Y", "JGB_10Y") else 0.55, 0, 0]
        elif cl == "fx":
            usd = -0.6 if nm.startswith("USD") else 0.6          # quote convention flips the sign
            L[j] = [0.25 if nm in ("AUDUSD",) else 0.05, 0, 0, usd, 0]
        else:
            L[j] = [0.30, 0, 0, -0.15, 0.45 if nm not in ("GOLD",) else 0.15]
    idio = np.sqrt(np.maximum(1.0 - (L ** 2).sum(axis=1), 0.05))

    # volatility clustering: global + asset log-AR(1), normalized to mean(m^2) = 1 per asset
    zg = rng.standard_normal(T)
    za = rng.standard_normal((T, n))
    phi = 0.985
    log_g = lfilter([1.0], [1.0, -phi], 0.20 * math.sqrt(1 - phi ** 2) * zg)
    log_a = lfilter([1.0], [1.0, -phi], 0.25 * math.sqrt(1 - phi ** 2) * za, axis=0)
    for s in rng.choice(np.arange(20, max(T - 20, 21)), size=max(1, rng.poisson(0.3 * T / 252)), replace=False):
        log_g[s:] += math.log(rng.uniform(1.8, 3.0)) * 0.5 ** (np.arange(T - s) / rng.uniform(10, 30))
    mult = np.exp(log_g[:, None] + log_a)
    mult /= np.sqrt(np.mean(mult ** 2, axis=0, keepdims=True))
    sig = vols[None, :] / math.sqrt(252.0) * mult                     # true daily vol

    df = cfg.fat_tails_df
    eps = _std_t(rng, df, (T, 5)) @ L.T + _std_t(rng, df, (T, n)) * idio[None, :]
    # drift regimes: common within class + asset-specific, unit variance overall
    zc = _regime_process(rng, T, 4, cfg.regime_days)
    zi = _regime_process(rng, T, n, cfg.regime_days)
    w = cfg.class_trend_share
    z = math.sqrt(w) * zc[:, cls_idx] + math.sqrt(1 - w) * zi
    drift = cfg.trend_strength * sig * z
    rets = drift + sig * eps
    dates = pd.bdate_range(cfg.start, periods=T)
    return FuturesMarket(
        returns=pd.DataFrame(rets, index=dates, columns=names),
        asset_class=pd.Series(classes, index=names, name="asset_class"),
        true_drift=pd.DataFrame(drift, index=dates, columns=names),
        vol=pd.DataFrame(sig, index=dates, columns=names), cfg=cfg,
    )


# =============================================================================================
# intraday session for execution labs
# =============================================================================================
@dataclass
class IntradayConfig:
    n_bins: int = 390
    price: float = 50.0
    daily_vol: float = 0.02
    adv_shares: float = 5e6
    spread_bps: float = 3.0
    close_auction_share: float = 0.10   # share of daily volume in the closing auction
    seed: int = 7
    # extras
    volume_noise: float = 0.35          # lognormal noise of per-minute volume
    day_volume_noise: float = 0.25      # lognormal noise of the day's total volume vs ADV


def intraday_volume_profile(n_bins: int = 390) -> np.ndarray:
    """U-shaped share of continuous-session volume per bin (sums to 1).

    Calibrated to the typical US large-cap shape: the first minutes trade ~3x the average
    minute, the midday trough ~0.6x, the last minutes ~2.5x (close auction excluded).
    """
    x = (np.arange(n_bins) + 0.5) / n_bins
    w = 0.55 + 2.4 * np.exp(-x / 0.035) + 0.45 * np.exp(-x / 0.25) + 1.9 * np.exp(-(1 - x) / 0.04) \
        + 0.35 * np.exp(-(1 - x) / 0.2)
    return w / w.sum()


def simulate_intraday_session(cfg: IntradayConfig | None = None, **overrides) -> pd.DataFrame:
    """One trading day of minute bars plus a closing auction (see module docstring)."""
    cfg = _make_cfg(IntradayConfig, cfg, overrides)
    rng = np.random.default_rng(cfg.seed)
    n = int(cfg.n_bins)
    prof = intraday_volume_profile(n)
    day_mult = math.exp(cfg.day_volume_noise * rng.standard_normal() - 0.5 * cfg.day_volume_noise ** 2)
    total = cfg.adv_shares * day_mult
    cont = total * (1 - cfg.close_auction_share)
    noise = np.exp(cfg.volume_noise * rng.standard_normal(n) - 0.5 * cfg.volume_noise ** 2)
    vol = np.round(cont * prof * noise / np.sum(prof * noise))
    # price: variance per minute proportional to the volume profile; 10 sub-steps per minute
    sub = 10
    var_bin = cfg.daily_vol ** 2 * prof                                # sums to daily variance
    shocks = _std_t(rng, 5.0, (n, sub)) * np.sqrt(var_bin[:, None] / sub)
    logp = math.log(cfg.price) + np.cumsum(shocks.ravel()).reshape(n, sub)
    p = np.exp(logp)
    open_px = cfg.price
    prev_close = np.r_[open_px, p[:-1, -1]]
    high = np.maximum(p.max(axis=1), prev_close)
    low = np.minimum(p.min(axis=1), prev_close)
    vwap = p.mean(axis=1)
    x = (np.arange(n) + 0.5) / n
    spread_bps = cfg.spread_bps * (1 + 1.5 * np.exp(-x / 0.03) + 0.2 * np.exp(-(1 - x) / 0.05)) \
        * np.exp(0.1 * rng.standard_normal(n))
    mid = p[:, -1]
    spread = np.maximum(np.round(mid * spread_bps / 1e4, 4), 0.01)
    close_auction_volume = float(np.round(total * cfg.close_auction_share * math.exp(0.2 * rng.standard_normal())))
    close_price = float(mid[-1] * math.exp(0.15 * cfg.daily_vol / math.sqrt(n) * rng.standard_normal()))
    bars = pd.DataFrame({"minute": np.arange(n), "volume": vol, "mid": mid, "spread": spread,
                         "spread_bps": spread / mid * 1e4, "high": high, "low": low, "vwap": vwap})
    bars.attrs.update({"close_auction_volume": close_auction_volume, "close_price": close_price,
                       "open_price": open_px, "continuous_volume": float(vol.sum())})
    return bars


# =============================================================================================
# selftest
# =============================================================================================
def _selftest() -> int:  # pragma: no cover - exercised from the command line
    results: list[tuple[bool, str]] = []

    def check(ok: bool, msg: str) -> None:
        results.append((bool(ok), msg))
        print(f"{'PASS' if ok else 'FAIL'}  {msg}", flush=True)

    # ------------------------------------------------------------------ equity
    t0 = time.time()
    m = simulate_equity_market()
    dt_eq = time.time() - t0
    check(dt_eq < 5.0, f"equity: default simulate_equity_market() in {dt_eq:.2f}s (< 5 s)")
    m2 = simulate_equity_market()
    check(np.array_equal(m.returns.to_numpy(), m2.returns.to_numpy()), "equity: deterministic given seed")
    mv = m.factor_returns["market"].std() * np.sqrt(252)
    check(0.13 <= mv <= 0.19, f"equity: realized market-factor vol {mv:.1%} (target ~16%)")
    roll = m.factor_returns["market"].rolling(21).std() * np.sqrt(252)
    check(roll.max() > 1.8 * roll.median(), f"equity: stress spikes, max 21d vol {roll.max():.0%} vs median {roll.median():.0%}")
    C = np.corrcoef(m.returns.to_numpy().T)
    iu = np.triu_indices_from(C, 1)
    avg_corr = C[iu].mean()
    same = (m.sector.to_numpy()[:, None] == m.sector.to_numpy()[None, :])[iu]
    check(0.20 <= avg_corr <= 0.35, f"equity: avg pairwise corr {avg_corr:.3f} (target 0.2-0.35)")
    check(C[iu][same].mean() > avg_corr + 0.05, f"equity: within-sector corr {C[iu][same].mean():.3f} > overall")
    sv = m.specific_returns.std()
    check(0.009 <= sv.quantile(0.05) and sv.quantile(0.95) <= 0.032,
          f"equity: daily specific vol 5-95% range {sv.quantile(.05):.2%}-{sv.quantile(.95):.2%} (~1-3%)")
    check(m.beta.min() >= 0.6 and m.beta.max() <= 1.5, f"equity: betas {m.beta.min():.2f}-{m.beta.max():.2f}")
    adv = m.adv_usd.mean()
    check(adv.min() > 2e6 and adv.max() < 3e9, f"equity: mean ADV ${adv.min()/1e6:.0f}M-${adv.max()/1e6:.0f}M")
    rho_sp = np.corrcoef(np.log(adv), m.spread_bps)[0, 1]
    check(m.spread_bps.between(2, 30).all() and rho_sp < -0.5,
          f"equity: spreads {m.spread_bps.min():.1f}-{m.spread_bps.max():.1f} bps, corr(log ADV, spread) {rho_sp:.2f}")
    fwd1 = m.forward_returns(1, specific=True)
    for name, spec in m.alpha_specs.items():
        ic = cross_sectional_ic(m.alphas[name], fwd1).mean()
        ric = cross_sectional_ic(m.alphas[name], fwd1, rank=True).mean()
        check(abs(ic - spec.ic) <= 0.005, f"equity: {name} measured IC {ic:.4f} (rank {ric:.4f}) vs target {spec.ic}")
        decay_ok, msgs = True, []
        for k in (1, 2, 5):
            fk = m.specific_returns.shift(-(1 + k))
            ick = cross_sectional_ic(m.alphas[name], fk).mean()
            tgt = spec.ic * spec.horizon_decay ** k
            decay_ok &= abs(ick - tgt) <= 0.006
            msgs.append(f"lag{k} {ick:.4f}/{tgt:.4f}")
        check(decay_ok, f"equity: {name} IC decay (measured/target) " + ", ".join(msgs))
    # turnover ordering follows half-life
    to = {k: (v.diff().abs().mean().mean()) for k, v in m.alphas.items()}
    check(to["alpha_fast"] > to["alpha_med"] > to["alpha_slow"], "equity: signal turnover ordered fast > med > slow")
    ns = noise_signals(m, 20, seed=1)
    nic = np.mean([cross_sectional_ic(s, fwd1).mean() for s in ns.values()])
    check(abs(nic) < 0.004, f"equity: 20 noise signals mean IC {nic:+.4f} (~0)")
    cov = m.true_covariance(100)
    check(np.allclose(cov.to_numpy(), cov.to_numpy().T) and np.all(np.linalg.eigvalsh(cov.to_numpy()) > 0),
          "equity: true_covariance symmetric positive definite")
    mr = simulate_equity_market(reversal_strength=0.04, momentum_strength=0.02)
    f1r = mr.forward_returns(1, specific=True)
    ic_rev = cross_sectional_ic(-reversal_signal(mr), f1r).mean()
    ic_mom = cross_sectional_ic(momentum_signal(mr), f1r).mean()
    check(abs(ic_rev - 0.04) <= 0.006 and abs(ic_mom - 0.02) <= 0.006,
          f"equity: endogenous reversal IC {ic_rev:.4f} (target 0.04), 12-1 momentum IC {ic_mom:.4f} (0.02)")
    al = (PlantedAlpha("late", ic=0.04, half_life=5, horizon_decay=0.5 ** (1 / 5), start_day=630),
          PlantedAlpha("decay", ic=0.05, half_life=5, horizon_decay=0.5 ** (1 / 5), ic_halflife_years=2.0))
    md = simulate_equity_market(alphas=al, seed=3)
    f1d = md.forward_returns(1, specific=True)
    late = cross_sectional_ic(md.alphas["late"], f1d)
    dec = cross_sectional_ic(md.alphas["decay"], f1d).groupby(np.arange(len(md.dates)) // 252).mean()
    check(abs(late.iloc[:630].mean()) < 0.006 and abs(late.iloc[630:].mean() - 0.04) < 0.006
          and dec.iloc[0] > 2 * dec.iloc[-1] > 0,
          f"equity: start_day (IC {late.iloc[:630].mean():+.4f} before, {late.iloc[630:].mean():.4f} after) and "
          f"ic_halflife_years=2 (yearly IC {', '.join(f'{x:.3f}' for x in dec)})")
    base = simulate_equity_market(alphas=())
    check(np.array_equal(base.factor_returns.to_numpy(), m.factor_returns.to_numpy()),
          "equity: planting alphas leaves factor returns unchanged (independent random streams)")

    # ------------------------------------------------------------------ LOB
    t0 = time.time()
    smoke = simulate_lob(n_seconds=1800)
    dt_smoke = time.time() - t0
    check(dt_smoke < 3.0, f"lob: 1,800-second smoke run in {dt_smoke:.2f}s (< 3 s), {len(smoke.events):,} events")
    replay = OrderBook(smoke.cfg.tick)
    vol = 0.0
    for ev in smoke.events.itertuples(index=False):
        if ev.type == "limit":
            replay.add_limit(ev.side, ev.price, ev.size)
            vol += sum(f.size for f in replay.last_fills)
        elif ev.type == "cancel":
            replay.cancel(ev.order_id, ev.size)
        else:
            vol += sum(f.size for f in replay.market(ev.side, ev.size))
    same = replay.depth(BID, 10) == smoke.book.depth(BID, 10) and replay.depth(ASK, 10) == smoke.book.depth(ASK, 10)
    check(same and vol == smoke.trades["size"].sum(),
          "lob: replaying `events` on a fresh OrderBook reproduces the final book and traded volume")
    t0 = time.time()
    sim = simulate_lob()
    dt_lob = time.time() - t0
    check(dt_lob < 20.0, f"lob: default simulate_lob() in {dt_lob:.1f}s (< 20 s), {len(sim.events):,} events")
    q = sim.quotes
    sp_ticks = np.round(q["spread"] / sim.cfg.tick)
    frac13 = sp_ticks.between(1, 3).mean()
    check(frac13 > 0.9, f"lob: spread 1-3 ticks in {frac13:.1%} of events (1 tick {np.mean(sp_ticks == 1):.0%}, "
                        f"2 ticks {np.mean(sp_ticks == 2):.0%})")
    imb_corr, _ = lob_imbalance_predictiveness(sim)
    check(imb_corr > 0.1, f"lob: corr(top-of-book imbalance, next mid move) = {imb_corr:.3f} (> 0)")
    mk = lob_markouts(sim, horizon=10.0)
    check(mk["informed"] < 0 < mk["noise"],
          f"lob: LP markout at 10s, ticks/share: informed {mk['informed']:+.2f}, noise {mk['noise']:+.2f}")
    err = (q["mid"] - sim.fair_value).abs() / sim.cfg.tick
    check(err.median() < 3, f"lob: median |mid - fair value| {err.median():.2f} ticks")
    bar = q.set_index(pd.to_timedelta(q["time"], unit="s"))["mid"].resample("5min").last().dropna()
    rv = np.log(bar).diff().std() * np.sqrt(len(bar))
    check(0.012 <= rv <= 0.035, f"lob: realized daily vol of mid from 5-min returns {rv:.2%} (fair value {sim.cfg.daily_vol:.0%})")

    # ------------------------------------------------------------------ options
    t0 = time.time()
    om = simulate_option_market()
    dt_opt = time.time() - t0
    check(dt_opt < 10.0, f"options: default simulate_option_market() in {dt_opt:.2f}s (< 10 s), {len(om.chain):,} rows")
    Kg, Tg = np.meshgrid(np.linspace(60, 160, 41), [0.02, 0.25, 1.0, 3.0])
    pr = options.bs_price(100, Kg, Tg, 0.02, 0.3, Kg > 100)
    tv = pr - np.where(Kg > 100, np.maximum(100 - Kg * np.exp(-0.02 * Tg), 0), np.maximum(Kg * np.exp(-0.02 * Tg) - 100, 0))
    ivs = options.implied_vol(pr, 100, Kg, Tg, 0.02, Kg > 100)
    iv_err = np.max(np.abs(ivs - 0.3)[tv > 1e-4])     # vol is only identifiable with some time value
    g = options.bs_greeks(100, 105, 0.5, 0.03, 0.25)
    hh = 1e-4
    fd_delta = (options.bs_price(100 + hh, 105, .5, .03, .25) - options.bs_price(100 - hh, 105, .5, .03, .25)) / (2 * hh)
    fd_vega = (options.bs_price(100, 105, .5, .03, .25 + hh) - options.bs_price(100, 105, .5, .03, .25 - hh)) / (2 * hh)
    fd_theta = -(options.bs_price(100, 105, .5 + hh, .03, .25) - options.bs_price(100, 105, .5 - hh, .03, .25)) / (2 * hh)
    check(iv_err < 1e-6 and abs(g["delta"] - fd_delta) < 1e-6 and abs(g["vega"] - fd_vega) < 1e-5
          and abs(g["theta"] - fd_theta) < 1e-5,
          f"options: Black-Scholes implied-vol round trip (max error {iv_err:.1e}) and greeks match finite differences")
    ref = options.heston_price(100, 100, 1.0, 0.0, 0.0175, 1.5768, 0.0398, 0.5751, -0.5711)
    check(abs(ref - 5.785155450) < 1e-3, f"options: Heston vs Fang-Oosterlee reference: {ref:.6f} vs 5.785155")
    c = om.chain
    atm30 = c[(c.expiry_days == 30) & (c.moneyness == 1.0) & c.call].set_index("day")["implied_vol"]
    sk = c[(c.expiry_days == 30) & c.call].pivot(index="day", columns="moneyness", values="implied_vol")
    skew = (sk[0.9] - sk[1.1]).mean()
    check(skew > 0.01, f"options: 30d skew IV(90%) - IV(110%) = {skew:+.3f} (negative skew)")
    fwd_rv = om.realized_vol(30, forward=True)
    vrp_gap = (atm30 - fwd_rv).dropna().mean()
    check(vrp_gap > 0.005, f"options: mean 30d ATM IV - subsequent realized vol = {vrp_gap:+.3f} (VRP > 0)")
    long = simulate_option_market(n_days=1260, steps_per_day=8, expiries_days=(30,), moneyness=(1.0,), seed=11)
    lc = long.chain[long.chain.call].set_index("day")["implied_vol"]
    gap_long = (lc - long.realized_vol(30, forward=True)).dropna().mean()
    check(gap_long > 0.005, f"options: same over a 5-year path, seed 11: {gap_long:+.3f}")
    pc = c[c.call].price.to_numpy() - c[~c.call].price.to_numpy()
    par = (c[c.call].spot - c[c.call].strike * np.exp(-om.cfg.r * c[c.call]["T"])).to_numpy()
    check(np.allclose(pc, par, atol=1e-8), "options: put-call parity holds in the chain")
    check(c.implied_vol.notna().mean() > 0.95, f"options: implied vol defined for {c.implied_vol.notna().mean():.1%} of rows")

    # ------------------------------------------------------------------ futures
    t0 = time.time()
    fm = simulate_futures()
    dt_fut = time.time() - t0
    check(dt_fut < 3.0, f"futures: default simulate_futures() in {dt_fut:.2f}s (< 3 s)")
    sr = tsmom_sharpe(fm)
    check(0.4 <= sr <= 1.2, f"futures: 12-month TSMOM gross Sharpe {sr:.2f} (target ~0.5-1.0)")
    av = fm.returns.std() * np.sqrt(252)
    check(av.min() > 0.01 and av.max() < 0.6, f"futures: annual vols {av.min():.0%}-{av.max():.0%}")

    # ------------------------------------------------------------------ intraday
    t0 = time.time()
    prof = intraday_volume_profile()
    bars = simulate_intraday_session()
    dt_in = time.time() - t0
    check(abs(prof.sum() - 1) < 1e-12 and prof[0] > 2 * np.median(prof) and prof[-1] > 2 * np.median(prof),
          f"intraday: U-shaped profile (first {prof[0] / prof.mean():.1f}x, mid {np.median(prof) / prof.mean():.1f}x,"
          f" last {prof[-1] / prof.mean():.1f}x the average minute)")
    tot = bars.volume.sum() + bars.attrs["close_auction_volume"]
    share = bars.attrs["close_auction_volume"] / tot
    check(0.3 < tot / 5e6 < 3 and 0.05 < share < 0.2,
          f"intraday: day volume {tot / 1e6:.2f}M shares, close auction {share:.1%}; {dt_in * 1e3:.0f} ms")

    n_fail = sum(not ok for ok, _ in results)
    print(f"\n{len(results) - n_fail}/{len(results)} checks passed")
    return 1 if n_fail else 0


# --------------------------------------------------------------------------- analysis helpers
def reversal_signal(m: EquityMarket) -> pd.DataFrame:
    """5-day cumulative specific return ending at t, cross-sectionally z-scored (reversal input)."""
    z = m.specific_returns / m.specific_vol
    return pd.DataFrame(_zscore_rows(z.rolling(5).sum().to_numpy()), index=m.dates, columns=m.tickers)


def momentum_signal(m: EquityMarket) -> pd.DataFrame:
    """12-1 month cumulative specific return (days t-251..t-21), z-scored (momentum input)."""
    z = m.specific_returns / m.specific_vol
    return pd.DataFrame(_zscore_rows(z.rolling(231).sum().shift(21).to_numpy()), index=m.dates, columns=m.tickers)


def lob_imbalance_predictiveness(sim: LOBSimulation) -> tuple[float, int]:
    """corr(top-of-book imbalance now, sign-free size of the NEXT mid change); n changes."""
    mid = sim.quotes["mid"].to_numpy()
    imb = sim.quotes["imbalance"].to_numpy()
    ok = np.isfinite(mid)
    mid, imb = mid[ok], imb[ok]
    chg = np.flatnonzero(np.diff(mid) != 0)            # rows after which the mid changes
    nxt = np.empty(mid.size)
    nxt[:] = np.nan
    # for every row, the next mid change after it
    idx = np.searchsorted(chg, np.arange(mid.size))
    has = idx < chg.size
    nxt[has] = mid[chg[idx[has]] + 1] - mid[np.arange(mid.size)[has]]
    good = np.isfinite(nxt) & np.isfinite(imb) & (nxt != 0)
    return float(np.corrcoef(imb[good], np.sign(nxt[good]))[0, 1]), int(chg.size)


def lob_markouts(sim: LOBSimulation, horizon: float = 10.0) -> dict:
    """Average liquidity-provider markout (ticks per share) at ``horizon`` seconds, by taker type.

    LP markout of a trade = -side x (mid(t + horizon) - trade price): positive = the passive side
    made money (earned more spread than it lost to the subsequent price move).
    """
    q, tr = sim.quotes, sim.trades
    times = q["time"].to_numpy()
    mid = q["mid"].ffill().to_numpy()
    j = np.searchsorted(times, tr["time"].to_numpy() + horizon, side="right") - 1
    mo = -tr["side"].to_numpy() * (mid[j] - tr["price"].to_numpy()) / sim.cfg.tick
    w = tr["size"].to_numpy()
    out = {}
    for name, mask in (("informed", tr["informed"].to_numpy()), ("noise", ~tr["informed"].to_numpy())):
        out[name] = float(np.average(mo[mask], weights=w[mask])) if mask.any() else float("nan")
    out["all"] = float(np.average(mo, weights=w))
    return out


def tsmom_sharpe(fm: FuturesMarket, lookback: int = 252, vol_span: int = 60) -> float:
    """Gross Sharpe of a simple 12-month time-series-momentum portfolio (equal risk per asset)."""
    r = fm.returns
    sig = np.sign(r.rolling(lookback).sum())
    vol = r.ewm(span=vol_span).std()
    pos = (sig / vol).shift(1)
    pnl = (pos * r).mean(axis=1) * 0.01
    pnl = pnl.iloc[lookback + 1:]
    return float(pnl.mean() / pnl.std() * np.sqrt(252))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Synthetic market engine; see module docstring.")
    ap.add_argument("--selftest", action="store_true", help="run realism / calibration checks")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(_selftest())
    print(__doc__)
