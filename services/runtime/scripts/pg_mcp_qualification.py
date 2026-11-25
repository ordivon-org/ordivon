#!/usr/bin/env python3
"""Qualify the existing native MCP binary with upstream Nextest evidence."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET

from pg_disposable_physical import ROOT, cargo_environment

PACKAGE = "ordivon-runtime-mcp"
BINARY = "pg_vertical"
# Required distinct consumer obligations; remaining inventory is native.
REQUIRED = frozenset({
    "fresh_pg_mcp_native_runner_success_and_cancel",
    "pg_binary_artifact_representation_is_not_registry_failure",
    "fresh_pg_mcp_real_database_and_no_false_launch_success",
    "fresh_pg_mcp_run_rejects_workspace_closed_after_source_plan_before_admit",
    "fresh_pg_revoked_writer_refuses_new_workspace_effects",
    "pg_runtime_refuses_privileged_session_hidden_behind_app_role",
    "pg_release_effect_atomic_admission_and_generic_dispatch_fence",
    "resource_queue_shared_workspace_restart_and_native_write_leases",
})
SELECTION = (
    "--locked", "-p", PACKAGE, "--features", "postgres-runtime",
    "--test", BINARY, "--run-ignored", "all", "--ignore-default-filter",
)


def inventory(raw: bytes) -> tuple[str, frozenset[str]]:
    doc = json.loads(raw)
    suites = doc["rust-suites"]
    if len(suites) != 1:
        raise ValueError("expected exactly one native MCP test binary")
    binary_id, suite = next(iter(suites.items()))
    if (binary_id != f"{PACKAGE}::{BINARY}" or suite["package-name"] != PACKAGE or suite["binary-name"] != BINARY
        or suite["binary-id"] != binary_id or suite["status"] != "listed"):
        raise ValueError("unexpected or unavailable native test binary")
    tests = suite["testcases"]
    names = frozenset(tests)
    if not REQUIRED <= names or doc["test-count"] != len(names):
        raise ValueError("required native witness absent or incomplete inventory")
    if any(t.get("kind") != "test" or t["filter-match"]["status"] != "matches" for t in tests.values()):
        raise ValueError("native consumer test deselected")
    return binary_id, names


def exact_passes(raw: bytes, binary_id: str, expected: frozenset[str]) -> int:
    report = ET.fromstring(raw)
    suites = report.findall("testsuite")
    if report.tag != "testsuites" or len(suites) != 1:
        raise ValueError("missing or unexpected native JUnit suite")
    suite = suites[0]
    if suite.get("name") != binary_id or not expected:
        raise ValueError("JUnit binary identity mismatch")
    for node in (report, suite):
        if (node.get("tests") != str(len(expected))
            or node.get("failures") != "0" or node.get("errors") != "0"
            or node.get("skipped", "0") != "0" or node.get("disabled", "0") != "0"):
            raise ValueError("JUnit aggregate not fully successful")
    cases = suite.findall("testcase")
    names = [c.get("name") for c in cases]
    if len(names) != len(expected) or frozenset(names) != expected:
        raise ValueError("JUnit missing, duplicate or unexpected test identity")
    for case in cases:
        if case.get("classname") != binary_id or any(
            node.tag not in {"system-out", "system-err"} for node in case
        ):
            raise ValueError("JUnit non-PASS, retried or foreign test")
    return len(cases)


def consumer_environment(original: dict[str, str]) -> dict[str, str]:
    env = cargo_environment(original)
    for name in list(env):
        if name.startswith(("PG", "NEXTEST_")) or name in {
            "ORDIVON_PG_TEST_DSN", "ORDIVON_PG_STAGE_TEST_DSN",
        }:
            env.pop(name)
    return env


def main() -> int:
    if sys.platform != "linux":
        raise RuntimeError("native MCP qualification requires Linux/systemd")
    env = consumer_environment(os.environ)
    required = tomllib.loads((ROOT / "mise.toml").read_text())["tools"]["http:cargo-nextest"]["version"]
    version = subprocess.check_output(["cargo", "nextest", "--version"], cwd=ROOT, env=env, text=True).splitlines()[0]
    if version.split()[:2] != ["cargo-nextest", required]:
        raise RuntimeError(f"Nextest identity drift: expected {required}, observed {version}")
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    print(f"sourceCut={source} standing={'DIRTY_UNQUALIFIED' if dirty else 'CLEAN'}", flush=True)
    if dirty:
        raise RuntimeError("strict native qualification requires a clean source cut")
    print(f"NEXTEST_TOOL={version}", flush=True)
    print(f"CARGO_LOCK_SHA256={hashlib.sha256((ROOT / 'Cargo.lock').read_bytes()).hexdigest()}", flush=True)
    destination = env.get("RUNTIME_NATIVE_MCP_EVIDENCE_DIR")
    evidence = Path(destination) if destination else None
    if evidence is not None:
        if not evidence.is_absolute():
            raise ValueError("evidence directory must be an explicit absolute new path")
        repo = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip()).resolve()
        if evidence.resolve().is_relative_to(repo):
            raise ValueError("evidence directory must be outside the source checkout")
        evidence.mkdir(mode=0o700, exist_ok=False)
    subprocess.run([
        "cargo", "build", "--locked", "-p", "ordivon-runtime-core",
        "--no-default-features", "--features", "runtime-contract",
        "--bin", "ordivon-runtime-runner",
    ], cwd=ROOT, env=env, check=True, timeout=400)
    with tempfile.TemporaryDirectory(prefix="ordivon-mcp-nextest-", dir="/var/tmp") as temp:
        base = Path(temp)
        config = base / "nextest.toml"
        # Private native report store, never reuse a shared old report.
        config.write_text(
            (ROOT / ".config/nextest.toml").read_text()
            + '\n[store]\ndir = ' + json.dumps(str(base / "store"))
            + '\n[profile.native-mcp.junit]\npath = "junit.xml"\nreport-skipped = "none"\n',
            encoding="utf-8",
        )
        common = ["--config-file", str(config), "--user-config-file", "none"]
        listed = subprocess.check_output(
            ["cargo", "nextest", "list", *common, *SELECTION,
             "--profile", "native-mcp", "--message-format", "json"],
            cwd=ROOT, env=env, timeout=400,
        )
        if evidence is not None:
            (evidence / "inventory.json").write_bytes(listed)
        binary_id, names = inventory(listed)
        print(f"NATIVE_MCP_DISCOVERED={len(names)}", flush=True)
        print(f"NATIVE_MCP_INVENTORY_SHA256={hashlib.sha256(listed).hexdigest()}", flush=True)
        print("NATIVE_MCP_SELECTED_TESTS=" + json.dumps(sorted(names)), flush=True)
        result = subprocess.run(
            ["cargo", "nextest", "run", *common, *SELECTION,
             "--profile", "native-mcp", "--no-tests", "fail", "--retries", "0",
             "--flaky-result", "fail", "--test-threads", "1", "--no-fail-fast"],
            cwd=ROOT, env=env, timeout=1800,
        )
        report = base / "store/native-mcp/junit.xml"
        if not report.is_file():
            raise RuntimeError("native JUnit report absent")
        raw = report.read_bytes()
        if evidence is not None:
            (evidence / "junit.xml").write_bytes(raw)
        print(f"NATIVE_MCP_JUNIT_SHA256={hashlib.sha256(raw).hexdigest()}", flush=True)
        cases = ET.fromstring(raw).findall("./testsuite/testcase")
        observed = {}
        for case in cases:
            name = case.get("name")
            tags = {child.tag for child in case} - {"system-out", "system-err"}
            status = "PASS" if not tags else "NONPASS:" + ",".join(sorted(tags))
            observed.setdefault(name, []).append(status)
        for name in sorted(names):
            print("NATIVE_MCP_CASE=" + json.dumps([name, observed.get(name, ["NOT_RUN"])]), flush=True)
        if result.returncode:
            return result.returncode
        count = exact_passes(raw, binary_id, names)
        if (subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != source
            or subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True) != dirty):
            raise RuntimeError("source standing changed during native qualification")
        print(f"NATIVE_MCP_PASS={count}/{count}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, RuntimeError, subprocess.SubprocessError, ET.ParseError) as exc:
        print(f"NATIVE_MCP_UNQUALIFIED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
