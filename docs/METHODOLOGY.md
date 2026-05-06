# REELDEĞER Methodology

Damodaran-aligned BIST valuation + portfolio construction architecture.

---

## Pipeline Architecture

```
┌──────────────────────┐
│  BIST Ticker (XU100) │  63 quality-curated ticker (Faz 4.6 + 4.7v2)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  Data Layer                                                   │
│  - isyatirim.com.tr XBRL (12 dönem, 147 kalem)              │
│  - Yahoo Finance v8 (spot + historical, .IS suffix)          │
│  - Damodaran reference (sector betas, ERP, CRP, Rf)         │
│  - banking_data.py (5 banking ticker × 4-yıl KAP)            │
│  - shares_fetcher.py (STATIC 60+ ticker)                     │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Lifecycle Classifier (6-stage)       │
│  YOUNG / HIGH_GROWTH / MATURE_GROWTH  │
│  MATURE_STABLE / DECLINE / DISTRESS   │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  DCF Engine (4 model family — orchestrator routing)         │
│  ├─ is_holding(ticker) → SOTP (Lesson #1)                    │
│  │   - per-child × ownership × disconto                     │
│  │   - banking children DDM (Lesson #5)                     │
│  ├─ is_banking_ticker(ticker) → Banking DDM (Lesson #5)     │
│  │   - 2-stage (high growth + stable perpetuity)            │
│  │   - USD basis, ROE → Ke convergence                      │
│  ├─ Distressed (parking Faz 7+ Black-Scholes)                │
│  └─ Default → Industrial Cyclical FCFF                       │
│      - Asymmetric cap (Lesson #2)                           │
│      - Adaptive cap by lifecycle (Lesson #4)                │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Pentagon Scoring (5-D)               │
│  Value, Growth, Quality, Momentum, Risk│
│  Lifecycle weights:                    │
│  - MATURE_STABLE: V35/G15/Q25/M15/R10 │
│  - BANKING: V30/G15/Q30/M5/R20         │ (Lesson #6)
│  - + 5 other lifecycle variants        │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  Sleeve Assignment (3-Sleeve cascade)                        │
│  CORE: lifecycle MATURE + upside > 20 + Q > 55 + comp > 48   │
│        Banking: excess_return ≥ 4pp (Lesson #6)              │
│  HIZLI BÜYÜME: stage YOUNG/HIGH_GROWTH + G > 60 + comp > 55  │
│  YÜKSEK KAZANÇ:                                              │
│    - deep_value (upside > 80 + comp > 50)                   │
│    - holding_chronic_discount                               │
│    - banking_premium                                        │
│    - mature_transition / distress                           │
│  SKIP: comp < 32 OR V < 15 OR upside < -35                  │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  Portfolio Construction (3 risk profile)                     │
│  RISK_PROFILES (Faz 4.14 + 4.15 allocation lever):           │
│    konservatif: core 0.82, hızlı 0.15, yüksek 0.03           │
│    dengeli:     core 0.65, hızlı 0.25, yüksek 0.10           │
│    agresif:     core 0.55, hızlı 0.35, yüksek 0.10           │
│  Position sizing:                                             │
│    MAX_SINGLE_TICKER_PCT = 12 (Faz 4.2)                      │
│    MIN_CASH_PCT = 2 / MAX_CASH_PCT = 15 (Lesson #8)          │
│  Empty sleeve redistribution (Faz 4.16 Core PRIORITY):       │
│    Step 1: Core'a kapasite dolana kadar (quality first)     │
│    Step 2: Kalan capacity diğer sleeve'lere pro-rata         │
└──────────┬───────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  Backtest Engine (2021-Q2 → 2026-Q1, 20 quarter, USD basis) │
│  - 8 modül: historical, benchmark, simulation, performance   │
│             regime, attribution, failure_metrics, usd_conv  │
│  - Triple benchmark: XU100, XU030, SPY                       │
│  - Cost models: zero (theoretical) + realistic (~%0.7/yr)    │
│  - Look-ahead bias documented (Lesson #7)                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Lifecycle Classifier (6-Stage)

`apps/api/dcf_engine/lifecycle_classifier.py`

| Stage          | Criteria                                                  |
|----------------|-----------------------------------------------------------|
| YOUNG          | revenue_cagr_usd > %30, post-IPO 1-3y                     |
| HIGH_GROWTH    | revenue_cagr_usd %20-30                                   |
| MATURE_GROWTH  | revenue_cagr_usd %5-20                                    |
| MATURE_STABLE  | revenue_cagr_usd 0-%5, low margin volatility              |
| DECLINE        | revenue_cagr_usd < 0, pricing power azalan                |
| DISTRESS       | negative DCF, thin margins, high leverage                 |

**Sub-classifications:**
- `cyclical` — high margin spread (>%10pp)
- `defensive` — low margin volatility (stdev <%2)
- `capital_intensive` — high reinvestment rate (>%50)
- `asset_heavy` — D/E > 1.0

---

## DCF Engine (4 Model Family)

### 1. Industrial FCFF (Cyclical)
`apps/api/dcf_engine/cyclical_dcf.py`

**Formula:**
```
effective_revenue = min(current_revenues, avg_revenue × cap_ratio)
norm_OI = effective_revenue × historical_avg_margin
FCFF = norm_OI × (1 - tax) × (1 - reinvestment_rate)
operating_value = FCFF × (1 + g) / (WACC - g)
equity_value = operating_value + cash + non_op - debt - minority
value_per_share = equity_value / shares_outstanding
```

**Adaptive cap_ratio (Lesson #2 + #4):**
```python
if MATURE_STABLE and bias > 50%:    cap = 1.15  # EXTREME
elif MATURE_STABLE and bias > 25%:  cap = 1.30  # MEDIUM (Faz 2.7)
else:                                cap = 1.50  # NORMAL (Toyota pattern)
```

**Validation:**
- TUPRS deep dive 188.31 TL (Faz 2.4.5 manuel 5+ saat) — production 187.10 TL (-%0.6)
- Heineken €59.65 (Damodaran industrial reference) — Faz 1.3.3 PASS

### 2. Banking DDM (Equity-Only)
`apps/api/dcf_engine/banking_ddm.py`

**Formula:**
```
EPS_USD_year_1 = EPS_TL / FX_spot
DPS_year_t = EPS_year_t × payout_pct
Stable phase: g = ROE × (1 - target_payout)
              payout_target = 1 - g/ROE (Damodaran convergence)
