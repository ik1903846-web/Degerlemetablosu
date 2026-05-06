# REELDEĞER USD-Basis Backtest — 20260506_235052

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
| konservatif | zero | +1062.79% | +128.29% | +67.62%/yr | +18.98%/yr | 0.28 | -29.42% |
| konservatif | realistic | +1035.96% | +123.02% | +66.79%/yr | +18.40%/yr | 0.27 | -29.73% |
| dengeli | zero | +939.98% | +104.18% | +63.72%/yr | +16.22%/yr | 0.24 | -28.64% |
| dengeli | realistic | +916.01% | +99.48% | +62.92%/yr | +15.65%/yr | 0.23 | -28.95% |
| agresif | zero | +939.98% | +104.18% | +63.72%/yr | +16.22%/yr | 0.24 | -28.64% |
| agresif | realistic | +916.01% | +99.48% | +62.92%/yr | +15.65%/yr | 0.23 | -28.95% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative +21.41pp, Δ annualized +2.68pp/yr → **OUTPERFORM**
- **vs XU030:** Δ cumulative +12.01pp, Δ annualized +1.47pp/yr → **OUTPERFORM**
- **vs SPY:** Δ cumulative +56.55pp, Δ annualized +7.67pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
