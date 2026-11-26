"""Gateway MCP wire protocol and result identity, without effect ownership.

The single decoder rejects conflicting snake_case/camelCase source aliases.
It has no remote client, durable Run state or permission decision.
"""

from __future__ import annotations

from anc_canonical import JsonValue, canonical_digest, validate_json_value
from .runtime_port import HarnessRuntimeClientError


def _tool_digest(raw: dict[str, JsonValue]) -> str:
    value = {
        "name": raw.get("name"),
        "description": raw.get("description"),
        "inputSchema": raw.get("inputSchema"),
        "outputSchema": raw.get("outputSchema"),
    }
    validate_json_value(value)
    return canonical_digest(value)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise HarnessRuntimeClientError(f"Gateway {label} is missing")
    return value


def _gateway_field(payload: dict[str, JsonValue], snake: str, camel: str) -> JsonValue | None:
    # A single source observation must not express two contradictory facts
    # merely by including both valid wire spellings. All four Gateway
    # execution endpoints share this one decoder; no extra state/authority.
    if snake in payload and camel in payload:
        primary, secondary = payload[snake], payload[camel]
        # JSON boolean and integer tokens never mean the same thing:
        # Python's False == 0 / True == 1 cannot stand in as wire identity.
        if type(primary) is not type(secondary) or primary != secondary:
            raise HarnessRuntimeClientError(
                f"Gateway {snake}/{camel} has conflicting source aliases"
            )
    if snake in payload:
        return payload[snake]
    return payload.get(camel)


_GATEWAY_DELIVERY_DISPOSITIONS = frozenset(
    {"committed", "reconciliation_required", "unknown", "in_progress"}
)
# Only these physical Runtime outcomes can support a committed result. Lost or
# orphaned are distinct UNKNOWN states; the Gateway cannot turn them into a
# successful Tool observation by asserting artifact_projection_complete.
_GATEWAY_CONCLUSIVE_EXECUTION_RESOLUTIONS = frozenset(
    {"succeeded", "failed", "timed_out", "cancelled"}
)


def _gateway_delivery_disposition(
    payload: dict[str, JsonValue], *, allow_missing: bool = False
) -> str:
    """Read a source-owned delivery enum without a raw TypeError or fallback.

    Gateway's nonterminal submit receipt has an optional disposition, for
    which the established source default is in_progress. Terminal observation
    requires a real Owner delivery value; malformed presence is never absence.
    """
    value = _gateway_field(payload, "delivery_disposition", "deliveryDisposition")
    if value is None and allow_missing:
        return "in_progress"
    if not isinstance(value, str) or value not in _GATEWAY_DELIVERY_DISPOSITIONS:
        raise HarnessRuntimeClientError("Gateway deliveryDisposition is missing or invalid")
    return value
