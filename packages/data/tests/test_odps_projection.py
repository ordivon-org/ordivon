"""Actual domain ODPS source-bound consumers; no invented source file locations."""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import tomllib

ROOT = Path(__file__).resolve().parents[3]
import sys

sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data.catalog import inspect_catalog
from ordivon_data.git_sources import committed_owner_products
from ordivon_data.local_evidence import LocalEvidenceBinding
from ordivon_data.odps_projection import project_catalog


class OwnerProductProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        # Discover real currently tracked producer contracts via Git, not
        # physical paths hard-coded into a second Owner's tests.
        discovered = subprocess.run(
            ["/usr/bin/git", "-C", str(ROOT), "ls-files", "-z", "--", "*/odps.json"],
            check=True,
            capture_output=True,
        )
        paths = [
            ROOT / raw.decode("utf-8") for raw in discovered.stdout.split(b"\0") if raw
        ]
        records = {
            json.loads(path.read_text(encoding="utf-8"))["id"]: path for path in paths
        }
        self.sources = [
            records["d14d7457-c9aa-59e0-8bf5-7783cea39c1c"],
            records["4b2a0b92-e9d6-5f31-8157-a1c16e4ef34b"],
        ]
        owner_rows = tomllib.loads((ROOT / "tools/repo/owners.toml").read_text())[
            "owners"
        ]
        source_relative = self.sources[0].relative_to(ROOT).as_posix()
        matches = [
            row["root"] for row in owner_rows if source_relative.startswith(row["root"])
        ]
        self.assertEqual(len(matches), 1)
        # Explicit exact consumer/source boundary, derived from the registered
        # Owner root; relocation must update both source and dependency seam.
        self.assertEqual(matches[0], "domains/capital/")
        self.finance_root = ROOT / matches[0]

    def test_real_owner_products_project_to_dcat_without_fake_access(self) -> None:
        projected = project_catalog(self.sources)
        reversed_order = project_catalog(list(reversed(self.sources)))
        self.assertEqual(projected, reversed_order)
        self.assertEqual(len(projected["dcat:dataset"]), 2)
        self.assertEqual(
            sum(len(x["dcat:distribution"]) for x in projected["dcat:dataset"]), 3
        )
        self.assertTrue(
            all(
                "dcat:accessURL" not in dist and "dct:identifier" not in dist
                for product in projected["dcat:dataset"]
                for dist in product["dcat:distribution"]
            )
        )
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "catalog.jsonld"
            output.write_text(json.dumps(projected), encoding="utf-8")
            readback = inspect_catalog(output, verify_local=True, allowed_roots=(ROOT,))
            self.assertEqual(len(readback["products"]), 2)
            self.assertEqual(
                sum(len(p["distributions"]) for p in readback["products"]), 3
            )
            self.assertTrue(
                all(
                    dist["verification"] == "UNKNOWN"
                    for product in readback["products"]
                    for dist in product["distributions"]
                )
            )

    def test_git_commit_view_ignores_worktree_and_index_mutations(self) -> None:
        """A published metadata SourceCut must be one Git tree, not mutable files."""
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def git(*args: str) -> bytes:
                return subprocess.run(
                    ["/usr/bin/git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                ).stdout

            git("init", "-q")
            entry = repo / "domains/capital/data-products/candidate/odps.json"
            entry.parent.mkdir(parents=True)
            initial = self.sources[0].read_bytes()
            entry.write_bytes(initial)
            git("add", ".")
            git(
                "-c",
                "user.name=Data Test",
                "-c",
                "user.email=data@example.invalid",
                "commit",
                "-qm",
                "admit source version one",
            )
            original_commit, original_blobs = committed_owner_products(repo, "HEAD")
            self.assertEqual(original_blobs, [initial])
            frozen_view = project_catalog(original_blobs)
            self.assertEqual(frozen_view, project_catalog([entry]))

            mutated = json.loads(initial)
            mutated["version"] = "deliberately-uncommitted-v2"
            entry.write_text(json.dumps(mutated), encoding="utf-8")
            git("add", ".")
            # Index now points to an uncommitted v2, but commit-scoped readers
            # still see the old v1, unlike default live working tree projection.
            unchanged_commit, unchanged_blobs = committed_owner_products(repo, "HEAD")
            self.assertEqual(unchanged_commit, original_commit)
            self.assertEqual(project_catalog(unchanged_blobs), frozen_view)
            self.assertNotEqual(project_catalog([entry]), frozen_view)

            git(
                "-c",
                "user.name=Data Test",
                "-c",
                "user.email=data@example.invalid",
                "commit",
                "-qm",
                "publish source version two",
            )
            next_commit, new_blobs = committed_owner_products(repo, "HEAD")
            self.assertNotEqual(next_commit, original_commit)
            self.assertNotEqual(project_catalog(new_blobs), frozen_view)
            prior_commit, prior_blobs = committed_owner_products(repo, original_commit)
            self.assertEqual(prior_commit, original_commit)
            self.assertEqual(project_catalog(prior_blobs), frozen_view)

    def test_git_view_rejects_symlinks_and_invalid_revision(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def git(*args: str) -> None:
                subprocess.run(
                    ["/usr/bin/git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                )

            git("init", "-q")
            entry = repo / "catalogs/data-products/test/odps.json"
            entry.parent.mkdir(parents=True)
            entry.symlink_to("/tmp/outside-file.json")
            git("add", ".")
            git(
                "-c",
                "user.name=Data Test",
                "-c",
                "user.email=data@example.invalid",
                "commit",
                "-qm",
                "symlink is not ODPS bytes",
            )
            with self.assertRaisesRegex(ValueError, "not a regular Git blob"):
                committed_owner_products(repo, "HEAD")
            with self.assertRaisesRegex(ValueError, "cannot be resolved"):
                committed_owner_products(repo, "not-a-commit")
            with self.assertRaisesRegex(ValueError, "nonempty revision"):
                committed_owner_products(repo, "--help")

    def test_exact_current_repo_git_view_matches_committed_owner_metadata(self) -> None:
        script = ROOT / "packages/data/scripts/project_owned_products.py"
        source = subprocess.run(
            [sys.executable, str(script), "--at-commit", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        commit = subprocess.run(
            ["/usr/bin/git", "-C", str(ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertIn(f"sourceCommit={commit}", source.stderr)
        self.assertEqual(json.loads(source.stdout), project_catalog(self.sources))
        invalid = subprocess.run(
            [
                sys.executable,
                str(script),
                "--at-commit",
                "HEAD",
                "--product",
                str(self.sources[0]),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("mutually exclusive", invalid.stderr)

    def test_duplicate_product_version_cannot_be_silently_overridden(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate owner product"):
            project_catalog([self.sources[0], self.sources[0]])

    def test_malformed_product_does_not_fall_back_to_unsafe_metadata(self) -> None:
        data = json.loads(self.sources[0].read_text(encoding="utf-8"))
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / "product.json"
            data["apiVersion"] = "v4.2.0"
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ODPS DataProduct v1.1.0"):
                project_catalog([file])
            data["apiVersion"] = "v1.1.0"
            # ODPS 1.1 port versions are independent of product versions.
            data["outputPorts"][0]["version"] = "port-v2"
            file.write_text(json.dumps(data), encoding="utf-8")
            projected = project_catalog([file])
            self.assertEqual(
                projected["dcat:dataset"][0]["dcat:distribution"][0]["dcat:version"],
                "port-v2",
            )

            # ODPS 1.1 port id and version are optional; do not mint identities.
            port = data["outputPorts"][0]
            port.pop("id")
            port.pop("version")
            file.write_text(json.dumps(data), encoding="utf-8")
            projected = project_catalog([file])
            distribution = projected["dcat:dataset"][0]["dcat:distribution"][0]
            self.assertNotIn("@id", distribution)
            self.assertNotIn("dcat:version", distribution)

            data["outputPorts"].append(dict(port))
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(
                ValueError, "duplicate output port name and version"
            ):
                project_catalog([file])

    def test_two_owner_files_are_real_verified_one_parquet_unknown(self) -> None:
        bindings = (
            LocalEvidenceBinding(
                "d14d7457-c9aa-59e0-8bf5-7783cea39c1c",
                "public-shadow-json",
                "sourceRelativePath",
                "sourceSha256",
                self.finance_root,
            ),
            LocalEvidenceBinding(
                "4b2a0b92-e9d6-5f31-8157-a1c16e4ef34b",
                "episode-corpus-manifest-json",
                "corpusManifestRelativePath",
                "corpusManifestSha256",
                ROOT,
            ),
        )
        projected = project_catalog(self.sources, bindings=bindings)
        self.assertEqual(
            projected,
            project_catalog(
                list(reversed(self.sources)), bindings=tuple(reversed(bindings))
            ),
        )
        with TemporaryDirectory() as tmp:
            file = Path(tmp) / "qualified.jsonld"
            file.write_text(json.dumps(projected), encoding="utf-8")
            observed = inspect_catalog(file, verify_local=True, allowed_roots=(ROOT,))
            verified = [
                dist
                for product in observed["products"]
                for dist in product["distributions"]
                if dist["verification"] == "VERIFIED"
            ]
            unknown = [
                dist
                for product in observed["products"]
                for dist in product["distributions"]
                if dist["verification"] == "UNKNOWN"
            ]
            self.assertEqual(len(verified), 2)
            self.assertEqual(len(unknown), 1)
            self.assertEqual(unknown[0]["title"], "episode-index-parquet")
            self.assertTrue(all(d["reason"] == "digest_match" for d in verified))
            self.assertTrue(all(d["uri"].startswith("file:///") for d in verified))

    def test_explicit_binding_must_match_owner_metadata_and_bytes(self) -> None:
        owner = self.sources[0]
        props = json.loads(owner.read_text(encoding="utf-8"))
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "owner-evidence.json"
            data.write_bytes(b"original")
            declared = hashlib.sha256(data.read_bytes()).hexdigest()
            custom = props["customProperties"]
            for prop in custom:
                if prop.get("property") == "sourceRelativePath":
                    prop["value"] = data.name
                if prop.get("property") == "sourceSha256":
                    prop["value"] = declared
            candidate = root / "odps.json"
            candidate.write_text(json.dumps(props), encoding="utf-8")
            binding = LocalEvidenceBinding(
                props["id"],
                "public-shadow-json",
                "sourceRelativePath",
                "sourceSha256",
                root,
            )
            project_catalog([candidate], bindings=(binding,))
            data.write_bytes(b"corrupted")
            with self.assertRaisesRegex(ValueError, "digest differs"):
                project_catalog([candidate], bindings=(binding,))
            data.write_bytes(b"original")
            with self.assertRaisesRegex(ValueError, "named output port"):
                project_catalog(
                    [candidate],
                    bindings=(
                        LocalEvidenceBinding(
                            props["id"],
                            "nonexistent-port",
                            "sourceRelativePath",
                            "sourceSha256",
                            root,
                        ),
                    ),
                )
            with self.assertRaisesRegex(ValueError, "duplicate local evidence"):
                project_catalog([candidate], bindings=(binding, binding))
            with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
                project_catalog(
                    [candidate],
                    bindings=(
                        LocalEvidenceBinding(
                            props["id"],
                            "public-shadow-json",
                            "unknown-property",
                            "sourceSha256",
                            root,
                        ),
                    ),
                )
            for prop in custom:
                if prop.get("property") == "sourceRelativePath":
                    prop["value"] = "../out-of-root.json"
            candidate.write_text(json.dumps(props), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not escape"):
                project_catalog([candidate], bindings=(binding,))

    def test_cli_verified_binding_is_read_only_and_missing_is_unknown(self) -> None:
        import subprocess

        script = ROOT / "packages/data/scripts/project_owned_products.py"
        cmd = [
            sys.executable,
            str(script),
            "--bind-local",
            "d14d7457-c9aa-59e0-8bf5-7783cea39c1c",
            "public-shadow-json",
            "sourceRelativePath",
            "sourceSha256",
            str(self.finance_root),
            "--bind-local",
            "4b2a0b92-e9d6-5f31-8157-a1c16e4ef34b",
            "episode-corpus-manifest-json",
            "corpusManifestRelativePath",
            "corpusManifestSha256",
            str(ROOT),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        projection = json.loads(result.stdout)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "from-cli.jsonld"
            path.write_text(json.dumps(projection), encoding="utf-8")
            observed = inspect_catalog(path, verify_local=True, allowed_roots=(ROOT,))
            statuses = [
                dist["verification"]
                for product in observed["products"]
                for dist in product["distributions"]
            ]
            self.assertEqual(sorted(statuses), ["UNKNOWN", "VERIFIED", "VERIFIED"])

    def test_dcat3_spdx_keeps_non_uuid_port_identity(self) -> None:
        """DCAT dct:identifier is identity; checksum is its own SPDX property."""
        product = json.loads(self.sources[0].read_text(encoding="utf-8"))
        product["outputPorts"][0]["id"] = "provider-defined-port-id"
        binding = LocalEvidenceBinding(
            product["id"],
            "public-shadow-json",
            "sourceRelativePath",
            "sourceSha256",
            self.finance_root,
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "modified-odps.json"
            path.write_text(json.dumps(product), encoding="utf-8")
            projected = project_catalog([path], bindings=(binding,))
            dist = projected["dcat:dataset"][0]["dcat:distribution"][0]
            self.assertEqual(dist["dct:identifier"], "provider-defined-port-id")
            self.assertNotIn("@id", dist)
            self.assertEqual(dist["spdx:checksum"]["@type"], "spdx:Checksum")
            self.assertEqual(
                dist["spdx:checksum"]["spdx:algorithm"]["@id"],
                "http://spdx.org/rdf/terms#checksumAlgorithm_sha256",
            )
            self.assertEqual(
                dist["spdx:checksum"]["spdx:checksumValue"]["@type"],
                "xsd:hexBinary",
            )
            catalog_path = Path(tmp) / "catalog.jsonld"
            catalog_path.write_text(json.dumps(projected), encoding="utf-8")
            observed = inspect_catalog(
                catalog_path, verify_local=True, allowed_roots=(ROOT,)
            )
            self.assertEqual(
                observed["products"][0]["distributions"][0]["verification"],
                "VERIFIED",
            )
            # A contradictory legacy digest is not silently overridden.
            dist["dct:identifier"] = "sha256:" + ("0" * 64)
            catalog_path.write_text(json.dumps(projected), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "conflicting legacy and SPDX"):
                inspect_catalog(catalog_path, verify_local=True, allowed_roots=(ROOT,))

    def test_scoped_port_gate_accepts_verified_manifest_without_parquet(self) -> None:
        """Consumer of one port must not claim the whole product is verified."""
        import subprocess

        episode = json.loads(self.sources[1].read_text(encoding="utf-8"))
        manifest_port = next(
            p["id"]
            for p in episode["outputPorts"]
            if p["name"] == "episode-corpus-manifest-json"
        )
        parquet_port = next(
            p["id"]
            for p in episode["outputPorts"]
            if p["name"] == "episode-index-parquet"
        )
        projected = project_catalog(
            [self.sources[1]],
            bindings=(
                LocalEvidenceBinding(
                    episode["id"],
                    "episode-corpus-manifest-json",
                    "corpusManifestRelativePath",
                    "corpusManifestSha256",
                    ROOT,
                ),
            ),
        )
        with TemporaryDirectory() as temp:
            catalog = Path(temp) / "qualified.jsonld"
            catalog.write_text(json.dumps(projected), encoding="utf-8")
            script = ROOT / "packages/data/scripts/inspect_federation.py"
            base = [
                sys.executable,
                str(script),
                "--catalog",
                str(catalog),
                "--verify-local",
            ]

            def invoke(*args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [*base, *args],
                    check=False,
                    text=True,
                    capture_output=True,
                    timeout=20,
                )

            target = (episode["id"], episode["version"], "urn:uuid:" + manifest_port)
            accepted = invoke("--require-port", *target)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            inspection = json.loads(accepted.stdout)["inspection"]
            self.assertEqual(inspection["integrityGate"], "NOT_ESTABLISHED")
            self.assertEqual(inspection["selectedPortIntegrityGate"], "PASS")
            self.assertEqual(inspection["verifiedCount"], 1)
            self.assertEqual(inspection["unknownCount"], 1)
            self.assertEqual(inspection["selectedPorts"][0]["verification"], "VERIFIED")

            all_port_gate = invoke("--require-verified")
            self.assertEqual(all_port_gate.returncode, 3)

            unknown = invoke(
                "--require-port",
                episode["id"],
                episode["version"],
                "urn:uuid:" + parquet_port,
            )
            self.assertEqual(unknown.returncode, 3)
            self.assertEqual(
                json.loads(unknown.stdout)["inspection"]["selectedPortIntegrityGate"],
                "NOT_ESTABLISHED",
            )
            wrong_version = invoke(
                "--require-port",
                episode["id"],
                "wrong-version",
                "urn:uuid:" + manifest_port,
            )
            self.assertEqual(wrong_version.returncode, 3)
            missing = invoke(
                "--require-port",
                episode["id"],
                episode["version"],
                "urn:uuid:00000000-0000-0000-0000-000000000000",
            )
            self.assertEqual(missing.returncode, 3)

            duplicate = invoke("--require-port", *target, "--require-port", *target)
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn("duplicate --require-port", duplicate.stderr)
            conflicting = invoke("--require-port", *target, "--require-verified")
            self.assertEqual(conflicting.returncode, 2)
            unverified = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--catalog",
                    str(catalog),
                    "--require-port",
                    *target,
                ],
                check=False,
                text=True,
                capture_output=True,
                timeout=20,
            )
            self.assertEqual(unverified.returncode, 2)
