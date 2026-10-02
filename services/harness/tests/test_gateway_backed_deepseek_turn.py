from __future__ import annotations

import inspect
import json
from pathlib import Path
import tempfile
import unittest

from anc_canonical import canonical_bytes, canonical_digest

from ordivon_harness.core_contracts import HarnessBoundReference, HarnessRunContract
from ordivon_harness.ordivon.deepseek import DeepSeekSettings, DeepSeekTurnAdapter
from ordivon_harness.ordivon.gateway_provider import HarnessGatewayProviderBinding
from ordivon_harness.ordivon.gateway_turn import GatewayBackedDeepSeekTurnAdapter
from ordivon_harness.ordivon.loop import OrdivonAgentLoop, RunBudget, RunStopCode
from ordivon_harness.ordivon.model import (
    AgentTurnAdapterError,
    AgentTurnDispatchSafety,
    AgentTurnFailureCode,
    AgentTurnRequest,
)
from ordivon_harness.ordivon.sqlite_agent_bridge import (
    NO_TOOL_AGENT_SURFACE_DIGEST,
    SQLiteHarnessAgentBridge,
)
from ordivon_harness.ordivon.sqlite_run_store import SQLiteHarnessRunContinuityStore
from ordivon_harness.protocol import HarnessProviderCallStatus
from ordivon_harness.sqlite_store import SQLiteHarnessStore


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def _binding(**overrides: object) -> HarnessGatewayProviderBinding:
    values: dict[str, object] = {
        "gateway_implementation": "CLIProxyAPI",
        "gateway_source_identity": "git:router-for-me/CLIProxyAPI@fixture",
        "endpoint": "http://127.0.0.1:18317",
        "ingress_protocol": "openai-chat",
        "capability_profile_digest": _digest("capabilities"),
        "requested_provider": "deepseek",
        "requested_model": "deepseek-v4-flash",
        "credential_authority_ref": "runtime:credential-authority:deepseek-provider",
        "credential_name_ref": "api_key",
        "network_authority_ref": "network-v2:model-provider",
        "network_egress_profile_ref": "model-provider",
        "direct_fallback": False,
        "allowed_effective_providers": ("deepseek",),
    }
    values.update(overrides)
    return HarnessGatewayProviderBinding(**values)  # type: ignore[arg-type]


def _request() -> AgentTurnRequest:
    return AgentTurnRequest(
        harness_run_id="harness-run:gateway-differential",
        turn_id="turn:gateway-differential:1",
        sequence=1,
        assignment_id="assignment:gateway-differential",
        context_digest=_digest("context"),
        tool_catalog_digest=_digest("tools"),
        messages=({"role": "user", "content": "finish"},),
        tools=(),
        remaining_budget={
            "modelCalls": 1,
            "toolCalls": 0,
            "totalTokens": 4096,
        },
    )


def _response() -> bytes:
    return canonical_bytes(
        {
            "id": "provider-call:gateway-fixture",
            "model": "deepseek-v4-flash",
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "toolcall:conclude",
                                "type": "function",
                                "function": {
                                    "name": "submit_run_conclusion",
                                    "arguments": json.dumps(
                                        {
                                            "status": "candidate_completed",
                                            "summary": "done",
                                            "artifact_refs": [],
                                            "evidence_refs": [],
                                            "unresolved_unknowns": [],
                                        },
                                        separators=(",", ":"),
                                    ),
                                },
                            }
                        ],
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 5,
                "total_tokens": 25,
            },
        }
    )


class RecordingHandle:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.cancelled = False

    def poll(self, timeout_seconds: float) -> bytes | None:
        if self.cancelled:
            raise AssertionError("poll after cancellation")
        return self.response

    def cancel(self) -> None:
        self.cancelled = True


class RecordingTransport:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def _record(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> None:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "body": bytes(body),
                "timeoutSeconds": timeout_seconds,
                "maxResponseBytes": max_response_bytes,
            }
        )

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes:
        self._record(
            url,
            headers=headers,
            body=body,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
        )
        return self.response

    def start_post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> RecordingHandle:
        self._record(
            url,
            headers=headers,
            body=body,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
        )
        return RecordingHandle(self.response)


class ErrorTransport:
    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes:
        raise AgentTurnAdapterError(
            "synthetic provider rejection",
            failure_code=AgentTurnFailureCode.REJECTED,
            dispatch_safety=AgentTurnDispatchSafety.PROVIDER_REJECTED,
        )


