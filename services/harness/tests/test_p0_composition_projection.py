from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ordivon_harness.api import HarnessAgentRun
from ordivon_harness.ordivon.model import ScriptedTurnAdapter

from tests.test_r3_supported_agent_run import (
    FakeRuntime,
    FixedClock,
    contract,
    execution_binding,
    needs_input,
)


class ProcessCompositionExplainTests(unittest.TestCase):
    def test_in_process_explain_reports_exact_contract_and_no_liveness_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            clock = FixedClock()
            value = contract("p0-explain")
            run = HarnessAgentRun.create(
                Path(directory) / "state",
                value,
                lambda _contract: ScriptedTurnAdapter((needs_input("model-call:p0-explain"),)),
                clock_ms=clock,
                monotonic_ms=clock,
            )
            explanation = run.explain()
            process = explanation["processLocal"]
            self.assertFalse(process["runtimeClient"]["supplied"])
            self.assertEqual(process["runtimeClient"]["liveness"], "not-probed")
            self.assertEqual(process["adapter"]["liveness"], "not-probed")
            self.assertEqual(explanation["run"]["contractDigest"], value.digest)
            self.assertEqual(
                explanation["run"]["toolCatalogDigest"], value.tool_catalog_digest
            )
            self.assertEqual(explanation["run"]["toolGrantDigest"], value.tool_grant_digest)

        with tempfile.TemporaryDirectory() as directory:
            value = contract("p0-runtime-explain", tools=True)
            run = HarnessAgentRun.create(
                Path(directory) / "state",
                value,
                lambda _contract: ScriptedTurnAdapter((needs_input("model-call:p0-runtime"),)),
                execution_binding=execution_binding(value),
                runtime=FakeRuntime(),
            )
            explanation = run.explain()
            process = explanation["processLocal"]
            self.assertTrue(process["runtimeClient"]["supplied"])
            self.assertEqual(process["runtimeClient"]["liveness"], "not-probed")
            self.assertTrue(process["executionBinding"]["supplied"])
            self.assertEqual(explanation["run"]["contractDigest"], value.digest)
            self.assertEqual(
                explanation["run"]["toolCatalogDigest"], value.tool_catalog_digest
            )


if __name__ == "__main__":
    unittest.main()
