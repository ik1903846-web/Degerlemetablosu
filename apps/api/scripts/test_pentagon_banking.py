#!/usr/bin/env python
"""
Banking-specific Pentagon scoring + sleeve test — Faz 6.5 (e).

7 TEST:
  1) GARAN re-score (CORE banking_intrinsic ★)
  2) AKBNK re-score (CORE banking_intrinsic)
  3) YKBNK re-score (CORE banking_intrinsic, low upside edge)
  4) ISCTR re-score (CORE banking_intrinsic, borderline)
  5) HALKB re-score (YÜKSEK KAZANÇ deep_value devam)
  6) TUPRS regression (industrial pipeline INTACT)
  7) KCHOL/SAHOL backward-compat (UNKNOWN/holding fallback korunur)
"""

import sys
import io
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio.pentagon_scoring import score_from_json_dict, score_ticker
from portfolio.sleeve_assignment import assign_sleeve, Sleeve


def _latest_batch_json():
    outputs = Path(__file__).parent.parent / "outputs"
    files = sorted(outputs.glob("bist_batch_LIVE_*.json"))
    if not files:
        raise FileNotFoundError("No bist_batch_LIVE_*.json")
    return json.loads(files[-1].read_text(encoding="utf-8"))


def _get_report(data, ticker):
    for r in data["reports"]:
        if r["ticker"] == ticker:
            return r
    return None


def _check_banking(ticker, expected_sleeve, expected_sub, comp_min, comp_max,
                   data, score_map):
    print(f"\n{'='*70}")
    print(f"TEST — {ticker} (banking)")
    print(f"{'='*70}")

    r = _get_report(data, ticker)
    if r is None:
        print(f"  [FAIL] Report YOK")
        return False

    s = score_map.get(ticker)
    if s is None:
        print(f"  [FAIL] Score YOK")
        return False

    print(f"  Stage:     {s.lifecycle_stage}")
    print(f"  V={s.value:.1f}  G={s.growth:.1f}  Q={s.quality:.1f}  "
          f"M={s.momentum:.1f}  R={s.risk:.1f}")
    print(f"  Composite: {s.composite:.2f}")
    print(f"  Reasoning:")
    for line in s.reasoning:
        print(f"    - {line}")

    a = assign_sleeve(r, s)
    print(f"\n  Sleeve:    {a.sleeve.value}")
    print(f"  Sub:       {a.sub_category or '-'}")
    print(f"  Reasoning: {a.reasoning[0] if a.reasoning else '-'}")

    checks = [
        ("Stage = BANKING", s.lifecycle_stage, "BANKING"),
        ("Sleeve match", a.sleeve, expected_sleeve),
        ("Sub-category match", a.sub_category, expected_sub),
        (f"Composite in [{comp_min},{comp_max}]",
         comp_min <= s.composite <= comp_max, True),
    ]
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: actual={actual}, expected={expected}")
        if not ok:
            all_pass = False
    return all_pass


def _check_industrial(ticker, expected_stage, expected_sleeve_in,
                       comp_min, comp_max, data, score_map):
    print(f"\n{'='*70}")
    print(f"TEST — {ticker} (industrial regression)")
    print(f"{'='*70}")

    r = _get_report(data, ticker)
    if r is None:
        print(f"  [FAIL] Report YOK")
        return False

    s = score_map.get(ticker)
    if s is None:
        print(f"  [FAIL] Score YOK")
        return False

    print(f"  Stage:     {s.lifecycle_stage}")
    print(f"  V={s.value:.1f}  G={s.growth:.1f}  Q={s.quality:.1f}  "
          f"M={s.momentum:.1f}  R={s.risk:.1f}")
    print(f"  Composite: {s.composite:.2f}")

    a = assign_sleeve(r, s)
    print(f"  Sleeve:    {a.sleeve.value} ({a.sub_category or '-'})")

    checks = [
        ("Stage matches", s.lifecycle_stage, expected_stage),
        (f"Sleeve in {expected_sleeve_in}",
         a.sleeve.value in expected_sleeve_in, True),
        (f"Composite in [{comp_min},{comp_max}]",
         comp_min <= s.composite <= comp_max, True),
    ]
    all_pass = True
    for name, actual, expected in checks:
        ok = actual == expected
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}: actual={actual}, expected={expected}")
        if not ok:
            all_pass = False
    return all_pass


def main() -> int:
    print("\n" + "#" * 80)
    print("# Pentagon Banking + Sleeve TEST (Faz 6.5 e — Damodaran Lesson #6)")
    print("#" * 80)

    data = _latest_batch_json()
    scores = score_from_json_dict(data)
    score_map = {s.ticker: s for s in scores}

    results = []
    # Banking 5 ticker
    results.append(("GARAN CORE banking_intrinsic",
                    _check_banking("GARAN", Sleeve.CORE, "banking_intrinsic",
                                    70, 85, data, score_map)))
    results.append(("AKBNK CORE banking_intrinsic",
                    _check_banking("AKBNK", Sleeve.CORE, "banking_intrinsic",
                                    60, 80, data, score_map)))
    results.append(("YKBNK CORE banking_intrinsic",
                    _check_banking("YKBNK", Sleeve.CORE, "banking_intrinsic",
                                    55, 75, data, score_map)))
    results.append(("ISCTR CORE banking_intrinsic",
                    _check_banking("ISCTR", Sleeve.CORE, "banking_intrinsic",
                                    50, 70, data, score_map)))
    results.append(("HALKB YÜKSEK_KAZANC deep_value",
                    _check_banking("HALKB", Sleeve.YUKSEK_KAZANC, "deep_value",
                                    55, 80, data, score_map)))

    # Industrial regression
    results.append(("TUPRS industrial regression",
                    _check_industrial("TUPRS", "MATURE_STABLE",
                                       ["skip", "core"], 30, 60,
                                       data, score_map)))
    # KCHOL UNKNOWN/holding
    results.append(("KCHOL UNKNOWN/holding fallback",
                    _check_industrial("KCHOL", "UNKNOWN",
                                       ["yuksek_kazanc", "skip"], 40, 70,
                                       data, score_map)))

    print("\n" + "#" * 80)
    print("# ÖZET")
    print("#" * 80)
    for name, ok in results:
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name}")

    all_pass = all(ok for _, ok in results)
    print(f"\n  Toplam: {sum(1 for _, ok in results if ok)}/{len(results)}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
