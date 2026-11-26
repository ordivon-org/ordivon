"""Shared canonical closure encoding and commitment projection.

No source byte is read here; historical consumption checks representation
consistency, not the execution witness or current installed environment.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


def is_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def closure_digest(files: list[dict[str, Any]]) -> str:
    payload = json.dumps({"schemaVersion": 1, "files": files}, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def canonical_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError("invalid closure path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("noncanonical closure path")
    return value


def closure_entries(files: object) -> dict[str, str]:
    if not isinstance(files, list) or not files:
        raise ValueError("selected source closure must contain files")
    entries: dict[str, str] = {}
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "digest"}:
            raise ValueError("invalid source closure entry")
        path = canonical_relative_path(item["path"])
        digest = item["digest"]
        if path in entries or not is_digest(digest):
            raise ValueError("duplicate or invalid source closure entry")
        entries[path] = digest
    if list(entries) != sorted(entries):
        raise ValueError("source closure entries must be canonically sorted")
    return entries


def source_commitments(root: Path, files: object, *, observe: bool = False) -> dict[str, str]:
    entries = closure_entries(files)
    root = root.resolve()
    result = {}
    for relative, digest in entries.items():
        path = root / relative
        if observe and path.resolve(strict=True) != path:
            raise ValueError("noncanonical selected source closure carrier")
        result[str(path)] = digest
    return result


def add_input_commitment(dependencies: dict[str, str], path: str, digest: str) -> None:
    if not isinstance(path, str) or not Path(path).is_absolute() or str(Path(path)) != path or ".." in Path(path).parts:
        raise ValueError("selected input must be canonical absolute path")
    if not is_digest(digest):
        raise ValueError("selected input digest must be SHA-256")
    if path in dependencies and dependencies[path] != digest:
        raise ValueError("selected Media input conflicts with source closure")
    dependencies[path] = digest


def commitment_rows(dependencies: dict[str, str]) -> list[dict[str, str]]:
    return [{"path": path, "expectedDigest": digest} for path, digest in sorted(dependencies.items())]


def validate_selected_closure(
    root: Path, plan: dict[str, Any], *, profile_path: str, adapter_path: str,
    required_paths: set[str],
) -> None:
    closure = plan["sourceClosureBinding"]
    binding = plan["inputByteBinding"]
    execution = plan["execution"]
    files = closure.get("files")
    entries = closure_entries(files)
    if closure.get("scope") != "declared-owner-local-source-files-not-installed-environment":
        raise ValueError("unsupported source closure scope")
    if closure.get("digest") != closure_digest(files):
        raise ValueError("source closure digest mismatch")
    if set(entries) != {profile_path, adapter_path, *required_paths}:
        raise ValueError("selected source closure inventory mismatch")
    if entries[profile_path] != plan.get("profileDigest") or entries[adapter_path] != plan.get("adapterDigest"):
        raise ValueError("selected profile or adapter digest mismatch in closure")
    if binding.get("status") != "proposed-not-executed" or binding.get("witnessScope") != "runtime_host_namespace_path_witness":
        raise ValueError("unsupported selected input binding")
    dependencies = source_commitments(root, files)
    add_input_commitment(dependencies, binding.get("inputPath"), binding.get("expectedDigest"))
    if execution.get("hostDependencies") != commitment_rows(dependencies):
        raise ValueError("selected Host Dependencies mismatch")
