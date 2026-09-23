from __future__ import annotations

import pytest

from ordivon_harness.gateway_execution_port import (
    GatewayExecutionAmbiguous,
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
        if name == 'capability.describe':
            return False, {
                'projection_digest': 'sha256:' + '7' * 64,
                'capabilities': [
                    {
                        'capability': arguments['capability'],
                        'configured': True,
                        'available': True,
                        'contexts': ['limited', 'elevated', 'active_user'],
                    }
                ],
            }
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


def test_absent_after_submit_response_loss_is_ambiguous_not_redispatched():
    client = FakeGateway(lose_submit=True, resolve_state='absent')
    port = GatewayExecutionPort(client)
    with pytest.raises(GatewayExecutionAmbiguous):
        port.execute(request())
    names = [name for name, _ in client.calls]
    assert names == ['execution.submit', 'execution.resolve']
    assert names.count('execution.submit') == 1


def test_long_running_execution_is_client_polled_beyond_old_twenty_observation_ceiling():
    client = FakeGateway(working_observations=25)
    port = GatewayExecutionPort(client, max_observations=40, poll_interval_seconds=0)
    result = port.execute(request())
    assert result.state == 'succeeded'
    gets = [args for name, args in client.calls if name == 'execution.get']
    assert len(gets) == 26
    assert all('waitMs' not in args for args in gets)


def test_capability_standing_preserves_owner_context_projection():
    client = FakeGateway()
    standing = GatewayExecutionPort(client).capability_standing('execution.windows')
    assert standing.capability == 'execution.windows'
    assert standing.configured is True
    assert standing.available is True
    assert standing.contexts == ('limited', 'elevated', 'active_user')
    assert standing.supports_context('active_user') is True
    assert standing.projection_digest == 'sha256:' + '7' * 64
    assert client.calls == [('capability.describe', {'capability': 'execution.windows'})]
