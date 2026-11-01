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
    parse_mcp_response,
    _catalog_result,
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

    def read(self, size=None):
        return json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}}).encode()


class RuntimeProbeWireContractTests(unittest.TestCase):
    def test_sse_progress_multiline_payload_and_unicode_are_one_response(self) -> None:
        payload = (
            b": keepalive\r\n\r\n"
            b'data: {"jsonrpc":"2.0","method":"notifications/progress"}\r\n\r\n'
            b"event: message\r\n"
            b'data: {"jsonrpc":"2.0",\r\n'
            b'data: "id":7,"result":{"ok":true}}\r\n\r\n'
        )
        self.assertEqual(
            parse_mcp_response("text/event-stream", payload),
            {"jsonrpc": "2.0", "id": 7, "result": {"ok": True}},
        )
        unicode_message = {"jsonrpc": "2.0", "id": 7, "result": {"text": "a\u2028b"}}
        single_event = b"data: " + json.dumps(unicode_message, ensure_ascii=False).encode() + b"\n\n"
        self.assertEqual(parse_mcp_response("text/event-stream", single_event), unicode_message)

    def test_sse_notification_without_final_response_is_not_success(self) -> None:
        notification = b'data: {"jsonrpc":"2.0","method":"notifications/progress"}\n\n'
        with self.assertRaisesRegex(McpProbeError, "final.*response"):
            parse_mcp_response("text/event-stream", notification)

    def test_sse_duplicate_terminal_responses_fail_closed(self) -> None:
        payload = (
            b'data: {"jsonrpc":"2.0","id":7,"result":{}}\n\n'
            b'data: {"jsonrpc":"2.0","id":7,"result":{"changed":true}}\n\n'
        )
        with self.assertRaisesRegex(McpProbeError, "multiple.*responses"):
            parse_mcp_response("text/event-stream", payload)

    def test_catalog_probe_rejects_duplicate_and_malformed_provider_tools(self) -> None:
        class ProbeClient:
            lifecycle = "legacy"
            protocol_version = "2025-06-18"

            def __init__(self, tools):
                self.tools = tools

            def request(self, method):
                assert method == "tools/list"
                return {"tools": self.tools}

        lifecycle = {"protocolVersion": "2025-06-18", "serverInfo": {"name": "fixture"}}
        for tools in (
            [{"name": "job.observe"}, {"name": "job.observe"}],
            [{"name": "job.observe"}, {"inputSchema": {"type": "object"}}],
        ):
            with self.subTest(tools=tools), self.assertRaises(McpProbeError):
                _catalog_result(
                    ProbeClient(tools),
                    lifecycle,
                    expected_tool_count=1,
                    required_tools=("job.observe",),
                )


