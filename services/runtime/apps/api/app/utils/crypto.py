import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN
from typing import Any

def utcnow() -> datetime:
    return datetime.now(UTC)

def utcnow_iso() -> str:
    return utcnow().isoformat()

def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def timeframe_to_ms(timeframe: str) -> int:
    unit = timeframe[-1]
    magnitude = int(timeframe[:-1])
    if unit == "m":
        return magnitude * 60 * 1000
    if unit == "h":
        return magnitude * 60 * 60 * 1000
    if unit == "d":
        return magnitude * 24 * 60 * 60 * 1000
    raise ValueError(f"Unsupported timeframe: {timeframe}")

def quantize_down(value: float, step: float | None, precision: int | None = None) -> float:
    if step and step > 0:
        decimal_value = Decimal(str(value))
        decimal_step = Decimal(str(step))
        return float((decimal_value / decimal_step).to_integral_value(rounding=ROUND_DOWN) * decimal_step)
    if precision is not None and precision >= 0:
        pattern = Decimal("1").scaleb(-precision)
        return float(Decimal(str(value)).quantize(pattern, rounding=ROUND_DOWN))
    return float(value)

def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)

def json_loads(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    return json.loads(value)
