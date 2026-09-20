from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_json_document(
    document_path: Path,
    schema_path: Path,
    expected_kind: str | None = None,
) -> dict[str, Any]:
    value = load_json(document_path)
    schema = load_json(schema_path)
    failures: list[str] = []

    if not isinstance(value, dict):
        failures.append("document must be a JSON object")
    elif expected_kind is not None and value.get("kind") != expected_kind:
        failures.append(f"document kind must equal {expected_kind}")

    validator = "jsonschema"
    schema_status = "NOT_RUN"
    schema_error: str | None = None
    if importlib.util.find_spec("jsonschema") is None:
        validator = "unavailable"
        schema_error = "Python jsonschema package is not installed"
    else:
        try:
            import jsonschema  # type: ignore

            jsonschema.Draft202012Validator.check_schema(schema)
            instance = dict(value) if isinstance(value, dict) else value
            if isinstance(instance, dict):
                instance.pop("$schema", None)
            jsonschema.Draft202012Validator(
                schema,
                format_checker=jsonschema.FormatChecker(),
            ).validate(instance)
            schema_status = "PASS"
        except Exception as error:
            schema_status = "FAIL"
            schema_error = str(error)
            failures.append(f"JSON Schema validation failed: {error}")

    return {
        "status": "PASS" if not failures and schema_status == "PASS" else "FAIL",
        "document": value,
        "failures": failures,
        "jsonSchema": {
            "dialect": "https://json-schema.org/draft/2020-12/schema",
            "validator": validator,
            "status": schema_status,
            "error": schema_error,
            "schemaPath": str(schema_path.resolve()),
        },
    }
