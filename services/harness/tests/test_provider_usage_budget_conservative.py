"""Regression: contradictory Provider usage must not silently undercharge a Run.

The historical original-PG PAUSED-resume consumer is validated separately;
these tests guard the pure normalizer used by fresh and reopened Runs.
"""
from __future__ import annotations

import pytest

from ordivon_harness.ordivon.loop import _usage_total_tokens


@pytest.mark.parametrize(
    ("usage", "expected"),
    [
        ({"total_tokens": 0, "input_tokens": 90, "output_tokens": 60}, 150),
        ({"totalTokens": 1, "promptTokens": 20, "completionTokens": 7}, 27),
        ({"total_tokens": 1, "totalTokens": 9, "input_tokens": 4, "output_tokens": 5}, 9),
        ({"total_tokens": False, "input_tokens": 3, "output_tokens": 4}, 7),
        ({"total_tokens": -5, "totalTokens": -1}, None),
        ({"input_tokens": 5}, None),
        ({"prompt_tokens": 4, "promptTokens": 9, "completion_tokens": 2, "completionTokens": 7}, 16),
        ({"inputTokens": 3, "outputTokens": 0, "cached_tokens": 200}, 3),
        ({}, None),
    ],
)
def test_provider_usage_reconciles_only_complete_nonnegative_counters(usage, expected):
    assert _usage_total_tokens(usage) == expected


@pytest.mark.skipif(
    not __import__("os").environ.get("HARNESS_PG_TEST_DSN"),
    reason="requires isolated original PostgreSQL test authority",
)
def test_original_pg_public_run_budget_rejects_contradictory_usage() -> None:
    """An actual PG Run cannot PAUSE with an undercharged Provider Call."""
    from dataclasses import replace

    from tests.pg_test_support import isolated_harness_schema
    from tests.test_r3_supported_agent_run import FixedClock, contract, needs_input
    from ordivon_harness.agent_run import HarnessAgentRun
    from ordivon_harness.ordivon.model import ScriptedTurnAdapter

    with isolated_harness_schema() as (dsn, schema):
        original = contract("r17-contradictory-usage-fresh")
        bounded = replace(original, budget={**original.budget, "maxTotalTokens": 50})
        turn = replace(
            needs_input("model-call:r17-contradictory-fresh"),
            usage={"total_tokens": 0, "input_tokens": 90, "output_tokens": 60},
        )
        clock = FixedClock()
        run = HarnessAgentRun.create(
            dsn, schema, bounded, lambda _: ScriptedTurnAdapter((turn,)),
            clock_ms=clock, monotonic_ms=clock,
        )
        result = run.run(({"role": "user", "content": "test budget"},))
        assert result.loop_result.stop_code.value == "budget_exhausted"
        assert not result.paused
        assert run.doctor()["healthy"] is True


@pytest.mark.skipif(
    not __import__("os").environ.get("HARNESS_PG_TEST_DSN"),
    reason="requires isolated original PostgreSQL test authority",
)
def test_original_pg_reopen_reconciles_historical_undercharge_before_provider_call() -> None:
    """A historical PAUSED total=0 cannot authorize another model effect."""
    from dataclasses import replace
    from unittest.mock import patch

    from tests.pg_test_support import isolated_harness_schema
    from tests.test_r3_supported_agent_run import FixedClock, completed, contract, needs_input
    from ordivon_harness.agent_run import HarnessAgentRun
    from ordivon_harness.ordivon.model import ScriptedTurnAdapter

    with isolated_harness_schema() as (dsn, schema):
        original = contract("r17-contradictory-usage-reopen")
        bounded = replace(original, budget={**original.budget, "maxTotalTokens": 50})
        turn = replace(
            needs_input("model-call:r17-contradictory-before-reopen"),
            usage={"total_tokens": 0, "input_tokens": 90, "output_tokens": 60},
        )
        clock = FixedClock()
        old_run = HarnessAgentRun.create(
            dsn, schema, bounded, lambda _: ScriptedTurnAdapter((turn,)),
            clock_ms=clock, monotonic_ms=clock,
        )
        # Reproduce a prior-version PAUSED snapshot with the actual PG writer.
        with patch("ordivon_harness.ordivon.loop._usage_total_tokens", return_value=0):
            paused = old_run.run(({"role": "user", "content": "old budget"},))
        assert paused.paused

        resume_adapter = ScriptedTurnAdapter(
            (completed("model-call:r17-must-not-dispatch"),)
        )
        new_run = HarnessAgentRun.open(
            dsn, schema, bounded.harness_run_id, lambda _: resume_adapter,
            clock_ms=clock, monotonic_ms=clock,
        )
        resumed = new_run.resume(
            additional_messages=({"role": "user", "content": "resume"},)
        )
        assert resumed.loop_result.stop_code.value == "budget_exhausted"
        assert resume_adapter.requests == []
        assert new_run.doctor()["healthy"] is True
