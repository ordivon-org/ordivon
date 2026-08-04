from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .timed_text import iter_cues


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIRECTORY = ROOT / "schemas"
PRODUCTION_DIRECTORY = ROOT / "productions"

DOCUMENT_SCHEMAS = {
    "production.json": "production.schema.json",
    "claims.json": "claims.schema.json",
    "assets.json": "asset.schema.json",
}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def _validator(schema_name: str) -> Draft202012Validator:
    schema = _load(SCHEMA_DIRECTORY / schema_name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


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


def _validate_production_semantics(production_path: Path, production: dict[str, Any], claims: dict[str, Any], assets: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    prefix = str(production_path.parent)

    if claims.get("productionId") != production.get("id"):
        errors.append(f"{prefix}: claims productionId does not match production id")
    if assets.get("productionId") != production.get("id"):
        errors.append(f"{prefix}: assets productionId does not match production id")

    binding_ids = [item["id"] for item in production.get("sourceBindings", []) if isinstance(item, dict) and isinstance(item.get("id"), str)]
    for duplicate in sorted(_duplicates(binding_ids)):
        errors.append(f"{prefix}: duplicate source binding id: {duplicate}")
    known_bindings = set(binding_ids)

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
        for evidence in claim.get("evidence", []):
            if isinstance(evidence, str) and not _is_repository_path(evidence):
                errors.append(f"{prefix}: claim {claim_id!r} has invalid evidence path {evidence!r}")
    for duplicate in sorted(_duplicates(claim_ids)):
        errors.append(f"{prefix}: duplicate claim id: {duplicate}")

    asset_ids = [item["id"] for item in assets.get("assets", []) if isinstance(item, dict) and isinstance(item.get("id"), str)]
    for duplicate in sorted(_duplicates(asset_ids)):
        errors.append(f"{prefix}: duplicate asset id: {duplicate}")

    output_ids = [item["id"] for item in production.get("outputs", []) if isinstance(item, dict) and isinstance(item.get("id"), str)]
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
            if not (production_path.parent / source_path).resolve().is_relative_to(ROOT.resolve()):
                errors.append(f"{prefix}: source escapes repository: {source_path}")
            elif not (production_path.parent / source_path).exists():
                errors.append(f"{prefix}: declared source does not exist: {source_path}")
    return errors


def validate_repository() -> list[str]:
    errors: list[str] = []
    validators = {name: _validator(schema) for name, schema in DOCUMENT_SCHEMAS.items()}
    timed_text_validator = _validator("timed-text.schema.json")

    for production_directory in sorted(path for path in PRODUCTION_DIRECTORY.iterdir() if path.is_dir()):
        documents: dict[str, dict[str, Any]] = {}
        for document_name, validator in validators.items():
            path = production_directory / document_name
            if not path.exists():
                errors.append(f"{path}: required production document is missing")
                continue
            document = _load(path)
            documents[document_name] = document
            for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
                location = "/".join(str(part) for part in error.path)
                errors.append(f"{path}:{location}: {error.message}")

        if set(documents) == set(DOCUMENT_SCHEMAS):
            errors.extend(
                _validate_production_semantics(
                    production_directory / "production.json",
                    documents["production.json"],
                    documents["claims.json"],
                    documents["assets.json"],
                )
            )

        timed_text_directory = production_directory / "timed-text"
        if timed_text_directory.is_dir():
            for path in sorted(timed_text_directory.glob("*.json")):
                document = _load(path)
                for error in sorted(timed_text_validator.iter_errors(document), key=lambda item: list(item.path)):
                    location = "/".join(str(part) for part in error.path)
                    errors.append(f"{path}:{location}: {error.message}")
                try:
                    tuple(iter_cues(document))
                except ValueError as error:
                    errors.append(f"{path}:semantic: {error}")
    return errors


def main() -> None:
    errors = validate_repository()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("Studio production models are valid.")


if __name__ == "__main__":
    main()
