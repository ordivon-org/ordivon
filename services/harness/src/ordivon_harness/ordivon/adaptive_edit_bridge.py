"""Internal Agent-facing Adaptive Edit bridge.

This module proves the first complete donor path:

``read_workspace`` -> exact source snapshot -> ``edit_workspace`` -> selected codec
-> canonical Runtime ``workspace.patch``.

It intentionally does not change the default Harness Tool surface. Consumers must
compose this bridge explicitly and provide a Tool Grant admitting the exact paths.
"""

from __future__ import annotations

from anc_canonical import JsonValue, canonical_digest, validate_json_value

from ..adaptive_edit import (
    AnchoredLineCodec,
    AnchoredLineEdit,
    EditCompileError,
    ExactReplacementCodec,
    ExactReplacementEdit,
    SourceSnapshot,
    anchored_line_plan,
    exact_replacement_plan,
    lower_plan_to_runtime_patch,
)
from ..agent_tool_observation import HarnessToolObservation
from ..protocol import HarnessRecoveryConsequence
from ..runtime_port import HarnessRuntimeClientError, HarnessRuntimeToolRejected
from .model import AgentToolCall, AgentToolDefinition
from .runtime_lowering import lower_runtime_tool
from .sqlite_runtime_bridge import SQLiteHarnessRuntimeBridge
from .tool_errors import ToolBridgeError, ToolBridgeErrorKind

_EDIT_SOURCE_MAX_BYTES = 4_194_304

READ_EDITABLE_WORKSPACE_DEFINITION = AgentToolDefinition(
    name="read_workspace",
    description=(
        "Read one complete UTF-8 workspace file for editing. The observation includes the "
        "exact Runtime source digest plus Harness-generated line anchors. Pass that digest "
        "back unchanged as sourceDigest when calling edit_workspace."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "relativePath": {"type": "string", "minLength": 1},
            "maxBytes": {
                "type": "integer",
                "minimum": 1,
                "maximum": _EDIT_SOURCE_MAX_BYTES,
                "default": 262_144,
            },
        },
        "required": ["relativePath"],
        "additionalProperties": False,
    },
)

EDIT_WORKSPACE_DEFINITION = AgentToolDefinition(
    name="edit_workspace",
    description=(
        "Apply one source-digest-fenced edit to a file previously read from this Workspace. "
        "Choose exact-replacement-v1 for unique oldText/newText replacement or "
        "anchored-line-v1 for full-line replacement using Harness-generated anchors. "
        "The Harness re-reads and verifies sourceDigest before any physical Patch admission."
    ),
    input_schema={
        "type": "object",
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "relativePath": {"type": "string", "minLength": 1},
                    "sourceDigest": {
                        "type": "string",
                        "pattern": "^sha256:[0-9a-f]{64}$",
                    },
                    "codec": {"const": ExactReplacementCodec.codec_id},
                    "oldText": {"type": "string", "minLength": 1},
                    "newText": {"type": "string"},
                    "maxDiffBytes": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": _EDIT_SOURCE_MAX_BYTES,
                        "default": 1_048_576,
                    },
                },
                "required": [
                    "relativePath",
                    "sourceDigest",
                    "codec",
                    "oldText",
                    "newText",
                ],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {
                    "relativePath": {"type": "string", "minLength": 1},
                    "sourceDigest": {
                        "type": "string",
                        "pattern": "^sha256:[0-9a-f]{64}$",
                    },
                    "codec": {"const": AnchoredLineCodec.codec_id},
                    "startAnchor": {
                        "type": "string",
                        "pattern": "^[1-9][0-9]*\\.[0-9a-f]{8}$",
                    },
                    "endAnchor": {
                        "type": "string",
                        "pattern": "^[1-9][0-9]*\\.[0-9a-f]{8}$",
                    },
                    "replacement": {"type": "string"},
                    "maxDiffBytes": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": _EDIT_SOURCE_MAX_BYTES,
                        "default": 1_048_576,
                    },
                },
                "required": [
                    "relativePath",
                    "sourceDigest",
                    "codec",
                    "startAnchor",
                    "endAnchor",
                    "replacement",
                ],
                "additionalProperties": False,
            },
        ],
    },
)

ADAPTIVE_EDIT_TOOL_SURFACE: dict[str, JsonValue] = {
    "schemaVersion": 1,
    "kind": "ordivon.adaptive-edit-tool-surface",
    "tools": [
        READ_EDITABLE_WORKSPACE_DEFINITION.to_dict(),
        EDIT_WORKSPACE_DEFINITION.to_dict(),
    ],
}
ADAPTIVE_EDIT_TOOL_SURFACE_DIGEST = canonical_digest(ADAPTIVE_EDIT_TOOL_SURFACE)
ADAPTIVE_EDIT_TOOL_GRANT_TEMPLATE: dict[str, JsonValue] = {
    "schemaVersion": 1,
    "kind": "ordivon.adaptive-edit-tool-grant-template",
    "tools": ["read_workspace", "edit_workspace"],
    "runtimeOperations": ["workspace.read", "workspace.patch", "workspace.patch.get"],
    "workspaceMutationAllowed": True,
}
ADAPTIVE_EDIT_TOOL_GRANT_TEMPLATE_DIGEST = canonical_digest(
    ADAPTIVE_EDIT_TOOL_GRANT_TEMPLATE
)


