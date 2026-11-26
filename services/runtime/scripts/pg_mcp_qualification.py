#!/usr/bin/env python3
"""Qualify the existing native MCP binary with upstream Nextest evidence."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET

from pg_disposable_physical import ROOT, cargo_environment
from qualify_focused_evidence import qualified_report, unique_object

PACKAGE = "ordivon-runtime-mcp"
BINARY = "pg_vertical"
FIXTURE_SCOPE_ENV = "ORDIVON_NATIVE_MCP_FIXTURE_ROOT"
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
    "terminal_observation::tests::same_identity_pending_then_failed_is_not_resubmission",
    "terminal_observation::tests::reject_foreign_attempt_job_operation_and_false_terminal",
    "terminal_observation::tests::no_unqualified_error_observation_or_vacuous_timeout",
    "fixture_lifecycle::tests::exact_absence_is_not_failed_or_inactive_unit",
    "fixture_lifecycle::tests::exact_fixture_binding_rejects_foreign_or_traversal",
    "native_pg_fixture_panic_preserves_root_after_owned_postmaster_stop",
    "native_pg_fixture_refuses_failed_registered_unit_until_native_absence",
    "pg18_original_harness_issued_dedicated_mcp_admit_then_revoke_before_dispatch",
    "pg18_original_harness_terminal_cut_joins_observed_and_unsubmitted_keys",
})
SELECTION = (
    "--locked", "-p", PACKAGE, "--no-default-features", "--features", "postgres-runtime",
    "--test", BINARY, "--run-ignored", "all", "--ignore-default-filter",
)

RUNNER_BUILD_ARGS = (
    "build", "--locked", "-p", "ordivon-runtime-core",
    "--no-default-features", "--features", "postgres-registry-admission",
    "--bin", "ordivon-runtime-runner",
)


def inventory(raw: bytes) -> tuple[str, frozenset[str]]:
    doc = json.loads(raw, object_pairs_hook=unique_object)
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
    # Selection policy stays physical: required ignored tests are executed
    # here, not admitted through the focused lane's selection policy.
    try:
        qualified_report({(binary_id, name) for name in expected}, report)
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise ValueError("native JUnit evidence is unqualified") from exc
    # Preserve the existing physical aggregate contract, including disabled.
    for node in (report, *report):
        if (node.get("tests") != str(len(expected))
            or node.get("failures") != "0" or node.get("errors") != "0"
            or node.get("skipped", "0") != "0" or node.get("disabled", "0") != "0"):
            raise ValueError("JUnit aggregate not fully successful")
    return len(expected)


def consumer_environment(original: dict[str, str]) -> dict[str, str]:
    env = cargo_environment(original)
    for name in list(env):
        if name.startswith(("PG", "NEXTEST_")) or name in {
            "ORDIVON_PG_TEST_DSN", "ORDIVON_PG_STAGE_TEST_DSN",
            FIXTURE_SCOPE_ENV,
            "HARNESS_PG_PYTHON", "VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH",
            "UV_PROJECT_ENVIRONMENT", "UV_PROJECT", "UV_PYTHON", "UV_NO_SYNC",
            "UV_NO_DEFAULT_GROUPS", "UV_NO_DEV", "UV_FROZEN", "UV_NO_EDITABLE",
        }:
            env.pop(name)
    return env


def allocate_fixture_scope() -> Path:
    # Not a TemporaryDirectory: timeout, panic and SIGKILL must not erase
    # the only attribution carrier. Empty verified scopes are removed below.
    scope = Path(tempfile.mkdtemp(prefix="od-mcp-", dir="/var/tmp"))
    scope.chmod(0o755)
    return scope


def release_empty_scope(scope: Path) -> None:
    meta = scope.lstat()
    if (scope.parent != Path("/var/tmp") or not scope.name.startswith("od-mcp-")
        or not stat.S_ISDIR(meta.st_mode) or meta.st_uid != os.getuid()
        or stat.S_IMODE(meta.st_mode) != 0o755 or scope.resolve() != scope):
        raise RuntimeError(f"native fixture scope identity changed: {scope}")
    retained = sorted(p.name for p in scope.iterdir())
    if retained:
        raise RuntimeError(f"native fixture resources retained: {scope}: {retained}")
    # rmdir is itself an emptiness check, not recursive cleanup.
    scope.rmdir()


def prepare_harness_python(root: Path, env: dict[str, str]) -> str:
    """Materialize the actual source-cut Harness lock in a private environment."""
    harness = ROOT.parent / "harness"
    lock = harness / "uv.lock"
    digest = hashlib.sha256(lock.read_bytes()).hexdigest()
    fixture_env = dict(env, UV_PROJECT_ENVIRONMENT=str(root / "harness-venv"))
    subprocess.run(
        ["uv", "sync", "--locked", "--no-editable", "--group", "test"],
        cwd=harness, env=fixture_env, check=True, timeout=400,
    )
    python = str(root / "harness-venv" / "bin" / "python")
    subprocess.run(
        [python, "-c", "import jsonschema, psycopg, pytest; import sys; print(sys.version)"],
        cwd=harness, env=fixture_env, check=True, timeout=30,
    )
    subprocess.run(
        [python, "tests/original_pg_issuer_native_fixture.py", "--help"],
        cwd=harness, env=dict(fixture_env, PYTHONPATH=f"{harness / 'src'}:{harness}"),
        check=True, timeout=30, stdout=subprocess.DEVNULL,
    )
    if hashlib.sha256(lock.read_bytes()).hexdigest() != digest:
        raise RuntimeError("Harness lock changed during environment preparation")
    print(f"HARNESS_UV_LOCK_SHA256={digest}", flush=True)
    return python


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
    subprocess.run(["cargo", *RUNNER_BUILD_ARGS], cwd=ROOT, env=env, check=True, timeout=400)
    with tempfile.TemporaryDirectory(prefix="ordivon-mcp-nextest-", dir="/var/tmp") as temp:
        base = Path(temp)
        env["HARNESS_PG_PYTHON"] = prepare_harness_python(base, env)
        config = base / "nextest.toml"
        # Private native report store, never reuse a shared old report.
        config.write_text(
            (ROOT / ".config/nextest.toml").read_text()
            + '\n[store]\ndir = ' + json.dumps(str(base / "store"))
            + '\n[profile.native-mcp]\nleak-timeout = { period = "500ms", result = "fail" }\n'
            + '[profile.native-mcp.junit]\npath = "junit.xml"\nreport-skipped = "none"\n',
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
        scope = allocate_fixture_scope()
        env[FIXTURE_SCOPE_ENV] = str(scope)
        print(f"NATIVE_MCP_FIXTURE_SCOPE={scope}", flush=True)
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
        # Preserve the original native report and exit before checking the
        # independent external-resource obligation. Retained scope stays
        # inspectable, never recursively deleted by the test runner.
        try:
            release_empty_scope(scope)
        except (OSError, RuntimeError) as exc:
            # stdout is a distinct retained verdict; compiler stderr may
            # already have reached the Runtime log capture limit.
            print(f"NATIVE_MCP_FIXTURE_UNQUALIFIED: {exc}", flush=True)
            if scope.is_dir() and not scope.is_symlink():
                for root in sorted(scope.iterdir()):
                    if root.is_dir() and not root.is_symlink():
                        marker = root / "fixture-retention.txt"
                        if marker.is_file() and not marker.is_symlink():
                            with marker.open("rb") as stream:
                                reason = stream.read(4096).decode("utf-8", "replace")
                            print("NATIVE_MCP_FIXTURE_DIAGNOSTIC=" + json.dumps([root.name, reason]), flush=True)
            return result.returncode or 1
        print("NATIVE_MCP_FIXTURE_SCOPE_EMPTY_AND_RELEASED", flush=True)
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
