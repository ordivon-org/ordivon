"""Read-only operator preflight transport for the existing authenticated PDP."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any

import requests

from .owner_identity import _read_private_token_file
from .pdp_wire import MAX_RESPONSE_BYTES, decode_object, read_response
from .policy_standing import StandingExpectation, qualify_decision, qualify_pair

ENDPOINT = "https://127.0.0.1:18787/access/v1/evaluation"
CONFIG_ENV = "ORDIVON_GATEWAY_RELEASE_POLICY_STANDING_CONFIG"
BEARER_ENV = "ORDIVON_GATEWAY_RELEASE_POLICY_STANDING_BEARER_FILE"
CA_ENV = "ORDIVON_GATEWAY_RELEASE_POLICY_STANDING_CA_FILE"


def _read_expectation(path: Path) -> StandingExpectation:
    # Explicit operator configuration only, not another service's private data.
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("operator standing expectation unavailable")
    with path.open("rb") as source:
        return StandingExpectation.from_document(decode_object(source.read(MAX_RESPONSE_BYTES + 1)))


def observe_pair(
    expectation: StandingExpectation,
    *,
    bearer: str,
    session: requests.Session,
    endpoint: str = ENDPOINT,
) -> dict[str, Any]:
    """Exactly two authenticated read evaluations, no retry or Owner call."""
    if len(bearer) < 32 or any(c.isspace() for c in bearer):
        raise ValueError("invalid standing client credential")
    witnesses = []
    deadline = time.monotonic() + 15
    for permit in (True, False):
        if time.monotonic() > deadline:
            raise ValueError("Security standing pair deadline exceeded")
        request_id = str(uuid.uuid4())
        started = time.time_ns() // 1_000_000
        with session.post(
            endpoint,
            data=expectation.payload(permit=permit),
            headers={
                "Authorization": "Bearer " + bearer,
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Request-ID": request_id,
                "X-Ordivon-Policy-Standing": "v1",
            },
            timeout=(3, 4),
            allow_redirects=False,
            stream=True,
        ) as response:
            if response.status_code != 200:
                raise ValueError("Security standing transport not qualified")
            body = read_response(response, deadline=deadline)
            witnesses.append(
                qualify_decision(
                    expectation,
                    permit=permit,
                    request_id=request_id,
                    response_request_id=response.headers.get("X-Request-ID"),
                    cache_control=response.headers.get("Cache-Control"),
                    response=body,
                    started_ms=started,
                    received_ms=time.time_ns() // 1_000_000,
                )
            )
    if time.monotonic() > deadline:
        raise ValueError("Security standing pair deadline exceeded")
    result = qualify_pair(*witnesses, now_ms=time.time_ns() // 1_000_000)
    result["policySha256"] = expectation.policy_sha256
    result["declaredReleaseRevision"] = expectation.release_revision
    return result


def observe_configured_pair() -> dict[str, Any]:
    config = os.environ.get(CONFIG_ENV, "")
    bearer_path = os.environ.get(BEARER_ENV, "")
    if (
        not config
        or not bearer_path
        or not Path(bearer_path).is_absolute()
        or not Path(config).is_absolute()
    ):
        raise ValueError("operator standing inputs unavailable")
    private = Path("/run/credentials/ordivon-security-gateway-authzen.service")
    # Resolve aliases before opening either operator-supplied input.
    if any(
        Path(path).resolve(strict=True).is_relative_to(private) for path in (config, bearer_path)
    ):
        raise ValueError("Security service private credentials are not consumer inputs")
    expectation = _read_expectation(Path(config))
    # The caller explicitly supplies its own authorized client credential.
    # Do not open any other systemd service's private credential directory.
    if Path(bearer_path).is_relative_to(
        "/run/credentials/ordivon-security-gateway-authzen.service"
    ):
        raise ValueError("Security service private credentials are not consumer inputs")
    bearer = _read_private_token_file(bearer_path)
    with requests.Session() as session:
        # No ambient proxy, netrc authentication, or redirect forwarding of bearer.
        session.trust_env = False
        ca = Path(os.environ.get(CA_ENV, "/etc/ssl/certs/ca-certificates.crt"))
        if not ca.is_absolute() or not ca.is_file():
            raise ValueError("Security standing TLS trust unavailable")
        session.verify = str(ca)
        return observe_pair(expectation, bearer=bearer, session=session)
