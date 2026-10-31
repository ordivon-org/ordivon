from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAREER = ROOT / "meta/next/evidence/career"
FIXTURES = ROOT / "meta/next/fixtures/career"
RANKING = CAREER / "github-career-provider-ranking-20261031.json"
STACK = ROOT / "meta/next/planning/career-external-provider-stack-r1.json"
REVIEW = CAREER / "independent-codex-review-baf7f557-20261101.json"
REPLAY = CAREER / "career-ops-1.38.0-replay-20261101.json"
JOBSPY_PLUGIN = ROOT / "extensions/ordivon-career-discovery"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CareerExternalProviderSnapshotTest(unittest.TestCase):
    """Snapshot/composition consistency only.

    Provider behavior is qualified by explicit replay commands/evidence, not by
    these JSON assertions.
    """

    def test_ranking_is_a_dated_discovery_snapshot_not_activation_authority(self) -> None:
        data = load(RANKING)
        rows = data["providers"]
        self.assertEqual(len(rows), len({row["repository"] for row in rows}))
        self.assertEqual(rows, sorted(rows, key=lambda row: row["stars"], reverse=True))
        self.assertIn("not correctness", data["truthBoundary"].lower())
        self.assertIn("adoption additionally requires", data["rankingRule"].lower())

    def test_stack_has_only_one_behaviorally_qualified_provider_capability(self) -> None:
        stack = load(STACK)
        self.assertEqual(stack["schemaVersion"], 3)
        self.assertTrue(stack["constraints"]["noCareerRuntime"])
        self.assertTrue(stack["constraints"]["noSecondGlobalRegistry"])
        self.assertTrue(stack["constraints"]["noDurableSqliteCareerState"])
        self.assertTrue(stack["constraints"]["unknownIsNotFalse"])

        qualified = stack["behaviorallyQualified"]
        self.assertEqual(len(qualified), 1)
        self.assertEqual(qualified[0]["provider"], "career-ops-hq/career-ops")
        self.assertEqual(qualified[0]["version"], "1.38.0")
        self.assertEqual(
            qualified[0]["releaseGitHead"],
            "115bc9873e3d43e23883f3c8f16436617facc62c",
        )
        self.assertEqual(qualified[0]["standing"], "BEHAVIORALLY_REPLAYED_SYNTHETIC")

    def test_interface_qualification_does_not_claim_reactive_resume_behavior(self) -> None:
        stack = load(STACK)
        interfaces = {x["provider"]: x for x in stack["interfaceQualified"]}
        reactive = interfaces["reactive-resume/reactive-resume"]
        self.assertEqual(reactive["stableRelease"], "v6.0.9")
        self.assertEqual(
            reactive["releaseCommit"],
            "854459a44eb896ca185611bf669a65be4d5111cf",
        )
        self.assertEqual(
            reactive["standing"],
            "STABLE_NATIVE_PLUGIN_INTERFACE_VERIFIED_NOT_CONNECTED",
        )
        self.assertEqual(
            reactive["consumerState"],
            "NO_AUTHENTICATED_CONSUMER_IN_THIS_CANDIDATE",
        )

        ev = load(CAREER / "reactive-resume-mcp-boundary-20261031.json")
        self.assertTrue(ev["acceptance"]["stableReleasePluginSchemasValid"])
        self.assertEqual(ev["hostedBoundaryProbe"]["httpStatus"], 401)
        self.assertIn("neither grants access", ev["truthBoundary"].lower())

    def test_unproven_providers_are_dormant_and_jobspy_plugin_is_deleted(self) -> None:
        stack = load(STACK)
        dormant = {x["provider"]: x for x in stack["dormantReferences"]}
        self.assertEqual(
            dormant["srbhr/Resume-Matcher"]["standing"],
            "EXPERIMENT_ONLY_NO_ADMITTED_CONSUMER",
        )
        self.assertEqual(
            dormant["Gsync/jobsync"]["standing"],
            "REFERENCE_ONLY_NO_ACTIVE_BINDING",
        )
        self.assertEqual(
            dormant["speedyapply/JobSpy"]["standing"],
            "DORMANT_FALLBACK_PACKAGE_SMOKE_ONLY",
        )
        self.assertFalse(JOBSPY_PLUGIN.exists())

    def test_independent_review_block_is_preserved_and_requires_fresh_rereview(self) -> None:
        review = load(REVIEW)
        self.assertEqual(review["reviewedHead"], "baf7f557e0bf29866f231cf1af4b8a4a58632257")
        self.assertEqual(review["verdict"], "BLOCK")
        self.assertEqual(
            {x["id"] for x in review["mergeBlockers"]},
            {"C1", "C2", "C3"},
        )
        self.assertFalse(review["secondHarnessAttempt"]["countedAsIndependentReview"])

        gate = load(STACK)["integrationGate"]
        self.assertEqual(gate["lastIndependentReview"]["verdict"], "BLOCK")
        self.assertTrue(gate["lastIndependentReview"]["independentCounterexampleObserved"])
        self.assertTrue(gate["freshIndependentReviewRequired"])
        self.assertFalse(gate["mergeAdmitted"])

    def test_provider_native_replay_evidence_is_bound_to_committed_fixtures(self) -> None:
        ev = load(REPLAY)
        self.assertEqual(ev["binding"]["version"], "1.38.0")
        self.assertEqual(
            ev["binding"]["releaseGitHead"],
            "115bc9873e3d43e23883f3c8f16436617facc62c",
        )
        jd = FIXTURES / "career-ops-synthetic-jd.md"
        cv = FIXTURES / "career-ops-synthetic-cv.md"
        self.assertEqual(ev["fixtures"]["jobDescription"]["sha256"], sha256(jd))
        self.assertEqual(ev["fixtures"]["syntheticCv"]["sha256"], sha256(cv))
        self.assertEqual(
            ev["observed"]["gapResult"]["supportedByResume"],
            ["TypeScript", "Rust", "Python", "Go"],
        )
        self.assertEqual(
            ev["observed"]["gapResult"]["gap"],
            ["Spring", "JavaScript", "C++"],
        )
        self.assertEqual(ev["observed"]["selfTestSummary"], "115 passed, 0 failed")
        self.assertEqual(ev["observed"]["negativeCurrentnessProbeExitCode"], 1)
        self.assertEqual(
            ev["observed"]["negativeCurrentnessProbeObserved"],
            "Unknown option: --url",
        )
        self.assertFalse(ev["acceptance"]["userDataUsed"])
        self.assertFalse(ev["acceptance"]["externalJobBoardQueried"])

    def test_historical_slices_are_not_admission_proof(self) -> None:
        stack = load(STACK)
        by_id = {x["id"]: x for x in stack["evidenceClassification"]}
        self.assertEqual(
            by_id["cloudflare-live-slice"]["standing"],
            "HISTORICAL_LIVE_OBSERVATION_NOT_REPLAY_COMPLETE",
        )
        self.assertEqual(
            by_id["resume-matcher-preservation-slice"]["standing"],
            "EXPERIMENT_ONLY_NOT_ADMITTED",
        )

        matcher = load(CAREER / "resume-matcher-1.4.0-artifact-compiler-slice-20261101.json")
        self.assertIn("GROUNDING_REVIEW_REQUIRED", matcher["positivePreservationCheck"]["grounding_warnings"][0])
        self.assertIn("SQLite", matcher["sqliteBoundary"])


if __name__ == "__main__":
    unittest.main()
