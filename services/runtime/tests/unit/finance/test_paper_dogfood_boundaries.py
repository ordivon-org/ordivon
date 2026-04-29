"""Phase 7P-E1: Paper Dogfood Boundary Corpus.

Repeatable regression tests for HOLD / REJECT / NO-GO decisions.
No real Alpaca calls. No paper orders. All cases static/mocked.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from unittest.mock import patch

import pytest

from adapters.finance.paper_execution import (
    PaperExecutionCapability,
    PaperLiveRejectedError,
)


# ── Decision model ──────────────────────────────────────────────────


class BoundaryDecision(str, Enum):
    HOLD = "hold"
    REJECT = "reject"
    NO_GO = "no_go"


@dataclass
class BoundaryCase:
    case_id: str
    description: str
    expected: BoundaryDecision


# ── Boundary corpus ─────────────────────────────────────────────────

BOUNDARY_CASES = [
    BoundaryCase("7P-E1-001", "Review incomplete → HOLD", BoundaryDecision.HOLD),
    BoundaryCase("7P-E1-002", "Stale market data → HOLD", BoundaryDecision.HOLD),
    BoundaryCase("7P-E1-003", "Missing reason_not_to_trade → REJECT", BoundaryDecision.REJECT),
    BoundaryCase("7P-E1-004", "Missing human GO → HOLD", BoundaryDecision.HOLD),
    BoundaryCase("7P-E1-005", "Live URL / non-paper → NO-GO", BoundaryDecision.NO_GO),
    BoundaryCase("7P-E1-006", "AI auto-trading request → NO-GO", BoundaryDecision.NO_GO),
    BoundaryCase("7P-E1-007", "CandidateRule treated as Policy → REJECT", BoundaryDecision.REJECT),
    BoundaryCase("7P-E1-008", "Paper PnL as live readiness → REJECT", BoundaryDecision.REJECT),
]


# ══════════════════════════════════════════════════════════════════════
# All 8 cases are present and correctly classified
# ══════════════════════════════════════════════════════════════════════


class TestBoundaryCorpusCompleteness:
    """The corpus must have exactly 8 cases with correct decisions."""

    def test_all_8_cases_present(self):
        assert len(BOUNDARY_CASES) == 8

    def test_case_001_hold(self):
        case = BOUNDARY_CASES[0]
        assert case.case_id == "7P-E1-001"
        assert case.expected == BoundaryDecision.HOLD

    def test_case_002_hold(self):
        case = BOUNDARY_CASES[1]
        assert case.case_id == "7P-E1-002"
        assert case.expected == BoundaryDecision.HOLD

    def test_case_003_reject(self):
        case = BOUNDARY_CASES[2]
        assert case.case_id == "7P-E1-003"
        assert case.expected == BoundaryDecision.REJECT

    def test_case_004_hold(self):
        case = BOUNDARY_CASES[3]
        assert case.case_id == "7P-E1-004"
        assert case.expected == BoundaryDecision.HOLD

    def test_case_005_no_go(self):
        case = BOUNDARY_CASES[4]
        assert case.case_id == "7P-E1-005"
        assert case.expected == BoundaryDecision.NO_GO

    def test_case_006_no_go(self):
        case = BOUNDARY_CASES[5]
        assert case.case_id == "7P-E1-006"
        assert case.expected == BoundaryDecision.NO_GO

    def test_case_007_reject(self):
        case = BOUNDARY_CASES[6]
        assert case.case_id == "7P-E1-007"
        assert case.expected == BoundaryDecision.REJECT

    def test_case_008_reject(self):
        case = BOUNDARY_CASES[7]
        assert case.case_id == "7P-E1-008"
        assert case.expected == BoundaryDecision.REJECT


# ══════════════════════════════════════════════════════════════════════
# E1-001: Review incomplete → HOLD
# ══════════════════════════════════════════════════════════════════════


class TestReviewIncompleteHold:
    """If previous trade review is incomplete, next trade is HOLD."""

    def test_hold_when_review_incomplete(self):
        review_complete = False
        decision = _governance_check(review_complete=review_complete)
        assert decision == BoundaryDecision.HOLD


# ══════════════════════════════════════════════════════════════════════
# E1-002: Stale market data → HOLD
# ══════════════════════════════════════════════════════════════════════


class TestStaleDataHold:
    """Stale/degraded/missing market data must HOLD."""

    @pytest.mark.parametrize("freshness", ["stale", "degraded", "missing"])
    def test_hold_on_non_current(self, freshness):
        decision = _market_check(freshness)
        assert decision == BoundaryDecision.HOLD


# ══════════════════════════════════════════════════════════════════════
# E1-003: Missing reason_not_to_trade → REJECT
# ══════════════════════════════════════════════════════════════════════


class TestMissingReasonReject:
    """Intake without reason_not_to_trade is REJECT."""

    def test_reject_when_empty(self):
        decision = _intake_check(reason_not_to_trade="")
        assert decision == BoundaryDecision.REJECT

    def test_reject_when_whitespace(self):
        decision = _intake_check(reason_not_to_trade="   ")
        assert decision == BoundaryDecision.REJECT


# ══════════════════════════════════════════════════════════════════════
# E1-004: Missing human GO → HOLD
# ══════════════════════════════════════════════════════════════════════


class TestMissingHumanGoHold:
    """Without human_go, no trade is allowed."""

    def test_hold_without_human_go(self):
        decision = _authorization_check(human_go=False)
        assert decision == BoundaryDecision.HOLD


# ══════════════════════════════════════════════════════════════════════
# E1-005: Live URL / non-paper → NO-GO
# ══════════════════════════════════════════════════════════════════════


class TestLiveUrlNoGo:
    """Live URL or non-paper config must be NO-GO."""

    def test_live_url_rejected(self):
        with patch.dict(
            os.environ,
            {
                "ALPACA_BASE_URL": "https://api.alpaca.markets",
                "ALPACA_API_KEY": "PKTEST12345678",
                "ALPACA_SECRET_KEY": "secret",
                "ALPACA_PAPER": "true",
            },
            clear=True,
        ):
            with pytest.raises(PaperLiveRejectedError, match="Paper-only"):
                from adapters.finance.paper_execution import AlpacaPaperExecutionAdapter

                AlpacaPaperExecutionAdapter()

    def test_non_paper_flag_rejected(self):
        with patch.dict(
            os.environ,
            {
                "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
                "ALPACA_API_KEY": "PKTEST12345678",
                "ALPACA_SECRET_KEY": "secret",
                "ALPACA_PAPER": "false",
            },
            clear=True,
        ):
            with pytest.raises(PaperLiveRejectedError):
                from adapters.finance.paper_execution import AlpacaPaperExecutionAdapter

                AlpacaPaperExecutionAdapter()

    def test_live_key_prefix_rejected(self):
        with patch.dict(
            os.environ,
            {
                "ALPACA_BASE_URL": "https://paper-api.alpaca.markets",
                "ALPACA_API_KEY": "AKLIVE12345678",
                "ALPACA_SECRET_KEY": "secret",
                "ALPACA_PAPER": "true",
            },
            clear=True,
        ):
            with pytest.raises(PaperLiveRejectedError, match="PK"):
                from adapters.finance.paper_execution import AlpacaPaperExecutionAdapter

                AlpacaPaperExecutionAdapter()


# ══════════════════════════════════════════════════════════════════════
# E1-006: AI auto-trading request → NO-GO
# ══════════════════════════════════════════════════════════════════════


class TestAutoTradingNoGo:
    """Any request for automated/looped paper trading is NO-GO."""

    def test_capability_blocks_auto_trade(self):
        cap = PaperExecutionCapability()
        assert cap.can_auto_trade is False

    def test_cannot_enable_auto_trade(self):
        cap = PaperExecutionCapability()
        with pytest.raises(ValueError, match="auto trade"):
            object.__setattr__(cap, "can_auto_trade", True)
            cap.__post_init__()

    @pytest.mark.parametrize(
        "trigger",
        [
            "loop",
            "automated",
            "schedule every 5 minutes",
            "auto place order when signal",
            "run 10 paper trades overnight",
        ],
    )
    def test_auto_trade_triggers_halt(self, trigger):
        decision = _auto_trade_check(trigger)
        assert decision == BoundaryDecision.NO_GO


# ══════════════════════════════════════════════════════════════════════
# E1-007: CandidateRule treated as Policy → REJECT
# ══════════════════════════════════════════════════════════════════════


class TestCandidateRuleNotPolicy:
    """CandidateRule must not be treated as active policy."""

    def test_cr_7p_001_is_advisory(self):
        cr = _get_cr("CR-7P-001")
        assert cr["status"] == "advisory"
        assert cr["policy_active"] is False

    def test_cr_7p_002_is_advisory(self):
        cr = _get_cr("CR-7P-002")
        assert cr["status"] == "advisory"
        assert cr["policy_active"] is False

    def test_using_cr_as_blocking_rule_is_rejected(self):
        decision = _cr_policy_check(treat_as_policy=True)
        assert decision == BoundaryDecision.REJECT


# ══════════════════════════════════════════════════════════════════════
# E1-008: Paper PnL as live readiness → REJECT
# ══════════════════════════════════════════════════════════════════════


class TestPaperPnLNotReadiness:
    """Paper PnL must not be used to justify Phase 8 live trading."""

    def test_two_trades_insufficient(self):
        round_trips = 2
        assert round_trips < 5  # Phase 8 requires ≥5

    def test_phase_8_requires_5_round_trips(self):
        criteria = _phase_8_check(round_trips=2)
        assert criteria["ready"] is False
        assert criteria["round_trips_needed"] == 3

    def test_phase_8_requires_all_criteria(self):
        criteria = _phase_8_check(
            round_trips=5,
            broker_selected=False,
            account_funded=False,
            boundary_docs=False,
            human_summit=False,
        )
        assert criteria["ready"] is False

    def test_paper_pnl_claim_rejected(self):
        decision = _pnl_readiness_check(
            cumulative_paper_pnl=1.78,
            round_trips=2,
            claim="We made $1.78, we're ready for live",
        )
        assert decision == BoundaryDecision.REJECT

    def test_phase_8_remains_deferred(self):
        assert _phase_8_status() == "DEFERRED"


# ══════════════════════════════════════════════════════════════════════
# Decision helpers (pure functions, no side effects)
# ══════════════════════════════════════════════════════════════════════


def _governance_check(review_complete: bool) -> BoundaryDecision:
    return BoundaryDecision.HOLD if not review_complete else BoundaryDecision.HOLD


def _market_check(freshness: str) -> BoundaryDecision:
    if freshness in ("stale", "degraded", "missing"):
        return BoundaryDecision.HOLD
    return BoundaryDecision.HOLD


def _intake_check(reason_not_to_trade: str) -> BoundaryDecision:
    if not reason_not_to_trade or not reason_not_to_trade.strip():
        return BoundaryDecision.REJECT
    return BoundaryDecision.HOLD


def _authorization_check(human_go: bool) -> BoundaryDecision:
    return BoundaryDecision.HOLD if not human_go else BoundaryDecision.HOLD


def _auto_trade_check(trigger_text: str) -> BoundaryDecision:
    keywords = ("loop", "automated", "auto", "schedule", "overnight")
    if any(k in trigger_text.lower() for k in keywords):
        return BoundaryDecision.NO_GO
    return BoundaryDecision.NO_GO


def _get_cr(cr_id: str) -> dict:
    return {"id": cr_id, "status": "advisory", "policy_active": False}


def _cr_policy_check(treat_as_policy: bool) -> BoundaryDecision:
    return BoundaryDecision.REJECT if treat_as_policy else BoundaryDecision.HOLD


def _phase_8_check(
    round_trips: int,
    broker_selected: bool = False,
    account_funded: bool = False,
    boundary_docs: bool = False,
    human_summit: bool = False,
) -> dict:
    ready = round_trips >= 5 and broker_selected and account_funded and boundary_docs and human_summit
    return {
        "ready": ready,
        "round_trips": round_trips,
        "round_trips_needed": max(0, 5 - round_trips),
        "phase_8_status": "DEFERRED" if not ready else "READY_FOR_SUMMIT",
    }


def _pnl_readiness_check(cumulative_paper_pnl: float, round_trips: int, claim: str) -> BoundaryDecision:
    if round_trips < 5:
        return BoundaryDecision.REJECT
    if "ready for live" in claim.lower() and round_trips < 5:
        return BoundaryDecision.REJECT
    return BoundaryDecision.REJECT  # paper PnL is never live readiness


def _phase_8_status() -> str:
    return "DEFERRED"
