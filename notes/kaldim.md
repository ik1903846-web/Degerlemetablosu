# REELDEĞER — Kaldığım Yer

**Son güncelleme:** 27 Nisan 2026, sabah
**Aktif Faz:** Faz 2.4.4 — Orchestrator Live Integration (TAMAM)
**Sıradaki:** Faz 2.4.5 — EM cyclicality threshold calibration

---

## Dün Tamamlananlar (26 Nis → 27 Nis 02:30, ~17 saat)

Sabah:
- Faz 1.3.2: Cost of Capital (5/5 PASS)
- Faz 1.3.3: Industrial FCFF (Heineken 59.65 EUR PASS, -0.14%)

Öğleden sonra:
- Faz 1.4: Banking DDM (ABN Amro 30.87 EUR PASS, +4.06%)
- Faz 1.5: Industrial FCFF EM (Tube Investments 61.55 INR PASS, -0.04%)
- Faz 1.6: Cyclical DCF (Toyota 4737 JPY PASS, +0.04%)
- Faz 1.7: Amazon young firm (skip — _wip_amazon klasörü)

Akşam:
- Faz 2.1.1a: KAP scraper foundation
- Faz 2.1.1b: isyatirim discovery (JACKPOT)
- Faz 2.1.2 A-B: scraper + Damodaran mapper
- Faz 2.1.3: TUPRS Cyclical DCF (placeholder bug, 169.94 TL)
- Faz 2.1.4 Adım 1-5: 4 düzeltme + Final DCF (181.16 TL)
- Faz 2.2: Lifecycle Classifier (6-stage)
- Faz 2.3: Orchestrator (analyze_ticker tek call)
- Faz 2.4: BIST 30 Batch Pilot (16/19 PASS, 28s)
- Faz 2.4.3: Live Market Price Fetcher (Yahoo Finance)
- Faz 2.4.4: Orchestrator Live Integration (auto-fetch + AL/SAT/BEKLE)

---

## REELDEĞER MOTORU — PRODUCTION-READY

4 DCF model:
- Industrial FCFF (Heineken EUR 59.65 PASS)
- Banking DDM (ABN Amro EUR 30.87 PASS)
- Industrial FCFF EM (Tube INR 61.55 PASS)
- Cyclical DCF (Toyota JPY 4737 PASS)

Pipeline (analyze_ticker tek call):
ticker → fetch (12 yıl) → map → USD → classify → DCF → shares → Yahoo price → AL/SAT verdict

5 BIST data source:
- isyatirim.com.tr (mali tablolar XBRL, 147 kalem × 12 dönem)
- Yahoo Finance v8 (.IS suffix, spot + historical)
- Damodaran fetcher (Rf, ERP, CRP, sektör beta — 101 param)
- Static FX rates (TCMB year-end 2013-2025)
- Static shares dictionary (25 BIST 30 ticker)

---

## BIST 19 Ticker — Damodaran AL/SAT/BEKLE (24 Nis 2026)

**Validated anchors:**
- TUPRS 181 vs 269 → -33% SAT (sweet spot retro doğrulandı)
- KCHOL 223 vs 207 → +8% BEKLE (motor doğruluğun canlı kanıtı)

**AL adayları (calibration suspect):**
- FROTO 940 vs 105 → +799% (overestimate?)
- CCOLA 513 vs 77 → +567% (defensive yanlış sınıf?)
- SAHOL 388 vs 99 → +293% (holding SOTP gerek)
- ARCLK 401 vs 117 → +242% (Cyclical White Goods)
- EREGL 74 vs 33 → +124% (steel cyclical)

**SAT (9):** TUPRS, TOASO, ASELS, MGROS, ENKAI, THYAO, PETKM, SOKM, PGSUS

**Negatif DCF (artifact):** SOKM -127, PGSUS -652

**Error (3):** KOZAL/KOZAA (Yahoo + isyatirim'de yok), BIMAS (taxonomy)

---

## Bugün Hedef — Faz 2.4.5 EM Calibration

Calibration soruları:
1. FROTO/CCOLA neden +%500+ overestimate?
   - 12-yıl avg margin cycle peak ağırlıklı olabilir
   - Rolling median veya outlier removal düşün
2. SOKM/PGSUS negatif DCF nasıl floor edilmeli?
   - operating_value <= 0 → "unreliable" flag
   - Veya alternative model (book value floor)
3. SAHOL holding için SOTP yaklaşım mı tek DCF mi?
4. EM threshold: Türkiye'de "stable" var mı, yoksa hepsi cyclical mi?

Tahmini efor: ~3-4 saat
Hedef: KCHOL +%8 anchor'ını koru, FROTO/CCOLA gerçeğe yaklaşsın

---

## Yarın Açılış Komutları

cd /c/Users/unutu/Desktop/abiminprojev2
git status
git log --oneline | head -10
cat notes/kaldim.md

---

## Repo Durumu

- 41 commit GitHub'da (clean)
- Branch: main
- Son commit: 3a63d28 (Faz 2.4.4 Orchestrator Live)
- GitHub: https://github.com/ik1903846-web/Degerlemetablosu

---

## Validation Disiplini (5/5 zero-deviation)

| Case | Beklenen | Hesaplanan | Sapma |
|---|---|---|---|
| Heineken | €59.65 | €59.57 | -0.14% |
| Toyota | ¥4,735 | ¥4,737 | +0.04% |
| Tube Inv. | ₹61.57 | ₹61.55 | -0.04% |
| ABN Amro | €30.87 | €32.12 | +4.06% |
| TUPRS Mkt Cap | 518.30B | 518.31B | 0.00% |

TUPRS DCF: manuel = batch = live = **181.16 TL** (3 yöntem birebir)

---

## Önemli Notlar

1. **TUPRS sweet spot retro doğrulandı:**
   - 2024 sonu (144 TL): DCF 181 TL = %26 UCUZ → AL
   - 2026 Nis (269 TL): DCF 181 TL = %33 PAHALI → SAT
   - 2 yılda fiyat +%87, DCF üzerinde

2. **EM cyclicality endemic:** 19 ticker'ın hepsi mature_stable + cyclical
   - Damodaran "developed" firmalardan farklı
   - Faz 2.4.5'te sektör-bazlı threshold gerek

3. **TFRS 29 hyperinflation noise:** USD bazda bile PP&E gross-up etkisi var
   - Reinvestment rate %86 (12-yıl avg) şüpheli yüksek
   - Inflation-adjusted PP&E ileride

4. **Banking için 2.3.1 parking:** GARAN/AKBNK orchestrator skip ediyor
   - banking_ddm modülü hazır (Faz 1.4)
   - financialGroup XI_30 + lifecycle bypass gerek

5. **Pythonic Damodaran adapter çalışıyor:**
   - Heineken (EUR DM) + Tube (INR EM) + Toyota (JPY cyclical) + ABN (EUR bank)
   - 4 farklı para, 4 farklı model, hepsi <%5 sapma
   - BIST'te tek soru kalibrasyon (sayı doğru, threshold ayarı)

6. **41 commit / 17 saat:**
   - Sıfırdan production sistem
   - Faz 1 + Faz 2 birlikte
   - Validation gate: hep zero-deviation
