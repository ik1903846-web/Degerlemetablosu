#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parameter Sensitivity Test - Faz B1 Adim 3
==========================================

Production cost_of_capital.py constants vs Damodaran 2026-05-09
parameters.json. DCF impact ölç.

Test sirketleri:
  1. TTRAK_approx - Turk Traktor (Mature Growth, λ ortalama)
  2. TYPICAL_DOMESTIC - Tipik domestic BIST profil (β=1, λ=1)

ANCHOR INTACT: TUPRS test edilmez. Adim 5'te shadow hesap.

Karar noktasi (audit_decision §3.4):
  Sapma < %5  → Faz B2'ye don (production zaten guncel?)
  Sapma %5-25 → BEKLENEN, Adim 5'e gec
  Sapma > %25 → STOP, audit derinlestir
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


# Production constants (cost_of_capital.py satir 27-31'den okundu, Adim 2C)
PRODUCTION = {
    "rf": 0.0397,
    "mature_erp": 0.0444,
    "turkey_crp": 0.0601,
    "turkey_sovereign_spread": 0.0446,
    "tax_rate": 0.25,
}


# Test profilleri - TUPRS yok (anchor riski)
PROFILES = {
    "TTRAK_approx": {
        "name": "Turk Traktor (Mature Growth, Stage 4)",
        "beta_unlevered": 0.95,   # Damodaran sector approx
        "debt_equity": 0.20,       # KAP TTRAK approx
        "lambda_country": 0.85,    # ihracat ~%15, domestic heavy
        "g_high": 0.06,            # mature growth
        "g_terminal": 0.025,
        "n_high_growth": 5,
        "kd_corp_spread": 0.015,   # corporate rating spread
        "fcff_0_normalized": 100,  # arbitrary base, sapma % degismez
    },
    "TYPICAL_DOMESTIC": {
        "name": "Tipik domestic BIST (Stage 4, sanity check)",
        "beta_unlevered": 1.00,
        "debt_equity": 0.50,
        "lambda_country": 1.00,
        "g_high": 0.05,
        "g_terminal": 0.025,
        "n_high_growth": 5,
        "kd_corp_spread": 0.020,
        "fcff_0_normalized": 100,
    },
}


def levered_beta(b_u, de, t):
    """Hamada formula"""
    return b_u * (1 + (1 - t) * de)


def cost_of_equity(rf, mature_erp, beta, lam, crp):
    """Modified CAPM with country lambda"""
    return rf + beta * mature_erp + lam * crp


def cost_of_debt_pretax(rf, sovereign_spread, corp_spread):
    return rf + sovereign_spread + corp_spread


def wacc(ke, kd_pretax, tax_rate, de):
    """WACC = we*ke + wd*kd*(1-t)"""
    we = 1.0 / (1.0 + de)
    wd = de / (1.0 + de)
    return we * ke + wd * kd_pretax * (1 - tax_rate)


def two_stage_dcf(fcff_0, g_high, n, g_terminal, discount_rate):
    """2-stage FCFF model"""
    if discount_rate <= g_terminal:
        return float("inf")
    pv_high = sum(
        fcff_0 * ((1 + g_high) ** t) / ((1 + discount_rate) ** t)
        for t in range(1, n + 1)
    )
    fcff_n = fcff_0 * ((1 + g_high) ** n)
    tv = fcff_n * (1 + g_terminal) / (discount_rate - g_terminal)
    pv_tv = tv / ((1 + discount_rate) ** n)
    return pv_high + pv_tv


def run_profile(profile_key, profile, prod_params, dam_params):
    """Bir profil için iki run (prod vs damodaran) ve sapma."""
    b_u = profile["beta_unlevered"]
    de = profile["debt_equity"]
    lam = profile["lambda_country"]
    tax = prod_params["tax_rate"]
    corp_spread = profile["kd_corp_spread"]
    fcff_0 = profile["fcff_0_normalized"]
    g_high = profile["g_high"]
    g_term = profile["g_terminal"]
    n = profile["n_high_growth"]

    beta_l = levered_beta(b_u, de, tax)

    # PRODUCTION RUN
    p_ke = cost_of_equity(
        prod_params["rf"], prod_params["mature_erp"],
        beta_l, lam, prod_params["turkey_crp"],
    )
    p_kd = cost_of_debt_pretax(
        prod_params["rf"],
        prod_params["turkey_sovereign_spread"],
        corp_spread,
    )
    p_wacc = wacc(p_ke, p_kd, tax, de)
    p_value = two_stage_dcf(fcff_0, g_high, n, g_term, p_wacc)

    # DAMODARAN RUN
    d_ke = cost_of_equity(
        dam_params["rf"], dam_params["mature_erp"],
        beta_l, lam, dam_params["turkey_crp"],
    )
    d_kd = cost_of_debt_pretax(
        dam_params["rf"],
        dam_params["turkey_sovereign_spread"],
        corp_spread,
    )
    d_wacc = wacc(d_ke, d_kd, tax, de)
    d_value = two_stage_dcf(fcff_0, g_high, n, g_term, d_wacc)

    deviation = (d_value / p_value - 1.0) * 100.0

    return {
        "key": profile_key,
        "name": profile["name"],
        "beta_levered": beta_l,
        "prod": {
            "ke": p_ke, "kd_pre": p_kd, "wacc": p_wacc, "value": p_value
        },
        "dam": {
            "ke": d_ke, "kd_pre": d_kd, "wacc": d_wacc, "value": d_value
        },
        "deviation_pct": deviation,
    }


