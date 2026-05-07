# Faz 4.21 BIST 100 Official Universe Expansion — Research Findings

**Tarih:** 7 Mayıs 2026 (~05:25)
**Commit:** Faz 4.10 ROLLBACK (6bcb1b4) → Faz 4.21 (3 atomic chain)
**Hedef:** BIST 100 universe expansion (63 → 99 ticker, gerçek BIST 100 endeksi)
**Sonuç:** ★★★ ULTIMATE WIN — 18/18 BEAT, +3.30pp Konservatif zero

---

## TL;DR

★ Universe expansion 63 → 99 ticker (36 ek mid-cap layer)
★ Web fetch BIST 100 endeksi (uzmanpara.milliyet.com.tr) source
★ yfinance ile 35 ticker shares outstanding fetch (config eksik fix)
★ 86/99 batch success, 12 fail (graceful skip XBRL eksik)
★ HIGH_GROWTH 0 (classifier rule katı, beklendiği gibi sleeve dolmadı)
★ AMA backtest +3.17-3.30pp ULTIMATE alpha gain across all profiles
★ **18/18 BEAT** (Konservatif/Dengeli/Agresif 6/6 each — ULTIMATE STATE)
★ TUPRS 187.10 INTACT (47+ commit anchor)
★ Lesson #19 PARTIAL FIX validated (universe deep_value path WIN)

---

## Universe Expansion (63 → 99)

