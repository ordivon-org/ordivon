"""An explicit browser selection is part of a new verify operation's receipt."""

import json
from pathlib import Path

import pytest

from artifact_operations.contract import operation_envelope
from artifact_operations.executor import ArtifactOperationExecutor
from artifact_operations.providers import DirectPythonOperationProvider
from artifact_operations.receipt import operation_file_fact

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "artifact-delivery/examples/web-r1.json"


def operation(path, selection=None, profile=PROFILE):
    options = {} if selection is None else {"webProvider": selection}
    return operation_envelope(
        "r16-verify",
        "verify",
        {"profile": operation_file_fact(profile), "artifact": operation_file_fact(path)},
        options,
    )


def test_explicit_provider_is_not_a_receipt_alias(tmp_path, monkeypatch):
    subject = tmp_path / "fixture.html"
    subject.write_text("<h1>test</h1>")
    provider = DirectPythonOperationProvider()
    executions = []

    def produce(kind, context, output):
        executions.append(context)
        (output / "native.json").write_text(json.dumps({"kind": kind}))
        return {"verifyReport": "native.json"}, {}

    monkeypatch.setattr(provider, "produce", produce)
    executor = ArtifactOperationExecutor(tmp_path / "state", provider=provider)
    first = executor.execute(operation(subject, "host"))
    assert not first["replayed"]
    with pytest.raises(RuntimeError, match="different immutable inputs"):
        executor.execute(operation(subject, "oci"))
    assert len(executions) == 1


def test_legacy_verify_intent_does_not_inherit_new_ambient_provider(tmp_path, monkeypatch):
    subject = tmp_path / "fixture.html"
    subject.write_text("<h1>test</h1>")
    monkeypatch.setenv("ARTIFACT_WEB_PROVIDER", "oci")
    value = DirectPythonOperationProvider().prepare_operation(operation(subject))
    assert set(value.immutable_inputs) == {"profile", "artifact"}
    assert value.context["webProviderRecipe"] == {"selection": "host"}


def test_explicit_source_recipe_change_cannot_replay(tmp_path, monkeypatch):
    from artifact_verifiers.web import oci

    subject = tmp_path / "fixture.html"
    subject.write_text("<h1>test</h1>")
    lock = tmp_path / "lock.json"
    lock.write_bytes(oci.LOCK.read_bytes())
    monkeypatch.setattr(oci, "LOCK", lock)
    provider = DirectPythonOperationProvider()

    def produce(kind, context, output):
        (output / "native.json").write_text(json.dumps(context["webProviderRecipe"]))
        return {"verifyReport": "native.json"}, {}

    monkeypatch.setattr(provider, "produce", produce)
    executor = ArtifactOperationExecutor(tmp_path / "state", provider=provider)
    first = executor.execute(operation(subject, "oci"))
    assert not first["replayed"]
    lock.write_bytes(lock.read_bytes() + b" ")
    with pytest.raises(RuntimeError, match="different immutable inputs"):
        executor.execute(operation(subject, "oci"))


@pytest.mark.integration
def test_runtime_owned_explicit_oci_verify_consumes_exact_receipt(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACT_WEB_PROVIDER", "host")
    subject = tmp_path / "page.html"
    subject.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Test</title></head>'
        "<body><main><h1>Test</h1></main></body></html>"
    )
    executor = ArtifactOperationExecutor(
        tmp_path / "state", provider=DirectPythonOperationProvider()
    )
    intent = operation(subject, "oci")
    first = executor.execute(intent)
    assert not first["replayed"]
    assert first["metadata"]["profileVerificationComplete"] is False
    assert {"target", "accessibility"} <= set(first["metadata"]["gateVsas"])
    raw = json.loads(Path(first["roles"]["rawEvidence:target"]["path"]).read_bytes())
    native = raw["browserEvidence"]
    recipe = first["inputs"]["webProviderRecipe"]
    assert native["provider"]["kind"] == "podman-oci"
    assert native["methodBound"] is True and native["digestBound"] is True
    for key in ("lockSha256", "runnerSha256", "nodeMetadataSha256"):
        assert native["provider"][key] == recipe[key]
    second = executor.execute(intent)
    assert second["replayed"] and first["roles"] == second["roles"]
    with pytest.raises(RuntimeError, match="different immutable inputs"):
        executor.execute(operation(subject, "host"))
    print(
        "RUNTIME_NATIVE_OCI_RECEIPT",
        json.dumps(
            {
                "recipe": recipe,
                "roles": first["roles"],
                "metadata": first["metadata"],
                "replayed": second["replayed"],
            },
            sort_keys=True,
        ),
    )
