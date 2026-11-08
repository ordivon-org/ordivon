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


def test_preverified_mise_reuses_disk_without_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"test fixture verified executable"
    monkeypatch.setenv("MISE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(imported, "BINARY_SHA256", hashlib.sha256(payload).hexdigest())
    target = tmp_path / "bin" / "mise"
    target.parent.mkdir()
    target.write_bytes(payload)

    def unexpected_network(*_args: object, **_kwargs: object) -> None:
        pytest.fail("preverified binary must not invoke network")

    monkeypatch.setattr(imported.subprocess, "run", unexpected_network)
    assert imported.provision() == target


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

def test_github_ci_preserves_native_mise_with_bounded_download_retries() -> None:
    workflow = (Path(__file__).parents[3] / ".github/workflows/ci.yml").read_text()
    assert workflow.count("MISE_JOBS=2 MISE_HTTP_TIMEOUT=30 mise install") == 3
    assert workflow.count("NETWORK_UPSTREAM_TOOL_DOWNLOAD_UNAVAILABLE") == 3
    assert workflow.count("for attempt in 1 2 3; do") >= 3
