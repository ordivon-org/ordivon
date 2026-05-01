#!/usr/bin/env python3
"""Ordivon Coverage Governance Checker (COV-1).

Validates the checker-coverage-manifest.json — verifies every governed
checker declares its universe, discovery method, exclusions, and pass scope.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "governance" / "checker-coverage-manifest.json"

GOVERNANCE_JSON_FILES = [
    ROOT / "docs" / "governance" / "checker-coverage-manifest.json",
    ROOT / "docs" / "governance" / "verification-gate-manifest.json",
    ROOT / "docs" / "governance" / "document-registry-exclusions.json",
]

GOVERNANCE_JSONL_FILES = [
    ROOT / "docs" / "governance" / "document-registry.jsonl",
    ROOT / "docs" / "governance" / "verification-debt-ledger.jsonl",
]


def check_governance_artifacts() -> list[str]:
    """Validate all governance data artifacts parse as valid JSON/JSONL."""
    errors = []
    for path in GOVERNANCE_JSON_FILES:
        if not path.exists():
            errors.append(f"missing JSON artifact: {path}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"invalid JSON artifact: {path} — {e}")
    for path in GOVERNANCE_JSONL_FILES:
        if not path.exists():
            errors.append(f"missing JSONL artifact: {path}")
            continue
        try:
            count = 0
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    json.loads(line)
                    count += 1
            if count == 0:
                errors.append(f"empty JSONL artifact: {path} has zero entries")
        except json.JSONDecodeError as e:
            errors.append(f"invalid JSONL artifact: {path} — {e}")
    # Additional invariants
    manifest = MANIFEST_PATH
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            checkers = data.get("checkers", [])
            if not checkers:
                errors.append("checker-coverage-manifest.json has empty checkers list")
            gate_manifest = ROOT / "docs" / "governance" / "verification-gate-manifest.json"
            if gate_manifest.exists():
                gm = json.loads(gate_manifest.read_text(encoding="utf-8"))
                gate_count = gm.get("gate_count", 0)
                gates = gm.get("gates", [])
                if gate_count != len(gates):
                    errors.append(
                        f"verification-gate-manifest gate_count ({gate_count}) != gates length ({len(gates)})"
                    )
        except json.JSONDecodeError:
            pass  # already reported above
    return errors


VALID_STATUSES = {"implemented", "partial", "deferred_with_reason", "not_applicable"}

CRITICAL_CHECKERS = {
    "document_registry",
    "verification_debt",
    "receipt_integrity",
    "verification_manifest",
    "pr_fast_baseline",
    "public_wedge_audit",
    "public_repo_dryrun",
    "private_install_smoke",
    "build_artifact_smoke",
}

REQUIRED_TOP_FIELDS = {"schema_version", "generated", "purpose", "coverage_policy", "checkers"}

REQUIRED_ENTRY_FIELDS = {
    "checker_id",
    "checker_path",
    "status",
    "claimed_universe",
    "discovery_method",
    "registry_or_manifest",
    "exclusion_policy",
    "reconciliation_required",
    "coverage_summary_required",
    "unknown_object_test_required",
    "pass_scope_statement_required",
    "known_gaps",
    "owner",
    "reviewed_at",
}


def load_manifest(path: Path | None = None) -> dict:
    p = path or MANIFEST_PATH
    if not p.exists():
        return {"checkers": []}
    with open(p) as f:
        return json.load(f)


def validate_manifest(data: dict) -> list[str]:
    errors: list[str] = []

    # Top-level fields
    missing_top = REQUIRED_TOP_FIELDS - set(data.keys())
    if missing_top:
        errors.append(f"manifest missing top-level fields: {missing_top}")

    checkers = data.get("checkers", [])
    if not isinstance(checkers, list):
        errors.append("'checkers' must be a list")
        return errors

    seen_ids: set[str] = set()
    checker_paths: dict[str, str] = {}

    for i, c in enumerate(checkers):
        cid = c.get("checker_id", f"<missing at index {i}>")

        # Required fields
        missing = REQUIRED_ENTRY_FIELDS - set(c.keys())
        if missing:
            errors.append(f"{cid}: missing required fields: {missing}")

        # Unique ID
        if cid in seen_ids:
            errors.append(f"{cid}: duplicate checker_id")
        seen_ids.add(cid)

        # Status
        status = c.get("status", "")
        if status not in VALID_STATUSES:
            errors.append(f"{cid}: invalid status '{status}'")

        # Path
        path = c.get("checker_path", "")
        if status != "deferred_with_reason":
            full = ROOT / path if path else None
            if not full or not full.exists():
                errors.append(f"{cid}: checker_path not found: {path}")
        checker_paths[cid] = path

        # Implemented/partial checks
        if status in ("implemented", "partial"):
            if not c.get("claimed_universe", "").strip():
                errors.append(f"{cid}: claimed_universe is empty")
            if not c.get("discovery_method", "").strip():
                errors.append(f"{cid}: discovery_method is empty")
            excl = c.get("exclusion_policy", "")
            if not excl.strip() and excl != "none_required":
                errors.append(f"{cid}: exclusion_policy is empty (use 'none_required' with reason if truly none)")
            if not c.get("owner", "").strip():
                errors.append(f"{cid}: owner is empty")
            if not c.get("reviewed_at", "").strip():
                errors.append(f"{cid}: reviewed_at is empty")
            if not c.get("pass_scope_statement_required", False):
                errors.append(f"{cid}: pass_scope_statement_required must be true")

        # Implemented-specific checks
        if status == "implemented":
            if c.get("reconciliation_required") is None:
                errors.append(f"{cid}: reconciliation_required must be explicitly true or false")
            if not c.get("coverage_summary_required", False):
                errors.append(f"{cid}: coverage_summary_required must be true for implemented status")

        # Deferred checks
        if status == "deferred_with_reason":
            gaps = c.get("known_gaps", [])
            if not gaps:
                errors.append(f"{cid}: deferred_with_reason must have known_gaps")

    # Critical checkers present
    present_ids = {c.get("checker_id", "") for c in checkers}
    missing_critical = CRITICAL_CHECKERS - present_ids
    if missing_critical:
        errors.append(f"critical checkers missing from manifest: {missing_critical}")

    return errors


def print_summary(data: dict, errors: list[str]) -> None:
    checkers = data.get("checkers", [])
    status_counts = {"implemented": 0, "partial": 0, "deferred_with_reason": 0, "not_applicable": 0}
    for c in checkers:
        s = c.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    missing_paths = sum(
        1
        for c in checkers
        if c.get("status") != "deferred_with_reason" and not (ROOT / c.get("checker_path", "")).exists()
    )

    print("=" * 60)
    print("CHECKER COVERAGE GOVERNANCE SUMMARY")
    print("=" * 60)
    print(f"  Total checkers:           {len(checkers)}")
    print(f"  Implemented:              {status_counts.get('implemented', 0)}")
    print(f"  Partial:                  {status_counts.get('partial', 0)}")
    print(f"  Deferred with reason:     {status_counts.get('deferred_with_reason', 0)}")
    print(f"  Not applicable:           {status_counts.get('not_applicable', 0)}")
    print(f"  Missing paths:            {missing_paths}")
    print(f"  Critical missing:         {len([e for e in errors if 'critical' in e.lower()])}")
    print(f"  Manifest violations:      {len(errors)}")


def main(json_output: bool = False) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        manifest_path = MANIFEST_PATH

    data = load_manifest(manifest_path)
    errors = validate_manifest(data)

    # Artifact integrity — governance data must parse
    artifact_errors = check_governance_artifacts()
    errors.extend(artifact_errors)

    if args.json:
        print(
            json.dumps(
                {
                    "manifest_path": str(manifest_path),
                    "total_checkers": len(data.get("checkers", [])),
                    "violations": len(errors),
                    "errors": errors,
                    "status": "PASS" if not errors else "FAIL",
                },
                indent=2,
            )
        )
    else:
        print_summary(data, errors)
        if errors:
            print(f"\n❌ {len(errors)} VIOLATION(S):\n")
            for e in errors:
                print(f"  - {e}")
            print()
            return 1
        print("\n✅ All coverage governance invariants pass.\n")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main("--json" in sys.argv))
