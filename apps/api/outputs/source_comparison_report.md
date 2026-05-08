# Session 3C — KAP-only 30 Ticker Cross-Check Report

Faz 11 v4.0 — multi-source orchestration validation

## Summary

- Total ticker tested: **30**
- ✓ PASS: **15**
- ⚠ FLAG: **15** (atypical, not error)
- ✗ FAIL: **0**

## Ticker Status Table

| Ticker | Cat | Dialect | Disc.idx | Revenue | Op M% | Equity | Shares | Float% | Subs | Status |
|--------|-----|---------|----------|---------|-------|--------|--------|--------|------|--------|
| TUPRS | anchor | industrial | 1510162 | 598,344,047 | 5.0 | 348,455,191 | 1,927,129,825 | 48.6 | 6 | ✓ PASS |
| GARAN | anchor | banking | 1508775 | 108,599,213 | 100.0 | — | 4,201,325,055 | 14.0 | 21 | ✓ PASS |
| AKBNK | anchor | banking | 1467850 | 36,443,971 | 100.0 | — | 5,200,808,744 | 53.8 | 16 | ✓ PASS |
| ARCLK | anchor | industrial | 1550376 | 523,933,321 | 2.0 | 75,905,153 | 676,063,578 | 17.6 | 122 | ⚠ FLAG |
| KUYAS | bug | industrial | 1441749 | 209,981,384 | -14.3 | 2,383,854,058 | 400,001,833 | 99.7 | 2 | ✓ PASS |
| INFO | bug | industrial | 1475884 | 20,723,661,139 | 1.9 | 2,229,188,582 | 960,493,275 | 58.4 | 3 | ✓ PASS |
| VESBE | bug | industrial | 1509466 | 57,378,851 | -4.4 | 38,310,045 | 1,600,420,513 | 22.7 | 0 | ✓ PASS |
| THYAO | random | holding | 1598897 | 257,961 | -1.0 | 966,363 | 1,380,228,680 | 50.4 | 20 | ✓ PASS |
| EREGL | random | industrial | 1431038 | 53,544,627 | 3.5 | 260,560,952 | 7,000,343,121 | 47.3 | 9 | ✓ PASS |
| KRDMD | random | industrial | 1569931 | 66,718,974,139 | 1.8 | 84,652,621,781 | 780,291,284 | 93.0 | 0 | ⚠ FLAG |
| SISE | random | industrial | 1557053 | 224,527,039 | 2.1 | 269,259,099 | 3,063,806,865 | 47.1 | 60 | ✓ PASS |
| BIMAS | random | industrial | 1478794 | 309,834,891 | 0.8 | 136,703,852 | 600,031,081 | 68.5 | 10 | ✓ PASS |
| MGROS | random | industrial | 1477134 | 174,844,068 | -3.7 | 67,409,040 | 181,055,996 | 50.8 | 7 | ✓ PASS |
| ASELS | random | industrial | 1431115 | 22,790,773 | 32.5 | 157,722,276 | 4,560,479,843 | 25.8 | 29 | ⚠ FLAG |
| KOZAL | random | — | — | — | — | — | — | — | 0 | ⚠ FLAG |
| TCELL | random | holding | 1477817 | 103,865,543 | 36.0 | 219,706,432 | 2,200,145,150 | 43.1 | 34 | ✓ PASS |
| FROTO | random | industrial | 1469124 | 365,359,745 | 5.5 | 140,459,002 | 3,509,415,852 | 17.7 | 4 | ✓ PASS |
| TOASO | random | holding | 1467464 | 100,278,425 | -0.7 | 48,238,985 | 5,001,745,834 | 2.4 | 3 | ⚠ FLAG |
| ENJSA | random | industrial | 1509205 | 163,175,634 | 17.0 | 89,632,419 | 1,181,619,379 | 20.0 | 9 | ✓ PASS |
| PETKM | random | industrial | 1435204 | 17,670,787 | -14.9 | 59,812,960 | 2,534,557,672 | 48.0 | 3 | ⚠ FLAG |
| AGROT | ipo | industrial | 1481009 | 1,295,737,352 | -17.1 | 7,292,407,074 | 2,400,333,282 | 40.0 | 9 | ⚠ FLAG |
| EUPWR | ipo | industrial | 1479991 | 3,891,297 | 13.2 | 9,707,804 | 6,601,962,289 | 3.0 | 18 | ⚠ FLAG |
| IZINV | ipo | industrial | 1480999 | 16,872,063 | -78.1 | 330,311,296 | 17,513,586 | 70.1 | 10 | ⚠ FLAG |
| NTGAZ | ipo | industrial | 1431062 | 2,198,895,401 | 24.9 | 4,283,830,709 | 690,154,303 | 38.4 | 3 | ⚠ FLAG |
| BAYRK | ipo | industrial | 1509467 | 173,784,245 | -36.7 | 322,253,636 | 250,000,089 | 75.8 | 0 | ⚠ FLAG |
| ERCB | ipo | industrial | 1480070 | 3,564,469,986 | 7.1 | 1,396,343,857 | 777,716,567 | 4.6 | 4 | ⚠ FLAG |
| MIPAZ | ipo | — | — | — | — | — | — | — | 0 | ⚠ FLAG |
| DENGE | ipo | industrial | 1479984 | 297,930,920 | -14.0 | 1,366,400,997 | 600,010,813 | 87.2 | 3 | ⚠ FLAG |
| KMPUR | ipo | industrial | 1478903 | 5,890,969,849 | 10.1 | 2,350,909,126 | 486,286,597 | 26.5 | 8 | ✓ PASS |
| ARSAN | ipo | holding | 1481005 | 48,519,130 | 617.2 | 9,564,334,229 | 1,762,247,702 | 35.5 | 9 | ⚠ FLAG |

