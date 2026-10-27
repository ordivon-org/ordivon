"""Bounded exact-source Research-v2 Phase 1 navigation ledger regression.

This reconstructs two exact Git path->blob projections from embedded evidence,
not a proof of consumer, installed, external-effect, or scientific semantics.
"""
from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

FILE = (
    Path(__file__).resolve().parents[2]
    / "docs/architecture/evidence/PHASE1_RESEARCH_V2_CURRENT_SOURCE_CELLS_20261027_R1.json"
)
CURRENT_CUT = "098c623d9c38a2fffcf620242f35577d7c827b69"


def ledger_digest(data: dict[str, tuple[str, str]]) -> str:
    b = b"".join((p + "\0" + mode + "\0" + oid + "\n").encode() for p, (mode, oid) in sorted(data.items()))
    return hashlib.sha256(b).hexdigest()


def qualified_source_overlay(d: dict) -> dict:
    assert d["kind"] == "ordivon.phase1-research-v2-live-sourcecut-cells"
    assert d["scope"] == "CURRENT_LINUX_REPOSITORY_GIT_TREE_NOT_WORKTREE_OR_INSTALLED_RUNTIME"
    assert d["sourceCut"] == CURRENT_CUT
    assert len(d["sourceTree"]) == len(d["frozenCompareTree"]) == 40
    assert d["consumerCoverage"] == d["installedCurrentness"] == "UNKNOWN"
    assert d["implementationProof"] == "NOT_PERFORMED"
    paths, groups = {}, set()
    statuses = {"ADDED": set(), "MODIFIED": set(), "UNCHANGED": set()}
    dense = []
    for cell in d["sourceCells"]:
        label, prefix = cell["sourceCell"], cell["physicalPrefix"]
        assert label not in groups and label.startswith("research_v2.")
        groups.add(label)
        assert cell["standing"] == "SOURCE_ONLY_NAVIGATION_NOT_CONSUMER_PROOF"
        assert cell["memberCount"] == len(cell["members"]) > 0
        assert cell["densityStatus"] in ("DIRECT_FILE_HOTSPOT", "BOUNDED_SOURCE_GROUP")
        assert cell["roleSet"] == sorted({x["sourceRole"] for x in cell["members"]})
        if cell["densityStatus"] == "DIRECT_FILE_HOTSPOT":
            assert len(cell["members"]) > 64
            assert all("/" not in x["path"][len(prefix)+1:] for x in cell["members"])
            dense.append({"prefix": prefix, "count": len(cell["members"])})
        else:
            assert len(cell["members"]) <= 64
        for x in cell["members"]:
            p = x["path"]
            assert p not in paths and not p.startswith("/") and "\\" not in p
            assert all(t not in ("", ".", "..") for t in p.split("/"))
            assert len(x["blob"]) == 40
            assert x["mode"] in ("100644", "100755", "120000")
            assert x["sourceRole"] != "UNQUALIFIED_SOURCE_PURPOSE"
            assert x["changeFromFrozen"] in statuses
            if prefix == "@root":
                assert "/" not in p
            else:
                assert p.startswith(prefix + "/")
            paths[p] = (x["mode"], x["blob"])
            statuses[x["changeFromFrozen"]].add(p)
    assert d["denseFlatCells"] == dense
    assert d["currentTreePathBlobDigest"] == ledger_digest(paths)
    removed = d["removedFromCurrentTree"]
    added = d["newlyAddedSourcePaths"]
    changed = d["changedGitBlobs"]
    assert len({x["path"] for x in removed}) == len(removed)
    assert len({x["path"] for x in added}) == len(added)
    assert len({x["path"] for x in changed}) == len(changed)
    assert {x["path"] for x in added} == statuses["ADDED"]
    assert {x["path"] for x in changed} == statuses["MODIFIED"]
    assert not any(x["path"] in paths for x in removed)
    prior = {p: paths[p] for p in statuses["UNCHANGED"]}
    for row in removed:
        assert row["currentBlob"] is None and row["currentMode"] is None
        assert len(row["priorBlob"]) == 40 and row["priorMode"] in ("100644", "100755", "120000")
        prior[row["path"]] = (row["priorMode"], row["priorBlob"])
    for row in changed:
        assert row["path"] in paths and row["path"] in statuses["MODIFIED"]
        assert row["currentBlob"] == paths[row["path"]][1]
        assert row["currentMode"] == paths[row["path"]][0]
        assert len(row["priorBlob"]) == 40 and row["priorMode"] in ("100644", "100755", "120000")
        assert (row["priorMode"], row["priorBlob"]) != paths[row["path"]]
        prior[row["path"]] = (row["priorMode"], row["priorBlob"])
    for row in added:
        assert row["priorBlob"] is None and row["priorMode"] is None
        assert row["currentBlob"] == paths[row["path"]][1]
        assert row["currentMode"] == paths[row["path"]][0]
    assert d["priorTreePathBlobDigest"] == ledger_digest(prior)
    assert len(prior) == 3000
    expected = d["counts"]
    assert expected == {
        "priorTracked": 3000, "currentTracked": 2904,
        "added": 23, "removed": 119, "modified": 21, "unchanged": 2860,
        "sourceCells": 267, "denseFlatCells": 6,
        "unknownPhysicalSourcePaths": 0, "duplicateSourcePaths": 0,
    }
    assert len(paths) == expected["currentTracked"]
    assert len(statuses["UNCHANGED"]) == expected["unchanged"]
    assert len(statuses["ADDED"]) == expected["added"]
    assert len(statuses["MODIFIED"]) == expected["modified"]
    assert len(removed) == expected["removed"]
    return expected


