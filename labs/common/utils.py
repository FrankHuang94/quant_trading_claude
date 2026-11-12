"""Small helpers shared by every lab: CLI flags, output locations, plotting style, results.

Conventions (see CLAUDE.md, "Labs"):
  * every lab is `labs/NN-name/lab.py`, runnable as `python labs/NN-name/lab.py [--smoke] [--seed N]`;
  * full runs write plots to docs/assets/labs/labNN-<name>.png (committed, embedded in the KB)
    and key numbers to labs/NN-name/results.json (committed, quoted by pages);
  * smoke runs (CI) write everything to labs/_smoke/NN-name/ (git-ignored) and must finish < 60 s.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ASSETS = REPO / "docs" / "assets" / "labs"
SMOKE_ROOT = REPO / "labs" / "_smoke"


@dataclass
class LabContext:
    lab_dir: Path      # labs/NN-name
    lab_id: str        # "NN"
    smoke: bool
    seed: int
    plot_dir: Path
    results_path: Path

    def fig_path(self, name: str) -> Path:
        """Path for a plot called `name` (no extension) -> labNN-name.png."""
        return self.plot_dir / f"lab{self.lab_id}-{name}.png"


def setup(lab_file: str, description: str = "") -> LabContext:
    """Parse --smoke/--seed and return a LabContext. Call first thing in main()."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--smoke", action="store_true", help="tiny, fast parameter set for CI (< 60 s)")
    ap.add_argument("--seed", type=int, default=7)
    args, _ = ap.parse_known_args()
    lab_dir = Path(lab_file).resolve().parent
    lab_id = lab_dir.name[:2]
    if args.smoke:
        plot_dir = SMOKE_ROOT / lab_dir.name
        results = plot_dir / "results.json"
    else:
        plot_dir = ASSETS
        results = lab_dir / "results.json"
    plot_dir.mkdir(parents=True, exist_ok=True)
    set_style()
    return LabContext(lab_dir, lab_id, args.smoke, args.seed, plot_dir, results)


def set_style() -> None:
    plt.rcParams.update({
        "figure.figsize": (9, 5), "figure.dpi": 110, "savefig.dpi": 130, "savefig.bbox": "tight",
        "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "font.size": 10, "legend.frameon": False,
    })


def save_fig(ctx: LabContext, fig: "plt.Figure", name: str) -> Path:
    path = ctx.fig_path(name)
    fig.savefig(path)
    plt.close(fig)
    print(f"  plot   -> {path.relative_to(REPO)}")
    return path


def _jsonable(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (np.floating,)):
        return round(float(x), 6)
    if isinstance(x, float):
        return round(x, 6)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.ndarray):
        return _jsonable(x.tolist())
    return x


def write_results(ctx: LabContext, results: dict) -> Path:
    payload = {"lab": ctx.lab_dir.name, "smoke": ctx.smoke, "seed": ctx.seed, **_jsonable(results)}
    ctx.results_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"  results-> {ctx.results_path.relative_to(REPO)}")
    return ctx.results_path


def annualized_sharpe(daily_pnl: np.ndarray, periods: int = 252) -> float:
    x = np.asarray(daily_pnl, dtype=float)
    x = x[np.isfinite(x)]
    if x.size < 2 or x.std(ddof=1) == 0:
        return float("nan")
    return float(np.sqrt(periods) * x.mean() / x.std(ddof=1))


def max_drawdown(cum_pnl: np.ndarray) -> float:
    c = np.asarray(cum_pnl, dtype=float)
    return float(np.max(np.maximum.accumulate(c) - c)) if c.size else 0.0
