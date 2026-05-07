# REELDEĞER USD-Basis Backtest — 20260508_010316

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
| konservatif | zero | +525.72% | +22.85% | +47.12%/yr | +4.43%/yr | 0.01 | -30.13% |
| konservatif | realistic | +511.10% | +19.98% | +46.39%/yr | +3.91%/yr | -0.00 | -30.32% |
| dengeli | zero | +527.12% | +23.12% | +47.18%/yr | +4.48%/yr | 0.01 | -30.21% |
| dengeli | realistic | +512.46% | +20.24% | +46.45%/yr | +3.96%/yr | -0.00 | -30.41% |
| agresif | zero | +528.07% | +23.31% | +47.23%/yr | +4.51%/yr | 0.01 | -30.27% |
| agresif | realistic | +513.37% | +20.42% | +46.50%/yr | +3.99%/yr | -0.00 | -30.47% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative -59.65pp, Δ annualized -9.06pp/yr → **UNDERPERFORM**
- **vs XU030:** Δ cumulative -69.04pp, Δ annualized -10.27pp/yr → **UNDERPERFORM**
- **vs SPY:** Δ cumulative -24.51pp, Δ annualized -4.07pp/yr → **UNDERPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
