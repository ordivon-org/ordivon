import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2.provenance import (
    build_provenance_statement,
    verify_build_provenance,
)


class ProvenanceTests(unittest.TestCase):
    def _statement(self, artifact: Path, revision: str = "a" * 40):
        return build_provenance_statement(
            artifact=artifact,
            source_uri="git+file:///repo",
            source_revision=revision,
            invocation_id="test-invocation",
            started_on="2026-09-12T00:00:00Z",
            finished_on="2026-09-12T00:00:01Z",
            builder_versions={"uv": "test", "python": "3.12"},
        )

    def test_exact_artifact_and_source_verify(self):
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "package.whl"
            artifact.write_bytes(b"wheel")
            result = verify_build_provenance(
                self._statement(artifact),
                artifact=artifact,
                expected_source_revision="a" * 40,
            )
            self.assertEqual(result["standing"], "BUILD_PROVENANCE_VERIFIED")

    def test_artifact_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "package.whl"
            artifact.write_bytes(b"wheel")
            statement = self._statement(artifact)
            artifact.write_bytes(b"mutated")
            with self.assertRaisesRegex(ValueError, "artifact digest mismatch"):
                verify_build_provenance(
                    statement, artifact=artifact, expected_source_revision="a" * 40
                )

    def test_source_revision_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "package.whl"
            artifact.write_bytes(b"wheel")
            with self.assertRaisesRegex(ValueError, "exact source revision"):
                verify_build_provenance(
                    self._statement(artifact),
                    artifact=artifact,
                    expected_source_revision="b" * 40,
                )
