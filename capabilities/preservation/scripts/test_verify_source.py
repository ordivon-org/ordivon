#!/usr/bin/env python3
"""Preservation source-boundary contract, including optimized Python execution."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_source.py")
FIXITY_CONTRACT = SCRIPT.with_name("fixity_consumer_contract.py")
BOUNDARY = SCRIPT.parents[1] / "SOURCE_BOUNDARY.json"

# Run the real verifier entry point, with only its JSON input substituted.
# In particular Python -O must not disable the owner boundary guarantee.
RUN_VERIFIER = """
import importlib.util
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve().parent))
spec = importlib.util.spec_from_file_location("preservation_source", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.BOUNDARY = Path(sys.argv[2])
if len(sys.argv) > 3:
    mode = sys.argv[3]
    original_load = module.yaml.safe_load
    def candidate_with_injected_compose_fault(stream):
        compose = original_load(stream)
        service = compose["services"].get("archivematica-storage-service")
        if mode == "drop-storage-service":
            compose["services"].pop("archivematica-storage-service", None)
        elif mode == "omit-host-port":
            service.pop("ports", None)
        elif mode == "expose-public-interface":
            service["ports"] = ["0.0.0.0:62081:8000"]
        elif mode == "wrong-host-port":
            service["ports"] = ["127.0.0.1:62082:8000"]
        else:
            raise ValueError("unknown injected fault " + mode)
        return compose
    module.yaml.safe_load = candidate_with_injected_compose_fault
raise SystemExit(module.main())
"""


class SourceBoundaryContractTests(unittest.TestCase):
    def verify(
        self,
        data: dict,
        *,
        optimized: bool,
        drop_storage: bool = False,
        injected_fault: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            boundary = Path(directory) / "SOURCE_BOUNDARY.json"
            boundary.write_text(json.dumps(data), encoding="utf-8")
            fault = "drop-storage-service" if drop_storage else injected_fault
            return subprocess.run(
                [
                    sys.executable,
                    *(["-O"] if optimized else []),
                    "-c",
                    RUN_VERIFIER,
                    str(SCRIPT),
                    str(boundary),
                    *([fault] if fault else []),
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

    def test_accepted_source_manifest_in_normal_and_optimized_python(self) -> None:
        valid = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.verify(valid, optimized=optimized)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_owner_local_lego_plan_requires_explicit_manifest_admission(self) -> None:
        """A newly added planning artifact is normal payload, never a free bypass."""
        valid = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        assert "planning/lego-plan-r1.json" in valid["includedPaths"]
        assert (BOUNDARY.parent / "planning/lego-plan-r1.json").is_file()
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                altered = copy.deepcopy(valid)
                altered["includedPaths"].remove("planning/lego-plan-r1.json")
                result = self.verify(altered, optimized=optimized)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("escaped SOURCE_BOUNDARY", result.stderr)
                self.assertIn("planning/lego-plan-r1.json", result.stderr)

    def test_patterns_do_not_match_across_directory_boundaries(self) -> None:
        import importlib.util

        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("preservation_source", SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(
            module._matches(
                "docs/creative-preservation-pilot.md",
                "docs/creative-preservation-*.md",
            )
        )
        self.assertFalse(
            module._matches(
                "docs/creative-preservation-nested/inside.md",
                "docs/creative-preservation-*.md",
            ),
            "a single-segment glob must never match a nested unregistered path",
        )
        self.assertTrue(
            module._matches(
                "artifacts/creative-preservation/subdir/a.bin",
                "artifacts/creative-preservation/**",
            )
        )

    def test_missing_required_storage_service_rejected_without_asserts(self) -> None:
        valid = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                result = self.verify(valid, optimized=optimized, drop_storage=True)
                self.assertNotEqual(
                    result.returncode,
                    0,
                    "missing Archivematica storage service silently accepted",
                )

    def test_host_fixity_port_binding_rejects_absence_exposure_and_mismatch(
        self,
    ) -> None:
        # CEGAR A0: a named running Compose service may lack a published route.
        # A1: reject missing, world-exposed and mismatched host port contracts.
        valid = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        for case in ("omit-host-port", "expose-public-interface", "wrong-host-port"):
            for optimized in (False, True):
                with self.subTest(case=case, optimized=optimized):
                    result = self.verify(
                        valid, optimized=optimized, injected_fault=case
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("loopback 127.0.0.1:62081", result.stderr)

    def test_rejects_invalid_authority_and_identity_in_optimized_python(self) -> None:
        valid = json.loads(BOUNDARY.read_text(encoding="utf-8"))
        cases = (
            ("kind", "ordivon.untrusted-preservation"),
            ("runtime-owned", True),
            ("not-local", False),
        )
        for name, wrong_value in cases:
            with self.subTest(name=name):
                altered = copy.deepcopy(valid)
                if name == "kind":
                    altered["kind"] = wrong_value
                elif name == "runtime-owned":
                    altered["authorityBoundary"]["runtimeFrameworkOwnedByOrdivon"] = (
                        wrong_value
                    )
                else:
                    altered["authorityBoundary"]["localProfileOnly"] = wrong_value
                result = self.verify(altered, optimized=True)
                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"optimized Python bypassed source-boundary contract: {name}: "
                    f"{result.stdout}{result.stderr}",
                )




class FormalLegoDeclarationTests(unittest.TestCase):
    """The four consumed Preservation LEGO seams need explicit proof obligations.

    These are source-test witnesses, not a model-checker PASS or installed Fixity.
    """

    def test_pv_contracts_have_scoped_unproven_formal_obligations(self) -> None:
        import importlib.util

        # Reuse the canonical phase-1 declaration predicate, not another schema.
        native_path = BOUNDARY.parent.parents[1] / "tools/repo/exhaustive_coverage.py"
        spec = importlib.util.spec_from_file_location("native_coverage", native_path)
        assert spec is not None and spec.loader is not None
        native = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(native)

        plan = json.loads(
            (BOUNDARY.parent / "planning/lego-plan-r1.json").read_text(encoding="utf-8")
        )
        nodes = {node["id"]: node for node in plan["nodes"]}
        self.assertEqual(set(nodes), {"PV00", "PV01", "PV02", "PV03"})
        for name, node in nodes.items():
            with self.subTest(node=name):
                self.assertEqual(
                    node.get("formalQualification"),
                    "DECLARED_SOURCE_ONLY_TESTED_NOT_MATHEMATICALLY_PROVED",
                )
                obligations = node.get("formalObligations")
                self.assertIsInstance(obligations, list)
                self.assertTrue(obligations)
                for item in obligations:
                    self.assertEqual(
                        set(item),
                        {"id", "predicate", "scope", "nativeWitness", "proofStanding"},
                    )
                    self.assertTrue(item["id"].startswith(name + ":"))
                    self.assertTrue(item["predicate"].strip())
                    self.assertEqual(item["scope"], "ORIGINAL_GIT_SOURCE_ONLY")
                    self.assertEqual(item["proofStanding"], "FINITE_NATIVE_TEST_NOT_FORMAL_PROOF")
                    class_name, test_name = item["nativeWitness"].split(".", 1)
                    cls = globals()[class_name]
                    self.assertTrue(callable(getattr(cls, test_name, None)))
                # An omitted obligation cannot remain a qualified declaration
                # merely because the owner has acceptance or source evidence.
                self.assertTrue(
                    native.declared_values(node, native.FIELDS["FORMAL"])
                )
                stripped = {
                    key: value
                    for key, value in node.items()
                    if key not in ("formalObligations", "formalQualification")
                }
                self.assertFalse(
                    native.declared_values(stripped, native.FIELDS["FORMAL"])
                )

# Source-only negative controls: no Docker/Systemd mutation and no reading
# of private credential environment bytes. Under -O the same verifier must
# reject a timer silently redirected to a different service.
FIXITY_SOURCE_CONSUMER = """
import importlib.util
import sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("preservation_fixity_consumer", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
root = Path(sys.argv[1]).resolve().parents[1]
service = (root / "systemd/ordivon-preservation-fixity-r7.service").read_text()
timer = (root / "systemd/ordivon-preservation-fixity-r7.timer").read_text()
mode = sys.argv[2]
if mode == "foreign-timer-unit":
    timer = timer.replace("Unit=ordivon-preservation-fixity-r7.service",
                          "Unit=unrelated.service")
elif mode == "wrong-environment":
    service = service.replace("EnvironmentFile=/etc/ordivon/fixity-r7.env",
                              "EnvironmentFile=/etc/ordivon/other.env")
elif mode == "wrong-local-provider":
    service = service.replace("fixity scanall --force-local",
                              "fixity scanall --unsafe-external")
elif mode == "no-schedule":
    timer = timer.replace("OnCalendar=Sun *-*-* 03:17:00 Asia/Singapore",
                          "OnCalendar=")
elif mode != "accepted":
    raise ValueError("unrecognized synthetic fault mode")
module.verify_fixity_consumer_binding(service, timer)
"""


class FixityConsumerSourceContractTests(unittest.TestCase):
    def run_consumer(
        self,
        mode: str,
        *,
        optimized: bool,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                *(["-O"] if optimized else []),
                "-c",
                FIXITY_SOURCE_CONSUMER,
                str(FIXITY_CONTRACT),
                mode,
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def test_exact_source_bound_consumer_is_admitted_without_provider_calls(
        self,
    ) -> None:
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                outcome = self.run_consumer("accepted", optimized=optimized)
                self.assertEqual(outcome.returncode, 0, outcome.stderr)

    def test_wrong_timer_environment_provider_or_schedule_fail_closed(self) -> None:
        for fault in (
            "foreign-timer-unit",
            "wrong-environment",
            "wrong-local-provider",
            "no-schedule",
        ):
            for optimized in (False, True):
                with self.subTest(fault=fault, optimized=optimized):
                    outcome = self.run_consumer(fault, optimized=optimized)
                    self.assertNotEqual(outcome.returncode, 0, fault)
                    self.assertIn("ValueError", outcome.stderr)


if __name__ == "__main__":
    unittest.main()
