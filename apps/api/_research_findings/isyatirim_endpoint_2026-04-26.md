# isyatirim.com.tr API Discovery — Faz 2.1.1b Findings

**Tarih:** 26 Nisan 2026
**Durum:** JACKPOT — Tek endpoint, 4 mali tablo

## Özet

isyatirim.com.tr Türkiye finans community'sinin uzun yıllar kullandığı
AJAX endpoint hâlâ aktif. Tek HTTP call ile TUPRS finansalları geliyor.

## Endpoint

URL: https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo

Parametreler:
- companyCode: BIST ticker (TUPRS, EREGL, GARAN, vb.)
- exchange: NTL (BIST endpoint kodu)
- financialGroup: XI_29 (industrial), XI_30 (banking, test edilecek)
- year1+period1, ..., year4+period4: Max 4 dönem comparison

Period kodları:
- 3 = Q1, 6 = H1, 9 = 9M, 12 = Yıllık

## JSON Response Yapısı

Top-level: ok, errorCode, errorDescription, transactionId, value (array)

Her item:
- itemCode: XBRL kalem kodu (1A, 3DF, 4C, vb.)
- itemDescTr: Türkçe açıklama
- itemDescEng: İngilizce açıklama (BAZEN null!)
- value1, value2, value3, value4: 4 dönem değer (STRING formatında)

## Defensive Coding Notları

1. value1-4 STRING formatında — Decimal cast gerekli
2. itemDescEng bazen null — (value or '') pattern
3. Negatif sayılar string '-prefix' ile
4. Indentation hiyerarşisi itemDescTr içinde whitespace
5. Summary rows (subtotals) kalemleri var

## itemCode Taxonomy (TUPRS 147 kalem doğrulandı)

Bilanço Aktif:
- 1A: Dönen Varlıklar (13 kalem)
- 1B: Duran Varlıklar (17 kalem)

Bilanço Pasif:
- 2A: Kısa Vadeli Yükümlülükler (14 kalem)
- 2B: Uzun Vadeli Yükümlülükler (13 kalem)

Özkaynaklar:
- 2N: Özkaynaklar TOPLAM (1 kalem)
- 2O: Ana Ortaklığa Ait Özkaynaklar (12 kalem)

Gelir Tablosu:
- 3B: Sürdürülen Faaliyetler (1)
- 3C: Satış / COGS (9)
- 3D: Brüt Kâr → Faaliyet Giderleri (8)
- 3H: Faaliyet Sonuçları (9)
- 3I: Vergi Öncesi Kâr / Vergi (5)
- 3J: Sürdürülen Faaliyetler Net (1)
- 3K: Durdurulan Faaliyetler (2)
- 3L: Dönem Karı / Azınlık (3)
- 3Z: EPS / Diluted EPS (5)

Nakit Akışı:
- 4B: Amortisman, Tazminat (8)
- 4C: Nakit Akış (CF tablosu) (26)

## Damodaran DCF Mapping (Industrial FCFF)

Bu kalemler industrial_fcff.py motorunun input'ları için gerekli:

| Damodaran Input | itemCode | Açıklama | TUPRS 2024 v1 |
|---|---|---|---|
| Revenues | 4BC + 4BD | Yurtiçi + Yurtdışı satış | 1072 milyar TL |
| EBIT | 3DF | FAALİYET KARI/ZARARI | 46.7 milyar TL |
| Pre-Tax | 3I | Vergi Öncesi Kar | 41.6 milyar TL |
| Net Income | 2OCF | Dönem Net Kar/Zararı | 24.0 milyar TL |
| CapEx | 4CB serisi | Yatırım faaliyetleri | (toplam) |
| ΔWorking Capital | 4CAF | İşletme Sermayesi Değişim | -9.7 milyar TL |
| Debt KV | 2AA | Finansal Borçlar Kısa | 11.9 milyar TL |
| Debt UV | 2BA | Finansal Borçlar Uzun | 13.0 milyar TL |
| Cash | 1AA | Nakit ve Benzerleri | 96.3 milyar TL |
| Equity | 2N | Özkaynaklar TOPLAM | 374.7 milyar TL |
| Depreciation | 4B | Amortisman Giderleri | 12.6 milyar TL |
| Operating CF | 4C | İşletme Faaliyetlerinden Net Nakit | 46.2 milyar TL |

## Yarın Plan (Faz 2.1.2)

apps/api/data_layer/isyatirim_scraper.py implement:
- fetch_financial_statements(ticker, years, period)
- FinancialStatements dataclass
- Damodaran input mapping
- Test: TUPRS pilot

## Riskler

1. Endpoint version değişimi (mitigation: version-aware fetcher)
2. Banking için XI_30 farklı financialGroup (mitigation: sector lookup)
3. Rate limiting bilinmiyor (mitigation: throttle + backoff)
4. null values + string casts (mitigation: defensive code)

## Sonuç

10/10 DCF kategorisi bulundu. MaliTablo tek endpoint = full financial data.
Faz 2.1.2 implementation hazır.
