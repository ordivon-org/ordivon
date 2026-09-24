from __future__ import annotations

import time
from dataclasses import dataclass

from anc_canonical import JsonValue, validate_json_value

from .mcp_http_client import HarnessMcpClient


class GatewayExecutionError(RuntimeError):
    pass


class GatewayExecutionAmbiguous(GatewayExecutionError):
    pass


def _field(payload: dict[str, JsonValue], snake: str, camel: str):
    return payload[snake] if snake in payload else payload.get(camel)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise GatewayExecutionError(f'Gateway {label} is missing or invalid')
    return value


@dataclass(frozen=True, slots=True)
class GatewayExecutionRequest:
    capability: str
    request_id: str
    workspace_id: str
    executable: str
    args: tuple[str, ...]
    cwd_relative: str = '.'
    context: str | None = None
    env: tuple[tuple[str, str], ...] = ()
    timeout_ms: int | None = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.capability, 'capability'),
            (self.request_id, 'request id'),
            (self.workspace_id, 'workspace id'),
            (self.executable, 'executable'),
            (self.cwd_relative, 'cwdRelative'),
        ):
            if not value or value != value.strip():
                raise ValueError(f'Gateway {label} must be non-empty and trimmed')
        if not self.capability.startswith('execution.'):
            raise ValueError('Gateway capability must be execution.*')
        if any(not isinstance(item, str) for item in self.args):
            raise ValueError('Gateway args must be strings')
        if self.context is not None and (not self.context or self.context != self.context.strip()):
            raise ValueError('Gateway context must be trimmed')
        if self.timeout_ms is not None and (
            type(self.timeout_ms) is not int or not 1 <= self.timeout_ms <= 900_000
        ):
            raise ValueError('Gateway timeout must be between 1 and 900000 ms')
        keys = [key for key, _ in self.env]
        if len(keys) != len(set(keys)):
            raise ValueError('Gateway env keys must be unique')

    def submit_arguments(self) -> dict[str, JsonValue]:
        value: dict[str, JsonValue] = {
            'capability': self.capability,
            'requestId': self.request_id,
            'workspaceId': self.workspace_id,
            'executable': self.executable,
            'args': list(self.args),
            'cwdRelative': self.cwd_relative,
        }
        if self.context is not None:
            value['context'] = self.context
        if self.env:
            value['env'] = {key: item for key, item in self.env}
        if self.timeout_ms is not None:
            value['timeoutMs'] = self.timeout_ms
        return value


@dataclass(frozen=True, slots=True)
class GatewayExecutionResult:
    operation_ref: str
    native_id: str
    state: str
    exit_code: int | None
    artifact_ids: tuple[str, ...]
    recovery_required: bool


@dataclass(frozen=True, slots=True)
class GatewayCapabilityStanding:
    capability: str
    configured: bool
    available: bool
    contexts: tuple[str, ...]
    projection_digest: str

    def supports_context(self, context: str) -> bool:
        return self.configured and self.available and context in self.contexts


