"""Engine A ProjectionInputs builder helpers (Phase 4a).

Damodaran-style input computations from TickerDataV4
(KAP + yfinance + Damodaran parameters).

ADR-080 Section 3 Adim 1.
"""

from typing import Optional


def compute_sales_to_capital(
    revenue: Optional[float],
    total_assets: Optional[float],
    cash: Optional[float],
) -> Optional[float]:
    """Damodaran sales-to-capital ratio.

    invested_capital = total_assets - excess_cash
    excess_cash       = max(0, cash - operating_cash_need)
    operating_cash_need = revenue * 2% (Damodaran heuristic, opcash)

    Returns None if inputs missing or invalid.

    Reference: Damodaran "Investment Valuation" Ch.10 reinvestment formula
      reinvestment_y = dRevenue_y / sales_to_capital

    Heineken validation case: 0.79 (5y avg) reference.
    """
    if not revenue or not total_assets:
        return None
    if revenue <= 0 or total_assets <= 0:
        return None

    operating_cash_need = revenue * 0.02
    excess_cash = max(0.0, (cash or 0.0) - operating_cash_need)
    invested_capital = total_assets - excess_cash

    if invested_capital <= 0:
        return None

    return revenue / invested_capital


def compute_explicit_growth_rate(
    revenue_current: Optional[float],
    revenue_previous: Optional[float],
    lifecycle_stage: Optional[str] = None,
) -> Optional[float]:
    """Phase 4a Adim 2: Composite explicit_growth_rate (Damodaran).

    Composite formula:
        raw_growth = (revenue_current / revenue_previous) - 1
        bounded    = clamp(raw_growth, lifecycle_min, lifecycle_max)

    Fallback chain:
        Tier 1: KAP 2y growth clamped to lifecycle bound
        Tier 2: lifecycle_default (KAP data missing)

    Damodaran "Act Your Age" framework alignment.

    ADR-080 v2 doctrine: 5y CAGR yerine composite (yfinance 4y data
    eksik + TRY currency mismatch + KAP Excel 2 period limit).

    Args:
        revenue_current:  KAP cari period revenue (TickerDataV4.revenue)
        revenue_previous: KAP onceki period revenue (yeni transfer Adim 5'te)
        lifecycle_stage:  TickerDataV4.lifecycle_stage

    Returns:
        Composite explicit growth rate (decimal, e.g. 0.10 = 10%) or
        lifecycle_default if KAP data missing.
    """
    from dcf_engine.lifecycle_classifier import get_lifecycle_defaults

    config = get_lifecycle_defaults(lifecycle_stage)
    growth_min = config["growth_min"]
    growth_max = config["growth_max"]
    growth_default = config["growth_default"]

    if revenue_current and revenue_previous and revenue_previous > 0:
        raw_growth = (revenue_current / revenue_previous) - 1.0
        return max(growth_min, min(growth_max, raw_growth))

    return growth_default


def compute_implied_roc(
    stable_growth: Optional[float],
    net_cap_ex_sales: Optional[float],
    stable_op_margin: Optional[float],
    tax_rate: float = 0.25,
) -> Optional[float]:
    """Phase 5c: Damodaran Implied ROC terminal value sanity (ImpliedROCROE.xls).

    Damodaran 'Sustainable Growth' rule:
      Stable phase: g = ROC x Reinvestment_Rate
      ROC = g / RR
      RR (NOPAT-based) = NetCapEx / EBIT(1-t)
                       = NCE_Sales / (OpMargin x (1-t))

    Standart Damodaran convention (g/RR):
      Implied_ROC = g_stable x (Margin x (1-t)) / NCE_Sales

    BRIEF formula (5c, user-specified):
      Implied_ROC = (g_stable x NCE_Sales) / (Margin x (1-t))

    NOT: Brief formula matematik inverse Damodaran standart g/RR.
    Brief formula yine sustainable-vs-unsustainable yön testini saglar
    (her iki formul ayni isaretle WACC karsisinda flag tetikler) ama
    magnitude farkli (TUPRS standart 4.51%% vs brief 1.39%%).

    Bu helper Damodaran STANDART formul kullanir (g/RR), brief'in
    matematik interpretation'inda iz birakmak icin.
    """
    if stable_op_margin is None or stable_op_margin <= 0:
        return None
    if stable_growth is None or stable_growth <= 0:
        return None
    if net_cap_ex_sales is None or net_cap_ex_sales <= 0:
        return None

    after_tax_margin = stable_op_margin * (1 - tax_rate)
    if after_tax_margin <= 0:
        return None

    # Damodaran standart: ROC = g / RR = g x (Margin x (1-t)) / NCE_Sales
    implied_roc = stable_growth * after_tax_margin / net_cap_ex_sales
    return implied_roc


