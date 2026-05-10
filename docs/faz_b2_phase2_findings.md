# Faz B2 Phase 2 — Findings (Keşif Bulgular)

**Session:** 7.x | **Tarih:** 2026-05-10 | **Durum:** SCOPE REVIZE

## Tespit: kpy41_acc8 YOK, Asıl Problem Parser Bug

Phase 1 sonrası planlanan kpy41_acc8 fetcher gereksiz çıktı.

### Veri Tabanı Gerçeği

KAP fetcher (kap_subsidiaries_fetcher.py) kpy41_acc7'den 3511 record
çekiyor. Bu form Damodaran'ın 4 kategorisini de kapsıyor:

- full: 2288 (median own=1.00)
- equity: 451 (median own=0.22)
- joint: 68 (median own=0.50)
- financial: 88 (median own=0.10)
- **NaN: 616 (parser limit)** ★

### Parser Bug Kanıtı (relationship_raw dolu, type NaN)

Çarpıcı örnekler:

| Parent → Sub | relationship_raw | Olması gereken | Mevcut |
|--------------|-----------------|----------------|--------|
| ALARK → ALGYO | BAĞLI ORTAKLIK (PAY %51,23) | full | NaN |
| EREGL → ISDMR | TAM KONSOLIDASYON | full | NaN |
| ALARK → ALCAR | MÜŞTEREK YÖNETIME TABI (PAY %42,03) | joint | NaN |
| INVES → PAMEL | Dolaylı İştirak | equity | NaN |
| IHEVA → IHLGM | Bağlı Menkul Kıymet | financial | NaN |

### Top Null Parent'lar (616 record dağılımı)

DOCO=89, ALARK=49, ENERY=18, KRVGD=13, TTKOM=13, BINHO=12,
ASELS=12, YKBNK=12, ICUGS=11, INVES=10

### Listed Null (Phase 1'de SKIP edilen)

18 listed sub null relationship'li → Phase 1'de skip edildi.
Çoğunluğu kurtarılabilir (raw_text yeterli).

## Karar: Phase 2 Scope Revize

**Eski plan (kpy41_acc8 fetcher):** GEREKSIZ
**Yeni plan:** kpy41_acc7 parser improvement

### Yeni Phase 2 Adımları (~3-5 gün)

- Adım 1: relationship_raw → relationship_type kategorizer (1 gün)
- Adım 2: ownership_pct fallback parse (1 gün)
- Adım 3: Holdings SOTP başlangıcı (2-3 gün) — KCHOL/SAHOL NaN problemi
- Adım 4: Regen + sensitivity + audit chain

## IFRS Bilanço Parse — Phase 3'te Kalsın

parsed_financials/*.json sadece DCF inputs (revenue, op_income, debt, vs).
"Finansal Yatırımlar" line item parse YOK. Phase 3 ayrı iş.
