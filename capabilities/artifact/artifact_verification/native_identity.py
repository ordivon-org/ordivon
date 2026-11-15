"""Pure consistency check between a native verifier report and its input commitment.

This is not a second format schema. It checks common facts already exposed by
existing family-native verifiers and keeps unreported legacy fields UNKNOWN.
"""
from __future__ import annotations

from typing import Any


def assess_native_identity(
    native: dict[str, Any],
    *,
    profile_id: str,
    subject_sha256: str,
    subject_size: int,
    contract_sha256: str | None,
    require_complete: bool,
) -> dict[str, Any]:
    """Any contradictory identity evidence is fatal; missing facts stay unknown.

    Exact byte identity is distinct from the provider's truthfulness. The
    report's claimed digest is independently compared to the input commitment;
    this function cannot prove that external tools read the bytes.
    """
    mismatches: list[str] = []
    not_evaluated: list[str] = []
    observations: dict[str, str] = {}

    def check(field: str, value: object, expected: object) -> None:
        if value is None:
            observations[field] = "NOT_EVALUATED"
            not_evaluated.append(field)
        elif type(value) is not type(expected) or value != expected:
            observations[field] = "FAIL"
            mismatches.append(f"native evidence identity mismatch: {field}")
        else:
            observations[field] = "PASS"

    check("profileId", native.get("profileId"), profile_id)

    artifact = native.get("artifact")
    if artifact is None:
        check("artifact.sha256", None, subject_sha256)
        check("artifact.size", None, subject_size)
    elif isinstance(artifact, dict):
        check("artifact.sha256", artifact.get("sha256"), subject_sha256)
        check("artifact.size", artifact.get("size"), subject_size)
    else:
        mismatches.append("native artifact identity is not an object")
        observations["artifact.sha256"] = "FAIL"
        observations["artifact.size"] = "FAIL"

    if contract_sha256 is not None:
        contract = native.get("contract")
        if contract is None:
            check("contract.sha256", None, contract_sha256)
        elif isinstance(contract, dict):
            check("contract.sha256", contract.get("sha256"), contract_sha256)
        else:
            mismatches.append("native contract identity is not an object")
            observations["contract.sha256"] = "FAIL"

    complete = not mismatches and not not_evaluated
    rejected = bool(mismatches) or (require_complete and bool(not_evaluated))
    return {
        "status": (
            "COMPLETE" if complete else
            "INCOMPLETE" if mismatches else
            "NOT_EVALUATED"
        ),
        "complete": complete,
        "rejected": rejected,
        "observations": observations,
        "mismatches": mismatches,
        "notEvaluated": not_evaluated,
        "boundary": (
            "Native-result identity consistency against request-bound bytes. "
            "Missing legacy facts remain NOT_EVALUATED; contradiction is never "
            "treated as PASS. This does not prove native verifier truthfulness, "
            "external decoder correctness or target consumer acceptance."
        ),
    }
