# REELDEĞER v4 — Session 4 Audit Decision

**Karar tarihi:** 9 Mayıs 2026
**Karar veren:** Claude Opus 4.7 (kullanıcı yetkilendirmesi: "sen karar ver")
**Önceki belge:** `docs/audit_findings_session4.md`
**Karar tipi:** Production parameter staleness remediation

---

## KARAR ÖZETİ

**Faz B1 (parametre düzelt + anchor karar) seçildi.**

Kullanıcı "sen karar ver" yetkilendirmesiyle, Claude (audit eden) iki ihtimal arasında en güvenli yolu seçti. Streamlit runtime'a doğrudan erişim olmadığı için "production zaten güncel mi?" sorusu kesin yanıtlanamadı. Ancak:

1. Damodaran resmi sayfası (Şubat 2026 Türkiye upgrade) **kanıtlandı**
2. Spec PDF'i (24 Nisan 2026) bu update'i **yansıtmıyor** (kanıtlandı)
3. Spec yazımında bilinmiyorsa fetcher'ın da çekmediği **olası** (P > 0.5)

Her iki ihtimalde de "kontrol + düzeltme" zorunlu → Faz B1 baseline.

---

## NEDEN B2 DEĞİL B1?

**Faz B2 (production zaten güncel, sadece spec güncelle):**
- Bu yola gitmek için "production runtime Cost of Equity ~12.84%" emin olmak şart
- Şu an emin olunamıyor
- Yanlış bilgilendirme = 1.58 pp yanlış discount rate = sistematik DCF hatası → 1M TL portföy üzerinde çok büyük bias

**Faz B1 (kontrol + düzelt):**
- Önce ölç, sonra hareket et
- Anchor disiplinine saygı gösterir (ama 6a yumuşak geçiş ile)
- "Disiplin > hız" kuralına uygun
- Damodaran felsefesine sadık ("intrinsic value matters, not anchor inertia")

**Karar gerekçesi:** Faz B1 hem yanlış parametre riskini, hem anchor disiplini riskini eşzamanlı yönetir.

---

## 8 ADIMLIK KADEMELİ GEÇİŞ

### Adım 1 — TANI (anchor INTACT)
**Amaç:** Yeni Damodaran verisini sisteme alma, henüz uygulamadan.
**Eylem:**

    fetch_damodaran() → /data/damodaran_2026_05_09/
      ├─ ctryprem.xlsx
      ├─ ERPbymonth.xlsx (Mayıs sütunu)
      └─ histimpl.xlsx

**Risk:** Sıfır. Read-only fetch.
**Çıktı:** Yeni data folder. Production config dokunulmamış.

---

### Adım 2 — DIFF RAPORU (anchor INTACT)
**Amaç:** Eski vs yeni parametre farkını **yan-script** olarak hesapla.
**Eylem:**

    # /scripts/parameter_diff.py — standalone, production code'a dokunmaz
    diff_report = compare_parameters(
        old=production_config,
        new=damodaran_2026_05_09
    )
    # Çıktı: /reports/parameter_diff_2026_05_09.csv

**Beklenen diff:**
| Param | Old | New | Δ |
|---|---|---|---|
| Turkey rating | B1 | Ba3 | upgrade |
| Turkey default | 4.46% | 3.06% | −1.40 pp |
| Turkey CRP | 6.01% | 4.66% | −1.35 pp |
| US default | 0.33% | 0.23% | −0.10 pp |
| Mature ERP | 4.44% | 4.23% | −0.21 pp |

