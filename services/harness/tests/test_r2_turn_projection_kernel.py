from __future__ import annotations

import unittest

from anc_canonical import canonical_digest

from ordivon_harness.ordivon.model import AgentToolDefinition
from ordivon_harness.ordivon.turn_projection import (
    AgentTurnProjector,
    project_agent_turn,
    project_turn_tool_working_set,
    select_turn_tool_working_set,
)
from ordivon_harness.working_view import (
    HarnessWorkingSetPin,
    HarnessWorkingSetSourceRef,
    HarnessWorkingView,
    HarnessWorkingViewSource,
    HarnessWorkingSetSpec,
    compile_working_view,
    compile_working_view_with_refs,
)


class WorkingViewSourceIdentityTests(unittest.TestCase):
    def test_source_identity_survives_detached_message_mutations(self) -> None:
        message = {"role": "user", "content": {"sections": ["original"]}}
        source = HarnessWorkingViewSource("source://identity", "g1", (message,))
        original = source.to_dict()
        digest = source.digest
        self.assertEqual(original, {
            "schemaVersion": 1,
            "kind": "ordivon.harness-working-view-source",
            "logicalRef": "source://identity",
            "logicalGeneration": "g1",
            "messages": [{"role": "user", "content": {"sections": ["original"]}}],
        })
        self.assertEqual(digest, canonical_digest(original))
        message["content"]["sections"].append("caller-change")
        source.messages[0]["content"]["sections"].append("read-change")
        exported = source.to_dict()
        exported["messages"][0]["content"]["sections"].append("export-change")
        self.assertEqual(source.digest, digest)
        self.assertEqual(source.to_dict(), original)
        self.assertEqual(source.messages[0]["content"], {"sections": ["original"]})

    def test_exact_source_roundtrip_preserves_projection_and_detaches_wire_input(self) -> None:
        original = HarnessWorkingViewSource(
            "source://identity", "g1", ({"role": "user", "content": {"items": [1]}},)
        )
        wire = original.to_dict()
        restored = HarnessWorkingViewSource.from_dict(wire)
        digest = restored.digest
        wire["messages"][0]["content"]["items"].append(2)
        pin = HarnessWorkingSetPin("task", restored.logical_ref, restored.logical_generation, digest)
        spec = HarnessWorkingSetSpec.initial("attempt:identity", pins=(pin,)).commit("test")

        class Objects:
            def get_object(self, object_digest, *, expected_kind=None):
                if object_digest != restored.digest or expected_kind != "harness-working-view-source":
                    raise ValueError("source identity differs")
                return restored.to_dict()

        view = compile_working_view(spec, Objects())
        self.assertEqual(view.messages, original.messages)
        self.assertEqual(restored.digest, original.digest)
        self.assertEqual(restored.to_dict(), original.to_dict())


