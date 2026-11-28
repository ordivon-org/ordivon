"""Opt-in native pytest attempt evidence, not a runner or CI authority."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import time
import uuid
from collections import Counter
from pathlib import Path

import pytest

HOST_ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(HOST_ROOT), *args],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    ).stdout.strip()


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return "sha256:" + hashlib.file_digest(stream, "sha256").hexdigest()


def _source() -> dict:
    repo = Path(_git("rev-parse", "--show-toplevel"))
    relative = HOST_ROOT.relative_to(repo).as_posix()
    tree = "HEAD^{tree}" if relative == "." else "HEAD:" + relative
    return {
        "commit": _git("rev-parse", "HEAD"),
        "hostTree": _git("rev-parse", tree),
        "lockDigest": _sha(HOST_ROOT / "uv.lock"),
        "clean": not _git("status", "--porcelain", "--untracked-files=normal"),
    }


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--host-evidence-dir", help="Fresh private directory for native attempt evidence."
    )


class _AttemptEvidence:
    def __init__(self, directory: Path, source: dict, provider: dict | None):
        self.directory = directory
        self.source = source
        self.provider = provider
        self.invocation = str(uuid.uuid4())
        self.started_ns = time.monotonic_ns()
        self.outcomes: Counter[str] = Counter()
        self.nonpassing_nodes: set[str] = set()

    def pytest_collectreport(self, report: pytest.CollectReport) -> None:
        if not report.passed:
            self.outcomes["collection:" + report.outcome] += 1
            self.nonpassing_nodes.add(report.nodeid)

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        kind = "subtest" if isinstance(report, pytest.SubtestReport) else report.when
        outcome = report.outcome
        if hasattr(report, "wasxfail"):
            outcome = "xpass" if report.passed else "xfail"
        self.outcomes[f"{kind}:{outcome}"] += 1
        if outcome != "passed":
            self.nonpassing_nodes.add(report.nodeid)

    @pytest.hookimpl(wrapper=True, tryfirst=True)
    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int):
        # The native JUnit writer and the complete-suite gate finish first.
        result = yield
        problems: list[str] = []
        try:
            final = _source()
            if final != self.source:
                problems.append("SOURCE_CHANGED")
        except OSError, ValueError, subprocess.SubprocessError:
            final = None
            problems.append("SOURCE_UNOBSERVABLE")
        report = self.directory / "junit.xml"
        native_xml = None
        try:
            if not report.is_file() or report.stat().st_size == 0:
                raise OSError("empty or missing native JUnit")
            report.chmod(0o600)
            native_xml = {"sha256": _sha(report), "bytes": report.stat().st_size}
        except OSError:
            problems.append("NATIVE_REPORT_UNOBSERVABLE")

        native_exit = int(session.exitstatus)
        if problems and native_exit == 0:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
        effective_exit = int(session.exitstatus)
        receipt = {
            "kind": "ordivon.host-test-attempt.v1",
            "invocationId": self.invocation,
            "providerDeclaration": self.provider,
            "sourceBefore": self.source,
            "sourceAfter": final,
            "environment": {"python": platform.python_version(), "pytest": pytest.__version__},
            "nativeExitAfterQualification": native_exit,
            "effectiveExit": effective_exit,
            "disposition": "UNQUALIFIED"
            if problems
            else ("PASS" if effective_exit == 0 else "NONPASS"),
            "qualificationProblems": problems,
            "selectedCount": len(session.items),
            "reportOutcomes": dict(sorted(self.outcomes.items())),
            "nonpassingNodeIds": sorted(self.nonpassing_nodes),
            "junit": native_xml,
            "elapsedNs": time.monotonic_ns() - self.started_ns,
        }
        # Exclusive creation in a private, newly created directory. No overwrite
        # path exists for a subsequent execution. Raw JUnit may contain tracebacks.
        path = self.directory / "receipt.json"
        try:
            with path.open("x", encoding="utf-8") as stream:
                json.dump(receipt, stream, sort_keys=True, ensure_ascii=False)
                stream.write("\n")
            path.chmod(0o600)
        except OSError:
            if effective_exit == 0:
                session.exitstatus = pytest.ExitCode.TESTS_FAILED
            raise
        return result


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    raw = config.getoption("--host-evidence-dir")
    if not raw:
        raise pytest.UsageError("HOST_ATTEMPT_EVIDENCE_DIR_REQUIRED")
    if not config.getoption("--host-require-complete-suite", default=False):
        raise pytest.UsageError("HOST_ATTEMPT_EVIDENCE_REQUIRES_COMPLETE_SUITE")
    directory = Path(raw).resolve()
    xmlpath = config.getoption("xmlpath", default=None)
    if not xmlpath or Path(xmlpath).resolve() != directory / "junit.xml":
        raise pytest.UsageError("HOST_ATTEMPT_EVIDENCE_NATIVE_JUNIT_REQUIRED")
    try:
        source = _source()
        if not source["clean"]:
            raise pytest.UsageError("HOST_ATTEMPT_EVIDENCE_DIRTY_SOURCE")
        if directory.is_relative_to(Path(_git("rev-parse", "--show-toplevel"))):
            raise pytest.UsageError("HOST_ATTEMPT_EVIDENCE_OUTSIDE_SOURCE_REQUIRED")
        provider = None
        if os.environ.get("GITHUB_ACTIONS") == "true":
            fields = (
                "GITHUB_REPOSITORY",
                "GITHUB_RUN_ID",
                "GITHUB_RUN_ATTEMPT",
                "GITHUB_JOB",
                "GITHUB_SHA",
            )
            provider = {key: os.environ.get(key) for key in fields}
            if not all(provider.values()) or provider["GITHUB_SHA"] != source["commit"]:
                raise pytest.UsageError("HOST_ATTEMPT_EVIDENCE_PROVIDER_SOURCE_MISMATCH")
        directory.mkdir(mode=0o700, exist_ok=False)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise pytest.UsageError("HOST_ATTEMPT_EVIDENCE_SOURCE_OR_DIRECTORY_INVALID") from error
    config.pluginmanager.register(
        _AttemptEvidence(directory, source, provider), "host-attempt-evidence"
    )
