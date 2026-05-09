# REELDEĞER v4 — Hızlı Büyüme Sekmesi Spec

**Belge tarihi:** 9 Mayıs 2026
**Hedef:** Streamlit Tarayıcı'ya genç ve yüksek büyüme firmaları için ayrı sekme
**Damodaran kaynak:** `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/spreadsh.htm#ginzumodels`
**Spec referansı:** v2.2 §5.7 (Young Firm), ADR-049 (Uber 9-Input), ADR-065 (6-Lesson Checklist)
**Mevcut durum:** Hızlı Büyüme **sleeve** spec'te tanımlı (ADR-066, ADR-067) — UI sekmesi henüz yok

---

## 1. NEDEN AYRI SEKME?

Damodaran'ın altın kuralı (Spec §4.1): **"Şirketin yaşam evresini bilmeden doğru değerleme modeli seçemezsin."**

Mature Growth (Stage 4) için 2-stage FCFF yeterli, ama:

| Stage | Pattern | Standard FCFF kafayetli mi? |
|---|---|---|
| Stage 2 (Young Growth) | Negatif/marjinal kar, %50+ büyüme | **Hayır** — distress çarpanı şart |
| Stage 3 (High Growth) | Pozitif kar, yüksek capex, %15-30 büyüme | **Yarı** — expansion options eksik |

Standard FCFF Stage 2/3'te şu hataları yapıyor:
1. Bottom-up beta yerine regression beta → manipule olabilir
2. Geçmişe dayalı revenue projection → genç firmaların TAM-bazlı backward path'ine ters
3. Re-investment formülü yanlış (capex yerine ΔRevenue / Sales-to-Capital)
4. Distress probability hesaba katılmıyor → Theranos riski
5. Option/dilution sayılmıyor → Tesla 2014 hatası

**Ayrı sekme = ayrı UI = ayrı validasyon = ayrı risk yönetimi.** Aynı motorla farklı parametre değil, farklı **felsefe**.

---

## 2. SEKME YERLEŞİMİ (Streamlit)

    Tarayıcı (mevcut UI)
    ├─ Sekme 1: Mature DCF (mevcut, fcffsimpleginzu)
    ├─ Sekme 2: Holding SOTP (mevcut)
    ├─ Sekme 3: 🆕 Hızlı Büyüme (YENİ)
    ├─ Sekme 4: Banking (mevcut)
    └─ Sekme 5: Lifecycle Classifier (mevcut, yönlendirici)

**Lifecycle Classifier** (Sekme 5) zaten Stage 2/3 tespit ediyorsa, kullanıcıyı **Sekme 3'e otomatik yönlendir** ("Bu şirket Stage 2 — Hızlı Büyüme sekmesinde değerleyin"). Mature DCF sekmesinde uyarı banner'ı göster.

---

## 3. SEKME 3 İÇERİK YAPISI

### 3.1 Üst Bilgi Bandı

    ┌────────────────────────────────────────┐
    │ 🚀 HIZLI BÜYÜME DEĞERLEME             │
    │                                        │
    │ Şirket: ALTNY (ALTINAY SAVUNMA)       │
    │ Lifecycle: Stage 2 (Young Growth)      │
    │ Damodaran model: higrowth.xls + Uber  │
    │ Last narrative update: 23 gün önce     │
    └────────────────────────────────────────┘

**Staleness uyarısı (ADR-065):** Last narrative update > 90 gün ise kırmızı banner.

### 3.2 6-Lesson Checklist (ADR-065) — sol panel

Damodaran'ın Young Firm 6 dersi UI olarak checklist:

    ☐ 1. Bottom-up beta kullanılıyor mu? (regression DEĞİL)
    ☐ 2. Backward revenue path: target year → today
    ☐ 3. Re-investment = ΔRev / Sales-to-Capital
    ☐ 4. 2D sensitivity matrix (margin × growth)
    ☐ 5. Options/dilution adjustment yapıldı mı?
    ☐ 6. Last revaluation < 90 gün

