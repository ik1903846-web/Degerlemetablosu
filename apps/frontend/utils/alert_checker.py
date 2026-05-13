"""Phase 7.3 Alert checker — 3 alert types (Damodaran disiplin)."""

from __future__ import annotations

from typing import Optional


def check_alerts(watchlist_tickers: list, ticker_records: list) -> list:
    """Phase 7.3 alert generator.

    Alert types:
      PRICE_DROP        — current_price < intrinsic * 0.85 (15%% fiyat alti)
      DISPERSION_ALERT  — consensus_dispersion > 0.50 (high disp Engine A review)
      VALUE_TRAP        — final_recommendation == VALUE_TRAP_WARNING

    Returns: list of alert dicts with severity HIGH/MEDIUM/LOW.
    """
    alerts: list = []
    by_ticker = {r.get("ticker"): r for r in ticker_records}
    for ticker in watchlist_tickers:
        r = by_ticker.get(ticker)
        if not r:
            alerts.append({
                "ticker": ticker,
                "alert_type": "MISSING_DATA",
                "message": "Ticker veriside yok",
                "severity": "LOW",
            })
            continue
        intrinsic = r.get("intrinsic_per_share_tl")
        price = r.get("current_price_tl")
        dispersion = r.get("consensus_dispersion")
        final_rec = r.get("final_recommendation")
        composite = r.get("composite_signal")

        # Alert 1: PRICE_DROP (price < intrinsic * 0.85)
        if intrinsic and price and intrinsic > 0:
            threshold = intrinsic * 0.85
            if price < threshold:
                alerts.append({
                    "ticker": ticker,
                    "alert_type": "PRICE_DROP",
                    "message": (
                        f"Fiyat {price:.2f} TL < intrinsic*0.85 ({threshold:.2f} TL), "
                        f"upside +{(intrinsic/price - 1)*100:.0f}%%"
                    ),
                    "severity": "HIGH" if composite == "BUY" else "MEDIUM",
                })

        # Alert 2: DISPERSION_ALERT (high multi-multiple sapma)
        if dispersion is not None and dispersion > 0.50:
            sev = "HIGH" if dispersion > 1.00 else "MEDIUM"
            alerts.append({
                "ticker": ticker,
                "alert_type": "DISPERSION_ALERT",
                "message": f"Multi-multiple dispersion %{dispersion*100:.0f} (Engine A review)",
                "severity": sev,
            })

        # Alert 3: VALUE_TRAP (BUY ama katalizor yok)
        if final_rec == "VALUE_TRAP_WARNING":
            alerts.append({
                "ticker": ticker,
                "alert_type": "VALUE_TRAP",
                "message": "BUY sinyali ama katalizor yok (ucuz ama value trap riski)",
                "severity": "MEDIUM",
            })

    # Severity sirala (HIGH -> MEDIUM -> LOW)
    sev_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    alerts.sort(key=lambda a: sev_order.get(a["severity"], 99))
    return alerts
