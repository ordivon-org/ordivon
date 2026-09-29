#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "mcp_e2e.py"
SPEC = importlib.util.spec_from_file_location("ordivon_mcp_e2e_test_target", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MCP_E2E = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MCP_E2E
SPEC.loader.exec_module(MCP_E2E)


class FakeClient:
    def __init__(self, observations: list[dict[str, object]]) -> None:
        self.observations = list(observations)
        self.calls: list[tuple[str, dict[str, object]]] = []

    def tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        self.calls.append((name, arguments))
        if not self.observations:
            raise AssertionError("unexpected tool call")
        return self.observations.pop(0)


def repairable(job_id: str = "job-1", attempt_id: str = "attempt-1") -> dict[str, object]:
    return {
        "status": "orphaned",
        "jobId": job_id,
        "attemptId": attempt_id,
        "deliveryDisposition": "reconciliation_required",
        "recoveryRequired": True,
        "executionReasonCode": "LIVE_UNIT_WITHOUT_LAUNCH_TOKEN_EVIDENCE",
    }


def succeeded(job_id: str = "job-1", attempt_id: str = "attempt-1") -> dict[str, object]:
    return {
        "status": "succeeded",
        "jobId": job_id,
        "attemptId": attempt_id,
        "deliveryDisposition": "committed",
        "executionDisposition": "succeeded",
        "recoveryRequired": False,
    }


class ReconciliationContractTests(unittest.TestCase):
    def test_non_reconciliation_projection_is_returned_without_polling(self) -> None:
        initial = succeeded()
        client = FakeClient([])
        observed, used = MCP_E2E.settle_reconciliation_required(client, initial)
        self.assertIs(observed, initial)
        self.assertFalse(used)
        self.assertEqual(client.calls, [])

    def test_repairable_terminal_reconciles_same_job_and_attempt_without_redispatch(self) -> None:
        initial = repairable()
        client = FakeClient([succeeded()])
        observed, used = MCP_E2E.settle_reconciliation_required(client, initial, timeout=1.0)
        self.assertTrue(used)
        self.assertEqual(observed["status"], "succeeded")
        self.assertEqual(len(client.calls), 1)
        name, arguments = client.calls[0]
        self.assertEqual(name, "job.observe")
        self.assertEqual(arguments["jobId"], "job-1")

    def test_reconciliation_fails_closed_if_attempt_identity_changes(self) -> None:
        client = FakeClient([succeeded(attempt_id="attempt-2")])
        with self.assertRaisesRegex(AssertionError, "changed Job/Attempt identity"):
            MCP_E2E.settle_reconciliation_required(client, repairable(), timeout=1.0)

    def test_reconciliation_required_timeout_does_not_redispatch(self) -> None:
        client = FakeClient([])
        with self.assertRaisesRegex(TimeoutError, "did not converge"):
            MCP_E2E.settle_reconciliation_required(client, repairable(), timeout=0.0)
        self.assertEqual(client.calls, [])

    def test_wait_terminal_does_not_treat_repairable_orphan_as_stable_terminal(self) -> None:
        client = FakeClient([repairable(), succeeded()])
        observed = MCP_E2E.wait_terminal(client, "job-1", timeout=1.0)
        self.assertEqual(observed["status"], "succeeded")
        self.assertEqual([name for name, _ in client.calls], ["job.observe", "job.observe"])

    def test_terminal_evidence_matches_current_recovered_standing_not_first_history(self) -> None:
        observation = {
            **succeeded(),
            "executionReasonCode": "LATE_IDENTITY_BOUND_RUNNER_RESULT",
            "artifacts": [
                {"artifactId": "old", "kind": "terminal_evidence"},
                {"artifactId": "current", "kind": "terminal_evidence"},
            ],
        }
        old = {
            "attemptId": "attempt-1",
            "executionDisposition": "orphaned",
            "deliveryDisposition": "reconciliation_required",
            "reasonCode": "LIVE_UNIT_WITHOUT_LAUNCH_TOKEN_EVIDENCE",
        }
        current = {
            "attemptId": "attempt-1",
            "executionDisposition": "succeeded",
            "deliveryDisposition": "committed",
            "reasonCode": "LATE_IDENTITY_BOUND_RUNNER_RESULT",
        }
        client = FakeClient([
            {"content": json.dumps(old)},
            {"content": json.dumps(current)},
        ])
        selected = MCP_E2E.terminal_evidence_for_observation(client, observation)
        self.assertEqual(selected, current)
        self.assertEqual(
            [(name, arguments["artifactId"]) for name, arguments in client.calls],
            [("artifact.read", "old"), ("artifact.read", "current")],
        )


if __name__ == "__main__":
    unittest.main()
