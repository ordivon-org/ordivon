import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

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

    def test_claimed_signature_or_complete_inputs_cannot_promote_content_binding(self):
        value = statement(self.artifact)
        value["authenticated"] = True
        value["signature"] = "caller-claimed-signature"
        value["predicate"]["buildDefinition"]["completeInputs"] = True
        result = self.verify(value)
        self.assertEqual(result["standing"], "PROVENANCE_CONTENT_BOUND")
        self.assertIs(result["authenticated"], False)
        self.assertNotIn("completeInputs", result)

    def test_duplicate_matching_source_dependency_is_ambiguous(self):
        value = statement(self.artifact)
        dependencies = value["predicate"]["buildDefinition"]["resolvedDependencies"]
        dependencies.append(dict(dependencies[0]))
        with self.assertRaisesRegex(ValueError, "not uniquely bound"):
            self.verify(value)

    def test_source_only_statement_does_not_establish_closed_inputs(self):
        # This is a valid content-bound statement even if the actual build read
        # an additional, undeclared file. This checker has no build readset.
        undeclared = self.artifact.parent / "unrecorded-input"
        undeclared.write_bytes(b"not represented in resolvedDependencies")
        # A tiny real build reads the undeclared input and emits the artifact.
        self.artifact.write_bytes(undeclared.read_bytes())
        result = self.verify(statement(self.artifact))
        self.assertEqual(result["sourceRevision"], "a" * 40)
        self.assertIs(result["authenticated"], False)
        self.assertNotIn("inputClosureVerified", result)

    def test_cli_observes_artifact_and_rejects_ambiguous_metadata(self):
        script = Path(__file__).resolve().parents[1] / "scripts/verify_build_provenance.py"
        report = self.artifact.parent / "provenance.json"
        raw = json.dumps(statement(self.artifact), indent=2)
        report.write_text(raw, encoding="utf-8")
        command = [
            sys.executable, str(script), "--artifact", str(self.artifact),
            "--provenance", str(report), "--source-revision", "a" * 40,
            "--source-uri", SOURCE, "--builder-id", BUILDER, "--build-type", BUILD_TYPE,
        ]
        valid = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(json.loads(valid.stdout), {
            "standing": "PROVENANCE_CONTENT_BOUND",
            "artifact": self.artifact.name,
            "artifactSha256": "sha256:" + hashlib.sha256(b"wheel").hexdigest(),
            "sourceRevision": "a" * 40,
            "builderId": BUILDER,
            "buildType": BUILD_TYPE,
            "authenticated": False,
        })
        # A synthetic duplicate metadata member cannot describe one unique observation.
        ambiguous = raw.replace(
            '"invocationId": "test-invocation"',
            '"invocationId": "first", "invocationId": "test-invocation"',
            1,
        )
        self.assertNotEqual(raw, ambiguous)
        report.write_text(ambiguous, encoding="utf-8")
        rejected = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(rejected.stdout, "")
        self.assertIn("duplicate JSON member", rejected.stderr)


@settings(max_examples=64, derandomize=True, database=None, deadline=None)
@given(st.binary(max_size=4096), st.sampled_from([40, 64]), st.booleans())
def check_content_projection_preserves_exact_artifact_identity(raw, revision_size, use_uri):
    with tempfile.TemporaryDirectory() as directory:
        artifact = Path(directory) / "fixture.bin"
        artifact.write_bytes(raw)
        revision = "a" * revision_size
        result = verify_build_provenance(
            statement(artifact, revision),
            artifact=artifact,
            expected_source_revision=revision,
            expected_source_uri=SOURCE if use_uri else None,
            expected_builder_id=BUILDER,
            expected_build_type=BUILD_TYPE,
        )
        assert result == {
            "standing": "PROVENANCE_CONTENT_BOUND",
            "artifact": "fixture.bin",
            "artifactSha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "sourceRevision": revision,
            "builderId": BUILDER,
            "buildType": BUILD_TYPE,
            "authenticated": False,
        }


class ProvenanceProperties(unittest.TestCase):
    def test_content_projection_preserves_exact_artifact_identity(self):
        check_content_projection_preserves_exact_artifact_identity()
