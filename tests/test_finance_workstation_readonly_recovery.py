from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "finance_workstation_readonly_recovery.py"
)
spec = importlib.util.spec_from_file_location("finance_workstation_readonly_recovery", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def owner(ok: bool, operation: str, *, result=None, error=None, effect=None):
    value = {"ok": ok, "operation": operation}
    if operation.startswith("finance."):
        value["schemaVersion"] = 1
        if ok:
            value["kind"] = "ordivon.finance.runtime-domain-result"
            value["domain"] = "finance"
        else:
            value["kind"] = "ordivon.finance.runtime-domain-error"
            value["externalFinancialWriteAttempted"] = False
    if result is not None:
        value["result"] = result
    if error is not None:
        value["error"] = error
    if effect is not None:
        value["effectContract"] = effect
    return value


FINANCE_EFFECT = {
    "schemaVersion": 1,
    "kind": "ordivon.semantic-effect-contract",
    "owner": "ordivon-finance",
    "effectClass": "CANONICAL_OBSERVATION",
    "credentialAccess": "read",
    "environmentMutation": False,
    "externalWorldRead": True,
    "externalFinancialWrite": False,
    "financialSubmission": False,
    "authorityMutation": False,
}
WORKSTATION_EFFECT = {
    "effectClass": "READ_ONLY",
    "credentialAccess": "none",
    "environmentMutation": False,
    "externalFinancialWrite": False,
}


class FakeRuntime:
    def __init__(self, envelopes):
        self.envelopes = list(envelopes)
        self.calls = []

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        envelope = self.envelopes.pop(0)
        index = len(self.calls)
        status = "succeeded" if envelope.get("ok") is not False else "failed"
        return {
            "jobId": f"job-{index}",
            "attemptId": f"attempt-{index}",
            "status": status,
            "semanticCompletionEvaluated": False,
            "stdoutTail": json.dumps(envelope),
        }




class EnvironmentRuntime:
    def __init__(self, *, failed=False):
        self.failed = failed
        self.calls = []

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "jobId": "job-env",
            "attemptId": "attempt-env",
            "status": "failed" if self.failed else "succeeded",
            "executionTerminal": True,
            "exitCode": 2 if self.failed else 0,
            "semanticCompletionEvaluated": False,
        }


class ArtifactRuntime:
    def __init__(self, envelope, *, truncated=False):
        self.stdout = json.dumps(envelope, sort_keys=True)
        self.truncated = truncated
        self.calls = []

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "workspace.exec":
            retained = self.stdout.encode("utf-8")
            return {
                "jobId": "job-artifact",
                "attemptId": "attempt-artifact",
                "status": "succeeded",
                "semanticCompletionEvaluated": False,
                "stdoutTail": self.stdout[-1024:],
                "artifacts": [
                    {
                        "artifactId": "stdout-artifact",
                        "kind": "stdout",
                        "retainedBytes": len(retained),
                        "truncated": self.truncated,
                        "droppedBytes": 1 if self.truncated else 0,
                    }
                ],
            }
        if name == "artifact.read":
            encoded = self.stdout.encode("utf-8")
            offset = arguments["offset"]
            end = min(offset + arguments["maxBytes"], len(encoded))
            return {
                "content": encoded[offset:end].decode("utf-8"),
                "offset": offset,
                "nextOffset": end,
                "eof": end == len(encoded),
            }
        raise AssertionError(name)


def run(fake):
    return module.run_finance_workstation_readonly_recovery(
        fake,
        finance_workspace_id="finance-ws",
        workstation_workspace_id="workstation-ws",
        finance_state_root="/tmp/finance-state",
        finance_app_python="/tmp/python",
        request_prefix="fixture",
    )


