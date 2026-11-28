"""Model validation and actual context consume the same selected evidence."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import unittest
from itertools import product
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from ordivon_studio.models import validate_repository
from ordivon_studio.production_context import build_production_context
from ordivon_studio.production_validation import _validate_production_semantics

TEMPLATE = Path(__file__).resolve().parents[1] / "productions/browser-perception-note"


def fixture(root: Path):
    production = json.loads((TEMPLATE / "production.json").read_text())
    claims = json.loads((TEMPLATE / "claims.json").read_text())
    for binding in production["sourceBindings"]:
        binding["repository"] = "fixture-external"
    production["sources"] = {"claims": "claims.json"}
    production["outputs"] = []
    (root / "claims.json").write_text(json.dumps(claims))
    return production, claims


def write_manifest(root, production):
    (root / "production.json").write_text(json.dumps(production))


class ProductionIdentityParityTests(unittest.TestCase):
    def test_manifest_selects_actual_claim_set_not_shadow(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "production"
            root.mkdir()
            production, claims = fixture(root)
            production["sources"]["claims"] = "selected.json"
            write_manifest(root, production)
            selected = root / "selected.json"
            foreign = copy.deepcopy(claims)
            foreign["productionId"] = "foreign"
            with patch("ordivon_studio.models.PRODUCTION_DIRECTORY", base), patch(
                "ordivon_studio.production_validation.ROOT", base
            ):
                selected.write_text(json.dumps(foreign))
                self.assertTrue(any("claims productionId" in e for e in validate_repository()))
                with self.assertRaisesRegex(ValueError, "productionId"):
                    build_production_context(root)
                selected.write_text(json.dumps(claims))
                (root / "claims.json").unlink()
                self.assertEqual(validate_repository(), [])
                self.assertEqual(build_production_context(root)["claims"]["count"], len(claims["claims"]))
                # Reintroduce a shadow with contradictory identity. It is not selected.
                (root / "claims.json").write_text(json.dumps(foreign))
                self.assertEqual(validate_repository(), [])
                self.assertEqual(build_production_context(root)["claims"]["count"], len(claims["claims"]))
                selected.unlink()
                self.assertTrue(any("required production document is missing" in e for e in validate_repository()))
                with self.assertRaises(FileNotFoundError):
                    build_production_context(root)
                outside = base / "outside.json"
                outside.write_text(json.dumps(claims))
                selected.symlink_to(outside)
                self.assertTrue(any("invalid claims source" in e for e in validate_repository()))
                with self.assertRaisesRegex(ValueError, "escapes"):
                    build_production_context(root)

    def test_finite_carrier_policy_matrix(self):
        # Independent finite outcome table: match, changed, missing, unstable
        # x source assertion / historical output hint. Missing/unstable output
        # is not a failed work, but cannot become matching evidence.
        expectations = {
            "match": ("MATCHES_DECLARED_DIGEST", False, False),
            "changed": ("DIFFERS_FROM_DECLARED_DIGEST", True, True),
            "missing": ("UNKNOWN_SELECTED_FILE_UNAVAILABLE", True, False),
            "unstable": ("UNKNOWN_SELECTED_FILE_UNSTABLE", True, False),
        }
        for role, state in product(("sourceCarrier", "outputCarrier"), expectations):
            with self.subTest(role=role, state=state), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                production, claims = fixture(root)
                payload = root / "payload.bin"
                if state != "missing":
                    payload.write_bytes(b"changed" if state == "changed" else b"original")
                if role == "sourceCarrier":
                    production["sources"]["scripts"] = ["payload.bin"]
                production["outputs"] = [{
                    "id": "out", "kind": "image", "status": "rendered", role: "payload.bin",
                    "blobDigest": "sha256:" + hashlib.sha256(b"original").hexdigest(),
                }]
                write_manifest(root, production)
                real_fstat = os.fstat
                calls = 0

                def changed(fd):
                    nonlocal calls
                    stat = real_fstat(fd)
                    calls += 1
                    if state == "unstable" and calls % 2 == 0:
                        return SimpleNamespace(
                            st_dev=stat.st_dev, st_ino=stat.st_ino, st_size=stat.st_size,
                            st_mtime_ns=stat.st_mtime_ns + 1, st_ctime_ns=stat.st_ctime_ns,
                        )
                    return stat

                with patch("ordivon_studio.production_validation.ROOT", root), patch(
                    "ordivon_studio.assets.os.fstat", side_effect=changed
                ):
                    errors = _validate_production_semantics(root / "production.json", production, claims, None)
                    projected = build_production_context(root)["outputByteIdentity"]
                expected, source_error, output_error = expectations[state]
                self.assertEqual(projected["observations"][0]["relation"], expected)
                self.assertEqual(bool(errors), source_error if role == "sourceCarrier" else output_error)
                self.assertEqual(projected["publicationAuthorization"], "not-evaluated")

    def test_invalid_carrier_aliases_rejected_before_byte_observation(self):
        for role, path in product(
            ("sourceCarrier", "outputCarrier"),
            ("./payload.bin", "dir/../payload.bin", "dir//payload.bin",
             "dir\\payload.bin", "C:payload.bin", "payload.bin/"),
        ):
            with self.subTest(role=role, path=path), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                production, claims = fixture(root)
                (root / "dir").mkdir()
                (root / "payload.bin").write_bytes(b"original")
                if role == "sourceCarrier":
                    production["sources"]["scripts"] = [path]
                production["outputs"] = [{
                    "id": "out", "kind": "image", "status": "rendered", role: path,
                    "blobDigest": "sha256:" + hashlib.sha256(b"original").hexdigest(),
                }]
                write_manifest(root, production)
                with patch("ordivon_studio.production_validation.ROOT", root), patch(
                    "ordivon_studio.production_output_identity.hash_file",
                    side_effect=AssertionError("invalid carrier must not be hashed"),
                ):
                    errors = _validate_production_semantics(root / "production.json", production, claims, None)
                    row = build_production_context(root)["outputByteIdentity"]["observations"][0]
                self.assertTrue(errors)
                self.assertTrue(row["relation"].startswith("INVALID_"))
                self.assertIsNone(row["observedBlob"])
