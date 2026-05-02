"""ADP-2R: Finance paper/live boundary invariant tests (P0-4).

Tests that the paper execution capability rejects live configurations
at construction time — checking invariants, not runtime behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pytest


class TestPaperExecutionCapabilityInvariants:
    """P0-4: PaperExecutionCapability must reject live configurations."""

    def test_environment_must_be_paper(self):
        """environment='live' must raise ValueError."""
        from adapters.finance.paper_execution import PaperExecutionCapability

        with pytest.raises(ValueError, match="environment"):
            PaperExecutionCapability(environment="live")

    def test_can_place_live_order_must_be_false(self):
        """can_place_live_order=True must raise ValueError."""
        from adapters.finance.paper_execution import PaperExecutionCapability

        with pytest.raises(ValueError, match="live orders"):
            PaperExecutionCapability(can_place_live_order=True)

    def test_can_cancel_live_order_must_be_false(self):
        """can_cancel_live_order=True must raise ValueError."""
        from adapters.finance.paper_execution import PaperExecutionCapability

        with pytest.raises(ValueError, match="live cancel"):
            PaperExecutionCapability(can_cancel_live_order=True)

    def test_can_withdraw_must_be_false(self):
        """can_withdraw=True must raise ValueError."""
        from adapters.finance.paper_execution import PaperExecutionCapability

        with pytest.raises(ValueError, match="withdraw"):
            PaperExecutionCapability(can_withdraw=True)

    def test_can_transfer_must_be_false(self):
        """can_transfer=True must raise ValueError."""
        from adapters.finance.paper_execution import PaperExecutionCapability

        with pytest.raises(ValueError, match="transfer"):
            PaperExecutionCapability(can_transfer=True)

    def test_can_auto_trade_must_be_false(self):
        """can_auto_trade=True must raise ValueError."""
        from adapters.finance.paper_execution import PaperExecutionCapability

        with pytest.raises(ValueError, match="auto.trade"):
            PaperExecutionCapability(can_auto_trade=True)

    def test_paper_configuration_is_valid(self):
        """Default paper configuration must not raise."""
        from adapters.finance.paper_execution import PaperExecutionCapability

        cap = PaperExecutionCapability()
        assert cap.environment == "paper"
        assert cap.can_place_paper_order is True
        assert cap.can_cancel_paper_order is True
        assert cap.can_place_live_order is False
        assert cap.can_cancel_live_order is False


class TestReadOnlyAdapterCapabilityInvariants:
    """ReadOnlyAdapterCapability must enforce read-only invariants."""

    def test_can_place_order_must_be_false(self):
        """can_place_order=True must raise ValueError."""
        from domains.finance.read_only_adapter import ReadOnlyAdapterCapability

        with pytest.raises(ValueError):
            ReadOnlyAdapterCapability(can_place_order=True)

    def test_can_cancel_order_must_be_false(self):
        """can_cancel_order=True must raise ValueError."""
        from domains.finance.read_only_adapter import ReadOnlyAdapterCapability

        with pytest.raises(ValueError):
            ReadOnlyAdapterCapability(can_cancel_order=True)

    def test_is_read_only_returns_true(self):
        """Read-only capability must report is_read_only=True."""
        from domains.finance.read_only_adapter import ReadOnlyAdapterCapability

        cap = ReadOnlyAdapterCapability()
        assert cap.is_read_only is True
        assert cap.can_place_order is False
        assert cap.can_cancel_order is False