**Risk:** Sıfır. Sadece rapor üretir.
**Karar:** Eğer diff sıfırsa → STOP (production zaten güncel, Faz B2'ye dön). Aksi halde devam.

---

### Adım 3 — TEST ŞİRKETİ DOĞRULAMASI (anchor INTACT)
**Amaç:** Anchor olmayan bir test şirketi üzerinde sapmayı ölç.

**Test şirketi seçimi:** TTRAK (Türk Traktör) **önerilen**.
- Mature Stable evre
- λ ortalama (ihracat var ama domestic ağırlıklı)
- Likit, KAP raporları temiz
- Stage 4 (Mature Growth) profil

**Alternatifler:** FROTO, AYGAZ. Holding değil, banking değil.

**Eylem:**

    # Standalone benchmark
    ttrak_old = dcf(ticker='TTRAK', params=production_config)
    ttrak_new = dcf(ticker='TTRAK', params=damodaran_2026_05_09)
    sapma = (ttrak_new - ttrak_old) / ttrak_old * 100

**Beklenen sapma:** %12-18 yukarı (Cost of Equity 1.58 pp düşüşü → terminal value ~%15 artış).

---

### Adım 4 — KARAR NOKTASI #1
**Sapma yorumu:**
- **< %5:** Production muhtemelen zaten güncel, Faz B2'ye geç. Sadece spec PDF güncelle.
- **%5-25:** Beklenen aralık. Adım 5'e devam.
- **> %25:** STOP. Audit derinleştir, beta veya λ hesabında bug var.

---

### Adım 5 — TUPRS GÖLGE HESAP (anchor 187.10 hala INTACT)
**Amaç:** TUPRS'u yeni parametrelerle hesapla, ama **anchor olarak ilan etme.**

**Eylem:**

    tuprs_v4_0_anchor = 187.10  # 52+ commit korunan değer
    tuprs_v4_1_shadow = dcf(ticker='TUPRS', params=damodaran_2026_05_09)

    print(f"v4.0 anchor:  {tuprs_v4_0_anchor:.2f} TL (Ocak 2026 params)")
    print(f"v4.1 shadow:  {tuprs_v4_1_shadow:.2f} TL (Şubat 2026 params)")
    print(f"Δ: {(tuprs_v4_1_shadow / tuprs_v4_0_anchor - 1) * 100:+.2f}%")

**Beklenen shadow değer:** 210-225 TL aralığında.

---

### Adım 6 — KARAR NOKTASI #2 (anchor disiplini)

**Önerilen: 6a Yumuşak geçiş**

    v4.0 anchor (187.10 TL) → Git tag: anchor-v4.0-pre-Feb2026
    v4.1 anchor (TUPRS shadow değer) → resmi yeni anchor
    Geçiş tarihi: bugün
    Yeni Δ tolerance: %0.50 (geçiş ayında esnek, sonra %0.30'a sıkılaşır)

**Reddedilen alternatifler:**
- 6b Çift anchor → operasyonel karmaşa, belirsizlik kaynağı
- 6c Anchor değiştirmeme → diğer şirketler güncel hesaba göre, TUPRS eski → bilimsel olmuyor (apples-to-oranges)

**Argüman:** Damodaran'ın "Hümilite Protokolü" (ADR-063) zaten "öncek tahminler raporu + yanılma pattern analizi" zorunlu kılıyor. v4.0 anchor'ı archive etmek bu protokolün gereği.

---

### Adım 7 — PRODUCTION CONFIG UPDATE (kod DEĞİL, sadece config)
**Eylem:**

    # parameters.yaml veya equivalent
    turkey:
      rating: Ba3        # was: B1
      default_spread: 0.0306   # was: 0.0446
      crp: 0.0466        # was: 0.0601
      total_erp_lambda1: 0.0889  # was: 0.1045
    us:
      rating: Aa1        # was: Aa2 implicit
      default_spread: 0.0023   # was: 0.0033
    mature_erp: 0.0423   # was: 0.0444
    last_damodaran_fetch: 2026-05-09
    last_turkey_update: 2026-02-XX  # Damodaran resmi notu

**Yasak:** `orchestrator.py`, `isyatirim_scraper.py`, `kap_excel_fetcher.py` vs. dokunulmaz (Session 6 atomic cutover kuralı).

---

### Adım 8 — ADR-040 POST-MORTEM
**Soru:** Şubat 2026 Türkiye upgrade'i neden otomatik fetch'lenmedi?

**Hipotezler:**
1. Fetcher cron schedule yarıyıllık → ara update'leri kaçırıyor
2. Event trigger sadece "downgrade" kategorisinde → upgrade'leri filtreliyor
3. ctryprem.xlsx dosyası içinde "Turkey (updated February 2026)" satır notu parse'lenmemiş
4. Sayfa hash check yok → değişikliği fark etmiyor

**Çözüm önerisi:**

    ADR-040 v2:
      - Aylık fetch zorunlu (yarıyıllık + 6 aylık ara fetch)
      - Sayfa hash check günlük (ucuz)
      - "updated [Month Year]" parser
      - Hem upgrade hem downgrade trigger

---

## EK DÜZENLEMELER (linklerden ek bulgu)

### Düzenleme #1 — ERP for US sütunu kullanımı
Damodaran tablosunda direkt "Equity Risk Premium" sütunu var (Türkiye için %8.89 = Mature 4.23 + CRP 4.66). Production'da default için bu sütunu **direkt** kullan, lambda hesabı için ayrıştır. Aritmetik hata sıfıra iner.

### Düzenleme #2 — Sovereign CDS cross-check
Damodaran tablosunda `Sovereign CDS` ve `ERP based on sovereign CDS` sütunları var. Türkiye CDS 2.85% → CDS-based ERP 8.56%. Rating-based ERP 8.89%. Fark 0.33 pp.

**Eylem:** ERP_rating ile ERP_CDS arasındaki farkı her audit run'da logla, > %1 puan fark = warning.

### Düzenleme #3 — Haftalık sayfa hash check
ctryprem.html "Last updated: January 5, 2026" diyor, ama Türkiye satırı Şubat'ta güncellenmiş. Yarıyıllık fetcher bu ara update'leri kaçırır.

**Çözüm:** Haftalık `HEAD` request, `Last-Modified` veya page hash kontrolü. Eğer değişmişse full fetch tetikle. Cost: günlük 1 HTTP request, sıfıra yakın.

---

## KIRMIZI ÇİZGİLER

| Yasak | Sebep |
|---|---|
| `orchestrator.py` veya `isyatirim_scraper.py`'a dokunmak | Session 6 atomic cutover kuralı |
| Anchor'ı gerekçesiz değiştirmek | 52+ commit disiplini — sadece 6a yumuşak geçiş ile |
| Test şirketi olarak TUPRS kullanmak | Anchor riski — TTRAK öner |
| Tüm 251 ticker'ı tek seferde yeniden hesaplamak | Single big-bang yasak |
| Spec felsefesini "düzeltmek" | Audit findings §4 koruma listesi (10 madde) |
| AI/LLM API kullanmak | Bütçe kuralı |

---

## SONRAKİ KARAR NOKTALARI

| Adım | Karar tetikleyici | Aksiyon |
|---|---|---|
| Adım 4 | Sapma %5-25 dışında | Audit yeniden aç |
| Adım 6 | Shadow değer 200 TL altında | Lifecycle yanlış sınıflandırma kontrolü |
| Adım 8 | Post-mortem 4 hipotezden hangisi | ADR-040 v2 yeniden yaz |

---

## DOKÜMAN SONU

Bu karar belgesi `audit_findings_session4.md`'nin devam belgesidir. Adım 1-8 tamamlandığında `audit_resolution_session4.md` ek belgesi yazılacak. Spec v3.0 Session 4 sonunda bu kararı yansıtacak şekilde hazırlanır.

**Onay:** Bu karar belgesi kullanıcının "sen karar ver" yetkilendirmesi ile Claude tarafından imzalanmıştır. Adımlar Claude Code tarafından yürütülür, her adım sonrası kullanıcı onayı alınmadan bir sonraki adıma geçilmez.
