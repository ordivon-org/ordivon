"""Unavailability is negative evidence, not an AttributeError or synthetic PASS."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from artifact_verification import stage


class MissingNativeValidatorEvidenceTests(unittest.TestCase):
    def test_document_absent_validator_metadata_is_bounded_failure(self):
        for output in ({"validator": None}, None):
            with self.subTest(validator_output=output), tempfile.TemporaryDirectory() as root:
                directory = Path(root)
                profile = directory / "profile.json"
                profile.write_text("{}")
                document = directory / "document.docx"
                document.write_bytes(b"synthetic-nonconforming-document")
                hooks = SimpleNamespace(
                    validate_profile=lambda _: {
                        "status": "PASS",
                        "profile": {
                            "id": "negative-document-profile",
                            "artifactClass": "document",
                            "gates": {"structural": True},
                        },
                    },
                    primary_suffix=lambda _: ".docx",
                    verify_openxml_artifact=lambda _: {
                        "status": "FAIL",
                        "validatorOutput": output,
                        "failures": ["OpenXML validator unavailable"],
                    },
                )
                def receipt(*args):
                    return {"status": args[4]["status"]}
                with mock.patch.object(stage, "write_gate_receipt", side_effect=receipt) as writer:
                    result = stage.execute_verify_stage(
                        profile, document, directory / "evidence", hooks=hooks
                    )
                self.assertEqual(result["status"], "FAIL", result)
                self.assertFalse(result["profileVerificationComplete"])
                self.assertEqual(result["failures"], ["executed verifier gate(s) failed: structural"])
                self.assertEqual(writer.call_args_list[1].args[6]["DocumentFormat.OpenXml"], "unknown")