## Per-Ticker Detail

### ✓ TUPRS  (anchor, expected=industrial)

- Disclosure: `1510162` (31.10.2025 18:19:22)
- Dialect detected: `industrial`
- Period: cari=30.09.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=1,927,129,825  sermaye=1,927,129,825 TL  pct=48.59%
- Subsidiaries: total=6 listed=6

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (5.0%)
- ✓ D/E=0.09
- ✓ ROE=6.3%
- ✓ shares=1,927,129,825
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ✓ GARAN  (anchor, expected=banking)

- Disclosure: `1508775` (30.10.2025 08:00:25)
- Dialect detected: `banking`
- Period: cari=30.09.2025 önceki=30.09.2025
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 368  Parsed: 5/12
- Float: shares=4,201,325,055  sermaye=4,201,325,055 TL  pct=13.98%
- Subsidiaries: total=21 listed=21

**Sanity passes**
- ✓ banking: net_interest_income > 0
- ✓ cash > 0
- ✓ shares=4,201,325,055
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ✓ AKBNK  (anchor, expected=banking)

- Disclosure: `1467850` (29.07.2025 18:15:23)
- Dialect detected: `banking`
- Period: cari=30.06.2025 önceki=30.06.2025
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 368  Parsed: 5/12
- Float: shares=5,200,808,744  sermaye=5,200,808,744 TL  pct=53.76%
- Subsidiaries: total=16 listed=16

**Sanity passes**
- ✓ banking: net_interest_income > 0
- ✓ cash > 0
- ✓ shares=5,200,808,744
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ⚠ ARCLK  (anchor, expected=industrial)

- Disclosure: `1550376` (30.01.2026 18:21:13)
- Dialect detected: `industrial`
- Period: cari=31.12.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=676,063,578  sermaye=676,063,578 TL  pct=17.56%
- Subsidiaries: total=122 listed=122

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (2.0%)
- ✓ D/E=2.67
- ✓ ROE=-12.9%
- ✓ shares=676,063,578
- ✓ sermaye/Bilanço magnitude OK (×1000)

**Sanity flags**
- ⚠ EBIT < Op Income (10,305,449 < 10,494,106)

### ✓ KUYAS  (bug, expected=industrial)

- Disclosure: `1441749` (24.05.2025 12:22:07)
- Dialect detected: `industrial`
- Period: cari=31.03.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=400,001,833  sermaye=400,001,833 TL  pct=99.73%
- Subsidiaries: total=2 listed=2

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (-14.3%)
- ✓ D/E=0.37
- ✓ ROE=10.4%
- ✓ shares=400,001,833
- ✓ sermaye/Bilanço magnitude OK (×1)

