"""Governance Approval tests — approve/reject/expire paths and guard checks."""
import pytest
from unittest.mock import MagicMock

from governance.approval import (
    ApprovalRecord,
    ApprovalRequiredError,
    HumanApprovalGate,
    VALID_APPROVAL_STATES,
)


# ═══════════════════════════════════════════════════════════════════════
# D1.1 — ApprovalRecord model validation
# ═══════════════════════════════════════════════════════════════════════

def test_approval_record_valid():
    """A valid ApprovalRecord must construct without error."""
    record = ApprovalRecord(
        action_key="review.complete",
        entity_type="review",
        entity_id="review_001",
        requested_by="system",
        reason="Requires human review for high-impact change",
    )
    assert record.status == "pending"
    assert record.id.startswith("approval")


def test_approval_record_missing_action_key_raises():
    with pytest.raises(ValueError, match="action_key"):
        ApprovalRecord(
            action_key="",
            entity_type="review",
            entity_id="review_001",
            requested_by="system",
            reason="test",
        )


def test_approval_record_missing_entity_type_raises():
    with pytest.raises(ValueError, match="entity_type"):
        ApprovalRecord(
            action_key="review.complete",
            entity_type="",
            entity_id="review_001",
            requested_by="system",
            reason="test",
        )


def test_approval_record_invalid_status_raises():
    with pytest.raises(ValueError, match="Unsupported approval state"):
        ApprovalRecord(
            action_key="review.complete",
            entity_type="review",
            entity_id="review_001",
            status="cancelled",  # not in VALID_APPROVAL_STATES
            requested_by="system",
            reason="test",
        )


def test_approval_record_valid_states():
    """All states in VALID_APPROVAL_STATES must be acceptable."""
    for state in VALID_APPROVAL_STATES:
        record = ApprovalRecord(
            action_key="test",
            entity_type="test",
            entity_id="test_001",
            status=state,
            requested_by="system",
            reason="test",
        )
        assert record.status == state


# ═══════════════════════════════════════════════════════════════════════
# D1.2 — HumanApprovalGate approve path
# ═══════════════════════════════════════════════════════════════════════

def test_approve_updates_status():
    repo = MagicMock()
    mock_row = MagicMock()
    mock_row.status = "pending"
    repo.get.return_value = mock_row
    repo.update_decision.return_value = mock_row

    gate = HumanApprovalGate(repo)
    result = gate.approve("approval_001", actor="admin")

    repo.update_decision.assert_called_once_with(
        "approval_001",
        status="approved",
        decided_by="admin",
        decided_note=None,
    )
    assert result is mock_row


def test_approve_with_note():
    repo = MagicMock()
    mock_row = MagicMock()
    repo.get.return_value = mock_row
    repo.update_decision.return_value = mock_row

    gate = HumanApprovalGate(repo)
    gate.approve("approval_002", actor="admin", note="Looks good.")

    repo.update_decision.assert_called_once_with(
        "approval_002",
        status="approved",
        decided_by="admin",
        decided_note="Looks good.",
    )


def test_approve_not_found_raises():
    repo = MagicMock()
    repo.get.return_value = None
    repo.update_decision.return_value = None

    gate = HumanApprovalGate(repo)
    with pytest.raises(ApprovalRequiredError, match="not found"):
        gate.approve("approval_missing", actor="admin")


# ═══════════════════════════════════════════════════════════════════════
# D1.3 — HumanApprovalGate reject path
# ═══════════════════════════════════════════════════════════════════════

def test_reject_updates_status():
    repo = MagicMock()
    mock_row = MagicMock()
    repo.get.return_value = mock_row
    repo.update_decision.return_value = mock_row

    gate = HumanApprovalGate(repo)
    result = gate.reject("approval_003", actor="admin")

    repo.update_decision.assert_called_once_with(
        "approval_003",
        status="rejected",
        decided_by="admin",
        decided_note=None,
    )
    assert result is mock_row


def test_reject_not_found_raises():
    repo = MagicMock()
    repo.get.return_value = None
    repo.update_decision.return_value = None

    gate = HumanApprovalGate(repo)
    with pytest.raises(ApprovalRequiredError, match="not found"):
        gate.reject("approval_missing", actor="admin")


# ═══════════════════════════════════════════════════════════════════════
# D1.4 — HumanApprovalGate ensure_approved guard
# ═══════════════════════════════════════════════════════════════════════

def test_ensure_approved_no_requirement_returns_none():
    repo = MagicMock()
    gate = HumanApprovalGate(repo)
    result = gate.ensure_approved(
        action_key="review.complete",
        entity_type="review",
        entity_id="review_001",
        approval_id=None,
        require_approval=False,
    )
    assert result is None
    repo.get.assert_not_called()


def test_ensure_approved_missing_id_raises():
    repo = MagicMock()
    gate = HumanApprovalGate(repo)
    with pytest.raises(ApprovalRequiredError, match="Approval required"):
        gate.ensure_approved(
            action_key="review.complete",
            entity_type="review",
            entity_id="review_001",
            approval_id=None,
            require_approval=True,
        )


def test_ensure_approved_wrong_action_key_raises():
    repo = MagicMock()
    mock_row = MagicMock()
    mock_row.action_key = "review.submit"  # different from requested
    mock_row.entity_type = "review"
    mock_row.entity_id = "review_001"
    repo.get.return_value = mock_row

    gate = HumanApprovalGate(repo)
    with pytest.raises(ApprovalRequiredError, match="does not match"):
        gate.ensure_approved(
            action_key="review.complete",
            entity_type="review",
            entity_id="review_001",
            approval_id="approval_001",
            require_approval=True,
        )


def test_ensure_approved_not_approved_status_raises():
    repo = MagicMock()
    mock_row = MagicMock()
    mock_row.action_key = "review.complete"
    mock_row.entity_type = "review"
    mock_row.entity_id = "review_001"
    mock_row.status = "pending"  # not approved
    repo.get.return_value = mock_row

    gate = HumanApprovalGate(repo)
    with pytest.raises(ApprovalRequiredError, match="not approved"):
        gate.ensure_approved(
            action_key="review.complete",
            entity_type="review",
            entity_id="review_001",
            approval_id="approval_001",
            require_approval=True,
        )


def test_ensure_approved_passes_when_approved():
    repo = MagicMock()
    mock_row = MagicMock()
    mock_row.action_key = "review.complete"
    mock_row.entity_type = "review"
    mock_row.entity_id = "review_001"
    mock_row.status = "approved"
    repo.get.return_value = mock_row

    gate = HumanApprovalGate(repo)
    result = gate.ensure_approved(
        action_key="review.complete",
        entity_type="review",
        entity_id="review_001",
        approval_id="approval_001",
        require_approval=True,
    )
    assert result is mock_row


# ═══════════════════════════════════════════════════════════════════════
# D1.5 — ApprovalRequiredError
# ═══════════════════════════════════════════════════════════════════════

def test_approval_required_error_has_status_code():
    err = ApprovalRequiredError("test", status_code=409, approval_id="app_001")
    assert err.status_code == 409
    assert err.approval_id == "app_001"
    assert str(err) == "test"
