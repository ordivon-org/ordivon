"""Web verifier consumer contracts, independent of implementation file layout."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from artifact_core.contracts import file_fact
from artifact_operations.providers import direct_python
from artifact_verifiers import web


@pytest.mark.parametrize("gate", ["conformance", "browser"])
def test_provider_delegates_web_observation_to_selected_capability(tmp_path, gate):
    subject = tmp_path / "page.html"
    subject.write_text("<!doctype html><html lang='en'><title>Example</title><h1>Example</h1>")
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"id": "test-web"}))
    provider = direct_python.DirectPythonOperationProvider()
    received = []

    def observation(path):
        received.append(path)
        return {"status": "NOT_RUN", "artifact": file_fact(path), "error": "fixture unavailability"}

    name = "verify_html_conformance" if gate == "conformance" else "verify_web_local"
    with patch.object(direct_python, name, observation):
        hooks = provider._verification_stage_hooks()
        value = getattr(hooks, name)(subject)
    assert received == [subject]
    assert value["artifact"] == file_fact(subject)
    assert value["status"] == "NOT_RUN"


@pytest.mark.parametrize("name", ["verify_html_conformance", "verify_web_local"])
def test_public_web_capability_preserves_identity_when_tool_unavailable(
    tmp_path, name, monkeypatch
):
    subject = tmp_path / "page.html"
    subject.write_bytes(b"<h1>identity</h1>")
    if name == "verify_html_conformance":
        monkeypatch.setattr("artifact_verifiers.web.conformance.vnu_jar", lambda: None)
    else:
        monkeypatch.setattr("artifact_verifiers.web.browser.node_executable", lambda: None)
    value = getattr(web, name)(subject)
    assert value["status"] == "NOT_RUN"
    assert value["artifact"] == file_fact(subject)
    assert value["error"]


@pytest.mark.parametrize("payload", ["[]", "{}", '{"messages":null}', '{"messages":{}}'])
def test_malformed_native_conformance_is_not_a_valid_positive(tmp_path, monkeypatch, payload):
    import subprocess

    subject = tmp_path / "page.html"
    subject.write_bytes(b"<h1>identity</h1>")
    jar = tmp_path / "checker.jar"
    jar.write_bytes(b"fixture")
    monkeypatch.setattr("artifact_verifiers.web.conformance.vnu_jar", lambda: jar)
    monkeypatch.setattr("artifact_verifiers.web.conformance.java_executable", lambda: jar)
    monkeypatch.setattr(
        "artifact_verifiers.web.conformance.subprocess.run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 0, payload, ""),
    )
    report = web.verify_html_conformance(subject)
    assert report["status"] == "NOT_RUN"
    assert report["parseError"]
    assert report["artifact"] == file_fact(subject)


@pytest.mark.parametrize(
    "messages,code,expected", [([], 0, "PASS"), ([{"type": "error"}], 1, "FAIL")]
)
def test_native_conformance_decisive_report_controls(
    tmp_path, monkeypatch, messages, code, expected
):
    import subprocess

    subject = tmp_path / "page.html"
    subject.write_bytes(b"<h1>identity</h1>")
    jar = tmp_path / "checker.jar"
    jar.write_bytes(b"fixture")
    monkeypatch.setattr("artifact_verifiers.web.conformance.vnu_jar", lambda: jar)
    monkeypatch.setattr("artifact_verifiers.web.conformance.java_executable", lambda: jar)
    monkeypatch.setattr(
        "artifact_verifiers.web.conformance.subprocess.run",
        lambda *a, **kw: subprocess.CompletedProcess(
            a, code, json.dumps({"messages": messages}), ""
        ),
    )
    report = web.verify_html_conformance(subject)
    assert report["status"] == expected
    assert report["messageCount"] == len(messages)
    assert report["parseError"] is None
