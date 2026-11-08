from __future__ import annotations

import hashlib
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

    def test_real_approved_article_binds_exact_source_carrier_bytes(self) -> None:
        context = build_production_context(ROOT / "productions/browser-perception-note")
        self.assertEqual(context["production"]["status"], "review")
        self.assertEqual(context["outputs"][0]["status"], "approved")
        evidence = context["outputByteIdentity"]
        observed = evidence["observations"][0]
        self.assertEqual(observed["sourceSelection"], "declared-exact-source-carrier")
        self.assertEqual(observed["relation"], "MATCHES_DECLARED_DIGEST")
        self.assertEqual(observed["expectedBlobDigest"], observed["observedBlob"]["digest"])
        self.assertEqual(
            context["inputManifestIdentity"]["productionManifestSha256"],
            "sha256:" + hashlib.sha256(
                (ROOT / "productions/browser-perception-note/production.json").read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            context["inputManifestIdentity"]["claimsManifestSha256"],
            "sha256:" + hashlib.sha256(
                (ROOT / "productions/browser-perception-note/claims.json").read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(evidence["publicationAuthorization"], "not-evaluated")

    def test_transformed_output_needs_explicit_file_and_is_never_auto_approved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production = root / "production"
            _write_fixture(production, revision="a" * 40)
            selected = root / "selected.mp4"
            selected.write_bytes(b"rendered-output")
            expected = "sha256:" + hashlib.sha256(selected.read_bytes()).hexdigest()
            manifest_path = production / "production.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["outputs"][0]["blobDigest"] = expected
            manifest_path.write_text(json.dumps(manifest))
            without_file = build_production_context(production)
            self.assertEqual(
                without_file["outputByteIdentity"]["observations"][0]["relation"],
                "UNKNOWN_NO_SELECTED_BYTES",
            )
            with_file = build_production_context(
                production, output_files={"fixture-output": selected}
            )
            self.assertEqual(
                with_file["outputByteIdentity"]["observations"][0]["relation"],
                "MATCHES_DECLARED_DIGEST",
            )
            self.assertEqual(with_file["outputs"][0]["status"], "rendered")
            self.assertEqual(
                with_file["outputByteIdentity"]["observations"][0]["selectedPath"],
                str(selected.resolve()),
            )
            self.assertEqual(
                with_file["outputByteIdentity"]["publicationAuthorization"], "not-evaluated"
            )

            selected.write_bytes(b"changed-output")
            stale = build_production_context(
                production, output_files={"fixture-output": selected}
            )
            self.assertEqual(
                stale["outputByteIdentity"]["observations"][0]["relation"],
                "DIFFERS_FROM_DECLARED_DIGEST",
            )
            selected.unlink()
            missing = build_production_context(
                production, output_files={"fixture-output": selected}
            )
            self.assertEqual(
                missing["outputByteIdentity"]["observations"][0]["relation"],
                "UNKNOWN_SELECTED_FILE_UNAVAILABLE",
            )

    def test_source_carrier_unlisted_missing_and_symlink_escape_cannot_be_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production = root / "production"
            _write_fixture(production, revision="b" * 40)
            manifest_path = production / "production.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["outputs"][0]["sourceCarrier"] = "raw.bin"
            manifest_path.write_text(json.dumps(manifest))
            unlisted = build_production_context(production)
            self.assertEqual(
                unlisted["outputByteIdentity"]["observations"][0]["relation"],
                "INVALID_UNDECLARED_SOURCE_CARRIER",
            )
            manifest["sources"]["scripts"] = ["raw.bin"]
            manifest_path.write_text(json.dumps(manifest))
            missing = build_production_context(production)
            self.assertEqual(
                missing["outputByteIdentity"]["observations"][0]["relation"],
                "UNKNOWN_SELECTED_FILE_UNAVAILABLE",
            )
            secret = root / "outside.bin"
            secret.write_bytes(b"not-production-data")
            (production / "raw.bin").symlink_to(secret)
            escaped = build_production_context(production)
            self.assertEqual(
                escaped["outputByteIdentity"]["observations"][0]["relation"],
                "INVALID_ESCAPING_SOURCE_CARRIER",
            )

    def test_real_production_local_output_carriers_are_byte_verified(self) -> None:
        # Real completed media consumers; no invented physical status or provider.
        expected = {
            "archive-archipelago-001": 4,
            "convergence-object-001": 1,
            "convergence-sonic-ident": 4,
            "friction-loop-field-zine": 1,
            "live-relay-001": 3,
            "ordivon-system-constellation-atlas": 3,
            "site-social-card": 1,
            "studio-expression-card": 1,
        }
        for production_id, count in expected.items():
            with self.subTest(production=production_id):
                context = build_production_context(ROOT / "productions" / production_id)
                selected = [
                    row for row in context["outputByteIdentity"]["observations"]
                    if row["sourceSelection"] == "declared-local-output-carrier"
                ]
                self.assertGreaterEqual(len(selected), count)
                self.assertTrue(
                    all(row["relation"] == "MATCHES_DECLARED_DIGEST" for row in selected)
                )
                self.assertEqual(
                    context["outputByteIdentity"]["publicationAuthorization"], "not-evaluated"
                )

    def test_local_output_carrier_never_promotes_missing_or_changed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            production = root / "production"
            _write_fixture(production, revision="c" * 40)
            carrier = production / "render" / "master.bin"
            carrier.parent.mkdir()
            carrier.write_bytes(b"exact original")
            manifest_path = production / "production.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["outputs"][0]["outputCarrier"] = "render/master.bin"
            manifest["outputs"][0]["blobDigest"] = (
                "sha256:" + hashlib.sha256(carrier.read_bytes()).hexdigest()
            )
            manifest_path.write_text(json.dumps(manifest))
            first = build_production_context(production)
            item = first["outputByteIdentity"]["observations"][0]
            self.assertEqual(item["sourceSelection"], "declared-local-output-carrier")
            self.assertEqual(item["relation"], "MATCHES_DECLARED_DIGEST")
            self.assertEqual(first["outputs"][0]["status"], "rendered")

            carrier.write_bytes(b"unapproved mutation")
            changed = build_production_context(production)
            self.assertEqual(
                changed["outputByteIdentity"]["observations"][0]["relation"],
                "DIFFERS_FROM_DECLARED_DIGEST",
            )
            carrier.unlink()
            missing = build_production_context(production)
            self.assertEqual(
                missing["outputByteIdentity"]["observations"][0]["relation"],
                "UNKNOWN_SELECTED_FILE_UNAVAILABLE",
            )
            secret = root / "external.bin"
            secret.write_bytes(b"outside")
            carrier.symlink_to(secret)
            escaped = build_production_context(production)
            self.assertEqual(
                escaped["outputByteIdentity"]["observations"][0]["relation"],
                "INVALID_ESCAPING_OUTPUT_CARRIER",
            )

            manifest["outputs"][0]["sourceCarrier"] = "render/master.bin"
            manifest_path.write_text(json.dumps(manifest))
            double = build_production_context(production)
            self.assertEqual(
                double["outputByteIdentity"]["observations"][0]["relation"],
                "INVALID_MULTIPLE_CARRIERS",
            )

    def test_unknown_output_selection_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown output"):
            build_production_context(
                ROOT / "productions/browser-perception-note",
                output_files={"not-output": Path("/does/not/matter")},
            )

    def test_unknown_source_binding_mapping_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown binding"):
            build_production_context(
                ROOT / "productions/runtime-introduction",
                source_repositories={"not-a-binding": ROOT},
            )


if __name__ == "__main__":
    unittest.main()
