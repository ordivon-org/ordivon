from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from conversation_relay_carrier import CarrierMaterializationRequest, MaterializationStanding  # noqa: E402
from windows_user_browser_materialization_target import (  # noqa: E402
    UserBrowserAttemptResult,
    WindowsUserBrowserMaterializationTarget,
)


class FakeController:
    def __init__(self, result: UserBrowserAttemptResult):
        self.result = result
        self.calls: list[dict] = []

    def materialize(self, **kwargs):
        self.calls.append(dict(kwargs))
        return self.result

    def reconcile(self, **kwargs):
        self.calls.append(dict(kwargs))
        return self.result


class WindowsUserBrowserMaterializationTargetTests(unittest.TestCase):
    def request(self) -> CarrierMaterializationRequest:
        return CarrierMaterializationRequest(
            request_id='effect-user-browser-1',
            preparation_digest='sha256:' + '1' * 64,
            bootstrap_prompt='hello from fenced request',
        )

    def test_bound_result_maps_to_existing_materialization_contract(self):
        with tempfile.TemporaryDirectory() as d:
            controller = FakeController(
                UserBrowserAttemptResult(
                    standing='bound',
                    provider_resource='https://chatgpt.com/c/abc',
                    evidence_digest='sha256:' + '2' * 64,
                    detail='normal Chrome submit observed and provider-bound',
                    provider_effect_attempted=True,
                )
            )
            target = WindowsUserBrowserMaterializationTarget(
                state_dir=Path(d), controller=controller
            )
            result = target.materialize(self.request())

            self.assertIs(result.standing, MaterializationStanding.BOUND)
            self.assertEqual(result.provider_conversation_coordinate, 'https://chatgpt.com/c/abc')
            self.assertEqual(len(controller.calls), 1)
            call = controller.calls[0]
            self.assertEqual(call['effect_id'], 'effect-user-browser-1')
            self.assertEqual(call['attempt_generation'], 1)
            self.assertEqual(call['prompt_digest'], target.prompt_digest(self.request()))
            self.assertTrue(Path(call['prompt_path']).is_file())
            self.assertEqual(Path(call['prompt_path']).read_text(), 'hello from fenced request')

    def test_challenge_is_pre_effect_hold_not_browserless_failover(self):
        with tempfile.TemporaryDirectory() as d:
            controller = FakeController(
                UserBrowserAttemptResult(
                    standing='pre-effect-failed',
                    provider_resource=None,
                    evidence_digest='sha256:' + '3' * 64,
                    detail='provider-boundary:challenge-gated',
                    provider_effect_attempted=False,
                )
            )
            target = WindowsUserBrowserMaterializationTarget(
                state_dir=Path(d), controller=controller
            )
            result = target.materialize(self.request())

            self.assertIs(result.standing, MaterializationStanding.PRE_EFFECT_FAILED)
            self.assertIsNone(result.provider_conversation_coordinate)
            self.assertEqual(len(controller.calls), 1)

    def test_unknown_post_send_result_never_becomes_retry_safe(self):
        with tempfile.TemporaryDirectory() as d:
            controller = FakeController(
                UserBrowserAttemptResult(
                    standing='unknown',
                    provider_resource=None,
                    evidence_digest='sha256:' + '4' * 64,
                    detail='browser process lost after submit boundary',
                    provider_effect_attempted=True,
                )
            )
            target = WindowsUserBrowserMaterializationTarget(
                state_dir=Path(d), controller=controller
            )
            result = target.materialize(self.request())
            self.assertIs(result.standing, MaterializationStanding.UNKNOWN)
            self.assertIn('after submit boundary', result.detail or '')

    def test_mapping_controller_payload_is_accepted_without_new_ledger_semantics(self):
        class MappingController:
            def materialize(self, **kwargs):
                return {
                    "standing": "bound",
                    "providerResource": "https://chatgpt.com/c/xyz",
                    "evidenceDigest": "sha256:" + "5" * 64,
                    "detail": "provider-bound",
                    "providerEffectAttempted": True,
                }
            def reconcile(self, **kwargs):
                return self.materialize(**kwargs)

        with tempfile.TemporaryDirectory() as d:
            target = WindowsUserBrowserMaterializationTarget(state_dir=Path(d), controller=MappingController())
            result = target.materialize(self.request())
            self.assertIs(result.standing, MaterializationStanding.BOUND)
            self.assertEqual(result.provider_conversation_coordinate, "https://chatgpt.com/c/xyz")


if __name__ == '__main__':
    unittest.main()
