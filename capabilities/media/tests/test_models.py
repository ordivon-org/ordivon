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


    def test_assetless_writing_does_not_require_empty_asset_manifest(self) -> None:
        production_root = ROOT / "productions/browser-perception-note"
        production = json.loads((production_root / "production.json").read_text(encoding="utf-8"))
        self.assertNotIn("assets", production["sources"])
        self.assertFalse((production_root / "assets.json").exists())
        self.assertEqual(validate_repository(), [])

    def test_receipt_references_are_only_enveloped_records(self) -> None:
        production = json.loads((ROOT / "productions/archive-archipelago-001/production.json").read_text(encoding="utf-8"))
        self.assertIn("evidence", production["sources"])
        self.assertGreater(len(production["sources"]["evidence"]), 0)
        for relative_path in production["sources"]["receipts"]:
            receipt = json.loads((ROOT / "productions/archive-archipelago-001" / relative_path).read_text(encoding="utf-8"))
            self.assertEqual(receipt.get("schemaVersion"), 1, relative_path)
            self.assertIsInstance(receipt.get("kind"), str, relative_path)
            self.assertTrue(receipt["kind"], relative_path)

    def test_source_documents_do_not_claim_asset_manifest_semantics(self) -> None:
        for production_id in ["live-relay-001", "ordivon-system-constellation-atlas"]:
            production = json.loads((ROOT / "productions" / production_id / "production.json").read_text(encoding="utf-8"))
            self.assertNotIn("assets", production["sources"])
            self.assertGreater(len(production["sources"]["sourceDocuments"]), 0)
            for relative_path in production["sources"]["sourceDocuments"]:
                self.assertTrue((ROOT / "productions" / production_id / relative_path).is_file())

    def test_current_claim_contract_replaces_legacy_boundary_shape(self) -> None:
        validator = _validator("claims.schema.json")
        for production_id in ["convergence-object-001", "ordivon-system-constellation-atlas"]:
            claims = json.loads((ROOT / "productions" / production_id / "claims.json").read_text(encoding="utf-8"))
            self.assertEqual(list(validator.iter_errors(claims)), [])
            self.assertEqual(claims["productionId"], production_id)
            for claim in claims["claims"]:
                self.assertNotIn("allowedMeaning", claim)
                self.assertNotIn("boundary", claim)

    def test_declared_media_assets_still_fail_schema_when_invalid(self) -> None:
        assets = json.loads((ROOT / "productions/runtime-introduction/assets.json").read_text(encoding="utf-8"))
        assets["assets"][0].pop("rights")
        errors = list(_validator("asset.schema.json").iter_errors(assets))
        self.assertTrue(any("rights" in error.message for error in errors))

    def test_active_cognition_is_bounded_frontier_with_historical_link(self) -> None:
        active = ROOT / "productions/runtime-introduction/cognition.md"
        history = ROOT / "productions/runtime-introduction/history/cognition-through-p4.md"
        self.assertEqual(_validate_cognition_record(active), [])
        self.assertTrue(history.is_file())
        self.assertLess(len(active.read_text(encoding="utf-8").split()), 700)
        self.assertGreater(len(history.read_text(encoding="utf-8").split()), len(active.read_text(encoding="utf-8").split()) * 2)

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
