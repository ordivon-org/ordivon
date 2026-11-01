from __future__ import annotations

from types import SimpleNamespace

import pytest

from anc_canonical import canonical_digest

from ordivon_harness.independent_result import (
    IndependentCompletionProposal,
    IndependentHarnessRunReceipt,
    IndependentRunRecorder,
)
from ordivon_harness.ordivon.events import HarnessRunEvent, HarnessTrace
from ordivon_harness.ordivon.loop import RunStopCode
from ordivon_harness.ordivon.model import AgentRunConclusion

DIGEST = "sha256:" + "a" * 64
RUN = "harness-run:claim-readback"
CALLER = "caller:claim-readback"
CALLER_REF = "caller-run:claim-readback"


def _readback_with_proposal_changes(
    *, overrides: dict | None = None, legacy_v1: bool = False,
    source_unknowns: tuple[str, ...] = ("external acceptance missing",)
) -> object:
    """Exercise the real persistence readback against *individually valid* stored objects.

    All content-addressed event and object references agree. Only semantic
    cross-object identity and source-conclusion claim equivalence can catch
    the mismatch.
    """
    trace = HarnessTrace(
        RUN,
        (HarnessRunEvent(1, "run_started", 0, {"source": "exact-contract"}),),
    )
    conclusion = AgentRunConclusion(
        status="candidate_completed",
        summary="Source candidate, not domain verified",
        evidence_refs=("evidence:source-unverified",),
        artifact_refs=("artifact:source",),
        unresolved_unknowns=source_unknowns,
    )
    receipt = IndependentHarnessRunReceipt(
        harness_run_id=RUN,
        caller_id=CALLER,
        caller_run_ref=CALLER_REF,
        contract_digest=DIGEST,
        harness_implementation_id="harness:local",
        system_manifest_digest=DIGEST,
        started_at_ms=0,
        finished_at_ms=1,
        stop_reason="completed",
        termination_code=RunStopCode.CANDIDATE_COMPLETED.value,
        trace_digest=trace.digest,
        context_digests=(DIGEST,),
        tool_catalog_digest=DIGEST,
        tool_grant_digest=DIGEST,
        runtime_job_refs=(),
        artifact_refs=(),
        usage={"totalTokens": 5},
        conclusion_digest=canonical_digest(conclusion.to_dict()),
    )
    fields = dict(
        completion_proposal_id="completion-proposal:claim-readback",
        harness_run_id=receipt.harness_run_id,
        caller_id=receipt.caller_id,
        caller_run_ref=receipt.caller_run_ref,
        contract_digest=receipt.contract_digest,
        run_receipt_digest=receipt.digest,
        trace_digest=trace.digest,
        summary=conclusion.summary,
        evidence_refs=conclusion.evidence_refs,
        artifact_refs=conclusion.artifact_refs,
        unresolved_unknowns=conclusion.unresolved_unknowns,
        usage=receipt.usage,
        created_at_ms=2,
    )
    fields.update(overrides or {})
    proposal = IndependentCompletionProposal(**fields)
    encoded_proposal = proposal.to_dict()
    if legacy_v1:
        encoded_proposal["schemaVersion"] = 1
        encoded_proposal.pop("unresolvedUnknowns")
    # v1 hashes differ from schema-v2 object hashes; this is still valid
    # canonical object evidence, and independent readback must support it.
    proposal_object_digest = canonical_digest(encoded_proposal)
    data = {
        "runReceiptObjectDigest": receipt.digest,
        "traceObjectDigest": trace.digest,
        "observationsObjectDigest": DIGEST,
        "conclusionObjectDigest": receipt.conclusion_digest,
        "completionProposalObjectDigest": proposal_object_digest,
        "runReceiptDigest": receipt.digest,
        "traceDigest": trace.digest,
        "conclusionDigest": receipt.conclusion_digest,
        "completionProposalDigest": (
            proposal_object_digest if legacy_v1 else proposal.digest
        ),
    }

    class ValidContentAddressedStore:
        def list_run_events(self, harness_run_id):
            assert harness_run_id == RUN
            return [SimpleNamespace(event_kind="harness.run-completed", data=data)]

        def get_object(self, object_digest, *, expected_kind):
            known = {
                "independent-harness-run-receipt": (receipt.digest, receipt.to_dict()),
                "harness-trace": (trace.digest, trace.to_dict()),
                "harness-tool-observations": (DIGEST, []),
                "harness-run-conclusion": (receipt.conclusion_digest, conclusion.to_dict()),
                "independent-completion-proposal": (proposal_object_digest, encoded_proposal),
            }
            expected_digest, content = known[expected_kind]
            assert object_digest == expected_digest, (object_digest, expected_digest)
            return content

        def inspect_object(self, object_digest):
            return SimpleNamespace(digest=object_digest)

    recorder = object.__new__(IndependentRunRecorder)
    recorder.contract = SimpleNamespace(
        harness_run_id=RUN,
        digest=DIGEST,
        privacy=SimpleNamespace(allow_model_content=True, allow_tool_content=True),
    )
    recorder.store = ValidContentAddressedStore()
    return recorder.load_terminal_result()


def test_valid_independent_completion_proposal_retains_original_claims() -> None:
    result = _readback_with_proposal_changes()
    assert result.completion_proposal is not None
    assert result.conclusion is not None
    assert result.completion_proposal.summary == result.conclusion.summary
    assert result.completion_proposal.unresolved_unknowns == (
        "external acceptance missing",
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"harness_run_id": "harness-run:foreign"}, "identity"),
        ({"caller_id": "caller:foreign"}, "identity"),
        ({"caller_run_ref": "caller-run:foreign"}, "identity"),
        ({"summary": "Domain VERIFIED: fabricated"}, "claims"),
        ({"evidence_refs": ("evidence:unobserved",)}, "claims"),
        ({"artifact_refs": ("artifact:forged",)}, "claims"),
        ({"unresolved_unknowns": ()}, "claims"),
        ({"usage": {"totalTokens": 999}}, "claims"),
    ],
)
def test_independent_completion_proposal_cannot_rebind_source_claim(
    mutation: dict, message: str
) -> None:
    with pytest.raises(ValueError, match=f"Completion Proposal {message}"):
        _readback_with_proposal_changes(overrides=mutation)


def test_legacy_v1_without_source_unknowns_remains_readable() -> None:
    # Historical v1 had no unresolvedUnknowns field. If the source had none,
    # accept the original v1 wire digest, without rewriting its evidence.
    result = _readback_with_proposal_changes(legacy_v1=True, source_unknowns=())
    assert result.conclusion.unresolved_unknowns == ()
    assert result.completion_proposal.unresolved_unknowns == ()


def test_legacy_v1_cannot_erase_original_unresolved_unknowns() -> None:
    # Missing v1 fields cannot be interpreted as affirmative absence when
    # the retained source conclusion actually carries unresolved claims.
    with pytest.raises(ValueError, match="Completion Proposal claims"):
        _readback_with_proposal_changes(legacy_v1=True)
