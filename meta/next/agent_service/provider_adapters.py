from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from .delivery import TransportBinding
from .failover import (
    ExecutionQuiescenceObservation,
    ExecutionQuiescenceProofRecord,
    ReplaySafetyObservation,
)
from .trust import RemoteDeliverySnapshot


class ProviderProtocolError(RuntimeError):
    """Provider response violated a protocol or correlation contract."""


class QuiescencePending(RuntimeError):
    """The quiescence request is durable but the provider has not proved stopped execution yet."""


class RemoteExecutionCompleted(RuntimeError):
    """Provider reports completed execution; route to R11 evidence verification instead of failover."""




class ProviderRemoteError(RuntimeError):
    def __init__(self, method: str, error: object) -> None:
        super().__init__(f"provider RPC {method} failed")
        self.method = method
        self.error = error


def _safe_http_endpoint(endpoint: str) -> None:
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme == "https":
        return
    if parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}:
        return
    raise ValueError("provider endpoint must use HTTPS unless it is loopback HTTP")


def _merge_headers(base: dict[str, str], extra: dict[str, str] | None) -> dict[str, str]:
    if extra is None:
        return base
    reserved = {key.lower() for key in base}
    for key, value in extra.items():
        if not isinstance(key, str) or not isinstance(value, str) or not key.strip():
            raise ValueError("provider headers must be non-empty strings")
        if "\r" in key or "\n" in key or "\r" in value or "\n" in value:
            raise ValueError("provider headers must not contain CR/LF")
        if key.lower() in reserved:
            raise ValueError(f"provider header override is not allowed: {key}")
        base[key] = value
    return base


def _parse_json_rpc_response(method: str, request_identity: str, status: int, body: bytes) -> dict[str, Any]:
    try:
        message = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProviderProtocolError("provider returned invalid JSON") from error
    if not isinstance(message, dict):
        raise ProviderProtocolError("provider JSON-RPC response must be an object")
    if message.get("id") != request_identity:
        raise ProviderProtocolError("provider JSON-RPC response id mismatch")
    rpc_error = message.get("error")
    if status >= 400 or isinstance(rpc_error, dict):
        raise ProviderRemoteError(method, rpc_error if isinstance(rpc_error, dict) else message)
    result = message.get("result")
    if not isinstance(result, dict):
        raise ProviderProtocolError("provider JSON-RPC response omitted result object")
    return result


HeaderProvider = Callable[[TransportBinding], dict[str, str]]
A2AVersionResolver = Callable[[TransportBinding], str]


