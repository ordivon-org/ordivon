from __future__ import annotations

import asyncio
import time
import unittest
from types import SimpleNamespace

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from scripts.skills_mcp import CloudflareAccessVerifier, HybridAuthApp, McpSettings


class _FakeKeys:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token: str):
        return SimpleNamespace(key=self.key)


class _FakeAccessVerifier:
    async def verify(self, token: str) -> bool:
        return token == "valid-access-assertion"


async def _downstream(_scope, receive, send):
    while True:
        message = await receive()
        if message.get("type") != "http.request" or not message.get("more_body"):
            break
    await send({"type": "http.response.start", "status": 204, "headers": []})
    await send({"type": "http.response.body", "body": b""})


async def _request(app, headers: list[tuple[bytes, bytes]]):
    sent = []
    messages = [{"type": "http.request", "body": b"", "more_body": False}]

    async def receive():
        return messages.pop(0) if messages else {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await app({"type": "http", "method": "POST", "path": "/mcp", "headers": headers}, receive, send)
    return next(message["status"] for message in sent if message["type"] == "http.response.start")


class SkillsMcpOAuthTests(unittest.TestCase):
    def test_access_verifier_requires_signature_issuer_audience_expiry_and_rs256(self) -> None:
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = private.public_key()
        verifier = CloudflareAccessVerifier(
            issuer="https://access.example.com",
            audience="skills-audience",
            jwks_url="https://access.example.com/cdn-cgi/access/certs",
        )
        verifier._keys = _FakeKeys(public)
        now = int(time.time())

        def token(**overrides):
            claims = {
                "iss": "https://access.example.com",
                "aud": "skills-audience",
                "sub": "user-1",
                "exp": now + 300,
            }
            claims.update(overrides)
            return jwt.encode(claims, private, algorithm="RS256", headers={"kid": "k1"})

        self.assertTrue(verifier._verify_sync(token()))
        self.assertFalse(verifier._verify_sync(token(iss="https://wrong.example.com")))
        self.assertFalse(verifier._verify_sync(token(aud="wrong-audience")))
        self.assertFalse(verifier._verify_sync(token(exp=now - 120)))
        hs = jwt.encode(
            {"iss": "https://access.example.com", "aud": "skills-audience", "exp": now + 300},
            "not-a-real-access-key-that-is-at-least-32-bytes-long",
            algorithm="HS256",
        )
        self.assertFalse(verifier._verify_sync(hs))

    def test_hybrid_auth_accepts_local_operator_or_verified_access_assertion(self) -> None:
        app = HybridAuthApp(
            _downstream,
            "x" * 64,
            body_limit_bytes=1024,
            access_verifier=_FakeAccessVerifier(),
        )
        local = asyncio.run(_request(app, [(b"authorization", b"Bearer " + b"x" * 64)]))
        access = asyncio.run(
            _request(app, [(b"cf-access-jwt-assertion", b"valid-access-assertion")])
        )
        invalid = asyncio.run(
            _request(app, [(b"cf-access-jwt-assertion", b"invalid-access-assertion")])
        )
        missing = asyncio.run(_request(app, []))
        self.assertEqual(local, 204)
        self.assertEqual(access, 204)
        self.assertEqual(invalid, 401)
        self.assertEqual(missing, 401)

    def test_access_assertion_is_not_trusted_when_access_mode_is_disabled(self) -> None:
        app = HybridAuthApp(_downstream, "x" * 64, body_limit_bytes=1024)
        status = asyncio.run(
            _request(app, [(b"cf-access-jwt-assertion", b"valid-access-assertion")])
        )
        self.assertEqual(status, 401)

    def test_settings_fail_closed_when_access_configuration_is_incomplete(self) -> None:
        with self.assertRaisesRegex(ValueError, "issuer"):
            McpSettings(config_file=__import__('pathlib').Path('/tmp/cfg'), trust_cf_access=True)
        with self.assertRaisesRegex(ValueError, "audience"):
            McpSettings(
                config_file=__import__('pathlib').Path('/tmp/cfg'),
                trust_cf_access=True,
                cf_access_issuer="https://access.example.com",
            )
        settings = McpSettings(
            config_file=__import__('pathlib').Path('/tmp/cfg'),
            trust_cf_access=True,
            cf_access_issuer="https://access.example.com",
            cf_access_audience="skills",
        )
        self.assertEqual(
            settings.cf_access_jwks_endpoint,
            "https://access.example.com/cdn-cgi/access/certs",
        )


if __name__ == "__main__":
    unittest.main()
