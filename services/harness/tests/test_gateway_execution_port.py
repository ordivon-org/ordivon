from __future__ import annotations

import pytest

from ordivon_harness.gateway_execution_port import (
    GatewayExecutionAmbiguous,
    GatewayExecutionError,
    GatewayExecutionPort,
    GatewayExecutionRequest,
)


class FakeGateway:
    def __init__(self, *, lose_submit: bool = False, resolve_state: str = 'found', working_observations: int = 0):
        self.lose_submit = lose_submit
        self.resolve_state = resolve_state
        self.calls: list[tuple[str, dict]] = []
        self.working_observations = working_observations

    def call_tool(self, name, arguments):
        self.calls.append((name, dict(arguments)))
        if name == 'execution.submit':
            if self.lose_submit:
                self.lose_submit = False
                raise RuntimeError('response lost after admission')
            return False, {
                'operation_ref': 'ordivon-exec:v1:runtime.windows:job-1',
                'native_id': 'job-1',
                'state': 'working',
                'terminal': False,
            }
        if name == 'execution.resolve':
            if self.resolve_state != 'found':
                return False, {
                    'resolution': self.resolve_state,
                    'request_id': arguments['requestId'],
                    'capability': arguments['capability'],
                }
            return False, {
                'resolution': 'found',
                'request_id': arguments['requestId'],
                'capability': arguments['capability'],
                'workspace_id': request().workspace_id,
                'operation_ref': 'ordivon-exec:v1:runtime.windows:job-1',
                'native_id': 'job-1',
            }
        if name == 'execution.get':
            if self.working_observations > 0:
                self.working_observations -= 1
                return False, {
                    'operation_ref': arguments['operationRef'],
                    'native_id': 'job-1',
                    'state': 'working',
                    'terminal': False,
                }
            return False, {
                'operation_ref': arguments['operationRef'],
                'native_id': 'job-1',
                'state': 'succeeded',
                'terminal': True,
                'delivery_disposition': 'committed',
                'execution_disposition': 'succeeded',
                'exit_code': 0,
                'recovery_required': False,
                'artifacts_available': True,
                'artifact_ids': ['attempt-1.stdout', 'attempt-1.result'],
                'artifact_projection_complete': True,
            }
        if name == 'artifact.read':
            assert arguments['artifactId'] == 'attempt-1.stdout'
            return False, {
                'operation_ref': arguments['operationRef'],
                'artifact_id': 'attempt-1.stdout',
                'offset': 0,
                'content': '{"standing":"bound"}\n',
                'next_offset': 21,
                'eof': True,
            }
        raise AssertionError(name)


def request():
    return GatewayExecutionRequest(
        capability='execution.windows',
        request_id='user-browser:effect-1',
        workspace_id='ws-user-browser-prod',
        executable=r'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe',
        args=('-NoProfile', '-NonInteractive', '-File', r'C:\\ProgramData\\Ordivon\\chat.ps1'),
        cwd_relative='.',
        context='active_user',
        timeout_ms=60_000,
    )


def test_response_loss_resolves_existing_job_without_second_submit():
    client = FakeGateway(lose_submit=True)
    port = GatewayExecutionPort(client)
    result = port.execute(request())
    assert result.native_id == 'job-1'
    assert result.exit_code == 0
    assert [name for name, _ in client.calls] == [
        'execution.submit', 'execution.resolve', 'execution.get'
    ]


def test_stdout_is_read_by_exact_artifact_identity():
    client = FakeGateway()
    port = GatewayExecutionPort(client)
    result = port.execute(request())
    assert port.read_stdout(result) == '{"standing":"bound"}\n'
    assert [name for name, _ in client.calls][-1] == 'artifact.read'
    calls = {name: arguments for name, arguments in client.calls if name in ('execution.get', 'artifact.read')}
    assert calls['execution.get']['requestId'] == request().request_id
    assert calls['execution.get']['capability'] == request().capability
    assert calls['artifact.read']['requestId'] == request().request_id
    assert calls['artifact.read']['capability'] == request().capability


def test_absent_after_submit_response_loss_is_ambiguous_not_redispatched():
    client = FakeGateway(lose_submit=True, resolve_state='absent')
    port = GatewayExecutionPort(client)
    with pytest.raises(GatewayExecutionAmbiguous):
        port.execute(request())
    names = [name for name, _ in client.calls]
    assert names == ['execution.submit', 'execution.resolve']
    assert names.count('execution.submit') == 1


@pytest.mark.parametrize("delivery", ("reconciliation_required", "unknown", "in_progress"))
def test_terminal_process_without_committed_delivery_is_not_consumer_terminal(delivery):
    class NotDelivered(FakeGateway):
        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "execution.get":
                value["delivery_disposition"] = delivery
                value["recovery_required"] = False
            return is_error, value

    client = NotDelivered()
    port = GatewayExecutionPort(client, max_observations=3, poll_interval_seconds=0)
    with pytest.raises(GatewayExecutionAmbiguous, match="delivery"):
        port.execute(request())
    assert [name for name, _ in client.calls].count("execution.submit") == 1
    assert [name for name, _ in client.calls].count("execution.get") == 3


def test_terminal_process_with_outstanding_recovery_is_not_consumer_terminal():
    class NeedsRecovery(FakeGateway):
        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "execution.get":
                value["recovery_required"] = True
            return is_error, value

    port = GatewayExecutionPort(NeedsRecovery(), max_observations=2, poll_interval_seconds=0)
    with pytest.raises(GatewayExecutionAmbiguous):
        port.execute(request())


