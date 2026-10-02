from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from anc_canonical import canonical_digest

from ordivon_harness.api import (
    HarnessAgentRun,
    HarnessCognitionProfile,
    HarnessCognitionRefresh,
    HarnessCognitionRefreshSource,
    HarnessCognitionSeed,
    HarnessCognitionSeedSource,
    HarnessPrivacyPolicy,
    HarnessWorkingViewSource,
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE_DIGEST,
)
from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
from ordivon_harness.ordivon.model import AgentTurnRequest, ScriptedTurnAdapter
from ordivon_harness.ordivon.run_store_port import (
    HarnessProviderCallRecoveryRequired,
    HarnessProviderCallRequestMismatch,
)
from ordivon_harness.ordivon.sqlite_run_store import SQLiteHarnessRunContinuityStore
from ordivon_harness.sqlite_store import SQLiteHarnessStore
from ordivon_harness.working_view import HarnessWorkingView, WorkingSetViewProjector

from tests.test_p0_sqlite_runtime_bridge import FixedClock
from tests.test_p0_sqlite_provider_store import state as provider_state
from tests.test_pc15_epistemic_control import needs_input_turn


def _digest(label: str) -> str:
    return canonical_digest({"dc2": label})


def _contract(suffix: str) -> HarnessRunContract:
    return HarnessRunContract(
        harness_run_id=f"harness-run:dc2-{suffix}",
        harness_implementation_id="ordivon-harness@dc2",
        caller_id="caller:dc2",
        caller_run_ref=f"caller-run:dc2-{suffix}",
        objective_ref=HarnessBoundReference(
            f"objective:dc2-{suffix}", "objective", _digest("objective")
        ),
        context_refs=(
            HarnessBoundReference(f"context:dc2-{suffix}", "context", _digest("context")),
        ),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=NO_TOOL_AGENT_GRANT_DIGEST,
        budget={"maxModelCalls": 4, "maxToolCalls": 0, "maxWallTimeMs": 10_000},
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            f"manifest:dc2-{suffix}", "system-manifest", _digest("manifest")
        ),
        created_at_ms=1_000,
        privacy=HarnessPrivacyPolicy(
            content_policy="bounded-private-content",
            allow_model_content=True,
            allow_tool_content=False,
        ),
    )


def _source(suffix: str, generation: str, content: str) -> HarnessWorkingViewSource:
    return HarnessWorkingViewSource(
        logical_ref=f"cognition://dc2/{suffix}",
        logical_generation=generation,
        messages=({"role": "system", "content": content},),
    )


def _seed_source(slot: str, source: HarnessWorkingViewSource) -> HarnessCognitionSeedSource:
    return HarnessCognitionSeedSource(slot=slot, source=source)


