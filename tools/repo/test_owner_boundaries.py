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

    def test_source_glob_grants_only_one_path_segment(self) -> None:
        same_directory = self.finding(
            "services/harness/scripts/browser_security_probe.py",
            'source = "platform/security"',
        )
        nested_directory = self.finding(
            "services/harness/scripts/browser_security_probe/escape.py",
            'source = "platform/security"',
        )
        self.assertTrue(MODULE._allowed(same_directory, SEAMS))
        self.assertFalse(
            MODULE._allowed(nested_directory, SEAMS),
            "a single '*' in a source_glob must not authorize a different directory",
        )

    def test_web_cold_ci_consumes_security_owner_lock_once(self) -> None:
        """Direct pnpm ci and mise verify must reach one Security lock authority."""
        import json
        import tomllib

        root = Path(__file__).resolve().parents[2]
        pkg = json.loads((root / "apps/web/package.json").read_text(encoding="utf-8"))
        mise = tomllib.loads((root / "apps/web/mise.toml").read_text(encoding="utf-8"))
        install = (
            "pnpm --dir ../../platform/security/contracts/"
            "agent-request-verifier-v1 install --frozen-lockfile"
        )
        self.assertIn(install, pkg["scripts"]["ci"])
        self.assertNotIn(install, mise["tasks"]["verify"]["run"])
        self.assertIn("pnpm run ci", mise["tasks"]["verify"]["run"])
        actual = self.finding(
            "apps/web/package.json",
            '"ci": "' + install + ' && pnpm typecheck && pnpm test"',
        )
        self.assertTrue(MODULE._allowed(actual, SEAMS))
        stale = self.finding("apps/web/mise.toml", install)
        self.assertFalse(MODULE._allowed(stale, SEAMS))

    def test_unrelated_web_file_cannot_gain_security_contract_by_owner_pair(self) -> None:
        finding = self.finding(
            "apps/web/src/store.ts",
            'const root = "../../../platform/security/contracts/agent-request-verifier-v1/";',
        )
        self.assertFalse(MODULE._allowed(finding, SEAMS))

    def test_meta_next_authority_records_are_navigation_not_runtime_edges(self) -> None:
        self.assertFalse(MODULE.is_active_path(
            "meta/next/authorities/records/iso/iso-28500-2017.json"
        ))

    def test_meta_next_domain_knowledge_is_navigation_not_runtime_edges(self) -> None:
        self.assertFalse(MODULE.is_active_path(
            "meta/next/domains/game/game-autonomous-interest-protocol-r7.json"
        ))

    def test_real_web_source_is_scanned(self) -> None:
        self.assertTrue(MODULE.is_active_path("apps/web/src/security-agent-verifier.ts"))


if __name__ == "__main__":
    unittest.main()