### ✓ INFO  (bug, expected=industrial)

- Disclosure: `1475884` (11.08.2025 18:10:41)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=960,493,275  sermaye=960,493,275 TL  pct=58.43%
- Subsidiaries: total=3 listed=3

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (1.9%)
- ✓ D/E=1.38
- ✓ ROE=5.7%
- ✓ shares=960,493,275
- ✓ sermaye/Bilanço magnitude OK (×1)

### ✓ VESBE  (bug, expected=industrial)

- Disclosure: `1509466` (30.10.2025 19:43:29)
- Dialect detected: `industrial`
- Period: cari=30.09.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=1,600,420,513  sermaye=1,600,420,513 TL  pct=22.65%

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (-4.4%)
- ✓ D/E=0.45
- ✓ ROE=-8.7%
- ✓ shares=1,600,420,513
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ✓ THYAO  (random, expected=industrial)

- Disclosure: `1598897` (29.04.2026 18:20:52)
- Dialect detected: `holding`
- Period: cari=31.03.2026 önceki=31.12.2025
- Sunum birimi: 1.000.000 TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=1,380,228,680  sermaye=1,380,228,680 TL  pct=50.42%
- Subsidiaries: total=20 listed=20

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (-1.0%)
- ✓ D/E=0.74
- ✓ ROE=1.0%
- ✓ shares=1,380,228,680
- ✓ sermaye/Bilanço magnitude OK (×1000166)
- ✓ holding subs=20 (listed=20)

### ✓ EREGL  (random, expected=industrial)

- Disclosure: `1431038` (29.04.2025 18:12:29)
- Dialect detected: `industrial`
- Period: cari=31.03.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=7,000,343,121  sermaye=7,000,343,121 TL  pct=47.31%
- Subsidiaries: total=9 listed=9

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (3.5%)
- ✓ D/E=0.44
- ✓ ROE=0.2%
- ✓ shares=7,000,343,121
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ⚠ KRDMD  (random, expected=industrial)

- Disclosure: `1569931` (10.03.2026 18:56:52)
- Dialect detected: `industrial`
- Period: cari=31.12.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=780,291,284  sermaye=780,291,284 TL  pct=92.98%

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (1.8%)
- ✓ D/E=0.10
- ✓ ROE=-2.0%
- ✓ shares=780,291,284

**Sanity flags**
- ⚠ EBIT < Op Income (860,327,666 < 1,223,249,120)
- ⚠ sermaye/Bilanço mismatch (×0.68)

### ✓ SISE  (random, expected=industrial)

- Disclosure: `1557053` (16.02.2026 18:37:25)
- Dialect detected: `industrial`
- Period: cari=31.12.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 737  Parsed: 12/12
- Float: shares=3,063,806,865  sermaye=3,063,806,865 TL  pct=47.09%
- Subsidiaries: total=60 listed=60

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (2.1%)
- ✓ D/E=0.44
- ✓ ROE=3.5%
- ✓ shares=3,063,806,865
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ✓ BIMAS  (random, expected=industrial)

- Disclosure: `1478794` (14.08.2025 20:21:13)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=600,031,081  sermaye=600,031,081 TL  pct=68.47%
- Subsidiaries: total=10 listed=10

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (0.8%)
- ✓ D/E=0.34
- ✓ ROE=4.1%
- ✓ shares=600,031,081
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ✓ MGROS  (random, expected=industrial)

- Disclosure: `1477134` (12.08.2025 20:49:43)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=181,055,996  sermaye=181,055,996 TL  pct=50.76%
- Subsidiaries: total=7 listed=7

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (-3.7%)
- ✓ D/E=0.33
- ✓ ROE=2.2%
- ✓ shares=181,055,996
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ⚠ ASELS  (random, expected=industrial)

- Disclosure: `1431115` (29.04.2025 18:30:43)
- Dialect detected: `industrial`
- Period: cari=31.03.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=4,560,479,843  sermaye=4,560,479,843 TL  pct=25.78%
- Subsidiaries: total=29 listed=29

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (32.5%)
- ✓ D/E=0.04
- ✓ ROE=1.4%
- ✓ shares=4,560,479,843
- ✓ sermaye/Bilanço magnitude OK (×1000)

