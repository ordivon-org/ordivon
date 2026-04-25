from __future__ import annotations

import logging

from domains.research.models import AnalysisResult
from infra.cache.llm_cache import build_llm_cache_key, get_cached_llm_response, set_cached_llm_response
from intelligence.runtime.base import AgentRuntime, RuntimeDescriptor
from intelligence.runtime.hermes_client import HermesClient, HermesRuntimeError
from intelligence.tasks import build_analysis_task, normalize_analysis_output
from intelligence.tasks.contracts import IntelligenceTaskRequest
from orchestrator.context.context_builder import AnalysisContext
from shared.config.settings import settings

logger = logging.getLogger(__name__)


class HermesRuntime(AgentRuntime):
    def __init__(self, client: HermesClient | None = None) -> None:
        self.client = client or HermesClient()

    @property
    def descriptor(self) -> RuntimeDescriptor:
        return RuntimeDescriptor(
            runtime_name="agent_runtime",
            provider_name="hermes",
            adapter_name="adapters.runtimes.hermes.runtime.HermesRuntime",
        )

    def health(self) -> dict:
        return self.client.health_check()

    def supports_memory_policy(self) -> bool:
        return True

    def supports_progress(self) -> bool:
        return False

    def analyze(self, ctx: AnalysisContext, request: IntelligenceTaskRequest | None = None) -> AnalysisResult:
        request = request or build_analysis_task(ctx)

        # ── cache lookup (feature-flagged, safe-fallback) ──
        cache_key: str | None = None
        if settings.llm_cache_enabled:
            cache_key = _build_cache_key_from_request(request)
            if cache_key:
                try:
                    cached_response = get_cached_llm_response(cache_key)
                except Exception:
                    cached_response = None

                if cached_response is not None:
                    logger.debug("LLM cache hit for key %s", cache_key)
                    return _result_from_cached_response(
                        request=request,
                        cached_response=cached_response,
                        cache_key=cache_key,
                        runtime=self,
                    )

        # ── original path — call Hermes ──
        try:
            response = self.client.run_task("analysis.generate", request.to_payload())
        except HermesRuntimeError as exc:
            exc.task_id = request.task_id
            exc.trace_id = request.trace_id
            exc.request_payload = request.to_payload()
            raise

        # ── cache store (only on success; errors not cached) ──
        if cache_key:
            try:
                set_cached_llm_response(cache_key, _response_to_cache_dict(response))
            except Exception:
                logger.debug("LLM cache store failed for key %s", cache_key, exc_info=True)

        return _result_from_live_response(request, response, self)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _build_cache_key_from_request(request: IntelligenceTaskRequest) -> str | None:
    """Build a deterministic cache key from an IntelligenceTaskRequest.

    Returns None if the payload contains secrets (auth headers, tokens, etc.).
    """
    payload = request.to_payload()
    # Safety: refuse to cache if auth/material secrets appear in payload.
    sensitive_keys = {"authorization", "api_key", "api_token", "cookie", "token", "secret"}
    if any(k in payload for k in sensitive_keys):
        logger.warning("Refusing to build cache key — payload contains sensitive key(s).")
        return None

    return build_llm_cache_key(
        provider=request.context_refs.provider,
        model=request.context_refs.model,
        task_type="analysis.generate",
        query=request.input.query,
        symbol=request.input.symbol,
        timeframe=request.input.timeframe,
        risk_mode=request.input.risk_mode,
        market_signals=request.input.market_signals,
        memory_lessons=request.input.memory_lessons,
        related_reviews=request.input.related_reviews,
        active_policies=request.input.active_policies,
        portfolio_snapshot=_portfolio_snapshot_from_request(request),
        prompt_version=None,
    )


def _portfolio_snapshot_from_request(request: IntelligenceTaskRequest) -> dict | None:
    cash = request.input.portfolio_cash_balance
    positions = request.input.portfolio_positions
    if cash is None and not positions:
        return None
    return {"cash_balance": cash, "positions": positions}


def _response_to_cache_dict(response: dict) -> dict:
    """Strip the Hermes response down to the cacheable fields.

    We intentionally omit tool_trace, memory_events, delegation_trace, and
    usage to keep the cached payload small and free of execution-specific data.
    """
    return {
        "cache_schema_version": "1",
        "status": response.get("status"),
        "task_id": response.get("task_id"),
        "task_type": response.get("task_type"),
        "provider": response.get("provider"),
        "model": response.get("model"),
        "session_id": response.get("session_id"),
        "trace_id": response.get("trace_id"),
        "output": response.get("output"),
    }


def _result_from_cached_response(
    *,
    request: IntelligenceTaskRequest,
    cached_response: dict,
    cache_key: str,
    runtime: HermesRuntime,
) -> AnalysisResult:
    """Construct an AnalysisResult from a cached Hermes response.

    Replays normalize_analysis_output so the downstream workflow steps
    receive the same structure as a live response.
    """
    normalized = normalize_analysis_output(request, cached_response)
    descriptor = runtime.descriptor
    return AnalysisResult(
        summary=normalized.summary,
        thesis=normalized.thesis,
        risks=normalized.risks,
        suggested_actions=normalized.suggested_actions,
        metadata=normalized.metadata.__dict__
        | {
            "agent_action": normalized.agent_action.__dict__,
            "runtime_name": descriptor.runtime_name,
            "runtime_adapter": descriptor.adapter_name,
            "cache_hit": True,
            "cache_key": cache_key,
        },
    )


def _result_from_live_response(
    request: IntelligenceTaskRequest,
    response: dict,
    runtime: HermesRuntime,
) -> AnalysisResult:
    """Construct an AnalysisResult from a live Hermes response (the original path)."""
    normalized = normalize_analysis_output(request, response)
    descriptor = runtime.descriptor
    return AnalysisResult(
        summary=normalized.summary,
        thesis=normalized.thesis,
        risks=normalized.risks,
        suggested_actions=normalized.suggested_actions,
        metadata=normalized.metadata.__dict__
        | {
            "agent_action": normalized.agent_action.__dict__,
            "runtime_name": descriptor.runtime_name,
            "runtime_adapter": descriptor.adapter_name,
        },
    )
