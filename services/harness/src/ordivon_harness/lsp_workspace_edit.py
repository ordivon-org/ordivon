"""Pure LSP WorkspaceEdit -> Harness CanonicalEditPlan lowering.

The LSP provider is a proposal source, not a file-mutation authority. Callers bind
server-returned file URIs to already-admitted Harness workspace paths and exact source
snapshots before this module compiles TextEdits. Physical writes remain Runtime-owned.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from anc_canonical import JsonValue, validate_json_value

from .adaptive_edit import (
    CanonicalEditPlan,
    CanonicalFilePatch,
    CanonicalTextEdit,
    EditCompileError,
    SourceSnapshot,
)

_SUPPORTED_POSITION_ENCODINGS = frozenset({"utf-8", "utf-16", "utf-32"})
_LSP_WORKSPACE_EDIT_CODEC = "lsp-workspace-edit-v1"


@dataclass(frozen=True, slots=True)
class LspDocumentBinding:
    """Caller-owned authority/freshness binding for one LSP file URI.

    Multiple URIs may intentionally bind the same relative path when a language server
    returns path aliases. Alias edit sets must agree exactly before they are deduplicated.
    """

    uri: str
    snapshot: SourceSnapshot
    document_version: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.uri, str) or not self.uri:
            raise ValueError("LSP document binding URI must be non-empty")
        if self.document_version is not None and type(self.document_version) is not int:
            raise TypeError("LSP document version must be an integer or None")

    @property
    def relative_path(self) -> str:
        return self.snapshot.relative_path


@dataclass(frozen=True, slots=True)
class _NormalizedTextEdit:
    start_line_zero: int
    start_character: int
    end_line_zero: int
    end_character: int
    new_text: str

    @property
    def identity(self) -> tuple[int, int, int, int, str]:
        return (
            self.start_line_zero,
            self.start_character,
            self.end_line_zero,
            self.end_character,
            self.new_text,
        )


def workspace_edit_to_canonical_plan(
    workspace_edit: Mapping[str, JsonValue],
    *,
    bindings: Iterable[LspDocumentBinding],
    position_encoding: str,
) -> CanonicalEditPlan:
    """Compile one LSP WorkspaceEdit without granting it physical write authority.

    Supported R7 slice:
    - ``WorkspaceEdit.changes`` containing TextEdits;
    - ``WorkspaceEdit.documentChanges`` containing TextDocumentEdits only.

    Resource operations remain rejected until separately authorized. Numeric
    ``TextDocumentEdit.textDocument.version`` must equal the caller-supplied binding.
    ``null`` versions are accepted only as "version not asserted by server"; source
    currentness is still fenced later by the exact snapshot digest at Runtime Patch.
    """

    if position_encoding not in _SUPPORTED_POSITION_ENCODINGS:
        raise EditCompileError(
            f"unsupported LSP position encoding: {position_encoding}; "
            f"expected one of {sorted(_SUPPORTED_POSITION_ENCODINGS)}"
        )
    value = dict(workspace_edit)
    validate_json_value(value)
    unknown = set(value) - {"changes", "documentChanges", "changeAnnotations"}
    if unknown:
        raise EditCompileError(f"WorkspaceEdit contains unsupported fields: {sorted(unknown)}")

    by_uri: dict[str, LspDocumentBinding] = {}
    for binding in bindings:
        if binding.uri in by_uri:
            raise ValueError(f"duplicate LSP URI binding: {binding.uri}")
        by_uri[binding.uri] = binding
    if not by_uri:
        raise ValueError("WorkspaceEdit compilation requires at least one URI binding")

    proposed: dict[str, list[tuple[str, list[_NormalizedTextEdit]]]] = {}
    changes = value.get("changes")
    document_changes = value.get("documentChanges")
    if changes is not None and document_changes is not None:
        raise EditCompileError(
            "R7 WorkspaceEdit adapter rejects simultaneous changes and documentChanges"
        )
    if changes is not None:
        if not isinstance(changes, dict):
            raise EditCompileError("WorkspaceEdit.changes must be an object")
        for uri, edits in changes.items():
            if not isinstance(uri, str):
                raise EditCompileError("WorkspaceEdit.changes URI keys must be strings")
            binding = _required_binding(by_uri, uri)
            normalized = _normalize_text_edits(edits, source=f"changes[{uri!r}]")
            proposed.setdefault(binding.relative_path, []).append((uri, normalized))
    elif document_changes is not None:
        if not isinstance(document_changes, list):
            raise EditCompileError("WorkspaceEdit.documentChanges must be an array")
        for index, change in enumerate(document_changes):
            if not isinstance(change, dict):
                raise EditCompileError(f"documentChanges[{index}] must be an object")
            if "textDocument" not in change:
                raise EditCompileError(
                    "WorkspaceEdit resource operations are not admitted in R7 prototype"
                )
            unknown_change = set(change) - {"textDocument", "edits"}
            if unknown_change:
                raise EditCompileError(
                    f"TextDocumentEdit contains unsupported fields: {sorted(unknown_change)}"
                )
            text_document = change.get("textDocument")
            if not isinstance(text_document, dict):
                raise EditCompileError(f"documentChanges[{index}].textDocument must be an object")
            if set(text_document) - {"uri", "version"}:
                raise EditCompileError("TextDocumentEdit.textDocument has unsupported fields")
            uri = text_document.get("uri")
            if not isinstance(uri, str) or not uri:
                raise EditCompileError("TextDocumentEdit.textDocument.uri must be non-empty")
            binding = _required_binding(by_uri, uri)
            version = text_document.get("version")
            if version is not None:
                if type(version) is not int:
                    raise EditCompileError("TextDocumentEdit version must be integer or null")
                if binding.document_version is None:
                    raise EditCompileError(
                        "versioned TextDocumentEdit has no caller-owned document version binding"
                    )
                if version != binding.document_version:
                    raise EditCompileError(
                        "TextDocumentEdit version differs from the exact caller binding"
                    )
            normalized = _normalize_text_edits(
                change.get("edits"), source=f"documentChanges[{index}].edits"
            )
            proposed.setdefault(binding.relative_path, []).append((uri, normalized))
    else:
        raise EditCompileError("WorkspaceEdit contains neither changes nor documentChanges")

    if not proposed:
        raise EditCompileError("WorkspaceEdit contains no text edits")

    patches: list[CanonicalFilePatch] = []
    for relative_path in sorted(proposed):
        alias_sets = proposed[relative_path]
        snapshot = by_uri[alias_sets[0][0]].snapshot
        if any(by_uri[uri].snapshot != snapshot for uri, _ in alias_sets[1:]):
            raise EditCompileError(
                f"LSP URI aliases for {relative_path} do not bind the same exact source snapshot"
            )
        normalized = _deduplicate_alias_sets(relative_path, alias_sets)
        canonical = tuple(
            _compile_text_edit(snapshot, edit, position_encoding=position_encoding)
            for edit in normalized
        )
        _reject_overlaps(canonical, relative_path=relative_path)
        patches.append(
            CanonicalFilePatch(
                relative_path=relative_path,
                expected_digest=snapshot.digest,
                edits=canonical,
            )
        )

    return CanonicalEditPlan(codec=_LSP_WORKSPACE_EDIT_CODEC, files=tuple(patches))


def _required_binding(by_uri: Mapping[str, LspDocumentBinding], uri: str) -> LspDocumentBinding:
    binding = by_uri.get(uri)
    if binding is None:
        raise EditCompileError(f"LSP WorkspaceEdit URI is not bound to Harness authority: {uri}")
    return binding


def _normalize_text_edits(value: JsonValue | None, *, source: str) -> list[_NormalizedTextEdit]:
    if not isinstance(value, list) or not value:
        raise EditCompileError(f"{source} must be a non-empty TextEdit array")
    result: list[_NormalizedTextEdit] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise EditCompileError(f"{source}[{index}] must be an object")
        unknown = set(item) - {"range", "newText", "annotationId"}
        if unknown:
            raise EditCompileError(
                f"{source}[{index}] contains unsupported TextEdit fields: {sorted(unknown)}"
            )
        rng = item.get("range")
        new_text = item.get("newText")
        if not isinstance(rng, dict) or not isinstance(new_text, str):
            raise EditCompileError(f"{source}[{index}] requires range and string newText")
        start = _position_object(rng.get("start"), source=f"{source}[{index}].range.start")
        end = _position_object(rng.get("end"), source=f"{source}[{index}].range.end")
        if end < start:
            raise EditCompileError(f"{source}[{index}] range end precedes start")
        result.append(
            _NormalizedTextEdit(
                start_line_zero=start[0],
                start_character=start[1],
                end_line_zero=end[0],
                end_character=end[1],
                new_text=new_text,
            )
        )
    return result


def _position_object(value: JsonValue | None, *, source: str) -> tuple[int, int]:
    if not isinstance(value, dict) or set(value) != {"line", "character"}:
        raise EditCompileError(f"{source} must contain only line and character")
    line = value.get("line")
    character = value.get("character")
    if type(line) is not int or type(character) is not int or line < 0 or character < 0:
        raise EditCompileError(f"{source} line/character must be non-negative integers")
    return line, character


def _deduplicate_alias_sets(
    relative_path: str,
    alias_sets: list[tuple[str, list[_NormalizedTextEdit]]],
) -> list[_NormalizedTextEdit]:
    first_uri, first = alias_sets[0]
    first_identities = sorted(edit.identity for edit in first)
    for uri, edits in alias_sets[1:]:
        identities = sorted(edit.identity for edit in edits)
        if identities != first_identities:
            raise EditCompileError(
                f"LSP URI aliases for {relative_path} propose conflicting edit sets: "
                f"{first_uri} vs {uri}"
            )
    # Preserve the first server-provided order; overlap validation below makes ordering irrelevant.
    unique: list[_NormalizedTextEdit] = []
    seen: set[tuple[int, int, int, int, str]] = set()
    for edit in first:
        if edit.identity not in seen:
            unique.append(edit)
            seen.add(edit.identity)
    if not unique:
        raise EditCompileError(f"LSP WorkspaceEdit has no unique text edits for {relative_path}")
    return unique


def _compile_text_edit(
    snapshot: SourceSnapshot,
    edit: _NormalizedTextEdit,
    *,
    position_encoding: str,
) -> CanonicalTextEdit:
    lines = snapshot.content.split("\n")
    if edit.start_line_zero >= len(lines) or edit.end_line_zero >= len(lines):
        raise EditCompileError("LSP TextEdit line is outside the exact source snapshot")
    start_column = _lsp_units_to_unicode_column(
        lines[edit.start_line_zero], edit.start_character, position_encoding
    )
    end_column = _lsp_units_to_unicode_column(
        lines[edit.end_line_zero], edit.end_character, position_encoding
    )
    expected = _slice_range(
        lines,
        edit.start_line_zero,
        start_column,
        edit.end_line_zero,
        end_column,
    )
    if expected == edit.new_text:
        raise EditCompileError("LSP TextEdit would be a no-op")
    return CanonicalTextEdit(
        start_line=edit.start_line_zero + 1,
        start_column=start_column,
        end_line=edit.end_line_zero + 1,
        end_column=end_column,
        expected_text=expected,
        replacement=edit.new_text,
    )


def _lsp_units_to_unicode_column(line: str, units: int, encoding: str) -> int:
    if units < 0:
        raise EditCompileError("LSP character offset must be non-negative")
    if encoding == "utf-32":
        if units > len(line):
            raise EditCompileError("LSP UTF-32 character offset exceeds line length")
        return units
    codec = "utf-8" if encoding == "utf-8" else "utf-16-le"
    unit_size = 1 if encoding == "utf-8" else 2
    consumed = 0
    for column, character in enumerate(line):
        if consumed == units:
            return column
        consumed += len(character.encode(codec)) // unit_size
        if consumed > units:
            raise EditCompileError(f"LSP {encoding} character offset splits an encoded character")
    if consumed == units:
        return len(line)
    raise EditCompileError(f"LSP {encoding} character offset exceeds line length")


def _slice_range(
    lines: list[str],
    start_line: int,
    start_column: int,
    end_line: int,
    end_column: int,
) -> str:
    if start_line == end_line:
        return lines[start_line][start_column:end_column]
    pieces = [lines[start_line][start_column:]]
    pieces.extend(lines[start_line + 1 : end_line])
    pieces.append(lines[end_line][:end_column])
    return "\n".join(pieces)


def _reject_overlaps(edits: tuple[CanonicalTextEdit, ...], *, relative_path: str) -> None:
    ordered = sorted(
        edits,
        key=lambda edit: (
            edit.start_line,
            edit.start_column,
            edit.end_line,
            edit.end_column,
        ),
    )
    previous_end: tuple[int, int] | None = None
    for edit in ordered:
        start = (edit.start_line, edit.start_column)
        end = (edit.end_line, edit.end_column)
        if previous_end is not None and start < previous_end:
            raise EditCompileError(f"LSP TextEdits overlap in {relative_path}")
        previous_end = end


__all__ = [
    "LspDocumentBinding",
    "workspace_edit_to_canonical_plan",
]
