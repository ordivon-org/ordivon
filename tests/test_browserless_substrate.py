from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from browserless_substrate import BrowserlessEndpoint, BrowserlessPool  # noqa: E402


class BrowserlessSubstrateTests(unittest.TestCase):
    def endpoint(self, root: Path, **extra):
        token = root / "browserless.token"
        token.write_text("secret-token\n")
        value = {
            "id": "carrier-a",
            "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
            "httpEndpoint": "http://127.0.0.1:3011",
            "tokenFile": str(token),
            "networkNamespace": "surfpath-test",
            "userDataDir": "/data",
            "launchArgs": ["--proxy-server=http://127.0.0.1:19081"],
        }
        value.update(extra)
        return BrowserlessEndpoint.from_dict(value)

    def test_connection_url_keeps_secret_out_of_public_identity(self):
        with tempfile.TemporaryDirectory() as d:
            endpoint = self.endpoint(Path(d))
            public = endpoint.public_connection_endpoint
            self.assertNotIn("secret-token", public)
            self.assertIn("launch=", public)
            launch = json.loads(
                __import__("urllib.parse").parse.parse_qs(
                    __import__("urllib.parse").parse.urlsplit(public).query
                )["launch"][0]
            )
            self.assertEqual(launch["userDataDir"], "/data")
            self.assertEqual(launch["args"], ["--proxy-server=http://127.0.0.1:19081"])
            private = endpoint.authenticated_connection_endpoint()
            self.assertIn("token=secret-token", private)
            self.assertNotIn("secret-token", endpoint.identity_digest)

    def test_user_data_dir_must_be_absolute_server_side_path(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "absolute server-side path"):
                self.endpoint(Path(d), userDataDir="relative/profile")

    def test_headless_false_is_explicit_launch_and_identity_input(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            endpoint = self.endpoint(root, headless=False)
            public = endpoint.public_connection_endpoint
            launch = json.loads(
                __import__("urllib.parse").parse.parse_qs(
                    __import__("urllib.parse").parse.urlsplit(public).query
                )["launch"][0]
            )
            self.assertIs(launch["headless"], False)
            before = endpoint.identity_digest
            headless = self.endpoint(root, headless=True)
            self.assertNotEqual(before, headless.identity_digest)

    def test_headless_rejects_non_boolean(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "headless must be boolean"):
                self.endpoint(Path(d), headless="false")

    def test_connection_timeout_is_request_scoped_and_not_part_of_identity(self):
        with tempfile.TemporaryDirectory() as d:
            endpoint = self.endpoint(Path(d))
            before = endpoint.identity_digest
            url = endpoint.connection_endpoint(timeout_ms=480000)
            self.assertIn("timeout=480000", url)
            self.assertEqual(endpoint.identity_digest, before)
            with self.assertRaises(ValueError):
                endpoint.connection_endpoint(timeout_ms=0)

    def test_sessions_observation_uses_endpoint_namespace_and_keeps_token_out_of_argv(self):
        with tempfile.TemporaryDirectory() as d:
            endpoint = self.endpoint(Path(d))
            completed = mock.Mock(
                returncode=0, stdout='[{"type":"page","trackingId":"h-1"}]', stderr=""
            )
            with mock.patch("browserless_substrate.subprocess.run", return_value=completed) as run:
                rows = endpoint.sessions(tracking_id="h-1")
            self.assertEqual(rows[0]["trackingId"], "h-1")
            argv = " ".join(run.call_args.args[0])
            self.assertIn("netns", argv)
            self.assertNotIn("secret-token", argv)
            self.assertIn("secret-token", run.call_args.kwargs["input"])

    def test_operator_connection_endpoint_rebases_websocket_and_preserves_launch_timeout(self):
        with tempfile.TemporaryDirectory() as d:
            endpoint = self.endpoint(Path(d), operatorHttpEndpoint="http://127.0.0.1:13111")
            public = endpoint.operator_connection_endpoint(timeout_ms=90000)
            parsed = __import__("urllib.parse").parse.urlsplit(public)
            self.assertEqual(parsed.scheme, "ws")
            self.assertEqual(parsed.netloc, "127.0.0.1:13111")
            self.assertEqual(parsed.path, "/chromium")
            query = __import__("urllib.parse").parse.parse_qs(parsed.query)
            self.assertEqual(query["timeout"], ["90000"])
            self.assertIn("launch", query)
            self.assertNotIn("token", query)
            private = endpoint.authenticated_operator_connection_endpoint(timeout_ms=90000)
            self.assertIn("token=secret-token", private)
            self.assertIn("127.0.0.1%3A19081", private)

    def test_operator_connection_endpoint_requires_explicit_loopback_bridge(self):
        with tempfile.TemporaryDirectory() as d:
            endpoint = self.endpoint(Path(d))
            with self.assertRaisesRegex(ValueError, "operatorHttpEndpoint is required"):
                endpoint.operator_connection_endpoint()

    def test_operator_url_rebases_outer_http_and_nested_devtools_websocket(self):
        with tempfile.TemporaryDirectory() as d:
            endpoint = self.endpoint(Path(d), operatorHttpEndpoint="http://127.0.0.1:13111")
            internal = "http://127.0.0.1:3011/devtools/inspector.html?ws=127.0.0.1%3A3011%2Fdevtools%2Fpage%2Fp1%3Ftoken%3Ds&token=s"
            out = endpoint.operator_url(internal)
            self.assertIn("127.0.0.1:13111/devtools/inspector.html", out)
            self.assertIn("127.0.0.1%3A13111%2Fdevtools%2Fpage%2Fp1", out)
            self.assertNotIn("127.0.0.1%3A3011%2Fdevtools%2Fpage", out)
            self.assertNotIn("operatorHttpEndpoint", endpoint.identity_digest)

    def test_pool_selection_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            token = root / "t"
            token.write_text("x")
            pool = BrowserlessPool.from_dict(
                {
                    "kind": "browserless",
                    "endpoints": [
                        {
                            "id": "a",
                            "websocketEndpoint": "ws://127.0.0.1:3011/chromium",
                            "httpEndpoint": "http://127.0.0.1:3011",
                            "tokenFile": str(token),
                        },
                        {
                            "id": "b",
                            "websocketEndpoint": "ws://127.0.0.1:3012/chromium",
                            "httpEndpoint": "http://127.0.0.1:3012",
                            "tokenFile": str(token),
                        },
                    ],
                }
            )
            self.assertEqual(pool.select("birth-1"), pool.select("birth-1"))

    def test_health_does_not_return_token(self):
        with tempfile.TemporaryDirectory() as d:
            endpoint = self.endpoint(Path(d))
            with mock.patch(
                "browserless_substrate.subprocess.run",
                return_value=mock.Mock(returncode=0, stdout="204", stderr=""),
            ) as run:
                result = endpoint.health()
            self.assertIn("netns", run.call_args.args[0])
            self.assertNotIn("secret-token", " ".join(run.call_args.args[0]))
            self.assertIn("secret-token", run.call_args.kwargs["input"])
            self.assertTrue(result["healthy"])
            self.assertNotIn("secret-token", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
