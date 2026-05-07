# REELDEĞER USD-Basis Backtest — 20260507_074353

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
| konservatif | zero | +1392.48% | +193.02% | +76.66%/yr | +25.40%/yr | 0.35 | -26.39% |
| konservatif | realistic | +1357.92% | +186.24% | +75.79%/yr | +24.78%/yr | 0.34 | -26.71% |
| dengeli | zero | +1239.25% | +162.94% | +72.68%/yr | +22.57%/yr | 0.32 | -25.72% |
| dengeli | realistic | +1208.30% | +156.86% | +71.83%/yr | +21.97%/yr | 0.31 | -26.04% |
| agresif | zero | +1137.73% | +143.00% | +69.83%/yr | +20.55%/yr | 0.30 | -25.24% |
| agresif | realistic | +1109.16% | +137.40% | +69.00%/yr | +19.96%/yr | 0.29 | -25.55% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative +80.16pp, Δ annualized +9.03pp/yr → **OUTPERFORM**
- **vs XU030:** Δ cumulative +70.77pp, Δ annualized +7.83pp/yr → **OUTPERFORM**
- **vs SPY:** Δ cumulative +115.30pp, Δ annualized +14.02pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
