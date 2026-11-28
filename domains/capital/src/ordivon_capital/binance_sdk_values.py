"""Pure value projection for Binance SDK response models; no client or IO."""

from __future__ import annotations

from typing import Any


def dump_sdk_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [dump_sdk_value(v) for v in value]
    return value


def unwrap_sdk_value(value: Any) -> Any:
    data = dump_sdk_value(value)
    if isinstance(data, dict) and "actual_instance" in data:
        return data["actual_instance"]
    return data
