from typing import List

from pydantic import BaseModel, Field, field_validator

from packs.finance.analyze_profile import DEFAULT_FINANCE_TIMEFRAME, SUPPORTED_FINANCE_TIMEFRAMES


class AnalyzeRequest(BaseModel):
    query: str
    symbols: List[str] = []
    timeframe: str | None = Field(default=DEFAULT_FINANCE_TIMEFRAME)
    context_mode: str = "standard"
    workflow: str = "analyze_and_suggest"

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, value: str | None) -> str | None:
        if value is None or value in SUPPORTED_FINANCE_TIMEFRAMES:
            return value
        raise ValueError(f"timeframe must be one of: {', '.join(SUPPORTED_FINANCE_TIMEFRAMES)}")
