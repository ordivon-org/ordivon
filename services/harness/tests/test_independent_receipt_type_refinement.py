"""R2.1 CEGAR: native JSON receipt version and clock identities are exact integers."""

from dataclasses import replace

import pytest

from ordivon_harness.independent_result import (
    IndependentCompletionProposal,
    IndependentHarnessRunReceipt,
)

DIGEST = "sha256:" + "a" * 64


def _receipt() -> IndependentHarnessRunReceipt:
    return IndependentHarnessRunReceipt(
        harness_run_id="harness-run:target",
        caller_id="caller:target",
        caller_run_ref="run:target",
        contract_digest=DIGEST,
        harness_implementation_id="harness:local",
        system_manifest_digest=DIGEST,
        started_at_ms=1,
        finished_at_ms=2,
        stop_reason="failed",
        termination_code="harness_failed",
        trace_digest=DIGEST,
        context_digests=(DIGEST,),
        tool_catalog_digest=DIGEST,
        tool_grant_digest=DIGEST,
        runtime_job_refs=(),
        artifact_refs=(),
        usage={},
    )


def _proposal() -> IndependentCompletionProposal:
    return IndependentCompletionProposal(
        completion_proposal_id="completion-proposal:target",
        harness_run_id="harness-run:target",
        caller_id="caller:target",
        caller_run_ref="run:target",
        contract_digest=DIGEST,
        run_receipt_digest=DIGEST,
        trace_digest=DIGEST,
        summary="Candidate only",
        evidence_refs=(),
        artifact_refs=(),
        unresolved_unknowns=(),
        usage={},
        created_at_ms=3,
    )


@pytest.mark.parametrize("alias", [True, 1.0, "1", None, 2])
def test_independent_receipt_version_requires_exact_integer(alias: object) -> None:
    encoded = _receipt().to_dict()
    encoded["schemaVersion"] = alias
    with pytest.raises(ValueError, match="version"):
        IndependentHarnessRunReceipt.from_dict(encoded)


@pytest.mark.parametrize("alias", [True, 1.0, "1", None, 2.0])
def test_independent_proposal_version_requires_exact_integer(alias: object) -> None:
    encoded = _proposal().to_dict()
    encoded["schemaVersion"] = alias
    if alias is True or alias == 1.0:
        # The legacy v1 shape may omit unresolvedUnknowns, but a bool/float
        # must never be used to masquerade as an earlier protocol version.
        encoded.pop("unresolvedUnknowns")
    with pytest.raises(ValueError, match="version"):
        IndependentCompletionProposal.from_dict(encoded)


@pytest.mark.parametrize("field", ["started_at_ms", "finished_at_ms"])
@pytest.mark.parametrize("alias", [True, 1.0])
def test_direct_receipt_times_cannot_be_bool_or_float(field: str, alias: object) -> None:
    with pytest.raises(ValueError, match="exact integers"):
        replace(_receipt(), **{field: alias})


@pytest.mark.parametrize("alias", [True, 3.0])
def test_direct_proposal_creation_time_requires_exact_integer(alias: object) -> None:
    with pytest.raises(ValueError, match="exact integer"):
        replace(_proposal(), created_at_ms=alias)


def test_valid_legacy_proposal_version_one_remains_decodable() -> None:
    encoded = _proposal().to_dict()
    encoded["schemaVersion"] = 1
    encoded.pop("unresolvedUnknowns")
    assert IndependentCompletionProposal.from_dict(encoded).unresolved_unknowns == ()
