"""Independent evidence failures for the native MCP acceptance seam."""
import copy
import json
from pathlib import Path
import sys
import os
import signal
import subprocess
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pg_mcp_qualification import (BINARY, PACKAGE, REQUIRED, FIXTURE_SCOPE_ENV, exact_passes,
                                   inventory, consumer_environment, allocate_fixture_scope, release_empty_scope)

ID = f"{PACKAGE}::{BINARY}"


def listed():
    return {"test-count": len(REQUIRED), "rust-suites": {ID: {
        "package-name": PACKAGE, "binary-name": BINARY, "binary-id": ID,
        "status": "listed", "testcases": {
            n: {"kind": "test", "ignored": True, "filter-match": {"status": "matches"}} for n in REQUIRED
        },
    }}}


def report():
    root = ET.Element("testsuites", tests=str(len(REQUIRED)), errors="0", failures="0")
    suite = ET.SubElement(root, "testsuite", name=ID, tests=str(len(REQUIRED)), errors="0", failures="0")
    for name in sorted(REQUIRED):
        ET.SubElement(suite, "testcase", name=name, classname=ID)
    return root, suite


class NativeEvidence(unittest.TestCase):
    def test_exact_native_success(self):
        binary, names = inventory(json.dumps(listed()).encode())
        root, _ = report()
        self.assertEqual(exact_passes(ET.tostring(root), binary, names), len(REQUIRED))

    def test_discovery_missing_deselected_or_wrong_binary(self):
        for mutation in ("missing", "deselected", "wrong", "count", "empty"):
            with self.subTest(mutation=mutation):
                doc = listed()
                suite = doc["rust-suites"][ID]
                name = next(iter(REQUIRED))
                if mutation == "missing":
                    del suite["testcases"][name]
                    doc["test-count"] -= 1
                elif mutation == "deselected":
                    suite["testcases"][name]["filter-match"]["status"] = "mismatch"
                elif mutation == "wrong":
                    suite["binary-name"] = "unit"
                elif mutation == "count":
                    doc["test-count"] += 1
                else:
                    doc["rust-suites"] = {}
                with self.assertRaises(ValueError):
                    inventory(json.dumps(doc).encode())

    def test_junit_skip_flake_duplicate_and_forged_summary(self):
        for mutation in ("skip", "error", "failure", "flakyFailure", "rerunError",
                         "missing", "duplicate", "foreign", "summary"):
            with self.subTest(mutation=mutation):
                root, suite = report()
                case = suite[0]
                if mutation == "missing":
                    suite.remove(case)
                elif mutation == "duplicate":
                    suite[-1] = copy.deepcopy(case)
                elif mutation == "foreign":
                    case.set("classname", "other")
                elif mutation == "summary":
                    root.set("tests", "0")
                else:
                    ET.SubElement(case, "skipped" if mutation == "skip" else mutation)
                with self.assertRaises(ValueError):
                    exact_passes(ET.tostring(root), ID, REQUIRED)

    def test_production_connection_and_filter_environment_removed(self):
        env = consumer_environment({"PATH": "/bin", "PGHOST": "prod", "PGOPTIONS": "secret",
                                    "ORDIVON_PG_TEST_DSN": "prod", "ORDIVON_PG_STAGE_TEST_DSN": "stage",
                                    "NEXTEST_RETRIES": "5", "NEXTEST_FILTERSET": "none()",
                                    "HARNESS_PG_PYTHON": "/unqualified/python", "UV_PROJECT_ENVIRONMENT": "/foreign/venv",
                                    "VIRTUAL_ENV": "/foreign", "PYTHONPATH": "/foreign/src", FIXTURE_SCOPE_ENV: "/foreign"})
        self.assertEqual(env, {"PATH": "/bin"})

    def test_native_scope_release_requires_actual_empty_directory(self):
        scope = allocate_fixture_scope()
        marker = scope / "owned-test-marker"
        try:
            marker.mkdir()
            with self.assertRaisesRegex(RuntimeError, "resources retained"):
                release_empty_scope(scope)
            self.assertTrue(marker.is_dir())
            marker.rmdir()
            release_empty_scope(scope)
            self.assertFalse(scope.exists())
        finally:
            if marker.is_dir():
                marker.rmdir()
            if scope.is_dir():
                scope.rmdir()

    def test_sigkill_retains_attribution_scope_without_recursive_cleanup(self):
        scope = allocate_fixture_scope()
        marker = scope / "owned-test-marker"
        try:
            child = subprocess.run([sys.executable, "-c",
                "import pathlib,os,signal,sys; pathlib.Path(sys.argv[1]).mkdir(); os.kill(os.getpid(),signal.SIGKILL)",
                str(marker)], check=False, timeout=10)
            self.assertEqual(child.returncode, -signal.SIGKILL)
            with self.assertRaisesRegex(RuntimeError, "resources retained"):
                release_empty_scope(scope)
            self.assertTrue(marker.is_dir(), "failed scope must remain attributable")
        finally:
            if marker.is_dir():
                marker.rmdir()
            if scope.is_dir():
                scope.rmdir()


if __name__ == "__main__":
    unittest.main()
