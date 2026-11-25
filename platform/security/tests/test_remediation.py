import json
import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2.remediation import verify_remediation_delta


class RemediationDeltaTests(unittest.TestCase):
    def _write(self, root, name, value):
        p = root / name
        p.write_text(json.dumps(value))
        return p

    def _report(self, vulnerabilities):
        return {"ArtifactType": "cyclonedx", "Results": [{"Vulnerabilities": vulnerabilities}]}

    def test_fresh_after_evidence_clears_baseline_ids(self):
        with tempfile.TemporaryDirectory() as td:
            r = Path(td)
            bsb = self._write(r, "b-sbom", {"component": "old"})
            asb = self._write(r, "a-sbom", {"component": "new"})
            br = self._write(r, "b-report", self._report([
                {"VulnerabilityID": "CVE-A", "PkgName": "p", "InstalledVersion": "1"},
                {"VulnerabilityID": "CVE-B", "PkgName": "p", "InstalledVersion": "1"},
            ]))
            ar = self._write(r, "a-report", self._report([]))
            result = verify_remediation_delta(package="p", before_sbom_path=bsb, before_report_path=br, after_sbom_path=asb, after_report_path=ar)
            self.assertEqual(result["clearedCount"], 2)

    def test_stale_same_sbom_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            r = Path(td)
            sb = self._write(r, "sbom", {"same": True})
            br = self._write(r, "b", self._report([{"VulnerabilityID": "CVE-A", "PkgName": "p", "InstalledVersion": "1"}]))
            ar = self._write(r, "a", self._report([]))
            with self.assertRaisesRegex(ValueError, "fresh changed SBOM"):
                verify_remediation_delta(package="p", before_sbom_path=sb, before_report_path=br, after_sbom_path=sb, after_report_path=ar)

    def test_remaining_baseline_vulnerability_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            r = Path(td)
            bsb = self._write(r, "b-sbom", {"component": "old"})
            asb = self._write(r, "a-sbom", {"component": "new"})
            v = {"VulnerabilityID": "CVE-A", "PkgName": "p", "InstalledVersion": "1"}
            br = self._write(r, "b", self._report([v]))
            ar = self._write(r, "a", self._report([{**v, "InstalledVersion": "2"}]))
            with self.assertRaisesRegex(ValueError, "remain after remediation"):
                verify_remediation_delta(package="p", before_sbom_path=bsb, before_report_path=br, after_sbom_path=asb, after_report_path=ar)

    def test_supplied_report_delta_is_not_fresh_scan_binding(self):
        with tempfile.TemporaryDirectory() as td:
            r = Path(td)
            bsb = self._write(r, "b-sbom", {"component": "old"})
            asb = self._write(r, "a-sbom", {"component": "new"})
            br = self._write(r, "b-report", self._report([
                {"VulnerabilityID": "CVE-A", "PkgName": "p", "InstalledVersion": "1"},
            ]))
            # A clean report from another scan can be supplied with any changed SBOM.
            ar = self._write(r, "unrelated-clean-report", self._report([]))
            result = verify_remediation_delta(package="p", before_sbom_path=bsb, before_report_path=br, after_sbom_path=asb, after_report_path=ar)
            self.assertEqual(result["standing"], "BASELINE_VULNERABILITY_IDS_ABSENT_IN_SUPPLIED_REPORTS")
            self.assertEqual(result["scanInputBinding"], "UNKNOWN")
            self.assertIs(result["authenticated"], False)

    def test_missing_results_is_not_an_observed_empty_result(self):
        with tempfile.TemporaryDirectory() as td:
            r = Path(td)
            bsb = self._write(r, "b-sbom", {"component": "old"})
            asb = self._write(r, "a-sbom", {"component": "new"})
            br = self._write(r, "b-report", self._report([
                {"VulnerabilityID": "CVE-A", "PkgName": "p", "InstalledVersion": "1"},
            ]))
            ar = self._write(r, "a-report", {"ArtifactType": "cyclonedx"})
            with self.assertRaisesRegex(ValueError, "Results"):
                verify_remediation_delta(package="p", before_sbom_path=bsb, before_report_path=br, after_sbom_path=asb, after_report_path=ar)
