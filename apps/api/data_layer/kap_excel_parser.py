"""
KAP Excel Financial Report Parser (Faz 11 v4.0 — Session 2 REVISED).

KAP Excel-HTML export → structured financial line items dict.

Excel-HTML format:
  - 735 sub-tables (cell merge artifact)
  - Main Bilanço table: ~595 rows × 5 cols
  - Period header: "Cari Dönem 30.09.YYYY  Önceki Dönem 31.12.YYYY"
  - Sunum birimi: 1.000 TL (binlik) veya 1 TL
  - Konsolide / Solo

Key sections (Türkçe Tablo Başlıkları):
  - Finansal Durum Tablosu (Bilanço): Varlıklar, Yükümlülükler, Özkaynaklar
  - Kar veya Zarar Tablosu: Hasılat, Brüt Kar, Esas Faaliyet Karı, Net Dönem Karı
  - Nakit Akış Tablosu: İşletme/Yatırım/Finansman faaliyetleri

Damodaran DCF Mapping (probe-level — schema mapping Session 3 expand):
  Hasılat                              → revenue
  Esas Faaliyet Karı / Faaliyet Karı   → operating_income
  Vergi Gideri                         → tax_expense
  Yatırım faaliyetleri / Maddi Duran   → capex
  Net Dönem Karı                       → net_income
  Toplam Varlıklar                     → total_assets
  Toplam Yükümlülükler                 → total_liabilities
  Özkaynaklar                          → total_equity
  Nakit ve Nakit Benzerleri            → cash
  Kısa+Uzun Vadeli Finansal Borçlar    → total_debt
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class FinancialLineItems:
    """KAP Excel'den parse edilmiş Damodaran-relevant fields."""
    disclosure_index: int
    cari_donem: Optional[str] = None       # örn "30.09.2025"
    onceki_donem: Optional[str] = None
    sunum_birimi: Optional[str] = None     # "1.000 TL" veya "1 TL"
    konsolide: Optional[bool] = None

    # Income statement (Cari + Önceki)
    revenue_cari: Optional[float] = None
    revenue_onceki: Optional[float] = None
    operating_income_cari: Optional[float] = None
    operating_income_onceki: Optional[float] = None
    net_income_cari: Optional[float] = None
    net_income_onceki: Optional[float] = None
    tax_expense_cari: Optional[float] = None

    # Balance sheet
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    cash: Optional[float] = None
    short_term_debt: Optional[float] = None
    long_term_debt: Optional[float] = None

    # Computed
    operating_margin_pct: Optional[float] = None  # op_income / revenue × 100

    raw_table_count: int = 0
    parsed_field_count: int = 0
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)


def _parse_tr_number(val: Any) -> Optional[float]:
    """Turkish number format: '1.234.567,89' → 1234567.89"""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s in ("-", "—", "n/a", "N/A"):
        return None
    # TR format: thousands sep '.', decimal ','
    cleaned = s.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _find_value_in_tables(
    tables: List[pd.DataFrame],
    label_keywords: List[str],
    period_col: str = "cari",  # "cari" → first numeric column, "onceki" → second
) -> Optional[float]:
    """Tüm tablolarda label keyword arar, ilk numeric value döner.

    KAP Excel format: column 1 = label, column 3 = cari period, column 4 = önceki.
    Bazı tablolarda label column 0 da olabilir.
    """
    keywords = [k.lower() for k in label_keywords]

    for df in tables:
        if df.shape[0] < 3 or df.shape[1] < 3:
            continue

        # Try label_col 0, 1, 2 — KAP format generally col=1
        for label_col_idx in (1, 0, 2):
            if label_col_idx >= df.shape[1]:
                continue
            label_col = df.iloc[:, label_col_idx].fillna("").astype(str).str.lower()
            for kw in keywords:
                mask = label_col.str.contains(re.escape(kw), regex=True, na=False)
                if not mask.any():
                    continue
                # Find first non-empty match
                for row_idx in mask[mask].index:
                    row = df.iloc[row_idx]
                    # KAP layout: col 0=section, col 1=label, col 2=note(small int),
                    #             col 3=cari period value, col 4=onceki period value
                    # Note number genelde 1-2 haneli (< 1000); finansal değerler büyük.
                    # Filter: numeric > 1000 = financial, < 1000 = note column.
                    numeric_values = []
                    for ci in range(2, min(df.shape[1], 8)):  # skip col 0,1
                        v = _parse_tr_number(row.iloc[ci])
                        if v is not None and abs(v) >= 1000:
                            numeric_values.append((ci, v))
                    if not numeric_values:
                        # Negatif/sıfır ya da küçük value (loss) için fallback
                        for ci in range(3, min(df.shape[1], 8)):
                            v = _parse_tr_number(row.iloc[ci])
                            if v is not None:
                                numeric_values.append((ci, v))
                    if not numeric_values:
                        continue
                    if period_col == "cari":
                        return numeric_values[0][1]
                    elif period_col == "onceki" and len(numeric_values) > 1:
                        return numeric_values[1][1]

    return None


