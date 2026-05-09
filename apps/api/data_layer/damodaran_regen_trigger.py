#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Damodaran Regen Trigger - Session 5.4a
=======================================

Hash state + cost_of_capital.py durum karsilastirmasiyla
"regen gerek mi?" karari verir. H5 problem'in kalici cozumu.

Input:
  - HashState (Session 5.2'den)
  - cost_of_capital.py constants snapshot

Output:
  - RegenDecision (reason + action)

Iki ayri trigger durumu:
  1. Damodaran update var (hash changed) ama
     cost_of_capital.py guncel degil:
     -> ALERT (manuel audit gerek)

  2. cost_of_capital.py degisti (hash unchanged):
     -> REGEN (JSON snapshot stale, orchestrator_v4 calistir)

YASAK:
  Bu modul SADECE karar verir. Action execution
  damodaran_daily_check.yml workflow'unda yapilir.
  cost_of_capital.py MODIFY ETMEZ (audit chain).
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class RegenReason(str, Enum):
    NONE = "none"
    HASH_CHANGED_ONLY = "hash_changed_only"
    COST_OF_CAPITAL_ONLY = "cost_of_capital_only"
    BOTH_CHANGED = "both_changed"
    FORCE = "force"


class RegenAction(str, Enum):
    SKIP = "skip"
    REGEN_JSON = "regen_json"
    ALERT_MANUAL_UPDATE = "alert_manual_update"
    REGEN_AND_ALERT = "regen_and_alert"


# Tracked constants (Adim 2C'den)
TRACKED_CONSTANTS = (
    "RF_USD_10Y",
    "MATURE_ERP_US",
    "TURKEY_CRP",
    "TURKEY_TAX_RATE",
    "TURKEY_SOVEREIGN_SPREAD",
)


@dataclass
class CostOfCapitalSnapshot:
    """cost_of_capital.py'nin AST-parsed durumu."""
    file_hash: str          # SHA256 dosya
    constants: dict[str, float]  # tracked constants degerleri
    last_modified_utc: str

    @classmethod
    def from_file(cls, path: Path) -> Optional["CostOfCapitalSnapshot"]:
        if not path.exists():
            return None
        try:
            content = path.read_bytes()
            file_hash = hashlib.sha256(content).hexdigest()
            tree = ast.parse(content.decode("utf-8"))
            constants = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and \
                           target.id in TRACKED_CONSTANTS:
                            if isinstance(node.value, ast.Constant) and \
                               isinstance(node.value.value, (int, float)):
                                constants[target.id] = float(node.value.value)
            mtime = datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
            return cls(
                file_hash=file_hash,
                constants=constants,
                last_modified_utc=mtime,
            )
        except Exception as e:
            logger.error(f"cost_of_capital snapshot fail: {e}")
            return None


@dataclass
class RegenDecision:
    """Regen karari."""
    reason: str  # RegenReason value
    action: str  # RegenAction value
    hash_changed_urls: list[str]
    cost_of_capital_changed: bool
    cost_of_capital_diff: dict[str, tuple[float, float]]  # name -> (old, new)
    timestamp_utc: str
    notes: list[str]


def decide_regen(
    hash_state_path: Path,
    cost_of_capital_path: Path,
    state_snapshot_path: Path,
    force: bool = False,
) -> RegenDecision:
    """Karar logic.

    Args:
        hash_state_path: damodaran/_hash_state.json
        cost_of_capital_path: dcf_engine_v4/cost_of_capital.py
        state_snapshot_path: ayri snapshot dosyasi (bu modulun)
                             apps/api/data/damodaran/_regen_state.json
        force: True ise her zaman REGEN_JSON

    Returns:
        RegenDecision
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    notes = []

    if force:
        return RegenDecision(
            reason=RegenReason.FORCE.value,
            action=RegenAction.REGEN_JSON.value,
            hash_changed_urls=[],
            cost_of_capital_changed=False,
            cost_of_capital_diff={},
            timestamp_utc=now_utc,
            notes=["Force flag, regen unconditional"],
        )

    # 1) Hash state degisikligi var mi?
    hash_changed_urls = []
    if hash_state_path.exists():
        try:
            hs_data = json.loads(hash_state_path.read_text(encoding="utf-8"))
            for name, urlstate in hs_data.get("urls", {}).items():
                # change_count > 0 ve last_check_utc == last_changed_utc
                # ise yeni bir change happened
                if urlstate.get("change_count", 0) > 0:
                    last_check = urlstate.get("last_check_utc")
                    last_change = urlstate.get("last_changed_utc")
                    if last_check and last_change and last_check == last_change:
                        hash_changed_urls.append(name)
        except Exception as e:
            notes.append(f"hash_state parse fail: {e}")
    else:
        notes.append("hash_state.json yok (workflow first run)")

    # 2) cost_of_capital.py degisikligi var mi?
    current = CostOfCapitalSnapshot.from_file(cost_of_capital_path)
    if current is None:
        notes.append("cost_of_capital.py okunamadi")
        return RegenDecision(
            reason=RegenReason.NONE.value,
            action=RegenAction.SKIP.value,
            hash_changed_urls=hash_changed_urls,
            cost_of_capital_changed=False,
            cost_of_capital_diff={},
            timestamp_utc=now_utc,
            notes=notes,
        )

    cost_changed = False
    cost_diff = {}
    if state_snapshot_path.exists():
        try:
            prev_data = json.loads(state_snapshot_path.read_text(encoding="utf-8"))
            prev_hash = prev_data.get("file_hash")
            if prev_hash and prev_hash != current.file_hash:
                cost_changed = True
                prev_consts = prev_data.get("constants", {})
                for name in TRACKED_CONSTANTS:
                    old = prev_consts.get(name)
                    new = current.constants.get(name)
                    if old != new:
                        cost_diff[name] = (old, new)
        except Exception as e:
            notes.append(f"prev snapshot parse fail: {e}")
    else:
        notes.append("snapshot yok, ilk run baseline")

    # 3) Karar matrisi
    if hash_changed_urls and cost_changed:
        reason = RegenReason.BOTH_CHANGED
        action = RegenAction.REGEN_AND_ALERT
    elif hash_changed_urls:
        reason = RegenReason.HASH_CHANGED_ONLY
        action = RegenAction.ALERT_MANUAL_UPDATE
    elif cost_changed:
        reason = RegenReason.COST_OF_CAPITAL_ONLY
        action = RegenAction.REGEN_JSON
    else:
        reason = RegenReason.NONE
        action = RegenAction.SKIP

    # 4) Snapshot guncelle (her zaman, baseline icin)
    try:
        state_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        state_snapshot_path.write_text(
            json.dumps({
                "file_hash": current.file_hash,
                "constants": current.constants,
                "last_modified_utc": current.last_modified_utc,
                "saved_utc": now_utc,
            }, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception as e:
        notes.append(f"snapshot save fail: {e}")

    return RegenDecision(
        reason=reason.value,
        action=action.value,
        hash_changed_urls=hash_changed_urls,
        cost_of_capital_changed=cost_changed,
        cost_of_capital_diff=cost_diff,
        timestamp_utc=now_utc,
        notes=notes,
    )


# ────────────────────────────────────────────────────────────────────
# Standalone smoke test
# ────────────────────────────────────────────────────────────────────

def _smoke_test() -> int:
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    repo_root = Path(__file__).resolve().parents[3]
    hash_state = repo_root / "apps" / "api" / "data" / "damodaran" / "_hash_state.json"
    cost_path = repo_root / "apps" / "api" / "dcf_engine_v4" / "cost_of_capital.py"
    snapshot = repo_root / "apps" / "api" / "data" / "damodaran" / "_regen_state.json"

    print("=" * 60)
    print("Damodaran Regen Trigger - Smoke Test")
    print("=" * 60)
    print(f"hash_state:    {hash_state.exists()}")
    print(f"cost_of_cap:   {cost_path.exists()}")
    print(f"snapshot:      {snapshot.exists()}")
    print()

    # Senaryo 1: ilk run (snapshot yok)
    print("[Senaryo 1] First run baseline")
    decision = decide_regen(hash_state, cost_path, snapshot)
    print(f"  reason: {decision.reason}")
    print(f"  action: {decision.action}")
    print(f"  notes:  {decision.notes}")
    print()

    # Senaryo 2: ikinci run (snapshot var, hicbir sey degismedi)
    print("[Senaryo 2] No-op run (snapshot var)")
    decision = decide_regen(hash_state, cost_path, snapshot)
    print(f"  reason: {decision.reason}")
    print(f"  action: {decision.action}")
    print(f"  hash_changed_urls: {decision.hash_changed_urls}")
    print(f"  cost_of_capital_changed: {decision.cost_of_capital_changed}")
    print()

    # Senaryo 3: force
    print("[Senaryo 3] Force flag")
    decision = decide_regen(hash_state, cost_path, snapshot, force=True)
    print(f"  reason: {decision.reason}")
    print(f"  action: {decision.action}")
    print()

    # Cleanup snapshot for fresh test next time
    if snapshot.exists():
        snapshot.unlink()
        print(f"Snapshot temizlendi: {snapshot}")

    print("=" * 60)
    print("Smoke test tamamlandi")
    print("=" * 60)
    return 0


def _cli_decide(output_path: Path) -> int:
    """Workflow CLI mode: karar ver, JSON dosyasina yaz."""
    repo_root = Path(__file__).resolve().parents[3]
    hash_state = repo_root / "apps" / "api" / "data" / "damodaran" / "_hash_state.json"
    cost_path = repo_root / "apps" / "api" / "dcf_engine_v4" / "cost_of_capital.py"
    snapshot = repo_root / "apps" / "api" / "data" / "damodaran" / "_regen_state.json"

    decision = decide_regen(hash_state, cost_path, snapshot)

    output_path.write_text(
        json.dumps(asdict(decision), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"reason={decision.reason}")
    print(f"action={decision.action}")
    print(f"hash_changed_count={len(decision.hash_changed_urls)}")
    print(f"cost_of_capital_changed={decision.cost_of_capital_changed}")
    print(f"output={output_path}")

    return 0


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Damodaran regen trigger - decision logic"
    )
    parser.add_argument(
        "--decide",
        action="store_true",
        help="CLI mode: karar ver, JSON output yaz",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("regen_decision.json"),
        help="Karar JSON output path (default: regen_decision.json)",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Smoke test calistir (3 senaryo)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    if args.decide:
        sys.exit(_cli_decide(args.output))
    else:
        sys.exit(_smoke_test())