Hepsi ✓ olmadan **"Final Value" gizli kalır.** Damodaran "all-or-nothing" disiplini.

### 3.3 Uber 9-Input Narrative Template (ADR-049) — orta panel

Damodaran'ın Uber 2014 6-Step → 9-Input template'i:

    INPUT 1: Total Addressable Market (TAM)
      → Kaynak: KAP segment + sektör raporu + firma sunumları
      → Validation: Top-down (sektör boyutu) + Bottom-up (penetration)

    INPUT 2: Market Share (target year, ör. 2036)
      → Default: %5 (konservatif), %10 (orta), %20 (agresif)

    INPUT 3: Operating Margin (target year)
      → Default: sektör ortalaması (Damodaran sector tablosu)

    INPUT 4: Sales-to-Capital Ratio
      → Default: industry global (Damodaran)
      → BIST düzeltmesi: sektör BIST regresyonu

    INPUT 5: Cost of Capital trajectory
      → Year 1-5: 12% (early high)
      → Year 6-10: 10% (transition)
      → Year 10+: 8% (mature)

    INPUT 6: Failure Probability (πFailure)
      → distress.xls'den çekilir
      → Default: rating-based, market bond price tabanlı

    INPUT 7: Cash on hand
      → KAP TR-IFRS bilanço

    INPUT 8: Debt outstanding
      → Operating lease dahil (oplease.xls)

    INPUT 9: Option/dilution overhang
      → employeeoption.xls
      → Stage 2/3 için kritik

**Çıktı formülü (Damodaran tarif):**

    Total Market × Market Share = Revenue (target year)
    × Operating Margin = Operating Income
    − Taxes = After-tax Operating Income
    − Reinvestment (ΔRev / Sales-to-Capital) = FCF
    ÷ Cost of Capital (12% → 8%) = PV
    × (1 − Failure Probability) = Value of Operating Assets
    + Cash − Debt = Equity Value
    ÷ Diluted Shares (option-adjusted) = Per Share

### 3.4 2D Sensitivity Matrix (Lesson #4) — sağ panel

                    Operating Margin (target)
                    5%    10%   15%   20%   25%
    Growth   10%   ──    ──    ──    ──    ──
    (target  20%   ──    ──    ──    ──    ──
    year)    30%   ──    ──   [▓▓]   ──    ──    ← base case
             50%   ──    ──    ──    ──    ──
             80%   ──    ──    ──    ──    ──

Heatmap: kırmızı (downside) → yeşil (upside). Base case işaretli.

### 3.5 Distress Probability Block (Lesson alttan)

    DISTRESS ANALYSIS
    ─────────────────
    Bond rating:      B+ (sentetik, ratings.xls)
    Implied πFailure: 21.3%
    Z-score (Altman): 1.42 (gri zone)
    DCF × (1 − π):    DCF × 0.787

    Eğer πFailure > %30 → Stage 2 → Stage 6 transition uyarısı

### 3.6 Final Output Card

    ╔══════════════════════════════════╗
    ║ ALTNY (ALTINAY SAVUNMA)         ║
    ║                                  ║
    ║ Stage: 2 (Young Growth)          ║
    ║ Sleeve: Hızlı Büyüme             ║
    ║                                  ║
    ║ Per share value (base):  44.20   ║
    ║ Per share value (low):   28.50   ║
    ║ Per share value (high):  68.70   ║
    ║                                  ║
    ║ Current market price:    52.30   ║
    ║ MoS (vs base):          −%18     ║
    ║ MoS (vs low):           −%83     ║
    ║                                  ║
    ║ Lesson checklist: 6/6 ✓          ║
    ║ Last revaluation: 23 gün önce ✓  ║
    ║                                  ║
    ║ SLEEVE EŞİĞİ:                    ║
    ║   ROIC trajectory: ↗ (geçti)     ║
    ║   Uber template: ✓ kuruldu       ║
    ║   6-Lesson: ✓ tam geçti          ║
    ║                                  ║
    ║ Decision: HIZLI BÜYÜME GİRİŞ     ║
    ║           ✓ uygun (sleeve %20)   ║
    ╚══════════════════════════════════╝

