"""Phase 1 exact-source Git object store topology and Media mirror guard.

Deliberately avoids replicating 510 identical Git entries: the exact Git cuts are
the source, the digest is a reproducible observation of their projection. This
test validates a bounded metadata ledger, not operational consumer absence.
"""
import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "docs/architecture/evidence/PHASE1_EXTERNAL_GIT_ROOT_AND_MEDIA_MIRROR_20261028_R1.json"

def source_partition(d):
    assert d["kind"] == "ordivon.phase1.external_git_views_and_media_mirror_sourcecut"
    assert d["truthScope"] == "GIT_SOURCE_ONLY_NO_CONSUMER_OR_INSTALLATION_CLOSURE"
    assert d["mathProofStanding"] == "NOT_FORMALIZED_SOURCE_IDENTITY_ONLY"
    t=d["sourceTopology"];v=t["views"]
    assert t["observedWorkingDirectories"]==len(v)==9
    assert t["distinctGitObjectStores"]==7 and t["linkedWorktreeViews"]==2
    assert t["configuredOriginViews"]==2
    assert len(t["groupsByGitObjectStore"])==7
    ids=[x["sourceRootLabel"] for x in v]
    assert len(set(ids))==9
    assert sorted(y for group in t["groupsByGitObjectStore"] for y in group)==sorted(ids)
    assert all(re.fullmatch(r"[a-z0-9_-]+",n) for n in ids)
    assert all(re.fullmatch(r"[0-9a-f]{40}",x["sourceGitCut"]) for x in v)
    assert all(re.fullmatch(r"[0-9a-f]{40}",x["sourceTree"]) for x in v)
    assert all(x["sourceScope"]=="GIT_VERSION_ONLY_NOT_INSTALLED_LEGO" for x in v)
    assert sum(x["sourceViewKind"]=="LINKED_GIT_WORKTREE_VIEW" for x in v)==2
    assert sorted(x["sourceRootLabel"] for x in v if x["sourceViewKind"]=="LINKED_GIT_WORKTREE_VIEW") == sorted(
        ["ordivon-paper1-emse-r3-frozen","ordivon-paper1-r25-reviewer-risk-closure-20260922"])
    assert sum(x["sourceRemoteClass"]=="CONFIGURED_ORIGIN" for x in v)==2
    assert d["compressionPolicy"].startswith("Do not repeat all 510")
    m=d["mediaMirror"]
    assert m["mainMediaPrefix"]=="capabilities/media/"
    assert m["actualConsumerScope"]=="UNKNOWN_STATIC_REFERENCES_DO_NOT_PROVE_COMPLETE_RUNTIME"
    assert m["sourceDeleteStanding"]=="NO_AUTOMATIC_DELETE_WHILE_SOURCE_OF_TRUTH_AND_EFFECTS_UNQUALIFIED"
    assert m["equalMirrorLedgerStanding"]=="EXACT_BLOB_DIGEST_REPLAY_REQUIRED_FROM_TWO_PINNED_GIT_TREES"
    assert m["mainGitCut"]==next(x["sourceGitCut"] for x in v if x["sourceRootLabel"]=="ordivon")
    assert m["externalMediaGitCut"]==next(x["sourceGitCut"] for x in v if x["sourceRootLabel"]=="ordivon-media")
    c=m["exactPathCounts"]
    assert c=={"main":582,"media":550,"identical":510,"divergent":39,"mainOnly":33,"externalOnly":1}
    assert "identical" not in m
    assert re.fullmatch(r"[0-9a-f]{64}",m["identicalBlobProjectionSha256"])
    assert re.fullmatch(r"[0-9a-f]{64}",m["partitionIdentitySha256"])
    assert all(len(m[k])==c[k] for k in ("divergent","mainOnly","externalOnly"))
    def check_entry(path,mode,blob):
        assert path and not path.startswith("/") and "\\" not in path
        assert all(piece not in ("",".","..") for piece in path.split("/"))
        assert mode in ("100644","100755","120000")
        assert re.fullmatch(r"[0-9a-f]{40}",blob)
    used=set()
    for x in m["divergent"]:
        path=x["relativePath"]
        check_entry(path,x["mainMode"],x["mainBlob"])
        check_entry(path,x["mediaMode"],x["mediaBlob"])
        assert (x["mainMode"],x["mainBlob"])!=(x["mediaMode"],x["mediaBlob"])
        assert path not in used
        used.add(path)
    for name,side in (("mainOnly","main"),("externalOnly","media")):
        for x in m[name]:
            path=x["relativePath"]
            check_entry(path,x[side+"Mode"],x[side+"Blob"])
            assert path not in used
            used.add(path)
    assert c["main"]==c["identical"]+c["divergent"]+c["mainOnly"]
    assert c["media"]==c["identical"]+c["divergent"]+c["externalOnly"]
    for x in m["identicalSample"]:
        check_entry(x["relativePath"],x["mode"],x["gitBlob"])
        assert x["relativePath"] not in used
    assert len({x["relativePath"] for x in m["identicalSample"]})==len(m["identicalSample"])
    assert any(x["evidenceClass"]=="PINNED_MAIN_GIT_SOURCE_STATIC_IMPORT" for x in d["knownStaticConsumerBoundaryExamples"])
    assert all(x["evidenceClass"] in ("PINNED_MAIN_GIT_SOURCE_STATIC_IMPORT","SOURCE_DECLARED_EXECUTABLE_NOT_INSTALLED") for x in d["knownStaticConsumerBoundaryExamples"])
    return c

class MediaMirrorSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(SOURCE.read_text())

    def test_source_topology_and_divergence(self):
        self.assertEqual(source_partition(self.d)["divergent"],39)

    def test_mislabeled_worktree_rejected(self):
        d=copy.deepcopy(self.d)
        next(x for x in d["sourceTopology"]["views"] if x["sourceRootLabel"]=="ordivon-media")["sourceViewKind"]="LINKED_GIT_WORKTREE_VIEW"
        with self.assertRaises(AssertionError):source_partition(d)

    def test_divergent_cannot_be_called_equal(self):
        d=copy.deepcopy(self.d)
        p=d["mediaMirror"]["divergent"][0]
        p["mediaBlob"]=p["mainBlob"]
        p["mediaMode"]=p["mainMode"]
        with self.assertRaises(AssertionError):source_partition(d)

    def test_path_escape_rejected(self):
        d=copy.deepcopy(self.d)
        d["mediaMirror"]["mainOnly"][0]["relativePath"]="../escape"
        with self.assertRaises(AssertionError):source_partition(d)

    def test_double_counted_source_rejected(self):
        d=copy.deepcopy(self.d)
        d["mediaMirror"]["mainOnly"][0]["relativePath"]=d["mediaMirror"]["divergent"][0]["relativePath"]
        with self.assertRaises(AssertionError):source_partition(d)

    def test_source_unknown_cannot_become_safe_to_delete(self):
        d=copy.deepcopy(self.d)
        d["mediaMirror"]["sourceDeleteStanding"]="SAFE_TO_DELETE"
        with self.assertRaises(AssertionError):source_partition(d)

    def test_current_cut_forgery_fails(self):
        d=copy.deepcopy(self.d)
        d["sourceTopology"]["views"][0]["sourceGitCut"]="0"*40
        with self.assertRaises(AssertionError):source_partition(d)

    def test_malformed_equal_blob_digest_fails(self):
        d=copy.deepcopy(self.d)
        d["mediaMirror"]["identicalBlobProjectionSha256"]="not-a-digest"
        with self.assertRaises(AssertionError):source_partition(d)

if __name__=="__main__":
    unittest.main()
