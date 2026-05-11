# Operasyonel Sertlestirme — Local Regen Pattern

Adim 1.7 stratejik pivot sonrasi karar: CI'da batch regen mumkun degil.
Local makinede daily regen + git push pattern.

## Neden Lokal?

7 run CI experiment kaniti (Run #1-7, 11 Mayis 2026):

- KAP main: 307 Redirect (dil header, cozulebilir)
- KAP float: 200 OK, 2 MB HTML (Next.js SPA, JS render gerek)
- Yahoo Finance: 429 Too Many Requests (CI runner IP rate-limit)
- Damodaran: 200 OK (kontrol grup, sorun yok)

CI'da headless browser + proxy karmasik, fragile. Local'de zaten cache hit
~16 sn'de regen biter (Phase 2 Adim 4 kanit).

## Daily Workflow

### Manuel (her gun veya ihtiyac aninda)

```bash
cd C:/Users/unutu/Desktop/abiminprojev2

# 1. Regen calistir (~16 sn cache hit, ~28 dk cache miss)
python apps/api/_regen_phase1.py

# 2. Sanity check (lokal hizli kontrol)
python -c "import json; d=json.load(open('apps/api/outputs/turkey_v4_batch.json')); print('total_count:', d['total_count']); print('dcf_count:', d['dcf_count']); print('anchor_tuprs:', d['anchor_tuprs'])"

# 3. Commit + push
git add apps/api/outputs/turkey_v4_batch.json
git commit -m "[CI-bypass] Daily regen 2026-05-11"
git push origin main
```

### Otomatik — Windows Task Scheduler

1. Task Scheduler ac (Windows Start)
2. Create Basic Task — "BIST Daily Regen"
3. Trigger: Daily 19:00 (BIST kapanis sonrasi)
4. Action: Start a program
5. Program: cmd.exe
6. Arguments:
   ```
   /c "cd /d C:\Users\unutu\Desktop\abiminprojev2 && python apps\api\_regen_phase1.py && git add apps\api\outputs\turkey_v4_batch.json && git commit -m \"[CI-bypass] Daily regen %DATE%\" && git push origin main"
   ```

### Streamlit Cloud Otomatik Redeploy

Git push sonrasi reeldeger.streamlit.app otomatik yenilenir (~2-3 dk).

## CI Validation Akisi

```
LOCAL: python _regen_phase1.py
  -> git push
GITHUB: batch_validation_daily.yml
  -> Sanity Gates (4 boyut)
  -> PASS = trigger redeploy
  -> FAIL = Issue acilir + Alert (user)
STREAMLIT: reeldeger.streamlit.app (otomatik 2-3 dk)
```

## Failure Recovery

### CI Issue Actiysa

1. Issue'yu ac — hangi gate fail etti gor (Gate A/B/C/D)
2. Lokal'de tekrar regen + sanity check calistir
3. Eger lokal de fail: kod debug
4. Eger lokal OK: revert push veya force-push

### TUPRS Anchor Drift (Gate A)

- 0.50% uzeri drift -> kod bug veya parametre degisimi
- Damodaran daily check ile karsilastir (parametre staleness)
- ADR-040 protokolu uygula
- Anchor v4.3 tag'i ile state compare

### Stale Data (Gate D)

- 7 gun uzeri -> WARN (uyari)
- 14 gun uzeri -> FAIL (issue)
- Daily regen kacirilmis demek
- Hizli regen + push
- Task Scheduler calisiyor mu kontrol et

## Audit Pattern

Her git push commit message format:
`[CI-bypass] Daily regen YYYY-MM-DD`

Bu prefix ile filter:
```bash
git log --grep="\[CI-bypass\]" --oneline
```

## Gecmis Audit Kayitlari

- 7 run CI experiment: docs/operasyonel_evre2_adim17_strategic_pivot.md
- Bug B post-mortem: docs/operasyonel_evre2_adim15_bug_b_postmortem.md
- Phase 1+2 audit chain: docs/faz_b2_phase{1,2}_*.md