class FinanceWorkstationCompositionTests(unittest.TestCase):
    def test_default_project_environment_preparation_is_python_locked_offline_runtime_plumbing(self):
        fake = EnvironmentRuntime()
        receipt = module._prepare_finance_project_environment(
            fake,
            finance_workspace_id="finance-ws",
            client_request_id="fixture-finance-project-environment",
        )
        self.assertEqual(receipt["mode"], "finance-python-lock-offline")
        self.assertFalse(receipt["networkAcquisitionAllowed"])
        self.assertFalse(receipt["lockfileMutationAllowed"])
        self.assertFalse(receipt["agentToolAuthorityGranted"])
        self.assertEqual(receipt["provider"], "/usr/bin/uv")
        self.assertEqual(receipt["args"], ["sync", "--locked", "--offline"])
        self.assertEqual(len(fake.calls), 1)
        name, arguments = fake.calls[0]
        self.assertEqual(name, "workspace.exec")
        self.assertEqual(arguments["execution"]["workspaceId"], "finance-ws")
        self.assertEqual(arguments["execution"]["executable"], "/usr/bin/uv")
        self.assertEqual(arguments["execution"]["args"], ["sync", "--locked", "--offline"])

    def test_project_environment_preparation_fails_closed_when_python_offline_closure_is_unavailable(self):
        fake = EnvironmentRuntime(failed=True)
        with self.assertRaisesRegex(RuntimeError, "Python project environment.*locked offline closure"):
            module._prepare_finance_project_environment(
                fake,
                finance_workspace_id="finance-ws",
                client_request_id="fixture-finance-project-environment-python-failed",
            )

    def test_finance_env_omits_cross_checkout_interpreter_when_no_expert_override_is_supplied(self):
        env = module._finance_env("/tmp/finance-state", None)
        self.assertNotIn("ORDIVON_FINANCE_APP_PYTHON", env)
        self.assertEqual(env["ORDIVON_FINANCE_STATE_DB"], "/tmp/finance-state/control/finance.db")

    def test_large_owner_stdout_is_recovered_from_runtime_artifact(self):
        envelope = owner(
            True,
            "finance.context.compile",
            result={"stateVersion": "v1", "padding": "x" * 70000},
        )
        fake = ArtifactRuntime(envelope)
        call = module._domain_exec(
            fake,
            owner="ordivon-finance",
            workspace_id="finance-ws",
            script="scripts/finance-domain.mjs",
            operation="finance.context.compile",
            arguments={},
            client_request_id="large-owner-output",
        )
        self.assertEqual(call.envelope, envelope)
        self.assertEqual(fake.calls[0][0], "workspace.exec")
        self.assertEqual(
            fake.calls[0][1]["execution"]["stdoutLimitBytes"],
            module._OWNER_STDOUT_LIMIT_BYTES,
        )
        self.assertEqual(fake.calls[1][0], "artifact.read")

    def test_truncated_owner_stdout_fails_closed_before_json_parse(self):
        fake = ArtifactRuntime(
            owner(True, "finance.context.compile", result={"stateVersion": "v1"}),
            truncated=True,
        )
        with self.assertRaisesRegex(RuntimeError, "retention bound"):
            module._domain_exec(
                fake,
                owner="ordivon-finance",
                workspace_id="finance-ws",
                script="scripts/finance-domain.mjs",
                operation="finance.context.compile",
                arguments={},
                client_request_id="truncated-owner-output",
            )
        self.assertEqual([name for name, _ in fake.calls], ["workspace.exec"])

    def test_healthy_path_exposes_only_finance_and_never_observes_or_mutates_workstation(self):
        fake = FakeRuntime(
            [
                owner(
                    True,
                    "finance.observe",
                    result={"status": "refreshed"},
                    effect=FINANCE_EFFECT,
                ),
            ]
        )
        receipt = run(fake)
        self.assertEqual(receipt["status"], "completed")
        self.assertEqual(
            [row[1]["execution"]["args"][3] for row in fake.calls],
            ["finance.observe"],
        )
        self.assertFalse(receipt["invariants"]["environmentMutationAttempted"])
        self.assertFalse(receipt["invariants"]["externalFinancialWriteAttempted"])

    def test_finance_observation_rejects_mislabeled_owner_envelope(self):
        fake = FakeRuntime(
            [
                owner(
                    True,
                    "finance.decide",
                    result={"status": "refreshed"},
                    effect=FINANCE_EFFECT,
                ),
            ]
        )
        with self.assertRaisesRegex(RuntimeError, "owner envelope differs"):
            run(fake)

    def test_finance_observation_rejects_financial_write_effect_claim(self):
        fake = FakeRuntime(
            [
                owner(
                    True,
                    "finance.observe",
                    result={"status": "refreshed"},
                    effect={**FINANCE_EFFECT, "externalFinancialWrite": True},
                ),
            ]
        )
        with self.assertRaisesRegex(RuntimeError, "externalFinancialWrite"):
            run(fake)

    def test_finance_observe_response_loss_replays_same_runtime_request_without_second_dispatch(self):
        class ResponseLossRuntime:
            def __init__(self):
                self.calls = []
                self.completed_by_request = {}
                self.physical_dispatches = 0
                self.lose_finance_observe_once = True

            def call_tool(self, name, arguments):
                if name != "workspace.exec":
                    raise AssertionError(name)
                self.calls.append((name, arguments))
                request_id = arguments.get("clientRequestId")
                if not isinstance(request_id, str):
                    raise AssertionError("workspace.exec request omitted clientRequestId")
                if request_id in self.completed_by_request:
                    return dict(self.completed_by_request[request_id])
                operation = arguments["execution"]["args"][3]
                if operation == "finance.observe":
                    envelope = owner(
                        True,
                        operation,
                        result={"status": "refreshed"},
                        effect=FINANCE_EFFECT,
                    )
                else:
                    raise AssertionError(operation)
                self.physical_dispatches += 1
                result = {
                    "jobId": f"job-{self.physical_dispatches}",
                    "attemptId": f"attempt-{self.physical_dispatches}",
                    "status": "succeeded",
                    "semanticCompletionEvaluated": False,
                    "stdoutTail": json.dumps(envelope),
                }
                self.completed_by_request[request_id] = dict(result)
                if operation == "finance.observe" and self.lose_finance_observe_once:
                    self.lose_finance_observe_once = False
                    raise RuntimeError("injected Finance observe response loss after durable Runtime completion")
                return result

        runtime = ResponseLossRuntime()
        with self.assertRaisesRegex(RuntimeError, "response loss"):
            run(runtime)
        replayed = run(runtime)
        self.assertEqual(replayed["status"], "completed")
        self.assertEqual(runtime.physical_dispatches, 1)
        self.assertEqual(len(runtime.calls), 2)
        request_ids = [arguments["clientRequestId"] for _, arguments in runtime.calls]
        self.assertEqual(request_ids[0], request_ids[1])

    def test_egress_failure_recovers_read_only_then_retries_finance(self):
        fake = FakeRuntime(
            [
                owner(False, "finance.observe", error={"code": "EGRESS_NOT_CURRENT"}),
                owner(
                    True,
                    "workstation.egress.observe",
                    result={
                        "status": "AVAILABLE",
                        "profileDigest": "sha256:" + "a" * 64,
                        "listenerReachable": True,
                    },
                    effect=WORKSTATION_EFFECT,
                ),
                owner(
                    True,
                    "finance.observe",
                    result={"status": "refreshed"},
                    effect=FINANCE_EFFECT,
                ),
            ]
        )
        receipt = run(fake)
        self.assertEqual(receipt["status"], "completed_after_egress_recovery")
        self.assertEqual(
            [row[1]["execution"]["args"][3] for row in fake.calls],
            [
                "finance.observe",
                "workstation.egress.observe",
                "finance.observe",
            ],
        )
        self.assertNotIn(
            "workstation.egress.pool.ensure",
            [row[1]["execution"]["args"][3] for row in fake.calls],
        )
        self.assertFalse(receipt["invariants"]["environmentMutationAttempted"])
        self.assertFalse(receipt["invariants"]["externalFinancialWriteAttempted"])


    def test_captured_egress_failure_replays_read_only_recovery_without_refiring_failure(self):
        fake = FakeRuntime(
            [
                owner(
                    True,
                    "workstation.egress.observe",
                    result={
                        "status": "AVAILABLE",
                        "profileDigest": "sha256:" + "d" * 64,
                        "listenerReachable": True,
                    },
                    effect=WORKSTATION_EFFECT,
                ),
                owner(
                    True,
                    "finance.observe",
                    result={"status": "refreshed"},
                    effect=FINANCE_EFFECT,
                ),
            ]
        )
        captured = owner(
            False,
            "finance.observe",
            error={"code": "EGRESS_NOT_CURRENT"},
        )
        receipt = module.run_finance_workstation_readonly_recovery(
            fake,
            finance_workspace_id="finance-ws",
            workstation_workspace_id="workstation-ws",
            finance_state_root="/tmp/finance-state",
            finance_app_python="/tmp/python",
            request_prefix="captured",
            initial_finance_envelope=captured,
            initial_finance_runtime_job_id="job-captured-finance-failure",
        )
        self.assertEqual(receipt["status"], "completed_after_egress_recovery")
        self.assertEqual(
            [row[1]["execution"]["args"][3] for row in fake.calls],
            ["workstation.egress.observe", "finance.observe"],
        )
        self.assertEqual(receipt["ownerCalls"][0]["runtimeJobId"], "job-captured-finance-failure")
        self.assertEqual(receipt["ownerCalls"][0]["ownerErrorCode"], "EGRESS_NOT_CURRENT")
        self.assertFalse(receipt["invariants"]["environmentMutationAttempted"])

    def test_recurrent_egress_staleness_recompiles_next_read_only_stage(self):
        fake = FakeRuntime(
            [
                owner(False, "finance.observe", error={"code": "EGRESS_NOT_CURRENT"}),
                owner(
                    True,
                    "workstation.egress.observe",
                    result={
                        "status": "AVAILABLE",
                        "profileDigest": "sha256:" + "e" * 64,
                        "listenerReachable": True,
                    },
                    effect=WORKSTATION_EFFECT,
                ),
                owner(False, "finance.observe", error={"code": "EGRESS_NOT_CURRENT"}),
            ]
        )
        receipt = run(fake)
        self.assertEqual(receipt["status"], "blocked_recurrent_egress")
        self.assertEqual(
            [row[1]["execution"]["args"][3] for row in fake.calls],
            [
                "finance.observe",
                "workstation.egress.observe",
                "finance.observe",
            ],
        )
        self.assertEqual(
            receipt["ownerCalls"][-1]["ownerErrorCode"], "EGRESS_NOT_CURRENT"
        )
        self.assertFalse(receipt["invariants"]["environmentMutationAttempted"])
        self.assertFalse(receipt["invariants"]["externalFinancialWriteAttempted"])

    def test_unavailable_egress_stops_without_environment_mutation(self):
        fake = FakeRuntime(
            [
                owner(False, "finance.observe", error={"code": "EGRESS_NOT_CURRENT"}),
                owner(
                    True,
                    "workstation.egress.observe",
                    result={
                        "status": "UNAVAILABLE",
                        "profileDigest": "sha256:" + "b" * 64,
                        "listenerReachable": False,
                    },
                    effect=WORKSTATION_EFFECT,
                ),
            ]
        )
        receipt = run(fake)
        self.assertEqual(receipt["status"], "blocked_environment")
        self.assertEqual(len(fake.calls), 2)
        self.assertFalse(receipt["invariants"]["environmentMutationAttempted"])

    def test_workstation_read_only_contract_is_enforced(self):
        fake = FakeRuntime(
            [
                owner(False, "finance.observe", error={"code": "EGRESS_NOT_CURRENT"}),
                owner(
                    True,
                    "workstation.egress.observe",
                    result={
                        "status": "AVAILABLE",
                        "profileDigest": "sha256:" + "c" * 64,
                        "listenerReachable": True,
                    },
                    effect={**WORKSTATION_EFFECT, "environmentMutation": True},
                ),
            ]
        )
        with self.assertRaisesRegex(RuntimeError, "environmentMutation"):
            run(fake)


if __name__ == "__main__":
    unittest.main()
