"""Guard against policy decisions reappearing in business modules."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "ordivon_gateway"
EXTRACTED = {
    "access_auth.py",
    "audit.py",
    "authorization_targets.py",
    "authzen_authorizer.py",
    "capability_authz.py",
    "http_ingress_guard.py",
    "ingress_identity.py",
    "owner_identity.py",
}
EXPECTED_SECURITY = EXTRACTED | {"__init__.py", "entrypoint.py", "execution_access.py"}


def test_permission_files_have_single_physical_home() -> None:
    assert {p.name for p in (ROOT / "security").glob("*.py")} == EXPECTED_SECURITY
    assert all(not (ROOT / name).exists() for name in EXTRACTED)


def test_business_modules_call_only_security_facade() -> None:
    for file in ROOT.glob("*.py"):
        content = file.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level == 1:
                    assert not (node.module is not None and node.module.startswith("security.")), (
                        file.name
                    )
                if node.level == 0:
                    assert not (
                        node.module is not None
                        and node.module.startswith("ordivon_gateway.security.")
                    ), file.name
        for forbidden in (
            "AuthZenPrincipalAuthorizer(",
            "GatewayCapabilityAuthorizationMiddleware(",
            "CloudflareAccessMiddleware(",
            "_read_private_secret_file(",
        ):
            assert forbidden not in content, (file.name, forbidden)
