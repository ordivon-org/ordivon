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
