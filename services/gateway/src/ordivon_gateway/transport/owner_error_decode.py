"""MCP Owner error decoder: typed, bounded evidence, never policy authority.

The SDK result may be structuredContent or text-only after a ToolError.
Only canonical envelopes for the exact authenticated Owner are promoted to
structured errors. Arbitrary prose and other-owner claims stay opaque.
"""

from __future__ import annotations

import json
from typing import Any


def _safe_bounded_error(error: dict[str, Any], max_bytes: int = 8192) -> bool:
    try:
        encoded = json.dumps(error, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except TypeError, ValueError, OverflowError:
        return False
    return len(encoded) <= max_bytes


def _validated_runtime_error(error: object) -> dict[str, Any] | None:
    if not isinstance(error, dict) or error.get("origin") != "runtime_core":
        return None
    if not _safe_bounded_error(error):
        return None
    if not all(
        isinstance(error.get(field), str) and bool(error[field])
        for field in ("code", "commitState", "message", "retryClass")
    ):
        return None
    if type(error.get("retryable")) is not bool:
        return None
    if error["commitState"] not in {"committed", "not_committed", "unknown"}:
        return None
    if "field" in error and not isinstance(error["field"], str):
        return None
    fields = ("code", "commitState", "message", "origin", "retryClass", "retryable", "field")
    return {field: error[field] for field in fields if field in error}


def _validated_host_error(error: object) -> dict[str, Any] | None:
    if not isinstance(error, dict) or not _safe_bounded_error(error):
        return None
    if (
        error.get("kind") != "ordivon.host-domain-error"
        or type(error.get("schemaVersion")) is not int
        or error["schemaVersion"] != 1
    ):
        return None
    code = error.get("code")
    if not isinstance(code, str) or not 0 < len(code) <= 96:
        return None
    retryable = error.get("retryable")
    if retryable is not None and type(retryable) is not bool:
        return None
    return dict(error)


def _qualified_error(error: object, owner_id: str) -> dict[str, Any] | None:
    if owner_id.startswith("runtime."):
        return _validated_runtime_error(error)
    if owner_id in {"host", "host.read"}:
        return _validated_host_error(error)
    # No other Owner has a currently qualified error envelope.
    return None


class _DuplicateJsonMember(ValueError):
    """A text carrier does not identify a unique JSON value."""


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonMember
        result[key] = value
    return result


def _same_evidence(left: dict[str, Any], right: dict[str, Any]) -> bool:
    # JSON equality is type-sensitive (Python bool == int is not).
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def extract_owner_tool_error(
    result: Any, *, owner_id: str, tool_name: str
) -> dict[str, Any] | None:
    """Require congruent Runtime evidence; preserve Host's structured-first ABI."""
    require_congruence = owner_id.startswith("runtime.")
    selected: dict[str, Any] | None = None
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        candidate = _qualified_error(structured.get("error"), owner_id)
        if candidate is not None:
            if not require_congruence:
                return candidate
            selected = candidate

    prefix = f"Error executing tool {tool_name}: "
    for item in getattr(result, "content", ()):
        raw = getattr(item, "text", None)
        if not isinstance(raw, str) or len(raw) > 8192:
            continue
        if owner_id.startswith("runtime."):
            candidate_text = raw[len(prefix) :] if raw.startswith(prefix) else raw
        elif owner_id in {"host", "host.read"}:
            if not raw.startswith(prefix):
                continue
            candidate_text = raw[len(prefix) :]
        else:
            continue
        try:
            value = (
                json.loads(candidate_text, object_pairs_hook=_unique_json_object)
                if require_congruence
                else json.loads(candidate_text)
            )
        except _DuplicateJsonMember:
            if require_congruence:
                return None
            continue
        except json.JSONDecodeError, RecursionError, ValueError:
            continue
        if owner_id.startswith("runtime."):
            if not isinstance(value, dict) or set(value) != {"error"}:
                continue
            error = value["error"]
        else:
            error = value
        candidate = _qualified_error(error, owner_id)
        if candidate is not None:
            if not require_congruence:
                return candidate
            if selected is not None and not _same_evidence(selected, candidate):
                return None
            selected = candidate
    return selected