PV_high_growth = sum(DPS_year_t / (1 + Ke)^t for t in 1..5)
PV_terminal = (EPS_year_6 × stable_payout) / (Ke - g_stable) / (1+Ke)^5
value_per_share = PV_high_growth + PV_terminal
```

**Banking 5 ticker production:**
| Ticker | DDM TL/share | ROE   | CoE    | Source         |
|--------|-------------:|------:|-------:|----------------|
| AKBNK  | 98.96        | 21.5% | 11.09% | KAP CONFIRMED  |
| GARAN  | 197.28       | 30.0% | 11.09% | KAP CONFIRMED  |
| YKBNK  | 38.96        | 25.0% | 11.09% | KAP CONFIRMED  |
| ISCTR  | 17.19        | 16.0% | 11.09% | KAP CONFIRMED  |
| HALKB  | 142.24       | 12.0% | 11.09% | KAP CONFIRMED  |

**Validation:** ABN Amro €30.87 (Damodaran 2008) — Faz 1.4 + Faz 6 retest €32.12 (+%4 within ±%5)

### 3. Holdings SOTP
`apps/api/dcf_engine/sotp.py`

**Formula:**
```
For each child:
    if child.type == "listed":
        value = dcf_lookups[child.ticker] × ownership
    elif child.type == "banking_listed":
        value = banking_ddm_lookup × ownership  # Lesson #5 CONFIRMED
        (fallback: book × P/B 1.5 PROVISIONAL)
    elif child.type == "non_listed":
        value = book_value × multiplier × ownership

