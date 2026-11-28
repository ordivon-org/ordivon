"""Validate embedded Runtime demonstration receipts as bounded Media evidence.

This is a read-only cross-owner evidence check, not Runtime Job/Workspace
authority, state repair, credential discovery or a new execution engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Vocabulary of the archived v1 demonstration, not today's Runtime state machine.
DEMO_IN_PROGRESS = {"accepted", "queued", "starting", "running", "working"}


def _trace_errors(execution: dict[str, Any]) -> list[str]:
    """Refine the schema-validated trace in a single ordered pass."""
    errors: list[str] = []
    observations = execution["observations"]
    total = observations[0]["totalSteps"]
    previous = None
    for index, current in enumerate(observations):
        label = f"observations[{index}]"
        if current["attemptId"] != execution["attemptId"]:
            errors.append(f"{label}: attemptId does not match execution")
        expected = {execution["status"]} if index == len(observations) - 1 else DEMO_IN_PROGRESS
        if current["status"] not in expected:
            errors.append(f"{label}: invalid status for trace position")
        if current["totalSteps"] != total or current["completedSteps"] > total:
            errors.append(f"{label}: inconsistent step count")
        if "currentStepIndex" in current and current["currentStepIndex"] >= total:
            errors.append(f"{label}: current step index out of range")
        if previous is not None:
            for field in ("elapsedMs", "progressRevision", "completedSteps"):
                if current[field] < previous[field]:
                    errors.append(f"{label}: {field} regressed")
        previous = current
    terminal = observations[-1]
    if terminal["completedSteps"] != total:
        errors.append("terminal observation: steps incomplete")
    for field in ("exitCode", "elapsedMs"):
        if terminal.get(field) != execution[field]:
            errors.append(f"terminal observation: {field} does not match execution")
    return errors


def _terminal_claim_errors(evidence: dict[str, Any]) -> list[str]:
    """Check v1 naming and disposition claims, never authenticate an Artifact."""
    errors: list[str] = []
    attempt = evidence["attemptId"]
    for field, expected in (
        ("executionDisposition", "succeeded"),
        ("deliveryDisposition", "committed"),
        ("processTreeDisposition", "terminal_clean"),
    ):
        if evidence[field] != expected:
            errors.append(f"evidence: {field} contradicts passed demonstration")
    artifact_ids = set(evidence["terminalArtifactIds"])
    if not all(item.startswith(attempt + ".") for item in artifact_ids):
        errors.append("evidence: terminalArtifactIds contain a foreign attempt")
    if not {f"{attempt}.{kind}" for kind in ("stdout", "stderr", "result")}.issubset(artifact_ids):
        errors.append("evidence: required terminal artifact claims are absent")
    expected_id = f"{attempt}.terminal-evidence.{evidence['digest'].removeprefix('sha256:')}"
    if evidence["artifactId"] != expected_id:
        errors.append("evidence: artifactId does not match attempt and declared digest")
    return errors


def _validate_receipt_envelope(path: Path, receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if receipt.get("schemaVersion") != 1:
        errors.append(f"{path}: receipt schemaVersion must be 1")
    kind = receipt.get("kind")
    if not isinstance(kind, str) or not kind:
        errors.append(f"{path}: receipt kind must be a non-empty string")
    return errors


def _validate_runtime_receipt(path: Path, receipt: dict[str, Any]) -> list[str]:
    # Caller must first establish the v1 JSON Schema shape. An empty result
    # means internal consistency only; native ownership and readback are separate.
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

    errors.extend(f"{path}: {error}" for error in _trace_errors(execution))
    errors.extend(f"{path}: {error}" for error in _terminal_claim_errors(evidence))

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
