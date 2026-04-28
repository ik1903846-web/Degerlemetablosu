# REELDEĞER USD-Basis Backtest — 20260428_090958

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
| konservatif | zero | +625.11% | +42.36% | +51.75%/yr | +7.72%/yr | 0.10 | -29.20% |
| konservatif | realistic | +608.81% | +39.16% | +51.03%/yr | +7.20%/yr | 0.09 | -29.85% |
| dengeli | zero | +689.59% | +55.02% | +54.50%/yr | +9.67%/yr | 0.15 | -29.13% |
| dengeli | realistic | +671.78% | +51.53% | +53.76%/yr | +9.14%/yr | 0.14 | -29.79% |
| agresif | zero | +660.65% | +49.34% | +53.29%/yr | +8.81%/yr | 0.13 | -29.11% |
| agresif | realistic | +643.42% | +45.96% | +52.55%/yr | +8.29%/yr | 0.12 | -29.77% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative -27.75pp, Δ annualized -3.87pp/yr → **UNDERPERFORM**
- **vs XU030:** Δ cumulative -37.14pp, Δ annualized -5.07pp/yr → **UNDERPERFORM**
- **vs SPY:** Δ cumulative +7.39pp, Δ annualized +1.12pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
