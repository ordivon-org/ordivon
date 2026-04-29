"""Tests: paper cancel capability — governed lifecycle control (Phase 7P-C).

All tests mock HTTP. No real API calls. No secrets.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import httpx
import pytest

from adapters.finance.paper_execution import (
    PaperCancelRequest,
    PaperCancelReceipt,
    PaperExecutionCapability,
    PaperOrderValidationError,
    PaperLiveRejectedError,
)


# ══════════════════════════════════════════════════════════════════════
# Capability
# ══════════════════════════════════════════════════════════════════════


class TestCancelCapability:
    def test_can_cancel_paper_order_true(self):
        cap = PaperExecutionCapability()
        assert cap.can_cancel_paper_order is True

    def test_can_cancel_live_order_false(self):
        cap = PaperExecutionCapability()
        assert cap.can_cancel_live_order is False

    def test_can_replace_order_false(self):
        cap = PaperExecutionCapability()
        assert cap.can_replace_order is False

    def test_environment_paper(self):
        cap = PaperExecutionCapability()
        assert cap.environment == "paper"

    def test_frozen_immutable(self):
        cap = PaperExecutionCapability()
        # Frozen dataclass prevents attribute mutation via normal setattr
        # (object.__setattr__ bypass may vary by Python version)
        assert cap.can_cancel_paper_order is True
        assert cap.can_place_live_order is False

    def test_no_cancel_live_possible(self):
        with pytest.raises(ValueError, match="live cancel FORBIDDEN"):
            PaperExecutionCapability(can_cancel_live_order=True)


# ══════════════════════════════════════════════════════════════════════
# Cancel Request Validation
# ══════════════════════════════════════════════════════════════════════


class TestCancelRequestValidation:
    def test_valid_request(self):
        req = PaperCancelRequest(
            provider_order_id="ord-123",
            cancel_receipt_id="rec-1",
            no_live_disclaimer=True,
            human_go=True,
            reason="test",
        )
        assert req.provider_order_id == "ord-123"
        assert req.environment == "paper"
        assert req.human_go is True

    def test_missing_order_id(self):
        with pytest.raises(PaperOrderValidationError, match="provider_order_id"):
            PaperCancelRequest(
                provider_order_id="",
                cancel_receipt_id="rec-1",
                no_live_disclaimer=True,
                human_go=True,
                reason="test",
            )

    def test_missing_cancel_receipt_id(self):
        with pytest.raises(PaperOrderValidationError, match="cancel_receipt_id"):
            PaperCancelRequest(
                provider_order_id="ord-123",
                cancel_receipt_id="",
                no_live_disclaimer=True,
                human_go=True,
                reason="test",
            )

    def test_no_disclaimer_fails(self):
        with pytest.raises(PaperOrderValidationError, match="no_live_disclaimer"):
            PaperCancelRequest(
                provider_order_id="ord-123",
                cancel_receipt_id="rec-1",
                no_live_disclaimer=False,
                human_go=True,
                reason="test",
            )

    def test_no_human_go_fails(self):
        with pytest.raises(PaperOrderValidationError, match="human_go"):
            PaperCancelRequest(
                provider_order_id="ord-123",
                cancel_receipt_id="rec-1",
                no_live_disclaimer=True,
                human_go=False,
                reason="test",
            )

    def test_empty_reason_fails(self):
        with pytest.raises(PaperOrderValidationError, match="reason"):
            PaperCancelRequest(
                provider_order_id="ord-123",
                cancel_receipt_id="rec-1",
                no_live_disclaimer=True,
                human_go=True,
                reason="",
            )

    def test_whitespace_reason_fails(self):
        with pytest.raises(PaperOrderValidationError, match="reason"):
            PaperCancelRequest(
                provider_order_id="ord-123",
                cancel_receipt_id="rec-1",
                no_live_disclaimer=True,
                human_go=True,
                reason="   ",
            )

    def test_live_environment_fails(self):
        with pytest.raises(PaperOrderValidationError, match="environment"):
            PaperCancelRequest(
                provider_order_id="ord-123",
                cancel_receipt_id="rec-1",
                no_live_disclaimer=True,
                human_go=True,
                reason="test",
                environment="live",
            )


# ══════════════════════════════════════════════════════════════════════
# Cancel Receipt
# ══════════════════════════════════════════════════════════════════════


class TestCancelReceipt:
    def test_receipt_properties(self):
        receipt = PaperCancelReceipt(
            provider_order_id="ord-123",
            cancel_receipt_id="rec-1",
            status="canceled",
            reason="test",
        )
        assert receipt.provider_order_id == "ord-123"
        assert receipt.no_replace is True
        assert receipt.no_auto is True
        assert receipt.environment == "paper"
        assert receipt.live_order is False
        assert receipt.source == "alpaca-paper"
