# Phase 3a Adim 1 — Tag Mapping Kanit Findings

**Tarih:** 12 Mayis 2026
**Scope:** KAP XBRL bilanco istirak/yatirim satir kanitlari
**Test ticker:** KCHOL (holding kompleks)

## Ozet Bulgu

KCHOL bilancosu (Tablo 2, 595x5) icinde 5 yatirim satiri tespit edildi.
Phase 3a'da 2 satir yeni field olarak parse edilecek.

## Eklenecek 2 Yeni Field

| Python Field | Turkce Tag | KCHOL Deger | Neden Ekleniyor |
|--------------|------------|-------------|------------------|
| equity_method_investments | Ozkaynak Yontemiyle Degerlenen Yatirimlar | 113.6B TL | Konsolide DISI, cross_holdings ile cakismaz |
| investment_properties | Yatirim Amacli Gayrimenkuller | 3.1B TL | Konsolide DISI, REIT iceren holding'lerde |

## SKIP Edilen 3 Satir

| Row | Label | KCHOL | Gerekce |
|-----|-------|-------|---------|
| 11 | Finansal Yatirimlar (kisa vadeli) | 45.6B | Cash equivalent |
| 113 | Finansal Yatirimlar (uzun vadeli) | 551.2B | KONSOLIDE icinde — double-count riski |
| 143 | Istirakler ve Bagli Ortakliklarda Yatirimlar | NaN | KCHOL kullanmamis |

## Kritik Tasarim Karari: Double-Count Onleme

Phase 1 cross_holdings = listed sub market_cap × ownership = 192B
Phase 3a equity_method_investments = 113.6B (konsolide DISI)
Phase 3a investment_properties = 3.1B (konsolide DISI)

Toplam = 308.7B (cakisma YOK)

Eger "Finansal Yatirimlar uzun vadeli" (551B) eklenseydi:
  Konsolide bilanco icindeki listed sub'lar tekrar sayilacakti
  -> SKIP edildi

## Multi-Dialect Etki

- Industrial (ARCLK): Yeni field'lar genelde None, etki minimal
- Holding (KCHOL/SAHOL): ANA hedef, 100B+ TL ek intrinsic katki
- Banking (AKBNK): Phase 3a kapsami DISI (banking_skip)

## Parser Notu

_find_value_in_tables ilk-match davranisi degistirilmiyor.
Yeni 2 tag KCHOL bilancosunda UNIQUE (tek gecis), sorun yok.

## Tag Mapping (Adim 3'te kullanilacak)

```python
NEW_INVESTMENT_TAGS = {
    "equity_method_investments": "Ozkaynak Yontemiyle Degerlenen Yatirimlar",
    "investment_properties": "Yatirim Amacli Gayrimenkuller",
}
```

## Validation Beklentisi (Adim 4)

- KCHOL.equity_method_investments ≈ 113.6B TL (±%5)
- KCHOL.investment_properties ≈ 3.1B TL (±%5)
- ARCLK.equity_method_investments = None (beklenen)
- TUPRS 211.95 INTACT
- 615 ticker total_count korundu

## Sonraki Adim

Adim 2 (commit 54): FinancialLineItems dataclass'a 2 field ekle
Adim 3 (commit 55): _parse_balance_sheet'e tag mapping ekle
Adim 4 (commit 56): Batch regen + validation
Adim 5 (commit 57): Audit chain + anchor v4.3.3-phase3a-sealed
