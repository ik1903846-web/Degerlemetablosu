# REELDEĞER USD-Basis Backtest — 20260428_142516

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
| konservatif | zero | +744.61% | +65.82% | +56.71%/yr | +11.23%/yr | 0.15 | -28.73% |
| konservatif | realistic | +725.07% | +61.99% | +55.94%/yr | +10.69%/yr | 0.14 | -29.41% |
| dengeli | zero | +575.80% | +32.68% | +49.52%/yr | +6.13%/yr | 0.05 | -28.86% |
| dengeli | realistic | +560.18% | +29.61% | +48.79%/yr | +5.61%/yr | 0.04 | -29.53% |
| agresif | zero | +564.74% | +30.51% | +49.00%/yr | +5.77%/yr | 0.04 | -31.05% |
| agresif | realistic | +549.34% | +27.49% | +48.27%/yr | +5.25%/yr | 0.03 | -31.71% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative -50.09pp, Δ annualized -7.40pp/yr → **UNDERPERFORM**
- **vs XU030:** Δ cumulative -59.49pp, Δ annualized -8.61pp/yr → **UNDERPERFORM**
- **vs SPY:** Δ cumulative -14.96pp, Δ annualized -2.41pp/yr → **UNDERPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
