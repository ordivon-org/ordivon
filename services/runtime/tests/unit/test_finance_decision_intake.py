from copy import deepcopy

from packs.finance.decision_intake import validate_finance_decision_intake


def _valid_payload() -> dict:
    return {
        "symbol": "BTC/USDT",
        "timeframe": "1h",
        "direction": "long",
        "thesis": "Momentum and structure are aligned.",
        "entry_condition": "Breakout with retest.",
        "invalidation_condition": "Range reclaim fails.",
        "stop_loss": "Below intraday support",
        "target": "Retest local high",
        "position_size_usdt": 150.0,
        "max_loss_usdt": 25.0,
        "risk_unit_usdt": 10.0,
        "is_revenge_trade": False,
        "is_chasing": False,
        "emotional_state": "calm",
        "confidence": 0.6,
        "rule_exceptions": [],
        "notes": "Controlled setup",
    }


def test_missing_required_fields_fail_validation_before_governance():
    required_cases = [
        "thesis",
        "stop_loss",
        "max_loss_usdt",
        "position_size_usdt",
        "risk_unit_usdt",
        "emotional_state",
        "is_revenge_trade",
        "is_chasing",
    ]

    for field_name in required_cases:
        payload = _valid_payload()
        payload[field_name] = None

        result = validate_finance_decision_intake(payload)

        assert result.is_valid is False
        assert any(error["field"] == field_name for error in result.validation_errors)


def test_explicit_false_booleans_pass_validation():
    result = validate_finance_decision_intake(_valid_payload())

    assert result.is_valid is True
    assert result.validation_errors == []
    assert result.payload["is_revenge_trade"] is False
    assert result.payload["is_chasing"] is False


def test_invalid_direction_fails_validation():
    payload = _valid_payload()
    payload["direction"] = "flip"

    result = validate_finance_decision_intake(payload)

    assert result.is_valid is False
    assert any(error["field"] == "direction" for error in result.validation_errors)


def test_confidence_outside_zero_to_one_fails_validation():
    payload = _valid_payload()
    payload["confidence"] = 1.2

    result = validate_finance_decision_intake(payload)

    assert result.is_valid is False
    assert any(error["field"] == "confidence" for error in result.validation_errors)


def test_numeric_fields_must_be_positive():
    for field_name in ("max_loss_usdt", "position_size_usdt", "risk_unit_usdt"):
        payload = _valid_payload()
        payload[field_name] = 0

        result = validate_finance_decision_intake(payload)

        assert result.is_valid is False
        assert any(error["field"] == field_name for error in result.validation_errors)


def test_client_cannot_silently_fill_missing_discipline_fields():
    payload = deepcopy(_valid_payload())
    payload["thesis"] = None
    payload["is_revenge_trade"] = None
    payload["is_chasing"] = None

    result = validate_finance_decision_intake(payload)

    assert result.is_valid is False
    assert result.payload["thesis"] is None
    assert result.payload["is_revenge_trade"] is None
    assert result.payload["is_chasing"] is None
