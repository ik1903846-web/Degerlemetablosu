# Amazon 2000 Young Firm DCF — WIP (Work in Progress)

## Durum
Faz 1.7 implementation FAIL ettiyse, Damodaran'ın özel revenue trajectory
pattern'ini reverse engineer'a ihtiyaç vardı. Karar: D (skip + Faz 2).

## Sebep
Damodaran Amazon 2000 PDF'inde "42% growth Year 1-5" deniyor ama tablo
custom yıllık taper pattern içeriyor (Year 1: ~150%, Y2: 100%, Y3: 75%,
Y4: 50%, Y5: 30%). Bu Damodaran'ın elle tuned özel young firm pattern'i,
generic 5-yr CAGR değil.

## Bu Dosyalar
- young_firm_dcf.py: 5 simultaneous taper + NOL + options engine (working)
- test_full_amazon.py: Test runner (FAIL - revenue trajectory bug)

## Ne Zaman Geri Dön?
- BIST'te real young firm validation'a ihtiyaç olunca
- Damodaran'ın yeni Amazon vintage'ı çıkarsa (2024+)
- Tesla/Uber benzeri başka young firm validation case ile

## .gitignore
Bu klasör track ediliyor (.gitignore'da DEĞİL) — kod kayıt için.
