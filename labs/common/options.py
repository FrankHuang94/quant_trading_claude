"""Option pricing helpers: Black-Scholes price/greeks/implied vol and a Heston pricer.

All functions are numpy-vectorized: pass scalars or arrays (they broadcast together).

Units and conventions
---------------------
* ``S`` spot, ``K`` strike, ``T`` time to expiry in **years**, ``r`` continuously compounded
  rate (decimal), ``sigma`` volatility (decimal, annualized: 0.20 = 20%). No dividends.
* ``call=True`` prices a call, ``False`` a put (may be a boolean array).
* Greeks from ``bs_greeks`` (per one unit of the underlying option):
    - ``delta``: dV/dS (call in [0, 1], put in [-1, 0]);
    - ``gamma``: d2V/dS2 (per $1 move, per $1);
    - ``vega``:  dV/dsigma per **1.00 of vol** (divide by 100 for "per vol point");
    - ``theta``: dV/dt per **year** of time passing, i.e. per unit of T (usually negative for a
      long option). Divide by the number of days per year in YOUR T convention: 365 if T counts
      calendar days, 252 if it counts trading days (``simulate_option_market`` uses 252).
* ``implied_vol`` returns NaN when the price is outside the no-arbitrage bounds
  (below intrinsic value or above the underlying/discounted strike), when T <= 0, or when the
  option has essentially no time value (vol not identifiable).
* ``heston_price``: Heston (1993) stochastic-volatility price via the Lewis (2001) single
  Fourier integral, using the Albrecher et al. (2007) "little trap" characteristic function
  and composite Gauss-Legendre panels whose range and width adapt to T, v0 and moneyness.
  Matches the Fang-Oosterlee (2008) reference value 5.785155450 to 2e-8 and adaptive
  quadrature to < 2e-5 (S = 100) over T from 1 day to 3 years, v0 from 0.0002 to 0.2, vol-of-vol
  up to 1.2. Vectorized over strikes, maturities, spots, rates and initial variances
  (~0.2 s for 9,000 options).

Example
-------
>>> round(float(bs_price(100, 100, 1.0, 0.0, 0.2)), 4)
7.9656
>>> round(float(implied_vol(7.965567, 100, 100, 1.0, 0.0)), 6)
0.2
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq
from scipy.special import ndtr

_SQRT_2PI = np.sqrt(2.0 * np.pi)


def _npdf(x: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * x * x) / _SQRT_2PI


def _d1d2(S, K, T, r, sigma):
    """d1, d2 of Black-Scholes; only valid where T > 0 and sigma > 0."""
    with np.errstate(divide="ignore", invalid="ignore"):
        sqT = np.sqrt(T)
        vsq = sigma * sqT
        d1 = (np.log(S / K) + (r + 0.5 * sigma * sigma) * T) / vsq
        d2 = d1 - vsq
    return d1, d2, sqT


def bs_price(S, K, T, r, sigma, call=True):
    """Black-Scholes price of a European call (``call=True``) or put. Vectorized.

    Edge cases: T <= 0 gives intrinsic value max(S-K, 0); sigma <= 0 gives the discounted
    forward intrinsic value max(S - K e^{-rT}, 0) (calls) / max(K e^{-rT} - S, 0) (puts).
    """
    S, K, T, r, sigma, call = np.broadcast_arrays(*(np.asarray(x, dtype=float) for x in (S, K, T, r, sigma)),
                                                  np.asarray(call, dtype=bool))
    disc = np.exp(-r * np.maximum(T, 0.0))
    d1, d2, _ = _d1d2(S, K, T, r, sigma)
    c = S * ndtr(d1) - K * disc * ndtr(d2)
    p = K * disc * ndtr(-d2) - S * ndtr(-d1)
    price = np.where(call, c, p)
    # degenerate cases
    fwd_intr = np.where(call, np.maximum(S - K * disc, 0.0), np.maximum(K * disc - S, 0.0))
    price = np.where(sigma <= 0, fwd_intr, price)
    spot_intr = np.where(call, np.maximum(S - K, 0.0), np.maximum(K - S, 0.0))
    price = np.where(T <= 0, spot_intr, price)
    return price[()] if price.ndim == 0 else price


def bs_greeks(S, K, T, r, sigma, call=True) -> dict:
    """Black-Scholes greeks: dict(delta, gamma, vega, theta). See module docstring for units.

    vega is per 1.00 of volatility; theta is per year. At T <= 0 or sigma <= 0 the greeks
    are those of the payoff (delta 0/1, others 0).
    """
    S, K, T, r, sigma, call = np.broadcast_arrays(*(np.asarray(x, dtype=float) for x in (S, K, T, r, sigma)),
                                                  np.asarray(call, dtype=bool))
    d1, d2, sqT = _d1d2(S, K, T, r, sigma)
    disc = np.exp(-r * np.maximum(T, 0.0))
    pdf = _npdf(d1)
    ok = (T > 0) & (sigma > 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        delta = np.where(call, ndtr(d1), ndtr(d1) - 1.0)
        gamma = pdf / (S * sigma * sqT)
        vega = S * pdf * sqT
        theta_common = -S * pdf * sigma / (2.0 * sqT)
        theta = np.where(call, theta_common - r * K * disc * ndtr(d2), theta_common + r * K * disc * ndtr(-d2))
    itm = np.where(call, S > K, S < K)
    delta = np.where(ok, delta, np.where(itm, np.where(call, 1.0, -1.0), 0.0))
    zero = np.zeros_like(S)
    out = {
        "delta": delta,
        "gamma": np.where(ok, gamma, zero),
        "vega": np.where(ok, vega, zero),
        "theta": np.where(ok, theta, zero),
    }
    return {k: (v[()] if v.ndim == 0 else v) for k, v in out.items()}


def implied_vol(price, S, K, T, r, call=True, tol: float = 1e-10, max_iter: int = 100,
                sigma_max: float = 10.0):
    """Black-Scholes implied volatility, vectorized and robust.

    Safeguarded Newton iterations inside a shrinking bisection bracket [1e-6, sigma_max]
    (all elements at once), then scipy's Brent root-finder for any element that has not
    converged. Returns NaN where the price is outside the no-arbitrage bounds, T <= 0, or the
    option's time value is below ~1e-12 x S (vol not identifiable).
    """
    price, S, K, T, r, call = np.broadcast_arrays(*(np.asarray(x, dtype=float) for x in (price, S, K, T, r)),
                                                  np.asarray(call, dtype=bool))
    shape = price.shape
    price, S, K, T, r, call = (a.ravel() for a in (price, S, K, T, r, call))
    out = np.full(price.shape, np.nan)
    disc = np.exp(-r * np.maximum(T, 0.0))
    lower = np.where(call, np.maximum(S - K * disc, 0.0), np.maximum(K * disc - S, 0.0))
    upper = np.where(call, S, K * disc)
    eps = 1e-12 * S
    valid = (T > 0) & np.isfinite(price) & (price > lower + eps) & (price < upper - eps)
    idx = np.flatnonzero(valid)
    if idx.size == 0:
        return out.reshape(shape)[()] if out.reshape(shape).ndim == 0 else out.reshape(shape)
    p, s, k, t, rr, c = price[idx], S[idx], K[idx], T[idx], r[idx], call[idx]
    # Invert the out-of-the-money twin instead of an in-the-money option (same implied vol by
    # put-call parity, but its price IS the time value, so there is no loss of precision).
    dk = k * np.exp(-rr * t)
    itm = np.where(c, s > dk, s < dk)
    p = np.where(itm, np.where(c, p - s + dk, p + s - dk), p)
    c = np.where(itm, ~c, c)
    lo = np.full(idx.size, 1e-6)
    hi = np.full(idx.size, sigma_max)
    # starting guess: Brenner-Subrahmanyam-style, clipped to a sane range
    sig = np.clip(np.sqrt(2.0 * np.abs(np.log(s / k) + rr * t) / t) + 0.1, 0.05, 2.0)
    active = np.ones(idx.size, dtype=bool)
    for _ in range(max_iter):
        a = np.flatnonzero(active)
        if a.size == 0:
            break
        sa = sig[a]
        pa = bs_price(s[a], k[a], t[a], rr[a], sa, c[a])
        diff = pa - p[a]
        vega = bs_greeks(s[a], k[a], t[a], rr[a], sa, c[a])["vega"]
        done = np.abs(diff) <= np.maximum(tol * p[a], 1e-14 * s[a])
        # keep the root bracketed: price is increasing in sigma
        hi[a] = np.where(diff > 0, sa, hi[a])
        lo[a] = np.where(diff <= 0, sa, lo[a])
        with np.errstate(divide="ignore", invalid="ignore"):
            newton = sa - diff / vega
        bad = ~np.isfinite(newton) | (newton <= lo[a]) | (newton >= hi[a])
        nxt = np.where(bad, 0.5 * (lo[a] + hi[a]), newton)
        done |= (hi[a] - lo[a]) < 1e-14
        sig[a] = np.where(done, sa, nxt)
        active[a[done]] = False
    res = sig.copy()
    # fallback: Brent on anything still unconverged
    for j in np.flatnonzero(active):
        f = lambda v, j=j: float(bs_price(s[j], k[j], t[j], rr[j], v, c[j])) - p[j]  # noqa: E731
        try:
            if f(1e-6) * f(sigma_max) < 0:
                res[j] = brentq(f, 1e-6, sigma_max, xtol=1e-12, maxiter=200)
            else:
                res[j] = np.nan
        except (ValueError, RuntimeError):
            res[j] = np.nan
    # a price above the sigma_max price (absurd) cannot be inverted
    res = np.where(res >= sigma_max * (1 - 1e-9), np.nan, res)
    out[idx] = res
    out = out.reshape(shape)
    return out[()] if out.ndim == 0 else out


# --------------------------------------------------------------------------- Heston
# The Fourier integral is evaluated with composite 32-node Gauss-Legendre panels: widths double
# from [0,1], [1,2], [2,4], ... (narrow panels resolve the peak near u = 0) up to a maximum width
# set by how fast the integrand oscillates (so every panel sees only a few cycles), then
# constant-width panels up to the truncation point U, chosen from a bound on the tail.
_GL32_X, _GL32_W = np.polynomial.legendre.leggauss(32)


def _fourier_grid(U: float, max_width: float) -> tuple[np.ndarray, np.ndarray]:
    """Nodes and weights of the composite rule on [0, >= U]."""
    edges, width = [0.0], 1.0
    while edges[-1] < U:
        edges.append(edges[-1] + width)          # panel widths 1, 2, 4, ... capped at max_width
        width = min(2.0 * width, max_width)
    e = np.asarray(edges)
    half, mid = 0.5 * np.diff(e), 0.5 * (e[1:] + e[:-1])
    u = (mid[:, None] + half[:, None] * _GL32_X[None, :]).ravel()
    w = (half[:, None] * _GL32_W[None, :]).ravel()
    return u, w


def heston_cf_coeffs(u, T, kappa, theta, xi, rho):
    """C(u, T), D(u, T) such that E[exp(i u X_T)] = exp(C + D v0), X_T = ln(S_T / F_T).

    Albrecher et al. (2007) "little Heston trap" form (no branch-cut problems). ``u`` may be
    complex; T is a scalar.
    """
    u = np.asarray(u, dtype=complex)
    iu = 1j * u
    b = kappa - rho * xi * iu
    d = np.sqrt(b * b + xi * xi * (iu + u * u))
    g = (b - d) / (b + d)
    edt = np.exp(-d * T)
    C = kappa * theta / (xi * xi) * ((b - d) * T - 2.0 * np.log((1.0 - g * edt) / (1.0 - g)))
    D = (b - d) / (xi * xi) * (1.0 - edt) / (1.0 - g * edt)
    return C, D


def _heston_grid(T, v0_min, v0_max, k_absmax, kappa, theta, xi, rho):
    """Truncation point and panel width for one maturity and a group of (v0, k) values."""
    # Integrand ~ exp(-a(u)) / u^2 with a(u) ~ min(vbar T u^2 / 2, c u): Gaussian (Black-Scholes
    # like) decay for small u, exponential decay for large u. Truncate where e^{-a(U)} / U < 1e-10.
    vbar = theta + (v0_min - theta) * (1.0 - np.exp(-kappa * T)) / (kappa * T)   # E[avg variance]
    vbar = max(vbar, 1e-6)
    c = np.sqrt(max(1.0 - rho * rho, 1e-4)) / xi * max(v0_min + kappa * theta * T, 1e-7)
    U = 16.0
    while min(vbar * T * U * U / 2.0, c * U) + np.log(U) < 23.0 and U < 2e5:
        U *= 1.2
    # oscillation frequency of e^{iuk} phi(u - i/2) in u: |k| plus the drift of arg(phi)
    freq = k_absmax + abs(rho) * (v0_max + kappa * theta * T) / xi + 1e-3
    max_width = float(np.clip(12.0 * np.pi / freq, 4.0, 4096.0))   # <= ~6 cycles per panel
    return U, max_width


def heston_price(S, K, T, r, v0, kappa, theta, xi, rho, call=True):
    """European option price under Heston (1993). Vectorized over S, K, T, r, v0 and ``call``.

    dS = r S dt + sqrt(v) S dW1,  dv = kappa (theta - v) dt + xi sqrt(v) dW2,  corr(dW1, dW2) = rho
    (risk-neutral parameters). Lewis (2001) formula:
        C = S - sqrt(S K) e^{-rT/2} / pi * Int_0^inf Re[e^{i u ln(F/K)} phi(u - i/2)] / (u^2 + 1/4) du
    evaluated on composite Gauss-Legendre panels over [0, U]. Puts via put-call parity.
    Elements are processed per maturity in chunks sorted by v0, each with its own grid.
    """
    arrs = np.broadcast_arrays(*(np.asarray(x, dtype=float) for x in (S, K, T, r, v0)),
                               np.asarray(call, dtype=bool))
    shape = arrs[0].shape
    S, K, T, r, v0, call = (a.ravel() for a in arrs)
    out = np.empty(S.shape)
    for Tu in np.unique(T):
        g = np.flatnonzero(T == Tu)
        if Tu <= 0:
            out[g] = np.where(call[g], np.maximum(S[g] - K[g], 0), np.maximum(K[g] - S[g], 0))
            continue
        g = g[np.argsort(v0[g], kind="stable")]
        for start in range(0, g.size, 1024):                   # chunks with similar v0
            gg = g[start:start + 1024]
            k = np.log(S[gg] / K[gg]) + r[gg] * Tu              # ln(F/K)
            U, width = _heston_grid(Tu, float(v0[gg].min()), float(v0[gg].max()),
                                    float(np.abs(k).max()), kappa, theta, xi, rho)
            u, w = _fourier_grid(U, width)
            w = w / (u * u + 0.25)
            C, D = heston_cf_coeffs(u - 0.5j, Tu, kappa, theta, xi, rho)
            integral = np.empty(gg.size)
            step = max(1, 4_000_000 // u.size)                 # bound the matrix size
            for s0 in range(0, gg.size, step):
                sl = slice(s0, s0 + step)
                expo = 1j * k[sl, None] * u[None, :] + C[None, :] + D[None, :] * v0[gg[sl], None]
                integral[sl] = np.real(np.exp(expo)) @ w
            c = S[gg] - np.sqrt(S[gg] * K[gg]) * np.exp(-0.5 * r[gg] * Tu) / np.pi * integral
            disc_k = K[gg] * np.exp(-r[gg] * Tu)
            c = np.clip(c, np.maximum(S[gg] - disc_k, 0.0), S[gg])   # remove tiny quadrature noise
            out[gg] = np.where(call[gg], c, c - S[gg] + disc_k)
    out = out.reshape(shape)
    return out[()] if out.ndim == 0 else out


def heston_price_reference(S, K, T, r, v0, kappa, theta, xi, rho, call=True) -> float:
    """Slow scalar reference: same Lewis integral with scipy's adaptive quad (for testing)."""
    from scipy.integrate import quad

    k = np.log(S / K) + r * T

    def f(u):
        C, D = heston_cf_coeffs(u - 0.5j, T, kappa, theta, xi, rho)
        return float(np.real(np.exp(1j * u * k + C + D * v0))) / (u * u + 0.25)

    integral, _ = quad(f, 0.0, np.inf, limit=500, epsabs=1e-12, epsrel=1e-12)
    c = S - np.sqrt(S * K) * np.exp(-0.5 * r * T) / np.pi * integral
    return float(c if call else c - S + K * np.exp(-r * T))


if __name__ == "__main__":
    import doctest

    print(doctest.testmod())
