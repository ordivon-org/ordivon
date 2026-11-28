from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest

from anc_canonical import canonical_digest
from ordivon_harness import _historical_receipt_validation as shared

ROOT = Path(__file__).resolve().parents[1]


class HistoricalReceiptValidationTests(unittest.TestCase):
    def test_all_three_readers_share_mechanical_validation(self):
        for script in (
            "check_codex_app_h3_receipt.py",
            "check_hermes_acp_h4_receipt.py",
            "check_harness_replacement_h5_receipt.py",
        ):
            with self.subTest(reader=script):
                spec = importlib.util.spec_from_file_location(script, ROOT / "scripts" / script)
                assert spec and spec.loader
                reader = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(reader)
                for name in ("object", "array", "string", "sha256", "all_true"):
                    self.assertIs(getattr(reader, "_" + name), getattr(shared, "require_" + name))
                if hasattr(reader, "_integer"):
                    self.assertIs(reader._integer, shared.require_integer)
                self.assertIs(reader.verify_integrity, shared.verify_integrity)

    def test_mechanical_checks_keep_exact_diagnostics(self):
        for function, value, expected in (
            (shared.require_object, [], "field must be an object"),
            (shared.require_array, {}, "field must be an array"),
            (shared.require_string, "", "field must be a non-empty string"),
            (shared.require_sha256, None, "field must be a non-empty string"),
            (shared.require_sha256, "sha256:" + "A" * 64, "field must be sha256:<64 lowercase hex>"),
            (shared.require_integer, True, "field must be an integer >= 0"),
        ):
            with self.subTest(function=function.__name__, value=value):
                with self.assertRaises(ValueError) as error:
                    function(value, "field")
                self.assertEqual(str(error.exception), expected)
        self.assertEqual(shared.require_sha256("sha256:" + "a" * 64, "field"), "sha256:" + "a" * 64)

    def test_check_set_requires_exact_boolean_true(self):
        self.assertEqual(shared.require_all_true({"a": True}, {"a"}, "checks"), {"a": True})
        for checks, message in (
            ({"a": 1}, "checks failed: ['a']"),
            ({"a": False}, "checks failed: ['a']"),
            ({"a": True, "b": True}, "checks set differs"),
            ({}, "checks set differs"),
        ):
            with self.subTest(checks=checks):
                with self.assertRaises(ValueError) as error:
                    shared.require_all_true(checks, {"a"}, "checks")
                self.assertEqual(str(error.exception), message)

    def test_integrity_verification_does_not_mutate_nested_receipt(self):
        receipt = {"value": {"a": [1, "two"]}}
        receipt["integrity"] = {
            "algorithm": "sha256",
            "canonicalization": "ordivon-canonical-json-v1",
            "payloadDigest": canonical_digest(receipt),
        }
        before = copy.deepcopy(receipt)
        self.assertIs(shared.verify_integrity(receipt, "integrity"), receipt["integrity"])
        self.assertEqual(receipt, before)
        receipt["value"]["a"].append(3)
        changed = copy.deepcopy(receipt)
        with self.assertRaisesRegex(ValueError, "receipt integrity digest differs"):
            shared.verify_integrity(receipt, "integrity")
        self.assertEqual(receipt, changed)


if __name__ == "__main__":
    unittest.main()
