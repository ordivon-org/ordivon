from __future__ import annotations

import re
from typing import Any

_MODEL_KEY = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
_STANDINGS = {"CORE", "MATURE_CONDITIONAL", "CONTESTED_CONDITIONAL", "STATE_MODEL"}
_ACTIVATIONS = {"ALWAYS", "CONDITIONAL"}
_ACTIONS = {"INFORM", "BASELINE", "TILT", "SIZE", "RISK_REVIEW", "EXECUTION_PLAN", "ATTRIBUTION"}


class InvestmentModelAtlasError(ValueError):
    pass


def _strings(value: Any, *, label: str, minimum: int = 0) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise InvestmentModelAtlasError(f"{label} must be an array with at least {minimum} items")
    if any(not isinstance(item, str) or not item for item in value):
        raise InvestmentModelAtlasError(f"{label} must contain non-empty strings")
    return value


def validate_investment_model_atlas_document(doc: Any) -> dict[str, Any]:
    if not isinstance(doc, dict):
        raise InvestmentModelAtlasError("atlas must be an object")
    required_root = {"schemaVersion", "kind", "truthRole", "principles", "models"}
    if set(doc) != required_root:
        raise InvestmentModelAtlasError("atlas root keys mismatch")
    if doc["schemaVersion"] != 1 or isinstance(doc["schemaVersion"], bool):
        raise InvestmentModelAtlasError("schemaVersion must equal 1")
    if doc["kind"] != "ordivon.capital.investment-model-atlas":
        raise InvestmentModelAtlasError("kind mismatch")
    if doc["truthRole"] != "EXTERNAL_MODEL_LIBRARY_NOT_INVESTMENT_TRUTH":
        raise InvestmentModelAtlasError("truthRole mismatch")
    _strings(doc["principles"], label="principles", minimum=1)
    if not isinstance(doc["models"], list) or not doc["models"]:
        raise InvestmentModelAtlasError("models must be a non-empty array")

    required = {
        "modelKey", "family", "role", "standing", "activation", "horizons",
        "decisionQuestions", "mechanism", "assumptions", "strongestWhen",
        "weakensWhen", "invalidators", "requiredTagsAll", "requiredTagsAny",
        "blockedTagsAny", "evidenceRefs", "allowedActions", "prohibitedActions",
    }
    seen: set[str] = set()
    for index, raw in enumerate(doc["models"]):
        label = f"models[{index}]"
        if not isinstance(raw, dict) or set(raw) != required:
            raise InvestmentModelAtlasError(f"{label} keys mismatch")
        key = raw["modelKey"]
        if not isinstance(key, str) or _MODEL_KEY.fullmatch(key) is None:
            raise InvestmentModelAtlasError(f"{label}.modelKey pattern mismatch")
        if key in seen:
            raise InvestmentModelAtlasError(f"duplicate modelKey: {key}")
        seen.add(key)
        for field in ("family", "role", "mechanism"):
            if not isinstance(raw[field], str) or not raw[field]:
                raise InvestmentModelAtlasError(f"{label}.{field} must be non-empty")
        if raw["standing"] not in _STANDINGS:
            raise InvestmentModelAtlasError(f"{label}.standing mismatch")
        if raw["activation"] not in _ACTIVATIONS:
            raise InvestmentModelAtlasError(f"{label}.activation mismatch")
        for field in (
            "horizons", "decisionQuestions", "assumptions", "strongestWhen",
            "weakensWhen", "invalidators", "requiredTagsAll", "requiredTagsAny",
            "blockedTagsAny", "evidenceRefs", "allowedActions", "prohibitedActions",
        ):
            _strings(raw[field], label=f"{label}.{field}")
        if not raw["decisionQuestions"] or not raw["evidenceRefs"]:
            raise InvestmentModelAtlasError(f"{label} needs decisionQuestions and evidenceRefs")
        if raw["activation"] == "CONDITIONAL" and not (raw["requiredTagsAll"] or raw["requiredTagsAny"]):
            raise InvestmentModelAtlasError(f"{label} conditional model has no routing tags")
        unknown_actions = set(raw["allowedActions"]) - _ACTIONS
        if unknown_actions:
            raise InvestmentModelAtlasError(f"{label}.allowedActions unknown={sorted(unknown_actions)}")
    return doc


def index_models(atlas: dict[str, Any]) -> dict[str, dict[str, Any]]:
    validate_investment_model_atlas_document(atlas)
    return {row["modelKey"]: row for row in atlas["models"]}
