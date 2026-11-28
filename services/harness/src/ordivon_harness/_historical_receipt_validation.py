"""Shared mechanical checks for the H3/H4/H5 historical receipt readers.

The readers still own their distinct provider, Host, Runtime and workload
acceptance conditions. These helpers neither authenticate evidence nor grant
current execution or domain authority.
"""
from __future__ import annotations

from typing import Any

from anc_canonical import canonical_digest, validate_digest


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def require_array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def require_integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an integer >= {minimum}")
    return value


def require_sha256(value: Any, label: str) -> str:
    text = require_string(value, label)
    try:
        return validate_digest(text)
    except ValueError as error:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>") from error


def require_all_true(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    checks = require_object(value, label)
    if set(checks) != expected:
        raise ValueError(f"{label} set differs")
    failed = sorted(name for name, result in checks.items() if result is not True)
    if failed:
        raise ValueError(f"{label} failed: {failed}")
    return checks


def verify_integrity(receipt: dict[str, Any], label: str) -> dict[str, Any]:
    integrity = require_object(receipt.get("integrity"), label)
    if integrity.get("algorithm") != "sha256":
        raise ValueError("receipt integrity algorithm differs")
    if integrity.get("canonicalization") != "ordivon-canonical-json-v1":
        raise ValueError("receipt canonicalization differs")
    # Canonical serialization is read-only, so a shallow top-level copy
    # preserves every nested value without duplicating the full receipt tree.
    payload = {key: value for key, value in receipt.items() if key != "integrity"}
    if integrity.get("payloadDigest") != canonical_digest(payload):
        raise ValueError("receipt integrity digest differs")
    return integrity
