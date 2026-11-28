"""Real loopback HTTP transport witnesses for bounded PDP response handling."""

from __future__ import annotations

import asyncio
import gzip
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from ordivon_gateway.security.authzen_authorizer import (
    AuthZenAuthorizerError,
    AuthZenPrincipalAuthorizer,
)
from ordivon_gateway.security.pdp_wire import MAX_RESPONSE_BYTES, decode_object


@contextmanager
def endpoint(body, *, media="application/json", encoding=None, truncated=False):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            calls.append(json.loads(self.rfile.read(length)))
            self.send_response(200)
            self.send_header("X-Request-ID", self.headers["X-Request-ID"])
            if media is not None:
                self.send_header("Content-Type", media)
            if encoding:
                self.send_header("Content-Encoding", encoding)
            self.send_header("Content-Length", str(len(body) + (50 if truncated else 0)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/access/v1/evaluation", calls
        finally:
            server.shutdown()
            thread.join(timeout=3)
            assert not thread.is_alive()


def authorize(url):
    with requests.Session() as session:
        session.trust_env = False
        auth = AuthZenPrincipalAuthorizer(
            url,
            bearer_token_provider=lambda: "fixture-" + "x" * 32,
            session=session,
            allow_insecure_loopback=True,
        )
        return asyncio.run(
            auth.authorize(
                principal_id="principal:fixture",
                issuer="https://issuer.test",
                requested_capability="artifact.runtime",
                requested_resource={"type": "fixture", "id": "fixture"},
                tool_name="artifact.read",
                arguments={},
                request_state={},
            )
        )


def padded(size):
    prefix = b'{"decision":true,"context":{"x":"'
    suffix = b'"}}'
    return prefix + b"a" * (size - len(prefix) - len(suffix)) + suffix


@pytest.mark.parametrize(
    ("body", "kwargs"),
    [
        (padded(MAX_RESPONSE_BYTES + 1), {}),
        (gzip.compress(padded(MAX_RESPONSE_BYTES + 1)), {"encoding": "gzip"}),
        (b'{"decision":true}', {"media": "text/html"}),
        (b'{"decision":true}', {"media": None}),
        (b'{"decision":true}', {"truncated": True}),
        (rb'{"decision":true,"context":{"x":"\ud800"}}', {}),
        (rb'{"decision":false,"decisi\u006fn":true}', {}),
    ],
    ids=[
        "over-bound",
        "decoded-gzip-over-bound",
        "wrong-media",
        "no-media",
        "truncated-stream",
        "surrogate",
        "duplicate",
    ],
)
def test_native_pdp_rejects_unqualified_wire_exactly_once(body, kwargs):
    with endpoint(body, **kwargs) as (url, calls):
        with pytest.raises(AuthZenAuthorizerError):
            authorize(url)
        assert len(calls) == 1


@pytest.mark.parametrize(
    ("body", "kwargs"),
    [
        (padded(MAX_RESPONSE_BYTES), {}),
        (gzip.compress(padded(MAX_RESPONSE_BYTES)), {"encoding": "gzip"}),
        (
            rb'{"decision":true,"context":{"x":"\ud83d\ude00"}}',
            {"media": "application/json; charset=utf-8"},
        ),
        (b'{"decision":false}', {}),
    ],
    ids=["exact-bound", "decoded-gzip-exact-bound", "unicode-scalar", "deny"],
)
def test_native_pdp_accepts_qualified_wire_exactly_once(body, kwargs):
    with endpoint(body, **kwargs) as (url, calls):
        expected = "DENY" if body == b'{"decision":false}' else "ALLOW"
        assert authorize(url)["outcome"] == expected
        assert len(calls) == 1


def test_shared_decoder_nested_and_escaped_member_identity():
    assert decode_object(rb'{"x":"\ud83d\ude00","n":1.5}') == {"x": "😀", "n": 1.5}
    for raw in (
        rb'{"x":{"a":1,"\u0061":2}}',
        rb'{"\udfff":0}',
        b'{"x":1e999}',
        b'{"x":NaN}',
        b"[" * 3000 + b"]" * 3000,
    ):
        with pytest.raises(ValueError):
            decode_object(raw)
