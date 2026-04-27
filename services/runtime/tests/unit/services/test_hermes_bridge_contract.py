"""H-1C: Bridge Contract Hardening — contract tests for services/hermes_bridge.

All tests mock run_analysis to avoid real DeepSeek API calls.
No business code modifications. No Hermes Agent upstream changes.
"""

from fastapi.testclient import TestClient

from services.hermes_bridge import config as bridge_config
from services.hermes_bridge.app import app
from services.hermes_bridge.schemas import TaskOutput, TaskResponse


def _valid_task_payload(task_type="analysis.generate"):
    return {
        "task_type": task_type,
        "task_id": "task_test_001",
        "input": {
            "query": "Analyze BTC/USDT 1h",
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "risk_mode": "normal",
        },
    }


def _fake_completed_run(task):
    return TaskResponse(
        status="completed",
        task_id=task.task_id,
        task_type=task.task_type,
        output=TaskOutput(
            summary="Bullish momentum with caution.",
            thesis="BTC shows strong support at 62k with increasing volume.",
            risks=["regulatory news spike", "thin weekend liquidity"],
            suggested_actions=["monitor support at 62k", "wait for volume confirmation"],
        ),
        provider="deepseek",
        model="deepseek-v4-pro",
        session_id="sess_test",
        trace_id="trace_test",
        tool_trace=[],
        usage={"total_tokens": 150},
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:01+00:00",
    )


def _fake_failed_run(task):
    return TaskResponse(
        status="failed",
        task_id=task.task_id,
        task_type=task.task_type,
        provider="deepseek",
        model="deepseek-v4-pro",
        session_id="sess_test",
        trace_id="trace_test",
        tool_trace=[],
        usage={},
        error="invalid_json_output",
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:01+00:00",
    )


# ── 1. Health ────────────────────────────────────────────────────────


