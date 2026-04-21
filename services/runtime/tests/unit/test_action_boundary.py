import pytest

from capabilities.boundary import ActionContext, build_action_context, require_action_context


def test_build_action_context_returns_validated_context():
    context = build_action_context(
        "report write",
        actor="workflow.analyze",
        context="write_wiki_step",
        reason="write analysis markdown report",
        idempotency_key="report-write:test",
    )

    assert context.actor == "workflow.analyze"
    assert context.context == "write_wiki_step"
    assert context.idempotency_key == "report-write:test"


def test_require_action_context_fails_on_missing_fields():
    with pytest.raises(ValueError, match="missing required action context fields"):
        require_action_context(
            "report write",
            ActionContext(
                actor="workflow.analyze",
                context="",
                reason="write analysis markdown report",
                idempotency_key="report-write:test",
            ),
        )