class ResearchV2CurrentSourceCellsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(FILE.read_text())

    def test_exact_current_git_path_and_blob_partition(self):
        self.assertEqual(qualified_source_overlay(self.evidence)["sourceCells"], 267)

    def test_unchanged_git_blob_tamper_rejected(self):
        d = copy.deepcopy(self.evidence)
        d["sourceCells"][0]["members"][0]["blob"] = "0" * 40
        with self.assertRaises(AssertionError):
            qualified_source_overlay(d)

    def test_duplicate_source_path_rejected(self):
        d = copy.deepcopy(self.evidence)
        d["sourceCells"][0]["members"].append(copy.deepcopy(d["sourceCells"][0]["members"][0]))
        with self.assertRaises(AssertionError):
            qualified_source_overlay(d)

    def test_source_cut_drift_rejected(self):
        d = copy.deepcopy(self.evidence)
        d["sourceCut"] = "0" * 40
        with self.assertRaises(AssertionError):
            qualified_source_overlay(d)

    def test_installed_or_consumer_authority_cannot_be_inferred(self):
        d = copy.deepcopy(self.evidence)
        d["installedCurrentness"] = "PROVEN"
        with self.assertRaises(AssertionError):
            qualified_source_overlay(d)

    def test_removed_paper_build_scripts_are_not_current(self):
        self.assertTrue({
            "dogfood/first_paper_r2/artifact_r2/build_r2_artifact.py",
            "dogfood/first_paper_r2/validate_exposure.py",
        }.issubset({r["path"] for r in self.evidence["removedFromCurrentTree"]}))
        qualified_source_overlay(self.evidence)

    def test_flat_hotspots_remain_visible(self):
        d = copy.deepcopy(self.evidence)
        d["denseFlatCells"] = []
        with self.assertRaises(AssertionError):
            qualified_source_overlay(d)

    def test_path_escape_fails_closed(self):
        d = copy.deepcopy(self.evidence)
        d["sourceCells"][0]["members"][0]["path"] = "../bad"
        with self.assertRaises(AssertionError):
            qualified_source_overlay(d)


if __name__ == "__main__":
    unittest.main()
