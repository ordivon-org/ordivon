"""Provider-neutral lifecycle port for proposal-only LSP integrations.

This module does not implement LSP transport. External integrations may use any mature
client library, but the Harness-facing port exposes observations and WorkspaceEdit
proposals only. Physical mutation remains outside this interface.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol, runtime_checkable

from anc_canonical import JsonValue, canonical_digest, validate_json_value

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_SUPPORTED_POSITION_ENCODINGS = frozenset({"utf-8", "utf-16", "utf-32"})


@dataclass(frozen=True, slots=True)
class LspProviderIdentity:
    provider_id: str
    implementation: str
    version: str

    def __post_init__(self) -> None:
        _trimmed(self.provider_id, "LSP provider id")
        _trimmed(self.implementation, "LSP provider implementation")
        _trimmed(self.version, "LSP provider version")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "providerId": self.provider_id,
            "implementation": self.implementation,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class LspProviderCapabilities:
    position_encoding: str
    rename: bool
    configuration_requests: bool
    publish_diagnostics: bool
    dynamic_registration: bool
    direct_workspace_mutation: bool = False

    def __post_init__(self) -> None:
        if self.position_encoding not in _SUPPORTED_POSITION_ENCODINGS:
            raise ValueError("unsupported LSP provider position encoding")
        for name in (
            "rename",
            "configuration_requests",
            "publish_diagnostics",
            "dynamic_registration",
            "direct_workspace_mutation",
        ):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"LSP provider capability {name} must be boolean")
        if self.direct_workspace_mutation:
            raise ValueError(
                "Harness LSP provider port forbids direct workspace mutation authority"
            )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "positionEncoding": self.position_encoding,
            "rename": self.rename,
            "configurationRequests": self.configuration_requests,
            "publishDiagnostics": self.publish_diagnostics,
            "dynamicRegistration": self.dynamic_registration,
            "directWorkspaceMutation": self.direct_workspace_mutation,
        }


@dataclass(frozen=True, slots=True)
class LspProviderReady:
    identity: LspProviderIdentity
    capabilities: LspProviderCapabilities

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-lsp-provider-ready",
            "identity": self.identity.to_dict(),
            "capabilities": self.capabilities.to_dict(),
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class LspRenameRequest:
    relative_path: str
    source_digest: str
    language_id: str
    document_version: int
    line: int
    unicode_column: int
    new_name: str

    def __post_init__(self) -> None:
        _trimmed(self.relative_path, "LSP rename relative path")
        if self.relative_path.startswith("/") or any(
            part in {"", ".", ".."} for part in self.relative_path.split("/")
        ):
            raise ValueError("LSP rename relative path must be a normalized relative path")
        if _DIGEST_RE.fullmatch(self.source_digest) is None:
            raise ValueError("LSP rename source digest must be sha256:<64 lowercase hex>")
        _trimmed(self.language_id, "LSP language id")
        if type(self.document_version) is not int or self.document_version < 0:
            raise ValueError("LSP document version must be a non-negative integer")
        if type(self.line) is not int or self.line < 1:
            raise ValueError("Harness LSP rename line must be one-based and positive")
        if type(self.unicode_column) is not int or self.unicode_column < 0:
            raise ValueError("Harness LSP rename Unicode column must be non-negative")
        _trimmed(self.new_name, "LSP rename new name")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-lsp-rename-request",
            "relativePath": self.relative_path,
            "sourceDigest": self.source_digest,
            "languageId": self.language_id,
            "documentVersion": self.document_version,
            "position": {
                "line": self.line,
                "unicodeColumn": self.unicode_column,
            },
            "newName": self.new_name,
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class LspWorkspaceEditProposal:
    request_digest: str
    provider: LspProviderIdentity
    position_encoding: str
    workspace_edit: dict[str, JsonValue]

    def __post_init__(self) -> None:
        if _DIGEST_RE.fullmatch(self.request_digest) is None:
            raise ValueError("LSP proposal request digest must be sha256:<64 lowercase hex>")
        if self.position_encoding not in _SUPPORTED_POSITION_ENCODINGS:
            raise ValueError("unsupported LSP proposal position encoding")
        validate_json_value(self.workspace_edit)
        if not self.workspace_edit:
            raise ValueError("LSP WorkspaceEdit proposal must be non-empty")

    @property
    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "schemaVersion": 1,
            "kind": "ordivon.harness-lsp-workspace-edit-proposal",
            "requestDigest": self.request_digest,
            "provider": self.provider.to_dict(),
            "positionEncoding": self.position_encoding,
            "workspaceEdit": self.workspace_edit,
        }
        validate_json_value(value)
        return value


@dataclass(frozen=True, slots=True)
class LspDiagnosticsObservation:
    uri: str
    document_version: int | None
    diagnostics: tuple[dict[str, JsonValue], ...]

    def __post_init__(self) -> None:
        _trimmed(self.uri, "LSP diagnostics URI")
        if self.document_version is not None and (
            type(self.document_version) is not int or self.document_version < 0
        ):
            raise ValueError("LSP diagnostics version must be null or non-negative integer")
        for diagnostic in self.diagnostics:
            validate_json_value(diagnostic)

    def to_dict(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            "uri": self.uri,
            "documentVersion": self.document_version,
            "diagnostics": list(self.diagnostics),
        }
        validate_json_value(value)
        return value


@runtime_checkable
class HarnessLspProviderPort(Protocol):
    """Lifecycle boundary for a proposal-only external LSP provider.

    The absence of any apply/write method is intentional. A WorkspaceEdit returned by
    ``rename`` still requires URI authority binding and compilation through
    ``workspace_edit_to_canonical_plan`` before Runtime may receive a physical Patch.
    """

    async def initialize(self) -> LspProviderReady: ...

    async def rename(self, request: LspRenameRequest) -> LspWorkspaceEditProposal: ...

    async def drain_diagnostics(self) -> tuple[LspDiagnosticsObservation, ...]: ...

    async def shutdown(self) -> None: ...


def unicode_column_to_lsp_character(
    line: str,
    unicode_column: int,
    position_encoding: str,
) -> int:
    """Convert a Harness Unicode-character column to an LSP encoding-unit offset."""

    if position_encoding not in _SUPPORTED_POSITION_ENCODINGS:
        raise ValueError("unsupported LSP position encoding")
    if type(unicode_column) is not int or unicode_column < 0 or unicode_column > len(line):
        raise ValueError("Unicode column is outside the source line")
    prefix = line[:unicode_column]
    if position_encoding == "utf-32":
        return len(prefix)
    if position_encoding == "utf-8":
        return len(prefix.encode("utf-8"))
    return len(prefix.encode("utf-16-le")) // 2


def _trimmed(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be non-empty and trimmed")


__all__ = [
    "HarnessLspProviderPort",
    "LspDiagnosticsObservation",
    "LspProviderCapabilities",
    "LspProviderIdentity",
    "LspProviderReady",
    "LspRenameRequest",
    "LspWorkspaceEditProposal",
    "unicode_column_to_lsp_character",
]
