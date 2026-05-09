#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production vs Damodaran Diff - Faz B1 Adim 2C
=============================================

cost_of_capital.py'deki hardcoded constants'i parametreler.json
ile karsilastir. Diff raporunu reports/ altinda markdown olarak
uret.

READ-ONLY: cost_of_capital.py modify edilmez.
"""

import ast
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
COST_OF_CAPITAL_PATH = (
    REPO_ROOT / "apps" / "api" / "dcf_engine_v4" / "cost_of_capital.py"
)
PARAMS_PATH = (
    REPO_ROOT / "apps" / "api" / "data" / "damodaran"
    / "2026_05_09" / "parameters.json"
)
REPORTS_DIR = REPO_ROOT / "reports"


# Aranacak constant isimleri (case-insensitive eslesme)
CONSTANT_MAP = {
    # cost_of_capital.py constant adi : parameters.json yolu
    "RF_USD_10Y": ("rf_usd_estimate", "numeric"),
    "MATURE_ERP_US": ("mature_erp", "numeric"),
    "TURKEY_CRP": ("turkey.crp", "numeric"),
    "TURKEY_SOVEREIGN_SPREAD": (
        "turkey.default_spread", "numeric"
    ),
    "TURKEY_DEFAULT_SPREAD": (
        "turkey.default_spread", "numeric"
    ),
    "TURKEY_RATING": ("turkey.rating", "exact"),
    "US_DEFAULT_SPREAD": ("us.default_spread", "numeric"),
    "US_RATING": ("us.rating", "exact"),
}


def parse_constants_from_file(path: Path) -> dict:
    """AST ile module-level constant assignments oku."""
    if not path.exists():
        raise FileNotFoundError(
            f"cost_of_capital.py bulunamadi: {path}"
        )

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    constants = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if name.isupper() or name in CONSTANT_MAP:
                        try:
                            value = ast.literal_eval(node.value)
                            constants[name] = {
                                "value": value,
                                "lineno": node.lineno,
                            }
                        except (ValueError, SyntaxError):
                            constants[name] = {
                                "value": "<non-literal>",
                                "lineno": node.lineno,
                            }

    return constants


def get_param_value(params: dict, dotted_path: str):
    """parameters.json'dan dotted path ile deger oku."""
    keys = dotted_path.split(".")
    val = params
    for k in keys:
        if isinstance(val, dict) and k in val:
            val = val[k]
        else:
            return None
    return val


def compare(prod: dict, params: dict) -> list[dict]:
    rows = []
    TOLERANCE = 0.0005

    for const_name, (param_path, mode) in CONSTANT_MAP.items():
        prod_entry = prod.get(const_name)
        param_val = get_param_value(params, param_path)

        if prod_entry is None:
            rows.append({
                "constant": const_name,
                "lineno": None,
                "production": "NOT FOUND",
                "damodaran": param_val,
                "delta": None,
                "status": "NOT_FOUND",
            })
            continue

        prod_val = prod_entry["value"]
        lineno = prod_entry["lineno"]

        if param_val is None:
            rows.append({
                "constant": const_name,
                "lineno": lineno,
                "production": prod_val,
                "damodaran": "NOT IN PARAMS",
                "delta": None,
                "status": "NO_PARAM",
            })
            continue

        if mode == "exact":
            ok = str(prod_val).strip() == str(param_val).strip()
            rows.append({
                "constant": const_name,
                "lineno": lineno,
                "production": prod_val,
                "damodaran": param_val,
                "delta": "exact",
                "status": "MATCH" if ok else "MISMATCH",
            })
        elif mode == "numeric":
            try:
                p_num = float(prod_val)
                d_num = float(param_val)
                delta = d_num - p_num
                ok = abs(delta) <= TOLERANCE
                rows.append({
                    "constant": const_name,
                    "lineno": lineno,
                    "production": p_num,
                    "damodaran": d_num,
                    "delta": delta,
                    "status": "MATCH" if ok else "MISMATCH",
                })
            except (TypeError, ValueError):
                rows.append({
                    "constant": const_name,
                    "lineno": lineno,
                    "production": prod_val,
                    "damodaran": param_val,
                    "delta": None,
                    "status": "PARSE_FAIL",
                })

    return rows


