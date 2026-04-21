from intelligence.runtime.hermes_client import HermesRuntimeError
from orchestrator.contracts.workflow import WorkflowContext
from orchestrator.runtime.recovery import RecoveryDetail, RecoveryPolicy, consume_recovery_detail, record_recovery_detail
from orchestrator.workflows.analyze import ReasonStep
from domains.research.models import AnalysisRequest


def test_reason_step_uses_recovery_policy_for_retryable_hermes_errors():
    step = ReasonStep()

    retryable_error = HermesRuntimeError("temporary", retryable=True)
    permanent_error = HermesRuntimeError("permanent", retryable=False)

    assert step.recovery_policy.should_retry(retryable_error, attempt=1) is True
    assert step.recovery_policy.should_retry(permanent_error, attempt=1) is False
    assert step.recovery_policy.should_retry(ValueError("not hermes"), attempt=1) is False
    assert step.recovery_policy.should_retry(retryable_error, attempt=2) is False


def test_recovery_detail_round_trips_through_context_metadata():
    ctx = WorkflowContext(request=AnalysisRequest(query="test"))

    record_recovery_detail(
        ctx,
        action="compensation",
        detail={"compensation_applied": True},
    )

    detail = consume_recovery_detail(ctx)

    assert detail == RecoveryDetail(
        action="compensation",
        detail={"compensation_applied": True},
    )
    assert consume_recovery_detail(ctx) is None


def test_recovery_policy_uses_terminal_action_without_detail():
    policy = RecoveryPolicy(terminal_action="none")

    assert policy.failure_action(None) == "none"
    assert policy.failure_detail(None) == {}