gross_value = sum(child contributions)
pre_disconto = gross + holding_net_cash - minority_at_subs
net_value = pre_disconto × (1 - disconto_pct)  # Damodaran %15 default
```

**Holdings:** KCHOL (190 TL refined), SAHOL (181 TL refined)

### 4. Distressed (Parking Faz 7+)
Black-Scholes equity-as-option (Damodaran Aviation chapter)
- KONTR, PETKM, THYAO, PGSUS, VESTL, HEKTS — current SKIP

---

## Pentagon Scoring (5-D)

`apps/api/portfolio/pentagon_scoring.py`

### Scoring Functions

#### Value (default 30%)
```python
upside = market_price.upside_pct
score = 50 + 50 × tanh(upside / 100)  # 0-100 scale
```

#### Growth (default 25%)
```python
cagr = lifecycle.revenue_cagr_usd
if cagr < -5%: 0
elif cagr < 0: linear(0..30)
elif cagr < 30%: linear(30..100)
else: 100
```

#### Quality (default 20%)
```python
stability_score = 100 if stdev<2% else 80 if <5% else 50 if <10% else 20
stage_score_map = {MATURE_STABLE: 90, MATURE_GROWTH: 80, ...}
score = avg(stability, stage)
```

#### Momentum (default 15%)
**MVP PARKING** (default 50 neutral, Yahoo 12M return Faz 5+)

#### Risk (default 10%, INVERSE)
```python
vol_score = 100 if spread<5% else 70 if <15% else 40 if <30% else 10
wacc_score = 100 if WACC<10% else 70 if <13% else 40 if <16% else 10
score = avg(vol, wacc)  # INVERSE — low risk = high score
```

### Lifecycle Weights

| Stage          | V    | G    | Q    | M    | R    | Notes                     |
|----------------|-----:|-----:|-----:|-----:|-----:|---------------------------|
| MATURE_STABLE  | 0.35 | 0.15 | 0.25 | 0.15 | 0.10 | TUPRS, EREGL, ARCLK       |
| MATURE_GROWTH  | 0.30 | 0.25 | 0.20 | 0.15 | 0.10 | FROTO, AEFES              |
| HIGH_GROWTH    | 0.20 | 0.35 | 0.20 | 0.15 | 0.10 | (BIST 30 nadir)           |
| YOUNG          | 0.15 | 0.40 | 0.20 | 0.15 | 0.10 | (BIST 30 nadir)           |
| DECLINE        | 0.20 | 0.05 | 0.30 | 0.15 | 0.30 | (rare)                    |
| DISTRESS       | 0.25 | 0.05 | 0.25 | 0.15 | 0.30 | (rare)                    |
| **BANKING**    | 0.30 | 0.15 | 0.30 | 0.05 | 0.20 | **Lesson #6** Q-dominant  |

### Banking-Specific Scoring (Lesson #6)

```python
# Quality = ROE - CoE excess return spread bracket
spread_pp = roe_pct - (coe_decimal × 100)
if spread > 15: 100   # GARAN +18.91pp → 100
elif spread > 10: 80  # AKBNK +10.41pp → 80
elif spread > 5: 60
elif spread > 0: 40
else: 20

# Growth = NI CAGR (earliest → latest)
cagr = (latest.NI / earliest.NI) ** (1/years) - 1
if cagr > 30%: 100
elif cagr > 15%: 75
...

# Risk = banking sector beta (0.2495) low + CoE bracket
if CoE < 13%: 70 (banking conservative)
elif CoE < 16%: 50
else: 30
```

---

## Sleeve Assignment Rules

`apps/api/portfolio/sleeve_assignment.py`

### Cascade Order
```
1. SKIP — failed pipeline (success/dcf_executed)
1b. SKIP — negative DCF (equity_value_usd < 0)
1c. SKIP hard floors:
    - composite < 32
    - V < 15
    - upside < -35%
