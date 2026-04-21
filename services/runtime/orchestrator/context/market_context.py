from dataclasses import dataclass, field


@dataclass
class MarketContext:
    symbol: str | None = None
    timeframe: str | None = None
    signals: dict = field(default_factory=dict)