class RuntimeCatalogPaginationTests(unittest.TestCase):
    """Operator readiness must not bless only the first MCP tools/list page."""

    class CatalogClient:
        lifecycle = "legacy"
        protocol_version = "2025-06-18"

        def __init__(self, pages):
            self.pages = pages
            self.requested = []

        def request(self, method, params=None):
            assert method == "tools/list"
            cursor = (params or {}).get("cursor")
            self.requested.append(cursor)
            return self.pages[cursor]

    @staticmethod
    def lifecycle():
        return {"protocolVersion": "2025-06-18", "serverInfo": {"name": "fixture"}}

    def test_pages_are_exhausted_before_operator_readiness_can_pass(self) -> None:
        client = self.CatalogClient(
            {
                None: {"tools": [{"name": "release.apply"}], "nextCursor": "page/2"},
                "page/2": {"tools": [{"name": "release.get"}]},
            }
        )
        receipt = _catalog_result(
            client,
            self.lifecycle(),
            expected_tool_count=None,
            required_tools=("release.apply",),
        )
        self.assertEqual(receipt["toolNames"], ["release.apply", "release.get"])
        self.assertEqual(receipt["toolCount"], 2)
        self.assertEqual(client.requested, [None, "page/2"])

    def test_empty_cursor_is_an_opaque_valid_continuation(self) -> None:
        client = self.CatalogClient(
            {
                None: {"tools": [{"name": "release.apply"}], "nextCursor": ""},
                "": {"tools": [{"name": "release.get"}]},
            }
        )
        receipt = _catalog_result(
            client,
            self.lifecycle(),
            expected_tool_count=2,
            required_tools=("release.apply", "release.get"),
        )
        self.assertEqual(receipt["toolCount"], 2)
        self.assertEqual(client.requested, [None, ""])

    def test_required_tool_may_be_on_second_page(self) -> None:
        client = self.CatalogClient(
            {
                None: {"tools": [{"name": "release.apply"}], "nextCursor": "p2"},
                "p2": {"tools": [{"name": "release.get"}]},
            }
        )
        self.assertEqual(
            _catalog_result(
                client,
                self.lifecycle(),
                expected_tool_count=2,
                required_tools=("release.get",),
            )["toolCount"],
            2,
        )

    def test_replayed_cursor_or_duplicate_tool_cannot_pass_as_complete(self) -> None:
        for pages in (
            {
                None: {"tools": [{"name": "release.apply"}], "nextCursor": "p2"},
                "p2": {"tools": [{"name": "release.get"}], "nextCursor": "p2"},
            },
            {
                None: {"tools": [{"name": "release.apply"}], "nextCursor": "p2"},
                "p2": {"tools": [{"name": "release.apply"}]},
            },
        ):
            with self.subTest(pages=pages):
                with self.assertRaises(McpProbeError):
                    _catalog_result(
                        self.CatalogClient(pages),
                        self.lifecycle(),
                        expected_tool_count=None,
                        required_tools=("release.apply",),
                    )

    def test_catalog_pages_are_bounded_before_readiness_passes(self) -> None:
        from mcp_probe import MAX_TOOL_CATALOG_PAGES, MAX_TOOL_CATALOG_NAMES

        pages = {None: {"tools": [{"name": "release.apply"}], "nextCursor": "p1"}}
        for i in range(1, MAX_TOOL_CATALOG_PAGES):
            pages[f"p{i}"] = {
                "tools": [{"name": f"tool-{i}"}],
                "nextCursor": f"p{i + 1}",
            }
        with self.assertRaisesRegex(McpProbeError, "page count"):
            _catalog_result(
                self.CatalogClient(pages),
                self.lifecycle(),
                expected_tool_count=None,
                required_tools=("release.apply",),
            )
        with self.assertRaisesRegex(McpProbeError, "tool count"):
            _catalog_result(
                self.CatalogClient(
                    {None: {"tools": [{"name": f"tool-{i}"} for i in range(MAX_TOOL_CATALOG_NAMES + 1)]}}
                ),
                self.lifecycle(),
                expected_tool_count=None,
                required_tools=(),
            )

    def test_malformed_cursor_and_incomplete_result_never_green(self) -> None:
        for invalid in ([], 123):
            with self.subTest(cursor=invalid):
                client = self.CatalogClient({None: {"tools": [{"name": "release.apply"}], "nextCursor": invalid}})
                with self.assertRaises(McpProbeError):
                    _catalog_result(
                        client,
                        self.lifecycle(),
                        expected_tool_count=None,
                        required_tools=("release.apply",),
                    )
        client = self.CatalogClient({None: {"resultType": "partial", "tools": [{"name": "release.apply"}]}})
        with self.assertRaises(McpProbeError):
            _catalog_result(
                client,
                self.lifecycle(),
                expected_tool_count=None,
                required_tools=("release.apply",),
            )


