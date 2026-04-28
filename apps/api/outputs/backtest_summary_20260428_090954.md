# REELDEĞER Backtest Summary — 20260428_090954

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
| konservatif | zero | +625.11% | +51.75%/yr | 35.64% | 1.34 | 6.85 | -15.70% |
| konservatif | realistic | +608.81% | +51.03%/yr | 35.63% | 1.32 | 6.61 | -16.05% |
| dengeli | zero | +689.59% | +54.50%/yr | 36.99% | 1.37 | 5.52 | -17.20% |
| dengeli | realistic | +671.78% | +53.76%/yr | 36.99% | 1.35 | 5.44 | -17.55% |
| agresif | zero | +660.65% | +53.29%/yr | 36.26% | 1.36 | 4.57 | -17.63% |
| agresif | realistic | +643.42% | +52.55%/yr | 36.26% | 1.34 | 4.50 | -17.99% |

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
| normal | 12 | +219.59% | +11.28% |
| moderate_stress | 4 | +80.04% | +18.21% |
| significant_stress | 1 | +5.73% | +5.73% |
| panic | 2 | +29.79% | +14.92% |

## Per-Sleeve Attribution (Dengeli zero)

| Sleeve | Avg Weight | Contribution |
|--------|-----------:|-------------:|
| core | 10.69% | +178.12% |
| yuksek_kazanc | 6.63% | +65.60% |

## 5-Failure Metric Tracker (realistic cost)

| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |
|---------|------------:|---------:|---------:|---------:|-------|
| konservatif | 0.03%/yr [OK] | 17.20%/yr [PASSIVE] | 0.50%/yr [OK] | 10.37% [IDEAL] | STABLE (MVP fixed weights) |
| dengeli | 0.03%/yr [OK] | 19.56%/yr [PASSIVE] | 0.50%/yr [OK] | 2.69% [OVERINVESTED] | STABLE (MVP fixed weights) |
| agresif | 0.03%/yr [OK] | 20.56%/yr [PASSIVE] | 0.50%/yr [OK] | 2.00% [OVERINVESTED] | STABLE (MVP fixed weights) |

## Bias Note

> MVP backtest: bugünkü Pentagon scores 20 quarter sabit. Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction muhafazakâr (bugünkü intrinsic değerler conservative). Faz 4.5'te historical Pentagon recompute ile bias kaldırılır.
