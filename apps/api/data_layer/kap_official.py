"""
KAP Official API client (Faz 11 prototype, Lesson #23 evidence).

Mevcut kap_scraper.py sadece HTML company-info-page okur.
Bu modül `kap-client` PyPI kütüphanesi ile resmi disclosure listing
+ attachment download API'sini kullanır.

NOT: Production orchestrator henüz buraya bağlanmadı (Faz 11.x parking).
Bu sadece KUYAS gibi anomalik ticker'larda KAP vs isyatirim
karşılaştırması için PROBE modülü.

Usage:
    from data_layer.kap_official import probe_latest_financial_report
    result = probe_latest_financial_report("KUYAS", year=2025)
    print(result["operating_margin"])  # KAP-sourced
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class FinancialReportProbe:
    """KAP'tan çekilen latest financial report özeti."""

    ticker: str
    company_oid: Optional[str] = None
    company_full_name: Optional[str] = None
    disclosures_found: int = 0
    latest_disclosure_index: Optional[int] = None
    latest_publish_date: Optional[str] = None
    attachment_count: int = 0
    attachment_filenames: List[str] = field(default_factory=list)
    error: Optional[str] = None


def probe_latest_financial_report(
    ticker: str,
    year: int,
    days_back: int = 365,
) -> FinancialReportProbe:
    """KAP resmi API'den ticker için latest FINANSAL_RAPOR disclosure'ı çek.

    Args:
        ticker: BIST ticker (örn 'KUYAS', 'TUPRS')
        year: Aranacak yıl (örn 2025) — mali yıl rapor
        days_back: Bugünden geriye N gün (default 365 = 1 yıl)

    Returns:
        FinancialReportProbe — disclosures sayısı, attachment listesi,
        latest publish date. Asıl XBRL parse Faz 11.x.
    """
    probe = FinancialReportProbe(ticker=ticker.upper())

    try:
        # Lazy import — kap-client opsiyonel dependency
        from kap_client import Kap, FundSubject  # type: ignore
    except ImportError as e:
        probe.error = f"kap-client not installed: {e}"
        return probe

    end = date.today()
    start = end - timedelta(days=days_back)

    try:
        with Kap() as kap:
            try:
                company = kap.find_company(ticker)
                probe.company_oid = company.oid
                probe.company_full_name = company.full_name or company.name
            except Exception as e:
                probe.error = f"find_company('{ticker}') failed: {type(e).__name__}: {e}"
                return probe

            try:
                disclosures = kap.fetch_disclosures(
                    ticker,
                    start.isoformat(),
                    end.isoformat(),
                    subject_oids=[FundSubject.FINANSAL_RAPOR.value],
                )
            except Exception as e:
                probe.error = f"fetch_disclosures failed: {type(e).__name__}: {e}"
                return probe

            probe.disclosures_found = len(disclosures)
            if not disclosures:
                probe.error = "No FINANSAL_RAPOR disclosures in date range"
                return probe

            # Latest (kap-client returns newest-first)
            latest = disclosures[0]
            probe.latest_disclosure_index = (
                getattr(latest, "disclosure_index", None)
                or getattr(latest, "index", None)
                or getattr(latest, "id", None)
            )
            probe.latest_publish_date = str(
                getattr(latest, "publish_date", None)
                or getattr(latest, "kap_publish_date", None)
                or "?"
            )

            if probe.latest_disclosure_index is not None:
                try:
                    attachments = kap.fetch_attachments(
                        probe.latest_disclosure_index
                    )
                    probe.attachment_count = len(attachments)
                    probe.attachment_filenames = [
                        getattr(a, "filename", None)
                        or getattr(a, "name", None)
                        or "?"
                        for a in attachments[:5]
                    ]
                except Exception as e:
                    probe.error = (
                        f"fetch_attachments failed: {type(e).__name__}: {e}"
                    )

    except Exception as e:
        probe.error = f"Kap session failed: {type(e).__name__}: {e}"

    return probe


def compare_with_isyatirim(ticker: str, year: int = 2025) -> Dict[str, Any]:
    """KAP vs isyatirim karşılaştırma (Faz 11 evidence)."""

    out: Dict[str, Any] = {
        "ticker": ticker.upper(),
        "year": year,
        "kap": None,
        "isyatirim": None,
    }

    # KAP probe
    out["kap"] = probe_latest_financial_report(ticker, year)

    # isyatirim mevcut data (latest batch JSON'dan)
    try:
        import json
        from pathlib import Path

        outputs = Path(__file__).resolve().parents[2] / "outputs"
        files = sorted(
            outputs.glob("bist_batch_LIVE_*.json"),
            reverse=True,
        )
        if files:
            data = json.loads(files[0].read_text(encoding="utf-8"))
            for r in data.get("reports", []):
                if r.get("ticker", "").upper() == ticker.upper():
                    lc = r.get("lifecycle") or {}
                    out["isyatirim"] = {
                        "stage": lc.get("stage"),
                        "avg_op_margin_pct": (
                            (lc.get("avg_operating_margin") or 0) * 100
                        ),
                        "avg_reinvestment_pct": (
                            (lc.get("avg_reinvestment_rate") or 0) * 100
                        ),
                        "revenue_cagr_usd_pct": (
                            (lc.get("revenue_cagr_usd") or 0) * 100
                        ),
                        "earnings_consistency_pct": (
                            (lc.get("earnings_consistency") or 0) * 100
                        ),
                        "source_file": files[0].name,
                    }
                    break
    except Exception as e:
        out["isyatirim_error"] = f"{type(e).__name__}: {e}"

    return out


if __name__ == "__main__":
    import json

    for t in ["KUYAS", "INFO", "VESBE", "TUPRS"]:
        print(f"\n{'='*70}\n{t}\n{'='*70}")
        result = compare_with_isyatirim(t, year=2025)
        kap = result["kap"]
        if kap:
            print(f"  KAP probe:")
            print(f"    Company OID:    {kap.company_oid}")
            print(f"    Company name:   {kap.company_full_name}")
            print(f"    Disclosures:    {kap.disclosures_found}")
            print(f"    Latest date:    {kap.latest_publish_date}")
            print(f"    Attachments:    {kap.attachment_count}")
            for fn in kap.attachment_filenames:
                print(f"      - {fn}")
            if kap.error:
                print(f"    ERROR:          {kap.error}")

        isy = result["isyatirim"]
        if isy:
            print(f"  isyatirim batch (current production):")
            print(f"    Stage:          {isy['stage']}")
            print(f"    Op margin:      {isy['avg_op_margin_pct']:.1f}%")
            print(f"    Reinvestment:   {isy['avg_reinvestment_pct']:.1f}%")
            print(f"    Revenue CAGR:   {isy['revenue_cagr_usd_pct']:.1f}%")
            print(f"    Source:         {isy['source_file']}")
        if "isyatirim_error" in result:
            print(f"  isyatirim ERROR: {result['isyatirim_error']}")