---

## 4. BIST ÖRNEK ŞİRKETLER (Stage 2/3 adayları)

Lifecycle classifier henüz tüm 251 ticker'a uygulanmadı, ama **a priori** Stage 2/3 olması beklenenler:

### Stage 2 (Young Growth) adayları
- ALTNY (Altınay Savunma) — savunma, R&D yoğun
- CWENE (CW Enerji) — yenilenebilir enerji
- ESEN (Esenboğa Elektrik) — yenilenebilir enerji
- KIMMR (Ersan Alışveriş) — perakende büyüme
- DOFRB (DOF Robotik) — ileri teknoloji

### Stage 3 (High Growth) adayları
- SASA — petrokimya kapasite genişleme
- ASTOR — enerji altyapı
- ENERY (Enerya) — doğalgaz dağıtım
- GESAN — elektrik altyapı
- BRLSM — HVAC mühendislik

**Not:** Bu liste lifecycle classifier çalıştırılana kadar **tahmin**. Kesin sınıflandırma 6-stage criteria sonrası belirir.

---

## 5. SLEEVE ENTEGRASYONU (ADR-066, ADR-067)

Spec v2.2'de **Hızlı Büyüme sleeve** zaten tanımlı:

    sleeve_hizli_buyume:
      lifecycle_evren: [Young, High Growth]
      giriş_kuralı:
        - Young Firm 6-Lesson tam geçti
        - Uber 9-Input narrative kuruldu
        - ROIC trajectory yukarı VEYA ROIC > WACC sustained
      pozisyon_sizing:
        max_tek_pozisyon: %20 sleeve içi (~%5 portföy)
        min_isim_sayısı: 5-8
      rebalance: quarterly + lifecycle change tetikli

Sekme UI bu sleeve'in **giriş kapısı** olur. Sleeve'e giriş için sekmeden ✓ alınması zorunlu.

---

## 6. NARRATIVE INTEGRITY HOOKS (ADR-050, ADR-051)

Hızlı büyüme şirketleri **Runaway Story riski** taşır (Theranos pattern). Sekmede entegre kontroller:

### 6.1 Runaway Story Detector (3-check)
- [ ] Karizmatik CEO + medya hype
- [ ] "Disrupting" söylemi (yıkıcı iddialar)
- [ ] Sosyal fayda narratifi (greenwash, defansif gerekçe)

3 ✓ varsa → **SCRUTINY flag** kırmızı, sleeve girişi engellenir

### 6.2 Meltdown Story Detector (3-check)
- [ ] Yönetim güvenilmezlik sinyali
- [ ] Story vs numbers uyumsuzluk
- [ ] Bad accounting model (KAP yorumu)

3 ✓ varsa → **DISTRESS up-flag** + Stage 6 transition

---

## 7. UI/UX İMPLEMENTASYON DETAYLARI

### 7.1 Streamlit komponent map

    # tarayici/pages/3_Hizli_Buyume.py
    import streamlit as st

    st.set_page_config(page_title="Hızlı Büyüme", page_icon="🚀")

    # Üst bilgi bandı
    ticker = st.selectbox("Şirket", filter_stage_2_3())
    st.info(f"Lifecycle: {get_lifecycle(ticker)}")

    # 3 kolon yapı
    col_lessons, col_inputs, col_sensitivity = st.columns([1, 2, 1])

    with col_lessons:
        render_6_lesson_checklist(ticker)

    with col_inputs:
        render_uber_9_input_template(ticker)

    with col_sensitivity:
        render_2d_sensitivity_heatmap(ticker)

    # Alt bilgi
    render_distress_block(ticker)
    render_narrative_integrity_check(ticker)

    # Final card
    if all_lessons_passed:
        render_final_card(ticker)
    else:
        st.warning("6-Lesson checklist tamamlanmadan değer görünmez.")

