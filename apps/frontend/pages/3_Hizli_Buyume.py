"""
Hızlı Büyüme Sekmesi — Placeholder
===================================

REELDEĞER v4 — Stage 2 (Young Growth) ve Stage 3 (High Growth)
şirketleri için ayrı değerleme arayüzü.

Damodaran kaynak:
  - higrowth.xls (genç firma DCF)
  - Uber 9-Input Narrative Template (ADR-049)
  - Young Firm 6-Lesson Checklist (ADR-065)

Detaylı spec: docs/young_growth_tab_spec.md

Implementation roadmap:
  Hafta 1: 6-Lesson checklist gating
  Hafta 2: Uber 9-Input form
  Hafta 3: 2D sensitivity heatmap + distress block
  Hafta 4: Narrative integrity hooks (Runaway/Meltdown detector)
  Hafta 5: Uber 2014 validation test ($6B target)
  Hafta 6: ALTNY/CWENE BIST cross-validation

UYARI — Audit dependency:
  Final card hesapları geçerli olmadan önce Audit Faz B1 Adım 1-7
  tamamlanmalı. Cost of Capital trajectory (12% → 8%) Damodaran
  resmi parametreleri (Şub 2026 update) sonrası valid.

Status: PLACEHOLDER (Coming Soon)
"""

import streamlit as st

# ─────────────────────────────────────────────────────────────────
# SAYFA AYARLARI
# ─────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Hızlı Büyüme — REELDEĞER v4",
    page_icon="🚀",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────
# BAŞLIK + BANNER
# ─────────────────────────────────────────────────────────────────

st.title("🚀 Hızlı Büyüme Değerleme")

st.warning(
    "**🚧 Coming Soon — Implementation aşamasında**\n\n"
    "Bu sekme Stage 2 (Young Growth) ve Stage 3 (High Growth) "
    "şirketleri için ayrı değerleme motorudur. Mature DCF "
    "sekmesi bu evreler için yanlış model — distress çarpanı, "
    "expansion options ve narrative-driven valuation gerekir."
)

st.info(
    "📋 **Detaylı tasarım dokümanı:** `docs/young_growth_tab_spec.md`\n\n"
    "📋 **Audit context:** `docs/audit_findings_session4.md`, "
    "`docs/audit_decision_v4.md`"
)

# ─────────────────────────────────────────────────────────────────
# DAMODARAN KURALI HATIRLATMA
# ─────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "> **Damodaran §4.1:** \"Şirketin yaşam evresini bilmeden "
    "doğru değerleme modeli seçemezsin.\""
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────────
# ROADMAP GÖRÜNÜMÜ
# ─────────────────────────────────────────────────────────────────

st.subheader("Implementation Roadmap (6 hafta)")

roadmap = {
    "Hafta 1": "Sekme iskelet + 6-Lesson checklist gating",
    "Hafta 2": "Uber 9-Input narrative template UI + form validation",
    "Hafta 3": "2D sensitivity heatmap + distress probability block",
    "Hafta 4": "Narrative integrity hooks (Runaway/Meltdown detector)",
    "Hafta 5": "Uber 2014 validation test ($6B target, ±%5 tolerance)",
    "Hafta 6": "ALTNY/CWENE BIST cross-validation + sleeve entegrasyon",
}

for hafta, eylem in roadmap.items():
    st.markdown(f"- **{hafta}:** {eylem}")

st.markdown("---")

# ─────────────────────────────────────────────────────────────────
# TODO MARKERS — IMPLEMENTATION KANCALARI
# ─────────────────────────────────────────────────────────────────

# TODO[Hafta 1]: Stage 2/3 lifecycle filter integration
#   - Lifecycle classifier'dan Stage 2/3 ticker listesi al
#   - st.selectbox("Şirket", filter_stage_2_3()) ile ticker seç
#   - Üst bilgi bandı: ticker + lifecycle stage + son güncelleme tarihi

# TODO[Hafta 1]: 6-Lesson Checklist gating
#   - Sol panel: 6 checkbox (ADR-065)
#   - Tüm 6 ✓ olmadan final card görünmez
#   - render_6_lesson_checklist(ticker)

# TODO[Hafta 2]: Uber 9-Input Narrative Template
#   - Orta panel: TAM, market share, op margin, sales-to-cap,
#     cost of capital trajectory, π_failure, cash, debt, options
#   - render_uber_9_input_template(ticker)

# TODO[Hafta 3]: 2D Sensitivity Heatmap
#   - Sağ panel: margin × growth matrix
#   - Heatmap: kırmızı (downside) → yeşil (upside)
#   - Base case işaretli
#   - render_2d_sensitivity_heatmap(ticker)

# TODO[Hafta 3]: Distress Probability Block
#   - Bond rating (sentetik, ratings.xls)
#   - π_failure (distress.xls)
#   - Z-score (Altman)
#   - DCF × (1 − π) son değer
#   - render_distress_block(ticker)

# TODO[Hafta 4]: Narrative Integrity Hooks
#   - Runaway Story Detector (3-check, ADR-050)
#   - Meltdown Story Detector (3-check, ADR-051)
#   - SCRUTINY/DISTRESS flag entegrasyonu
#   - render_narrative_integrity_check(ticker)

# TODO[Hafta 4]: Final Output Card
#   - Per share value (low/base/high)
#   - MoS calculation
#   - Sleeve eligibility check
#   - Decision: HIZLI BÜYÜME GİRİŞ uygun mu?
#   - render_final_card(ticker) — ONLY IF all_lessons_passed

# TODO[Cross-cutting]: Audit Faz B1 dependency
#   - Cost of Capital parameters Damodaran Şub 2026 update'inden gelmeli
#   - apps/api/data/damodaran/{date}/parameters.json okunacak
#   - Eğer parameters.json yok → "Audit Adım 1 önce çalıştırılmalı"
#     warning göster, sekmeyi disable et

# ─────────────────────────────────────────────────────────────────
# PLACEHOLDER STATUS BADGE
# ─────────────────────────────────────────────────────────────────

st.markdown("---")
st.caption(
    "Status: 🚧 PLACEHOLDER · "
    "Last updated: 2026-05-09 · "
    "Owner: docs/young_growth_tab_spec.md"
)
