"""Exact-source, fail-closed Phase 1 peer-composable research/eval names."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[2] / "docs/architecture/evidence"
PARENT = EVIDENCE / "PHASE1_FINE_MULTIREPO_SOURCE_TAXONOMY_20261027_R1.json"
ADDENDUM = EVIDENCE / "PHASE1_CROSSREPO_AGENT_SOURCE_NAMES_20261027_R2.json"


def check(doc: dict, parent: dict) -> dict[str, int]:
    assert doc["sourceTruthRole"] == "GIT_SOURCE_LAYOUT_ONLY_NOT_AGENT_OWNER_OR_RUNNING_LEGO"
    assert doc["proofAndEffectStatus"] == "UNKNOWN_NOT_PROVED"
    assert doc["baseEvidenceHead"] == "92bd659dbf404d00847ae388b5defe7e5578278c"
    assert set(doc["scopeNonOverlap"]) == {
        "ordivon-media (peer agent working on it)",
        "ordivon-sts2mcp (peer agent working on it)",
        "ordivon.monorepo (PR948/983/989 and other peers)",
    }
    roots = {r["sourceRepoName"]: r for r in parent["nestedAreas"][1:]}
    unknown = parent["unqualifiedPathCarrierEvidence"]["allUnknownRoleGitBlobObservations"]
    keys = {(o["sourceRepo"], o["sourceSection"], o["sourcePath"]): o for o in unknown}
    names = set()
    visited = set()
    counters = {"independentGitRoots": 0, "newlyNamedSourceCells": 0,
                "legacyUnqualifiedCarrierObservations": 0,
                "allMemberPathsInTheseCells": 0}
    for r in doc["evidenceGroups"]:
        repo = r["repository"]
        assert repo in roots and repo not in visited
        assert repo not in {"ordivon-media", "ordivon-sts2mcp", "ordivon"}
        visited.add(repo)
        source = roots[repo]
        assert r["exactGitSourceCut"] == source["sourceCut"]
        assert re.fullmatch(r"[0-9a-f]{40}", r["gitTree"])
        assert r["sourceOnlyStanding"] == "DERIVED_GIT_TREE_SOURCE_PROPOSAL_NOT_CONSUMER"
        sections = {g["sectionPathKey"]: g for g in source["sourceGroups"]
                    if g["observedLayoutRoles"].get("PATH_ROLE_UNQUALIFIED", 0)}
        actual_sections = set()
        counters["independentGitRoots"] += 1
        for g in r["sourceCells"]:
            section = g["sourceSection"]
            assert section in sections and section not in actual_sections
            actual_sections.add(section)
            name = g["agentSemanticSourceCell"]
            assert re.fullmatch(r"[a-z][a-z0-9_.]*", name) and name not in names
            names.add(name)
            assert g["semanticRoleEvidence"] == "PROPOSED_FROM_SECTION_AND_EXACT_FILE_NAMES_NOT_CONSUMER_PROOF"
            assert g["selectionDefinition"] == "EXACT_REPO_GIT_CUT_PLUS_SOURCE_SECTION_FROM_PARENT_MANIFEST"
            assert g["dynamicConsumer"] == g["installedCurrentness"] == "UNKNOWN"
            assert g["proofStanding"] == "NOT_PROVED"
            base = sections[section]
            assert g["observedMemberCount"] == base["trackedPaths"]
            assert g["legacyUnknownCarrierCount"] == base["observedLayoutRoles"]["PATH_ROLE_UNQUALIFIED"]
            blobs = g["priorUnqualifiedBlobKeys"]
            assert len(blobs) == g["legacyUnknownCarrierCount"]
            assert [x["sourcePath"] for x in blobs] == sorted(x["sourcePath"] for x in blobs)
            for x in blobs:
                path = x["sourcePath"]
                assert not path.startswith("/") and "\\" not in path
                assert path and all(part not in ("", ".", "..") for part in path.split("/"))
                assert re.fullmatch(r"[0-9a-f]{40}", x["gitBlob"])
                peer = keys[(repo, section, path)]
                assert x["gitBlob"] == peer["gitBlob"]
                assert x["carrierKind"] == peer["carrierKind"]
            counters["newlyNamedSourceCells"] += 1
            counters["legacyUnqualifiedCarrierObservations"] += len(blobs)
            counters["allMemberPathsInTheseCells"] += g["observedMemberCount"]
        assert actual_sections == set(sections)
    assert visited == set(roots) - {"ordivon-media", "ordivon-sts2mcp"}
    assert counters == doc["counts"]
    assert counters == {"independentGitRoots": 6, "newlyNamedSourceCells": 19,
                        "legacyUnqualifiedCarrierObservations": 36,
                        "allMemberPathsInTheseCells": 46}
    return counters


class Phase1CrossRepositorySourceNamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = json.loads(PARENT.read_text())
        cls.doc = json.loads(ADDENDUM.read_text())

    def test_19_cells_have_exact_git_blob_witnesses(self):
        self.assertEqual(check(self.doc, self.parent)["newlyNamedSourceCells"], 19)

    def test_unknown_cannot_become_installed_without_evidence(self):
        doc = json.loads(json.dumps(self.doc))
        doc["evidenceGroups"][0]["sourceCells"][0]["installedCurrentness"] = "PROVEN"
        with self.assertRaises(AssertionError):
            check(doc, self.parent)

    def test_cross_repository_alias_cannot_replace_exact_blob(self):
        doc = json.loads(json.dumps(self.doc))
        doc["evidenceGroups"][0]["sourceCells"][0]["priorUnqualifiedBlobKeys"][0]["gitBlob"] = "0"*40
        with self.assertRaises(AssertionError):
            check(doc, self.parent)

    def test_duplicate_cell_name_is_rejected(self):
        doc = json.loads(json.dumps(self.doc))
        doc["evidenceGroups"][1]["sourceCells"][0]["agentSemanticSourceCell"] = doc["evidenceGroups"][0]["sourceCells"][0]["agentSemanticSourceCell"]
        with self.assertRaises(AssertionError):
            check(doc, self.parent)

    def test_stale_repository_revision_rejected(self):
        doc = json.loads(json.dumps(self.doc))
        doc["evidenceGroups"][0]["exactGitSourceCut"] = "0"*40
        with self.assertRaises(AssertionError):
            check(doc, self.parent)

    def test_physical_path_escape_rejected(self):
        doc = json.loads(json.dumps(self.doc))
        doc["evidenceGroups"][0]["sourceCells"][0]["priorUnqualifiedBlobKeys"][0]["sourcePath"] = "../unsafe"
        with self.assertRaises(AssertionError):
            check(doc, self.parent)


if __name__ == "__main__":
    unittest.main()