def parse_excel_html(content_bytes: bytes, disclosure_index: int = 0) -> FinancialLineItems:
    """KAP Excel-HTML bytes → FinancialLineItems."""

    fli = FinancialLineItems(disclosure_index=disclosure_index)

    try:
        all_tables = pd.read_html(io.BytesIO(content_bytes))
    except Exception as e:
        fli.error = f"read_html failed: {type(e).__name__}: {e}"
        return fli

    fli.raw_table_count = len(all_tables)
    if not all_tables:
        fli.error = "No tables found"
        return fli

    # Header (Table 0): Sunum birimi + Konsolide
    try:
        t0 = all_tables[0]
        if t0.shape[0] >= 2 and t0.shape[1] >= 2:
            t0_dict = dict(zip(t0.iloc[:, 0].astype(str), t0.iloc[:, 1].astype(str)))
            for k, v in t0_dict.items():
                if "para birimi" in k.lower():
                    fli.sunum_birimi = v.strip()
                elif "niteli" in k.lower():
                    fli.konsolide = "konsolide" in v.lower()
    except Exception as e:
        fli.notes.append(f"Header parse warn: {e}")

    # Period dates (search across all tables for header row)
    for df in all_tables:
        if df.shape[0] < 3:
            continue
        for i in range(min(5, df.shape[0])):
            row_str = " ".join(str(x) for x in df.iloc[i].fillna(""))
            period_match = re.findall(r"\d{2}\.\d{2}\.\d{4}", row_str)
            if len(period_match) >= 2:
                fli.cari_donem = fli.cari_donem or period_match[0]
                fli.onceki_donem = fli.onceki_donem or period_match[1]
                break
        if fli.cari_donem:
            break

    # Damodaran field extraction (cross-table search)
    # Income Statement
    fli.revenue_cari = _find_value_in_tables(all_tables, ["Hasılat"], "cari")
    fli.revenue_onceki = _find_value_in_tables(all_tables, ["Hasılat"], "onceki")
    fli.operating_income_cari = _find_value_in_tables(
        all_tables, ["Esas Faaliyet Karı", "Faaliyet Karı"], "cari",
    )
    fli.operating_income_onceki = _find_value_in_tables(
        all_tables, ["Esas Faaliyet Karı", "Faaliyet Karı"], "onceki",
    )
    fli.net_income_cari = _find_value_in_tables(
        all_tables, ["Dönem Karı", "Net Dönem Karı"], "cari",
    )
    fli.tax_expense_cari = _find_value_in_tables(
        all_tables, ["Vergi Gideri", "Vergi Karşılığı"], "cari",
    )

    # Balance Sheet
    fli.total_assets = _find_value_in_tables(
        all_tables, ["Toplam Varlıklar"], "cari",
    )
    fli.total_liabilities = _find_value_in_tables(
        all_tables, ["Toplam Yükümlülükler"], "cari",
    )
    fli.total_equity = _find_value_in_tables(
        all_tables, ["Özkaynaklar"], "cari",
    )
    fli.cash = _find_value_in_tables(
        all_tables, ["Nakit ve Nakit Benzerleri"], "cari",
    )

    # Computed
    if fli.revenue_cari and fli.operating_income_cari:
        if fli.revenue_cari != 0:
            fli.operating_margin_pct = fli.operating_income_cari / fli.revenue_cari * 100

    fli.parsed_field_count = sum(1 for v in [
        fli.revenue_cari, fli.operating_income_cari, fli.net_income_cari,
        fli.total_assets, fli.total_equity, fli.cash,
    ] if v is not None)

    return fli


if __name__ == "__main__":
    import sys
    import io as _io
    from pathlib import Path

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kap_excel_fetcher import fetch_excel_export  # noqa: E402

    print("=" * 70)
    print("KAP Excel Parser — Session 2 Revised Validation")
    print("=" * 70)

    targets = [
        ("TUPRS",   1510162, "ANCHOR  — DCF /share TL: 187.10 ±%5"),
        ("KUYAS",   1480086, "BUG     — isyatirim op_margin %16,027"),
        ("AGROT",   1481009, "NEW IPO — eski 559'da yoktu"),
    ]

    for ticker, idx, note in targets:
        print(f"\n{'─'*70}")
        print(f"{ticker}  disclosure_index={idx}  ({note})")
        print('─'*70)

        dl = fetch_excel_export(idx)
        if not dl.success:
            print(f"  ✗ Download fail: {dl.error}")
            continue
        print(f"  ✓ Downloaded {dl.content_length:,} bytes")

        fli = parse_excel_html(dl.content_bytes, disclosure_index=idx)
        if fli.error:
            print(f"  ⚠ Parse warning: {fli.error}")

        print(f"  Period:           Cari {fli.cari_donem}  Önceki {fli.onceki_donem}")
        print(f"  Sunum birimi:     {fli.sunum_birimi}")
        print(f"  Konsolide:        {fli.konsolide}")
        print(f"  Tables found:     {fli.raw_table_count}")
        print(f"  Fields parsed:    {fli.parsed_field_count} / 6")
        print(f"  Revenue (cari):   {fli.revenue_cari:>20,.0f}" if fli.revenue_cari else "  Revenue: ?")
        print(f"  OpIncome (cari):  {fli.operating_income_cari:>20,.0f}" if fli.operating_income_cari else "  OpIncome: ?")
        print(f"  Net Income:       {fli.net_income_cari:>20,.0f}" if fli.net_income_cari else "  Net Income: ?")
        print(f"  Total Assets:     {fli.total_assets:>20,.0f}" if fli.total_assets else "  Total Assets: ?")
        print(f"  Total Equity:     {fli.total_equity:>20,.0f}" if fli.total_equity else "  Total Equity: ?")
        print(f"  Cash:             {fli.cash:>20,.0f}" if fli.cash else "  Cash: ?")
        if fli.operating_margin_pct is not None:
            print(f"  ★ Op Margin:      {fli.operating_margin_pct:>20.2f}%")
