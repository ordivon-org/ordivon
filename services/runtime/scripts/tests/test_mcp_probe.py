from __future__ import annotations

import os
import stat
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import json

SCRIPTS = Path(__file__).resolve().parents[1]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from mcp_probe import (
    McpClient,
    McpProbeError,
    PROBE_USER_AGENT,
    _read_bounded_regular_file_text,
    load_bearer_token,
    load_environment_file,
)


class _Headers(dict):
    def items(self):
        return super().items()


class _Response:
    status = 200
    headers = _Headers({"Content-Type": "application/json"})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode()


class RuntimeProbeTransportTests(unittest.TestCase):
    def test_probe_uses_stable_machine_user_agent(self) -> None:
        client = McpClient(
            "https://mcp.example.invalid/mcp",
            "test-token",
            client_name="probe-test",
        )
        with mock.patch("mcp_probe.urllib.request.urlopen", return_value=_Response()) as opened:
            self.assertEqual(client.request("server/discover", {}), {})
        request = opened.call_args.args[0]
        self.assertEqual(request.get_header("User-agent"), PROBE_USER_AGENT)
        self.assertNotIn("Python-urllib", request.get_header("User-agent"))


class RuntimeCredentialTests(unittest.TestCase):
    def test_inline_credential_remains_migration_compatible(self) -> None:
        self.assertEqual(load_bearer_token({"ORDIVON_BEARER_TOKEN": "test"}), "test")

    def test_environment_file_parser_is_shared_and_bounded_to_key_value_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime.env"
            path.write_text(
                "# comment\nORDIVON_BIND=127.0.0.1:8897\n"
                "ORDIVON_BEARER_TOKEN_FILE='/etc/ordivon/runtime-mcp.token'\n",
                encoding="utf-8",
            )
            self.assertEqual(
                load_environment_file(path),
                {
                    "ORDIVON_BIND": "127.0.0.1:8897",
                    "ORDIVON_BEARER_TOKEN_FILE": "/etc/ordivon/runtime-mcp.token",
                },
            )
            path.write_text("BROKEN\n", encoding="utf-8")
            with self.assertRaisesRegex(McpProbeError, "invalid environment line"):
                load_environment_file(path)

    def test_environment_file_rejects_fifo_symlink_nonregular_oversize_and_invalid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            fifo = root / "runtime.fifo"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(McpProbeError, "regular file"):
                load_environment_file(fifo)

            valid = root / "runtime.env"
            valid.write_text("ORDIVON_BIND=127.0.0.1:8897\n", encoding="utf-8")
            symlink = root / "runtime-link.env"
            symlink.symlink_to(valid)
            with self.assertRaisesRegex(McpProbeError, "securely open"):
                load_environment_file(symlink)

            nonregular = root / "runtime-dir"
            nonregular.mkdir()
            with self.assertRaisesRegex(McpProbeError, "regular file"):
                load_environment_file(nonregular)

            oversized = root / "oversized.env"
            oversized.write_bytes(b"A" * (64 * 1024 + 1))
            with self.assertRaisesRegex(McpProbeError, "configured bound"):
                load_environment_file(oversized)

            invalid = root / "invalid.env"
            invalid.write_bytes(b"ORDIVON_BIND=\xff\n")
            with self.assertRaisesRegex(McpProbeError, "valid UTF-8"):
                load_environment_file(invalid)

    def test_descriptor_snapshot_survives_path_replacement_and_bounds_growth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "authority"
            replacement = root / "replacement"
            path.write_text("first", encoding="utf-8")
            replacement.write_text("second", encoding="utf-8")
            real_fstat = os.fstat

            def replace_after_open(descriptor):
                os.replace(replacement, path)
                return real_fstat(descriptor)

            with mock.patch("mcp_probe.os.fstat", side_effect=replace_after_open):
                self.assertEqual(
                    _read_bounded_regular_file_text(
                        path,
                        max_bytes=16,
                        label="replacement-test",
                    ),
                    "first",
                )
            self.assertEqual(path.read_text(encoding="utf-8"), "second")

            path.write_text("x", encoding="utf-8")
            with mock.patch("mcp_probe.os.read", side_effect=lambda _fd, size: b"x" * size):
                with self.assertRaisesRegex(McpProbeError, "configured bound"):
                    _read_bounded_regular_file_text(
                        path,
                        max_bytes=16,
                        label="growth-test",
                    )

    def test_file_backed_token_rejects_fifo_symlink_nonregular_oversize_and_invalid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            fifo = root / "token.fifo"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(McpProbeError, "regular file"):
                load_bearer_token({"ORDIVON_BEARER_TOKEN_FILE": str(fifo)})

            valid = root / "token"
            valid.write_text("token-value\n", encoding="utf-8")
            os.chmod(valid, 0o600)
            symlink = root / "token-link"
            symlink.symlink_to(valid)
            with self.assertRaisesRegex(McpProbeError, "securely open"):
                load_bearer_token({"ORDIVON_BEARER_TOKEN_FILE": str(symlink)})

            nonregular = root / "token-dir"
            nonregular.mkdir()
            with self.assertRaisesRegex(McpProbeError, "regular file"):
                load_bearer_token({"ORDIVON_BEARER_TOKEN_FILE": str(nonregular)})

            oversized = root / "oversized-token"
            oversized.write_bytes(b"x" * (16_384 + 1))
            os.chmod(oversized, 0o600)
            with self.assertRaisesRegex(McpProbeError, "configured bound"):
                load_bearer_token({"ORDIVON_BEARER_TOKEN_FILE": str(oversized)})

            invalid = root / "invalid-token"
            invalid.write_bytes(b"\xff")
            os.chmod(invalid, 0o600)
            with self.assertRaisesRegex(McpProbeError, "valid UTF-8"):
                load_bearer_token({"ORDIVON_BEARER_TOKEN_FILE": str(invalid)})

    def test_file_backed_token_binds_permissions_and_content_to_same_descriptor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "token"
            replacement = root / "replacement"
            path.write_text("first-token\n", encoding="utf-8")
            replacement.write_text("second-token\n", encoding="utf-8")
            os.chmod(path, 0o600)
            os.chmod(replacement, 0o644)
            real_fstat = os.fstat

            def replace_after_open(descriptor):
                os.replace(replacement, path)
                return real_fstat(descriptor)

            with mock.patch("mcp_probe.os.fstat", side_effect=replace_after_open):
                self.assertEqual(
                    load_bearer_token({"ORDIVON_BEARER_TOKEN_FILE": str(path)}),
                    "first-token",
                )
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o644)

    def test_private_token_file_is_the_canonical_local_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime-mcp.token"
            path.write_text("token-value\n", encoding="utf-8")
            os.chmod(path, 0o600)
            self.assertEqual(
                load_bearer_token({"ORDIVON_BEARER_TOKEN_FILE": str(path)}),
                "token-value",
            )

    def test_ambiguous_or_permissive_sources_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime-mcp.token"
            path.write_text("token-value\n", encoding="utf-8")
            os.chmod(path, 0o640)
            with self.assertRaisesRegex(McpProbeError, "group or others"):
                load_bearer_token({"ORDIVON_BEARER_TOKEN_FILE": str(path)})
            os.chmod(path, 0o600)
            with self.assertRaisesRegex(McpProbeError, "exactly one"):
                load_bearer_token({
                    "ORDIVON_BEARER_TOKEN": "inline",
                    "ORDIVON_BEARER_TOKEN_FILE": str(path),
                })


if __name__ == "__main__":
    unittest.main()
