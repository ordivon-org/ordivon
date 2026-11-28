"""Qualify a focused Nextest run from native inventory and JUnit evidence.

Not a test runner. Nextest owns selection, scheduling and execution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import uuid
import xml.etree.ElementTree as ET


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def selected_tests(data):
    """Use the native list with --run-ignored all, never run ignored tests."""
    selected = set()
    ignored = set()
    for binary, suite in data["rust-suites"].items():
        if suite["binary-id"] != binary:
            raise ValueError("binary identity mismatch")
        for name, case in suite.get("testcases", {}).items():
            match = case["filter-match"]["status"]
            if match == "mismatch":
                continue
            if match != "matches" or case["kind"] != "test" or type(case["ignored"]) is not bool:
                raise ValueError("unsupported selected test metadata")
            identity = (binary, name)
            selected.add(identity)
            if case["ignored"]:
                ignored.add(identity)
    if ignored:
        raise ValueError(f"{len(ignored)} selected ignored tests; use the explicit physical-test lane")
    return selected


def qualified_report(expected, root):
    if not expected or root.tag != "testsuites":
        raise ValueError("empty selection or invalid JUnit root")
    run_id = str(uuid.UUID(root.attrib["uuid"]))
    observed = set()
    observed_binaries = set()
    expected_binaries = {binary for binary, _ in expected}
    for suite in root:
        if suite.tag != "testsuite":
            raise ValueError("unsupported JUnit root child")
        binary = suite.attrib["name"]
        if binary not in expected_binaries or binary in observed_binaries:
            raise ValueError("unexpected or duplicate JUnit binary suite")
        observed_binaries.add(binary)
        # The focused Nextest profile emits one suite per executed binary,
        # with verdicts and captured output contained in testcase elements.
        # Reject foreign suite-level nodes instead of silently dropping them.
        if any(child.tag != "testcase" for child in suite):
            raise ValueError("unsupported JUnit suite child")
        cases = list(suite)
        if not cases:
            raise ValueError("empty JUnit binary suite")
        check_counts(suite, len(cases))
        for case in cases:
            identity = (binary, case.attrib["name"])
            if case.attrib["classname"] != identity[0] or identity in observed:
                raise ValueError("duplicate or inconsistent test identity")
            if any(child.tag not in {"system-out", "system-err"} for child in case):
                raise ValueError("non-PASS test evidence")
            observed.add(identity)
    check_counts(root, len(observed))
    if expected != observed:
        raise ValueError(f"test identity mismatch: missing={len(expected - observed)} unexpected={len(observed - expected)}")
    return run_id


def check_counts(element, count):
    if int(element.attrib["tests"]) != count:
        raise ValueError("JUnit test count mismatch")
    if any(int(element.attrib[key]) != 0 for key in ("skipped", "failures", "errors")):
        raise ValueError("JUnit contains non-PASS verdicts")


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def qualify_carrier(path, expected_digest):
    actual = digest(path)
    if actual != expected_digest:
        raise ValueError("native build carrier changed")
    return actual


def main():
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--digest":
            print(digest(Path(sys.argv[2])))
            return
        if len(sys.argv) not in (2, 5):
            raise SystemExit("usage: qualify_focused_evidence.py INVENTORY [JUNIT ARCHIVE ARCHIVE_SHA256]")
        inventory = Path(sys.argv[1])
        selected = selected_tests(json.loads(inventory.read_text(encoding="utf-8"), object_pairs_hook=unique_object))
        if len(sys.argv) == 2:
            print(f"Native selected test identities: {len(selected)}")
            return
        report = Path(sys.argv[2])
        carrier = Path(sys.argv[3])
        run_id = qualified_report(selected, ET.parse(report).getroot())
        carrier_digest = qualify_carrier(carrier, sys.argv[4])
        print(json.dumps({
            "standing": "QUALIFIED_FOCUSED_PASS",
            "archiveSha256": carrier_digest,
            "archiveBytes": carrier.stat().st_size,
            "runId": run_id,
            "tests": len(selected),
            "inventorySha256": digest(inventory),
            "junitSha256": digest(report),
            "cargoLockSha256": digest(Path("Cargo.lock")),
            "nextestConfigSha256": digest(Path(".config/nextest.toml")),
        }, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as exc:
        raise SystemExit(f"Focused evidence rejected: {exc}") from exc


if __name__ == "__main__":
    main()
