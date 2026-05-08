# Türkiye Sektör Beta — Damodaran Bottom-Up

Faz 11 v4.0 — Session 3.6

Methodology: weekly log returns, 5y, OLS regression vs BIST 100

Tax rate (Türkiye 2025): %25


## Summary

- Total ticker:    **587**
- Included:        **541**
- Excluded:        **46**
- Banking dialect: 0 (regression beta direct, unlever skip)
- Sectors:         **37**
- Single-firm:     **8**
- High dispersion (stdev>0.30): **3**

## Sector Beta Table (sorted by ticker count)

| sectorNo | Sector | N | Mean β_unlev | Median | Stdev | Flag |
|----------|--------|---|--------------|--------|-------|------|
| 008000.004000. | HOLDİNGLER VE YATIRIM ŞİRKETLERİ | 53/55 | 0.696 | 0.741 | 0.290 |  |
| 008000.008000. | GAYRİMENKUL YATIRIM ORTAKLIKLARI | 48/53 | 0.711 | 0.678 | 0.225 |  |
| 003000.001000. | GIDA, İÇECEK VE TÜTÜN | 46/49 | 0.726 | 0.754 | 0.209 |  |
| 003000.005000. | KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER | 46/49 | 0.754 | 0.782 | 0.231 |  |
| 003000.008000. | METAL EŞYA MAKİNE ELEKTRİKLİ CİHAZLAR VE ULAŞIM AR | 44/44 | 0.798 | 0.824 | 0.188 |  |
| 004000.001000. | ELEKTRİK GAZ VE BUHAR | 36/39 | 0.749 | 0.769 | 0.262 |  |
| 011000.001000. | BİLİŞİM | 35/39 | 0.738 | 0.765 | 0.223 |  |
| 003000.007000. | ANA METAL SANAYİ | 31/31 | 0.792 | 0.851 | 0.215 |  |
| 003000.006000. | TAŞ VE TOPRAĞA DAYALI | 28/28 | 0.722 | 0.734 | 0.202 |  |
| 003000.002000. | TEKSTİL, GİYİM EŞYASI VE DERİ | 25/25 | 0.646 | 0.703 | 0.203 |  |
| 006000.002000. | PERAKENDE TİCARET | 16/16 | 0.712 | 0.800 | 0.253 |  |
| 003000.004000. | KAĞIT VE KAĞIT ÜRÜNLERİ BASIM | 14/14 | 0.697 | 0.690 | 0.141 |  |
| 005000.001000. | İNŞAAT VE BAYINDIRLIK İŞLERİ | 14/15 | 0.723 | 0.720 | 0.195 |  |
| 008000.001000. | BANKALAR | 14/27 | 1.044 | 1.216 | 0.382 | high_dispersion |
| 007000.001000. | ULAŞTIRMA VE DEPOLAMA | 12/12 | 0.737 | 0.794 | 0.250 |  |
| 006000.001000. | TOPTAN TİCARET | 10/10 | 0.663 | 0.660 | 0.173 |  |
| 008000.003000. | FİNANSAL KİRALAMA VE FAKTORİNG ŞİRKETLERİ | 9/10 | 0.762 | 0.762 | 0.188 |  |
| 008000.007000. | ARACI KURUMLAR | 9/17 | 0.766 | 0.689 | 0.298 |  |
| 008000.009000. | MENKUL KIYMET YATIRIM ORTAKLIKLARI | 9/9 | 0.635 | 0.687 | 0.138 |  |
| 003000.003000. | ORMAN ÜRÜNLERİ VE MOBİLYA | 6/6 | 0.578 | 0.566 | 0.181 |  |
| 008000.002000. | SİGORTA ŞİRKETLERİ | 6/6 | 0.765 | 0.764 | 0.137 |  |
| 001000.001000. | TARIM VE HAYVANCILIK AVCILIK VE İLGİLİ HİZMET FAAL | 4/4 | 0.827 | 0.842 | 0.342 | high_dispersion |
| 011000.002000. | SAVUNMA | 4/4 | 0.616 | 0.600 | 0.285 |  |
| 013000.001000. | KİRALAMA VE LEASING FAALİYETLERİ | 4/4 | 0.430 | 0.322 | 0.380 | high_dispersion |
| 014000.001000. | GAYRİMENKUL FAALİYETLERİ | 4/4 | 0.774 | 0.743 | 0.112 |  |
| 002000.001000. | KÖMÜR VE LİNYİT MADENCİLİĞİ | 2/2 | 0.814 | 0.814 | 0.154 |  |
| 012000.003000. | MİMARLIK VE MÜHENDİSLİK FAALİYETLERİ; TEKNİK MUAYE | 2/2 | 0.917 | 0.917 | 0.196 |  |
| 013000.006000. | BÜRO YÖNETİMİ, BÜRO DESTEĞİ VE DİĞER ŞİRKET DESTEK | 2/2 | 0.665 | 0.665 | 0.237 |  |
| 001000.003000. | BALIKÇILIK VE SU ÜRÜNLERİ | 1/1 | 0.594 | 0.594 | — | single_firm |
| 002000.003000. | METAL CEVHERİ MADENCİLİĞİ | 1/3 | 0.821 | 0.821 | — | single_firm |
| 002000.004000. | DİĞER MADENCİLİK VE TAŞ OCAKÇILIĞI | 1/1 | 0.527 | 0.527 | — | single_firm |
| 003000.009000. | DİĞER İMALAT SANAYİİ | 1/1 | 0.919 | 0.919 | — | single_firm |
| 009000.004000. | SPOR EĞLENCE BOŞ ZAMANLARI DEĞERLENDİRME HİZMETLER | 1/1 | 0.352 | 0.352 | — | single_firm |
| 012000.001000. | HUKUK VE MUHASEBE FAALİYETLERİ | 1/1 | 0.652 | 0.652 | — | single_firm |
| 012000.005000. | REKLAMCILIK VE PAZAR ARAŞTIRMASI | 1/1 | 0.661 | 0.661 | — | single_firm |
| 013000.003000. | SEYAHAT ACENTESİ, TUR OPERATÖRÜ VE DİĞER REZERVASY | 1/1 | 0.536 | 0.536 | — | single_firm |
| 002000.002000. | HAM PETROL VE DOĞAL GAZ ÇIKARTILMASI | 0/1 | — | — | — |  |

## TUPRS Anchor

- Sektör: KİMYA İLAÇ PETROL LASTİK VE PLASTİK ÜRÜNLER (003000.005000.)
- β_levered (regression): 0.9687194955483913
- R²: 0.41834178359385354
- D/E: None
- β_unlevered (firma): 0.9687194955483913
- Sektör β_unlevered ortalama: 0.7539601590646189
- β_relevered (sektör + firma D/E): 0.7539601590646189
- Flags: ['dialect_unknown_skip_unlever']