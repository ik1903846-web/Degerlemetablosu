"""
Damodaran Lessons Timeline — 15 lesson keşif (Faz 2.5 → Faz 4.16).

REELDEĞER methodology evolution dökümante.
"""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Lessons | REELDEĞER", layout="wide")

st.title("15 Damodaran Lessons — REELDEĞER Methodology Timeline")
st.caption("Faz 2.5 (24 Nis 2026) → Faz 4.16 (28 Nis 2026) — 5-day marathon")


# ============================================================================
# 15 Lessons
# ============================================================================

LESSONS = [
    {
        "id": 1, "faz": "Faz 2.5", "title": "Holdings cannot be valued like industrial firms",
        "status": "VALIDATED", "category": "Valuation",
        "summary": (
            "Holdings için cyclical_dcf YANLIŞ — SAHOL banking revenue mock %55 op_margin "
            "→ +%256 fake AL. SOTP intrinsic-correct (per-child × ownership × disconto). "
            "KCHOL 233 TL, SAHOL 202 TL stable production."
        ),
    },
    {
        "id": 2, "faz": "Faz 2.6", "title": "Cyclical DCF asymmetric cap (peak year)",
        "status": "VALIDATED", "category": "DCF",
        "summary": (
            "current × avg_margin formula PEAK yıllarında inflation üretiyor "
            "(Damodaran Toyota 2009 reference TROUGH için doğru). "
            "Asymmetric cap: effective_revenue = min(current, avg × 1.5). "
            "Trough year korunur, peak year disipline."
        ),
    },
    {
        "id": 3, "faz": "Faz 3", "title": "Cash > overpay when universe inadequate",
        "status": "VALIDATED → REVISITED Faz 4.2", "category": "Portfolio",
        "summary": (
            "BIST 30 / 1M TL: Konservatif %72 cash, Dengeli %65, Agresif %55. "
            "Better to under-invest at intrinsic prices than to overpay. "
            "Faz 4.2'de cap %15 strict edildi (Lesson #8)."
        ),
    },
    {
        "id": 4, "faz": "Faz 2.7", "title": "Adaptive cap by lifecycle + recent margin bias",
        "status": "VALIDATED → EXTENDED Faz 4.7", "category": "DCF",
        "summary": (
            "CCOLA Pentagon Top 1 + extreme upside +%418 NET diagnosis. "
            "MATURE_STABLE + bias > %25 → cap_ratio 1.5 → 1.3. Selektif: SADECE CCOLA. "
            "Faz 4.7'de 3-tier extreme detection (1.15x bias > %50)."
        ),
    },
    {
        "id": 5, "faz": "Faz 6", "title": "Banking DDM > P/B fallback (SOTP refinement)",
        "status": "VALIDATED", "category": "Banking",
        "summary": (
            "SAHOL %63 banking weight: book × P/B 1.5 fallback overestimates by ~%19 "
            "vs DDM USD-basis. SAHOL refined 202 → 181 TL, KCHOL 203 → 190 TL. "
            "ABN Amro €30.87 PASS (Faz 1 baseline INTACT)."
        ),
    },
    {
        "id": 6, "faz": "Faz 6.5 e", "title": "Banking-specific Pentagon weights",
        "status": "VALIDATED", "category": "Pentagon",
        "summary": (
            "Banking için V30/G15/Q30/M5/R20 weights (Q-dominant ROE-CoE excess return). "
            "GARAN composite 58 → 83, AKBNK 56 → 75. 4 banking ticker Core'a girdi."
        ),
    },
    {
        "id": 7, "faz": "Faz 4", "title": "MVP backtest documented look-ahead bias",
        "status": "ACKNOWLEDGED", "category": "Backtest",
        "summary": (
            "Bugünkü Pentagon scores 20 quarter sabit. Look-ahead bias documented. "
            "Bias direction conservative — mevcut intrinsic değerler past Q'da overstate. "
            "Faz 4.10+ historical Pentagon recompute (Option A) parking."
        ),
    },
    {
        "id": 8, "faz": "Faz 4.2", "title": "Cash band strict %15 + empty sleeve redistribute",
        "status": "VALIDATED ★", "category": "Portfolio",
        "summary": (
            "Cash policy %30 → %15 cap. Empty sleeve overflow → aktif sleeve'lere "
            "capacity-pro-rata redistribution. USD alpha +%9.08pp/yr (Dengeli). "
            "Cash drag drama düşüşü: %70 → %10, %27 → %3, %35 → %2."
        ),
    },
    {
        "id": 9, "faz": "Faz 4.5", "title": "Universe size diminishing returns + DD via diversification",
        "status": "VALIDATED", "category": "Universe",
        "summary": (
            "BIST 30 → BIST 50 (+19 ticker). USD ann +1.11pp (mütevazı), AMA Max DD "
            "-7.6pp İYİLEŞTİRDİ (16 vs 11 pozisyon diversification). "
            "Asıl alpha gap kapatma değil, risk-adjusted improvement."
        ),
    },
    {
        "id": 10, "faz": "Faz 4.7", "title": "Hypothesis falsification > methodology force-fit",
        "status": "META-LESSON ★", "category": "Methodology",
        "summary": (
            "AEFES/AKSA hipotez (post-COVID bias > 50%) FAIL — bias gerçek 5-10%. "
            "3-tier cap (1.15/1.3/1.5x) implement edildi gelecek için, mevcut etkisiz. "
            "Hipotez fail dökümante > methodology force-fit. 'Measure twice cut once'."
        ),
    },
    {
        "id": 11, "faz": "Faz 4.8", "title": "Tactical regime overlay NOT EFFECTIVE BIST",
        "status": "FALSIFIED ★", "category": "Backtest",
        "summary": (
            "VIX-based 4-regime cash escalation (panic %25). USD alpha -3.4pp/yr KAYIP, "
            "Max DD aynı/hafif kötü. BIST drawdown'ları correlated (TL devaluation), "
            "USD cash da TL-exposed. 'Value over timing' confirmed."
        ),
    },
    {
        "id": 12, "faz": "Faz 4.6", "title": "Universe expansion PROFILE-DEPENDENT",
        "status": "VALIDATED", "category": "Universe",
        "summary": (
            "BIST 50 → BIST 100 (+15 ticker). Konservatif zero +0.27pp BEAT XU100 ★. "
            "Dengeli/Agresif alpha LOSS -%1.83 to -%2.14 (deep value drag). "
            "Quality > universe size. Profile-aware expansion strategy."
        ),
    },
    {
        "id": 13, "faz": "Faz 4.13", "title": "Pentagon Q (past) ≠ future return; filter FAIL",
        "status": "FALSIFIED → ROLLBACK", "category": "Methodology",
        "summary": (
            "Yüksek Kazanç filter strict (Q > 45, upside > 120). TÜM profilerde "
            "alpha LOSS -2.90pp Konservatif. Drop'lanan HALKB/ARENA/BOSSA historical "
            "alpha sources. Pentagon Q margin stability (past) ≠ future return. "
            "Rollback Faz 4.7 v2 baseline."
        ),
    },
    {
        "id": 14, "faz": "Faz 4.14", "title": "Allocation > Filter — sleeve target lever WIN",
        "status": "VALIDATED ★★★", "category": "Portfolio",
        "summary": (
            "Yüksek Kazanç sleeve target reduction (allocation, NOT filter). "
            "TÜM 6 backtest USD alpha GAIN (+0.46 to +1.73pp). HALKB/ARENA/BOSSA + 14 "
            "ticker SLEEVE'DE KALDI. Konservatif XU100 BEAT genişledi (+1.33pp), "
            "Dengeli SPY BEAT geri kazanıldı (+0.42pp)."
        ),
    },
    {
        "id": 15, "faz": "Faz 4.16", "title": "Empty sleeve redistribution Core PRIORITY",
        "status": "VALIDATED ★★★", "category": "Portfolio",
        "summary": (
            "★★★ ULTIMATE VALIDATION — TÜM 6 BACKTEST TÜM 3 BENCHMARK BEAT. "
            "Capacity-pro-rata yerine Core PRIORITY (quality first). "
            "Konservatif zero USD: -0.21% → +18.98%/yr (vs XU100 +5.44pp BEAT). "
            "vs XU030 (TR peer) ilk kez tüm profillerde BEAT. vs SPY +7-10pp BEAT."
        ),
    },
    {
        "id": 16, "faz": "Faz 4.17", "title": "Profile differentiation (Yüksek %10/%15)",
        "status": "Production", "category": "Portfolio",
        "summary": (
            "Faz 4.16 sonrası Dengeli/Agresif IDENTICAL emergent. Yüksek %10 "
            "her ikisinde + Core PRIORITY → spread kayboldu. Fix: Agresif Yüksek "
            "%10 → %15 differentiation. 3 distinct profile spectrum."
        ),
    },
    {
        "id": 17, "faz": "Faz 7→7.1→7.2→7.3", "title": "Distress as Call Option (Black-Scholes)",
        "status": "MODULE-ONLY ★", "category": "Methodology",
        "summary": (
            "Damodaran Dark Side equity-as-call (Eurotunnel £122M ±0.06% PASS). "
            "Module + smoke + pipeline + backtest 4 katman validate. "
            "BIST production'da -1.64pp drag (race-fixed evidence) → "
            "module-only parking, longer horizon (40Q+) için future iteration."
        ),
    },
    {
        "id": 18, "faz": "Faz 7.1→7.2→7.3→4.18", "title": "Race condition methodology tool integrity",
        "status": "AUTOMATION ★", "category": "Methodology",
        "summary": (
            "USD backtest mtime-sort race condition stale TL artifact. "
            "Fix: --tl-results explicit path + run_pipeline_full.py wrapper. "
            "META → FIX → AUTOMATION evolution. 'Validate hypothesis with frozen "
            "baseline; environmental drift confounds methodology evaluation.'"
        ),
    },
    {
        "id": 19, "faz": "Faz 4.21→4.22→4.22EXT→4.23", "title": "Universe expansion deep-value alpha",
        "status": "★★★★ QUADRUPLE WIN", "category": "Universe",
        "summary": (
            "63 → 99 → 118 → 200 → 559 ticker (BIST Tüm). 4 ardışık ULTIMATE "
            "WIN cumulative +6.75pp Konservatif zero. Saturation profile-spesifik "
            "(Konservatif BIST 200, Agresif BIST Tüm üstü). NOT: Faz 10'da bu "
            "rakamlar leverage artifact bulgusu ile revize."
        ),
    },
    {
        "id": 20, "faz": "Faz 10 P0", "title": "Sermaye matematiği bug → backtest leverage artifact",
        "status": "VALIDATED → CRITICAL ⚠", "category": "Methodology",
        "summary": (
            "MIN_SINGLE_TICKER_PCT %2 cap, 34 ticker × %2 = %68 sleeve total. "
            "Konservatif Yüksek %3 target ile 22x aşım → Core %95 + Yüksek %68 "
            "= %163 invested, total CSV 1.560.000 TL > 1M sermaye. Backtest "
            "engine raw weights × returns = fictitious leverage. Önceki "
            "+25.86%/yr ULTIMATE WIN bug'lı leveraged sistemden geldi.\n\n"
            "FIX: Sleeve renormalize (cap edilmiş weights × scale-down factor "
            "= sleeve_target). Total ≤ 100% guaranteed. Real money math correct.\n\n"
            "GERÇEK SONUÇ: Konservatif zero USD +4.43%/yr, Sharpe 0.01 vs XU100 "
            "+13.54% Sharpe 0.23. 0/18 BEAT (tüm benchmark UNDERPERFORM). "
            "Damodaran Humility Protocol: gerçeği kabul et, ders çıkar.\n\n"
            "Generalization: Real money production'da total_invested ≤ "
            "total_capital constraint zorunlu. Backtest tool integrity check "
            "için sleeve sum invariant test eklenecek (Faz 10.x parking)."
        ),
    },
]


