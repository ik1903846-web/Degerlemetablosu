"""
BIST Bottom-Up Sektör Beta (Faz 11 v4.0 — Session 3.6 ADIM B-F).

Damodaran-pure metodoloji + BIST data, %100 yerel:

  ADIM B) Per-ticker regression beta:
    yfinance 5-yıl günlük close × BIST 100 (XU100.IS)
    log returns, weekly aggregation (NOISE filter)
    β_levered = cov(r_stock, r_market) / var(r_market)
    R² ve N raporla

  ADIM C) Per-ticker unlever:
    Industrial/Holding: β_unlevered = β / (1 + (1-tax) × D/E)
    Banking dialect: skip unlever (regulatory leverage farklı)
    Insurance/Unknown: skip (Session 3B parking)

  ADIM D) Sektör ortalaması:
    Equal-weighted (basit + outlier resistant median)
    Quality filter:
      - history < 250 weekly point → exclude
      - negative equity → exclude
      - R² < 0.05 → flag (warning, not exclude)

  ADIM E) Re-lever:
    β_levered_per_ticker = β_unlevered_sector
                           × (1 + (1-tax) × D/E_firma)

  ADIM F) Output:
    apps/api/outputs/turkey_sector_beta.json
    apps/api/outputs/sector_beta_report.md

Kurallar:
  ✓ TÜM halka açık şirket dahil (sayı min YOK)
  ✓ Tek firma sektör → kendisi sektör (merge yok)
  ✓ KAP /tr/Sektorler resmi taksonomisi (Session 3.6 ADIM A)
  ✗ Damodaran Global override YOK (sapma sadece info-only rapor)
  ✗ AI/LLM API kullanımı YOK
  ✗ İş Yatırım kullanımı YOK (yfinance fiyat-only kapsam)
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict, field
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Tuple

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kap_sector_fetcher import load_snapshot as load_sector_snapshot  # noqa: E402
from kap_excel_fetcher import fetch_excel_export                      # noqa: E402
from kap_excel_parser import parse_excel_html                         # noqa: E402
from kap_official_v2 import fetch_disclosures                         # noqa: E402
from kap_float_fetcher import fetch_float_snapshot, lookup_ticker     # noqa: E402


YFINANCE_CACHE = Path(__file__).resolve().parents[1] / "_cache" / "yfinance"
BIST100_CACHE = YFINANCE_CACHE / "_BIST100.csv"
OUTPUT_JSON = Path(__file__).resolve().parents[1] / "outputs" / "turkey_sector_beta.json"
OUTPUT_MD = Path(__file__).resolve().parents[1] / "outputs" / "sector_beta_report.md"
FUNDAMENTALS_CACHE = Path(__file__).resolve().parents[1] / "_cache" / "fundamentals.json"
SECTOR_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "config" / "sector_overrides.json"

# Damodaran corporate tax rate Türkiye (2025 ~%25)
DEFAULT_TAX_RATE_TR = 0.25

# Quality thresholds
MIN_WEEKLY_POINTS = 250 // 5   # ~50 weekly points (1 yıl)
MIN_R_SQUARED = 0.05


@dataclass
class TickerBeta:
    ticker: str
    sector_oid: str
    sector_name: str
    sector_no: str
    dialect: Optional[str] = None
    # Regression
    beta_levered: Optional[float] = None
    r_squared: Optional[float] = None
    n_obs: int = 0
    # Fundamentals
    de_ratio: Optional[float] = None
    tax_rate: float = DEFAULT_TAX_RATE_TR
    market_cap_tl: Optional[float] = None
    # Computed
    beta_unlevered: Optional[float] = None
    sector_beta_unlevered: Optional[float] = None
    beta_relevered: Optional[float] = None
    # Status
    flags: List[str] = field(default_factory=list)
    excluded: bool = False
    exclude_reason: Optional[str] = None


@dataclass
class SectorAggregate:
    sector_oid: str
    sector_name: str
    sector_no: str
    n_total: int = 0
    n_included: int = 0
    n_excluded: int = 0
    beta_unlevered_mean: Optional[float] = None
    beta_unlevered_median: Optional[float] = None
    beta_unlevered_stdev: Optional[float] = None
    single_firm: bool = False
    high_dispersion: bool = False  # stdev > 0.30 → flag (broad-bucket symptom)


# ============================================================================
# 1) Returns + regression
# ============================================================================

def _load_close(path: Path) -> Optional[pd.Series]:
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, parse_dates=["date"])
    except Exception:
        return None
    if "close" not in df.columns or df.empty:
        return None
    return df.set_index("date")["close"].astype(float).sort_index()


def _weekly_log_returns(close: pd.Series) -> pd.Series:
    """Weekly log returns (Friday-anchored), noise filter."""
    weekly = close.resample("W-FRI").last().dropna()
    return (weekly / weekly.shift(1)).apply(lambda x: math.log(x) if x and x > 0 else None).dropna()


def _regress_beta(stock_ret: pd.Series, market_ret: pd.Series) -> Tuple[Optional[float], Optional[float], int]:
    """OLS β = cov(s,m)/var(m); R² standart."""
    common = stock_ret.index.intersection(market_ret.index)
    if len(common) < MIN_WEEKLY_POINTS:
        return None, None, len(common)
    s = stock_ret.loc[common]
    m = market_ret.loc[common]
    var_m = m.var()
    if var_m == 0:
        return None, None, len(common)
    beta = ((s - s.mean()) * (m - m.mean())).sum() / ((m - m.mean()) ** 2).sum()
    # R²
    s_pred = beta * (m - m.mean()) + s.mean()
    ss_res = ((s - s_pred) ** 2).sum()
    ss_tot = ((s - s.mean()) ** 2).sum()
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    return float(beta), float(r2), len(common)


# ============================================================================
# 2) Fundamentals fetch (KAP Bilanço — D/E)
# ============================================================================

def _atomic_write_json(path: Path, data: Dict) -> None:
    """Atomic JSON write: temp file → rename. Cache integrity safe."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _fetch_one_fundamental(ticker: str) -> Tuple[str, Dict]:
    """Tek ticker fundamentals (KAP Bilanço D/E + dialect). Thread-safe pure-fn."""
    try:
        s = fetch_disclosures(ticker, days_back=400)
        if s.error or not s.disclosures:
            return ticker, {"error": "no_FR"}
        idx = s.disclosures[0].disclosure_index
        dl = fetch_excel_export(idx)
        if not dl.success:
            return ticker, {"error": "download"}
        fli = parse_excel_html(dl.content_bytes, disclosure_index=idx)
        de = None
        if (fli.total_debt is not None and fli.total_equity is not None
                and fli.total_equity > 0):
            de = fli.total_debt / fli.total_equity
        return ticker, {
            "dialect":          fli.dialect,
            "de_ratio":         de,
            "equity":           fli.total_equity,
            "total_debt":       fli.total_debt,
            "disclosure_index": idx,
        }
    except Exception as e:
        return ticker, {"error": f"{type(e).__name__}: {str(e)[:80]}"}


