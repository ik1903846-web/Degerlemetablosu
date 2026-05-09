# ADR-040 Post-Mortem — Şubat 2026 Türkiye Ba3 Upgrade Kaçırılma Analizi

**Belge tarihi:** 9 Mayıs 2026
**Faz:** B1 Adım 8
**Önceki:** `docs/audit_findings_session4.md`, `docs/audit_decision_v4.md`, `docs/audit_progress_session4.md`

---

## 1. Bağlam

9 Mayıs 2026'da Damodaran `ctryprem.html` sayfasında "Turkey (updated February 2026)" notu fark edildi. Production `cost_of_capital.py` Ocak 2026 değerleri kullanmaya devam ediyordu:

| Parametre | Production (eski) | Damodaran resmi (Şub 2026) | Δ |
|-----------|-------------------|-----------------------------|---|
| Turkey CRP | 6.01% | 4.66% | −1.35 pp |
| Turkey Sov Spread | 4.46% | 3.06% | −1.40 pp |
| Mature ERP US | 4.44% | 4.23% | −0.21 pp |

Cost of Equity etkisi: −1.58 pp toplam staleness. DCF impact: +%15.62 (TUPRS shadow). Bu kaçırılma, 3 ay üstü bir gecikme yaratmıştır.

## 2. ADR-040 Mevcut Durumu

ADR-040 spec'i (`spec v2.2`): "Extraordinary event trigger (rating change, oil shock, crisis)". Yazılmış, **implement edilmemiş**.

`apps/api/scripts/fetch_damodaran.py` (v1) durumu:
- Line 4 docstring: "Faz 1.2 başlangıç (ADR-040b)" — sadece referans
- Trigger logic: YOK
- Cron entegrasyonu: YOK
- Page hash check: YOK (page-change anlamında)
- Vintage parser: KISMEN (ERP dinamik, ctryprem+betas hardcoded)

## 3. 4 Hipotez Test Sonuçları

### H1 — Cron yarıyıllık manuel → ara update'ler kaçıyor: **DOĞRULANDI**

Kanıt:
- Cron/systemd/yml entegrasyonu **sıfır** (`apps/api/config/scheduler.json` yok)
- Script docstring: "Manual run: python scripts/fetch_damodaran.py"
- Inline comment (line 63): "Damodaran ctryprem vintage (manual, yarıyıllık update)"
- `apps/api/data/damodaran/` audit öncesi **boş** (v1 hiç filesystem fetch yapmamış, DB-only)

Sonuç: Manuel rejim + disiplinsiz uygulama → 3 aylık gecikme.

### H2 — Event trigger sadece DOWNGRADE'de: **REDDEDILDI (yanlış formülasyon)**

Gerçek durum: Event trigger SİSTEMİ **tamamen yok**. Downgrade/upgrade ayrımı yapılamaz çünkü hiç trigger logic'i yok.

ADR-040 docstring'de referans var ("ADR-040b"), implementation eksik. Kararı yazıp unutmak.

### H3 — xlsx içi "updated [Month]" parser yok: **DOĞRULANDI**

Kanıt:
- `CTRYPREM_VINTAGE = "2025-12"` hardcoded (line 65)
- `BETAS_VINTAGE = "2026-01"` hardcoded (line 78)
- Inline comment: "Yarın smart parser eklenir (Excel cell'den extract)" — TODO 3+ ay açık
- `ERPbymonth.xlsx` için dinamik parse VAR (line 181-192) — ama ctryprem ve betas için yok
- Damodaran xlsx içinde:
  - "Summary of Most Recent Update" sheet (genel update tarihi)
  - "ERPs by country" sheet, "Turkey (updated February 2026)" notu Country kolonunda

Bu metadata parse edilmiyor → "Şubat update var" sinyali yakalanmıyor.

### H4 — Sayfa hash check yok: **DOĞRULANDI (yanıltıcı bulgu)**

Kanıt:
- `hashlib.sha256` var (line 103, 272, 446)
- AMA kullanım amacı: DB'de "duplicate detection" (parameter+vintage unique check, line 590-597)
- Page-change-detection için **HEAD request / Last-Modified / ETag check YOK**

Yani: "indirdiğim dosya DB'de var mı?" sorgusu var, "page sunucuda değişti mi?" sorgusu yok.

## 4. Kök Sebep Özeti

**Triple failure:**

1. **Schedule layer** — Manuel rejim, kimse periyodik yapmadı (H1)
2. **Vintage parsing layer** — Hardcoded sabitler, smart parser TODO (H3)
3. **Change detection layer** — Hash var ama yanlış amaçla (H4)

