from __future__ import annotations

import unittest

from ordivon_harness.adaptive_edit import (
    AnchoredLineCodec,
    AnchoredLineEdit,
    EditCompileError,
    ExactReplacementCodec,
    ExactReplacementEdit,
    SourceSnapshot,
    dispatch_runtime_patch_once,
    reconcile_runtime_patch,
    anchored_line_plan,
    choose_edit_codec,
    exact_replacement_plan,
    lower_plan_to_runtime_patch,
)
from ordivon_harness.execution_binding import HarnessExecutionBinding
from ordivon_harness.runtime_port import (
    HarnessRuntimeClientError,
    HarnessRuntimeErrorDetail,
    HarnessRuntimeToolRejected,
)

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def binding() -> HarnessExecutionBinding:
    return HarnessExecutionBinding(
        harness_run_id="harness-run:adaptive-edit-r2",
        workspace_ref="ws-adaptive-edit-r2",
        runtime_references=(
            {
                "namespace": "ordivon.harness",
                "type": "harness_run",
                "id": "harness-run:adaptive-edit-r2",
                "generation": "1",
                "digest": DIGEST_B,
            },
        ),
    )


class FakePatchRuntime:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.calls: list[tuple[str, dict]] = []

    def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        request_id = arguments.get("clientRequestId")
        if name == "workspace.patch":
            if self.mode in {"loss_committed", "loss_prepared", "loss_unknown"}:
                raise HarnessRuntimeClientError("injected response loss")
            if self.mode == "precommit_reject":
                raise HarnessRuntimeToolRejected(
                    name,
                    HarnessRuntimeErrorDetail(
                        code="revision_mismatch",
                        message="source changed before Patch admission",
                        commit_state="not_committed",
                        retryable=False,
                        field="files[0].expectedDigest",
                    ),
                )
            return {
                "operationId": "patch-direct",
                "clientRequestId": request_id,
                "requestDigest": DIGEST_A,
                "replayed": False,
                "patch": {"files": []},
            }
        if name == "workspace.patch.get":
            state = {
                "loss_committed": "committed",
                "loss_prepared": "prepared",
                "loss_unknown": "unknown",
            }.get(self.mode, self.mode)
            value = {
                "operationId": "patch-status",
                "clientRequestId": request_id,
                "requestDigest": DIGEST_A,
                "workspaceId": "ws-adaptive-edit-r2",
                "state": state,
            }
            if state == "committed":
                value["patch"] = {"files": []}
            return value
        raise AssertionError(f"unexpected Runtime tool: {name}")


