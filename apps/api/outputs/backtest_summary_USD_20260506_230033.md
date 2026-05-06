# REELDEĞER USD-Basis Backtest — 20260506_230033

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
| konservatif | zero | +884.11% | +93.21% | +61.83%/yr | +14.87%/yr | 0.22 | -28.26% |
| konservatif | realistic | +861.43% | +88.76% | +61.04%/yr | +14.31%/yr | 0.21 | -28.57% |
| dengeli | zero | +683.92% | +53.91% | +54.27%/yr | +9.50%/yr | 0.12 | -26.73% |
| dengeli | realistic | +665.87% | +50.36% | +53.51%/yr | +8.97%/yr | 0.11 | -27.04% |
| agresif | zero | +613.89% | +40.16% | +51.26%/yr | +7.37%/yr | 0.08 | -26.65% |
| agresif | realistic | +597.45% | +36.93% | +50.52%/yr | +6.84%/yr | 0.07 | -26.96% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative -28.87pp, Δ annualized -4.04pp/yr → **UNDERPERFORM**
- **vs XU030:** Δ cumulative -38.26pp, Δ annualized -5.24pp/yr → **UNDERPERFORM**
- **vs SPY:** Δ cumulative +6.27pp, Δ annualized +0.95pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