def _build_fundamentals_cache(
    tickers: List[str],
    force_refresh: bool = False,
    max_workers: int = 5,           # B mode aggressive (Session 3.7 retry)
    throttle_sec: float = 0.5,      # B mode aggressive
) -> Dict[str, Dict]:
    """Per ticker: KAP'tan en yeni FR Excel → D/E + tax + dialect.

    Paralel ThreadPoolExecutor (max_workers=5, conservative throttle).
    Atomic per-ticker cache write — kill-safe.

    Cache: apps/api/_cache/fundamentals.json
    """
    cache: Dict[str, Dict] = {}
    if FUNDAMENTALS_CACHE.exists() and not force_refresh:
        try:
            cache = json.loads(FUNDAMENTALS_CACHE.read_text(encoding="utf-8"))
            print(f"  Cache loaded: {len(cache)} ticker (resume mode)")
        except Exception:
            cache = {}

    pending = [t for t in tickers if t not in cache]
    if not pending:
        print(f"  All {len(tickers)} cached, skip fetch")
        return cache

    # Cache-only mode (env var SECTOR_BETA_CACHE_ONLY=1) → no KAP fetch
    import os
    if os.environ.get("SECTOR_BETA_CACHE_ONLY"):
        print(f"  CACHE-ONLY mode: {len(pending)} pending → fallback flag (no fetch)")
        for t in pending:
            cache[t] = {"error": "cache_only_pending"}
        return cache

    print(f"  Fetching {len(pending)} ticker (paralel, max_workers={max_workers})…")
    FUNDAMENTALS_CACHE.parent.mkdir(parents=True, exist_ok=True)

    cache_lock = Lock()
    rate_limit_state = {"consecutive_429": 0, "abort": False}
    completed = [0]
    write_counter = [0]

    def _save_cache_locked():
        # Çağrıldığında cache_lock zaten alınmış olmalı
        _atomic_write_json(FUNDAMENTALS_CACHE, cache)

    def _process(ticker: str) -> None:
        if rate_limit_state["abort"]:
            return
        ticker_v, data = _fetch_one_fundamental(ticker)
        # Rate limit detection
        err_str = str(data.get("error", "")) if "error" in data else ""
        is_429 = ("429" in err_str) or ("rate" in err_str.lower())
        with cache_lock:
            cache[ticker_v] = data
            completed[0] += 1
            write_counter[0] += 1
            if is_429:
                rate_limit_state["consecutive_429"] += 1
                if rate_limit_state["consecutive_429"] >= 5:
                    rate_limit_state["abort"] = True
                    print(f"\n  ⚠ 5 ardışık 429 — paralel abort, sequential fallback gerek")
                    return
            else:
                rate_limit_state["consecutive_429"] = 0
            # Save every 10 completions (reduce I/O)
            if write_counter[0] >= 10:
                _save_cache_locked()
                write_counter[0] = 0
            n = completed[0]
            total = len(pending)
            de = data.get("de_ratio")
            de_str = f"{de:.3f}" if de is not None else "n/a"
            d = data.get("dialect") or data.get("error", "-")
            print(f"  [{len(cache):3d}/{len(tickers)}] {ticker_v:6} "
                  f"d={str(d)[:12]:12} de={de_str}")
        time.sleep(throttle_sec)

    with ThreadPoolExecutor(max_workers=max_workers) as exec_:
        futures = [exec_.submit(_process, t) for t in pending]
        for _ in as_completed(futures):
            if rate_limit_state["abort"]:
                break

    # Final save
    with cache_lock:
        _save_cache_locked()

    if rate_limit_state["abort"]:
        # Sequential fallback for remaining
        print("  → Sequential fallback for remaining tickers (1 worker, 1 sec)")
        for t in pending:
            if t in cache:
                continue
            tv, d = _fetch_one_fundamental(t)
            cache[tv] = d
            with cache_lock:
                _save_cache_locked()
            time.sleep(1.0)

    return cache


