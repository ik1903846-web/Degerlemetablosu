# Türkiye Sektör Beta — Damodaran Bottom-Up

Faz 11 v4.0 — Session 3.6

Methodology: weekly log returns, 5y, OLS regression vs BIST 100

Tax rate (Türkiye 2025): %25


## Summary

- Total ticker:    **587**
- Included:        **537**
- Excluded:        **50**
- Banking dialect: 25 (regression beta direct, unlever skip)
- Sectors:         **44**
- Single-firm:     **13**
- High dispersion (stdev>0.30): **4**

## Sector Beta Table (sorted by ticker count)

| sectorNo | Sector | N | Mean β_unlev | Median | Stdev | Flag |
|----------|--------|---|--------------|--------|-------|------|
| 008000.004000. | HOLDİNGLER VE YATIRIM ŞİRKETLERİ | 52/55 | 0.616 | 0.702 | 0.252 |  |
| 008000.008000. | GAYRİMENKUL YATIRIM ORTAKLIKLARI | 48/53 | 0.690 | 0.677 | 0.222 |  |
| 003000.001000. | GIDA, İÇECEK VE TÜTÜN | 46/49 | 0.587 | 0.580 | 0.184 |  |
| 003000.005000. | KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER | 42/45 | 0.601 | 0.549 | 0.227 |  |
| 003000.008000. | METAL EŞYA MAKİNE ELEKTRİKLİ CİHAZLAR VE ULAŞIM AR | 39/39 | 0.638 | 0.681 | 0.225 |  |
| 004000.001000. | ELEKTRİK GAZ VE BUHAR | 36/39 | 0.623 | 0.598 | 0.262 |  |
| 011000.001000. | BİLİŞİM | 34/39 | 0.637 | 0.695 | 0.241 |  |
| 003000.007000. | ANA METAL SANAYİ | 31/31 | 0.625 | 0.635 | 0.245 |  |
| 003000.006000. | TAŞ VE TOPRAĞA DAYALI | 28/28 | 0.632 | 0.660 | 0.176 |  |
| 003000.002000. | TEKSTİL, GİYİM EŞYASI VE DERİ | 24/25 | 0.560 | 0.607 | 0.180 |  |
| 006000.002000. | PERAKENDE TİCARET | 16/16 | 0.473 | 0.420 | 0.252 |  |
| 005000.001000. | İNŞAAT VE BAYINDIRLIK İŞLERİ | 14/15 | 0.636 | 0.532 | 0.216 |  |
| 008000.001000. | BANKALAR | 14/27 | 1.044 | 1.216 | 0.382 | high_dispersion |
| 003000.004000. | KAĞIT VE KAĞIT ÜRÜNLERİ BASIM | 13/14 | 0.620 | 0.612 | 0.163 |  |
| 007000.001000. | ULAŞTIRMA VE DEPOLAMA | 12/12 | 0.554 | 0.574 | 0.200 |  |
| 006000.001000. | TOPTAN TİCARET | 10/10 | 0.510 | 0.628 | 0.242 |  |
| 008000.003000. | FİNANSAL KİRALAMA VE FAKTORİNG ŞİRKETLERİ | 9/10 | 0.762 | 0.762 | 0.188 |  |
| 008000.007000. | ARACI KURUMLAR | 9/17 | 0.535 | 0.364 | 0.317 | high_dispersion |
| 008000.009000. | MENKUL KIYMET YATIRIM ORTAKLIKLARI | 9/9 | 0.629 | 0.667 | 0.142 |  |
| 003000.003000. | ORMAN ÜRÜNLERİ VE MOBİLYA | 6/6 | 0.453 | 0.461 | 0.069 |  |
| 008000.002000. | SİGORTA ŞİRKETLERİ | 6/6 | 0.765 | 0.764 | 0.137 |  |
| 001000.001000. | TARIM VE HAYVANCILIK AVCILIK VE İLGİLİ HİZMET FAAL | 4/4 | 0.806 | 0.803 | 0.346 | high_dispersion |
| 013000.001000. | KİRALAMA VE LEASING FAALİYETLERİ | 4/4 | 0.322 | 0.164 | 0.384 | high_dispersion |
| 014000.001000. | GAYRİMENKUL FAALİYETLERİ | 4/4 | 0.774 | 0.743 | 0.112 |  |
| OVERRIDE | Otomotiv (Türkiye) | 3/3 | 0.617 | 0.577 | 0.171 |  |
| 011000.002000. | SAVUNMA | 3/3 | 0.469 | 0.501 | 0.200 |  |
| 002000.001000. | KÖMÜR VE LİNYİT MADENCİLİĞİ | 2/2 | 0.814 | 0.814 | 0.154 |  |
| OVERRIDE | Beyaz Eşya (Türkiye) | 2/2 | 0.422 | 0.422 | 0.152 |  |
| 012000.003000. | MİMARLIK VE MÜHENDİSLİK FAALİYETLERİ; TEKNİK MUAYE | 2/2 | 0.407 | 0.407 | 0.114 |  |
| 013000.006000. | BÜRO YÖNETİMİ, BÜRO DESTEĞİ VE DİĞER ŞİRKET DESTEK | 2/2 | 0.665 | 0.665 | 0.237 |  |
| 001000.003000. | BALIKÇILIK VE SU ÜRÜNLERİ | 1/1 | 0.344 | 0.344 | — | single_firm |
| 002000.003000. | METAL CEVHERİ MADENCİLİĞİ | 1/3 | 0.728 | 0.728 | — | single_firm |
| 002000.004000. | DİĞER MADENCİLİK VE TAŞ OCAKÇILIĞI | 1/1 | 0.524 | 0.524 | — | single_firm |
| OVERRIDE | Lastik (Türkiye) | 1/1 | 0.636 | 0.636 | — | single_firm |
| OVERRIDE | İlaç (Türkiye) | 1/1 | 0.682 | 0.682 | — | single_firm |
| OVERRIDE | Petrokimya (Türkiye) | 1/1 | 0.678 | 0.678 | — | single_firm |
| OVERRIDE | Petrol Rafinerisi (Türkiye) | 1/1 | 0.910 | 0.910 | — | single_firm |
| 003000.009000. | DİĞER İMALAT SANAYİİ | 1/1 | 0.498 | 0.498 | — | single_firm |
| 009000.004000. | SPOR EĞLENCE BOŞ ZAMANLARI DEĞERLENDİRME HİZMETLER | 1/1 | 0.319 | 0.319 | — | single_firm |
| OVERRIDE | Savunma (Türkiye) | 1/1 | 0.947 | 0.947 | — | single_firm |
| 012000.001000. | HUKUK VE MUHASEBE FAALİYETLERİ | 1/1 | 0.632 | 0.632 | — | single_firm |
| 012000.005000. | REKLAMCILIK VE PAZAR ARAŞTIRMASI | 1/1 | 0.656 | 0.656 | — | single_firm |
| 013000.003000. | SEYAHAT ACENTESİ, TUR OPERATÖRÜ VE DİĞER REZERVASY | 1/1 | 0.319 | 0.319 | — | single_firm |
| 002000.002000. | HAM PETROL VE DOĞAL GAZ ÇIKARTILMASI | 0/1 | — | — | — |  |

## TUPRS Anchor

- Sektör: Petrol Rafinerisi (Türkiye) (OVERRIDE)
- β_levered (regression): 0.9687194955483913
- R²: 0.41834178359385354
- D/E: 0.08577757993566525
- β_unlevered (firma): 0.9101656410274455
- Sektör β_unlevered ortalama: 0.9101656410274455
- β_relevered (sektör + firma D/E): 0.9687194955483913
- Flags: ['sector_override: KİMYA İLAÇ PETROL LASTİK VE PL → Petrol Rafinerisi (Türkiye)']