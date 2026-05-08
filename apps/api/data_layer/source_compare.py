"""
KAP-only Data Layer 30 Ticker Cross-Check (Faz 11 v4.0 — Session 3C).

Multi-source orchestration validation:
  - KAP company resolution    (kap_official_v2)
  - KAP Excel financials      (kap_excel_fetcher + parser)
  - KAP free float            (kap_float_fetcher, kpy41_acc5)
  - KAP subsidiaries          (kap_subsidiaries_fetcher, kpy41_acc7)

30 ticker:
  4 anchor:   TUPRS GARAN AKBNK ARCLK
  3 bug:      KUYAS INFO VESBE
  13 random:  THYAO EREGL KRDMD SISE BIMAS MGROS ASELS KOZAL
              TCELL FROTO TOASO ENJSA PETKM
  10 IPO:     AGROT EUPWR IZINV NTGAZ BAYRK ERCB MIPAZ DENGE KMPUR ARSAN

Sanity checks:
  A) Financial: Revenue > 0, Equity > 0, BS identity ±%1, EBIT ≥ Op
  B) Ratio:     Op margin -30%..50% (KUYAS exception)
  C) Float:     0 < float_pct ≤ 1, sermaye match Bilanço paid-in ±%5
  D) Holding:   sub count ≥ 1 if holding/SOTP
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kap_official_v2 import fetch_disclosures, SUBJECT_FINANSAL_RAPOR  # noqa: E402
from kap_excel_fetcher import fetch_excel_export                       # noqa: E402
from kap_excel_parser import parse_excel_html, FinancialLineItems      # noqa: E402
from kap_float_fetcher import fetch_float_snapshot, lookup_ticker      # noqa: E402
from kap_subsidiaries_fetcher import (
    fetch_subsidiaries_snapshot,
    lookup_parent,
)  # noqa: E402


TICKERS: List[Tuple[str, str, str]] = [
    # (ticker, expected_dialect, category)
    # Anchors
    ("TUPRS", "industrial", "anchor"),
    ("GARAN", "banking",    "anchor"),
    ("AKBNK", "banking",    "anchor"),
    ("ARCLK", "industrial", "anchor"),
    # Bug tests
    ("KUYAS", "industrial", "bug"),
    ("INFO",  "industrial", "bug"),
    ("VESBE", "industrial", "bug"),
    # Random 559
    ("THYAO", "industrial", "random"),
    ("EREGL", "industrial", "random"),
    ("KRDMD", "industrial", "random"),
    ("SISE",  "industrial", "random"),
    ("BIMAS", "industrial", "random"),
    ("MGROS", "industrial", "random"),
    ("ASELS", "industrial", "random"),
    ("KOZAL", "industrial", "random"),
    ("TCELL", "industrial", "random"),
    ("FROTO", "industrial", "random"),
    ("TOASO", "industrial", "random"),
    ("ENJSA", "industrial", "random"),
    ("PETKM", "industrial", "random"),
    # New IPO (605 coverage)
    ("AGROT", "industrial", "ipo"),
    ("EUPWR", "industrial", "ipo"),
    ("IZINV", "industrial", "ipo"),
    ("NTGAZ", "industrial", "ipo"),
    ("BAYRK", "industrial", "ipo"),
    ("ERCB",  "industrial", "ipo"),
    ("MIPAZ", "industrial", "ipo"),
    ("DENGE", "industrial", "ipo"),
    ("KMPUR", "industrial", "ipo"),
    ("ARSAN", "industrial", "ipo"),
]


@dataclass
class TickerCheck:
    ticker: str
    category: str
    expected_dialect: str
    # Disclosure
    disclosure_index: Optional[int] = None
    disclosure_date: Optional[str] = None
    disclosure_error: Optional[str] = None
    # Excel parse
    fli: Optional[FinancialLineItems] = None
    # Float
    sermaye_tl: Optional[float] = None
    float_pct: Optional[float] = None
    shares_outstanding: Optional[float] = None
    # Subsidiaries
    subs_count: int = 0
    listed_subs: int = 0
    # Sanity
    sanity_passes: List[str] = field(default_factory=list)
    sanity_flags: List[str] = field(default_factory=list)
    sanity_fails: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.sanity_fails:
            return "FAIL"
        if self.sanity_flags:
            return "FLAG"
        return "PASS"


def _sanity_financial(t: TickerCheck) -> None:
    """A) Finansal sanity."""
    fli = t.fli
    if not fli:
        t.sanity_fails.append("financial: parse missing")
        return

    if fli.dialect == "banking":
        # Banking exempt from many checks (BS fields not parsed)
        if fli.net_interest_income_cari is not None and fli.net_interest_income_cari > 0:
            t.sanity_passes.append("banking: net_interest_income > 0")
        elif fli.net_interest_income_cari is not None:
            t.sanity_flags.append(f"banking: NII negatif ({fli.net_interest_income_cari:,.0f})")
        if fli.cash and fli.cash > 0:
            t.sanity_passes.append("cash > 0")
        return

    if fli.dialect == "insurance" or fli.dialect == "unknown":
        # Insurance parking — sadece BS varlığı kontrol
        if fli.total_assets and fli.total_assets > 0:
            t.sanity_passes.append("BS partial: total_assets > 0")
        else:
            t.sanity_flags.append("insurance/unknown: BS missing (parking)")
        return

    # Industrial / holding
    if fli.revenue_cari and fli.revenue_cari > 0:
        t.sanity_passes.append("revenue > 0")
    else:
        t.sanity_fails.append(f"revenue ≤ 0 ({fli.revenue_cari})")

    if fli.total_assets and fli.total_assets > 0:
        t.sanity_passes.append("total_assets > 0")
    else:
        t.sanity_fails.append("total_assets missing")

    if fli.total_equity is None:
        t.sanity_fails.append("total_equity missing")
    elif fli.total_equity < 0:
        t.sanity_flags.append(f"negative equity ({fli.total_equity:,.0f}) — distress")
    else:
        t.sanity_passes.append("equity > 0")

    # BS identity: A = L + E ±%1
    if (fli.total_assets and fli.total_liabilities is not None
            and fli.total_equity is not None and fli.total_assets > 0):
        sum_le = fli.total_liabilities + fli.total_equity
        diff_pct = abs(sum_le - fli.total_assets) / fli.total_assets * 100
        if diff_pct <= 1.0:
            t.sanity_passes.append(f"BS identity ✓ (Δ={diff_pct:.2f}%)")
        else:
            t.sanity_flags.append(f"BS identity off (Δ={diff_pct:.2f}%)")

    # EBIT ≥ Op Income (typically)
    if (fli.ebit_cari is not None and fli.operating_income_cari is not None
            and fli.ebit_cari < fli.operating_income_cari - 1):
        t.sanity_flags.append(
            f"EBIT < Op Income ({fli.ebit_cari:,.0f} < {fli.operating_income_cari:,.0f})"
        )

    # Cash ≤ Total Assets
    if (fli.cash is not None and fli.total_assets
            and fli.cash > fli.total_assets):
        t.sanity_fails.append(f"cash > total_assets ({fli.cash} > {fli.total_assets})")


def _sanity_ratios(t: TickerCheck) -> None:
    """B) Ratio sanity."""
    fli = t.fli
    if not fli or fli.dialect in ("banking", "insurance", "unknown"):
        return

    # Op margin
    if fli.operating_margin_pct is not None:
        m = fli.operating_margin_pct
        if -30 <= m <= 50:
            t.sanity_passes.append(f"op_margin in band ({m:.1f}%)")
        elif t.ticker == "KUYAS":
            t.sanity_flags.append(f"KUYAS atypical op_margin {m:.1f}% (KAP raw data)")
        else:
            t.sanity_flags.append(f"op_margin out of band ({m:.1f}%)")

    # Debt / Equity
    if (fli.total_debt is not None and fli.total_equity
            and fli.total_equity > 0):
        de = fli.total_debt / fli.total_equity
        if de <= 5:
            t.sanity_passes.append(f"D/E={de:.2f}")
        else:
            t.sanity_flags.append(f"D/E={de:.2f} > 5 (highly levered)")

    # ROE
    if (fli.net_income_cari is not None and fli.total_equity
            and fli.total_equity > 0):
        roe = fli.net_income_cari / fli.total_equity * 100
        if -100 < roe < 100:
            t.sanity_passes.append(f"ROE={roe:.1f}%")
        else:
            t.sanity_flags.append(f"ROE={roe:.1f}% out of band")


def _sanity_float(t: TickerCheck) -> None:
    """C) Float data sanity + Bilanço paid-in cross-check."""
    if t.shares_outstanding is None:
        t.sanity_fails.append("float data missing (kpy41_acc5)")
        return
    if not (0 < (t.float_pct or 0) <= 1.5):
        t.sanity_flags.append(f"float_pct out of band ({t.float_pct})")
    if t.shares_outstanding > 0:
        t.sanity_passes.append(f"shares={t.shares_outstanding:,.0f}")

    # Cross-check: Bilanço paid-in vs float-derived sermaye
    if (t.fli and t.fli.paid_in_capital is not None
            and t.sermaye_tl is not None and t.sermaye_tl > 0):
        # Bilanço paid_in birim (binlik/milyon) + float TL bazında olabilir
        # Yalnız magnitude order kontrolü
        ratio = t.sermaye_tl / max(t.fli.paid_in_capital, 1)
        # Order of magnitude: 1, 1000, 1000000 (TL / binlik / milyon TL)
        if any(0.95 <= ratio / k <= 1.05 for k in (1, 1000, 1_000_000)):
            t.sanity_passes.append(f"sermaye/Bilanço magnitude OK (×{ratio:.0f})")
        else:
            t.sanity_flags.append(
                f"sermaye/Bilanço mismatch (×{ratio:.2f})"
            )


def _sanity_holding(t: TickerCheck) -> None:
    """D) Holding-specific sub count."""
    if t.fli and t.fli.dialect == "holding":
        if t.subs_count >= 1:
            t.sanity_passes.append(f"holding subs={t.subs_count} (listed={t.listed_subs})")
        else:
            t.sanity_flags.append("holding sub list empty")


def check_ticker(
    ticker: str,
    category: str,
    expected_dialect: str,
    float_snapshot,
    subs_snapshot,
) -> TickerCheck:
    t = TickerCheck(
        ticker=ticker,
        category=category,
        expected_dialect=expected_dialect,
    )

    # Pre-validation: ticker kpy41_acc5 universe'inde mi?
    # (Yanlış/delisted ticker'lar disclosure aşamasında 'not found' verir;
    #  data quality issue olarak FLAG'lensin, FAIL değil.)
    fr_pre = lookup_ticker(float_snapshot, ticker)
    if fr_pre is None:
        t.sanity_flags.append(
            f"data_quality: ticker '{ticker}' not in KAP kpy41_acc5 "
            f"(delisted/invalid/non-BIST)"
        )
        return t

    # 1) Disclosure
    s = fetch_disclosures(ticker, days_back=400)
    if s.error:
        t.disclosure_error = s.error
        t.sanity_fails.append(f"disclosure: {s.error[:80]}")
        return t
    if not s.disclosures:
        t.disclosure_error = "no FR disclosures"
        t.sanity_flags.append("disclosure: no FR (insufficient_history)")
        return t
    newest = s.disclosures[0]
    t.disclosure_index = newest.disclosure_index
    t.disclosure_date = newest.publish_date

    # 2) Excel + parse (retry once for transient network errors)
    dl = fetch_excel_export(t.disclosure_index)
    if not dl.success:
        dl = fetch_excel_export(t.disclosure_index, force_refresh=True)
    if not dl.success:
        t.sanity_fails.append(f"excel download: {dl.error[:80]}")
        return t
    t.fli = parse_excel_html(dl.content_bytes, disclosure_index=t.disclosure_index)
    if t.fli.error:
        t.sanity_fails.append(f"parse: {t.fli.error[:80]}")
        return t

    # 3) Float lookup
    fr = lookup_ticker(float_snapshot, ticker)
    if fr is None:
        t.sanity_flags.append("float: ticker not in kpy41_acc5")
    else:
        t.sermaye_tl = fr.odenmis_sermaye_tl
        t.float_pct = fr.float_pct
        t.shares_outstanding = fr.shares_outstanding

    # 4) Subsidiaries
    subs = lookup_parent(subs_snapshot, ticker)
    t.subs_count = len(subs)
    t.listed_subs = sum(1 for s_ in subs if s_.subsidiary_ticker)

    # Sanity
    _sanity_financial(t)
    _sanity_ratios(t)
    _sanity_float(t)
    _sanity_holding(t)

    return t


def render_markdown(checks: List[TickerCheck]) -> str:
    lines: List[str] = []
    lines.append("# Session 3C — KAP-only 30 Ticker Cross-Check Report\n")
    lines.append("Faz 11 v4.0 — multi-source orchestration validation\n")

    n = len(checks)
    n_pass = sum(1 for c in checks if c.status == "PASS")
    n_flag = sum(1 for c in checks if c.status == "FLAG")
    n_fail = sum(1 for c in checks if c.status == "FAIL")

    lines.append("## Summary\n")
    lines.append(f"- Total ticker tested: **{n}**")
    lines.append(f"- ✓ PASS: **{n_pass}**")
    lines.append(f"- ⚠ FLAG: **{n_flag}** (atypical, not error)")
    lines.append(f"- ✗ FAIL: **{n_fail}**\n")

    lines.append("## Ticker Status Table\n")
    lines.append("| Ticker | Cat | Dialect | Disc.idx | Revenue | Op M% | Equity | Shares | Float% | Subs | Status |")
    lines.append("|--------|-----|---------|----------|---------|-------|--------|--------|--------|------|--------|")
    for c in checks:
        fli = c.fli
        rev = f"{fli.revenue_cari:,.0f}" if fli and fli.revenue_cari else "—"
        opm = f"{fli.operating_margin_pct:.1f}" if fli and fli.operating_margin_pct is not None else "—"
        eq = f"{fli.total_equity:,.0f}" if fli and fli.total_equity else "—"
        sh = f"{c.shares_outstanding:,.0f}" if c.shares_outstanding else "—"
        fp = f"{c.float_pct*100:.1f}" if c.float_pct is not None else "—"
        dialect = (fli.dialect if fli else "—") or "—"
        emoji = {"PASS": "✓", "FLAG": "⚠", "FAIL": "✗"}[c.status]
        lines.append(
            f"| {c.ticker} | {c.category} | {dialect} | "
            f"{c.disclosure_index or '—'} | {rev} | {opm} | {eq} | {sh} | "
            f"{fp} | {c.subs_count} | {emoji} {c.status} |"
        )

    lines.append("\n## Per-Ticker Detail\n")
    for c in checks:
        emoji = {"PASS": "✓", "FLAG": "⚠", "FAIL": "✗"}[c.status]
        lines.append(f"### {emoji} {c.ticker}  ({c.category}, expected={c.expected_dialect})\n")
        if c.disclosure_index:
            lines.append(f"- Disclosure: `{c.disclosure_index}` ({c.disclosure_date or 'n/a'})")
        if c.fli:
            lines.append(f"- Dialect detected: `{c.fli.dialect}`")
            lines.append(f"- Period: cari={c.fli.cari_donem} önceki={c.fli.onceki_donem}")
            lines.append(f"- Sunum birimi: {c.fli.sunum_birimi}  Konsolide: {c.fli.konsolide}")
            lines.append(f"- Tables: {c.fli.raw_table_count}  Parsed: {c.fli.parsed_field_count}/12")
        if c.shares_outstanding:
            lines.append(
                f"- Float: shares={c.shares_outstanding:,.0f}  "
                f"sermaye={c.sermaye_tl:,.0f} TL  pct={(c.float_pct or 0)*100:.2f}%"
            )
        if c.subs_count:
            lines.append(f"- Subsidiaries: total={c.subs_count} listed={c.listed_subs}")

        if c.sanity_passes:
            lines.append("\n**Sanity passes**")
            for p in c.sanity_passes:
                lines.append(f"- ✓ {p}")
        if c.sanity_flags:
            lines.append("\n**Sanity flags**")
            for fl in c.sanity_flags:
                lines.append(f"- ⚠ {fl}")
        if c.sanity_fails:
            lines.append("\n**Sanity FAIL**")
            for fa in c.sanity_fails:
                lines.append(f"- ✗ {fa}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 78)
    print("Session 3C — KAP-only 30 Ticker Cross-Check")
    print("=" * 78)

    print("\n→ Loading kpy41_acc5 (float)...")
    float_snap = fetch_float_snapshot(cache=True)
    if float_snap.error:
        print(f"  ✗ Float fetch FAIL: {float_snap.error}")
        return 1
    print(f"  ✓ {float_snap.record_count} records")

    print("\n→ Loading kpy41_acc7 (subsidiaries)...")
    subs_snap = fetch_subsidiaries_snapshot(cache=True, float_snapshot=float_snap)
    if subs_snap.error:
        print(f"  ✗ Subs fetch FAIL: {subs_snap.error}")
        return 1
    print(f"  ✓ {subs_snap.record_count} records  matched_parents={subs_snap.matched_parents}")

    print("\n→ Per-ticker checks (30 ticker)...")
    checks: List[TickerCheck] = []
    for i, (ticker, exp_dialect, cat) in enumerate(TICKERS, 1):
        print(f"  [{i:2d}/{len(TICKERS)}] {ticker:6} ({cat}) ...", end=" ", flush=True)
        try:
            c = check_ticker(ticker, cat, exp_dialect, float_snap, subs_snap)
        except Exception as e:
            c = TickerCheck(ticker=ticker, category=cat,
                            expected_dialect=exp_dialect)
            c.sanity_fails.append(f"orchestration error: {type(e).__name__}: {e}")
        checks.append(c)
        print(f"{c.status}")

    # TUPRS anchor regression check
    tuprs = next((c for c in checks if c.ticker == "TUPRS"), None)
    if tuprs and tuprs.fli:
        anchor_ok = (
            tuprs.fli.parsed_field_count == 12
            and tuprs.fli.dialect == "industrial"
            and tuprs.fli.revenue_cari is not None
        )
        print(f"\n  ★ TUPRS anchor regression: "
              f"{'INTACT ✓' if anchor_ok else 'BREAK ✗'}")

    # Output report
    out_path = Path(__file__).resolve().parents[1] / "outputs" / "source_comparison_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(checks), encoding="utf-8")
    print(f"\n  ✓ Report saved: {out_path.relative_to(Path.cwd())}"
          if out_path.is_relative_to(Path.cwd())
          else f"\n  ✓ Report saved: {out_path}")

    # Summary
    n_pass = sum(1 for c in checks if c.status == "PASS")
    n_flag = sum(1 for c in checks if c.status == "FLAG")
    n_fail = sum(1 for c in checks if c.status == "FAIL")
    print(f"\n{'─'*78}")
    print(f"  PASS: {n_pass:2d}/30   FLAG: {n_flag:2d}/30   FAIL: {n_fail:2d}/30")
    print('─'*78)

    return 0 if n_fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
