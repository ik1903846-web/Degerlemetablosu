# SOTP BIST Batch Validation — Faz 2.5 ADIM 5

**Tarih:** 27 Nisan 2026
**Commit:** 468197b (Faz 2.5 ADIM 4 — Orchestrator SOTP integration sonrası)
**Methodology:** Component 1+2+3 (industrial) + Faz 2.5 SOTP (holdings)
**Runner:** apps/api/scripts/test_orchestrator_live.py
**Output:** apps/api/outputs/bist_batch_LIVE_20260427_184141.{csv,json}

---

## Hedef

KCHOL/SAHOL SOTP routing batch context'inde validate. Component 4 (Faz 2.4.6) industrial anchor regression korunur, holdings için SOTP intrinsic değerleri görünür.

## Sonuç Özeti

| Metric | Değer |
|---|---|
| Duration | 48.9s (19 ticker, 2-phase batch) |
| Successful | 17/19 (BIMAS+SOKM fail — 16-yıl coverage gap, Component 5 parking) |
| TUPRS DCF | 188.29 TL (Component 4 INTACT, deep dive 188.31 ±0.02) |
| KCHOL SOTP | 233.36 TL (+%13.84 IZLE-AL) |
| SAHOL SOTP | 202.09 TL (+%105.90 AL) |
| Avg upside | +34.65% |
| Deep value (>+30%) | 6 |
| Overvalued (<-30%) | 9 |

---

## Holdings Anchor Regression (Faz 2.4.6 → Faz 2.5)

| Ticker | Faz 2.4.6 (Component 4 cyclical+whitelist) | Faz 2.5 (SOTP) | Δ DCF | Δ Verdict |
|--------|--------------------------------------------|----------------|-------|-----------|
| KCHOL  | 189.21 TL (-%8.77 BEKLE)                   | 233.36 TL (+%13.84 IZLE-AL) | +44 TL (+%23) | BEKLE → IZLE-AL |
| SAHOL  | 354.60 TL (+%256.56 AL)                    | 202.09 TL (+%105.90 AL) | -152 TL (-%43) | AL → AL (disciplined) |

### Methodology Yorumu

**KCHOL +44 TL (+%23):**
- Component 4 cyclical_dcf with β=1 fallback (whitelist) — basit yaklaşım
- SOTP iştirak-bazlı intrinsic + banking P/B 1.5 + non-listed book
- Banking-light (%12 YKBNK) → SOTP slightly aggressive
- Banking + non-listed pool ekstra value tanır
- Disconto %15 sonrası bile Component 4'ten yüksek

**SAHOL -152 TL (-%43):**
- Component 4 cyclical_dcf β=1 → çok yüksek intrinsic (banking handling
  yetersiz)
- SOTP disconto %15 + book × multiplier conservative → daha disipline
- Banking-heavy (%63 AKBNK) → P/B 1.5 büyük ama disconto compensates
- Methodology daha disiplinli (deep value AL görüşü korunur, ama oran azaldı)

## Non-Holdings Anchor Regression (Component 4 → Faz 2.5)

| Ticker | Component 4 | Faz 2.5 batch | Status |
|--------|-------------|----------------|--------|
| TUPRS  | 188.29 TL   | 188.29 TL      | ★ INTACT |
| ARCLK  | 311.54 TL   | 311.54 TL      | INTACT |
| FROTO  | 671.37 TL   | 671.37 TL      | INTACT |
| TOASO  | 114.90 TL   | 114.90 TL      | INTACT |
| EREGL  | 58.54 TL    | 58.54 TL       | INTACT |
| CCOLA  | 486.30 TL   | 486.30 TL      | INTACT |
| ASELS  | 145.74 TL   | 145.74 TL      | INTACT |
| MGROS  | 267.61 TL   | 267.61 TL      | INTACT |
| ENKAI  | 31.86 TL    | 31.86 TL       | INTACT |
| THYAO  | 16.45 TL    | 16.45 TL       | INTACT |
| PETKM  | -3.76 TL    | -3.76 TL       | INTACT (artifact) |
| PGSUS  | -839.77 TL  | -839.77 TL     | INTACT (artifact) |
| KRDMD  | 26.37 TL    | 26.37 TL       | INTACT |
| TRALT  | 157.88 TL   | 157.88 TL      | INTACT |
| TRMET  | 69.14 TL    | 69.14 TL       | INTACT |
| BIMAS  | error       | error          | 16-yıl coverage gap |
| SOKM   | error       | error          | 16-yıl coverage gap |

