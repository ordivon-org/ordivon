from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ordivon_harness.api import HarnessAgentRun

from .continuation_r1 import (
    AgentContinuationCoordinator,
    AgentContinuationPlan,
    AttentionReplayPort,
)
from .work_reattachment_r1 import (
    HostWorkDiscoveryPort,
    WorkReattachmentCoordinator,
    WorkReattachmentRequest,
    WorkReattachmentStanding,
)


class CrossOwnerReentryError(RuntimeError):
    """A bounded Work -> Harness -> effect navigation projection cannot be proven."""


@dataclass(frozen=True, slots=True)
class CrossOwnerReentryProjection:
    work_ref: str
    work_revision: int
    harness_run_id: str
    harness_run_revision: int
    caller_id: str
    continuation_action: str
    reference_refs: tuple[str, ...]
    harness_ref: str
    runtime_refs: tuple[str, ...]
    provider_refs: tuple[str, ...]
    other_refs: tuple[str, ...]
    response_rehydration_required: bool
    physical_revalidation_required: bool = True
    effect_redispatch_allowed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.agent-cross-owner-reentry-projection",
            "truthRole": "derived-read-only-cross-owner-navigation-projection",
            "work": {
                "workRef": self.work_ref,
                "revision": self.work_revision,
            },
            "harness": {
                "harnessRunId": self.harness_run_id,
                "runRevision": self.harness_run_revision,
                "callerId": self.caller_id,
                "callerRunRef": self.work_ref,
                "referenceRef": self.harness_ref,
            },
            "continuation": {
                "action": self.continuation_action,
                "responseRehydrationRequired": self.response_rehydration_required,
                "effectRedispatchAllowed": self.effect_redispatch_allowed,
            },
            "references": {
                "all": list(self.reference_refs),
                "runtime": list(self.runtime_refs),
                "provider": list(self.provider_refs),
                "other": list(self.other_refs),
            },
            "physicalRevalidationRequired": self.physical_revalidation_required,
            "proofBoundary": (
                "This is navigation/correlation only. Host remains semantic continuity owner; "
                "Harness, Runtime, Provider, Git, and domain truth must be re-read at their "
                "natural owners before consequential action. The projection never authorizes "
                "effect redispatch."
            ),
        }


class CrossOwnerReentryCoordinator:
    """Compose existing owner-native continuation primitives without creating new authority.

    The coordinator first reattaches to canonical Host Work, then opens the unique durable
    Harness Run whose callerRunRef is exactly that WorkRef. Host referenceRefs must contain
    exactly one Harness reference matching the recovered Run. Runtime/provider references are
    retained verbatim for later owner-native reconciliation; their state is never copied here.
    """

    def __init__(
        self,
        work_port: HostWorkDiscoveryPort,
        continuation: AgentContinuationCoordinator,
    ) -> None:
        self.work_port = work_port
        self.work = WorkReattachmentCoordinator(work_port)
        self.continuation = continuation

    def resolve_and_inspect(
        self,
        request: WorkReattachmentRequest,
        state_root: str | Path,
        caller_id: str,
        adapter_factory,
        *,
        attention_actor_ref: str | None = None,
        attention_replay: AttentionReplayPort | None = None,
        **run_open_kwargs,
    ) -> tuple[HarnessAgentRun, AgentContinuationPlan, CrossOwnerReentryProjection]:
        reattachment = self.work.resolve(request)
        if (
            reattachment.standing is not WorkReattachmentStanding.REATTACH
            or reattachment.canonical_work_ref is None
        ):
            raise CrossOwnerReentryError(
                f"Host Work reattachment is {reattachment.standing.value}; exact continuation is unavailable"
            )
        work_ref = reattachment.canonical_work_ref
        work = self.work_port.get_work(work_ref)
        if work.get("workRef") != work_ref:
            raise CrossOwnerReentryError("Host Work projection changed canonical Work identity")
        work_revision = work.get("revision")
        if type(work_revision) is not int or work_revision < 1:
            raise CrossOwnerReentryError("Host Work projection omitted a positive revision")
        snapshot = work.get("snapshot")
        if not isinstance(snapshot, dict):
            raise CrossOwnerReentryError("Host Work projection omitted snapshot")
        raw_refs = snapshot.get("referenceRefs")
        if not isinstance(raw_refs, list) or any(
            not isinstance(ref, str) or not ref or ref != ref.strip() for ref in raw_refs
        ):
            raise CrossOwnerReentryError("Host Work snapshot omitted valid referenceRefs")
        refs = tuple(raw_refs)
        if len(refs) != len(set(refs)):
            raise CrossOwnerReentryError("Host Work snapshot referenceRefs are not unique")

        try:
            run, plan = self.continuation.locate_and_inspect(
                state_root,
                caller_id,
                work_ref,
                adapter_factory,
                attention_actor_ref=attention_actor_ref,
                attention_replay=attention_replay,
                **run_open_kwargs,
            )
        except (KeyError, FileNotFoundError) as error:
            raise CrossOwnerReentryError(
                "no durable Harness Run is bound to the canonical WorkRef callerRunRef"
            ) from error
        if plan.caller_run_ref != work_ref:
            raise CrossOwnerReentryError("Harness callerRunRef differs from canonical WorkRef")

        harness_refs = tuple(ref for ref in refs if ref.startswith("harness:run:"))
        if len(harness_refs) != 1:
            raise CrossOwnerReentryError(
                "Host Work must retain exactly one Harness Run reference for bounded re-entry"
            )
        expected_harness_ref = f"harness:run:{plan.harness_run_id}"
        if harness_refs[0] != expected_harness_ref:
            raise CrossOwnerReentryError(
                "Host Harness reference differs from the Run bound to canonical WorkRef"
            )

        runtime_refs = tuple(ref for ref in refs if ref.startswith("runtime:"))
        provider_refs = tuple(ref for ref in refs if ref.startswith("provider:"))
        other_refs = tuple(
            ref
            for ref in refs
            if ref != expected_harness_ref
            and not ref.startswith("runtime:")
            and not ref.startswith("provider:")
        )
        projection = CrossOwnerReentryProjection(
            work_ref=work_ref,
            work_revision=work_revision,
            harness_run_id=plan.harness_run_id,
            harness_run_revision=plan.run_revision,
            caller_id=plan.caller_id,
            continuation_action=plan.action.value,
            reference_refs=refs,
            harness_ref=expected_harness_ref,
            runtime_refs=runtime_refs,
            provider_refs=provider_refs,
            other_refs=other_refs,
            response_rehydration_required=plan.response_rehydration_required,
        )
        return run, plan, projection


__all__ = [
    "CrossOwnerReentryCoordinator",
    "CrossOwnerReentryError",
    "CrossOwnerReentryProjection",
]
