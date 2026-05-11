# Operasyonel Sertleştirme Evre 2 Adim 1.5 — Bug B Post-Mortem

**Tarih:** 11 Mayıs 2026
**Olay:** CI Run #4 sessiz fail → production turkey_v4_batch.json korupsiyon
**Hasar:** 13266 satır silindi, TUPRS anchor kayboldu
**Süre (RTO):** Tespit-Restore arasi ~10 dk
**Veri kaybı:** SIFIR (local stash sayesinde)

## Olay Akışı

1. **T+0:** Run #4 başladı, commit dc347f6 (HEAD)
2. **T+22s:** Install dependencies PASS (httpx + openpyxl OK)
3. **T+25s:** Restore runtime cache PASS (önceki run'lardan boş cache)
4. **T+26s:** Run batch regen başladı
5. **T+28s:** float_snap KAP HTTP fetch FAIL (region-block/rate limit)
6. **T+28s:** universe = [] (silent fail in kap_float_fetcher)
7. **T+30s:** Regen 0 ticker üzerinde döndü
8. **T+30s:** save_v4_batch_json yazdı: total_count=0, anchor=None
9. **T+30s:** Sanity gates Python: "FAIL Gate A: TUPRS intrinsic None"
10. **T+30s:** Python sys.exit(2) — AMA `tee` pipe exit code yuttu
11. **T+30s:** Step yeşil tick (false positive)
12. **T+31s:** Auto-commit step: `if: success()` PASS → commit + push
13. **T+31s:** main branch'e 1cde3d1 push'landı (production hasar)

## Root Cause Analysis

### Bug A: Universe count: 0
- **Kaynak:** `apps/api/data_layer/kap_float_fetcher.py`
- **Mekanizma:** Cache key `kap_float_{today.isoformat()}.csv` — CI'da bugünün dosyası yok, KAP fetch denendi, fail oldu, exception fırlatılmadı, snap.records boş döndü
- **Çözüm:** [Commit 43] `_regen_phase1.py` wrapper'a en yeni cache CSV fallback eklendi

### Bug B: Sanity gates tee pipe sessiz yutuyor (BU OLAY)
- **Kaynak:** `.github/workflows/batch_regen_daily.yml` Sanity gates step
- **Mekanizma:** `python -u <<'PY' 2>&1 | tee sanity_output.txt` pattern. Bash default'ta pipe exit code = son komut (tee, exit 0). Python'un exit 2'si yutuldu.
- **Çözüm:** [Commit 43] `set -eo pipefail` eklendi
- **Ek savunma:** [Commit 45] Auto-commit step'inde içerik validation guard

## Savunma Katmanları (Defense in Depth)

### Katman 1: Pipefail (eklendi commit 43)

```
set -eo pipefail
python -u <<'PY' 2>&1 | tee sanity_output.txt
```

### Katman 2: Auto-commit content validation (commit 45)
Auto-commit ÖNCESİ batch.json içeriği kontrol:
- `total_count > 100` (universe sane)
- `anchor_tuprs not null` (TUPRS intact)
- Eğer FAIL → commit skip + issue

### Katman 3: Issue idempotency (TODO Adım 1.6)
Aynı tarih için bir kez issue açılsın, spam olmasın.

## Lessons Learned

1. **Yeşil tick ≠ iş yapıldı.** Step exit code 0, içeriğin doğru olduğunu kanıtlamaz.
2. **tee pipe Python exit code'unu yutar.** Her `python | tee` pattern'inde `set -eo pipefail` zorunlu.
3. **Auto-commit defense in depth gerekir.** Tek if koşulu yetmez, içerik validation şart.
4. **Local stash kritik.** Stash pop ile RTO 10 dk'da restore. Lessons: rebase öncesi stash daima.
5. **Production data prosedürü:** Otomatik silinmeye karşı içerik validation **zorunlu**.

## Etkilenen Komponentler

| Komponent | Durum |
|-----------|-------|
| turkey_v4_batch.json | RESTORED (commit 44) |
| TUPRS 211.95 anchor | INTACT (stash sayesinde) |
| Phase 1+2 production code | INTACT (hiç değişmedi) |
| Damodaran daily workflow | INTACT (paralel, etkilenmedi) |
| Anchor v4.3 git tag | INTACT |

## Sonuc

Hasarsız atlatıldı. Bug B defense in depth ile düzeltildi.
Ders: CI workflow'larda her pipe'da pipefail + her auto-commit'te içerik validation.
