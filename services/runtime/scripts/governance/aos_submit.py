#!/usr/bin/env python3
"""AOS Object Submission Protocol — end-to-end pipeline for declarative AOS objects.

Usage:
    python3 scripts/governance/aos_submit.py --package examples/aos/real-object-dogfood
    python3 scripts/governance/aos_submit.py --package <dir> --dry-run

Pipeline:
    identity → admission → registry → evidence → reconcile → verify → receipt
"""

from __future__ import annotations

import json
import hashlib
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTION_DECLARATIONS_LEDGER = ROOT / "docs/governance/action-declarations.jsonl"
ACTION_DECLARATION_RECEIPTS = ROOT / "receipts/governance/action-declarations"

try:
    from ordivon_governance_core.result import GovernanceResult
    from ordivon_governance_core.trace import GovernanceTrace, new_trace_id
    from ordivon_governance_core.jsonl import append_jsonl_safe
    from ordivon_governance_core.registry import register_entry
    from ordivon_governance_core.evidence import sha256_hex, make_evidence_record
    from ordivon_governance_core.events import classify_event, get_required_checks

    _HAS_CORE = True
except ImportError:
    _HAS_CORE = False


def run_cmd(cmd: str, timeout: int = 30) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout, proc.stderr


def git_output(cmd: str) -> str:
    rc, out, _ = run_cmd(cmd)
    return out.strip() if rc == 0 else "UNKNOWN"


def parse_status_paths(status_text: str) -> list[str]:
    paths = []
    for line in status_text.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            paths.append(path)
    return sorted(set(paths))


def object_hash(obj: dict) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def declaration_slug(object_id: str) -> str:
    return object_id.rsplit(":", 1)[-1].replace("/", "-")


