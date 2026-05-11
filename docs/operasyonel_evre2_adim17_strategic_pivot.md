# Operasyonel Sertlestirme Evre 2 Adim 1.7 — Stratejik Pivot

**Tarih:** 11 Mayis 2026
**Karar:** CI auto-regen iptal, Local regen + CI validation hibrit (Plan B)

## Olay Tarihcesi (7 Run Kanit)

| Run | Commit | Sonuc | Bulgu |
|-----|--------|-------|-------|
| #1  | 4d65a9e | False PASS | _regen_phase1.py yok, tee yutuldu (29s) |
| #2  | 4d65a9e | FAIL | Re-run, ayni eksik dosya |
| #3  | 414d172 | FAIL | httpx ModuleNotFoundError, pipefail PASS |
| #4  | dc347f6 | FALSE PASS | Universe=0, sanity yutuldu, production hasar (Bug B) |
| #5  | b01448f | FAIL | Universe fallback eklendi ama CSV yok |
| #6  | 72b0aab | FAIL | Universe 615 (seed), kap_excel cache yok, NaN patlama |
| #7  | df7d80a | FAIL + Diagnostic | KAP SPA + Yahoo 429, gercek root cause |

## Root Cause — CI Constraints

### KAP (Kamuyu Aydinlatma Platformu)
- HTTP erisim: 200 OK (erisim var)
- Content: Next.js SPA (JavaScript render)
- httpx GET 2 MB HTML alir AMA tablo verisi script icinde
- Cozum gereksinimi: Headless browser (Playwright/Selenium)
- CI'da kurulum: 50+ MB Chromium download, ~10 dk runtime, fragile

### Yahoo Finance (yfinance)
- HTTP erisim: 429 Too Many Requests
- CI runner IP'leri Yahoo tarafindan rate-limit'lenmis
- Cozum gereksinimi: Proxy veya VPN
- CI'da uygulanabilirlik: Maliyetli, etik gri alan

### Damodaran (kontrol)
- HTTP erisim: 200 OK
- Content: Static HTML (Excel/PDF linkler)
- Sorun yok — bu yuzden Damodaran daily check workflow CALISIYOR

## 3 Katmanli Savunma Dogrulamasi

Tum 7 run boyunca production turkey_v4_batch.json bir kez haric INTACT kaldi:

**Katman 0 — Universe fallback (commit 43):**
- Run #5'te ilk kez tetiklendi
- kap_float CSV yoksa FATAL exit 1
- Production hasarina engel

**Katman 1 — Sanity pipefail (commit 43):**
- Run #5'ten itibaren her false-positive engellenmis
- Run #4 oncesi olsaydi production hasarsiz olurdu

**Katman 2 — Auto-commit content guard (commit 45):**
- Run #5-7'de auto-commit step SKIP'lendi
- Bos batch.json'un main'e push edilmesi imkansiz hale geldi

**Run #4 hasari:** Bug B savunmalari henuz kurulmamisti, false PASS yutuldu.
Commit 44 (stash pop restore) ile hasarsiz atlatildi.

## Karar Kriterleri

### Plan A: CI'da Headless Browser
- Pro: CI'da regen mumkun olur
- Con:
  - Playwright + Chromium runner setup karmasik
  - Her run +10 dk
  - KAP UI degisikliklerine kirilgan
  - Yahoo bypass icin yine ayri cozum gerek
- Damodaran ilkesi "Keep it simple": UYMAZ

### Plan B: Daily Validation + Local Regen (SECILDI)
- Pro:
  - Lokal regen zaten calisiyor (Phase 2: 16 sn cache hit)
  - Production data integrity hala otomatik (CI validation)
  - Streamlit Cloud auto-redeploy korunur
  - Lokal cache zaten dolu (KAP+yfinance erisiliyor)
  - Failure recovery seffaf (CI issue acar)
- Con:
  - Daily manuel push gerekli (veya Task Scheduler)
- Damodaran ilkesi "Keep it simple, stay grounded": UYAR

### Plan C: CI Workflow Tamamen Kaldir
- Pro: Minimum karmasa
- Con: Production validation kaybolur
- KARAR: Reddedildi (CI hala deger uretir)

## Pivot Etkisi

### Etkilenen
- .github/workflows/batch_regen_daily.yml -> batch_validation_daily.yml
- Workflow scope: auto-regen -> daily validation
- Trigger pattern: cron -> push + cron + manual

### Etkilenmeyen
- Production code (cross_holdings, fcff_engine, orchestrator_v4)
- Phase 1+2 audit chain (anchor v4.2, v4.3 INTACT)
- TUPRS 211.95 anchor
- Damodaran daily hash check workflow (ayri)
- Local _regen_phase1.py
- Streamlit Cloud deploy

### Yeni Pattern
- Local daily regen (kullanici veya Task Scheduler)
- Git push -> CI auto-validate
- Sanity fail -> Issue + Alert
- Streamlit Cloud auto-redeploy

## Lessons Learned

1. CI'da external HTTP scraping fragile. Public API'ler IP rate-limit, SPA'lar JS gerektirir.
2. Diagnostic-driven karar ustun. 7 run hayalle degil veriyle karar verdi.
3. 3 katmanli savunma kritik. Bug B incident'i tek katman olsaydi geri donussuz olurdu.
4. Lokal cron + CI validation hibrit Damodaran ilkesi ile uyumlu. "Keep it simple, stay grounded."
5. Auto-issue acilmasi faydali. Run #7'de ilk gercek issue olustu — alert chain dogrulandi.
6. Stash kritik guvenlik agi. Commit 44 restore'u stash sayesinde oldu.
7. Workflow rename != delete. Audit history korunur, yeni dosya pivot'u temsil eder.

## Sonraki Adimlar (Evre 2 Devam)

- Adim 1 SEALED (validation mode ile farkli isim ama pivot tamam)
- Adim 2: Freshness warning (Streamlit UI'da batch yasi goster)
- Adim 3: Alert webhook (Discord/Slack/Telegram)
- Adim 4: KAP feed listener (yeni sirket girisi)
- Adim 5: SPK dilution tracker
