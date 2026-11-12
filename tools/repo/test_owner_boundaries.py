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

    def test_tracked_active_owner_paths_are_native_git_byte_records(self) -> None:
        """A quoted newline filename cannot hide an active cross-owner seam."""
        import os
        import subprocess
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(["git", "init", "-q", "-b", "main", folder], check=True)
            paths = ["apps/web/src/newline\nsource.ts"]
            if os.name != "nt":
                paths.append(os.fsdecode(b"apps/web/src/nonutf8-\xff.ts"))
            for name in paths:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('const source = "platform/security";\n', encoding="utf-8")
            subprocess.run(["git", "-C", folder, "add", "--all"], check=True)
            with patch.object(MODULE, "ROOT", root):
                actual = set(MODULE.tracked_active_files())
                self.assertEqual(actual, set(paths))
                for name in paths:
                    source = (root / name).read_text(encoding="utf-8")
                    observed = MODULE.findings_for_text(name, source, OWNERS)
                    self.assertEqual(len(observed), 1)
                    self.assertEqual(observed[0].to_owner, "security")

    def test_identical_cross_owner_seam_is_rejected(self) -> None:
        """A repeated source/consumer relation is one LEGO, never two grants."""
        import tempfile

        original = MODULE.POLICY.read_text(encoding="utf-8")
        block = original.split("[[seams]]", 2)[1]
        with tempfile.TemporaryDirectory() as folder:
            policy = Path(folder) / "duplicate-seam.toml"
            policy.write_text(original + "\n[[seams]]" + block, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate dependency seam"):
                MODULE.load_policy(policy)

    def test_unused_exception_is_not_rescued_by_unrelated_literal_on_same_path(self) -> None:
        """Source/Owner/path coincidence is NOT a witness for this exception."""
        real = next(
            seam for seam in SEAMS
            if seam.source_glob == "apps/web/src/security-agent-verifier.ts"
        )
        broken = MODULE.Seam(
            real.from_owner, real.to_owner, real.source_glob,
            "platform/security/retired-private-api/", real.kind, real.contract_ref,
        )
        observed = self.finding(
            real.source_glob,
            'from "../../../platform/security/contracts/agent-request-verifier-v1/src/index.ts";',
        )
        with self.assertRaisesRegex(AssertionError, "stale dependency seam declarations"):
            MODULE.validate_consumed_seams((broken,), (observed,))

    def test_ambiguous_policy_exceptions_cannot_double_authorize_one_literal(self) -> None:
        """Two grants over one literal would hide a redundant permission."""
        real = next(
            seam for seam in SEAMS
            if seam.source_glob == "apps/web/src/security-agent-verifier.ts"
        )
        alias = MODULE.Seam(
            real.from_owner, real.to_owner, real.source_glob,
            "platform/security/contracts", real.kind, real.contract_ref,
        )
        observed = self.finding(
            real.source_glob,
            'from "../../../platform/security/contracts/agent-request-verifier-v1/src/index.ts";',
        )
        with self.assertRaisesRegex(AssertionError, "ambiguous dependency seam"):
            MODULE.validate_consumed_seams((real, alias), (observed,))

    def test_sibling_prefix_does_not_create_cross_owner_dependency(self) -> None:
        source = "platform/security/mise.toml"
        for path in (
            "services/gateway-authzen",
            "services/gateway_extra",
            "services/gateway2",
            "prefixservices/gateway-src",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    MODULE.findings_for_text(source, f'run = "{path}"', OWNERS),
                    (),
                )

    def test_real_gateway_path_still_requires_cross_owner_contract(self) -> None:
        observed = MODULE.findings_for_text(
            "platform/security/mise.toml",
            'command = "services/gateway/src/ordivon_gateway/mcp_server.py"',
            OWNERS,
        )
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0].to_owner, "gateway")

    def test_current_declared_source_consumers_are_literal_matched(self) -> None:
        """This is a bounded source-text witness, not live consumer semantics."""
        findings = []
        for path in MODULE.tracked_active_files():
            if MODULE.owner_for_path(path, OWNERS) is None:
                continue
            source = (MODULE.ROOT / path).read_text(encoding="utf-8", errors="ignore")
            findings.extend(MODULE.findings_for_text(path, source, OWNERS))
        witnessed = MODULE.validate_consumed_seams(SEAMS, tuple(findings))
        self.assertEqual(set(witnessed), set(SEAMS))
        self.assertTrue(all(witnessed.values()))

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

    def test_external_authority_records_are_navigation_not_runtime_edges(self) -> None:
        self.assertFalse(MODULE.is_active_path(
            "catalogs/authorities/records/iso/iso-28500-2017.json"
        ))

    def test_meta_next_domain_knowledge_is_navigation_not_runtime_edges(self) -> None:
        self.assertFalse(MODULE.is_active_path(
            "profiles/domains/game/game-autonomous-interest-protocol-r7.json"
        ))

    def test_python_owner_packages_derive_from_source_roots(self) -> None:
        paths = (
            "services/host/src/ordivon_host_v2/__init__.py",
            "services/harness/src/ordivon_harness/__init__.py",
            "services/harness/src/ordivon_harness/internal/__init__.py",
        )
        self.assertEqual(
            MODULE.python_package_owners(paths, OWNERS),
            {"ordivon_host_v2": "host", "ordivon_harness": "harness"},
        )

    def test_ast_catches_cross_owner_import_without_path_literal(self) -> None:
        path = "services/harness/src/ordivon_harness/foreign_effect.py"
        text = "from ordivon_host_v2.work_store import WorkStore"
        namespaces = {"ordivon_host_v2": "host"}
        self.assertEqual(MODULE.findings_for_text(path, text, OWNERS), ())
        findings = MODULE.python_import_findings_for_text(
            path, text, OWNERS, namespaces
        )
        self.assertEqual(len(findings), 1)
        self.assertEqual((findings[0].from_owner, findings[0].to_owner), ("harness", "host"))
        self.assertFalse(MODULE._allowed(findings[0], SEAMS))

    def test_import_alias_and_own_package_do_not_depend_on_model_wording(self) -> None:
        path = "services/harness/src/ordivon_harness/foreign_effect.py"
        namespaces = {"ordivon_host_v2": "host", "ordivon_harness": "harness"}
        foreign = MODULE.python_import_findings_for_text(
            path, "import ordivon_host_v2.work_store as storage", OWNERS, namespaces
        )
        self.assertEqual(len(foreign), 1)
        self.assertEqual(foreign[0].import_module, "ordivon_host_v2.work_store")
        self.assertEqual(MODULE.python_import_findings_for_text(
            path, "import ordivon_harness.run_continuity", OWNERS, namespaces
        ), ())

    def test_public_python_import_needs_source_and_contract_bound_seam(self) -> None:
        path = "services/harness/src/ordivon_harness/public_bridge.py"
        namespaces = {"ordivon_host_v2": "host"}
        seam = MODULE.Seam(
            "harness", "host", path, "ordivon_host_v2.public_api",
            "PUBLIC_PACKAGE_DEPENDENCY", "services/host/README.md",
        )
        def inspect(source_path: str, text: str):
            return MODULE.python_import_findings_for_text(
                source_path, text, OWNERS, namespaces
            )[0]
        self.assertTrue(MODULE._allowed(
            inspect(path, "from ordivon_host_v2.public_api import PublicReceipt"), (seam,)
        ))
        self.assertFalse(MODULE._allowed(
            inspect("services/harness/src/ordivon_harness/other.py",
                    "from ordivon_host_v2.public_api import PublicReceipt"), (seam,)
        ))
        self.assertFalse(MODULE._allowed(
            inspect(path, "from ordivon_host_v2.work_store import WorkStore"), (seam,)
        ))
        self.assertFalse(MODULE._allowed(
            inspect(path, "from ordivon_host_v2.public_api_private import Leaked"), (seam,)
        ))
        self.assertFalse(MODULE._allowed(
            inspect(path, "from ordivon_host_v2.work_store import WorkStore # ordivon_host_v2.public_api"), (seam,)
        ))

    def test_real_web_source_is_scanned(self) -> None:
        self.assertTrue(MODULE.is_active_path("apps/web/src/security-agent-verifier.ts"))


if __name__ == "__main__":
    unittest.main()
