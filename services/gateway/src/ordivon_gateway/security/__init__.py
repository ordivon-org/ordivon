"""Gateway Security boundary: Cloudflare ingress, optional PDP and Runtime identity.

Business services import only this façade. Policy targets, credentials and
decision formats stay inside the Security package.
"""

from .access_auth import CloudflareAccessVerifier
from .audit import GatewayAuditMiddleware
from .authzen_authorizer import AuthZenPrincipalAuthorizer
from .capability_authz import CapabilityAuthorizer
from .entrypoint import (
    access_verifier_from_env,
    capability_authorizer_from_env,
    install_tool_security,
    protect_http_app,
    require_release_access,
)
from .execution_access import (
    qualify_gateway_operation_ref,
    require_http_execution_identity,
    verified_execution_request_id,
    verified_execution_scope,
)
from .owner_identity import (
    OwnerCallError,
    OwnerEndpoint,
    _headers_for_endpoint,
    _read_private_secret_file,
    _read_private_token_file,
    _runtime_identity_configured,
    _validate_windows_private_secret_file,
)
from .owner_identity import (
    _owner_error_result as owner_error_result,
)

__all__ = [
    "AuthZenPrincipalAuthorizer",
    "GatewayAuditMiddleware",
    "OwnerCallError",
    "OwnerEndpoint",
    "owner_error_result",
    "_headers_for_endpoint",
    "_read_private_secret_file",
    "_read_private_token_file",
    "_runtime_identity_configured",
    "_validate_windows_private_secret_file",
    "CloudflareAccessVerifier",
    "CapabilityAuthorizer",
    "access_verifier_from_env",
    "capability_authorizer_from_env",
    "install_tool_security",
    "protect_http_app",
    "qualify_gateway_operation_ref",
    "require_http_execution_identity",
    "require_release_access",
    "verified_execution_request_id",
    "verified_execution_scope",
]
