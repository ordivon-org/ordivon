import hashlib
import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2.provenance import verify_build_provenance

BUILDER = "https://example.invalid/expected-builder"
BUILD_TYPE = "https://example.invalid/expected-build-type"
SOURCE = "git+https://github.com/ordivon-org/ordivon.git"


def statement(artifact: Path, revision: str = "a" * 40) -> dict:
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": artifact.name, "digest": {
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        }}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": BUILD_TYPE,
                "resolvedDependencies": [{"uri": SOURCE, "digest": {"gitCommit": revision}}],
            },
            "runDetails": {
                "builder": {"id": BUILDER},
                "metadata": {
                    "invocationId": "test-invocation",
                    "startedOn": "2026-09-12T00:00:00Z",
                    "finishedOn": "2026-09-12T00:00:01Z",
                },
            },
        },
    }


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.artifact = Path(temporary.name) / "package.whl"
        self.artifact.write_bytes(b"wheel")

    def verify(self, value, **overrides):
        options = {
            "artifact": self.artifact,
            "expected_source_revision": "a" * 40,
            "expected_source_uri": SOURCE,
            "expected_builder_id": BUILDER,
            "expected_build_type": BUILD_TYPE,
        }
        options.update(overrides)
        return verify_build_provenance(value, **options)

    def test_content_binding_does_not_claim_signed_authenticity(self):
        result = self.verify(statement(self.artifact))
        self.assertEqual(result["standing"], "PROVENANCE_CONTENT_BOUND")
        self.assertIs(result["authenticated"], False)

    def test_artifact_mutation_fails_closed(self):
        value = statement(self.artifact)
        self.artifact.write_bytes(b"mutated")
        with self.assertRaisesRegex(ValueError, "artifact digest mismatch"):
            self.verify(value)

    def test_source_revision_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "source revision/URI"):
            self.verify(statement(self.artifact, "b" * 40))

    def test_source_uri_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "source revision/URI"):
            self.verify(statement(self.artifact), expected_source_uri="git+https://wrong.invalid")

    def test_builder_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "builder identity mismatch"):
            self.verify(statement(self.artifact), expected_builder_id="wrong")

    def test_build_type_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "buildType mismatch"):
            self.verify(statement(self.artifact), expected_build_type="wrong")

    def test_no_self_asserted_builder_authority(self):
        with self.assertRaisesRegex(ValueError, "expected builder and build type"):
            self.verify(statement(self.artifact), expected_builder_id="")
