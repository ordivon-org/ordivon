from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from ordivon_harness.api import (
    NO_TOOL_AGENT_GRANT_DIGEST,
    NO_TOOL_AGENT_SURFACE_DIGEST,
    AgentTurnResult,
    HarnessAgentRun,
    HarnessBoundReference,
    HarnessPrivacyPolicy,
    HarnessRunContract,
)
from ordivon_harness.ordivon.model import AgentRunConclusion, ScriptedTurnAdapter

from ordivon_agent import (
    AgentContinuationCoordinator,
    CrossOwnerReentryCoordinator,
    CrossOwnerReentryError,
    ResponseContinuityStore,
    WorkDiscoveryNotFound,
    WorkReattachmentRequest,
)


def _digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def _contract(work_ref: str, harness_run_id: str) -> HarnessRunContract:
    return HarnessRunContract(
        harness_run_id=harness_run_id,
        harness_implementation_id="ordivon-harness@cross-owner-reentry-r1",
        caller_id="caller:chatgpt",
        caller_run_ref=work_ref,
        objective_ref=HarnessBoundReference("objective:r1", "objective", _digest("objective")),
        context_refs=(HarnessBoundReference("context:r1", "context", _digest("context")),),
        provider_id="provider:scripted",
        adapter_id=ScriptedTurnAdapter.adapter_id,
        requested_model_id=ScriptedTurnAdapter.model_id,
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=NO_TOOL_AGENT_GRANT_DIGEST,
        budget={
            "maxModelCalls": 1,
            "maxToolCalls": 0,
            "maxObservationBytes": 65536,
            "maxWallTimeMs": 10000,
            "maxTotalTokens": 1000,
            "maxModelRetries": 0,
            "maxToolCorrections": 0,
            "maxConclusionCorrections": 1,
            "maxObservationOnlyTurns": 1,
            "maxNoProgressTurns": 1,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "manifest:r1", "system-manifest", _digest("manifest")
        ),
        created_at_ms=1000,
        privacy=HarnessPrivacyPolicy(),
    )


class FakeHostPort:
    def __init__(self, work: dict[str, object]) -> None:
        self.work = work
        self.list_calls = 0

    def get_work(self, work_ref: str):
        if self.work.get("workRef") != work_ref:
            raise WorkDiscoveryNotFound(work_ref)
        return self.work

    def list_works(self, *, state: str, limit: int):
        self.list_calls += 1
        return {"works": [], "hasMore": False}


def _work(work_ref: str, harness_run_id: str, refs: tuple[str, ...] | None = None):
    reference_refs = (
        refs
        if refs is not None
        else (
            f"harness:run:{harness_run_id}",
            "runtime:job:job-r1",
            "provider:effect:effect-r1",
            "git:revision:abc123",
        )
    )
    return {
        "workRef": work_ref,
        "workKind": "research",
        "state": "open",
        "revision": 3,
        "createdByActorRef": "actor:agent:emm",
        "writerActorRef": "actor:agent:emm",
        "snapshot": {
            "objective": "test bounded cross-owner re-entry",
            "referenceRefs": list(reference_refs),
        },
    }


def _adapter(_contract):
    return ScriptedTurnAdapter(
        (
            AgentTurnResult(
                model_call_id="model-call:cross-owner-reentry-r1",
                model_id=ScriptedTurnAdapter.model_id,
                content="ready",
                tool_calls=(),
                conclusion=AgentRunConclusion(
                    status="candidate_completed",
                    summary="fixture result",
                ),
                usage={"inputTokens": 1, "outputTokens": 1},
                finish_reason="stop",
                raw_response_digest=_digest("fixture-result"),
            ),
        )
    )


