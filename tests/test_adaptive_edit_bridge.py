from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from anc_canonical import JsonValue, canonical_digest

from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
from ordivon_harness.execution_binding import HarnessExecutionBinding
from ordivon_harness.ordivon.adaptive_edit_bridge import (
    ADAPTIVE_EDIT_TOOL_SURFACE_DIGEST,
    AdaptiveEditRuntimeBridge,
    EDIT_WORKSPACE_DEFINITION,
    READ_EDITABLE_WORKSPACE_DEFINITION,
)
from ordivon_harness.ordivon.loop import OrdivonAgentLoop, RunBudget, RunStopCode
from ordivon_harness.ordivon.model import (
    AgentRunConclusion,
    AgentToolCall,
    AgentTurnResult,
    ScriptedTurnAdapter,
)
from ordivon_harness.ordivon.sqlite_run_store import SQLiteHarnessRunContinuityStore
from ordivon_harness.ordivon.tool_errors import ToolBridgeError
from ordivon_harness.sqlite_store import SQLiteHarnessStore

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
SOURCE_DIGEST = "sha256:" + "1" * 64
CHANGED_DIGEST = "sha256:" + "2" * 64
GRANT_DIGEST = "sha256:" + "3" * 64


class FixedClock:
    def __init__(self) -> None:
        self.value = 1_000

    def __call__(self) -> int:
        self.value += 1
        return self.value


class EditGrant:
    allow_opaque_exec = False

    def allows_path(self, name: str, relative_path: str) -> bool:
        return name in {"read_workspace", "edit_workspace"} and relative_path == "demo.py"

    def execution_check(self, check_id: str):
        raise KeyError(check_id)


class FakeRuntime:
    def __init__(self, *, changed: bool = False, patch_loss: bool = False) -> None:
        self.changed = changed
        self.patch_loss = patch_loss
        self.calls: list[tuple[str, dict[str, JsonValue]]] = []
        self.content = "alpha\nβeta = 1\nomega\n"
        self.patch_request: dict[str, JsonValue] | None = None

    def call_tool(self, name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        self.calls.append((name, arguments))
        if name == "workspace.read":
            return {
                "workspaceId": arguments["workspaceId"],
                "relativePath": arguments["relativePath"],
                "content": self.content,
                "digest": CHANGED_DIGEST if self.changed else SOURCE_DIGEST,
                "byteLength": len(self.content.encode()),
            }
        if name == "workspace.patch":
            self.patch_request = dict(arguments)
            if self.patch_loss:
                from ordivon_harness.runtime_port import HarnessRuntimeClientError

                raise HarnessRuntimeClientError("injected Patch response loss")
            return {
                "operationId": "patch:adaptive-edit",
                "clientRequestId": arguments["clientRequestId"],
                "requestDigest": DIGEST_A,
                "replayed": False,
                "patch": {"workspaceId": arguments["workspaceId"], "files": []},
            }
        if name == "workspace.patch.get":
            assert self.patch_request is not None
            return {
                "operationId": "patch:adaptive-edit",
                "clientRequestId": arguments["clientRequestId"],
                "requestDigest": DIGEST_A,
                "workspaceId": self.patch_request["workspaceId"],
                "state": "committed",
                "patch": {"workspaceId": self.patch_request["workspaceId"], "files": []},
            }
        raise AssertionError(f"unexpected Runtime tool {name}")


def contract(suffix: str) -> HarnessRunContract:
    return HarnessRunContract(
        harness_run_id=f"harness-run:adaptive-edit-{suffix}",
        harness_implementation_id="ordivon-harness@test",
        caller_id="caller:adaptive-edit-test",
        caller_run_ref=f"trial:adaptive-edit-{suffix}",
        objective_ref=HarnessBoundReference(
            f"objective:adaptive-edit-{suffix}", "objective", DIGEST_A
        ),
        context_refs=(
            HarnessBoundReference(
                f"context:adaptive-edit-{suffix}", "context", DIGEST_B
            ),
        ),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=ADAPTIVE_EDIT_TOOL_SURFACE_DIGEST,
        tool_grant_digest=GRANT_DIGEST,
        budget={"maxModelCalls": 4, "maxToolCalls": 4, "maxWallTimeMs": 10_000},
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            f"system-manifest:adaptive-edit-{suffix}", "system-manifest", DIGEST_C
        ),
        created_at_ms=1_000,
    )


def binding(run_contract: HarnessRunContract, continuity) -> HarnessExecutionBinding:
    assignment = continuity.binding
    return HarnessExecutionBinding(
        harness_run_id=run_contract.harness_run_id,
        workspace_ref="ws-adaptive-edit-test",
        runtime_references=(
            {
                "namespace": "ordivon.harness",
                "type": "harness_run",
                "id": run_contract.harness_run_id,
                "generation": str(assignment.assignment_generation),
                "digest": assignment.digest,
            },
            {
                "namespace": "ordivon.harness",
                "type": "run_contract",
                "id": f"harness-run-contract:{run_contract.digest[7:31]}",
                "generation": "1",
                "digest": run_contract.digest,
            },
            {
                "namespace": "ordivon.harness",
                "type": "tool_grant",
                "id": f"tool-grant:{run_contract.tool_grant_digest[7:31]}",
                "generation": "1",
                "digest": run_contract.tool_grant_digest,
            },
        ),
    )


