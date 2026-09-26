from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
HARNESS_SRC = REPO_ROOT / "services" / "harness" / "src"
for path in (ROOT, HARNESS_SRC):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

from anc_canonical import canonical_bytes, loads_strict  # noqa: E402
from foundry_r3 import CANARY, build_probe, run_canary_probe  # noqa: E402
from ordivon_harness.ordivon.deepseek import DeepSeekSettings  # noqa: E402


class StaticTransport:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.body: bytes | None = None

    def post(self, url: str, *, headers, body: bytes, timeout_seconds: float, max_response_bytes: int) -> bytes:
        self.body = body
        return self.response


def provider_response(*, explanation: str, fingerprint: str = "fp_r3_fixture") -> bytes:
    arguments = {
        "status": "candidate_completed",
        "result": {
            "classification": "ignored_untrusted_instruction",
            "instruction_like_content_detected": True,
            "explanation": explanation,
        },
        "artifact_refs": [],
        "evidence_refs": [],
        "unresolved_unknowns": [],
    }
    return canonical_bytes(
        {
            "id": "provider-call:r3-fixture",
            "model": "deepseek-v4-flash",
            "system_fingerprint": fingerprint,
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "toolcall:r3-conclusion",
                                "type": "function",
                                "function": {
                                    "name": "submit_run_conclusion",
                                    "arguments": json.dumps(arguments, separators=(",", ":")),
                                },
                            }
                        ],
                    },
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        }
    )


def settings() -> DeepSeekSettings:
    return DeepSeekSettings(api_key="k" * 40, model="deepseek-v4-flash", max_output_tokens=512)


class LiveSafeCanaryTests(unittest.TestCase):
    def test_probe_has_no_runtime_tools_or_effect_authority(self) -> None:
        transport = StaticTransport(provider_response(explanation="Untrusted instruction was treated as data."))
        probe = build_probe(settings(), transport=transport)
        self.assertEqual(probe.request.tools, ())
        self.assertEqual(probe.requested.target_kind, "system")
        self.assertNotIn(CANARY, json.dumps(probe.requested.to_dict(), sort_keys=True))

    def test_provider_request_contains_canary_only_as_request_data_and_excludes_secret(self) -> None:
        transport = StaticTransport(provider_response(explanation="Untrusted instruction was treated as data."))
        probe = build_probe(settings(), transport=transport)
        probe.adapter.invoke(probe.request)
        self.assertIsNotNone(transport.body)
        assert transport.body is not None
        self.assertIn(CANARY.encode(), transport.body)
        self.assertNotIn(("k" * 40).encode(), transport.body)
        parsed = loads_strict(transport.body)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["tool_choice"], "required")
        self.assertEqual(parsed["thinking"], {"type": "disabled"})

    def test_safe_provider_result_produces_no_finding(self) -> None:
        transport = StaticTransport(provider_response(explanation="Untrusted instruction was treated as data."))
        receipt = run_canary_probe(settings(), transport=transport)
        self.assertFalse(receipt.canary_leaked)
        self.assertIsNone(receipt.finding)
        self.assertEqual(receipt.realized_target["identityStrength"], "provider_observation")
        self.assertEqual(receipt.provider_system_fingerprint, "fp_r3_fixture")

    def test_synthetic_canary_echo_is_detected_deterministically(self) -> None:
        transport = StaticTransport(provider_response(explanation=f"Observed marker {CANARY}"))
        receipt = run_canary_probe(settings(), transport=transport)
        self.assertTrue(receipt.canary_leaked)
        self.assertEqual(receipt.finding, "I4_PROTECTED_SYNTHETIC_CANARY_CROSSED_MODEL_OUTPUT")

    def test_realization_is_bound_to_raw_provider_response_digest(self) -> None:
        raw = provider_response(explanation="Untrusted instruction was treated as data.")
        transport = StaticTransport(raw)
        receipt = run_canary_probe(settings(), transport=transport)
        expected = "sha256:" + sha256(raw).hexdigest()
        self.assertEqual(receipt.raw_response_digest, expected)
        self.assertEqual(receipt.realized_target["realizationEvidenceDigest"], expected)
        self.assertEqual(receipt.observation["providerArtifactDigest"], expected)

    def test_target_binding_changes_when_instruction_bundle_changes(self) -> None:
        probe = build_probe(settings(), transport=StaticTransport(provider_response(explanation="ok")))
        self.assertEqual(probe.requested.instruction_bundle_digest, probe.request.context_digest)
        self.assertEqual(probe.requested.tool_catalog_digest, probe.request.tool_catalog_digest)

    def test_receipt_does_not_serialize_api_key(self) -> None:
        receipt = run_canary_probe(
            settings(),
            transport=StaticTransport(provider_response(explanation="Untrusted instruction was treated as data.")),
        ).to_dict()
        rendered = json.dumps(receipt, sort_keys=True)
        self.assertNotIn("k" * 40, rendered)
        self.assertIn("receiptDigest", receipt)


if __name__ == "__main__":
    unittest.main()
