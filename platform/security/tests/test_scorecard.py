import unittest

from ordivon_security_v2.scorecard import validate_scorecard_report


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
