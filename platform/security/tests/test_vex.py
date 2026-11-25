import copy
import unittest

from ordivon_security_v2.vex import bom_link, validate_vex_against_sbom


class CycloneDxVexTests(unittest.TestCase):
    def setUp(self):
        self.sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.7",
            "serialNumber": "urn:uuid:11111111-2222-3333-4444-555555555555",
            "version": 1,
            "components": [
                {"bom-ref": "pkg:pypi/packaging@25.0", "type": "library", "name": "packaging", "version": "25.0"}
            ],
        }
        link = bom_link(
            sbom_serial=self.sbom["serialNumber"], sbom_version=1, bom_ref="pkg:pypi/packaging@25.0"
        )
        self.vex = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.7",
            "serialNumber": "urn:uuid:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "version": 1,
            "vulnerabilities": [{
                "id": "SECURITY-V2-ACCEPTANCE-R1",
                "analysis": {
                    "state": "not_affected",
                    "justification": "code_not_reachable",
                    "response": ["will_not_fix"],
                    "detail": "Acceptance-only statement with an explicit non-reachability rationale.",
                },
                "affects": [{"ref": link}],
            }],
        }

    def test_exact_component_link_is_accepted(self):
        result = validate_vex_against_sbom(self.vex, self.sbom)
        self.assertEqual(result["standing"], "VEX_BOUND_TO_EXACT_SBOM_COMPONENTS")

    def test_changed_component_link_fails_closed(self):
        vex = copy.deepcopy(self.vex)
        vex["vulnerabilities"][0]["affects"][0]["ref"] += "-changed"
        with self.assertRaisesRegex(ValueError, "exact SBOM component"):
            validate_vex_against_sbom(vex, self.sbom)

    def test_not_affected_without_justification_fails_closed(self):
        vex = copy.deepcopy(self.vex)
        del vex["vulnerabilities"][0]["analysis"]["justification"]
        with self.assertRaisesRegex(ValueError, "recognized justification"):
            validate_vex_against_sbom(vex, self.sbom)

    def test_not_affected_without_detail_fails_closed(self):
        vex = copy.deepcopy(self.vex)
        del vex["vulnerabilities"][0]["analysis"]["detail"]
        with self.assertRaisesRegex(ValueError, "specific analysis detail"):
            validate_vex_against_sbom(vex, self.sbom)

    def test_file_result_digest_identifies_the_parsed_bytes(self):
        import hashlib
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from ordivon_security_v2.vex import load_and_validate_vex

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vex_path, sbom_path = root / "vex.json", root / "sbom.json"
            original = json.dumps(self.sbom).encode()
            replacement = json.dumps({**self.sbom, "components": []}).encode()
            sbom_path.write_bytes(original)
            vex_path.write_text(json.dumps(self.vex), encoding="utf-8")
            real_read_text = Path.read_text
            real_read_bytes = Path.read_bytes

            def read_then_replace(path, *args, **kwargs):
                data = real_read_text(path, *args, **kwargs)
                if path == sbom_path:
                    path.write_bytes(replacement)
                return data

            def read_bytes_then_replace(path, *args, **kwargs):
                data = real_read_bytes(path, *args, **kwargs)
                if path == sbom_path:
                    path.write_bytes(replacement)
                return data

            with (
                patch.object(Path, "read_text", read_then_replace),
                patch.object(Path, "read_bytes", read_bytes_then_replace),
            ):
                result = load_and_validate_vex(vex_path, sbom_path)
            self.assertEqual(result["sbomSha256"], "sha256:" + hashlib.sha256(original).hexdigest())
            self.assertEqual(sbom_path.read_bytes(), replacement)

    def test_file_boundary_rejects_duplicate_analysis_state(self):
        import json
        import tempfile
        from pathlib import Path

        from ordivon_security_v2.vex import load_and_validate_vex

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vex_path, sbom_path = root / "vex.json", root / "sbom.json"
            sbom_path.write_text(json.dumps(self.sbom), encoding="utf-8")
            raw = json.dumps(self.vex).replace('"state": "not_affected"', '"state": "exploitable", "state": "not_affected"')
            vex_path.write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_and_validate_vex(vex_path, sbom_path)
