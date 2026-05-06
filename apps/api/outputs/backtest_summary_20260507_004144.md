# REELDEĞER Backtest Summary — 20260507_004144

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
| konservatif | zero | +1062.79% | +67.62%/yr | 53.08% | 1.20 | 4.92 | -18.50% |
| konservatif | realistic | +1035.96% | +66.79%/yr | 53.07% | 1.18 | 4.86 | -18.86% |
| dengeli | zero | +939.98% | +63.72%/yr | 50.23% | 1.19 | 4.87 | -17.60% |
| dengeli | realistic | +916.01% | +62.92%/yr | 50.22% | 1.17 | 4.81 | -17.96% |
| agresif | zero | +858.91% | +60.95%/yr | 48.19% | 1.18 | 4.84 | -16.95% |
| agresif | realistic | +836.82% | +60.16%/yr | 48.19% | 1.17 | 4.77 | -17.31% |

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
| normal | 12 | +276.17% | +13.57% |
| moderate_stress | 4 | +96.31% | +22.64% |
| significant_stress | 1 | +3.36% | +3.36% |
| panic | 2 | +36.25% | +18.15% |

## Per-Sleeve Attribution (Dengeli zero)

| Sleeve | Avg Weight | Contribution |
|--------|-----------:|-------------:|
| core | 8.00% | +216.77% |
| yuksek_kazanc | 2.00% | +76.34% |

## 5-Failure Metric Tracker (realistic cost)

| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |
|---------|------------:|---------:|---------:|---------:|-------|
| konservatif | 0.05%/yr [OK] | 32.59%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| dengeli | 0.05%/yr [OK] | 30.48%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| agresif | 0.04%/yr [OK] | 29.11%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |

## Bias Note

> MVP backtest: bugünkü Pentagon scores 20 quarter sabit. Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction muhafazakâr (bugünkü intrinsic değerler conservative). Faz 4.5'te historical Pentagon recompute ile bias kaldırılır.
