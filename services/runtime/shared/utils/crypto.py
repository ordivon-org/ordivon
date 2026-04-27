"""
pfios.core.utils.crypto — 数值工具

quantize_down 等精度处理函数。
迁移来源：apps/api/app/utils/crypto.py + quant-agent/scripts/pipeline_core.py
"""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN


def quantize_down(value: float, step: float | None, precision: int | None = None) -> float:
    """向下舍入到指定精度。

    用于交易所下单时的价格/数量精度对齐。
    来源：quant-agent pipeline_core.quantize_down
    """
    if step and step > 0:
        decimal_value = Decimal(str(value))
        decimal_step = Decimal(str(step))
        return float((decimal_value / decimal_step).to_integral_value(rounding=ROUND_DOWN) * decimal_step)
    if precision is not None and precision >= 0:
        pattern = Decimal("1").scaleb(-precision)
        return float(Decimal(str(value)).quantize(pattern, rounding=ROUND_DOWN))
    return float(value)


def sanitize_name(name: str) -> str:
    """将符号/路径名中的特殊字符替换为下划线。

    来源：quant-agent pipeline_core.sanitize_name
    """
    return name.replace("/", "_").replace(":", "_").replace(" ", "_").replace(".", "_")
