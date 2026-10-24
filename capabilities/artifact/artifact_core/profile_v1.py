from __future__ import annotations

from pathlib import Path
from typing import Any

from .json_validation import validate_json_document

DEFAULT_PROFILE_V1_SCHEMA = Path(__file__).resolve().parents[1] / "artifact-delivery/profile-v1.schema.json"


def validate_profile_v1(
    profile_path: Path,
    schema_path: Path = DEFAULT_PROFILE_V1_SCHEMA,
) -> dict[str, Any]:
    """Reuse the owner's JSON Schema 2020-12 validation without shadow rules."""
    result = validate_json_document(profile_path, schema_path)
    return {
        "status": result["status"],
        "profile": result["document"],
        # Preserve the existing receipt's field for downstream callers.
        "minimalContractErrors": result["failures"],
        "jsonSchema": result["jsonSchema"],
    }