class AdaptiveEditRuntimeBridge(SQLiteHarnessRuntimeBridge):
    """Explicit mutable bridge for digest-fenced Agent edits.

    Runtime remains source-of-truth for current bytes and physical Patch outcome.
    The bridge owns only ACI translation and Harness durable Tool semantics.
    """

    recovery_consequence = HarnessRecoveryConsequence.WORKSPACE_CHANGE_POSSIBLE

    def __init__(self, *args, **kwargs) -> None:
        if "tool_definitions" not in kwargs:
            kwargs["tool_definitions"] = (
                READ_EDITABLE_WORKSPACE_DEFINITION,
                EDIT_WORKSPACE_DEFINITION,
            )
        if "tool_surface_digest" not in kwargs:
            kwargs["tool_surface_digest"] = ADAPTIVE_EDIT_TOOL_SURFACE_DIGEST
        super().__init__(*args, **kwargs)

    def _lower_runtime_tool_call(
        self,
        call: AgentToolCall,
        *,
        step_id: str,
    ) -> tuple[str, dict[str, JsonValue], str | None]:
        if call.name != "edit_workspace":
            return lower_runtime_tool(
                call,
                step_id=step_id,
                execution_binding=self.execution_binding,
                tool_grant=self._tool_grant,
                known_job_ids=frozenset(),
                known_artifacts=frozenset(),
            )
        return self._lower_edit_workspace(call, step_id=step_id)

    def _lower_edit_workspace(
        self,
        call: AgentToolCall,
        *,
        step_id: str,
    ) -> tuple[str, dict[str, JsonValue], str]:
        arguments = dict(call.arguments)
        relative_path = _required_string(arguments, "relativePath")
        source_digest = _required_digest(arguments, "sourceDigest")
        codec = _required_string(arguments, "codec")
        max_diff_bytes = _optional_positive_int(
            arguments,
            "maxDiffBytes",
            1_048_576,
            maximum=_EDIT_SOURCE_MAX_BYTES,
        )

        if self._tool_grant is not None:
            try:
                allowed = self._tool_grant.allows_path(call.name, relative_path)
            except ValueError as error:
                raise ToolBridgeError(
                    str(error), kind=ToolBridgeErrorKind.AUTHORITY_DENIED
                ) from error
            if not allowed:
                raise ToolBridgeError(
                    f"edit_workspace path is outside the Tool Grant: {relative_path}",
                    kind=ToolBridgeErrorKind.AUTHORITY_DENIED,
                )

        snapshot = self._read_source_snapshot(relative_path, source_digest)
        try:
            if codec == ExactReplacementCodec.codec_id:
                allowed_fields = {
                    "relativePath",
                    "sourceDigest",
                    "codec",
                    "oldText",
                    "newText",
                    "maxDiffBytes",
                }
                _only(arguments, allowed_fields)
                plan = exact_replacement_plan(
                    (snapshot,),
                    (
                        ExactReplacementEdit(
                            relative_path=relative_path,
                            old_text=_required_string(arguments, "oldText", trim=False),
                            new_text=_required_string(
                                arguments, "newText", trim=False, allow_empty=True
                            ),
                        ),
                    ),
                )
            elif codec == AnchoredLineCodec.codec_id:
                allowed_fields = {
                    "relativePath",
                    "sourceDigest",
                    "codec",
                    "startAnchor",
                    "endAnchor",
                    "replacement",
                    "maxDiffBytes",
                }
                _only(arguments, allowed_fields)
                plan = anchored_line_plan(
                    (snapshot,),
                    (
                        AnchoredLineEdit(
                            relative_path=relative_path,
                            start_anchor=_required_string(arguments, "startAnchor"),
                            end_anchor=_required_string(arguments, "endAnchor"),
                            replacement=_required_string(
                                arguments,
                                "replacement",
                                trim=False,
                                allow_empty=True,
                            ),
                        ),
                    ),
                )
            else:
                raise ToolBridgeError(
                    f"edit_workspace codec is not implemented: {codec}",
                    kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
                )
        except EditCompileError as error:
            raise ToolBridgeError(
                str(error), kind=ToolBridgeErrorKind.MODEL_CORRECTABLE
            ) from error

        return lower_plan_to_runtime_patch(
            plan,
            execution_binding=self.execution_binding,
            step_id=step_id,
            action_digest=call.digest,
            max_diff_bytes=max_diff_bytes,
        )

    def _read_source_snapshot(
        self,
        relative_path: str,
        source_digest: str,
    ) -> SourceSnapshot:
        try:
            payload = self.runtime.call_tool(
                "workspace.read",
                {
                    "schemaVersion": 1,
                    "workspaceId": self.execution_binding.workspace_ref,
                    "relativePath": relative_path,
                    "mode": "FULL",
                    "offset": 0,
                    "maxBytes": _EDIT_SOURCE_MAX_BYTES,
                },
            )
            validate_json_value(payload)
        except HarnessRuntimeToolRejected as error:
            raise ToolBridgeError(
                f"source snapshot read was rejected: {error}",
                kind=(
                    ToolBridgeErrorKind.MODEL_CORRECTABLE
                    if error.detail.commit_state in {"not_started", "not_committed"}
                    else ToolBridgeErrorKind.PROTOCOL_INVALID
                ),
            ) from error
        except HarnessRuntimeClientError as error:
            raise ToolBridgeError(
                f"source snapshot read failed before Patch admission: {error}",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            ) from error

        observed_path = payload.get("relativePath")
        observed_digest = payload.get("digest")
        content = payload.get("content")
        if (
            observed_path != relative_path
            or not isinstance(observed_digest, str)
            or not isinstance(content, str)
        ):
            raise ToolBridgeError(
                "Runtime workspace.read returned an invalid source snapshot",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            )
        if observed_digest != source_digest:
            raise ToolBridgeError(
                (
                    "edit_workspace sourceDigest is stale: "
                    f"expected {source_digest}, observed {observed_digest}"
                ),
                kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
            )
        return SourceSnapshot(relative_path, observed_digest, content)

    @classmethod
    def _observation_from_payload(
        cls,
        *,
        tool_call_id: str,
        tool_name: str,
        payload: dict[str, JsonValue],
        query: str | None,
        relative_path: str | None,
        reconciled: bool,
    ) -> HarnessToolObservation:
        observation = super()._observation_from_payload(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            payload=payload,
            query=query,
            relative_path=relative_path,
            reconciled=reconciled,
        )
        if tool_name != "read_workspace" or observation.status != "observed":
            return observation
        structured = dict(observation.structured_content)
        content = structured.get("content")
        digest = structured.get("digest")
        path = structured.get("relativePath")
        if not isinstance(content, str) or not isinstance(digest, str) or not isinstance(path, str):
            raise ToolBridgeError(
                "editable read omitted exact content/digest/path",
                kind=ToolBridgeErrorKind.PROTOCOL_INVALID,
            )
        snapshot = SourceSnapshot(path, digest, content)
        lines = content.split("\n")
        structured["editSnapshot"] = {
            "relativePath": path,
            "sourceDigest": digest,
            "lineAnchors": [
                {"line": index, "anchor": snapshot.line_anchor(index)}
                for index in range(1, len(lines) + 1)
            ],
            "codecs": [
                ExactReplacementCodec.codec_id,
                AnchoredLineCodec.codec_id,
            ],
        }
        return HarnessToolObservation(
            tool_call_id=observation.tool_call_id,
            tool_name=observation.tool_name,
            status=observation.status,
            structured_content=structured,
            runtime_job_ref=observation.runtime_job_ref,
            artifact_refs=observation.artifact_refs,
            reconciled=observation.reconciled,
        )