### 7.2 Veri kaynakları (sekme için yeni)

| Veri | Kaynak | Cache süresi |
|---|---|---|
| TAM (sektör boyutu) | KAP segment + manuel input | 1 ay |
| Market share | Manuel input + KAP rakip karşılaştırma | 1 hafta |
| Sales-to-Capital | Damodaran sector data | 6 ay |
| πFailure | distress.xls + bond rating | 1 hafta |
| Option overhang | KAP yıllık rapor + employeeoption.xls | 3 ay |

### 7.3 State management

User'ın 9-input girdileri **session-scoped** kalır. Save → JSON export, repo dışı. (PII riski yok ama strateji bilgisi.)

---

## 8. TEST PLANI

Sekme implement edildikten sonra **2 validation case** ile test:

### Test 1: Uber 2014 reproduction
- Damodaran'ın "Narrative & Numbers" kitabındaki orijinal hesabı yeniden çalıştır
- Hedef: $6B value (urban car service narrative, Damodaran original)
- Tolerance: ±%5 (ADR-024)
- Çıktı kriteri: Sekme Uber 2014 setup'ı ile $5.7B-$6.3B arası üretmeli

### Test 2: BIST içi cross-validation
- ALTNY için sekme hesabı vs Mature DCF sekmesi
- Mature DCF Stage 2 için yanlış model olduğu için **sapma > %30 BEKLENİR**
- Bu sapma "neden ayrı sekme şart" argümanını **kanıtlar**

---

## 9. ROADMAP (Session 4 içine entegre)

| Hafta | Eylem |
|---|---|
| 1 | Sekme iskelet (placeholder) + 6-Lesson checklist |
| 2 | Uber 9-Input template UI + form validation |
| 3 | 2D sensitivity heatmap + distress block |
| 4 | Narrative integrity hooks + final card |
| 5 | Uber 2014 validation test |
| 6 | ALTNY/CWENE BIST test + sleeve entegrasyon |

**Toplam: ~6 hafta** (Audit Step 1-2 ile parallel ilerleyebilir).

---

## 10. KIRMIZI ÇİZGİLER

| Yasak | Sebep |
|---|---|
| Mature DCF sekmesinin Stage 2/3'e zorla genişletilmesi | Yanlış model = yanlış değer (Damodaran ana kuralı) |
| 6-Lesson checklist'siz "Final Value" göstermek | Damodaran disiplini |
| TAM input'unu otomatik web scraping ile çekmek | Üçüncü taraf veri yasak (Lesson #25, #28) |
| Sekme veriyi production database'e yazmak | Session 6 atomic cutover öncesi schema değişikliği yasak |
| AI/LLM API ile narrative generation | Bütçe kuralı |

---

## 11. AUDIT FINDINGS İLE ETKİLEŞİM

**Önemli not:** Bu sekme `audit_findings_session4.md` ve `audit_decision_v4.md` ile **uyumlu** olmalı.

- Cost of Capital 12% → 8% trajectory **Damodaran resmi parametreleri** ile (Şubat 2026 update'i sonrası)
- Mature ERP ve Turkey CRP **Faz B1 Adım 7 sonrası config'den** gelir
- Sekme implement edilmeden önce Audit Faz B1 Adım 1-4 tamamlanmalı (parameter staleness etkilemesin)

---

## DOKÜMAN SONU

Bu spec'i Session 4 sonunda v3.0 ana spec'e entegre et. Implementation Faz B1 ile parallel başlayabilir, ama final card hesapları Faz B1 Adım 7 (config update) tamamlandıktan sonra valid olur.
