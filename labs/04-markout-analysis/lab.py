"""Lab 04: markout analysis -- how much of the spread a liquidity provider keeps, by segment.

What it demonstrates
  * Markouts of passive fills: for every fill of a resting (liquidity-providing) order, the mid
    h seconds later minus the fill price, signed from the passive side and expressed in basis
    points. At h = 0 (the mid just before the trade) it is the spread captured; the drop from
    there is the adverse selection (the price moving against the liquidity provider).
  * The classic picture on every passive fill of three simulated days (~140,000 fills): spread
    captured at t = 0, then a decay that turns negative for informed ("toxic") flow and stays
    positive for uninformed flow.
  * Segments a desk can actually observe: the taker's order size and the spread when the order
    arrived. The simulator's informed flag is the planted truth: the lab reports the informed
    share of each segment to show why its markout curve looks the way it does.
  * An income statement for the liquidity providers: spread captured minus adverse selection.
  * Pitfalls: (1) too short a horizon makes toxic flow look profitable; (2) naive standard errors
    treat overlapping fills as independent and understate uncertainty at long horizons; (3)
    averaging per fill instead of per share understates toxicity (big orders are more informed).

Data: labs/common/simulate.py `simulate_lob` (synthetic $50 stock, 1-cent tick = 2 bps).

Supports: docs/03-algorithms/f-market-making-and-hft-algorithms/adverse-selection-and-markouts.md,
          docs/02-strategies/a-liquidity-provision/equity-market-making.md
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import simulate, utils  # noqa: E402

HORIZONS_S = [0, 1, 2, 5, 10, 30, 60, 120, 300]   # 0 = the mid just before the fill
BLOCK_S = 600                                      # time blocks for clustered standard errors
SIZE_BUCKETS = [("100 sh", 100, 100), ("200-300 sh", 200, 300), ("400-700 sh", 400, 700), ("800+ sh", 800, np.inf)]
SPREAD_BUCKETS = [("1 tick", 1, 1), ("2 ticks", 2, 2), ("3+ ticks", 3, np.inf)]
COLORS = {"informed": "#eb6834", "uninformed (noise)": "#2a78d6", "all fills": "#52514e"}
RAMP_4 = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]   # ordinal: small -> large orders
RAMP_3 = ["#6da7ec", "#256abf", "#0d366b"]              # ordinal: tight -> wide spread


# =====================================================================================
# === CORE ALGORITHM ===
# Markout of a passive fill at horizon h, in bps (positive = the passive side made money):
#     markout_h = side * (mid(t_fill + h) - fill_price) / fill_price * 1e4
# side = +1 if we bought (our bid was hit), -1 if we sold (our offer was lifted).
# =====================================================================================

def markouts(fills, mid_series, horizons=HORIZONS_S):
    """Markout of every fill at every horizon, in basis points.

    fills: DataFrame with columns time (s), price, side (+1 passive buy, -1 passive sell).
    mid_series: pd.Series of mid prices indexed by time (s), sorted, one value per book update.
    horizons: seconds after the fill. h = 0 uses the mid just BEFORE the fill, so markout_0 is
              the spread captured (half-spread, plus more if the order walked the book).
    Returns a DataFrame (one row per fill, one column per horizon).
    """
    t_book = mid_series.index.to_numpy()
    mid = mid_series.ffill().to_numpy()
    t_fill, price, side = (fills[c].to_numpy() for c in ("time", "price", "side"))
    out = {}
    for h in horizons:
        if h == 0:
            j = np.searchsorted(t_book, t_fill, side="left") - 1      # last mid strictly before
        else:
            j = np.searchsorted(t_book, t_fill + h, side="right") - 1  # last mid at or before t+h
        out[h] = side * (mid[j] - price) / price * 1e4
    return pd.DataFrame(out, index=fills.index)


def markout_curve(mo, weights, blocks):
    """Share-weighted average markout per horizon with a block-clustered standard error.

    Fills close in time share the same future price path, so they are not independent. The
    standard error treats each time block (e.g. 10 minutes) as one observation.
    Returns (mean, se) as Series indexed by horizon.
    """
    w = np.asarray(weights, float)
    mean = (mo.mul(w, axis=0).sum() / w.sum())
    resid = (mo - mean).mul(w, axis=0)                      # weighted deviations
    by_block = resid.groupby(np.asarray(blocks)).sum()       # sum within each time block
    se = np.sqrt((by_block**2).sum()) / w.sum()              # cluster-robust (ratio estimator)
    return mean, se


# === END CORE ALGORITHM ===
# =====================================================================================


def passive_fills(sim, day, max_h):
    """Every fill from the passive (maker) side, with the segments a desk would look at."""
    tr, q, ev = sim.trades, sim.quotes, sim.events
    idx = tr["event_idx"].to_numpy()
    fills = pd.DataFrame({
        "time": tr["time"].to_numpy(), "price": tr["price"].to_numpy(),
        "side": -tr["side"].to_numpy(),                         # maker is the opposite of the taker
        "size": tr["size"].to_numpy(), "informed": tr["informed"].to_numpy(),
        "taker_order_size": ev["size"].to_numpy()[idx],         # the whole market order
        "spread_ticks_before": np.rint(q["spread"].to_numpy()[idx - 1] / sim.cfg.tick),
        "day": day})
    fills["block"] = day * 1000 + (fills["time"] // BLOCK_S).astype(int)
    return fills[fills["time"] <= sim.cfg.n_seconds - max_h].reset_index(drop=True)


def bucket(values, buckets):
    out = np.full(len(values), "", dtype=object)
    for name, lo, hi in buckets:
        out[(values >= lo) & (values <= hi)] = name
    return out


def main() -> None:
    ctx = utils.setup(__file__, "Lab 04: markout analysis")
    n_days = 1 if ctx.smoke else 3
    n_seconds = 3600 if ctx.smoke else 23400
    print("Lab 04: markouts of passive fills, by counterparty, order size and spread")
    print(f"  simulating {n_days} day(s) of {n_seconds:,} s ...")
    all_fills, all_mo = [], []
    for d in range(n_days):
        sim = simulate.simulate_lob(n_seconds=n_seconds, seed=ctx.seed + d)
        fills = passive_fills(sim, d, max(HORIZONS_S))
        mid_series = pd.Series(sim.quotes["mid"].to_numpy(), index=sim.quotes["time"].to_numpy())
        all_fills.append(fills)
        all_mo.append(markouts(fills, mid_series, HORIZONS_S))
    fills = pd.concat(all_fills, ignore_index=True)
    mo = pd.concat(all_mo, ignore_index=True)
    w, blocks = fills["size"].to_numpy(), fills["block"].to_numpy()
    fills["size_bucket"] = bucket(fills["taker_order_size"].to_numpy(), SIZE_BUCKETS)
    fills["spread_bucket"] = bucket(fills["spread_ticks_before"].to_numpy(), SPREAD_BUCKETS)
    print(f"  {len(fills):,} passive fills, {w.sum():,.0f} shares; informed share of volume "
          f"{w[fills['informed']].sum() / w.sum():.0%}; mean fill price ${fills['price'].mean():.2f} (1 tick = "
          f"{1e4 * 0.01 / fills['price'].mean():.1f} bps)")

    def curve(mask):
        m, s = markout_curve(mo[mask], w[mask], blocks[mask])
        return m, s

    segments = {}
    for name, mask in (("all fills", np.ones(len(fills), bool)), ("informed", fills["informed"].to_numpy()),
                       ("uninformed (noise)", ~fills["informed"].to_numpy())):
        segments[("counterparty", name)] = (mask, *curve(mask))
    for col, buckets in (("size_bucket", SIZE_BUCKETS), ("spread_bucket", SPREAD_BUCKETS)):
        for name, _, _ in buckets:
            mask = (fills[col] == name).to_numpy()
            segments[(col, name)] = (mask, *curve(mask))

    rows = []
    for (group, name), (mask, m, s) in segments.items():
        rows.append({"group": group, "segment": name, "volume_share": w[mask].sum() / w.sum(),
                     "informed_share_truth": w[mask & fills["informed"].to_numpy()].sum() / w[mask].sum(),
                     **{f"markout_{h}s_bps": m[h] for h in HORIZONS_S}, **{f"se_{h}s_bps": s[h] for h in HORIZONS_S}})
    table = pd.DataFrame(rows)
    show = table[["group", "segment", "volume_share", "informed_share_truth", "markout_0s_bps", "markout_1s_bps",
                  "markout_10s_bps", "markout_60s_bps", "markout_300s_bps", "se_60s_bps"]]
    print("\n  Share-weighted markouts, bps (positive = the liquidity provider made money):")
    print(show.round(2).to_string(index=False))

    # ---- income statement for the liquidity providers (all passive fills), $ per day
    notional = (fills["price"] * fills["size"]).to_numpy()
    usd = {h: float((notional * mo[h].to_numpy()).sum() / 1e4 / n_days) for h in HORIZONS_S}
    income = {"spread_captured_usd_per_day": usd[0],
              "adverse_selection_10s_usd_per_day": usd[10] - usd[0],
              "adverse_selection_60s_usd_per_day": usd[60] - usd[0],
              "net_after_60s_usd_per_day": usd[60],
              "share_of_spread_kept_at_60s": usd[60] / usd[0]}
    inf = fills["informed"].to_numpy()
    by_cp = {name: {"spread_captured_usd_per_day": float((notional[m] * mo[0].to_numpy()[m]).sum() / 1e4 / n_days),
                    "net_after_60s_usd_per_day": float((notional[m] * mo[60].to_numpy()[m]).sum() / 1e4 / n_days)}
             for name, m in (("informed", inf), ("uninformed", ~inf))}
    print(f"\n  Liquidity providers' income statement, $ per day: spread captured {usd[0]:+,.0f}; adverse selection "
          f"(60 s) {usd[60] - usd[0]:+,.0f}; net {usd[60]:+,.0f} ({usd[60] / usd[0]:.0%} of the spread kept)")
    print("  by counterparty: " + "; ".join(f"{k}: captured {v['spread_captured_usd_per_day']:+,.0f}, net "
                                            f"{v['net_after_60s_usd_per_day']:+,.0f}" for k, v in by_cp.items()))

    # ---- pitfalls
    mi = segments[("counterparty", "informed")][1]
    first_negative = next((h for h in HORIZONS_S if mi[h] < 0), None)
    naive_se = {h: float(np.sqrt(np.average((mo[h] - segments[("counterparty", "all fills")][1][h]) ** 2, weights=w)
                                 / (w.sum() ** 2 / (w**2).sum()))) for h in (10, 300)}
    block_se = {h: float(segments[("counterparty", "all fills")][2][h]) for h in (10, 300)}
    per_fill = mo.mean()                                      # each fill counts once, whatever its size
    per_share = segments[("counterparty", "all fills")][1]
    print(f"\n  Pitfall, horizon: informed flow shows {mi[1]:+.2f} bps at 1 s (looks profitable); first negative at {first_negative} s")
    print(f"  Pitfall, standard errors (all fills): naive {naive_se[10]:.3f} / {naive_se[300]:.3f} bps vs block-clustered "
          f"{block_se[10]:.3f} / {block_se[300]:.3f} bps at 10 s / 300 s")
    print(f"  Pitfall, weighting: markout at 60 s per fill {per_fill[60]:+.2f} bps vs per share {per_share[60]:+.2f} bps")

    # ---------------------------------------------------------------- plots
    x = np.array(HORIZONS_S, float)

    def setup_axis(ax):
        ax.set_xscale("symlog", linthresh=1)
        ax.set_xticks(x, [str(h) for h in HORIZONS_S])
        ax.set_xlim(-0.1, 330)
        ax.axhline(0, color="0.3", lw=0.8)
        ax.set_xlabel("Seconds after the fill (0 = mid just before the trade)")

    fig, ax = plt.subplots(figsize=(9, 5))
    for name, marker in (("informed", "s"), ("uninformed (noise)", "o"), ("all fills", "D")):
        _, m, s = segments[("counterparty", name)]
        share = table.loc[(table.group == "counterparty") & (table.segment == name), "volume_share"].iloc[0]
        ax.fill_between(x, m - 2 * s, m + 2 * s, color=COLORS[name], alpha=0.15, lw=0)
        ax.plot(x, m, marker=marker, ms=7, lw=2, color=COLORS[name], label=f"{name} ({share:.0%} of volume)")
        ax.annotate(name, (x[-1], m.iloc[-1]), xytext=(6, 0), textcoords="offset points", va="center",
                    fontsize=9, color="0.2")
    setup_axis(ax)
    ax.set_xlim(-0.1, 700)
    ax.annotate("spread captured", (0, segments[("counterparty", "informed")][1][0]), xytext=(12, 8),
                textcoords="offset points", fontsize=9, color="0.2")
    ax.set_ylabel("Markout, bps (1 tick = 2 bps; + = liquidity provider gains)")
    ax.set_title("Lab 04: markouts of passive fills by counterparty (synthetic data)")
    ax.legend(loc="lower left", fontsize=9)
    fig.text(0.5, -0.03, f"{len(fills):,} passive fills over {n_days} simulated days of a $50 stock; share-weighted means "
             "with +/-2 block-clustered standard errors (10-minute blocks).", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "markouts-by-counterparty")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
    for ax, group, buckets, ramp, title in ((axes[0], "size_bucket", SIZE_BUCKETS, RAMP_4, "By taker order size"),
                                            (axes[1], "spread_bucket", SPREAD_BUCKETS, RAMP_3, "By spread before the trade")):
        for (name, _, _), color in zip(buckets, ramp):
            _, m, s = segments[(group, name)]
            row = table[(table.group == group) & (table.segment == name)].iloc[0]
            ax.fill_between(x, m - 2 * s, m + 2 * s, color=color, alpha=0.12, lw=0)
            ax.plot(x, m, marker="o", ms=6, lw=2, color=color,
                    label=f"{name}: {row.volume_share:.0%} of volume, {row.informed_share_truth:.0%} informed")
        setup_axis(ax)
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
    axes[0].set_ylabel("Markout, bps (+ = liquidity provider gains)")
    fig.suptitle("Lab 04: markouts by observable segment (synthetic data)", fontweight="bold")
    fig.text(0.5, -0.03, "Informed share = the simulator's ground truth (not observable by a real desk). Bands: +/-2 "
             "block-clustered standard errors.", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "markouts-by-segment")

    # ---------------------------------------------------------------- results
    def seg(group, name, h):
        return float(table.loc[(table.group == group) & (table.segment == name), f"markout_{h}s_bps"].iloc[0])

    results = {
        "n_days": n_days, "seconds_per_day": n_seconds, "n_passive_fills": len(fills),
        "shares_filled": float(w.sum()), "informed_share_of_volume": float(w[inf].sum() / w.sum()),
        "bps_per_tick": 1e4 * 0.01 / float(fills["price"].mean()),
        "horizons_s": HORIZONS_S,
        "markout_bps_informed": {f"{h}s": float(mi[h]) for h in HORIZONS_S},
        "markout_bps_uninformed": {f"{h}s": seg("counterparty", "uninformed (noise)", h) for h in HORIZONS_S},
        "markout_bps_all": {f"{h}s": float(per_share[h]) for h in HORIZONS_S},
        "markout_60s_bps_by_taker_size": {name: seg("size_bucket", name, 60) for name, _, _ in SIZE_BUCKETS},
        "informed_share_by_taker_size": {r.segment: r.informed_share_truth for r in table[table.group == "size_bucket"].itertuples()},
        "markout_0s_and_60s_bps_by_spread": {name: [seg("spread_bucket", name, 0), seg("spread_bucket", name, 60)] for name, _, _ in SPREAD_BUCKETS},
        "income_statement_usd_per_day": income,
        "income_by_counterparty_usd_per_day": by_cp,
        "informed_first_negative_horizon_s": first_negative,
        "se_bps_all_naive_vs_block": {"10s": [naive_se[10], block_se[10]], "300s": [naive_se[300], block_se[300]]},
        "markout_60s_bps_per_fill_vs_per_share": [float(per_fill[60]), float(per_share[60])],
        "segments": table.round(4).to_dict(orient="records"),
    }
    utils.write_results(ctx, results)
    print(f"\nSummary: liquidity providers capture {per_share[0]:+.2f} bps at the trade and keep {per_share[60]:+.2f} bps after "
          f"60 s; informed flow goes from {mi[0]:+.2f} to {mi[60]:+.2f} bps, noise flow ends at "
          f"{seg('counterparty', 'uninformed (noise)', 60):+.2f} bps. Orders of 800+ shares are "
          f"{table.loc[(table.group == 'size_bucket') & (table.segment == '800+ sh'), 'informed_share_truth'].iloc[0]:.0%} informed "
          f"and end at {seg('size_bucket', '800+ sh', 60):+.2f} bps.")


if __name__ == "__main__":
    main()
