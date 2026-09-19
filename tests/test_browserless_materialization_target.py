from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from browserless_materialization_target import BrowserlessMaterializationTarget  # noqa: E402
from browserless_substrate import BrowserlessEndpoint  # noqa: E402
from conversation_relay_carrier import CarrierMaterializationRequest  # noqa: E402


class BrowserlessMaterializationTargetTests(unittest.TestCase):
    def target(self, root: Path):
        token = root / "token"
        token.write_text("secret")
        endpoint = BrowserlessEndpoint.from_dict(
            {
                "id": "a",
                "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
                "httpEndpoint": "http://127.0.0.1:3011",
                "tokenFile": str(token),
            }
        )
        return BrowserlessMaterializationTarget(
            endpoint=endpoint,
            state_dir=root / "state",
            submit_script=root / "submit.py",
            reconcile_script=root / "reconcile.py",
            playwright_python=Path("/python"),
        )

    def request(self):
        return CarrierMaterializationRequest(
            request_id="effect-test-1",
            preparation_digest="sha256:" + "1" * 64,
            bootstrap_prompt="hello",
        )

    def test_bound_receipt_from_browserless_handle(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = self.target(root)
            request = self.request()

            def run(cmd, **kwargs):
                handle_path = Path(cmd[cmd.index("--handle-out") + 1])
                handle_path.parent.mkdir(parents=True, exist_ok=True)
                handle_path.write_text(
                    json.dumps(
                        {
                            "effectId": "effect-test-1",
                            "bindingDigest": "sha256:" + "2" * 64,
                            "providerResource": "https://chatgpt.com/c/abc",
                            "generationStarted": True,
                            "composerCleared": True,
                        }
                    )
                )
                return mock.Mock(returncode=0, stdout="", stderr="")

            with mock.patch("browserless_materialization_target.subprocess.run", side_effect=run):
                result = target.materialize(request)
            self.assertEqual(result.standing.value, "bound")
            self.assertEqual(result.provider_conversation_coordinate, "https://chatgpt.com/c/abc")

    def test_pre_effect_blocker_remains_retry_safe_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = self.target(root)
            request = self.request()

            def run(cmd, **kwargs):
                p = Path(cmd[cmd.index("--pre-effect-out") + 1])
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(
                    json.dumps(
                        {
                            "effectId": "effect-test-1",
                            "providerEffectAttempted": False,
                            "evidenceDigest": "sha256:" + "3" * 64,
                            "blocker": "browserless-connect:TimeoutError",
                        }
                    )
                )
                return mock.Mock(returncode=42, stdout="", stderr="")

            with mock.patch("browserless_materialization_target.subprocess.run", side_effect=run):
                result = target.materialize(request)
            self.assertEqual(result.standing.value, "pre-effect-failed")


if __name__ == "__main__":
    unittest.main()
