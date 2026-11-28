from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "workstation/providers/single_file_materialization.py"
SPEC = importlib.util.spec_from_file_location("single_file_materialization_test", MODULE)
assert SPEC is not None and SPEC.loader is not None
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)


def test_materializer_content_addresses_bytes_and_publishes_receipt(tmp_path: Path) -> None:
    source = tmp_path / "Provider.ps1"
    source.write_bytes(b"provider-v1")
    receipt = tmp_path / "receipts/provider.json"
    materializer = M.SingleFileProviderMaterializer(
        source=source,
        root=tmp_path / "installed",
        receipt=receipt,
        materialization_kind="example.materialization",
        mismatch_error="digest mismatch",
        include_source=True,
        materialization_fields={"ownerFact": False},
        status_kind="example.status",
    )

    payload = materializer.materialize()
    digest = M.sha256_file(source)
    target = tmp_path / "installed" / digest / source.name

    assert target.read_bytes() == source.read_bytes()
    assert payload == {
        "schemaVersion": 1,
        "kind": "example.materialization",
        "sourceSha256": f"sha256:{digest}",
        "target": str(target),
        "targetSha256": f"sha256:{digest}",
        "source": str(source),
        "ownerFact": False,
    }
    assert json.loads(receipt.read_text(encoding="utf-8")) == payload
    assert materializer.status() == {
        "schemaVersion": 1,
        "kind": "example.status",
        "sourceSha256": f"sha256:{digest}",
        "target": str(target),
        "present": True,
        "matches": True,
    }


def test_materializer_rejects_conflicting_existing_target(tmp_path: Path) -> None:
    source = tmp_path / "Provider.ps1"
    source.write_bytes(b"provider-v1")
    materializer = M.SingleFileProviderMaterializer(
        source=source,
        root=tmp_path / "installed",
        receipt=tmp_path / "receipt.json",
        materialization_kind="example.materialization",
        mismatch_error="digest mismatch",
    )
    digest = M.sha256_file(source)
    target = tmp_path / "installed" / digest / source.name
    target.parent.mkdir(parents=True)
    target.write_bytes(b"other-bytes")

    with pytest.raises(RuntimeError, match="digest mismatch"):
        materializer.materialize()


def test_materializer_rejects_owner_fields_that_override_canonical_fields(tmp_path: Path) -> None:
    source = tmp_path / "Provider.ps1"
    source.write_bytes(b"provider-v1")
    materializer = M.SingleFileProviderMaterializer(
        source=source,
        root=tmp_path / "installed",
        receipt=tmp_path / "receipt.json",
        materialization_kind="example.materialization",
        mismatch_error="digest mismatch",
        materialization_fields={"target": "wrong"},
    )

    with pytest.raises(ValueError, match="canonical field"):
        materializer.materialize()


def _load_wrapper(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("name", "relative", "kind", "status_kind", "extra", "include_source"),
    (
        (
            "materialize_windows_wsl_contract",
            "workstation/providers/windows_wsl/materialize.py",
            "ordivon.workstation.windows-wsl-provider-materialization",
            "ordivon.workstation.windows-wsl-provider-status",
            {"mutationCapabilityAdvertised": False},
            True,
        ),
        (
            "materialize_authority_validation_contract",
            "workstation/providers/authority_validation/materialize.py",
            "ordivon.workstation.authority-validation-provider-materialization",
            None,
            {"issuesAuthority": False, "renewsAuthority": False},
            False,
        ),
        (
            "materialize_windows_wsl_service_contract",
            "workstation/providers/windows_wsl_service/materialize.py",
            "ordivon.workstation.windows-wsl-service-control-provider-materialization",
            None,
            {"targetNodeIds": ["linux-local"]},
            False,
        ),
    ),
)
def test_provider_entrypoints_preserve_exact_materialization_contract(
    tmp_path: Path,
    name: str,
    relative: str,
    kind: str,
    status_kind: str | None,
    extra: dict[str, object],
    include_source: bool,
) -> None:
    wrapper = _load_wrapper(name, relative)
    materializer = replace(
        wrapper.MATERIALIZER,
        root=tmp_path / name / "installed",
        receipt=tmp_path / name / "receipts/provider.json",
    )

    payload = materializer.materialize()
    digest = M.sha256_file(wrapper.SOURCE)
    target = materializer.root / digest / wrapper.SOURCE.name
    expected = {
        "schemaVersion": 1,
        "kind": kind,
        "sourceSha256": f"sha256:{digest}",
        "target": str(target),
        "targetSha256": f"sha256:{digest}",
        **extra,
    }
    if include_source:
        expected["source"] = str(wrapper.SOURCE)
    assert payload == expected

    status = materializer.status()
    expected_status = {
        "schemaVersion": 1,
        "sourceSha256": f"sha256:{digest}",
        "target": str(target),
        "present": True,
        "matches": True,
    }
    if status_kind is not None:
        expected_status["kind"] = status_kind
    assert status == expected_status
