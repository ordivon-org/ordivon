from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import artifact_capabilities.publication.provider_adapter as provider_adapter

ROOT = Path(__file__).resolve().parents[1]

from artifact_capabilities.publication.perceptual import evaluate_perceptual_conformance
from artifact_capabilities.publication.provider_adapter import (
    PerceptualProviderAdapterError,
    ProviderExecutionSpec,
    run_observer_provider,
)


class PublicationProviderAdapterR1Tests(unittest.TestCase):
    CARRIER = "sha256:" + "a" * 64

    def test_provider_contract_exposes_receipt_binding_loader(self) -> None:
        self.assertTrue(hasattr(provider_adapter, "load_provider_bound_observer_reports"))

    def test_provider_contract_accepts_owner_bound_lineage(self) -> None:
        self.assertIn(
            "lineage_refs",
            inspect.signature(run_observer_provider).parameters,
        )

    def _fixture(
        self,
        root: Path,
        *,
        provider_role: str = "BLIND_VISION",
        observer_id: str = "fixture-observer",
    ) -> tuple[Path, Path, Path]:
        packet = root / "packet"
        packet.mkdir()
        (packet / "packet-manifest-r1.json").write_text(
            json.dumps({"schemaVersion": 1, "kind": "packet"}), encoding="utf-8"
        )
        envelope = root / "envelope.json"
        envelope.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "kind": "publication-perceptual-observer-task",
                    "taskId": "PC10-TEST",
                    "role": provider_role,
                    "carrierSha256": self.CARRIER,
                }
            ),
            encoding="utf-8",
        )
        provider = root / "provider.py"
        provider.write_text(
            textwrap.dedent(
                f"""
                import argparse, json
                p=argparse.ArgumentParser()
                p.add_argument("--task-envelope")
                p.add_argument("--packet-root")
                p.add_argument("--output")
                p.add_argument("--independence-key")
                a=p.parse_args()
                envelope=json.load(open(a.task_envelope))
                value={{
                  "schemaVersion":1,
                  "kind":"publication-perceptual-observer-report",
                  "observerId":"{observer_id}",
                  "role":"{provider_role}",
                  "independenceKey":a.independence_key,
                  "carrierSha256":envelope["carrierSha256"],
                  "standing":"PASS",
                  "inputScope":{{"allowed":[],"forbidden":[]}},
                  "coverage":{{
                    "pagesExpected":20,"pagesReviewed":20,
                    "figuresExpected":4,"figuresReviewed":4,
                    "tablesExpected":5,"tablesReviewed":5
                  }},
                  "findings":[]
                }}
                with open(a.output,"w",encoding="utf-8") as f:
                    json.dump(value,f)
                """
            ),
            encoding="utf-8",
        )
        return packet, envelope, provider

    def test_direct_local_receipts_cannot_supply_pass_enabling_execution_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report_paths: list[Path] = []
            receipt_paths: list[Path] = []
            fixtures = (
                ("BLIND_VISION", "vision-a", "attempt-a"),
                ("VENUE_AWARE_VISION", "vision-b", "attempt-b"),
                ("SEMANTIC_LAYOUT", "layout-c", "attempt-c"),
            )
            for role, observer_id, independence_key in fixtures:
                fixture_root = root / observer_id
                fixture_root.mkdir()
                packet, envelope, provider = self._fixture(
                    fixture_root,
                    provider_role=role,
                    observer_id=observer_id,
                )
                output = fixture_root / "observer.json"
                receipt_path = fixture_root / "receipt.json"
                _, receipt = run_observer_provider(
                    spec=ProviderExecutionSpec(
                        provider_id="fixture-provider",
                        executable=sys.executable,
                        args=(str(provider),),
                    ),
                    task_envelope_path=envelope,
                    packet_root=packet,
                    output_path=output,
                    expected_carrier_sha256=self.CARRIER,
                    expected_role=role,
                    independence_key=independence_key,
                    lineage_refs={"modelRef": "model:shared"},
                )
                provider_adapter.write_provider_execution_receipt(receipt_path, receipt)
                report_paths.append(output)
                receipt_paths.append(receipt_path)

            reports, lineage = provider_adapter.load_provider_bound_observer_reports(
                observer_report_paths=tuple(report_paths),
                provider_receipt_paths=tuple(receipt_paths),
                expected_carrier_sha256=self.CARRIER,
            )
            result = evaluate_perceptual_conformance(
                carrier_sha256=self.CARRIER,
                deterministic_standing="PASS",
                expected_pages=20,
                expected_figures=4,
                expected_tables=5,
                observer_reports=reports,
                observer_lineage_refs=lineage,
            )

            self.assertEqual(result["standing"], "ESCALATE_SPECIALIST")
            self.assertTrue(
                all("executionRef" not in values for values in lineage.values())
            )
            self.assertTrue(
                any(
                    reason.get("id") == "observer-lineage-missing"
                    and reason.get("dimension") == "executionRef"
                    for reason in result["adjudicationReasons"]
                )
            )

    def test_provider_execution_binds_carrier_role_and_independence(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            output = root / "observer.json"
            report, receipt = run_observer_provider(
                spec=ProviderExecutionSpec(
                    provider_id="fixture-provider",
                    executable=sys.executable,
                    args=(str(provider),),
                ),
                task_envelope_path=envelope,
                packet_root=packet,
                output_path=output,
                expected_carrier_sha256=self.CARRIER,
                expected_role="BLIND_VISION",
                independence_key="attempt-fixture-a",
            )
            self.assertEqual(report.standing, "PASS")
            self.assertEqual(receipt["standing"], "PASS_PROVIDER_EXECUTION_BOUND")
            self.assertEqual(receipt["independenceKey"], "attempt-fixture-a")
            self.assertTrue(receipt["observerReportSha256"].startswith("sha256:"))

    def test_receipt_binding_loader_preserves_non_execution_lineage_only(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            output = root / "observer.json"
            receipt_path = root / "receipt.json"
            _, receipt = run_observer_provider(
                spec=ProviderExecutionSpec(
                    provider_id="fixture-provider",
                    executable=sys.executable,
                    args=(str(provider),),
                ),
                task_envelope_path=envelope,
                packet_root=packet,
                output_path=output,
                expected_carrier_sha256=self.CARRIER,
                expected_role="BLIND_VISION",
                independence_key="attempt-fixture-a",
                lineage_refs={"modelRef": "model:shared"},
            )
            provider_adapter.write_provider_execution_receipt(receipt_path, receipt)
            reports, lineage = provider_adapter.load_provider_bound_observer_reports(
                observer_report_paths=(output,),
                provider_receipt_paths=(receipt_path,),
                expected_carrier_sha256=self.CARRIER,
            )
            self.assertEqual([report.observer_id for report in reports], ["fixture-observer"])
            self.assertNotIn("executionRef", lineage["fixture-observer"])
            self.assertEqual(lineage["fixture-observer"]["modelRef"], "model:shared")

    def test_receipt_binding_loader_rejects_tampered_report_digest(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            output = root / "observer.json"
            receipt_path = root / "receipt.json"
            _, receipt = run_observer_provider(
                spec=ProviderExecutionSpec(
                    provider_id="fixture-provider",
                    executable=sys.executable,
                    args=(str(provider),),
                ),
                task_envelope_path=envelope,
                packet_root=packet,
                output_path=output,
                expected_carrier_sha256=self.CARRIER,
                expected_role="BLIND_VISION",
                independence_key="attempt-fixture-a",
            )
            receipt["observerReportSha256"] = "sha256:" + "0" * 64
            provider_adapter.write_provider_execution_receipt(receipt_path, receipt)
            with self.assertRaisesRegex(
                PerceptualProviderAdapterError,
                "observer report digest mismatch",
            ):
                provider_adapter.load_provider_bound_observer_reports(
                    observer_report_paths=(output,),
                    provider_receipt_paths=(receipt_path,),
                    expected_carrier_sha256=self.CARRIER,
                )

    def test_receipt_binding_loader_does_not_admit_forged_execution_owner_proof(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            output = root / "observer.json"
            receipt_path = root / "receipt.json"
            _, receipt = run_observer_provider(
                spec=ProviderExecutionSpec(
                    provider_id="fixture-provider",
                    executable=sys.executable,
                    args=(str(provider),),
                ),
                task_envelope_path=envelope,
                packet_root=packet,
                output_path=output,
                expected_carrier_sha256=self.CARRIER,
                expected_role="BLIND_VISION",
                independence_key="attempt-fixture-a",
                lineage_refs={"modelRef": "model:shared"},
            )
            receipt["executionOwnerProof"] = {
                "schemaVersion": 1,
                "kind": "publication-perceptual-provider-execution-proof",
                "owner": "provider-adapter-direct-execution",
                "ownerNonce": "0" * 64,
                "evidenceDigest": "sha256:" + "1" * 64,
                "executionRef": "provider-execution:sha256:" + "2" * 64,
            }
            provider_adapter.write_provider_execution_receipt(receipt_path, receipt)
            reports, lineage = provider_adapter.load_provider_bound_observer_reports(
                observer_report_paths=(output,),
                provider_receipt_paths=(receipt_path,),
                expected_carrier_sha256=self.CARRIER,
            )
            self.assertEqual([report.observer_id for report in reports], ["fixture-observer"])
            self.assertEqual(lineage["fixture-observer"], {"modelRef": "model:shared"})

    def test_provider_execution_receipt_binds_report_without_owner_execution_proof(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            output = root / "observer.json"
            _, receipt = run_observer_provider(
                spec=ProviderExecutionSpec(
                    provider_id="fixture-provider",
                    executable=sys.executable,
                    args=(str(provider),),
                ),
                task_envelope_path=envelope,
                packet_root=packet,
                output_path=output,
                expected_carrier_sha256=self.CARRIER,
                expected_role="BLIND_VISION",
                independence_key="attempt-fixture-a",
                lineage_refs={"modelRef": "model:shared"},
            )
            self.assertEqual(receipt["observerId"], "fixture-observer")
            self.assertEqual(receipt["lineageRefs"], {"modelRef": "model:shared"})
            self.assertNotIn("executionOwnerProof", receipt)
            self.assertTrue(
                any(
                    "does not establish an owner-native execution occurrence" in value
                    for value in receipt["nonClaims"]
                )
            )

    def test_provider_execution_rejects_caller_asserted_execution_ref(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            with self.assertRaisesRegex(ValueError, "executionRef is owner-bound"):
                run_observer_provider(
                    spec=ProviderExecutionSpec(
                        provider_id="fixture-provider",
                        executable=sys.executable,
                        args=(str(provider),),
                    ),
                    task_envelope_path=envelope,
                    packet_root=packet,
                    output_path=root / "observer.json",
                    expected_carrier_sha256=self.CARRIER,
                    expected_role="BLIND_VISION",
                    independence_key="attempt-fixture-a",
                    lineage_refs={"executionRef": "caller-label"},
                )

    def test_provider_exec_cli_help_does_not_claim_direct_execution_ref_minting(self) -> None:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT)
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/publication_perceptual_provider_exec.py"),
                "--help",
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        normalized_help = " ".join(completed.stdout.split())
        self.assertNotIn("minted by the direct provider adapter", normalized_help)
        self.assertIn(
            "direct provider adapter does not mint executionRef",
            normalized_help,
        )
        self.assertIn(
            "native execution lineage is required for PASS",
            normalized_help,
        )

    def test_provider_exec_cli_binds_optional_lineage_without_owner_execution_proof(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            output = root / "observer.json"
            receipt_path = root / "receipt.json"
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/publication_perceptual_provider_exec.py"),
                    "--provider-id",
                    "fixture-provider",
                    "--provider-executable",
                    sys.executable,
                    "--provider-arg",
                    str(provider),
                    "--task-envelope",
                    str(envelope),
                    "--packet-root",
                    str(packet),
                    "--output",
                    str(output),
                    "--receipt",
                    str(receipt_path),
                    "--carrier-sha256",
                    self.CARRIER,
                    "--role",
                    "BLIND_VISION",
                    "--independence-key",
                    "attempt-fixture-a",
                    "--lineage-ref",
                    "modelRef=model:shared",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["lineageRefs"], {"modelRef": "model:shared"})
            self.assertNotIn("executionOwnerProof", receipt)

    def test_provider_exec_cli_rejects_caller_asserted_execution_ref(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/publication_perceptual_provider_exec.py"),
                    "--provider-id",
                    "fixture-provider",
                    "--provider-executable",
                    sys.executable,
                    "--provider-arg",
                    str(provider),
                    "--task-envelope",
                    str(envelope),
                    "--packet-root",
                    str(packet),
                    "--output",
                    str(root / "observer.json"),
                    "--receipt",
                    str(root / "receipt.json"),
                    "--carrier-sha256",
                    self.CARRIER,
                    "--role",
                    "BLIND_VISION",
                    "--independence-key",
                    "attempt-fixture-a",
                    "--lineage-ref",
                    "executionRef=caller-label",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("executionRef is owner-bound", completed.stderr)

    def test_role_mismatch_fails_closed_before_provider_execution(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            with self.assertRaises(PerceptualProviderAdapterError):
                run_observer_provider(
                    spec=ProviderExecutionSpec(
                        provider_id="fixture-provider",
                        executable=sys.executable,
                        args=(str(provider),),
                    ),
                    task_envelope_path=envelope,
                    packet_root=packet,
                    output_path=root / "observer.json",
                    expected_carrier_sha256=self.CARRIER,
                    expected_role="SEMANTIC_LAYOUT",
                    independence_key="attempt-fixture-c",
                )

    def test_report_independence_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            packet, envelope, provider = self._fixture(root)
            provider.write_text(
                provider.read_text(encoding="utf-8").replace(
                    '"independenceKey":a.independence_key',
                    '"independenceKey":"wrong-key"',
                ),
                encoding="utf-8",
            )
            with self.assertRaises(PerceptualProviderAdapterError):
                run_observer_provider(
                    spec=ProviderExecutionSpec(
                        provider_id="fixture-provider",
                        executable=sys.executable,
                        args=(str(provider),),
                    ),
                    task_envelope_path=envelope,
                    packet_root=packet,
                    output_path=root / "observer.json",
                    expected_carrier_sha256=self.CARRIER,
                    expected_role="BLIND_VISION",
                    independence_key="attempt-fixture-a",
                )


if __name__ == "__main__":
    unittest.main()
