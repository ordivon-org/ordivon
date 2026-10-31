from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAREER = ROOT / "meta/next/evidence/career"
RANKING = CAREER / "github-career-provider-ranking-20261031.json"
STACK = ROOT / "meta/next/planning/career-external-provider-stack-r1.json"
PLUGIN = ROOT / "extensions/ordivon-career-discovery"
MCP_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


class CareerExternalProviderStackTest(unittest.TestCase):
    def test_ranking_is_unique_descending_and_current_selection_is_maintained(self) -> None:
        rows = load(RANKING)["providers"]
        self.assertEqual(len(rows), len({row["repository"] for row in rows}))
        self.assertEqual(rows, sorted(rows, key=lambda row: row["stars"], reverse=True))
        by_repo = {row["repository"]: row for row in rows}
        for repo in (
            "career-ops-hq/career-ops",
            "reactive-resume/reactive-resume",
            "srbhr/Resume-Matcher",
            "speedyapply/JobSpy",
        ):
            row = by_repo[repo]
            self.assertFalse(row["archived"], repo)
            self.assertIn(row["license"], {"MIT", "Apache-2.0"}, repo)
            self.assertGreater(row["commits30d"], 0, repo)
        self.assertEqual(by_repo["xitanggg/open-resume"]["decision"], "NO_NEW_ADOPTION_STALE")
        self.assertEqual(by_repo["xitanggg/open-resume"]["commits90d"], 0)

    def test_stack_separates_release_identity_authority_and_persistence(self) -> None:
        stack = load(STACK)
        self.assertEqual(stack["schemaVersion"], 2)
        self.assertEqual(stack["providerIdentityPolicy"]["executableContract"], "stable release/package/commit identity")
        self.assertTrue(stack["providerIdentityPolicy"]["floatingLatestForbiddenForDurableExecution"])
        self.assertTrue(stack["constraints"]["noCareerRuntime"])
        self.assertTrue(stack["constraints"]["noSecondGlobalRegistry"])
        self.assertTrue(stack["constraints"]["noDurableSqliteCareerState"])
        self.assertTrue(stack["constraints"]["providerScoresAreDiagnosticsNotOutcomeProbability"])
        by_id = {layer["id"]: layer for layer in stack["layers"]}

        career_ops = by_id["workflow"]
        self.assertEqual(career_ops["pin"], "1.38.0")
        self.assertEqual(career_ops["releaseGitHead"], "115bc9873e3d43e23883f3c8f16436617facc62c")
        self.assertNotEqual(career_ops["releaseGitHead"], career_ops["observedMain"])
        self.assertEqual(career_ops["standing"], "RELEASE_INIT_VERIFIED")

        reactive = by_id["product-surface"]
        self.assertEqual(reactive["primary"], "reactive-resume/reactive-resume")
        self.assertIn("NATIVE_PLUGIN", reactive["standing"])
        self.assertEqual(reactive["stableChannel"], "v6.0.9")
        self.assertEqual(reactive["releaseCommit"], "854459a44eb896ca185611bf669a65be4d5111cf")
        self.assertEqual(reactive["hostedMcpEndpoint"], "https://rxresu.me/mcp")

        matcher = by_id["artifact-compiler"]
        self.assertEqual(matcher["pin"], "1.4.0")
        self.assertEqual(matcher["testedPython"], "3.13")
        self.assertIn("create_application", matcher["excludedInitialTools"])
        self.assertIn("SQLite", matcher["persistenceRule"])
        self.assertNotIn("create_application", matcher["allowedInitialTools"])

        jobsync = by_id["opportunity-discovery-methods"]
        self.assertIn("NO_PARALLEL_PRODUCT", jobsync["standing"])

    def test_jobspy_agent_plugin_is_pinned_and_secret_free(self) -> None:
        plugin = load(PLUGIN / "plugin.json")
        mcp = load(PLUGIN / "mcp.json")
        self.assertEqual(plugin["$schema"], PLUGIN_SCHEMA)
        self.assertEqual(mcp["$schema"], MCP_SCHEMA)
        server = mcp["mcpServers"]["jobspy"]
        self.assertEqual(server["type"], "stdio")
        self.assertEqual(server["command"], "uvx")
        self.assertEqual(server["args"], ["--from", "python-jobspy[mcp]==1.4.1", "mcp-jobspy"])
        self.assertNotIn("@latest", json.dumps(mcp))
        self.assertNotIn("env", server)

    def test_career_ops_release_is_executable_and_main_drift_is_not_promoted(self) -> None:
        ev = load(CAREER / "career-ops-1.38.0-provider-smoke-20261031.json")
        self.assertTrue(ev["acceptance"]["fullEphemeralInit"])
        self.assertTrue(ev["acceptance"]["freshStateDetectedWithoutFabrication"])
        self.assertTrue(ev["acceptance"]["releaseVsMainDriftDetected"])
        self.assertNotEqual(ev["releaseGitHead"], ev["observedMain"])
        self.assertIn("Unknown option", ev["currentnessCounterexample"]["executedNegativeProbe"])

    def test_reactive_resume_reuses_upstream_plugin_and_preserves_auth_boundary(self) -> None:
        ev = load(CAREER / "reactive-resume-mcp-boundary-20261031.json")
        self.assertEqual(ev["stableRelease"]["tag"], "v6.0.9")
        self.assertEqual(ev["stableRelease"]["gitCommit"], "854459a44eb896ca185611bf669a65be4d5111cf")
        self.assertTrue(ev["acceptance"]["stableReleaseLatestAtObservation"])
        self.assertTrue(ev["acceptance"]["stableReleasePluginSchemasValid"])
        self.assertEqual(ev["adoptionRule"]["wrapperDecision"], "REUSE_UPSTREAM_NATIVE_PLUGIN_NO_ORDIVON_WRAPPER")
        self.assertEqual(ev["hostedBoundaryProbe"]["httpStatus"], 401)
        self.assertTrue(ev["acceptance"]["currentPluginSchemasValid"])
        self.assertTrue(ev["acceptance"]["authBoundaryObserved"])

    def test_provider_overlap_falsification_preserves_only_unique_roles(self) -> None:
        ev = load(CAREER / "provider-overlap-falsification-20261101.json")
        self.assertEqual(ev["reactiveResume"]["stableRelease"], "v6.0.9")
        self.assertEqual(
            ev["jobSyncOverlap"]["decision"],
            "KEEP_METHOD_DONOR_REJECT_PARALLEL_TRACKER_PRODUCT",
        )
        self.assertIn("scheduled Greenhouse discovery", ev["jobSyncOverlap"]["uniqueRetainedMethods"])
        self.assertEqual(
            ev["resumeMatcherOverlap"]["decision"],
            "KEEP_NARROW_PRESERVATION_VERIFIER",
        )
        self.assertFalse(ev["resumeMatcherOverlap"]["equivalentReactiveResumeNamedToolObserved"])
        self.assertEqual(ev["lowerStarSearch"]["conclusionState"], "UNKNOWN")
        self.assertEqual(ev["correction"]["priorReactiveResumeStableChannel"], "v6.0.2")
        self.assertEqual(ev["correction"]["correctedStableChannel"], "v6.0.9")

    def test_official_ats_to_gap_slice_keeps_diagnostics_bounded(self) -> None:
        ev = load(CAREER / "cloudflare-8245211-career-ops-vertical-slice-20261031.json")
        self.assertEqual(ev["providerBindings"]["opportunityIntake"]["provider"], "Greenhouse official Job Board API")
        self.assertTrue(ev["syntheticCandidate"])
        self.assertGreater(len(ev["extractedSkills"]), 0)
        self.assertGreaterEqual(ev["coverage"]["coveragePct"], 0)
        self.assertLessEqual(ev["coverage"]["coveragePct"], 100)
        self.assertIn("not employer eligibility", ev["truthBoundary"])

    def test_resume_matcher_stable_runtime_and_artifact_preservation(self) -> None:
        smoke = load(CAREER / "resume-matcher-1.4.0-provider-smoke-20261101.json")
        self.assertTrue(smoke["acceptance"]["defaultHostPythonRejected"])
        self.assertTrue(smoke["acceptance"]["python313CliStarts"])
        self.assertEqual(smoke["getStatus"]["value"]["backend"], "sqlite")
        self.assertIn("create_application", smoke["adoptionBoundary"]["excludedInitialTools"])

        ev = load(CAREER / "resume-matcher-1.4.0-artifact-compiler-slice-20261101.json")
        self.assertTrue(ev["acceptance"]["canonicalMasterReadBack"])
        self.assertTrue(ev["acceptance"]["positiveTailoredDraftAccepted"])
        self.assertTrue(ev["acceptance"]["factMutationRejected"])
        self.assertFalse(ev["acceptance"]["applicationCrudUsed"])
        self.assertTrue(ev["positivePreservationCheck"]["valid"])
        self.assertFalse(ev["negativePreservationCheck"]["valid"])
        self.assertTrue(any("education.identity" in x for x in ev["negativePreservationCheck"]["violations"]))
        self.assertIn("not hiring probability", ev["truthBoundary"])


if __name__ == "__main__":
    unittest.main()
