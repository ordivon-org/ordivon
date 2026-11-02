"""Host Social Graph input admission must preserve exact SQL bigint semantics.

Existing Pydantic and PostgreSQL owners: no new validator/parser dependency.
CEGAR rejection covers values that Pydantic would otherwise coerce to int.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest
from pydantic import ValidationError

from ordivon_host_v2.collaboration_inputs import MessageInput
from ordivon_host_v2.coordination_inputs import CoordinationIntentInput

BIGINT_MAX = (1 << 63) - 1
VALID_INPUTS = (
    (MessageInput, "recorded_at_ms", {
        "message_ref": "message:k03-test",
        "client_request_id": "request:k03-test",
        "space_ref": "space:k03-test",
        "topic_ref": "topic:k03-test",
        "author_actor_ref": "actor:agent:k03-test",
        "body": "typed timestamp",
        "recorded_at_ms": 1,
    }),
    (CoordinationIntentInput, "observed_at_ms", {
        "intent_ref": "intent:k03-test",
        "actor_ref": "actor:agent:k03-test",
        "subject_ref": "subject:k03-test",
        "operation": "inspect",
        "observed_at_ms": 1,
        "expires_at_ms": None,
    }),
    (CoordinationIntentInput, "expires_at_ms", {
        "intent_ref": "intent:k03-test",
        "actor_ref": "actor:agent:k03-test",
        "subject_ref": "subject:k03-test",
        "operation": "inspect",
        "observed_at_ms": 0,
        "expires_at_ms": 1,
    }),
)


@pytest.mark.parametrize("input_value", (
    True, False, 1.0, Decimal("1"), Fraction(1, 1), "1", float("nan"),
    float("inf"), BIGINT_MAX + 1,
))
@pytest.mark.parametrize("model,field,payload", VALID_INPUTS)
def test_timestamp_rejects_type_aliases_and_sql_bigint_overflow(
    model, field: str, payload: dict[str, object], input_value: object,
) -> None:
    with pytest.raises(ValidationError):
        model.model_validate({**payload, field: input_value})


@pytest.mark.parametrize("json_value", ("true", "false", "1.0", '"1"', str(BIGINT_MAX + 1)))
@pytest.mark.parametrize("model,field,payload", VALID_INPUTS)
def test_timestamp_json_cannot_coerce_types_or_overflow(
    model, field: str, payload: dict[str, object], json_value: str,
) -> None:
    import json

    body = json.dumps({**payload, field: 1})
    key = json.dumps(field)
    body = body.replace(f"{key}: 1", f"{key}: {json_value}")
    with pytest.raises(ValidationError):
        model.model_validate_json(body)


@pytest.mark.parametrize("timestamp", (0, 1, BIGINT_MAX))
@pytest.mark.parametrize("model,field,payload", VALID_INPUTS)
def test_timestamp_accepts_full_exact_postgresql_bigint_domain(
    model, field: str, payload: dict[str, object], timestamp: int,
) -> None:
    result = model.model_validate({**payload, field: timestamp})
    assert getattr(result, field) == timestamp
    assert type(getattr(result, field)) is int


def test_optional_intent_expiry_remains_nullable() -> None:
    _, _, payload = VALID_INPUTS[1]
    result = CoordinationIntentInput.model_validate(payload)
    assert result.expires_at_ms is None
