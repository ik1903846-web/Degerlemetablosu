# REELDEĞER Backtest Summary — 20260428_142515

**Period:** 2021-06-30 → 2026-03-31 (20 quarter-end)
**Look-ahead bias:** `True` (Damodaran Lesson #7)

## Triple Benchmark

| Benchmark | Cumulative | Annualized | Vol | Sharpe | Max DD |
|-----------|-----------:|-----------:|----:|-------:|-------:|
| XU100 | +830.94% | +59.95%/yr | 41.95% | 1.33 | -12.64% |
| XU030 | +878.78% | +61.65%/yr | 40.53% | 1.42 | -10.94% |
| SPY | +47.64% | +8.55%/yr | 15.21% | 0.30 | -24.80% |

## Portfolio Performance (3 profile × 2 cost)

| Profile | Cost | Cumulative | Annualized | Vol | Sharpe | Sortino | Max DD |
|---------|------|-----------:|-----------:|----:|-------:|--------:|-------:|
| konservatif | zero | +744.61% | +56.71%/yr | 47.38% | 1.11 | 4.70 | -16.29% |
| konservatif | realistic | +725.07% | +55.94%/yr | 47.38% | 1.10 | 4.63 | -16.65% |
| dengeli | zero | +575.80% | +49.52%/yr | 41.50% | 1.10 | 4.56 | -14.64% |
| dengeli | realistic | +560.18% | +48.79%/yr | 41.50% | 1.08 | 4.49 | -15.01% |
| agresif | zero | +564.74% | +49.00%/yr | 41.51% | 1.08 | 4.31 | -15.96% |
| agresif | realistic | +549.34% | +48.27%/yr | 41.51% | 1.07 | 4.24 | -16.32% |

## Regime Calendar (VIX-based)

| Quarter-End | VIX | Regime |
|-------------|----:|--------|
| 2021-06-30 | 15.83 | normal |
| 2021-09-30 | 23.14 | moderate_stress |
| 2021-12-31 | 17.22 | normal |
| 2022-03-31 | 20.56 | moderate_stress |
| 2022-06-30 | 28.71 | significant_stress |
| 2022-09-30 | 31.62 | panic |
| 2022-12-31 | 21.67 | moderate_stress |
| 2023-03-31 | 18.70 | normal |
| 2023-06-30 | 13.59 | normal |
| 2023-09-30 | 17.52 | normal |
| 2023-12-31 | 12.45 | normal |
| 2024-03-31 | 13.01 | normal |
| 2024-06-30 | 12.44 | normal |
| 2024-09-30 | 16.73 | normal |
| 2024-12-31 | 17.35 | normal |
| 2025-03-31 | 22.28 | moderate_stress |
| 2025-06-30 | 16.73 | normal |
| 2025-09-30 | 16.28 | normal |
| 2025-12-31 | 14.95 | normal |
| 2026-03-31 | 30.61 | panic |

## Per-Regime Attribution (Dengeli zero)

| Regime | n | Cumulative | Avg/Q |
|--------|--:|-----------:|------:|
| normal | 12 | +193.11% | +10.79% |
| moderate_stress | 4 | +76.10% | +18.11% |
| significant_stress | 1 | +3.51% | +3.51% |
| panic | 2 | +26.49% | +13.35% |

## Per-Sleeve Attribution (Dengeli zero)

| Sleeve | Avg Weight | Contribution |
|--------|-----------:|-------------:|
| core | 5.65% | +159.72% |
| yuksek_kazanc | 2.09% | +72.37% |

## 5-Failure Metric Tracker (realistic cost)

| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |
|---------|------------:|---------:|---------:|---------:|-------|
| konservatif | 0.04%/yr [OK] | 28.31%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| dengeli | 0.04%/yr [OK] | 24.96%/yr [PASSIVE] | 0.50%/yr [OK] | 0.91% [OVERINVESTED] | STABLE (MVP fixed weights) |
| agresif | 0.04%/yr [OK] | 25.55%/yr [PASSIVE] | 0.50%/yr [OK] | 2.00% [OVERINVESTED] | STABLE (MVP fixed weights) |

## Bias Note

> MVP backtest: bugünkü Pentagon scores 20 quarter sabit. Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction muhafazakâr (bugünkü intrinsic değerler conservative). Faz 4.5'te historical Pentagon recompute ile bias kaldırılır.
