from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qualify_focused_evidence import digest, qualified_report, qualify_carrier, selected_tests, unique_object  # noqa: E402


def inventory():
    return {"rust-suites": {"binary": {"binary-id": "binary", "testcases": {
        "run": {"kind": "test", "ignored": False, "filter-match": {"status": "matches"}},
        "held": {"kind": "test", "ignored": True, "filter-match": {"status": "mismatch", "reason": "expression"}},
    }}}}


def report():
    return ET.fromstring(
        '<testsuites tests="1" skipped="0" failures="0" errors="0" uuid="1deda4b7-8a89-4301-a31f-c6ef43e2586e">'
        '<testsuite name="binary" tests="1" skipped="0" failures="0" errors="0">'
        '<testcase name="run" classname="binary"/></testsuite></testsuites>'
    )


class FocusedEvidenceTests(unittest.TestCase):
    def test_changed_build_carrier_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            carrier = Path(directory) / "tests.tar.zst"
            carrier.write_bytes(b"original")
            original = digest(carrier)
            self.assertEqual(qualify_carrier(carrier, original), original)
            carrier.write_bytes(b"replaced")
            with self.assertRaisesRegex(ValueError, "carrier changed"):
                qualify_carrier(carrier, original)

    def test_exact_native_identity(self):
        self.assertEqual(qualified_report(selected_tests(inventory()), report()),
                         "1deda4b7-8a89-4301-a31f-c6ef43e2586e")

    def test_selected_ignored_rejected_but_unrelated_ignored_allowed(self):
        data = inventory()
        self.assertEqual(selected_tests(data), {("binary", "run")})
        data["rust-suites"]["binary"]["testcases"]["held"]["filter-match"] = {"status": "matches"}
        with self.assertRaisesRegex(ValueError, "selected ignored"):
            selected_tests(data)

    def test_duplicate_json_identity(self):
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            json.loads('{"a":1,"a":2}', object_pairs_hook=unique_object)

    def test_unknown_native_match_standing(self):
        data = inventory()
        data["rust-suites"]["binary"]["testcases"]["run"]["filter-match"] = {"status": "unknown"}
        with self.assertRaises(ValueError):
            selected_tests(data)

    def test_nonempty_exact_selection_required(self):
        for expected in (set(), {("binary", "other")}, {("binary", "run"), ("binary", "extra")}):
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                qualified_report(expected, report())

    def test_suite_grammar_and_binary_partition_are_exact(self):
        for change in ("suite-error", "unknown-child", "duplicate-binary", "empty-foreign-suite"):
            with self.subTest(change=change):
                root = report()
                suite = root[0]
                suite.append(ET.Element("testcase", name="second", classname="binary"))
                suite.set("tests", "2")
                root.set("tests", "2")
                expected = {("binary", "run"), ("binary", "second")}
                self.assertTrue(qualified_report(expected, root))
                if change == "suite-error":
                    ET.SubElement(suite, "error").text = "setup failed"
                elif change == "unknown-child":
                    ET.SubElement(suite, "unknown-verdict")
                elif change == "duplicate-binary":
                    second = suite[1]
                    suite.remove(second)
                    suite.set("tests", "1")
                    ET.SubElement(root, "testsuite", dict(suite.attrib)).append(second)
                else:
                    ET.SubElement(root, "testsuite", name="foreign", tests="0",
                                  skipped="0", failures="0", errors="0")
                with self.assertRaises(ValueError):
                    qualified_report(expected, root)

    def test_mutated_report_cannot_be_qualified(self):
        expected = selected_tests(inventory())
        for change in ("duplicate", "skipped", "failure", "error", "flakyFailure",
                       "wrong-class", "wrong-count", "wrong-id", "missing"):
            with self.subTest(change=change):
                root = report()
                suite, case = root[0], root[0][0]
                if change == "duplicate":
                    suite.append(copy.deepcopy(case))
                    suite.set("tests", "2")
                    root.set("tests", "2")
                elif change in {"skipped", "failure", "error", "flakyFailure"}:
                    ET.SubElement(case, change)
                elif change == "wrong-class":
                    case.set("classname", "other")
                elif change == "wrong-count":
                    root.set("tests", "0")
                elif change == "wrong-id":
                    root.set("uuid", "not-a-uuid")
                elif change == "missing":
                    suite.remove(case)
                    root.set("tests", "0")
                    suite.set("tests", "0")
                with self.assertRaises(ValueError):
                    qualified_report(expected, root)


if __name__ == "__main__":
    unittest.main()
