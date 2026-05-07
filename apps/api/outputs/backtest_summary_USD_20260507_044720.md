# REELDEĞER USD-Basis Backtest — 20260507_044720

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
| konservatif | zero | +1068.95% | +129.50% | +67.80%/yr | +19.11%/yr | 0.28 | -29.44% |
| konservatif | realistic | +1041.98% | +124.21% | +66.98%/yr | +18.53%/yr | 0.27 | -29.75% |
| dengeli | zero | +945.16% | +105.20% | +63.89%/yr | +16.34%/yr | 0.24 | -28.65% |
| dengeli | realistic | +921.08% | +100.47% | +63.09%/yr | +15.77%/yr | 0.23 | -28.96% |
| agresif | zero | +863.45% | +89.16% | +61.11%/yr | +14.36%/yr | 0.21 | -28.10% |
| agresif | realistic | +841.27% | +84.80% | +60.32%/yr | +13.80%/yr | 0.20 | -28.40% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative +22.42pp, Δ annualized +2.80pp/yr → **OUTPERFORM**
- **vs XU030:** Δ cumulative +13.03pp, Δ annualized +1.60pp/yr → **OUTPERFORM**
- **vs SPY:** Δ cumulative +57.56pp, Δ annualized +7.79pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
