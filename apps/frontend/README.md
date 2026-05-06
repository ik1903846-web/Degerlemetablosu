# REELDEĞER Frontend (Streamlit Dashboard)

User-facing UI for REELDEĞER Damodaran-aligned BIST valuation platform.

## Setup

```bash
cd apps/frontend
pip install -r requirements.txt
```

(Veya `apps/api/.venv` zaten kurulu ise reuse: streamlit + plotly oraya
eklendi.)

## Run

```bash
cd apps/frontend
streamlit run app.py

# Veya tam path:
../api/.venv/Scripts/python.exe -m streamlit run app.py
```

Default URL: `http://localhost:8501`

## Sayfalar

- **🏠 Home** (`app.py`) — Hero metrics, 3 profile USD comparison, lesson preview
- **📊 Portfolio** (`pages/1_Portfolio.py`) — Profile detail, sleeve pie, Pentagon radar
- **📈 Backtest** (`pages/2_Backtest.py`) — USD/TL toggle, benchmark chart, wealth path
- **📚 Lessons** (`pages/3_Lessons.py`) — 15 Damodaran Lesson timeline (filtrable)

## Veri Kaynağı

`apps/api/outputs/` JSON dosyaları (cross-app, read-only):
- `portfolio_plan_{profile}_*.json` — 3 risk profile
- `backtest_results_*.json` — TL basis
- `backtest_results_USD_*.json` — USD basis (ADR-002)
- `bist_batch_LIVE_*.json` — Pentagon scores per ticker

`utils/data_loader.py` latest dosyaları otomatik picks.

## Tema

Streamlit dark theme + Plotly dark template:
- Primary: `#FFB700` (amber)
- Banking accent: `#00D4FF` (cyan)
- Deep value: `#FF6B6B` (red)
- Cash: `#4ECDC4` (teal)