# ============================================================================
# Filter Sidebar
# ============================================================================

with st.sidebar:
    st.markdown("### Filtre")

    categories = sorted(set(l["category"] for l in LESSONS))
    selected_cat = st.multiselect(
        "Kategori",
        categories,
        default=categories,
    )

    statuses = sorted(set(l["status"] for l in LESSONS))
    selected_status = st.multiselect(
        "Status",
        statuses,
        default=statuses,
    )

    st.divider()
    st.markdown("**Lesson Counts:**")
    st.caption(f"Total: {len(LESSONS)}")
    validated = sum(1 for l in LESSONS if "VALIDATED" in l["status"])
    falsified = sum(1 for l in LESSONS if "FALSIFIED" in l["status"])
    st.caption(f"Validated: {validated}")
    st.caption(f"Falsified: {falsified}")
    st.caption(f"Acknowledged: {len(LESSONS) - validated - falsified}")


# ============================================================================
# Lesson Cards (Filtered)
# ============================================================================

filtered = [
    l for l in LESSONS
    if l["category"] in selected_cat and l["status"] in selected_status
]

st.markdown(f"### {len(filtered)}/{len(LESSONS)} Lesson")

for lesson in filtered:
    status_color = "#4ECDC4" if "VALIDATED" in lesson["status"] else \
                    "#FF6B6B" if "FALSIFIED" in lesson["status"] else "#FFB700"

    with st.expander(
        f"#{lesson['id']:>2} · {lesson['title']} · {lesson['faz']} · {lesson['status']}",
        expanded=False,
    ):
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(lesson["summary"])

        with col2:
            st.markdown(f"**Faz:** `{lesson['faz']}`")
            st.markdown(f"**Kategori:** `{lesson['category']}`")
            st.markdown(
                f"**Status:** <span style='color:{status_color};'>"
                f"{lesson['status']}</span>",
                unsafe_allow_html=True,
            )


# ============================================================================
# Footer Pattern Note
# ============================================================================

st.divider()
st.markdown(
    """
    ### Methodology Pattern (Lesson #10 reinforced)

    **3 ardışık hipotez fail** (Faz 4.7 cap + Faz 4.8 tactical + Faz 4.13 filter)
    Damodaran disipline `validate before claim` prensibini doğruladı:
    methodology change ad-hoc değil, backtest evidence gerektirir.

    **2 hipotez WIN** (Faz 4.14 allocation + Faz 4.16 Core PRIORITY) ULTIMATE
    VALIDATION'a götürdü — TÜM 6 backtest TÜM 3 benchmark BEAT.

    **Methodology asset:** Negative results (Lesson #10/11/13) future
    implementation kararlarında reference olarak duruyor.
    """
)
