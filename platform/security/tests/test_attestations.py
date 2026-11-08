import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2.attestations import (
    REFERENCE_PREDICATE,
    STATEMENT_TYPE,
    VSA_PREDICATE,
    reference_statement,
    subject_descriptor,
    vsa_statement,
)
from ordivon_security_v2.evidence import EvidenceRef, build_gate_input

OWNER = Path(__file__).resolve().parents[1]
PROVIDERS = (
    ("gitleaks", "sarif", "gitleaks.sarif"),
    ("semgrep", "sarif", "semgrep.sarif"),
    ("trivy", "sarif", "trivy.sarif"),
    ("syft", "cyclonedx-json", "sbom.cdx.json"),
    ("osv-scanner", "json", "osv.json"),
)


class AttestationTests(unittest.TestCase):
    def test_reference_statement_uses_in_toto_v1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "report.json"
            artifact.write_text("{}\n", encoding="utf-8")
            subject = subject_descriptor(name="repo", git_commit="a" * 40)
            statement = reference_statement(
                subject=subject,
                attester_id="https://example.invalid/verifier",
                reference_path=artifact,
            )
            self.assertEqual(statement["_type"], STATEMENT_TYPE)
            self.assertEqual(statement["predicateType"], REFERENCE_PREDICATE)
            self.assertEqual(statement["subject"][0]["digest"], {"gitCommit": "a" * 40})

    def test_vsa_failed_does_not_claim_slsa_level(self) -> None:
        subject = subject_descriptor(name="repo", git_commit="b" * 40)
        statement = vsa_statement(
            subject=subject,
            verifier_id="https://example.invalid/verifier",
            verifier_versions={"verifier": "1"},
            resource_uri="git+https://example.invalid/repo",
            policy_uri="file:///policy.rego",
            policy_sha256="c" * 64,
            input_attestations=[],
            passed=False,
        )
        self.assertEqual(statement["predicateType"], VSA_PREDICATE)
        self.assertEqual(statement["predicate"]["verificationResult"], "FAILED")
        self.assertEqual(statement["predicate"]["verifiedLevels"], ["FAILED"])


class AttestationEmissionBoundaryTests(unittest.TestCase):
    """Use real native OPA decisions and exact on-disk provider reports."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        self.output = self.root / "emitted"
        self.revision = "a" * 40

    def create_gate(self, *, finding: bool = False) -> None:
        references = []
        results = []
        for provider, format_name, filename in PROVIDERS:
            file = self.artifacts / filename
            file.write_text('{"runs":[]}', encoding="utf-8")
            references.append(EvidenceRef.from_path(
                provider=provider, format=format_name, path=file
            ))
            blocked = finding and provider == "osv-scanner"
            results.append({
                "provider": provider,
                "exitCode": 1 if blocked else 0,
                "mechanicalSuccess": True,
                "blocking": blocked,
            })
        status = {
            "profile": "product",
            "observedSubjectRevision": self.revision,
            "providers": results,
        }
        status_path = self.artifacts / "provider-status.json"
        status_path.write_text(json.dumps(status), encoding="utf-8")
        references.append(EvidenceRef.from_path(
            provider="ordivon-runner", format="json", path=status_path
        ))
        gate = build_gate_input(
            subject_ref="git+https://github.com/ordivon-org/ordivon.git",
            subject_revision=self.revision,
            evidence=references,
            authority="security-verification",
        )
        gate["observedSubjectRevision"] = self.revision
        gate["providerResults"] = results
        self.gate = self.root / "gate-input.json"
        self.gate.write_text(json.dumps(gate), encoding="utf-8")
        decision = subprocess.run(
            [
                "opa", "eval", "--format=raw", "--data",
                str(OWNER / "policies/admission.rego"),
                "--stdin-input", "data.ordivon.security.v2.decision",
            ],
            input=json.dumps(gate),
            text=True,
            check=True,
            capture_output=True,
        )
        self.decision = self.root / "decision.json"
        self.decision.write_text(decision.stdout, encoding="utf-8")

    def emit(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable, str(OWNER / "scripts/emit_attestations.py"),
                "--gate-input", str(self.gate),
                "--decision", str(self.decision),
                "--output-dir", str(self.output),
                "--subject-name", "ordivon",
                "--verifier-revision", self.revision,
                "--policy", str(OWNER / "policies/admission.rego"),
            ],
            cwd=OWNER,
            env={**os.environ, "PYTHONPATH": str(OWNER / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

    def test_emits_vsa_only_when_status_and_policy_are_bound(self) -> None:
        self.create_gate()
        run = self.emit()
        self.assertEqual(run.returncode, 0, run.stderr)
        statement = json.loads(
            (self.output / "verification-summary.vsa.intoto.json").read_text()
        )
        self.assertEqual(statement["predicateType"], VSA_PREDICATE)
        self.assertEqual(statement["predicate"]["verificationResult"], "PASSED")
        self.assertEqual(len(statement["predicate"]["inputAttestations"]), 6)

    def test_rejects_mutated_evidence_before_writing_vsa(self) -> None:
        self.create_gate()
        (self.artifacts / "gitleaks.sarif").write_bytes(b'{"new":"content"}')
        run = self.emit()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("changed after gate binding", run.stderr)
        self.assertFalse((self.output / "verification-summary.vsa.intoto.json").exists())

    def test_rejects_forged_current_decision_for_blocked_provider(self) -> None:
        self.create_gate(finding=True)
        decision = json.loads(self.decision.read_text())
        self.assertEqual(decision["standing"], "BLOCKED")
        decision["standing"] = "CURRENT"
        decision["allow"] = True
        self.decision.write_text(json.dumps(decision), encoding="utf-8")
        run = self.emit()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("does not match current policy", run.stderr)
        self.assertFalse((self.output / "verification-summary.vsa.intoto.json").exists())

    def test_rejects_report_result_rebinding_without_new_receipt(self) -> None:
        self.create_gate()
        gate = json.loads(self.gate.read_text())
        gate["providerResults"][0]["exitCode"] = 1
        gate["providerResults"][0]["blocking"] = True
        self.gate.write_text(json.dumps(gate), encoding="utf-8")
        run = self.emit()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("provider receipt and gate results differ", run.stderr)


if __name__ == "__main__":
    unittest.main()
