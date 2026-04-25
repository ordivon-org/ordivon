from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ALLOWED_FINANCE_DECISION_DIRECTIONS = {"long", "short", "hold", "observe"}


@dataclass(slots=True)
class FinanceDecisionValidationResult:
    payload: dict[str, Any]
    validation_errors: list[dict[str, str]] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.validation_errors


def validate_finance_decision_intake(payload: dict[str, Any]) -> FinanceDecisionValidationResult:
    normalized_payload = {
        "symbol": payload.get("symbol"),
        "timeframe": payload.get("timeframe"),
        "direction": payload.get("direction"),
        "thesis": payload.get("thesis"),
        "entry_condition": payload.get("entry_condition"),
        "invalidation_condition": payload.get("invalidation_condition"),
        "stop_loss": payload.get("stop_loss"),
        "target": payload.get("target"),
        "position_size_usdt": payload.get("position_size_usdt"),
        "max_loss_usdt": payload.get("max_loss_usdt"),
        "risk_unit_usdt": payload.get("risk_unit_usdt"),
        "is_revenge_trade": payload.get("is_revenge_trade"),
        "is_chasing": payload.get("is_chasing"),
        "emotional_state": payload.get("emotional_state"),
        "confidence": payload.get("confidence"),
        "rule_exceptions": list(payload.get("rule_exceptions") or []),
        "notes": payload.get("notes"),
    }
    errors: list[dict[str, str]] = []

    _require_non_empty_text(errors, "thesis", normalized_payload["thesis"])
    _require_non_empty_text(errors, "stop_loss", normalized_payload["stop_loss"])
    _require_non_empty_text(errors, "emotional_state", normalized_payload["emotional_state"])

    _require_positive_number(errors, "max_loss_usdt", normalized_payload["max_loss_usdt"])
    _require_positive_number(errors, "position_size_usdt", normalized_payload["position_size_usdt"])
    _require_positive_number(errors, "risk_unit_usdt", normalized_payload["risk_unit_usdt"])
    _require_explicit_boolean(errors, "is_revenge_trade", normalized_payload["is_revenge_trade"])
    _require_explicit_boolean(errors, "is_chasing", normalized_payload["is_chasing"])

    direction = normalized_payload["direction"]
    if not isinstance(direction, str) or direction not in ALLOWED_FINANCE_DECISION_DIRECTIONS:
        errors.append(
            {
                "field": "direction",
                "code": "invalid_choice",
                "message": "direction must be one of: long, short, hold, observe.",
            }
        )

    confidence = normalized_payload["confidence"]
    if confidence is not None:
        try:
            parsed_confidence = float(confidence)
        except (TypeError, ValueError):
            errors.append(
                {
                    "field": "confidence",
                    "code": "invalid_number",
                    "message": "confidence must be numeric when provided.",
                }
            )
        else:
            if parsed_confidence < 0 or parsed_confidence > 1:
                errors.append(
                    {
                        "field": "confidence",
                        "code": "out_of_range",
                        "message": "confidence must be between 0 and 1.",
                    }
                )
            else:
                normalized_payload["confidence"] = parsed_confidence

    return FinanceDecisionValidationResult(payload=normalized_payload, validation_errors=errors)


def _require_non_empty_text(errors: list[dict[str, str]], field_name: str, value: Any) -> None:
    if isinstance(value, str) and value.strip():
        return
    errors.append(
        {
            "field": field_name,
            "code": "required",
            "message": f"{field_name} is required before governance.",
        }
    )


def _require_positive_number(errors: list[dict[str, str]], field_name: str, value: Any) -> None:
    if value is None:
        errors.append(
            {
                "field": field_name,
                "code": "required",
                "message": f"{field_name} is required before governance.",
            }
        )
        return

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        errors.append(
            {
                "field": field_name,
                "code": "invalid_number",
                "message": f"{field_name} must be numeric.",
            }
        )
        return

    if parsed <= 0:
        errors.append(
            {
                "field": field_name,
                "code": "non_positive",
                "message": f"{field_name} must be positive.",
            }
        )


def _require_explicit_boolean(errors: list[dict[str, str]], field_name: str, value: Any) -> None:
    if isinstance(value, bool):
        return
    errors.append(
        {
            "field": field_name,
            "code": "explicit_answer_required",
            "message": f"{field_name} must be explicitly answered before governance.",
        }
    )
