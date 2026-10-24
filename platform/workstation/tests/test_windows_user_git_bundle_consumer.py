"""A Windows active_user Git bundle handoff is a narrow consumer, not a new Git backend."""
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "windows" / "user_git_bundle_checkout.ps1"


def test_bundle_checkout_requires_exact_rev_and_refuses_service_context():
    code = SCRIPT.read_text(encoding="utf-8")
    assert "ExpectedRevision" in code
    assert "^[0-9a-fA-F]{40}$" in code
    assert "SERVICE_IDENTITY_NOT_AGENT" in code
    assert "git" in code.lower()
    assert "bundle" in code.lower()


def test_bundle_checkout_reuses_git_and_no_ambient_trust_or_shared_objects():
    code = SCRIPT.read_text(encoding="utf-8")
    assert "list-heads" in code
    assert "--no-local" in code
    assert "--no-hardlinks" in code
    assert "--no-checkout" in code
    assert "objects\\info\\alternates" in code
    assert "rev-parse HEAD" in code
    assert "remote remove origin" in code
    assert "SOURCE_REVISION_MISMATCH" in code
    assert "TARGET_ALREADY_EXISTS" in code
    assert "git config --global" not in code
    assert "safe.directory=*" not in code
    assert "Set-Acl" not in code
    assert "icacls" not in code


def test_bundle_checkout_emits_receipt_without_false_dependency_claims():
    code = SCRIPT.read_text(encoding="utf-8")
    assert "READY_TO_CONSUME" in code
    assert "dependencies_materialized" in code
    assert "external_effects" in code
    assert "selectedToolPaths" not in code


def test_bundle_receipt_is_published_only_after_transactional_checkout():
    """A failed clone may never occupy the consumer's final Workspace path."""
    code = SCRIPT.read_text(encoding="utf-8")
    assert "GetRandomFileName" in code
    assert "[IO.Directory]::Move($staging, $target)" in code
    assert "finally {" in code
    assert "Remove-Item -LiteralPath $staging -Recurse -Force" in code
    assert code.index("[IO.Directory]::Move($staging, $target)") < code.index(
        "standing = 'READY_TO_CONSUME'"
    )
