# REELDEĞER User Manual

BIST Damodaran-aligned valuation + portfolio construction platform.
Backend (FastAPI/Python) + Frontend (Streamlit dashboard).

---

## Quick Start

### 1. Backend (Valuation + Backtest)

```bash
cd apps/api
.venv/Scripts/python.exe scripts/test_orchestrator_live.py     # BIST 100 batch
.venv/Scripts/python.exe scripts/run_portfolio_pipeline.py     # 3 risk profile
.venv/Scripts/python.exe scripts/run_backtest_2021_2026.py     # TL backtest
.venv/Scripts/python.exe scripts/run_backtest_usd_basis.py     # USD backtest
```

Output: `apps/api/outputs/` (JSON + CSV + MD).

### 2. Frontend (Streamlit Dashboard)

```bash
cd apps/frontend
../api/.venv/Scripts/python.exe -m streamlit run app.py
# Browser açılır: http://localhost:8501
```

İlk kurulumda:
```bash
pip install -r requirements.txt
```

---

## System Requirements

- **Python:** 3.12.x (apps/api/.venv kurulu)
- **Streamlit:** 1.32+
- **Plotly:** 5.20+
- **Pandas:** 2.2+
- **Internet:** Yahoo Finance API (price data) + isyatirim.com.tr (XBRL)
- **Disk:** ~500MB (cache + outputs)

---

## Investment Workflow (5 Adım)

### Adım 1 — Refresh Data
Latest price + fundamentals fetch (15-30 saniye):
```bash
.venv/Scripts/python.exe scripts/test_orchestrator_live.py
```
Output: `apps/api/outputs/bist_batch_LIVE_<timestamp>.json` (63 ticker scan)

### Adım 2 — Build Portfolio Plan
3 risk profile (Konservatif/Dengeli/Agresif) plan oluştur:
```bash
.venv/Scripts/python.exe scripts/run_portfolio_pipeline.py
```
Output: `apps/api/outputs/portfolio_plan_<profile>_<timestamp>.{csv,json}`

### Adım 3 — Profile Selection
Frontend'de profile selector'dan seç:
- **Konservatif** — Core %82, Hızlı %15, Yüksek %3 (US ann +18.98%/yr ★)
- **Dengeli** — Core %65, Hızlı %25, Yüksek %10 (USD +16.22%/yr)
- **Agresif** — Core %55, Hızlı %35, Yüksek %10 (USD +16.22%/yr)

(Faz 4.14 + 4.16 allocation lever sonrası targets.)

### Adım 4 — Monitor & Backtest
20-quarter (4.75 yıl) backtest sonuçlarını gözlemle:
```bash
.venv/Scripts/python.exe scripts/run_backtest_2021_2026.py
.venv/Scripts/python.exe scripts/run_backtest_usd_basis.py
```
Frontend `📈 Backtest` sayfasında USD/TL toggle, benchmark karşılaştırma.

### Adım 5 — Periodic Rebalance
- **Quarterly schedule** (Mart, Haziran, Eylül, Aralık sonu)
- Adım 1-4'ü tekrarla
- Position changes: yeni weight'leri aktarma (manuel broker entry)
- Cash %2-15 band'ında tut (Faz 4.2 Lesson #8)

---

## Profile Selection Guide

| Profile     | Core | Hızlı | Yüksek | USD Ann   | Max DD  | Sharpe | Önerilen           |
|-------------|-----:|------:|-------:|----------:|--------:|-------:|---------------------|
| Konservatif | 82%  | 15%   | 3%     | +18.98%/y | -18.50% | 1.20   | Drawdown sensitive  |
| Dengeli     | 65%  | 25%   | 10%    | +16.22%/y | -17.60% | 1.19   | Default başlangıç   |
| Agresif     | 55%  | 35%   | 10%    | +16.22%/y | -17.60% | 1.19   | Higher conviction   |

**Not (Faz 4.16):** Dengeli ve Agresif identical sonuç (Yüksek target %10
her ikisinde, Core PRIORITY redistribution Core'u capacity dolana kadar
full doldurdu). Faz 4.17 differentiation parking.

---

## Frontend Pages Tour

### 🏠 Home (`app.py`)
- Hero metrics: Konservatif USD ann + vs XU100/SPY benchmark
- 3 profile USD performance table (6 backtest + 3 benchmark)
- 5 Lesson preview (top recent)
- Sidebar: navigation, universe stats

### 📊 Portfolio (`pages/1_Portfolio.py`)
- Profile selector (sidebar)
- Hero: position count, core %, Yüksek %, cash
- Sleeve allocation donut pie chart
- Pozisyonlar sortable table (ticker, sleeve, weight, composite, capital)
- Sleeve composite bar chart (color by sleeve)
- Pentagon radar chart (selected ticker, V/G/Q/M/R + composite)

