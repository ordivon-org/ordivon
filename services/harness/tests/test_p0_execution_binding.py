from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.execution_binding import HarnessExecutionBinding
from ordivon_harness.ordivon.model import AgentToolCall
from ordivon_harness.ordivon.runtime_lowering import lower_runtime_tool
from ordivon_harness.ordivon.tool_errors import ToolBridgeError, ToolBridgeErrorKind

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
DIGEST_D = "sha256:" + "d" * 64
DIGEST_E = "sha256:" + "e" * 64


def binding() -> HarnessExecutionBinding:
    return HarnessExecutionBinding(
        harness_run_id="harness-run:p0-execution-binding-001",
        workspace_ref="workspace:p0-execution-binding-001",
        runtime_references=(
            dict(
                namespace="ordivon.harness",
                type="harness_run",
                id="harness-run:p0-execution-binding-001",
                generation="1",
                digest=DIGEST_B,
            ),
            dict(
                namespace="ordivon.harness",
                type="run_contract",
                id="harness-run-contract:p0-execution-binding-001",
                generation="1",
                digest=DIGEST_A,
            ),
            dict(
                namespace="ordivon.harness",
                type="tool_grant",
                id="tool-grant:p0-execution-binding-001",
                generation="1",
                digest=DIGEST_D,
            ),
        ),
    )