class AdaptiveEditTests(unittest.TestCase):
    def test_exact_replacement_compiles_unique_multiline_unicode_range(self) -> None:
        snapshot = SourceSnapshot(
            relative_path="src/demo.py",
            digest=DIGEST_A,
            content="alpha\nβeta = 1\nomega\n",
        )
        patch = ExactReplacementCodec().compile(
            snapshot,
            ExactReplacementEdit(
                relative_path="src/demo.py",
                old_text="βeta = 1\nomega",
                new_text="βeta = 2\nomega",
            ),
        )
        edit = patch.edits[0]
        self.assertEqual((edit.start_line, edit.start_column), (2, 0))
        self.assertEqual((edit.end_line, edit.end_column), (3, 5))
        self.assertEqual(edit.expected_text, "βeta = 1\nomega")
        self.assertEqual(patch.expected_digest, DIGEST_A)

    def test_exact_replacement_rejects_missing_ambiguous_and_noop(self) -> None:
        snapshot = SourceSnapshot("a.txt", DIGEST_A, "same same")
        with self.assertRaisesRegex(EditCompileError, "ambiguous"):
            ExactReplacementCodec().compile(
                snapshot, ExactReplacementEdit("a.txt", "same", "new")
            )
        with self.assertRaisesRegex(EditCompileError, "not found"):
            ExactReplacementCodec().compile(
                snapshot, ExactReplacementEdit("a.txt", "absent", "new")
            )
        with self.assertRaisesRegex(EditCompileError, "no-op"):
            ExactReplacementCodec().compile(
                snapshot, ExactReplacementEdit("a.txt", "same same", "same same")
            )

    def test_anchored_view_and_compile_bind_line_content_to_snapshot(self) -> None:
        snapshot = SourceSnapshot(
            "a.py",
            DIGEST_A,
            "first\nsecond\nthird",
        )
        view = snapshot.anchored_view()
        self.assertIn(snapshot.line_anchor(2) + "\tsecond", view)
        patch = AnchoredLineCodec().compile(
            snapshot,
            AnchoredLineEdit(
                relative_path="a.py",
                start_anchor=snapshot.line_anchor(2),
                end_anchor=snapshot.line_anchor(3),
                replacement="replacement\nthird2",
            ),
        )
        edit = patch.edits[0]
        self.assertEqual((edit.start_line, edit.start_column), (2, 0))
        self.assertEqual((edit.end_line, edit.end_column), (3, 5))
        self.assertEqual(edit.expected_text, "second\nthird")

    def test_anchored_compile_rejects_forged_or_stale_anchor(self) -> None:
        snapshot = SourceSnapshot("a.py", DIGEST_A, "first\nsecond")
        forged = snapshot.line_anchor(2)[:-1] + "0"
        if forged == snapshot.line_anchor(2):
            forged = snapshot.line_anchor(2)[:-1] + "1"
        with self.assertRaisesRegex(EditCompileError, "does not match"):
            AnchoredLineCodec().compile(
                snapshot,
                AnchoredLineEdit("a.py", forged, snapshot.line_anchor(2), "new"),
            )

    def test_plans_support_atomic_multi_file_runtime_lowering(self) -> None:
        snapshots = (
            SourceSnapshot("a.txt", DIGEST_A, "alpha"),
            SourceSnapshot("b.txt", DIGEST_B, "beta"),
        )
        plan = exact_replacement_plan(
            snapshots,
            (
                ExactReplacementEdit("a.txt", "alpha", "omega"),
                ExactReplacementEdit("b.txt", "beta", "gamma"),
            ),
        )
        operation, request, request_id = lower_plan_to_runtime_patch(
            plan,
            execution_binding=binding(),
            step_id="turn-1-edit",
            action_digest=plan.digest,
        )
        self.assertEqual(operation, "workspace.patch")
        self.assertEqual(request["clientRequestId"], request_id)
        self.assertEqual(request["workspaceId"], "ws-adaptive-edit-r2")
        self.assertEqual(len(request["files"]), 2)
        self.assertEqual(request["files"][0]["expectedDigest"], DIGEST_A)
        self.assertEqual(request["files"][1]["expectedDigest"], DIGEST_B)
        repeated = lower_plan_to_runtime_patch(
            plan,
            execution_binding=binding(),
            step_id="turn-1-edit",
            action_digest=plan.digest,
        )
        self.assertEqual(repeated, (operation, request, request_id))

    def test_anchored_plan_is_a_codec_not_a_physical_writer(self) -> None:
        snapshot = SourceSnapshot("a.txt", DIGEST_A, "one\ntwo")
        plan = anchored_line_plan(
            (snapshot,),
            (
                AnchoredLineEdit(
                    "a.txt",
                    snapshot.line_anchor(1),
                    snapshot.line_anchor(1),
                    "ONE",
                ),
            ),
        )
        self.assertEqual(plan.codec, "anchored-line-v1")
        self.assertEqual(plan.files[0].expected_digest, DIGEST_A)

    def test_protocol_selection_is_measured_profile_input_not_global_default(self) -> None:
        self.assertEqual(
            choose_edit_codec(measured_winner="exact-replacement-v1", anchored_reliable=True),
            "exact-replacement-v1",
        )
        self.assertEqual(
            choose_edit_codec(measured_winner=None, anchored_reliable=True),
            "anchored-line-v1",
        )
        self.assertEqual(
            choose_edit_codec(measured_winner=None, anchored_reliable=False),
            "exact-replacement-v1",
        )
        with self.assertRaisesRegex(ValueError, "not implemented"):
            choose_edit_codec(
                measured_winner=None,
                anchored_reliable=False,
                patch_reliable=True,
            )

    def test_patch_response_loss_reconciles_with_patch_get_without_redispatch(self) -> None:
        request = {
            "schemaVersion": 1,
            "clientRequestId": "request:harness-patch:test",
            "workspaceId": "ws-adaptive-edit-r2",
            "files": [],
            "maxDiffBytes": 1024,
        }
        runtime = FakePatchRuntime("loss_committed")
        result = dispatch_runtime_patch_once(runtime, request)
        self.assertEqual(result.status, "committed")
        self.assertTrue(result.reconciled)
        self.assertFalse(result.safe_to_correct)
        self.assertEqual([name for name, _ in runtime.calls], ["workspace.patch", "workspace.patch.get"])

    def test_patch_prepared_after_response_loss_is_proven_not_committed(self) -> None:
        request = {
            "schemaVersion": 1,
            "clientRequestId": "request:harness-patch:prepared",
            "workspaceId": "ws-adaptive-edit-r2",
            "files": [],
            "maxDiffBytes": 1024,
        }
        runtime = FakePatchRuntime("loss_prepared")
        result = dispatch_runtime_patch_once(runtime, request)
        self.assertEqual(result.status, "not_committed")
        self.assertTrue(result.reconciled)
        self.assertTrue(result.safe_to_correct)
        self.assertEqual([name for name, _ in runtime.calls].count("workspace.patch"), 1)

    def test_patch_unknown_never_becomes_fallback_authority(self) -> None:
        runtime = FakePatchRuntime("loss_unknown")
        result = dispatch_runtime_patch_once(
            runtime,
            {
                "schemaVersion": 1,
                "clientRequestId": "request:harness-patch:unknown",
                "workspaceId": "ws-adaptive-edit-r2",
                "files": [],
                "maxDiffBytes": 1024,
            },
        )
        self.assertEqual(result.status, "unknown")
        self.assertFalse(result.safe_to_correct)
        self.assertEqual([name for name, _ in runtime.calls].count("workspace.patch"), 1)

    def test_patch_precommit_rejection_is_safe_to_correct_without_patch_get(self) -> None:
        runtime = FakePatchRuntime("precommit_reject")
        result = dispatch_runtime_patch_once(
            runtime,
            {
                "schemaVersion": 1,
                "clientRequestId": "request:harness-patch:reject",
                "workspaceId": "ws-adaptive-edit-r2",
                "files": [],
                "maxDiffBytes": 1024,
            },
        )
        self.assertEqual(result.status, "rejected")
        self.assertTrue(result.safe_to_correct)
        self.assertEqual([name for name, _ in runtime.calls], ["workspace.patch"])

    def test_direct_patch_status_reconciliation_never_dispatches_patch(self) -> None:
        runtime = FakePatchRuntime("committed")
        result = reconcile_runtime_patch(runtime, "request:harness-patch:status-only")
        self.assertEqual(result.status, "committed")
        self.assertEqual([name for name, _ in runtime.calls], ["workspace.patch.get"])

    def test_r2_prototype_rejects_multiple_edits_per_file_instead_of_guessing_order(self) -> None:
        snapshot = SourceSnapshot("a.txt", DIGEST_A, "alpha beta")
        with self.assertRaisesRegex(EditCompileError, "at most one edit per file"):
            exact_replacement_plan(
                (snapshot,),
                (
                    ExactReplacementEdit("a.txt", "alpha", "omega"),
                    ExactReplacementEdit("a.txt", "beta", "gamma"),
                ),
            )


if __name__ == "__main__":
    unittest.main()
