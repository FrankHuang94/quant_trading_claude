"""Lab 17: VWAP, TWAP, POV and a close-heavy schedule on simulated trading days.

What it demonstrates
  * A buy order for 10% of ADV (500,000 shares of a $50 stock, $25M) executed over one day with
      - TWAP: equal slices every minute of the continuous session;
      - VWAP: slices in proportion to a historical (20-day average) volume curve that includes the
        closing auction;
      - POV 10%: each minute, buy enough to keep our share of printed volume at 10% (reacting to
        volume already seen), plus 10% of the indicated closing-auction volume;
      - Close-heavy ("target close"): 30% of the order in the closing auction, the rest along the
        volume curve from 14:00.
  * A simple stylized cost model: half-spread + temporary impact ~ participation^0.6 + permanent
    impact linear in shares already bought. The closing auction has no spread, but our demand moves
    the closing price itself.
  * Implementation shortfall vs the arrival price (Perold 1988), decomposed into spread, temporary
    impact, permanent impact, market drift (timing) and opportunity cost of unfilled shares; plus
    slippage vs interval VWAP and vs the close, over hundreds of simulated days.
  * Pitfalls: (1) a day's result is dominated by price drift, not by the algorithm (schedule risk);
    (2) the VWAP benchmark moves with you, so it hides your own impact; (3) POV does not guarantee
    completion: on a low-volume day it leaves shares unfilled; (4) the "best" algorithm depends on
    the benchmark you are measured against.

Supports: docs/03-algorithms/e-execution-algorithms/vwap-twap-pov.md,
          docs/03-algorithms/e-execution-algorithms/execution-algorithms-overview.md

Run: python labs/17-vwap-twap-pov/lab.py [--smoke] [--seed N]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_var, "1")   # small arrays: avoid BLAS thread oversubscription

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common import simulate, utils  # noqa: E402


# =====================================================================================
# === CORE ALGORITHM ===
# Time is split into bins: 390 one-minute bins of the continuous session + 1 closing-auction bin.
# Costs for a BUY, in bps of the price, per child order of q shares in a bin where the rest of
# the market trades v shares (stylized; functional form after Almgren et al. 2005):
#   spread    = half the quoted spread (we cross it; the auction has no spread)
#   temporary = eta * daily_vol * (q / v) ** 0.6   (q / v = our shares per share traded by
#               others in the bin; paid on this child order only)
#   permanent = gamma * daily_vol * (shares bought so far / ADV)  (shifts all later prices)
# =====================================================================================

def vwap_schedule(volume_curve, qty):
    """Shares per bin proportional to the forecast volume curve (integers summing to qty).

    volume_curve: expected share of the day's volume in each bin (any positive scale).
    TWAP is the special case of a flat curve. Rounding the cumulative target keeps the total exact.
    """
    w = np.asarray(volume_curve, dtype=float)
    cum_target = np.round(qty * np.cumsum(w) / w.sum())
    return np.diff(np.concatenate([[0.0], cum_target]))


def pov_child_order(target_rate, market_volume_so_far, executed_so_far, remaining):
    """Shares to buy now so that our share of total volume tracks target_rate.

    We want ours / (others + ours) = rate, i.e. ours = rate / (1 - rate) * others. Only volume
    already printed by others is used (no look-ahead), so POV lags volume by one bin and cannot
    promise to finish: it buys what the market lets it.
    """
    target = target_rate / (1.0 - target_rate) * market_volume_so_far
    return float(np.clip(target - executed_so_far, 0.0, remaining))


def child_order_costs_bps(qty, market_volume, half_spread_bps, bought_before, adv, daily_vol,
                          eta=0.15, gamma=0.30, exponent=0.6):
    """Spread, temporary and permanent impact (bps) for child orders in each bin (arrays)."""
    participation = np.divide(qty, market_volume, out=np.zeros_like(qty, dtype=float),
                              where=market_volume > 0)
    temporary = 1e4 * eta * daily_vol * participation ** exponent
    permanent = 1e4 * gamma * daily_vol * bought_before / adv
    spread = np.where(qty > 0, half_spread_bps, 0.0)
    return spread, temporary, permanent


# === END CORE ALGORITHM ===
# =====================================================================================


def simulate_days(seeds, cfg_kw):
    """Simulate sessions; return arrays (days x 391) of others' volume and exogenous prices."""
    vols, prices, half_spreads, opens = [], [], [], []
    for s in seeds:
        b = simulate.simulate_intraday_session(seed=int(s), **cfg_kw)
        vols.append(np.r_[b["volume"].to_numpy(), b.attrs["close_auction_volume"]])
        prices.append(np.r_[b["vwap"].to_numpy(), b.attrs["close_price"]])   # avg price in bin; close
        half_spreads.append(np.r_[b["spread_bps"].to_numpy() / 2, 0.0])     # no spread in the auction
        opens.append(b.attrs["open_price"])
    return np.array(vols), np.array(prices), np.array(half_spreads), np.array(opens)


