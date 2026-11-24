"""Explicitly configured Cloudflare Access operator trust.

Cloudflare Access remains the JWT issuer/audience/JWKS/expiry verifier.
This object is a *security policy composition choice*, NOT a second identity
provider or a caller-authored Actor claim. Only the ingress middleware can
stamp a request state as a verified Cloudflare JWT. Local Harness bearers,
stdio and unverified MCP metadata can never inherit the trusted operator path.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .ingress_identity import identity_from_state


@dataclass(frozen=True, slots=True)
class TrustedCloudflareOperator:
    issuer: str

    def allows(self, state: Mapping[str, Any]) -> bool:
        identity = identity_from_state(state)
        return bool(
            identity is not None
            and state.get("ordivon_access_verified_by_gateway") == "cloudflare_access_jwt"
            and identity.issuer == self.issuer
            and identity.principal.startswith("principal:cf-access:")
            and len(identity.principal) == len("principal:cf-access:") + 64
            and all(char in "0123456789abcdef" for char in identity.principal[-64:])
        )
