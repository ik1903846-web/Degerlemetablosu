# REELDEĞER USD-Basis Backtest — 20260507_052038

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
| konservatif | zero | +1230.92% | +161.30% | +72.45%/yr | +22.41%/yr | 0.34 | -26.82% |
| konservatif | realistic | +1200.25% | +155.28% | +71.61%/yr | +21.81%/yr | 0.33 | -27.13% |
| dengeli | zero | +1089.98% | +133.63% | +68.43%/yr | +19.56%/yr | 0.30 | -26.68% |
| dengeli | realistic | +1062.60% | +128.25% | +67.61%/yr | +18.98%/yr | 0.29 | -26.88% |
| agresif | zero | +996.96% | +115.37% | +65.57%/yr | +17.53%/yr | 0.27 | -26.59% |
| agresif | realistic | +971.74% | +110.42% | +64.76%/yr | +16.95%/yr | 0.26 | -26.79% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative +50.86pp, Δ annualized +6.02pp/yr → **OUTPERFORM**
- **vs XU030:** Δ cumulative +41.47pp, Δ annualized +4.82pp/yr → **OUTPERFORM**
- **vs SPY:** Δ cumulative +86.00pp, Δ annualized +11.01pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
