"""Phase 7.2 Catalyst Scorer — PROXY MVP (insider fetcher pending).

Damodaran "Katalizor sinyali olmadan ucuz = value trap" rule.

Phase 7.2.1 PROXY MVP (commit 103):
  Mevcut sinyallerden composite (insider/dividend/ROE history infra YOK):
    terminal_value_sustainable (Phase 5c)  : +20 (Damodaran terminal health)
    consensus_dispersion validated (<0.30) : +15 (multi-multiple uyum)
    revenue_yoy positive (KAP cari/onceki) : +10 (basic momentum)
    mos_consensus >= 0 (cross-check undervalued): +5
  Max: 50

Phase 7.2.2 PARK (gelecek):
  KAP insider transactions fetcher (Subject UUID 'Icsel Bilgi Ozel Durum')
  Insider buying_count 90d, volume_tl: +15 + +10 (en güclu Damodaran sinyal)
  Ceo change KAP rapor: +5
  Dividend yield > sector median: replace revenue proxy
  ROE YoY: replace mos proxy
"""

from typing import Optional


def compute_catalyst_score_mvp(
    terminal_sustainable: Optional[bool],
    consensus_dispersion: Optional[float],
    revenue_current: Optional[float],
    revenue_previous: Optional[float],
    mos_consensus: Optional[float],
) -> int:
    """Phase 7.2.1 PROXY score 0-50.

    Component breakdown:
      A. terminal_value_sustainable=True   : +20 (Damodaran terminal health)
      B. consensus_dispersion <= 0.30       : +15 (multi-multiple validated)
      C. revenue_yoy > 0 (TL nominal)        : +10
      D. mos_consensus >= 0                  : +5  (cross-check undervalued)
    """
    score = 0
    if terminal_sustainable is True:
        score += 20
    if consensus_dispersion is not None and consensus_dispersion <= 0.30:
        score += 15
    if revenue_current and revenue_previous and revenue_previous > 0:
        if (revenue_current / revenue_previous - 1) > 0:
            score += 10
    if mos_consensus is not None and mos_consensus >= 0:
        score += 5
    return score


def classify_catalyst_signal(score: Optional[int]) -> Optional[str]:
    """Phase 7.2.1 catalyst 4-level threshold (PROXY MVP calibrated).

    PROXY MVP score range 0-30 typical (insider/dividend/ROE infra YOK),
    threshold ona gore (Phase 7.2.2 insider fetcher sonrasi recalibrate).
    """
    if score is None:
        return None
    if score <= 10:
        return "VALUE_TRAP_RISK"
    elif score <= 15:
        return "WATCHLIST"
    elif score <= 25:
        return "SWEET_SPOT"
    else:
        return "STRONG_BUY"


def compute_final_recommendation(
    composite_signal: Optional[str],
    catalyst_signal: Optional[str],
) -> Optional[str]:
    """Phase 7.2.1 Damodaran karar matrix (composite x catalyst).

    BUY + STRONG_BUY/SWEET_SPOT   : PRIMARY_TARGET
    BUY + WATCHLIST               : SECONDARY_TARGET
    BUY + VALUE_TRAP_RISK         : VALUE_TRAP_WARNING (ucuz ama katalizor yok)
    WAIT + STRONG_BUY/SWEET_SPOT  : RE_EVALUATE (cross-check incele)
    Else                          : BEKLE
    """
    if composite_signal == "BUY":
        if catalyst_signal in ("SWEET_SPOT", "STRONG_BUY"):
            return "PRIMARY_TARGET"
        elif catalyst_signal == "WATCHLIST":
            return "SECONDARY_TARGET"
        else:
            return "VALUE_TRAP_WARNING"
    if composite_signal == "WAIT" and catalyst_signal in ("SWEET_SPOT", "STRONG_BUY"):
        return "RE_EVALUATE"
    return "BEKLE"


def apply_catalyst_to_td(td) -> None:
    """Phase 7.2 catalyst + final_recommendation in-place compute.

    Tum dialect coverage (industrial / banking / holding / sector / book).
    Phase 7.1 composite_signal + Phase 7.2 catalyst -> final_recommendation.
    """
    # Revenue YoY: industrial dialect KAP transfer (Phase 4a Adim 5)
    rev_current = getattr(td, "revenue", None)
    rev_previous = getattr(td, "revenue_onceki", None)
    ts_sustain = getattr(td, "terminal_value_sustainable", None)
    cons_disp = getattr(td, "consensus_dispersion", None)
    mos_cons = getattr(td, "mos_consensus", None)

    score = compute_catalyst_score_mvp(ts_sustain, cons_disp, rev_current, rev_previous, mos_cons)
    sig = classify_catalyst_signal(score)
    rec = compute_final_recommendation(getattr(td, "composite_signal", None), sig)

    td.catalyst_score = score
    td.catalyst_signal = sig
    td.final_recommendation = rec
