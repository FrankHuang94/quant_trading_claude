"""Lab 05: optimal market-making quotes -- naive vs Avellaneda-Stoikov (2008) vs GLFT (2013).

What it demonstrates
  * A single-stock dealer posts a bid and an ask around a mid-price that follows Brownian motion.
    Each quote is filled at Poisson rate lambda(delta) = A exp(-k delta), where delta is the
    quote's distance from the mid: quote tighter, get filled more often, earn less per fill.
  * Three quoting rules, Monte Carlo over thousands of one-hour sessions:
      (i)   naive: symmetric quotes at a fixed distance from the mid, ignoring inventory;
      (ii)  Avellaneda & Stoikov (2008): quote around a reservation price that leans against
            inventory, r = mid - q gamma sigma^2 (T - t), with an optimal total spread;
      (iii) Gueant, Lehalle & Fernandez-Tapia (2013): closed-form asymptotic quotes with
            inventory limits; stationary (no T - t), and they depend on the fill parameters A, k.
  * Every strategy is held to the same hard inventory limit and flattens at the end of the
    session (paying a stylized liquidation cost).
  * An income statement per strategy: spread capture + inventory (mark-to-market) P&L + adverse
    selection + liquidation cost = total P&L, plus mean, std, Sharpe-like ratio and inventory
    statistics, and a mean-vs-risk frontier as risk aversion gamma (or the naive spread) varies.
  * Pitfalls: (1) the literal AS formula with a long horizon quotes very wide early in the session
    and stops controlling inventory near the end; (2) adverse selection is invisible in the
    spread-capture line: in a second "world", news jumps arrive and informed traders pick off the
    dealer's stale quote just before each jump. That cuts every strategy's P&L, most of all the
    tight quoters, unless quotes are widened by the measured markout.

Units (stylized, chosen for readable numbers): prices in CENTS per share, inventory q in LOTS of
100 shares, so 1 cent x 1 lot = $1 and P&L is in dollars. All parameters are illustrative.

Supports: docs/03-algorithms/f-market-making-and-hft-algorithms/quoting-and-inventory-control.md,
          docs/02-strategies/a-liquidity-provision/equity-market-making.md
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from common import utils  # noqa: E402

# ---- stylized market (illustrative; see README "Key parameters")
PRICE_CENTS = 5000.0                       # $50 stock
SIGMA = 100.0 / np.sqrt(23400.0)           # 2% daily vol = 100 cents/day -> 0.654 cents per sqrt(second)
A_FILL = 0.06                              # fills per second per side if quoting AT the mid (delta = 0)
K_FILL = 1.5                               # intensity decay per cent of distance from the mid
T_SESSION = 3600.0                         # one-hour session (seconds); flat at the start and the end
DT = 1.0                                   # time step (seconds)
Q_MAX = 10                                 # hard inventory limit, lots (1,000 shares)
LIQ_HALF_SPREAD = 0.5                      # liquidation cost at the close: 0.5 cent per share ...
LIQ_IMPACT = 0.1                           # ... plus 0.1 cent per share for each lot liquidated
NEWS_RATE = 1.0 / 60.0                     # adverse-selection world: news jumps per second (1 a minute)
NEWS_MEAN_CENTS = 1.5                      # jump size ~ exponential, mean 1.5 cents (3 bps), random sign


# =====================================================================================
# === CORE ALGORITHM ===
# mid, quotes, sigma in cents (per share); q in lots; gamma in 1/$; k in 1/cent; A in 1/s; t, T in s.
# A quote at distance delta from the mid is filled at rate A * exp(-k * delta).
# =====================================================================================

def as_quotes(mid, q, t, gamma, sigma, k, T):
    """Avellaneda & Stoikov (2008) bid and ask.

    reservation price  r = mid - q * gamma * sigma^2 * (T - t)    (lean against inventory)
    total spread       s = gamma * sigma^2 * (T - t) + (2 / gamma) * ln(1 + gamma / k)
    bid, ask           r - s / 2,  r + s / 2
    Long inventory (q > 0) lowers both quotes: sell more readily, buy less readily. Both the lean
    and the extra width shrink to zero as t -> T (inventory is valued at the mid at T).
    """
    tau = T - t
    reservation = mid - q * gamma * sigma**2 * tau
    spread = gamma * sigma**2 * tau + (2.0 / gamma) * np.log1p(gamma / k)
    return reservation - spread / 2, reservation + spread / 2


def glft_quotes(q, gamma, sigma, A, k, q_max=np.inf):
    """Gueant, Lehalle & Fernandez-Tapia (2013) closed-form asymptotic quotes (distance from mid).

    delta_bid(q) = (1/gamma) ln(1 + gamma/k) + (2q + 1)/2 * c
    delta_ask(q) = (1/gamma) ln(1 + gamma/k) - (2q - 1)/2 * c
    c = sqrt( sigma^2 gamma / (2 k A) * (1 + gamma/k)^(1 + k/gamma) )   (lean per lot, cents)
    Stationary: no T - t. The more fills you expect (large A), the less you lean. Inventory
    limits: no bid at q >= q_max, no ask at q <= -q_max (returned as +inf = not quoting).
    """
    base = np.log1p(gamma / k) / gamma
    c = np.sqrt(sigma**2 * gamma / (2 * k * A) * np.exp((1 + k / gamma) * np.log1p(gamma / k)))
    d_bid = base + (2 * q + 1) / 2 * c
    d_ask = base - (2 * q - 1) / 2 * c
    return np.where(q >= q_max, np.inf, d_bid), np.where(q <= -q_max, np.inf, d_ask)


def step_pnl(q_before, bought, sold, d_bid, d_ask, jump, diffusion):
    """Income-statement increments ($) for one time step: fills first, then the mid moves.

    spread capture = distance of each fill from the mid (always >= 0 when quoting outside it)
    adverse selection = the price jump right after the fills, on the lots just traded (an informed
                        trader picks off a stale quote just before news: always negative for them)
    inventory P&L  = inventory held x the rest of the mid move (mark-to-market)
    Sum over steps + liquidation cost = total P&L = cash + q_T * mid_T - liquidation cost.
    """
    spread = bought * d_bid + sold * d_ask
    adverse = (bought - sold) * jump
    inventory = q_before * jump + (q_before + bought - sold) * diffusion
    return spread, adverse, inventory


# === END CORE ALGORITHM ===
# =====================================================================================


@dataclass
class Strategy:
    name: str
    kind: str              # "naive" | "as" | "glft"
    param: float           # naive: half-spread (cents); as / glft: gamma (1/$)
    widen: float = 0.0     # extra distance added to both quotes (cents), e.g. expected markout
    cancel_speed: float = 0.0   # chance of pulling a stale quote before an informed trader hits it


def quote_offsets(strats, mid, q, t):
    """Distances (cents) of bid and ask from the mid for every strategy row (shape: n_strat x n)."""
    d_bid = np.empty_like(q, dtype=float)
    d_ask = np.empty_like(q, dtype=float)
    for i, s in enumerate(strats):
        if s.kind == "naive":
            d_bid[i], d_ask[i] = s.param, s.param
        elif s.kind == "as":
            bid, ask = as_quotes(mid[i], q[i], t, s.param, SIGMA, K_FILL, T_SESSION)
            d_bid[i], d_ask[i] = mid[i] - bid, ask - mid[i]
        else:
            d_bid[i], d_ask[i] = glft_quotes(q[i], s.param, SIGMA, A_FILL, K_FILL, Q_MAX)
        d_bid[i] += s.widen
        d_ask[i] += s.widen
    d_bid = np.where(q >= Q_MAX, np.inf, np.maximum(d_bid, 0.0))   # same hard limit for everyone;
    d_ask = np.where(q <= -Q_MAX, np.inf, np.maximum(d_ask, 0.0))  # never quote through the mid
    return d_bid, d_ask


def run_sessions(strats, n_sessions, seed, adverse_selection=False, save_every=10):
    """Monte Carlo of n_sessions one-hour sessions for every strategy (common random numbers).

    Uninformed flow: each quote is filled at rate A exp(-k delta). Adverse-selection world: news
    arrives at NEWS_RATE; the mid jumps by +/-J (J exponential); just before the jump an informed
    trader hits the dealer's quote on the losing side if the jump exceeds its distance (J > delta).
    """
    rng = np.random.default_rng(seed)
    n_s, n_steps = len(strats), int(T_SESSION / DT)
    mid = np.full(n_sessions, PRICE_CENTS)                        # same mid path for every strategy
    q = np.zeros((n_s, n_sessions), dtype=np.int64)
    lines = {k: np.zeros((n_s, n_sessions)) for k in ("spread", "adverse", "inventory")}
    cash = np.zeros((n_s, n_sessions))
    n_fills = np.zeros((n_s, n_sessions))
    n_picked_off = np.zeros((n_s, n_sessions))
    abs_q_sum = np.zeros((n_s, n_sessions))
    at_limit = np.zeros((n_s, n_sessions))
    q_saved = np.zeros((n_s, n_steps // save_every + 1, n_sessions), dtype=np.int16)
    news_rate = NEWS_RATE if adverse_selection else 0.0
    speed = np.array([[st.cancel_speed] for st in strats])
    for step in range(n_steps):
        t = step * DT
        if step % save_every == 0:
            q_saved[:, step // save_every] = q
        d_bid, d_ask = quote_offsets(strats, np.broadcast_to(mid, q.shape), q, t)
        u_b, u_a, u_news, u_fast = rng.random((4, n_sessions))              # shared by all strategies
        size = rng.exponential(NEWS_MEAN_CENTS, n_sessions)
        sign = np.where(rng.random(n_sessions) < 0.5, 1.0, -1.0)
        diffusion = SIGMA * np.sqrt(DT) * rng.standard_normal(n_sessions)
        news = u_news < news_rate * DT
        jump = np.where(news, sign * size, 0.0)                             # +: price jumps up
        bought = (u_b < -np.expm1(-A_FILL * np.exp(-K_FILL * d_bid) * DT)).astype(float)
        sold = (u_a < -np.expm1(-A_FILL * np.exp(-K_FILL * d_ask) * DT)).astype(float)
        too_slow = u_fast >= speed                              # fast dealers cancel in time
        picked_bid = news & (jump < 0) & (d_bid < -jump) & too_slow   # stale bid hit before a down-jump
        picked_ask = news & (jump > 0) & (d_ask < jump) & too_slow    # stale ask lifted before an up-jump
        bought = np.maximum(bought, picked_bid)                 # at most one lot per side per step
        sold = np.maximum(sold, picked_ask)
        fill_d_bid = np.where(bought > 0, d_bid, 0.0)
        fill_d_ask = np.where(sold > 0, d_ask, 0.0)
        s_line, a_line, i_line = step_pnl(q, bought, sold, fill_d_bid, fill_d_ask, jump, diffusion)
        lines["spread"] += s_line
        lines["adverse"] += a_line
        lines["inventory"] += i_line
        cash += sold * (mid + fill_d_ask) - bought * (mid - fill_d_bid)
        q += (bought - sold).astype(np.int64)
        mid = mid + jump + diffusion
        n_fills += bought + sold
        n_picked_off += picked_bid + picked_ask
        abs_q_sum += np.abs(q)
        at_limit += np.abs(q) >= Q_MAX
    q_saved[:, -1] = q
    liquidation = -np.abs(q) * (LIQ_HALF_SPREAD + LIQ_IMPACT * np.abs(q))
    total = lines["spread"] + lines["adverse"] + lines["inventory"] + liquidation
    wealth = cash + q * mid + liquidation                    # cash + inventory at the final mid
    assert np.allclose(total, wealth, atol=1e-6), "income statement does not add up"
    return {"total": total, **lines, "liquidation": liquidation, "fills": n_fills, "picked_off": n_picked_off,
            "mean_abs_q": abs_q_sum / n_steps, "time_at_limit": at_limit / n_steps, "q_end": q,
            "q_samples": q_saved}


def summarize(strats, res):
    rows = []
    for i, s in enumerate(strats):
        tot = res["total"][i]
        rows.append({
            "strategy": s.name, "kind": s.kind, "param": s.param, "widen": s.widen,
            "mean_pnl": float(tot.mean()), "std_pnl": float(tot.std(ddof=1)),
            "sharpe_like": float(tot.mean() / tot.std(ddof=1)),
            "p5_pnl": float(np.percentile(tot, 5)),
            "spread_capture": float(res["spread"][i].mean()), "adverse_selection": float(res["adverse"][i].mean()),
            "inventory_pnl": float(res["inventory"][i].mean()), "liquidation_cost": float(res["liquidation"][i].mean()),
            "inventory_pnl_std": float(res["inventory"][i].std(ddof=1)),
            "fills": float(res["fills"][i].mean()),
            "spread_capture_per_fill_cents": float(res["spread"][i].sum() / res["fills"][i].sum()),
            "mean_abs_inventory_lots": float(res["mean_abs_q"][i].mean()),
            "std_inventory_lots": float(res["q_samples"][i].std()),
            "time_at_limit": float(res["time_at_limit"][i].mean()),
            "mean_abs_inventory_at_close_lots": float(np.abs(res["q_end"][i]).mean())})
    return rows


def glft_lean_per_lot(gamma):
    """GLFT lean c (cents per lot) and the equivalent AS horizon tau* = c / (gamma sigma^2) (s)."""
    d_bid0, _ = glft_quotes(np.array(0), gamma, SIGMA, A_FILL, K_FILL)
    d_bid1, _ = glft_quotes(np.array(1), gamma, SIGMA, A_FILL, K_FILL)
    c = float(d_bid1 - d_bid0)
    return c, c / (gamma * SIGMA**2)


INCOME_LINES = ["spread_capture", "inventory_pnl", "adverse_selection", "liquidation_cost", "mean_pnl"]


def print_income(rows, title):
    print(f"\n  {title}  ($ per one-hour session, mean over sessions)")
    print(f"  {'strategy':<38}{'spread':>8}{'invent.':>9}{'adv.sel':>9}{'liquid.':>9}{'TOTAL':>9}{'std':>8}"
          f"{'Sharpe':>8}{'fills':>7}{'|q|':>6}{'|q_T|':>7}")
    for r in rows:
        print(f"  {r['strategy']:<38}{r['spread_capture']:8.1f}{r['inventory_pnl']:9.1f}{r['adverse_selection']:9.1f}"
              f"{r['liquidation_cost']:9.1f}{r['mean_pnl']:9.1f}{r['std_pnl']:8.1f}{r['sharpe_like']:8.2f}"
              f"{r['fills']:7.0f}{r['mean_abs_inventory_lots']:6.2f}{r['mean_abs_inventory_at_close_lots']:7.2f}")


def main() -> None:
    ctx = utils.setup(__file__, "Lab 05: Avellaneda-Stoikov and GLFT quoting")
    n_sessions = 150 if ctx.smoke else 2000
    gamma_glft = 0.01                                        # headline risk aversion (1/$)
    naive_half = 1.0 / K_FILL                                # risk-neutral optimal distance: 1/k
    naive_grid = [0.33, 0.5, naive_half, 1.0, 1.5]
    as_grid = [1e-5, 3e-5, 1e-4, 3e-4, 6e-4, 1e-3, 3e-3, 1e-2]
    glft_grid = [1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1]
    if ctx.smoke:
        naive_grid, as_grid, glft_grid = [naive_half, 1.0], [3e-4, 6e-4, 1e-2], [3e-3, 1e-2, 3e-2]
    sweep = ([Strategy(f"naive, half-spread {d:.2f} c", "naive", d) for d in naive_grid]
             + [Strategy(f"AS, gamma {g:g}", "as", g) for g in as_grid]
             + [Strategy(f"GLFT, gamma {g:g}", "glft", g) for g in glft_grid])
    c_lean, tau_star = glft_lean_per_lot(gamma_glft)
    print("Lab 05: market-making quotes -- naive vs Avellaneda-Stoikov (2008) vs GLFT (2013)")
    print(f"  {n_sessions:,} one-hour sessions per strategy; fills A exp(-k delta), A = {A_FILL}/s, k = {K_FILL}/cent; "
          f"sigma = {SIGMA:.3f} cents/sqrt(s); limit +/-{Q_MAX} lots")
    print(f"  GLFT gamma = {gamma_glft}: lean {c_lean:.3f} cents per lot of inventory = AS with a fixed horizon "
          f"T - t = {tau_star:.0f} s")

    # ---- world A: no adverse selection (the models' own assumptions)
    res_a = run_sessions(sweep, n_sessions, ctx.seed, adverse_selection=False)
    rows_a = summarize(sweep, res_a)
    by_name_a = {r["strategy"]: r for r in rows_a}
    glft_name = f"GLFT, gamma {gamma_glft:g}"
    naive_name = f"naive, half-spread {naive_half:.2f} c"
    as_rows = [r for r in rows_a if r["kind"] == "as"]
    as_match = min(as_rows, key=lambda r: abs(r["std_pnl"] - by_name_a[glft_name]["std_pnl"]))
    as_same = by_name_a.get(f"AS, gamma {gamma_glft:g}")
    head_names = [naive_name, as_match["strategy"], glft_name]
    head_labels = {naive_name: f"(i) naive, fixed {naive_half:.2f}-cent half-spread",
                   as_match["strategy"]: f"(ii) AS, gamma {as_match['param']:g} (matched risk)",
                   glft_name: f"(iii) GLFT, gamma {gamma_glft:g}"}
    print_income([{**by_name_a[n], "strategy": head_labels[n]} for n in head_names]
                 + ([{**as_same, "strategy": f"pitfall: AS with GLFT's gamma {gamma_glft:g}"}] if as_same else []),
                 "WORLD A, no adverse selection")

    # ---- world B: news jumps + stale-quote sniping; then the fixes (widen by markout, cancel faster)
    res_b = run_sessions(sweep, n_sessions, ctx.seed, adverse_selection=True)
    rows_b = summarize(sweep, res_b)
    by_name_b = {r["strategy"]: r for r in rows_b}
    g_b = by_name_b[glft_name]
    markout_per_fill = -g_b["adverse_selection"] / g_b["fills"]          # cents per fill (= $ per lot)
    fixes = [Strategy(f"GLFT + widen {w:.2f} c", "glft", gamma_glft, widen=w)
             for w in (0.25, round(markout_per_fill, 2), 1.0)]
    fixes.append(Strategy("GLFT + cancel 50% of stale quotes in time", "glft", gamma_glft, cancel_speed=0.5))
    res_fix = run_sessions(fixes, n_sessions, ctx.seed, adverse_selection=True)
    rows_fix = summarize(fixes, res_fix)
    print_income([{**by_name_b[n], "strategy": head_labels[n]} for n in head_names] + rows_fix,
                 "WORLD B, with adverse selection (news + stale-quote sniping)")
    picked = {n: float(res_b["picked_off"][sweep.index(next(s for s in sweep if s.name == n))].mean()) for n in head_names}
    # planted truth: a quote at distance d is picked off when the jump J > d (prob exp(-d / mean)), and
    # each pick-off loses J on the lot, E[J | J > d] = d + mean (exponential jumps are memoryless)
    d0 = float(glft_quotes(np.array(0), gamma_glft, SIGMA, A_FILL, K_FILL)[0])
    n_news = NEWS_RATE * T_SESSION
    planted = {"glft_half_spread_at_q0_cents": d0, "news_per_session": n_news,
               "expected_pick_offs_at_q0": n_news * np.exp(-d0 / NEWS_MEAN_CENTS),
               "expected_adverse_selection_at_q0": -n_news * np.exp(-d0 / NEWS_MEAN_CENTS) * (d0 + NEWS_MEAN_CENTS),
               "measured_pick_offs": float(res_b["picked_off"][sweep.index(next(s for s in sweep if s.name == glft_name))].mean()),
               "measured_adverse_selection": g_b["adverse_selection"]}
    print(f"  planted vs measured (GLFT): pick-offs {planted['expected_pick_offs_at_q0']:.1f} vs {planted['measured_pick_offs']:.1f}"
          f" per session; adverse selection ${planted['expected_adverse_selection_at_q0']:.1f} vs ${planted['measured_adverse_selection']:.1f}")
    print(f"  measured adverse selection for GLFT: {markout_per_fill:.2f} cents per fill; pick-offs per session: "
          + ", ".join(f"{head_labels[n].split(',')[0]} {v:.1f}" for n, v in picked.items()))

    # ---- inventory over the session (std across sessions, by minute)
    idx = {n: next(i for i, s in enumerate(sweep) if s.name == n) for n in head_names}
    q_std_t = {n: res_a["q_samples"][idx[n]].std(axis=1) for n in head_names}   # every 10 s
    t_grid = np.arange(res_a["q_samples"].shape[1]) * 10 / 60.0                  # minutes

    # ---------------------------------------------------------------- plots
    colors = {naive_name: "#52514e", as_match["strategy"]: "#eb6834", glft_name: "#2a78d6"}
    fam_colors = {"naive": "#52514e", "as": "#eb6834", "glft": "#2a78d6"}
    fam_labels = {"naive": "naive (vary half-spread)", "as": "Avellaneda-Stoikov (vary gamma)", "glft": "GLFT (vary gamma)"}
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    ax = axes[0]
    all_tot = np.concatenate([res_a["total"][idx[n]] for n in head_names])
    bins = np.linspace(np.percentile(all_tot, 0.5), np.percentile(all_tot, 99.5), 70)
    for n in head_names:
        tot = res_a["total"][idx[n]]
        ax.hist(tot, bins=bins, histtype="step", lw=2, color=colors[n], density=True,
                label=f"{head_labels[n]}: mean \\${tot.mean():.0f}, sd \\${tot.std():.0f}")
        ax.axvline(tot.mean(), color=colors[n], lw=1, ls="--")
    ax.set_xlabel("P&L per one-hour session (\\$)")
    ax.set_ylabel("Density")
    ax.set_title("P&L distribution, no adverse selection", fontsize=10)
    ax.legend(fontsize=7.5, loc="upper left")
    ax = axes[1]
    for world, rows, ls, mfc in (("A", rows_a, "-", None), ("B", rows_b, "--", "white")):
        for fam in ("naive", "as", "glft"):
            pts = sorted([(r["param"], r["std_pnl"], r["mean_pnl"]) for r in rows if r["kind"] == fam])
            _, xs, ys = zip(*pts)                      # connected in parameter order
            ax.plot(xs, ys, ls=ls, marker="o", ms=6, lw=1.8, color=fam_colors[fam], mfc=mfc or fam_colors[fam],
                    label=fam_labels[fam] if world == "A" else None)
            if world == "A" and fam != "naive":
                for (g, x0, y0), offset in ((pts[0], (6, 6)), (pts[-1], (5, -13))):
                    ax.annotate(f"gamma {g:g}", (x0, y0), xytext=offset, textcoords="offset points",
                                fontsize=7.5, color="0.3")
    for n in head_names:
        r = by_name_a[n]
        ax.plot(r["std_pnl"], r["mean_pnl"], marker="*", ms=15, color=colors[n], mec="black", mew=0.8, ls="none")
    ax.plot([], [], ls="-", color="0.4", label="solid: no adverse selection")
    ax.plot([], [], ls="--", color="0.4", marker="o", mfc="white", label="dashed: with adverse selection")
    ax.set_xscale("log")
    ax.set_xlabel("Standard deviation of session P&L (\\$, log scale)")
    ax.set_ylabel("Mean session P&L (\\$)")
    ax.set_title("Mean vs risk as the parameter varies (stars = headline)", fontsize=10)
    ax.legend(fontsize=7.5, loc="lower right")
    fig.suptitle("Lab 05: market-making P&L by quoting rule (synthetic Monte Carlo)", fontweight="bold")
    fig.text(0.5, -0.03, f"{n_sessions:,} simulated one-hour sessions per strategy; stylized parameters (A = {A_FILL}/s, "
             f"k = {K_FILL}/cent, 2% daily vol, \\$50 stock, 100-share lots).", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "pnl")

    fig = plt.figure(figsize=(10.5, 8.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.05], hspace=0.38, wspace=0.25)
    ax = fig.add_subplot(gs[0, :])
    for n in head_names:
        ax.step(t_grid, res_a["q_samples"][idx[n], :, 0], where="post", lw=1.6, color=colors[n], label=head_labels[n])
    ax.axhline(Q_MAX, color="0.5", lw=0.8, ls=":")
    ax.axhline(-Q_MAX, color="0.5", lw=0.8, ls=":")
    ax.annotate("inventory limit", (1, Q_MAX), xytext=(0, 3), textcoords="offset points", fontsize=8, color="0.35")
    ax.set_xlabel("Minutes into the session")
    ax.set_ylabel("Inventory (lots of 100 shares)")
    ax.set_title("One simulated session, same order flow for all three", fontsize=10)
    ax.legend(fontsize=8, loc="lower left", ncol=3)
    ax = fig.add_subplot(gs[1, 0])
    for n in head_names:
        ax.plot(t_grid, q_std_t[n], lw=2, color=colors[n], label=head_labels[n].split(",")[0])
    ax.set_xlabel("Minutes into the session")
    ax.set_ylabel("Std of inventory across sessions (lots)")
    ax.set_title("Inventory dispersion through the session", fontsize=10)
    ax.legend(fontsize=8)
    ax = fig.add_subplot(gs[1, 1])
    q_axis = np.arange(-6, 7)
    lean_glft = -q_axis * c_lean
    ax.plot(q_axis, lean_glft, lw=2.5, color=colors[glft_name], label=f"GLFT (any time): {c_lean:.2f} c per lot")
    g_as = as_match["param"]
    for minute, alpha in ((0, 1.0), (30, 0.65), (55, 0.35)):
        lean_as = -q_axis * g_as * SIGMA**2 * (T_SESSION - 60 * minute)
        ax.plot(q_axis, lean_as, lw=2, color=colors[as_match["strategy"]], alpha=alpha, ls="--",
                label=f"AS at minute {minute}: {g_as * SIGMA**2 * (T_SESSION - 60 * minute):.2f} c per lot")
    ax.axhline(0, color="0.3", lw=0.8)
    ax.set_xlabel("Inventory q (lots)")
    ax.set_ylabel("Quote center minus mid (cents)")
    ax.set_title("Skew: how far quotes lean against inventory", fontsize=10)
    ax.legend(fontsize=7.5)
    fig.suptitle("Lab 05: inventory paths and quote skew (synthetic Monte Carlo)", fontweight="bold", y=0.98)
    fig.text(0.5, 0.01, "No adverse selection. Naive quotes do not lean at all; quotes never cross the mid and stop "
             f"on one side at +/-{Q_MAX} lots.", ha="center", fontsize=8, color="0.35")
    utils.save_fig(ctx, fig, "inventory")

    # ---------------------------------------------------------------- results
    keep = ["mean_pnl", "std_pnl", "sharpe_like", "p5_pnl", "spread_capture", "inventory_pnl", "adverse_selection",
            "liquidation_cost", "fills", "spread_capture_per_fill_cents", "mean_abs_inventory_lots",
            "std_inventory_lots", "time_at_limit", "mean_abs_inventory_at_close_lots"]

    def pick(r):
        return {k: round(float(r[k]), 3) for k in keep}

    best_fix = max(rows_fix[:-1], key=lambda r: r["mean_pnl"])
    results = {
        "n_sessions": n_sessions, "session_seconds": T_SESSION, "units": "prices in cents/share, inventory in 100-share lots, P&L in $",
        "params": {"A_per_s": A_FILL, "k_per_cent": K_FILL, "sigma_cents_per_sqrt_s": SIGMA, "inventory_limit_lots": Q_MAX,
                   "liquidation_cost": f"|q| x ({LIQ_HALF_SPREAD} + {LIQ_IMPACT} |q|) $",
                   "news_per_minute": NEWS_RATE * 60, "news_jump_mean_cents": NEWS_MEAN_CENTS},
        "gamma_glft": gamma_glft, "glft_lean_cents_per_lot": c_lean, "glft_equivalent_as_horizon_s": tau_star,
        "gamma_as_matched_risk": as_match["param"], "naive_half_spread_cents": naive_half,
        "world_a_no_adverse_selection": {head_labels[n]: pick(by_name_a[n]) for n in head_names},
        "world_b_with_adverse_selection": {head_labels[n]: pick(by_name_b[n]) for n in head_names},
        "world_b_fixes": {r["strategy"]: pick(r) for r in rows_fix},
        "pitfall_as_same_gamma_as_glft_world_a": pick(as_same) if as_same else None,
        "glft_adverse_selection_cents_per_fill": markout_per_fill,
        "planted_vs_measured_adverse_selection_glft": planted,
        "pick_offs_per_session": {head_labels[n]: v for n, v in picked.items()},
        "best_widening": {"strategy": best_fix["strategy"], "mean_pnl": best_fix["mean_pnl"]},
        "inventory_std_lots_at_minute_30_and_59": {head_labels[n]: [float(q_std_t[n][180]), float(q_std_t[n][354])]
                                                   for n in head_names} if not ctx.smoke else None,
        "frontier_world_a": [{"strategy": r["strategy"], "mean": round(r["mean_pnl"], 2), "std": round(r["std_pnl"], 2)} for r in rows_a],
        "frontier_world_b": [{"strategy": r["strategy"], "mean": round(r["mean_pnl"], 2), "std": round(r["std_pnl"], 2)} for r in rows_b],
    }
    utils.write_results(ctx, results)
    ga, gb = by_name_a[glft_name], by_name_b[glft_name]
    na = by_name_a[naive_name]
    print(f"\nSummary: GLFT (gamma {gamma_glft}) earns ${ga['mean_pnl']:.0f} per hour with sd ${ga['std_pnl']:.0f} (Sharpe-like "
          f"{ga['sharpe_like']:.2f}) vs naive ${na['mean_pnl']:.0f} / ${na['std_pnl']:.0f} ({na['sharpe_like']:.2f}) and AS at "
          f"matched risk ${as_match['mean_pnl']:.0f}. With adverse selection GLFT's spread capture rises to "
          f"${gb['spread_capture']:.0f} but adverse selection costs ${-gb['adverse_selection']:.0f}: total ${gb['mean_pnl']:.0f}.")


if __name__ == "__main__":
    main()
