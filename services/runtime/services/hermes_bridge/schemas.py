"""PFIOS Hermes Bridge — request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TaskInput(BaseModel):
    query: str
    symbol: str | None = None
    timeframe: str | None = None
    market_signals: dict[str, Any] = {}
    memory_lessons: list[Any] = []
    related_reviews: list[Any] = []
    active_policies: list[Any] = []
    risk_mode: str | None = None
    portfolio_cash_balance: float | int | None = None
    portfolio_positions: list[dict[str, Any]] = []


class TaskContextRefs(BaseModel):
    provider: str = "deepseek"
    model: str = "deepseek-v4-pro"


class TaskConstraints(BaseModel):
    must_return_fields: list[str] = ["summary", "thesis", "risks", "suggested_actions"]


class TaskExecutionPolicy(BaseModel):
    enable_delegation: bool = False
    enable_memory: bool = False
    enable_moa: bool = False


class TaskRequest(BaseModel):
    task_type: str
    task_id: str
    input: TaskInput
    context_refs: TaskContextRefs = TaskContextRefs()
    constraints: TaskConstraints = TaskConstraints()
    execution_policy: TaskExecutionPolicy = TaskExecutionPolicy()


class TaskOutput(BaseModel):
    summary: str
    thesis: str
    risks: list[str]
    suggested_actions: list[str]


class TaskResponse(BaseModel):
    status: str  # "completed" | "failed"
    task_id: str
    task_type: str
    output: TaskOutput | None = None
    provider: str | None = None
    model: str | None = None
    session_id: str | None = None
    trace_id: str | None = None
    tool_trace: list[dict[str, Any]] = []
    usage: dict[str, Any] = {}
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    bridge: str = "pfios-hermes-bridge"
    bridge_version: str = "0.1.0"
    hermes_binary: str = "/root/.local/bin/hermes"
    provider: str = "deepseek"
    model: str = "deepseek-v4-pro"
    tools_enabled: bool = False