def compute_pe_implied_intrinsic(
    op_income: Optional[float],
    shares_outstanding: Optional[float],
    sector_pe: Optional[float],
    tax_rate: float = 0.25,
) -> Optional[float]:
    """Phase 4d: Multi-multiple PE-implied intrinsic.

    Net Income proxy = Op_Income x (1 - tax_rate)  (interest expense ihmal)
    EPS = Net_Income / shares
    PE_implied = EPS x sector_PE

    Currency-invariant: shares/op_income same currency -> output same currency.
    """
    if op_income is None or op_income <= 0:
        return None
    if shares_outstanding is None or shares_outstanding <= 0:
        return None
    if sector_pe is None or sector_pe <= 0 or sector_pe > 100:
        return None
    net_income = op_income * (1 - tax_rate)
    eps = net_income / shares_outstanding
    return eps * sector_pe


def compute_pbv_implied_intrinsic(
    total_equity: Optional[float],
    shares_outstanding: Optional[float],
    sector_pbv: Optional[float],
) -> Optional[float]:
    """Phase 4d: Multi-multiple PBV-implied intrinsic.

    BVPS = book_equity / shares
    PBV_implied = BVPS x sector_PBV
    """
    if total_equity is None or total_equity <= 0:
        return None
    if shares_outstanding is None or shares_outstanding <= 0:
        return None
    if sector_pbv is None or sector_pbv <= 0 or sector_pbv > 20:
        return None
    bvps = total_equity / shares_outstanding
    return bvps * sector_pbv


def compute_consensus(
    intrinsic: Optional[float],
    pe_implied: Optional[float],
    pbv_implied: Optional[float],
) -> tuple:
    """Phase 4d: 3-way consensus median + dispersion.

    Returns (consensus_median, dispersion).
    dispersion = stdev / median (>0.5 -> high dispersion warning)
    """
    import statistics as _stat
    valid = [v for v in [intrinsic, pe_implied, pbv_implied] if v is not None and v > 0]
    if not valid:
        return None, None
    median_val = _stat.median(valid)
    if len(valid) > 1 and median_val > 0:
        try:
            disp = _stat.stdev(valid) / median_val
        except _stat.StatisticsError:
            disp = None
    else:
        disp = None
    return median_val, disp


def compute_taper_config(lifecycle_stage: Optional[str] = None) -> dict:
    """Phase 4a Adim 4: Damodaran 'Act Your Age' taper config builder.

    Returns ProjectionInputs taper fields (Engine A industrial_fcff):
      margin_taper_start_year, margin_taper_end_year (lifecycle-aware)
      tax_taper_start_year, tax_taper_end_year (5/10 Damodaran convention)
      explicit_period_years (5 mature, 10 growth)
      transition_period_years (5 Damodaran default)

    Damodaran convention (Heineken/ABN PASS pattern):
      tax_taper Year 5-10 (her ticker icin sabit, country tax convergence)
      margin_taper Year-N..10 (lifecycle stage'e gore N degisir)

    Unknown stage -> mature_stable conservative.
    """
    from dcf_engine.lifecycle_classifier import get_lifecycle_defaults

    config = get_lifecycle_defaults(lifecycle_stage)

    return {
        "margin_taper_start_year": int(config["margin_taper_start"]),
        "margin_taper_end_year": int(config["margin_taper_end"]),
        # Damodaran tax_taper convention (country tax converge Y5-Y10)
        "tax_taper_start_year": 5,
        "tax_taper_end_year": 10,
        "explicit_period_years": int(config["explicit_period_years"]),
        "transition_period_years": int(config["transition_period_years"]),
    }


