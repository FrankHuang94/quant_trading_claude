"""Lab 02: fair value from the order book -- mid, weighted mid and the Stoikov (2018) microprice.

What it demonstrates
  * Three estimators of "where the price really is" built only from the top of the book:
      - the mid-price (bid + ask) / 2;
      - the size-weighted mid ("weighted mid"), which leans toward the side with less size;
      - the Stoikov (2018) microprice: mid + g*(imbalance, spread), where the adjustment g* is
        the expected long-run change of the mid given the current imbalance and spread,
        estimated from data with Stoikov's Markov-chain (iterative) method.
  * How well each predicts the FUTURE mid h = 1 s ... 120 s ahead (mean squared error, out of
    sample) and how close each is to the simulator's latent fair value (the planted truth).
  * A labeled baseline: the "conditional-expectation" adjustment E[mid(t+h) - mid(t) | state],
    fitted separately for each horizon h (the best any function of the book state can do at h).
  * Pitfalls: the weighted mid over-reacts (it jumps a full half-spread when queue sizes flip,
    and is worse than the plain mid when the spread is wide); and the gain from any of these
    estimators is a short-horizon effect: at 1-2 minutes, future price noise swamps it.

Data: labs/common/simulate.py `simulate_lob` (synthetic $50 stock, 1-cent tick). The adjustment
is estimated on training days and evaluated on separate test days (different seeds).

Supports: docs/03-algorithms/f-market-making-and-hft-algorithms/fair-value-and-microprice.md
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common import simulate, utils  # noqa: E402

N_IMB = 11                                   # imbalance buckets (odd: bucket 5 = balanced book)
MAX_SPREAD_TICKS = 3                         # spreads of 1, 2, 3 ticks (~96% of the time)
HORIZONS_S = [1, 2, 5, 10, 30, 60, 120]      # forecast horizons, seconds
COLORS = {"mid": "#52514e", "weighted mid": "#eb6834", "microprice": "#2a78d6",
          "conditional mean (per horizon)": "#1baf7a", "latent fair value (oracle)": "#6250d6"}


# =====================================================================================
# === CORE ALGORITHM ===
# imbalance = (bid_size - ask_size) / (bid_size + ask_size), in [-1, +1]
# All adjustments are in ticks; fair value = mid + adjustment * tick.
# =====================================================================================

def weighted_mid(bid, ask, bid_size, ask_size):
    """Size-weighted mid: (bid * ask_size + ask * bid_size) / (bid_size + ask_size).

    Equivalent to mid + imbalance * spread / 2: a big bid queue (buyers waiting) pulls the
    estimate toward the ask. Simple and fast, but it moves a full half-spread when one queue
    empties, and it is not a martingale (it over-reacts).
    """
    return (bid * ask_size + ask * bid_size) / (bid_size + ask_size)


def book_state(imbalance, spread_ticks, n_imb=N_IMB, max_spread_ticks=MAX_SPREAD_TICKS):
    """Discretize the book into a state id = (spread - 1) * n_imb + imbalance bucket.

    Imbalance buckets are symmetric around 0 (bucket centers -1.0, -0.8, ..., +1.0 for
    n_imb = 11), so a mirrored book maps to the mirrored bucket. Returns -1 for spreads
    outside 1..max_spread_ticks (those rows are left out).
    """
    half = (n_imb - 1) // 2
    bucket = np.rint(np.asarray(imbalance) * half).astype(int) + half
    spread = np.rint(np.asarray(spread_ticks)).astype(int)
    ok = (spread >= 1) & (spread <= max_spread_ticks)
    return np.where(ok, (spread - 1) * n_imb + bucket, -1)


def estimate_microprice_adjustment(state, mid_ticks, n_moves=None, n_imb=N_IMB,
                                   max_spread_ticks=MAX_SPREAD_TICKS, max_iter=200, tol=1e-6):
    """Stoikov (2018) microprice adjustment by the Markov-chain method, in ticks.

    state, mid_ticks: book state and mid (in ticks) at consecutive book updates (event time).
    Each update -> next update is one transition. If the mid did not move it is a transition
    between book states (matrix Q); if it moved we record the move and the new state (matrix R):
        G1 = (I - Q)^-1 r    expected mid change up to and including the NEXT mid move
        B  = (I - Q)^-1 R    distribution of the book state right after that move
        G^k = G1 + B G1 + ... + B^(k-1) G1    expected change over the next k mid moves
        g*  = lim G^k        the microprice adjustment (n_moves=None)
    The data are symmetrized (mirror book, flipped move) so the series converges.
    Returns an array (max_spread_ticks, n_imb): row = spread - 1, column = imbalance bucket.
    """
    s, s_next, dm = state[:-1], state[1:], np.diff(mid_ticks)
    mirror = lambda x: (x // n_imb) * n_imb + (n_imb - 1 - x % n_imb)   # noqa: E731
    s, s_next, dm = (np.concatenate([s, mirror(s)]), np.concatenate([s_next, mirror(s_next)]),
                     np.concatenate([dm, -dm]))
    n = n_imb * max_spread_ticks
    count = np.maximum(np.bincount(s, minlength=n), 1).astype(float)
    moved = dm != 0
    Q, R = np.zeros((n, n)), np.zeros((n, n))
    np.add.at(Q, (s[~moved], s_next[~moved]), 1.0)   # book changed, mid unchanged
    np.add.at(R, (s[moved], s_next[moved]), 1.0)     # mid moved; book is now in state s_next
    Q, R = Q / count[:, None], R / count[:, None]
    r = np.bincount(s, weights=dm, minlength=n) / count  # mean mid move per update from s
    inv = np.linalg.inv(np.eye(n) - Q)
    G1, B = inv @ r, inv @ R
    g, term = G1.copy(), G1.copy()
    for _ in range((n_moves or max_iter) - 1):
        term = B @ term                               # contribution of the next mid move
        g += term
        if n_moves is None and np.max(np.abs(term)) < tol:
            break
    return g.reshape(max_spread_ticks, n_imb)


# === END CORE ALGORITHM ===
# =====================================================================================


def book_updates(sim):
    """Rows where the top of book changed (prices or sizes), with a usable state. For training."""
    q = sim.quotes
    x = q[["bid", "ask", "bid_size", "ask_size"]].to_numpy()
    changed = np.r_[True, np.any(x[1:] != x[:-1], axis=1)] & q["mid"].notna().to_numpy()
    q = q[changed]
    tick = sim.cfg.tick
    state = book_state(q["imbalance"].to_numpy(), q["spread"].to_numpy() / tick)
    ok = state >= 0
    return state[ok], q["mid"].to_numpy()[ok] / tick


def sample_grid(sim, clock_h, event_k, step=1.0):
    """Book state on a regular clock grid plus the realized future mid at each horizon (ticks).

    clock_h: horizons in seconds; event_k: horizons in number of mid changes ("mid after the
    k-th mid change from now"). Grid points whose horizon runs past the end are dropped.
    """
    q, tick = sim.quotes, sim.cfg.tick
    times = q["time"].to_numpy()
    mid = q["mid"].ffill().bfill().to_numpy() / tick
    t_grid = np.arange(step, sim.cfg.n_seconds - max(clock_h), step)
    j = np.searchsorted(times, t_grid, side="right") - 1
    out = {"mid": mid[j], "fv": sim.fair_value.to_numpy()[j] / tick,
           "spread": q["spread"].to_numpy()[j] / tick,
           "state": book_state(q["imbalance"].to_numpy()[j], q["spread"].to_numpy()[j] / tick),
           "wmid": weighted_mid(q["bid"].to_numpy()[j], q["ask"].to_numpy()[j],
                                q["bid_size"].to_numpy()[j], q["ask_size"].to_numpy()[j]) / tick}
    for h in clock_h:
        out[f"t{h}"] = mid[np.searchsorted(times, t_grid + h, side="right") - 1]
    change_rows = np.flatnonzero(np.diff(mid) != 0) + 1          # rows carrying a new mid
    nxt = np.searchsorted(change_rows, j, side="right")          # first change after row j
    valid = nxt + max(event_k) - 1 < change_rows.size
    for k in event_k:
        out[f"k{k}"] = mid[change_rows[np.minimum(nxt + k - 1, change_rows.size - 1)]]
    keep = valid & np.isfinite(out["wmid"]) & np.isfinite(out["mid"])
    return {name: v[keep] for name, v in out.items()}


def stack(samples):
    return {k: np.concatenate([s[k] for s in samples]) for k in samples[0]}


def conditional_mean(state, y, n_imb=N_IMB, max_spread_ticks=MAX_SPREAD_TICKS):
    """Baseline: E[y | state] by bucket averages, symmetrized like the microprice (ticks)."""
    n = n_imb * max_spread_ticks
    ok = state >= 0
    s, y = state[ok], y[ok]
    mirror = (s // n_imb) * n_imb + (n_imb - 1 - s % n_imb)
    s2, y2 = np.concatenate([s, mirror]), np.concatenate([y, -y])
    return (np.bincount(s2, weights=y2, minlength=n) /
            np.maximum(np.bincount(s2, minlength=n), 1)).reshape(max_spread_ticks, n_imb)


def apply_adjustment(table, state):
    """mid adjustment (ticks) for each row; 0 (= plain mid) where the spread is out of range."""
    flat = table.ravel()
    return np.where(state >= 0, flat[np.maximum(state, 0)], 0.0)


def mse(est, target):
    return float(np.mean((est - target) ** 2))


def main() -> None:
    ctx = utils.setup(__file__, "Lab 02: fair value, weighted mid and the microprice")
    n_seconds = 1800 if ctx.smoke else 23400
    train_seeds = [ctx.seed] if ctx.smoke else [ctx.seed, ctx.seed + 1]
    test_seeds = [ctx.seed + 10] if ctx.smoke else [ctx.seed + 10, ctx.seed + 11]
    clock_h = [1, 2, 5, 10, 30, 60] if ctx.smoke else HORIZONS_S
    event_k = [1, 2, 3, 5, 10, 20]
    print("Lab 02: fair value from the order book -- mid, weighted mid, Stoikov microprice")
    print(f"  simulating {len(train_seeds)} training + {len(test_seeds)} test day(s) of {n_seconds:,} s ...")
    train_sims = [simulate.simulate_lob(n_seconds=n_seconds, seed=s) for s in train_seeds]
    test_sims = [simulate.simulate_lob(n_seconds=n_seconds, seed=s) for s in test_seeds]

    # ---- 1) estimate the microprice adjustment on the training days (event time)
    S, M = zip(*(book_updates(sim) for sim in train_sims))
    # concatenating days adds one spurious transition per day boundary (of ~66,000): negligible
    state_tr, mid_tr = np.concatenate(S), np.concatenate(M)
    g_star = estimate_microprice_adjustment(state_tr, mid_tr)
    g_k = {k: estimate_microprice_adjustment(state_tr, mid_tr, n_moves=k) for k in event_k}
    n_iter = next(i for i in range(1, 500)
                  if np.max(np.abs(estimate_microprice_adjustment(state_tr, mid_tr, n_moves=i) - g_star)) < 0.005)
    print(f"  microprice: {state_tr.size:,} book updates for training; G^k is within 0.005 ticks of the "
          f"limit after {n_iter} mid moves")

    # ---- 2) evaluation samples (1 s clock grid) and conditional-mean baselines
    tr = stack([sample_grid(sim, clock_h, event_k) for sim in train_sims])
    te = stack([sample_grid(sim, clock_h, event_k) for sim in test_sims])
    cond = {f"k{k}": conditional_mean(tr["state"], tr[f"k{k}"] - tr["mid"]) for k in event_k}
    cond.update({f"t{h}": conditional_mean(tr["state"], tr[f"t{h}"] - tr["mid"]) for h in clock_h})
    micro = te["mid"] + apply_adjustment(g_star, te["state"])
    print(f"  evaluation: {te['mid'].size:,} one-second grid points on {len(test_seeds)} unseen day(s); "
          f"spread 1/2/3 ticks {np.mean(np.rint(te['spread']) == 1):.0%}/"
          f"{np.mean(np.rint(te['spread']) == 2):.0%}/{np.mean(np.rint(te['spread']) == 3):.0%} of the time")

    def table(horizons):
        rows = {}
        for key in horizons:
            target = te[key]
            base = mse(te["mid"], target)
            cm = te["mid"] + apply_adjustment(cond[key], te["state"])
            rows[key] = {"mse_mid": base, "mse_weighted_mid": mse(te["wmid"], target),
                         "mse_microprice": mse(micro, target), "mse_conditional_mean": mse(cm, target),
                         "mse_latent_fair_value": mse(te["fv"], target)}
            for name in ("weighted_mid", "microprice", "conditional_mean", "latent_fair_value"):
                rows[key][f"change_vs_mid_pct_{name}"] = 100 * (rows[key][f"mse_{name}"] / base - 1)
        return rows

    ev_rows = table([f"k{k}" for k in event_k])
    ck_rows = table([f"t{h}" for h in clock_h])
    print("\n  MSE vs the future mid, % change relative to using the plain mid (negative = better)")
    print("  horizon            weighted mid  microprice  cond. mean (per horizon)  latent FV (oracle)")
    for key, r in list(ev_rows.items()) + list(ck_rows.items()):
        label = f"next {key[1:]} mid change(s)" if key[0] == "k" else f"{key[1:]} s"
        print(f"  {label:<22} {r['change_vs_mid_pct_weighted_mid']:+9.1f}% {r['change_vs_mid_pct_microprice']:+10.1f}%"
              f" {r['change_vs_mid_pct_conditional_mean']:+14.1f}% {r['change_vs_mid_pct_latent_fair_value']:+18.1f}%"
              f"   (mid MSE {r['mse_mid']:.2f} ticks^2)")

    # ---- 3) by spread state at the next mid change (where the weighted mid goes wrong)
    by_spread = {}
    spread_t = np.rint(te["spread"])
    for s in (1, 2, 3):
        m = spread_t == s
        target = te["k1"][m]
        base = mse(te["mid"][m], target)
        by_spread[f"{s}_tick"] = {
            "share_of_time": float(m.mean()),
            "change_vs_mid_pct_weighted_mid": 100 * (mse(te["wmid"][m], target) / base - 1),
            "change_vs_mid_pct_microprice": 100 * (mse(micro[m], target) / base - 1)}
    print("\n  Next mid change, by spread:",
          "; ".join(f"{k}: wmid {v['change_vs_mid_pct_weighted_mid']:+.0f}%, micro {v['change_vs_mid_pct_microprice']:+.0f}%"
                    for k, v in by_spread.items()))

    # ---- 4) calibration: is the predicted adjustment the right size? slope of realized on predicted
    adj_micro = micro - te["mid"]
    adj_wmid = te["wmid"] - te["mid"]
    slope = {name: {k: float(np.sum(a * (te[f"k{k}"] - te["mid"])) / np.sum(a * a)) for k in event_k}
             for name, a in (("weighted_mid", adj_wmid), ("microprice", adj_micro))}
    print("  Slope of realized mid change on predicted adjustment (1 = unbiased):")
    for name, d in slope.items():
        print(f"    {name:<13}" + "  ".join(f"k={k}: {v:.2f}" for k, v in d.items()))

    # ---- 5) Markov model vs reality: predicted change over the next k moves vs realized (test days)
    b08 = N_IMB - 2                                               # imbalance bucket centered at +0.8
    markov_vs_real = {}
    for k in (1, 3, 20):
        realized = conditional_mean(te["state"], te[f"k{k}"] - te["mid"])
        markov_vs_real[f"k{k}"] = {f"spread{sp}": [round(float(g_k[k][sp - 1, b08]), 3), round(float(realized[sp - 1, b08]), 3)]
                                   for sp in (1, 2)}
    print("  Markov G^k vs realized at imbalance +0.8, ticks [predicted, realized]: "
          + "; ".join(f"{k}: {v}" for k, v in markov_vs_real.items()))

    # ---- 6) the planted truth: does the book state know the latent fair value?
    gap = te["fv"] - te["mid"]
    corr_fv = {"microprice_adjustment": float(np.corrcoef(adj_micro, gap)[0, 1]),
               "weighted_mid_adjustment": float(np.corrcoef(adj_wmid, gap)[0, 1])}
    fv_mse = {"mid": mse(te["mid"], te["fv"]), "weighted_mid": mse(te["wmid"], te["fv"]),
              "microprice": mse(micro, te["fv"])}
    print(f"  Latent fair value: std(FV - mid) = {gap.std():.2f} ticks; corr(adjustment, FV - mid): "
          f"microprice {corr_fv['microprice_adjustment']:+.3f}, weighted mid {corr_fv['weighted_mid_adjustment']:+.3f}")

    # ---------------------------------------------------------------- plots
    centers = np.linspace(-1, 1, N_IMB)
    emp1 = conditional_mean(te["state"], te["k1"] - te["mid"])     # out-of-sample, test days
    emp20 = conditional_mean(te["state"], te["k20"] - te["mid"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
    for ax, s in zip(axes, (1, 2)):
        ax.plot(centers, centers * s / 2, ls="--", lw=2, color=COLORS["weighted mid"], label="weighted mid: imbalance x spread/2")
        ax.plot(centers, g_star[s - 1], lw=2.2, marker="o", ms=6, color=COLORS["microprice"], label="microprice g* (Markov, training days)")
        ax.plot(centers, emp1[s - 1], lw=0, marker="s", ms=7, color=COLORS["conditional mean (per horizon)"],
                label="realized: mid after the next mid change (test days)")
        ax.plot(centers, emp20[s - 1], lw=0, marker="^", ms=7, color=COLORS["latent fair value (oracle)"],
                label="realized: mid after 20 mid changes (test days)")
        ax.axhline(0, color="0.3", lw=0.8)
        ax.set_title(f"Spread = {s} tick{'s' if s > 1 else ''}", fontsize=10)
        ax.set_xlabel("Imbalance (bid size - ask size) / (bid size + ask size)")
    axes[0].set_ylabel("Fair value minus mid, ticks (1 tick = $0.01)")
    axes[1].legend(fontsize=8, loc="upper left")
    fig.suptitle("Lab 02: microprice adjustment vs imbalance (synthetic data)", fontweight="bold")
    fig.text(0.5, -0.03, "Synthetic $50 stock, 1-cent tick. Realized points = average future mid minus current mid in "
             "each imbalance bucket, symmetrized.", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "adjustment")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
    ks = np.array(event_k)
    for name, key, marker in (("weighted mid", "weighted_mid", "s"), ("microprice", "microprice", "o"),
                              ("conditional mean (per horizon)", "conditional_mean", "^")):
        axes[0].plot(ks, [ev_rows[f"k{k}"][f"change_vs_mid_pct_{key}"] for k in event_k], marker=marker, ms=7,
                     lw=2, color=COLORS[name], label=name)
    axes[0].axhline(0, color="0.3", lw=0.8)
    axes[0].set_xscale("log")
    axes[0].set_xticks(ks, [str(k) for k in event_k])
    axes[0].set_xlabel("Horizon: number of future mid changes")
    axes[0].set_ylabel("MSE vs future mid, % change relative to the mid")
    axes[0].set_title("Forecast error (below 0 = better than the mid)", fontsize=10)
    axes[0].legend(fontsize=8)
    for name, key, marker in (("weighted mid", "weighted_mid", "s"), ("microprice", "microprice", "o")):
        axes[1].plot(ks, [slope[key][k] for k in event_k], marker=marker, ms=7, lw=2, color=COLORS[name], label=name)
    axes[1].axhline(1, color="0.3", lw=1, ls=":")
    axes[1].annotate("unbiased = 1", (ks[-1], 1), xytext=(-60, -14), textcoords="offset points", fontsize=8, color="0.3")
    axes[1].axhline(0, color="0.3", lw=0.8)
    axes[1].set_xscale("log")
    axes[1].set_xticks(ks, [str(k) for k in event_k])
    axes[1].set_xlabel("Horizon: number of future mid changes")
    axes[1].set_ylabel("Slope of realized mid change on predicted adjustment")
    axes[1].set_title("Calibration (does the adjustment come true?)", fontsize=10)
    axes[1].legend(fontsize=8)
    fig.suptitle("Lab 02: out-of-sample forecast error and calibration (synthetic data)", fontweight="bold")
    fig.text(0.5, -0.03, f"{te['mid'].size:,} one-second grid points on unseen simulated days; adjustments estimated "
             "on separate training days.", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "forecast-error")

    # ---------------------------------------------------------------- results
    def r1(d):
        return {k: round(float(v), 3) for k, v in d.items()}

    k1 = ev_rows["k1"]
    results = {
        # headline numbers (next mid change = the horizon the microprice is built for)
        "headline_next_mid_change_mse_change_pct_microprice": round(k1["change_vs_mid_pct_microprice"], 2),
        "headline_next_mid_change_mse_change_pct_weighted_mid": round(k1["change_vs_mid_pct_weighted_mid"], 2),
        "headline_next_mid_change_mse_change_pct_conditional_mean": round(k1["change_vs_mid_pct_conditional_mean"], 2),
        "headline_spread1_next_change_mse_change_pct_microprice": round(by_spread["1_tick"]["change_vs_mid_pct_microprice"], 2),
        "headline_spread2_next_change_mse_change_pct_weighted_mid": round(by_spread["2_tick"]["change_vs_mid_pct_weighted_mid"], 2),
        "headline_calibration_slope_microprice_1_vs_20_moves": [round(slope["microprice"][1], 3), round(slope["microprice"][20], 3)],
        "headline_corr_microprice_adjustment_with_latent_fv_gap": round(corr_fv["microprice_adjustment"], 4),
        "train_days": len(train_seeds), "test_days": len(test_seeds), "seconds_per_day": n_seconds,
        "n_train_book_updates": int(state_tr.size), "n_test_grid_points": int(te["mid"].size),
        "imbalance_bucket_centers": [round(float(c), 2) for c in centers],
        "microprice_adjustment_ticks_spread1": [round(float(x), 3) for x in g_star[0]],
        "microprice_adjustment_ticks_spread2": [round(float(x), 3) for x in g_star[1]],
        "microprice_adjustment_ticks_spread3": [round(float(x), 3) for x in g_star[2]],
        "weighted_mid_adjustment_ticks_at_imbalance_0.8": {"spread1": 0.4, "spread2": 0.8, "spread3": 1.2},
        "microprice_adjustment_ticks_at_imbalance_0.8": {f"spread{s}": round(float(g_star[s - 1, -2]), 3) for s in (1, 2, 3)},
        "mid_moves_to_converge": n_iter,
        "next_mid_change_mse_change_vs_mid_pct": r1({k.replace("change_vs_mid_pct_", ""): v for k, v in ev_rows["k1"].items() if k.startswith("change")}),
        "mse_change_vs_mid_pct_by_event_horizon": {k: r1({kk.replace("change_vs_mid_pct_", ""): vv for kk, vv in r.items() if kk.startswith("change")}) for k, r in ev_rows.items()},
        "mse_change_vs_mid_pct_by_clock_horizon_s": {k: r1({kk.replace("change_vs_mid_pct_", ""): vv for kk, vv in r.items() if kk.startswith("change")}) for k, r in ck_rows.items()},
        "mid_mse_ticks2": {k: round(r["mse_mid"], 3) for k, r in {**ev_rows, **ck_rows}.items()},
        "next_mid_change_by_spread": {k: r1(v) for k, v in by_spread.items()},
        "markov_vs_realized_at_imbalance_0.8": markov_vs_real,
        "calibration_slope_by_mid_changes": {n: {f"k{k}": round(v, 3) for k, v in d.items()} for n, d in slope.items()},
        "latent_fv_gap_std_ticks": float(gap.std()),
        "corr_adjustment_with_latent_fv_gap": corr_fv,
        "mse_vs_latent_fv_ticks2": fv_mse,
    }
    utils.write_results(ctx, results)
    print(f"\nSummary: at the next mid change the microprice cuts forecast MSE by {-k1['change_vs_mid_pct_microprice']:.1f}% vs the mid, "
          f"the weighted mid raises it by {k1['change_vs_mid_pct_weighted_mid']:.0f}% (it over-reacts when the spread is wide). "
          f"The effect is short-lived: calibration slope {slope['microprice'][1]:.2f} at 1 move -> {slope['microprice'][20]:.2f} at 20 moves.")


if __name__ == "__main__":
    main()
