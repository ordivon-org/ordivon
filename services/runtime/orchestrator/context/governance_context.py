from dataclasses import dataclass, field


@dataclass
class GovernanceContext:
    active_policies: list[str] = field(default_factory=list)
    risk_mode: str = "normal"