class R2TurnProjectionKernelTests(unittest.TestCase):
    def test_equal_message_projection_does_not_identify_working_set_selection(self) -> None:
        source = HarnessWorkingViewSource(
            logical_ref="source://r2/shared",
            logical_generation="g1",
            messages=({"role": "user", "content": "same selected bytes"},),
        )

        class Objects:
            def get_object(self, digest, *, expected_kind=None):
                if (
                    digest != source.digest
                    or expected_kind != "harness-working-view-source"
                ):
                    raise KeyError(digest)
                return source.to_dict()

        def selection(slot):
            return HarnessWorkingSetSpec.initial(
                "working-attempt:r2-selection",
                pins=(
                    HarnessWorkingSetPin(
                        slot=slot,
                        logical_ref=source.logical_ref,
                        logical_generation=source.logical_generation,
                        resolved_digest=source.digest,
                    ),
                ),
            )

        a, b = selection("a"), selection("b")
        a_view, a_refs = compile_working_view_with_refs(a.commit("select"), Objects())
        b_view, b_refs = compile_working_view_with_refs(b.commit("select"), Objects())
        self.assertEqual(a_view.messages, b_view.messages)
        self.assertNotEqual(a_view.digest, b_view.digest)
        self.assertNotEqual(a_refs, b_refs)
        # A legal mutation of the mutable selections also separates their future
        # committed message projections. Current bytes are not a congruence.
        a_next, _ = compile_working_view_with_refs(
            a.remove_pin("a").commit("select"), Objects()
        )
        b_next, _ = compile_working_view_with_refs(
            b.remove_pin("a").commit("select"), Objects()
        )
        self.assertEqual(a_next.messages, ())
        self.assertEqual(b_next.messages, source.messages)

    def test_nonprojected_turn_preserves_canonical_request_shape_and_runtime_tools(self) -> None:
        canonical = ({"role": "user", "content": "canonical"},)
        tool = AgentToolDefinition(
            name="observe",
            description="observe",
            input_schema={"type": "object", "properties": {}},
        )
        projected = project_agent_turn(
            harness_run_id="harness-run:r2-plain",
            turn_id="turn:r2-plain:1",
            sequence=1,
            assignment_id="assignment:r2-plain",
            canonical_context_digest=canonical_digest({"context": "plain"}),
            canonical_messages=canonical,
            tool_catalog_digest=canonical_digest({"tools": "plain"}),
            runtime_tools=(tool,),
            remaining_budget={"modelCalls": 2, "toolCalls": 1},
            working_set_transition_installed=False,
            caller_ingress_promotion_installed=False,
            working_set_history_installed=False,
        )
        self.assertEqual(projected.request.messages, canonical)
        self.assertEqual(projected.request.tools, (tool,))
        self.assertTrue(projected.request.capabilities.conclusion)
        self.assertIsNone(projected.effective_working_view)
        self.assertIsNone(projected.projected_messages_digest)

    def test_projected_turn_orders_pre_caller_post_and_derives_exact_refs(self) -> None:
        pin = HarnessWorkingSetPin(
            slot="task",
            logical_ref="source://r2/task",
            logical_generation="g1",
            resolved_digest=canonical_digest({"r2": "task-source"}),
        )
        base = HarnessWorkingView(
            attempt_id="working-attempt:r2-a",
            working_set_digest=canonical_digest({"r2": "working-set"}),
            messages=({"role": "user", "content": "selected task"},),
        )
        refs = (
            HarnessWorkingSetSourceRef(
                pin=pin, request_message_start_index=0, request_message_end_index=1
            ),
        )
        pre = ({"role": "assistant", "content": "pre-tool"},)
        caller = ((3, {"role": "user", "content": "caller"}),)
        post = ({"role": "tool", "content": "post-tool"},)
        projected = project_agent_turn(
            harness_run_id="harness-run:r2-projected",
            turn_id="turn:r2-projected:2",
            sequence=2,
            assignment_id="assignment:r2-projected",
            canonical_context_digest=canonical_digest({"unused": True}),
            canonical_messages=({"role": "user", "content": "history"},),
            tool_catalog_digest=canonical_digest({"tools": "projected"}),
            runtime_tools=(),
            remaining_budget={"modelCalls": 1, "toolCalls": 0},
            working_set_transition_installed=True,
            caller_ingress_promotion_installed=True,
            working_set_history_installed=True,
            base_working_view=base,
            working_set_refs=refs,
            caller_entries=caller,
            pre_caller_tool_exchange_messages=pre,
            post_caller_tool_exchange_messages=post,
        )
        request = projected.request
        self.assertEqual(
            request.messages,
            base.messages + pre + (caller[0][1],) + post,
        )
        self.assertEqual(request.working_set_refs, refs)
        self.assertEqual(request.caller_ingress_refs[0].caller_message_index, 3)
        self.assertEqual(request.caller_ingress_refs[0].request_message_index, 2)
        self.assertTrue(request.capabilities.working_set_transition)
        self.assertTrue(request.capabilities.caller_ingress_promotion)
        self.assertTrue(request.capabilities.working_set_history)
        self.assertEqual(projected.transient_tool_exchange_messages, 2)
        self.assertEqual(projected.caller_cognition_ingress_messages, 1)
        self.assertEqual(request.context_digest, projected.effective_working_view.digest)

    def test_projected_only_inputs_require_a_base_working_view(self) -> None:
        pin = HarnessWorkingSetPin(
            slot="task",
            logical_ref="source://r2/invalid",
            logical_generation="g1",
            resolved_digest=canonical_digest({"r2": "invalid-source"}),
        )
        ref = HarnessWorkingSetSourceRef(
            pin=pin, request_message_start_index=0, request_message_end_index=1
        )
        common = dict(
            harness_run_id="harness-run:r2-invalid",
            turn_id="turn:r2-invalid:1",
            sequence=1,
            assignment_id="assignment:r2-invalid",
            canonical_context_digest=canonical_digest({"r2": "invalid-context"}),
            canonical_messages=({"role": "user", "content": "canonical"},),
            tool_catalog_digest=canonical_digest({"r2": "invalid-tools"}),
            runtime_tools=(),
            remaining_budget={"modelCalls": 1, "toolCalls": 0},
            working_set_transition_installed=True,
            caller_ingress_promotion_installed=True,
            working_set_history_installed=False,
        )
        invalid_inputs = (
            {"working_set_refs": (ref,)},
            {"caller_entries": ((0, {"role": "user", "content": "caller"}),)},
            {
                "pre_caller_tool_exchange_messages": (
                    {"role": "assistant", "content": "pre"},
                )
            },
            {
                "post_caller_tool_exchange_messages": (
                    {"role": "tool", "content": "post"},
                )
            },
        )
        for extra in invalid_inputs:
            with self.subTest(extra=tuple(extra)):
                with self.assertRaisesRegex(
                    ValueError,
                    "require a base WorkingView",
                ):
                    project_agent_turn(**common, **extra)

    def test_installed_promotion_without_addressable_caller_is_not_capability(self) -> None:
        base = HarnessWorkingView(
            attempt_id="working-attempt:r2-no-caller",
            working_set_digest=canonical_digest({"r2": "no-caller"}),
            messages=({"role": "user", "content": "selected"},),
        )
        projected = project_agent_turn(
            harness_run_id="harness-run:r2-no-caller",
            turn_id="turn:r2-no-caller:1",
            sequence=1,
            assignment_id="assignment:r2-no-caller",
            canonical_context_digest=canonical_digest({"unused": True}),
            canonical_messages=(),
            tool_catalog_digest=canonical_digest({"tools": "none"}),
            runtime_tools=(),
            remaining_budget={"modelCalls": 1, "toolCalls": 0},
            working_set_transition_installed=False,
            caller_ingress_promotion_installed=True,
            working_set_history_installed=False,
            base_working_view=base,
        )
        self.assertFalse(projected.request.capabilities.caller_ingress_promotion)
        self.assertEqual(projected.request.caller_ingress_refs, ())

    def test_projector_discards_transient_exchange_from_predecessor_working_set(self) -> None:
        current = HarnessWorkingView(
            attempt_id="working-attempt:r2-current",
            working_set_digest=canonical_digest({"r2": "current"}),
            messages=({"role": "user", "content": "current durable"},),
        )

        class ViewProjector:
            def project(self):
                return current

        class ToolSurface:
            catalog_digest = canonical_digest({"r2": "catalog"})

            def definitions(self):
                return ()

        projector = AgentTurnProjector(
            tool_surface=ToolSurface(),
            working_view_projector=ViewProjector(),
            caller_ingress_promotion_installed=True,
        )
        projection = projector.project(
            harness_run_id="harness-run:r2-stale",
            turn_id="turn:r2-stale:2",
            sequence=2,
            assignment_id="assignment:r2-stale",
            canonical_context_digest=canonical_digest({"r2": "context"}),
            canonical_messages=({"role": "user", "content": "history"},),
            remaining_budget={"modelCalls": 1, "toolCalls": 0},
            admit_runtime_tools=False,
            transient_working_set_digest=canonical_digest({"r2": "predecessor"}),
            caller_ingress_messages=({"role": "user", "content": "caller"},),
            pre_caller_tool_exchange_messages=(
                {"role": "assistant", "content": "stale-pre"},
            ),
            post_caller_tool_exchange_messages=(
                {"role": "tool", "content": "stale-post"},
            ),
        )
        self.assertTrue(projection.discarded_stale_transient_tool_exchange)
        self.assertEqual(
            projection.request.messages,
            current.messages + ({"role": "user", "content": "caller"},),
        )
        self.assertEqual(projection.transient_tool_exchange_messages, 0)
        self.assertTrue(projection.request.capabilities.caller_ingress_promotion)




