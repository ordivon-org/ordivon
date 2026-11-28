from __future__ import annotations

from typing import Any


def dump_sdk_model(value: Any) -> Any:
    """Project Binance generated SDK models into their plain Python representation."""
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [dump_sdk_model(item) for item in value]
    return value


def unwrap_sdk_oneof(value: Any) -> Any:
    """Unwrap the generated SDK's oneOf carrier after applying model projection."""
    data = dump_sdk_model(value)
    if isinstance(data, dict) and "actual_instance" in data:
        return data["actual_instance"]
    return data
