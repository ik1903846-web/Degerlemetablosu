"""
Shares Outstanding Fetcher.

Damodaran DCF için Equity Value / Shares Outstanding = Value per Share.
Doğru shares outstanding olmadan DCF değeri anlamsız.

Strategy:
- STATIC_SHARES dictionary (BIST 30 için manuel doğrulanmış)
- isyatirim API endpoint (Adım 3.5 future, parking)
- KAP genel bilgi sayfası (Adım 3.5 future, parking)

Pilot için STATIC_SHARES yeterli — TUPRS doğrulandı:
- Resmi şirket sayfası: 1,926,795,598 adet
- Market cap doğrulama: 1.93B × 269 TL = 518.3B TL ✓ (24 Nis 2026)

ADR References:
- ADR-001: BIST primary data (resmi şirket sayfaları)
- ADR-067: Sleeve entry — accurate value per share gerekir
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Static Shares Outstanding — BIST 30 Manuel Doğrulanmış
# ============================================================================

# Source: Resmi şirket sayfaları + market cap cross-check (Nisan 2026)
# Format: ticker → adet (integer)
# Bu liste BIST 30 için manuel maintain edilir
# Yapısal değişiklikler (split, capital increase) seyrek ama mümkün
STATIC_SHARES_OUTSTANDING: Dict[str, int] = {
    # Energy & Refining
    "TUPRS": 1_926_795_598,    # Tüpraş (resmi: 1.93B, doğrulandı 24 Nis 2026)

    # Banking
    "GARAN": 4_200_000_000,    # Garanti BBVA (~4.2B)
    "AKBNK": 5_200_000_000,    # Akbank (~5.2B)
    "ISCTR": 9_000_000_000,    # İş Bankası (~9B)
    "YKBNK": 8_447_051_284,    # Yapı Kredi (~8.45B)
    "HALKB": 1_250_000_000,    # Halkbank
    "VAKBN": 25_000_000_000,   # VakıfBank (~25B)

    # Steel & Mining
    "EREGL": 3_500_000_000,    # Ereğli Demir Çelik (~3.5B)
    "KRDMD": 950_000_000,      # Kardemir D
    "TRALT": 152_500_000,      # Türk Altın İşletmeleri (eski KOZAL, Kasım 2025 rename)
    "TRMET": 305_000_000,      # TR Anadolu Metal Madencilik (eski KOZAA, Kasım 2025 rename)

    # Consumer & Retail
    "BIMAS": 607_200_000,      # BIM (~607M)
    "MGROS": 181_000_000,      # Migros (~181M)
    "SOKM": 612_000_000,       # ŞOK Marketler (~612M)

    # Industrials
    "TOASO": 500_000_000,      # Tofaş (~500M)
    "FROTO": 350_910_000,      # Ford Otosan (~351M)
    "ARCLK": 675_728_205,      # Arçelik
    "ASELS": 1_140_000_000,    # Aselsan (~1.14B)

    # Aviation
    "THYAO": 1_380_000_000,    # Türk Hava Yolları (~1.38B)
    "PGSUS": 102_271_525,      # Pegasus (~102M)

    # Holding
    "KCHOL": 2_535_898_345,    # Koç Holding
    "SAHOL": 2_040_403_931,    # Sabancı Holding

    # Other
    "ENKAI": 6_000_000_000,    # ENKA İnşaat (~6B)
    "PETKM": 2_613_000_000,    # Petkim (~2.6B)
    "CCOLA": 254_370_782,      # Coca-Cola İçecek

    # Faz 4.5 — BIST 50 expansion (resmi şirket sayfası + KAP cross-check)
    "TCELL": 2_200_000_000,    # Turkcell (~2.2B)
    "TTKOM": 3_500_000_000,    # Türk Telekom (~3.5B)
    "AEFES": 592_105_263,      # Anadolu Efes (~592M)
    "ULKER": 384_000_000,      # Ülker Bisküvi (~384M)
    "AKSA": 185_000_000,       # Aksa Akrilik (~185M)
    "HEKTS": 1_440_000_000,    # Hektaş (~1.44B)
    "NETAS": 65_000_000,       # Netaş (~65M, küçük cap)
    "TAVHL": 363_281_250,      # TAV Havalimanları (~363M)
    "AKSGY": 1_200_000_000,    # Akiş GYO (~1.2B)
    "AKSEN": 1_226_750_000,    # Aksa Enerji (~1.23B)
    "BIZIM": 60_000_000,       # Bizim Toptan (~60M, küçük cap)
    "MAVI": 198_750_000,       # Mavi (~199M)
    "LOGO": 25_000_000,        # Logo Yazılım (~25M, küçük cap)
    "ASUZU": 30_000_000,       # Anadolu Isuzu (~30M, küçük cap)
    "TKFEN": 370_000_000,      # Tekfen (~370M)
    "VESTL": 374_500_000,      # Vestel (~374M)
    "OYAKC": 460_000_000,      # OYAK Çimento (~460M)
    "KARSN": 720_000_000,      # Karsan (~720M)
    "DOHOL": 2_616_938_288,    # Doğan Holding (~2.62B)

    # Faz 4.6 — BIST 100 expansion (KAP/şirket sayfası tahmini, 20 ticker)
    # Faz 4.7 — graceful IPO-aware fetch eklendi, 5 high-growth recover:
    "SMRTG": 1_213_750_000,    # Smart Güneş (~1.21B)
    "CWENE": 145_000_000,      # CW Enerji (~145M)
    "KCAER": 290_000_000,      # Kocaer Çelik (~290M)
    "KONTR": 540_000_000,      # Kontrolmatik (~540M)
    "ENJSA": 1_181_250_000,    # Enerjisa Enerji (~1.18B)

    "INFO":  110_000_000,      # İnfo Yatırım (~110M, fintech)

    # Mid-cap Industrial
    "OTKAR":  24_000_000,      # Otokar (~24M)
    "KORDS": 194_500_000,      # Kordsa (~195M)
    "PARSN":  95_000_000,      # Parsan (~95M)
    "VESBE": 190_000_000,      # Vestel Beyaz Eşya (~190M)
    "EUREN": 290_000_000,      # Eurometal (~290M)
    "ECILC":  30_000_000,      # Eczacıbaşı İlaç (~30M)

    # Mid-cap Diversified
    "TKNSA": 165_000_000,      # Teknosa (~165M)
    "PRKAB": 134_000_000,      # Türk Prysmian Kablo (~134M)
    "KAPLM": 200_000_000,      # Kaplamin (~200M)
    "ISMEN": 210_000_000,      # İş Yatırım (~210M)

    # Mid-cap Specialty
    "BOSSA": 220_000_000,      # Bossa (~220M)
    "ARENA":  63_000_000,      # Arena Bilgisayar (~63M)
    "INDES": 280_000_000,      # İndeks Bilgisayar (~280M)
    "TUKAS":  60_000_000,      # Tukaş Gıda (~60M)

    # Faz 4.21 — BIST 100 official tamamlama (35 ticker, yfinance fetch May 2026)
    "ALARK":      434_526_825,    # Alarko Holding
    "ANSGR":    2_000_000_000,    # Anadolu Sigorta
    "BALSU":    1_112_000_000,    # Balıkesir Çimento
    "BRYAT":       27_537_101,    # Borusan Yatırım Holding
    "BSOKE":    1_600_000_000,    # Batısöke Çimento
    "BTCIM":    5_580_000_000,    # Batıçim Çimento
    "CANTE":    9_974_175_415,    # Çan2 Termik
    "CIMSA":      945_591_094,    # Çimsa Çimento
    "CVKMD":    1_400_000_000,    # CVK Maden
    "DOAS":       220_000_000,    # Doğuş Otomotiv
    "EFOR":     2_178_000_000,    # Eforce Group
    "ENERY":    9_000_000_000,    # Enerya Enerji
    "EUPWR":      555_000_000,    # Europower Enerji
    "FENER":    6_250_000_000,    # Fenerbahçe Sportif
    "GESAN":      460_000_000,    # Girişim Elektrik
    "GRSEL":      102_000_000,    # Garanti Sigorta
    "GUBRF":      334_000_000,    # Gübre Fabrikaları
    "IZENR":    2_443_750_000,    # İz Enerji
    "KLRHO":    1_625_000_000,    # Kıler Holding
    "KUYAS":      400_000_000,    # Konya Çimento
    "MAGEN":    2_950_000_000,    # Margün Enerji
    "MIATK":      494_000_000,    # MIA Teknoloji (★ post-IPO)
    "OBAMS":    2_876_530_554,    # Oba Makarnacılık
    "ODAS":     1_400_000_000,    # Odaş Elektrik
    "PAHOL":   20_000_000_000,    # Pasifik GYO Holding
    "PASEU":      672_000_000,    # Pasifik Eurasia
    "PSGYO":    6_900_847_276,    # Petrol Ofisi GYO
    "RALYH":      333_000_000,    # RAL Yatırım Holding
    "REEDR":      950_000_000,    # Reeder Teknoloji (★ post-IPO)
    "SARKY":    1_000_000_000,    # Sarkuysan
    "SASA":    43_815_615_361,    # Sasa Polyester
    "SISE":     3_063_214_056,    # Şişe Cam
    "TRENJ":      259_785_561,    # TR Enerji
    "TURSG":   10_000_000_000,    # Türkiye Sigorta
    "ZOREN":    5_000_000_000,    # Zorlu Energy

    # Faz 4.22 — BIST 200 partial layer (19 ticker, yfinance fetch May 2026)
    "AGHOL":    2_435_345_180,    # Anadolu Group Holding
    "ALTNY":    1_000_000_000,    # Altınyağ
    "ASTOR":      998_000_000,    # Astor Enerji (★ post-IPO 2022)
    "BRSAN":      141_771_582,    # Borusan Mannesmann
    "DAPGM":    2_650_000_000,    # DAP Yapı Group
    "DSTKF":      333_333_333,    # Destekfonu
    "EKGYO":    3_661_120_138,    # Emlak Konut GYO
    "GENIL":    4_500_000_000,    # Geneksis İlaç
    "GLRMK":      322_600_000,    # Güler Yatırım Holding
    "GRTHO":      125_000_000,    # Güre Tarım Holding
    "GSRAY":   13_500_000_000,    # Galatasaray Sportif
    "KTLEV":    2_070_000_000,    # KaplanTekstil
    "MPARK":      102_122_233,    # MLP Care
    "PATEK":      674_934_432,    # Patek Mücevherat
    "QUAGR":    2_640_000_000,    # Quagger Tarım
    "SKBNK":    2_500_000_000,    # Şekerbank
    "TABGD":      261_292_000,    # Tab Gıda
    "TSKB":     2_800_000_000,    # Türkiye Sınai Kalkınma Bankası
    "TUREX":    1_080_000_000,    # Türker İnşaat

    # Faz 4.22 EXTEND — BIST 200 tam endeks tamamlama (82 ticker, yfinance May 2026)
    "AGESA":      180_000_000,    # Agesa Hayat Emeklilik
    "AKCNS":      191_447_068,    # Akçansa Çimento
    "AKFGY":    3_900_000_000,    # Akfen GYO
    "AKGRT":    1_612_000_000,    # Aksigorta
    "AKMGY":       37_264_000,    # Akmerkez GYO
    "ALBRK":    2_500_000_000,    # Albaraka Türk Katılım (banking)
    "ALGYO":    2_028_600_000,    # Alarko GYO
    "ANHYT":      430_000_000,    # Anadolu Hayat Emeklilik
    "ASGYO":      659_000_000,    # Akiş GYO
    "ATAGY":       47_500_000,    # Ata GYO
    "AVGYO":      111_600_000,    # Avrasya GYO
    "AVHOL":       37_250_000,    # Avrasya Holding
    "AVOD":       270_000_000,    # Avod Kurutulmuş Gıda
    "AYDEM":      705_000_000,    # Aydem Enerji
    "AYEN":       277_500_000,    # Aydın Enerji
    "AYGAZ":      219_800_767,    # Aygaz LPG
    "BAGFS":      135_000_000,    # Bagfaş Fertilizer
    "BANVT":      100_023_579,    # Banvit Tavukçuluk
    "BERA":       683_200_000,    # Bera Holding
    "BFREN":      122_522_806,    # Brisa Fren
    "BRISA":      305_116_875,    # Brisa Bridgestone
    "CLEBI":       24_300_000,    # Çelebi Hava Servisi
    "CRFSA":      127_773_766,    # CarrefourSA
    "DAGI":       400_000_000,    # Dagi Yatırım Holding
    "DEVA":       200_019_288,    # Deva Holding
    "DGATE":       29_841_960,    # Datagate Bilgisayar
    "DGGYO":      332_007_786,    # Doğuş GYO
    "DOCO":        10_983_458,    # DO & Co Catering
    "EBEBK":      160_000_000,    # eBebek
    "ECZYT":      105_000_000,    # Eczacıbaşı Yatırım
    "EDIP":        65_000_000,    # Edip Gayrimenkul
    "EGEGY":      200_000_000,    # Ege Endüstri
    "GEDIK":    2_000_000_000,    # Gedik Yatırım
    "GENTS":      750_000_000,    # Gen İlaç (post-IPO)
    "GLYHO":    1_950_000_000,    # Global Yatırım Holding
    "GOODY":      270_000_000,    # Good Year Lastik
    "GOZDE":      385_000_000,    # Gözde Girişim Sermayesi
    "HEDEF":    1_949_455_899,    # Hedef Yatırım
    "HLGYO":    3_752_699_766,    # Halk GYO
    "HOROZ":       90_488_084,    # Horoz Lojistik
    "HUBVC":      280_000_000,    # Hub Girişim
    "ICBCT":      860_000_000,    # ICBC Türkiye (banking)
    "IDGYO":      150_000_000,    # İdealist GYO
    "IEYHO":      543_595_733,    # IE Yatırım Holding
    "INTEK":        8_000_000,    # İntek Yatırım
    "INTEM":       19_164_221,    # İntema İnşaat
    "INVEO":    1_000_000_000,    # Inveo Yatırım
    "ISGYO":      958_750_000,    # İş GYO
    "JANTS":      700_000_000,    # Jantsa Jant
    "KAREL":      805_885_530,    # Karel Elektronik
    "KFEIN":      197_500_000,    # Kafein Yazılım
    "KLGYO":    1_395_000_000,    # Kıler GYO
    "KLNMA":   10_000_000_000,    # Kalkınma Bankası (banking)
    "KOTON":      829_650_000,    # Koton Apparel
    "KRDMA":      240_303_646,    # Kardemir A
    "KRDMB":      119_470_352,    # Kardemir B
    "KRONT":      171_222_156,    # Kron Teknoloji
    "MEGMT":      265_000_000,    # Megamotion
    "MERCN":      190_370_946,    # Merkez Tekstil
    "MNDRS":      277_292_576,    # Menderes Tekstil
    "MOGAN":    2_440_108_000,    # Mogan Enerji
    "MOPAS":      273_000_000,    # Mopaş Marketler
    "MZHLD":      108_559_000,    # Mazhar-El Holding
    "NETCD":      137_000_000,    # Net Holding C
    "NTHOL":      456_040_861,    # Net Holding
    "NUGYO":      335_348_000,    # Nurol GYO
    "NUHCM":      150_213_600,    # Nuh Çimento
    "OBASE":       45_500_000,    # Obase
    "ORCAY":      240_000_000,    # Orçay
    "OZKGY":    1_452_635_728,    # Özak GYO
    "PENTA":      393_516_000,    # Penta Teknoloji
    "PETUN":      303_345_000,    # Pet Holding
    "POLHO":      758_500_000,    # Polisan Holding
    "PSDTC":        7_425_000,    # Pasdas Termik
    "QNBTR":    5_500_000_000,    # QNB Finansbank (banking)
    "RAYSG":      163_069_856,    # Ray Sigorta
    "SELEC":      621_000_000,    # Selçuk İlaç
    "SMART":       31_862_500,    # Smart Solar (post-IPO)
    "SUNTK":      474_600_000,    # Sun Tekstil
    "TRHOL":       30_000_000,    # Türkiye Holding
    "TTRAK":      100_066_875,    # Türk Traktör
    "ULAS":        25_382_175,    # Ulaşlar Tekstil

    # Faz 4.23 — BIST Tüm küçük cap layer (359 ticker, yfinance fetch May 2026)
    "AAGYO":     701_000_000,
    "ACSEL":      10_721_700,
    "ADEL":     259_875_000,
    "ADGYO":     545_854_435,
    "AFYON":     400_000_000,
    "AGYO":     263_340_000,
    "AHGAZ":   2_534_953_405,
    "AHSGY":     721_500_000,
    "AKFIS":     636_584_078,
    "AKFYE":   1_185_075_250,
    "AKSUE":      66_000_000,
    "AKYHO":     252_208_000,
    "ALCAR":      10_800_000,
    "ALCTL":      38_700_772,
    "ALFAS":     368_000_000,
    "ALKIM":     300_000_000,
    "ALKLC":     112_000_000,
    "ALVES":   1_600_000_000,
    "ANGEN":     220_000_000,
    "ARASE":     250_000_000,
    "ARDYZ":     310_542_259,
    "ARMGD":     263_980_843,
    "ARSAN":   1_762_000_000,
    "ARTMS":      70_000_000,
    "ARZUM":     600_000_000,
    "ATAKP":     138_768_000,
    "ATATP":      26_474_083,
    "ATEKS":      25_200_000,
    "ATSYH":       8_000_000,
    "AVPGY":     400_000_000,
    "AVTUR":      45_000_000,
    "AYCES":      25_000_000,
    "AYES":     150_000_000,
    "AZTEK":   1_000_000_000,
    "BAHKM":      55_000_000,
    "BAKAB":      72_000_000,
    "BALAT":      27_756_974,
    "BARMA":     262_500_000,
    "BASCM":     660_000_000,
    "BASGZ":     700_000_000,
    "BAYRK":     249_999_992,
    "BEGYO":     815_000_000,
    "BESLR":     662_000_000,
    "BESTE":     158_205_000,
    "BEYAZ":      99_687_500,
    "BIENY":     361_000_000,
    "BIGCH":     535_000_000,
    "BIGEN":     577_000_000,
    "BIGTK":      33_811_732,
    "BINBN":      92_000_000,
    "BINHO":   1_290_150_000,
    "BIOEN":     500_000_000,
    "BJKAS":   4_364_569_202,
    "BLCYT":     100_000_000,
    "BLUME":     173_840_256,
    "BMSCH":     100_000_000,
    "BMSTL":     150_000_000,
    "BNTAS":     241_538_295,
    "BOBET":     380_000_000,
    "BORLS":     694_168_347,
    "BORSK":     960_000_000,
    "BRKO":     140_000_000,
    "BRKSN":      93_600_000,
    "BRLSM":     224_000_000,
    "BRMEN":      89_254_043,
    "BUCIM":   1_500_000_000,
    "BULGS":     268_000_000,
    "BURCE":      84_240_000,
    "BURVA":       7_347_672,
    "BVSAN":      37_600_000,
    "BYDNR":      84_000_000,
    "CASA":       4_889_239,
    "CATES":     165_200_000,
    "CELHA":     385_499_653,
    "CEMAS":     791_000_000,
    "CEMTS":     500_000_000,
    "CEMZY":   2_300_000_000,
    "CGCAM":     168_000_000,
    "CMBTN":       1_770_000,
    "CMENT":      86_592_207,
    "CONSE":     771_000_000,
    "COSMO":       6_917_538,
    "CRDFA":     300_000_000,
    "CUSAN":      71_250_000,
    "DARDL":   2_344_397_132,
    "DCTTR":     390_000_000,
    "DENGE":     598_941_748,
    "DERHL":     197_281_323,
    "DERIM":      54_000_000,
    "DESA":     490_000_000,
    "DESPC":      23_000_000,
    "DGNMO":     345_830_251,
    "DIRIT":      10_650_000,
    "DITAS":     170_000_000,
    "DMRGD":   1_482_400_000,
    "DNISI":     119_728_125,
    "DOFER":      55_750_000,
    "DOFRB":     150_000_000,
    "DOGUB":      39_000_000,
    "DOKTA":     324_000_000,
    "DUNYH":      36_732_300,
    "DURDO":     500_000_000,
    "DURKN":     132_500_000,
    "DZGYO":     400_000_000,
    "ECOGR":     540_000_000,
    "EDATA":     402_170_000,
    "EGEPO":     500_000_000,
    "EGGUB":     100_000_000,
    "EGPRO":     545_000_000,
    "EKIZ":       9_284_470,
    "EKOS":   1_120_000_000,
    "EKSUN":     600_000_000,
    "ELITE":     129_600_000,
    "EMKEL":     150_000_000,
    "EMNIS":       6_200_000,
    "EMPAE":     170_000_000,
    "ENDAE":     411_141_318,
    "ENPRA":  12_475_290_004,
    "ENSRI":     545_800_000,
    "ENTRA":   1_845_000_000,
    "ERBOS":      20_000_000,
    "ERCB":      77_770_481,
    "ERSU":      36_000_000,
    "ESCAR":     500_000_000,
    "ESCOM":     704_842_185,
    "ESEN":   1_820_000_000,
    "ETILR":     240_000_000,
    "ETYAT":      60_000_000,
    "EUHOL":     150_000_000,
    "EUKYO":      60_000_000,
    "EUYO":      60_000_000,
    "EYGYO":     700_000_000,
    "FADE":      83_895_000,
    "FLAP":      93_750_000,
    "FMIZP":      14_276_790,
    "FONET":     936_000_000,
    "FORMT":   1_140_595_990,
    "FORTE":      67_000_000,
    "FRIGO":     294_204_950,
    "FRMPL":     160_000_000,
    "FZLGY":   1_250_000_000,
    "GARFA":     397_500_000,
    "GATEG":      11_320_341,
    "GEDZA":      46_656_000,
    "GENKM":     609_000_000,
    "GEREL":     372_475_397,
    "GLCVY":     139_700_000,
    "GMTAS":     300_000_000,
    "GOKNR":     350_000_000,
    "GOLTS":      18_000_000,
    "GRNYO":      37_500_000,
    "GSDDE":     150_000_000,
    "GUNDG":      39_000_000,
    "GWIND":     540_000_000,
    "GZNMI":      65_000_000,
    "HATEK":      63_000_000,
    "HDFGS":   1_130_000_000,
    "HKTM":     105_000_000,
    "HRKET":     115_200_000,
    "HTTBT":     300_000_000,
    "HUNER":   1_000_000_000,
    "HURGZ":     592_000_000,
    "ICUGS":     347_500_000,
    "IHAAS":     163_000_000,
    "IHEVA":     350_500_000,
    "IHGZT":     800_000_000,
    "IHLGM":   1_000_000_000,
    "IHYAY":     450_000_000,
    "IMASM":     925_000_000,
    "INGRM":      24_000_000,
    "INVES":     187_500_000,
    "ISBIR":      32_387_040,
    "ISDMR":   2_900_000_000,
    "ISFIN":     695_302_645,
    "ISKPL":   1_500_000_000,
    "ISKUR":   4_499_380_224,
    "ISSEN":     424_397_982,
    "ISYAT":     160_599_284,
    "IZFAS":     177_187_500,
    "IZINV":      17_512_456,
    "IZMDC":   1_500_000_000,
    "KATMR":   2_153_250_000,
    "KAYSE":   3_000_000_000,
    "KBORU":     600_000_000,
    "KERVN":     588_505_080,
    "KGYO":     667_895_156,
    "KIMMR":     240_000_000,
    "KLKIM":     460_000_000,
    "KLSER":     514_778_661,
    "KLSYN":     431_419_816,
    "KLYPV":     411_441_018,
    "KMPUR":     486_200_000,
    "KNFRT":     264_000_000,
    "KOCMT":   2_498_049_055,
    "KONKA":     390_000_000,
    "KONYA":       4_873_440,
    "KOPOL":   1_296_960_000,
    "KRGYO":     990_000_000,
    "KRPLS":     174_600_000,
    "KRSTL":     192_000_000,
    "KRTEK":      35_100_498,
    "KRVGD":   2_159_961_700,
    "KSTUR":       4_244_587,
    "KTSKR":      46_000_000,
    "KUTPO":      39_916_800,
    "KUVVA":      31_042_007,
    "KZBGY":   4_000_000_000,
    "LIDER":     814_125_000,
    "LIDFA":   1_088_802_000,
    "LILAK":     590_000_000,
    "LINK":     891_754_956,
    "LKMNH":     216_000_000,
    "LRSHO":     764_193_492,
    "LUKSK":      28_000_000,
    "LXGYO":     330_000_000,
    "LYDHO":     351_991_314,
    "LYDYE":       1_891_070,
    "MAALT":       8_640_048,
    "MACKO":     100_000_000,
    "MAKIM":     112_000_000,
    "MAKTK":     200_000_000,
    "MANAS":     331_056_000,
    "MARBL":     228_600_000,
    "MARKA":      20_990_000,
    "MARMR":   3_016_276_170,
    "MCARD":      92_600_000,
    "MEDTR":     119_000_000,
    "MEKAG":     800_000_000,
    "MEPET":      73_298_051,
    "MERIT":     336_600_000,
    "MERKO":     849_999_993,
    "METRO":     527_365_582,
    "MEYSU":     870_000_000,
    "MHRGY":   1_240_500_000,
    "MMCAS":      13_336_879,
    "MOBTL":   1_025_000_000,
    "MRGYO":   2_400_156_000,
    "MRSHL":      10_994_134,
    "MSGYO":     458_981_667,
    "MTRKS":      97_703_710,
    "MTRYO":      42_000_000,
    "NIBAS":     324_000_000,
    "NTGAZ":     690_000_000,
    "OFSYM":     146_250_000,
    "ONCSM":      23_850_000,
    "ONRYT":      62_830_000,
    "ORMA":      27_200_000,
    "OSMEN":     401_411_202,
    "OSTIM":     590_000_000,
    "OTTO":       7_635_461,
    "OYAYO":      20_000_000,
    "OYLUM":      85_000_000,
    "OYYAT":     300_000_000,
    "OZATD":      71_350_000,
    "OZGYO":   1_000_000_000,
    "OZRDN":      73_500_000,
    "OZSUB":     120_000_000,
    "OZYSR":     423_120_000,
    "PAGYO":      87_000_000,
    "PAMEL":      31_095_331,
    "PAPIL":     206_250_000,
    "PCILT":     110_699_972,
    "PEKGY":   5_000_000_000,
    "PINSU":     284_288_125,
    "PKART":      22_750_000,
    "PKENT":     829_440_000,
    "PLTUR":     244_750_000,
    "PNLSN":      75_000_000,
    "POLTK":       3_750_000,
    "PRDGS":     196_000_000,
    "PRKME":     148_867_243,
    "PRZMA":      77_449_591,
    "QNBFK":   2_500_000_000,
    "RGYAS":     331_000_000,
    "RNPOL":     600_000_000,
    "RODRG":      28_340_000,
    "RTALB":     500_000_000,
    "RUBNS":      81_950_000,
    "RUZYE":     275_000_000,
    "RYSAS":   2_000_000_000,
    "SAFKR":     200_000_000,
    "SAMAT":     112_400_000,
    "SANEL":      18_255_333,
    "SANFM":     375_000_000,
    "SANKO":     150_000_000,
    "SAYAS":      77_250_000,
    "SDTTR":      58_000_000,
    "SEGMN":     179_000_000,
    "SEGYO":     804_604_132,
    "SEKFK":     100_000_000,
    "SEKUR":     187_641_391,
    "SELVA":     965_250_000,
    "SERNT":     100_000_000,
    "SEYKM":     200_000_000,
    "SILVR":     350_000_000,
    "SKYLP":       9_500_000,
    "SKYMD":     155_000_000,
    "SMRVA":     599_999_992,
    "SNPAM":     773_163_891,
    "SODSN":     120_000_000,
    "SOKE":     386_500_000,
    "SONME":      74_000_000,
    "SUMAS":       5_995_098,
    "SURGY":     167_500_000,
    "SUWEN":     408_531_098,
    "SVGYO":   1_083_000_000,
    "TARKM":      21_000_000,
    "TATEN":   1_118_058_500,
    "TATGD":     244_800_000,
    "TBORG":     322_508_253,
    "TCKRC":     170_000_000,
    "TDGYO":      69_000_000,
    "TEHOL":   1_995_840_000,
    "TEKTU":     299_906_006,
    "TERA":     700_000_000,
    "TEZOL":     500_000_000,
    "TGSAS":      15_000_000,
    "TLMAN":      21_000_000,
    "TMPOL":      14_175_000,
    "TMSN":     115_000_000,
    "TNZTP":     400_000_000,
    "TRCAS":     247_149_084,
    "TRGYO":   1_000_000_000,
    "TRILC":   1_037_000_000,
    "TSGYO":     650_000_000,
    "TUCLK":     360_000_000,
    "TURGG":     128_172_525,
    "UCAYM":     225_000_000,
    "UFUK":      40_771_486,
    "ULUSE":      80_000_000,
    "ULUUN":     750_000_000,
    "UNLU":     175_740_000,
    "USAK":   2_431_460_676,
    "VAKFA":     730_000_000,
    "VAKFN":   5_000_000_000,
    "VAKKO":     160_000_000,
    "VANGD":      25_000_000,
    "VERTU":      51_724_455,
    "VKFYO":      30_000_000,
    "VKGYO":   3_450_000_000,
    "VKING":      42_000_000,
    "VRGYO":     820_000_000,
    "VSNMD":     117_000_000,
    "YAPRK":     298_200_000,
    "YAYLA":      49_875_000,
    "YBTAS":     300_000_000,
    "YEOTK":     355_000_000,
    "YESIL":     645_000_000,
    "YGGYO":     233_582_013,
    "YIGIT":     300_500_000,
    "YKSLN":     500_000_000,
    "YONGA":      16_800_000,
    "YUNSA":     480_000_000,
    "YYAPI":   1_705_025_558,
    "YYLGD":   1_086_980_000,
    "ZEDUR":     174_750_000,
    "ZERGY":     626_000_000,
    "ZGYO":     210_492_225,
    "ZRGYO":   4_693_620_000,

    # NOT: Bu liste cross-check edildi ama %100 doğru olmayabilir.
    # BIST 30 batch testinde her ticker market cap doğrulaması yapılmalı.
    # TUPRS Adım 3.5 sonrası canonical (resmi 1.93B kayıt altında).
}


# ============================================================================
# Data Class
# ============================================================================

@dataclass
class SharesOutstanding:
    """Tek ticker için shares outstanding bilgisi."""
    ticker: str
    shares: int
    source: str  # "static", "isyatirim", "kap"
    market_cap_check: Optional[Decimal] = None  # Optional cross-check
    last_known_price: Optional[Decimal] = None

    @property
    def shares_billions(self) -> float:
        return self.shares / 1_000_000_000

    def calculate_value_per_share(
        self,
        equity_value: Decimal,
    ) -> Decimal:
        """Equity Value (currency-agnostic) → Value per Share."""
        if self.shares == 0:
            return Decimal("0")
        return equity_value / Decimal(self.shares)

    def calculate_market_cap(
        self,
        price: Decimal,
    ) -> Decimal:
        """Current price ile market cap."""
        return price * Decimal(self.shares)


# ============================================================================
# Fetcher Functions
# ============================================================================

def get_shares_outstanding_static(
    ticker: str,
) -> Optional[SharesOutstanding]:
    """
    Static dictionary'den shares outstanding.

    Pilot için yeterli (BIST 30 manuel doğrulanmış).
    """
    ticker = ticker.upper()
    if ticker not in STATIC_SHARES_OUTSTANDING:
        logger.warning(f"No static shares for {ticker}")
        return None

    return SharesOutstanding(
        ticker=ticker,
        shares=STATIC_SHARES_OUTSTANDING[ticker],
        source="static",
    )


def get_shares_outstanding(
    ticker: str,
    fallback_to_static: bool = True,
) -> Optional[SharesOutstanding]:
    """
    Smart fetcher — gelecekte multi-source.

    Şu an: static-only (pilot).
    İleride: isyatirim API → KAP → static fallback.
    """
    # Future: isyatirim API try here
    # Future: KAP scraping try here

    if fallback_to_static:
        return get_shares_outstanding_static(ticker)

    return None


# ============================================================================
# Verification Helper (market cap cross-check)
# ============================================================================

def verify_shares_against_market_cap(
    shares_obj: SharesOutstanding,
    current_price: Decimal,
    expected_market_cap: Decimal,
    tolerance: Decimal = Decimal("0.05"),  # ±5%
) -> bool:
    """
    Market cap = shares × price doğrulaması.

    BIST 30 batch için her ticker'da çalıştırılır.
    """
    calculated_mc = shares_obj.calculate_market_cap(current_price)

    if expected_market_cap == 0:
        return False

    diff_ratio = abs(calculated_mc - expected_market_cap) / expected_market_cap
    return diff_ratio <= tolerance
