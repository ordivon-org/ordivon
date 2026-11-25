"""Consumer-facing browser carrier behavior."""

import json
import subprocess
from pathlib import Path

import pytest

from artifact_verifiers.web.browser import verify_web_local


def test_explicit_unknown_provider_never_falls_back(tmp_path, monkeypatch):
    path = tmp_path / "page.html"
    path.write_text("<h1>witness</h1>")
    monkeypatch.setenv("ARTIFACT_WEB_PROVIDER", "unqualified")
    result = verify_web_local(path)
    assert result["status"] == "NOT_RUN"
    assert result.get("digestBound") is not True


@pytest.mark.integration
def test_native_oci_positive_and_negative(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACT_WEB_PROVIDER", "oci")
    profile = json.loads(
        (Path(__file__).resolve().parents[1] / "artifact-delivery/examples/web-r1.json").read_text()
    )
    from artifact_verifiers.web.policy import assess_browser_report

    for negative in (False, True):
        path = tmp_path / f"page-{negative}.html"
        extra = (
            '<button></button><img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">'
            if negative
            else ""
        )
        path.write_text(
            f'<!doctype html><html lang="en"><head><title>Test</title></head><body><main><h1>Test</h1>{extra}</main></body></html>'
        )
        result = verify_web_local(path)
        assert result["provider"]["kind"] == "podman-oci"
        assert result["digestBound"] is True
        value = assess_browser_report(result, profile, result["artifact"]["digest"]["sha256"])
        assert value["target"] == "PASS", result
        assert value["accessibility"] == ("FAIL" if negative else "PASS"), result


@pytest.mark.parametrize("case", ["duplicate", "method", "missing_engine_version", "axe_count"])
def test_oci_report_cannot_promote_ambiguous_observation(tmp_path, monkeypatch, case):
    from artifact_core.contracts import file_fact
    from artifact_verifiers.web import browser
    from artifact_verifiers.web.policy import assess_browser_report

    path = tmp_path / "subject.html"
    path.write_text("<h1>witness</h1>")
    sha = file_fact(path)["digest"]["sha256"]
    methods = {"playwright": "1.64.1", "axePlaywright": "4.14.0"}
    provider = {"kind": "podman-oci", "expectedTooling": methods, "inputSnapshotSha256": sha}
    value = {
        "schemaVersion": 1,
        "kind": "artifact-web-local-verification-evidence",
        "status": "PASS",
        "subject": {"sha256": sha},
        "tooling": methods.copy(),
        "browsers": {
            key: {
                "name": name,
                "status": "PASS",
                "version": "1",
                "executable": "/browser",
                "title": "test",
                "headingCount": 1,
            }
            for key, name in (
                ("chromium", "Chromium"),
                ("firefox", "Firefox"),
                ("webkit", "WebKit"),
            )
        },
    }
    value["browsers"]["chromium"]["accessibility"] = {
        "status": "PASS",
        "violationCount": 0,
        "violations": [],
    }
    if case == "method":
        value["tooling"]["playwright"] = "0"
    elif case == "missing_engine_version":
        value["browsers"]["firefox"].pop("version")
    elif case == "axe_count":
        value["browsers"]["chromium"]["accessibility"]["violations"] = [{"id": "button-name"}]
    raw = json.dumps(value)
    if case == "duplicate":
        raw = '{"status":"FAIL",' + raw[1:]
    monkeypatch.setenv("ARTIFACT_WEB_PROVIDER", "oci")
    monkeypatch.setattr(
        browser,
        "run_oci_browser",
        lambda *_: (subprocess.CompletedProcess([], 0, raw, ""), provider),
    )
    report = browser.verify_web_local(path)
    profile = json.loads(
        (Path(__file__).resolve().parents[1] / "artifact-delivery/examples/web-r1.json").read_text()
    )
    standing = assess_browser_report(report, profile, sha)
    if case == "axe_count":
        assert standing["target"] == "PASS" and standing["accessibility"] == "UNKNOWN"
    else:
        assert standing["target"] == "UNKNOWN"
    if case == "method":
        assert report["digestBound"] is True
        assert report["methodBound"] is False


@pytest.mark.parametrize("case", ["lock_image", "metadata", "transport", "subject_drift"])
def test_oci_admission_rejects_before_browser_run(tmp_path, monkeypatch, case):
    import shutil

    from artifact_core.contracts import file_fact
    from artifact_verifiers.web import oci

    source = tmp_path / "source"
    source.mkdir()
    installed = tmp_path / "toolchain/node/1.64.1"
    installed.mkdir(parents=True)
    for name in oci.METADATA:
        shutil.copyfile(oci.NODE_SOURCE / name, source / name)
        shutil.copyfile(source / name, installed / name)
    lock = tmp_path / "lock.json"
    value = json.loads(oci.LOCK.read_text())
    if case == "lock_image":
        value["imageId"] = "mutable-tag"
    lock.write_text(json.dumps(value))
    monkeypatch.setattr(oci, "LOCK", lock)
    monkeypatch.setattr(oci, "NODE_SOURCE", source)
    monkeypatch.setattr(oci, "GLOBAL_ARTIFACT_TOOLCHAIN_ROOT", tmp_path / "toolchain")
    monkeypatch.setattr(oci.shutil, "which", lambda _: "/usr/bin/podman")
    if case == "metadata":
        (installed / "pnpm-lock.yaml").write_bytes(b"wrong")
    subject = tmp_path / "page.html"
    subject.write_text("witness")
    artifact = file_fact(subject)
    if case == "subject_drift":
        subject.write_text("changed")
    calls = []

    def run(argv, **kwargs):
        calls.append(argv[1:3])
        assert argv[1:3] == ["image", "inspect"], "native browser cannot run"
        output = (
            "wrong image"
            if case == "transport"
            else f"{value['imageId']} {value['manifestDigest']}"
        )
        return subprocess.CompletedProcess(argv, 0, output, "")

    monkeypatch.setattr(oci.subprocess, "run", run)
    with pytest.raises((ValueError, RuntimeError)):
        oci.run_oci_browser(artifact, oci.ROOT / "artifact_verifiers/web/node/verify_html.mjs")
    assert len(calls) == (1 if case in ("transport", "subject_drift") else 0)


@pytest.mark.integration
def test_native_oci_stage_keeps_gate_and_delivery_standing_separate(tmp_path, monkeypatch):
    from artifact_operations.providers import DirectPythonOperationProvider

    monkeypatch.setenv("ARTIFACT_WEB_PROVIDER", "oci")
    profile = Path(__file__).resolve().parents[1] / "artifact-delivery/examples/web-r1.json"
    subject = tmp_path / "page.html"
    subject.write_text(
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Test</title></head><body><main><h1>Test</h1></main></body></html>'
    )
    evidence = tmp_path / "evidence"
    report = DirectPythonOperationProvider().execute_verify_stage(profile, subject, evidence)
    for gate in ("target", "accessibility"):
        assert report["receipts"][gate]["status"] == "PASS", report
        assert (evidence / f"{gate}.vsa.json").is_file()
        raw = json.loads((evidence / f"{gate}.raw.json").read_text())
        assert raw["browserEvidence"]["provider"]["kind"] == "podman-oci"
        assert raw["browserEvidence"]["methodBound"] is True
    assert report["profileVerificationComplete"] is False
    assert report["standingCoverage"]["verificationStatus"] == "UNKNOWN"
