"""Conservative MCP schema comparison, not a general implication solver."""

from __future__ import annotations

import json
from typing import Any

# JSON Schema keywords whose values are subschemas, not arbitrary JSON.
_SCHEMA_MAPS = {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas"}
_SCHEMA_ARRAYS = {"allOf", "anyOf", "oneOf", "prefixItems"}
_SCHEMA_VALUES = {
    "additionalProperties",
    "unevaluatedProperties",
    "propertyNames",
    "additionalItems",
    "unevaluatedItems",
    "contains",
    "not",
    "if",
    "then",
    "else",
    "contentSchema",
    "items",
}
_SCHEMA_ANNOTATIONS = {"title", "description", "examples"}


def _semantic_schema(value: Any) -> Any:
    """Ignore prose only at schema positions; preserve data and named maps.

    JSON Schema properties and definition names can themselves be "title",
    "description" or "examples". Defaults, constants, enumerations and
    unrecognized extension keywords are opaque JSON, never subschemas.
    The comparator is conservative, not a schema implication solver.
    """
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key in _SCHEMA_ANNOTATIONS:
            continue
        if key in _SCHEMA_MAPS and isinstance(item, dict):
            result[key] = {name: _semantic_schema(schema) for name, schema in item.items()}
        elif (key in _SCHEMA_ARRAYS or key == "items") and isinstance(item, list):
            result[key] = [_semantic_schema(schema) for schema in item]
        elif key in _SCHEMA_VALUES:
            result[key] = _semantic_schema(item)
        elif key == "dependencies" and isinstance(item, dict):
            # Legacy dialect: a dependency is either a schema or property names.
            result[key] = {name: _semantic_schema(schema) for name, schema in item.items()}
        else:
            result[key] = item
    return result


def _same_schema(previous: Any, candidate: Any) -> bool:
    # JSON booleans are not numbers, unlike Python's True == 1.
    return json.dumps(_semantic_schema(previous), sort_keys=True) == json.dumps(
        _semantic_schema(candidate), sort_keys=True
    )


def _tool_contract_map(contracts: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(contracts, list):
        raise ValueError("native MCP contracts must be a list")
    values: dict[str, dict[str, Any]] = {}
    for item in contracts:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str):
            raise ValueError("invalid native MCP tool row")
        name = item["name"]
        if not name or name in values or not isinstance(item.get("inputSchema"), dict):
            raise ValueError(f"duplicate/invalid native MCP input tool: {name}")
        if (
            "outputSchema" in item
            and item["outputSchema"] is not None
            and not isinstance(item["outputSchema"], dict)
        ):
            raise ValueError(f"invalid native MCP output schema: {name}")
        values[name] = item
    return values


# Only this deliberately small object fragment has a local directional rule.
# Other JSON Schema constraints can couple fields, references and evaluation.
_SIMPLE_OBJECT = {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "title",
    "description",
    "examples",
    "$defs",
    "$schema",
}


def _qualified_schema(value: dict[str, Any]) -> bool:
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError

    # Native MCP's current dialect is 2020-12. Other explicit dialects need
    # their own validator and comparison contract, never an inferred PASS.
    if (
        value.get("type") != "object"
        or value.get("$schema", "https://json-schema.org/draft/2020-12/schema")
        != "https://json-schema.org/draft/2020-12/schema"
    ):
        return False
    try:
        Draft202012Validator.check_schema(value)
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except SchemaError, ValueError, TypeError, RecursionError:
        return False
    return True


def _contains_reference_identity(value: Any) -> bool:
    if isinstance(value, dict):
        if value.keys() & {"$ref", "$dynamicRef", "$id", "$anchor", "$dynamicAnchor"}:
            return True
        return any(_contains_reference_identity(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_reference_identity(child) for child in value)
    return False


def _new_fields_qualified(
    previous: dict[str, Any], candidate: dict[str, Any], *, input_side: bool
) -> bool:
    """Sufficient structural conditions only; not general schema implication."""
    if (
        previous.get("type") != "object"
        or candidate.get("type") != "object"
        or not previous.keys() <= _SIMPLE_OBJECT
        or not candidate.keys() <= _SIMPLE_OBJECT
        or _contains_reference_identity(previous)
        or _contains_reference_identity(candidate)
    ):
        return False
    old_extra = previous.get("additionalProperties", True)
    # Old closed input could never contain the new name; optional additions
    # preserve its input language. Old open output permits a new name.
    # Schema-valued additionalProperties needs a separate proof.
    return old_extra is False if input_side else old_extra is True


def _compare_object_schema(
    name: str, field: str, previous: Any, candidate: Any, *, input_side: bool
) -> list[str]:
    issues: list[str] = []
    if previous is None:
        return issues if candidate is None else [f"{field} added schema {name}"]
    if not isinstance(previous, dict) or not isinstance(candidate, dict):
        return [f"{field} removed schema {name}"]
    if not _qualified_schema(previous) or not _qualified_schema(candidate):
        return [f"{field} malformed schema {name}"]
    previous_props = previous.get("properties", {})
    next_props = candidate.get("properties", {})
    previous_defs = previous.get("$defs", {})
    next_defs = candidate.get("$defs", {})
    if not all(
        isinstance(value, dict) for value in (previous_props, next_props, previous_defs, next_defs)
    ):
        return [f"{field} malformed schema {name}"]

    old_required = set(previous.get("required", []))
    new_required = set(candidate.get("required", []))
    required_delta = new_required - old_required if input_side else old_required - new_required
    for prop in sorted(required_delta):
        issues.append(f"{field} {'new' if input_side else 'lost'} required {name}.{prop}")
    added = next_props.keys() - previous_props.keys()
    if added and not _new_fields_qualified(previous, candidate, input_side=input_side):
        for prop in sorted(added):
            issues.append(f"{field} unqualified added field {name}.{prop}")
    for prop in sorted(previous_props.keys() - next_props.keys()):
        issues.append(f"{field} removed field {name}.{prop}")
    for prop in sorted(previous_props.keys() & next_props.keys()):
        if not _same_schema(previous_props[prop], next_props[prop]):
            issues.append(f"{field} changed field {name}.{prop}")
    if next_defs.keys() - previous_defs.keys():
        # Reference-resolution changes require independent qualification.
        for definition in sorted(next_defs.keys() - previous_defs.keys()):
            issues.append(f"{field} added definition {name}.{definition}")
    for definition in sorted(previous_defs.keys() - next_defs.keys()):
        issues.append(f"{field} removed definition {name}.{definition}")
    for definition in sorted(previous_defs.keys() & next_defs.keys()):
        if not _same_schema(previous_defs[definition], next_defs[definition]):
            issues.append(f"{field} changed definition {name}.{definition}")
    # The outer object constraints matter too: additionalProperties=false,
    # oneOf/anyOf, maxProperties and new closed-world clauses can break callers.
    ignored = {"properties", "required", "$defs", "title", "description", "examples"}
    old_outer = {k: v for k, v in previous.items() if k not in ignored}
    new_outer = {k: v for k, v in candidate.items() if k not in ignored}
    if not _same_schema(old_outer, new_outer):
        issues.append(f"{field} changed object constraints {name}")
    return issues


def compare_native_tool_contracts(previous: Any, candidate: Any) -> list[str]:
    """Conservative provider check: old tools and call/result schemas must survive.

    This is NOT a claim of behavioral, authorization, or deployed Agent
    compatibility. A reported change requires owner-qualified consumer
    evidence or a versioned ABI, not a guessed waiver.
    """
    old = _tool_contract_map(previous)
    new = _tool_contract_map(candidate)
    issues = [f"removed tool {name}" for name in sorted(old.keys() - new.keys())]
    for name in sorted(new.keys() - old.keys()):
        row = new[name]
        for field in ("inputSchema", "outputSchema"):
            if row.get(field) is not None and not _qualified_schema(row[field]):
                issues.append(f"{field} malformed schema {name}")
    for name in sorted(old.keys() & new.keys()):
        issues.extend(
            _compare_object_schema(
                name,
                "input",
                old[name]["inputSchema"],
                new[name]["inputSchema"],
                input_side=True,
            )
        )
        issues.extend(
            _compare_object_schema(
                name,
                "output",
                old[name].get("outputSchema"),
                new[name].get("outputSchema"),
                input_side=False,
            )
        )
    return issues