# ============================================================================
# 3) Pipeline orchestration
# ============================================================================

def _load_sector_overrides() -> Dict[str, Dict]:
    """sector_overrides.json → ticker → override mapping."""
    if not SECTOR_OVERRIDES_PATH.exists():
        return {}
    try:
        data = json.loads(SECTOR_OVERRIDES_PATH.read_text(encoding="utf-8"))
        return data.get("overrides", {})
    except Exception:
        return {}


def compute_beta_per_ticker(
    sector_snap,
    market_returns: pd.Series,
    fundamentals: Dict[str, Dict],
    market_caps: Dict[str, float],
) -> List[TickerBeta]:
    overrides = _load_sector_overrides()
    results: List[TickerBeta] = []
    for r in sector_snap.records:
        # Damodaran-granular override apply
        ov = overrides.get(r.ticker)
        sector_oid = ov["override_sector_oid"] if ov else r.sector_oid
        sector_name = ov["override_sector_name"] if ov else r.sector_name
        sector_no = "OVERRIDE" if ov else r.sector_no

        tb = TickerBeta(
            ticker=r.ticker,
            sector_oid=sector_oid,
            sector_name=sector_name,
            sector_no=sector_no,
        )
        if ov:
            tb.flags.append(f"sector_override: {r.sector_name[:30]} → {sector_name[:30]}")
        # Fundamentals
        f = fundamentals.get(r.ticker, {})
        tb.dialect = f.get("dialect")
        tb.de_ratio = f.get("de_ratio")
        tb.market_cap_tl = market_caps.get(r.ticker)

        # Equity check
        eq = f.get("equity")
        if eq is not None and eq < 0:
            tb.excluded = True
            tb.exclude_reason = "negative_equity"
            results.append(tb)
            continue

        # Price load
        px = _load_close(YFINANCE_CACHE / f"{r.ticker}.csv")
        if px is None or len(px) < 250:
            tb.excluded = True
            tb.exclude_reason = "insufficient_history"
            results.append(tb)
            continue

        sret = _weekly_log_returns(px)
        beta, r2, n = _regress_beta(sret, market_returns)
        tb.beta_levered = beta
        tb.r_squared = r2
        tb.n_obs = n
        if beta is None:
            tb.excluded = True
            tb.exclude_reason = "regression_failed"
            results.append(tb)
            continue
        if r2 is not None and r2 < MIN_R_SQUARED:
            tb.flags.append(f"low_r2={r2:.3f}")

        # Unlever (industrial/holding)
        if tb.dialect == "banking":
            tb.flags.append("banking_skip_unlever")
            tb.beta_unlevered = beta  # Damodaran "banks" pratiği
        elif tb.dialect in (None, "insurance", "unknown"):
            tb.flags.append("dialect_unknown_skip_unlever")
            tb.beta_unlevered = beta
        else:
            de = tb.de_ratio if tb.de_ratio is not None else 0.0
            tb.beta_unlevered = beta / (1 + (1 - tb.tax_rate) * de)

        results.append(tb)
    return results


