"""Generation reuse and pointer safety, independent of Nix installation."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import artifact_openxml_environment as m


def candidate(base):
    lock = m.load_lock()
    spec = {
        "schemaVersion": 1,
        "methodId": lock["methodId"],
        "dotnetNixStorePath": "/nix/store/fixture",
        "observedDotnetSdk": "10.0.404",
    }
    gid = hashlib.sha256(m.canonical(spec)).hexdigest()
    gen = base / "generations" / gid
    gen.mkdir(parents=True)
    binding = {**spec, "kind": "artifact-openxml-generation-binding", "generationId": gid}
    (gen / "binding.json").write_text(json.dumps(binding))
    return lock, spec, gid, gen, binding


def test_reuse_cannot_relabel_recipe(tmp_path):
    lock, spec, gid, gen, binding = candidate(tmp_path)
    binding["methodId"] = "wrong"
    (gen / "binding.json").write_text(json.dumps(binding))
    with (
        patch.object(m, "generation_spec", return_value=spec),
        pytest.raises(RuntimeError, match="binding"),
    ):
        m.build_generation(tmp_path, lock, {}, [])


def test_status_rejects_non_generation_namespace(tmp_path):
    gen = tmp_path / "other"
    gen.mkdir()
    (gen / "binding.json").write_text(
        json.dumps({"dotnetNixStorePath": "/nix/store/fixture", "observedDotnetSdk": "10.0.404"})
    )
    (tmp_path / "current").symlink_to(gen)
    with (
        patch.object(m, "gc_root_registered", return_value=True),
        patch.object(
            m, "run", return_value=type("P", (), {"returncode": 0, "stdout": "10.0.404"})()
        ),
    ):
        assert not m.status(tmp_path)["ready"]


def test_failed_publication_restores_previous_link(tmp_path):
    lock, spec, gid, gen, binding = candidate(tmp_path)
    lock["stableRoot"] = str(tmp_path)
    old = gen.parent / "old"
    old.mkdir()
    current = tmp_path / "current"
    current.symlink_to(Path("generations/old"))
    with (
        patch.object(m, "MAIN", m.ROOT),
        patch.object(m, "load_lock", return_value=lock),
        patch.object(m, "nuget_sources", return_value=[]),
        patch.object(
            m, "nix_dotnet_status", return_value={"storePath": spec["dotnetNixStorePath"]}
        ),
        patch.object(m, "generation_spec", return_value=spec),
        patch.object(m, "build_generation", return_value=(gid, gen, binding)),
        patch.object(m, "verify_external_evidence", return_value={}),
        patch.object(m, "register_generation_gc_root"),
        patch.object(m, "qualify_materialization", return_value=binding),
        patch.object(m, "status", return_value={"ready": False}),
    ):
        with pytest.raises(RuntimeError):
            m.apply()
    assert current.readlink() == Path("generations/old")


def test_recipe_and_materialization_are_independent(tmp_path):
    import shutil

    lock = m.load_lock()
    source = m.nix_source_cut(m.NIX_FLAKE / "flake.lock")
    dotnet = {
        "storePath": "/nix/store/fixture",
        "narHash": "sha256-fixture",
        "observedSdkVersion": lock["nixDotnet"]["expectedSdkVersion"],
        **source,
    }
    spec = m.generation_spec(lock, dotnet, [])
    gid = hashlib.sha256(m.canonical(spec)).hexdigest()
    gen = tmp_path / "generations" / gid
    for name in ("bin", "validator", "source", "provenance"):
        (gen / name).mkdir(parents=True)
    for src, dst in (
        (m.DOTNET_WRAPPER, "bin/dotnet"),
        (m.VALIDATOR_WRAPPER, "bin/validate-openxml"),
        (m.ROOT / lock["sourceProject"], "source/ArtifactOpenXmlValidator.csproj"),
        (m.ROOT / lock["sourceProgram"], "source/Program.cs"),
        (m.NIX_FLAKE / "flake.lock", "provenance/openxml-nix-flake.lock"),
    ):
        shutil.copyfile(src, gen / dst)
    output = gen / "validator" / "fixture.dll"
    output.write_bytes(b"first")
    binding = {
        **spec,
        "kind": "artifact-openxml-generation-binding",
        "generationId": gid,
        "validatorTreeDigest": m.tree_digest(gen / "validator"),
    }
    (gen / "binding.json").write_text(json.dumps(binding))
    assert m.qualify_materialization(tmp_path, gen, spec) == binding
    output.write_bytes(b"second")
    with pytest.raises(RuntimeError, match="materialization tree drift"):
        m.qualify_materialization(tmp_path, gen, spec)
    binding["validatorTreeDigest"] = m.tree_digest(gen / "validator")
    (gen / "binding.json").write_text(json.dumps(binding))
    assert m.qualify_materialization(tmp_path, gen, spec) == binding
    (gen / "source" / "Program.cs").write_bytes(b"drift")
    with pytest.raises(RuntimeError, match="provenance mismatch"):
        m.qualify_materialization(tmp_path, gen, spec)
