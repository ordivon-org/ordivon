from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .common import (
    DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA,
    DEFAULT_PRESENTATION_SOURCE_SCHEMA,
    _presentation_source_material_facts,
    _semantic_svg_source_material_facts,
)

JsonValidator = Callable[[Path, Path, str | None], dict[str, Any]]


def admit_presentation_source(
    source_path: Path,
    *,
    validate_json_document: JsonValidator,
    source_schema_path: Path = DEFAULT_PRESENTATION_SOURCE_SCHEMA,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    result = validate_json_document(source_path, source_schema_path, "presentation-source")
    failures: list[str] = []
    if result.get("status") != "PASS":
        failures.append("presentation source did not PASS validation")
    document = result.get("document", {}) if isinstance(result, dict) else {}
    materials: list[dict[str, Any]] = []
    if isinstance(document, dict):
        materials, material_failures = _presentation_source_material_facts(source_path, document)
        failures.extend(material_failures)
    return result, materials, failures


def admit_semantic_svg_source(
    source_path: Path,
    *,
    validate_json_document: JsonValidator,
    source_schema_path: Path = DEFAULT_PRESENTATION_SEMANTIC_SVG_SOURCE_SCHEMA,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str]]:
    result = validate_json_document(source_path, source_schema_path, "presentation-semantic-svg-source")
    failures: list[str] = []
    if result.get("status") != "PASS":
        failures.append("semantic SVG presentation source did not PASS validation")
    document = result.get("document", {}) if isinstance(result, dict) else {}
    materials: list[dict[str, Any]] = []
    if isinstance(document, dict):
        materials, material_failures = _semantic_svg_source_material_facts(source_path, document)
        failures.extend(material_failures)
    return result, materials, failures
