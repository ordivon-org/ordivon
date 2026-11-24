"""Source-only Run inspections, separated from Provider/Tool Journal commands.

This mixin ONLY projects the existing Harness Run event stream, with existing
revision fencing and privacy guards. It neither writes events nor authorizes
Runtime Claims, native OS effects, or recipient delivery. The containing
EventSourcedRunContinuity remains the same public facade and PG Writer.
"""
from __future__ import annotations

from anc_canonical import JsonValue

from ..protocol import HarnessToolStepIntent, HarnessToolStepReceipt
from ..store import HarnessRunEventRecord, HarnessRunProjection
from ..store_errors import HarnessRevisionConflict
from .continuity_guards import (
    _TOOL_EVENT_KINDS,
    inspect_all_unsettled_effect_sources,
    required_event_digest,
    require_tool_intent_binding,
)


class RunSourceInspection:
    def _read_verified_source_cut(
        self,
    ) -> tuple[HarnessRunProjection, tuple[HarnessRunEventRecord, ...]]:
        """Reuse original Store integrity and bind the read to one Run revision.

        A latest Event matching the projection does not prove the absence of
        missing earlier events or detached CAS references. This full check is
        for explicit owner recovery/finalization reads, not the hot Turn path.
        Concurrent legitimate appends invalidate the cut, not the Journal.
        """
        projection = self.store.load_run(self.harness_run_id)
        self.store.validate_run_history(self.harness_run_id)
        events = self.store.list_run_events(self.harness_run_id)
        if (
            not events
            or len(events) != projection.revision
            or any(
                event.run_revision != revision or event.harness_run_id != self.harness_run_id
                for revision, event in enumerate(events, 1)
            )
        ):
            raise HarnessRevisionConflict(
                "Run source history differs from the original revision"
            )
        self._require_current_source_cut(projection)
        return projection, events

    def _require_current_source_cut(self, projection: HarnessRunProjection) -> None:
        if self.store.load_run(self.harness_run_id).revision != projection.revision:
            raise HarnessRevisionConflict("Run changed during source verification")

    def _inspect_original_tool_sources(self, *, include_settled: bool) -> dict[str, JsonValue]:
        """Read verified original Tool Intent identities without duplicating a Registry.

        This is not a dispatch permission, Owner Job observation, or release
        certificate. Never return Tool arguments, model content, or credentials.
        A legacy Run may hide an unresolved Intent behind a later observed one.
        """
        projection, events = self._read_verified_source_cut()
        _, pending = inspect_all_unsettled_effect_sources(
            events,
            store=self.store,
            harness_run_id=self.harness_run_id,
            binding=self.binding,
            allow_tool_content=self.contract.privacy.allow_tool_content,
            provider_record_reader=self._load_provider_from_event,
        )
        # The recovery view deliberately excludes previously settled Intent
        # heads. A Run-epoch revoke/drain consumer must instead enumerate
        # EVERY original Prepared Intent, including OBSERVED/REJECTED/CANCELLED,
        # before asking Runtime to prove physical quiescence. These are only
        # source identities, never Runtime Job/OS/Domain acknowledgement.
        selected_set = (
            {
                required_event_digest(event.data, "toolStepIntentDigest")
                for event in events
                if event.event_kind == "harness.tool-step-prepared"
            }
            if include_settled
            else set(pending)
        )
        sources: dict[str, dict[str, JsonValue]] = {}
        for event in events:
            digest = event.data.get("toolStepIntentDigest")
            if digest not in selected_set:
                continue
            if event.event_kind == "harness.tool-step-prepared":
                raw = self.store.get_object(
                    required_event_digest(event.data, "toolStepIntentObjectDigest"),
                    expected_kind="harness-tool-step-intent",
                )
                if not isinstance(raw, dict):
                    raise ValueError("Tool recovery source Intent is not an object")
                intent = HarnessToolStepIntent.from_dict(raw)
                require_tool_intent_binding(intent, self.harness_run_id, self.binding)
                if intent.digest != digest or digest in sources:
                    raise ValueError("Tool recovery source Intent identity differs")
                sources[digest] = {
                    "intentDigest": intent.digest,
                    "intentObjectDigest": required_event_digest(
                        event.data, "toolStepIntentObjectDigest"
                    ),
                    "preparedEventId": event.event_id,
                    "preparedRunRevision": event.run_revision,
                    "toolCallId": intent.tool_call_id,
                    "clientRequestId": intent.client_request_id,
                    "runtimeOperation": intent.runtime_operation,
                    "runtimeArgumentsDigest": intent.runtime_arguments_digest,
                    "dispatchFenceDigest": event.data.get("dispatchFenceDigest"),
                    "lastRecordedStatus": None,
                    "sourceOwnerJobRef": None,
                }
            elif event.event_kind in _TOOL_EVENT_KINDS:
                # The full original Event verifier above already validates
                # predecessor identity, immutable Receipt and observation.
                source = sources.get(digest)
                if source is None:
                    raise ValueError("Tool recovery Receipt precedes its Intent")
                receipt_raw = self.store.get_object(
                    required_event_digest(event.data, "receiptObjectDigest"),
                    expected_kind="harness-tool-step-receipt",
                )
                if not isinstance(receipt_raw, dict):
                    raise ValueError("Tool recovery source Receipt is not an object")
                receipt = HarnessToolStepReceipt.from_dict(receipt_raw)
                source["lastRecordedStatus"] = receipt.status.value
                source["sourceOwnerJobRef"] = receipt.runtime_job_ref
        if set(sources) != selected_set:
            raise ValueError("Original Run Tool sources do not cover the selected Intent identities")
        # A third Writer may append a new Event between the first projection
        # and this projection. No mixed-revision source may be presented.
        self._require_current_source_cut(projection)
        # The original Run's clientRequestIds form the exact existing Runtime
        # idempotency keys (within its dedicated principal). A recycled key
        # cannot represent two distinct ToolIntents in a reliable drain set.
        if include_settled:
            keys = [source["clientRequestId"] for source in sources.values()]
            if len(keys) != len(set(keys)):
                raise ValueError("Original Run issued Tool Intents reuse a clientRequestId")
        kind = (
            "ordivon.harness-issued-tool-sources"
            if include_settled
            else "ordivon.harness-tool-recovery-sources"
        )
        standing = (
            "source-identities-only"
            if include_settled
            else ("blocked" if sources else "no-pending-tool-intent")
        )
        key = "issuedIntents" if include_settled else "unsettledIntents"
        result: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": kind,
            "harnessRunId": self.harness_run_id,
            "contractDigest": self.contract.digest,
            "toolGrantDigest": self.contract.tool_grant_digest,
            "runRevision": projection.revision,
            "sourceStanding": standing,
            key: [sources[digest] for digest in sorted(sources)],
            "runtimeOwnerProofStanding": "unknown",
            "safeToDispatch": False,
            "runtimeClaimReleaseStanding": "unknown",
        }
        if include_settled:
            # Source Journal completeness is not a no-future-OS-spawn proof;
            # the caller still must close issuer admissions AND reconcile all
            # original Runtime clientRequestIds/Attempts and native Unit jobs.
            result["originalRunIssuedCount"] = len(sources)
            result["noFutureSpawnAckStanding"] = "unknown"
            result["safeToAcknowledgeNoFutureSpawn"] = False
        return result


    def inspect_unsettled_tool_sources(self) -> dict[str, JsonValue]:
        """Retain the existing recovery-only subset contract unchanged."""
        return self._inspect_original_tool_sources(include_settled=False)

    def inspect_issued_tool_sources(self) -> dict[str, JsonValue]:
        """Enumerate ALL source-issued Tool Intents in one revision-fenced Run.

        This read-only original Journal projection preserves exact
        clientRequestId/Intent/Run bindings, but cannot prove Runtime OS
        termination, all future dispatch fenced, or Domain byte acceptance.
        Do not use it by itself as a RevokeACK or GC release certificate.
        """
        return self._inspect_original_tool_sources(include_settled=True)

    def inspect_finalization_source(self) -> dict[str, JsonValue]:
        """Project source-owned closure, never an authorized Runtime Claim release.

        External Job/Artifact, Git or Domain delivery is a separate natural
        owner's proof, not a fact this Harness PostgreSQL Journal can certify.
        UNKNOWN remains unresolved even on a terminal Run projection.
        """
        from ..independent_result_reader import IndependentRunReader
        from .continuity_guards import inspect_all_unsettled_effect_sources

        projection, events = self._read_verified_source_cut()
        if not projection.status.terminal:
            # Nonterminal status blocks Release, not owner recovery of original effects.
            provider_ids, tool_digests = inspect_all_unsettled_effect_sources(
                events,
                store=self.store,
                harness_run_id=self.harness_run_id,
                binding=self.binding,
                allow_tool_content=self.contract.privacy.allow_tool_content,
                provider_record_reader=self._load_provider_from_event,
            )
            self._require_current_source_cut(projection)
            blockers = ["run_not_terminal"]
            if provider_ids:
                blockers.append("provider_unsettled")
            if tool_digests:
                blockers.append("tool_unsettled")
            return {
                "schemaVersion": 1,
                "kind": "ordivon.harness-finalization-source-assessment",
                "harnessRunId": self.harness_run_id,
                "contractDigest": self.contract.digest,
                "toolGrantDigest": self.contract.tool_grant_digest,
                "runRevision": projection.revision,
                "terminalEventId": None,
                "runReceiptDigest": None,
                "sourceStanding": "blocked",
                "blockers": blockers,
                "unsettledProviderCallIds": list(provider_ids),
                "unsettledToolIntentDigests": list(tool_digests),
                "externalDeliveryStanding": "unknown",
                "runtimeClaimStanding": "unknown",
            }
        if events[-1].event_id != projection.terminal_event_id:
            raise ValueError("finalization Run terminal projection differs from Journal")
        terminal = IndependentRunReader(
            self.store, self.contract, self.binding, clock_ms=self.clock_ms
        ).load_terminal_result()
        provider_ids, tool_digests = inspect_all_unsettled_effect_sources(
            events,
            store=self.store,
            harness_run_id=self.harness_run_id,
            binding=self.binding,
            allow_tool_content=self.contract.privacy.allow_tool_content,
            provider_record_reader=self._load_provider_from_event,
        )
        self._require_current_source_cut(projection)
        blockers: list[str] = []
        if terminal.receipt.stop_reason == "unknown":
            blockers.append("unknown_run_stop")
        if provider_ids:
            blockers.append("provider_unsettled")
        if tool_digests:
            blockers.append("tool_unsettled")
        return {
            "schemaVersion": 1,
            "kind": "ordivon.harness-finalization-source-assessment",
            "harnessRunId": self.harness_run_id,
            "contractDigest": self.contract.digest,
            "toolGrantDigest": self.contract.tool_grant_digest,
            "runRevision": projection.revision,
            "terminalEventId": projection.terminal_event_id,
            "runReceiptDigest": terminal.receipt.digest,
            "sourceStanding": "blocked" if blockers else "source-settled",
            "blockers": blockers,
            "unsettledProviderCallIds": list(provider_ids),
            "unsettledToolIntentDigests": list(tool_digests),
            "externalDeliveryStanding": "unknown",
            "runtimeClaimStanding": "unknown",
        }
