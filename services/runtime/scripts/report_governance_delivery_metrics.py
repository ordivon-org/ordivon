#!/usr/bin/env python3
"""Read-only EGB-2 governance delivery and trust-budget metrics.

This script reads local registries, ledgers, and receipts. It does not call the
network, run agents, mutate files, or authorize action.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_REGISTRY = ROOT / "docs" / "governance" / "document-registry.jsonl"
ARTIFACT_REGISTRY = ROOT / "docs" / "governance" / "artifact-registry.jsonl"
DEBT_LEDGER = ROOT / "docs" / "governance" / "verification-debt-ledger.jsonl"
MATURITY_LEDGER = ROOT / "docs" / "governance" / "checker-maturity-ledger.jsonl"
SOURCE_REGISTRY = ROOT / "docs" / "governance" / "external-benchmark-source-registry.jsonl"
RUNTIME_DIR = ROOT / "docs" / "runtime"


def _load_jsonl(path: Path) -> list[dict]:
    entries: list[dict] = []
    if not path.exists():
        return entries
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            entries.append(value)
    return entries


def _receipt_texts() -> list[str]:
    if not RUNTIME_DIR.exists():
        return []
    texts: list[str] = []
    for path in sorted(RUNTIME_DIR.rglob("*")):
        if path.suffix.lower() not in {".md", ".json"}:
            continue
        try:
            texts.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return texts


def _count_receipt_pattern(pattern: str) -> int:
    regex = re.compile(pattern, re.IGNORECASE)
    return sum(len(regex.findall(text)) for text in _receipt_texts())


def _open_debt_count() -> int:
    count = 0
    for entry in _load_jsonl(DEBT_LEDGER):
        if str(entry.get("status", "")).lower() not in {"closed", "resolved"}:
            count += 1
    return count


def _checker_shadow_count() -> int:
    return sum(1 for entry in _load_jsonl(MATURITY_LEDGER) if str(entry.get("maturity", "")).lower() == "shadow_tested")


def _stale_source_count(reference_date: date | None = None) -> int:
    reference_date = reference_date or date.today()
    stale = 0
    for entry in _load_jsonl(SOURCE_REGISTRY):
        try:
            last_checked = date.fromisoformat(str(entry.get("last_checked", "")))
            freshness_days = int(entry.get("freshness_days", 0))
        except (TypeError, ValueError):
            stale += 1
            continue
        if freshness_days <= 0 or (reference_date - last_checked).days > freshness_days:
            stale += 1
    return stale


def _registry_drift_count() -> int:
    drift = 0
    for registry in (DOC_REGISTRY, ARTIFACT_REGISTRY):
        for entry in _load_jsonl(registry):
            rel = entry.get("path")
            if not isinstance(rel, str) or not rel:
                drift += 1
                continue
            if not (ROOT / rel).exists():
                drift += 1
    return drift


def collect_metrics(reference_date: date | None = None) -> dict:
    missing_evidence_count = _count_receipt_pattern(r"\bmissing[_\s-]?evidence\b")
    degraded_count = _count_receipt_pattern(r"\bDEGRADED\b")
    blocked_count = _count_receipt_pattern(r"\bBLOCKED\b")
    metrics = {
        "missing_evidence_count": missing_evidence_count,
        "degraded_count": degraded_count,
        "blocked_count": blocked_count,
        "stale_source_count": _stale_source_count(reference_date),
        "registry_drift_count": _registry_drift_count(),
        "open_debt_count": _open_debt_count(),
        "checker_shadow_count": _checker_shadow_count(),
        "rework_placeholder": 0,
        "disclaimer": (
            "Read-only diagnostic metrics. Evidence only; not merge, release, "
            "deployment, publication, trading, policy, or external-action authorization."
        ),
    }
    metrics["interpretation"] = interpret_metrics(metrics)
    return metrics


def interpret_metrics(metrics: dict) -> dict:
    """Split raw trust-budget counters into operating categories.

    The raw BLOCKED/DEGRADED counts are mostly historical receipt mentions and
    preserved fixtures. Registry drift and stale external sources are current
    blocker candidates because they describe live governance substrate health.
    """
    current_blockers = int(metrics.get("registry_drift_count", 0)) + int(metrics.get("stale_source_count", 0))
    return {
        "current_blocker_count": current_blockers,
        "historical_sample_indicators": {
            "blocked_mentions": int(metrics.get("blocked_count", 0)),
            "degraded_mentions": int(metrics.get("degraded_count", 0)),
            "missing_evidence_mentions": int(metrics.get("missing_evidence_count", 0)),
        },
        "diagnostic_debt_count": int(metrics.get("open_debt_count", 0)),
        "shadow_surface_count": int(metrics.get("checker_shadow_count", 0)),
        "notes": [
            "blocked/degraded/missing-evidence counts are text evidence indicators, not a quality score",
            "registry drift and stale source counts are current blocker candidates",
            "shadow checker count indicates calibration surfaces, not hard-gate promotion",
        ],
    }


def print_human(metrics: dict) -> None:
    print("EGB-2 Governance Delivery Metrics")
    print("=" * 40)
    for key in [
        "missing_evidence_count",
        "degraded_count",
        "blocked_count",
        "stale_source_count",
        "registry_drift_count",
        "open_debt_count",
        "checker_shadow_count",
        "rework_placeholder",
    ]:
        print(f"{key:28s} {metrics[key]}")
    interpretation = metrics.get("interpretation", {})
    if interpretation:
        print()
        print("Interpretation")
        print("-" * 40)
        print(f"current_blocker_count       {interpretation.get('current_blocker_count', 0)}")
        print(f"diagnostic_debt_count       {interpretation.get('diagnostic_debt_count', 0)}")
        print(f"shadow_surface_count        {interpretation.get('shadow_surface_count', 0)}")
    print()
    print(metrics["disclaimer"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only EGB-2 governance delivery metrics")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)
    metrics = collect_metrics()
    if args.json:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    else:
        print_human(metrics)
    return 0


if __name__ == "__main__":
    sys.exit(main())
