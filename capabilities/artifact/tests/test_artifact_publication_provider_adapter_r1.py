from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from artifact_capabilities.publication.provider_adapter import (
    PerceptualProviderAdapterError,
    ProviderExecutionSpec,
    run_observer_provider,
)


class PublicationProviderAdapterR1Tests(unittest.TestCase):
    CARRIER = "sha256:" + "a" * 64

    def _fixture(
        self, root: Path, *, provider_role: str = "BLIND_VISION"
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
                  "observerId":"fixture-observer",
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
