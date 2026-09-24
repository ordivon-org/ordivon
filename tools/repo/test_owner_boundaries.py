#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("check_owner_boundaries.py")
SPEC = importlib.util.spec_from_file_location("check_owner_boundaries", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

OWNERS = MODULE.load_owners()
SEAMS = MODULE.load_policy()


class OwnerBoundaryTests(unittest.TestCase):
    def finding(self, source_path: str, line: str):
        findings = MODULE.findings_for_text(source_path, line, OWNERS)
        self.assertEqual(len(findings), 1)
        return findings[0]

    def test_public_security_contract_is_allowed(self) -> None:
        finding = self.finding(
            "apps/web/src/security-agent-verifier.ts",
            'from "../../../platform/security/contracts/agent-request-verifier-v1/src/index.ts";',
        )
        self.assertTrue(MODULE._allowed(finding, SEAMS))

    def test_security_internal_source_is_not_covered_by_public_contract(self) -> None:
        finding = self.finding(
            "apps/web/src/security-agent-verifier.ts",
            'from "../../../platform/security/src/ordivon_security_v2/evidence.py";',
        )
        self.assertFalse(MODULE._allowed(finding, SEAMS))

    def test_unrelated_web_file_cannot_gain_security_contract_by_owner_pair(self) -> None:
        finding = self.finding(
            "apps/web/src/store.ts",
            'const root = "../../../platform/security/contracts/agent-request-verifier-v1/";',
        )
        self.assertFalse(MODULE._allowed(finding, SEAMS))

    def test_meta_next_authority_records_are_navigation_not_runtime_edges(self) -> None:
        self.assertFalse(MODULE.is_active_path(
            "catalogs/authorities/records/iso/iso-28500-2017.json"
        ))

    def test_catalog_knowledge_is_navigation_not_runtime_edges(self) -> None:
        self.assertFalse(MODULE.is_active_path(
            "catalogs/knowledge/graphs/agent-architecture-lego-catalog-r1.json"
        ))

    def test_real_web_source_is_scanned(self) -> None:
        self.assertTrue(MODULE.is_active_path("apps/web/src/security-agent-verifier.ts"))


if __name__ == "__main__":
    unittest.main()
