from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
EVIDENCE = ROOT / "evidence" / "ai-redteam-foundry-r1-evidence.json"


def digest_bytes(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def current_manifest() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        parts = Path(rel).parts
        if "__pycache__" in parts or rel.startswith("evidence/") or path.suffix == ".pyc":
            continue
        data = path.read_bytes()
        entries.append({"path": rel, "sha256": digest_bytes(data), "byteLength": len(data)})
    return entries


class EvidenceBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = json.loads(EVIDENCE.read_text())

    def test_bundle_digest_recomputes_exactly(self) -> None:
        claimed = self.bundle["bundleDigest"]
        unsigned = dict(self.bundle)
        del unsigned["bundleDigest"]
        self.assertEqual(claimed, digest_bytes(canonical_bytes(unsigned)))

    def test_study_tree_manifest_matches_current_bytes(self) -> None:
        manifest = current_manifest()
        self.assertEqual(self.bundle["studyTreeManifest"], manifest)
        self.assertEqual(self.bundle["studyTreeDigest"], digest_bytes(canonical_bytes(manifest)))

    def test_bundle_source_revision_remains_reachable_from_current_head(self) -> None:
        head = subprocess.check_output(["/usr/bin/git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
        source_revision = self.bundle["sourceRevision"]
        result = subprocess.run(
            ["/usr/bin/git", "merge-base", "--is-ancestor", source_revision, head],
            cwd=REPO_ROOT,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            "evidence-producing sourceRevision must remain reachable from the current integrated history",
        )

    def test_bundle_does_not_claim_production_security_standing(self) -> None:
        self.assertEqual(
            self.bundle["standing"],
            "EXPERIMENTAL_STUDY_EVIDENCE_NOT_PRODUCTION_SECURITY_STANDING",
        )
        joined = " ".join(self.bundle["limitations"])
        self.assertIn("does not prove universal model robustness", joined)


if __name__ == "__main__":
    unittest.main()