def render_console(result):
    p = result["prod"]
    d = result["dam"]
    print(f"\n  {result['name']} (key: {result['key']})")
    print(f"    Beta levered: {result['beta_levered']:.4f}")
    print(f"    {'Metric':<20} {'Production':>14} {'Damodaran':>14} {'Delta':>12}")
    print(f"    {'-'*60}")
    print(
        f"    {'Cost of Equity':<20} "
        f"{p['ke']*100:>13.2f}% {d['ke']*100:>13.2f}% "
        f"{(d['ke']-p['ke'])*100:>11.2f}pp"
    )
    print(
        f"    {'Cost of Debt (pre)':<20} "
        f"{p['kd_pre']*100:>13.2f}% {d['kd_pre']*100:>13.2f}% "
        f"{(d['kd_pre']-p['kd_pre'])*100:>11.2f}pp"
    )
    print(
        f"    {'WACC':<20} "
        f"{p['wacc']*100:>13.2f}% {d['wacc']*100:>13.2f}% "
        f"{(d['wacc']-p['wacc'])*100:>11.2f}pp"
    )
    print(
        f"    {'DCF value (norm)':<20} "
        f"{p['value']:>14.2f} {d['value']:>14.2f} "
        f"{result['deviation_pct']:>+11.2f}%"
    )