class CallerCognitionRefreshTests(unittest.TestCase):
    def _create_run(self, root: Path, suffix: str):
        contract = _contract(suffix)
        run = HarnessAgentRun.create(
            root,
            contract,
            lambda _exact: ScriptedTurnAdapter((needs_input_turn("dc2-unused", "unused"),)),
            cognition_profile=HarnessCognitionProfile(),
            clock_ms=FixedClock(),
            monotonic_ms=FixedClock(),
        )
        environment = _source(f"{suffix}/environment", "generation:1", "ENVIRONMENT V1")
        agent_note = _source(f"{suffix}/agent-note", "generation:agent", "AGENT NOTE")
        seed = HarnessCognitionSeed(
            attempt_id=f"working-attempt:{suffix}:a",
            sources=(
                _seed_source("agent-note", agent_note),
                _seed_source("environment", environment),
            ),
            basis="initial exact cognition",
        )
        # A cognition-enabled Run materializes its seed before Provider dispatch. A scripted
        # adapter with no results will fail after admission, so use the continuity owner
        # directly for deterministic setup without introducing Provider evidence.
        with SQLiteHarnessStore(root) as store:
            continuity = SQLiteHarnessRunContinuityStore(store, contract, clock_ms=FixedClock())
            pins = []
            for item in seed.sources:
                stored = continuity.store_working_view_source(item.source)
                from ordivon_harness.working_view import HarnessWorkingSetPin, HarnessWorkingSetSpec

                pins.append(
                    HarnessWorkingSetPin(
                        slot=item.slot,
                        logical_ref=item.source.logical_ref,
                        logical_generation=item.source.logical_generation,
                        resolved_digest=stored.digest,
                    )
                )
            initial = HarnessWorkingSetSpec.initial(
                seed.attempt_id, pins=tuple(sorted(pins, key=lambda pin: pin.slot))
            )
            continuity.record_working_set(initial)
            continuity.record_working_set(initial.commit(seed.basis))
        return run, contract, environment, agent_note

    def test_public_refresh_replaces_only_target_slot_and_preserves_agent_pin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            run, contract, environment, agent_note = self._create_run(root, "preserve")
            replacement = _source("preserve/environment", "generation:2", "ENVIRONMENT V2")
            refresh = HarnessCognitionRefresh(
                next_attempt_id="working-attempt:preserve:b",
                sources=(
                    HarnessCognitionRefreshSource(
                        slot="environment",
                        expected_source=environment,
                        replacement_source=replacement,
                    ),
                ),
                basis="owner-qualified environment refresh",
            )
            digest = run.apply_cognition_refresh(refresh)
            with SQLiteHarnessStore(root) as store:
                continuity = SQLiteHarnessRunContinuityStore(store, contract, clock_ms=FixedClock())
                current = continuity.load_current_working_set()
                self.assertEqual(current.digest, digest)
                self.assertTrue(current.committed)
                by_slot = {pin.slot: pin for pin in current.pins}
                self.assertEqual(set(by_slot), {"agent-note", "environment"})
                self.assertEqual(by_slot["environment"].logical_generation, "generation:2")
                self.assertEqual(by_slot["agent-note"].logical_generation, "generation:agent")
                agent_raw = store.get_object(
                    by_slot["agent-note"].resolved_digest,
                    expected_kind="harness-working-view-source",
                )
                self.assertEqual(HarnessWorkingViewSource.from_dict(agent_raw), agent_note)
                events = [
                    event
                    for event in store.list_run_events(contract.harness_run_id)
                    if event.event_kind == "harness.working-set-recorded"
                    and event.data.get("attemptId") == refresh.next_attempt_id
                ]
                self.assertEqual(len(events), 3)
                self.assertTrue(
                    all(
                        event.data.get("cognitionRefreshDigest") == refresh.digest
                        and event.data.get("refreshProvenance") == "caller"
                        and "transitionProposalDigest" not in event.data
                        for event in events
                    )
                )

    def test_refresh_preserves_unrelated_pin_changed_after_caller_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            run, contract, environment, _agent_note = self._create_run(root, "compose")
            with SQLiteHarnessStore(root) as store:
                continuity = SQLiteHarnessRunContinuityStore(store, contract, clock_ms=FixedClock())
                current = continuity.load_current_working_set()
                changed_note = _source("compose/agent-note", "generation:agent-2", "AGENT NOTE 2")
                stored = continuity.store_working_view_source(changed_note)
                from ordivon_harness.working_view import HarnessWorkingSetPin

                replacement_note_pin = HarnessWorkingSetPin(
                    slot="agent-note",
                    logical_ref=changed_note.logical_ref,
                    logical_generation=changed_note.logical_generation,
                    resolved_digest=stored.digest,
                )
                by_slot = {pin.slot: pin for pin in current.pins}
                by_slot["agent-note"] = replacement_note_pin
                replanned = current.replan("working-attempt:compose:agent")
                selected = replanned.select_pins(tuple(by_slot[key] for key in sorted(by_slot)))
                committed = selected.commit("unrelated Agent cognition selection")
                for spec in (replanned, selected, committed):
                    continuity.record_working_set(spec)

            refresh = HarnessCognitionRefresh(
                next_attempt_id="working-attempt:compose:refresh",
                sources=(
                    HarnessCognitionRefreshSource(
                        slot="environment",
                        expected_source=environment,
                        replacement_source=_source(
                            "compose/environment", "generation:2", "ENVIRONMENT V2"
                        ),
                    ),
                ),
                basis="refresh environment without lost update",
            )
            run.apply_cognition_refresh(refresh)
            with SQLiteHarnessStore(root) as store:
                continuity = SQLiteHarnessRunContinuityStore(store, contract, clock_ms=FixedClock())
                by_slot = {pin.slot: pin for pin in continuity.load_current_working_set().pins}
                self.assertEqual(by_slot["agent-note"].logical_generation, "generation:agent-2")
                self.assertEqual(by_slot["environment"].logical_generation, "generation:2")

    def test_refresh_replay_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            run, contract, environment, _agent_note = self._create_run(root, "replay")
            replacement = _source("replay/environment", "generation:2", "ENVIRONMENT V2")
            refresh = HarnessCognitionRefresh(
                next_attempt_id="working-attempt:replay:b",
                sources=(
                    HarnessCognitionRefreshSource(
                        slot="environment",
                        expected_source=environment,
                        replacement_source=replacement,
                    ),
                ),
                basis="same exact refresh",
            )
            first = run.apply_cognition_refresh(refresh)
            second = run.apply_cognition_refresh(refresh)
            self.assertEqual(first, second)
            with SQLiteHarnessStore(root) as store:
                events = [
                    event
                    for event in store.list_run_events(contract.harness_run_id)
                    if event.event_kind == "harness.working-set-recorded"
                    and event.data.get("attemptId") == refresh.next_attempt_id
                ]
                self.assertEqual(len(events), 3)

    def test_refresh_fails_when_expected_slot_source_is_stale(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            run, contract, environment, _agent_note = self._create_run(root, "stale")
            first_replacement = _source("stale/environment", "generation:2", "ENVIRONMENT V2")
            first = HarnessCognitionRefresh(
                next_attempt_id="working-attempt:stale:b",
                sources=(
                    HarnessCognitionRefreshSource(
                        slot="environment",
                        expected_source=environment,
                        replacement_source=first_replacement,
                    ),
                ),
                basis="first refresh",
            )
            run.apply_cognition_refresh(first)
            stale_refresh = HarnessCognitionRefresh(
                next_attempt_id="working-attempt:stale:c",
                sources=(
                    HarnessCognitionRefreshSource(
                        slot="environment",
                        expected_source=environment,
                        replacement_source=_source(
                            "stale/environment", "generation:3", "ENVIRONMENT V3"
                        ),
                    ),
                ),
                basis="stale refresh",
            )
            with self.assertRaisesRegex(
                HarnessProviderCallRequestMismatch,
                "expected source is no longer current",
            ):
                run.apply_cognition_refresh(stale_refresh)
            with SQLiteHarnessStore(root) as store:
                continuity = SQLiteHarnessRunContinuityStore(store, contract, clock_ms=FixedClock())
                self.assertEqual(
                    {
                        pin.slot: pin.logical_generation
                        for pin in continuity.load_current_working_set().pins
                    }["environment"],
                    "generation:2",
                )

    def test_refresh_is_blocked_while_provider_call_is_claimed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            run, contract, environment, _agent_note = self._create_run(root, "claimed")
            with SQLiteHarnessStore(root) as store:
                continuity = SQLiteHarnessRunContinuityStore(store, contract, clock_ms=FixedClock())
                bound_state = replace(provider_state(wall_time_ms=10_000), messages=())
                continuity.bind_state(bound_state)
                current = continuity.load_current_working_set()
                base_view = WorkingSetViewProjector(store, continuity).project()
                messages = base_view.messages
                effective = HarnessWorkingView(
                    attempt_id=current.attempt_id,
                    working_set_digest=current.digest,
                    messages=messages,
                )
                request = AgentTurnRequest(
                    harness_run_id=contract.harness_run_id,
                    turn_id="turn:dc2-claimed",
                    sequence=1,
                    assignment_id=continuity.binding.assignment_id,
                    context_digest=effective.digest,
                    tool_catalog_digest=contract.tool_catalog_digest,
                    messages=messages,
                    tools=(),
                    remaining_budget=bound_state.remaining_budget,
                )
                continuity.claim_provider_call(
                    source=continuity.assignment_provider_source(),
                    turn_id=request.turn_id,
                    turn_sequence=request.sequence,
                    request_digest=request.dispatch_digest,
                    provider_request_digest=_digest("provider-request"),
                    adapter_id=ScriptedTurnAdapter.adapter_id,
                    requested_model_id=ScriptedTurnAdapter.model_id,
                    holder_id="holder:dc2-claimed",
                    ttl_ms=30_000,
                    request=request,
                )
            refresh = HarnessCognitionRefresh(
                next_attempt_id="working-attempt:claimed:b",
                sources=(
                    HarnessCognitionRefreshSource(
                        slot="environment",
                        expected_source=environment,
                        replacement_source=_source(
                            "claimed/environment", "generation:2", "ENVIRONMENT V2"
                        ),
                    ),
                ),
                basis="must wait for provider recovery",
            )
            with self.assertRaises(HarnessProviderCallRecoveryRequired):
                run.apply_cognition_refresh(refresh)

    def test_refresh_value_rejects_logical_identity_change(self) -> None:
        expected = _source("identity/environment", "generation:1", "ENVIRONMENT V1")
        replacement = HarnessWorkingViewSource(
            logical_ref="cognition://dc2/other",
            logical_generation="generation:2",
            messages=({"role": "system", "content": "ENVIRONMENT V2"},),
        )
        with self.assertRaisesRegex(ValueError, "preserve source logical reference"):
            HarnessCognitionRefreshSource(
                slot="environment",
                expected_source=expected,
                replacement_source=replacement,
            )


if __name__ == "__main__":
    unittest.main()
