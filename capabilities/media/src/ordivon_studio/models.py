from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .production_validation import _validate_cognition_record, _validate_production_semantics
from .runtime_receipt_validation import _validate_receipt_envelope, _validate_runtime_receipt
from .timed_text import iter_cues

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIRECTORY = ROOT / "schemas"
PRODUCTION_DIRECTORY = ROOT / "productions"

DOCUMENT_SCHEMAS = {
    "production.json": "production.schema.json",
    "claims.json": "claims.schema.json",
}
RUNTIME_RECEIPT_KIND = "ordivon-runtime-demo-receipt"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def _validator(schema_name: str) -> Draft202012Validator:
    schema = _load(SCHEMA_DIRECTORY / schema_name)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_repository() -> list[str]:
    errors: list[str] = []
    validators = {name: _validator(schema) for name, schema in DOCUMENT_SCHEMAS.items()}
    timed_text_validator = _validator("timed-text.schema.json")
    receipt_validator = _validator("runtime-demo-receipt.schema.json")

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

        production = documents.get("production.json")
        assets: dict[str, Any] | None = None
        if isinstance(production, dict):
            sources = production.get("sources", {})
            asset_reference = sources.get("assets") if isinstance(sources, dict) else None
            if isinstance(asset_reference, str):
                asset_path = production_directory / asset_reference
                if asset_path.is_file():
                    assets = _load(asset_path)
                    asset_validator = _validator("asset.schema.json")
                    for error in sorted(asset_validator.iter_errors(assets), key=lambda item: list(item.path)):
                        location = "/".join(str(part) for part in error.path)
                        errors.append(f"{asset_path}:{location}: {error.message}")

        if set(documents) == set(DOCUMENT_SCHEMAS) and isinstance(production, dict):
            errors.extend(
                _validate_production_semantics(
                    production_directory / "production.json",
                    production,
                    documents["claims.json"],
                    assets,
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

        if isinstance(production, dict):
            sources = production.get("sources", {})
            cognition_path = sources.get("cognition") if isinstance(sources, dict) else None
            if isinstance(cognition_path, str):
                errors.extend(_validate_cognition_record(production_directory / cognition_path))
            receipt_paths = sources.get("receipts", []) if isinstance(sources, dict) else []
            for relative_path in receipt_paths:
                if not isinstance(relative_path, str):
                    continue
                path = production_directory / relative_path
                if not path.is_file():
                    continue
                receipt = _load(path)
                errors.extend(_validate_receipt_envelope(path, receipt))
                if receipt.get("kind") == RUNTIME_RECEIPT_KIND:
                    for error in sorted(receipt_validator.iter_errors(receipt), key=lambda item: list(item.path)):
                        location = "/".join(str(part) for part in error.path)
                        errors.append(f"{path}:{location}: {error.message}")
                    errors.extend(_validate_runtime_receipt(path, receipt))
    return errors


def main() -> None:
    errors = validate_repository()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("Studio production models are valid.")


if __name__ == "__main__":
    main()
