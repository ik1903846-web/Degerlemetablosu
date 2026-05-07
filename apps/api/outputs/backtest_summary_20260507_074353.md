# REELDEĞER Backtest Summary — 20260507_074353

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
| konservatif | zero | +1392.48% | +76.66%/yr | 61.37% | 1.18 | 4.84 | -18.34% |
| konservatif | realistic | +1357.92% | +75.79%/yr | 61.37% | 1.17 | 4.78 | -18.48% |
| dengeli | zero | +1239.25% | +72.68%/yr | 58.30% | 1.18 | 4.80 | -17.38% |
| dengeli | realistic | +1208.30% | +71.83%/yr | 58.30% | 1.16 | 4.75 | -17.52% |
| agresif | zero | +1137.73% | +69.83%/yr | 56.11% | 1.17 | 4.77 | -16.70% |
| agresif | realistic | +1109.16% | +69.00%/yr | 56.11% | 1.16 | 4.71 | -16.84% |

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
| normal | 12 | +283.59% | +14.42% |
| moderate_stress | 4 | +142.98% | +29.99% |
| significant_stress | 1 | +6.26% | +6.26% |
| panic | 2 | +35.23% | +17.44% |

## Per-Sleeve Attribution (Dengeli zero)

| Sleeve | Avg Weight | Contribution |
|--------|-----------:|-------------:|
| core | 6.29% | +223.88% |
| yuksek_kazanc | 2.00% | +110.27% |

## 5-Failure Metric Tracker (realistic cost)

| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |
|---------|------------:|---------:|---------:|---------:|-------|
| konservatif | 0.06%/yr [OK] | 37.27%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| dengeli | 0.05%/yr [OK] | 35.01%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| agresif | 0.05%/yr [OK] | 33.45%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |

## Bias Note

> MVP backtest: bugünkü Pentagon scores 20 quarter sabit. Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction muhafazakâr (bugünkü intrinsic değerler conservative). Faz 4.5'te historical Pentagon recompute ile bias kaldırılır.
