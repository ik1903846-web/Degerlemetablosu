# REELDEĞER USD-Basis Backtest — 20260507_021119

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
| konservatif | zero | +1015.65% | +119.04% | +66.16%/yr | +17.95%/yr | 0.24 | -34.11% |
| konservatif | realistic | +989.42% | +113.89% | +65.33%/yr | +17.36%/yr | 0.23 | -34.76% |
| dengeli | zero | +910.97% | +98.49% | +62.75%/yr | +15.53%/yr | 0.21 | -33.91% |
| dengeli | realistic | +887.27% | +93.83% | +61.94%/yr | +14.95%/yr | 0.20 | -34.56% |
| agresif | zero | +840.92% | +84.73% | +60.31%/yr | +13.79%/yr | 0.18 | -33.78% |
| agresif | realistic | +818.90% | +80.41% | +59.51%/yr | +13.23%/yr | 0.17 | -34.42% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative +15.71pp, Δ annualized +1.99pp/yr → **OUTPERFORM**
- **vs XU030:** Δ cumulative +6.32pp, Δ annualized +0.78pp/yr → **OUTPERFORM**
- **vs SPY:** Δ cumulative +50.85pp, Δ annualized +6.98pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
