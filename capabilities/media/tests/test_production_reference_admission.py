"""Exercise selected local references in actual model and learning consumers."""
from __future__ import annotations

import json
import tempfile
import unittest
from itertools import product
from pathlib import Path
from unittest.mock import patch

from ordivon_studio.learning_context import _production_learning_records
from ordivon_studio.models import validate_repository

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "productions/browser-perception-note"
STAGES = ("FRAME", "BIND", "EXPRESS", "RENDER", "AUDIT", "DECIDE", "LEARNING")


class ProductionReferenceAdmissionTests(unittest.TestCase):
    def test_local_reference_matrix_rejects_before_read(self):
        for role, case in product(("assets", "receipts", "cognition"), ("directory", "outside", "symlink", "alias")):
            with self.subTest(role=role, case=case), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                productions = root / "productions"
                production_root = productions / "fixture"
                production_root.mkdir(parents=True)
                p = json.loads((TEMPLATE / "production.json").read_bytes())
                claims = json.loads((TEMPLATE / "claims.json").read_bytes())
                for binding in p["sourceBindings"]:
                    binding["repository"] = "fixture-external"
                p["outputs"] = []
                (production_root / "claims.json").write_text(json.dumps(claims))
                payload = "\n\n".join("## " + stage + "\nbody" for stage in STAGES)
                if role == "assets":
                    payload = json.dumps({"schemaVersion": 1, "productionId": p["id"], "assets": []})
                elif role == "receipts":
                    payload = json.dumps({"schemaVersion": 1, "kind": "fixture"})
                outside = root / "outside"
                outside.write_text(payload)
                if case == "directory":
                    (production_root / "directory").mkdir()
                    selected = "directory"
                elif case == "outside":
                    selected = "../../outside"
                elif case == "symlink":
                    (production_root / "link").symlink_to(outside)
                    selected = "link"
                else:
                    (production_root / "local").write_text(payload)
                    selected = "./local"
                p["sources"] = {"claims": "claims.json", role: [selected] if role == "receipts" else selected}
                (production_root / "production.json").write_text(json.dumps(p))
                original_bytes = Path.read_bytes
                original_text = Path.read_text

                def guard_bytes(path):
                    if path.resolve() in (outside, production_root / "local"):
                        raise AssertionError("invalid selected source must not be read")
                    return original_bytes(path)

                def guard_text(path, *args, **kwargs):
                    if path.resolve() in (outside, production_root / "local"):
                        raise AssertionError("invalid selected source must not be read")
                    return original_text(path, *args, **kwargs)

                with patch("ordivon_studio.models.PRODUCTION_DIRECTORY", productions), patch(
                    "ordivon_studio.production_validation.ROOT", root
                ), patch.object(Path, "read_bytes", guard_bytes), patch.object(Path, "read_text", guard_text):
                    errors = validate_repository()
                    expected = "receipt" if role == "receipts" else role
                    self.assertTrue(any(f"invalid {expected} source" in error for error in errors), errors)
                    if role == "cognition":
                        if case == "directory":
                            self.assertEqual(_production_learning_records(root), [])
                        else:
                            with self.assertRaises(ValueError):
                                _production_learning_records(root)

    def test_malformed_selected_receipt_is_a_diagnostic_not_a_crash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            productions = root / "productions"
            prod = productions / "fixture"
            prod.mkdir(parents=True)
            p = json.loads((TEMPLATE / "production.json").read_bytes())
            claims = json.loads((TEMPLATE / "claims.json").read_bytes())
            for binding in p["sourceBindings"]:
                binding["repository"] = "fixture-external"
            p["outputs"] = []
            p["sources"] = {"claims": "claims.json", "receipts": ["receipt.json"]}
            (prod / "production.json").write_text(json.dumps(p))
            (prod / "claims.json").write_text(json.dumps(claims))
            for invalid in (b'{"bad":', b'[]', b'\xff'):
                (prod / "receipt.json").write_bytes(invalid)
                with patch("ordivon_studio.models.PRODUCTION_DIRECTORY", productions), patch(
                    "ordivon_studio.production_validation.ROOT", root
                ):
                    errors = validate_repository()
                self.assertTrue(any("receipt.json: invalid production document" in e for e in errors), errors)
