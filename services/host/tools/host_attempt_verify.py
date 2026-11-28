"""Read-only consumer for an explicitly pinned native Host test attempt.

This proves a bounded report/receipt consistency predicate, not a signature,
Runtime terminal state, independent test adequacy, or a production release.
The native XML count is an explicit external observation, not inferred from
successful pytest subtest events.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate receipt key")
        result[key] = value
    return result


def invalid_constant(value):
    raise ValueError("nonfinite receipt number: " + value)


def positive(value) -> bool:
    return type(value) is int and value > 0


def zero(value) -> bool:
    return type(value) is int and value == 0


def verify(
    receipt_raw: bytes,
    xml_raw: bytes,
    *,
    receipt_sha: str,
    commit: str,
    host_tree: str,
    lock_digest: str,
    invocation: str,
    expected_xml_cases: int,
) -> dict:
    require(
        len(receipt_raw) <= 1024 * 1024 and len(xml_raw) <= 16 * 1024 * 1024,
        "report size exceeds consumer budget",
    )
    require(digest(receipt_raw) == receipt_sha, "receipt digest mismatch")
    r = json.loads(receipt_raw, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    require(
        isinstance(r, dict) and r.get("kind") == "ordivon.host-test-attempt.v1",
        "unsupported receipt kind",
    )
    require(
        bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit))
        and bool(re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", host_tree))
        and bool(re.fullmatch(r"sha256:[0-9a-f]{64}", lock_digest)),
        "invalid source pin",
    )
    require(bool(invocation) and r.get("invocationId") == invocation, "invocation mismatch")
    expected = {"commit": commit, "hostTree": host_tree, "lockDigest": lock_digest, "clean": True}
    for field in ("sourceBefore", "sourceAfter"):
        observed = r.get(field)
        require(
            isinstance(observed, dict) and observed.get("clean") is True and observed == expected,
            "source mismatch: " + field,
        )
    require(
        r.get("disposition") == "PASS"
        and zero(r.get("effectiveExit"))
        and zero(r.get("nativeExitAfterQualification")),
        "not a native PASS",
    )
    require(
        r.get("qualificationProblems") == [] and r.get("nonpassingNodeIds") == [],
        "nonpassing qualification evidence",
    )
    n = r.get("selectedCount")
    require(positive(n) and positive(expected_xml_cases), "invalid count")
    reports = r.get("reportOutcomes")
    require(isinstance(reports, dict), "missing report outcomes")
    required = {"setup:passed", "call:passed", "teardown:passed"}
    require(
        required <= reports.keys() <= required | {"subtest:passed"}, "nonpassing or unknown report"
    )
    require(all(positive(reports[k]) and reports[k] == n for k in required), "phase count mismatch")
    subtests = reports.get("subtest:passed", 0)
    require(zero(subtests) or positive(subtests), "invalid subtest count")
    require(n <= expected_xml_cases <= n + subtests, "XML count outside observed report bounds")
    meta = r.get("junit")
    require(
        isinstance(meta, dict)
        and positive(meta.get("bytes"))
        and meta == {"bytes": len(xml_raw), "sha256": digest(xml_raw)},
        "JUnit bytes mismatch",
    )
    # Only consume the ordinary native UTF-8 JUnit profile; never expand DTDs.
    decoded = xml_raw.decode("utf-8")
    require(not re.search(r"<!\s*(?:DOCTYPE|ENTITY)", decoded, re.I), "unsupported XML declaration")
    root = ET.fromstring(decoded)
    require(root.tag in ("testsuites", "testsuite"), "unsupported JUnit root")
    suites = [root] if root.tag == "testsuite" else list(root)
    require(
        bool(suites) and all(s.tag == "testsuite" for s in suites),
        "unsupported JUnit suite structure",
    )
    cases = [c for suite in suites for c in suite.findall("testcase")]
    require(cases == list(root.iter("testcase")), "misplaced JUnit case")
    require(len(cases) == expected_xml_cases, "JUnit count mismatch")
    require(
        not any(e.tag in ("error", "failure", "skipped") for e in root.iter()),
        "JUnit contains nonpassing result",
    )
    require(all(bool(c.get("name")) for c in cases), "unnamed JUnit case")
    for suite in suites:
        for name in ("errors", "failures", "skipped"):
            require(suite.get(name) == "0", "JUnit suite nonpassing or missing summary")
    return {
        "kind": "host-test-attempt-consumer-v1",
        "verified": True,
        "receiptSha256": receipt_sha,
        "junitSha256": meta["sha256"],
        "source": expected,
        "invocationId": invocation,
        "selectedCount": n,
        "subtestReports": subtests,
        "xmlCases": expected_xml_cases,
        "scope": "pinned native report consistency; not provider authentication or terminal proof",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipt", type=Path)
    p.add_argument("junit", type=Path)
    for name in ("receipt-sha", "commit", "host-tree", "lock-digest", "invocation"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--expected-xml-cases", type=int, required=True)
    a = p.parse_args()
    try:
        # Bounded reads even if caller supplied a much larger report.
        with a.receipt.open("rb") as stream:
            receipt = stream.read(1024 * 1024 + 1)
        with a.junit.open("rb") as stream:
            xml = stream.read(16 * 1024 * 1024 + 1)
        result = verify(
            receipt,
            xml,
            receipt_sha=a.receipt_sha,
            commit=a.commit,
            host_tree=a.host_tree,
            lock_digest=a.lock_digest,
            invocation=a.invocation,
            expected_xml_cases=a.expected_xml_cases,
        )
    except (ValueError, OSError, ET.ParseError) as exc:
        p.exit(2, f"unqualified evidence: {exc}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
