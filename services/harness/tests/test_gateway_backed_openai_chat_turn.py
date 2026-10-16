from __future__ import annotations

import inspect
import json
import unittest

from anc_canonical import canonical_bytes, canonical_digest

from ordivon_harness.ordivon.gateway_provider import HarnessGatewayProviderBinding
from ordivon_harness.ordivon.gateway_turn import GatewayBackedOpenAIChatTurnAdapter
from ordivon_harness.ordivon.model import AgentTurnRequest


MODEL = "cohere/north-mini-code:free"


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def _binding(**overrides: object) -> HarnessGatewayProviderBinding:
    values: dict[str, object] = {
        "gateway_implementation": "CCSwitch",
        "gateway_source_identity": "cc-switch-cli:v5.11.1",
        "endpoint": "http://127.0.0.1:18422",
        "ingress_protocol": "openai-chat",
        "capability_profile_digest": _digest("openrouter-capabilities"),
        "requested_provider": "openrouter",
        "requested_model": MODEL,
        "credential_authority_ref": "runtime:credential-authority:openrouter-provider",
        "credential_name_ref": "api_key",
        "network_authority_ref": "network-v2:model-provider",
        "network_egress_profile_ref": "model-provider",
        "direct_fallback": False,
        "allowed_effective_providers": ("openrouter",),
    }
    values.update(overrides)
    return HarnessGatewayProviderBinding(**values)  # type: ignore[arg-type]


def _request() -> AgentTurnRequest:
    return AgentTurnRequest(
        harness_run_id="harness-run:openrouter-gateway",
        turn_id="turn:openrouter-gateway:1",
        sequence=1,
        assignment_id="assignment:openrouter-gateway",
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
            "id": "provider-call:openrouter-fixture",
            "model": MODEL,
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


class RecordingTransport:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int,
    ) -> bytes:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "body": bytes(body),
                "timeoutSeconds": timeout_seconds,
                "maxResponseBytes": max_response_bytes,
            }
        )
        return self.response


class GatewayBackedOpenAIChatTurnAdapterTests(unittest.TestCase):
    def test_openrouter_route_reuses_codec_without_provider_secret_surface(self) -> None:
        transport = RecordingTransport(_response())
        adapter = GatewayBackedOpenAIChatTurnAdapter(
            _binding(),
            transport=transport,
            max_output_tokens=512,
        )
        result = adapter.invoke(_request())

        self.assertEqual(result.model_id, MODEL)
        self.assertEqual(len(transport.calls), 1)
        call = transport.calls[0]
        self.assertEqual(call["url"], "http://127.0.0.1:18422/v1/chat/completions")
        body = json.loads(call["body"])
        self.assertEqual(body["model"], MODEL)
        headers = call["headers"]
        assert isinstance(headers, dict)
        self.assertNotIn("Authorization", headers)
        self.assertNotIn("ordivon-gateway-codec-not-a-provider-secret", repr(call))

    def test_binding_is_single_provider_and_fail_closed(self) -> None:
        cases = (
            _binding(ingress_protocol="openai-responses"),
            _binding(direct_fallback=True),
            _binding(allowed_effective_providers=("openrouter", "deepseek")),
            _binding(allowed_effective_providers=("deepseek",)),
            _binding(credential_name_ref=None),
            _binding(network_egress_profile_ref=None),
        )
        for binding in cases:
            with self.subTest(binding=binding):
                with self.assertRaises(ValueError):
                    GatewayBackedOpenAIChatTurnAdapter(binding)

    def test_adapter_has_no_provider_credential_or_retry_authority(self) -> None:
        signature = inspect.signature(GatewayBackedOpenAIChatTurnAdapter)
        self.assertNotIn("api_key", signature.parameters)
        adapter = GatewayBackedOpenAIChatTurnAdapter(_binding())
        for name in (
            "retry",
            "fallback",
            "materialize_credential",
            "select_credential",
            "select_network",
            "switch_provider",
        ):
            self.assertFalse(hasattr(adapter, name), name)

    def test_effective_model_identity_is_exact(self) -> None:
        adapter = GatewayBackedOpenAIChatTurnAdapter(_binding())
        self.assertTrue(adapter.accepts_effective_model_id(MODEL))
        self.assertFalse(adapter.accepts_effective_model_id("openrouter/free"))
        self.assertFalse(adapter.accepts_effective_model_id("openai/gpt-4.1-mini"))

    def test_request_identity_binds_provider_model_and_binding(self) -> None:
        request = _request()
        first = GatewayBackedOpenAIChatTurnAdapter(_binding())
        second = GatewayBackedOpenAIChatTurnAdapter(
            _binding(capability_profile_digest=_digest("openrouter-capabilities-v2"))
        )
        self.assertNotEqual(
            first.provider_request_digest(request),
            second.provider_request_digest(request),
        )
        self.assertEqual(
            first.gateway_request_digest(request),
            first.provider_request_digest(request),
        )


if __name__ == "__main__":
    unittest.main()
