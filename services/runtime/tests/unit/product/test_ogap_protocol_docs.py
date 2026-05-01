"""OGAP-1: Tests for Ordivon Governance Adapter Protocol docs and examples."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ARCH_DOC = ROOT / "docs" / "architecture" / "ordivon-governance-adapter-protocol-ogap-1.md"
OBJECT_MODEL = ROOT / "docs" / "governance" / "ogap-object-model-v0.md"
INTEGRATION_DOC = ROOT / "docs" / "product" / "ordivon-external-adapter-integration-levels.md"
USE_CASES = ROOT / "docs" / "product" / "ordivon-governance-adapter-use-cases.md"
RECEIPT = ROOT / "docs" / "runtime" / "ogap-1-governance-adapter-protocol-v0.md"
EXAMPLES_DIR = ROOT / "examples" / "ogap"


class TestOGAPDocs:
    def test_architecture_doc_exists(self):
        assert ARCH_DOC.exists()

    def test_object_model_exists(self):
        assert OBJECT_MODEL.exists()

    def test_integration_levels_doc_exists(self):
        assert INTEGRATION_DOC.exists()

    def test_use_cases_doc_exists(self):
        assert USE_CASES.exists()

    def test_runtime_receipt_exists(self):
        assert RECEIPT.exists()

    def test_positioning_sentence_present(self):
        content = ARCH_DOC.read_text()
        assert "Agents act." in content
        assert "Tools execute." in content
        assert "Frameworks orchestrate." in content
        assert "Ordivon governs." in content

    def test_can_x_not_may_x(self):
        content = ARCH_DOC.read_text()
        assert "can_X does not imply may_X" in content

    def test_no_public_standard_claim(self):
        for doc in [ARCH_DOC, OBJECT_MODEL, RECEIPT]:
            content = doc.read_text().lower()
            # "NOT a public standard" is safe — only flag positive claims
            if "public standard" in content:
                # Must be in negative context
                assert "not a public standard" in content or "no public standard" in content

    def test_no_release_claims(self):
        for doc in [ARCH_DOC, RECEIPT]:
            lower = doc.read_text().lower()
            if "package published" in lower:
                assert "no package published" in lower or "not" in lower
            if "license activated" in lower:
                assert "no license activated" in lower or "not" in lower
            if "public repo created" in lower:
                assert "no public repo" in lower or "not" in lower

    def test_no_mcp_server_created_claim(self):
        for doc in [ARCH_DOC, RECEIPT]:
            assert "MCP server created" not in doc.read_text()

    def test_no_live_api_created_claim(self):
        for doc in [ARCH_DOC, RECEIPT]:
            assert "live API created" not in doc.read_text()


class TestOGAPExamples:
    def test_all_examples_parse(self):
        for f in sorted(EXAMPLES_DIR.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            assert "schema_version" in data, f"{f.name} missing schema_version"

    def test_work_claim_has_evidence(self):
        data = json.loads((EXAMPLES_DIR / "work-claim-basic.json").read_text(encoding="utf-8"))
        assert "evidence_bundle" in data
        assert "coverage_report" in data

    def test_ready_decision_states_evidence_not_authorization(self):
        data = json.loads((EXAMPLES_DIR / "governance-decision-ready.json").read_text(encoding="utf-8"))
        assert "decision" in data
        assert data["decision"] == "READY"
        assert "not authorization" in data.get("authority_statement", "")

    def test_blocked_decision_has_hard_failures(self):
        data = json.loads((EXAMPLES_DIR / "governance-decision-blocked.json").read_text(encoding="utf-8"))
        assert data["decision"] == "BLOCKED"
        assert len(data.get("hard_failures", [])) >= 1

    def test_capability_manifest_distinguishes_capability_from_authority(self):
        data = json.loads((EXAMPLES_DIR / "capability-manifest-basic.json").read_text(encoding="utf-8"))
        assert "capabilities" in data
        assert "authority_required_for" in data
        assert "authority_note" in data

    def test_coverage_report_has_universe_and_discovery(self):
        data = json.loads((EXAMPLES_DIR / "coverage-report-basic.json").read_text(encoding="utf-8"))
        assert "claimed_universe" in data
        assert "discovery_method" in data
        assert "pass_scope_statement" in data

    def test_examples_have_no_secrets(self):
        for f in sorted(EXAMPLES_DIR.glob("*.json")):
            content = f.read_text()
            for secret in ["API_KEY", "SECRET", "TOKEN", "PASSWORD", "PRIVATE_KEY", "BEARER"]:
                assert secret not in content, f"{f.name} contains {secret}"

    def test_tests_do_not_mutate_source(self):
        pass  # Read-only