**17/17 industrial ticker davranışı %100 korunmuş** (backward-compat başarısı).

## Damodaran Methodology Validation

### TUPRS Deep Dive Baseline (Faz 2.4.5)
- Manual deep dive (5+ saat): 188.31 TL
- Production (Component 1+2+3+4): 188.29 TL
- Faz 2.5 batch: 188.29 TL (sapma 0.02 TL, baseline INTACT)

### Holdings Discount Analiz

**KCHOL:**
- Market: 205 TL
- SOTP intrinsic: 233.36 TL
- Upside: +13.84% (IZLE-AL band)
- Gedik analyst observed discount: -33% (current), -13% (15-yıl avg)
- Bizim SOTP'ye göre +13.84% premium → market hafif altta

**SAHOL:**
- Market: 98.15 TL
- SOTP intrinsic: 202.09 TL
- Upside: +105.90% (AL band)
- SAHOL self-reported NAV discount: -46% (Q4 2024)
- Bizim SOTP'ye göre +106% premium → SAHOL chronic deep discount kanıtı

### Sleeve Implication (Future Faz 3 Portfolio)

- **KCHOL** (mild discount): "Mature Holding" sleeve candidate
  - Methodology-justified +%14 upside, banking-light, listed children'ın
    çoğunda DCF lookup mevcut
  - Conservative AL — IZLE-AL verdict mantıklı
- **SAHOL** (deep discount): "Deep Value" sleeve candidate
  - Methodology disiplinli +%106 upside (eski +%256'dan disconto +
    book conservative ile rasyonelleşti)
  - Banking-heavy (%63 AKBNK) → AKBNK'nin gerçek P/B'sine bağlı
  - Faz 2.3.1 banking equity-only model gelince hassasiyet artar

## SOTP Children Breakdown

### KCHOL (16.73B USD net intrinsic)

**Listed (DCF lookup):** 4 ticker
- TUPRS (40% × $10.26B = $4.10B)
- FROTO (38.7% × $6.66B = $2.58B)
- ARCLK (41.4% × $5.95B = $2.46B)
- TOASO (37.6% × $1.62B = $0.61B)

**Listed (book fallback):** 3 ticker (BIST 30 dışı)
- OTKAR (47.4% × $1.65B = $0.78B)
- TTRAK (37.5% × $2.32B = $0.87B)
- AYGAZ (40.7% × $0.99B = $0.40B)

**Banking (P/B 1.5):** 1 ticker
- YKBNK (41% × $12B × 1.5 = $4.92B) [PROVISIONAL]

**Non-listed pool:** 4 segment
- Otokoç (96.4% × $1.10B = $1.06B)
- Tourism Pool (Altınyunus, Mares, Setur)
- Real Estate Pool
- Other Non-Listed (Koç Sistem, Token, WAT, Koçtaş, Düzey, Koç Finans, Arçelik LG)

**Aggregation:**
- Listed: $11.81B + Banking: $4.92B + Non-listed: $1.97B = $18.71B
- Net cash: +$0.98B (Gedik report)
- Pre-disconto: $19.68B
- Disconto -%15: $16.73B
- Per share: $6.60 → 233.36 TL

### SAHOL (11.66B USD net intrinsic)

**Listed (DCF lookup):** 0 ticker (BIST 30 industrial dışı)

**Listed (book fallback):** 9 ticker
- ENJSA, AKGRT, AGESA, AKCNS, CIMSA, BRISA, KORDS, CRFSA, TKNSA

**Banking (P/B 1.5):** 1 ticker
- AKBNK (41% × $12B × 1.5 = $7.38B) ★ DOMINANT (%63 contribution)

**Non-listed pool:** 6 segment
- Enerjisa Üretim (50% × $3.95B = $1.98B)
- Sabancı Climate Tech (100% × $0.46B)
- Other (Tursa, AEO, TMA, SabancıDx, DxBV, TUA, Çimsa Building Solutions)