**Sistemik hata:** ADR-040 yazıldı, implement edilmedi. Karar dokümantasyonu var ama ürünleştirilmedi (disiplin açığı).

**Bonus güçlendirici:** Yarıyıllık manuel reminder de yoktu. Aralık 2025 ve Temmuz 2026 doğal kontrol noktaları boştu.

## 5. ADR-040 v2 Çözüm Spec'i (Session 5+ Implementation)

> **Önemli:** Bu sadece spec. Implementation Session 5+ kapsamında.

### 5.1 Smart Vintage Parser
- `Summary of Most Recent Update` sheet parse (genel update tarihi)
- `ERPs by country` sheet Country kolonunda regex: `r"\(updated (\w+ \d{4})\)"`
- 2 kaynak cross-check (uyumlu olmalı)
- Hardcoded `CTRYPREM_VINTAGE`, `BETAS_VINTAGE` kaldırılır

### 5.2 Page Hash Check (Daily)
- Günlük HEAD request her URL için
- Öncelik: ETag → Last-Modified → Content-MD5 → full body hash (resort)
- State dosyası: `apps/api/data/damodaran/_hash_state.json`
- Hash değişti → trigger fetch + parameters.json yaz

### 5.3 Scheduler Entegrasyonu
**Önerilen: GitHub Actions schedule** (zaten repo + log integration + free tier)
- `.github/workflows/damodaran_daily_check.yml`
- Cron: `0 6 * * *` (UTC günlük 06:00)
- Hash değişmediyse fetch atla, sadece log
- Hash değişti VEYA event trigger → fetch + commit + tag

Alternatifler (Session 5 kararı):
- B) systemd timer (VPS deploy senaryosu)
- C) Streamlit Cloud cron-like trigger (kısıtlı)
- D) Manuel daily reminder (acil failsafe)

### 5.4 Event Trigger Logic
- Sovereign rating change (Moody's/S&P feed veya Damodaran sayfa change)
- Oil shock > %20 (24h price change)
- US Treasury yield curve inversion (advisory)
- Major Fed action (advisory)
- **Upgrade VE downgrade ikisi de tetikler** (ADR-040 v1 hipotezi reddedildi)

### 5.5 Audit Trail
- Her fetch öncesi/sonrası diff log
- `apps/api/data/damodaran/_fetch_log.jsonl` append-only
- Significant Δ (>0.5 pp herhangi bir constant) → opsiyonel email/webhook
- Git commit auto-tag: `param-update-YYYY-MM-DD`

### 5.6 Failsafe
- Cron 48h fail → manuel alert
- Hash check fail → fallback full fetch
- Vintage parser başarısız → eski hardcoded + warning + alert
- Network/timeout → exponential backoff (max 3 retry)

## 6. Risk Register Güncelleme

| Risk | Olasılık | Etki | Mitigation |
|------|----------|------|------------|
| ADR-040 v2 Session 5'e ertelenir, bir update daha kaçar | Yüksek | Yüksek | Aralık 2026 + Temmuz 2027 manuel audit reminder |
| GitHub Actions cron rate limit | Düşük | Orta | Daily HEAD request hafif (1-2 req/day) |
| Vintage parser regex fragile | Orta | Orta | 2 kaynak cross-check + fallback hardcoded |
| Damodaran sayfa schema değişir | Düşük | Yüksek | Smart parser exception → manuel alert |

## 7. Geçici Köprü Önlemler (Session 5 Öncesi)

ADR-040 v2 implementation tamamlanana kadar:

1. **Aylık manuel kontrol:** Her ayın ilk haftası `fetch_damodaran_v2_audit.py` çalıştır, parameters.json diff
2. **Calendar reminder:** 1 Aralık 2026 ve 1 Temmuz 2027 — yarıyıllık doğal update zamanları
3. **Damodaran blog/Twitter takibi:** Aswath Damodaran significant update'leri duyurur

## 8. Sonuç

ADR-040 v2 spec yazıldı. Implementation Session 5+ kapsamında. Faz B1 audit sürecinde kullanılan toolchain (`fetch_damodaran_v2_audit.py`, `verify_damodaran_xlsx.py`, `diff_production_vs_damodaran.py`) Session 5 implementation'ın temeli olarak yeniden kullanılacak.

**Faz B1 ile ilgili son adım:** `audit_resolution_session4.md` (Adım 1-8 kapanış belgesi).

---

*Bu post-mortem read-only inspection sonucu. fetch_damodaran.py MODIFY EDİLMEDİ.*
