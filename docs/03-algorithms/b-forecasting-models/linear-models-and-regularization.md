# Linear models and regularization

> **TL;DR**
>
> - The workhorse equity forecaster is still linear: regress forward residual returns on standardized signals, then shrink the coefficients (ridge, lasso, elastic net).
> - Returns are mostly noise: the best monthly stock-level out-of-sample R² in Gu, Kelly & Xiu (2020) was 0.40%; daily, 0.05–0.25% is good `[Estimate]`. At that signal-to-noise ratio, estimation variance dominates, so shrunk coefficients beat OLS.
> - Pooled and per-date (Fama–MacBeth) regressions differ mainly in how they weight dates.
> - The penalty is chosen by purged walk-forward cross-validation on rank IC, never by random K-fold.

**Level:** Core · **Pipeline stage:** forecast · **Last verified:** 2026-11

| Field | Value |
|---|---|
| Purpose (the question it answers) | What is the best linear forecast of next-period return from 10–300 standardized signals, and how much should each be trusted? |
| Inputs → Outputs | Signal panel (date × stock × K, ranked or z-scored per date) and forward residual returns → coefficients β and per-stock forecasts in bps |
| Used by strategies | [Cross-sectional alpha](../../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md) · [Fundamental quant signals](../../02-strategies/d-mid-frequency-alpha/fundamental-quant-signals.md) · [Analyst revisions and sentiment](../../02-strategies/d-mid-frequency-alpha/analyst-revisions-and-sentiment.md) · [Factor-residual mean reversion](../../02-strategies/c-statistical-arbitrage/factor-residual-mean-reversion.md) · [Short-term reversal](../../02-strategies/c-statistical-arbitrage/short-term-cross-sectional-reversal.md) · [ML-driven short-horizon alpha](../../02-strategies/c-statistical-arbitrage/ml-driven-short-horizon-alpha.md) · [Factor investing](../../02-strategies/e-risk-premia-and-factors/factor-investing-fundamentals.md) · [Equity market making](../../02-strategies/a-liquidity-provision/equity-market-making.md) |
| Latency / compute regime | Overnight batch: ridge on 2,000 stocks × 750 days × 100 signals takes seconds. Inference is a dot product (µs even in HFT fair-value models) |
| Key parameters | Penalty λ (by CV); elastic-net L1 share 0.1–0.5; window 1–3 years rolling or expanding; horizon 1–20 days; refit daily to monthly; winsorize at ±3σ |
| Main failure modes | Small λ with many signals; leakage from overlapping labels; sign-flipping coefficients under collinearity; stale β after regime shifts; microcap outliers |
| Lab | [Lab 12](https://github.com/FrankHuang94/quant_trading_claude/tree/main/labs/12-alpha-combination-purged-cv) |

## Intuition

Treat each signal as a witness about tomorrow's return; a regression decides how much to trust each one given the others. Over 99% of return variance is unpredictable, so some witnesses look reliable by luck, and OLS puts large, offsetting weights on correlated ones.

Regularization is a haircut on every estimate, like a reserve against numbers you cannot fully audit. **Ridge** shrinks all coefficients and spreads weight across correlated signals; **lasso** sets weak ones to zero; **elastic net** mixes both. You accept a little bias for a large cut in variance, the error that dominates at this [signal-to-noise ratio](../../09-reference/glossary.md#signal-to-noise-ratio). Linear forecasts also decompose by signal for attribution and change little day to day, which keeps turnover down.

## Where it sits in the pipeline

```mermaid
flowchart LR
    D2["Feature engineering"] --> D3["Signal transforms<br/>rank, z-score, winsorize"]
    D3 --> F1["Linear model<br/>ridge, lasso, elastic net"]
    V1["Purged walk-forward CV"] -->|"choose lambda, window"| F1
    F1 --> F5["Alpha combination"]
    F1 --> D4["Signal evaluation<br/>IC, decay"]
    F5 --> P3["Optimizer with risk and costs"]
    style F1 fill:#ffd54f,stroke:#333
```

## The algorithm

1. **Features:** per date, rank or z-score each signal, winsorize, fill missing with 0 (the mean). Standardizing matters because the penalty is scale-dependent.
2. **Target:** forward [residual return](../../09-reference/glossary.md#residual-return) over the holding horizon *h*, winsorized or ranked.
3. **Scheme:** *pooled* (stack all dates) or *per-date* ([Fama–MacBeth](../../09-reference/glossary.md#fama-macbeth-regression): one cross-sectional regression per date, average the slopes).
4. **Shrink and choose λ:** walk-forward folds, training only on dates whose *h*-day labels end before each validation block; score mean daily [rank IC](../../09-reference/glossary.md#information-coefficient-ic).
5. **Refit** on a rolling or expanding window; forecast = signals × β.

```python
import numpy as np
import pandas as pd
# rank_target, fit_ridge, walk_forward_splits: Lab 12 core functions (same names and logic).
# zscore_xs, fama_macbeth, rank_ic and choose_lambda are sketches added here.

def zscore_xs(X):                          # X: (n_stocks, k) signals for ONE date
    X = (X - np.nanmean(X, 0)) / np.nanstd(X, 0)
    return np.nan_to_num(np.clip(X, -3, 3))     # winsorize at 3 sd; missing -> 0 (the mean)

def rank_target(ret, dates):               # per-date percentile rank of forward return, in [-0.5, 0.5]
    g = pd.Series(ret).groupby(dates)
    return ((g.rank() - 1) / (g.transform("count") - 1) - 0.5).to_numpy()

def fit_ridge(X, y, lam):                  # no intercept: X z-scored, y ranked per date (mean 0)
    return np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ y)

def walk_forward_splits(n_dates, n_folds=5, horizon=5):
    blocks = np.array_split(np.arange(n_dates), n_folds + 1)
    for test in blocks[1:]:                # train only on dates whose label ends before the test block
        yield np.arange(0, test[0] - horizon + 1), test

def fama_macbeth(Xs, ys):
    # one OLS per date; the slopes' time series is each signal's daily "factor return"
    B = np.array([np.linalg.lstsq(X, y, rcond=None)[0] for X, y in zip(Xs, ys)])
    return B.mean(0), B.mean(0) / (B.std(0, ddof=1) / np.sqrt(len(B)))   # mean slope, t-stat

def rank_ic(pred, y):
    return np.corrcoef(pred.argsort().argsort(), y.argsort().argsort())[0, 1]

def choose_lambda(Xs, ys, lams, n_folds=5, horizon=5):
    # Xs[t]: (n_stocks, k) z-scored signals; ys[t]: rank_target of date t's forward residual return
    score = {lam: [] for lam in lams}
    for tr, te in walk_forward_splits(len(Xs), n_folds, horizon):
        Xtr, ytr = np.vstack([Xs[t] for t in tr]), np.concatenate([ys[t] for t in tr])
        for lam in lams:                   # Lab 12 fixes lam = 0.1 x training rows instead
            b = fit_ridge(Xtr, ytr, lam)
            score[lam] += [rank_ic(Xs[t] @ b, ys[t]) for t in te]
    return max(lams, key=lambda lam: np.mean(score[lam]))   # best mean daily rank IC

# Daily step on date t (expanding window; labels known for dates <= t - horizon):
# beta = fit_ridge(np.vstack(Xs[:t - horizon + 1]), np.concatenate(ys[:t - horizon + 1]), lam_star)
# forecast_t = zscore_xs(raw_signals_t) @ beta
```

## Worked example with numbers

Illustrative. Two standardized reversal signals with correlation 0.8 and ICs of 0.030 and 0.026.

**OLS:** Σ⁻¹ = (1/0.36)·[[1, −0.8], [−0.8, 1]] = 2.78·[[1, −0.8], [−0.8, 1]].
β₁ = 2.78 × (0.030 − 0.8 × 0.026) = 0.0256; β₂ = 2.78 × (0.026 − 0.8 × 0.030) = 0.0056.
In-sample R² = 0.030 × 0.0256 + 0.026 × 0.0056 = **0.091%**, versus 0.030² = 0.090% for the first signal alone.

**Noise:** with ~10,000 effectively independent observations, each IC has standard error ≈ 0.010, so each OLS coefficient has ≈ √2.78 × 0.010 = **0.0167**, larger than β₂ itself.

**Ridge, λ = 1 (correlation units):** (Σ + I)⁻¹ = (1/3.36)·[[2, −0.8], [−0.8, 2]].
β₁ = (2 × 0.030 − 0.8 × 0.026)/3.36 = 0.0117; β₂ = (2 × 0.026 − 0.8 × 0.030)/3.36 = 0.0083.
Standard error = √0.184 × 0.010 = **0.0043**, four times smaller: a sliver of in-sample fit buys stable coefficients.

## Key parameters and how practitioners tune them

- **λ:** grid over 4–6 orders of magnitude; take the best validation rank IC or the largest λ within one standard error of it (the ESL rule).
- **Ridge vs lasso:** many weak, correlated signals favor ridge; many candidates with few real ones favor lasso `[Lore]`.
- **Window:** rolling 1–3 years (or 6–24-month half-lives) for short-horizon books, expanding for slow fundamental signals `[Lore]`; GKX refit annually on an expanding window `[Verified]`.
- **Weights:** √(market cap) or inverse residual variance, so microcaps don't dominate `[Lore]`.

## Textbook version vs what firms actually do

- **Fama–MacBeth as a diagnostic:** built to test asset pricing models ([Fama & MacBeth 1973](https://doi.org/10.1086/260061)). In practice each day's slope is the return of a unit-exposure portfolio in that signal, i.e. the signal's P&L series; Barra-style [risk models](../d-portfolio-construction/risk-models.md) run the same regressions `[Verified]` (MSCI USE4).
- **Shrinkage matters:** in [GKX 2020](https://doi.org/10.1093/rfs/hhaa009), OLS on ~900 predictors had *negative* out-of-sample R². Penalized and reduced-rank linear models recovered roughly 0.1–0.3% per month, versus 0.16% for a three-characteristic OLS and 0.33–0.40% for trees and nets `[Verified]`.
- **Lasso at high frequency:** Chinco, Clark-Joseph & Ye (2019) ran lasso on lagged one-minute returns of all NYSE stocks and found sparse, short-lived predictors that improved out-of-sample fit `[Verified]`.
- **Contested:** Kelly, Malamud & Zhou (2024) argue heavily over-parameterized ridge models *improve* market timing; the claim is debated.
- Many books still combine alphas linearly, with nonlinear models in short-horizon sleeves `[Lore]`.

## How to tell if it's working

- Out-of-sample rank IC (mean, t-stat, by year) beats the best single signal on folds the λ search never touched.
- Out-of-sample R² against a zero forecast (the GKX convention), not the historical mean.
- IC vs log λ is hump-shaped; coefficients keep their signs across refits.
- Out-of-sample IC below half of in-sample IC signals overfitting `[Lore]`. In [Lab 12](https://github.com/FrankHuang94/quant_trading_claude/tree/main/labs/12-alpha-combination-purged-cv), ridge kept all of it; GBDT kept 28% (synthetic lab result).

## Failure modes and pitfalls

- **Overlapping labels:** consecutive 5-day forward returns share 4 days, so random K-fold leaks ([time-series CV](../c-validation-and-backtesting/time-series-cross-validation.md)).
- **Full-sample standardization** is [look-ahead bias](../../09-reference/glossary.md#look-ahead-bias).
- **Outliers:** one +300% microcap day can set an OLS coefficient.
- **Stale coefficients** after regime breaks ([regime detection](regime-detection.md)).
- **Tuning on the test set:** a λ × window × horizon grid is a [multiple-testing](../c-validation-and-backtesting/overfitting-and-multiple-testing.md) problem.

## How practitioners talk about it

- "We ridge everything; OLS weights on correlated alphas are noise." → Unshrunk collinear coefficients are unstable.
- "The FM t-stat is 2.1, but half of it is 2009." → Significance comes from one period.
- "Pick lambda on rank IC, not R²." → Rank IC resists outliers and matches how forecasts are used.
- "Lasso keeps swapping the two value signals." → L1 picks arbitrarily among near-duplicates, adding turnover.
- "Twenty bps of daily R² is a good model, not a bad one." → Tiny per-stock fit; the Sharpe comes from breadth.

## Questions you could ask a quant about this

1. Pooled or per-date, and how do you weight observations? (basic)
2. Raw, residual or ranked target, over what horizon? (basic)
3. How do you choose the penalty, and on what metric? (informed)
4. Do you smooth coefficients across refits? (informed)
5. How much IC does the combination add over the best single signal? (sharp)
6. When did a nonlinear model last beat your linear one after costs? 🔒 (sharp)

## Go deeper

<details markdown="1">
<summary>Math: ridge, lasso, Fama–MacBeth, out-of-sample R²</summary>

Ridge (Gaussian prior on β):

$$
\hat\beta_{\text{ridge}} = (X^\top X + \lambda I)^{-1} X^\top y
$$

Lasso with orthonormal $X$ soft-thresholds OLS: $\hat\beta_j = \operatorname{sign}(b_j)(\lvert b_j\rvert - \lambda/2)_+$.

Fama–MacBeth: $\hat\gamma_t = (X_t^\top X_t)^{-1} X_t^\top r_{t+1}$, $\bar\gamma = \tfrac{1}{T}\sum_t \hat\gamma_t$, $\text{se} = \text{sd}(\hat\gamma_t)/\sqrt{T}$ (Newey–West if horizons overlap).

$R^2_{oos} = 1 - \sum (r - \hat r)^2 / \sum r^2$. For one standardized predictor $R^2 \approx \text{IC}^2$: daily ICs of 0.02–0.05 mean R² of 0.04–0.25% `[Estimate]`.

Cost: $O(nk^2 + k^3)$; one eigendecomposition serves the whole λ grid.

</details>

## Related pages

- [Tree ensembles](tree-ensembles.md) · [Neural nets and sequence models](neural-nets-and-sequence-models.md)
- [Alpha combination and ensembling](alpha-combination-and-ensembling.md)
- [Signal transforms](../a-data-and-signals/signal-transforms.md) · [Evaluating signals](../a-data-and-signals/evaluating-signals.md)
- [Cross-sectional alpha and neutralization](../../02-strategies/d-mid-frequency-alpha/cross-sectional-alpha-and-neutralization.md)

## Sources

- [Verified] Gu, S., Kelly, B. & Xiu, D. (2020). "Empirical Asset Pricing via Machine Learning." *Review of Financial Studies* 33(5), 2223–2273. <https://doi.org/10.1093/rfs/hhaa009> (accessed 2026-11)
- [Verified] Fama, E. F. & MacBeth, J. D. (1973). "Risk, Return, and Equilibrium: Empirical Tests." *Journal of Political Economy* 81(3), 607–636. <https://doi.org/10.1086/260061> (accessed 2026-11)
- [Verified] Hoerl, A. E. & Kennard, R. W. (1970). "Ridge Regression: Biased Estimation for Nonorthogonal Problems." *Technometrics* 12(1), 55–67. <https://doi.org/10.1080/00401706.1970.10488634> (accessed 2026-11)
- [Verified] Tibshirani, R. (1996). "Regression Shrinkage and Selection via the Lasso." *Journal of the Royal Statistical Society B* 58(1), 267–288. <https://doi.org/10.1111/j.2517-6161.1996.tb02080.x> (accessed 2026-11)
- [Verified] Zou, H. & Hastie, T. (2005). "Regularization and Variable Selection via the Elastic Net." *Journal of the Royal Statistical Society B* 67(2), 301–320. <https://doi.org/10.1111/j.1467-9868.2005.00503.x> (accessed 2026-11)
- [Verified] Chinco, A., Clark-Joseph, A. D. & Ye, M. (2019). "Sparse Signals in the Cross-Section of Returns." *Journal of Finance* 74(1), 449–492. <https://doi.org/10.1111/jofi.12733> (accessed 2026-11)
- [Verified] Kelly, B., Malamud, S. & Zhou, K. (2024). "The Virtue of Complexity in Return Prediction." *Journal of Finance* 79(1), 459–503. <https://doi.org/10.1111/jofi.13298> (accessed 2026-11)
- [Verified] MSCI (2011). "Barra US Equity Model (USE4)" fact sheet. <https://www.msci.com/documents/10199/242721/Barra_US_Equity_Model_USE4.pdf> (accessed 2026-11)
- [Verified] Hastie, T., Tibshirani, R. & Friedman, J. (2009). *The Elements of Statistical Learning*, 2nd ed., Springer (ch. 3 and 7). <https://hastie.su.domains/ElemStatLearn/> (accessed 2026-11)