**Sanity flags**
- ⚠ EBIT < Op Income (7,339,975 < 7,406,479)

### ⚠ KOZAL  (random, expected=industrial)


**Sanity flags**
- ⚠ data_quality: ticker 'KOZAL' not in KAP kpy41_acc5 (delisted/invalid/non-BIST)

### ✓ TCELL  (random, expected=industrial)

- Disclosure: `1477817` (13.08.2025 18:45:10)
- Dialect detected: `holding`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 737  Parsed: 12/12
- Float: shares=2,200,145,150  sermaye=2,200,145,150 TL  pct=43.13%
- Subsidiaries: total=34 listed=34

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (36.0%)
- ✓ D/E=0.59
- ✓ ROE=3.4%
- ✓ shares=2,200,145,150
- ✓ sermaye/Bilanço magnitude OK (×1000)
- ✓ holding subs=34 (listed=34)

### ✓ FROTO  (random, expected=industrial)

- Disclosure: `1469124` (30.07.2025 19:56:17)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=3,509,415,852  sermaye=3,509,415,852 TL  pct=17.74%
- Subsidiaries: total=4 listed=4

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (5.5%)
- ✓ D/E=0.82
- ✓ ROE=9.2%
- ✓ shares=3,509,415,852
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ⚠ TOASO  (random, expected=industrial)

- Disclosure: `1467464` (28.07.2025 23:30:29)
- Dialect detected: `holding`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=5,001,745,834  sermaye=5,001,745,834 TL  pct=2.41%
- Subsidiaries: total=3 listed=3

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (-0.7%)
- ✓ D/E=0.49
- ✓ ROE=3.3%
- ✓ shares=5,001,745,834
- ✓ holding subs=3 (listed=3)

**Sanity flags**
- ⚠ sermaye/Bilanço mismatch (×10003.49)

### ✓ ENJSA  (random, expected=industrial)

- Disclosure: `1509205` (30.10.2025 18:15:13)
- Dialect detected: `industrial`
- Period: cari=30.09.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=1,181,619,379  sermaye=1,181,619,379 TL  pct=19.98%
- Subsidiaries: total=9 listed=9

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (17.0%)
- ✓ D/E=0.46
- ✓ ROE=0.5%
- ✓ shares=1,181,619,379
- ✓ sermaye/Bilanço magnitude OK (×1000)

### ⚠ PETKM  (random, expected=industrial)

- Disclosure: `1435204` (08.05.2025 07:32:51)
- Dialect detected: `industrial`
- Period: cari=31.03.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=2,534,557,672  sermaye=2,534,557,672 TL  pct=48.03%
- Subsidiaries: total=3 listed=3

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (-14.9%)
- ✓ D/E=0.80
- ✓ ROE=-4.3%
- ✓ shares=2,534,557,672
- ✓ sermaye/Bilanço magnitude OK (×1000)

**Sanity flags**
- ⚠ EBIT < Op Income (-2,694,071 < -2,630,835)

### ⚠ AGROT  (ipo, expected=industrial)

- Disclosure: `1481009` (19.08.2025 20:13:57)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=2,400,333,282  sermaye=2,400,333,282 TL  pct=39.96%
- Subsidiaries: total=9 listed=9

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (-17.1%)
- ✓ ROE=-2.6%
- ✓ shares=2,400,333,282

**Sanity flags**
- ⚠ sermaye/Bilanço mismatch (×2.00)

### ⚠ EUPWR  (ipo, expected=industrial)

- Disclosure: `1479991` (18.08.2025 18:18:43)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: 1.000 TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=6,601,962,289  sermaye=6,601,962,289 TL  pct=3.02%
- Subsidiaries: total=18 listed=18

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (13.2%)
- ✓ D/E=0.11
- ✓ ROE=2.4%
- ✓ shares=6,601,962,289

**Sanity flags**
- ⚠ sermaye/Bilanço mismatch (×10002.97)

### ⚠ IZINV  (ipo, expected=industrial)

