"""Cross-owner native OPA / AuthZEN / HTTPS evidence qualification.

Opt in with an exact reviewed Security checkout. Only disposable fixture
credentials and grants; no production endpoint, policy data or credentials.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest
import requests
import uvicorn

from ordivon_gateway.security.policy_standing import StandingExpectation
from ordivon_gateway.security.standing_transport import observe_pair

SOURCE = os.environ.get("ORDIVON_SECURITY_STANDING_FIXTURE_SOURCE")
pytestmark = pytest.mark.skipif(
    not SOURCE, reason="requires independently selected exact Security producer source"
)
REVISION = "a" * 40  # Deliberately synthetic release label; policy bytes are hashed.
PERMIT = "principal:cf-access:" + "a" * 64
DENY = "principal:cf-access:" + "b" * 64
ISSUER = "https://fixture.invalid"
REF = "message:fixture:中a文"


@dataclass(frozen=True)
class Fixture:
    policy: Path
    data: Path
    token_path: Path
    token: str
    cert: Path
    key: Path
    opa: str
    expectation: StandingExpectation
    make_app: object
    document: dict


@pytest.fixture
def native_fixture(tmp_path, monkeypatch):
    root = Path(SOURCE).resolve(strict=True)
    assert (root / "src/ordivon_security_gateway_authzen/policy_evaluation.py").is_file()
    monkeypatch.syspath_prepend(str(root / "src"))
    from ordivon_security_gateway_authzen.server import make_app

    opa, openssl = shutil.which("opa"), shutil.which("openssl")
    assert opa and openssl, "native OPA and OpenSSL required by opted-in qualification"
    policy = tmp_path / "releases" / REVISION / "policies" / "gateway_artifact.rego"
    policy.parent.mkdir(parents=True)
    shutil.copyfile(root / "policies/gateway_artifact.rego", policy)
    data, token_path = tmp_path / "data.json", tmp_path / "token"
    now = int(time.time())
    grant = {
        "active": True,
        "principalId": PERMIT,
        "issuer": ISSUER,
        "actorRef": "actor:fixture:read",
        "notBeforeEpochSeconds": now - 30,
        "expiresAtEpochSeconds": now + 3600,
        "allowedTools": ["message.get"],
        "allowedActions": [],
        "exactRefs": [REF],
        "namespacePrefixes": [],
    }
    document = {
        "ordivon": {
            "security": {
                "gateway_artifact_config": {"cf_issuer": ISSUER},
                "gateway_host_actor_grants": [grant],
            }
        }
    }
    data.write_text(json.dumps(document))
    token = secrets.token_hex(32)
    token_path.write_text(token)
    data.chmod(0o600)
    token_path.chmod(0o600)
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=127.0.0.1",
            "-addext",
            "subjectAltName=IP:127.0.0.1",
            "-keyout",
            str(key),
            "-out",
            str(cert),
        ],
        check=True,
        capture_output=True,
        timeout=10,
    )
    exp = StandingExpectation.from_document(
        {
            "policySha256": "sha256:" + hashlib.sha256(policy.read_bytes()).hexdigest(),
            "releaseRevision": REVISION,
            "issuer": ISSUER,
            "permitPrincipal": PERMIT,
            "denyPrincipal": DENY,
            "messageRef": REF,
        }
    )
    return Fixture(policy, data, token_path, token, cert, key, opa, exp, make_app, document)


@contextmanager
def native_server(fixture):
    app = fixture.make_app(
        token_path=str(fixture.token_path),
        policy=str(fixture.policy),
        policy_data=str(fixture.data),
        opa=fixture.opa,
    )
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(
            uvicorn.Config(
                app,
                host="127.0.0.1",
                port=port,
                log_level="critical",
                access_log=False,
                ssl_certfile=str(fixture.cert),
                ssl_keyfile=str(fixture.key),
            )
        )
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 8
            while not server.started and thread.is_alive() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert server.started
            yield f"https://127.0.0.1:{port}/access/v1/evaluation"
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive(), "private fixture server failed to stop"


class ObservingSession(requests.Session):
    def __init__(self, cert, *, before_second=None, second_endpoint=None):
        super().__init__()
        self.verify = str(cert)
        self.trust_env = False
        self.calls = 0
        self.before_second = before_second
        self.second_endpoint = second_endpoint

    def post(self, url, **kwargs):
        self.calls += 1
        if self.calls == 2:
            if self.before_second:
                self.before_second()
            if self.second_endpoint:
                url = self.second_endpoint
        return super().post(url, **kwargs)


def test_real_security_producer_gateway_consumer_native_tls(native_fixture):
    f = native_fixture
    with native_server(f) as endpoint, ObservingSession(f.cert) as session:
        result = observe_pair(f.expectation, bearer=f.token, session=session, endpoint=endpoint)
        assert result["standing"] == "OBSERVED_FOR_EXACT_READ_PAIR"
        assert result["policySha256"] == f.expectation.policy_sha256
        assert result["declaredReleaseRevision"] == REVISION
        assert session.calls == 2
        assert f.token not in json.dumps(result) and PERMIT not in json.dumps(result)
        assert "policyDataCommitment" not in result


def test_same_decisions_different_native_data_commitment_rejected(native_fixture):
    f = native_fixture

    def change_data():
        f.document["fixtureUnrelated"] = True
        f.data.write_text(json.dumps(f.document))

    with (
        native_server(f) as endpoint,
        ObservingSession(f.cert, before_second=change_data) as session,
    ):
        with pytest.raises(ValueError, match="not one fresh policy observation"):
            observe_pair(f.expectation, bearer=f.token, session=session, endpoint=endpoint)
        assert session.calls == 2


def test_two_real_producer_instances_cannot_be_composed(native_fixture):
    f = native_fixture
    with (
        native_server(f) as first,
        native_server(f) as second,
        ObservingSession(f.cert, second_endpoint=second) as session,
    ):
        with pytest.raises(ValueError, match="not one fresh policy observation"):
            observe_pair(f.expectation, bearer=f.token, session=session, endpoint=first)
        assert session.calls == 2


@pytest.mark.parametrize("mode", ["invalid_bearer", "wrong_policy", "grant_removed"])
def test_native_negative_does_not_attempt_second_probe(native_fixture, mode):
    f = native_fixture
    expectation, bearer = f.expectation, f.token
    if mode == "invalid_bearer":
        bearer = secrets.token_hex(32)
    elif mode == "wrong_policy":
        from dataclasses import replace

        expectation = replace(expectation, policy_sha256="sha256:" + "0" * 64)
    else:
        f.document["ordivon"]["security"]["gateway_host_actor_grants"] = []
        f.data.write_text(json.dumps(f.document))
    with native_server(f) as endpoint, ObservingSession(f.cert) as session:
        with pytest.raises(ValueError):
            observe_pair(expectation, bearer=bearer, session=session, endpoint=endpoint)
        assert session.calls == 1


def test_native_untrusted_tls_certificate_refused(native_fixture, tmp_path):
    f = native_fixture
    # A valid but unrelated local CA must not authenticate the fixture endpoint.
    openssl = shutil.which("openssl")
    other, key = tmp_path / "other.pem", tmp_path / "other-key.pem"
    subprocess.run(
        [
            openssl,
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=UnrelatedFixtureCA",
            "-keyout",
            str(key),
            "-out",
            str(other),
        ],
        check=True,
        capture_output=True,
        timeout=10,
    )
    with native_server(f) as endpoint, ObservingSession(other) as session:
        with pytest.raises(requests.exceptions.SSLError):
            observe_pair(f.expectation, bearer=f.token, session=session, endpoint=endpoint)
        assert session.calls == 1


def test_native_policy_bytes_change_between_decisions_rejected(native_fixture):
    f = native_fixture

    def change_policy():
        # Comment only: both native authorization decisions still hold, but
        # the second response no longer proves the expected exact policy.
        f.policy.write_bytes(f.policy.read_bytes() + b"\n# changed source bytes\n")

    with (
        native_server(f) as endpoint,
        ObservingSession(f.cert, before_second=change_policy) as session,
    ):
        with pytest.raises(ValueError, match="standing identity or input binding invalid"):
            observe_pair(f.expectation, bearer=f.token, session=session, endpoint=endpoint)
        assert session.calls == 2
