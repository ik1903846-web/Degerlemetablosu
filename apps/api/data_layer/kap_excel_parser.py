"""
KAP Excel Financial Report Parser (Faz 11 v4.0 — Session 3A REFINEMENT).

KAP Excel-HTML export → structured financial line items dict.

Excel-HTML format:
  - 735 sub-tables (cell merge artifact)
  - Main Bilanço table (Tablo 1): ~595 rows × 5 cols
  - Income Statement (Tablo 300): ~142 rows × 8 cols
  - Cash Flow (Tablo 457): ~419 rows × 5 cols
  - Period header: "Cari Dönem 30.09.YYYY  Önceki Dönem 31.12.YYYY"
  - Sunum birimi: 1.000 TL (binlik) veya 1 TL
  - Konsolide / Solo

Session 3A FIX (Lesson #26 candidate):
  Türkçe ı/i collation bug. Python str.lower() Latin-only:
    'TOPLAM VARLIKLAR'.lower() → 'toplam varliklar'  (i, U+0069)
    'Toplam Varlıklar'.lower() → 'toplam varlıklar'  (ı, U+0131)
  ASCII collation match FAIL. _normalize_tr() ı→i fold çözer.

Damodaran DCF Mapping (Session 3A — full set):
  Hasılat                              → revenue_cari
  Esas Faaliyet Karı (Zararı)          → operating_income_cari
  Finansman Öncesi Faaliyet Karı       → ebit_cari
  Sürdürülen Faaliyet Vergi Gideri    → tax_expense_cari
  Dönem Karı (Zararı)                  → net_income_cari
  Maddi+Maddi Olmayan Alım             → capex_cari (negatif sign clean)
  Amortisman ve İtfa                   → depreciation_cari
  TOPLAM VARLIKLAR                     → total_assets
  TOPLAM YÜKÜMLÜLÜKLER                 → total_liabilities
  TOPLAM ÖZKAYNAKLAR                   → total_equity
  Nakit ve Nakit Benzerleri            → cash
  Kısa Vadeli Borçlanmalar             → short_term_debt
  Uzun Vadeli Borçlanmalar             → long_term_debt
  TOPLAM DÖNEN VARLIKLAR               → current_assets
  TOPLAM KISA VADELİ YÜKÜMLÜLÜKLER     → current_liabilities
  Ödenmiş Sermaye                      → paid_in_capital (shares proxy)
  Working Capital                      = current_assets - current_liabilities
  Total Debt                           = short_term_debt + long_term_debt
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
    dialect: Optional[str] = None          # industrial / banking / holding / insurance / unknown

    # Income statement (Cari + Önceki)
    revenue_cari: Optional[float] = None
    revenue_onceki: Optional[float] = None
    operating_income_cari: Optional[float] = None
    operating_income_onceki: Optional[float] = None
    ebit_cari: Optional[float] = None  # Finansman öncesi faaliyet karı
    net_income_cari: Optional[float] = None
    net_income_onceki: Optional[float] = None
    tax_expense_cari: Optional[float] = None

    # Banking-specific dialect fields (yalnız banking için doludur)
    interest_income_cari: Optional[float] = None    # FAİZ GELİRLERİ
    interest_expense_cari: Optional[float] = None   # FAİZ GİDERLERİ (negatif)
    net_interest_income_cari: Optional[float] = None  # interest_income + interest_expense

    # Holding-specific (Hasılat'a ek finans hizmetleri hasılatı)
    finance_sector_revenue_cari: Optional[float] = None

    # Cash Flow
    capex_cari: Optional[float] = None             # negatif → absolute saklanır
    depreciation_cari: Optional[float] = None

    # Balance sheet
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    total_equity: Optional[float] = None
    cash: Optional[float] = None
    short_term_debt: Optional[float] = None
    long_term_debt: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    paid_in_capital: Optional[float] = None        # Ödenmiş Sermaye (shares proxy)
    # Phase 3a: holding sub valuation icin (konsolide bilanco DISI)
    equity_method_investments: Optional[float] = None
    investment_properties: Optional[float] = None

    # Computed
    operating_margin_pct: Optional[float] = None   # op_income / revenue × 100
    total_debt: Optional[float] = None             # short + long
    working_capital: Optional[float] = None        # current_assets - current_liabilities

    raw_table_count: int = 0
    parsed_field_count: int = 0
    error: Optional[str] = None
    notes: List[str] = field(default_factory=list)


def _normalize_tr(s: str) -> str:
    """Türkçe-aware lowercase + ı↔i fold.

    Python str.lower() Latin-only — ı (U+0131, dotless) ile
    i (U+0069, dotted) AYRI karakterler. KAP Excel'de büyük 'I'
    standart Latin → lower → 'i' (dotted), Türkçe pattern içinde
    'ı' yer alır → match FAIL. Bu helper'ı her iki tarafta kullan.

    NOT: İ (U+0130).lower() = 'i̇' (i + combining dot above).
    Combining dot da silinir ki saf 'i' kalsın.
    """
    if not s:
        return ""
    s = s.lower()
    s = s.replace("ı", "i")          # dotless ı → dotted i
    s = s.replace("̇", "")      # combining dot above (post İ.lower())
    return s


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
    period_col: str = "cari",        # "cari" → 1st numeric col, "onceki" → 2nd
    table_indices: Optional[List[int]] = None,  # opsiyonel: sadece bu tablolarda ara
    require_exact: bool = False,     # True → tam eşleşme (ekstra parantezli ek kabul edilir)
) -> Optional[float]:
    """Tüm tablolarda label keyword arar (TR-normalize), ilk numeric value döner.

    KAP Excel format:
      col 0 = section header (label tekrar — pandas merge artifact)
      col 1 = label (data row)
      col 2 = note number (small int)
      col 3+ = period values (cari, [3-aylık], önceki, [3-aylık])

    Note column: küçük int (1-99). Filter: abs(v) >= 1000 → financial value.
    """
    norm_keywords = [_normalize_tr(k) for k in label_keywords]

    iter_tables = (
        [(i, tables[i]) for i in table_indices if i < len(tables)]
        if table_indices is not None
        else list(enumerate(tables))
    )

    for ti, df in iter_tables:
        if df.shape[0] < 1 or df.shape[1] < 3:
            continue

        # Try label_col 1 first (KAP standard data row), then 0, 2
        for label_col_idx in (1, 0, 2):
            if label_col_idx >= df.shape[1]:
                continue
            label_col_raw = df.iloc[:, label_col_idx].fillna("").astype(str)
            label_col_norm = label_col_raw.map(_normalize_tr)

            for kw in norm_keywords:
                if require_exact:
                    # Exact (parantezli ek tolere edilir: "ESAS FAALİYET KARI (ZARARI)")
                    pat = rf"^{re.escape(kw)}(\s*\([^)]*\))?\s*$"
                    mask = label_col_norm.str.match(pat, na=False)
                else:
                    mask = label_col_norm.str.contains(
                        re.escape(kw), regex=True, na=False,
                    )
                if not mask.any():
                    continue

                for row_idx in mask[mask].index:
                    row = df.iloc[row_idx]
                    # KAP layout: col 0/1 = label (skip), col 2 = note column,
                    # col 3+ = period values (cari, [3-aylık], önceki, [3-aylık])
                    # Note: integer 1-99999 (TFRS standart referansı, ör. 41011).
                    # Financial values: col 3+'ta her TR-parse-able sayı kabul
                    # (KCHOL gibi 1.000.000 TL sunum biriminde değerler 5-haneli).
                    numeric_values: List = []
                    for ci in range(2, min(df.shape[1], 8)):
                        v = _parse_tr_number(row.iloc[ci])
                        if v is None:
                            continue
                        # Note filter ONLY for col 2
                        if ci == 2:
                            is_note = (v == int(v) and 1 <= abs(v) <= 99999)
                            if is_note:
                                continue
                            if abs(v) < 1000:  # Boş/eser değer skip
                                continue
                        # col 3+ → her sayı financial (sıfır dahil)
                        numeric_values.append((ci, v))
                    if not numeric_values:
                        continue
                    if period_col == "cari":
                        return numeric_values[0][1]
                    elif period_col == "onceki" and len(numeric_values) > 1:
                        # Tablo 300'de 4 col olabilir: cari 9M, cari 3M, önceki 9M, önceki 3M
                        # 'onceki' = 9M önceki → numeric_values[2] (cari 3M skip)
                        # Yoksa 2 col → numeric_values[1] = önceki
                        if len(numeric_values) >= 3:
                            return numeric_values[2][1]
                        return numeric_values[1][1]

    return None


def _detect_dialect(all_tables: List[pd.DataFrame]) -> str:
    """KAP Excel-HTML → dialect classification.

    industrial: Hasılat + ESAS FAALİYET KARI (TUPRS, ARCLK gibi)
    banking:    FAİZ GELİRLERİ + FAİZ GİDERLERİ ana satırı (GARAN, AKBNK)
    holding:    Hasılat + Finans Sektörü Hasılatı ikisi anlamlı (SAHOL, KCHOL)
    insurance:  Hasar Karşılıkları / Net Tahakkuk Eden Primler
    unknown:    Hiçbiri eşleşmedi (parser skip-safe)

    Heuristic: tablolarda label normalize edilmiş anahtar kelime varlığı +
    aynı satırda numeric value var mı kontrolü.
    """
    has_revenue = False
    has_finance_revenue = False
    has_op_income = False
    has_interest_income = False
    has_interest_expense = False
    has_insurance_terms = False

    for df in all_tables:
        if df.shape[0] < 5 or df.shape[1] < 4 or df.shape[1] > 10:
            continue
        for lcol in (0, 1):
            if lcol >= df.shape[1]:
                continue
            labels = df.iloc[:, lcol].fillna("").astype(str)
            for ri, raw_lbl in enumerate(labels):
                lbl = _normalize_tr(raw_lbl).strip()
                if not lbl or len(lbl) < 4:
                    continue
                # numeric value var mı row'da? (col 3+ where note artifact yok)
                row = df.iloc[ri]
                has_num = False
                for ci in range(3, min(df.shape[1], 8)):
                    v = _parse_tr_number(row.iloc[ci])
                    if v is None:
                        continue
                    if abs(v) >= 1:  # KCHOL gibi milyon-TL'de değerler küçük olabilir
                        has_num = True
                        break

                if lbl == "hasilat" and has_num:
                    has_revenue = True
                if "finans sektoru faaliyetleri hasilati" in lbl and has_num:
                    has_finance_revenue = True
                if lbl.startswith("esas faaliyet kari") and has_num:
                    has_op_income = True
                if lbl == "faiz gelirleri" and has_num:
                    has_interest_income = True
                if lbl.startswith("faiz giderleri") and has_num:
                    has_interest_expense = True
                if ("hasar karsilik" in lbl or
                    "net tahakkuk eden prim" in lbl) and has_num:
                    has_insurance_terms = True

    # Banking primary signal
    if has_interest_income and has_interest_expense and not has_op_income:
        return "banking"
    # Insurance primary
    if has_insurance_terms and not has_revenue:
        return "insurance"
    # Holding: hem industrial revenue hem finance sector revenue anlamlı
    if has_revenue and has_finance_revenue and has_op_income:
        return "holding"
    # Industrial default (TUPRS regression)
    if has_revenue and has_op_income:
        return "industrial"
    if has_revenue:
        return "industrial"
    return "unknown"


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
                k_norm = _normalize_tr(k)
                if "para birimi" in k_norm:
                    fli.sunum_birimi = v.strip()
                elif "niteli" in k_norm:
                    fli.konsolide = "konsolide" in _normalize_tr(v)
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

    # =====================================================================
    # Dialect detection (Session 3B)
    # =====================================================================
    fli.dialect = _detect_dialect(all_tables)

    # Banking: ayrı income statement path
    if fli.dialect == "banking":
        _parse_banking_income(fli, all_tables)
    elif fli.dialect == "insurance":
        fli.notes.append("Insurance dialect — IS parse skipped (3rd dialect parking)")
        # Bilanço alanları yine denenecek (genellikle uyumlu)
    else:
        # industrial + holding aynı path
        _parse_industrial_income(fli, all_tables)
        # Finans Sektörü Hasılatı — holding template ek (her zaman dene).
        # Industrial template'da bu satır boş, _find_value_in_tables None döner,
        # revenue toplaması no-op (TUPRS regression-safe).
        fs_rev = _find_value_in_tables(
            all_tables,
            ["Finans Sektörü Faaliyetleri Hasılatı"],
            "cari", require_exact=True,
        )
        fli.finance_sector_revenue_cari = fs_rev
        if fs_rev is not None and fli.revenue_cari is not None:
            fli.revenue_cari = fli.revenue_cari + fs_rev
            if fli.dialect == "industrial":
                # Auto-promote dialect: Hasılat + Finans Sektörü Hasılatı her ikisi
                # değer varsa template HOLDING'tir.
                fli.dialect = "holding"

    # =====================================================================
    # Bilanço (tüm dialect'lerde benzer pattern)
    # =====================================================================
    _parse_balance_sheet(fli, all_tables)

    # =====================================================================
    # Cash Flow (industrial/holding; banking'de bazıları farklı isim alabilir)
    # =====================================================================
    if fli.dialect in ("industrial", "holding", "unknown"):
        _parse_cash_flow(fli, all_tables)

    # =====================================================================
    # Computed fields
    # =====================================================================
    if fli.revenue_cari and fli.operating_income_cari is not None:
        if fli.revenue_cari != 0:
            fli.operating_margin_pct = fli.operating_income_cari / fli.revenue_cari * 100
    if fli.short_term_debt is not None and fli.long_term_debt is not None:
        fli.total_debt = fli.short_term_debt + fli.long_term_debt
    if fli.current_assets is not None and fli.current_liabilities is not None:
        fli.working_capital = fli.current_assets - fli.current_liabilities

    # Field counter
    fli.parsed_field_count = sum(1 for v in [
        fli.revenue_cari, fli.operating_income_cari, fli.ebit_cari,
        fli.tax_expense_cari, fli.net_income_cari,
        fli.capex_cari, fli.depreciation_cari,
        fli.total_assets, fli.total_liabilities, fli.total_equity,
        fli.cash, fli.paid_in_capital,
    ] if v is not None)

    return fli


def _parse_banking_income(fli: FinancialLineItems, all_tables: List[pd.DataFrame]) -> None:
    """Banking dialect (TFRS 9 banka mali tablosu) — Faiz Geliri/Gideri tabanlı."""
    fli.interest_income_cari = _find_value_in_tables(
        all_tables, ["Faiz Gelirleri"], "cari", require_exact=True,
    )
    fli.interest_expense_cari = _find_value_in_tables(
        all_tables, ["Faiz Giderleri (-)", "Faiz Giderleri"],
        "cari", require_exact=True,
    )
    if fli.interest_income_cari is not None and fli.interest_expense_cari is not None:
        fli.net_interest_income_cari = (
            fli.interest_income_cari + fli.interest_expense_cari  # gider negatif
        )

    # Banking convention: revenue ≈ NET FAİZ GELİRİ (Damodaran banking model)
    fli.revenue_cari = fli.net_interest_income_cari

    # Net Income — banks have "DÖNEM NET KARI/ZARARI" pattern
    fli.net_income_cari = _find_value_in_tables(
        all_tables,
        ["Dönem Net Karı/Zararı", "Dönem Net Kar/Zararı",
         "Net Dönem Karı/Zararı", "Dönem Karı (Zararı)", "Dönem Karı"],
        "cari", require_exact=True,
    )

    # Tax — banks
    fli.tax_expense_cari = _find_value_in_tables(
        all_tables,
        ["Vergi Karşılığı (-)", "Sürdürülen Faaliyetler Vergi Karşılığı (-)",
         "Sürdürülen Faaliyetler Vergi (Gideri) Geliri",
         "Vergi Karşılığı"],
        "cari", require_exact=True,
    )

    # Banking'de "operating income" yerine net interest income proxy kullanılır
    fli.operating_income_cari = fli.net_interest_income_cari
    fli.notes.append(
        "Banking dialect: revenue=NET FAİZ GELİRİ, "
        "operating_income=NET FAİZ GELİRİ proxy (Damodaran banking model)"
    )


def _parse_industrial_income(fli: FinancialLineItems, all_tables: List[pd.DataFrame]) -> None:
    """Industrial / Holding dialect — TUPRS-style Tablo 300."""
    fli.revenue_cari = _find_value_in_tables(all_tables, ["Hasılat"], "cari")
    fli.revenue_onceki = _find_value_in_tables(all_tables, ["Hasılat"], "onceki")
    fli.operating_income_cari = _find_value_in_tables(
        all_tables,
        ["Esas Faaliyet Karı (Zararı)", "Esas Faaliyet Karı"],
        "cari", require_exact=True,
    )
    fli.operating_income_onceki = _find_value_in_tables(
        all_tables,
        ["Esas Faaliyet Karı (Zararı)", "Esas Faaliyet Karı"],
        "onceki", require_exact=True,
    )
    fli.ebit_cari = _find_value_in_tables(
        all_tables,
        ["Finansman Geliri (Gideri) Öncesi Faaliyet Karı (Zararı)",
         "Finansman Geliri (Gideri) Öncesi Faaliyet Karı",
         "Finansman Öncesi Faaliyet Karı"],
        "cari", require_exact=True,
    )
    fli.net_income_cari = _find_value_in_tables(
        all_tables, ["Dönem Karı", "Net Dönem Karı"], "cari", require_exact=True,
    )
    fli.tax_expense_cari = _find_value_in_tables(
        all_tables,
        ["Sürdürülen Faaliyetler Vergi (Gideri) Geliri",
         "Sürdürülen Faaliyetler Vergi Gideri",
         "Vergi Gideri", "Vergi Karşılığı"],
        "cari", require_exact=True,
    )


def _parse_cash_flow(fli: FinancialLineItems, all_tables: List[pd.DataFrame]) -> None:
    """Cash Flow Statement (Tablo 457 ve civarı)."""
    capex_raw = _find_value_in_tables(
        all_tables,
        ["Maddi ve Maddi Olmayan Duran Varlıkların Alımından Kaynaklanan Nakit Çıkışları",
         "Maddi Duran Varlık Alımından Kaynaklanan Nakit Çıkışları"],
        "cari", require_exact=True,
    )
    if capex_raw is not None:
        fli.capex_cari = abs(capex_raw)  # Damodaran convention: positive
    fli.depreciation_cari = _find_value_in_tables(
        all_tables,
        ["Amortisman ve İtfa Gideri İle İlgili Düzeltmeler",
         "Amortisman ve İtfa Gideri Düzeltmeleri"],
        "cari", require_exact=True,
    )


def _parse_balance_sheet(fli: FinancialLineItems, all_tables: List[pd.DataFrame]) -> None:
    """Bilanço (Tablo 1 ve civarı) — industrial/holding/banking ortak."""
    fli.total_assets = _find_value_in_tables(
        all_tables, ["Toplam Varlıklar"], "cari", require_exact=True,
    )
    fli.total_liabilities = _find_value_in_tables(
        all_tables, ["Toplam Yükümlülükler"], "cari", require_exact=True,
    )
    fli.total_equity = _find_value_in_tables(
        all_tables, ["Toplam Özkaynaklar"], "cari", require_exact=True,
    )
    fli.cash = _find_value_in_tables(
        all_tables, ["Nakit ve Nakit Benzerleri"], "cari", require_exact=True,
    )
    fli.short_term_debt = _find_value_in_tables(
        all_tables, ["Kısa Vadeli Borçlanmalar"], "cari", require_exact=True,
    )
    fli.long_term_debt = _find_value_in_tables(
        all_tables, ["Uzun Vadeli Borçlanmalar"], "cari", require_exact=True,
    )
    fli.current_assets = _find_value_in_tables(
        all_tables, ["Toplam Dönen Varlıklar"], "cari", require_exact=True,
    )
    fli.current_liabilities = _find_value_in_tables(
        all_tables, ["Toplam Kısa Vadeli Yükümlülükler"], "cari", require_exact=True,
    )
    fli.paid_in_capital = _find_value_in_tables(
        all_tables, ["Ödenmiş Sermaye"], "cari", require_exact=True,
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kap_excel_fetcher import fetch_excel_export  # noqa: E402

    print("=" * 78)
    print("KAP Excel Parser — Session 3B Multi-Dialect Validation")
    print("=" * 78)

    targets = [
        # Industrial regression
        ("TUPRS",   1510162, "industrial", "ANCHOR — 12/12 PASS olmalı"),
        ("AGROT",   1481009, "industrial", "Yeni IPO"),
        # Banking
        ("GARAN",   1508775, "banking",    "Net Faiz Gel. proxy"),
        ("AKBNK",   1467850, "banking",    "Net Faiz Gel. proxy"),
        # Holding (KUYAS bug eliminate)
        ("SAHOL",   1477828, "holding",    "Hasılat + Finans Sektörü"),
        ("KCHOL",   1470523, "holding",    "Hasılat + Finans Sektörü"),
        ("KUYAS",   1480086, "industrial", "BUG bypass test"),
        # Insurance (parser skip)
        ("ANSGR",   1599078, "insurance",  "3rd dialect parking"),
    ]

    for ticker, idx, expected_dialect, note in targets:
        print(f"\n{'─'*78}")
        print(f"{ticker}  idx={idx}  expected={expected_dialect}  ({note})")
        print('─'*78)

        dl = fetch_excel_export(idx)
        if not dl.success:
            print(f"  ✗ Download fail: {dl.error}")
            continue

        fli = parse_excel_html(dl.content_bytes, disclosure_index=idx)
        if fli.error:
            print(f"  ⚠ Parse warning: {fli.error}")

        dialect_match = "✓" if fli.dialect == expected_dialect else "⚠"
        print(f"  Dialect detected: {fli.dialect}  {dialect_match}  (expected={expected_dialect})")
        print(f"  Period: {fli.cari_donem} / {fli.onceki_donem}  "
              f"Birim: {fli.sunum_birimi}  Konsolide: {fli.konsolide}")
        print(f"  Tables: {fli.raw_table_count}  Parsed: {fli.parsed_field_count}/12")

        def fmt(v): return f"{v:>22,.0f}" if v is not None else f"{'?':>22}"
        print(f"  ── INCOME STATEMENT ─────────────────────────────────")
        print(f"    Revenue (cari):      {fmt(fli.revenue_cari)}")
        print(f"    Op Income (cari):    {fmt(fli.operating_income_cari)}")
        print(f"    EBIT (cari):         {fmt(fli.ebit_cari)}")
        print(f"    Tax Expense:         {fmt(fli.tax_expense_cari)}")
        print(f"    Net Income (cari):   {fmt(fli.net_income_cari)}")
        if fli.dialect == "banking":
            print(f"    Faiz Gelirleri:      {fmt(fli.interest_income_cari)}")
            print(f"    Faiz Giderleri:      {fmt(fli.interest_expense_cari)}")
            print(f"    Net Faiz Geliri:     {fmt(fli.net_interest_income_cari)}")
        if fli.dialect == "holding":
            print(f"    Finans Sek. Hasılatı:{fmt(fli.finance_sector_revenue_cari)}")
        if fli.operating_margin_pct is not None:
            print(f"    Op Margin: {fli.operating_margin_pct:.2f}%")
        print(f"  ── BALANCE SHEET ────────────────────────────────────")
        print(f"    Total Assets:        {fmt(fli.total_assets)}")
        print(f"    Total Equity:        {fmt(fli.total_equity)}")
        print(f"    Cash:                {fmt(fli.cash)}")
        print(f"    Total Debt:          {fmt(fli.total_debt)}")
        print(f"    Paid-in Capital:     {fmt(fli.paid_in_capital)}")
        if fli.notes:
            print(f"  Notes: {'; '.join(fli.notes)[:120]}")
