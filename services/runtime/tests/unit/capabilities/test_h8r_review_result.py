"""H-8R: ReviewResult outcome_ref 字段单元测试."""

import pytest
from capabilities.contracts.domain import ReviewResult


def test_review_result_default_outcome_ref_is_none():
    """ReviewResult 默认 outcome_ref 字段为 None — 向后兼容。"""
    result = ReviewResult(
        id="rv-test",
        status="completed",
        created_at="2026-01-01T00:00:00Z",
        recommendation_id=None,
        lessons_created=0,
    )
    assert result.outcome_ref_type is None
    assert result.outcome_ref_id is None


def test_review_result_populated_outcome_ref():
    """ReviewResult 可以填充 outcome_ref 值。"""
    result = ReviewResult(
        id="rv-test",
        status="completed",
        created_at="2026-01-01T00:00:00Z",
        recommendation_id=None,
        lessons_created=2,
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-abc123",
    )
    assert result.outcome_ref_type == "finance_manual_outcome"
    assert result.outcome_ref_id == "fmout-abc123"


def test_review_result_serializable():
    """ReviewResult 可以被序列化（dataclass asdict）。"""
    from dataclasses import asdict

    result = ReviewResult(
        id="rv-test",
        status="completed",
        created_at="2026-01-01T00:00:00Z",
        recommendation_id=None,
        lessons_created=2,
        outcome_ref_type="finance_manual_outcome",
        outcome_ref_id="fmout-abc123",
    )
    d = asdict(result)
    assert d["outcome_ref_type"] == "finance_manual_outcome"
    assert d["outcome_ref_id"] == "fmout-abc123"