- Disclosure: `1480999` (19.08.2025 20:07:43)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=17,513,586  sermaye=17,513,586 TL  pct=70.08%
- Subsidiaries: total=10 listed=10

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ D/E=0.01
- ✓ ROE=-11.4%
- ✓ shares=17,513,586
- ✓ sermaye/Bilanço magnitude OK (×1)

**Sanity flags**
- ⚠ op_margin out of band (-78.1%)

### ⚠ NTGAZ  (ipo, expected=industrial)

- Disclosure: `1431062` (29.04.2025 18:15:52)
- Dialect detected: `industrial`
- Period: cari=31.03.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 735  Parsed: 12/12
- Float: shares=690,154,303  sermaye=690,154,303 TL  pct=38.41%
- Subsidiaries: total=3 listed=3

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (24.9%)
- ✓ D/E=0.06
- ✓ ROE=8.2%
- ✓ shares=690,154,303
- ✓ sermaye/Bilanço magnitude OK (×1)

**Sanity flags**
- ⚠ EBIT < Op Income (544,052,608 < 547,095,460)

### ⚠ BAYRK  (ipo, expected=industrial)

- Disclosure: `1509467` (30.10.2025 19:43:36)
- Dialect detected: `industrial`
- Period: cari=30.09.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=250,000,089  sermaye=250,000,089 TL  pct=75.78%

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ D/E=0.81
- ✓ ROE=-20.4%
- ✓ shares=250,000,089

**Sanity flags**
- ⚠ op_margin out of band (-36.7%)
- ⚠ sermaye/Bilanço mismatch (×4.43)

### ⚠ ERCB  (ipo, expected=industrial)

- Disclosure: `1480070` (18.08.2025 18:41:55)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=777,716,567  sermaye=777,716,567 TL  pct=4.57%
- Subsidiaries: total=4 listed=4

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (7.1%)
- ✓ D/E=2.39
- ✓ ROE=-6.7%
- ✓ shares=777,716,567

**Sanity flags**
- ⚠ sermaye/Bilanço mismatch (×10.00)

### ⚠ MIPAZ  (ipo, expected=industrial)


**Sanity flags**
- ⚠ data_quality: ticker 'MIPAZ' not in KAP kpy41_acc5 (delisted/invalid/non-BIST)

### ⚠ DENGE  (ipo, expected=industrial)

- Disclosure: `1479984` (18.08.2025 18:17:22)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=600,010,813  sermaye=600,010,813 TL  pct=87.23%
- Subsidiaries: total=3 listed=3

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (-14.0%)
- ✓ D/E=0.07
- ✓ ROE=-20.5%
- ✓ shares=600,010,813
- ✓ sermaye/Bilanço magnitude OK (×1)

**Sanity flags**
- ⚠ EBIT < Op Income (-107,391,995 < -41,629,914)

### ✓ KMPUR  (ipo, expected=industrial)

- Disclosure: `1478903` (15.08.2025 08:20:02)
- Dialect detected: `industrial`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=486,286,597  sermaye=486,286,597 TL  pct=26.45%
- Subsidiaries: total=8 listed=8

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ op_margin in band (10.1%)
- ✓ D/E=2.01
- ✓ ROE=-25.0%
- ✓ shares=486,286,597
- ✓ sermaye/Bilanço magnitude OK (×1)

### ⚠ ARSAN  (ipo, expected=industrial)

- Disclosure: `1481005` (19.08.2025 20:09:24)
- Dialect detected: `holding`
- Period: cari=30.06.2025 önceki=31.12.2024
- Sunum birimi: TL  Konsolide: True
- Tables: 731  Parsed: 12/12
- Float: shares=1,762,247,702  sermaye=1,762,247,702 TL  pct=35.46%
- Subsidiaries: total=9 listed=9

**Sanity passes**
- ✓ revenue > 0
- ✓ total_assets > 0
- ✓ equity > 0
- ✓ BS identity ✓ (Δ=0.00%)
- ✓ D/E=0.00
- ✓ ROE=1.4%
- ✓ shares=1,762,247,702
- ✓ holding subs=9 (listed=9)

**Sanity flags**
- ⚠ op_margin out of band (617.2%)
- ⚠ sermaye/Bilanço mismatch (×8.62)