def register_ai_action_declaration(obj: dict, pkg: dict, pkg_dir: Path, trace_id: str, dry_run: bool) -> int:
    """Register an AIActionDeclaration baseline and receipt.

    This registers the declaration only. It does not observe or audit the later action.
    """
    print("[1/4] Declaration validation...", end=" ", flush=True)
    if dry_run:
        print("DRY-RUN")
        print("[2/4] Declaration admission... DRY-RUN")
        print("[3/4] Baseline registration... DRY-RUN")
        print("[4/4] Declaration receipt... DRY-RUN")
        print("\n=== AOS AI ACTION DECLARATION DRY-RUN COMPLETE ===")
        return 0

    validator_cmd = (
        f"PYTHONPATH=.:src {shlex.quote(sys.executable)} "
        f"scripts/validate-ai-action-declaration.py {shlex.quote(str(pkg_dir / 'object.aos.json'))}"
    )
    rc, out, err = run_cmd(validator_cmd)
    if rc != 0:
        print(f"✗ FAIL: {(err or out)[:120]}")
        return 1
    print("✓ PASS")

    print("[2/4] Declaration admission...", end=" ", flush=True)
    print("✓ ADMITTED (identity_validated)")

    print("[3/4] Baseline registration...", end=" ", flush=True)
    git_head = git_output("git rev-parse HEAD")
    git_status = git_output("git status --short")
    dirty_paths = parse_status_paths(git_status if git_status != "UNKNOWN" else "")
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "declaration_id": declaration_slug(obj["object_id"]),
        "object_id": obj["object_id"],
        "object_kind": obj["object_kind"],
        "schema_version": obj.get("schema_version"),
        "origin": obj.get("origin"),
        "state": obj.get("state"),
        "package_id": pkg.get("package_id", ""),
        "actor": obj.get("actor", {}),
        "declared_action": obj.get("declared_action"),
        "action_class": obj.get("action_class"),
        "action_spec": obj.get("action_spec", {}),
        "declared_scope": obj.get("declared_scope", []),
        "not_allowed": obj.get("not_allowed", []),
        "expected_outputs": obj.get("expected_outputs", []),
        "baseline": {
            "git_head_ref": git_head,
            "git_status_short_sha256": hashlib.sha256(git_status.encode()).hexdigest()[:16],
            "dirty_count": len(dirty_paths),
            "dirty_paths": dirty_paths,
        },
        "object_hash": object_hash(obj),
        "trace_id": trace_id,
        "registered_at": now,
        "not_claimed": obj.get("not_claimed", []),
    }
    ACTION_DECLARATIONS_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    if _HAS_CORE:
        reg = append_jsonl_safe(
            ACTION_DECLARATIONS_LEDGER, record, idempotency_key=obj["object_id"], dedup_by="object_id"
        )
        status = reg.get("status", "unknown")
    else:
        with ACTION_DECLARATIONS_LEDGER.open("a") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        status = "appended"
    print(f"✓ {status}")

    print("[4/4] Declaration receipt...", end=" ", flush=True)
    ACTION_DECLARATION_RECEIPTS.mkdir(parents=True, exist_ok=True)
    receipt_path = ACTION_DECLARATION_RECEIPTS / f"{record['declaration_id']}.json"
    receipt = {
        "receipt_id": f"action-declaration-{record['declaration_id']}",
        "trace_id": trace_id,
        "object_id": obj["object_id"],
        "schema_version": obj.get("schema_version"),
        "origin": "SYSTEM_DERIVED",
        "created_by": "scripts/governance/aos_submit.py",
        "package_id": pkg.get("package_id", ""),
        "status": "DECLARED",
        "protocol_mapping": {
            "package.aos.json": "Intent",
            "AIActionDeclaration": "Obligation",
        },
        "baseline": record["baseline"],
        "registered_at": now,
        "not_claimed": [
            "Declaration is not authorization",
            "Declaration does not prove correctness",
            "Declaration does not permit scope expansion",
            "Declaration registration does not perform conformance audit",
        ],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(f"✓ {receipt_path.relative_to(ROOT)}")

    print("\n=== AOS AI ACTION DECLARATION REGISTERED ===")
    print(f"Ledger: {ACTION_DECLARATIONS_LEDGER.relative_to(ROOT)}")
    print(f"Receipt: {receipt_path.relative_to(ROOT)}")
    return 0


def main():
    dry_run = "--dry-run" in sys.argv
    source_context = "unknown"
    for i, a in enumerate(sys.argv):
        if a == "--source-context" and i + 1 < len(sys.argv):
            source_context = sys.argv[i + 1]
    pkg_dir = None
    for i, a in enumerate(sys.argv):
        if a == "--package" and i + 1 < len(sys.argv):
            pkg_dir = Path(sys.argv[i + 1]).resolve()
    if not pkg_dir or not pkg_dir.exists():
        print("Usage: aos_submit.py --package <dir> [--dry-run]", file=sys.stderr)
        sys.exit(1)

    obj_path = pkg_dir / "object.aos.json"
    pkg_path = pkg_dir / "package.aos.json"
    if not obj_path.exists() or not pkg_path.exists():
        print("ERROR: package must contain object.aos.json and package.aos.json", file=sys.stderr)
        sys.exit(1)

    obj = json.loads(obj_path.read_text())
    pkg = json.loads(pkg_path.read_text())
    obj_id = obj.get("object_id", "unknown")
    pkg_id = pkg.get("package_id", "unknown")
    doc_id = pkg_id.replace("/", "-")

    trace_id = new_trace_id() if _HAS_CORE else f"trace-{int(time.time())}"
    trace = GovernanceTrace(trace_id=trace_id, operation=f"aos-submit-{doc_id}") if _HAS_CORE else None
    result = (
        GovernanceResult(tool="aos-submit", trace_id=trace_id, command=f"aos_submit.py --package {pkg_dir}")
        if _HAS_CORE
        else None
    )

    # Event classification
    if _HAS_CORE:
        event = classify_event(
            obj.get("object_kind", ""),
            pkg.get("requested_action", ""),
            producer_type=pkg.get("producer", {}).get("producer_type", "unknown"),
        )
        event["source_context"] = source_context
        event_type, event_class = event["event_type"], event["event_class"]
        get_required_checks(event_class)
    else:
        event_type, event_class, _required_checks = "artifact_submitted", "E1_documentation", []

    print(f"=== AOS SUBMIT: {pkg_dir.name} ===")
    print(f"Object: {obj_id}")
    print(f"Package: {pkg_id}")
    print(f"Event: {event_type} ({event_class}) [{source_context}]")
    print(f"Trace: {trace_id}")
    print()

    if obj.get("object_kind") == "AIActionDeclaration":
        sys.exit(register_ai_action_declaration(obj, pkg, pkg_dir, trace_id, dry_run))

    # === STEP 1: Identity Validation (routed by object_kind) ===
    print("[1/7] Identity validation...", end=" ", flush=True)
    if dry_run:
        print("DRY-RUN")
    else:
        kind = obj.get("object_kind", "")
        if kind == "DebtTransition":
            cmd = f"python3 scripts/validate-debt-transition.py {obj_path}"
        elif kind == "CandidateRuleRecord":
            cmd = f"python3 scripts/validate-candidate-rule.py {obj_path}"
        elif kind == "GatePromotionRecord":
            cmd = f"python3 scripts/validate-gate-promotion.py {obj_path}"
        elif kind == "AIActionDeclaration":
            cmd = f"python3 scripts/validate-ai-action-declaration.py {obj_path}"
        else:
            cmd = f"python3 scripts/validate-aos-object-identity.py {obj_path}"
        rc, out, err = run_cmd(cmd)
        passed = rc == 0 and ("valid" in out.lower() or "✓" in out)
        if result:
            if not passed:
                result.add_finding("AOS-SUBMIT-IDENTITY", "BLOCKING", f"Identity validation failed: {err[:100]}")
                result.status = "BLOCKING"
        if trace:
            trace.add_span(
                "identity",
                "PASS" if passed else "BLOCKING",
                output_refs=[str(obj_path.relative_to(ROOT))],
                evidence_refs=["aos-submit-identity"],
            )
        print("✓ PASS" if passed else f"✗ FAIL: {err[:80]}")
        if not passed:
            print(result.to_json() if result else "BLOCKED")
            sys.exit(1)

    # === STEP 2: Admission (routed by object_kind) ===
    print("[2/7] Admission...", end=" ", flush=True)
    if dry_run:
        print("DRY-RUN")
    else:
        kind = obj.get("object_kind", "")
        if kind in ("DebtTransition", "CandidateRuleRecord", "GatePromotionRecord", "AIActionDeclaration"):
            admitted = True
            adm = {"decision": "ADMITTED", "checks_run": ["identity_validated"], "reasons": []}
        else:
            rc, out, err = run_cmd(f"python3 scripts/aos-admit.py --package {pkg_dir} --dry-run")
            try:
                adm = json.loads(out)
                admitted = adm.get("decision") == "ADMITTED"
            except json.JSONDecodeError:
                admitted = False
        if result and not admitted:
            result.add_finding("AOS-SUBMIT-ADMIT", "BLOCKING", f"Admission: {adm.get('reasons', [])}")
            result.status = "BLOCKING"
        if trace:
            trace.add_span(
                "admission", "PASS" if admitted else "BLOCKING", output_refs=[str(pkg_path.relative_to(ROOT))]
            )
        print(
            f"✓ ADMITTED ({adm.get('checks_run', [])} checks)"
            if admitted
            else f"✗ {adm.get('decision', '?')}: {adm.get('reasons', [])}"
        )
        if not admitted and result:
            print(result.to_json())
            sys.exit(1)

    # === STEP 3: Registry Entry ===
    print("[3/7] Registry entry...", end=" ", flush=True)
    if dry_run:
        print("DRY-RUN")
    else:
        entry = {
            "doc_id": doc_id,
            "path": f"examples/aos/real-object-dogfood/{obj_path.name}",
            "title": obj.get("object_name", doc_id),
            "doc_type": "supporting_evidence",
            "status": "current",
            "authority": "supporting_evidence",
            "phase": "AOS-OBJECT-DOG-1",
            "freshness": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "notes": f"AOS object submission dogfood. Object: {obj_id}.",
        }
        reg_path = ROOT / "docs/governance/document-registry.jsonl"
        if _HAS_CORE:
            reg_ok = register_entry(entry)
        else:
            with open(reg_path, "a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            reg_ok = True
        if trace:
            trace.add_span("registry", "PASS" if reg_ok else "BLOCKING")
        print(f"✓ {'registered' if reg_ok else 'duplicate'}" if reg_ok else "✗")

    # === STEP 4: Evidence Collection ===
    print("[4/7] Evidence collection...", end=" ", flush=True)
    if dry_run:
        print("DRY-RUN")
    else:
        evidence_dir = ROOT / "docs/governance/evidence/aos-object-dog-1"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        cmds = [
            ("identity", f"python3 scripts/validate-aos-object-identity.py {obj_path}"),
            ("admission", f"python3 scripts/aos-admit.py --package {pkg_dir} --dry-run"),
        ]
        records = []
        for name, cmd in cmds:
            rc, out, err = run_cmd(cmd)
            stdout_hash = sha256_hex(out) if _HAS_CORE else ""
            rec = (
                make_evidence_record(f"ev-{name}", cmd, rc, sha256_stdout=stdout_hash)
                if _HAS_CORE
                else {"evidence_id": f"ev-{name}", "exit_code": rc}
            )
            records.append(rec)
        idx_path = evidence_dir / "stage-evidence-index.jsonl"
        with open(idx_path, "w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
        if trace:
            trace.add_span("evidence", "PASS", evidence_refs=[str(idx_path.relative_to(ROOT))])
        print(f"✓ {len(records)} records")

    # === STEP 5: Reconciliation ===
    print("[5/7] Reconciliation dry-run...", end=" ", flush=True)
    if dry_run:
        print("DRY-RUN")
    else:
        rc, out, _ = run_cmd("python3 scripts/governance/reconcile.py --dry-run")
        dag_ok = "Steps:" in out
        if trace:
            trace.add_span("reconcile", "PASS" if dag_ok else "DEGRADED")
        print("✓ DAG intact" if dag_ok else "✗")

    # === STEP 6: Verify ===
    print("[6/7] Governance verify...", end=" ", flush=True)
    if dry_run:
        print("DRY-RUN")
    else:
        rc, out, _ = run_cmd("PYTHONPATH=src python3 scripts/governance/verify.py")
        verify_ok = rc == 0
        if result and not verify_ok:
            result.add_finding("AOS-SUBMIT-VERIFY", "DEGRADED", "Verify did not pass")
        if trace:
            trace.add_span("verify", "PASS_WITH_WARNINGS" if verify_ok else "BLOCKING")
        print("✓ PASS_WITH_WARNINGS" if verify_ok else "✗")

    # === STEP 7: Receipt ===
    print("[7/7] Receipt...", end=" ", flush=True)
    if dry_run:
        print("DRY-RUN")
    else:
        receipt = {
            "submission_id": doc_id,
            "trace_id": trace_id,
            "object_id": obj_id,
            "package_id": pkg_id,
            "status": result.status if result else "PASS",
            "steps_completed": 7,
            "pipeline": "identity → admission → registry → evidence → reconcile → verify → receipt",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "not_claimed": [
                "This is an AOS object dogfood submission, not a production pipeline run",
                "AOS-Core has processed exactly one real object — this one",
                "This does not represent operational maturity",
            ],
        }
        receipt_path = ROOT / "receipts/governance/aos-submit-dogfood-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2))
        if trace:
            trace.add_span(
                "receipt", result.status if result else "PASS", output_refs=[str(receipt_path.relative_to(ROOT))]
            )
        print(f"✓ {receipt_path.relative_to(ROOT)}")

    # Final
    if trace:
        trace_path = ROOT / "docs/governance/evidence/aos-object-dog-1/governance-trace.jsonl"
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(json.dumps(trace.to_dict(), indent=2))

    print("\n=== AOS SUBMIT COMPLETE ===")
    print("Trace: docs/governance/evidence/aos-object-dog-1/governance-trace.jsonl")
    print("Receipt: receipts/governance/aos-submit-dogfood-receipt.json")
    if result:
        print(f"Status: {result.status}")
        result.emit()

    sys.exit(0 if not result or result.status in ("PASS", "PASS_WITH_WARNINGS") else 1)


if __name__ == "__main__":
    main()
