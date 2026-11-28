"""Network scoped GitHub release acquisition, without live network in unit tests."""
from __future__ import annotations

import importlib.util
import hashlib
from pathlib import Path

import pytest

MODULE = Path(__file__).parents[1] / "consumers/developer-egress/github_release_mise.py"
spec = importlib.util.spec_from_file_location("github_release_mise", MODULE)
assert spec and spec.loader
imported = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imported)


def valid_metadata() -> dict[str, object]:
    return {
        "id": imported.ASSET_ID, "name": imported.ASSET_NAME,
        "size": imported.ASSET_SIZE, "digest": "sha256:" + imported.ASSET_SHA256,
        "state": "uploaded",
    }


def test_official_release_asset_identity_and_digest() -> None:
    imported.verify_metadata(valid_metadata())


@pytest.mark.parametrize(
    "key,incorrect",
    [
        ("id", -1), ("name", "wrong.tar.zst"), ("size", 10),
        ("digest", "sha256:" + "0" * 64), ("state", "deleted"),
    ],
)
def test_mutated_upstream_asset_metadata_is_rejected(key: str, incorrect: object) -> None:
    record = valid_metadata()
    record[key] = incorrect
    with pytest.raises(ValueError, match="identity/size/digest"):
        imported.verify_metadata(record)