def test_projection_composes_work_harness_and_effect_refs_without_authority_transfer():
    work_ref = "work:research:emm-cross-owner:r1"
    harness_run_id = "harness-run:emm-cross-owner:r1"
    with TemporaryDirectory() as directory:
        root = Path(directory)
        HarnessAgentRun.create(root / "harness", _contract(work_ref, harness_run_id), _adapter)
        port = FakeHostPort(_work(work_ref, harness_run_id))
        with ResponseContinuityStore(root / "responses") as responses:
            run, plan, projection = CrossOwnerReentryCoordinator(
                port, AgentContinuationCoordinator(responses)
            ).resolve_and_inspect(
                WorkReattachmentRequest(exact_work_ref=work_ref),
                root / "harness",
                "caller:chatgpt",
                _adapter,
            )

        assert run.harness_run_id == harness_run_id
        assert plan.caller_run_ref == work_ref
        assert port.list_calls == 0
        assert projection.harness_ref == f"harness:run:{harness_run_id}"
        assert projection.runtime_refs == ("runtime:job:job-r1",)
        assert projection.other_refs == (
            "provider:effect:effect-r1",
            "git:revision:abc123",
        )
        assert projection.physical_revalidation_required is True
        assert projection.effect_redispatch_allowed is False
        view = projection.to_dict()
        assert view["truthRole"] == "derived-read-only-cross-owner-navigation-projection"
        assert view["continuation"]["effectRedispatchAllowed"] is False
        assert view["harness"]["callerRunRef"] == work_ref
        assert "provider" not in view["references"]
        assert view["references"]["other"] == [
            "provider:effect:effect-r1",
            "git:revision:abc123",
        ]


def test_mismatched_host_harness_reference_fails_closed():
    work_ref = "work:research:emm-cross-owner:mismatch"
    harness_run_id = "harness-run:emm-cross-owner:mismatch"
    with TemporaryDirectory() as directory:
        root = Path(directory)
        HarnessAgentRun.create(root / "harness", _contract(work_ref, harness_run_id), _adapter)
        port = FakeHostPort(
            _work(work_ref, harness_run_id, refs=("harness:run:harness-run:other",))
        )
        with ResponseContinuityStore(root / "responses") as responses:
            with pytest.raises(CrossOwnerReentryError, match="differs from the Run"):
                CrossOwnerReentryCoordinator(
                    port, AgentContinuationCoordinator(responses)
                ).resolve_and_inspect(
                    WorkReattachmentRequest(exact_work_ref=work_ref),
                    root / "harness",
                    "caller:chatgpt",
                    _adapter,
                )


def test_multiple_harness_refs_fail_closed_instead_of_guessing():
    work_ref = "work:research:emm-cross-owner:ambiguous"
    harness_run_id = "harness-run:emm-cross-owner:ambiguous"
    with TemporaryDirectory() as directory:
        root = Path(directory)
        HarnessAgentRun.create(root / "harness", _contract(work_ref, harness_run_id), _adapter)
        port = FakeHostPort(
            _work(
                work_ref,
                harness_run_id,
                refs=(f"harness:run:{harness_run_id}", "harness:run:harness-run:stale"),
            )
        )
        with ResponseContinuityStore(root / "responses") as responses:
            with pytest.raises(CrossOwnerReentryError, match="exactly one Harness Run reference"):
                CrossOwnerReentryCoordinator(
                    port, AgentContinuationCoordinator(responses)
                ).resolve_and_inspect(
                    WorkReattachmentRequest(exact_work_ref=work_ref),
                    root / "harness",
                    "caller:chatgpt",
                    _adapter,
                )


def test_missing_work_bound_harness_run_fails_closed():
    work_ref = "work:research:emm-cross-owner:no-run"
    harness_run_id = "harness-run:emm-cross-owner:no-run"
    with TemporaryDirectory() as directory:
        root = Path(directory)
        port = FakeHostPort(_work(work_ref, harness_run_id))
        with ResponseContinuityStore(root / "responses") as responses:
            with pytest.raises(CrossOwnerReentryError, match="no durable Harness Run"):
                CrossOwnerReentryCoordinator(
                    port, AgentContinuationCoordinator(responses)
                ).resolve_and_inspect(
                    WorkReattachmentRequest(exact_work_ref=work_ref),
                    root / "harness",
                    "caller:chatgpt",
                    _adapter,
                )
