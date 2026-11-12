"""Lab 18: a toy smart order router (SOR) that prices fees, fill probability and toxicity.

What it demonstrates
  * Six stylized US-equity venues: two maker-taker lit exchanges (high and standard rebate), an
    inverted lit exchange, a low-fee lit exchange, and two midpoint dark pools (one with natural
    institutional contra flow, one full of fast/toxic flow). Fees are realistic in size under the
    long-standing $0.0030/share access-fee cap; fill rates and markouts are invented but plausible.
  * Child orders are routed passively (post a limit order; if it does not fill, cross the spread
    later) and aggressively (marketable IOC; if it misses, re-route to a default lit venue).
  * Router policies: (1) fee-greedy (best published fee), (2) fill-probability-weighted (learns fill
    rates online and minimizes expected spread + fees + non-fill cost, but ignores markouts),
    (3) net-of-toxicity (also learns each venue's post-fill markout online; a bandit that explores
    by Thompson sampling), (4) an oracle that knows the true venue parameters.
  * All-in cost per share = spread + fees + markout (+ the cost of cleaning up non-fills).
  * Pitfalls: chasing fill rates routes you to the toxic pool; markouts are so noisy that telling
    two venues 0.5 bp apart takes hundreds of fills; a router with no memory cap (cumulative means)
    keeps routing to a venue long after its toxicity jumps (regime break halfway, passive run).

Supports: docs/03-algorithms/e-execution-algorithms/smart-order-routing.md
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from common import utils  # noqa: E402

PRICE = 50.0            # $/share
HALF_SPREAD_BPS = 1.0   # 1-cent spread on a $50 stock = 2 bps, half = 1 bp
FALLBACK_BPS = {        # expected cost (bps) when the child order does not fill at the chosen venue
    "passive": 2.6,     # cross later: half-spread 1.0 + take fee 0.6 + adverse drift while waiting 1.0
    "aggressive": 2.1,  # re-route: half-spread 1.0 + take fee 0.6 + markout 0.3 + quote fade 0.2
}

# Published (router-visible) venue data. Fees in $/share: + = fee paid, - = rebate received.
VENUES = [
    {"name": "A: lit maker-taker, high rebate", "kind": "lit", "make": -0.0025, "take": 0.0030},
    {"name": "B: lit maker-taker, std rebate", "kind": "lit", "make": -0.0016, "take": 0.0029},
    {"name": "C: lit inverted", "kind": "lit", "make": 0.0015, "take": -0.0010},
    {"name": "D: lit low-fee", "kind": "lit", "make": 0.0000, "take": 0.0009},
    {"name": "E: dark midpoint, natural", "kind": "mid", "make": 0.0010, "take": 0.0010},
    {"name": "F: dark midpoint, toxic", "kind": "mid", "make": 0.0005, "take": 0.0005},
]
# Hidden truth (routers never see this): fill probability and mean post-fill markout (bps, + = adverse).
TRUE_FILL = {"passive": [0.30, 0.40, 0.50, 0.35, 0.20, 0.70],
             "aggressive": [0.95, 0.92, 0.70, 0.85, 0.15, 0.50]}
TRUE_MARKOUT = {"passive": [1.5, 0.6, 1.3, 0.5, 0.4, 3.0],
                "aggressive": [0.3, 0.3, 0.8, 0.1, 0.2, 1.8]}
MARKOUT_NOISE_BPS = {"passive": 5.0, "aggressive": 4.0}   # per-fill std of a ~10-s markout
FALLBACK_NOISE_BPS = 3.0
BREAK_VENUE, BREAK_MARKOUT = 1, 2.4   # passive run: venue B's markout jumps 0.6 -> 2.4 bp halfway


# =====================================================================================
# === CORE ALGORITHM ===
# =====================================================================================

def expected_all_in_cost(venue, mode, fill_prob, markout_bps, price=PRICE,
                         half_spread_bps=HALF_SPREAD_BPS, fallback_bps=None):
    """Expected all-in cost (bps, + = cost) of sending one child order to `venue`.

    filled:  spread (passive lit earns the half-spread, aggressive lit pays it, midpoint = 0)
             + venue fee or rebate + expected post-fill markout (adverse selection)
    missed:  fallback cost of finishing the order elsewhere (cross the spread later / re-route).
    """
    fee_bps = (venue["make"] if mode == "passive" else venue["take"]) / price * 1e4
    if venue["kind"] == "mid":
        spread_bps = 0.0
    else:
        spread_bps = -half_spread_bps if mode == "passive" else half_spread_bps
    if fallback_bps is None:
        fallback_bps = FALLBACK_BPS[mode]
    return fill_prob * (spread_bps + fee_bps + markout_bps) + (1.0 - fill_prob) * fallback_bps


def route(order, venues, stats, policy="net_of_toxicity", rng=None, markout_sd_bps=5.0):
    """Pick a venue index for one child order.

    order:  {"mode": "passive" | "aggressive", "qty": shares}  (qty unused in this toy; a real
            router compares it with each venue's displayed size)
    stats:  the router's online estimates per venue (see update_stats)
    policy: "fee_greedy"      -> best published make (passive) or take (aggressive) fee;
            "fill_weighted"   -> min expected cost from learned fill rates, markouts ignored;
            "net_of_toxicity" -> min expected cost from learned fill rates AND markouts.
    With an rng the learned policies explore by Thompson sampling: draw a plausible fill rate and
    markout for each venue given how much evidence we have, then route to the cheapest draw.
    """
    mode = order["mode"]
    if policy == "fee_greedy":
        return int(np.argmin([v["make"] if mode == "passive" else v["take"] for v in venues]))
    best, best_cost = 0, math.inf
    for i, v in enumerate(venues):
        n_sent = stats["sent"][i] + stats["prior_n"]
        n_fill = stats["fills"][i] + stats["prior_n"]
        fill, markout = stats["fill_rate"][i], stats["markout"][i]
        if rng is not None:                       # posterior draws: wide when evidence is thin
            fill = rng.beta(1 + fill * n_sent, 1 + (1 - fill) * n_sent)
            markout = rng.normal(markout, markout_sd_bps / math.sqrt(n_fill))
        if policy == "fill_weighted":
            markout = 0.0                         # the blind spot: toxicity is not priced
        cost = expected_all_in_cost(v, mode, fill, markout)
        if cost < best_cost:
            best, best_cost = i, cost
    return best


def update_stats(stats, venue, filled, markout_bps, memory=math.inf):
    """Update the router's estimates for `venue` after one child order.

    Running means weighted 1/(count + prior_n). Counts are capped at `memory` observations, so once
    a venue has that much history the update becomes an EWMA: the estimate keeps tracking a venue
    whose fill rate or toxicity changes, and Thompson draws never become over-confident.
    """
    stats["sent"][venue] = min(stats["sent"][venue] + 1, memory)
    w = 1.0 / (stats["sent"][venue] + stats["prior_n"])
    stats["fill_rate"][venue] += w * (float(filled) - stats["fill_rate"][venue])
    if filled:
        stats["fills"][venue] = min(stats["fills"][venue] + 1, memory)
        w = 1.0 / (stats["fills"][venue] + stats["prior_n"])
        stats["markout"][venue] += w * (markout_bps - stats["markout"][venue])


# === END CORE ALGORITHM ===
# =====================================================================================


def new_stats(n_venues, prior_fill=0.5, prior_markout=1.0, prior_n=5):
    """Uninformative-ish priors: every venue starts at 50% fill and 1 bp markout."""
    return {"sent": np.zeros(n_venues), "fills": np.zeros(n_venues),
            "fill_rate": np.full(n_venues, prior_fill), "markout": np.full(n_venues, prior_markout),
            "prior_n": prior_n}


def true_params(mode, t, n_orders):
    fill = list(TRUE_FILL[mode])
    mark = list(TRUE_MARKOUT[mode])
    if mode == "passive" and t >= n_orders // 2:
        mark[BREAK_VENUE] = BREAK_MARKOUT
    return fill, mark


def run_policy(policy, mode, draws, memory=math.inf, seed=0):
    """Route n child orders with one policy; return chosen venues and cost components (bps)."""
    u_fill, z_mark, z_fb = draws
    n = u_fill.shape[0]
    stats = new_stats(len(VENUES))
    router_rng = np.random.default_rng(seed)     # the router's own randomness (Thompson draws)
    choice = np.empty(n, dtype=int)
    comp = np.zeros((n, 4))   # spread, fee, markout, fallback (non-fill) cost
    for t in range(n):
        fill_p, mark_mu = true_params(mode, t, n)
        if policy == "oracle":
            v = int(np.argmin([expected_all_in_cost(VENUES[i], mode, fill_p[i], mark_mu[i])
                               for i in range(len(VENUES))]))
        else:
            v = route({"mode": mode, "qty": 200}, VENUES, stats, policy, router_rng)
        filled = u_fill[t, v] < fill_p[v]
        if filled:
            venue = VENUES[v]
            fee = (venue["make"] if mode == "passive" else venue["take"]) / PRICE * 1e4
            spread = 0.0 if venue["kind"] == "mid" else (-HALF_SPREAD_BPS if mode == "passive"
                                                         else HALF_SPREAD_BPS)
            markout = mark_mu[v] + MARKOUT_NOISE_BPS[mode] * z_mark[t, v]
            comp[t, :3] = spread, fee, markout
        else:
            markout = np.nan
            comp[t, 3] = FALLBACK_BPS[mode] + FALLBACK_NOISE_BPS * z_fb[t]
        if policy != "oracle":
            update_stats(stats, v, filled, markout, memory)
        choice[t] = v
    return choice, comp, stats


def rolling_share(choice, n_venues, window):
    onehot = np.eye(n_venues)[choice]
    csum = np.cumsum(np.vstack([np.zeros(n_venues), onehot]), axis=0)
    return (csum[window:] - csum[:-window]) / window


def main():
    ctx = utils.setup(__file__, "Lab 18: smart order router toy")
    rng = np.random.default_rng(ctx.seed)
    n_orders = 4_000 if ctx.smoke else 40_000
    window = 400 if ctx.smoke else 1_000
    memory = 1_000                     # router estimates remember ~1,000 observations per venue
    policies = {"fee_greedy": "Fee-greedy", "fill_weighted": "Fill-probability-weighted",
                "net_of_toxicity": "Net-of-toxicity (bandit)", "oracle": "Oracle (knows truth)"}

    out, runs = {}, {}
    for mode in ("passive", "aggressive"):
        # common random numbers: every policy faces the same fill/markout draws for (order, venue)
        draws = (rng.random((n_orders, len(VENUES))), rng.standard_normal((n_orders, len(VENUES))),
                 rng.standard_normal(n_orders))
        for pol in policies:
            runs[(mode, pol)] = run_policy(pol, mode, draws, memory, seed=ctx.seed + 1)
            out[(mode, pol)] = runs[(mode, pol)][1].sum(axis=1).mean()
        if mode == "passive":   # pitfall: the same bandit with cumulative (never-forgetting) means
            runs[(mode, "no_cap")] = run_policy("net_of_toxicity", mode, draws, math.inf, seed=ctx.seed + 1)

    # ---- regime break (passive): cost and orders still sent to venue B afterwards -----
    half = n_orders // 2
    after = {k: (runs[("passive", k)][1][half:].sum(axis=1).mean(),
                 int(np.sum(runs[("passive", k)][0][half:] == BREAK_VENUE)))
             for k in ("net_of_toxicity", "no_cap", "oracle")}

    # ---- truth recovery: learned vs true markouts (aggressive run is stationary) -------
    st = runs[("aggressive", "net_of_toxicity")][2]
    well_sampled = st["fills"] >= 200
    mk_err = np.abs(st["markout"] - np.array(TRUE_MARKOUT["aggressive"]))[well_sampled]
    fills_to_separate = (1.96 * MARKOUT_NOISE_BPS["passive"] * math.sqrt(2) / 0.5) ** 2
    to_toxic = {m: float(np.mean(runs[(m, "fill_weighted")][0] == 5)) for m in ("passive", "aggressive")}

    # ---- plot 1: all-in cost decomposition by policy ---------------------------------
    labels = ["spread paid (+) / earned (-)", "fees (+) / rebates (-)", "markout (adverse selection)",
              "non-fill cleanup"]
    colors = ["#4C72B0", "#DD8452", "#C44E52", "#8C8C8C"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), sharey=True)
    for ax, mode in zip(axes, ("passive", "aggressive")):
        for j, pol in enumerate(policies):
            comp = runs[(mode, pol)][1].mean(axis=0)
            pos, neg = 0.0, 0.0
            for k in range(4):
                base = pos if comp[k] >= 0 else neg
                ax.bar(j, comp[k], bottom=base, color=colors[k], width=0.6,
                       label=labels[k] if j == 0 else None)
                pos, neg = (pos + comp[k], neg) if comp[k] >= 0 else (pos, neg + comp[k])
            total = comp.sum()
            ax.plot(j, total, "kD", ms=7, label="all-in total" if j == 0 else None)
            ax.annotate(f"{total:.2f}", (j, pos + 0.08), ha="center", fontsize=9, fontweight="bold")
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xticks(range(len(policies)))
        ax.set_xticklabels([p.replace(" (", "\n(").replace("-weighted", "-\nweighted")
                            for p in policies.values()], fontsize=8.5)
        ax.set_title(f"{mode.capitalize()} child orders ({n_orders:,} per policy)")
    axes[0].set_ylabel("cost per share (bps of price, + = cost)")
    handles, labs = axes[0].get_legend_handles_labels()
    fig.legend(handles, labs, loc="lower center", ncol=5, fontsize=8.5, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.07, 1, 0.9))
    fig.suptitle("Smart order router: all-in cost = spread + fees + markout + non-fill cleanup\n"
                 "(synthetic venues, illustrative fees; 1 bp = \\$0.005/share at \\$50)", fontweight="bold")
    utils.save_fig(ctx, fig, "all-in-cost")

    # ---- plot 2: learned venue allocation over time + regime break -------------------
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True,
                                   gridspec_kw={"height_ratios": [1.3, 1]})
    share = rolling_share(runs[("passive", "net_of_toxicity")][0], len(VENUES), window)
    x = np.arange(window, n_orders + 1)
    vcols = ["#4C72B0", "#55A868", "#8172B3", "#CCB974", "#64B5CD", "#C44E52"]
    ax1.stackplot(x, 100 * share.T, labels=[v["name"] for v in VENUES], colors=vcols, alpha=0.9)
    ax1.axvline(half, color="k", ls="--", lw=1.2)
    ax1.text(half + n_orders * 0.01, 95, f"venue B turns toxic\n(passive markout "
             f"{TRUE_MARKOUT['passive'][BREAK_VENUE]} -> {BREAK_MARKOUT} bp)", fontsize=8.5, va="top",
             bbox=dict(fc="white", ec="none", alpha=0.85))
    ax1.set_ylabel(f"share of child orders\n(%, rolling {window:,})")
    ax1.set_ylim(0, 100)
    ax1.set_title("Net-of-toxicity bandit: learned venue allocation, passive orders (synthetic)")
    ax1.legend(fontsize=7.5, loc="center left", bbox_to_anchor=(1.0, 0.5))
    smooth = 2 * window
    x2 = np.arange(smooth, n_orders + 1)
    for key, lab, c in (("fee_greedy", "fee-greedy", "C0"),
                        ("no_cap", "bandit, cumulative means (no memory cap)", "C1"),
                        ("net_of_toxicity", f"bandit, memory {memory:,} obs per venue", "C2"),
                        ("oracle", "oracle", "k")):
        cost = runs[("passive", key)][1].sum(axis=1)
        ax2.plot(x2, np.convolve(cost, np.ones(smooth) / smooth, mode="valid"), color=c, lw=1.5, label=lab)
    ax2.axvline(half, color="k", ls="--", lw=1.2)
    ax2.set_xlabel("child order number")
    ax2.set_ylabel(f"all-in cost per share\n(bps, rolling {smooth:,})")
    ax2.legend(fontsize=8, loc="center left", bbox_to_anchor=(1.0, 0.5))
    utils.save_fig(ctx, fig, "venue-allocation")

    # ---- results ---------------------------------------------------------------------
    res = {f"{mode}_all_in_bps_{pol}": v for (mode, pol), v in out.items()}
    for mode in ("passive", "aggressive"):
        res[f"{mode}_saving_vs_fee_greedy_bps"] = out[(mode, "fee_greedy")] - out[(mode, "net_of_toxicity")]
        res[f"{mode}_regret_vs_oracle_bps"] = out[(mode, "net_of_toxicity")] - out[(mode, "oracle")]
        res[f"{mode}_fill_weighted_share_to_toxic_dark_pool"] = to_toxic[mode]
    res.update({
        "passive_saving_vs_fee_greedy_usd_per_million_shares":
            res["passive_saving_vs_fee_greedy_bps"] * 1e-4 * PRICE * 1e6,
        "post_break_cost_bps_memory_capped": after["net_of_toxicity"][0],
        "post_break_cost_bps_cumulative_means": after["no_cap"][0],
        "post_break_cost_bps_oracle": after["oracle"][0],
        "post_break_orders_to_toxic_venue_memory_capped": after["net_of_toxicity"][1],
        "post_break_orders_to_toxic_venue_cumulative_means": after["no_cap"][1],
        "learned_markout_max_abs_error_bps": float(mk_err.max()) if mk_err.size else float("nan"),
        "venues_with_200plus_fills": int(well_sampled.sum()),
        "fills_needed_to_separate_venues_0p5bp_apart": fills_to_separate,
    })
    utils.write_results(ctx, res)

    print(f"\nAll-in cost per share (bps; 1 bp = ${PRICE * 1e-4:.4f}/share), {n_orders:,} child orders per run")
    print(f"{'policy':<30}{'passive':>9}{'aggressive':>12}")
    for pol, name in policies.items():
        print(f"{name:<30}{out[('passive', pol)]:>9.2f}{out[('aggressive', pol)]:>12.2f}")
    print(f"Fill-weighted router sends {100*to_toxic['passive']:.0f}% (passive) / "
          f"{100*to_toxic['aggressive']:.0f}% (aggressive) of orders to the toxic dark pool F.")
    print(f"After venue B turns toxic: cost {after['net_of_toxicity'][0]:.2f} bp (memory cap) vs "
          f"{after['no_cap'][0]:.2f} (cumulative) vs {after['oracle'][0]:.2f} (oracle); orders still "
          f"sent to B: {after['net_of_toxicity'][1]:,} vs {after['no_cap'][1]:,}")
    print(f"Learned aggressive markouts: max abs error {res['learned_markout_max_abs_error_bps']:.2f} bp "
          f"over {int(well_sampled.sum())} venues with >= 200 fills; "
          f"~{fills_to_separate:.0f} fills per venue to separate 0.5 bp.")


if __name__ == "__main__":
    main()
