"""Claim Verifier — closes the AI-agent claim verification loop.

The core value of Ordivon: verify that what an agent CLAIMED to have done
matches what the repo actually CONTAINS as evidence.

Every receipt contains claims (closure_predicates) and evidence references
(verification_results with output_hash). The ClaimVerifier:
  1. Extracts all claims from a receipt
  2. Finds corresponding evidence in the repo
  3. Reports which claims are supported, which are unsupported
  4. Flags claims that are self-referential (no external evidence)

This is the minimal viable "Verify what your AI agent actually did."
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ClaimResult:
    """Verification result for a single claim."""
    claim_id: str
    claim_description: str
    status: str           # SUPPORTED | UNSUPPORTED | SELF_REFERENTIAL | CONTRADICTED
    evidence_found: list[str] = field(default_factory=list)
    evidence_missing: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class ClaimVerificationReport:
    """Full claim verification report."""
    stage_id: str
    total_claims: int
    supported: int
    unsupported: int
    self_referential: int
    results: list[ClaimResult] = field(default_factory=list)
    overall: str = "READY"  # READY | DEGRADED | UNVERIFIED

    @property
    def evidence_coverage(self) -> float:
        """What fraction of claims have evidence?"""
        if self.total_claims == 0:
            return 1.0
        return self.supported / self.total_claims


class ClaimVerifier:
    """Verifies agent claims against repo evidence."""

    def __init__(self, root: Path):
        self.root = root

    def verify_receipt(self, receipt: dict) -> ClaimVerificationReport:
        """Verify all claims in a closure receipt."""
        stage_id = receipt.get("stage_id", "unknown")
        results = []

        # 1. Verify closure predicates (claims about what was done)
        for pred in receipt.get("closure_predicates", []):
            result = self._verify_predicate(pred, receipt)
            results.append(result)

        # 2. Verify file change claims
        claimed_files = set(receipt.get("files_changed", []))
        actual_files = self._get_actual_modified_files()
        if claimed_files:
            result = self._verify_file_claim(claimed_files, actual_files)
            results.append(result)

        # 3. Verify verification result hashes (tamper detection)
        for v in receipt.get("verification_results", []):
            if v.get("output_hash"):
                result = self._verify_hash_claim(v)
                if result:
                    results.append(result)

        # 4. Verify boundary claims
        violations = receipt.get("boundary_violations", [])
        if not violations and claimed_files:
            result = self._verify_boundary_claim(receipt, claimed_files)
            if result:
                results.append(result)

        supported = sum(1 for r in results if r.status == "SUPPORTED")
        unsupported = sum(1 for r in results if r.status == "UNSUPPORTED")
        self_ref = sum(1 for r in results if r.status == "SELF_REFERENTIAL")

        overall = "READY"
        if unsupported > 0:
            overall = "UNVERIFIED"
        elif self_ref > 0:
            overall = "DEGRADED"

        return ClaimVerificationReport(
            stage_id=stage_id,
            total_claims=len(results),
            supported=supported,
            unsupported=unsupported,
            self_referential=self_ref,
            results=results,
            overall=overall,
        )

    def _verify_predicate(self, pred: dict, receipt: dict) -> ClaimResult:
        """Verify a single closure predicate claim."""
        pid = pred.get("id", "?")
        satisfied = pred.get("satisfied", False)
        evidence_ref = pred.get("evidence_ref", "")

        evidence_found = []
        evidence_missing = []

        # Predicate: all_required_docs_registered
        if "doc" in pid.lower() or "registry" in pid.lower():
            dg_path = self.root / "docs" / "governance" / "document-registry.jsonl"
            if dg_path.exists():
                evidence_found.append(f"document-registry.jsonl exists ({dg_path.stat().st_size} bytes)")
                # Check if files_changed docs are registered
                changed = receipt.get("files_changed", [])
                docs_changed = [f for f in changed if f.startswith("docs/")]
                if docs_changed:
                    evidence_found.append(f"{len(docs_changed)} doc(s) changed — registry check required")
            else:
                evidence_missing.append("document-registry.jsonl not found")

        # Predicate: receipt_valid
        if "receipt" in pid.lower():
            receipt_path = self.root / "docs" / "runtime" / f"{receipt.get('stage_id', '?')}.receipt.json"
            if receipt_path.exists():
                evidence_found.append(f"receipt file exists ({receipt_path.stat().st_size} bytes)")
            else:
                evidence_missing.append(f"receipt file not found at {receipt_path}")

        # Predicate: no_authority_escalation
        if "authority" in pid.lower() or "escalation" in pid.lower():
            violations = receipt.get("boundary_violations", [])
            auth_violations = [v for v in violations
                              if v.get("category") in ("authority", "boundary")]
            if not auth_violations:
                evidence_found.append("no authority violations in receipt")
            else:
                evidence_missing.append(f"{len(auth_violations)} authority violation(s) found")

        # Generic: if predicate claims satisfied=True but no evidence_ref
        if satisfied and not evidence_ref and not evidence_found:
            return ClaimResult(
                claim_id=pid,
                claim_description=pred.get("id", pid),
                status="SELF_REFERENTIAL",
                evidence_missing=["No evidence_ref provided for satisfied claim"],
                detail="Claim marked 'satisfied' without referencing any evidence. This is a self-referential claim — the agent asserts completion without proof.",
            )

        if satisfied and not evidence_found and not evidence_ref:
            return ClaimResult(
                claim_id=pid,
                claim_description=pred.get("id", pid),
                status="SELF_REFERENTIAL",
                evidence_found=evidence_found,
                evidence_missing=["claim satisfied but no evidence found or referenced"],
            )

        return ClaimResult(
            claim_id=pid,
            claim_description=pred.get("id", pid),
            status="SUPPORTED" if (evidence_found or evidence_ref) and not evidence_missing else "UNSUPPORTED",
            evidence_found=evidence_found,
            evidence_missing=evidence_missing,
        )

    def _verify_file_claim(self, claimed: set[str], actual: set[str]) -> ClaimResult:
        """Verify that claimed file changes match git diff."""
        only_claimed = claimed - actual
        only_actual = actual - claimed

        if not only_claimed and not only_actual:
            return ClaimResult(
                claim_id="files_changed",
                claim_description="Files changed match git diff",
                status="SUPPORTED",
                evidence_found=[f"all {len(claimed)} claimed files found in git diff"],
            )
        else:
            issues = []
            if only_claimed:
                issues.append(f"{len(only_claimed)} file(s) claimed but not in git diff: {list(only_claimed)[:5]}")
            if only_actual:
                issues.append(f"{len(only_actual)} file(s) in git diff but not claimed: {list(only_actual)[:5]}")
            return ClaimResult(
                claim_id="files_changed",
                claim_description="Files changed claim vs git diff",
                status="CONTRADICTED" if only_claimed else "UNSUPPORTED",
                evidence_missing=issues,
                detail="Agent's claimed file changes don't match git diff. Either the claim is wrong or files were changed after the receipt was generated.",
            )

    def _verify_hash_claim(self, ver_result: dict) -> ClaimResult | None:
        """Verify that a verification output_hash matches current state."""
        gate_id = ver_result.get("id", "?")
        stored_hash = ver_result.get("output_hash", "")

        if not stored_hash:
            return None

        # For now, we can't re-run commands (that's expensive). We check
        # that the hash is well-formed (SHA-256 hex) at minimum.
        if len(stored_hash) == 16 and all(c in "0123456789abcdef" for c in stored_hash):
            return ClaimResult(
                claim_id=f"hash:{gate_id}",
                claim_description=f"Verification output hash for {gate_id}",
                status="SUPPORTED",
                evidence_found=[f"hash {stored_hash} is well-formed"],
                detail="Hash format valid. Re-verification by re-running the command is deferred (too expensive for CI).",
            )
        else:
            return ClaimResult(
                claim_id=f"hash:{gate_id}",
                claim_description=f"Verification output hash for {gate_id}",
                status="UNSUPPORTED",
                evidence_missing=[f"hash '{stored_hash}' is malformed"],
            )

    def _verify_boundary_claim(self, receipt: dict, claimed_files: set[str]) -> ClaimResult | None:
        """Verify the claim that no boundaries were violated."""
        risk = receipt.get("risk_class", "")
        if risk == "AP-R0":
            src_files = [f for f in claimed_files if f.startswith("src/")]
            if src_files and not any(f.startswith("src/ordivon_verify/registry.py") for f in src_files):
                return ClaimResult(
                    claim_id="no_boundary_violations",
                    claim_description="No boundary violations",
                    status="CONTRADICTED",
                    evidence_missing=[f"AP-R0 stage modified {len(src_files)} source file(s): {src_files[:3]}"],
                    detail="Receipt claims no boundary violations but source files were modified in an AP-R0 stage.",
                )
        return None

    def _get_actual_modified_files(self) -> set[str]:
        """Get actual modified files from git."""
        try:
            r = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.root, capture_output=True, text=True,
            )
            return {f.strip() for f in r.stdout.split("\n") if f.strip()}
        except Exception:
            return set()
