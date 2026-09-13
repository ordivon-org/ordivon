from __future__ import annotations

import argparse
import hashlib
import http.client
import importlib.util
import io
import json
import os
import subprocess
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts" / "ordivon_edge_client.py"
SPEC = importlib.util.spec_from_file_location("ordivon_edge_client", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load Edge client")
client = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = client
SPEC.loader.exec_module(client)


class FakeResponse:
    def __init__(self, body: bytes = b"{}", status: int = 200, headers: dict[str, str] | None = None):
        self.body = body
        self.status = status
        self.headers = headers or {"content-type": "application/json"}

    def __enter__(self):
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class ClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = client.Config(
            endpoint="https://edge.invalid",
            key_id="runtime-v1",
            secret=b"x" * 32,
        )

    def test_transport_retry_preserves_request_identity_and_body(self) -> None:
        calls = []

        def urlopen(request, timeout=0):
            calls.append(request)
            if len(calls) == 1:
                raise http.client.RemoteDisconnected("connection closed")
            return FakeResponse(b'{"ok":true}')

        sleeps: list[float] = []
        with mock.patch.object(client.urllib.request, "urlopen", side_effect=urlopen):
            status, _, body = client.request(
                self.config,
                "POST",
                "/v1/fetch",
                body=b'{"url":"https://example.com/"}',
                request_id="request_retry_001",
                sleep=sleeps.append,
            )

        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"ok":true}')
        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [0.25])
        for request in calls:
            self.assertEqual(request.headers["X-ordivon-request-id"], "request_retry_001")
            self.assertEqual(request.data, b'{"url":"https://example.com/"}')

    def test_artifact_hash_mismatch_preserves_existing_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = pathlib.Path(directory) / "artifact.bin"
            destination.write_bytes(b"existing")
            args = argparse.Namespace(key="fetch/v2/request/g1/body", output=str(destination), sha256=None)
            with mock.patch.object(
                client,
                "request",
                return_value=(200, {"X-Ordivon-Sha256": "0" * 64}, b"new"),
            ):
                with self.assertRaises(client.ClientError):
                    client.command_artifact_get(self.config, args)
            self.assertEqual(destination.read_bytes(), b"existing")

    def test_artifact_download_is_verified_atomic_and_private(self) -> None:
        body = b"verified-artifact"
        digest = hashlib.sha256(body).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            destination = pathlib.Path(directory) / "artifact.bin"
            args = argparse.Namespace(key="fetch/v2/request/g1/body", output=str(destination), sha256=digest)
            output = io.StringIO()
            with (
                mock.patch.object(
                    client,
                    "request",
                    return_value=(
                        200,
                        {
                            "X-Ordivon-Sha256": digest,
                            "X-Ordivon-Media-Type": "text/plain",
                            "Content-Type": "application/octet-stream",
                        },
                        body,
                    ),
                ),
                redirect_stdout(output),
            ):
                result = client.command_artifact_get(self.config, args)
            self.assertEqual(result, 0)
            self.assertEqual(destination.read_bytes(), body)
            self.assertEqual(os.stat(destination).st_mode & 0o777, 0o600)
            self.assertIn('"verified": true', output.getvalue().lower())
            self.assertEqual(list(pathlib.Path(directory).glob(".*.tmp")), [])

    def test_release_digest_supports_monorepo_provider_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            provider = repository / "providers" / "cloudflare"
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.name", "Test"],
                check=True,
            )
            for relative in client.WORKER_RELEASE_INPUTS:
                target = provider / relative
                if relative == "src":
                    target.mkdir(parents=True, exist_ok=True)
                    (target / "index.ts").write_text("worker\n")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(relative + "\n")
            subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-qm", "worker"], check=True)
            commit = subprocess.check_output(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            from_root = client.release_digest(repository, commit)
            from_provider = client.release_digest(provider, commit)
            self.assertEqual(from_root, from_provider)
            self.assertEqual(len(from_root), 64)

    def test_status_reports_older_source_with_current_worker_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = pathlib.Path(directory)
            subprocess.run(["git", "init", "-q", str(repository)], check=True)
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.email", "test@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.name", "Test"],
                check=True,
            )
            (repository / "src").mkdir()
            (repository / "src" / "index.ts").write_text("worker\n")
            for relative in client.WORKER_RELEASE_INPUTS[1:]:
                target = repository / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(relative + "\n")
            subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-qm", "worker"], check=True)
            deployed = subprocess.check_output(
                ["git", "-C", str(repository), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            digest = client.release_digest(repository, deployed)
            (repository / "README.md").write_text("docs only\n")
            subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repository), "commit", "-qm", "docs"], check=True)
            health = {
                "service": "ordivon-edge",
                "status": "ok",
                "policy_version": "p1.6.test",
                "worker_version": {
                    "id": "version-old",
                    "tag": f"git-{deployed[:12]}-src-{digest[:16]}-123",
                    "timestamp": "2026-07-28T00:00:00Z",
                },
                "deployment_identity": {
                    "source_commit": deployed[:12],
                    "worker_release_digest": digest[:16],
                },
            }
            output = io.StringIO()
            args = argparse.Namespace(repo=str(repository), expected_ref="HEAD")
            with (
                mock.patch.object(
                    client,
                    "request",
                    return_value=(200, {}, json.dumps(health).encode()),
                ),
                redirect_stdout(output),
            ):
                result = client.command_status(self.config, args)
            report = json.loads(output.getvalue())
            self.assertEqual(result, 0)
            self.assertEqual(report["deployment"]["source_relation"], "behind")
            self.assertEqual(report["deployment"]["worker_inputs"], "current")
            self.assertEqual(report["deployment"]["source_commit"], deployed)



if __name__ == "__main__":
    unittest.main()
