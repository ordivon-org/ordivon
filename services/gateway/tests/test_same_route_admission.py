"""Adversarial proof boundaries for Gateway same-route promotion qualification.

The physical source/Host/AuthZEN/cloudflare service canaries run in a separate
installed-acceptance lane; CI does not invent a live authorized Principal.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging" / "check_same_route_admission.py"
INSTALL = ROOT / "packaging" / "install_release.sh"


@pytest.fixture(scope="module")
def qualifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location("gateway_same_route_admission", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _release(tmp_path: Path, name: str, rel: str, content: str) -> Path:
    release = tmp_path / name
    path = release / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return release


def test_original_gateway_root_only_allows_exact_host_error_refactor(
    qualifier: ModuleType, tmp_path: Path
) -> None:
    rel = qualifier.MCP_ROOT
    old = _release(
        tmp_path,
        "old",
        rel,
        "from .security import owner_error_result as _owner_error_result\n"
        "from .service import GatewayService\n"
        "register_host_tools(server, gateway, _owner_boundary)\n",
    )
    new = _release(
        tmp_path,
        "new",
        rel,
        "from .service import GatewayService\n"
        "from .transport.owner_error_projection import "
        "owner_error_result as _owner_error_result\n"
        "register_host_tools(server, gateway, _owner_boundary, _owner_error_result)\n",
    )
    assert qualifier._same_mcp_composition(old, new)
    # The synthetic consumer's policy / registration cannot change invisibly.
    attack = (
        (new / rel)
        .read_text()
        .replace("register_host_tools(server,", "register_host_tools_unprotected(server,")
    )
    (new / rel).write_text(attack)
    assert not qualifier._same_mcp_composition(old, new)


def test_changed_or_symlinked_security_source_does_not_qualify(
    qualifier: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for rel in qualifier.STABLE_SECURITY_SOURCE:
        _release(tmp_path, "old", rel, "same protected source\n")
        _release(tmp_path, "new", rel, "same protected source\n")
    old, new = tmp_path / "old", tmp_path / "new"
    monkeypatch.setattr(qualifier, "_same_security_package", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_owner_credentials", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_mcp_composition", lambda *_: True)
    assert qualifier.source_same_route(old, new)
    security_path = "src/ordivon_gateway/security/capability_authz.py"
    (new / security_path).write_text("deny=False # authorization bypass\n")
    assert not qualifier.source_same_route(old, new)
    (new / security_path).unlink()
    (new / security_path).symlink_to(old / security_path)
    with pytest.raises(ValueError, match="regular"):
        qualifier.source_same_route(old, new)


def test_ambiguous_systemd_environment_not_authority(qualifier: ModuleType) -> None:
    for env in (
        "ORDIVON_GATEWAY_HOST_URL=a ORDIVON_GATEWAY_HOST_URL=b",
        "MISSING_EQUALS",
        'ORDIVON_GATEWAY_HOST_URL="broken',
    ):
        with pytest.raises(ValueError):
            qualifier._parse_unit_environment(env)


def test_source_drift_fails_closed_before_contacting_any_remote_owner(
    qualifier: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "releases"
    (root / "old").mkdir(parents=True)
    (root / "new").mkdir(parents=True)
    (tmp_path / "current").symlink_to(root / "old")
    monkeypatch.setattr(qualifier, "LIVE_PREFIX", tmp_path)
    monkeypatch.setattr(qualifier, "source_same_route", lambda *_: False)
    monkeypatch.setattr(
        qualifier,
        "_qualified_live_config",
        lambda *_: pytest.fail("source drift must never ask owner credentials"),
    )
    result = qualifier.assess(root / "old", root / "new")
    assert result["status"] == "NO_GO"
    assert result["reason"] == "SOURCE_AUTHORITY_OR_COMPOSITION_DRIFT"


def test_owner_token_reader_and_mcp_auth_refactor_cannot_expand_authority(
    qualifier: ModuleType, tmp_path: Path
) -> None:
    for rel in (qualifier.OWNER_IDENTITY_SOURCE, qualifier.UPSTREAM_SOURCE):
        tracked = (ROOT / rel).read_text(encoding="utf-8")
        _release(tmp_path, "old", rel, tracked)
        _release(tmp_path, "new", rel, tracked)
    old, new = tmp_path / "old", tmp_path / "new"
    assert qualifier._same_owner_credentials(old, new)
    token_file = new / qualifier.OWNER_IDENTITY_SOURCE
    original = token_file.read_text(encoding="utf-8")
    assert 'return _read_private_secret_file(path_text, "owner bearer token")' in original
    token_file.write_text(
        original.replace(
            'return _read_private_secret_file(path_text, "owner bearer token")',
            'return "untrusted credential substitution"',
        )
    )
    assert not qualifier._same_owner_credentials(old, new)


@pytest.mark.parametrize(
    ("status", "qualified"), [(200, False), (302, False), (401, True), (403, True), (500, False)]
)
def test_remote_cloudflare_negative_requires_exact_auth_denial_without_redirect(
    qualifier: ModuleType, monkeypatch: pytest.MonkeyPatch, status: int, qualified: bool
) -> None:
    import urllib.error
    import urllib.request

    def opener(*handlers):
        assert any(isinstance(h, urllib.request.ProxyHandler) for h in handlers)
        assert any(type(h).__name__ == "_NoRedirect" for h in handlers)

        class Client:
            def open(self, request, *, timeout):
                assert request.full_url == "https://gateway-mcp.ordivon.com/mcp"
                if status != 200:
                    raise urllib.error.HTTPError(request.full_url, status, "probe", None, None)

                class Response:
                    def close(self) -> None:
                        pass

                return Response()

        return Client()

    monkeypatch.setattr(qualifier.urllib.request, "build_opener", opener)
    assert qualifier._remote_anonymous_denied() is qualified


def test_same_route_backend_cutover_not_contained_in_a_source_result(
    qualifier: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old = tmp_path / "releases" / "old"
    new = tmp_path / "releases" / "new"
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    (tmp_path / "current").symlink_to(old)
    monkeypatch.setattr(qualifier, "LIVE_PREFIX", tmp_path)
    monkeypatch.setattr(qualifier, "source_same_route", lambda *_: False)
    result = qualifier.assess(old, new)
    assert result["status"] == "NO_GO"
    assert result.get("candidateRealHostReadAccepted") is None


def test_security_package_drift_and_hidden_new_module_fail_closed(
    qualifier: ModuleType, tmp_path: Path
) -> None:
    import shutil

    original = ROOT / "src/ordivon_gateway/security"
    for branch in ("old", "new"):
        shutil.copytree(original, tmp_path / branch / "src/ordivon_gateway/security")
    old, new = tmp_path / "old", tmp_path / "new"
    assert qualifier._same_security_package(old, new)

    source = new / "src/ordivon_gateway/security/trusted_operator.py"
    baseline = source.read_text(encoding="utf-8")
    source.write_text(baseline + "\n# forged trusted operator export\n")
    assert not qualifier._same_security_package(old, new)
    source.write_text(baseline)

    poison = new / "src/ordivon_gateway/security/unreviewed_grant.py"
    poison.write_text("ALLOW_ALL = True\n")
    assert not qualifier._same_security_package(old, new)
    poison.unlink()

    facade = new / "src/ordivon_gateway/security/__init__.py"
    facade.write_text(facade.read_text() + "\nunsafe_alias = lambda *_: True\n")
    assert not qualifier._same_security_package(old, new)


def test_release_source_parent_symlink_does_not_masquerade_as_immutable_source(
    qualifier: ModuleType, tmp_path: Path
) -> None:
    root = tmp_path / "release"
    actual = root / "trusted"
    actual.mkdir(parents=True)
    (actual / "policy.py").write_text("allow=False\n")
    (root / "alias").symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        qualifier._safe_regular(root, "alias/policy.py")


def test_install_release_accepts_only_native_derived_same_route_or_original_cutover() -> None:
    source = INSTALL.read_text(encoding="utf-8")
    assert "check_same_route_admission.py" in source
    assert "check_live_host_admission.py" in source
    # A caller-supplied --skip-security or --same-route is not a classification.
    assert "--skip-security" not in source
    assert "--same-route" not in source
    assert source.index("check_same_route_admission.py") < source.index(
        "check_live_host_admission.py"
    )
    assert source.index("check_live_host_admission.py") < source.index('ln -sfn "releases/$COMMIT"')
