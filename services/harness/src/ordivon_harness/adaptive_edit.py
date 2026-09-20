"""Adaptive Agent-facing edit codecs lowered to Runtime Workspace Patch.

This module is intentionally mechanical. It does not choose what source should mean,
which change is correct, or whether a changed repository satisfies a caller objective.
It translates already-authored edit intent against an exact source snapshot into the
single durable Runtime ``workspace.patch`` representation.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Protocol

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from .execution_binding import HarnessExecutionBinding
from .runtime_port import (
    HarnessRuntimeClient,
    HarnessRuntimeClientError,
    HarnessRuntimeToolRejected,
)

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_ANCHOR_RE = re.compile(r"^(?P<line>[1-9][0-9]*)\.(?P<tag>[0-9a-f]{8})$")


class EditCompileError(ValueError):
    """Model-correctable mechanical edit encoding failure before physical commit."""


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    relative_path: str
    digest: str
    content: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.relative_path, str)
            or not self.relative_path
            or self.relative_path != self.relative_path.strip()
        ):
            raise ValueError("source snapshot path must be non-empty and trimmed")
        if _DIGEST_RE.fullmatch(self.digest) is None:
            raise ValueError("source snapshot digest must be sha256:<64 lowercase hex>")
        if not isinstance(self.content, str):
            raise TypeError("source snapshot content must be UTF-8 text")

    @property
    def tag(self) -> str:
        return self.digest[7:15]

    def line_anchor(self, line_number: int) -> str:
        lines = self.content.split("\n")
        if line_number < 1 or line_number > len(lines):
            raise ValueError("line number is outside the source snapshot")
        line = lines[line_number - 1]
        payload = f"{self.digest}\0{line_number}\0{line}".encode()
        tag = hashlib.sha256(payload).hexdigest()[:8]
        return f"{line_number}.{tag}"

    def anchored_view(self) -> str:
        return "\n".join(
            f"{self.line_anchor(index)}\t{line}"
            for index, line in enumerate(self.content.split("\n"), start=1)
        )


@dataclass(frozen=True, slots=True)
class ExactReplacementEdit:
    relative_path: str
    old_text: str
    new_text: str


@dataclass(frozen=True, slots=True)
class AnchoredLineEdit:
    relative_path: str
    start_anchor: str
    end_anchor: str
    replacement: str


@dataclass(frozen=True, slots=True)
class CanonicalTextEdit:
    start_line: int
    start_column: int
    end_line: int
    end_column: int
    expected_text: str
    replacement: str

    def to_runtime_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "range": {
                "start": {"line": self.start_line, "column": self.start_column},
                "end": {"line": self.end_line, "column": self.end_column},
            },
            "expectedText": self.expected_text,
            "replacement": self.replacement,
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class CanonicalFilePatch:
    relative_path: str
    expected_digest: str
    edits: tuple[CanonicalTextEdit, ...]

    def to_runtime_dict(self) -> dict[str, JsonValue]:
        if not self.edits:
            raise ValueError("canonical file patch requires at least one edit")
        value: dict[str, JsonValue] = {
            "relativePath": self.relative_path,
            "expectedDigest": self.expected_digest,
            "edits": [edit.to_runtime_dict() for edit in self.edits],
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class CanonicalEditPlan:
    codec: str
    files: tuple[CanonicalFilePatch, ...]

    def __post_init__(self) -> None:
        if not self.files:
            raise ValueError("canonical edit plan requires at least one file")
        paths = [file.relative_path for file in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("canonical edit plan cannot target one path twice")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-canonical-edit-plan",
            "codec": self.codec,
            "files": [file.to_runtime_dict() for file in self.files],
        }
        validate_json_value(value)
        return value

    def runtime_files(self) -> list[JsonValue]:
        return [file.to_runtime_dict() for file in self.files]


class EditCodec(Protocol):
    codec_id: str


class ExactReplacementCodec:
    codec_id = "exact-replacement-v1"

    def compile(
        self,
        snapshot: SourceSnapshot,
        edit: ExactReplacementEdit,
    ) -> CanonicalFilePatch:
        if edit.relative_path != snapshot.relative_path:
            raise EditCompileError("edit path differs from source snapshot path")
        if not edit.old_text:
            raise EditCompileError("exact replacement oldText must be non-empty")
        if edit.old_text == edit.new_text:
            raise EditCompileError("exact replacement would be a no-op")

        first = snapshot.content.find(edit.old_text)
        if first < 0:
            raise EditCompileError("exact replacement oldText was not found in source snapshot")
        second = snapshot.content.find(edit.old_text, first + 1)
        if second >= 0:
            raise EditCompileError("exact replacement oldText is ambiguous in source snapshot")

        start_line, start_column = _position(snapshot.content, first)
        end_line, end_column = _position(snapshot.content, first + len(edit.old_text))
        return CanonicalFilePatch(
            relative_path=snapshot.relative_path,
            expected_digest=snapshot.digest,
            edits=(
                CanonicalTextEdit(
                    start_line=start_line,
                    start_column=start_column,
                    end_line=end_line,
                    end_column=end_column,
                    expected_text=edit.old_text,
                    replacement=edit.new_text,
                ),
            ),
        )


class AnchoredLineCodec:
    """Hashline-like full-line range codec bound to one exact source snapshot.

    The model names two content-derived line anchors. Infrastructure checks both
    anchors and derives Runtime line/column coordinates and expectedText. This
    prototype deliberately avoids a bespoke patch language; a future wire syntax
    can be added without changing the canonical edit plan.
    """

    codec_id = "anchored-line-v1"

    def compile(
        self,
        snapshot: SourceSnapshot,
        edit: AnchoredLineEdit,
    ) -> CanonicalFilePatch:
        if edit.relative_path != snapshot.relative_path:
            raise EditCompileError("edit path differs from source snapshot path")
        start = _parse_anchor(snapshot, edit.start_anchor)
        end = _parse_anchor(snapshot, edit.end_anchor)
        if end < start:
            raise EditCompileError("anchored edit end precedes start")
        lines = snapshot.content.split("\n")
        expected = "\n".join(lines[start - 1 : end])
        if expected == edit.replacement:
            raise EditCompileError("anchored edit would be a no-op")
        return CanonicalFilePatch(
            relative_path=snapshot.relative_path,
            expected_digest=snapshot.digest,
            edits=(
                CanonicalTextEdit(
                    start_line=start,
                    start_column=0,
                    end_line=end,
                    end_column=len(lines[end - 1]),
                    expected_text=expected,
                    replacement=edit.replacement,
                ),
            ),
        )


def exact_replacement_plan(
    snapshots: tuple[SourceSnapshot, ...],
    edits: tuple[ExactReplacementEdit, ...],
) -> CanonicalEditPlan:
    return _compile_one_edit_per_file(ExactReplacementCodec(), snapshots, edits)


def anchored_line_plan(
    snapshots: tuple[SourceSnapshot, ...],
    edits: tuple[AnchoredLineEdit, ...],
) -> CanonicalEditPlan:
    return _compile_one_edit_per_file(AnchoredLineCodec(), snapshots, edits)


def lower_plan_to_runtime_patch(
    plan: CanonicalEditPlan,
    *,
    execution_binding: HarnessExecutionBinding,
    step_id: str,
    action_digest: str,
    max_diff_bytes: int = 1_048_576,
) -> tuple[str, dict[str, JsonValue], str]:
    """Lower a canonical plan to the existing durable Runtime Patch operation."""

    if _DIGEST_RE.fullmatch(action_digest) is None:
        raise ValueError("edit action digest must be sha256:<64 lowercase hex>")
    if max_diff_bytes <= 0:
        raise ValueError("maxDiffBytes must be positive")
    client_request_id = execution_binding.patch_request_id(step_id, action_digest)
    request: dict[str, JsonValue] = {
        "schemaVersion": 1,
        "clientRequestId": client_request_id,
        "workspaceId": execution_binding.workspace_ref,
        "files": plan.runtime_files(),
        "maxDiffBytes": max_diff_bytes,
    }
    validate_json_value(request)
    return "workspace.patch", request, client_request_id


@dataclass(frozen=True, slots=True)
class PatchDispatchResult:
    """One physical Patch dispatch outcome after bounded Runtime reconciliation.

    This is deliberately not semantic completion. ``committed`` proves only that
    Runtime established the exact requested file state. ``not_committed`` proves
    the queried durable Patch operation remains physically at its before-state.
    ``unknown`` forbids codec fallback or redispatch.
    """

    status: str
    client_request_id: str
    payload: dict[str, JsonValue]
    reconciled: bool
    safe_to_correct: bool

    def __post_init__(self) -> None:
        if self.status not in {"committed", "not_committed", "rejected", "unknown"}:
            raise ValueError("unsupported Patch dispatch status")
        if self.status == "unknown" and self.safe_to_correct:
            raise ValueError("unknown Patch outcome cannot be safe to correct")
        validate_json_value(self.payload)


def dispatch_runtime_patch_once(
    runtime: HarnessRuntimeClient,
    request: dict[str, JsonValue],
) -> PatchDispatchResult:
    """Dispatch exactly one ``workspace.patch`` and reconcile response loss by status.

    This helper never retries ``workspace.patch``. After an ambiguous transport/result
    failure it asks only ``workspace.patch.get`` for the same ``clientRequestId``.
    Higher layers may choose a new codec only when the returned standing proves no
    physical commit; they must never treat ``unknown`` as retry authority.
    """

    client_request_id = request.get("clientRequestId")
    if not isinstance(client_request_id, str) or not client_request_id:
        raise ValueError("Runtime Patch request omitted clientRequestId")
    try:
        payload = runtime.call_tool("workspace.patch", request)
        validate_json_value(payload)
        return PatchDispatchResult(
            status="committed",
            client_request_id=client_request_id,
            payload=dict(payload),
            reconciled=False,
            safe_to_correct=False,
        )
    except HarnessRuntimeToolRejected as error:
        if error.detail.commit_state in {"not_started", "not_committed"}:
            return PatchDispatchResult(
                status="rejected",
                client_request_id=client_request_id,
                payload={
                    "type": type(error).__name__,
                    "code": error.detail.code,
                    "message": error.detail.message[:2_048],
                    "commitState": error.detail.commit_state,
                    "field": error.detail.field,
                },
                reconciled=False,
                safe_to_correct=True,
            )
    except HarnessRuntimeClientError:
        pass

    return reconcile_runtime_patch(runtime, client_request_id)


def reconcile_runtime_patch(
    runtime: HarnessRuntimeClient,
    client_request_id: str,
) -> PatchDispatchResult:
    """Inspect one exact durable Runtime Patch identity without redispatching it."""

    if not isinstance(client_request_id, str) or not client_request_id:
        raise ValueError("Runtime Patch reconciliation requires clientRequestId")
    try:
        payload = runtime.call_tool(
            "workspace.patch.get",
            {"schemaVersion": 1, "clientRequestId": client_request_id},
        )
        validate_json_value(payload)
    except HarnessRuntimeToolRejected as error:
        if error.detail.commit_state in {"not_started", "not_committed"}:
            return PatchDispatchResult(
                status="not_committed",
                client_request_id=client_request_id,
                payload={
                    "type": type(error).__name__,
                    "code": error.detail.code,
                    "message": error.detail.message[:2_048],
                    "commitState": error.detail.commit_state,
                    "field": error.detail.field,
                },
                reconciled=True,
                safe_to_correct=True,
            )
        return PatchDispatchResult(
            status="unknown",
            client_request_id=client_request_id,
            payload={
                "type": type(error).__name__,
                "code": error.detail.code,
                "message": error.detail.message[:2_048],
                "commitState": error.detail.commit_state,
                "field": error.detail.field,
            },
            reconciled=True,
            safe_to_correct=False,
        )
    except HarnessRuntimeClientError as error:
        return PatchDispatchResult(
            status="unknown",
            client_request_id=client_request_id,
            payload={
                "type": type(error).__name__,
                "message": str(error)[:2_048],
            },
            reconciled=True,
            safe_to_correct=False,
        )

    if payload.get("clientRequestId") != client_request_id:
        raise ValueError("Runtime Patch status returned another clientRequestId")
    state = payload.get("state")
    if state == "committed":
        if not isinstance(payload.get("patch"), dict):
            raise ValueError("committed Runtime Patch status omitted patch result")
        return PatchDispatchResult(
            status="committed",
            client_request_id=client_request_id,
            payload=dict(payload),
            reconciled=True,
            safe_to_correct=False,
        )
    if state == "prepared":
        return PatchDispatchResult(
            status="not_committed",
            client_request_id=client_request_id,
            payload=dict(payload),
            reconciled=True,
            safe_to_correct=True,
        )
    if state == "unknown":
        return PatchDispatchResult(
            status="unknown",
            client_request_id=client_request_id,
            payload=dict(payload),
            reconciled=True,
            safe_to_correct=False,
        )
    raise ValueError("Runtime Patch status returned unsupported state")


def choose_edit_codec(
    *,
    measured_winner: str | None,
    anchored_reliable: bool,
    patch_reliable: bool = False,
) -> str:
    """Small policy-free selector hook for benchmark-owned model profiles.

    ``patch_reliable`` is retained in the selector surface even though a conventional
    patch codec is not yet implemented. Selection never dispatches physical effects.
    """

    supported = {ExactReplacementCodec.codec_id, AnchoredLineCodec.codec_id}
    if measured_winner is not None:
        if measured_winner not in supported:
            raise ValueError("measured edit winner is not implemented")
        return measured_winner
    if anchored_reliable:
        return AnchoredLineCodec.codec_id
    if patch_reliable:
        raise ValueError("conventional patch codec is not implemented in R2 prototype")
    return ExactReplacementCodec.codec_id


def _compile_one_edit_per_file(codec, snapshots, edits) -> CanonicalEditPlan:
    snapshot_by_path = {snapshot.relative_path: snapshot for snapshot in snapshots}
    if len(snapshot_by_path) != len(snapshots):
        raise ValueError("source snapshots must have unique paths")
    patches: list[CanonicalFilePatch] = []
    seen: set[str] = set()
    for edit in edits:
        if edit.relative_path in seen:
            raise EditCompileError("R2 prototype accepts at most one edit per file")
        snapshot = snapshot_by_path.get(edit.relative_path)
        if snapshot is None:
            raise EditCompileError("edit references a path without an exact source snapshot")
        patches.append(codec.compile(snapshot, edit))
        seen.add(edit.relative_path)
    if not patches:
        raise EditCompileError("edit plan requires at least one edit")
    return CanonicalEditPlan(codec=codec.codec_id, files=tuple(patches))


def _parse_anchor(snapshot: SourceSnapshot, value: str) -> int:
    if not isinstance(value, str):
        raise EditCompileError("line anchor must be a string")
    match = _ANCHOR_RE.fullmatch(value)
    if match is None:
        raise EditCompileError("line anchor must use <line>.<8-hex-tag>")
    line = int(match.group("line"))
    try:
        expected = snapshot.line_anchor(line)
    except ValueError as error:
        raise EditCompileError(str(error)) from error
    if value != expected:
        raise EditCompileError("line anchor does not match the exact source snapshot")
    return line


def _position(content: str, character_offset: int) -> tuple[int, int]:
    if character_offset < 0 or character_offset > len(content):
        raise ValueError("character offset is outside source content")
    prefix = content[:character_offset]
    line = prefix.count("\n") + 1
    column = len(prefix.rsplit("\n", 1)[-1])
    return line, column


__all__ = [
    "AnchoredLineCodec",
    "AnchoredLineEdit",
    "CanonicalEditPlan",
    "CanonicalFilePatch",
    "CanonicalTextEdit",
    "EditCompileError",
    "ExactReplacementCodec",
    "ExactReplacementEdit",
    "PatchDispatchResult",
    "SourceSnapshot",
    "anchored_line_plan",
    "choose_edit_codec",
    "dispatch_runtime_patch_once",
    "exact_replacement_plan",
    "lower_plan_to_runtime_patch",
    "reconcile_runtime_patch",
]