def test_health_returns_provider_and_model():
    """GET /pfios/v1/health returns 200 with provider/model/tools_enabled=False."""
    client = TestClient(app)
    response = client.get("/pfios/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["bridge"] == "pfios-hermes-bridge"
    assert payload["provider"] == "deepseek"
    assert payload["model"] == "deepseek-v4-pro"
    assert payload["tools_enabled"] is False


def test_health_tools_explicitly_disabled():
    """Health response must confirm tools are disabled."""
    client = TestClient(app)
    response = client.get("/pfios/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["tools_enabled"] is False, (
        "Bridge contract violation: tools must never be enabled. "
        "H-1 is 'One Real Model Under Control', not agent autonomy."
    )


# ── 2. Successful task ───────────────────────────────────────────────


def test_tasks_analysis_generate_success(monkeypatch):
    """POST /pfios/v1/tasks with task_type=analysis.generate returns completed."""
    monkeypatch.setattr(
        "services.hermes_bridge.app.run_analysis",
        _fake_completed_run,
    )

    client = TestClient(app)
    response = client.post("/pfios/v1/tasks", json=_valid_task_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["task_id"] == "task_test_001"
    assert payload["task_type"] == "analysis.generate"
    assert payload["provider"] == "deepseek"
    assert payload["model"] == "deepseek-v4-pro"

    output = payload["output"]
    assert output is not None
    assert "Bullish" in output["summary"]
    assert "BTC" in output["thesis"]
    assert len(output["risks"]) >= 1
    assert len(output["suggested_actions"]) >= 1

    # Contract invariant: bridge never returns tool_trace entries
    assert payload["tool_trace"] == []


# ── 3. Unsupported task_type ─────────────────────────────────────────


def test_tasks_unsupported_task_type():
    """POST /pfios/v1/tasks with unsupported task_type must fail with 400."""
    payload = _valid_task_payload(task_type="analysis.unknown")

    client = TestClient(app)
    response = client.post("/pfios/v1/tasks", json=payload)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "unsupported" in detail.lower()
    assert "analysis.unknown" in detail


def test_tasks_empty_task_type():
    """POST with empty task_type must be rejected."""
    payload = _valid_task_payload(task_type="")

    client = TestClient(app)
    response = client.post("/pfios/v1/tasks", json=payload)

    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_tasks_non_analysis_task_type():
    """POST with a plausible but unsupported task_type (e.g. execution.run)
    must be rejected, proving the bridge is NOT a general-purpose agent."""
    payload = _valid_task_payload(task_type="execution.run")

    client = TestClient(app)
    response = client.post("/pfios/v1/tasks", json=payload)

    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


# ── 4. Auth rejection ────────────────────────────────────────────────


def test_health_rejects_missing_auth(monkeypatch):
    """When BRIDGE_API_TOKEN is set, missing Authorization header → 401."""
    monkeypatch.setattr(
        "services.hermes_bridge.app.BRIDGE_API_TOKEN",
        "test-secret-token",
    )

    client = TestClient(app)
    response = client.get("/pfios/v1/health")

    assert response.status_code == 401


def test_tasks_rejects_missing_auth(monkeypatch):
    """When BRIDGE_API_TOKEN is set, POST without auth → 401."""
    monkeypatch.setattr(
        "services.hermes_bridge.app.BRIDGE_API_TOKEN",
        "test-secret-token",
    )

    client = TestClient(app)
    response = client.post("/pfios/v1/tasks", json=_valid_task_payload())

    assert response.status_code == 401


def test_health_rejects_wrong_bearer_token(monkeypatch):
    """When BRIDGE_API_TOKEN is set, wrong Bearer token → 401."""
    monkeypatch.setattr(
        "services.hermes_bridge.app.BRIDGE_API_TOKEN",
        "test-secret-token",
    )

    client = TestClient(app)
    response = client.get(
        "/pfios/v1/health",
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401


def test_tasks_rejects_wrong_bearer_token(monkeypatch):
    """When BRIDGE_API_TOKEN is set, wrong Bearer token → 401."""
    monkeypatch.setattr(
        "services.hermes_bridge.app.BRIDGE_API_TOKEN",
        "test-secret-token",
    )

    client = TestClient(app)
    response = client.post(
        "/pfios/v1/tasks",
        json=_valid_task_payload(),
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert response.status_code == 401


def test_health_accepts_valid_bearer_token(monkeypatch):
    """When BRIDGE_API_TOKEN is set, correct Bearer token → 200."""
    monkeypatch.setattr(
        "services.hermes_bridge.app.BRIDGE_API_TOKEN",
        "test-secret-token",
    )

    client = TestClient(app)
    response = client.get(
        "/pfios/v1/health",
        headers={"Authorization": "Bearer test-secret-token"},
    )

    assert response.status_code == 200


# ── 5. Invalid model output must fail, not fake completed ────────────


def test_tasks_failed_model_output_is_not_completed(monkeypatch):
    """When run_analysis returns status=failed (e.g. invalid JSON),
    the /tasks endpoint must NOT return status=completed."""
    monkeypatch.setattr(
        "services.hermes_bridge.app.run_analysis",
        _fake_failed_run,
    )

    client = TestClient(app)
    response = client.post("/pfios/v1/tasks", json=_valid_task_payload())

    assert response.status_code == 200
    payload = response.json()
    # The /tasks endpoint returns the TaskResponse as-is; if run_analysis
    # says "failed", the endpoint must reflect that honestly.
    assert payload["status"] == "failed", (
        "Contract violation: failed model output MUST NOT be reported as 'completed'. "
        "Actual status: %s" % payload.get("status")
    )
    assert payload["error"] == "invalid_json_output"
    assert payload["output"] is None
    # Even on failure, tool_trace must remain empty
    assert payload["tool_trace"] == []


def test_tasks_failed_output_has_no_summary(monkeypatch):
    """Failed task must not leak a fake summary — output must be None."""
    monkeypatch.setattr(
        "services.hermes_bridge.app.run_analysis",
        _fake_failed_run,
    )

    client = TestClient(app)
    response = client.post("/pfios/v1/tasks", json=_valid_task_payload())

    payload = response.json()
    assert payload["output"] is None, (
        "Failed tasks must not carry output — this prevents downstream "
        "consumers from treating garbage as valid analysis."
    )


# ── 6. Config safety flags ───────────────────────────────────────────


def test_config_safety_flags_all_false():
    """ALLOW_TOOLS, ALLOW_FILE_WRITE, ALLOW_SHELL must all be False.
    This is a hard invariant for H-1: 'One Real Model Under Control' —
    the bridge owns the model, the model does not own tools."""
    assert bridge_config.ALLOW_TOOLS is False, (
        "H-1 safety violation: ALLOW_TOOLS must be False. The bridge is an analysis adapter, not an agent harness."
    )
    assert bridge_config.ALLOW_FILE_WRITE is False, "H-1 safety violation: ALLOW_FILE_WRITE must be False."
    assert bridge_config.ALLOW_SHELL is False, "H-1 safety violation: ALLOW_SHELL must be False."


# ── 7. Contract: bridge does not participate in LLM cache ────────────


def test_bridge_has_no_llm_cache_config():
    """The bridge config must not expose llm_cache_enabled.
    LLM cache is an Ordivon concern (R-3B), not a bridge concern."""
    assert not hasattr(bridge_config, "LLM_CACHE_ENABLED"), (
        "llm_cache_enabled does not belong in bridge config. Cache decisions live in Ordivon, not in the bridge."
    )
    assert not hasattr(bridge_config, "llm_cache_enabled"), "llm_cache_enabled does not belong in bridge config."