def render_markdown(results, prod, dam):
    now = datetime.now(timezone.utc).isoformat()
    md = []
    md.append("# Parameter Sensitivity Test - Faz B1 Adim 3")
    md.append("")
    md.append(f"**Rapor tarihi (UTC):** {now}")
    md.append("**Production source:** apps/api/dcf_engine_v4/cost_of_capital.py (Adim 2C okundu)")
    md.append("**Damodaran source:** apps/api/data/damodaran/2026_05_09/parameters.json")
    md.append("")
    md.append("## Parametre Snapshot")
    md.append("")
    md.append("| Parametre | Production | Damodaran | Delta |")
    md.append("|-----------|------------|-----------|-------|")
    md.append(
        f"| RF | {prod['rf']*100:.2f}% | {dam['rf']*100:.2f}% | "
        f"{(dam['rf']-prod['rf'])*100:+.2f}pp |"
    )
    md.append(
        f"| Mature ERP | {prod['mature_erp']*100:.2f}% | "
        f"{dam['mature_erp']*100:.2f}% | "
        f"{(dam['mature_erp']-prod['mature_erp'])*100:+.2f}pp |"
    )
    md.append(
        f"| Turkey CRP | {prod['turkey_crp']*100:.2f}% | "
        f"{dam['turkey_crp']*100:.2f}% | "
        f"{(dam['turkey_crp']-prod['turkey_crp'])*100:+.2f}pp |"
    )
    md.append(
        f"| Turkey Sovereign Spread | "
        f"{prod['turkey_sovereign_spread']*100:.2f}% | "
        f"{dam['turkey_sovereign_spread']*100:.2f}% | "
        f"{(dam['turkey_sovereign_spread']-prod['turkey_sovereign_spread'])*100:+.2f}pp |"
    )
    md.append("")
    md.append("## Profil Bazli DCF Sapmalari")
    md.append("")

    for r in results:
        p = r["prod"]
        d = r["dam"]
        md.append(f"### {r['name']}")
        md.append("")
        md.append(f"- Profile key: `{r['key']}`")
        md.append(f"- Beta levered: {r['beta_levered']:.4f}")
        md.append("")
        md.append("| Metric | Production | Damodaran | Delta |")
        md.append("|--------|------------|-----------|-------|")
        md.append(
            f"| Cost of Equity | {p['ke']*100:.2f}% | "
            f"{d['ke']*100:.2f}% | "
            f"{(d['ke']-p['ke'])*100:+.2f}pp |"
        )
        md.append(
            f"| Cost of Debt (pre-tax) | {p['kd_pre']*100:.2f}% | "
            f"{d['kd_pre']*100:.2f}% | "
            f"{(d['kd_pre']-p['kd_pre'])*100:+.2f}pp |"
        )
        md.append(
            f"| WACC | {p['wacc']*100:.2f}% | "
            f"{d['wacc']*100:.2f}% | "
            f"{(d['wacc']-p['wacc'])*100:+.2f}pp |"
        )
        md.append(
            f"| DCF value (normalized) | {p['value']:.2f} | "
            f"{d['value']:.2f} | "
            f"**{r['deviation_pct']:+.2f}%** |"
        )
        md.append("")

    avg_dev = sum(r["deviation_pct"] for r in results) / len(results)
    md.append("## Ozet")
    md.append("")
    md.append(f"- Profil sayisi: {len(results)}")
    md.append(
        f"- Ortalama DCF sapma: **{avg_dev:+.2f}%**"
    )
    md.append("")
    md.append("## Karar Noktasi (audit_decision §3.4)")
    md.append("")
    if abs(avg_dev) < 5:
        md.append(
            "- **< %5:** Production muhtemelen zaten guncel. "
            "Faz B2'ye don, sadece spec PDF guncelle."
        )
        md.append("- Adim 5 (TUPRS shadow) GEREKMEZ.")
    elif abs(avg_dev) <= 25:
        md.append(
            "- **%5-25 (BEKLENEN):** Audit hipotezi teyit. "
            "Adim 5'e gec (TUPRS shadow hesap)."
        )
        md.append("- Anchor 187.10 INTACT, sadece shadow run.")
    else:
        md.append(
            "- **> %25:** STOP. Sapma cok yuksek, beta veya lambda "
            "hesabinda bug var. Audit derinlestir."
        )
    md.append("")
    md.append("---")
    md.append("")
    md.append(
        "*Read-only test. cost_of_capital.py MODIFY EDILMEDI. "
        "TUPRS test edilmedi (anchor riski).*"
    )
    return "\n".join(md) + "\n"


def main() -> int:
    print("=" * 60)
    print("Parameter Sensitivity Test - Faz B1 Adim 3")
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
    print(f"\n[2] Parametre snapshot:")
    print(
        f"    RF:                  prod={PRODUCTION['rf']*100:.2f}% "
        f"dam={DAMODARAN['rf']*100:.2f}%"
    )
    print(
        f"    Mature ERP:          prod={PRODUCTION['mature_erp']*100:.2f}% "
        f"dam={DAMODARAN['mature_erp']*100:.2f}%"
    )
    print(
        f"    Turkey CRP:          prod={PRODUCTION['turkey_crp']*100:.2f}% "
        f"dam={DAMODARAN['turkey_crp']*100:.2f}%"
    )
    print(
        f"    Turkey Sov Spread:   "
        f"prod={PRODUCTION['turkey_sovereign_spread']*100:.2f}% "
        f"dam={DAMODARAN['turkey_sovereign_spread']*100:.2f}%"
    )

    print(f"\n[3] Profil bazli sensitivity testleri...")
    results = []
    for key, profile in PROFILES.items():
        r = run_profile(key, profile, PRODUCTION, DAMODARAN)
        render_console(r)
        results.append(r)

    print(f"\n[4] Markdown rapor uretiliyor...")
    md = render_markdown(results, PRODUCTION, DAMODARAN)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "sensitivity_test_2026_05_09.md"
    report_path.write_text(md, encoding="utf-8")
    print(f"    Rapor: {report_path}")

    avg_dev = sum(r["deviation_pct"] for r in results) / len(results)
    print("\n" + "=" * 60)
    print(f"ORTALAMA SAPMA: {avg_dev:+.2f}%")
    print("=" * 60)

    if abs(avg_dev) < 5:
        print("KARAR: Faz B2'ye don (production zaten guncel?)")
        return 2
    elif abs(avg_dev) <= 25:
        print("KARAR: BEKLENEN ARALIK. Adim 5 (TUPRS shadow) onayla.")
        return 0
    else:
        print("KARAR: STOP. Sapma > %25, audit derinlestir.")
        return 3


if __name__ == "__main__":
    sys.exit(main())