**Aggregation:**
- Listed: $2.92B + Banking: $7.38B + Non-listed: $3.06B = $13.36B
- Net cash: +$0.35B
- Pre-disconto: $13.72B
- Disconto -%15: $11.66B
- Per share: $5.71 → 202.09 TL

## 2-Phase Batch Flow Validation

```
Phase 1: Holdings vs non-holdings ayrım
  Non-holdings: TUPRS, PETKM, EREGL, KRDMD, TRALT, TRMET, BIMAS, MGROS,
                SOKM, CCOLA, TOASO, FROTO, ARCLK, ASELS, THYAO, PGSUS,
                ENKAI (17)
  Holdings:     KCHOL, SAHOL (2)

Phase 2: Non-holdings paralel analyze (~30s)
  Industrial flow: Component 1+2+3 (bottom-up beta + sovereign+sector + 16-yıl)

Phase 3: dcf_lookups dict from successful non-holdings
  TUPRS: $10.26B
  FROTO: $6.66B
  ARCLK: $5.95B
  TOASO: $1.62B
  + 11 diğer (CCOLA, ENKAI, vb.)

Phase 4: Holdings paralel SOTP routing
  KCHOL: dcf_lookups'tan 4 child DCF → 233.36 TL
  SAHOL: dcf_lookups'ta 0 child (BIST 30 dışı) → all book → 202.09 TL

Total: 48.9s (Component 4 batch'ten +5.5s, 2-phase overhead minimal)
```

## Bilinen Sınırlar (Faz 2.6+ Parking)

### 1. SAHOL Listed Children BIST 30 Dışı

**Problem:** ENJSA, AKGRT, AGESA, AKCNS, CIMSA, BRISA, KORDS, CRFSA, TKNSA — hiçbiri batch'te DCF lookup'a sahip → hep book_fallback.

**Çözüm seçenekleri:**
- A) BIST evren genişletme (BIST 30 → BIST 50)
- B) Holdings için child-specific DCF helper (recursive analyze tüm listed)
- C) Sabancı PDF'ten doğrudan market-based valuation (intrinsic sapması)

### 2. Banking Book Values PROVISIONAL

**Problem:** YKBNK (~$8B), AKBNK (~$12B) book equity rough estimate.

**Çözüm:** Faz 2.3.1 banking equity-only model — KAP'tan gerçek özkaynak fetch.

### 3. KCHOL TUPRS Effective Ownership (EYAS Chain)

**Mevcut:** %40 (KCHOL 86.6% × EYAS 46% TUPRS)
**Çözüm:** Annual KAP/Gedik raporu ile validate (yıllık güncelleme).

### 4. 16-Yıl Coverage Gap (BIMAS, SOKM)

Component 4 sonrası bilinen gap, Faz 2.5'te değişmedi. Lifecycle-adaptive years_back gerekli.

### 5. Negatif DCF Artifacts (PETKM, PGSUS)

Cycle dipi extreme. Distress-adjusted DCF (Faz 2.5+ Black-Scholes) çözecek.

## Output Files

- apps/api/outputs/bist_batch_LIVE_20260427_184141.csv (full data)
- apps/api/outputs/bist_batch_LIVE_20260427_184141.json (full data)

## Sonraki Adım

- ADIM 6: Faz 2.5 KAPANIŞ (kaldim.md + memory + atomic commit)
- Faz 2.6 adayları:
  - Banking equity-only model (Faz 2.3.1 backlog)
  - BIST evren genişletme (BIST 50)
  - Lifecycle-adaptive years_back (BIMAS+SOKM coverage fix)
  - Cycle bias refinement (FROTO/CCOLA extreme upside)

## REELDEĞER MILESTONE

Faz 2.5 SOTP integration tamamlandı. KCHOL/SAHOL holdings için
Damodaran-aligned intrinsic NAV hesabı production-ready. 4 atomic
commit (holdings_config + sotp.py + orchestrator + batch validation).

Industrial Component 1+2+3+4 anchor regression %100 korundu (TUPRS
188.29 TL ve 17 non-holding ticker INTACT).