### 📈 Backtest (`pages/2_Backtest.py`)
- Basis toggle USD/TL (sidebar)
- Hero: best profile USD ann, vs XU100/SPY
- 6 backtest × 3 benchmark comparison table
- USD annualized bar chart (with benchmark hline overlays)
- Cumulative wealth path line chart (selected profile vs benchmarks)

### 📚 Lessons (`pages/3_Lessons.py`)
- Filter: kategori (Pentagon/Banking/Portfolio/Methodology/Universe)
- Filter: status (VALIDATED/FALSIFIED/META-LESSON/ACKNOWLEDGED)
- 15 Lesson expandable cards (full content)
- Status badge (color-coded)
- Methodology pattern footer

---

## Output Files Reference

`apps/api/outputs/` dizininde tüm analiz sonuçları:

### Batch Results
- `bist_batch_LIVE_<timestamp>.csv` — flat ticker × DCF table
- `bist_batch_LIVE_<timestamp>.json` — full diagnostic (Pentagon, lifecycle, reasoning)

### Portfolio Plans
- `portfolio_plan_konservatif_<timestamp>.{csv,json}` — Konservatif positions
- `portfolio_plan_dengeli_<timestamp>.{csv,json}` — Dengeli positions
- `portfolio_plan_agresif_<timestamp>.{csv,json}` — Agresif positions