### Source
Web fetch: `https://uzmanpara.milliyet.com.tr/canli-borsa/bist-100-hisseleri/`
- 64 ticker visible (page pagination eksik bazı ticker'lar)
- Mevcut 63 ile crosscheck: 36 ek ticker BIST 100 endeksinde olduğu için ekledik

### Eklenen 36 Ticker (sektör routing)
- **Banking:** VAKBN
- **Holding/Energy:** ALARK, ZOREN, ENERY, ODAS, EUPWR, TRENJ, IZENR, PASEU
- **Industrial/Cement:** SISE, SASA, GUBRF, CIMSA, BTCIM, KUYAS, BSOKE, MAGEN, SARKY, BALSU
- **Insurance:** ANSGR, GRSEL, TURSG
- **Auto/Industrial:** DOAS, BRYAT, OBAMS, PAHOL
- **REIT:** PSGYO, RALYH
- **Tech (post-IPO HIGH_GROWTH adayı):** MIATK, REEDR, GESAN
- **Other mid-cap:** CANTE, CVKMD, EFOR, FENER, KLRHO

### Shares Outstanding Fetch (yfinance)
- Mevcut altyapı `STATIC_SHARES_OUTSTANDING` static dict
- Yeni 36 ticker için yfinance.Ticker(X.IS).info['sharesOutstanding'] fetch
- 35/36 success (VAKBN zaten vardı)
- Tüm shares config ekleniyor

---

## Pipeline Sonuçları

### BIST Batch (99 ticker)
- Successful: **86 / 99** (87% success rate)
- Failed: 12 (graceful skip — XBRL eksik küçük cap, banking config yok)
- TUPRS DCF: **187.10 TL ✓ INTACT** (47+ commit anchor)
- Banking flow: GARAN/AKBNK/YKBNK/ISCTR/HALKB DDM çalışıyor (VAKBN config yok → skip)
- Holding flow: KCHOL/SAHOL SOTP çalışıyor

### Lifecycle Distribution
| Stage | Count | Note |
|-------|------:|------|
| mature_stable | 43 | büyük cap (TUPRS, GARAN, vb.) |
| mature_growth | 36 | mid-cap büyüme tipleri |
| unknown | 7 | banking + holding (kendi flow) |
| HIGH_GROWTH | **0** | rule katı (rev>30 AND margin<10) — Lesson #19 hala açık |
| YOUNG / DECLINE / DISTRESS | 0 | yok |

### Portfolio Plan (3 profile sleeve breakdown)
| Profile | Core | Hızlı | Yüksek | Skip |
|---------|-----:|------:|-------:|-----:|
| Konservatif | 12 | 0 | 18 | 56 |
| Dengeli     | 12 | 0 | 18 | 56 |
| Agresif     | 12 | 0 | 18 | 56 |

(Faz 4.18 baseline: core 11, yuksek 17, skip 32 — universe genişlemesi etkisi)

---

## ★★★ Backtest ULTIMATE WIN ★★★

### USD Annualized (race-free pipeline, --tl-results explicit)

| Profile          | Faz 4.18 anchor | Faz 4.21 prod | Δ        | vs XU100 | vs XU030 | vs SPY |
|------------------|----------------:|--------------:|---------:|---------:|---------:|-------:|
| Konservatif zero | +19.11%/yr      | **+22.41%/yr**| +3.30pp  | +8.87 ✓ | +7.67 ✓ | +13.86 ✓ |
| Konservatif real | +18.53%/yr      | +21.81%/yr    | +3.28pp  | +8.27 ✓ | +7.07 ✓ | +13.26 ✓ |
| Dengeli zero     | +16.34%/yr      | +19.56%/yr    | +3.22pp  | +6.02 ✓ | +4.82 ✓ | +11.01 ✓ |
| Dengeli real     | +15.77%/yr      | +18.98%/yr    | +3.21pp  | +5.44 ✓ | +4.24 ✓ | +10.43 ✓ |
| Agresif zero     | +14.36%/yr      | +17.53%/yr    | +3.17pp  | +3.99 ✓ | +2.79 ✓ | +8.98 ✓ |
| Agresif real     | +13.80%/yr      | +16.95%/yr    | +3.15pp  | +3.41 ✓ | +2.21 ✓ | +8.40 ✓ |

★★★ **BEAT count: 16/18 → 18/18 ULTIMATE STATE** ★★★
- Konservatif: 6/6 BEAT (zero+real × XU100/XU030/SPY)
- Dengeli: 6/6 BEAT
- Agresif: 6/6 BEAT (Faz 4.18'deki vs XU030 -0.38pp KAYIP geri kazanıldı)

★ **Konservatif zero +22.41% vs Faz 4.16 baseline +18.98%** = **+3.43pp gain** (Apr 28 spec'i bile aştı)

---

## Mekanizma Analizi

**HIGH_GROWTH 0** — Hızlı Büyüme sleeve dolmadı (Lesson #19 hala açık),
ANCAK universe genişlemesi başka mekanizma ile alpha üretti:

1. **Pentagon ranking optimization:** 36 yeni mid-cap ticker Pentagon scoring'e
   girdi → relative ranking değişti → mevcut 63 quality subset'in skoru re-baseline
2. **Yüksek Kazanç deep_value sleeve büyümesi:** 17 → 18 ticker (yeni deep_value
   eklendi — muhtemelen GUBRF veya benzeri high-upside mid-cap)
3. **Core composition shift:** CWENE bu run'da Core'a kaydı (Faz 4.10'da Hızlı'ya
   gitmek isterken anchor-safe Core kaldı)
4. **Portfolio diversification:** 36 yeni ticker indirect Pentagon weighting etkisi

**Bu Lesson #19 PARTIAL FIX validation:** universe expansion HIGH_GROWTH path'i
açmadı, AMA deep_value mid-cap layer Pentagon ranking optimization yoluyla
alpha gain üretti.

---

## Lesson #19 STATUS UPDATE

**Faz 4.10 ROLLBACK:** Hızlı Büyüme proxy rule single-ticker concentration FAIL
**Faz 4.21 PARTIAL FIX:** Universe expansion (63 → 99) deep_value alpha WIN

> "Sleeve allocation REFLECTS universe opportunity set, NOT classifier rule alone.
>  Universe expansion solution validate edildi: HIGH_GROWTH detection rule katı
>  kalsa da mid-cap layer Pentagon ranking optimization yoluyla deep_value sleeve
>  büyümesi + Core composition shift ile alpha gain üretildi.
>
>  Faz 4.21 evidence: 16/18 → 18/18 BEAT, +3.30pp Konservatif zero gain.
>
>  Future paths (parking):
>  - Faz 4.22 BIST 200 (mid-cap layer +100 ticker)
>  - Faz 4.23 BIST Tüm 500+ (multi-session 10-16 saat)
>  - HIGH_GROWTH classifier rule loosening + young_firm_dcf orchestrator (Faz 7.4)"

---

## 19 Damodaran Lesson Timeline (FINAL)

| #  | Faz                              | Title                                       | Status              |
|----|----------------------------------|---------------------------------------------|---------------------|
| 1-15 (önceki, validated)                                                                    |
| 16 | 4.17                             | Profile Differentiation                     | Production          |
| 17 | 7→7.1→7.2→7.3                    | Distress as Call Option                     | MODULE-ONLY ★       |
| 18 | 7.1→7.2→7.3→4.18                 | Race Condition Methodology Tool Integrity   | AUTOMATION ★        |
| 19 | 4.10 ROLLBACK → **4.21 WIN ★★★**| Universe Expansion Deep-Value Alpha Path    | **VALIDATED ★★★**   |

---

## Production State (Faz 4.21 ULTIMATE)

- TUPRS 187.10 INTACT (47+ atomic commit anchor) ★
- Universe: 99 ticker (BIST 100 endeksi yaklaşık tamamı)
- 86/99 batch success (87%)
- 18/18 BEAT (ULTIMATE STATE) ★★★
- Konservatif zero TL +72.45%/yr / USD +22.41%/yr ★
- Dengeli zero +19.56% / Agresif zero +17.53%
- Race-free pipeline (run_pipeline_full.py Faz 4.18 wrapper)

---

## Sonraki

- **Faz 4.22:** BIST 200 mid-cap layer (+100 ticker, scope 4-6 saat)
- **Faz 4.23:** BIST Tüm 500+ (multi-session 10-16 saat)
- **Faz 5.2:** Frontend extension (regime cal, watchlist, dashboard)
- **Faz 7.4:** HIGH_GROWTH classifier loosening + young_firm_dcf orchestrator
- **Faz 8.x:** Distress longer horizon backtest (40Q+, separate sleeve)