def _only(arguments: dict[str, JsonValue], allowed: set[str]) -> None:
    unknown = set(arguments) - allowed
    if unknown:
        raise ToolBridgeError(
            f"edit_workspace arguments contain unsupported fields: {sorted(unknown)}",
            kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
        )


def _required_string(
    arguments: dict[str, JsonValue],
    name: str,
    *,
    trim: bool = True,
    allow_empty: bool = False,
) -> str:
    value = arguments.get(name)
    if not isinstance(value, str):
        raise ToolBridgeError(
            f"edit_workspace {name} must be a string",
            kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
        )
    if not allow_empty and not value:
        raise ToolBridgeError(
            f"edit_workspace {name} must be non-empty",
            kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
        )
    if trim and value != value.strip():
        raise ToolBridgeError(
            f"edit_workspace {name} must be trimmed",
            kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
        )
    return value


def _required_digest(arguments: dict[str, JsonValue], name: str) -> str:
    value = _required_string(arguments, name)
    if (
        len(value) != 71
        or not value.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise ToolBridgeError(
            f"edit_workspace {name} must be sha256:<64 lowercase hex>",
            kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
        )
    return value


def _optional_positive_int(
    arguments: dict[str, JsonValue],
    name: str,
    default: int,
    *,
    maximum: int,
) -> int:
    value = arguments.get(name, default)
    if type(value) is not int or value < 1 or value > maximum:
        raise ToolBridgeError(
            f"edit_workspace {name} must be in 1..={maximum}",
            kind=ToolBridgeErrorKind.MODEL_CORRECTABLE,
        )
    return value


__all__ = [
    "ADAPTIVE_EDIT_TOOL_GRANT_TEMPLATE",
    "ADAPTIVE_EDIT_TOOL_GRANT_TEMPLATE_DIGEST",
    "ADAPTIVE_EDIT_TOOL_SURFACE",
    "ADAPTIVE_EDIT_TOOL_SURFACE_DIGEST",
    "AdaptiveEditRuntimeBridge",
    "EDIT_WORKSPACE_DEFINITION",
    "READ_EDITABLE_WORKSPACE_DEFINITION",
]