@pytest.mark.parametrize("delivery", (None, "delivered", True))
def test_terminal_delivery_requires_known_gateway_disposition(delivery):
    class InvalidDelivery(FakeGateway):
        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "execution.get":
                value["delivery_disposition"] = delivery
            return is_error, value

    port = GatewayExecutionPort(InvalidDelivery(), max_observations=2, poll_interval_seconds=0)
    with pytest.raises(GatewayExecutionError, match="delivery disposition"):
        port.execute(request())


def test_nonterminal_committed_delivery_is_a_contract_violation():
    class Contradictory(FakeGateway):
        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "execution.get":
                value["terminal"] = False
                value["delivery_disposition"] = "committed"
            return is_error, value

    with pytest.raises(GatewayExecutionError, match="contradicts"):
        GatewayExecutionPort(Contradictory()).execute(request())


def test_gateway_observation_cannot_rebind_operation_ref():
    class WrongOperation(FakeGateway):
        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "execution.get":
                value["operation_ref"] = "ordivon-exec:v1:runtime.windows:another-job"
            return is_error, value

    with pytest.raises(GatewayExecutionError, match="operation identity"):
        GatewayExecutionPort(WrongOperation()).execute(request())


def test_long_running_execution_is_client_polled_beyond_old_twenty_observation_ceiling():
    client = FakeGateway(working_observations=25)
    port = GatewayExecutionPort(client, max_observations=40, poll_interval_seconds=0)
    result = port.execute(request())
    assert result.state == 'succeeded'
    gets = [args for name, args in client.calls if name == 'execution.get']
    assert len(gets) == 26
    assert all('waitMs' not in args for args in gets)



def test_committed_terminal_with_incomplete_projection_is_not_consumer_terminal():
    """Runtime/Gateway committed physical result does not discharge Harness artifact identity."""
    class IncompleteProjection(FakeGateway):
        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "execution.get":
                value["artifact_count"] = 2
                value["artifact_ids"] = []
                value["artifact_projection_complete"] = False
            return is_error, value

    client = IncompleteProjection()
    port = GatewayExecutionPort(client, max_observations=3, poll_interval_seconds=0)
    with pytest.raises(GatewayExecutionAmbiguous, match="projection|delivery"):
        port.execute(request())
    names = [name for name, _ in client.calls]
    assert names.count("execution.submit") == 1
    assert names.count("execution.get") == 3


def test_delayed_complete_projection_is_consumed_without_redispatch():
    class DelayedProjection(FakeGateway):
        observations = 0

        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "execution.get":
                self.observations += 1
                if self.observations == 1:
                    value["artifact_count"] = 2
                    value["artifact_ids"] = []
                    value["artifact_projection_complete"] = False
            return is_error, value

    client = DelayedProjection()
    result = GatewayExecutionPort(
        client, max_observations=3, poll_interval_seconds=0
    ).execute(request())
    assert result.artifact_ids == ("attempt-1.stdout", "attempt-1.result")
    assert [name for name, _ in client.calls].count("execution.submit") == 1
    assert [name for name, _ in client.calls].count("execution.get") == 2



@pytest.mark.parametrize(
    "patch",
    (
        {"artifact_projection_complete": "true"},
        {"artifact_projection_complete": None},
        {"artifact_count": True},
        {"artifact_count": 3},
    ),
)
def test_committed_terminal_rejects_typed_or_inconsistent_artifact_proof(patch):
    """The Gateway complete-artifact witness has a typed finite-set cardinality."""
    class InvalidArtifactWitness(FakeGateway):
        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "execution.get":
                value["artifact_count"] = 2
                value.update(patch)
            return is_error, value

    with pytest.raises(GatewayExecutionError, match="artifact"):
        GatewayExecutionPort(InvalidArtifactWitness()).execute(request())

@pytest.mark.parametrize(
    ("mutation", "reason"),
    (
        ({"operation_ref": "ordivon-exec:v1:runtime.windows:foreign"}, "operation"),
        ({"offset": 7}, "offset"),
    ),
)
def test_stdout_readback_rejects_foreign_operation_or_discontinuous_offset(
    mutation, reason
):
    """CEGAR: matching artifactId alone is not a source-bound byte stream."""
    class ForgedArtifact(FakeGateway):
        def call_tool(self, name, arguments):
            is_error, value = super().call_tool(name, arguments)
            if name == "artifact.read":
                value.update(mutation)
            return is_error, value

    port = GatewayExecutionPort(ForgedArtifact())
    result = port.execute(request())
    with pytest.raises(GatewayExecutionError, match=reason):
        port.read_stdout(result)

@pytest.mark.parametrize(
    ("identity_field", "foreign_value"),
    (
        ("request_id", "foreign-request"),
        ("capability", "execution.linux"),
        ("workspace_id", "ws-foreign-recovery"),
        ("request_id", None),
        ("capability", None),
        ("workspace_id", None),
    ),
)
def test_lost_submit_response_rejects_foreign_gateway_resolution_identity(
    identity_field, foreign_value
):
    """A found Job cannot bind a different original request, route, or Workspace."""

    class ForeignResolution(FakeGateway):
        def call_tool(self, name, arguments):
            error, result = super().call_tool(name, arguments)
            if name == "execution.resolve":
                result.update(
                    request_id=arguments["requestId"],
                    capability=arguments["capability"],
                    workspace_id=request().workspace_id,
                )
                result[identity_field] = foreign_value
            return error, result

    client = ForeignResolution(lose_submit=True)
    with pytest.raises(GatewayExecutionAmbiguous, match="identity"):
        GatewayExecutionPort(client).execute(request())
    assert [name for name, _ in client.calls] == [
        "execution.submit", "execution.resolve"
    ]
