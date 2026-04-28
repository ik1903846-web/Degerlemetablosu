# REELDEĞER Backtest Summary — 20260428_140021

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
| konservatif | zero | +854.11% | +60.78%/yr | 48.07% | 1.18 | 4.83 | -16.91% |
| konservatif | realistic | +832.13% | +59.99%/yr | 48.06% | 1.16 | 4.77 | -17.27% |
| dengeli | zero | +626.59% | +51.82%/yr | 41.46% | 1.15 | 4.68 | -14.81% |
| dengeli | realistic | +609.85% | +51.08%/yr | 41.46% | 1.14 | 4.61 | -15.17% |
| agresif | zero | +587.37% | +50.05%/yr | 41.09% | 1.12 | 4.36 | -15.05% |
| agresif | realistic | +571.48% | +49.32%/yr | 41.09% | 1.10 | 4.29 | -15.41% |

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
| normal | 12 | +203.59% | +11.05% |
| moderate_stress | 4 | +78.80% | +18.65% |
| significant_stress | 1 | +3.49% | +3.49% |
| panic | 2 | +29.34% | +14.71% |

## Per-Sleeve Attribution (Dengeli zero)

| Sleeve | Avg Weight | Contribution |
|--------|-----------:|-------------:|
| core | 6.03% | +163.43% |
| yuksek_kazanc | 2.01% | +76.63% |

## 5-Failure Metric Tracker (realistic cost)

| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |
|---------|------------:|---------:|---------:|---------:|-------|
| konservatif | 0.04%/yr [OK] | 29.02%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| dengeli | 0.04%/yr [OK] | 25.01%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| agresif | 0.04%/yr [OK] | 25.33%/yr [PASSIVE] | 0.50%/yr [OK] | 2.00% [OVERINVESTED] | STABLE (MVP fixed weights) |

## Bias Note

> MVP backtest: bugünkü Pentagon scores 20 quarter sabit. Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction muhafazakâr (bugünkü intrinsic değerler conservative). Faz 4.5'te historical Pentagon recompute ile bias kaldırılır.