def compute_non_operating_assets(
    financial_investments: Optional[float],
    investment_properties: Optional[float],
    equity_method_investments: Optional[float],
) -> float:
    """Phase 4a Adim 5: Damodaran non_operating_assets aggregate.

    Damodaran formal equity bridge convention:
      non_op_assets = financial_investments
                    + investment_properties (Phase 3a)
                    + equity_method_investments (Phase 3a)

    Equity bridge (Engine A industrial_fcff dcf_valuation):
      equity = operating_value - debt - minority + cash + non_op_assets

    Graceful degradation: None inputs -> 0.0.
    """
    total = 0.0
    total += financial_investments or 0.0
    total += investment_properties or 0.0
    total += equity_method_investments or 0.0
    return total


_SECTOR_MAP_CACHE: Optional[dict] = None


def _load_bist_to_damodaran_sector_map() -> dict:
    """Lazy-load BIST -> Damodaran sector mapping (Phase 3c config)."""
    global _SECTOR_MAP_CACHE
    if _SECTOR_MAP_CACHE is None:
        import json
        from pathlib import Path
        map_path = Path(__file__).resolve().parents[2] / "apps/api/config/damodaran_sector_map.json"
        if not map_path.exists():
            # Fallback path resolution
            map_path = Path("apps/api/config/damodaran_sector_map.json")
        try:
            with map_path.open(encoding="utf-8") as f:
                data = json.load(f)
            _SECTOR_MAP_CACHE = data.get("mapping", data)
        except Exception:
            _SECTOR_MAP_CACHE = {}
    return _SECTOR_MAP_CACHE


def compute_terminal_ebit_margin(
    ticker_sector_tr: Optional[str],
    starting_margin: Optional[float],
    sector_multiples_data: Optional[dict] = None,
    em_margin_data: Optional[dict] = None,
    damodaran_sector_override: Optional[str] = None,
) -> Optional[float]:
    """Phase 4a Adim 3 + Phase 5b.2: Damodaran terminal_ebit_margin.

    4-tier fallback chain (Phase 5b.2 EM_FIRST):
      Tier 0: EM-first lookup (margin_emerg.json, Phase 5a) if em_margin_data
      Tier 1: Global sector op_margin_pretax (sector_multiples.json)
      Tier 2: 0.5 x starting_margin (Damodaran compression)
      Tier 3: 0.10 (mature_stable conservative default)

    Sanity cap: [0.05, 0.40]

    Args:
        ticker_sector_tr: TickerDataV4.sector_name (BIST TR)
        starting_margin: td.op_income / td.revenue
        sector_multiples_data: Global sector_multiples.json content
        em_margin_data: Phase 5a margin_emerg.json content (EM-first lookup)
        damodaran_sector_override: Ticker-level Damodaran sector override
                                   (Phase 5b.1.2.A: TUPRS Distribution, EREGL Steel, etc)
    """
    SANITY_LOW = 0.05
    SANITY_HIGH = 0.40

    damodaran_sector = damodaran_sector_override
    if not damodaran_sector and ticker_sector_tr:
        sector_map = _load_bist_to_damodaran_sector_map()
        damodaran_sector = sector_map.get(ticker_sector_tr)

    # Tier 0 (Phase 5b.2): EM-first lookup
    if damodaran_sector and em_margin_data:
        sd = em_margin_data.get(damodaran_sector, {})
        m = sd.get("Pre-tax Unadjusted Operating Margin")
        if m is not None and m > 0:
            return max(SANITY_LOW, min(SANITY_HIGH, float(m)))

    # Tier 1: Global sector lookup
    if damodaran_sector and sector_multiples_data:
        sd = sector_multiples_data.get(damodaran_sector, {})
        m = sd.get("op_margin_pretax")
        if m is not None and m > 0:
            return max(SANITY_LOW, min(SANITY_HIGH, float(m)))

    # Tier 2: Compression heuristic (Damodaran convention)
    if starting_margin is not None and starting_margin > 0:
        compressed = starting_margin * 0.5
        return max(SANITY_LOW, min(SANITY_HIGH, compressed))

    # Tier 3: Mature stable conservative default
    return 0.10
