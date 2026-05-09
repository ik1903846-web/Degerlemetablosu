#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUPRS Shadow Calculation - Faz B1 Adim 5
========================================

Anchor 187.10 TL DOKUNULMAZ. WACC ratio yontemi ile Damodaran
params altinda shadow value hesaplanir.

Matematik:
  Production value = sum(FCFF_t / (1+wacc_old)^t) + TV_old
  Damodaran value  = sum(FCFF_t / (1+wacc_new)^t) + TV_new

  FCFF projection ve growth aynidir (TUPRS finansallari degismedi).
  ratio = damodaran_value / production_value
  shadow_tl = 187.10 * ratio

3 profil sensitivity:
  TUPRS_defensive  (beta=0.95, lambda=0.85)
  TUPRS_base       (beta=1.05, lambda=1.00) <- Damodaran sector
  TUPRS_aggressive (beta=1.15, lambda=1.15)
"""

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PARAMS_PATH = (
    REPO_ROOT / "apps" / "api" / "data" / "damodaran"
    / "2026_05_09" / "parameters.json"
)
REPORTS_DIR = REPO_ROOT / "reports"

# ANCHOR - DOKUNULMAZ, sadece okuma
TUPRS_ANCHOR_TL = 187.10
ANCHOR_PARAM_DATE = "Ocak 2026 (production stale)"

# Production constants (cost_of_capital.py'dan, Adim 2C)
PRODUCTION = {
    "rf": 0.0397,
    "mature_erp": 0.0444,
    "turkey_crp": 0.0601,
    "turkey_sovereign_spread": 0.0446,
    "tax_rate": 0.25,
}


# TUPRS sensitivity profiles (3 varyasyon)
TUPRS_PROFILES = {
    "TUPRS_defensive": {
        "name": "TUPRS Defansif (dusuk beta, lambda<1)",
        "beta_unlevered": 0.95,
        "debt_equity": 0.30,
        "lambda_country": 0.85,
        "g_high": 0.04,
        "g_terminal": 0.025,
        "n_high_growth": 5,
        "kd_corp_spread": 0.015,
        "rationale": "Petrokimya defansif yorum, ihracat dusuk varsayim",
    },
    "TUPRS_base": {
        "name": "TUPRS Base (Damodaran sector cyclical)",
        "beta_unlevered": 1.05,
        "debt_equity": 0.40,
        "lambda_country": 1.00,
        "g_high": 0.05,
        "g_terminal": 0.025,
        "n_high_growth": 5,
        "kd_corp_spread": 0.018,
        "rationale": "Damodaran sector beta cyclical petrokimya, "
                     "lambda=1 domestik+regional heavy",
    },
    "TUPRS_aggressive": {
        "name": "TUPRS Agresif (yuksek beta, commodity export)",
        "beta_unlevered": 1.15,
        "debt_equity": 0.50,
        "lambda_country": 1.15,
        "g_high": 0.06,
        "g_terminal": 0.025,
        "n_high_growth": 5,
        "kd_corp_spread": 0.020,
        "rationale": "Cyclical aggressive yorum, commodity export "
                     "lambda > 1 (Damodaran formulu)",
    },
}


def levered_beta(b_u, de, t):
    return b_u * (1 + (1 - t) * de)


def cost_of_equity(rf, mature_erp, beta, lam, crp):
    return rf + beta * mature_erp + lam * crp


def cost_of_debt_pretax(rf, sovereign, corp):
    return rf + sovereign + corp


def wacc(ke, kd_pre, tax, de):
    we = 1.0 / (1.0 + de)
    wd = de / (1.0 + de)
    return we * ke + wd * kd_pre * (1 - tax)


def two_stage_dcf(fcff_0, g_high, n, g_term, r):
    if r <= g_term:
        return float("inf")
    pv_high = sum(
        fcff_0 * ((1 + g_high) ** t) / ((1 + r) ** t)
        for t in range(1, n + 1)
    )
    fcff_n = fcff_0 * ((1 + g_high) ** n)
    tv = fcff_n * (1 + g_term) / (r - g_term)
    return pv_high + tv / ((1 + r) ** n)


def calc_shadow(profile, prod, dam, anchor_tl):
    b_u = profile["beta_unlevered"]
    de = profile["debt_equity"]
    lam = profile["lambda_country"]
    tax = prod["tax_rate"]
    corp = profile["kd_corp_spread"]
    g_high = profile["g_high"]
    g_term = profile["g_terminal"]
    n = profile["n_high_growth"]

    bl = levered_beta(b_u, de, tax)

    p_ke = cost_of_equity(
        prod["rf"], prod["mature_erp"], bl, lam, prod["turkey_crp"]
    )
    p_kd = cost_of_debt_pretax(
        prod["rf"], prod["turkey_sovereign_spread"], corp
    )
    p_wacc = wacc(p_ke, p_kd, tax, de)
    p_value = two_stage_dcf(100, g_high, n, g_term, p_wacc)

    d_ke = cost_of_equity(
        dam["rf"], dam["mature_erp"], bl, lam, dam["turkey_crp"]
    )
    d_kd = cost_of_debt_pretax(
        dam["rf"], dam["turkey_sovereign_spread"], corp
    )
    d_wacc = wacc(d_ke, d_kd, tax, de)
    d_value = two_stage_dcf(100, g_high, n, g_term, d_wacc)

    ratio = d_value / p_value
    shadow = anchor_tl * ratio
    delta_pct = (ratio - 1) * 100

    return {
        "name": profile["name"],
        "rationale": profile["rationale"],
        "beta_levered": bl,
        "p_wacc": p_wacc,
        "d_wacc": d_wacc,
        "wacc_delta_pp": (d_wacc - p_wacc) * 100,
        "ratio": ratio,
        "shadow_tl": shadow,
        "delta_pct": delta_pct,
    }


def render_console(key, r):
    print(f"\n  {r['name']}")
    print(f"    Profile key:    {key}")
    print(f"    Rationale:      {r['rationale']}")
    print(f"    Beta levered:   {r['beta_levered']:.4f}")
    print(f"    WACC prod:      {r['p_wacc']*100:.2f}%")
    print(f"    WACC damodaran: {r['d_wacc']*100:.2f}%")
    print(f"    WACC delta:     {r['wacc_delta_pp']:+.2f} pp")
    print(f"    Ratio:          {r['ratio']:.4f}")
    print(f"    Anchor:         {TUPRS_ANCHOR_TL:.2f} TL (INTACT)")
    print(f"    Shadow:         {r['shadow_tl']:.2f} TL")
    print(f"    Delta vs anchor: {r['delta_pct']:+.2f}%")


def render_markdown(results, prod, dam):
    now = datetime.now(timezone.utc).isoformat()

    shadows = [r["shadow_tl"] for r in results.values()]
    deltas = [r["delta_pct"] for r in results.values()]
    shadow_min = min(shadows)
    shadow_max = max(shadows)
    shadow_mean = sum(shadows) / len(shadows)
    delta_mean = sum(deltas) / len(deltas)

    md = []
    md.append("# TUPRS Shadow Calculation - Faz B1 Adim 5")
    md.append("")
    md.append(f"**Rapor tarihi (UTC):** {now}")
    md.append("**Yontem:** WACC ratio (anchor INTACT, FCFF projection sabit)")
    md.append("")
    md.append("## Anchor Durumu")
    md.append("")
    md.append(f"- **TUPRS_v4.0_anchor:** {TUPRS_ANCHOR_TL:.2f} TL")
    md.append(f"- **Param state:** {ANCHOR_PARAM_DATE}")
    md.append("- **Status:** INTACT - Bu hesapta DOKUNULMADI")
    md.append("")
    md.append("## Sensitivity Profiles")
    md.append("")

    for key, r in results.items():
        md.append(f"### {r['name']}")
        md.append("")
        md.append(f"- Profile key: `{key}`")
        md.append(f"- Rationale: {r['rationale']}")
        md.append("")
        md.append("| Metric | Production | Damodaran | Delta |")
        md.append("|--------|------------|-----------|-------|")
        md.append(
            f"| Beta levered | {r['beta_levered']:.4f} | "
            f"{r['beta_levered']:.4f} | (sabit) |"
        )
        md.append(
            f"| WACC | {r['p_wacc']*100:.2f}% | "
            f"{r['d_wacc']*100:.2f}% | "
            f"{r['wacc_delta_pp']:+.2f}pp |"
        )
        md.append(f"| Value ratio (norm) | 1.0000 | {r['ratio']:.4f} | "
                  f"{r['delta_pct']:+.2f}% |")
        md.append(
            f"| TUPRS shadow (TL) | {TUPRS_ANCHOR_TL:.2f} | "
            f"**{r['shadow_tl']:.2f}** | "
            f"**{r['delta_pct']:+.2f}%** |"
        )
        md.append("")

    md.append("## Shadow Range Ozeti")
    md.append("")
    md.append(f"- **Min shadow:** {shadow_min:.2f} TL")
    md.append(f"- **Max shadow:** {shadow_max:.2f} TL")
    md.append(f"- **Mean shadow:** {shadow_mean:.2f} TL")
    md.append(f"- **Mean delta:** {delta_mean:+.2f}%")
    md.append("")

    md.append("## Audit Decision §3.5 Beklentisi vs Sonuc")
    md.append("")
    md.append("- Beklenen shadow: 210-225 TL araligi")
    md.append(
        f"- Olculen shadow range: {shadow_min:.2f} - {shadow_max:.2f} TL"
    )
    expected_low, expected_high = 210, 225
    if shadow_min >= expected_low and shadow_max <= expected_high:
        md.append("- **Sonuc: BEKLENTI ICINDE (range bekleneni kapsiyor)**")
    elif shadow_mean >= expected_low and shadow_mean <= expected_high:
        md.append(
            "- **Sonuc: MEAN BEKLENTI ICINDE, range biraz disari "
            "(profile sensitivity normal)**"
        )
    else:
        md.append(
            f"- **Sonuc: BEKLENTI DISI** "
            f"(beklenen {expected_low}-{expected_high}, "
            f"olculen mean {shadow_mean:.2f})"
        )
    md.append("")

    md.append("## Adim 6 Onerisi (audit_decision §3.6)")
    md.append("")
    md.append("**Onerilen: 6a Yumusak Gecis**")
    md.append("")
    md.append("- v4.0 anchor (187.10 TL): Git tag `anchor-v4.0-pre-Feb2026`")
    md.append(f"- v4.1 anchor (yeni): {shadow_mean:.2f} TL "
              f"(3 profil ortalamasi)")
    md.append("- Gecis tarihi: bugun (2026-05-09)")
    md.append("- Yeni Δ tolerance: %0.50 (gecis ayinda esnek)")
    md.append("- 1 ay sonra Δ tolerance %0.30'a sikilasir")
    md.append("")
    md.append(
        "Reddedilen: 6b cift anchor (operasyonel karmasa), "
        "6c degistirme (apples-to-oranges, bilimsel olmuyor)."
    )
    md.append("")
    md.append("## Sonraki Adim")
    md.append("")
    md.append(
        "- **Adim 6:** Yumusak gecis kararini commit'le "
        "(yeni anchor ilan, eski archive)"
    )
    md.append(
        "- **Adim 7:** cost_of_capital.py constants update "
        "(atomic, audit_decision_v4.md)"
    )
    md.append(
        "- **Adim 8:** ADR-040 post-mortem"
    )
    md.append("")
    md.append("---")
    md.append("")
    md.append("*Read-only test. TUPRS anchor 187.10 DOKUNULMADI. "
              "cost_of_capital.py DOKUNULMADI.*")

    return "\n".join(md) + "\n"


def main() -> int:
    print("=" * 60)
    print("TUPRS Shadow Calculation - Faz B1 Adim 5")
    print("=" * 60)

    print(f"\n[1] parameters.json yukleniyor...")
    if not PARAMS_PATH.exists():
        print(f"    HATA: {PARAMS_PATH} bulunamadi")
        return 1
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))

    DAMODARAN = {
        "rf": params["rf_usd_estimate"],
        "mature_erp": params["mature_erp"],
        "turkey_crp": params["turkey"]["crp"],
        "turkey_sovereign_spread": params["turkey"]["default_spread"],
        "tax_rate": params["turkey"]["tax_rate"],
    }

    print(f"    fetch_date: {params.get('fetch_date')}")
    print(f"\n[2] TUPRS Anchor: {TUPRS_ANCHOR_TL:.2f} TL "
          f"(INTACT, {ANCHOR_PARAM_DATE})")

    print(f"\n[3] 3 profil sensitivity hesabi...")
    results = {}
    for key, profile in TUPRS_PROFILES.items():
        r = calc_shadow(profile, PRODUCTION, DAMODARAN, TUPRS_ANCHOR_TL)
        render_console(key, r)
        results[key] = r

    shadows = [r["shadow_tl"] for r in results.values()]
    deltas = [r["delta_pct"] for r in results.values()]
    shadow_min = min(shadows)
    shadow_max = max(shadows)
    shadow_mean = sum(shadows) / len(shadows)
    delta_mean = sum(deltas) / len(deltas)

    print(f"\n[4] Markdown rapor uretiliyor...")
    md = render_markdown(results, PRODUCTION, DAMODARAN)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "tuprs_shadow_2026_05_09.md"
    report_path.write_text(md, encoding="utf-8")
    print(f"    Rapor: {report_path}")

    print("\n" + "=" * 60)
    print(f"SHADOW RANGE: {shadow_min:.2f} - {shadow_max:.2f} TL "
          f"(mean: {shadow_mean:.2f})")
    print(f"MEAN DELTA:   {delta_mean:+.2f}%")
    print("=" * 60)
    print(f"ANCHOR 187.10 TL: INTACT (dokunulmadi)")
    print(f"ADIM 6 ONERILEN: 6a Yumusak Gecis "
          f"(yeni anchor: {shadow_mean:.2f} TL)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
