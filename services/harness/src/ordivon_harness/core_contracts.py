from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field as dataclass_field
from types import MappingProxyType
from typing import Any

from anc_canonical import (
    JsonValue,
    canonical_bytes,
    canonical_digest,
    validate_json_value,
)

from .structured_result_conformance import validate_structured_result_schema

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TRACEPARENT_RE = re.compile(r"^[0-9a-f]{2}-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$")
_CONTENT_POLICIES = {"metadata-only", "bounded-private-content"}
STRUCTURED_COMPLETION_MODE = "structured-result-v1"
_MAX_STRUCTURED_RESULT_SCHEMA_BYTES = 65_536


def _exact(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ValueError(f"{label} fields differ: {sorted(set(value) ^ expected)}")


def _text(value: str, label: str, *, max_bytes: int = 2_048) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} UTF-8 bytes")
    return value


def _identity(value: str, prefix: str, label: str) -> str:
    _text(value, label, max_bytes=300)
    if not value.startswith(prefix + ":"):
        raise ValueError(f"{label} must start with {prefix}:")
    return value


def _digest(value: str, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> JsonValue:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    validate_json_value(value)
    return value


def _json_object(
    value: Mapping[str, JsonValue], label: str, *, require_non_empty: bool = True
) -> None:
    if require_non_empty and not value:
        raise ValueError(f"{label} must be non-empty")
    # ``dataclasses.replace`` may feed an already-frozen MappingProxyType back
    # through the constructor. Validate the canonical JSON projection rather
    # than the container implementation used to prevent post-construction drift.
    validate_json_value(dict(value))


@dataclass(frozen=True, slots=True)
class HarnessBoundReference:
    """One caller-neutral immutable reference used by a Harness Run Contract."""

    ref: str
    kind: str
    digest: str

    def __post_init__(self) -> None:
        _text(self.ref, "Harness reference", max_bytes=1_024)
        _text(self.kind, "Harness reference kind", max_bytes=200)
        _digest(self.digest, "Harness reference digest")

    def to_dict(self) -> dict[str, JsonValue]:
        return {"ref": self.ref, "kind": self.kind, "digest": self.digest}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> HarnessBoundReference:
        _exact(value, {"ref", "kind", "digest"}, "HarnessBoundReference")
        if not all(isinstance(value[key], str) for key in ("ref", "kind", "digest")):
            raise ValueError("HarnessBoundReference fields must be strings")
        return cls(ref=value["ref"], kind=value["kind"], digest=value["digest"])


def _validate_legacy_correlation(value: dict[str, Any]) -> dict[str, JsonValue]:
    """Validate schema-v1 transport correlation for exact historical replay only."""

    _exact(value, {"traceparent", "tracestate", "links"}, "legacy Run correlation")
    traceparent = value["traceparent"]
    tracestate = value["tracestate"]
    links = value["links"]
    if traceparent is not None:
        if not isinstance(traceparent, str) or _TRACEPARENT_RE.fullmatch(traceparent) is None:
            raise ValueError("legacy Harness traceparent is not W3C Trace Context format")
        if traceparent[3:35] == "0" * 32 or traceparent[36:52] == "0" * 16:
            raise ValueError("legacy Harness traceparent cannot use zero Trace or Span identity")
    if tracestate is not None:
        if not isinstance(tracestate, str):
            raise ValueError("legacy Harness tracestate must be a string or null")
        _text(tracestate, "legacy Harness tracestate", max_bytes=512)
    if not isinstance(links, list) or any(not isinstance(item, dict) for item in links):
        raise ValueError("legacy Harness correlation links must be objects")
    decoded_links = tuple(HarnessBoundReference.from_dict(item) for item in links)
    refs = [item.ref for item in decoded_links]
    if len(refs) != len(set(refs)):
        raise ValueError("legacy Harness correlation links must have unique refs")
    return {
        "traceparent": traceparent,
        "tracestate": tracestate,
        "links": [item.to_dict() for item in decoded_links],
    }


@dataclass(frozen=True, slots=True)
class HarnessPrivacyPolicy:
    content_policy: str = "metadata-only"
    allow_model_content: bool = False
    allow_tool_content: bool = False

    def __post_init__(self) -> None:
        if self.content_policy not in _CONTENT_POLICIES:
            raise ValueError(f"unsupported Harness content policy: {self.content_policy}")
        if self.content_policy == "metadata-only" and (
            self.allow_model_content or self.allow_tool_content
        ):
            raise ValueError("metadata-only Harness policy cannot enable content capture")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "contentPolicy": self.content_policy,
            "allowModelContent": self.allow_model_content,
            "allowToolContent": self.allow_tool_content,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> HarnessPrivacyPolicy:
        _exact(
            value,
            {"contentPolicy", "allowModelContent", "allowToolContent"},
            "HarnessPrivacyPolicy",
        )
        if not isinstance(value["contentPolicy"], str):
            raise ValueError("Harness content policy must be a string")
        if (
            type(value["allowModelContent"]) is not bool
            or type(value["allowToolContent"]) is not bool
        ):
            raise ValueError("Harness content capture flags must be booleans")
        return cls(
            content_policy=value["contentPolicy"],
            allow_model_content=value["allowModelContent"],
            allow_tool_content=value["allowToolContent"],
        )


@dataclass(frozen=True, slots=True)
class HarnessRunContract:
    """Caller-neutral immutable authority presented to one Harness Run.

    The contract deliberately contains no Host projection, lease, Journal revision,
    CAS metadata, extension event, Runtime credential, or domain outcome field.
    """

    harness_run_id: str
    harness_implementation_id: str
    caller_id: str
    caller_run_ref: str
    objective_ref: HarnessBoundReference
    context_refs: tuple[HarnessBoundReference, ...]
    provider_id: str
    adapter_id: str
    requested_model_id: str
    tool_catalog_digest: str
    tool_grant_digest: str
    budget: Mapping[str, JsonValue]
    completion_contract: Mapping[str, JsonValue]
    system_manifest_ref: HarnessBoundReference
    created_at_ms: int
    source_refs: tuple[HarnessBoundReference, ...] = ()
    prior_artifact_refs: tuple[HarnessBoundReference, ...] = ()
    privacy: HarnessPrivacyPolicy = HarnessPrivacyPolicy()
    deadline_ms: int | None = None
    _schema_version: int = dataclass_field(default=2, repr=False)
    _legacy_correlation: Mapping[str, JsonValue] | None = dataclass_field(default=None, repr=False)

    def __post_init__(self) -> None:
        _identity(self.harness_run_id, "harness-run", "Harness Run")
        _text(self.harness_implementation_id, "Harness implementation identity", max_bytes=300)
        _identity(self.caller_id, "caller", "Harness caller")
        _text(self.caller_run_ref, "Harness caller Run reference", max_bytes=1_024)
        if not self.context_refs:
            raise ValueError("Harness Run Contract requires at least one Context reference")
        self._unique_refs(self.context_refs, "Context")
        self._unique_refs(self.source_refs, "source")
        self._unique_refs(self.prior_artifact_refs, "prior Artifact")
        _text(self.provider_id, "Harness Provider identity", max_bytes=300)
        _text(self.adapter_id, "Harness Adapter identity", max_bytes=300)
        _text(self.requested_model_id, "Harness requested model identity", max_bytes=300)
        _digest(self.tool_catalog_digest, "Harness Tool catalog digest")
        _digest(self.tool_grant_digest, "Harness Tool grant digest")
        _json_object(self.budget, "Harness budget")
        _json_object(self.completion_contract, "Harness completion contract")
        if self.completion_contract.get("mode") == STRUCTURED_COMPLETION_MODE:
            result_schema = self.completion_contract.get("resultSchema")
            if not isinstance(result_schema, Mapping):
                raise ValueError(
                    "structured completion resultSchema must be an object"
                )
            _json_object(
                result_schema,
                "structured completion resultSchema",
            )
            if len(canonical_bytes(dict(result_schema))) > _MAX_STRUCTURED_RESULT_SCHEMA_BYTES:
                raise ValueError(
                    "structured completion resultSchema exceeds 65536 canonical bytes"
                )
            validate_structured_result_schema(self.completion_contract)
        elif "conformancePolicy" in self.completion_contract:
            raise ValueError(
                "structured completion conformancePolicy requires structured-result-v1"
            )
        object.__setattr__(self, "budget", MappingProxyType(dict(self.budget)))
        completion_snapshot = _thaw_json(self.completion_contract)
        assert isinstance(completion_snapshot, dict)
        object.__setattr__(
            self,
            "completion_contract",
            _freeze_json(completion_snapshot),
        )
        if self._schema_version not in {1, 2}:
            raise ValueError("Harness Run Contract schema version is unsupported")
        if self._schema_version == 1:
            if self._legacy_correlation is None:
                raise ValueError("schema-v1 Harness Run Contract requires legacy correlation")
            correlation_snapshot = _thaw_json(self._legacy_correlation)
            if not isinstance(correlation_snapshot, dict):
                raise ValueError("schema-v1 Harness Run correlation must be an object")
            validated = _validate_legacy_correlation(correlation_snapshot)
            object.__setattr__(self, "_legacy_correlation", _freeze_json(validated))
        elif self._legacy_correlation is not None:
            raise ValueError("schema-v2 Harness Run Contract must not contain correlation")
        if self.created_at_ms < 0:
            raise ValueError("Harness Run creation time must be non-negative")
        if self.deadline_ms is not None:
            if self.deadline_ms < self.created_at_ms:
                raise ValueError("Harness Run deadline precedes creation")

    @staticmethod
    def _unique_refs(values: tuple[HarnessBoundReference, ...], label: str) -> None:
        refs = [item.ref for item in values]
        if len(refs) != len(set(refs)):
            raise ValueError(f"Harness {label} references must be unique")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": self._schema_version,
            "kind": "ordivon.harness-run-contract",
            "harnessRunId": self.harness_run_id,
            "harnessImplementationId": self.harness_implementation_id,
            "callerId": self.caller_id,
            "callerRunRef": self.caller_run_ref,
            "objectiveRef": self.objective_ref.to_dict(),
            "contextRefs": [item.to_dict() for item in self.context_refs],
            "providerId": self.provider_id,
            "adapterId": self.adapter_id,
            "requestedModelId": self.requested_model_id,
            "toolCatalogDigest": self.tool_catalog_digest,
            "toolGrantDigest": self.tool_grant_digest,
            "budget": dict(self.budget),
            "completionContract": _thaw_json(self.completion_contract),
            "systemManifestRef": self.system_manifest_ref.to_dict(),
            "createdAtMs": self.created_at_ms,
            "sourceRefs": [item.to_dict() for item in self.source_refs],
            "priorArtifactRefs": [item.to_dict() for item in self.prior_artifact_refs],
            "privacy": self.privacy.to_dict(),
            "deadlineMs": self.deadline_ms,
        }
        if self._schema_version == 1:
            correlation = _thaw_json(self._legacy_correlation)
            assert isinstance(correlation, dict)
            value["correlation"] = correlation
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> HarnessRunContract:
        schema_version = value.get("schemaVersion")
        if schema_version not in {1, 2} or value.get("kind") != "ordivon.harness-run-contract":
            raise ValueError("HarnessRunContract version or kind is invalid")
        expected = {
            "schemaVersion",
            "kind",
            "harnessRunId",
            "harnessImplementationId",
            "callerId",
            "callerRunRef",
            "objectiveRef",
            "contextRefs",
            "providerId",
            "adapterId",
            "requestedModelId",
            "toolCatalogDigest",
            "toolGrantDigest",
            "budget",
            "completionContract",
            "systemManifestRef",
            "createdAtMs",
            "sourceRefs",
            "priorArtifactRefs",
            "privacy",
            "deadlineMs",
        }
        if schema_version == 1:
            expected.add("correlation")
        _exact(value, expected, "HarnessRunContract")
        string_fields = (
            "harnessRunId",
            "harnessImplementationId",
            "callerId",
            "callerRunRef",
            "providerId",
            "adapterId",
            "requestedModelId",
            "toolCatalogDigest",
            "toolGrantDigest",
        )
        if any(not isinstance(value[field], str) for field in string_fields):
            raise ValueError("HarnessRunContract text and identity fields must be strings")
        object_fields = [
            "objectiveRef",
            "budget",
            "completionContract",
            "systemManifestRef",
            "privacy",
        ]
        if schema_version == 1:
            object_fields.append("correlation")
        if any(not isinstance(value[field], dict) for field in object_fields):
            raise ValueError("HarnessRunContract structured fields must be objects")
        for field in ("contextRefs", "sourceRefs", "priorArtifactRefs"):
            raw = value[field]
            if not isinstance(raw, list) or any(not isinstance(item, dict) for item in raw):
                raise ValueError(f"HarnessRunContract {field} must contain objects")
        created_at_ms = value["createdAtMs"]
        deadline_ms = value["deadlineMs"]
        if type(created_at_ms) is not int:
            raise ValueError("HarnessRunContract creation time must be an integer")
        if deadline_ms is not None and type(deadline_ms) is not int:
            raise ValueError("HarnessRunContract deadline must be an integer or null")
        budget = value["budget"]
        completion = value["completionContract"]
        validate_json_value(budget)
        validate_json_value(completion)
        return cls(
            harness_run_id=value["harnessRunId"],
            harness_implementation_id=value["harnessImplementationId"],
            caller_id=value["callerId"],
            caller_run_ref=value["callerRunRef"],
            objective_ref=HarnessBoundReference.from_dict(value["objectiveRef"]),
            context_refs=tuple(
                HarnessBoundReference.from_dict(item) for item in value["contextRefs"]
            ),
            provider_id=value["providerId"],
            adapter_id=value["adapterId"],
            requested_model_id=value["requestedModelId"],
            tool_catalog_digest=value["toolCatalogDigest"],
            tool_grant_digest=value["toolGrantDigest"],
            budget=dict(budget),
            completion_contract=dict(completion),
            system_manifest_ref=HarnessBoundReference.from_dict(value["systemManifestRef"]),
            created_at_ms=created_at_ms,
            source_refs=tuple(
                HarnessBoundReference.from_dict(item) for item in value["sourceRefs"]
            ),
            prior_artifact_refs=tuple(
                HarnessBoundReference.from_dict(item) for item in value["priorArtifactRefs"]
            ),
            privacy=HarnessPrivacyPolicy.from_dict(value["privacy"]),
            deadline_ms=deadline_ms,
            _schema_version=schema_version,
            _legacy_correlation=(
                dict(value["correlation"]) if schema_version == 1 else None
            ),
        )