def aggregate_sectors(per_ticker: List[TickerBeta]) -> Dict[str, SectorAggregate]:
    by_sector: Dict[str, List[TickerBeta]] = {}
    for tb in per_ticker:
        by_sector.setdefault(tb.sector_oid, []).append(tb)

    out: Dict[str, SectorAggregate] = {}
    for soid, lst in by_sector.items():
        agg = SectorAggregate(
            sector_oid=soid,
            sector_name=lst[0].sector_name,
            sector_no=lst[0].sector_no,
            n_total=len(lst),
        )
        included = [t for t in lst if not t.excluded and t.beta_unlevered is not None]
        agg.n_included = len(included)
        agg.n_excluded = len(lst) - len(included)
        if not included:
            out[soid] = agg
            continue
        betas = [t.beta_unlevered for t in included]
        agg.beta_unlevered_mean = float(sum(betas) / len(betas))
        agg.beta_unlevered_median = float(statistics.median(betas))
        if len(betas) >= 2:
            agg.beta_unlevered_stdev = float(statistics.stdev(betas))
        agg.single_firm = (len(included) == 1)
        if agg.beta_unlevered_stdev and agg.beta_unlevered_stdev > 0.30:
            agg.high_dispersion = True
        out[soid] = agg
    return out


def relever_per_ticker(
    per_ticker: List[TickerBeta],
    sector_aggs: Dict[str, SectorAggregate],
) -> None:
    for tb in per_ticker:
        agg = sector_aggs.get(tb.sector_oid)
        if not agg or agg.beta_unlevered_mean is None:
            continue
        tb.sector_beta_unlevered = agg.beta_unlevered_mean
        if tb.dialect == "banking":
            # Banking: re-lever YAPMA, regression beta direct
            tb.beta_relevered = tb.beta_levered
            continue
        de = tb.de_ratio if tb.de_ratio is not None else 0.0
        tb.beta_relevered = agg.beta_unlevered_mean * (1 + (1 - tb.tax_rate) * de)


# ============================================================================
# 4) Output (json + markdown)
# ============================================================================

