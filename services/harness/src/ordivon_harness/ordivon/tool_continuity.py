"""Original Tool Intent, dispatch-fence and Receipt lifecycle.

Composed by the original Run facade: one Store, one Run lease discipline,
no additional Writer or authority.
"""
from __future__ import annotations
from anc_canonical import JsonValue, canonical_digest, validate_json_value
from ..protocol import (
    HarnessDispatchFence,
    HarnessRunPauseReason,
    HarnessToolStepIntent,
    HarnessToolStepReceipt,
    HarnessToolStepStatus,
    tool_receipt_successor_allowed,
)
from ..store_errors import (
    HarnessRevisionConflict,
)
from ..store import (
    HarnessRunEventRecord,
    StoredHarnessObject,
)
from .continuity_guards import (
    continuity_event_id,
    required_event_digest,
    require_tool_intent_binding,
    validate_tool_event,
    inspect_all_unsettled_effect_sources,
)
from .continuity_records import (
    HarnessDispatchFenceV2,
)
from .run_store_port import (
    HarnessDispatchFenceView,
    HarnessSuperseded,
    StoredHarnessRunSnapshot,
    StoredHarnessToolStep,
)


_DISPATCH_FENCE_TTL_MS = 30_000


class ToolContinuity:
    """Original Tool Intent, dispatch-fence and Receipt lifecycle."""

    def prepare_tool_step(
        self,
        intent: HarnessToolStepIntent,
        *,
        original_request: dict[str, JsonValue] | None = None,
    ) -> StoredHarnessRunSnapshot:
        require_tool_intent_binding(intent, self.harness_run_id, self.binding)
        physical_execution_digest = None
        if original_request is not None:
            validate_json_value(original_request)
            execution = original_request.get("execution")
            if (
                intent.runtime_operation != "workspace.exec"
                or canonical_digest(original_request) != intent.runtime_arguments_digest
                or original_request.get("clientRequestId") != intent.client_request_id
                or not isinstance(execution, dict)
            ):
                raise ValueError("Harness original frozen physical request differs from Intent")
            # Privacy first: never persist raw args/env/tool input. This
            # digest commits the FULL exact original physical execution
            # projection already bound by the canonical Tool Intent.
            physical_execution_digest = canonical_digest(execution)
        state = self._require_state()
        observed_revision = self.store.load_run(self.harness_run_id).revision
        try:
            current_step = self.load_current_tool_step()
        except KeyError:
            current_step = None
        if current_step is not None and current_step.intent.digest == intent.digest:
            raise HarnessSuperseded("Harness Tool Step Intent is already prepared")
        if current_step is not None and (
            current_step.receipt is None
            or current_step.receipt.status
            not in {
                HarnessToolStepStatus.OBSERVED,
                HarnessToolStepStatus.REJECTED,
                HarnessToolStepStatus.CANCELLED,
            }
        ):
            # An older prepared/UNKNOWN Tool is a possible physical effect.
            # Never replace its consumer-visible head with a new Intent until
            # the original Owner resolves that exact request identity.
            raise HarnessSuperseded(
                "unresolved Tool Step must be owner-reconciled before a new Intent"
            )
        # A previous installed Writer could prepare B while A was unresolved,
        # then observe B. The latest Tool head is B and is not a proof that A
        # settled. Reuse the same full-Journal source observer as Finalization.
        # The exact observed_revision below is still fenced by the PG Lease
        # acquisition; a concurrent Writer cannot bypass this admission CAS.
        unsettled_provider_ids, unsettled_tool_digests = inspect_all_unsettled_effect_sources(
            self.store.list_run_events(self.harness_run_id),
            store=self.store,
            harness_run_id=self.harness_run_id,
            binding=self.binding,
            allow_tool_content=self.contract.privacy.allow_tool_content,
            provider_record_reader=self._load_provider_from_event,
            new_tool_client_request_id=intent.client_request_id,
        )
        if unsettled_provider_ids:
            # A Provider CLAIMED/DISPATCHING/UNKNOWN still owns a possible
            # external effect. Do not admit a Tool based on a later Tool head
            # while this independently verified Provider source is unsettled.
            raise HarnessSuperseded(
                "unresolved Provider Call remains in original PG history; "
                "exact Owner reconciliation required before a new Tool Intent"
            )
        if unsettled_tool_digests:
            raise HarnessSuperseded(
                "unresolved Tool Step remains in original PG history; "
                "exact Owner reconciliation required before a new Intent"
            )
        now_ms = self.clock_ms()
        try:
            lease = self._acquire_lease(
                "tool-prepare",
                intent.digest,
                now_ms=now_ms,
                expected_run_revision=observed_revision,
            )
        except HarnessRevisionConflict as error:
            raise HarnessSuperseded(str(error)) from error
        try:
            snapshot = self._build_snapshot(
                HarnessRunPauseReason.EFFECT_DISPATCH_PENDING,
                active_intent_digests=(intent.digest,),
                created_at_ms=self._recorded_time(now_ms),
            )
            retained = self._store_snapshot(snapshot, state)
            intent_object = self.store.put_object(intent.to_dict(), kind="harness-tool-step-intent")
            fence = HarnessDispatchFenceV2(
                fence_id=(
                    "harness-dispatch-fence:"
                    f"{self.harness_run_id.removeprefix('harness-run:')}:"
                    f"{intent.digest[7:31]}"
                ),
                harness_run_id=self.harness_run_id,
                run_revision=lease.run_revision + 1,
                binding_digest=self.binding.digest,
                intent_digest=intent.digest,
                runtime_operation=intent.runtime_operation,
                client_request_id=intent.client_request_id,
                issued_at_ms=now_ms,
                expires_at_ms=now_ms + _DISPATCH_FENCE_TTL_MS,
            )
            fence_object = self.store.put_object(fence.to_dict(), kind="harness-dispatch-fence")
            data: dict[str, JsonValue] = {
                "toolStepIntentDigest": intent.digest,
                "toolStepIntentObjectDigest": intent_object.digest,
                "dispatchFenceDigest": fence.digest,
                "dispatchFenceObjectDigest": fence_object.digest,
                "snapshotDigest": snapshot.digest,
                "snapshotObjectDigest": retained.snapshot_object.digest,
                "stateObjectDigest": retained.state_object.digest,
                "receiptDigest": None,
                "receiptObjectDigest": None,
                "previousReceiptObjectDigest": None,
                "observationObjectDigest": None,
            }
            if physical_execution_digest is not None:
                data["physicalExecutionDigest"] = physical_execution_digest
            self._append_event(
                lease=lease,
                event_kind="harness.tool-step-prepared",
                event_id=continuity_event_id("tool-prepared", intent.digest),
                data=data,
                recorded_at_ms=snapshot.created_at_ms,
                referenced_objects=(
                    intent_object,
                    fence_object,
                    retained.snapshot_object,
                    retained.state_object,
                ),
                caused_by_event_id=self._latest_event_id(),
            )
            return retained
        finally:
            self.store.release_run_lease(lease)

    def assert_dispatch_fence_current(
        self,
        fence: HarnessDispatchFenceView,
        *,
        require_unexpired: bool = True,
    ) -> None:
        step = self.load_current_tool_step()
        projection = self.store.load_run(self.harness_run_id)
        if step.fence != fence or step.intent.digest != fence.intent_digest:
            raise HarnessSuperseded("Harness Dispatch Fence is no longer current")
        if projection.revision != fence.authority_generation:
            raise HarnessSuperseded("Harness Dispatch Fence revision is no longer current")
        if require_unexpired and self.clock_ms() > fence.expires_at_ms:
            raise HarnessSuperseded("Harness Dispatch Fence expired before Runtime admission")

    def record_tool_step_receipt(
        self,
        receipt: HarnessToolStepReceipt,
        observation: dict[str, JsonValue],
    ) -> None:
        if receipt.harness_run_id != self.harness_run_id:
            raise ValueError("Tool Step Receipt belongs to another Harness Run")
        validate_json_value(observation)
        if canonical_digest(observation) != receipt.observation_digest:
            raise ValueError("Tool Step Receipt differs from its Observation")
        now_ms = self.clock_ms()
        lease = self._acquire_lease("tool-receipt", receipt.digest, now_ms=now_ms)
        try:
            current = self.load_current_tool_step()
            if current.intent.digest != receipt.intent_digest:
                raise ValueError("Tool Step Receipt belongs to another Intent")
            previous = current.receipt
            if previous == receipt:
                if current.observation is not None and current.observation != observation:
                    raise ValueError("Tool Step Receipt replay differs from retained Observation")
                return
            expected_previous = None if previous is None else previous.digest
            if receipt.previous_receipt_digest != expected_previous:
                raise ValueError("Tool Step Receipt predecessor differs from current history")
            if previous is not None and not tool_receipt_successor_allowed(previous, receipt):
                raise ValueError(
                    "terminal Tool Step Receipt cannot be superseded without "
                    "source-bound UNKNOWN Owner reconciliation"
                )
            receipt_object = self.store.put_object(
                receipt.to_dict(), kind="harness-tool-step-receipt"
            )
            observation_object = (
                self.store.put_object(observation, kind="harness-tool-observation")
                if self.contract.privacy.allow_tool_content
                else None
            )
            referenced: list[StoredHarnessObject] = [
                current.intent_object,
                receipt_object,
            ]
            if observation_object is not None:
                referenced.append(observation_object)
            if current.fence_object is not None:
                referenced.append(current.fence_object)
            if current.receipt_object is not None:
                referenced.append(current.receipt_object)
            data: dict[str, JsonValue] = {
                "toolStepIntentDigest": current.intent.digest,
                "toolStepIntentObjectDigest": current.intent_object.digest,
                "dispatchFenceDigest": (None if current.fence is None else current.fence.digest),
                "dispatchFenceObjectDigest": (
                    None if current.fence_object is None else current.fence_object.digest
                ),
                "receiptDigest": receipt.digest,
                "receiptObjectDigest": receipt_object.digest,
                "previousReceiptObjectDigest": (
                    None if current.receipt_object is None else current.receipt_object.digest
                ),
                "observationObjectDigest": (
                    None if observation_object is None else observation_object.digest
                ),
            }
            if receipt.status is HarnessToolStepStatus.UNKNOWN:
                event_kind = "harness.tool-step-unknown"
            elif receipt.reconciled:
                event_kind = "harness.tool-step-reconciled"
            else:
                event_kind = "harness.tool-step-recorded"
            self._append_event(
                lease=lease,
                event_kind=event_kind,
                event_id=continuity_event_id("tool-receipt", receipt.digest),
                data=data,
                recorded_at_ms=self._recorded_time(
                    receipt.created_at_ms,
                    previous_recorded_at_ms=(None if previous is None else previous.created_at_ms),
                ),
                referenced_objects=tuple(referenced),
                caused_by_event_id=self._tool_event_id_for_intent(current.intent.digest),
            )
        finally:
            self.store.release_run_lease(lease)

    def load_current_tool_step(self) -> StoredHarnessToolStep:
        event = self._heads().tool
        if event is None:
            raise KeyError("Harness Run has no current Tool Step")
        data = event.data
        intent_object_digest = required_event_digest(data, "toolStepIntentObjectDigest")
        raw_intent = self.store.get_object(
            intent_object_digest,
            expected_kind="harness-tool-step-intent",
        )
        if not isinstance(raw_intent, dict):
            raise TypeError("Harness Tool Step Intent object is invalid")
        intent = HarnessToolStepIntent.from_dict(raw_intent)
        require_tool_intent_binding(intent, self.harness_run_id, self.binding)
        intent_object = self.store.inspect_object(intent_object_digest)
        if data.get("toolStepIntentDigest") != intent.digest:
            raise ValueError("Harness Tool Step Intent digest differs")

        fence = None
        fence_object = None
        fence_object_digest = data.get("dispatchFenceObjectDigest")
        if fence_object_digest is not None:
            if not isinstance(fence_object_digest, str):
                raise ValueError("Harness Dispatch Fence object reference is invalid")
            raw_fence = self.store.get_object(
                fence_object_digest,
                expected_kind="harness-dispatch-fence",
            )
            if not isinstance(raw_fence, dict):
                raise ValueError("Harness Dispatch Fence object is invalid")
            version = raw_fence.get("schemaVersion")
            if version == 2:
                fence = HarnessDispatchFenceV2.from_dict(raw_fence)
            elif version == 1:
                fence = HarnessDispatchFence.from_dict(raw_fence)
            else:
                raise ValueError("Harness Dispatch Fence version is unsupported")
            fence_object = self.store.inspect_object(fence_object_digest)
            if (
                data.get("dispatchFenceDigest") != fence.digest
                or fence.intent_digest != intent.digest
                or fence.harness_run_id != self.harness_run_id
                or fence.runtime_operation != intent.runtime_operation
                or fence.client_request_id != intent.client_request_id
            ):
                raise ValueError("Harness Dispatch Fence differs from its Intent")

        receipt_object_digest = data.get("receiptObjectDigest")
        observation_object_digest = data.get("observationObjectDigest")
        if receipt_object_digest is None:
            if observation_object_digest is not None:
                raise TypeError("Harness Tool Step Observation cannot exist without a Receipt")
            return StoredHarnessToolStep(
                intent,
                intent_object,
                fence,
                fence_object,
                None,
                None,
                None,
                None,
                None,
                None,
            )
        if not isinstance(receipt_object_digest, str):
            raise TypeError("Harness Tool Step Receipt reference is invalid")
        raw_receipt = self.store.get_object(
            receipt_object_digest,
            expected_kind="harness-tool-step-receipt",
        )
        if not isinstance(raw_receipt, dict):
            raise TypeError("Harness Tool Step Receipt object is invalid")
        receipt = HarnessToolStepReceipt.from_dict(raw_receipt)
        if (
            data.get("receiptDigest") != receipt.digest
            or receipt.intent_digest != intent.digest
            or receipt.tool_call_id != intent.tool_call_id
        ):
            raise ValueError("Harness Tool Step Receipt differs from its Intent")

        observation = None
        observation_object = None
        if observation_object_digest is not None:
            if not isinstance(observation_object_digest, str):
                raise TypeError("Harness Tool Observation reference is invalid")
            raw_observation = self.store.get_object(
                observation_object_digest,
                expected_kind="harness-tool-observation",
            )
            if not isinstance(raw_observation, dict):
                raise TypeError("Harness Tool Observation object is invalid")
            validate_json_value(raw_observation)
            if canonical_digest(raw_observation) != receipt.observation_digest:
                raise ValueError("Harness Tool Observation differs from its Receipt")
            observation = dict(raw_observation)
            observation_object = self.store.inspect_object(observation_object_digest)
        elif self.contract.privacy.allow_tool_content and receipt.observation_digest is not None:
            raise ValueError(
                "Harness Tool Observation content was authorized but its object is missing"
            )

        previous_receipt = None
        previous_receipt_object = None
        previous_object_digest = data.get("previousReceiptObjectDigest")
        if receipt.previous_receipt_digest is None:
            if previous_object_digest is not None:
                raise ValueError("initial Tool Step Receipt unexpectedly references a predecessor")
        else:
            if not isinstance(previous_object_digest, str):
                raise ValueError("Tool Step Receipt predecessor object is missing")
            raw_previous = self.store.get_object(
                previous_object_digest,
                expected_kind="harness-tool-step-receipt",
            )
            if not isinstance(raw_previous, dict):
                raise ValueError("Tool Step Receipt predecessor is invalid")
            previous_receipt = HarnessToolStepReceipt.from_dict(raw_previous)
            previous_receipt_object = self.store.inspect_object(previous_object_digest)
            if (
                previous_receipt.digest != receipt.previous_receipt_digest
                or previous_receipt.intent_digest != intent.digest
                or not tool_receipt_successor_allowed(previous_receipt, receipt)
            ):
                raise ValueError("Tool Step Receipt predecessor chain is invalid")
        return StoredHarnessToolStep(
            intent,
            intent_object,
            fence,
            fence_object,
            receipt,
            self.store.inspect_object(receipt_object_digest),
            previous_receipt,
            previous_receipt_object,
            observation,
            observation_object,
        )

    def _validate_tool_event(self, event: HarnessRunEventRecord) -> None:
        validate_tool_event(
            event,
            store=self.store,
            harness_run_id=self.harness_run_id,
            binding=self.binding,
            allow_tool_content=self.contract.privacy.allow_tool_content,
        )

    def _tool_event_id_for_intent(self, digest: str) -> str | None:
        for event in reversed(self.store.list_run_events(self.harness_run_id)):
            if event.data.get("toolStepIntentDigest") == digest:
                return event.event_id
        return None
