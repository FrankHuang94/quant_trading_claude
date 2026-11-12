"""Lab 01: matching engine and order book -- price-time priority and the value of queue position.

Part A builds a tiny order book by hand and walks through price-time priority, printing the
book before and after each step.

Part B runs the synthetic order-book simulator (labs/common/simulate.py) with a small "probe"
agent that, every few seconds, posts a real 100-share passive order at the BACK of the best
bid or ask queue. Queue lengths vary, so the probes start with different numbers of shares
ahead of them. We measure
  (i)  the probability of being filled within N seconds vs shares ahead, and
  (ii) the markout of the fills (how the mid moves after we are filled), front vs back.
A robustness check tracks "virtual" orders at the front, middle and back of the SAME queue at
the same moment (the queue-position model backtesters use), which separates the effect of
priority from the effect of how long the queue was.

Run: python labs/01-matching-engine-order-book/lab.py [--smoke] [--seed N]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import utils, simulate  # noqa: E402
from common.orderbook import BUY, SELL, OrderBook  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PROBE_SIZE = 100                            # shares per probe order
HORIZONS = [0, 1, 2, 5, 10, 20, 30, 60]     # markout horizons, seconds
FILL_WINDOWS = [5, 10, 30]                  # "filled within N seconds"
WINDOW_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]           # categorical (validated, CVD-safe)
QUEUE_RAMP_4 = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # ordinal blue: front (light) -> back (dark)
QUEUE_RAMP_3 = ["#6da7ec", "#256abf", "#0d366b"]


# ----------------------------------------------------------------------------- Part A
def price_time_priority_demo() -> dict:
    """Hand-built example: who gets filled, in what order, and what is left."""
    book = OrderBook(tick=0.01)
    book.time = 1; a = book.add_limit(BUY, 10.00, 300, owner="A")    # noqa: E702
    book.time = 2; b = book.add_limit(BUY, 10.00, 200, owner="B")    # noqa: E702  same price, later
    book.time = 3; book.add_limit(BUY, 9.99, 500, owner="C")         # noqa: E702
    book.time = 4; book.add_limit(SELL, 10.01, 100, owner="D")       # noqa: E702
    book.time = 5; book.add_limit(SELL, 10.01, 300, owner="E")       # noqa: E702
    book.time = 6; book.add_limit(SELL, 10.02, 400, owner="F")       # noqa: E702
    print("\n[A] Book after six limit orders (each level lists its queue front -> back as owner:size)")
    print(book.to_string())
    print(f"    shares ahead of B at 10.00: {book.queue_ahead(b):g} (A arrived first)")

    print("\n[A1] T1 sells 400 at market: A (first in line) is filled completely, then B partly")
    book.time = 7
    fills1 = book.market(SELL, 400, owner="T1")
    for f in fills1:
        print(f"    fill {f.size:g} @ {f.price:.2f}  maker {f.maker_owner}  taker {f.taker_owner}")
    print(f"    A still resting? {book.order(a) is not None};  B has {book.order(b).size:g} left, now at the front")

    print("\n[A2] G joins the 10.00 bid behind B; then B cancels, so G moves to the front")
    book.time = 8
    g = book.add_limit(BUY, 10.00, 200, owner="G")
    ahead_before = book.queue_ahead(g)
    book.cancel(b)
    ahead_after = book.queue_ahead(g)
    print(f"    shares ahead of G: {ahead_before:g} before B cancels, {ahead_after:g} after")

    print("\n[A3] H sends a marketable limit: buy 500 @ 10.01. It takes D then E at 10.01 (time")
    print("     priority within the level) and the unfilled 100 rests as the new best bid")
    book.time = 9
    h = book.add_limit(BUY, 10.01, 500, owner="H")
    fills3 = book.last_fills
    for f in fills3:
        print(f"    fill {f.size:g} @ {f.price:.2f}  maker {f.maker_owner}  taker {f.taker_owner}")
    print(book.to_string())
    return {
        "fills_market_sell_400": [(f.maker_owner, f.size, f.price) for f in fills1],
        "g_shares_ahead_before_after_cancel": [ahead_before, ahead_after],
        "fills_marketable_buy_500": [(f.maker_owner, f.size, f.price) for f in fills3],
        "h_resting_size": book.order(h).size,
        "final_best_bid": book.best_bid(), "final_best_ask": book.best_ask(),
    }


# ----------------------------------------------------------------------------- Part B
class QueueProbeAgent:
    """Posts a 100-share order at the back of the best bid/ask every `every` seconds.

    Orders not filled within `max_wait` seconds are cancelled. In parallel it tracks three
    virtual orders per probe time (front, middle and back of the same queue): a virtual order
    is filled once a trade at its price (or through it) hits an order that was NOT ahead of it,
    i.e. once everything ahead of it has traded or cancelled. Virtual orders never trade, so
    they do not change the simulation.
    """

    def __init__(self, every: int = 5, max_wait: float = 60.0) -> None:
        self.every, self.max_wait = every, max_wait
        self.n_calls = 0
        self.live: dict[int, dict] = {}         # order id -> record of our resting probe
        self.probes: list[dict] = []            # every real probe ever posted
        self.virtual: list[dict] = []           # every virtual order ever created
        self.pending: list[dict] = []           # virtual orders still waiting
        self.subscribed = False

    def on_fill(self, f) -> None:
        """Book callback for EVERY fill: update the virtual orders."""
        for v in self.pending:
            if v["filled"] or f.taker_side != -v["side"]:
                continue                        # bids are hit by sells, asks are lifted by buys
            at_or_through = f.price <= v["price"] + 1e-9 if v["side"] == BUY else f.price >= v["price"] - 1e-9
            if at_or_through and f.maker_id not in v["ahead_ids"]:
                v["traded"] += f.size           # volume that would have reached us
                if v["traded"] >= PROBE_SIZE:
                    v["filled"], v["fill_time"] = True, f.time

    def __call__(self, ctx) -> None:
        if not self.subscribed:
            ctx.book.subscribe(self.on_fill)
            self.subscribed = True
        # 1) record fills of our real probes (exact fill times come with the Fill objects)
        for f in ctx.new_fills:
            rec = self.live.get(f.maker_id)
            if rec is not None:
                rec["filled_size"] += f.size
                if rec["filled_size"] >= PROBE_SIZE:
                    rec["fill_time"], rec["fill_price"] = f.time, f.price
                    del self.live[f.maker_id]
        # 2) cancel probes that waited too long
        for oid, rec in list(self.live.items()):
            if ctx.t - rec["t_post"] >= self.max_wait:
                ctx.cancel(oid)
                del self.live[oid]
        self.pending = [v for v in self.pending if not v["filled"] and ctx.t - v["t_post"] < self.max_wait]
        # 3) every `every` seconds post a new probe, alternating bid and ask
        self.n_calls += 1
        if self.n_calls % self.every:
            return
        side = BUY if (self.n_calls // self.every) % 2 else SELL
        price = ctx.book.best_bid() if side == BUY else ctx.book.best_ask()
        if price is None:
            return
        queue = ctx.book.level_orders(side, price)            # front of the queue first
        total = sum(o.size for o in queue)
        for label, frac in (("front", 0.0), ("middle", 0.5), ("back", 1.0)):
            ahead, shares = set(), 0
            for o in queue:                                   # orders that fit before our slot
                if shares + o.size > frac * total + 1e-9:
                    break
                ahead.add(o.id)
                shares += o.size
            v = {"label": label, "side": side, "price": price, "t_post": ctx.t, "ahead_ids": ahead,
                 "shares_ahead": shares, "traded": 0.0, "filled": False, "fill_time": np.nan}
            self.virtual.append(v)
            self.pending.append(v)
        oid = ctx.add_limit(side, price, PROBE_SIZE)          # the real order joins the back
        rec = {"side": side, "price": price, "t_post": ctx.t, "shares_ahead": ctx.book.queue_ahead(oid),
               "filled_size": 0.0, "fill_time": np.nan, "fill_price": np.nan}
        self.live[oid] = rec
        self.probes.append(rec)


def markouts(df: pd.DataFrame, quotes: pd.DataFrame, tick: float) -> pd.DataFrame:
    """Markout of each fill at each horizon, in ticks: side x (mid(t_fill + h) - fill price).

    Positive = the passive order made money (we bought below / sold above the later mid).
    """
    times = quotes["time"].to_numpy()
    mid = quotes["mid"].ffill().to_numpy()
    out = {}
    for h in HORIZONS:
        j = np.searchsorted(times, df["fill_time"].to_numpy() + h, side="right") - 1
        out[f"m{h}"] = df["side"].to_numpy() * (mid[j] - df["price"].to_numpy()) / tick
    return pd.DataFrame(out, index=df.index)


def run_day(seed: int, n_seconds: int):
    agent = QueueProbeAgent(every=5, max_wait=60.0)
    sim = simulate.simulate_lob(n_seconds=n_seconds, seed=seed, agent=agent)
    real = pd.DataFrame(agent.probes)
    virt = pd.DataFrame(agent.virtual).drop(columns=["ahead_ids"])
    tick = sim.cfg.tick
    for df in (real, virt):
        df["wait"] = df["fill_time"] - df["t_post"]
        df["day"] = seed
        filled = df["wait"].notna()
        mo = markouts(df[filled], sim.quotes, tick)
        for c in mo:
            df.loc[filled, c] = mo[c]
    # probes posted in the last 60 s have not had a fair chance: drop them
    real = real[real["t_post"] <= n_seconds - 60]
    virt = virt[virt["t_post"] <= n_seconds - 60]
    sp = np.round(sim.quotes["spread"] / tick)
    stats = {"events": len(sim.events), "trades": len(sim.trades),
             "spread_1tick_share": float((sp == 1).mean()), "spread_mean_ticks": float(sp.mean()),
             "touch_size_median": float(sim.quotes["bid_size"].median())}
    return real, virt, stats


def main() -> None:
    ctx = utils.setup(__file__, "Lab 01: matching engine, price-time priority and queue position")
    n_days = 1 if ctx.smoke else 3
    n_seconds = 1800 if ctx.smoke else 23400
    print("Lab 01: matching engine, price-time priority and the value of queue position")
    demo = price_time_priority_demo()

    print(f"\n[B] Simulating {n_days} x {n_seconds:,} s of order flow with a probe agent ...")
    reals, virts, day_stats = [], [], []
    for d in range(n_days):
        r, v, st = run_day(ctx.seed + d, n_seconds)
        reals.append(r); virts.append(v); day_stats.append(st)   # noqa: E702
    real = pd.concat(reals, ignore_index=True)
    virt = pd.concat(virts, ignore_index=True)
    print(f"    {len(real):,} real probes, {real['wait'].notna().sum():,} filled within 60 s; "
          f"book: spread = 1 tick {np.mean([s['spread_1tick_share'] for s in day_stats]):.0%} of the time, "
          f"median touch size {np.median([s['touch_size_median'] for s in day_stats]):.0f} shares")

    # (i) fill probability vs shares ahead
    for n in FILL_WINDOWS:
        real[f"fill_{n}s"] = (real["wait"] <= n).astype(float)
        virt[f"fill_{n}s"] = (virt["wait"] <= n).astype(float)
    edges = [0, 200, 400, 700, 1000, 1500, 2500, np.inf]
    real["bin"] = pd.cut(real["shares_ahead"], edges, right=False)
    by_bin = real.groupby("bin", observed=True).agg(
        n=("shares_ahead", "size"), shares_ahead=("shares_ahead", "mean"),
        **{f"fill_{n}s": (f"fill_{n}s", "mean") for n in FILL_WINDOWS}).dropna()
    by_bin = by_bin[by_bin["n"] >= 20]
    print("\n    Fill probability by shares ahead at entry (real probes):")
    print(by_bin.round(3).to_string())

    # (ii) markouts: quartiles of shares ahead (real), and front/middle/back of the same queue (virtual)
    q_edges = real["shares_ahead"].quantile([0, 0.25, 0.5, 0.75, 1.0]).to_numpy()
    q_edges[-1] += 1
    q_edges = np.unique(q_edges)
    labels = [f"Q{i + 1}: {lo:,.0f}-{hi - 1:,.0f} shares ahead" for i, (lo, hi) in enumerate(zip(q_edges[:-1], q_edges[1:]))]
    real["quartile"] = pd.cut(real["shares_ahead"], q_edges, right=False, labels=labels)
    mcols = [f"m{h}" for h in HORIZONS]
    real_mo = real.dropna(subset=["m0"]).groupby("quartile", observed=True)[mcols].mean()
    virt_mo = virt.dropna(subset=["m0"]).groupby("label")[mcols].mean().reindex(["front", "middle", "back"])
    virt_fill = virt.groupby("label")[[f"fill_{n}s" for n in FILL_WINDOWS]].mean().reindex(["front", "middle", "back"])
    virt_ahead = virt.groupby("label")["shares_ahead"].mean().reindex(["front", "middle", "back"])
    real_fill_q = real.groupby("quartile", observed=True)[[f"fill_{n}s" for n in FILL_WINDOWS]].mean()
    print("\n    Markout of fills, ticks per share (positive = the passive order made money):")
    print(real_mo.round(2).to_string())
    print("\n    Same queue, same moment (virtual orders): fill probability and markouts")
    print(pd.concat([virt_ahead.rename("shares_ahead"), virt_fill, virt_mo[["m10", "m30"]]], axis=1).round(2).to_string())

    # value of a posted order = P(fill) x average markout of the fill (unfilled orders earn 0)
    first, last = labels[0], real_mo.index[-1]
    fill60 = real.groupby("quartile", observed=True)["wait"].apply(lambda w: w.notna().mean())
    value_front = fill60[first] * real_mo.loc[first, "m30"]
    value_back = fill60[last] * real_mo.loc[last, "m30"]
    print(f"\n    Expected value per posted order at 30 s: front quartile {value_front:+.2f} ticks/share, "
          f"back quartile {value_back:+.2f} ticks/share "
          f"(= ${100 * 0.01 * (value_front - value_back):.2f} per 100 shares of queue priority)")

    # ---------------------------------------------------------------- plots
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for n, marker, color in zip(FILL_WINDOWS, ["o", "s", "^"], WINDOW_COLORS):
        p = by_bin[f"fill_{n}s"]
        se = np.sqrt(p * (1 - p) / by_bin["n"])
        ax.errorbar(by_bin["shares_ahead"], p, yerr=1.96 * se, marker=marker, ms=7, lw=2, capsize=3,
                    color=color, label=f"filled within {n} s")
        ax.annotate(f"{n} s", (by_bin["shares_ahead"].iloc[-1], p.iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color="0.2")   # direct label
    ax.set_xlim(right=by_bin["shares_ahead"].max() * 1.08)
    ax.set_xlabel("Shares ahead in the queue when the order is posted")
    ax.set_ylabel("Fill probability")
    ax.set_ylim(0, 1.02)
    ax.set_title("Lab 01: the longer the queue ahead, the lower the chance of a fill")
    ax.legend(loc="lower left")
    fig.text(0.5, -0.03, f"{len(real):,} simulated 100-share probes on a synthetic $50 stock with a 1-cent tick; "
             "error bars are 95% binomial intervals.", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "fill-prob-vs-queue")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8), sharey=True)
    for (name, row), c in zip(real_mo.iterrows(), QUEUE_RAMP_4):
        axes[0].plot(HORIZONS, row.to_numpy(), marker="o", ms=6, lw=2, color=c, label=name)
    axes[0].set_title("Real probes, by shares ahead at entry", fontsize=10)
    for name, c in zip(["front", "middle", "back"], QUEUE_RAMP_3):
        axes[1].plot(HORIZONS, virt_mo.loc[name].to_numpy(), marker="o", ms=6, lw=2, color=c,
                     label=f"{name} of queue ({virt_ahead[name]:,.0f} shares ahead on avg.)")
    axes[1].set_title("Same queue, same moment (virtual orders)", fontsize=10)
    for ax, loc in zip(axes, ["upper right", "lower left"]):
        ax.axhline(0, color="0.3", lw=0.8)
        ax.set_xlabel("Seconds after the fill")
        ax.legend(fontsize=8, loc=loc)
    axes[0].set_ylabel("Markout, ticks per share (1 tick = $0.01)")
    fig.suptitle("Lab 01: fills at the back of the queue are more adversely selected", fontweight="bold")
    fig.text(0.5, -0.02, "Markout = side x (mid t seconds after the fill - fill price); positive = the passive "
             "order made money. Synthetic $50 stock.", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "queue-markouts")

    # ---------------------------------------------------------------- results
    results = {
        "demo": demo,
        "n_days": n_days, "seconds_per_day": n_seconds,
        "n_probes": int(len(real)), "n_probe_fills_60s": int(real["wait"].notna().sum()),
        "sim_spread_1tick_share": float(np.mean([s["spread_1tick_share"] for s in day_stats])),
        "sim_touch_size_median": float(np.median([s["touch_size_median"] for s in day_stats])),
        "fill_prob_by_shares_ahead": [
            {"bin": str(i), "n": int(r.n), "mean_shares_ahead": float(r.shares_ahead),
             **{f"fill_{n}s": float(r[f"fill_{n}s"]) for n in FILL_WINDOWS}} for i, r in by_bin.iterrows()],
        "quartile_shares_ahead_edges": [float(x) for x in np.unique(q_edges)],
        "fill_prob_10s_front_quartile": float(real_fill_q.loc[first, "fill_10s"]),
        "fill_prob_10s_back_quartile": float(real_fill_q.loc[last, "fill_10s"]),
        "markout_10s_ticks_front_quartile": float(real_mo.loc[first, "m10"]),
        "markout_10s_ticks_back_quartile": float(real_mo.loc[last, "m10"]),
        "markout_30s_ticks_front_quartile": float(real_mo.loc[first, "m30"]),
        "markout_30s_ticks_back_quartile": float(real_mo.loc[last, "m30"]),
        "value_per_order_30s_ticks_front": float(value_front),
        "value_per_order_30s_ticks_back": float(value_back),
        "queue_priority_value_usd_per_100_shares": float(100 * 0.01 * (value_front - value_back)),
        "markout_horizons_s": HORIZONS,
        "markout_curves_ticks_by_quartile": {str(k): [float(x) for x in row] for k, row in real_mo.iterrows()},
        "markout_curves_ticks_virtual": {k: [float(x) for x in virt_mo.loc[k]] for k in ["front", "middle", "back"]},
        "virtual_same_queue": {
            name: {"shares_ahead": float(virt_ahead[name]), "fill_10s": float(virt_fill.loc[name, "fill_10s"]),
                   "markout_10s_ticks": float(virt_mo.loc[name, "m10"]),
                   "markout_30s_ticks": float(virt_mo.loc[name, "m30"])} for name in ["front", "middle", "back"]},
    }
    utils.write_results(ctx, results)
    print("\nSummary: queue priority is worth money twice over. Orders near the front fill more often"
          f" ({results['fill_prob_10s_front_quartile']:.0%} vs {results['fill_prob_10s_back_quartile']:.0%}"
          f" within 10 s) and their fills are less toxic ({results['markout_10s_ticks_front_quartile']:+.2f} vs"
          f" {results['markout_10s_ticks_back_quartile']:+.2f} ticks at 10 s).")


if __name__ == "__main__":
    main()
