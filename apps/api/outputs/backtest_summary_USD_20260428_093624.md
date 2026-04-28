# REELDEĞER USD-Basis Backtest — 20260428_093624

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
| konservatif | zero | +738.78% | +64.68% | +56.48%/yr | +11.07%/yr | 0.18 | -25.11% |
| konservatif | realistic | +719.93% | +60.98% | +55.73%/yr | +10.54%/yr | 0.17 | -25.80% |
| dengeli | zero | +728.33% | +62.63% | +56.07%/yr | +10.78%/yr | 0.18 | -24.91% |
| dengeli | realistic | +709.64% | +58.96% | +55.32%/yr | +10.25%/yr | 0.16 | -25.60% |
| agresif | zero | +714.88% | +59.99% | +55.53%/yr | +10.40%/yr | 0.17 | -24.93% |
| agresif | realistic | +696.42% | +56.36% | +54.78%/yr | +9.87%/yr | 0.16 | -25.62% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative -20.15pp, Δ annualized -2.76pp/yr → **UNDERPERFORM**
- **vs XU030:** Δ cumulative -29.54pp, Δ annualized -3.96pp/yr → **UNDERPERFORM**
- **vs SPY:** Δ cumulative +14.99pp, Δ annualized +2.23pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
