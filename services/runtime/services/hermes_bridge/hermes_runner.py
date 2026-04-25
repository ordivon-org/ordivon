"""PFIOS Hermes Bridge — model runner via openai SDK."""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from openai import OpenAI

from services.hermes_bridge.config import (
    ALLOW_TOOLS,
    MODEL_API_KEY,
    MODEL_BASE_URL,
    MODEL_NAME,
    MODEL_PROVIDER,
)
from services.hermes_bridge.schemas import TaskOutput, TaskRequest, TaskResponse

logger = logging.getLogger(__name__)

_ANALYSIS_SYSTEM_PROMPT = """You are serving PFIOS / Ordivon analysis.generate.
You are a disciplined financial risk analyst.

Return ONLY valid JSON. Do NOT include Markdown. Do NOT include code fences.
Do NOT suggest executing trades. Do NOT call tools. Do NOT run commands.
Do NOT modify files. Do NOT mention that you are an AI.

Required JSON schema:
{
  "summary": "string — concise executive summary of the analysis",
  "thesis": "string — the core analytical thesis",
  "risks": ["string — specific risk factor", ...],
  "suggested_actions": ["string — actionable next step (not trade execution)", ...]
}

Rules:
- summary must be 2-4 sentences.
- thesis must state a clear directional view with reasoning.
- risks must be specific and meaningful (no generic placeholder).
- suggested_actions must be concrete (observe, wait, reassess, gather data)
  but NEVER actual buy/sell/trade order suggestions.
- If insufficient data, state that honestly in the thesis."""


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences that some models insist on emitting."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_analysis(task: TaskRequest) -> TaskResponse:
    """Execute an analysis.generate task against the configured model."""
    started_at = _utc_now_iso()
    trace_id = f"bridge-{uuid.uuid4().hex[:12]}"
    session_id = f"bridge-sess-{uuid.uuid4().hex[:8]}"

    if not MODEL_API_KEY:
        return TaskResponse(
            status="failed",
            task_id=task.task_id,
            task_type=task.task_type,
            error="bridge_not_configured: MODEL_API_KEY is empty",
            started_at=started_at,
            completed_at=_utc_now_iso(),
        )

    client = OpenAI(base_url=MODEL_BASE_URL, api_key=MODEL_API_KEY)

    user_prompt = _build_user_prompt(task)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
            tools=None if not ALLOW_TOOLS else [],
        )
    except Exception as exc:
        logger.exception("Model call failed for task %s", task.task_id)
        return TaskResponse(
            status="failed",
            task_id=task.task_id,
            task_type=task.task_type,
            provider=MODEL_PROVIDER,
            model=MODEL_NAME,
            session_id=session_id,
            trace_id=trace_id,
            error=f"model_call_failed: {exc}",
            started_at=started_at,
            completed_at=_utc_now_iso(),
        )

    raw_text = completion.choices[0].message.content or ""
    usage = {}
    if completion.usage:
        usage = {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens,
        }

    output = _parse_output(raw_text)
    completed_at = _utc_now_iso()

    if output is None:
        return TaskResponse(
            status="failed",
            task_id=task.task_id,
            task_type=task.task_type,
            provider=MODEL_PROVIDER,
            model=MODEL_NAME,
            session_id=session_id,
            trace_id=trace_id,
            tool_trace=[],
            usage=usage,
            error="invalid_json_output",
            started_at=started_at,
            completed_at=completed_at,
        )

    return TaskResponse(
        status="completed",
        task_id=task.task_id,
        task_type=task.task_type,
        output=output,
        provider=MODEL_PROVIDER,
        model=MODEL_NAME,
        session_id=session_id,
        trace_id=trace_id,
        tool_trace=[],
        usage=usage,
        started_at=started_at,
        completed_at=completed_at,
    )


def _build_user_prompt(task: TaskRequest) -> str:
    symbol = task.input.symbol or "UNKNOWN"
    timeframe = task.input.timeframe or "N/A"
    query = task.input.query
    risk_mode = task.input.risk_mode or "normal"

    return (
        f"Symbol: {symbol}\n"
        f"Timeframe: {timeframe}\n"
        f"Risk mode: {risk_mode}\n"
        f"Query: {query}\n\n"
        f"Analyze the above and return ONLY the JSON object with summary, thesis, risks, and suggested_actions."
    )


def _parse_output(raw: str) -> TaskOutput | None:
    cleaned = _strip_json_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse model output as JSON: %.200s", raw)
        return None

    if not isinstance(data, dict):
        return None

    summary = str(data.get("summary", "")).strip()
    thesis = str(data.get("thesis", "")).strip()
    risks = data.get("risks", [])
    suggested_actions = data.get("suggested_actions", [])

    if not isinstance(risks, list):
        risks = []
    if not isinstance(suggested_actions, list):
        suggested_actions = []

    risks = [str(r) for r in risks if r]
    suggested_actions = [str(a) for a in suggested_actions if a]

    if not summary or not thesis:
        return None

    return TaskOutput(
        summary=summary,
        thesis=thesis,
        risks=risks,
        suggested_actions=suggested_actions,
    )
