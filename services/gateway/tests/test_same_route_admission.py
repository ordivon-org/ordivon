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
    monkeypatch.setattr(qualifier, "_same_package_release_contract", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_security_package", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_owner_credentials", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_mcp_composition", lambda *_: True)
    # This synthetic fixture isolates the original Security-file equality
    # contract; the full executable source-closure has its own real-tree test.
    monkeypatch.setattr(qualifier, "_same_executable_source", lambda *_: True)
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
    monkeypatch.setattr(qualifier, "_authority_source_unchanged", lambda *_: False)
    monkeypatch.setattr(
        qualifier,
        "_qualified_live_config",
        lambda *_: pytest.fail("source drift must never ask owner credentials"),
    )
    result = qualifier.assess(root / "old", root / "new")
    assert result["status"] == "NO_GO"
    assert result["reason"] == "AUTHORITY_SOURCE_CHANGE_REQUIRES_SEPARATE_MIGRATION_PROOF"


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
    monkeypatch.setattr(qualifier, "_authority_source_unchanged", lambda *_: False)
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


def test_dep_lock_toolchain_and_old_security_release_checker_cannot_change(
    qualifier: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for rel in qualifier.STABLE_SECURITY_SOURCE:
        _release(tmp_path, "old", rel, "unchanged\n")
        _release(tmp_path, "new", rel, "unchanged\n")
    for branch in ("old", "new"):
        _release(
            tmp_path,
            branch,
            "pyproject.toml",
            '[project]\nname = "ordivon-gateway"\nversion = "0.10.20"\n',
        )
        _release(
            tmp_path,
            branch,
            "uv.lock",
            'version = 1\n\n[[package]]\nname = "ordivon-gateway"\nversion = "0.10.20"\n',
        )
    old, new = tmp_path / "old", tmp_path / "new"
    monkeypatch.setattr(qualifier, "_same_security_package", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_owner_credentials", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_mcp_composition", lambda *_: True)
    # This test isolates the original lock/toolchain contract.
    monkeypatch.setattr(qualifier, "_same_executable_source", lambda *_: True)
    assert qualifier.source_same_route(old, new)

    for relative in (".python-version", "packaging/check_live_host_admission.py"):
        original = new / relative
        original.write_text("untrusted new version or security checker\n")
        assert not qualifier.source_same_route(old, new), relative
        original.write_text("unchanged\n")

    project = new / "pyproject.toml"
    lock = new / "uv.lock"
    project.write_text(project.read_text().replace("0.10.20", "0.10.21"))
    assert not qualifier._same_package_release_contract(old, new)  # mismatched lock
    lock.write_text(lock.read_text().replace("0.10.20", "0.10.21"))
    assert qualifier.source_same_route(old, new)  # only version metadata advanced
    lock.write_text(lock.read_text() + '\n[[package]]\nname = "rogue"\nversion = "1.0.0"\n')
    assert not qualifier.source_same_route(old, new)  # different dependency graph
    lock.write_text(
        lock.read_text().replace('\n[[package]]\nname = "rogue"\nversion = "1.0.0"\n', "")
    )
    project.write_text(project.read_text().replace("0.10.21", "0.10.19"))
    lock.write_text(lock.read_text().replace("0.10.21", "0.10.19"))
    assert not qualifier.source_same_route(old, new)  # version downgrade


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
    assert "runtime_process_restarted=false" in source
    assert "post_promotion_agent_consumer_verified=false" in source


def test_same_route_fences_actual_owner_dispatch_source_closure(
    qualifier: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A public read action must not secretly dispatch an Owner write action."""
    import shutil

    for name in ("old", "candidate"):
        shutil.copytree(
            ROOT / "src/ordivon_gateway",
            tmp_path / name / "src/ordivon_gateway",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    old, candidate = tmp_path / "old", tmp_path / "candidate"
    monkeypatch.setattr(qualifier, "STABLE_SECURITY_SOURCE", ())
    monkeypatch.setattr(qualifier, "_same_package_release_contract", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_security_package", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_owner_credentials", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_mcp_composition", lambda *_: True)
    assert qualifier.source_same_route(old, candidate)

    # Only an isolated source transformation. No MCP call or Host effect.
    path = candidate / "src/ordivon_gateway/capabilities/host/work.py"
    original = path.read_text()
    read_dispatch = 'return await _host("work.get", {"workRef": workRef, "revision": revision})'
    assert original.count(read_dispatch) == 1
    path.write_text(
        original.replace(
            read_dispatch,
            'return await _host("work.snapshot.commit", '
            '{"workRef": workRef, "revision": revision})',
        )
    )
    assert not qualifier.source_same_route(old, candidate)
    path.write_text(original)

    # Future non-protected leaf modules, owner transport methods and dynamic
    # module additions are in the same executable-closure obligation.
    for relative in (
        "src/ordivon_gateway/capabilities/execution/commands.py",
        "src/ordivon_gateway/transport/upstream.py",
        "src/ordivon_gateway/logic/capability_projection.py",
    ):
        target = candidate / relative
        original_source = target.read_text()
        target.write_text(original_source + "\nR46_UNQUALIFIED_EXECUTABLE_CHANGE = True\n")
        assert not qualifier.source_same_route(old, candidate), relative
        target.write_text(original_source)

    new_module = candidate / "src/ordivon_gateway/capabilities/host/unreviewed_effect.py"
    new_module.write_text('def forward_write(): return "work.snapshot.commit"\n')
    assert not qualifier.source_same_route(old, candidate)
    new_module.unlink()
    assert qualifier.source_same_route(old, candidate)


def test_same_route_allows_source_comment_but_not_symlinked_module(
    qualifier: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil

    for name in ("old", "candidate"):
        shutil.copytree(
            ROOT / "src/ordivon_gateway",
            tmp_path / name / "src/ordivon_gateway",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    old, candidate = tmp_path / "old", tmp_path / "candidate"
    monkeypatch.setattr(qualifier, "STABLE_SECURITY_SOURCE", ())
    monkeypatch.setattr(qualifier, "_same_package_release_contract", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_security_package", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_owner_credentials", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_mcp_composition", lambda *_: True)
    path = candidate / "src/ordivon_gateway/capabilities/host/work.py"
    original = path.read_text()
    path.write_text(original + "\n# comment-only update: same executable AST\n")
    assert qualifier.source_same_route(old, candidate)
    path.unlink()
    path.symlink_to(old / "src/ordivon_gateway/capabilities/host/work.py")
    with pytest.raises(ValueError, match="symlink|regular"):
        qualifier.source_same_route(old, candidate)


def test_business_action_change_is_a_separate_proven_source_boundary(
    qualifier: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No historical source-digest exception and no arbitrary module bypass."""
    import shutil

    old, candidate = tmp_path / "old", tmp_path / "candidate"
    for root in (old, candidate):
        shutil.copytree(
            ROOT / "src/ordivon_gateway",
            root / "src/ordivon_gateway",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    # This is an isolated SOURCE INVENTORY test. Real immutable release
    # trust-root/SDK/Owner/PEP checks run separately in the original assessor.
    monkeypatch.setattr(qualifier, "_authority_source_unchanged", lambda *_: True)
    assert qualifier._business_action_change_scope(old, candidate) is None
    assert qualifier._same_executable_source(old, candidate)

    # Old code would have required a hardcoded previous/next SHA pair for
    # this actual business module. C instead scopes an existing operation
    # seam, preserving a mandatory independent Action/Effect canary.
    commands = candidate / "src/ordivon_gateway/capabilities/execution/commands.py"
    original = commands.read_text()
    commands.write_text(original + "\nR48_PROFILE_ACTION_SOURCE_CHANGE = True\n")
    assert not qualifier._same_executable_source(old, candidate)
    assert qualifier._business_action_change_scope(old, candidate) == frozenset(
        {Path("src/ordivon_gateway/capabilities/execution/commands.py")}
    )
    commands.write_text(original)

    # Additional new executable module, changed Owner routing, changed
    # authorization target, or arbitrary Host wrapper must NOT qualify C.
    for relative in (
        "src/ordivon_gateway/logic/routing.py",
        "src/ordivon_gateway/security/authorization_targets.py",
        "src/ordivon_gateway/capabilities/host/work.py",
        "src/ordivon_gateway/transport/upstream.py",
    ):
        target = candidate / relative
        baseline = target.read_text()
        target.write_text(baseline + "\nR48_UNREVIEWED_ROUTE_CHANGE = True\n")
        assert qualifier._business_action_change_scope(old, candidate) is None, relative
        target.write_text(baseline)

    added = candidate / "src/ordivon_gateway/capabilities/execution/hidden_owner.py"
    added.write_text('def invoke_owner(): return "release.apply"\n')
    assert qualifier._business_action_change_scope(old, candidate) is None
    added.unlink()

    candidate_path = candidate / "src/ordivon_gateway/security/capability_authz.py"
    candidate_path.unlink()
    candidate_path.symlink_to(old / "src/ordivon_gateway/security/capability_authz.py")
    with pytest.raises(ValueError, match="symlink|regular"):
        qualifier._business_action_change_scope(old, candidate)


def test_candidate_native_action_effect_canary_is_source_only_and_fail_closed(
    qualifier: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same native project Python, no Host/Runtime/Security external call."""
    assert qualifier._candidate_action_effect_canary(ROOT)
    monkeypatch.setattr(
        qualifier,
        "_CANDIDATE_ACTION_EFFECT_PROBE",
        'raise AssertionError("unsafe delegated Owner operation")',
    )
    assert not qualifier._candidate_action_effect_canary(ROOT)


def test_changed_business_code_cannot_be_relabelled_host_migration() -> None:
    installer = INSTALL.read_text(encoding="utf-8")
    # Exit 4 is a real code-only NO_GO: do not call the unrelated B checker.
    assert 'elif [ "$QUALIFICATION_RC" -eq 4 ]; then' in installer
    assert "UNQUALIFIED_BUSINESS_CODE_NO_GO" in installer
    assert installer.index("UNQUALIFIED_BUSINESS_CODE_NO_GO") < installer.index(
        "check_live_host_admission.py"
    )
    assert "QUALIFIED_BUSINESS_ACTION_CHANGE" in installer
    assert "--skip-security" not in installer


@pytest.mark.parametrize(
    ("status", "reason", "expected_code"),
    [
        ("QUALIFIED_SAME_ROUTE", None, 0),
        ("QUALIFIED_ACTION_CHANGE", None, 0),
        ("NO_GO", "UNQUALIFIED_BUSINESS_ACTION_SOURCE_CHANGE", 4),
        ("NO_GO", "ACTION_EFFECT_CONSUMER_PROOF_MISSING", 4),
        ("NO_GO", "LIVE_SAME_ROUTE_PRECONDITIONS_FAILED", 4),
        ("NO_GO", "AUTHORITY_SOURCE_CHANGE_REQUIRES_SEPARATE_MIGRATION_PROOF", 3),
        ("NO_GO", "SAME_ROUTE_PRECONDITIONS_UNOBSERVABLE", 3),
    ],
)
def test_original_release_qualification_exit_distinguishes_real_migration_from_code(
    qualifier: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    status: str,
    reason: str | None,
    expected_code: int,
) -> None:
    import sys

    observation = {
        "schemaVersion": 1,
        "kind": "ordivon.gateway-same-route-qualification",
        "status": status,
    }
    if reason is not None:
        observation["reason"] = reason
    monkeypatch.setattr(qualifier, "assess", lambda *_: observation)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "packaging/check_same_route_admission.py",
            "--installed-release",
            "/tmp/existing",
            "--candidate-release",
            "/tmp/candidate",
        ],
    )
    assert qualifier.main() == expected_code
    assert f'"status": "{status}"' in capsys.readouterr().out


def test_class_c_cannot_change_imported_authzen_host_resource_selectors(
    qualifier: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R49 live counterexample: changed import breaks PEP even if projector bytes stay."""
    import shutil

    old, candidate = tmp_path / "old", tmp_path / "candidate"
    for root in (old, candidate):
        shutil.copytree(
            ROOT / "src/ordivon_gateway",
            root / "src/ordivon_gateway",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

    # Isolate the real imported Host bindings from unrelated package metadata.
    monkeypatch.setattr(
        qualifier,
        "STABLE_SECURITY_SOURCE",
        tuple(
            path
            for path in qualifier.STABLE_SECURITY_SOURCE
            if path.startswith("src/ordivon_gateway/")
        ),
    )
    monkeypatch.setattr(qualifier, "_same_package_release_contract", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_owner_credentials", lambda *_: True)
    monkeypatch.setattr(qualifier, "_same_mcp_composition", lambda *_: True)

    target = candidate / "src/ordivon_gateway/logic/host_tool_contracts.py"
    baseline = target.read_text(encoding="utf-8")
    assert qualifier._same_security_consumed_host_bindings(old, candidate)

    # A source change in the imported selector map would make an actual
    # work.get by workRef appear unscoped to the AuthZEN target projector.
    unsafe = baseline.replace('"work.get": ("workRef",),', '"work.get": ("topicRef",),')
    assert unsafe != baseline and baseline.count('"work.get": ("workRef",),') == 1
    target.write_text(unsafe, encoding="utf-8")
    assert not qualifier._same_security_consumed_host_bindings(old, candidate)
    assert not qualifier._authority_source_unchanged(old, candidate)
    assert qualifier._business_action_change_scope(old, candidate) is None

    # Removing an Owner write from the Host capabilities list is also
    # security-relevant even if authorization_targets.py is byte-identical.
    target.write_text(
        baseline.replace('        "work.snapshot.commit",\n', "", 1), encoding="utf-8"
    )
    assert not qualifier._same_security_consumed_host_bindings(old, candidate)
    assert qualifier._business_action_change_scope(old, candidate) is None

    # A harmless addition of a non-PEP helper may still enter the separate
    # bounded Action→Effect canary; C is not the old whole-source AST A gate.
    target.write_text(
        baseline + "\n\ndef _non_security_test_helper():\n    return None\n",
        encoding="utf-8",
    )
    assert qualifier._same_security_consumed_host_bindings(old, candidate)
    assert qualifier._business_action_change_scope(old, candidate) == frozenset(
        {Path("src/ordivon_gateway/logic/host_tool_contracts.py")}
    )
