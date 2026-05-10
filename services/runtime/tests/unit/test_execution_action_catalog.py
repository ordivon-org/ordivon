import pytest

from execution.catalog import (
    ExecutionActionSpec,
    get_execution_action,
    get_primary_receipt_candidates,
    list_execution_actions,
    validate_execution_catalog,
)


def test_execution_action_catalog_lists_known_actions():
    actions = list_execution_actions()
    action_ids = {spec.action_id for spec in actions}

    assert "analysis_report_write" in action_ids
    assert "recommendation_status_update" in action_ids
    assert "review_complete" in action_ids


def test_execution_action_catalog_exposes_primary_receipt_candidates():
    candidates = {spec.action_id for spec in get_primary_receipt_candidates()}

    assert "analysis_report_write" in candidates
    assert "review_complete" in candidates
    assert "validation_issue_report" in candidates


def test_execution_action_catalog_rejects_duplicate_action_ids():
    with pytest.raises(ValueError, match="Duplicate execution action_id"):
        validate_execution_catalog((
            ExecutionActionSpec(
                action_id="dup_action",
                family="analysis",
                side_effect_level="state_mutation",
                owner_path="owner.one",
                boundary_status="covered",
                state_targets=("analyses",),
                primary_receipt_candidate=False,
            ),
            ExecutionActionSpec(
                action_id="dup_action",
                family="analysis",
                side_effect_level="state_mutation",
                owner_path="owner.two",
                boundary_status="covered",
                state_targets=("analyses",),
                primary_receipt_candidate=False,
            ),
        ))


def test_get_execution_action_raises_for_unknown_action():
    with pytest.raises(KeyError, match="Unknown execution action"):
        get_execution_action("unknown.action")
