from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts" / "configure_r2_lifecycle.py"
SPEC = importlib.util.spec_from_file_location("configure_r2_lifecycle", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load lifecycle controller")
lifecycle = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lifecycle
SPEC.loader.exec_module(lifecycle)


class LifecycleTests(unittest.TestCase):
    def test_managed_rules_use_policy_days_as_age_seconds(self) -> None:
        rules = lifecycle.managed_rules(
            {
                "request_state": 90,
                "receipt_mirror": 90,
                "artifacts": 91,
                "cleanup_tasks": 90,
            }
        )
        by_prefix = {rule["conditions"]["prefix"]: rule for rule in rules}
        self.assertEqual(
            by_prefix["fetch/v2/"]["deleteObjectsTransition"]["condition"]["maxAge"],
            91 * 86400,
        )
        self.assertEqual(
            by_prefix["requests/v2/"]["deleteObjectsTransition"]["condition"]["maxAge"],
            90 * 86400,
        )

    def test_main_preserves_non_managed_rules_and_verifies_update(self) -> None:
        retention = {
            "request_state": 90,
            "receipt_mirror": 90,
            "artifacts": 91,
            "cleanup_tasks": 90,
        }
        expected = lifecycle.managed_rules(retention)
        default = {
            "id": "Default Multipart Abort Rule",
            "enabled": True,
            "conditions": {},
            "abortMultipartUploadsTransition": {
                "condition": {"type": "Age", "maxAge": 604800}
            },
        }
        calls = []

        def api(method, path, token, body=None):
            calls.append((method, path, body))
            if method == "GET" and len(calls) == 1:
                return {
                    "rules": [
                        default,
                        {
                            "id": "edge-v2-fetch-artifacts-30d",
                            "enabled": True,
                            "conditions": {"prefix": "fetch/v2/"},
                        },
                    ]
                }
            if method == "PUT":
                self.assertEqual(body, {"rules": [default, *expected]})
                return None
            return {"rules": [default, *expected]}

        with (
            mock.patch.object(
                lifecycle,
                "load_json",
                side_effect=[
                    {"api_token": "token", "account_id": "account"},
                    {"retention_days": retention},
                ],
            ),
            mock.patch.object(lifecycle, "api_request", side_effect=api),
        ):
            self.assertEqual(lifecycle.main([]), 0)
        self.assertEqual([call[0] for call in calls], ["GET", "PUT", "GET"])

    def test_check_is_read_only_and_reports_policy_drift(self) -> None:
        retention = {
            "request_state": 90,
            "receipt_mirror": 90,
            "artifacts": 91,
            "cleanup_tasks": 90,
        }
        expected = lifecycle.managed_rules(retention)
        calls = []

        def api(method, path, token, body=None):
            calls.append((method, path, body))
            return {"rules": expected}

        with (
            mock.patch.object(
                lifecycle,
                "load_json",
                side_effect=[
                    {"api_token": "token", "account_id": "account"},
                    {"retention_days": retention},
                ],
            ),
            mock.patch.object(lifecycle, "api_request", side_effect=api),
        ):
            self.assertEqual(lifecycle.main(["--check"]), 0)
        self.assertEqual([call[0] for call in calls], ["GET"])


if __name__ == "__main__":
    unittest.main()
