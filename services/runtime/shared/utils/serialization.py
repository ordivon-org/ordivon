import json
from typing import Any


def to_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def from_json_text(value: str | None, default: Any):
    if value is None or value == "":
        return default
    return json.loads(value)
