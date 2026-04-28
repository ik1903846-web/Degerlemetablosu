# REELDEĞER USD-Basis Backtest — 20260428_085551

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
| konservatif | zero | +404.37% | -0.98% | +40.59%/yr | -0.21%/yr | -0.14 | -28.41% |
| konservatif | realistic | +392.95% | -3.22% | +39.91%/yr | -0.69%/yr | -0.16 | -29.05% |
| dengeli | zero | +422.65% | +2.61% | +41.65%/yr | +0.54%/yr | -0.11 | -28.42% |
| dengeli | realistic | +410.81% | +0.29% | +40.96%/yr | +0.06%/yr | -0.13 | -29.07% |
| agresif | zero | +319.92% | -17.56% | +35.27%/yr | -3.98%/yr | -0.29 | -27.81% |
| agresif | realistic | +310.32% | -19.44% | +34.61%/yr | -4.45%/yr | -0.31 | -28.46% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative -80.16pp, Δ annualized -12.99pp/yr → **UNDERPERFORM**
- **vs XU030:** Δ cumulative -89.55pp, Δ annualized -14.20pp/yr → **UNDERPERFORM**
- **vs SPY:** Δ cumulative -45.02pp, Δ annualized -8.00pp/yr → **UNDERPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
