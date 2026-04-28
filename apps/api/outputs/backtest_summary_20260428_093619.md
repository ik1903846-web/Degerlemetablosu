# REELDEĞER Backtest Summary — 20260428_093619

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
| konservatif | zero | +738.78% | +56.48%/yr | 38.28% | 1.37 | 9.22 | -9.87% |
| konservatif | realistic | +719.93% | +55.73%/yr | 38.28% | 1.35 | 9.09 | -10.24% |
| dengeli | zero | +728.33% | +56.07%/yr | 37.02% | 1.41 | 6.91 | -9.80% |
| dengeli | realistic | +709.64% | +55.32%/yr | 37.02% | 1.39 | 6.85 | -9.94% |
| agresif | zero | +714.88% | +55.53%/yr | 36.08% | 1.43 | 5.47 | -11.54% |
| agresif | realistic | +696.42% | +54.78%/yr | 36.08% | 1.41 | 5.39 | -11.67% |

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
| normal | 12 | +229.47% | +11.52% |
| moderate_stress | 4 | +89.57% | +19.67% |
| significant_stress | 1 | +4.03% | +4.03% |
| panic | 2 | +27.48% | +13.78% |

## Per-Sleeve Attribution (Dengeli zero)

| Sleeve | Avg Weight | Contribution |
|--------|-----------:|-------------:|
| core | 8.38% | +175.23% |
| yuksek_kazanc | 3.87% | +73.32% |

## 5-Failure Metric Tracker (realistic cost)

| Profile | Trading Cost | Turnover | Tax Drag | Cash Avg | Style |
|---------|------------:|---------:|---------:|---------:|-------|
| konservatif | 0.03%/yr [OK] | 19.39%/yr [PASSIVE] | 0.50%/yr [OK] | 1.76% [OVERINVESTED] | STABLE (MVP fixed weights) |
| dengeli | 0.03%/yr [OK] | 20.77%/yr [PASSIVE] | 0.50%/yr [OK] | 2.00% [OVERINVESTED] | STABLE (MVP fixed weights) |
| agresif | 0.03%/yr [OK] | 21.95%/yr [PASSIVE] | 0.50%/yr [OK] | 2.00% [OVERINVESTED] | STABLE (MVP fixed weights) |

## Bias Note

> MVP backtest: bugünkü Pentagon scores 20 quarter sabit. Geçmiş quarter performansı 'ileri-bakış' içerir; bias direction muhafazakâr (bugünkü intrinsic değerler conservative). Faz 4.5'te historical Pentagon recompute ile bias kaldırılır.
