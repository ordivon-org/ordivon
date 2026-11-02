from __future__ import annotations

from typing import Any

from .execution_refs import GatewayError
from .upstream import OwnerToolCaller


def _configured(caller: OwnerToolCaller, owner_id: str) -> bool:
    probe = getattr(caller, "is_configured", None)
    if callable(probe):
        return bool(probe(owner_id))
    return True


def _configuration_error(caller: OwnerToolCaller, owner_id: str) -> str | None:
    probe = getattr(caller, "configuration_error", None)
    if callable(probe):
        value = probe(owner_id)
        return str(value) if value else None
    return None


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise GatewayError(f"owner response omitted {key}")
    return value


def _required_bool(payload: dict[str, Any], key: str) -> bool:
    """Runtime is the physical state owner; reject non-JSON-boolean terminality."""
    value = payload.get(key)
    if type(value) is not bool:
        raise GatewayError(f"Runtime owner response requires boolean {key}")
    return value
