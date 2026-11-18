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