class HarnessExecutionBindingTests(unittest.TestCase):
    def test_round_trip_digest_and_request_identity_are_deterministic(self) -> None:
        value = binding()
        self.assertEqual(HarnessExecutionBinding.from_dict(value.to_dict()), value)
        self.assertEqual(
            HarnessExecutionBinding.from_dict(value.to_dict()).digest,
            value.digest,
        )
        self.assertEqual(
            value.client_request_id("turn-1-tool-1"),
            binding().client_request_id("turn-1-tool-1"),
        )
        self.assertNotEqual(
            value.client_request_id("turn-1-tool-1"),
            value.client_request_id("turn-1-tool-2"),
        )

    def test_patch_lowering_uses_authorized_snapshot_despite_grant_callback_mutation(self) -> None:
        call = AgentToolCall(
            tool_call_id="tool-call:patch-authority-snapshot",
            name="patch_workspace",
            arguments={
                "files": [{"relativePath": "README.md", "edits": [{"replacement": "trusted"}]}]
            },
        )
        admitted_digest = call.digest

        class MutatingGrant:
            allow_opaque_exec = False

            def allows_path(self, name: str, relative_path: str) -> bool:
                self_test.assertEqual((name, relative_path), ("patch_workspace", "README.md"))
                call.arguments["files"][0]["relativePath"] = "../private.txt"
                call.arguments["files"][0]["edits"][0]["replacement"] = "tampered"
                return True

            def execution_check(self, check_id: str):
                raise KeyError(check_id)

        self_test = self
        operation, request, request_id = lower_runtime_tool(
            call,
            step_id="turn-1-authority-snapshot",
            execution_binding=binding(),
            tool_grant=MutatingGrant(),
            known_job_ids=frozenset(),
            known_artifacts=frozenset(),
        )
        self.assertEqual(operation, "workspace.patch")
        self.assertEqual(request["files"][0]["relativePath"], "README.md")
        self.assertEqual(request["files"][0]["edits"][0]["replacement"], "trusted")
        self.assertEqual(
            request_id, binding().patch_request_id("turn-1-authority-snapshot", admitted_digest)
        )
        self.assertNotEqual(call.digest, admitted_digest)
        call.arguments["files"][0]["edits"][0]["replacement"] = "changed-again"
        self.assertEqual(request["files"][0]["edits"][0]["replacement"], "trusted")

    def test_run_in_workspace_lowering_has_only_harness_references(self) -> None:
        call = AgentToolCall(
            tool_call_id="tool-call:p0-execution-binding-run",
            name="run_in_workspace",
            arguments={
                "executable": "/usr/bin/python3",
                "args": ["-c", "print('p0')"],
                "waitMs": 30_000,
            },
        )
        operation, request, client_request_id = lower_runtime_tool(
            call,
            step_id="turn-1-tool-1",
            execution_binding=binding(),
            tool_grant=None,
            known_job_ids=frozenset(),
            known_artifacts=frozenset(),
        )
        self.assertEqual(operation, "workspace.exec")
        self.assertEqual(client_request_id, request["clientRequestId"])
        self.assertEqual(request["execution"]["workspaceId"], binding().workspace_ref)
        references = request["execution"]["foreignReferences"]
        self.assertEqual(
            [item["type"] for item in references],
            ["harness_run", "run_contract", "tool_grant"],
        )
        self.assertEqual({item["namespace"] for item in references}, {"ordivon.harness"})
        rendered = str(request)
        self.assertNotIn("task:", rendered)
        self.assertNotIn("task_attempt", rendered)
        self.assertNotIn("ordivon.host", rendered)

    def test_run_in_workspace_rejects_runtime_invalid_execution_contract(self) -> None:
        invalid_cases = (
            {"timeoutMs": 0},
            {"stdoutLimitBytes": 0},
            {"stderrLimitBytes": 0},
            {"env": {"NOT-AN-ENV-NAME": "value"}},
            {"env": {"VALID_NAME": "\x00"}},
            {"args": ["invalid\x00argument"]},
            {"executable": "/bin/echo\x00bad"},
            {"cwdRelative": "workspace\x00dir"},
            {"cwdRelative": "/tmp/escape-workspace"},
        )
        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                call = AgentToolCall(
                    tool_call_id="tool-call:p0-execution-binding-invalid-runtime",
                    name="run_in_workspace",
                    arguments={"executable": "/bin/echo", **invalid},
                )
                with self.assertRaises(ToolBridgeError) as caught:
                    lower_runtime_tool(
                        call,
                        step_id="turn-1-tool-invalid-runtime",
                        execution_binding=binding(),
                        tool_grant=None,
                        known_job_ids=frozenset(),
                        known_artifacts=frozenset(),
                    )
                self.assertEqual(caught.exception.kind, ToolBridgeErrorKind.MODEL_CORRECTABLE)

    def test_runtime_exec_accepts_valid_edge_inputs(self) -> None:
        call = AgentToolCall(
            tool_call_id="tool-call:p0-runtime-valid-bounds",
            name="run_in_workspace",
            arguments={
                "executable": "/bin/bash",
                "cwdRelative": "src",
                "env": {"_VALID_9": ""},
                "timeoutMs": 1,
                "stdoutLimitBytes": 1,
                "stderrLimitBytes": 1,
            },
        )
        operation, request, _ = lower_runtime_tool(
            call,
            step_id="turn-1-runtime-valid-bounds",
            execution_binding=binding(),
            tool_grant=None,
            known_job_ids=frozenset(),
            known_artifacts=frozenset(),
        )
        self.assertEqual(operation, "workspace.exec")
        self.assertEqual(request["execution"]["cwdRelative"], "src")
        self.assertEqual(request["execution"]["env"], {"_VALID_9": ""})
        self.assertEqual(request["execution"]["timeoutMs"], 1)

    def test_granted_run_check_numeric_fields_reject_python_equality_aliases(self) -> None:
        """A grant is a typed assertion, not an integer type witness."""
        class CheckGrant:
            allow_opaque_exec = False

            def __init__(self, check: object) -> None:
                self.check = check

            def allows_path(self, name: str, relative_path: str) -> bool:
                return True

            def execution_check(self, check_id: str) -> object:
                if check_id != "owner-native":
                    raise KeyError(check_id)
                return self.check

        for field in ("timeout_ms", "stdout_limit_bytes", "stderr_limit_bytes"):
            for illegal in (True, 1.0, "1"):
                with self.subTest(field=field, illegal=illegal):
                    params = {
                        "executable": "/bin/echo",
                        "args": ("ok",),
                        "cwd_relative": ".",
                        "env": (),
                        "timeout_ms": 30000,
                        "stdout_limit_bytes": 8192,
                        "stderr_limit_bytes": 8192,
                    }
                    params[field] = illegal
                    call = AgentToolCall(
                        tool_call_id="tool-call:p0-granted-native-check",
                        name="run_check",
                        arguments={"checkId": "owner-native"},
                    )
                    with self.assertRaises(ToolBridgeError) as caught:
                        lower_runtime_tool(
                            call,
                            step_id="turn-1-bad-check-numeric-type",
                            execution_binding=binding(),
                            tool_grant=CheckGrant(SimpleNamespace(**params)),
                            known_job_ids=frozenset(),
                            known_artifacts=frozenset(),
                        )
                    self.assertEqual(caught.exception.kind, ToolBridgeErrorKind.MODEL_CORRECTABLE)

        legal = SimpleNamespace(
            executable="/bin/echo",
            args=("ok",),
            cwd_relative=".",
            env=(),
            timeout_ms=30000,
            stdout_limit_bytes=8192,
            stderr_limit_bytes=8192,
        )
        operation, request, _ = lower_runtime_tool(
            AgentToolCall(
                tool_call_id="tool-call:p0-valid-native-check",
                name="run_check",
                arguments={"checkId": "owner-native"},
            ),
            step_id="turn-1-valid-check-numeric-type",
            execution_binding=binding(),
            tool_grant=CheckGrant(legal),
            known_job_ids=frozenset(),
            known_artifacts=frozenset(),
        )
        self.assertEqual(operation, "workspace.exec")
        self.assertEqual(request["execution"]["timeoutMs"], 30000)


    def test_generic_search_lowering_uses_execution_binding(self) -> None:
        call = AgentToolCall(
            tool_call_id="tool-call:p0-execution-binding-search",
            name="search_workspace",
            arguments={
                "query": "HarnessExecutionBinding",
                "relativePath": "src",
                "maxMatches": 12,
            },
        )
        operation, request, client_request_id = lower_runtime_tool(
            call,
            step_id="turn-1-tool-search",
            execution_binding=binding(),
            tool_grant=None,
            known_job_ids=frozenset(),
            known_artifacts=frozenset(),
        )
        self.assertEqual(operation, "workspace.exec")
        self.assertEqual(client_request_id, request["clientRequestId"])
        self.assertEqual(
            client_request_id,
            binding().client_request_id("turn-1-tool-search"),
        )
        execution = request["execution"]
        self.assertEqual(execution["executable"], "/usr/bin/rg")
        lowering = (Path(__file__).resolve().parents[1] / "src" / "ordivon_harness" / "ordivon" / "runtime_lowering.py").read_text()
        self.assertIn('RUNTIME_SEARCH_EXECUTABLES["ripgrep"]', lowering)
        self.assertEqual(execution["workspaceId"], binding().workspace_ref)
        self.assertEqual(
            {item["namespace"] for item in execution["foreignReferences"]},
            {"ordivon.harness"},
        )

    def test_search_lowering_honors_provider_visible_defaults(self) -> None:
        call = AgentToolCall(
            tool_call_id="tool-call:p0-execution-binding-search-defaults",
            name="search_workspace",
            arguments={"query": "HarnessExecutionBinding"},
        )
        operation, request, _ = lower_runtime_tool(
            call,
            step_id="turn-1-tool-search-defaults",
            execution_binding=binding(),
            tool_grant=None,
            known_job_ids=frozenset(),
            known_artifacts=frozenset(),
        )
        self.assertEqual(operation, "workspace.exec")
        args = request["execution"]["args"]
        self.assertIn("50", args)
        self.assertEqual(args[-2:], ["HarnessExecutionBinding", "."])

    def test_patch_identity_is_binding_and_tool_call_bound(self) -> None:
        value = binding()
        first = value.patch_request_id("turn-1-tool-patch", DIGEST_E)
        self.assertEqual(
            first,
            binding().patch_request_id("turn-1-tool-patch", DIGEST_E),
        )
        self.assertNotEqual(
            first,
            value.patch_request_id(
                "turn-1-tool-patch",
                canonical_digest({"different": True}),
            ),
        )

    def test_references_must_be_unique_and_sorted(self) -> None:
        value = binding().to_dict()
        value["runtimeReferences"] = list(reversed(value["runtimeReferences"]))
        with self.assertRaisesRegex(ValueError, "uniquely sorted"):
            HarnessExecutionBinding.from_dict(value)

    def test_runtime_native_reference_digest_is_opaque_logical_id(self) -> None:
        value = binding().to_dict()
        value["runtimeReferences"][0]["digest"] = "runtime-owned-generation-token"
        rebound = HarnessExecutionBinding.from_dict(value)
        self.assertEqual(
            rebound.to_dict()["runtimeReferences"][0]["digest"],
            "runtime-owned-generation-token",
        )

    def test_runtime_native_reference_rejects_unknown_fields_and_control_characters(self) -> None:
        value = binding().to_dict()
        value["runtimeReferences"][0]["extra"] = "nope"
        with self.assertRaisesRegex(ValueError, "fields differ"):
            HarnessExecutionBinding.from_dict(value)

        value = binding().to_dict()
        value["runtimeReferences"][0]["id"] = "bad\nreference"
        with self.assertRaisesRegex(ValueError, "control-free"):
            HarnessExecutionBinding.from_dict(value)

    def test_runtime_native_reference_rejects_duplicate_identity(self) -> None:
        value = binding().to_dict()
        duplicate = dict(value["runtimeReferences"][0])
        value["runtimeReferences"].insert(1, duplicate)
        with self.assertRaisesRegex(ValueError, "uniquely sorted"):
            HarnessExecutionBinding.from_dict(value)

    def test_generic_binding_and_lowering_have_no_host_imports(self) -> None:
        root = Path(__file__).resolve().parents[1] / "src" / "ordivon_harness"
        for relative in ("execution_binding.py", "ordivon/runtime_lowering.py"):
            source = (root / relative).read_text(encoding="utf-8")
            for forbidden in (
                "ordivon_host",
                "_host_compat",
                "CommittedHarnessAssignment",
                "HostHarnessRunStore",
            ):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
