"""Validate owner-native Production, Claim and cognition semantics.

JSON Schema handles structure; this module checks exact source binding,
historical Git blobs, declared source carriers and bounded cognition order.
It never promotes a source snapshot to current owner intent or edits assets.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .cognition_sections import COGNITION_SECTIONS, cognition_sections
from .production_output_identity import declared_source_files, observe_output_blob

ROOT = Path(__file__).resolve().parents[2]


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
        source_paths = declared_source_files(sources)
        for source_path in sorted(source_paths):
            resolved = (production_path.parent / source_path).resolve()
            if not resolved.is_relative_to(ROOT.resolve()):
                errors.append(f"{prefix}: source escapes repository: {source_path}")
            elif not resolved.is_file():
                errors.append(f"{prefix}: declared source is not an accessible regular file: {source_path}")

        # Same observed byte relation as the actual Production context.
        # Validation policy differs by role: a sourceCarrier is a required
        # exact-byte assertion; a missing/unstable outputCarrier is UNKNOWN.
        for output in production.get("outputs", []):
            if not isinstance(output, dict):
                continue
            role = "sourceCarrier" if output.get("sourceCarrier") is not None else "outputCarrier"
            if output.get(role) is None:
                continue
            row = observe_output_blob(
                production_path.parent, output,
                declared_source_files=source_paths, selected_file=None,
            )
            relation = row["relation"]
            label = f"{prefix}: output {output.get('id')!r}"
            messages = {
                "INVALID_MULTIPLE_CARRIERS": "has multiple carrier types",
                "INVALID_UNDECLARED_SOURCE_CARRIER": "sourceCarrier is not a declared source",
                "INVALID_SOURCE_CARRIER_PATH": "invalid sourceCarrier path",
                "INVALID_OUTPUT_CARRIER": "invalid outputCarrier path",
                "INVALID_ESCAPING_SOURCE_CARRIER": "sourceCarrier escapes Production root",
                "INVALID_ESCAPING_OUTPUT_CARRIER": "outputCarrier escapes Production root",
                "UNKNOWN_NO_VALID_DECLARED_DIGEST": f"{role} requires blobDigest",
                "DIFFERS_FROM_DECLARED_DIGEST": f"{role} digest mismatch",
            }
            if relation in messages:
                errors.append(f"{label} {messages[relation]}")
            elif role == "sourceCarrier" and relation != "MATCHES_DECLARED_DIGEST":
                errors.append(f"{label} sourceCarrier lacks stable byte evidence: {relation}")
    return errors


def _validate_cognition_record(path: Path) -> list[str]:
    if not path.is_file():
        return [f"{path}: cognition record does not exist"]
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    observed = [section.title for section in cognition_sections(text) if section.title in COGNITION_SECTIONS]
    for section in COGNITION_SECTIONS:
        count = observed.count(section)
        if not count:
            errors.append(f"{path}: missing cognition section {section}")
        elif count > 1:
            errors.append(f"{path}: duplicate cognition section {section}")
    if not errors and tuple(observed) != COGNITION_SECTIONS:
        errors.append(f"{path}: cognition sections are out of protocol order")
    return errors
