from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import re
from types import MappingProxyType
from typing import Any
import unicodedata

from anc_canonical import JsonValue, canonical_digest

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _text(value: str, label: str, *, max_bytes: int = 300) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} UTF-8 bytes")
    return value


def _digest(value: str, label: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def _runtime_logical_id(value: object, label: str) -> str:
    """Validate Runtime's current logical-id contract at the Harness boundary."""

    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    if not 1 <= len(value) <= 256 or value != value.strip() or any(
        unicodedata.category(character) == "Cc" for character in value
    ):
        raise ValueError(
            f"{label} must contain 1..=256 Unicode characters, be trimmed, and be control-free"
        )
    return value


def _normalize_runtime_reference(
    value: Mapping[str, Any],
) -> Mapping[str, JsonValue]:
    """Freeze one Runtime-native ForeignReference mapping without minting a Harness value type."""

    allowed = {"namespace", "type", "id", "generation", "digest"}
    if not isinstance(value, Mapping):
        raise ValueError("Runtime foreign reference must be a mapping")
    if not {"namespace", "type", "id"}.issubset(value) or set(value) - allowed:
        raise ValueError("Runtime foreign reference fields differ")
    normalized: dict[str, JsonValue] = {
        "namespace": _runtime_logical_id(value["namespace"], "Runtime reference namespace"),
        "type": _runtime_logical_id(value["type"], "Runtime reference type"),
        "id": _runtime_logical_id(value["id"], "Runtime reference identity"),
    }
    for field in ("generation", "digest"):
        item = value.get(field)
        if item is not None:
            normalized[field] = _runtime_logical_id(item, f"Runtime reference {field}")
    return MappingProxyType(normalized)


@dataclass(frozen=True, slots=True)
class HarnessExecutionBinding:
    """Minimal caller-supplied Runtime target binding for one Harness Run.

    Contract/continuity facts stay owned by their canonical sources. This binding
    carries only the Run identity needed to prevent cross-Run reuse plus the exact
    Runtime Workspace and foreign references actually sent to Runtime.
    """

    harness_run_id: str
    workspace_ref: str
    runtime_references: tuple[Mapping[str, JsonValue], ...]

    def __post_init__(self) -> None:
        _text(self.harness_run_id, "Harness Run identity")
        if not self.harness_run_id.startswith("harness-run:"):
            raise ValueError("Harness Run identity must start with harness-run:")
        _text(self.workspace_ref, "Runtime Workspace reference")
        references = tuple(_normalize_runtime_reference(reference) for reference in self.runtime_references)
        keys = [
            (reference["namespace"], reference["type"], reference["id"])
            for reference in references
        ]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("Runtime references must be uniquely sorted")
        object.__setattr__(self, "runtime_references", references)

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 2,
            "kind": "ordivon.harness-execution-binding",
            "harnessRunId": self.harness_run_id,
            "workspaceRef": self.workspace_ref,
            "runtimeReferences": [dict(reference) for reference in self.runtime_references],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> HarnessExecutionBinding:
        expected = {
            "schemaVersion",
            "kind",
            "harnessRunId",
            "workspaceRef",
            "runtimeReferences",
        }
        if set(value) != expected:
            raise ValueError(
                f"HarnessExecutionBinding fields differ: {sorted(set(value) ^ expected)}"
            )
        if value["schemaVersion"] != 2 or value["kind"] != "ordivon.harness-execution-binding":
            raise ValueError("HarnessExecutionBinding version or kind is invalid")
        if not isinstance(value["harnessRunId"], str) or not isinstance(value["workspaceRef"], str):
            raise ValueError("HarnessExecutionBinding identity fields must be strings")
        references = value["runtimeReferences"]
        if not isinstance(references, list) or any(
            not isinstance(item, dict) for item in references
        ):
            raise ValueError("HarnessExecutionBinding references must be objects")
        return cls(
            harness_run_id=value["harnessRunId"],
            workspace_ref=value["workspaceRef"],
            runtime_references=tuple(dict(item) for item in references),
        )

    def client_request_id(self, step_id: str) -> str:
        _text(step_id, "Harness Runtime step identity", max_bytes=200)
        digest = canonical_digest(
            {
                "schemaVersion": 2,
                "kind": "ordivon.harness-runtime-request-identity",
                "executionBindingDigest": self.digest,
                "stepId": step_id,
            }
        )
        return f"request:harness:{digest[7:39]}"

    def patch_request_id(self, step_id: str, tool_call_digest: str) -> str:
        _text(step_id, "Harness Runtime step identity", max_bytes=200)
        _digest(tool_call_digest, "Tool Call digest")
        token = canonical_digest(
            {
                "schemaVersion": 2,
                "kind": "ordivon.harness-runtime-patch-request-identity",
                "executionBindingDigest": self.digest,
                "stepId": step_id,
                "toolCallDigest": tool_call_digest,
            }
        )[7:39]
        return f"request:harness-patch:{token}"
