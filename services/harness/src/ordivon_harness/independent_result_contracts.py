"""Independent Run immutable receipt/proposal contracts; no Store effect owner.

Canonical identities and wire codecs are shared by the terminal read capability
and the Journal writer without either importing Run Continuity.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any

from anc_canonical import (
    JsonValue,
    canonical_bytes,
    canonical_digest,
    loads_strict,
    validate_json_value,
)

from .agent_tool_observation import HarnessArtifactReference, HarnessToolObservation
from .ordivon.events import HarnessTrace
from .ordivon.model import AgentRunConclusion
from .store import StoredHarnessObject


def _exact(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} fields differ: {sorted(set(value) ^ expected)}")


def _text(value: str, label: str, *, max_bytes: int = 2_048) -> str:
    if not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} UTF-8 bytes")
    return value


def _identity(value: str, prefix: str, label: str) -> str:
    _text(value, label, max_bytes=500)
    if not value.startswith(prefix + ":"):
        raise ValueError(f"{label} must start with {prefix}:")
    return value


def _digest(value: str, label: str) -> str:
    if (
        len(value) != 71
        or not value.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def _unique_text(values: tuple[str, ...], label: str) -> None:
    for value in values:
        _text(value, label, max_bytes=1_024)
    if len(values) != len(set(values)):
        raise ValueError(f"{label} values must be unique")

@dataclass(frozen=True, slots=True)
class IndependentHarnessRunReceipt:
    harness_run_id: str
    caller_id: str
    caller_run_ref: str
    contract_digest: str
    harness_implementation_id: str
    system_manifest_digest: str
    started_at_ms: int
    finished_at_ms: int
    stop_reason: str
    termination_code: str
    trace_digest: str
    context_digests: tuple[str, ...]
    tool_catalog_digest: str
    tool_grant_digest: str
    runtime_job_refs: tuple[str, ...]
    artifact_refs: tuple[HarnessArtifactReference, ...]
    # Observer-facing projection; only _usage_bytes participates in evidence identity.
    usage: dict[str, JsonValue] = dataclass_field(compare=False)
    _usage_bytes: bytes = dataclass_field(init=False, repr=False)
    conclusion_digest: str | None = None

    def __post_init__(self) -> None:
        _identity(self.harness_run_id, "harness-run", "Harness Run")
        _identity(self.caller_id, "caller", "Harness caller")
        _text(self.caller_run_ref, "caller Run reference", max_bytes=1_024)
        _digest(self.contract_digest, "Harness Run Contract digest")
        _text(self.harness_implementation_id, "Harness implementation identity", max_bytes=300)
        _digest(self.system_manifest_digest, "System Manifest digest")
        if type(self.started_at_ms) is not int or type(self.finished_at_ms) is not int:
            raise ValueError("independent Harness Run times must be exact integers")
        if self.started_at_ms < 0 or self.finished_at_ms < self.started_at_ms:
            raise ValueError("independent Harness Run times are invalid")
        if self.stop_reason not in {"completed", "stopped", "failed", "unknown"}:
            raise ValueError(f"unsupported independent Run stop reason: {self.stop_reason}")
        _text(self.termination_code, "Harness termination code", max_bytes=300)
        _digest(self.trace_digest, "Harness Trace digest")
        if not self.context_digests:
            raise ValueError("independent Harness Run requires Context digests")
        for digest in self.context_digests:
            _digest(digest, "Harness Context digest")
        if len(self.context_digests) != len(set(self.context_digests)):
            raise ValueError("Harness Context digests must be unique")
        _digest(self.tool_catalog_digest, "Harness Tool catalog digest")
        _digest(self.tool_grant_digest, "Harness Tool grant digest")
        _unique_text(self.runtime_job_refs, "Runtime Job reference")
        refs = [item.ref for item in self.artifact_refs]
        if len(refs) != len(set(refs)):
            raise ValueError("Harness Artifact references must be unique")
        validate_json_value(self.usage)
        # Seal at admission; neither constructor aliases nor readback can
        # rewrite the canonical receipt or its equality/digest identity.
        sealed_usage = canonical_bytes(self.usage)
        object.__setattr__(self, "_usage_bytes", sealed_usage)
        object.__setattr__(self, "usage", loads_strict(sealed_usage))
        if self.conclusion_digest is not None:
            _digest(self.conclusion_digest, "Harness conclusion digest")
        if self.stop_reason == "completed" and self.conclusion_digest is None:
            raise ValueError("completed independent Run requires a conclusion")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 1,
            "kind": "ordivon.independent-harness-run-receipt",
            "harnessRunId": self.harness_run_id,
            "callerId": self.caller_id,
            "callerRunRef": self.caller_run_ref,
            "contractDigest": self.contract_digest,
            "harnessImplementationId": self.harness_implementation_id,
            "systemManifestDigest": self.system_manifest_digest,
            "startedAtMs": self.started_at_ms,
            "finishedAtMs": self.finished_at_ms,
            "stopReason": self.stop_reason,
            "terminationCode": self.termination_code,
            "traceDigest": self.trace_digest,
            "contextDigests": list(self.context_digests),
            "toolCatalogDigest": self.tool_catalog_digest,
            "toolGrantDigest": self.tool_grant_digest,
            "runtimeJobRefs": list(self.runtime_job_refs),
            "artifactRefs": [item.to_dict() for item in self.artifact_refs],
            "usage": loads_strict(self._usage_bytes),
            "conclusionDigest": self.conclusion_digest,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> IndependentHarnessRunReceipt:
        expected = {
            "schemaVersion",
            "kind",
            "harnessRunId",
            "callerId",
            "callerRunRef",
            "contractDigest",
            "harnessImplementationId",
            "systemManifestDigest",
            "startedAtMs",
            "finishedAtMs",
            "stopReason",
            "terminationCode",
            "traceDigest",
            "contextDigests",
            "toolCatalogDigest",
            "toolGrantDigest",
            "runtimeJobRefs",
            "artifactRefs",
            "usage",
            "conclusionDigest",
        }
        _exact(value, expected, "IndependentHarnessRunReceipt")
        if (
            type(value["schemaVersion"]) is not int
            or value["schemaVersion"] != 1
            or value["kind"] != "ordivon.independent-harness-run-receipt"
        ):
            raise ValueError("IndependentHarnessRunReceipt version or kind is invalid")
        string_fields = (
            "harnessRunId",
            "callerId",
            "callerRunRef",
            "contractDigest",
            "harnessImplementationId",
            "systemManifestDigest",
            "stopReason",
            "terminationCode",
            "traceDigest",
            "toolCatalogDigest",
            "toolGrantDigest",
        )
        if any(not isinstance(value[field], str) for field in string_fields):
            raise ValueError("IndependentHarnessRunReceipt identity fields must be strings")
        for field in ("startedAtMs", "finishedAtMs"):
            if type(value[field]) is not int:
                raise ValueError(f"IndependentHarnessRunReceipt {field} must be an integer")
        for field in ("contextDigests", "runtimeJobRefs"):
            if not isinstance(value[field], list) or any(
                not isinstance(item, str) for item in value[field]
            ):
                raise ValueError(f"IndependentHarnessRunReceipt {field} must contain strings")
        artifacts = value["artifactRefs"]
        if not isinstance(artifacts, list) or any(not isinstance(item, dict) for item in artifacts):
            raise ValueError("IndependentHarnessRunReceipt Artifact refs are invalid")
        if not isinstance(value["usage"], dict):
            raise ValueError("IndependentHarnessRunReceipt usage must be an object")
        conclusion_digest = value["conclusionDigest"]
        if conclusion_digest is not None and not isinstance(conclusion_digest, str):
            raise ValueError("IndependentHarnessRunReceipt conclusion digest is invalid")
        return cls(
            harness_run_id=value["harnessRunId"],
            caller_id=value["callerId"],
            caller_run_ref=value["callerRunRef"],
            contract_digest=value["contractDigest"],
            harness_implementation_id=value["harnessImplementationId"],
            system_manifest_digest=value["systemManifestDigest"],
            started_at_ms=value["startedAtMs"],
            finished_at_ms=value["finishedAtMs"],
            stop_reason=value["stopReason"],
            termination_code=value["terminationCode"],
            trace_digest=value["traceDigest"],
            context_digests=tuple(value["contextDigests"]),
            tool_catalog_digest=value["toolCatalogDigest"],
            tool_grant_digest=value["toolGrantDigest"],
            runtime_job_refs=tuple(value["runtimeJobRefs"]),
            artifact_refs=tuple(HarnessArtifactReference.from_dict(item) for item in artifacts),
            usage=dict(value["usage"]),
            conclusion_digest=conclusion_digest,
        )


@dataclass(frozen=True, slots=True)
class IndependentCompletionProposal:
    completion_proposal_id: str
    harness_run_id: str
    caller_id: str
    caller_run_ref: str
    contract_digest: str
    run_receipt_digest: str
    trace_digest: str
    summary: str
    evidence_refs: tuple[str, ...]
    artifact_refs: tuple[str, ...]
    unresolved_unknowns: tuple[str, ...]
    # Observer-facing projection; only _usage_bytes participates in evidence identity.
    usage: dict[str, JsonValue] = dataclass_field(compare=False)
    _usage_bytes: bytes = dataclass_field(init=False, repr=False)
    created_at_ms: int

    def __post_init__(self) -> None:
        _identity(self.completion_proposal_id, "completion-proposal", "Completion Proposal")
        _identity(self.harness_run_id, "harness-run", "Harness Run")
        _identity(self.caller_id, "caller", "Harness caller")
        _text(self.caller_run_ref, "caller Run reference", max_bytes=1_024)
        _digest(self.contract_digest, "Harness Run Contract digest")
        _digest(self.run_receipt_digest, "Harness Run Receipt digest")
        _digest(self.trace_digest, "Harness Trace digest")
        _text(self.summary, "Completion Proposal summary", max_bytes=8_000)
        _unique_text(self.evidence_refs, "Completion evidence reference")
        _unique_text(self.artifact_refs, "Completion Artifact reference")
        _unique_text(self.unresolved_unknowns, "Completion unresolved unknown")
        validate_json_value(self.usage)
        # Seal at admission; neither constructor aliases nor readback can
        # rewrite the canonical receipt or its equality/digest identity.
        sealed_usage = canonical_bytes(self.usage)
        object.__setattr__(self, "_usage_bytes", sealed_usage)
        object.__setattr__(self, "usage", loads_strict(sealed_usage))
        if type(self.created_at_ms) is not int:
            raise ValueError("Completion Proposal creation time must be an exact integer")
        if self.created_at_ms < 0:
            raise ValueError("Completion Proposal creation time must be non-negative")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 2,
            "kind": "ordivon.independent-completion-proposal",
            "completionProposalId": self.completion_proposal_id,
            "harnessRunId": self.harness_run_id,
            "callerId": self.caller_id,
            "callerRunRef": self.caller_run_ref,
            "contractDigest": self.contract_digest,
            "runReceiptDigest": self.run_receipt_digest,
            "traceDigest": self.trace_digest,
            "summary": self.summary,
            "evidenceRefs": list(self.evidence_refs),
            "artifactRefs": list(self.artifact_refs),
            "unresolvedUnknowns": list(self.unresolved_unknowns),
            "usage": loads_strict(self._usage_bytes),
            "createdAtMs": self.created_at_ms,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> IndependentCompletionProposal:
        version = value.get("schemaVersion")
        if type(version) is not int or version not in {1, 2}:
            raise ValueError("IndependentCompletionProposal version or kind is invalid")
        common = {
            "schemaVersion",
            "kind",
            "completionProposalId",
            "harnessRunId",
            "callerId",
            "callerRunRef",
            "contractDigest",
            "runReceiptDigest",
            "traceDigest",
            "summary",
            "evidenceRefs",
            "artifactRefs",
            "usage",
            "createdAtMs",
        }
        expected = common if version == 1 else common | {"unresolvedUnknowns"}
        _exact(value, expected, "IndependentCompletionProposal")
        if value["kind"] != "ordivon.independent-completion-proposal":
            raise ValueError("IndependentCompletionProposal version or kind is invalid")
        for field in (
            "completionProposalId",
            "harnessRunId",
            "callerId",
            "callerRunRef",
            "contractDigest",
            "runReceiptDigest",
            "traceDigest",
            "summary",
        ):
            if not isinstance(value[field], str):
                raise ValueError(f"IndependentCompletionProposal {field} must be a string")
        for field in ("evidenceRefs", "artifactRefs"):
            if not isinstance(value[field], list) or any(
                not isinstance(item, str) for item in value[field]
            ):
                raise ValueError(f"IndependentCompletionProposal {field} must contain strings")
        unresolved = value.get("unresolvedUnknowns", [])
        if not isinstance(unresolved, list) or any(
            not isinstance(item, str) for item in unresolved
        ):
            raise ValueError(
                "IndependentCompletionProposal unresolvedUnknowns must contain strings"
            )
        if not isinstance(value["usage"], dict) or type(value["createdAtMs"]) is not int:
            raise ValueError("IndependentCompletionProposal usage or time is invalid")
        return cls(
            completion_proposal_id=value["completionProposalId"],
            harness_run_id=value["harnessRunId"],
            caller_id=value["callerId"],
            caller_run_ref=value["callerRunRef"],
            contract_digest=value["contractDigest"],
            run_receipt_digest=value["runReceiptDigest"],
            trace_digest=value["traceDigest"],
            summary=value["summary"],
            evidence_refs=tuple(value["evidenceRefs"]),
            artifact_refs=tuple(value["artifactRefs"]),
            unresolved_unknowns=tuple(unresolved),
            usage=dict(value["usage"]),
            created_at_ms=value["createdAtMs"],
        )


@dataclass(frozen=True, slots=True)
class StoredIndependentRunResult:
    receipt: IndependentHarnessRunReceipt
    receipt_object: StoredHarnessObject
    trace: HarnessTrace
    trace_object: StoredHarnessObject
    observations: tuple[HarnessToolObservation, ...]
    observations_object: StoredHarnessObject
    conclusion: AgentRunConclusion | None
    conclusion_object: StoredHarnessObject | None
    completion_proposal: IndependentCompletionProposal | None
    completion_proposal_object: StoredHarnessObject | None