class RuntimeProbeTransportTests(unittest.TestCase):
    def test_mcp_transport_never_reads_unbounded_json_or_sse(self) -> None:
        class BoundedResponse:
            status = 200
            headers = _Headers({"Content-Type": "application/json"})

            def __init__(self, too_large: bool):
                self.too_large = too_large
                self.read_sizes = []

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, size=None):
                self.read_sizes.append(size)
                if self.too_large:
                    return b"x" * 17
                return b'{"jsonrpc":"2.0","id":1,"result":{}}'

        from mcp_probe import McpClient

        for exceeds in (False, True):
            with self.subTest(exceeds=exceeds):
                response = BoundedResponse(exceeds)
                client = McpClient("http://127.0.0.1:1/mcp", "test-only", client_name="bounded")
                with (
                    mock.patch("mcp_probe.MAX_MCP_RESPONSE_BYTES", 16 if exceeds else 64, create=True),
                    mock.patch("mcp_probe.urllib.request.urlopen", return_value=response),
                ):
                    if exceeds:
                        with self.assertRaisesRegex(McpProbeError, "size|bound|large"):
                            client.request("tools/list")
                    else:
                        self.assertEqual(client.request("tools/list"), {})
                self.assertEqual(response.read_sizes, [17 if exceeds else 65])

    def test_http_error_response_cannot_exceed_the_same_body_limit(self) -> None:
        from io import BytesIO
        from urllib.error import HTTPError

        url = "http://127.0.0.1:1/mcp"
        error = HTTPError(
            url,
            503,
            "upstream unavailable",
            _Headers({"Content-Type": "application/json"}),
            BytesIO(b"x" * 17),
        )
        with (
            mock.patch("mcp_probe.MAX_MCP_RESPONSE_BYTES", 16),
            mock.patch("mcp_probe.urllib.request.urlopen", side_effect=error),
        ):
            with self.assertRaisesRegex(McpProbeError, "bounded response size"):
                McpClient(url, "test-only", client_name="error-bound").request("tools/list")

    def test_sse_success_still_decodes_below_response_limit(self) -> None:
        class SseResponse:
            status = 200
            headers = _Headers({"Content-Type": "text/event-stream"})

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, size=None):
                self.read_bound = size
                return b'data: {"jsonrpc":"2.0","id":1,"result":{"tools":[]}}\n\n'

        response = SseResponse()
        with (
            mock.patch("mcp_probe.MAX_MCP_RESPONSE_BYTES", 128),
            mock.patch("mcp_probe.urllib.request.urlopen", return_value=response),
        ):
            value = McpClient("http://127.0.0.1:1/mcp", "test-only", client_name="sse-bound").request("tools/list")
        self.assertEqual(value, {"tools": []})
        self.assertEqual(response.read_bound, 129)

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

    def test_probe_client_accepts_notification_before_exact_sse_result(self) -> None:
        class SseResponse(_Response):
            headers = _Headers({"Content-Type": "text/event-stream"})

            def read(self, size=None):
                return (
                    b'data: {"jsonrpc":"2.0","method":"notifications/progress"}\n\n'
                    b'data: {"jsonrpc":"2.0","id":1,"result":{"supportedVersions":[]}}\n\n'
                )

        client = McpClient("https://mcp.example.invalid/mcp", "test-token", client_name="consumer")
        with mock.patch("mcp_probe.urllib.request.urlopen", return_value=SseResponse()):
            self.assertEqual(client.request("server/discover", {}), {"supportedVersions": []})


class RuntimeCredentialTests(unittest.TestCase):
    def test_inline_credential_remains_migration_compatible(self) -> None:
        self.assertEqual(load_bearer_token({"ORDIVON_BEARER_TOKEN": "test"}), "test")

    def test_environment_file_parser_is_shared_and_bounded_to_key_value_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runtime.env"
            path.write_text(
                "# comment\nORDIVON_BIND=127.0.0.1:8897\nORDIVON_BEARER_TOKEN_FILE='/etc/ordivon/runtime-mcp.token'\n",
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
                load_bearer_token(
                    {
                        "ORDIVON_BEARER_TOKEN": "inline",
                        "ORDIVON_BEARER_TOKEN_FILE": str(path),
                    }
                )


if __name__ == "__main__":
    unittest.main()
