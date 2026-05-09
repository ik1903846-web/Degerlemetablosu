#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Damodaran Audit Log - Session 5.5a
====================================

Append-only JSONL log of every workflow run outcome.
Long-term audit trail for ADR-040 v2 monitoring.

Each line = 1 run record:
  {
    "timestamp_utc": "2026-05-09T20:30:00+00:00",
    "run_id": "25611272304",
    "run_url": "https://github.com/.../actions/runs/...",
    "conclusion": "success",
    "hash_check": {"changed": 3, "errors": 0},
    "regen_decision": {"reason": "...", "action": "..."},
    "issue_created": false,
    "issue_number": null,
    "vintage_detected": null,
    "notes": []
  }

Log path: apps/api/data/damodaran/_fetch_log.jsonl
.gitignore: zaten _fetch_log.jsonl ignore (Session 5.2'de eklendi)
Cache: state cache'e dahil (5.5b artifact)

Usage:
    python -m apps.api.data_layer.damodaran_audit_log \\
        --run-id 25611272304 \\
        --decision regen_decision.json \\
        --hash-output check_output.txt \\
        --conclusion success
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = (
    Path(__file__).resolve().parents[3]
    / "apps" / "api" / "data" / "damodaran" / "_fetch_log.jsonl"
)


@dataclass
class HashCheckSummary:
    changed: int = 0
    errors: int = 0
    total: int = 0


@dataclass
class RegenDecisionSummary:
    reason: str = "unknown"
    action: str = "unknown"
    hash_changed_urls: list[str] = field(default_factory=list)
    cost_of_capital_changed: bool = False


@dataclass
class RunRecord:
    timestamp_utc: str
    run_id: Optional[str]
    run_url: Optional[str]
    conclusion: str  # success | failure | partial
    trigger: str     # schedule | workflow_dispatch | unknown
    hash_check: HashCheckSummary
    regen_decision: RegenDecisionSummary
    issue_created: bool = False
    issue_number: Optional[int] = None
    vintage_detected: Optional[str] = None
    notes: list[str] = field(default_factory=list)


def parse_hash_output(text: str) -> HashCheckSummary:
    """check_output.txt'den 'Changed: N' / 'Error: N' parse."""
    summary = HashCheckSummary()
    for line in text.splitlines():
        m_changed = re.search(r"Changed:\s+(\d+)", line)
        if m_changed:
            summary.changed = int(m_changed.group(1))
        m_error = re.search(r"Error:\s+(\d+)", line)
        if m_error:
            summary.errors = int(m_error.group(1))
        m_total = re.search(r"Toplam URL:\s+(\d+)", line)
        if m_total:
            summary.total = int(m_total.group(1))
    return summary


def parse_decision_json(path: Path) -> RegenDecisionSummary:
    """regen_decision.json'dan dataclass parse."""
    if not path.exists():
        return RegenDecisionSummary()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return RegenDecisionSummary(
            reason=data.get("reason", "unknown"),
            action=data.get("action", "unknown"),
            hash_changed_urls=data.get("hash_changed_urls", []),
            cost_of_capital_changed=data.get("cost_of_capital_changed", False),
        )
    except Exception as e:
        logger.error(f"decision parse fail: {e}")
        return RegenDecisionSummary()


def append_record(record: RunRecord, log_path: Path = DEFAULT_LOG_PATH) -> None:
    """JSONL'e append (atomic write)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # asdict serialization
    line = json.dumps(asdict(record), ensure_ascii=False, sort_keys=False)

    # Append-only mode
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")

    logger.info(f"Record appended: {log_path}")


def read_recent(log_path: Path = DEFAULT_LOG_PATH,
                limit: int = 10) -> list[dict]:
    """Son N satırı oku."""
    if not log_path.exists():
        return []
    try:
        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        recent = lines[-limit:] if len(lines) > limit else lines
        return [json.loads(l) for l in recent if l.strip()]
    except Exception as e:
        logger.error(f"read_recent fail: {e}")
        return []


def cli_record(args: argparse.Namespace) -> int:
    """Workflow CLI: tek run kaydet."""
    now_utc = datetime.now(timezone.utc).isoformat()

    # Hash check parse
    hash_summary = HashCheckSummary()
    if args.hash_output and Path(args.hash_output).exists():
        try:
            text = Path(args.hash_output).read_text(encoding="utf-8")
            hash_summary = parse_hash_output(text)
        except Exception as e:
            logger.warning(f"hash output parse fail: {e}")

    # Decision parse
    decision_summary = RegenDecisionSummary()
    if args.decision and Path(args.decision).exists():
        decision_summary = parse_decision_json(Path(args.decision))

    # Build record
    record = RunRecord(
        timestamp_utc=now_utc,
        run_id=args.run_id,
        run_url=args.run_url,
        conclusion=args.conclusion or "success",
        trigger=args.trigger or "unknown",
        hash_check=hash_summary,
        regen_decision=decision_summary,
        issue_created=args.issue_created,
        issue_number=args.issue_number,
        vintage_detected=args.vintage,
        notes=args.notes or [],
    )

    log_path = Path(args.log) if args.log else DEFAULT_LOG_PATH
    append_record(record, log_path)

    print(f"Record appended to: {log_path}")
    print(f"Total lines: {len(log_path.read_text(encoding='utf-8').splitlines())}")
    return 0


def cli_recent(args: argparse.Namespace) -> int:
    """Son N kayıt göster."""
    log_path = Path(args.log) if args.log else DEFAULT_LOG_PATH
    records = read_recent(log_path, limit=args.limit)

    print(f"Recent {len(records)} records from {log_path}:")
    print("-" * 60)
    for r in records:
        ts = r.get("timestamp_utc", "?")
        ru = r.get("run_id", "?")
        co = r.get("conclusion", "?")
        ac = r.get("regen_decision", {}).get("action", "?")
        ch = r.get("hash_check", {}).get("changed", "?")
        print(f"  {ts}  run={ru}  conclusion={co}  changed={ch}  action={ac}")
    return 0


def _smoke_test() -> int:
    """Standalone smoke test: 3 record append + read back."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s | %(name)s | %(message)s")

    test_log = Path("/tmp/_test_audit_log.jsonl") \
               if os.name != "nt" \
               else Path(os.environ.get("TEMP", ".")) / "_test_audit_log.jsonl"

    if test_log.exists():
        test_log.unlink()

    print("=" * 60)
    print("Audit Log - Smoke Test")
    print("=" * 60)
    print(f"Test log: {test_log}")
    print()

    # Record 1: success skip
    r1 = RunRecord(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        run_id="test_001",
        run_url="https://example.com/runs/001",
        conclusion="success",
        trigger="workflow_dispatch",
        hash_check=HashCheckSummary(changed=0, errors=0, total=3),
        regen_decision=RegenDecisionSummary(reason="none", action="skip"),
    )
    append_record(r1, test_log)

    # Record 2: alert
    r2 = RunRecord(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        run_id="test_002",
        run_url="https://example.com/runs/002",
        conclusion="success",
        trigger="schedule",
        hash_check=HashCheckSummary(changed=3, errors=0, total=3),
        regen_decision=RegenDecisionSummary(
            reason="hash_changed_only",
            action="alert_manual_update",
            hash_changed_urls=["ctryprem", "ERPbymonth", "betaemerg"],
        ),
        issue_created=True,
        issue_number=42,
        vintage_detected="2026-02",
    )
    append_record(r2, test_log)

    # Record 3: regen
    r3 = RunRecord(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        run_id="test_003",
        run_url="https://example.com/runs/003",
        conclusion="success",
        trigger="workflow_dispatch",
        hash_check=HashCheckSummary(changed=0, errors=0, total=3),
        regen_decision=RegenDecisionSummary(
            reason="cost_of_capital_only",
            action="regen_json",
            cost_of_capital_changed=True,
        ),
        notes=["Adim 7 sonrasi cost_of_capital update detected"],
    )
    append_record(r3, test_log)

    print(f"\n3 records appended\n")

    # Read back
    records = read_recent(test_log, limit=10)
    print(f"Read back: {len(records)} records")
    print()
    for i, r in enumerate(records, 1):
        print(f"[{i}] {r['run_id']}: {r['regen_decision']['action']} "
              f"(changed={r['hash_check']['changed']}, "
              f"issue={r.get('issue_created', False)})")

    # Cleanup
    test_log.unlink()
    print(f"\nTest log temizlendi: {test_log}")

    print("=" * 60)
    print("Smoke test PASS")
    print("=" * 60)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Damodaran audit log (JSONL append-only)"
    )
    sub = parser.add_subparsers(dest="cmd")

    # record subcommand
    p_rec = sub.add_parser("record", help="Append run record")
    p_rec.add_argument("--run-id", help="GitHub Actions run ID")
    p_rec.add_argument("--run-url", help="Workflow run URL")
    p_rec.add_argument("--conclusion", default="success",
                       help="success | failure | partial")
    p_rec.add_argument("--trigger", default="unknown",
                       help="schedule | workflow_dispatch")
    p_rec.add_argument("--hash-output", help="check_output.txt path")
    p_rec.add_argument("--decision", help="regen_decision.json path")
    p_rec.add_argument("--issue-created", action="store_true")
    p_rec.add_argument("--issue-number", type=int)
    p_rec.add_argument("--vintage", help="Detected vintage (YYYY-MM)")
    p_rec.add_argument("--notes", nargs="*", help="Additional notes")
    p_rec.add_argument("--log", help="Custom log path")

    # recent subcommand
    p_rec2 = sub.add_parser("recent", help="Show recent records")
    p_rec2.add_argument("--limit", type=int, default=10)
    p_rec2.add_argument("--log", help="Custom log path")

    # smoke-test subcommand
    sub.add_parser("smoke-test", help="Run smoke test")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s | %(name)s | %(message)s")

    if args.cmd == "record":
        return cli_record(args)
    elif args.cmd == "recent":
        return cli_recent(args)
    elif args.cmd == "smoke-test" or args.cmd is None:
        return _smoke_test()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
