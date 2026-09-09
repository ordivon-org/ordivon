from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from anc_canonical import JsonValue, canonical_digest, validate_json_value

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


@dataclass(frozen=True, slots=True)
class HarnessRuntimeReference:
    namespace: str
    reference_type: str
    reference_id: str
    generation: str | None = None
    digest: str | None = None

    def __post_init__(self) -> None:
        _text(self.namespace, "Runtime reference namespace", max_bytes=120)
        _text(self.reference_type, "Runtime reference type", max_bytes=120)
        _text(self.reference_id, "Runtime reference identity")
        if self.generation is not None:
            _text(self.generation, "Runtime reference generation", max_bytes=120)
        if self.digest is not None:
            _digest(self.digest, "Runtime reference digest")

    @property
    def sort_key(self) -> tuple[str, str, str]:
        return (self.namespace, self.reference_type, self.reference_id)

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "namespace": self.namespace,
            "type": self.reference_type,
            "id": self.reference_id,
        }
        if self.generation is not None:
            value["generation"] = self.generation
        if self.digest is not None:
            value["digest"] = self.digest
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> HarnessRuntimeReference:
        allowed = {"namespace", "type", "id", "generation", "digest"}
        if not {"namespace", "type", "id"}.issubset(value) or set(value) - allowed:
            raise ValueError("HarnessRuntimeReference fields differ")
        for field in ("namespace", "type", "id"):
            if not isinstance(value[field], str):
                raise ValueError("HarnessRuntimeReference identity fields must be strings")
        generation = value.get("generation")
        digest = value.get("digest")
        if generation is not None and not isinstance(generation, str):
            raise ValueError("HarnessRuntimeReference generation must be a string")
        if digest is not None and not isinstance(digest, str):
            raise ValueError("HarnessRuntimeReference digest must be a string")
        return cls(
            namespace=value["namespace"],
            reference_type=value["type"],
            reference_id=value["id"],
            generation=generation,
            digest=digest,
        )


@dataclass(frozen=True, slots=True)
class HarnessExecutionBinding:
    """Minimal caller-supplied Runtime target binding for one Harness Run.

    Contract/continuity facts stay owned by their canonical sources. This binding
    carries only the Run identity needed to prevent cross-Run reuse plus the exact
    Runtime Workspace and foreign references actually sent to Runtime.
    """

    harness_run_id: str
    workspace_ref: str
    runtime_references: tuple[HarnessRuntimeReference, ...]

    def __post_init__(self) -> None:
        _text(self.harness_run_id, "Harness Run identity")
        if not self.harness_run_id.startswith("harness-run:"):
            raise ValueError("Harness Run identity must start with harness-run:")
        _text(self.workspace_ref, "Runtime Workspace reference")
        keys = [reference.sort_key for reference in self.runtime_references]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            raise ValueError("Runtime references must be uniquely sorted")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "schemaVersion": 2,
            "kind": "ordivon.harness-execution-binding",
            "harnessRunId": self.harness_run_id,
            "workspaceRef": self.workspace_ref,
            "runtimeReferences": [reference.to_dict() for reference in self.runtime_references],
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
            runtime_references=tuple(
                HarnessRuntimeReference.from_dict(item) for item in references
            ),
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


def build_harness_workspace_exec_request_from_binding(
    binding: HarnessExecutionBinding,
    *,
    step_id: str,
    executable: str,
    args: tuple[str, ...] = (),
    cwd_relative: str = ".",
    env: dict[str, str] | None = None,
    timeout_ms: int = 30_000,
    stdout_limit_bytes: int = 262_144,
    stderr_limit_bytes: int = 262_144,
    wait_ms: int = 0,
    stdout_tail_bytes: int = 8_192,
    stderr_tail_bytes: int = 8_192,
) -> dict[str, JsonValue]:
    _text(executable, "Runtime executable")
    if not executable.startswith("/"):
        raise ValueError("Runtime executable must be absolute")
    _text(cwd_relative, "Runtime working directory")
    for argument in args:
        if not isinstance(argument, str):
            raise ValueError("Runtime arguments must be strings")
    environment = {} if env is None else dict(env)
    if any(
        not isinstance(key, str) or not isinstance(item, str) or not key or key != key.strip()
        for key, item in environment.items()
    ):
        raise ValueError("Runtime environment must contain trimmed string keys and values")
    if timeout_ms < 0:
        raise ValueError("Runtime timeout must be non-negative")
    if stdout_limit_bytes < 0 or stderr_limit_bytes < 0:
        raise ValueError("Runtime output limits must be non-negative")
    if wait_ms < 0 or wait_ms > 30_000:
        raise ValueError("Runtime wait must be between 0 and 30000 milliseconds")
    if not 0 <= stdout_tail_bytes <= 65_536 or not 0 <= stderr_tail_bytes <= 65_536:
        raise ValueError("Runtime tail limits must be between 0 and 65536 bytes")
    request: dict[str, JsonValue] = {
        "schemaVersion": 1,
        "clientRequestId": binding.client_request_id(step_id),
        "execution": {
            "workspaceId": binding.workspace_ref,
            "executable": executable,
            "args": list(args),
            "cwdRelative": cwd_relative,
            "env": environment,
            "timeoutMs": timeout_ms,
            "stdoutLimitBytes": stdout_limit_bytes,
            "stderrLimitBytes": stderr_limit_bytes,
            "foreignReferences": [reference.to_dict() for reference in binding.runtime_references],
        },
        "waitMs": wait_ms,
        "stdoutTailBytes": stdout_tail_bytes,
        "stderrTailBytes": stderr_tail_bytes,
    }
    validate_json_value(request)
    return request
