# REELDEĞER USD-Basis Backtest — 20260428_134251

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
| konservatif | zero | +841.49% | +84.85% | +60.33%/yr | +13.81%/yr | 0.22 | -28.52% |
| konservatif | realistic | +820.06% | +80.64% | +59.55%/yr | +13.26%/yr | 0.20 | -29.20% |
| dengeli | zero | +665.25% | +50.24% | +53.48%/yr | +8.95%/yr | 0.12 | -28.18% |
| dengeli | realistic | +647.77% | +46.81% | +52.74%/yr | +8.42%/yr | 0.11 | -28.85% |
| agresif | zero | +642.67% | +45.81% | +52.52%/yr | +8.26%/yr | 0.10 | -28.63% |
| agresif | realistic | +625.63% | +42.46% | +51.78%/yr | +7.74%/yr | 0.09 | -29.30% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative -32.53pp, Δ annualized -4.59pp/yr → **UNDERPERFORM**
- **vs XU030:** Δ cumulative -41.92pp, Δ annualized -5.79pp/yr → **UNDERPERFORM**
- **vs SPY:** Δ cumulative +2.61pp, Δ annualized +0.40pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
