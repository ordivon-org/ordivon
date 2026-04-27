"""ADR-006: Finance Pack Trading Discipline Policy.

All H-5/H-9C gate logic extracted from Core RiskEngine.
Core only delegates — it never knows about stop_loss, is_chasing, etc.
"""

from __future__ import annotations

# ── Reason types (mirror RiskEngine's reject/escalate distinction) ────


class RejectReason:
    def __init__(self, message: str) -> None:
        self.message = message


class EscalateReason:
    def __init__(self, message: str) -> None:
        self.message = message


# ── Constants (from RiskEngine engine.py + thesis_quality.py) ─────────

_MAX_LOSS_TO_RISK_UNIT_RATIO = 2.0
_MAX_POSITION_TO_RISK_UNIT_RATIO = 10.0

_EMOTIONAL_RISK_KEYWORDS: frozenset[str] = frozenset(
    {
        "stress",
        "stressed",
        "stressful",
        "fear",
        "fearful",
        "scared",
        "terrified",
        "panicked",
        "panic",
        "anger",
        "angry",
        "furious",
        "frustrated",
        "fomo",
        "greedy",
        "desperate",
        "reckless",
        "revenge",
        "impulsive",
    }
)

_BANNED_THESIS_PATTERNS: tuple[str, ...] = (
    "just feels right",
    "feels right",
    "looks good",
    "probably pump",
    "should go up",
    "should go down",
    "vibes",
    "no specific thesis",
    "trust me",
    "yolo",
    "because i said so",
    "i think so",
    "let's see",
    "we'll see",
    "who knows",
    "idk",
    "just a hunch",
    "gut feeling",
    "hoping for",
    "praying for",
)

_INVALIDATION_WORDS: tuple[str, ...] = (
    "unless",
    "invalid",
    "invalidate",
    "falsif",
    "if not",
    "stop if",
    "exit if",
    "cut if",
)

_CONFIRMATION_WORDS: tuple[str, ...] = (
    "confirm",
    "confirmed when",
    "verif",
    "must hold",
    "must close",
    "needs to",
    "requires",
)


class TradingDisciplinePolicy:
    """Finance Pack intake policy — all H-5 gate rules.

    Extracted from Core RiskEngine per ADR-006.
    """

    # ── Gate 1: Field existence + thesis quality ──────────────────────

    def validate_fields(self, payload: dict) -> list[RejectReason | EscalateReason]:
        reasons: list[RejectReason | EscalateReason] = []

        thesis = _as_str(payload.get("thesis"))
        if not thesis:
            reasons.append(RejectReason("Missing required field: thesis."))
        else:
            lowered = thesis.lower()
            for banned in _BANNED_THESIS_PATTERNS:
                if banned in lowered:
                    reasons.append(RejectReason(f"Thesis quality rejected: {banned}."))
                    break
            if len(thesis.strip()) < 50:
                reasons.append(
                    EscalateReason(
                        f"Thesis is too short ({len(thesis.strip())} chars, minimum 50) — requires human review."
                    )
                )
            if not _has_verifiability(thesis):
                reasons.append(
                    EscalateReason(
                        "Thesis lacks verifiability criteria (no invalidation "
                        "or confirmation conditions) — requires human review."
                    )
                )

        stop_loss = _as_str(payload.get("stop_loss"))
        if not stop_loss:
            reasons.append(RejectReason("Missing required field: stop_loss."))

        emotional_state = _as_str(payload.get("emotional_state"))
        if not emotional_state:
            reasons.append(RejectReason("Missing required field: emotional_state."))

        return reasons

    # ── Gate 2: Numeric fields ────────────────────────────────────────

    def validate_numeric(self, payload: dict) -> list[RejectReason]:
        reasons: list[RejectReason] = []

        max_loss = _as_positive_float(payload.get("max_loss_usdt"))
        if max_loss is None:
            reasons.append(RejectReason("Missing or non-positive field: max_loss_usdt."))

        position_size = _as_positive_float(payload.get("position_size_usdt"))
        if position_size is None:
            reasons.append(RejectReason("Missing or non-positive field: position_size_usdt."))

        risk_unit = _as_positive_float(payload.get("risk_unit_usdt"))
        if risk_unit is None:
            reasons.append(RejectReason("Missing or non-positive field: risk_unit_usdt."))

        return reasons

    # ── Gate 3: Risk limit ratios ─────────────────────────────────────

    def validate_limits(self, payload: dict) -> list[RejectReason]:
        reasons: list[RejectReason] = []

        max_loss = _as_positive_float(payload.get("max_loss_usdt"))
        position_size = _as_positive_float(payload.get("position_size_usdt"))
        risk_unit = _as_positive_float(payload.get("risk_unit_usdt"))

        if max_loss is not None and risk_unit is not None and risk_unit > 0:
            if max_loss > _MAX_LOSS_TO_RISK_UNIT_RATIO * risk_unit:
                reasons.append(
                    RejectReason(
                        f"max_loss_usdt ({max_loss}) exceeds "
                        f"{_MAX_LOSS_TO_RISK_UNIT_RATIO}× risk_unit_usdt "
                        f"({risk_unit}), max allowed: "
                        f"{_MAX_LOSS_TO_RISK_UNIT_RATIO * risk_unit}."
                    )
                )

        if position_size is not None and risk_unit is not None and risk_unit > 0:
            if position_size > _MAX_POSITION_TO_RISK_UNIT_RATIO * risk_unit:
                reasons.append(
                    RejectReason(
                        f"position_size_usdt ({position_size}) exceeds "
                        f"{_MAX_POSITION_TO_RISK_UNIT_RATIO}× risk_unit_usdt "
                        f"({risk_unit}), max allowed: "
                        f"{_MAX_POSITION_TO_RISK_UNIT_RATIO * risk_unit}."
                    )
                )

        return reasons

    # ── Gate 4: Behavioral red flags ──────────────────────────────────

    def validate_behavioral(self, payload: dict) -> list[EscalateReason]:
        reasons: list[EscalateReason] = []

        if payload.get("is_revenge_trade") is True:
            reasons.append(EscalateReason("is_revenge_trade=true — requires human review."))

        if payload.get("is_chasing") is True:
            reasons.append(EscalateReason("is_chasing=true — requires human review."))

        emotional = _as_str(payload.get("emotional_state"))
        if emotional and _contains_emotional_risk(emotional):
            reasons.append(
                EscalateReason(f"emotional_state='{emotional}' indicates elevated risk — requires human review.")
            )

        rule_exceptions = payload.get("rule_exceptions")
        if isinstance(rule_exceptions, list) and len(rule_exceptions) > 0:
            reasons.append(
                EscalateReason(f"rule_exceptions not empty ({len(rule_exceptions)} item(s)) — requires human review.")
            )

        confidence = payload.get("confidence")
        if isinstance(confidence, (int, float)) and 0 <= confidence < 0.3:
            reasons.append(EscalateReason(f"confidence={confidence} is below 0.3 threshold — requires human review."))

        return reasons


# ── Private helpers (from RiskEngine) ─────────────────────────────────


def _as_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _as_positive_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _contains_emotional_risk(emotional_state: str) -> bool:
    lowered = emotional_state.lower()
    return any(keyword in lowered for keyword in _EMOTIONAL_RISK_KEYWORDS)


def _has_verifiability(thesis: str) -> bool:
    """Check if thesis contains invalidation or confirmation language."""
    lowered = thesis.lower()
    has_invalidation = any(w in lowered for w in _INVALIDATION_WORDS)
    has_confirmation = any(w in lowered for w in _CONFIRMATION_WORDS)
    return has_invalidation or has_confirmation