@pytest.mark.parametrize("warm", [False, True])
@pytest.mark.parametrize("signature_valid", [False, True])
def test_signature_before_extract_or_reuse(tmp_path, monkeypatch, warm, signature_valid):
    from subprocess import CalledProcessError, CompletedProcess

    payload = b"verified executable"
    monkeypatch.setenv("MISE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(imported, "BINARY_SHA256", hashlib.sha256(payload).hexdigest())
    target = tmp_path / "bin" / "mise"
    if warm:
        target.parent.mkdir()
        target.write_bytes(payload)
    calls = []

    def acquire(path, asset_id, size, digest):
        calls.append(("acquire", asset_id))
        path.write_bytes(b"fixture")

    def native(args, **kwargs):
        calls.append(tuple(args[:3]))
        if args[:3] == ["gh", "attestation", "verify"]:
            assert kwargs["check"] is True
            assert args[args.index("--source-ref") + 1] == "refs/tags/v" + imported.VERSION
            assert args[args.index("--predicate-type") + 1] == "https://packslip.dev/release/v1"
            assert args[args.index("--cert-oidc-issuer") + 1] == "https://token.actions.githubusercontent.com"
            if not signature_valid:
                raise CalledProcessError(1, args)
        elif args[0] == "tar":
            binary = Path(args[args.index("-C") + 1]) / "mise/bin/mise"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(payload)
        elif args[-1] == "version":
            return CompletedProcess(args, 0, imported.VERSION + " fixture", "")
        else:
            pytest.fail(f"unexpected command {args}")
        return CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(imported, "acquire_pinned_asset", acquire)
    monkeypatch.setattr(imported.subprocess, "run", native)
    if signature_valid:
        assert imported.provision() == target
        assert target.read_bytes() == payload
        assert calls[2] == ("gh", "attestation", "verify")
        assert calls[3][0] == "tar"
    else:
        with pytest.raises(CalledProcessError):
            imported.provision()
        assert calls == [("acquire", imported.ASSET_ID), ("acquire", imported.BUNDLE_ID),
                         ("gh", "attestation", "verify")]
        assert target.exists() == warm


def test_binary_only_cache_cannot_bypass_signature_when_offline(tmp_path, monkeypatch):
    payload = b"verified executable"
    monkeypatch.setenv("MISE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(imported, "BINARY_SHA256", hashlib.sha256(payload).hexdigest())
    target = tmp_path / "bin" / "mise"
    target.parent.mkdir()
    target.write_bytes(payload)

    def offline(*args, **kwargs):
        raise OSError("network unavailable")

    monkeypatch.setattr(imported.subprocess, "run", offline)
    with pytest.raises(OSError, match="unavailable"):
        imported.provision()
    assert target.read_bytes() == payload


def test_changed_existing_binary_must_refetch_not_be_trusted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MISE_DATA_DIR", str(tmp_path))
    target = tmp_path / "bin" / "mise"
    target.parent.mkdir()
    target.write_bytes(b"untrusted cached contents")
    called = []

    def fail_fetch(*args: object, **_kwargs: object) -> None:
        called.append(args)
        raise OSError("network unavailable")

    monkeypatch.setattr(imported.subprocess, "run", fail_fetch)
    with pytest.raises(OSError, match="unavailable"):
        imported.provision()
    assert called, "a mutated cached binary must require official asset revalidation"
    assert target.read_bytes() == b"untrusted cached contents"


def test_xdg_data_directory_natural_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISE_DATA_DIR", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert imported.mise_dir() == tmp_path / "mise"
    monkeypatch.setenv("MISE_DATA_DIR", str(tmp_path / "custom"))
    assert imported.mise_dir() == tmp_path / "custom"



def test_partial_binary_fails_before_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from subprocess import CompletedProcess

    monkeypatch.setenv("MISE_DATA_DIR", str(tmp_path))

    def fake_gh(args: list[str], **kwargs: object) -> CompletedProcess[str]:
        if kwargs.get("capture_output"):
            import json
            return CompletedProcess(args, 0, json.dumps(valid_metadata()), "")
        output = kwargs.get("stdout")
        assert output is not None
        output.write(b"truncated-asset")
        return CompletedProcess(args, 0, None, None)

    monkeypatch.setattr(imported.subprocess, "run", fake_gh)
    with pytest.raises(ValueError, match="partial download"):
        imported.provision()
    assert not (tmp_path / "bin/mise").exists()



def test_cached_python_interpreter_digest_mutation_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MISE_DATA_DIR", str(tmp_path))
    bin_dir = tmp_path / "installs" / "python" / "3.15.1" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python3.15").write_bytes(b"fake executable whose version may lie")
    (bin_dir / "python").symlink_to("python3.15")

    def no_exec(*_args: object, **_kwargs: object) -> None:
        pytest.fail("a digest-mismatched Python binary must never execute")

    monkeypatch.setattr(imported.subprocess, "run", no_exec)
    with pytest.raises(ValueError, match="pinned upstream"):
        imported.provision_python()


def test_python_release_metadata_pin_is_unambiguous() -> None:
    assert imported.PYTHON_REPO == "astral-sh/python-build-standalone"
    assert imported.PYTHON_ASSET_ID == 663549456
    assert imported.PYTHON_ASSET_SIZE == 38075450
    assert len(imported.PYTHON_EXECUTABLE_SHA256) == 64


@pytest.fixture
def pinned_pair(monkeypatch):
    archive, bundle = b"pinned archive", b"pinned bundle"
    for name, value in (
        ("ASSET_SIZE", len(archive)), ("ASSET_SHA256", hashlib.sha256(archive).hexdigest()),
        ("BUNDLE_SIZE", len(bundle)), ("BUNDLE_SHA256", hashlib.sha256(bundle).hexdigest()),
    ):
        monkeypatch.setattr(imported, name, value)
    return {imported.ASSET_NAME: archive, imported.BUNDLE_NAME: bundle}


@pytest.mark.parametrize("cache_state", ["absent", "empty", "complete", "archive_only",
                                        "bundle_only", "bad_archive", "bad_bundle",
                                        "unexpected_member", "symlink_member", "nonfile_member"])
def test_signed_pair_cache_classification(tmp_path, pinned_pair, cache_state):
    cache = tmp_path / "cache"
    base = tmp_path / "base"
    base.mkdir()
    if cache_state != "absent":
        cache.mkdir()
    if cache_state not in {"absent", "empty"}:
        for name, payload in pinned_pair.items():
            if cache_state == "archive_only" and name == imported.BUNDLE_NAME:
                continue
            if cache_state == "bundle_only" and name == imported.ASSET_NAME:
                continue
            (cache / name).write_bytes(payload)
        if cache_state == "bad_archive":
            (cache / imported.ASSET_NAME).write_bytes(b"wrong archive")
        elif cache_state == "bad_bundle":
            (cache / imported.BUNDLE_NAME).write_bytes(b"wrong bundle")
        elif cache_state == "unexpected_member":
            (cache / "receipt.json").write_text("{}")
        elif cache_state == "symlink_member":
            other = tmp_path / "outside"
            other.write_bytes(pinned_pair[imported.ASSET_NAME])
            (cache / imported.ASSET_NAME).unlink()
            (cache / imported.ASSET_NAME).symlink_to(other)
        elif cache_state == "nonfile_member":
            (cache / imported.BUNDLE_NAME).unlink()
            (cache / imported.BUNDLE_NAME).mkdir()
    if cache_state in {"absent", "empty", "complete"}:
        assert imported.restore_signed_pair(cache, base) == (cache_state == "complete")
        if cache_state == "complete":
            assert {p.name: p.read_bytes() for p in base.iterdir()} == pinned_pair
    else:
        with pytest.raises(ValueError, match="cache"):
            imported.restore_signed_pair(cache, base)


@pytest.mark.parametrize("initial_empty", [False, True])
def test_publish_pair_atomically_and_never_overwrite(tmp_path, pinned_pair, initial_empty):
    base = tmp_path / "base"
    base.mkdir()
    cache = tmp_path / "cache"
    if initial_empty:
        cache.mkdir()
    for name, payload in pinned_pair.items():
        (base / name).write_bytes(payload)
    imported.publish_signed_pair(cache, base)
    assert {p.name: p.read_bytes() for p in cache.iterdir()} == pinned_pair
    with pytest.raises(OSError):
        imported.publish_signed_pair(cache, base)
    assert {p.name: p.read_bytes() for p in cache.iterdir()} == pinned_pair


@pytest.mark.parametrize("warm", [False, True])
@pytest.mark.parametrize("signature_valid", [False, True])
def test_native_verification_required_on_every_cache_path(
    tmp_path, monkeypatch, pinned_pair, warm, signature_valid,
):
    from subprocess import CalledProcessError, CompletedProcess

    cache = tmp_path / "cache"
    monkeypatch.setenv("ORDIVON_MISE_SIGNED_PAIR_CACHE_DIR", str(cache))
    monkeypatch.setenv("MISE_DATA_DIR", str(tmp_path / "mise"))
    binary = b"verified executable"
    monkeypatch.setattr(imported, "BINARY_SHA256", hashlib.sha256(binary).hexdigest())
    if warm:
        cache.mkdir()
        for name, payload in pinned_pair.items():
            (cache / name).write_bytes(payload)
    calls = []

    def acquire(path, asset_id, size, digest):
        calls.append(("acquire", asset_id))
        path.write_bytes(pinned_pair[path.name])

    def native(args, **kwargs):
        calls.append(tuple(args[:3]))
        if args[:3] == ["gh", "attestation", "verify"]:
            assert kwargs["check"] is True
            if not signature_valid:
                raise CalledProcessError(1, args)
        elif args[0] == "tar":
            path = Path(args[args.index("-C") + 1]) / "mise/bin/mise"
            path.parent.mkdir(parents=True)
            path.write_bytes(binary)
        elif args[-1] == "version":
            return CompletedProcess(args, 0, imported.VERSION + " fixture", "")
        else:
            pytest.fail(f"unexpected command {args}")
        return CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(imported, "acquire_pinned_asset", acquire)
    monkeypatch.setattr(imported.subprocess, "run", native)
    prefix = [] if warm else [("acquire", imported.ASSET_ID), ("acquire", imported.BUNDLE_ID)]
    if signature_valid:
        target = imported.provision()
        assert target.read_bytes() == binary
        assert calls[:len(prefix) + 1] == prefix + [("gh", "attestation", "verify")]
        assert {p.name: p.read_bytes() for p in cache.iterdir()} == pinned_pair
    else:
        with pytest.raises(CalledProcessError):
            imported.provision()
        assert calls == prefix + [("gh", "attestation", "verify")]
        assert cache.exists() == warm
        assert not (tmp_path / "mise/bin/mise").exists()


def test_pair_publication_failure_leaves_no_partial_pair(tmp_path, monkeypatch, pinned_pair):
    base = tmp_path / "base"
    base.mkdir()
    cache = tmp_path / "cache"
    for name, payload in pinned_pair.items():
        (base / name).write_bytes(payload)

    def interrupted(*args, **kwargs):
        raise OSError("interrupted before publication")

    monkeypatch.setattr(imported.os, "replace", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        imported.publish_signed_pair(cache, base)
    assert not cache.exists()
    assert list(tmp_path.iterdir()) == [base]
