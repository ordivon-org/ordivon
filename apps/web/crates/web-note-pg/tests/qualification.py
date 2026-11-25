"""Consume upstream discovery and JUnit, not a second test runner."""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import xml.etree.ElementTree as ET

REQUIRED = {
    "native": {
        "native_contract_and_differential",
        "pool_saturation_and_precommit_cancellation",
        "commit_ack_loss_and_postcommit_cancellation",
        "pool_reuse_clean_reset_and_reconnect",
    },
    "stateful": {"generated_native_trajectories", "known_model_counterexamples"},
    "effect": {"contract::actual_create_publish_sqlite_differential", "concurrent::native_effect_grant_and_approval_contention", "contract::native_effect_postconditions_rollback", "contract::effect_commit_ack_loss_is_observable", "model::generated_effect_authority_histories", "concurrent::native_effect_two_writer_histories", "authority::native_authority_writer_lifecycle_and_terminal_replay", "authority::native_authority_writer_faults_and_races"},
    "migration": {"actual_owner_schema_exact_import", "malformed_and_native_constraint_import_roll_back", "native_dump_restore_and_real_note_consumer", "copy_faults_rollback_exact_postconditions"},
    "concurrent": {"generated_concurrent_histories", "bounded_oracle_rejects_impossible_histories", "coherent_snapshot_under_forced_commit", "native_identity_conflicts_have_one_winner"},
}


def discover(data: dict, targets: tuple[str, ...]) -> dict[str, set[tuple[str, str]]]:
    expected = {t: set() for t in targets}
    for binary, suite in data["rust-suites"].items():
        target = suite["binary-name"]
        if suite["status"] == "listed" and not suite["testcases"]:
            continue
        if target not in expected or suite["status"] != "listed":
            raise ValueError(f"unexpected or undiscovered native binary: {binary}")
        for name, test in suite["testcases"].items():
            if test["ignored"] or test["filter-match"]["status"] != "matches":
                raise ValueError(f"native test omitted: {binary}::{name}")
            expected[target].add((binary, name))
    for target, identities in expected.items():
        if not REQUIRED[target].issubset({name for _, name in identities}):
            raise ValueError(f"missing required native obligations: {target}")
    if data["test-count"] != sum(map(len, expected.values())):
        raise ValueError("native discovery count mismatch")
    return expected


def qualify_report(path: Path, expected: set[tuple[str, str]]) -> dict:
    raw = path.read_bytes()  # missing report is failure, never previous success
    root = ET.fromstring(raw)
    actual = Counter((case.attrib["classname"], case.attrib["name"]) for case in root.findall(".//testcase"))
    if not expected or actual != Counter(expected):
        raise ValueError(f"JUnit test identity mismatch: {actual} vs {expected}")
    if root.tag != "testsuites" or not root.attrib.get("uuid"):
        raise ValueError("missing nextest run identity")
    if int(root.attrib["tests"]) != len(expected):
        raise ValueError("JUnit count mismatch")
    for suite in [root, *root.findall(".//testsuite")]:
        if any(int(suite.attrib[k]) != 0 for k in ("skipped", "errors", "failures")):
            raise ValueError("nonpassing JUnit outcome")
    if any(child.tag in {"failure", "error", "skipped", "flakyFailure", "rerunFailure", "rerunError"}
           for case in root.findall(".//testcase") for child in case):
        raise ValueError("JUnit contains a nonpassing or retried test")
    return {"runId": root.attrib["uuid"], "tests": sorted([list(x) for x in expected]),
            "reportSha256": sha256(raw).hexdigest(), "status": "PASS"}


def print_report(path: Path, expected: set[tuple[str, str]]) -> None:
    print("native qualification:", json.dumps(qualify_report(path, expected), sort_keys=True), flush=True)