def render_markdown(per_ticker: List[TickerBeta],
                    sector_aggs: Dict[str, SectorAggregate]) -> str:
    lines: List[str] = []
    lines.append("# Türkiye Sektör Beta — Damodaran Bottom-Up\n")
    lines.append("Faz 11 v4.0 — Session 3.6\n")
    lines.append(f"Methodology: weekly log returns, 5y, OLS regression vs BIST 100\n")
    lines.append(f"Tax rate (Türkiye 2025): %{DEFAULT_TAX_RATE_TR*100:.0f}\n")

    n_total = len(per_ticker)
    n_included = sum(1 for t in per_ticker if not t.excluded)
    n_banking = sum(1 for t in per_ticker if t.dialect == "banking")
    lines.append(f"\n## Summary\n")
    lines.append(f"- Total ticker:    **{n_total}**")
    lines.append(f"- Included:        **{n_included}**")
    lines.append(f"- Excluded:        **{n_total - n_included}**")
    lines.append(f"- Banking dialect: {n_banking} (regression beta direct, unlever skip)")
    lines.append(f"- Sectors:         **{len(sector_aggs)}**")
    n_single = sum(1 for a in sector_aggs.values() if a.single_firm)
    n_high_disp = sum(1 for a in sector_aggs.values() if a.high_dispersion)
    lines.append(f"- Single-firm:     **{n_single}**")
    lines.append(f"- High dispersion (stdev>0.30): **{n_high_disp}**\n")

    # Sector table
    lines.append("## Sector Beta Table (sorted by ticker count)\n")
    lines.append("| sectorNo | Sector | N | Mean β_unlev | Median | Stdev | Flag |")
    lines.append("|----------|--------|---|--------------|--------|-------|------|")
    sorted_aggs = sorted(sector_aggs.values(),
                         key=lambda a: a.n_included, reverse=True)
    for a in sorted_aggs:
        flag = ""
        if a.single_firm:
            flag = "single_firm"
        elif a.high_dispersion:
            flag = "high_dispersion"
        mean = f"{a.beta_unlevered_mean:.3f}" if a.beta_unlevered_mean is not None else "—"
        med = f"{a.beta_unlevered_median:.3f}" if a.beta_unlevered_median is not None else "—"
        std = f"{a.beta_unlevered_stdev:.3f}" if a.beta_unlevered_stdev is not None else "—"
        lines.append(
            f"| {a.sector_no} | {a.sector_name[:50]} | "
            f"{a.n_included}/{a.n_total} | {mean} | {med} | {std} | {flag} |"
        )

    # Anchor: TUPRS detail
    lines.append("\n## TUPRS Anchor\n")
    tuprs = next((t for t in per_ticker if t.ticker == "TUPRS"), None)
    if tuprs:
        lines.append(f"- Sektör: {tuprs.sector_name} ({tuprs.sector_no})")
        lines.append(f"- β_levered (regression): {tuprs.beta_levered}")
        lines.append(f"- R²: {tuprs.r_squared}")
        lines.append(f"- D/E: {tuprs.de_ratio}")
        lines.append(f"- β_unlevered (firma): {tuprs.beta_unlevered}")
        lines.append(f"- Sektör β_unlevered ortalama: {tuprs.sector_beta_unlevered}")
        lines.append(f"- β_relevered (sektör + firma D/E): {tuprs.beta_relevered}")
        lines.append(f"- Flags: {tuprs.flags}")
    else:
        lines.append("- TUPRS NOT FOUND in per_ticker results")

    return "\n".join(lines)


