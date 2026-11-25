"""Static direct dependency guards, not a claim about dynamic Python imports."""

from __future__ import annotations

import ast
from importlib.util import resolve_name
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "src" / "ordivon_gateway"
SECURITY = "ordivon_gateway.security"
SECURITY_CHILDREN = {p.stem for p in (ROOT / "security").glob("*.py") if p.stem != "__init__"}
FORBIDDEN_CONSTRUCTORS = {
    "AuthZenPrincipalAuthorizer",
    "GatewayCapabilityAuthorizationMiddleware",
    "CloudflareAccessMiddleware",
    "_read_private_secret_file",
}


def violations(source: str, relative: Path) -> list[str]:
    """Resolve static absolute and relative imports by actual package location."""
    if relative.parts[0] == "security":
        return []
    package = ".".join(("ordivon_gateway", *relative.parts[:-1]))
    tree = ast.parse(source)
    violations = []
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = (
                resolve_name("." * node.level + (node.module or ""), package)
                if node.level
                else node.module or ""
            )
            paths = [(module, alias) for alias in node.names]
        elif isinstance(node, ast.Import):
            paths = [(alias.name, alias) for alias in node.names]
        else:
            continue
        for module, alias in paths:
            imported = f"{module}.{alias.name}" if isinstance(node, ast.ImportFrom) else module
            aliases[alias.asname or alias.name] = alias.name
            if imported != SECURITY and not imported.startswith(SECURITY + "."):
                continue
            if relative.parts[0] in {"logic", "capabilities"}:
                violations.append(f"business dependency: {imported}")
            elif (
                (module == SECURITY and alias.name in SECURITY_CHILDREN)
                or module.startswith(SECURITY + ".")
                or (isinstance(node, ast.Import) and imported.startswith(SECURITY + "."))
            ):
                # Existing transport configuration imports only its pure
                # endpoint representation, not a policy/credential operation.
                if not (
                    relative == Path("transport/owner_endpoint_config.py")
                    and imported == SECURITY + ".owner_identity.OwnerEndpoint"
                ):
                    violations.append(f"private security dependency: {imported}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = aliases.get(node.func.id, node.func.id)
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                continue
            if name in FORBIDDEN_CONSTRUCTORS:
                violations.append(f"security construction outside security: {name}")
    return violations


def test_permission_files_have_single_physical_home() -> None:
    # The security directory may evolve; duplicate former/root copies are not
    # permitted. Discover actual modules recursively rather than freeze names.
    internal = {p.name for p in (ROOT / "security").rglob("*.py") if p.name != "__init__.py"}
    assert internal
    duplicates = [
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*.py")
        if p.relative_to(ROOT).parts[0] != "security" and p.name in internal
    ]
    assert duplicates == []


def test_business_modules_call_only_security_facade() -> None:
    findings = {
        str(p.relative_to(ROOT)): violations(p.read_text(encoding="utf-8"), p.relative_to(ROOT))
        for p in ROOT.rglob("*.py")
    }
    assert {path: issues for path, issues in findings.items() if issues} == {}


@pytest.mark.parametrize(
    ("source", "path"),
    [
        ("from ..security import access_auth", "logic/new.py"),
        ("from ...security import access_auth", "capabilities/nested/new.py"),
        ("from .. import security", "capabilities/new.py"),
        ("import ordivon_gateway.security.owner_identity as s", "transport/new.py"),
        ("from .security.policy_standing import qualify_pair", "new.py"),
        ("from .security import policy_standing", "new.py"),
        ("from .security import AuthZenPrincipalAuthorizer as A\nA()", "new.py"),
        ("import ordivon_gateway.security as s\ns._read_private_secret_file()", "new.py"),
    ],
)
def test_direct_permission_boundary_mutants_are_rejected(source, path) -> None:
    assert violations(source, Path(path))


@pytest.mark.parametrize(
    ("source", "path"),
    [
        ("from ..contracts import CapabilityRoute", "logic/new.py"),
        ("from .security import protect_http_app", "new.py"),
        (
            "from ..security.owner_identity import OwnerEndpoint",
            "transport/owner_endpoint_config.py",
        ),
        ("from .owner_identity import _read_private_secret_file", "security/new.py"),
    ],
)
def test_non_authority_module_growth_is_permitted(source, path) -> None:
    assert violations(source, Path(path)) == []