class A2AJsonRpcHttpClient:
    """Current A2A JSON-RPC HTTP caller with explicit per-Binding protocol version."""

    def __init__(
        self,
        protocol_version: str | A2AVersionResolver | None = None,
        *,
        header_provider: HeaderProvider | None = None,
        timeout_seconds: float = 20.0,
        opener: Callable[..., Any] = urllib.request.urlopen,
    ) -> None:
        self._protocol_version = protocol_version
        self._header_provider = header_provider
        self._timeout_seconds = float(timeout_seconds)
        self._opener = opener

    def __repr__(self) -> str:
        return "A2AJsonRpcHttpClient(protocol_version=<configured>, headers=<provider>)"

    def __call__(
        self,
        *,
        binding: TransportBinding,
        method: str,
        params: dict[str, Any],
        request_identity: str,
    ) -> dict[str, Any]:
        _safe_http_endpoint(binding.endpoint)
        configured_version = (
            self._protocol_version(binding)
            if callable(self._protocol_version)
            else self._protocol_version
        )
        bound_version = getattr(binding, "protocol_version", None)
        if (
            isinstance(bound_version, str)
            and bound_version
            and isinstance(configured_version, str)
            and configured_version
            and bound_version != configured_version.strip()
        ):
            raise ValueError("configured A2A protocol version conflicts with immutable Binding")
        version = bound_version or configured_version
        if not isinstance(version, str) or not version.strip():
            raise ValueError("A2A protocol version is absent from Binding and client configuration")
        payload = {
            "jsonrpc": "2.0",
            "id": request_identity,
            "method": method,
            "params": params,
        }
        headers = _merge_headers(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "A2A-Version": version.strip(),
            },
            None if self._header_provider is None else self._header_provider(binding),
        )
        request = urllib.request.Request(
            binding.endpoint,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                status = int(response.status)
                body = response.read()
        except urllib.error.HTTPError as error:
            status = int(error.code)
            body = error.read()
        return _parse_json_rpc_response(method, request_identity, status, body)


class MCPTasksHttpClient:
    """Stateless MCP 2026-07-28 Tasks extension caller.

    Client capability and routing headers are attached to every tasks/* request.
    Credential material, when needed, is supplied by header_provider outside the
    Agent Service semantic objects.
    """

    PROTOCOL_VERSION = "2026-07-28"

    def __init__(
        self,
        *,
        header_provider: HeaderProvider | None = None,
        timeout_seconds: float = 20.0,
        opener: Callable[..., Any] = urllib.request.urlopen,
        client_name: str = "ordivon-agent-service",
        client_version: str = "r13",
    ) -> None:
        self._header_provider = header_provider
        self._timeout_seconds = float(timeout_seconds)
        self._opener = opener
        self._client_name = client_name
        self._client_version = client_version

    def __repr__(self) -> str:
        return "MCPTasksHttpClient(protocol_version='2026-07-28', headers=<provider>)"

    def __call__(
        self,
        *,
        binding: TransportBinding,
        method: str,
        params: dict[str, Any],
        request_identity: str,
    ) -> dict[str, Any]:
        _safe_http_endpoint(binding.endpoint)
        bound_version = getattr(binding, "protocol_version", None)
        if bound_version is not None and bound_version != self.PROTOCOL_VERSION:
            raise ValueError(
                "MCP Binding protocol_version does not match MCPTasksHttpClient protocol"
            )
        task_id = params.get("taskId")
        if method in {"tasks/get", "tasks/cancel", "tasks/update"} and (
            not isinstance(task_id, str) or not task_id
        ):
            raise ValueError(f"{method} requires taskId")
        effective_params = dict(params)
        effective_params["_meta"] = {
            "io.modelcontextprotocol/protocolVersion": self.PROTOCOL_VERSION,
            "io.modelcontextprotocol/clientInfo": {
                "name": self._client_name,
                "version": self._client_version,
            },
            "io.modelcontextprotocol/clientCapabilities": {
                "extensions": {
                    "io.modelcontextprotocol/tasks": {},
                }
            },
        }
        payload = {
            "jsonrpc": "2.0",
            "id": request_identity,
            "method": method,
            "params": effective_params,
        }
        base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "MCP-Protocol-Version": self.PROTOCOL_VERSION,
            "Mcp-Method": method,
        }
        if isinstance(task_id, str) and task_id:
            base_headers["Mcp-Name"] = task_id
        headers = _merge_headers(
            base_headers,
            None if self._header_provider is None else self._header_provider(binding),
        )
        request = urllib.request.Request(
            binding.endpoint,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                status = int(response.status)
                body = response.read()
        except urllib.error.HTTPError as error:
            status = int(error.code)
            body = error.read()
        return _parse_json_rpc_response(method, request_identity, status, body)

ProviderCaller = Callable[..., dict[str, Any]]


def _require_remote_task_id(receipt: Any | None, latest: RemoteDeliverySnapshot | None) -> str:
    task_id = None if receipt is None else getattr(receipt, "remote_task_id", None)
    if task_id is None and latest is not None:
        task_id = latest.remote_task_id
    if not isinstance(task_id, str) or not task_id.strip():
        raise ProviderProtocolError("remote task identity is required for provider quiescence")
    return task_id.strip()


def _expected_remote_context(receipt: Any | None, latest: RemoteDeliverySnapshot | None) -> str | None:
    context_id = None if receipt is None else getattr(receipt, "remote_context_id", None)
    if context_id is None and latest is not None:
        context_id = latest.remote_context_id
    return context_id


def _unwrap_a2a_task(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProviderProtocolError("A2A response must be an object")
    if isinstance(value.get("task"), dict):
        value = value["task"]
    task_id = value.get("id")
    status = value.get("status")
    if not isinstance(task_id, str) or not task_id:
        raise ProviderProtocolError("A2A Task omitted id")
    if not isinstance(status, dict):
        raise ProviderProtocolError("A2A Task omitted status object")
    state = status.get("state")
    if not isinstance(state, str) or not state:
        raise ProviderProtocolError("A2A Task omitted status.state")
    return value


class A2AQuiescenceAdapter:
    """A2A CancelTask/GetTask adapter for the R12 quiescence contract.

    CancelTask is idempotent at the A2A operation layer, but a successful call is not
    interpreted as quiescence unless the returned/observed Task state is terminal and
    unsuccessful. Completed execution is sent back to the R11 evidence path.
    """

    QUIESCENT_STATES = {
        "TASK_STATE_CANCELED",
        "TASK_STATE_FAILED",
        "TASK_STATE_REJECTED",
    }
    COMPLETED_STATES = {"TASK_STATE_COMPLETED"}
    PENDING_STATES = {
        "TASK_STATE_UNSPECIFIED",
        "TASK_STATE_SUBMITTED",
        "TASK_STATE_WORKING",
        "TASK_STATE_INPUT_REQUIRED",
        "TASK_STATE_AUTH_REQUIRED",
    }

    def __init__(self, caller: ProviderCaller) -> None:
        self._call = caller

    def prove_quiescence(
        self,
        *,
        quiescence_request_id: str,
        binding: TransportBinding,
        receipt: Any | None,
        envelope: Any,
        latest_observation: RemoteDeliverySnapshot | None,
    ) -> ExecutionQuiescenceObservation:
        if binding.transport != "a2a-jsonrpc":
            raise ValueError("A2AQuiescenceAdapter requires a2a-jsonrpc Binding")
        remote_task_id = _require_remote_task_id(receipt, latest_observation)
        expected_context = _expected_remote_context(receipt, latest_observation)

        try:
            task = self._call(
                binding=binding,
                method="CancelTask",
                params={"id": remote_task_id},
                request_identity=f"{quiescence_request_id}:cancel",
            )
        except ProviderRemoteError as error:
            code = error.error.get("code") if isinstance(error.error, dict) else None
            if code != -32002:
                raise
            task = self._call(
                binding=binding,
                method="GetTask",
                params={"id": remote_task_id, "historyLength": 0},
                request_identity=f"{quiescence_request_id}:get-after-not-cancelable",
            )
        task = _unwrap_a2a_task(task)
        state = self._validate_a2a_task(
            task,
            expected_task_id=remote_task_id,
            expected_context_id=expected_context,
        )
        if state in self.PENDING_STATES:
            task = self._call(
                binding=binding,
                method="GetTask",
                params={"id": remote_task_id, "historyLength": 0},
                request_identity=f"{quiescence_request_id}:get",
            )
            task = _unwrap_a2a_task(task)
            state = self._validate_a2a_task(
                task,
                expected_task_id=remote_task_id,
                expected_context_id=expected_context,
            )

        if state in self.COMPLETED_STATES:
            raise RemoteExecutionCompleted(
                f"A2A task {remote_task_id} completed; semantic verification is required"
            )
        if state in self.QUIESCENT_STATES:
            return ExecutionQuiescenceObservation(
                quiescent=True,
                provider_status=state,
                remote_task_id=remote_task_id,
                remote_context_id=expected_context,
                evidence_ref=f"a2a://{binding.id}/tasks/{remote_task_id}/status/{state}",
            )
        if state in self.PENDING_STATES:
            raise QuiescencePending(
                f"A2A task {remote_task_id} remains non-terminal after cancellation attempt: {state}"
            )
        raise ProviderProtocolError(f"unsupported A2A TaskState: {state}")

    @staticmethod
    def _validate_a2a_task(
        task: dict[str, Any],
        *,
        expected_task_id: str,
        expected_context_id: str | None,
    ) -> str:
        if task.get("id") != expected_task_id:
            raise ProviderProtocolError("A2A task identity changed during quiescence")
        observed_context = task.get("contextId")
        if expected_context_id is not None and observed_context != expected_context_id:
            raise ProviderProtocolError("A2A context identity changed during quiescence")
        status = task["status"]
        state = status["state"]
        if not isinstance(state, str) or not state:
            raise ProviderProtocolError("A2A status.state must be non-empty")
        return state


class MCPTaskQuiescenceAdapter:
    """MCP 2026-07-28 Tasks adapter.

    tasks/cancel is only an acknowledgement of cancellation intent. Quiescence is
    derived only from a subsequent tasks/get state.
    """

    QUIESCENT_STATES = {"cancelled", "failed"}
    COMPLETED_STATES = {"completed"}
    PENDING_STATES = {"working", "input_required"}

    def __init__(self, caller: ProviderCaller) -> None:
        self._call = caller

    def prove_quiescence(
        self,
        *,
        quiescence_request_id: str,
        binding: TransportBinding,
        receipt: Any | None,
        envelope: Any,
        latest_observation: RemoteDeliverySnapshot | None,
    ) -> ExecutionQuiescenceObservation:
        if binding.transport != "mcp":
            raise ValueError("MCPTaskQuiescenceAdapter requires mcp Binding")
        remote_task_id = _require_remote_task_id(receipt, latest_observation)
        remote_context_id = _expected_remote_context(receipt, latest_observation)

        ack = self._call(
            binding=binding,
            method="tasks/cancel",
            params={"taskId": remote_task_id},
            request_identity=f"{quiescence_request_id}:cancel",
        )
        if not isinstance(ack, dict):
            raise ProviderProtocolError("MCP tasks/cancel result must be an object")
        result_type = ack.get("resultType")
        if result_type is not None and result_type != "complete":
            raise ProviderProtocolError("MCP tasks/cancel acknowledgement has invalid resultType")

        task = self._call(
            binding=binding,
            method="tasks/get",
            params={"taskId": remote_task_id},
            request_identity=f"{quiescence_request_id}:get",
        )
        state = self._validate_mcp_task(task, expected_task_id=remote_task_id)

        if state in self.COMPLETED_STATES:
            raise RemoteExecutionCompleted(
                f"MCP task {remote_task_id} completed; semantic verification is required"
            )
        if state in self.QUIESCENT_STATES:
            return ExecutionQuiescenceObservation(
                quiescent=True,
                provider_status=state,
                remote_task_id=remote_task_id,
                remote_context_id=remote_context_id,
                evidence_ref=f"mcp://{binding.id}/tasks/{remote_task_id}/status/{state}",
            )
        if state in self.PENDING_STATES:
            raise QuiescencePending(
                f"MCP task {remote_task_id} remains non-terminal after cancellation acknowledgement: {state}"
            )
        raise ProviderProtocolError(f"unsupported MCP task status: {state}")

    @staticmethod
    def _validate_mcp_task(task: dict[str, Any], *, expected_task_id: str) -> str:
        if not isinstance(task, dict):
            raise ProviderProtocolError("MCP tasks/get result must be an object")
        result_type = task.get("resultType")
        if result_type is not None and result_type != "complete":
            raise ProviderProtocolError("MCP tasks/get resultType must be complete")
        if task.get("taskId") != expected_task_id:
            raise ProviderProtocolError("MCP task identity changed during quiescence")
        state = task.get("status")
        if not isinstance(state, str) or not state:
            raise ProviderProtocolError("MCP tasks/get omitted task status")
        return state


@dataclass(frozen=True)
class EffectLedgerEffect:
    effect_id: str
    state: str
    idempotency_key: str | None
    replay_target_binding_id: str | None
    evidence_ref: str


@dataclass(frozen=True)
class EffectLedgerSnapshot:
    task_id: str
    source_binding_id: str
    target_binding_id: str
    complete: bool
    effects: tuple[EffectLedgerEffect, ...]
    evidence_ref: str




class EffectLedgerReplaySafetyAdapter:
    """Derive R12 replay classifications from explicit effect/idempotency evidence.

    Absence of effect rows is only NO_EFFECTS when the snapshot is explicitly marked
    complete. A committed effect is replay-safe only when the ledger binds a non-empty
    idempotency key to the exact fallback Binding.
    """

    EFFECT_STATES = {
        "COMMITTED",
        "ROLLED_BACK",
        "COMPENSATED",
        "PARTIAL",
        "UNKNOWN",
    }

    def __init__(self, reader: Any) -> None:
        if not callable(getattr(reader, "read_replay_snapshot", None)):
            raise TypeError(
                "effect-ledger reader must expose callable read_replay_snapshot()"
            )
        self._reader = reader

    def evaluate_replay_safety(
        self,
        *,
        replay_safety_request_id: str,
        task: Any,
        envelope: Any,
        source_binding: TransportBinding,
        target_binding: TransportBinding,
        quiescence_proof: ExecutionQuiescenceProofRecord,
        source_receipt: Any | None,
        source_observations: tuple[RemoteDeliverySnapshot, ...],
    ) -> ReplaySafetyObservation:
        snapshot = self._reader.read_replay_snapshot(
            task=task,
            envelope=envelope,
            source_binding=source_binding,
            target_binding=target_binding,
            quiescence_proof=quiescence_proof,
            source_receipt=source_receipt,
            source_observations=source_observations,
        )
        if not isinstance(snapshot, EffectLedgerSnapshot):
            raise TypeError("effect-ledger reader must return EffectLedgerSnapshot")
        return self._evaluate_snapshot(
            snapshot,
            expected_task_id=task.id,
            expected_source_binding_id=source_binding.id,
            expected_target_binding_id=target_binding.id,
        )

    @staticmethod
    def _evaluate_snapshot(
        snapshot: EffectLedgerSnapshot,
        *,
        expected_task_id: str,
        expected_source_binding_id: str,
        expected_target_binding_id: str,
    ) -> ReplaySafetyObservation:
        if snapshot.task_id != expected_task_id:
            raise ProviderProtocolError("effect ledger snapshot Task identity mismatch")
        if snapshot.source_binding_id != expected_source_binding_id:
            raise ProviderProtocolError("effect ledger snapshot source Binding mismatch")
        if snapshot.target_binding_id != expected_target_binding_id:
            raise ProviderProtocolError("effect ledger snapshot target Binding mismatch")
        if not isinstance(snapshot.evidence_ref, str) or not snapshot.evidence_ref.strip():
            raise ProviderProtocolError("effect ledger snapshot evidence_ref must be non-empty")

        seen_ids: set[str] = set()
        normalized: list[EffectLedgerEffect] = []
        for effect in snapshot.effects:
            if not isinstance(effect, EffectLedgerEffect):
                raise ProviderProtocolError("effect ledger entries must be EffectLedgerEffect")
            if not isinstance(effect.effect_id, str) or not effect.effect_id.strip():
                raise ProviderProtocolError("effect ledger effect_id must be non-empty")
            if effect.effect_id in seen_ids:
                raise ProviderProtocolError("effect ledger contains duplicate effect identity")
            seen_ids.add(effect.effect_id)
            state = effect.state.strip().upper() if isinstance(effect.state, str) else ""
            if state not in EffectLedgerReplaySafetyAdapter.EFFECT_STATES:
                raise ProviderProtocolError(f"unsupported effect ledger state: {effect.state!r}")
            if not isinstance(effect.evidence_ref, str) or not effect.evidence_ref.strip():
                raise ProviderProtocolError("effect ledger effect evidence_ref must be non-empty")
            normalized.append(
                EffectLedgerEffect(
                    effect_id=effect.effect_id.strip(),
                    state=state,
                    idempotency_key=None if effect.idempotency_key is None else effect.idempotency_key.strip(),
                    replay_target_binding_id=effect.replay_target_binding_id,
                    evidence_ref=effect.evidence_ref.strip(),
                )
            )

        if not snapshot.complete:
            return ReplaySafetyObservation(
                safe=False,
                classification="UNKNOWN",
                reason="effect ledger coverage is incomplete",
                evidence_ref=snapshot.evidence_ref,
            )
        if not normalized:
            return ReplaySafetyObservation(
                safe=True,
                classification="NO_EFFECTS",
                reason=None,
                evidence_ref=snapshot.evidence_ref,
            )

        states = {effect.state for effect in normalized}
        if "UNKNOWN" in states:
            return ReplaySafetyObservation(
                safe=False,
                classification="UNKNOWN",
                reason="effect ledger contains unknown effect state",
                evidence_ref=snapshot.evidence_ref,
            )
        if "PARTIAL" in states:
            return ReplaySafetyObservation(
                safe=False,
                classification="PARTIAL_EFFECTS",
                reason="effect ledger contains partial/unresolved side effects",
                evidence_ref=snapshot.evidence_ref,
            )

        committed = [effect for effect in normalized if effect.state == "COMMITTED"]
        if committed:
            replay_protected = all(
                isinstance(effect.idempotency_key, str)
                and bool(effect.idempotency_key)
                and effect.replay_target_binding_id == expected_target_binding_id
                for effect in committed
            )
            if replay_protected:
                return ReplaySafetyObservation(
                    safe=True,
                    classification="IDEMPOTENT_REPLAY",
                    reason=None,
                    evidence_ref=snapshot.evidence_ref,
                )
            return ReplaySafetyObservation(
                safe=False,
                classification="PARTIAL_EFFECTS",
                reason="committed effects are not idempotency-protected for the exact fallback Binding",
                evidence_ref=snapshot.evidence_ref,
            )

        if states == {"ROLLED_BACK"}:
            return ReplaySafetyObservation(
                safe=True,
                classification="ROLLED_BACK",
                reason=None,
                evidence_ref=snapshot.evidence_ref,
            )
        if states.issubset({"ROLLED_BACK", "COMPENSATED"}) and "COMPENSATED" in states:
            return ReplaySafetyObservation(
                safe=True,
                classification="COMPENSATED",
                reason=None,
                evidence_ref=snapshot.evidence_ref,
            )

        return ReplaySafetyObservation(
            safe=False,
            classification="UNKNOWN",
            reason="effect ledger state combination is not replay-safe",
            evidence_ref=snapshot.evidence_ref,
        )
