from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ordivon_studio.models import _validate_runtime_receipt, validate_repository


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = json.loads(
    (ROOT / "productions/runtime-introduction/evidence/runtime-demo.receipt.json").read_text(encoding="utf-8")
)


class ModelTests(unittest.TestCase):
    def test_repository_models_are_valid(self) -> None:
        self.assertEqual(validate_repository(), [])

    def test_receipt_rejects_identity_drift(self) -> None:
        receipt = copy.deepcopy(RECEIPT)
        receipt["evidence"]["jobId"] = "job-different"
        errors = _validate_runtime_receipt(Path("receipt.json"), receipt)
        self.assertTrue(any("jobId does not match" in error for error in errors))

    def test_receipt_rejects_private_paths(self) -> None:
        receipt = copy.deepcopy(RECEIPT)
        receipt["presentation"][0]["detail"] = "/root/private/source"
        errors = _validate_runtime_receipt(Path("receipt.json"), receipt)
        self.assertTrue(any("private material" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
