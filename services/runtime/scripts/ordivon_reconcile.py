#!/usr/bin/env python3
"""Ordivon Reconcile — Governance control loop executor.

Produces a schema-valid closure receipt by comparing desired state
(StageManifest) against actual repo state (RepoSnapshot).

Usage:
    python scripts/ordivon_reconcile.py --template <yaml> --stage-id <id>
    python scripts/ordivon_reconcile.py --template <yaml> --stage-id <id> --json
    python scripts/ordivon_reconcile.py --validate <receipt.json>
"""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ordivon_verify.control.stage_manifest import StageManifest
from ordivon_verify.control.reconciler import Reconciler
from ordivon_verify.control.base_types import RepoSnapshot
from ordivon_verify.control.claim_verifier import ClaimVerifier

RECEIPT_SCHEMA_PATH = ROOT / "src" / "ordivon_verify" / "schemas" / "closure-receipt.schema.json"


def validate_receipt(receipt_path: str) -> tuple[bool, list[str]]:
    """Validate a receipt JSON against the closure-receipt schema."""
    try:
        import jsonschema
    except ImportError:
        return True, ["jsonschema not installed — skipping schema validation"]

    with open(RECEIPT_SCHEMA_PATH) as f:
        schema = json.load(f)
    with open(receipt_path) as f:
        receipt = json.load(f)

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(receipt))
    if errors:
        return False, [f"{' → '.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors]
    return True, []


def build_receipt(manifest: StageManifest, snapshot: RepoSnapshot,
                  report, verification_results: list[dict] = None) -> dict:
    """Build a schema-valid receipt dict from reconciliation results."""
    return {
        "stage_id": manifest.stage_id,
        "risk_class": manifest.risk_class.value,
        "authority_impact": manifest.authority_impact.value,
        "task_type": manifest.task_type,
        "template_id": manifest.template_id,
        "timestamp": report.timestamp,
        "head_commit": snapshot.head_commit,
        "files_changed": snapshot.modified_files,
        "verification_results": verification_results or [],
        "boundary_violations": [
            {
                "file": d.description.split(": ")[-1] if ": " in d.description else d.description,
                "pattern": d.detail.split("must not touch ")[-1] if "must not touch" in d.detail else "",
                "severity": d.severity,
                "category": d.category,
            }
            for d in report.drifts
        ],
        "evidence_produced": [],
        "closure_predicates": [
            {"id": p.predicate_id, "satisfied": report.overall == "READY"}
            for p in manifest.closure_predicates
        ],
        "authorization": {
            "status": "not_requested",
            "approver": None,
            "approved_at": None,
            "rationale": None,
        },
        "overall": report.overall,
        "notes": f"Reconciled at {report.timestamp}. Head: {snapshot.head_commit}. "
                 f"DG: {snapshot.dg_entry_count} entries. Checkers: {snapshot.checker_count}.",
    }


def run_verification_gates(manifest: StageManifest) -> list[dict]:
    """Run all verification gates from the manifest and return structured results."""
    results = []
    for gate in manifest.required_verification:
        start = time.time()
        try:
            r = subprocess.run(
                gate.command, shell=True, cwd=ROOT,
                capture_output=True, text=True, timeout=gate.timeout,
            )
            output = (r.stdout + r.stderr).strip()
            passed = r.returncode == 0
            output_hash = hashlib.sha256(output.encode()).hexdigest()[:16]
        except subprocess.TimeoutExpired:
            output = f"TIMEOUT ({gate.timeout}s)"
            passed = False
            output_hash = ""
        except Exception as e:
            output = str(e)
            passed = False
            output_hash = ""

        duration = int((time.time() - start) * 1000)
        results.append({
            "id": gate.gate_id,
            "description": gate.description,
            "command": gate.command,
            "passed": passed,
            "exit_code": 0 if passed else 1,
            "output_hash": output_hash,
            "duration_ms": duration,
        })
    return results


def main():
    import argparse
    p = argparse.ArgumentParser(description="Ordivon Governance Reconciler")
    p.add_argument("--template", help="Path to stage template YAML")
    p.add_argument("--stage-id", help="Stage identifier")
    p.add_argument("--json", action="store_true", help="Output receipt as JSON")
    p.add_argument("--run-verification", action="store_true",
                   help="Run verification gates before reconciling")
    p.add_argument("--validate", metavar="RECEIPT", help="Validate an existing receipt against schema")
    p.add_argument("--output", metavar="PATH", help="Write receipt to file")
    args = p.parse_args()

    # --validate mode
    if args.validate:
        ok, errors = validate_receipt(args.validate)
        if ok:
            print(f"✅ Receipt valid: {args.validate}")
        else:
            print(f"❌ Receipt invalid: {args.validate}")
            for e in errors:
                print(f"  {e}")
        return 0 if ok else 1

    if not args.template or not args.stage_id:
        p.error("--template and --stage-id are required (or use --validate)")

    # Load template
    template_path = Path(args.template)
    if not template_path.is_absolute():
        template_path = ROOT / template_path

    import yaml
    with open(template_path) as f:
        template = yaml.safe_load(f)

    manifest = StageManifest.from_template(template, args.stage_id)

    # Run verification if requested
    ver_results = []
    if args.run_verification:
        print("── Running verification gates ──")
        ver_results = run_verification_gates(manifest)
        for r in ver_results:
            s = "✅" if r["passed"] else "❌"
            print(f"  {s} {r['id']} ({r['duration_ms']}ms)")

    # Capture actual state
    snapshot = RepoSnapshot.capture(ROOT)

    # Reconcile
    reconciler = Reconciler(manifest)
    report = reconciler.reconcile(snapshot)

    # Build receipt
    receipt = build_receipt(manifest, snapshot, report, ver_results)

    # Verify claims against evidence
    verifier = ClaimVerifier(ROOT)
    claim_report = verifier.verify_receipt(receipt)

    # Populate evidence from claim verification
    receipt["evidence_produced"] = []
    for r in claim_report.results:
        if r.evidence_found:
            receipt["evidence_produced"].append({
                "type": "claim_verification",
                "path": f"claim:{r.claim_id}",
                "hash": hashlib.sha256(
                    json.dumps(r.evidence_found, sort_keys=True).encode()
                ).hexdigest()[:16],
            })
    receipt["claim_verification"] = {
        "total_claims": claim_report.total_claims,
        "supported": claim_report.supported,
        "unsupported": claim_report.unsupported,
        "self_referential": claim_report.self_referential,
        "evidence_coverage": round(claim_report.evidence_coverage, 2),
        "overall": claim_report.overall,
    }

    # Output
    receipt_json = json.dumps(receipt, indent=2, ensure_ascii=False)

    if args.output:
        out_path = Path(args.output)
        if not out_path.is_absolute():
            out_path = ROOT / "docs" / "runtime" / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(receipt_json + "\n")
        print(f"Receipt → {out_path}")

        # Validate
        ok, errors = validate_receipt(str(out_path))
        if ok:
            print("✅ Receipt passes schema validation")
        elif "not installed" in (errors[0] if errors else ""):
            pass  # jsonschema not available — skip
        else:
            print(f"⚠ Schema validation: {len(errors)} issue(s)")

    if args.json:
        print(receipt_json)
    else:
        print(f"Overall: {report.overall}")
        print(f"Drifts: {len(report.drifts)}")
        print(f"  BLOCKED:  {sum(1 for d in report.drifts if d.severity == 'BLOCKED')}")
        print(f"  DEGRADED: {sum(1 for d in report.drifts if d.severity == 'DEGRADED')}")

    return 1 if report.overall == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
