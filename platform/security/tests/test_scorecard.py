import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ordivon_security_v2.scorecard import (
    load_and_validate_scorecard_report,
    validate_scorecard_report,
)


class ScorecardEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.commit = "a" * 40
        self.report = {
            "repo": {"name": "github.com/example/project", "commit": self.commit},
            "score": 8.9,
            "checks": [
                {"name": "Branch-Protection", "score": 8, "reason": "not maximal"},
                {"name": "Token-Permissions", "score": 9, "reason": "one broad token"},
                {"name": "Vulnerabilities", "score": 0, "reason": "known vulnerabilities"},
            ],
        }

    def test_named_checks_are_retained_and_aggregate_is_not_authority(self):
        result = validate_scorecard_report(
            self.report,
            expected_repo="github.com/example/project",
            expected_commit=self.commit,
            required_checks=("Branch-Protection", "Vulnerabilities"),
        )
        self.assertEqual(result["standing"], "SCORECARD_EVIDENCE_CURRENT")
        self.assertEqual(result["providerAggregateScore"], 8.9)
        self.assertFalse(result["aggregateAuthoritative"])
        self.assertEqual(
            [x["name"] for x in result["checks"]],
            ["Branch-Protection", "Token-Permissions", "Vulnerabilities"],
        )

    def test_changed_revision_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "revision mismatch"):
            validate_scorecard_report(
                self.report,
                expected_repo="github.com/example/project",
                expected_commit="b" * 40,
            )

    def test_missing_required_check_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "missing required"):
            validate_scorecard_report(
                self.report,
                expected_repo="github.com/example/project",
                expected_commit=self.commit,
                required_checks=("Signed-Releases",),
            )

    def test_duplicate_check_fails_closed(self):
        self.report["checks"].append(dict(self.report["checks"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_scorecard_report(
                self.report,
                expected_repo="github.com/example/project",
                expected_commit=self.commit,
            )

    def test_file_projection_digest_matches_observed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scorecard.json"
            original = (json.dumps(self.report, indent=2) + "\n").encode()
            path.write_bytes(original)

            def validate_then_replace(report, **kwargs):
                result = validate_scorecard_report(report, **kwargs)
                changed = dict(self.report, score=1)
                path.write_text(json.dumps(changed), encoding="utf-8")
                return result

            with patch(
                "ordivon_security_v2.scorecard.validate_scorecard_report",
                side_effect=validate_then_replace,
            ):
                result = load_and_validate_scorecard_report(
                    path,
                    expected_repo="github.com/example/project",
                    expected_commit=self.commit,
                )
            self.assertEqual(result["providerAggregateScore"], 8.9)
            self.assertEqual(result["evidenceSha256"], "sha256:" + hashlib.sha256(original).hexdigest())

    def test_file_consumer_rejects_ambiguous_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "scorecard.json"
            raw = json.dumps(self.report).replace('"score": 8.9', '"score": 3, "score": 8.9', 1)
            path.write_text(raw, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON member"):
                load_and_validate_scorecard_report(
                    path,
                    expected_repo="github.com/example/project",
                    expected_commit=self.commit,
                )

    def test_cli_consumes_exact_report_and_rejects_ambiguous_input(self):
        script = Path(__file__).resolve().parents[1] / "scripts/validate_scorecard_result.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            raw = (json.dumps(self.report, indent=2) + "\n").encode()
            path.write_bytes(raw)
            command = [
                sys.executable, str(script), str(path),
                "--repo", "github.com/example/project", "--commit", self.commit,
                "--require-check", "Vulnerabilities",
            ]
            valid = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            result = json.loads(valid.stdout)
            self.assertEqual(result["evidenceSha256"], "sha256:" + hashlib.sha256(raw).hexdigest())
            self.assertEqual(result["requiredChecks"], ["Vulnerabilities"])
            self.assertFalse(result["aggregateAuthoritative"])
            self.assertEqual(result["providerAggregateScore"], 8.9)
            path.write_bytes(raw.replace(b'"score": 8.9', b'"score": 3, "score": 8.9', 1))
            invalid = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertEqual(invalid.stdout, "")
            self.assertIn("duplicate JSON member", invalid.stderr)