# ============================================================================
# 5) CLI
# ============================================================================

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 78)
    print("Session 3.6 — BIST Bottom-Up Sektör Beta (KAP+yfinance)")
    print("=" * 78)

    # 1) Sektör snapshot (Session 3.6 ADIM A)
    print("\n→ Loading ticker_sectors.json (KAP /tr/Sektorler)…")
    sec_snap = load_sector_snapshot()
    if sec_snap is None:
        print("  ✗ ticker_sectors.json missing — kap_sector_fetcher önce çalıştırın")
        return 1
    print(f"  ✓ {sec_snap.record_count} ticker, {sec_snap.distinct_sectors} sektör")

    # 2) BIST 100 returns
    print("\n→ Loading BIST 100 cache…")
    bist_close = _load_close(BIST100_CACHE)
    if bist_close is None:
        print(f"  ✗ {BIST100_CACHE} missing")
        return 1
    market_returns = _weekly_log_returns(bist_close)
    print(f"  ✓ BIST 100 weekly log returns: {len(market_returns)}")

    # 3) Float snapshot for market caps
    print("\n→ Loading kpy41_acc5 (float)…")
    float_snap = fetch_float_snapshot(cache=True)
    if float_snap.error:
        print(f"  ✗ Float fetch FAIL: {float_snap.error}")
        return 1
    market_caps: Dict[str, float] = {}
    # placeholder: market cap = shares × current price requires yfinance fast_info
    # şimdilik 0 — sektör mean equal-weighted
    print(f"  ✓ {float_snap.record_count} float records (market cap = equal-weight fallback)")

    # 4) Fundamentals (605 ticker × KAP Bilanço)
    print("\n→ Building KAP fundamentals cache (D/E + dialect)…")
    print("  NOT: First run ~10 dakika sürer (605 ticker × KAP fetch).")
    print("       Cached after first run — sonraki çalıştırmalar instant.")
    tickers = [r.ticker for r in sec_snap.records]
    fundamentals = _build_fundamentals_cache(tickers, force_refresh=False)
    print(f"  ✓ {len(fundamentals)} ticker fundamentals cached")

    # 5) Beta regression per ticker
    print("\n→ Computing per-ticker regression beta…")
    per_ticker = compute_beta_per_ticker(sec_snap, market_returns, fundamentals, market_caps)
    n_inc = sum(1 for t in per_ticker if not t.excluded)
    n_exc = sum(1 for t in per_ticker if t.excluded)
    print(f"  ✓ {n_inc} included / {n_exc} excluded")

    # 6) Sector aggregates
    print("\n→ Aggregating sector betas…")
    sector_aggs = aggregate_sectors(per_ticker)
    print(f"  ✓ {len(sector_aggs)} sector aggregates")

    # 7) Re-lever per ticker
    print("\n→ Re-levering per-ticker betas…")
    relever_per_ticker(per_ticker, sector_aggs)
    n_relevered = sum(1 for t in per_ticker if t.beta_relevered is not None)
    print(f"  ✓ {n_relevered} ticker re-levered")

    # 8) Output
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetch_date": date.today().isoformat(),
        "methodology": "Damodaran bottom-up beta, weekly log returns, 5y, BIST 100",
        "tax_rate_tr": DEFAULT_TAX_RATE_TR,
        "ticker_count": len(per_ticker),
        "included_count": n_inc,
        "sector_count": len(sector_aggs),
        "tickers": [asdict(t) for t in per_ticker],
        "sectors": [asdict(a) for a in sector_aggs.values()],
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(per_ticker, sector_aggs), encoding="utf-8")
    print(f"\n  ✓ JSON: {OUTPUT_JSON.relative_to(Path.cwd()) if OUTPUT_JSON.is_relative_to(Path.cwd()) else OUTPUT_JSON}")
    print(f"  ✓ MD:   {OUTPUT_MD.relative_to(Path.cwd()) if OUTPUT_MD.is_relative_to(Path.cwd()) else OUTPUT_MD}")

    # Anchor TUPRS print
    tuprs = next((t for t in per_ticker if t.ticker == "TUPRS"), None)
    if tuprs:
        print(f"\n  ★ TUPRS anchor:")
        print(f"      sector:           {tuprs.sector_name[:50]}")
        print(f"      β_levered:        {tuprs.beta_levered}")
        print(f"      R²:               {tuprs.r_squared}")
        print(f"      D/E:              {tuprs.de_ratio}")
        print(f"      β_unlevered:      {tuprs.beta_unlevered}")
        print(f"      sector mean β:    {tuprs.sector_beta_unlevered}")
        print(f"      β_relevered:      {tuprs.beta_relevered}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
