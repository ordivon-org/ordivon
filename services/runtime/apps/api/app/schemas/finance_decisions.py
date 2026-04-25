from __future__ import annotations

from pydantic import BaseModel, Field


class FinanceDecisionIntakeRequest(BaseModel):
    symbol: str
    timeframe: str | None = None
    direction: str
    thesis: str | None = None
    entry_condition: str | None = None
    invalidation_condition: str | None = None
    stop_loss: str | None = None
    target: str | None = None
    position_size_usdt: float | None = None
    max_loss_usdt: float | None = None
    risk_unit_usdt: float | None = None
    is_revenge_trade: bool | None = None
    is_chasing: bool | None = None
    emotional_state: str | None = None
    confidence: float | None = None
    rule_exceptions: list[str] = Field(default_factory=list)
    notes: str | None = None


class DecisionIntakeValidationErrorResponse(BaseModel):
    field: str
    code: str
    message: str


class GovernanceAdvisoryHintResponse(BaseModel):
    target: str
    hint_type: str
    summary: str
    evidence_object_ids: list[str] = Field(default_factory=list)


class FinanceDecisionIntakeResponse(BaseModel):
    id: str
    pack_id: str
    intake_type: str
    status: str
    payload: dict
    validation_errors: list[DecisionIntakeValidationErrorResponse]
    governance_status: str
    advisory_hints: list[GovernanceAdvisoryHintResponse] | None = None
    created_at: str