def render_markdown(rows: list[dict]) -> str:
    now = datetime.now(timezone.utc).isoformat()

    md = []
    md.append("# Production vs Damodaran Parameter Diff")
    md.append("")
    md.append(f"**Rapor tarihi (UTC):** {now}")
    md.append(f"**Audit faz:** Faz B1 Adim 2C")
    md.append(
        f"**Production source:** apps/api/dcf_engine_v4/cost_of_capital.py"
    )
    md.append(
        f"**Damodaran source:** apps/api/data/damodaran/"
        f"2026_05_09/parameters.json"
    )
    md.append("")
    md.append("## Karsilastirma")
    md.append("")
    md.append(
        "| Constant | Line | Production | Damodaran (2026-05-09) | "
        "Delta | Status |"
    )
    md.append(
        "|----------|------|------------|------------------------|"
        "-------|--------|"
    )

    for r in rows:
        line = r["lineno"] if r["lineno"] else "—"
        prod = r["production"]
        dam = r["damodaran"]
        delta = r["delta"]
        status = r["status"]

        if isinstance(prod, float):
            prod_str = f"{prod:.4f}"
        else:
            prod_str = str(prod)

        if isinstance(dam, float):
            dam_str = f"{dam:.4f}"
        else:
            dam_str = str(dam)

        if isinstance(delta, float):
            delta_str = f"{delta:+.4f} ({delta*100:+.2f} pp)"
        else:
            delta_str = str(delta) if delta else "—"

        md.append(
            f"| `{r['constant']}` | {line} | {prod_str} | "
            f"{dam_str} | {delta_str} | **{status}** |"
        )

    md.append("")

    mismatches = [r for r in rows if r["status"] == "MISMATCH"]
    not_found = [r for r in rows if r["status"] == "NOT_FOUND"]

    md.append("## Ozet")
    md.append("")
    md.append(f"- Toplam kontrol: {len(rows)}")
    md.append(
        f"- MATCH: {sum(1 for r in rows if r['status'] == 'MATCH')}"
    )
    md.append(f"- MISMATCH: {len(mismatches)}")
    md.append(f"- NOT_FOUND: {len(not_found)}")
    md.append("")

    if mismatches:
        md.append("## Kritik Sapmalar (MISMATCH)")
        md.append("")
        for r in mismatches:
            if isinstance(r["delta"], float):
                pp = r["delta"] * 100
                md.append(
                    f"- **{r['constant']}** (line {r['lineno']}): "
                    f"production={r['production']}, "
                    f"damodaran={r['damodaran']}, "
                    f"delta={pp:+.2f} pp"
                )
            else:
                md.append(
                    f"- **{r['constant']}** (line {r['lineno']}): "
                    f"production={r['production']!r}, "
                    f"damodaran={r['damodaran']!r}"
                )
        md.append("")

    md.append("## Sonraki Adim")
    md.append("")
    if mismatches:
        md.append(
            "- **Adim 3:** TTRAK uzerinde test sirketi "
            "dogrulamasi (anchor INTACT)"
        )
        md.append(
            "- **Adim 7:** cost_of_capital.py constants update "
            "(atomic, audit_decision_v4.md kurali)"
        )
        md.append(
            "- **Adim 8:** ADR-040 post-mortem - neden Subat "
            "2026 update otomatik fetch'lenmedi?"
        )
    else:
        md.append(
            "- Production zaten guncel. Faz B2'ye gec, sadece "
            "spec PDF guncelle."
        )

    md.append("")
    md.append("---")
    md.append("")
    md.append(
        "*Bu rapor read-only diff'ten uretildi. "
        "cost_of_capital.py MODIFY EDILMEDI.*"
    )

    return "\n".join(md) + "\n"


def main() -> int:
    print("=" * 60)
    print("Production vs Damodaran Diff - Faz B1 Adim 2C")
    print("=" * 60)

    print(f"\n[1] cost_of_capital.py read-only parse...")
    print(f"    Path: {COST_OF_CAPITAL_PATH}")
    try:
        prod_constants = parse_constants_from_file(COST_OF_CAPITAL_PATH)
    except Exception as e:
        print(f"    HATA: {e}")
        return 1
    print(f"    Bulunan {len(prod_constants)} module-level constant")
    for name, info in prod_constants.items():
        print(f"      line {info['lineno']:3d}: {name} = {info['value']!r}")

    print(f"\n[2] parameters.json yukleniyor...")
    if not PARAMS_PATH.exists():
        print(f"    HATA: {PARAMS_PATH} bulunamadi")
        return 1
    params = json.loads(PARAMS_PATH.read_text(encoding="utf-8"))
    print(f"    fetch_date: {params.get('fetch_date')}")

    print(f"\n[3] Karsilastirma...")
    rows = compare(prod_constants, params)

    print(f"\n[4] Markdown rapor uretiliyor...")
    md = render_markdown(rows)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "parameter_diff_2026_05_09.md"
    report_path.write_text(md, encoding="utf-8")
    print(f"    Rapor: {report_path}")

    print("\n" + "=" * 60)
    mismatches = [r for r in rows if r["status"] == "MISMATCH"]
    not_found = [r for r in rows if r["status"] == "NOT_FOUND"]

    print(f"  MATCH: {sum(1 for r in rows if r['status'] == 'MATCH')}")
    print(f"  MISMATCH: {len(mismatches)}")
    print(f"  NOT_FOUND: {len(not_found)}")

    if mismatches:
        print("\n  KRITIK SAPMALAR:")
        for r in mismatches:
            if isinstance(r["delta"], float):
                pp = r["delta"] * 100
                print(
                    f"    - {r['constant']} (line {r['lineno']}): "
                    f"prod={r['production']}, dam={r['damodaran']}, "
                    f"delta={pp:+.2f} pp"
                )

    print("=" * 60)
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
