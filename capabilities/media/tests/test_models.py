from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ordivon_studio.models import _validate_cognition_record, _validate_runtime_receipt, _validator, validate_repository


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = json.loads(
    (ROOT / "productions/runtime-introduction/evidence/runtime-demo.receipt.json").read_text(encoding="utf-8")
)


class ModelTests(unittest.TestCase):
    def test_repository_models_are_valid(self) -> None:
        self.assertEqual(validate_repository(), [])

    def test_production_cognition_uses_protocol_sections_without_second_manifest(self) -> None:
        path = ROOT / "productions/runtime-introduction/cognition.md"
        self.assertEqual(_validate_cognition_record(path), [])
        text = path.read_text(encoding="utf-8")
        self.assertIn("not a second Production manifest", text)
        production = json.loads((ROOT / "productions/runtime-introduction/production.json").read_text(encoding="utf-8"))
        self.assertEqual(production["sources"]["cognition"], "cognition.md")

    def test_working_profile_does_not_force_video_shape_on_writing(self) -> None:
        production = json.loads((ROOT / "productions/runtime-introduction/production.json").read_text(encoding="utf-8"))
        production["workingProfile"] = {}
        errors = list(_validator("production.schema.json").iter_errors(production))
        self.assertEqual(errors, [])

    def test_cognition_rejects_missing_protocol_stage(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cognition.md"
            path.write_text("## FRAME\n\n## BIND\n", encoding="utf-8")
            errors = _validate_cognition_record(path)
            self.assertTrue(any("missing cognition section EXPRESS" in error for error in errors))

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