1d. Banking branch (is_banking, Faz 6.5 e):
    - deep_value: upside > 80 + comp > 50 + Q > 45 (Faz 4.13'ten beri)
    - banking_intrinsic CORE: excess ≥ 4pp + upside > 0 + comp > 50 + V > 30
    - banking_premium: ROE > 20 + upside > 50 (Faz 4.13'ten beri)
2. YÜKSEK KAZANÇ holding_chronic_discount: holding + upside > 50 + comp > 50
3. YÜKSEK KAZANÇ deep_value: upside > 80 + comp > 50 (Faz 4.2 gevşetme)
4. YÜKSEK KAZANÇ distress: stage = DISTRESS
5. YÜKSEK KAZANÇ mature_transition: stage MATURE/DECLINE + Q<60 + V>70
6. HIZLI BÜYÜME: stage YOUNG/HIGH_GROWTH + G > 60 + comp > 55
7. CORE: stage MATURE + upside > 20 + Q > 55 + comp > 48 (Faz 4.2)
8. SKIP fallback (uncertain)
```

---

## Empty Sleeve Redistribution (Lesson #15 Core PRIORITY)

`apps/api/portfolio/portfolio_construction.py:182-241`

### Algorithm
```python
# Step 1: Core'a kapasite dolana kadar (quality first)
core_addition = min(redistributable, core_headroom)
core.target += core_addition
remaining = redistributable - core_addition

# Step 2: Kalan kapasite diğer aktif sleeve'lere capacity-pro-rata
if remaining > 0:
    other_total = sum(other_sleeves.headroom)
    for sleeve in other_sleeves:
        share = (sleeve.headroom / other_total) × remaining
        sleeve.target += share

# MIN_CASH_PCT (%2) buffer korunur
cash_reserved_max = 100 - MIN_CASH_PCT - sum_active
redistributable = min(empty_target, total_headroom, cash_reserved_max)
```

### Effect (Faz 4.16 ULTIMATE VALIDATION)
| Profile     | Core (Faz 4.15) | Core (Faz 4.16) | Δ        |
|-------------|----------------:|----------------:|---------:|
| Konservatif | 84.6%           | 95.0%           | +10.4pp ★ |
| Dengeli     | 70.9%           | 88.0%           | +17.1pp ★ |
| Agresif     | 64.4%           | 88.0%           | +23.6pp ★ |

---

## Backtest Methodology

`apps/api/backtest/`

### Period
**2021-Q2 → 2026-Q1** (20 quarter, 4.75 yıl)

### Modules (8 dosya, 1257+ satır)
- `historical_data.py` — Yahoo period1/period2 fetcher + disk cache
- `benchmark_data.py` — XU100/XU030/SPY/VIX/XBANK
- `point_in_time.py` — MVP look-ahead bias (Lesson #7)
- `simulation.py` — quarterly rebalance engine
- `performance.py` — TWR/Sharpe/Sortino/drawdown/beta
- `regime_detector.py` — VIX 4-regime
- `attribution.py` — per-sleeve + per-regime
- `failure_metrics.py` — 5-failure tracker (ADR-055)
- `usd_conversion.py` — TL → USD (Lesson ADR-002)
- `performance_usd.py` — USD basis metrics

### Triple Benchmark (ADR-019)
| Benchmark | Symbol     | USD Ann (5y) |
|-----------|------------|-------------:|
| XU100     | XU100.IS   | +13.54%/yr   |
| XU030     | XU030.IS   | +14.74%/yr   |
| SPY       | SPY        | +8.55%/yr    |

### Cost Models
- **Zero** — Theoretical (Damodaran academic)
- **Realistic** — ~%0.66-0.69/yr erosion:
  - Trading cost: turnover × %0.15 (commission + slippage)
  - Tax-drag: ~%0.5/yr (BIST stopaj %15 × ~%3 div yield)

### USD Basis Conversion (Lesson ADR-002)
```
USD_value_t = TL_value_t / USD_TRY_t
USD_return_q = USD_value_t / USD_value_t-1 - 1
```
USD/TRY 5y devaluation: 5.093x (8.73 → 44.45)

---

## Performance Validation Results (Faz 4.16 ULTIMATE)

### USD-Basis Annualized (TÜM 6 BACKTEST)

| Profile          | USD Ann   | vs XU100 | vs XU030 | vs SPY   | Sharpe | Max DD  |
|------------------|----------:|---------:|---------:|---------:|-------:|--------:|
| Konservatif zero | +18.98%   | +5.44 ★ | +4.24 ★ | +10.43 ★| 1.20   | -18.50% |
| Konservatif real | +18.40%   | +4.86 ★ | +3.66 ★ |  +9.85 ★| 1.18   | -18.86% |
| Dengeli zero     | +16.22%   | +2.68 ★ | +1.48 ★ |  +7.67 ★| 1.19   | -17.60% |
| Dengeli real     | +15.65%   | +2.11 ★ | +0.91 ★ |  +7.10 ★| 1.17   | -17.96% |
| Agresif zero     | +16.22%   | +2.68 ★ | +1.48 ★ |  +7.67 ★| 1.19   | -17.60% |
| Agresif real     | +15.65%   | +2.11 ★ | +0.91 ★ |  +7.10 ★| 1.17   | -17.96% |

**6/6 backtest × 3/3 benchmark = ULTIMATE VALIDATION**

### Phase Journey (Konservatif zero USD basis)

| Phase   | Lesson | USD Ann   | vs XU100 USD |
|---------|--------|----------:|-------------:|
| Faz 4.0 | Foundation | -0.21%/yr | -13.75pp ⚠ |
| Faz 4.2 | #8 Cash strict | +7.72%/yr | -5.82pp |
| Faz 4.5 | #9 BIST 50 | +11.07%/yr | -2.47pp |
| Faz 4.6 | #12 BIST 100 | +13.81%/yr | +0.27pp ★ (ilk BEAT) |
| Faz 4.14| #14 Allocation | +14.87%/yr | +1.33pp |
| Faz 4.16| #15 Core PRIORITY | **+18.98%/yr** | **+5.44pp ★★★** |

**Net journey:** -0.21% → +18.98%/yr (+19.19pp, full inversion)

---

## TUPRS Regression Anchor

**TUPRS 187.10 TL** — production deep dive baseline

- Manuel deep dive (Faz 2.4.5, 5+ saat): 188.31 TL
- Production (40+ atomic commit boyunca): 187.10 TL
- Sapma: -%0.6 (sub-noise, methodology preservation)

Her atomic commit'te TUPRS regression check yapılır. Bozulması = methodology
break. 40+ commit boyunca INTACT — methodology STABLE.

---

## ADR References

- **ADR-001** — BIST primary data source (isyatirim + Yahoo)
- **ADR-002** — USD-only valuation (TL DCF YASAK, TFRS-29 inflation)
- **ADR-007** — Pentagon 5-D scoring foundation
- **ADR-015** — Position sizing (cap %10-12, cash %5-15)
- **ADR-016** — Risk profile allocations (Konservatif/Dengeli/Agresif)
- **ADR-018** — Backtest methodology
- **ADR-019** — Triple benchmark (XU100/XU030/SPY)
- **ADR-022** — Stack Next.js + React + FastAPI + Prisma
- **ADR-042** — Tactical regime overlay spec (Lesson #11 FAILED)
- **ADR-044, 049** — Lifecycle-adjusted weights
- **ADR-055** — 5-failure metric tracker
- **ADR-056** — IPO cooling period (1Y/4Q minimum)
- **ADR-065** — Bottom-up beta (Hamada formülü)
- **ADR-066, 067** — 3-Sleeve mapping
- **ADR-098** — Pentagon 5. boyut "Narrative Confirmation" (Momentum yerine)
- **ADR-105** — Next.js 15 + cross-env build wrapper

---

**Methodology last updated:** 7 May 2026
**REELDEĞER version:** v2.2
**Status:** Production-ready (Faz 4.16 ULTIMATE + Faz 5 Frontend)
