"""Native child processes, not manufactured JUnit or exit codes."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HOST = Path(__file__).resolve().parents[1]


def _repo(tmp_path: Path, source: str) -> Path:
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "tests").mkdir()
    shutil.copy2(HOST / "tools/host_attempt_evidence.py", repo / "tools")
    shutil.copy2(HOST / "tests/conftest.py", repo / "tests")
    (repo / "tests/test_probe.py").write_text(source, encoding="utf-8")
    (repo / "uv.lock").write_text("fixture lock\n", encoding="utf-8")
    (repo / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
    for args in (
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "user.name=Probe",
            "-c",
            "user.email=probe@local.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
    ):
        subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=10)
    return repo


def _run(repo: Path, directory: Path, *, fail=False, extras=(), provider=None):
    env = dict(os.environ)
    for key in (
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "GITHUB_ACTIONS",
        "ORDIVON_HOST_QUEUE_EVIDENCE_DIR",
    ):
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PROBE_FAIL"] = "1" if fail else "0"
    if provider:
        env.update(provider)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "tools.host_attempt_evidence",
            "--host-require-complete-suite",
            "--host-evidence-dir",
            str(directory),
            "--junitxml",
            str(directory / "junit.xml"),
            *extras,
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _receipt(directory: Path):
    receipt = json.loads((directory / "receipt.json").read_bytes())
    xml = (directory / "junit.xml").read_bytes()
    assert receipt["junit"] == {
        "sha256": "sha256:" + hashlib.sha256(xml).hexdigest(),
        "bytes": len(xml),
    }
    return receipt


def test_native_failure_then_independent_pass_preserves_first_attempt(tmp_path):
    repo = _repo(tmp_path, "import os\ndef test_probe(): assert os.environ['PROBE_FAIL']=='0'\n")
    first, second = tmp_path / "first", tmp_path / "second"
    a = _run(repo, first, fail=True)
    assert a.returncode == 1, a.stdout + a.stderr
    old = {p.name: p.read_bytes() for p in first.iterdir()}
    r1 = _receipt(first)
    assert r1["effectiveExit"] == 1 and r1["disposition"] == "NONPASS"
    assert r1["reportOutcomes"]["call:failed"] == 1
    assert r1["nonpassingNodeIds"] == ["tests/test_probe.py::test_probe"]
    b = _run(repo, second)
    assert b.returncode == 0, b.stdout + b.stderr
    r2 = _receipt(second)
    assert r2["effectiveExit"] == 0 and r2["disposition"] == "PASS"
    assert r1["invocationId"] != r2["invocationId"]
    assert r1["sourceBefore"] == r2["sourceBefore"] == r2["sourceAfter"]
    assert {p.name: p.read_bytes() for p in first.iterdir()} == old
    stale = _run(repo, first)
    assert stale.returncode != 0
    assert {p.name: p.read_bytes() for p in first.iterdir()} == old


def test_native_gate_failure_not_overridden_by_junit(tmp_path):
    repo = _repo(tmp_path, "import pytest\ndef test_probe(): pytest.skip('unavailable')\n")
    dest = tmp_path / "skip"
    result = _run(repo, dest)
    assert result.returncode == 1, result.stdout + result.stderr
    receipt = _receipt(dest)
    assert receipt["disposition"] == "NONPASS" and receipt["effectiveExit"] == 1
    assert receipt["reportOutcomes"]["call:skipped"] == 1


def test_source_changed_during_test_never_qualifies(tmp_path):
    repo = _repo(
        tmp_path,
        "from pathlib import Path\ndef test_probe(): Path('uv.lock').write_text('changed')\n",
    )
    dest = tmp_path / "drift"
    result = _run(repo, dest)
    assert result.returncode == 1, result.stdout + result.stderr
    receipt = _receipt(dest)
    assert receipt["nativeExitAfterQualification"] == 0
    assert receipt["effectiveExit"] == 1
    assert receipt["disposition"] == "UNQUALIFIED"
    assert receipt["qualificationProblems"] == ["SOURCE_CHANGED"]


def test_native_subtests_remain_separate_evidence(tmp_path):
    repo = _repo(
        tmp_path,
        "def test_probe(subtests):\n    for i in range(2):\n        with subtests.test(i=i): assert i>=0\n",
    )
    dest = tmp_path / "subtests"
    result = _run(repo, dest)
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = _receipt(dest)
    assert receipt["selectedCount"] == 1
    assert receipt["reportOutcomes"]["subtest:passed"] == 2
    assert receipt["reportOutcomes"]["call:passed"] == 1


@pytest.mark.parametrize("mode", ["dirty", "provider"])
def test_unqualified_source_rejected_before_output(tmp_path, mode):
    repo = _repo(tmp_path, "def test_probe(): pass\n")
    dest = tmp_path / "rejected"
    provider = None
    if mode == "dirty":
        (repo / "uv.lock").write_text("dirty")
    else:
        provider = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "example/example",
            "GITHUB_RUN_ID": "123",
            "GITHUB_RUN_ATTEMPT": "2",
            "GITHUB_JOB": "host",
            "GITHUB_SHA": "0" * 40,
        }
    result = _run(repo, dest, provider=provider)
    assert result.returncode != 0, result.stdout + result.stderr
    assert not dest.exists()
