from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FinanceToolRefs:
    market_data: tuple[str, ...]
    news_data: tuple[str, ...]
    broker: tuple[str, ...]


def get_finance_tool_refs() -> FinanceToolRefs:
    return FinanceToolRefs(
        market_data=("tools.market_data",),
        news_data=("tools.news_data",),
        broker=("tools.broker",),
    )
