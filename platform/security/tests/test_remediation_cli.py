"""Exercise the actual report-delta CLI boundary, not a substitute scanner."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RemediationCliTests(unittest.TestCase):
    def test_cli_standing_and_exact_report_identity(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            inputs = {
                "before-sbom": {"components": [{"name": "fixture", "version": "1"}]},
                "after-sbom": {"components": [{"name": "fixture", "version": "2"}]},
                "before-report": {
                    "ArtifactType": "cyclonedx",
                    "Results": [
                        {
                            "Vulnerabilities": [
                                {
                                    "VulnerabilityID": "FIXTURE-OLD",
                                    "PkgName": "fixture",
                                    "InstalledVersion": "1",
                                }
                            ]
                        }
                    ],
                },
                "after-report": {
                    "ArtifactType": "cyclonedx",
                    "Results": [
                        {
                            "Vulnerabilities": [
                                {
                                    "VulnerabilityID": "FIXTURE-OTHER",
                                    "PkgName": "fixture",
                                    "InstalledVersion": "2",
                                }
                            ]
                        }
                    ],
                },
            }
            command = [
                sys.executable,
                str(ROOT / "scripts/verify_remediation_delta.py"),
                "--package",
                "fixture",
            ]
            identities = {}
            for name, value in inputs.items():
                path = directory / name
                raw = (json.dumps(value, indent=2) + "\n").encode()
                path.write_bytes(raw)
                identities[name] = "sha256:" + hashlib.sha256(raw).hexdigest()
                command.extend(["--" + name, str(path)])
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(
                data["standing"], "BASELINE_VULNERABILITY_IDS_ABSENT_IN_SUPPLIED_REPORTS"
            )
            self.assertEqual(
                data,
                {
                    "standing": "BASELINE_VULNERABILITY_IDS_ABSENT_IN_SUPPLIED_REPORTS",
                    "scanInputBinding": "UNKNOWN",
                    "authenticated": False,
                    "package": "fixture",
                    "clearedVulnerabilityIds": ["FIXTURE-OLD"],
                    "clearedCount": 1,
                    "newOrRemainingAfterCount": 1,
                    "beforeObservedVersions": ["1"],
                    "afterVulnerableVersions": ["2"],
                    "beforeSbomSha256": identities["before-sbom"],
                    "afterSbomSha256": identities["after-sbom"],
                    "beforeReportSha256": identities["before-report"],
                    "afterReportSha256": identities["after-report"],
                },
            )
            self.assertEqual(type(data["authenticated"]), bool)

            # A provider report without Results is not an explicit observation.
            (directory / "after-report").write_text(
                '{"ArtifactType":"cyclonedx"}', encoding="utf-8"
            )
            rejected = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(rejected.stdout, "")
            self.assertIn("Results", rejected.stderr)