class GatewayExecutionPort:
    def __init__(
        self,
        client: HarnessMcpClient,
        *,
        max_observations: int = 4096,
        poll_interval_seconds: float = 0.25,
    ) -> None:
        if max_observations < 1:
            raise ValueError('max_observations must be positive')
        if not 0 <= poll_interval_seconds <= 5:
            raise ValueError('poll_interval_seconds must be between 0 and 5')
        self.client = client
        self.max_observations = max_observations
        self.poll_interval_seconds = poll_interval_seconds

    def _call(self, name: str, arguments: dict[str, JsonValue]) -> dict[str, JsonValue]:
        is_error, payload = self.client.call_tool(name, arguments)
        if is_error:
            raise GatewayExecutionError(f'Gateway MCP {name} returned an error result')
        validate_json_value(payload)
        return payload

    def capability_standing(self, capability: str) -> GatewayCapabilityStanding:
        if not capability.startswith('execution.'):
            raise ValueError('Gateway capability standing is limited to execution.*')
        payload = self._call('capability.describe', {'capability': capability})
        projection_digest = _required_text(
            _field(payload, 'projection_digest', 'projectionDigest'), 'capability projection digest'
        )
        values = payload.get('capabilities')
        if not isinstance(values, list):
            raise GatewayExecutionError('Gateway capability projection omitted capabilities')
        matches = [
            item
            for item in values
            if isinstance(item, dict) and item.get('capability') == capability
        ]
        if len(matches) != 1:
            raise GatewayExecutionError(
                'Gateway capability projection did not return exactly one capability'
            )
        item = matches[0]
        configured = item.get('configured')
        available = item.get('available')
        contexts = item.get('contexts')
        if not isinstance(configured, bool) or not isinstance(available, bool):
            raise GatewayExecutionError('Gateway capability projection omitted availability')
        if not isinstance(contexts, list) or any(not isinstance(value, str) for value in contexts):
            raise GatewayExecutionError('Gateway capability projection has invalid contexts')
        return GatewayCapabilityStanding(
            capability=capability,
            configured=configured,
            available=available,
            contexts=tuple(contexts),
            projection_digest=projection_digest,
        )

    def _resolve_after_submit_loss(
        self, request: GatewayExecutionRequest, error: Exception
    ) -> tuple[str, str]:
        try:
            resolution = self._call(
                'execution.resolve',
                {'capability': request.capability, 'requestId': request.request_id},
            )
        except Exception as resolve_error:
            raise GatewayExecutionAmbiguous(
                f'Gateway submit response lost and resolution failed: {type(resolve_error).__name__}: {resolve_error}'
            ) from error
        standing = _required_text(resolution.get('resolution'), 'execution resolution')
        if standing != 'found':
            raise GatewayExecutionAmbiguous(
                f'Gateway submit response lost; resolution is {standing}; redispatch forbidden'
            ) from error
        operation_ref = _required_text(
            _field(resolution, 'operation_ref', 'operationRef'), 'operationRef'
        )
        native_id = _required_text(_field(resolution, 'native_id', 'nativeId'), 'nativeId')
        return operation_ref, native_id

    def execute(self, request: GatewayExecutionRequest) -> GatewayExecutionResult:
        try:
            receipt = self._call('execution.submit', request.submit_arguments())
        except Exception as error:
            operation_ref, native_id = self._resolve_after_submit_loss(request, error)
        else:
            operation_ref = _required_text(
                _field(receipt, 'operation_ref', 'operationRef'), 'operationRef'
            )
            native_id = _required_text(_field(receipt, 'native_id', 'nativeId'), 'nativeId')

        last: dict[str, JsonValue] | None = None
        execution_budget = (request.timeout_ms or 60_000) / 1000 + 15.0
        deadline = time.monotonic() + execution_budget
        for _ in range(self.max_observations):
            last = self._call(
                'execution.get',
                {'operationRef': operation_ref, 'eventLimit': 10},
            )
            observed_native = _required_text(
                _field(last, 'native_id', 'nativeId'), 'observation nativeId'
            )
            if observed_native != native_id:
                raise GatewayExecutionError('Gateway observation changed native execution identity')
            terminal = _field(last, 'terminal', 'terminal')
            if terminal is True:
                artifact_ids = _field(last, 'artifact_ids', 'artifactIds') or []
                if not isinstance(artifact_ids, list) or any(
                    not isinstance(item, str) for item in artifact_ids
                ):
                    raise GatewayExecutionError('Gateway observation artifact ids are invalid')
                exit_code = _field(last, 'exit_code', 'exitCode')
                if exit_code is not None and type(exit_code) is not int:
                    raise GatewayExecutionError('Gateway observation exit code is invalid')
                recovery = _field(last, 'recovery_required', 'recoveryRequired')
                if recovery is None:
                    recovery = False
                if not isinstance(recovery, bool):
                    raise GatewayExecutionError('Gateway observation recoveryRequired is invalid')
                return GatewayExecutionResult(
                    operation_ref=operation_ref,
                    native_id=native_id,
                    state=_required_text(last.get('state'), 'execution state'),
                    exit_code=exit_code,
                    artifact_ids=tuple(artifact_ids),
                    recovery_required=recovery,
                )
            if terminal is not False:
                raise GatewayExecutionError('Gateway observation omitted terminal')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            if self.poll_interval_seconds:
                time.sleep(min(self.poll_interval_seconds, remaining))
        state = last.get('state') if isinstance(last, dict) else None
        raise GatewayExecutionAmbiguous(
            f'Gateway execution remained non-terminal after bounded observation; state={state}'
        )

    def read_stdout(self, result: GatewayExecutionResult, *, max_bytes: int = 1_048_576) -> str:
        stdout = [item for item in result.artifact_ids if item.endswith('.stdout')]
        if len(stdout) != 1:
            raise GatewayExecutionError(
                f'Gateway execution must expose exactly one stdout artifact; observed={stdout}'
            )
        artifact_id = stdout[0]
        offset = 0
        chunks: list[str] = []
        while True:
            payload = self._call(
                'artifact.read',
                {
                    'operationRef': result.operation_ref,
                    'artifactId': artifact_id,
                    'offset': offset,
                    'maxBytes': max_bytes,
                },
            )
            observed_id = _field(payload, 'artifact_id', 'artifactId')
            if observed_id != artifact_id:
                raise GatewayExecutionError('Gateway artifact read changed artifact identity')
            content = payload.get('content')
            if not isinstance(content, str):
                raise GatewayExecutionError('Gateway artifact read omitted text content')
            chunks.append(content)
            eof = payload.get('eof')
            if eof is True:
                return ''.join(chunks)
            next_offset = _field(payload, 'next_offset', 'nextOffset')
            if type(next_offset) is not int or next_offset <= offset:
                raise GatewayExecutionError('Gateway artifact pagination did not advance')
            offset = next_offset


__all__ = [
    'GatewayCapabilityStanding',
    'GatewayExecutionAmbiguous',
    'GatewayExecutionError',
    'GatewayExecutionPort',
    'GatewayExecutionRequest',
    'GatewayExecutionResult',
]