def execute(q, vol, px, hs, arrival, order_qty, adv, daily_vol, eta, gamma):
    """Fill child orders q (391 bins, last = auction) and measure costs vs benchmarks (buy order).

    Returns a dict of bps figures (+ = cost) relative to the arrival-price notional of the order.
    """
    bought_before = np.concatenate([[0.0], np.cumsum(q)[:-1]])
    spread, temp, perm = child_order_costs_bps(q, vol, hs, bought_before, adv, daily_vol, eta, gamma)
    mkt_px = px * (1 + perm / 1e4)                         # market prices shifted by our permanent impact
    mkt_px[-1] = px[-1] * (1 + (perm[-1] + temp[-1]) / 1e4)  # our auction demand moves the close itself
    fill_px = mkt_px * (1 + (spread + np.where(np.arange(len(q)) < len(q) - 1, temp, 0.0)) / 1e4)
    filled = q.sum()
    notional = order_qty * arrival
    to_bps = 1e4 / notional
    close = mkt_px[-1]
    # Perold implementation shortfall = execution cost of filled shares + opportunity cost
    parts = {
        "spread": (q * mkt_px * spread / 1e4).sum() * to_bps,
        "temporary": ((q * mkt_px * temp / 1e4)[:-1].sum() + q[-1] * px[-1] * temp[-1] / 1e4) * to_bps,
        "permanent": (q * px * perm / 1e4).sum() * to_bps,
        "timing": (q * (px - arrival)).sum() * to_bps,
        "opportunity": (order_qty - filled) * (close - arrival) * to_bps,
    }
    shortfall = ((q * (fill_px - arrival)).sum() + (order_qty - filled) * (close - arrival)) * to_bps
    assert abs(shortfall - sum(parts.values())) < 1e-6
    avg_px = (q * fill_px).sum() / filled
    active = np.flatnonzero(q > 0)
    sl = slice(active[0], active[-1] + 1)                  # interval from first to last fill
    cont = slice(sl.start, min(sl.stop, len(q) - 1))       # its continuous-session part
    interval_vwap = ((vol[sl] * mkt_px[sl]).sum() + (q[sl] * fill_px[sl]).sum()) / (vol[sl] + q[sl]).sum()
    return dict(shortfall=shortfall, **parts,
                vs_vwap=1e4 * (avg_px / interval_vwap - 1), vs_close=1e4 * (avg_px / close - 1),
                completion=filled / order_qty,
                participation=q[cont].sum() / (q[cont] + vol[cont]).sum())