def setup_bridge(root: Path, suffix: str, runtime: FakeRuntime):
    run_contract = contract(suffix)
    store = SQLiteHarnessStore.initialize(root)
    store.create_run(run_contract)
    clock = FixedClock()
    continuity = SQLiteHarnessRunContinuityStore(store, run_contract, clock_ms=clock)
    bridge = AdaptiveEditRuntimeBridge(
        run_contract,
        continuity,
        binding(run_contract, continuity),
        runtime,
        tool_grant_digest=GRANT_DIGEST,
        tool_grant=EditGrant(),
    )
    bridge.bind_run_state(
        messages=({"role": "user", "content": "edit demo.py"},),
        observations=(),
        remaining_budget={
            "modelCalls": 4,
            "toolCalls": 4,
            "wallTimeMs": 10_000,
            "observationOnlyTurns": 4,
            "noProgressTurns": 3,
        },
        requested_model_id=ScriptedTurnAdapter.model_id,
        effective_model_id=None,
        active_elapsed_ms=0,
    )
    return store, continuity, bridge


def read_call(suffix: str) -> AgentToolCall:
    return AgentToolCall(
        tool_call_id=f"tool-call:{suffix}:read",
        name="read_workspace",
        arguments={"relativePath": "demo.py", "maxBytes": 4096},
    )


def exact_edit_call(suffix: str, *, digest: str = SOURCE_DIGEST) -> AgentToolCall:
    return AgentToolCall(
        tool_call_id=f"tool-call:{suffix}:edit",
        name="edit_workspace",
        arguments={
            "relativePath": "demo.py",
            "sourceDigest": digest,
            "codec": "exact-replacement-v1",
            "oldText": "βeta = 1",
            "newText": "βeta = 2",
        },
    )




def scripted_tool_turn(suffix: str, index: int, call: AgentToolCall) -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id=f"model-call:{suffix}:{index}",
        model_id=ScriptedTurnAdapter.model_id,
        content=None,
        tool_calls=(call,),
        conclusion=None,
        usage={"inputTokens": 10, "outputTokens": 10},
        finish_reason="tool_calls",
        raw_response_digest=canonical_digest(
            {"suffix": suffix, "index": index, "tool": call.to_dict()}
        ),
    )


def scripted_completion(suffix: str) -> AgentTurnResult:
    return AgentTurnResult(
        model_call_id=f"model-call:{suffix}:3",
        model_id=ScriptedTurnAdapter.model_id,
        content="edit complete",
        tool_calls=(),
        conclusion=AgentRunConclusion(
            status="candidate_completed",
            summary="Source edit completed through the adaptive edit bridge.",
        ),
        usage={"inputTokens": 10, "outputTokens": 10},
        finish_reason="stop",
        raw_response_digest=canonical_digest({"suffix": suffix, "kind": "complete"}),
    )

