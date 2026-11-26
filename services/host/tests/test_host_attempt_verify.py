"""Native producer/independent consumer tests plus rehashed negative reports."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET

import pytest
from test_host_attempt_evidence import _repo, _run

from tools.host_attempt_verify import verify


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@pytest.fixture(scope="module")
def native(tmp_path_factory):
    d = tmp_path_factory.mktemp("native-consumer")
    repo = _repo(
        d,
        "def test_probe(subtests):\n    for i in range(3):\n        with subtests.test(i=i): assert i>=0\n",
    )
    report = d / "report"
    result = _run(repo, report)
    assert result.returncode == 0, result.stdout + result.stderr
    raw = (report / "receipt.json").read_bytes()
    xml = (report / "junit.xml").read_bytes()
    r = json.loads(raw)
    # Source expectations use native Git and actual fixture lock, not receipt fields.
    import subprocess

    def git(ref):
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", ref], text=True
        ).strip()

    pins = dict(
        receipt_sha=sha(raw),
        commit=git("HEAD"),
        host_tree=git("HEAD^{tree}"),
        lock_digest=sha((repo / "uv.lock").read_bytes()),
        invocation=r["invocationId"],
        expected_xml_cases=1,
    )
    return raw, xml, pins


def test_native_consumer(native):
    raw, xml, pins = native
    result = verify(raw, xml, **pins)
    assert result["selectedCount"] == 1 and result["subtestReports"] == 3
    assert result["xmlCases"] == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("commit", "0" * 40),
        ("host_tree", "0" * 40),
        ("lock_digest", "sha256:" + "0" * 64),
        ("invocation", "wrong"),
        ("receipt_sha", "sha256:" + "0" * 64),
        ("expected_xml_cases", 2),
    ],
)
def test_external_pin_mismatch(native, field, value):
    raw, xml, pins = native
    with pytest.raises(ValueError):
        verify(raw, xml, **{**pins, field: value})


@pytest.mark.parametrize(
    "mutant",
    [
        "phase",
        "bool",
        "exit",
        "nonpass",
        "dirty",
        "duplicate",
        "xml_failure",
        "xml_empty",
        "xml_misplaced",
        "xml_doctype",
    ],
)
def test_rehashed_bad_evidence(native, mutant):
    raw, xml, pins = native
    r = json.loads(raw)
    if mutant == "phase":
        r["reportOutcomes"]["teardown:passed"] = 2
    elif mutant == "bool":
        r["selectedCount"] = True
    elif mutant == "exit":
        r["effectiveExit"] = False
    elif mutant == "nonpass":
        r["reportOutcomes"]["call:skipped"] = 1
    elif mutant == "dirty":
        r["sourceAfter"]["clean"] = False
    elif mutant == "duplicate":
        raw = raw.replace(b'"disposition":', b'"disposition":"NONPASS","disposition":', 1)
        with pytest.raises(ValueError, match="duplicate"):
            verify(raw, xml, **{**pins, "receipt_sha": sha(raw)})
        return
    elif mutant == "xml_failure":
        root = ET.fromstring(xml)
        ET.SubElement(next(root.iter("testcase")), "failure")
        xml = ET.tostring(root)
    elif mutant == "xml_empty":
        xml = b"<testsuites/>"
    elif mutant == "xml_misplaced":
        xml = b'<testsuites><testcase name="probe"/></testsuites>'
    elif mutant == "xml_doctype":
        xml = b"<!DOCTYPE testsuites>" + xml
    r["junit"] = {"bytes": len(xml), "sha256": sha(xml)}
    raw = json.dumps(r).encode()
    with pytest.raises(ValueError):
        verify(raw, xml, **{**pins, "receipt_sha": sha(raw)})


def test_native_failure_cannot_be_consumed(tmp_path):
    repo = _repo(tmp_path, "def test_probe(): assert False\n")
    report = tmp_path / "report"
    result = _run(repo, report)
    assert result.returncode == 1
    raw = (report / "receipt.json").read_bytes()
    r = json.loads(raw)
    s = r["sourceBefore"]
    with pytest.raises(ValueError, match="not a native PASS"):
        verify(
            raw,
            (report / "junit.xml").read_bytes(),
            receipt_sha=sha(raw),
            commit=s["commit"],
            host_tree=s["hostTree"],
            lock_digest=s["lockDigest"],
            invocation=r["invocationId"],
            expected_xml_cases=1,
        )
