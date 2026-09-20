from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from ordivon_studio.production_context import build_production_context

ROOT = Path(__file__).resolve().parents[1]


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def _write_fixture(production_root: Path, *, revision: str) -> None:
    production_root.mkdir(parents=True, exist_ok=True)
    (production_root / "claims.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "productionId": "fixture-production",
                "claims": [
                    {
                        "id": "fixture-claim",
                        "source": {"binding": "runtime", "path": "README.md#purpose"},
                        "meaning": "One bounded test claim.",
                        "evidence": ["README.md#purpose"],
                        "avoid": ["stronger claim"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (production_root / "production.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "id": "fixture-production",
                "title": "Fixture Production",
                "status": "review",
                "intent": "Test the read-only production projection.",
                "audiences": ["agent"],
                "sourceBindings": [
                    {
                        "id": "runtime",
                        "repository": "https://example.invalid/runtime.git",
                        "revision": revision,
                        "role": "source-facts",
                    }
                ],
                "workingProfile": {},
                "sources": {"claims": "claims.json"},
                "outputs": [
                    {
                        "id": "fixture-output",
                        "kind": "image",
                        "status": "rendered",
                        "blobDigest": "sha256:" + "1" * 64,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


class ProductionContextTests(unittest.TestCase):
    def test_runtime_introduction_projects_without_claiming_source_currentness(self) -> None:
        context = build_production_context(ROOT / "productions/runtime-introduction")
        self.assertEqual(context["kind"], "ordivon.studio.production-context")
        self.assertEqual(context["truthRole"], "derived-read-only-projection")
        self.assertEqual(context["production"]["id"], "runtime-introduction")
        self.assertEqual(context["production"]["status"], "review")
        self.assertGreater(context["claims"]["count"], 0)
        rendered = next(item for item in context["outputs"] if item["id"] == "runtime-film-en-landscape")
        self.assertEqual(rendered["status"], "rendered")
        self.assertTrue(rendered["blobDigest"].startswith("sha256:"))
        currentness = context["sourceBindingCurrentness"]
        self.assertFalse(currentness["allBindingsRevalidated"])
        self.assertEqual(currentness["semanticApplicability"], "not-evaluated")
        observation = currentness["observations"][0]
        self.assertFalse(observation["revalidated"])
        self.assertEqual(observation["relation"], "unverified")

    def test_git_relation_never_becomes_semantic_applicability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_repo = root / "source"
            source_repo.mkdir()
            subprocess.check_call(["git", "-C", str(source_repo), "init", "-q"])
            subprocess.check_call(["git", "-C", str(source_repo), "config", "user.email", "test@ordivon.local"])
            subprocess.check_call(["git", "-C", str(source_repo), "config", "user.name", "Ordivon Test"])
            (source_repo / "README.md").write_text("v1\n", encoding="utf-8")
            subprocess.check_call(["git", "-C", str(source_repo), "add", "README.md"])
            subprocess.check_call(["git", "-C", str(source_repo), "commit", "-qm", "v1"])
            bound_revision = _git(source_repo, "rev-parse", "HEAD")

            production_root = root / "production"
            _write_fixture(production_root, revision=bound_revision)
            first = build_production_context(
                production_root,
                source_repositories={"runtime": source_repo},
            )
            first_observation = first["sourceBindingCurrentness"]["observations"][0]
            self.assertTrue(first_observation["revalidated"])
            self.assertEqual(first_observation["relation"], "head-matches-binding")
            self.assertEqual(first_observation["semanticApplicability"], "not-evaluated")

            (source_repo / "README.md").write_text("v2\n", encoding="utf-8")
            subprocess.check_call(["git", "-C", str(source_repo), "add", "README.md"])
            subprocess.check_call(["git", "-C", str(source_repo), "commit", "-qm", "v2"])
            second = build_production_context(
                production_root,
                source_repositories={"runtime": source_repo},
            )
            second_observation = second["sourceBindingCurrentness"]["observations"][0]
            self.assertEqual(second_observation["relation"], "head-differs-from-binding")
            self.assertEqual(second_observation["boundRevision"], bound_revision)
            self.assertTrue(second_observation["revisionPresent"])
            self.assertEqual(second_observation["semanticApplicability"], "not-evaluated")

    def test_unknown_source_binding_mapping_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown binding"):
            build_production_context(
                ROOT / "productions/runtime-introduction",
                source_repositories={"not-a-binding": ROOT},
            )


if __name__ == "__main__":
    unittest.main()
