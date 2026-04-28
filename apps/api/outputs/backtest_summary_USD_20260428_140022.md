# REELDEĞER USD-Basis Backtest — 20260428_140022

**Period:** 2021-06-30 → 2026-03-31 (4.75 yıl)
**ADR Reference:** ADR-002 (USD-only zorunlu, TL DCF yasak)
**FX devaluation:** 8.73 → 44.45 TL/USD = 5.093x (TL %80.4 lost vs USD)

## Triple Benchmark — TL vs USD

| Benchmark | TL Cum   | USD Cum | TL Ann   | USD Ann   | USD Sharpe | USD Max DD |
|-----------|---------:|--------:|---------:|----------:|-----------:|-----------:|
| XU100 | +830.94% | +82.77% | +59.95%/yr | +13.54%/yr | 0.23 | -24.91% |
| XU030 | +878.78% | +92.17% | +61.65%/yr | +14.74%/yr | 0.27 | -22.72% |
| SPY | +47.64% | +47.64% | +8.55%/yr | +8.55%/yr | 0.30 | -24.80% |

## Portfolio — TL vs USD

| Profile | Cost | TL Cum | USD Cum | TL Ann | USD Ann | USD Sharpe | USD DD |
|---------|------|-------:|--------:|-------:|--------:|-----------:|-------:|
| konservatif | zero | +854.11% | +87.32% | +60.78%/yr | +14.13%/yr | 0.21 | -28.04% |
| konservatif | realistic | +832.13% | +83.01% | +59.99%/yr | +13.57%/yr | 0.20 | -28.35% |
| dengeli | zero | +626.59% | +42.65% | +51.82%/yr | +7.77%/yr | 0.09 | -26.69% |
| dengeli | realistic | +609.85% | +39.37% | +51.08%/yr | +7.24%/yr | 0.08 | -26.88% |
| agresif | zero | +587.37% | +34.95% | +50.05%/yr | +6.51%/yr | 0.06 | -28.18% |
| agresif | realistic | +571.48% | +31.83% | +49.32%/yr | +5.99%/yr | 0.05 | -28.86% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative -40.12pp, Δ annualized -5.77pp/yr → **UNDERPERFORM**
- **vs XU030:** Δ cumulative -49.51pp, Δ annualized -6.98pp/yr → **UNDERPERFORM**
- **vs SPY:** Δ cumulative -4.98pp, Δ annualized -0.78pp/yr → **UNDERPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
