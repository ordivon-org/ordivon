from __future__ import annotations

import unittest

from anc_canonical import canonical_digest

from ordivon_harness.ordivon.gateway_provider import (
    HarnessGatewayAttemptObservation,
    HarnessGatewayProviderBinding,
    HarnessGatewayProviderCallObservation,
)
from ordivon_harness.protocol import HarnessProtocolError


def _digest(label: str) -> str:
    return canonical_digest({"fixture": label})


def _binding() -> HarnessGatewayProviderBinding:
    return HarnessGatewayProviderBinding(
        gateway_implementation="CLIProxyAPI",
        gateway_source_identity="git:router-for-me/CLIProxyAPI@fixture",
        endpoint="http://127.0.0.1:8317",
        ingress_protocol="openai-chat",
        capability_profile_digest=_digest("capabilities"),
        requested_provider="deepseek",
        requested_model="deepseek-v4-flash",
        credential_authority_ref="openrouter-provider",
        credential_name_ref="provider-key",
        network_authority_ref="network-v2:provider-egress",
        network_egress_profile_ref="model-provider",
        direct_fallback=False,
        allowed_effective_providers=("deepseek",),
    )


class GatewayProviderBindingTests(unittest.TestCase):
    def test_round_trip_has_stable_digest_and_no_secret_surface(self) -> None:
        binding = _binding()
        decoded = HarnessGatewayProviderBinding.from_dict(binding.to_dict())
        self.assertEqual(decoded, binding)
        self.assertEqual(decoded.digest, canonical_digest(binding.to_dict()))
        encoded = binding.to_dict()
        self.assertNotIn("apiKey", encoded)
        self.assertNotIn("secret", encoded)
        self.assertNotIn("headers", encoded)

    def test_endpoint_must_be_loopback_and_cannot_embed_credentials(self) -> None:
        value = _binding().to_dict()
        for endpoint in (
            "https://gateway.example.com:443",
            "http://user:pass@127.0.0.1:8317",
            "http://127.0.0.1",
        ):
            with self.subTest(endpoint=endpoint):
                malformed = dict(value)
                malformed["endpoint"] = endpoint
                with self.assertRaises(HarnessProtocolError):
                    HarnessGatewayProviderBinding.from_dict(malformed)

    def test_unknown_fields_fail_closed(self) -> None:
        value = _binding().to_dict()
        value["execute"] = True
        with self.assertRaises(HarnessProtocolError):
            HarnessGatewayProviderBinding.from_dict(value)

    def test_binding_is_evidence_only_not_an_execution_port(self) -> None:
        binding = _binding()
        for name in ("invoke", "dispatch", "retry", "cancel", "materialize_credential"):
            self.assertFalse(hasattr(binding, name), name)


class GatewayProviderCallObservationTests(unittest.TestCase):
    def test_committed_attempt_round_trips_and_matches_effective_identity(self) -> None:
        binding = _binding()
        observation = HarnessGatewayProviderCallObservation(
            binding_digest=binding.digest,
            provider_call_ref="provider-call:fixture:1",
            gateway_request_digest=_digest("gateway-request"),
            translator_path=("openai-chat", "provider-openai-compatible"),
            attempts=(
                HarnessGatewayAttemptObservation(
                    sequence=1,
                    provider="deepseek",
                    model="deepseek-v4-flash",
                    standing="failed_before_commit",
                    connection_ref="connection:one",
                    retry_or_fallback_reason="synthetic 429",
                    provider_request_id="request:one",
                ),
                HarnessGatewayAttemptObservation(
                    sequence=2,
                    provider="deepseek",
                    model="deepseek-v4-flash",
                    standing="committed",
                    connection_ref="connection:two",
                    retry_or_fallback_reason="same-provider fallback",
                    provider_request_id="request:two",
                ),
            ),
            effective_provider="deepseek",
            effective_model="deepseek-v4-flash",
            effective_connection_ref="connection:two",
            stream_terminal_standing="not_streaming",
            response_digest=_digest("response"),
            evidence_refs=("runtime:job:fixture",),
        )
        decoded = HarnessGatewayProviderCallObservation.from_dict(
            observation.to_dict()
        )
        self.assertEqual(decoded, observation)
        self.assertEqual(decoded.digest, canonical_digest(observation.to_dict()))

    def test_dispatched_unknown_fences_later_attempts(self) -> None:
        binding = _binding()
        with self.assertRaisesRegex(HarnessProtocolError, "dispatched_unknown"):
            HarnessGatewayProviderCallObservation(
                binding_digest=binding.digest,
                provider_call_ref="provider-call:fixture:unknown",
                gateway_request_digest=_digest("gateway-request"),
                attempts=(
                    HarnessGatewayAttemptObservation(
                        sequence=1,
                        provider="deepseek",
                        model="deepseek-v4-flash",
                        standing="dispatched_unknown",
                    ),
                    HarnessGatewayAttemptObservation(
                        sequence=2,
                        provider="deepseek",
                        model="deepseek-v4-flash",
                        standing="committed",
                    ),
                ),
                effective_provider="deepseek",
                effective_model="deepseek-v4-flash",
                stream_terminal_standing="unknown",
                response_digest=_digest("response"),
            )

    def test_committed_identity_must_match_terminal_attempt(self) -> None:
        binding = _binding()
        attempt = HarnessGatewayAttemptObservation(
            sequence=1,
            provider="deepseek",
            model="deepseek-v4-flash",
            standing="committed",
        )
        with self.assertRaisesRegex(HarnessProtocolError, "effective Provider"):
            HarnessGatewayProviderCallObservation(
                binding_digest=binding.digest,
                provider_call_ref="provider-call:fixture:mismatch",
                gateway_request_digest=_digest("gateway-request"),
                attempts=(attempt,),
                effective_provider="openrouter",
                effective_model="deepseek-v4-flash",
                stream_terminal_standing="complete",
                response_digest=_digest("response"),
            )

    def test_noncommitted_observation_cannot_claim_effective_identity(self) -> None:
        binding = _binding()
        attempt = HarnessGatewayAttemptObservation(
            sequence=1,
            provider="deepseek",
            model="deepseek-v4-flash",
            standing="failed_before_commit",
        )
        with self.assertRaisesRegex(HarnessProtocolError, "cannot claim effective"):
            HarnessGatewayProviderCallObservation(
                binding_digest=binding.digest,
                provider_call_ref="provider-call:fixture:failed",
                gateway_request_digest=_digest("gateway-request"),
                attempts=(attempt,),
                effective_provider="deepseek",
                effective_model="deepseek-v4-flash",
                stream_terminal_standing="not_streaming",
            )

    def test_observation_is_evidence_only_not_retry_authority(self) -> None:
        binding = _binding()
        observation = HarnessGatewayProviderCallObservation(
            binding_digest=binding.digest,
            provider_call_ref="provider-call:fixture:evidence",
            gateway_request_digest=_digest("gateway-request"),
            attempts=(
                HarnessGatewayAttemptObservation(
                    sequence=1,
                    provider="deepseek",
                    model="deepseek-v4-flash",
                    standing="cancelled",
                ),
            ),
            stream_terminal_standing="unknown",
            unknown_fields=("provider-final-standing",),
        )
        for name in ("invoke", "dispatch", "retry", "cancel", "reconcile"):
            self.assertFalse(hasattr(observation, name), name)


if __name__ == "__main__":
    unittest.main()
