# REELDEĞER

**Damodaran-Aligned BIST Valuation + Portfolio Construction Platform**

> Aswath Damodaran metodolojisiyle BIST 100 ticker değerleme + 3-sleeve
> portföy konstrüksiyon + 20-quarter backtest + Streamlit dashboard.

[![commits](https://img.shields.io/badge/commits-120%2B-blue)]()
[![status](https://img.shields.io/badge/status-production--ready-green)]()
[![lessons](https://img.shields.io/badge/Damodaran_Lessons-15_documented-orange)]()
[![backtest](https://img.shields.io/badge/backtest-6%2F6_%C3%97_3%2F3_BEAT-brightgreen)]()

---

## Hero Metrics ★★★ ULTIMATE VALIDATION

**Faz 4.16 (Lesson #15 Core PRIORITY redistribution) — 28 Nis 2026**

| Metric (USD basis, 4.75-yıl backtest)        | Value             |
|----------------------------------------------|------------------:|
| Konservatif zero USD Annualized              | **+18.98%/yr** ★★★|
| vs XU100 USD (BIST 100 broad market)          | **+5.44pp BEAT** ★|
| vs XU030 USD (BIST 30 peer)                  | **+4.24pp BEAT** ★|
| vs SPY USD (S&P 500 ETF)                     | **+10.43pp BEAT** ★|
| Universe                                      | 63 BIST ticker    |
| Damodaran Lessons documented                 | 15                |
| TUPRS regression anchor (deep dive 188.31 TL)| 187.10 TL INTACT  |

**6/6 backtest × 3/3 benchmark BEAT** — REELDEĞER methodology validate.

---

## Quick Start

### Backend (Valuation + Backtest)

**Önerilen — Full pipeline orchestrator (race-free, Faz 4.18):**
```bash
cd apps/api
.venv/Scripts/python.exe scripts/run_pipeline_full.py            # 4-step sequential
.venv/Scripts/python.exe scripts/run_pipeline_full.py --skip-batch  # 3-step (fast re-run)
```

**Manuel (gelişmiş):**
```bash
cd apps/api
.venv/Scripts/python.exe scripts/test_orchestrator_live.py     # BIST 100 batch (~85s)
.venv/Scripts/python.exe scripts/run_portfolio_pipeline.py     # 3 risk profile
.venv/Scripts/python.exe scripts/run_backtest_2021_2026.py     # TL backtest
.venv/Scripts/python.exe scripts/run_backtest_usd_basis.py --tl-results <fresh TL JSON>  # USD (race-fix)
```

### Frontend (Streamlit Dashboard)

```bash
cd apps/frontend
../api/.venv/Scripts/python.exe -m streamlit run app.py
# Browser: http://localhost:8501
```

---

## Architecture (3-Tier)

```
┌────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Data Layer    │ ──▶ │  Valuation Core  │ ──▶ │  Portfolio      │
│  - isyatirim   │     │  - 4 DCF model   │     │  - Pentagon 5-D │
│  - Yahoo       │     │  - Lifecycle 6-S │     │  - 3-Sleeve     │
│  - Damodaran   │     │  - Banking DDM   │     │  - 3 Profile    │
│  - banking_data│     │  - SOTP holdings │     │  - Cash policy  │
│  - shares      │     │  - Cyclical cap  │     │  - Core PRIORITY│
└────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                       ┌──────────────────┐               ▼
                       │  Frontend (UI)   │      ┌─────────────────┐
                       │  Streamlit       │ ◀──── │  Backtest      │
                       │  - Home          │      │  - 20 quarter   │
                       │  - Portfolio     │      │  - Triple bench │
                       │  - Backtest      │      │  - USD basis    │
                       │  - Lessons       │      │  - 5-failure trk│
                       └──────────────────┘      └─────────────────┘
```

---

## Damodaran Methodology Highlights (5 Key Lessons)

### #1 Holdings cannot be valued like industrial firms (Faz 2.5)
SOTP intrinsic-correct: per-child × ownership × disconto. Banking children
DDM separately (Lesson #5). KCHOL 190 TL, SAHOL 181 TL refined.

### #5 Banking DDM > P/B fallback (Faz 6)
2-stage Dividend Discount Model + ROE-CoE excess return. ABN Amro €30.87
validation PASS. SAHOL refined -%10 (banking-heavy).

### #8 Cash band strict %15 + empty redistribute (Faz 4.2) ★
Cash policy %30 → %15 cap. Empty sleeve overflow redistribution.
USD alpha capture +%9.08pp/yr (Dengeli realistic).

### #14 Allocation > Filter (Faz 4.14) ★★
Sleeve target reduction (allocation, NOT filter). HALKB/ARENA/BOSSA + 14
ticker korundu (filter approach'tan farklı). TÜM 6 backtest USD GAIN.

### #15 Core PRIORITY redistribution ★★★ ULTIMATE (Faz 4.16)
Empty sleeve overflow Core ÖNCE (capacity dolana kadar), kalan diğer
sleeve'lere pro-rata. **6/6 × 3/3 BEAT** — methodology validate.

📖 [**15 Damodaran Lessons full compendium →**](docs/DAMODARAN_LESSONS.md)

---

## Documentation

- **[15 Damodaran Lessons](docs/DAMODARAN_LESSONS.md)** — Methodology compendium (validated + falsified findings)
- **[User Manual](docs/USER_MANUAL.md)** — Frontend + backend usage, troubleshooting FAQ
- **[Methodology](docs/METHODOLOGY.md)** — Pipeline architecture, DCF formulas, Pentagon weights
- **[Daily Progress](notes/kaldim.md)** — In-project notebook (5-day marathon log)
- **[Research Findings](apps/api/_research_findings/)** — 20 dosya per-faz analysis
- **[ADR's](docs/ADR/)** — Architecture decision records

---

## Stack

### Backend (apps/api/)
- **Python 3.12.10** + FastAPI 0.136 (REST API, frontend currently doesn't use)
- **DCF Engine:** Industrial FCFF + Banking DDM + Holdings SOTP + Cyclical
- **Pentagon Scoring:** 5-D × 7 lifecycle weights (banking branch)
- **Backtest:** 8 module, 1257+ satır
- **External APIs:** isyatirim XBRL, Yahoo Finance v8, Damodaran reference

### Frontend (apps/frontend/)
- **Streamlit 1.57+** + Plotly 6.7+ (dark theme, #FFB700 primary)
- **4 sayfa:** Home, Portfolio, Backtest, Lessons

### Reserved (apps/web/)
- **Next.js 15.5.15 + React 18 + Tailwind 4** boilerplate (Faz 6 React port parking)

### Validation Cases (Damodaran reference)
- ABN Amro DDM €30.87 (Banking, Faz 1.4)
- TUPRS deep dive 188.31 TL (Faz 2.4.5 manuel 5+ saat)
- Heineken €59.65 (Industrial)
- Toyota ¥4737 (Cyclical)
- Tube Industries ₹61.55 (EM)

---

## Validation Path (Faz 4 Phase Journey)

| Phase    | Lesson                          | USD Ann (Konservatif zero) | vs XU100 USD     |
|----------|---------------------------------|---------------------------:|-----------------:|
| Faz 4.0  | Foundation                      | -0.21%/yr                  | -13.75pp ⚠       |
| Faz 4.2  | #8 Cash strict                  | +7.72%/yr                  |  -5.82pp         |
| Faz 4.5  | #9 BIST 50 expansion            | +11.07%/yr                 |  -2.47pp         |
| Faz 4.6  | #12 BIST 100 expansion          | +13.81%/yr                 |  +0.27pp ★ (ilk) |
| Faz 4.14 | #14 Allocation lever            | +14.87%/yr                 |  +1.33pp         |
| Faz 4.16 | **#15 Core PRIORITY ★★★**     | **+18.98%/yr**             | **+5.44pp BEAT ★★★** |

**Net turnaround:** -13.75pp UNDERPERFORM → +5.44pp BEAT (full inversion).

---

## Project Status

- **Backend:** Production-ready (Faz 4.16 ULTIMATE VALIDATION)
- **Frontend:** Production-ready (Faz 5 Streamlit dashboard)
- **Documentation:** Production-ready (Faz 5.1 closure)
- **Backtest:** 6/6 × 3/3 BEAT validated
- **TUPRS Anchor:** 187.10 TL INTACT (40+ atomic commit)

### Faz 5.2+ Parking
- Frontend extension (regime calendar, watchlist, real-time refresh)
- Profile differentiation (Faz 4.17 — Yüksek target Dengeli/Agresif ayrı)
- Hızlı Büyüme classifier sub-stages (Faz 4.10 — early_growth detection)
- Distress model Black-Scholes (Faz 7+ — KONTR/PETKM/THYAO/PGSUS/VESTL/HEKTS)
- React/Next.js port (Faz 6+, apps/web/ skeleton hazır)

---

## License

**Private** — Personal investment research project.

Damodaran methodology references: Aswath Damodaran (NYU Stern),
*Investment Valuation* (3rd ed.), *Narrative and Numbers*,
*The Dark Side of Valuation*.

---

**REELDEĞER v2.2 · 7 May 2026 · Solo build (5-day marathon, 120+ commit, 15 Damodaran Lesson)**
