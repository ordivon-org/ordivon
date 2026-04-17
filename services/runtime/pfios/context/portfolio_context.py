from dataclasses import dataclass, field


@dataclass
class PortfolioContext:
    positions: list[dict] = field(default_factory=list)
    cash_balance: float = 0.0
