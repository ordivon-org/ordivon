from __future__ import annotations

import asyncio
import ipaddress
import uuid
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import urlsplit

import requests


class AuthZenAuthorizerError(RuntimeError):
    pass


def _validate_endpoint(endpoint: str, *, allow_insecure_loopback: bool) -> str:
    value = endpoint.strip()
    parsed = urlsplit(value)
    if parsed.scheme == "https" and parsed.netloc and parsed.path:
        return value
    if allow_insecure_loopback and parsed.scheme == "http" and parsed.hostname:
        try:
            loopback = ipaddress.ip_address(parsed.hostname).is_loopback
        except ValueError:
            loopback = parsed.hostname == "localhost"
        if loopback and parsed.port is not None and parsed.path:
            return value
    raise AuthZenAuthorizerError(
        "AuthZEN evaluation endpoint must use HTTPS; explicit loopback HTTP is canary-only"
    )


class AuthZenPrincipalAuthorizer:
    """H2 Principal-profile AuthZEN PEP adapter.

    This adapter transports one already-verified ingress Principal plus a Gateway-derived
    capability/resource target to a standards-compatible PDP. It does not mint Agent identity,
    Delegation Grants, approvals, effect receipts, or provider truth. No request is retried.
    """

    def __init__(
        self,
        evaluation_endpoint: str,
        *,
        bearer_token_provider: Callable[[], str],
        timeout_seconds: float = 3.0,
        allow_insecure_loopback: bool = False,
        session: requests.Session | None = None,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 30:
            raise AuthZenAuthorizerError("AuthZEN timeout must be within (0, 30] seconds")
        self._endpoint = _validate_endpoint(
            evaluation_endpoint, allow_insecure_loopback=allow_insecure_loopback
        )
        self._bearer_token_provider = bearer_token_provider
        self._timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    async def authorize(
        self,
        *,
        principal_id: str,
        issuer: str,
        requested_capability: str,
        requested_resource: Mapping[str, Any],
        tool_name: str,
        arguments: Mapping[str, Any],
        request_state: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        del arguments, request_state, tool_name
        return await asyncio.to_thread(
            self._authorize_sync,
            principal_id,
            issuer,
            requested_capability,
            dict(requested_resource),
        )

    def _authorize_sync(
        self,
        principal_id: str,
        issuer: str,
        requested_capability: str,
        requested_resource: dict[str, Any],
    ) -> Mapping[str, Any]:
        token = self._bearer_token_provider().strip()
        if len(token) < 16 or any(ch.isspace() for ch in token):
            raise AuthZenAuthorizerError("AuthZEN bearer token provider returned invalid material")

        request_id = str(uuid.uuid4())
        payload = {
            "subject": {
                "type": "user",
                "id": principal_id,
                "properties": {"issuer": issuer},
            },
            "resource": requested_resource,
            "action": {"name": requested_capability},
        }
        try:
            response = self._session.post(
                self._endpoint,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-Request-ID": request_id,
                },
                timeout=self._timeout_seconds,
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise AuthZenAuthorizerError("AuthZEN PDP transport failed") from exc

        if response.status_code != 200:
            raise AuthZenAuthorizerError(
                f"AuthZEN PDP returned unexpected HTTP status {response.status_code}"
            )
        response_request_id = response.headers.get("X-Request-ID")
        if response_request_id != request_id:
            raise AuthZenAuthorizerError("AuthZEN PDP did not echo the exact X-Request-ID")
        try:
            body = response.json()
        except ValueError as exc:
            raise AuthZenAuthorizerError("AuthZEN PDP returned invalid JSON") from exc
        if not isinstance(body, dict) or not isinstance(body.get("decision"), bool):
            raise AuthZenAuthorizerError("AuthZEN PDP returned an invalid evaluation response")

        allowed = body["decision"]
        return {
            "schemaVersion": 3,
            "kind": "ordivon.security.gateway-capability-authz",
            "principalId": principal_id,
            "issuer": issuer,
            "requestedCapability": requested_capability,
            "requestedResource": requested_resource,
            "qualificationTarget": True,
            "authorizationProfile": "interactive-principal-authzen",
            "outcome": "ALLOW" if allowed else "DENY",
            "reason": "authzen-permit" if allowed else "authzen-deny",
            "authorizationEvidence": {
                "standard": "openid-authzen-authorization-api-1.0",
                "requestId": request_id,
                "responseRequestId": response_request_id,
                "decision": allowed,
            },
            "authorityProjection": None,
            "effectAdmission": None,
            "claimBoundary": (
                "Interactive Principal capability authorization only. This AuthZEN decision does "
                "not establish Agent identity, Delegation Grant, effect admission, provider "
                "execution, Artifact bytes, external effect occurrence, or domain success."
            ),
        }