### Backtest Results
- `backtest_results_<timestamp>.{csv,json}` — TL basis (3 profile × 2 cost = 6 run)
- `backtest_summary_<timestamp>.md` — TL basis human-readable summary
- `backtest_results_USD_<timestamp>.{csv,json}` — USD basis (ADR-002)
- `backtest_summary_USD_<timestamp>.md` — USD basis summary
- `backtest_results_TACTICAL_<timestamp>.{csv,json}` — tactical comparison (Lesson #11)

### Frontend Auto-Loads
Streamlit `utils/data_loader.py` latest dosyaları otomatik picks:
- `load_latest_portfolio_plan(profile)` → en yeni profile plan
- `load_latest_usd_backtest()` → en yeni USD backtest
- `load_latest_batch()` → en yeni Pentagon scores

---

## Backend CLI Commands

### Full Pipeline (Önerilen, Faz 4.18 race-free)
```bash
.venv/Scripts/python.exe scripts/run_pipeline_full.py
# Sequential 4-step:
#   1/4 BIST batch (orchestrator live)
#   2/4 Portfolio plan (3 risk profile)
#   3/4 TL backtest (20-quarter)
#   4/4 USD backtest (--tl-results <fresh path>, race-free)

.venv/Scripts/python.exe scripts/run_pipeline_full.py --skip-batch
# 3-step (batch atlandı, hızlı re-run mevcut latest batch ile)
```

Race-free by design (Damodaran Lesson #18 actionable):
- File-based handoff with auto-detect fresh outputs
- Step 4 USD backtest explicit `--tl-results <step3 fresh TL>`
- Logs: `C:/tmp/pipeline_<step>_<timestamp>.log`

### Tek Ticker Analiz
```python
# apps/api/scripts/test_orchestrator.py içinde:
from dcf_engine.orchestrator import analyze_ticker
import asyncio

report = asyncio.run(analyze_ticker("TUPRS", market_price_tl=274.0))
print(report.value_per_share_tl)  # 187.10 TL
print(report.upside_pct)           # -31.71%
print(report.damodaran_verdict)    # SAT
```

### BIST 100 Batch
```bash
.venv/Scripts/python.exe scripts/test_orchestrator_live.py
# 63 ticker, 3-phase flow (industrial + banking + holdings)
# Duration: ~85-130s
```

### Portfolio Pipeline
```bash
.venv/Scripts/python.exe scripts/run_portfolio_pipeline.py
# Pentagon → Sleeve → Portfolio (3 profile)
# Reads latest bist_batch_LIVE_*.json
# Writes portfolio_plan_*_<ts>.{csv,json}
```

### Backtest (TL + USD)
```bash
.venv/Scripts/python.exe scripts/run_backtest_2021_2026.py
.venv/Scripts/python.exe scripts/run_backtest_usd_basis.py
# 20 quarter × 3 profile × 2 cost = 6 backtest run
# USD basis ADR-002 compliant
```

### Tactical Comparison (Lesson #11 reference)
```bash
.venv/Scripts/python.exe scripts/run_backtest_tactical.py
# Static vs Tactical regime overlay
# Note: tactical NOT EFFECTIVE BIST period (Lesson #11)
```

---

## Periodic Rebalance Process

### Quarterly Schedule
- **Q1 sonu** (31 Mart) — Pentagon refresh, profile rebalance
- **Q2 sonu** (30 Haziran)
- **Q3 sonu** (30 Eylül)
- **Q4 sonu** (31 Aralık)

### Rebalance Steps
1. **Tarih:** Quarter sonu son trading day, market kapandıktan sonra
2. **Refresh:** `test_orchestrator_live.py` (15-30s)
3. **Pipeline:** `run_portfolio_pipeline.py` (3 profile yeni weights)
4. **Compare:** Frontend'de mevcut vs yeni weights (Δ position size)
5. **Execute:** Manuel broker entry (Δ > %1pp olan pozisyonlar)
6. **Cash band:** %2-15 strict (Faz 4.2 Lesson #8)
7. **Document:** Rebalance log (broker confirmation + portfolio_plan_*_<ts>.json)

### Turnover Expectation
- Backtest annualized turnover: ~%16/yr (PASSIVE, Damodaran disipline)
- Trading cost: ~%0.02/yr (BIST commission %0.05-0.1 + slippage minimal)
- Tax-drag: ~%0.5/yr (BIST stopaj %15 × ~%3 div yield)

---

## Troubleshooting (FAQ)

### S: Streamlit "ModuleNotFoundError: streamlit" veriyor
```bash
cd apps/frontend
../api/.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### S: "No items in response for SMRTG" hatası
- Cevap: SMRTG XBRL endpoint quirk (Faz 4.10+ debug parking)
- Geçici: Bu ticker drop, batch sürdürür (gracefully handled)
- Permanent fix: Faz 4.10 lifecycle classifier sub-stages

### S: TUPRS regression bozulmuş (≠ 187.10 TL)
- Cevap: Anchor 188.31 TL deep dive baseline (Faz 2.4.5)
- 187.10 ± 1.0 TL acceptable (sapma -%0.6 sub-noise)
- Eğer büyük sapma: `git log --grep TUPRS` ile son DCF değişimini kontrol et

### S: USD backtest farklı sonuç veriyor (Konservatif zero ≠ +18.98%)
- Cevap: Latest portfolio plan + latest backtest aynı zamandan olmalı
- Pipeline → Backtest sırayla çalıştır, ARA timestamp uyumsuzluğu çıkmasın

### S: Hızlı Büyüme sleeve hep boş
- Cevap: BIST 100'de gerçek young/high-growth firms az
- KCAER/CWENE/ENJSA mature_growth lifecycle'a düştü (4-yıl revenue CAGR declining)
- Faz 4.10 classifier sub-stages parking (early_growth detection)

### S: GitHub push "Repository not found"
- Cevap: Token expired veya repo private oldu
- Çözüm: `gh auth login` (browser OAuth, en temiz) veya yeni Personal Access Token

### S: Yeni ticker eklemek istiyorum (BIST 100 dışı)
1. `dcf_engine/batch_analyzer.py:BIST_100_ADDITIONS` listeye ekle
2. `data_layer/shares_fetcher.py:STATIC_SHARES_OUTSTANDING` shares ekle
3. isyatirim XBRL coverage probe (4-yıl en az gerekli)
4. Pipeline + backtest re-run

---

## Stack & Versions

```
Backend:
  Python 3.12.10
  FastAPI 0.136.1 (mevcut, frontend'de kullanılmıyor)
  pandas 3.0.2
  asyncpg 0.30.0
  httpx 0.27+

DCF Engine:
  Industrial FCFF (cyclical_dcf.py)
  Banking DDM (banking_ddm.py) — 2-stage
  Holdings SOTP (sotp.py)

Frontend:
  Streamlit 1.57+
  Plotly 6.7+
  Dark theme (#FFB700 primary)

External APIs:
  Yahoo Finance v8 (price + benchmarks + FX)
  isyatirim.com.tr (XBRL financial statements, XI_29 industrial)
  TCMB year-end FX (static fallback)

Validation:
  ABN Amro €30.87 (Damodaran banking, Faz 1)
  TUPRS deep dive 188.31 TL (Faz 2.4.5, 5+ saat manuel)
  Heineken €59.65 (Damodaran industrial, Faz 1)
  Toyota ¥4737 (Damodaran cyclical, Faz 1)
  Tube Industries ₹61.55 (Damodaran EM, Faz 1)
```

---

## Documentation Links

- **15 Damodaran Lessons:** `docs/DAMODARAN_LESSONS.md`
- **Methodology + Architecture:** `docs/METHODOLOGY.md`
- **Project README:** `README.md` (root)
- **Daily Progress:** `notes/kaldim.md` (in-project notebook)
- **Research Findings:** `apps/api/_research_findings/` (20 dosya)
- **ADR's:** `docs/ADR/`

---

**User Manual last updated:** 7 May 2026
**Project commit:** 120+
**Status:** Production-ready (Faz 4.16 ULTIMATE VALIDATION + Faz 5 Frontend)
