# REELDEĞER v4 — Session 4 Production Audit

**Audit tarihi:** 9 Mayıs 2026
**Audit kapsamı:** Spec v2.2 (24 Nisan 2026) parametre/formül uyumu vs Damodaran resmi kaynaklar
**Audit kaynağı:** `pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html` (last updated Jan 5, 2026, Turkey updated Feb 2026)
**Felsefe:** Sadece resmi kaynak. İş Yatırım yasak. Anchor disiplini > hız.

---

## 0. ÖN AYRIM — KRİTİK

Bu audit'te her bulgu için **iki ayrı katman** ayrılmalı:

**Katman A — Spec dokümantasyon (PDF'lerde yazan parametreler):**
v2.2 spec'in §15 "Güncel Parametre Paneli" tablosu 24 Nisan 2026 tarihli. Damodaran'ın Şubat 2026 Türkiye upgrade'ini kaçırmış olabilir.

**Katman B — Production runtime (Streamlit + Damodaran fetcher canlı çıktısı):**
Eğer ADR-040 event trigger ve aylık fetcher düzgün çalışıyorsa, production zaten güncel parametre kullanıyor olabilir; sadece spec PDF'i geride kalmış olur.

**İlk eylem (Audit Step 0):** Streamlit'te bir test şirketinin Cost of Equity output'unu kontrol et:
- Eğer ~14.4% civarında → spec parametreleri canlı, **kritik düzeltme gerekli**
- Eğer ~12.8% civarında → spec dokümantasyon stale, sadece dokümantasyonu güncelle

Aşağıdaki tüm bulgular **Katman A kesin** olarak doğrulanmıştır. Katman B duruma göre eylemi belirler.

---

## 1. KRİTİK BULGULAR

### 1.1 [P0-CRITICAL] Türkiye parametreleri eski

**Kanıt:** Damodaran resmi country risk tablosu, "Turkey (updated February 2026)" satırı:

| Parametre | Spec v2.2 | Damodaran resmi (Şub 2026) | Δ |
|---|---|---|---|
| Moody's rating | B1 | **Ba3** | upgrade kaçırılmış |
| Adj. default spread | 4.46% | **3.06%** | −1.40 pp |
| Country Risk Premium | 6.01% | **4.66%** | −1.35 pp |
| Total ERP (Aaa+CRP, λ=1) | 10.45% | **8.89%** | **−1.56 pp** |
| Sovereign CDS | (yok) | 2.85% | yeni veri |

**Etki:** Türkiye odaklı bir BIST şirketinde (β=1, λ=1) Cost of Equity **1.56 pp yüksek hesaplanıyor** → DCF değeri sistematik düşük → "ucuz değil" hatası.

**Sebep analizi:** ADR-040 (extraordinary event trigger) listesinde "sovereign rating change" var ama Şubat 2026 Ba3 upgrade'i otomatik fetch'lenmemiş.

### 1.2 [P0-CRITICAL] US default spread eski

| Parametre | Spec v2.2 | Damodaran resmi | Δ |
|---|---|---|---|
| US Moody's rating | (implicit Aa2) | **Aa1** | upgrade |
| US default spread | 0.33% | **0.23%** | −0.10 pp |
| Mature ERP | 4.44% | **4.23%** | −0.21 pp |

**Etki:** Tüm DCF'lerde mature ERP overstated → discount rate yüksek → tüm değerler az.

### 1.3 [P0-CRITICAL] Cost of Equity bileşik etki

Tipik BIST şirketi (β=1, λ=1, USD-bazlı):

Spec hesabı:
Rf_USD + β × Mature_ERP + λ × Turkey_CRP
= 3.97  + 1   × 4.44     + 1   × 6.01
= 14.42%
Damodaran resmi (Şubat 2026):
Rf_USD + β × Mature_ERP + λ × Turkey_CRP
= 3.95  + 1   × 4.23     + 1   × 4.66
= 12.84%
FARK: 1.58 pp


**DCF terminal value etkisi (kabaca):**
- g = 2.5% kabul edilirse:
- Spec: TV = CF / (14.42% − 2.5%) = CF / 11.92% = CF × 8.39
- Damodaran: TV = CF / (12.84% − 2.5%) = CF / 10.34% = CF × 9.67
- TV ratio: 9.67 / 8.39 = **1.153** → terminal value %15 daha yüksek olur

Stage 4 Mature Growth şirketleri için bu fark, içsel değer üzerinde **%10-20 underestimation** demek.

### 1.4 [P0-CRITICAL] TUPRS anchor durum kontrolü

Spec parametreleriyle anchor: 187.10 TL (Δ %0.28 tolerance, 52+ commit korunur).

**Damodaran resmi parametrelerle TUPRS yeniden hesaplandığında muhtemelen:**
- Discount rate düşeceği için: 187.10 → ~210-225 TL aralığında olur (kaba tahmin)
- Bu Δ tolerance'ı **kesinlikle aşar**
- Anchor disiplini bir karar gerektirir (bkz §6)

**Production runtime kontrolü olmadan kesin sayı verilemez** → Audit Step 0 sonucuna göre netleşir.

---

## 2. ORTA BULGULAR

### 2.1 [P1] Damodaran'ın yeni metodolojisi (post-Moody's downgrade) doğru uygulanmış

Damodaran sayfası Ocak 2026 güncellemesinde yeni formül:

Riskfree rate in US dollars = US treasury bond rate − Default spread for the US
ERP for US                   = Implied Expected Return on S&P 500 − Riskfree rate in US dollars
Mature market ERP            = ERP for US − Default spread for the US


Spec §6.1, §6.2'de bu formül **mantıken doğru** uygulanmış. Sadece parametre değerleri stale.

**Öneri:** Formül kodda dynamic olarak fetcher'dan geliyorsa Katman B sorunu yok.

### 2.2 [P1] "Valuations (Examples)" tablosu Damodaran tarafında boş

`valuationtools.html#valegs` anchor'undaki tablo header'ı var ama içeriği dolu değil. v2.2 spec'in §11'deki 20 validation case bu tablodan alınmamış — Dark Side, Narrative & Numbers PDF'leri ve blog post'lardan derlenmiş.

**Sonuç:** Spec doğru kaynak kullanmış. Bu boş tablo sadece web sayfası issue'su, validation methodology etkilenmiyor.

### 2.3 [P1] Spreadsheet kapsama eksikleri

Damodaran'ın resmi listesinden spec'te bahsedilmemiş ama yararlı olanlar:

| Spreadsheet | Spec durumu | Önerilen öncelik | Gerekçe |
|---|---|---|---|
| `growthbreakdown.xls` | Bahsedilmemiş | **Orta** | Growth premium hesabı, intrinsic vs relative cross-check |
| `buybacks.xls` | YOK / Düşük | **Orta** | Damodaran 2025+ buyback önemini artırdı |
| `synergyvaluation.xls` | YOK | Düşük (Faz 5+) | M&A senaryoları için |
| `complscore.xls` | Bahsedilmemiş | Düşük | Şirket karmaşıklık skoru, holding analizi için |
| `multiplecalculator.xls` | Bahsedilmemiş | Orta | Faz 4 Relative Valuation için |
| `evavaln.xls` / `fcffeva.xls` | Bahsedilmemiş | Orta | EVA-DCF reconciliation, ADR-024 cross-check |

### 2.4 [P1] fcffsimpleginzu vs fcffginzu primary seçimi

Spec primary olarak `fcffsimpleginzu.xlsx` seçmiş (ADR-024).

Damodaran'ın kendi tarifi:
- `fcffsimpleginzu` — "few inputs, default assumptions, quick all-in-one"
- `fcffginzu` — "ratings + earnings normalizer + R&D + lease + bottom-up beta hepsi içinde"

**Konservatif 1M TL portföy için fcffginzu (full) daha defensive.** Sadeleştirme riski: bazı düzeltmeler (lease, R&D, options) atlanmış olabilir.

**Öneri:** İki spreadsheet'i parallel runner ile çalıştır, sapma > %3 ise warning üret.

---

## 3. DÜŞÜK ÖNCELİK BULGULAR

### 3.1 [P2] Sektör beta'sı yenilenme tarihi belirsiz

Damodaran her Ocak ayında yıllık güncelleme yapar, Mart sonuna kadar tamamlar. Spec'te "Yıllık (Ocak)" denmiş ama sistemin son fetch tarihi audit edilmeli.

### 3.2 [P2] uValue iOS app referans dışı

Son güncelleme Haziran 2020. Production'a girmiyor, sadece kavramsal referans. v4 sisteminde rolü yok, çıkarılabilir.

### 3.3 [P2] financetools.idc.ac.il Beta strategy 4. seçenek

Damodaran resmi tools sayfasında listelenmiş (Eran Ben Horin team). Bottom-up beta için manuel cross-check katmanı olarak değerlendirilebilir — bekleyen Beta strategy kararına ek seçenek.

---

## 4. SPEC'İN DOĞRU YAPTIĞI ŞEYLER (DEĞİŞTİRME)

Bu bölüm Session 4'te yanlışlıkla "düzeltilmemesi" gereken kararları vurgular:

1. **Lambda formülü (revenue-based):** Doğru. Damodaran §6.4 ile uyumlu.
2. **3-method CRP (rating / CDS / equity-adjusted):** Doğru. Damodaran sayfası bunu doğruluyor.
3. **6-stage lifecycle:** Damodaran 2024 Corporate Life Cycles kitabıyla uyumlu.
4. **Banking firm valuation YASAK, equity-only zorunlu:** Damodaran finsvc.pdf ile uyumlu.
5. **20 validation case kaynakları:** Doğru kaynaklar (Dark Side, Narrative & Numbers, blog).
6. **Cell-level replication protocol (ADR-048):** Damodaran best practice.
7. **±%5 tolerance:** Standard.
8. **USD-only valuation, TL DCF yasak (ADR-002):** Doğru, inflation/FX consistency.
9. **3-sleeve portfolio architecture (ADR-066):** Damodaran'ın philosophical alignment ile uyumlu.
10. **Pentagon scoring 30/25/20/15/10 + lifecycle-adjusted weights:** Tutarlı.

---

## 5. EYLEM PLANI

### Faz A — ACİL (Audit Step 0 öncesi)

| # | Eylem | Süre |
|---|---|---|
| A1 | Streamlit'te bir test şirketinin Cost of Equity output'unu logla | 5 dk |
| A2 | 14.4% mı, 12.8% mı? Belirle | 1 dk |
| A3 | Bu raporu (`audit_findings_session4.md`) `docs/` altına commit'le | Claude Code |

### Faz B1 — Eğer Cost of Equity ~14.4% (production parametreleri eski)

| # | Eylem | Risk |
|---|---|---|
| B1.1 | Damodaran fetcher manuel run, Şubat 2026 Türkiye update'i çek | Düşük |
| B1.2 | `parameters.json` veya equivalent config'i update et | Düşük |
| B1.3 | TUPRS dahil tüm hesapları yeniden çalıştır | Anchor riski! |
| B1.4 | TUPRS yeni değerini logla, anchor karar matrisine giriş | — |
| B1.5 | ADR-040 event trigger post-mortem, neden Şubat update'i kaçırıldı? | — |

### Faz B2 — Eğer Cost of Equity ~12.8% (production zaten güncel)

| # | Eylem |
|---|---|
| B2.1 | Spec PDF'i v2.3'e revize et (sadece §15 parametre paneli + ADR-040 status notu) |
| B2.2 | Production değişiklik gerekmez |
| B2.3 | TUPRS anchor zaten güncel parametrelerle hesaplandıysa 187.10 doğru |

### Faz C — Session 5 kapsamına eklen

| # | Eylem |
|---|---|
| C1 | KAP feed listener + **Damodaran ctryprem haftalık check** (ADR-040 robusteme) |
| C2 | `growthbreakdown.xls` modülü ekle (Faz 4 Relative için ön hazırlık) |
| C3 | `buybacks.xls` priority Düşük → **Orta** yükselt |
| C4 | `fcffginzu` (full) parallel runner — `fcffsimpleginzu` ile tutarlılık testi |
| C5 | financetools.idc.ac.il Beta strategy 4. seçenek olarak değerlendir |

### Faz D — Session 6 kapsamına eklen

| # | Eylem |
|---|---|
| D1 | uValue iOS app referansını envanterden çıkar |
| D2 | Spec v3.0 hazırla (audit findings'i yansıt) |
| D3 | Atomic cutover sırasında `evavaln.xls` cross-check entegrasyonu |

---

## 6. ANCHOR KARAR MATRİSİ

TUPRS 187.10 anchor'ı 52+ commit korunmuş. Damodaran düzeltmesi sonrası muhtemelen yukarı revize olur. Üç seçenek:

### Seçenek 1: Anchor 187.10'u koru, Damodaran update'i v4.1 yan-anchor olarak işaretle

**Pro:**
- Disiplin korunur, geriye dönük tutarlılık
- Session 3 mührü bozulmaz
- Tarayıcı'nın geçmiş çıktıları geçerli kalır

**Con:**
- Bilinçli olarak güncel olmayan parametre kullanmış olursun
- 12 BIST hissesi "doğru hesapla ucuz" olabilirken sistem "değil" diyor
- Yatırım kararlarında **systematic bias**

### Seçenek 2: Damodaran resmi paramlerle TUPRS yeniden hesapla, yeni anchor ilan et

**Pro:**
- Doğru parametre = doğru karar
- Damodaran felsefesine sadık (intrinsic value matters, not anchor inertia)
- 1M TL konservatif portföy için defansif

**Con:**
- 52+ commit'lik anchor disiplini kırılır
- Geçmiş Tarayıcı çıktıları "v4 öncesi" olarak işaretlenir
- Session 3 mühürlü iş kısmen invalidate olur

### Seçenek 3 (ÖNERİLEN): Hibrit — Audit Step 0 sonucuna göre branch et

**Karar ağacı:**


Audit Step 0 sonucu:
├─ Cost of Equity ~14.4% (production stale)
│  └─ Seçenek 2 zorunlu (yanlış parametre = yanlış değer = yanlış karar)
│     ├─ TUPRS yeni anchor: yeniden hesapla ve ilan et
│     └─ Eski anchor: “v4-pre-Feb2026” tag’iyle archive et
│
└─ Cost of Equity ~12.8% (production zaten güncel)
└─ Seçenek 1 zorunlu (anchor zaten doğru parametreler ile hesaplanmış)
├─ TUPRS 187.10 INTACT
└─ Sadece spec PDF güncellemesi yeterli


**Önerilen final karar:** Audit Step 0'ı çalıştırmadan anchor kararı verme. **Karar production state'in fonksiyonu.**

---

## 7. ADR-REVİZE ÖNERİLERİ

Aşağıdaki ADR'ler audit findings'e göre revize edilmeli:

| ADR | Mevcut | Önerilen değişiklik |
|-----|--------|---------------------|
| ADR-005 | 3-kadans + event trigger | **Haftalık ctryprem check ekle** (event trigger backup) |
| ADR-040 | Extraordinary event trigger | **Sovereign rating change için aylık otomatik kontrol** zorunlu |
| ADR-024 | fcffsimpleginzu primary | **fcffginzu parallel runner ekle**, sapma > %3 warning |
| ADR-027 | Turkey Macro Benchmark PE=12 | **Şubat 2026 Ba3 upgrade'i not düş** |
| ADR-055 | 5-Failure Metric Tracker | **6. metric ekle: parameter staleness (max 30 gün)** |

---

## 8. SONUÇ

**Kesin tespit (Katman A):**
Spec dokümantasyonu (PDF, 24 Nisan 2026) Damodaran'ın Şubat 2026 Türkiye upgrade'ini ve Ocak 2026 US Aa1 upgrade'ini yansıtmıyor. Spec parametreleriyle Cost of Equity 1.58 pp yüksek hesaplanır.

**Belirsizlik (Katman B):**
Production runtime'da gerçek hesaplama parametreleri ne durumda? Bu **Audit Step 0** ile netleşir.

**Yapılmaması gereken:**
- Audit Step 0 olmadan production code'a dokunma (`orchestrator.py` + `isyatirim_scraper.py` Session 6 atomic cutover'a kadar mühürlü, kural devam ediyor)
- Anchor değişikliği kararını Audit Step 0 olmadan verme
- Spec felsefesinin doğru parçalarını "düzeltmek" iddiasıyla değiştirme (§4 listesi)

**Yapılması gereken:**
- Audit Step 0'ı **bugün** çalıştır
- Sonuca göre Faz B1 veya B2'ye gir
- Bu doküman audit baseline olarak repo'da kalsın (`docs/audit_findings_session4.md`)

---

## EKLERİ — KAYNAK DOĞRULAMASI

**Damodaran country risk tablosu fetched 9 Mayıs 2026:**
- URL: `https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html`
- Last updated: January 5, 2026 (Turkey row updated February 2026)
- Direct quote: "Turkey (updated February 2026) | Ba3 | 3.06% | 4.66% | 8.89% | 25.00% | 2.85% | 8.56%"

**Damodaran yeni metodoloji (post-Moody's US downgrade):**
- URL: aynı sayfa
- Direct quote: "Riskfree rate in US dollars = US treasury bond rate minus Default spread for the US. ERP for US = Implied Expected return on the S&P 500 minus Riskfree rate in US dollars. Mature market ERP = ERP for US minus Default spread for the US"

**ERP 2026 paper:**
- URL: `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6361419`
- Title: "Equity Risk Premiums (ERP): Determinants, Estimates and Implications - The 2026 Edition"
- Date: March 5, 2026
- Author: Aswath Damodaran

---

## DOKÜMAN SONU

**Audit imzası:** Bu doküman Session 4 öncesi production state baseline'ıdır. Karar çıkarıldıktan sonra `audit_findings_session4_resolved.md` ek belgesi ile kapatılır. Spec v3.0 bu audit'i yansıtacak şekilde Session 4 sonunda hazırlanır.
