"""Fail-closed source identity checks for frozen cross-repository name collisions.

This verifies a versioned evidence *structure*, not live consumer closure,
LEGO semantic identity, source repository installations, or proof reuse.
"""
from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs/architecture/evidence"
CROSSWALK = EVIDENCE / "PHASE1_CROSSREPO_SOURCE_NAME_CONFLICTS_20261027_R1.json"
PARENT = EVIDENCE / "PHASE1_FINE_MULTIREPO_SOURCE_TAXONOMY_20261027_R1.json"
SHA = re.compile(r"[0-9a-f]{40}\Z")


def check(doc: dict, parent: dict) -> tuple[int, int]:
    assert doc["kind"] == "ordivon.phase1-cross-repository-path-name-collision-audit"
    assert doc["truthRole"] == "PINNED_GIT_TREE_PATH_AND_BLOB_DIFFERENCE_ONLY"
    assert doc["machineAdmissibilityBoundary"]["SAME_FUNCTION"] == "UNKNOWN"
    assert doc["machineAdmissibilityBoundary"]["ACTUAL_CONSUMER"] == "UNKNOWN"
    assert doc["machineAdmissibilityBoundary"]["INSTALLED_CURRENTNESS"] == "UNKNOWN"
    assert doc["machineAdmissibilityBoundary"]["PERMISSION_TO_DELETE_OR_MERGE"] == "NO"
    originals = {r["sourceRepoName"]: r for r in parent["nestedAreas"]}
    pinned = {r["repo"]: r for r in doc["pinnedRepositories"]}
    assert len(pinned) == len(originals) == 9
    for name, original in originals.items():
        pin = pinned[name]
        assert pin["commit"] == original["sourceCut"]
        assert pin["tree"] == original["tree"]
        assert pin["tracked"] == original["count"]
        assert SHA.fullmatch(pin["commit"])
        assert SHA.fullmatch(pin["tree"])
    records = doc["nameConflictRows"]
    assert len(records) == 84
    assert len({r["relativePath"] for r in records}) == len(records)
    assert doc["counts"]["samePathDifferentBlobAliases"] == len(records)
    assert doc["counts"]["sameRelativePathsAcrossRepos"] == 2649
    assert doc["counts"]["identicalBlobAliases"] == 2565
    assert doc["counts"]["trackedSourcePathEntries"] == sum(x["count"] for x in originals.values()) == 14209
    assert doc["counts"]["unqualifiedCarrierRoleHints"] == 0
    role_counts = {}
    for row in records:
        path = row["relativePath"]
        assert path and not path.startswith("/") and "\\" not in path
        assert all(x not in ("", ".", "..") for x in path.split("/"))
        assert row["consumerOrReplacementEquivalence"] == "UNKNOWN_NOT_INFERRED"
        assert row["productionOrLatestVersion"] == "UNKNOWN_NOT_INFERRED_FROM_REPOSITORY_NAME"
        assert row["sameNameDifferentGitBytes"] is True
        assert row["proposedRoleSpecificName"]
        versions = row["versions"]
        assert len(versions) >= 2
        assert len({v["repo"] for v in versions}) == len(versions)
        assert row["distinctContentOids"] == len({v["blobOid"] for v in versions}) > 1
        for v in versions:
            assert v["repo"] in pinned
            assert v["commit"] == pinned[v["repo"]]["commit"]
            assert SHA.fullmatch(v["blobOid"])
            assert v["agentReadableSourceId"] == f'git:{v["repo"]}@{v["commit"]}:{path}'
            assert v["sourceIdentityStanding"] == "GIT_TREE_OBJECT_OBSERVED_ONLY"
        role_counts[row["sourceRoleHint"]] = role_counts.get(row["sourceRoleHint"], 0) + 1
    assert dict(sorted(role_counts.items())) == doc["conflictKinds"]
    observed = doc["boundedSamePathCurrentnessCheck"]["perRepository"]
    assert {x["repo"] for x in observed} == set(originals)
    assert sum(x["pinnedConflictingPathOccurrences"] for x in observed) == sum(len(x["versions"]) for x in records)
    for item in observed:
        assert item["baselineCut"] == pinned[item["repo"]]["commit"]
        assert SHA.fullmatch(item["observedComparisonCut"])
        assert sum(item["sourceCurrentnessCounts"].values()) == item["pinnedConflictingPathOccurrences"]
        assert all(x["standing"] in ("CHANGED_GIT_OBJECT", "ABSENT_FROM_OBSERVED_CUT")
                   for x in item["objectChangedOrAbsentAtComparison"])
        assert len(item["objectChangedOrAbsentAtComparison"]) == (
            item["sourceCurrentnessCounts"].get("CHANGED_GIT_OBJECT", 0)
            + item["sourceCurrentnessCounts"].get("ABSENT_FROM_OBSERVED_CUT", 0)
        )
    return len(records), len(pinned)


class CrossRepoNameConflictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(CROSSWALK.read_text())
        cls.parent = json.loads(PARENT.read_text())

    def test_all_84_conflicts_remain_source_qualified(self):
        self.assertEqual(check(self.doc, self.parent), (84, 9))

    def test_undeclared_equivalence_must_fail(self):
        bad = copy.deepcopy(self.doc)
        bad["nameConflictRows"][0]["consumerOrReplacementEquivalence"] = "EQUIVALENT"
        with self.assertRaises(AssertionError):
            check(bad, self.parent)

    def test_dropped_repository_identity_must_fail(self):
        bad = copy.deepcopy(self.doc)
        row = bad["nameConflictRows"][0]
        row["versions"][1]["repo"] = row["versions"][0]["repo"]
        with self.assertRaises(AssertionError):
            check(bad, self.parent)

    def test_stale_or_forged_commit_must_fail(self):
        bad = copy.deepcopy(self.doc)
        bad["nameConflictRows"][0]["versions"][0]["commit"] = "0"*40
        with self.assertRaises(AssertionError):
            check(bad, self.parent)

    def test_collapsed_blob_difference_must_fail(self):
        bad = copy.deepcopy(self.doc)
        row = bad["nameConflictRows"][0]
        for version in row["versions"]:
            version["blobOid"] = "0"*40
        row["distinctContentOids"] = 1
        with self.assertRaises(AssertionError):
            check(bad, self.parent)

    def test_traversal_is_not_a_source_path(self):
        bad = copy.deepcopy(self.doc)
        bad["nameConflictRows"][0]["relativePath"] = "../unsafe"
        with self.assertRaises(AssertionError):
            check(bad, self.parent)

    def test_installed_upgrade_is_not_admitted(self):
        bad = copy.deepcopy(self.doc)
        bad["machineAdmissibilityBoundary"]["INSTALLED_CURRENTNESS"] = "VERIFIED"
        with self.assertRaises(AssertionError):
            check(bad, self.parent)


if __name__ == "__main__":
    unittest.main()
