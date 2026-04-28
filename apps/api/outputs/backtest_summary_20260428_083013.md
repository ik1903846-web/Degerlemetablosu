# REELDEĞER Backtest Summary — 20260428_083013

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
| konservatif | zero | +404.37% | +40.59%/yr | 28.34% | 1.29 | 7.23 | -12.10% |
| konservatif | realistic | +392.95% | +39.91%/yr | 28.33% | 1.27 | 7.10 | -12.46% |
| dengeli | zero | +422.65% | +41.65%/yr | 28.81% | 1.31 | 6.57 | -12.80% |
| dengeli | realistic | +410.81% | +40.96%/yr | 28.80% | 1.28 | 6.45 | -13.15% |
| agresif | zero | +319.92% | +35.27%/yr | 24.37% | 1.28 | 4.74 | -11.69% |
| agresif | realistic | +310.32% | +34.61%/yr | 24.37% | 1.26 | 4.69 | -12.05% |

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
| normal | 12 | +159.41% | +8.97% |
| moderate_stress | 4 | +56.60% | +13.35% |
| significant_stress | 1 | +4.75% | +4.75% |
| panic | 2 | +22.83% | +11.50% |

## Per-Sleeve Attribution (Dengeli zero)

| Sleeve | Avg Weight | Contribution |
|--------|-----------:|-------------:|
| core | 9.60% | +159.12% |
| yuksek_kazanc | 3.00% | +29.68% |

## 5-Failure Metric Tracker (realistic cost)

| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |
|---------|------------:|---------:|---------:|---------:|-------|
| konservatif | 0.02%/yr [OK] | 14.50%/yr [PASSIVE] | 0.50%/yr [OK] | 30.00% [ELEVATED] | STABLE (MVP fixed weights) |
| dengeli | 0.02%/yr [OK] | 15.21%/yr [PASSIVE] | 0.50%/yr [OK] | 27.39% [ELEVATED] | STABLE (MVP fixed weights) |
| agresif | 0.02%/yr [OK] | 15.02%/yr [PASSIVE] | 0.50%/yr [OK] | 35.00% [UNDERINVESTED] | STABLE (MVP fixed weights) |

## Bias Note

> MVP backtest: bugünkü Pentagon scores 20 quarter sabit. Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction muhafazakâr (bugünkü intrinsic değerler conservative). Faz 4.5'te historical Pentagon recompute ile bias kaldırılır.