class AdaptiveEditBridgeTests(unittest.TestCase):
    def test_full_agent_loop_reads_edits_and_concludes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = FakeRuntime()
            store, continuity, bridge = setup_bridge(
                Path(directory) / "state", "agent-loop", runtime
            )
            adapter = ScriptedTurnAdapter(
                (
                    scripted_tool_turn("agent-loop", 1, read_call("agent-loop")),
                    scripted_tool_turn(
                        "agent-loop", 2, exact_edit_call("agent-loop")
                    ),
                    scripted_completion("agent-loop"),
                )
            )
            clock = FixedClock()
            result = OrdivonAgentLoop(
                adapter,
                bridge,
                budget=RunBudget(
                    max_model_calls=4,
                    max_tool_calls=4,
                    max_observation_bytes=128_000,
                    max_wall_time_ms=10_000,
                    max_model_observation_bytes=64_000,
                ),
                clock_ms=clock,
                monotonic_ms=clock,
            ).run(
                harness_run_id=bridge.contract.harness_run_id,
                assignment_id=continuity.binding.assignment_id,
                context_digest=bridge.contract.context_refs[0].digest,
                initial_messages=({"role": "user", "content": "edit demo.py"},),
            )
            self.assertTrue(result.candidate_completed)
            self.assertEqual(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
            self.assertEqual(result.model_calls, 3)
            self.assertEqual(result.tool_calls, 2)
            self.assertEqual(
                [name for name, _ in runtime.calls],
                ["workspace.read", "workspace.read", "workspace.patch"],
            )
            edit_observation = result.observations[-1]
            self.assertEqual(edit_observation.tool_name, "edit_workspace")
            self.assertEqual(edit_observation.status, "observed")
            store.close()

    def test_surface_is_explicit_internal_composition(self) -> None:
        self.assertEqual(
            [READ_EDITABLE_WORKSPACE_DEFINITION.name, EDIT_WORKSPACE_DEFINITION.name],
            ["read_workspace", "edit_workspace"],
        )

    def test_editable_read_returns_exact_source_digest_and_harness_generated_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = FakeRuntime()
            store, _, bridge = setup_bridge(Path(directory) / "state", "read", runtime)
            observation = bridge.execute(read_call("read"), step_id="turn-1-read")
            snapshot = observation.structured_content["editSnapshot"]
            self.assertEqual(snapshot["sourceDigest"], SOURCE_DIGEST)
            self.assertEqual(snapshot["relativePath"], "demo.py")
            self.assertEqual(len(snapshot["lineAnchors"]), 4)
            self.assertEqual(
                snapshot["codecs"],
                ["exact-replacement-v1", "anchored-line-v1"],
            )
            store.close()

    def test_exact_edit_re_reads_digest_then_lowers_to_one_durable_patch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = FakeRuntime()
            store, continuity, bridge = setup_bridge(
                Path(directory) / "state", "exact", runtime
            )
            observation = bridge.execute(exact_edit_call("exact"), step_id="turn-2-edit")
            self.assertEqual(observation.status, "observed")
            self.assertEqual([name for name, _ in runtime.calls], ["workspace.read", "workspace.patch"])
            assert runtime.patch_request is not None
            file = runtime.patch_request["files"][0]
            self.assertEqual(file["expectedDigest"], SOURCE_DIGEST)
            edit = file["edits"][0]
            self.assertEqual(edit["expectedText"], "βeta = 1")
            self.assertEqual(edit["replacement"], "βeta = 2")
            retained = continuity.load_current_tool_step()
            self.assertEqual(retained.intent.tool_name, "edit_workspace")
            self.assertEqual(retained.intent.runtime_operation, "workspace.patch")
            store.close()

    def test_stale_source_digest_rejects_before_patch_admission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = FakeRuntime(changed=True)
            store, _, bridge = setup_bridge(Path(directory) / "state", "stale", runtime)
            with self.assertRaisesRegex(ToolBridgeError, "sourceDigest is stale"):
                bridge.execute(exact_edit_call("stale"), step_id="turn-2-edit")
            self.assertEqual([name for name, _ in runtime.calls], ["workspace.read"])
            store.close()

    def test_anchored_edit_uses_harness_generated_anchor_and_same_patch_backend(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = FakeRuntime()
            store, _, bridge = setup_bridge(Path(directory) / "state", "anchor", runtime)
            read = bridge.execute(read_call("anchor"), step_id="turn-1-read")
            anchors = read.structured_content["editSnapshot"]["lineAnchors"]
            line2 = anchors[1]["anchor"]
            call = AgentToolCall(
                tool_call_id="tool-call:anchor:edit",
                name="edit_workspace",
                arguments={
                    "relativePath": "demo.py",
                    "sourceDigest": SOURCE_DIGEST,
                    "codec": "anchored-line-v1",
                    "startAnchor": line2,
                    "endAnchor": line2,
                    "replacement": "βeta = 2",
                },
            )
            observation = bridge.execute(call, step_id="turn-2-edit")
            self.assertEqual(observation.status, "observed")
            patch_calls = [args for name, args in runtime.calls if name == "workspace.patch"]
            self.assertEqual(len(patch_calls), 1)
            edit = patch_calls[0]["files"][0]["edits"][0]
            self.assertEqual(edit["expectedText"], "βeta = 1")
            self.assertEqual(edit["replacement"], "βeta = 2")
            store.close()

    def test_patch_response_loss_reconciles_without_second_physical_patch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = FakeRuntime(patch_loss=True)
            store, continuity, bridge = setup_bridge(
                Path(directory) / "state", "loss", runtime
            )
            observation = bridge.execute(exact_edit_call("loss"), step_id="turn-2-edit")
            self.assertEqual(observation.status, "observed")
            self.assertTrue(observation.reconciled)
            self.assertEqual(
                [name for name, _ in runtime.calls],
                ["workspace.read", "workspace.patch", "workspace.patch.get"],
            )
            retained = continuity.load_current_tool_step()
            self.assertTrue(retained.receipt.reconciled)
            store.close()

    def test_recovery_of_prepared_edit_uses_original_edit_tool_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = FakeRuntime(patch_loss=True)
            store, continuity, bridge = setup_bridge(
                Path(directory) / "state", "identity", runtime
            )
            call = exact_edit_call("identity")
            observation = bridge.execute(call, step_id="turn-2-edit")
            self.assertEqual(observation.tool_name, "edit_workspace")
            retained = continuity.load_current_tool_step()
            self.assertEqual(retained.intent.tool_call_digest, call.digest)
            self.assertEqual(retained.intent.tool_name, "edit_workspace")
            store.close()


if __name__ == "__main__":
    unittest.main()