def main():
    ctx = utils.setup(__file__, "Lab 17: VWAP, TWAP, POV and the closing auction")
    n_hist, n_test = (5, 40) if ctx.smoke else (20, 500)
    cfg_kw = dict(adv_shares=5e6, price=50.0, daily_vol=0.02, spread_bps=3.0, close_auction_share=0.10)
    adv, daily_vol = cfg_kw["adv_shares"], cfg_kw["daily_vol"]
    order_qty = 0.10 * adv                       # buy 10% of ADV
    pov_rate = 0.10
    close_share, close_start = 0.30, 270         # close-heavy: 30% in the auction, rest from 14:00
    eta, gamma = 0.15, 0.30                      # stylized impact coefficients (see README)
    n_bins = 390

    seeds = np.random.SeedSequence(ctx.seed).generate_state(n_hist + n_test)
    vol_h, _, _, _ = simulate_days(seeds[:n_hist], cfg_kw)
    vols, prices, hss, opens = simulate_days(seeds[n_hist:], cfg_kw)
    hist_curve = (vol_h / vol_h.sum(axis=1, keepdims=True)).mean(axis=0)   # 391 bins incl. auction

    twap_q = vwap_schedule(np.r_[np.ones(n_bins), 0.0], order_qty)
    vwap_q = vwap_schedule(hist_curve, order_qty)
    late_curve = hist_curve.copy()
    late_curve[:close_start] = 0.0
    late_curve[-1] = 0.0
    close_q = vwap_schedule(late_curve, (1 - close_share) * order_qty)
    close_q[-1] = order_qty - close_q.sum()

    def pov_q(vol):
        q = np.zeros(n_bins + 1)
        done = 0.0
        for t in range(n_bins + 1):
            # continuous bins see others' volume printed before this minute; for the auction we use
            # the published indicative auction volume (assumed accurate) plus the whole session
            seen = vol[:t].sum() if t < n_bins else vol.sum()
            q[t] = np.floor(pov_child_order(pov_rate, seen, done, order_qty - done))
            done += q[t]
        return q

    names = ["TWAP", "VWAP (20-day curve)", "POV 10%", "Close-heavy (30% auction)"]
    runs = {k: [] for k in names + ["VWAP (perfect foresight)"]}
    pov_all = []
    for d in range(n_test):
        vol, px, hs, arrival = vols[d], prices[d], hss[d], opens[d]
        perfect_q = vwap_schedule(vol, order_qty)
        pq = pov_q(vol)
        pov_all.append(pq)
        for name, q in zip(names + ["VWAP (perfect foresight)"], [twap_q, vwap_q, pq, close_q, perfect_q]):
            runs[name].append(execute(q, vol, px, hs, arrival, order_qty, adv, daily_vol, eta, gamma))
    stats = {}
    for name, rows in runs.items():
        arr = {k: np.array([r[k] for r in rows]) for k in rows[0]}
        stats[name] = {
            "is_mean": arr["shortfall"].mean(), "is_sd": arr["shortfall"].std(ddof=1),
            "is_p95": np.percentile(arr["shortfall"], 95),
            **{f"is_{k}": arr[k].mean() for k in ("spread", "temporary", "permanent", "timing", "opportunity")},
            "is_timing_se": arr["timing"].std(ddof=1) / np.sqrt(len(rows)),
            "expected_cost": arr["spread"].mean() + arr["temporary"].mean() + arr["permanent"].mean()
            + arr["opportunity"].mean(),
            "vwap_mean": arr["vs_vwap"].mean(), "vwap_sd": arr["vs_vwap"].std(ddof=1),
            "close_mean": arr["vs_close"].mean(), "close_sd": arr["vs_close"].std(ddof=1),
            "completion_mean": arr["completion"].mean(),
            "pct_days_complete": 100 * np.mean(arr["completion"] >= 0.999),
            "participation_mean": arr["participation"].mean(),
            "_is": arr["shortfall"], "_vwap": arr["vs_vwap"], "_completion": arr["completion"],
        }
    day_volume = vols.sum(axis=1)
    pov_c = stats["POV 10%"]["_completion"]
    low_day = day_volume < np.median(day_volume)

    # ---------------------------------------------------------------- plot 1: schedules
    colors = {names[0]: "#2a78d6", names[1]: "#eb6834", names[2]: "#1baf7a", names[3]: "#6250d6"}
    x = np.r_[np.arange(1, n_bins + 1), n_bins + 6]          # minute index; auction drawn at 16:00+
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1.3, 1]})
    v0 = vols[0]
    ax1.fill_between(x, 100 * np.cumsum(v0) / v0.sum(), step="post", color="0.85",
                     label="market volume (cumulative % of day)")
    for name, q in zip(names, [twap_q, vwap_q, pov_all[0], close_q]):
        ax1.step(x, 100 * np.cumsum(q) / order_qty, where="post", color=colors[name], lw=2, label=name)
    ax1.axvline(n_bins, color="0.4", ls=":", lw=1)
    ax1.text(n_bins - 4, 4, "closing\nauction", ha="right", fontsize=8, color="0.3")
    ticks = [0, 90, 180, 270, 390]
    ax1.set_xticks(ticks, ["9:30", "11:00", "12:30", "14:00", "16:00"])
    ax1.set_xlabel("time of day")
    ax1.set_ylabel("cumulative % of order (or of day volume)")
    ax1.set_title("Execution schedules, one simulated day", fontsize=11)
    ax1.legend(fontsize=8, loc="upper left")
    ax1.set_ylim(0, 103)
    # participation by half-hour bucket, averaged over days, plus the auction
    edges = np.arange(0, n_bins + 1, 30)
    labels = [f"{9 + (30 + e) // 60}:{(30 + e) % 60:02d}" for e in edges[:-1]] + ["auction"]
    for name in names:
        part = []
        for d in range(n_test):
            q = {names[0]: twap_q, names[1]: vwap_q, names[2]: pov_all[d], names[3]: close_q}[name]
            ours = np.r_[[q[a:b].sum() for a, b in zip(edges[:-1], edges[1:])], q[-1]]
            theirs = np.r_[[vols[d][a:b].sum() for a, b in zip(edges[:-1], edges[1:])], vols[d][-1]]
            part.append(ours / (ours + theirs))
        avg = 100 * np.mean(part, axis=0)
        n_cont = len(labels) - 1
        ax2.plot(np.arange(n_cont), avg[:-1], "-o", color=colors[name], ms=4, lw=1.8, label=name)
        ax2.plot(n_cont + 0.6, avg[-1], "s", color=colors[name], ms=8, mec="white")   # the auction
    ax2.axvline(len(labels) - 1.2, color="0.4", ls=":", lw=1)
    ax2.set_xticks(list(np.arange(0, len(labels) - 1, 2)) + [len(labels) - 0.4],
                   labels[:-1:2] + ["close\nauction"], fontsize=8)
    ax2.set_xlabel("half-hour bucket (start time)")
    ax2.set_ylabel("our share of traded volume (%)")
    ax2.set_title("Participation rate, average over simulated days", fontsize=11)
    ax2.set_ylim(bottom=0)
    fig.suptitle(f"Buying 10% of ADV ({order_qty:,.0f} shares of a $50 stock) in one day (synthetic data)",
                 fontweight="bold")
    fig.subplots_adjust(top=0.86, wspace=0.22)
    utils.save_fig(ctx, fig, "schedules")

    # ---------------------------------------------------------------- plot 2: slippage distributions
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), gridspec_kw={"width_ratios": [1, 1, 1.1]})
    for ax, key, title, xlab in ((axes[0], "_is", "vs arrival price (implementation shortfall)",
                                  "bps of order notional (+ = cost)"),
                                 (axes[1], "_vwap", "vs interval VWAP", "bps (+ = paid above VWAP)")):
        data = [stats[n][key] for n in names][::-1]
        bp = ax.boxplot(data, vert=False, widths=0.6, showfliers=False, patch_artist=True,
                        medianprops=dict(color="k"), whis=(5, 95))
        for patch, n in zip(bp["boxes"], names[::-1]):
            patch.set_facecolor(colors[n])
            patch.set_alpha(0.55)
        ax.plot([d.mean() for d in data], np.arange(1, len(data) + 1), "D", color="k", ms=5, label="mean")
        ax.axvline(0, color="0.4", lw=0.8)
        ax.set_yticks(np.arange(1, len(data) + 1), [n.replace(" (", "\n(") for n in names[::-1]], fontsize=8.5)
        ax.set_title(title, fontsize=10.5)
        ax.set_xlabel(xlab)
    axes[0].legend(fontsize=8, loc="lower right")
    axes[1].set_yticklabels([])
    comp = ["spread", "temporary", "permanent", "opportunity"]
    comp_colors = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
    left = np.zeros(len(names))
    for c, col in zip(comp, comp_colors):
        vals = np.array([stats[n][f"is_{c}"] for n in names[::-1]])
        axes[2].barh(np.arange(len(names)), vals, left=left, color=col, height=0.6,
                     label=f"{c} impact" if c in ("temporary", "permanent") else c)
        left += vals
    for i, n in enumerate(names[::-1]):
        axes[2].text(left[i] + 0.3, i, f"{left[i]:.1f}\n(drift {stats[n]['is_timing']:+.1f}"
                     f" +/- {stats[n]['is_timing_se']:.1f})", va="center", fontsize=7.5)
    axes[2].set_yticks(np.arange(len(names)), [])
    axes[2].set_xlim(0, 1.45 * left.max())
    axes[2].set_xlabel("mean cost, bps of order notional")
    axes[2].set_title("Mean cost excluding market drift", fontsize=10.5)
    axes[2].legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=4, frameon=False)
    fig.suptitle(f"Slippage over {n_test} simulated days, buy 10% of ADV (boxes: 25-75%, whiskers 5-95%; "
                 "synthetic data)", fontweight="bold")
    fig.subplots_adjust(top=0.85, wspace=0.08)
    utils.save_fig(ctx, fig, "slippage")

    # ---------------------------------------------------------------- results
    short = {names[0]: "twap", names[1]: "vwap", names[2]: "pov10", names[3]: "close_heavy",
             "VWAP (perfect foresight)": "vwap_perfect_curve"}
    res = {"order_pct_adv": 100 * order_qty / adv, "order_usd": order_qty * cfg_kw["price"],
           "n_test_days": n_test, "close_auction_share": cfg_kw["close_auction_share"]}
    for name, s in stats.items():
        res[short[name]] = {k: v for k, v in s.items() if not k.startswith("_")}
    res["pov10_completion_low_volume_days"] = float(pov_c[low_day].mean())
    res["pov10_completion_high_volume_days"] = float(pov_c[~low_day].mean())
    res["day_volume_cv"] = float(day_volume.std() / day_volume.mean())
    # how many orders would an unpaired comparison (e.g. two brokers) need to tell VWAP from TWAP?
    tw, vw = stats[names[0]], stats[names[1]]
    gap = tw["expected_cost"] - vw["expected_cost"]
    res["vwap_minus_twap_expected_cost_bps"] = -gap
    res["orders_needed_to_detect_twap_vs_vwap_gap_2se"] = float((2 * np.hypot(tw["is_sd"], vw["is_sd"]) / gap) ** 2)
    utils.write_results(ctx, res)

    print(f"\nBuy {order_qty:,.0f} shares (10% of ADV, ${order_qty * 50 / 1e6:.0f}M), {n_test} simulated days")
    print(f"{'strategy':<27}{'IS mean':>8}{'IS sd':>7}{'spread':>7}{'temp':>6}{'perm':>6}{'opp':>6}"
          f"{'vsVWAP':>8}{'VWAP sd':>8}{'vsClose':>8}{'done%':>7}{'part%':>7}")
    for name, s in stats.items():
        print(f"{name:<27}{s['is_mean']:>8.1f}{s['is_sd']:>7.1f}{s['is_spread']:>7.1f}{s['is_temporary']:>6.1f}"
              f"{s['is_permanent']:>6.1f}{s['is_opportunity']:>6.1f}{s['vwap_mean']:>8.1f}{s['vwap_sd']:>8.1f}"
              f"{s['close_mean']:>8.1f}{100 * s['completion_mean']:>7.1f}{100 * s['participation_mean']:>7.1f}")
    print(f"POV 10% completes the order on {stats['POV 10%']['pct_days_complete']:.0f}% of days "
          f"(mean fill {100 * pov_c[low_day].mean():.0f}% on below-median-volume days)")
    print("Expected cost (spread + impact + opportunity, excluding drift): "
          + ", ".join(f"{k} {s['expected_cost']:.1f}" for k, s in stats.items()))
    print(f"Orders needed to separate TWAP from VWAP by realized shortfall (2 s.e., unpaired): "
          f"{res['orders_needed_to_detect_twap_vs_vwap_gap_2se']:,.0f}")


if __name__ == "__main__":
    main()
