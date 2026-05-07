# REELDEĞER USD-Basis Backtest — 20260507_083554

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
| konservatif | zero | +1418.64% | +198.16% | +77.31%/yr | +25.86%/yr | 0.31 | -34.99% |
| konservatif | realistic | +1381.74% | +190.91% | +76.39%/yr | +25.21%/yr | 0.30 | -35.20% |
| dengeli | zero | +1294.80% | +173.84% | +74.16%/yr | +23.62%/yr | 0.29 | -34.48% |
| dengeli | realistic | +1261.10% | +167.23% | +73.27%/yr | +22.99%/yr | 0.28 | -34.69% |
| agresif | zero | +1210.80% | +157.35% | +71.90%/yr | +22.02%/yr | 0.28 | -34.13% |
| agresif | realistic | +1179.24% | +151.16% | +71.02%/yr | +21.39%/yr | 0.27 | -34.33% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative +91.07pp, Δ annualized +10.09pp/yr → **OUTPERFORM**
- **vs XU030:** Δ cumulative +81.68pp, Δ annualized +8.88pp/yr → **OUTPERFORM**
- **vs SPY:** Δ cumulative +126.21pp, Δ annualized +15.08pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
