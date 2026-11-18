"""Validate embedded Runtime demonstration receipts as bounded Media evidence.

This is a read-only cross-owner evidence check, not Runtime Job/Workspace
authority, state repair, credential discovery or a new execution engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TERMINAL = {"succeeded", "failed", "timed_out", "cancelled", "lost", "orphaned"}


def _validate_receipt_envelope(path: Path, receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if receipt.get("schemaVersion") != 1:
        errors.append(f"{path}: receipt schemaVersion must be 1")
    kind = receipt.get("kind")
    if not isinstance(kind, str) or not kind:
        errors.append(f"{path}: receipt kind must be a non-empty string")
    return errors


def _validate_runtime_receipt(path: Path, receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    execution = receipt.get("execution", {})
    evidence = receipt.get("evidence", {})
    workspace = receipt.get("workspace", {})
    source = receipt.get("source", {})
    close = receipt.get("close", {})
    diff = receipt.get("diff", {})

    expected_pairs = (
        ("execution/evidence jobId", execution.get("jobId"), evidence.get("jobId")),
        ("execution/evidence attemptId", execution.get("attemptId"), evidence.get("attemptId")),
        ("workspace/evidence workspaceId", workspace.get("workspaceId"), evidence.get("workspaceId")),
        ("source/workspace revision", source.get("revision"), workspace.get("sourceRevision")),
        ("source/evidence revision", source.get("revision"), evidence.get("sourceRevision")),
        ("workspace/close sourceStateDigest", workspace.get("sourceStateDigest"), close.get("sourceStateDigest")),
    )
    for label, left, right in expected_pairs:
        if left != right:
            errors.append(f"{path}: {label} does not match")

    observations = execution.get("observations", [])
    if isinstance(observations, list) and not any(
        isinstance(item, dict) and item.get("status") not in TERMINAL for item in observations
    ):
        errors.append(f"{path}: receipt contains no non-terminal observation")

    changed = set(diff.get("changedPaths", [])) if isinstance(diff.get("changedPaths"), list) else set()
    modified = set(diff.get("modifiedPaths", [])) if isinstance(diff.get("modifiedPaths"), list) else set()
    if not modified.issubset(changed):
        errors.append(f"{path}: modifiedPaths is not a subset of changedPaths")

    kinds = {
        item.get("kind")
        for item in receipt.get("presentation", [])
        if isinstance(item, dict) and isinstance(item.get("kind"), str)
    }
    required_kinds = {"source", "workspace", "patch", "job", "recover", "step", "evidence", "diff", "close"}
    if not required_kinds.issubset(kinds):
        errors.append(f"{path}: presentation omits required proof events")

    encoded = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    forbidden = (
        "ORDIVON_BEARER_TOKEN",
        "Authorization",
        "Bearer ",
        "/root/",
        "/var/lib/",
        "/tmp/",
        "\\Users\\",
    )
    for value in forbidden:
        if value in encoded:
            errors.append(f"{path}: receipt contains forbidden private material: {value!r}")
    return errors
