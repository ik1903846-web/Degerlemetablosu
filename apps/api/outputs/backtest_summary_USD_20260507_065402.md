# REELDEĞER USD-Basis Backtest — 20260507_065402

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
| konservatif | zero | +1290.73% | +173.04% | +74.05%/yr | +23.55%/yr | 0.35 | -27.13% |
| konservatif | realistic | +1258.68% | +166.75% | +73.20%/yr | +22.94%/yr | 0.34 | -27.45% |
| dengeli | zero | +1144.55% | +144.34% | +70.03%/yr | +20.69%/yr | 0.32 | -26.73% |
| dengeli | realistic | +1115.92% | +138.72% | +69.20%/yr | +20.10%/yr | 0.30 | -26.93% |
| agresif | zero | +1048.00% | +125.39% | +67.17%/yr | +18.66%/yr | 0.29 | -26.64% |
| agresif | realistic | +1021.61% | +120.21% | +66.35%/yr | +18.08%/yr | 0.28 | -26.84% |

## USD-Basis Verdict (vs Triple Benchmark)

- **vs XU100:** Δ cumulative +61.57pp, Δ annualized +7.16pp/yr → **OUTPERFORM**
- **vs XU030:** Δ cumulative +52.18pp, Δ annualized +5.95pp/yr → **OUTPERFORM**
- **vs SPY:** Δ cumulative +96.71pp, Δ annualized +12.15pp/yr → **OUTPERFORM**

## Damodaran Lesson #7 Reinforce

> 'Backtest reporting must be currency-consistent. TL nominal returns
> hide TL devaluation effects. USD-basis is the proper benchmark for
> active management value-add measurement (ADR-002).'
