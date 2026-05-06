# REELDEĞER Backtest Summary — 20260506_230032

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
| konservatif | zero | +884.11% | +61.83%/yr | 48.84% | 1.18 | 4.85 | -17.16% |
| konservatif | realistic | +861.43% | +61.04%/yr | 48.84% | 1.17 | 4.78 | -17.52% |
| dengeli | zero | +683.92% | +54.27%/yr | 43.27% | 1.16 | 4.73 | -15.39% |
| dengeli | realistic | +665.87% | +53.51%/yr | 43.27% | 1.14 | 4.66 | -15.75% |
| agresif | zero | +613.89% | +51.26%/yr | 41.10% | 1.15 | 4.65 | -14.65% |
| agresif | realistic | +597.45% | +50.52%/yr | 41.09% | 1.13 | 4.58 | -15.01% |

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
| normal | 12 | +217.73% | +11.57% |
| moderate_stress | 4 | +82.45% | +19.48% |
| significant_stress | 1 | +3.44% | +3.44% |
| panic | 2 | +30.73% | +15.40% |

## Per-Sleeve Attribution (Dengeli zero)

| Sleeve | Avg Weight | Contribution |
|--------|-----------:|-------------:|
| core | 6.45% | +174.66% |
| yuksek_kazanc | 2.00% | +76.34% |

## 5-Failure Metric Tracker (realistic cost)

| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |
|---------|------------:|---------:|---------:|---------:|-------|
| konservatif | 0.04%/yr [OK] | 29.54%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| dengeli | 0.04%/yr [OK] | 26.01%/yr [PASSIVE] | 0.50%/yr [OK] | 0.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| agresif | 0.04%/yr [OK] | 24.86%/yr [PASSIVE] | 0.50%/yr [OK] | 0.63% [OVERINVESTED] | STABLE (MVP fixed weights) |

## Bias Note

> MVP backtest: bugünkü Pentagon scores 20 quarter sabit. Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction muhafazakâr (bugünkü intrinsic değerler conservative). Faz 4.5'te historical Pentagon recompute ile bias kaldırılır.
