"""Explicit cross-Owner acceptance against an independently selected Security source.

No production credentials or ports. Not silently skipped by the caller; missing
producer, native OPA or OpenSSL is a failed qualification. The caller binds the
producer root to its exact Git SourceCut independently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import replace
from pathlib import Path

import requests
import uvicorn

from ordivon_gateway.security.policy_standing import StandingExpectation
from ordivon_gateway.security.standing_transport import observe_pair


def reject(label, operation):
    try:
        operation()
    except ValueError, requests.RequestException:
        print("NATIVE_NEGATIVE", label, flush=True)
    else:
        raise AssertionError(label)


def qualify(root: Path, producer: Path, revision: str, opa: Path) -> None:
    sys.path.insert(0, str(producer / "src"))
    from ordivon_security_gateway_authzen import server as producer_server

    assert Path(producer_server.__file__).resolve().is_relative_to(producer.resolve())
    issuer = "https://fixture-issuer.test"
    positive = "principal:cf-access:" + "a" * 64
    negative = "principal:cf-access:" + "b" * 64
    ref = "message:fixture:exact"
    token = secrets.token_hex(32)
    key, cert = root / "key.pem", root / "cert.pem"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-days",
            "1",
            "-subj",
            "/CN=127.0.0.1",
            "-addext",
            "subjectAltName=IP:127.0.0.1",
        ],
        check=True,
        capture_output=True,
        timeout=15,
    )
    policy = root / "releases" / revision / "policies" / "gateway_artifact.rego"
    policy.parent.mkdir(parents=True)
    policy.write_bytes((producer / "policies/gateway_artifact.rego").read_bytes())
    token_path = root / "token"
    token_path.write_text(token, encoding="utf-8")
    token_path.chmod(0o600)
    data = root / "data.json"
    now = int(time.time())
    grant = {
        "active": True,
        "principalId": positive,
        "issuer": issuer,
        "actorRef": "agent:fixture:standing",
        "notBeforeEpochSeconds": now - 60,
        "expiresAtEpochSeconds": now + 600,
        "allowedTools": ["message.get"],
        "exactRefs": [ref],
        "namespacePrefixes": [],
    }

    def put(grants, extra=None):
        data.write_text(
            json.dumps(
                {
                    "ordivon": {
                        "security": {
                            "gateway_artifact_config": {"cf_issuer": issuer},
                            "gateway_host_actor_grants": grants,
                        }
                    },
                    "fixture": extra,
                }
            ),
            encoding="utf-8",
        )

    put([grant])
    expected = StandingExpectation.from_document(
        {
            "policySha256": "sha256:" + hashlib.sha256(policy.read_bytes()).hexdigest(),
            "releaseRevision": revision,
            "issuer": issuer,
            "permitPrincipal": positive,
            "denyPrincipal": negative,
            "messageRef": ref,
        }
    )

    class ChangingSession(requests.Session):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def post(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 2:
                put([grant], "different data bytes, same decisions")
            return super().post(*args, **kwargs)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(128)
        address = sock.getsockname()
        app = producer_server.make_app(
            token_path=str(token_path),
            policy=str(policy),
            policy_data=str(data),
            opa=str(opa),
        )
        server = uvicorn.Server(
            uvicorn.Config(app, log_level="error", ssl_keyfile=str(key), ssl_certfile=str(cert))
        )
        thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + 10
            while not server.started and time.monotonic() < deadline:
                time.sleep(0.02)
            assert server.started
            url = f"https://127.0.0.1:{address[1]}/access/v1/evaluation"
            with requests.Session() as session:
                session.trust_env = False
                session.verify = str(cert)

                def observe(expectation=expected, bearer=token):
                    return observe_pair(expectation, bearer=bearer, session=session, endpoint=url)

                good = observe()
                assert good["standing"] == "OBSERVED_FOR_EXACT_READ_PAIR"
                assert good["policySha256"] == expected.policy_sha256
                assert good["declaredReleaseRevision"] == revision
                print("NATIVE_REAL_OPA_TLS_PAIR", str(opa), good["standing"], flush=True)
                reject(
                    "wrong policy digest",
                    lambda: observe(replace(expected, policy_sha256="sha256:" + "f" * 64)),
                )
                reject(
                    "wrong release", lambda: observe(replace(expected, release_revision="f" * 40))
                )
                reject("wrong credential", lambda: observe(bearer="x" * 64))
                put([])
                reject("revoked grant", observe)
                put([grant, {**grant, "principalId": negative}])
                reject("foreign principal unexpectedly permitted", observe)
                put([grant])
            with ChangingSession() as session:
                session.trust_env = False
                session.verify = str(cert)
                reject(
                    "policy data changed between decisions",
                    lambda: observe_pair(expected, bearer=token, session=session, endpoint=url),
                )
            put([grant])
            with requests.Session() as session:
                session.trust_env = False
                reject(
                    "untrusted TLS",
                    lambda: observe_pair(expected, bearer=token, session=session, endpoint=url),
                )
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            assert not thread.is_alive()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--producer-root", type=Path, required=True)
    parser.add_argument("--producer-revision", required=True)
    parser.add_argument("--opa", type=Path, required=True)
    args = parser.parse_args()
    root = args.producer_root.resolve(strict=True)
    opa = args.opa.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="gateway-standing-native-") as tmp:
        qualify(Path(tmp), root, args.producer_revision, opa)
    print("NATIVE_PRODUCER_CONSUMER_PASS", args.producer_revision, flush=True)


if __name__ == "__main__":
    main()
