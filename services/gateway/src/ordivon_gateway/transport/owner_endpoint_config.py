"""Owner endpoint configuration projection, independent of MCP network calls.

Environment variables supply endpoint references and credential-file paths;
actual credential verification/loading remains in security.owner_identity.
"""

from __future__ import annotations

import os

from ..security.owner_identity import OwnerEndpoint


def owner_endpoints_from_env() -> dict[str, OwnerEndpoint]:
    owners: dict[str, OwnerEndpoint] = {}
    mapping = {
        "runtime.linux": {
            "url": "ORDIVON_GATEWAY_LINUX_RUNTIME_URL",
            "bearer": "ORDIVON_GATEWAY_LINUX_RUNTIME_BEARER_TOKEN_FILE",
        },
        "runtime.harness": {
            "url": "ORDIVON_GATEWAY_HARNESS_RUNTIME_URL",
            "bearer": "ORDIVON_GATEWAY_HARNESS_RUNTIME_BEARER_TOKEN_FILE",
        },
        "runtime.windows": {
            "url": "ORDIVON_GATEWAY_WINDOWS_RUNTIME_URL",
            "bearer": "ORDIVON_GATEWAY_WINDOWS_RUNTIME_BEARER_TOKEN_FILE",
            "access_id": "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_ID_FILE",
            "access_secret": "ORDIVON_GATEWAY_WINDOWS_ACCESS_CLIENT_SECRET_FILE",
            "mcp_mode": "ORDIVON_GATEWAY_WINDOWS_RUNTIME_MCP_MODE",
        },
        "host": {
            "url": "ORDIVON_GATEWAY_HOST_URL",
            "bearer": "ORDIVON_GATEWAY_HOST_BEARER_TOKEN_FILE",
        },
        "host.read": {
            "url": "ORDIVON_GATEWAY_HOST_READ_URL",
            "bearer": "ORDIVON_GATEWAY_HOST_READ_BEARER_TOKEN_FILE",
        },
        "skills": {
            "url": "ORDIVON_GATEWAY_SKILLS_URL",
            "bearer": "ORDIVON_GATEWAY_SKILLS_BEARER_TOKEN_FILE",
        },
    }
    for owner_id, keys in mapping.items():
        url = os.environ.get(str(keys["url"]), "").strip()
        if not url:
            continue
        token_file = os.environ.get(str(keys["bearer"]))
        access_id_key = keys.get("access_id")
        access_secret_key = keys.get("access_secret")
        access_id = os.environ.get(str(access_id_key)) if access_id_key else None
        access_secret = os.environ.get(str(access_secret_key)) if access_secret_key else None
        mode_key = keys.get("mcp_mode")
        mcp_mode = os.environ.get(str(mode_key), "auto").strip() if mode_key else "auto"
        owners[owner_id] = OwnerEndpoint(
            url=url,
            bearer_token_file=token_file.strip() if token_file else None,
            access_client_id_file=access_id.strip() if access_id else None,
            access_client_secret_file=access_secret.strip() if access_secret else None,
            mcp_mode=mcp_mode,
        )
    return owners
