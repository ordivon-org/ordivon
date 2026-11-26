"""Task-local JSON evidence admission and canonical identity.

Strict wire decoding and in-memory digest admission are separate operations.
The historical canonical encoding is preserved for valid JSON values.
"""

from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class CircuitContractError(ValueError):
    pass


def _require_json_representation(value: Any) -> None:
    """Refuse Python coercions before the native JSON encoder binds identity.

    Shared acyclic containers are valid JSON projections. The encoder retains
    responsibility for cycle, scalar Unicode and finite numeric validation.
    """
    pending = [value]
    seen: set[int] = set()
    while pending:
        item = pending.pop()
        if isinstance(item, (dict, list)):
            identity = id(item)
            if identity in seen:
                continue
            seen.add(identity)
            if isinstance(item, dict):
                if not all(isinstance(key, str) for key in item):
                    raise CircuitContractError("JSON evidence object keys must be strings")
                pending.extend(item.values())
            else:
                pending.extend(item)
        elif not isinstance(item, (str, int, float, type(None))):
            raise CircuitContractError("non-JSON representation in LEGO evidence digest")


def _canonical_bytes(value: Any) -> bytes:
    _require_json_representation(value)
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except UnicodeError as exc:
        raise CircuitContractError("non-Unicode scalar in LEGO evidence digest") from exc
    except (TypeError, RecursionError) as exc:
        raise CircuitContractError("invalid JSON representation in LEGO evidence digest") from exc
    except ValueError as exc:
        raise CircuitContractError("non-JSON numeric value in LEGO evidence digest") from exc


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _single_valued_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """RFC 8259 object binding: reject ambiguous repeated keys at any depth."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CircuitContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> None:
    raise CircuitContractError(f"invalid JSON constant: {value}")


def _finite_json_float(value: str) -> float:
    """Reject overflow to Infinity at the source boundary, before any proof use."""
    parsed = float(value)
    if not math.isfinite(parsed):
        raise CircuitContractError(f"non-finite JSON number: {value}")
    # R2.1 representation/equivalence boundary: a finite binary float can
    # silently collapse DISTINCT decimal evidence values before their
    # semantic digest is computed (e.g. 1e-324 vs 0.0, or 2**53+1 vs 2**53).
    # Preserve the existing float API, but admit only numeric lexemes whose
    # exact decimal value equals its emitted canonical float representation.
    # This check is NOT a proof of the consumer's implementation refinement.
    try:
        if Decimal(value) != Decimal(str(parsed)):
            raise CircuitContractError(f"lossy JSON numeric evidence: {value}")
    except InvalidOperation as exc:
        raise CircuitContractError("invalid JSON numeric evidence") from exc
    return parsed


# Limit is explicit even if the host disables CPython's default 4300-digit
# conversion fence. This is a bounded JSON evidence admission contract.
MAX_JSON_INTEGER_DIGITS = 4300


def _bounded_json_integer(value: str) -> int:
    if len(value) - int(value.startswith("-")) > MAX_JSON_INTEGER_DIGITS:
        raise CircuitContractError("JSON integer exceeds evidence digit bound")
    try:
        return int(value)
    except ValueError as exc:
        raise CircuitContractError("JSON integer cannot be represented") from exc


def _require_unicode_scalars(
    value: Any, *, git_byte_path_fields: frozenset[str] = frozenset()
) -> None:
    # Git pathname bytes may be decoded with surrogateescape; JSON evidence
    # elsewhere MUST remain Unicode scalar text. Exemption is restricted to
    # exact path-valued fields at the caller's explicit CLI boundary.
    pending: list[tuple[Any, str | None]] = [(value, None)]
    while pending:
        item, field = pending.pop()
        if isinstance(item, str):
            try:
                item.encode(
                    "utf-8",
                    errors="surrogateescape" if field in git_byte_path_fields else "strict",
                )
            except UnicodeError as exc:
                raise CircuitContractError("invalid Unicode scalar in JSON evidence") from exc
        elif isinstance(item, dict):
            # Object KEYS are never byte paths and cannot inherit exemption.
            pending.extend((key, None) for key in item)
            pending.extend((child, key) for key, child in item.items())
        elif isinstance(item, list):
            pending.extend((child, field) for child in item)


def _load_json_value(
    path: Path,
    *,
    source_bytes: bytes | None = None,
    git_byte_path_fields: frozenset[str] = frozenset(),
) -> Any:
    """One source/evidence admission boundary shared by Composition CLIs.

    The opt-in byte-path exemption is only for Repo's Git source members and
    natural Owner sourcePaths; it never changes other JSON evidence contracts.
    """
    try:
        raw = source_bytes if source_bytes is not None else path.read_bytes()
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_single_valued_json_object,
            parse_constant=_reject_non_json_constant,
            parse_float=_finite_json_float,
            parse_int=_bounded_json_integer,
        )
        _require_unicode_scalars(value, git_byte_path_fields=git_byte_path_fields)
    except CircuitContractError:
        raise
    except (UnicodeError, RecursionError) as exc:
        raise CircuitContractError("invalid UTF-8 or nesting in JSON evidence") from exc
    return value


def _load_json(
    path: Path,
    *,
    source_bytes: bytes | None = None,
    git_byte_path_fields: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    value = _load_json_value(
        path, source_bytes=source_bytes, git_byte_path_fields=git_byte_path_fields
    )
    if not isinstance(value, dict):
        raise CircuitContractError(f"{path}: root must be an object")
    return value