class TurnToolWorkingSetTests(unittest.TestCase):
    def _tools(self):
        return (
            AgentToolDefinition(name="read_fact", description="Read", input_schema={"type":"object","properties":{}}),
            AgentToolDefinition(name="write_fact", description="Write", input_schema={"type":"object","properties":{}}),
            AgentToolDefinition(name="inspect_fact", description="Inspect", input_schema={"type":"object","properties":{}}),
        )

    def test_subset_only_selection_preserves_catalog_order_and_digest_evidence(self):
        tools=self._tools()
        selected=select_turn_tool_working_set(tools,("inspect_fact","read_fact"))
        self.assertEqual([tool.name for tool in selected],["read_fact","inspect_fact"])
        projection=project_turn_tool_working_set(tools,("inspect_fact","read_fact"))
        self.assertEqual(projection["availableCount"],3)
        self.assertEqual(projection["selectedCount"],2)
        self.assertEqual(projection["omittedCount"],1)
        self.assertFalse(projection["canExpandAuthority"])
        self.assertTrue(str(projection["selectedDefinitionsDigest"]).startswith("sha256:"))

    def test_unknown_or_duplicate_tool_fails_before_provider(self):
        tools=self._tools()
        with self.assertRaisesRegex(ValueError,"outside the admitted surface"):
            select_turn_tool_working_set(tools,("invented",))
        with self.assertRaisesRegex(ValueError,"must be unique"):
            select_turn_tool_working_set(tools,("read_fact","read_fact"))

    def test_explicit_empty_selection_is_valid_narrowing(self):
        self.assertEqual(select_turn_tool_working_set(self._tools(),()),())

if __name__ == "__main__":
    unittest.main()
