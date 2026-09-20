from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

DEFAULT_PROFILE_V1_SCHEMA = Path(__file__).resolve().parents[1] / "artifact-delivery/profile-v1.schema.json"


def _minimal_profile_checks(value: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["profile must be a JSON object"]
    required = {
        "profileVersion", "id", "artifactClass", "authorityMode", "locale",
        "primaryOutput", "targetRenderer", "gates", "deliveryTargets",
    }
    missing = sorted(required - set(value))
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    if value.get("profileVersion") != 1:
        errors.append("profileVersion must equal 1")
    expected_primary = {"presentation": "pptx", "document": "docx", "spreadsheet": "xlsx", "web": "html"}
    artifact_class = value.get("artifactClass")
    primary = value.get("primaryOutput")
    if artifact_class in expected_primary:
        if not isinstance(primary, dict) or primary.get("format") != expected_primary[artifact_class]:
            errors.append(f"{artifact_class} primaryOutput.format must be {expected_primary[artifact_class]}")
    if artifact_class in {"fixed-view", "archive", "accessible"}:
        if not isinstance(primary, dict) or primary.get("format") not in {"pdf", "pdf-a-4", "pdf-ua-2"}:
            errors.append(f"{artifact_class} primaryOutput.format must be a PDF format")
    if artifact_class == "presentation":
        for field in ("aspectRatio", "fontPolicy", "fonts"):
            if field not in value:
                errors.append(f"presentation profile requires {field}")
    gates = value.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
    else:
        for key in ("profileSchema", "structural", "target", "deliveryReadback"):
            if not isinstance(gates.get(key), bool):
                errors.append(f"gates.{key} must be boolean")
        for key, flag in gates.items():
            if not isinstance(flag, bool):
                errors.append(f"gates.{key} must be boolean")
    return errors


def validate_profile_v1(
    profile_path: Path,
    schema_path: Path = DEFAULT_PROFILE_V1_SCHEMA,
) -> dict[str, Any]:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = _minimal_profile_checks(profile)
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
            instance = dict(profile)
            instance.pop("$schema", None)
            jsonschema.Draft202012Validator(schema).validate(instance)
            schema_status = "PASS"
        except Exception as error:
            schema_status = "FAIL"
            schema_error = str(error)
            errors.append(f"JSON Schema validation failed: {error}")
    return {
        "status": "PASS" if not errors and schema_status == "PASS" else "FAIL",
        "profile": profile,
        "minimalContractErrors": errors,
        "jsonSchema": {
            "dialect": "https://json-schema.org/draft/2020-12/schema",
            "validator": validator,
            "status": schema_status,
            "error": schema_error,
            "schemaPath": str(schema_path.resolve()),
        },
    }
