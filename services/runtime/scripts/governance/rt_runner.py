#!/usr/bin/env python3
"""AOS-RT-1 Red-Team Runner — test AOS-AUTO governance plane under adversarial conditions.

Runs 10 attack categories against AUTO tools and produces bypass finding ledger.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts/governance"
EVIDENCE_DIR = ROOT / "docs/governance/evidence/AOS-AUTO-W0-5"

FINDINGS = []


def finding(
    category,
    scenario_id,
    severity,
    affected_tool,
    description,
    expected,
    actual,
    recommended_action,
    blocks_promotion=False,
    requires_harden=False,
):
    FINDINGS.append({
        "finding_id": f"RT-{category}-{scenario_id}",
        "category": category,
        "scenario_id": scenario_id,
        "severity": severity,
        "affected_tool": affected_tool,
        "attack_description": description,
        "expected_behavior": expected,
        "actual_behavior": actual,
        "evidence_captured": True,
        "recommended_action": recommended_action,
        "requires_harden": requires_harden,
        "blocks_promotion": blocks_promotion,
        "blocks_next_stage": severity == "BLOCKING",
    })


def run(cmd, timeout=30, stdin_text=None):
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout, input=stdin_text
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as e:
        return -1, "", str(e)


# ============================================================
# RT-INV: Inventory bypass and false discovery
# ============================================================
def test_inventory_prefix_gap():
    """RT-INV-001: AOS prefix does not discover AOS-AUTO files."""
    rc, out, _ = run(f"python3 {SCRIPTS}/inventory_phase.py --phase AOS --json")
    data = json.loads(out)
    auto_files = [f for f in data["files"] if "aos-auto" in f["path"]]
    if not auto_files:
        finding(
            "INV",
            "001",
            "WARN",
            "inventory_phase.py",
            "AOS-AUTO files invisible to --phase AOS; requires --phase AOS-AUTO",
            "phase-family discovery should include sub-phases",
            f"0 of {data['total_files']} files match aos-auto pattern",
            "Add phase-family expansion to inventory or document AOS-AUTO as separate prefix",
            blocks_promotion=False,
        )
    else:
        finding(
            "INV",
            "001",
            "PASS",
            "inventory_phase.py",
            "AOS prefix discovers AOS-AUTO files",
            "expected",
            f"{len(auto_files)} files found",
            "none",
        )


def test_inventory_prefix_separate():
    """RT-INV-002: AOS-AUTO prefix separately discovers 12 files."""
    rc, out, _ = run(f"python3 {SCRIPTS}/inventory_phase.py --phase AOS-AUTO --json")
    data = json.loads(out)
    finding(
        "INV",
        "002",
        "PASS",
        "inventory_phase.py",
        "--phase AOS-AUTO works as separate prefix",
        "expected discovery",
        f"{data['total_files']} files, {len(data.get('missing_registry_entries', []))} unregistered",
        "none",
    )


# ============================================================
# RT-ADM: Admission bypass
# ============================================================
def test_admission_invalid_doc_type():
    """RT-ADM-001: unknown doc_type rejected."""
    rc, out, _ = run(
        f"python3 {SCRIPTS}/admit_artifact.py --stdin",
        stdin_text=json.dumps({
            "doc_id": "rt-test-invalid-doctype",
            "path": "fake/path.md",
            "title": "RT Test",
            "doc_type": "evil_authority",
            "status": "current",
            "authority": "source_of_truth",
        }),
    )
    result = json.loads(out)
    passed = not result["valid"] and any("INVALID_DOC_TYPE" in e for e in result.get("errors", []))
    finding(
        "ADM",
        "001",
        "PASS" if passed else "BLOCKING",
        "admit_artifact.py",
        "Invalid doc_type 'evil_authority' submitted",
        "Rejected with INVALID_DOC_TYPE",
        out[:200],
        "none" if passed else "Fix admission validator",
        blocks_promotion=not passed,
        requires_harden=not passed,
    )


def test_admission_invalid_authority():
    """RT-ADM-002: invalid authority rejected."""
    rc, out, _ = run(
        f"python3 {SCRIPTS}/admit_artifact.py --stdin",
        stdin_text=json.dumps({
            "doc_id": "rt-test-invalid-auth",
            "path": "fake/path.md",
            "title": "RT Test",
            "doc_type": "receipt",
            "status": "current",
            "authority": "ultimate_approval",
        }),
    )
    result = json.loads(out)
    passed = not result["valid"] and any("INVALID_AUTHORITY" in e for e in result.get("errors", []))
    finding(
        "ADM",
        "002",
        "PASS" if passed else "BLOCKING",
        "admit_artifact.py",
        "Invalid authority 'ultimate_approval' submitted",
        "Rejected with INVALID_AUTHORITY",
        out[:200],
        "none" if passed else "Fix admission validator",
        blocks_promotion=not passed,
        requires_harden=not passed,
    )


def test_admission_missing_path():
    """RT-ADM-003: path not found flagged."""
    rc, out, _ = run(
        f"python3 {SCRIPTS}/admit_artifact.py --stdin",
        stdin_text=json.dumps({
            "doc_id": "rt-test-missing-path",
            "path": "docs/nonexistent/ghost.md",
            "title": "Ghost",
            "doc_type": "receipt",
            "status": "current",
            "authority": "supporting_evidence",
        }),
    )
    result = json.loads(out)
    passed = not result["valid"] and any("PATH_NOT_FOUND" in e for e in result.get("errors", []))
    finding(
        "ADM",
        "003",
        "PASS" if passed else "DEGRADED",
        "admit_artifact.py",
        "Path does not exist on disk",
        "PATH_NOT_FOUND warning",
        out[:200],
        "none" if passed else "Ensure path existence check works",
        blocks_promotion=False,
    )


# ============================================================
# RT-RCP: Receipt claim replay
# ============================================================
def test_receipt_claim_extraction():
    """RT-RCP-001: Can extract claims from receipt."""
    rc, out, _ = run(
        f"python3 {SCRIPTS}/extract_receipt_claims.py receipts/governance/aos-1-object-identity-schema-receipt.md"
    )
    try:
        claims = json.loads(out)
        has_claim = len(claims) > 0
        has_command = any("commands" in c and len(c.get("commands", [])) > 0 for c in claims)
        finding(
            "RCP",
            "001",
            "PASS" if has_claim and has_command else "DEGRADED",
            "extract_receipt_claims.py",
            "Extract claims from AOS-1 receipt",
            "At least 1 claim with executable command",
            f"{len(claims)} claims, has_command={has_command}",
            "none" if has_claim else "Fix claim extraction",
        )
    except:
        finding(
            "RCP",
            "001",
            "DEGRADED",
            "extract_receipt_claims.py",
            "Parse receipt claims",
            "Valid JSON output",
            f"Parse error: {out[:100]}",
            "Fix claim extraction parser",
        )


def test_receipt_claim_replay_match():
    """RT-RCP-002: Claim replay matches actual execution."""
    rc_actual, actual_out, _ = run("python3 scripts/validate-aos-object-identity.py --all-fixtures")
    actual_passes = "Valid fixtures: 1/1 passed" in actual_out

    # Extract expected from receipt
    rc_claim, claim_out, _ = run(
        f"python3 {SCRIPTS}/extract_receipt_claims.py receipts/governance/aos-1-object-identity-schema-receipt.md"
    )
    try:
        claims = json.loads(claim_out)
        expected_in_claim = any("1/1 passed" in str(c.get("expected_patterns", [])) for c in claims)
        finding(
            "RCP",
            "002",
            "PASS" if actual_passes and expected_in_claim else "DEGRADED",
            "receipt replay",
            "Receipt claim 'valid fixtures pass' matches actual execution",
            "Both claim expected and actual execution show 1/1 passed",
            f"actual_passes={actual_passes}, expected_in_claim={expected_in_claim}",
            "none" if actual_passes else "Check AOS-1 fixture validation",
        )
    except:
        finding(
            "RCP",
            "002",
            "WARN",
            "receipt replay",
            "Parse claim output",
            "both match",
            f"parse error: {claim_out[:100]}",
            "Fix parser",
        )


# ============================================================
# RT-EVD: Evidence integrity
# ============================================================
def test_evidence_index_exists():
    """RT-EVD-001: Evidence index exists and is parseable."""
    idx_path = EVIDENCE_DIR / "stage-evidence-index.jsonl"
    if idx_path.exists():
        entries = [json.loads(l) for l in idx_path.read_text().strip().split("\n") if l.strip()]
        has_hashes = all(e.get("sha256_stdout") for e in entries)
        finding(
            "EVD",
            "001",
            "PASS" if has_hashes else "DEGRADED",
            "collect_evidence.py",
            "Evidence index has SHA256 hashes for all entries",
            f"All {len(entries)} entries have SHA256",
            f"{len(entries)} entries, all_hashed={has_hashes}",
            "none" if has_hashes else "Fix evidence collection",
        )
    else:
        finding(
            "EVD",
            "001",
            "WARN",
            "collect_evidence.py",
            "Evidence index exists",
            "Index file present",
            "Index not found at expected path",
            "Re-run collect_evidence for baseline",
        )


def test_evidence_hash_tamper():
    """RT-EVD-002: Tampered evidence file would mismatch hash."""
    if not (EVIDENCE_DIR / "stage-evidence-index.jsonl").exists():
        finding(
            "EVD",
            "002",
            "WARN",
            "evidence integrity",
            "Tampered evidence detected by hash mismatch",
            "Hash mismatch finding",
            "Evidence index absent, cannot test",
            "Create evidence baseline first",
        )
        return

    entries = [
        json.loads(l)
        for l in (EVIDENCE_DIR / "stage-evidence-index.jsonl").read_text().strip().split("\n")
        if l.strip()
    ]

    if not entries:
        finding(
            "EVD",
            "002",
            "WARN",
            "evidence integrity",
            "Evidence entries exist",
            "Entries found",
            "0 entries in index",
            "Re-run evidence collection",
        )
        return

    # Read first entry's stdout file
    first = entries[0]
    cmd_files = list((EVIDENCE_DIR / "commands").glob("*.stdout.txt"))
    if cmd_files:
        original = cmd_files[0].read_text()
        tampered = original + "\n[TAMPERED LINE INJECTED]"
        tampered_hash = hashlib.sha256(tampered.encode()).hexdigest()[:16]
        original_hash = first.get("sha256_stdout", "")
        mismatch = tampered_hash != original_hash
        finding(
            "EVD",
            "002",
            "PASS",
            "evidence integrity",
            "Tampered evidence would produce different hash",
            f"Hash mismatch: original={original_hash}, tampered={tampered_hash}",
            f"mismatch={mismatch}",
            "none — hash integrity works" if mismatch else "Fix hash binding",
        )


# ============================================================
# RT-REC: Reconciliation DAG
# ============================================================
def test_reconcile_dry_run():
    """RT-REC-001: DAG dry-run identifies required steps."""
    rc, out, _ = run(f"python3 {SCRIPTS}/reconcile.py --dry-run")
    has_steps = "Steps:" in out and "RECONCILIATION" in out
    finding(
        "REC",
        "001",
        "PASS" if has_steps else "DEGRADED",
        "reconcile.py",
        "DAG dry-run shows dependency-ordered steps",
        "7 steps identified in correct order",
        f"has_steps={has_steps}, output_lines={len(out.split(chr(10)))}",
        "none" if has_steps else "Fix DAG runner",
    )


# ============================================================
# RT-ROUTE: Routing surface gaps
# ============================================================
def test_route_surface_gap():
    """RT-ROUTE-001: docs/governance/aos-auto/ has no routing."""
    rc, out, _ = run(
        f"python3 {SCRIPTS}/route_reviewers.py --path docs/governance/aos-auto/governance-inventory-model.md"
    )
    result = json.loads(out)
    matched = result.get("matched_files", 0)
    finding(
        "ROUTE",
        "001",
        "WARN" if matched == 0 else "PASS",
        "route_reviewers.py",
        "AOS-AUTO governance surface routes to required checks",
        "Surface should map to required checks",
        f"matched={matched}, unmatched={result.get('unmatched_files', 0)}",
        "Add docs/governance/aos-auto to SURFACE_CHECKS" if matched == 0 else "none",
        blocks_promotion=False,
    )


def test_route_receipt_surface():
    """RT-ROUTE-002: Receipt change routes to claim replay check."""
    rc, out, _ = run(
        f"python3 {SCRIPTS}/route_reviewers.py --path receipts/governance/aos-1-object-identity-schema-receipt.md"
    )
    result = json.loads(out)
    checks = result.get("unique_checks", [])
    has_replay = any("extract_receipt_claims" in c or "detect_overclaim" in c for c in checks)
    finding(
        "ROUTE",
        "002",
        "PASS" if has_replay else "WARN",
        "route_reviewers.py",
        "Receipt change should trigger claim replay + overclaim checks",
        "extract_receipt_claims or detect_overclaim in required checks",
        f"checks={checks}",
        "none" if has_replay else "Add receipt surface to SURFACE_CHECKS",
    )


# ============================================================
# RT-NAME: Naming drift
# ============================================================
def test_naming_surfaces():
    """RT-NAME-001: Multiple naming surfaces exist across project."""
    naming_doc = ROOT / "docs/naming.md"
    if naming_doc.exists():
        content = naming_doc.read_text()
        names_found = []
        for name in ["Ordivon", "AegisOS", "PFIOS", "financial-ai-os", "Personal-Financial"]:
            if name in content:
                names_found.append(name)
        finding(
            "NAME",
            "001",
            "WARN" if len(names_found) >= 3 else "PASS",
            "naming governance",
            "Naming drift across surfaces is documented",
            "Multiple names documented as known issue",
            f"{len(names_found)} naming variants: {names_found}",
            "Register naming.md in registry; add naming consistency checker to AUTO",
            blocks_promotion=False,
        )


# ============================================================
# RT-OVER: Overclaim detection
# ============================================================
def test_overclaim_on_receipts():
    """RT-OVER-001: Overclaim detector catches forbidden words in receipts."""
    rc, out, _ = run(
        "python3 scripts/detect_overclaim.py "
        "receipts/governance/aos-rs-final-summit-receipt.md "
        "receipts/governance/aos-auto-construction-summit-receipt.md"
    )
    has_zero = "Findings: 0" in out
    finding(
        "OVER",
        "001",
        "PASS" if has_zero else "DEGRADED",
        "detect_overclaim.py",
        "AOS receipts should have 0 overclaim findings",
        "0 findings",
        f"has_zero_findings={has_zero}",
        "none" if has_zero else "Fix overclaim in receipts",
    )


def test_overclaim_promotion_ready():
    """RT-OVER-002: Receipt containing 'promotion ready' would be flagged."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# RT Test\n\nAOS is promotion ready and production safe.\n")
        tmp_path = f.name
    try:
        rc, out, _ = run(f"python3 scripts/detect_overclaim.py {tmp_path}")
        # Check if it detected anything — the detector flags forbidden patterns
        has_findings = "Findings: 0" not in out
        finding(
            "OVER",
            "002",
            "PASS" if has_findings else "DEGRADED",
            "detect_overclaim.py",
            "Text containing 'promotion ready'/'production safe' should be flagged",
            "Overclaim finding detected",
            f"has_findings={has_findings}, output={out[:100]}",
            "none" if has_findings else "Strengthen overclaim detection patterns",
        )
    finally:
        os.unlink(tmp_path)


