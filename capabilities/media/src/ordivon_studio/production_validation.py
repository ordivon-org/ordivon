"""Validate owner-native Production, Claim and cognition semantics.

JSON Schema handles structure; this module checks exact source binding,
historical Git blobs, declared source carriers and bounded cognition order.
It never promotes a source snapshot to current owner intent or edits assets.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
COGNITION_SECTIONS = ("FRAME", "BIND", "EXPRESS", "RENDER", "AUDIT", "DECIDE", "LEARNING")


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _is_repository_path(value: str) -> bool:
    path = value.split("#", 1)[0]
    return bool(path) and not path.startswith(("/", "\\")) and "://" not in path and ".." not in Path(path).parts


def _validate_production_semantics(
    production_path: Path,
    production: dict[str, Any],
    claims: dict[str, Any],
    assets: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    prefix = str(production_path.parent)

    if claims.get("productionId") != production.get("id"):
        errors.append(f"{prefix}: claims productionId does not match production id")
    if assets is not None and assets.get("productionId") != production.get("id"):
        errors.append(f"{prefix}: assets productionId does not match production id")

    binding_ids = [
        item["id"]
        for item in production.get("sourceBindings", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    for duplicate in sorted(_duplicates(binding_ids)):
        errors.append(f"{prefix}: duplicate source binding id: {duplicate}")
    known_bindings = set(binding_ids)

    # Verify source revisions only for explicitly local monorepo bindings.
    # Other repositories retain their own source authority; a successful
    # local check must never be reported as a remote-owner qualification.
    local_sources = {
        item["id"]: item["revision"]
        for item in production.get("sourceBindings", [])
        if isinstance(item, dict)
        and item.get("repository") == "ordivon"
        and isinstance(item.get("id"), str)
        and isinstance(item.get("revision"), str)
    }
    verified_revisions: set[str] = set()
    for revision in sorted(set(local_sources.values())):
        observed = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-t", f"{revision}^{{commit}}"],
            check=False, capture_output=True, text=True,
        )
        if observed.returncode != 0 or observed.stdout.strip() != "commit":
            errors.append(f"{prefix}: declared local source revision unavailable: {revision}")
        else:
            verified_revisions.add(revision)

    claim_ids: list[str] = []
    for claim in claims.get("claims", []):
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        if isinstance(claim_id, str):
            claim_ids.append(claim_id)
        source = claim.get("source")
        if isinstance(source, dict):
            binding = source.get("binding")
            if binding not in known_bindings:
                errors.append(f"{prefix}: claim {claim_id!r} references unknown binding {binding!r}")
            source_path = source.get("path")
            if isinstance(source_path, str) and not _is_repository_path(source_path):
                errors.append(f"{prefix}: claim {claim_id!r} has invalid source path {source_path!r}")
            elif isinstance(source_path, str) and binding in local_sources:
                revision = local_sources[binding]
                if revision in verified_revisions:
                    # Require the actual historical Git object to be a file,
                    # not merely an existing path or a current-worktree file.
                    observed = subprocess.run(
                        ["git", "-C", str(ROOT), "cat-file", "-t",
                         f"{revision}:{source_path.split('#', 1)[0]}"],
                        check=False, capture_output=True, text=True,
                    )
                    if observed.returncode != 0 or observed.stdout.strip() != "blob":
                        errors.append(
                            f"{prefix}: claim {claim_id!r} historical source missing at "
                            f"{revision}:{source_path}"
                        )
        for evidence in claim.get("evidence", []):
            if isinstance(evidence, str) and not _is_repository_path(evidence):
                errors.append(f"{prefix}: claim {claim_id!r} has invalid evidence path {evidence!r}")
    for duplicate in sorted(_duplicates(claim_ids)):
        errors.append(f"{prefix}: duplicate claim id: {duplicate}")

    asset_ids = [
        item["id"]
        for item in (assets or {}).get("assets", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    for duplicate in sorted(_duplicates(asset_ids)):
        errors.append(f"{prefix}: duplicate asset id: {duplicate}")

    output_ids = [
        item["id"]
        for item in production.get("outputs", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    for duplicate in sorted(_duplicates(output_ids)):
        errors.append(f"{prefix}: duplicate output id: {duplicate}")

    sources = production.get("sources", {})
    if isinstance(sources, dict):
        source_paths: list[str] = []
        for value in sources.values():
            if isinstance(value, str):
                source_paths.append(value)
            elif isinstance(value, list):
                source_paths.extend(item for item in value if isinstance(item, str))
        for source_path in source_paths:
            resolved = (production_path.parent / source_path).resolve()
            if not resolved.is_relative_to(ROOT.resolve()):
                errors.append(f"{prefix}: source escapes repository: {source_path}")
            elif not resolved.exists():
                errors.append(f"{prefix}: declared source does not exist: {source_path}")

        # One owner-native, opt-in exact-byte seam. JSON Schema can check only a
        # digest's shape; a real source-carrier witness must inspect the bytes.
        # Derived article chapters and encoded media outputs must not be forced
        # to equal an unrelated source artifact.
        for output in production.get("outputs", []):
            if not isinstance(output, dict) or "sourceCarrier" not in output:
                continue
            carrier = output["sourceCarrier"]
            output_id = output.get("id")
            if not isinstance(carrier, str) or carrier not in source_paths:
                errors.append(f"{prefix}: output {output_id!r} sourceCarrier is not a declared source")
                continue
            path = (production_path.parent / carrier).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
                errors.append(f"{prefix}: output {output_id!r} sourceCarrier is not an accessible repository file")
                continue
            expected_digest = output.get("blobDigest")
            if not isinstance(expected_digest, str):
                errors.append(f"{prefix}: output {output_id!r} sourceCarrier requires blobDigest")
                continue
            try:
                with path.open("rb") as source_file:
                    actual_digest = "sha256:" + hashlib.file_digest(source_file, "sha256").hexdigest()
            except OSError as exc:
                errors.append(f"{prefix}: output {output_id!r} sourceCarrier unreadable: {exc}")
                continue
            if actual_digest != expected_digest:
                errors.append(f"{prefix}: output {output_id!r} sourceCarrier digest mismatch")
    return errors


def _validate_cognition_record(path: Path) -> list[str]:
    if not path.is_file():
        return [f"{path}: cognition record does not exist"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    positions: list[int] = []
    for section in COGNITION_SECTIONS:
        marker = f"## {section}"
        position = text.find(marker)
        if position < 0:
            errors.append(f"{path}: missing cognition section {section}")
        else:
            positions.append(position)
    if not errors and positions != sorted(positions):
        errors.append(f"{path}: cognition sections are out of protocol order")
    return errors
