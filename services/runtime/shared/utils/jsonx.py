"""
pfios.core.utils.jsonx — JSON 工具

统一的 JSON 序列化/反序列化策略。
迁移来源：quant-agent/scripts/pipeline_core.py
"""

from __future__ import annotations

import json
from typing import Any


def json_dumps(value: Any) -> str:
    """确定性 JSON 序列化（排序 keys，ASCII 安全）。"""
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def json_dumps_pretty(value: Any) -> str:
    """格式化 JSON 输出（用于报告/日志）。"""
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def json_loads(value: str | None, default: Any = None) -> Any:
    """安全的 JSON 反序列化（空值/异常时返回默认值）。"""
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default