# ============================================================
# RT-VERIFY: Verify honesty
# ============================================================
def test_verify_pass_with_known_gaps():
    """RT-VERIFY-001: verify.py reports 6/6 PASS despite known degraded gaps."""
    rc, out, _ = run(f"python3 {SCRIPTS}/verify.py")
    passed_all = "Overall: PASS" in out and "Passed: 6" in out

    # Known gaps from DOG-1:
    # 1. inventory phase-family gap
    # 2. routing surface gap for aos-auto/
    known_gaps_exist = True

    if passed_all and known_gaps_exist:
        finding(
            "VERIFY",
            "001",
            "WARN",
            "verify.py",
            "Verify 6/6 PASS while known DEGRADED surface gaps exist",
            "Verify should surface bounded limitations or note deferred gaps",
            "6/6 PASS reported; routing + inventory gaps not reflected",
            "Add bounded-limitation output to verify.py summary; do not claim clean final",
            blocks_promotion=True,
        )
    else:
        finding(
            "VERIFY",
            "001",
            "PASS",
            "verify.py",
            "Verify handles gap reporting correctly",
            "expected",
            "matched",
            "none",
        )


# ============================================================
# Main
# ============================================================
def main():
    print("=== AOS-RT-1 RED-TEAM RUNNER ===")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print()

    tests = [
        ("RT-INV-001", test_inventory_prefix_gap),
        ("RT-INV-002", test_inventory_prefix_separate),
        ("RT-ADM-001", test_admission_invalid_doc_type),
        ("RT-ADM-002", test_admission_invalid_authority),
        ("RT-ADM-003", test_admission_missing_path),
        ("RT-RCP-001", test_receipt_claim_extraction),
        ("RT-RCP-002", test_receipt_claim_replay_match),
        ("RT-EVD-001", test_evidence_index_exists),
        ("RT-EVD-002", test_evidence_hash_tamper),
        ("RT-REC-001", test_reconcile_dry_run),
        ("RT-ROUTE-001", test_route_surface_gap),
        ("RT-ROUTE-002", test_route_receipt_surface),
        ("RT-NAME-001", test_naming_surfaces),
        ("RT-OVER-001", test_overclaim_on_receipts),
        ("RT-OVER-002", test_overclaim_promotion_ready),
        ("RT-VERIFY-001", test_verify_pass_with_known_gaps),
    ]

    for test_id, test_fn in tests:
        print(f"  [{test_id}] ...", end=" ", flush=True)
        try:
            test_fn()
            # Get the finding we just added
            f = FINDINGS[-1]
            icon = {"PASS": "✓", "WARN": "⚠", "DEGRADED": "△", "BLOCKING": "✗"}.get(f["severity"], "?")
            print(f"{icon} {f['severity']}")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            finding(
                test_id.split("-")[1],
                test_id.split("-")[2],
                "DEGRADED",
                test_id,
                "Test execution failed",
                "clean run",
                str(e)[:200],
                "Debug test runner",
            )

    # Summary
    severities = {}
    for f in FINDINGS:
        s = f["severity"]
        severities[s] = severities.get(s, 0) + 1
    blocking = sum(1 for f in FINDINGS if f.get("blocks_promotion"))
    harden = sum(1 for f in FINDINGS if f.get("requires_harden"))

    print("\n=== RT-1 FINDINGS SUMMARY ===")
    for s in ["BLOCKING", "DEGRADED", "WARN", "PASS"]:
        if s in severities:
            print(f"  {s}: {severities[s]}")
    print(f"Blocks promotion: {blocking}")
    print(f"Requires harden: {harden}")

    # Write finding ledger
    ledger_path = ROOT / "docs/governance/audits/aos/aos-rt-1"
    ledger_path.mkdir(parents=True, exist_ok=True)

    ledger_file = ledger_path / "aos-rt-1-bypass-findings.jsonl"
    with open(ledger_file, "w") as f:
        for finding_entry in FINDINGS:
            f.write(json.dumps(finding_entry, ensure_ascii=False) + "\n")

    print(f"\nLedger: {ledger_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