class FixedClock:
    def __init__(self, value: int = 1_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


def _run_contract() -> HarnessRunContract:
    return HarnessRunContract(
        harness_run_id="harness-run:gateway-backed-loop",
        harness_implementation_id="ordivon-harness@gateway-test",
        caller_id="caller:gateway-test",
        caller_run_ref="trial:gateway-backed-loop",
        objective_ref=HarnessBoundReference(
            "objective:gateway-backed-loop",
            "objective",
            _digest("objective"),
        ),
        context_refs=(
            HarnessBoundReference(
                "context:gateway-backed-loop",
                "context",
                _digest("context-loop"),
            ),
        ),
        provider_id="provider:gateway-deepseek",
        adapter_id=GatewayBackedDeepSeekTurnAdapter.adapter_id,
        requested_model_id="deepseek-v4-flash",
        tool_catalog_digest=NO_TOOL_AGENT_SURFACE_DIGEST,
        tool_grant_digest=canonical_digest(
            {
                "schemaVersion": 1,
                "kind": "ordivon.no-tool-grant",
                "tools": [],
            }
        ),
        budget={
            "maxModelCalls": 1,
            "maxToolCalls": 0,
            "maxWallTimeMs": 10_000,
        },
        completion_contract={"mode": "record"},
        system_manifest_ref=HarnessBoundReference(
            "system-manifest:gateway-backed-loop",
            "system-manifest",
            _digest("system-manifest"),
        ),
        created_at_ms=1_000,
    )


class GatewayBackedDeepSeekTurnAdapterTests(unittest.TestCase):
    def test_direct_and_gateway_paths_share_exact_codec_body_and_result(self) -> None:
        response = _response()
        direct_transport = RecordingTransport(response)
        gateway_transport = RecordingTransport(response)
        direct = DeepSeekTurnAdapter(
            DeepSeekSettings(
                api_key="d" * 40,
                model="deepseek-v4-flash",
                max_output_tokens=512,
            ),
            transport=direct_transport,
        )
        gateway = GatewayBackedDeepSeekTurnAdapter(
            _binding(),
            gateway_access_token="local-gateway-client-token",
            transport=gateway_transport,
            max_output_tokens=512,
        )
        request = _request()

        direct_result = direct.invoke(request)
        gateway_result = gateway.invoke(request)

        self.assertEqual(gateway_result.to_dict(), direct_result.to_dict())
        self.assertEqual(len(direct_transport.calls), 1)
        self.assertEqual(len(gateway_transport.calls), 1)
        direct_call = direct_transport.calls[0]
        gateway_call = gateway_transport.calls[0]
        self.assertEqual(gateway_call["body"], direct_call["body"])
        self.assertEqual(
            gateway_call["url"],
            "http://127.0.0.1:18317/v1/chat/completions",
        )
        headers = gateway_call["headers"]
        assert isinstance(headers, dict)
        self.assertEqual(
            headers["Authorization"],
            "Bearer local-gateway-client-token",
        )
        self.assertNotIn("d" * 40, repr(gateway_call))
        self.assertNotIn("ordivon-gateway-codec-not-a-provider-secret", repr(gateway_call))

    def test_gateway_without_client_token_emits_no_authorization_header(self) -> None:
        transport = RecordingTransport(_response())
        adapter = GatewayBackedDeepSeekTurnAdapter(
            _binding(),
            transport=transport,
            max_output_tokens=512,
        )
        adapter.invoke(_request())
        headers = transport.calls[0]["headers"]
        assert isinstance(headers, dict)
        self.assertNotIn("Authorization", headers)

    def test_request_identity_binds_gateway_evidence_not_client_token(self) -> None:
        request = _request()
        first = GatewayBackedDeepSeekTurnAdapter(
            _binding(),
            gateway_access_token="local-token-one",
            transport=RecordingTransport(_response()),
        )
        second = GatewayBackedDeepSeekTurnAdapter(
            _binding(),
            gateway_access_token="local-token-two",
            transport=RecordingTransport(_response()),
        )
        changed_binding = GatewayBackedDeepSeekTurnAdapter(
            _binding(capability_profile_digest=_digest("capabilities-v2")),
            gateway_access_token="local-token-one",
            transport=RecordingTransport(_response()),
        )

        self.assertEqual(
            first.provider_request_digest(request),
            second.provider_request_digest(request),
        )
        self.assertNotEqual(
            first.provider_request_digest(request),
            changed_binding.provider_request_digest(request),
        )
        self.assertEqual(
            first.gateway_request_digest(request),
            first.provider_request_digest(request),
        )

    def test_binding_guard_rejects_authority_broadening(self) -> None:
        cases = (
            _binding(ingress_protocol="openai-responses"),
            _binding(requested_provider="openrouter"),
            _binding(direct_fallback=True),
            _binding(allowed_effective_providers=("deepseek", "openrouter")),
            _binding(credential_name_ref=None),
            _binding(network_egress_profile_ref=None),
        )
        for binding in cases:
            with self.subTest(binding=binding):
                with self.assertRaises(ValueError):
                    GatewayBackedDeepSeekTurnAdapter(
                        binding,
                        transport=RecordingTransport(_response()),
                    )

    def test_adapter_has_no_provider_credential_or_retry_authority_surface(self) -> None:
        signature = inspect.signature(GatewayBackedDeepSeekTurnAdapter)
        self.assertNotIn("api_key", signature.parameters)
        adapter = GatewayBackedDeepSeekTurnAdapter(
            _binding(),
            transport=RecordingTransport(_response()),
        )
        for name in (
            "retry",
            "fallback",
            "materialize_credential",
            "select_credential",
            "select_network",
        ):
            self.assertFalse(hasattr(adapter, name), name)

    def test_effective_model_validation_is_delegated_to_existing_codec(self) -> None:
        adapter = GatewayBackedDeepSeekTurnAdapter(
            _binding(),
            transport=RecordingTransport(_response()),
        )
        self.assertTrue(adapter.accepts_effective_model_id("deepseek-v4-flash"))
        self.assertTrue(adapter.accepts_effective_model_id("deepseek-flash"))
        self.assertFalse(adapter.accepts_effective_model_id("openrouter/auto"))

    def test_gateway_failure_preserves_provider_rejected_dispatch_safety(self) -> None:
        adapter = GatewayBackedDeepSeekTurnAdapter(
            _binding(),
            transport=ErrorTransport(),
        )
        with self.assertRaises(AgentTurnAdapterError) as raised:
            adapter.invoke(_request())
        self.assertEqual(
            raised.exception.failure_code,
            AgentTurnFailureCode.REJECTED,
        )
        self.assertEqual(
            raised.exception.dispatch_safety,
            AgentTurnDispatchSafety.PROVIDER_REJECTED,
        )
        self.assertIn("Gateway-backed DeepSeek call failed", str(raised.exception))

    def test_real_agent_loop_uses_existing_durable_provider_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "state"
            clock = FixedClock()
            contract = _run_contract()
            store = SQLiteHarnessStore.initialize(root)
            store.create_run(contract)
            continuity = SQLiteHarnessRunContinuityStore(
                store,
                contract,
                clock_ms=clock,
            )
            transport = RecordingTransport(_response())
            adapter = GatewayBackedDeepSeekTurnAdapter(
                _binding(),
                gateway_access_token="local-gateway-client-token",
                transport=transport,
                max_output_tokens=512,
            )
            bridge = SQLiteHarnessAgentBridge(contract, continuity)
            loop = OrdivonAgentLoop(
                adapter,
                bridge,
                budget=RunBudget(
                    max_model_calls=1,
                    max_tool_calls=0,
                    max_observation_bytes=16_384,
                    max_wall_time_ms=10_000,
                    max_total_tokens=10_000,
                    max_model_retries=0,
                ),
                clock_ms=clock,
                monotonic_ms=clock,
            )

            result = loop.run(
                harness_run_id=contract.harness_run_id,
                assignment_id=continuity.binding.assignment_id,
                context_digest=contract.context_refs[0].digest,
                initial_messages=({"role": "user", "content": "finish"},),
            )

            self.assertTrue(result.candidate_completed)
            self.assertEqual(result.stop_code, RunStopCode.CANDIDATE_COMPLETED)
            self.assertEqual(result.model_calls, 1)
            self.assertEqual(len(transport.calls), 1)
            retained = continuity.load_current_provider_call()
            self.assertEqual(retained.record.status, HarnessProviderCallStatus.COMPLETED)
            self.assertEqual(
                retained.record.adapter_id,
                GatewayBackedDeepSeekTurnAdapter.adapter_id,
            )
            self.assertEqual(retained.record.requested_model_id, "deepseek-v4-flash")
            self.assertTrue(
                retained.record.provider_request_digest.startswith("sha256:")
            )
            self.assertEqual(len(retained.record.provider_request_digest), 71)
            store.close()


if __name__ == "__main__":
    unittest.main()
