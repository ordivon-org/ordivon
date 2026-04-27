from shared.errors.domain import InvalidStateTransition


ALLOWED_INTELLIGENCE_RUN_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}


class IntelligenceRunStateMachine:
    def can_transition(self, current: str, target: str) -> bool:
        return target in ALLOWED_INTELLIGENCE_RUN_TRANSITIONS.get(current, set())

    def ensure_transition(self, current: str, target: str) -> None:
        if not self.can_transition(current, target):
            raise InvalidStateTransition(f"Invalid intelligence run transition: {current} -> {target}")
