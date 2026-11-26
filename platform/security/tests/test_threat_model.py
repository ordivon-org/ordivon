import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_security_v2.threat_model import architecture_envelope_digest, validate_model_binding


class ThreatModelBindingTests(unittest.TestCase):
    def test_exact_architecture_envelope_is_current_and_mutation_is_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.md").write_text("alpha\n")
            (root / "b.md").write_text("beta\n")
            paths = ["b.md", "a.md"]
            digest = architecture_envelope_digest(root, paths)
            model = {
                "version": "1.0",
                "extensions": {
                    "ordivon.dev/security/source-binding": {
                        "schemaVersion": 1,
                        "architecturePaths": paths,
                        "architectureEnvelopeSha256": digest,
                    }
                },
            }
            result = validate_model_binding(model, root)
            self.assertEqual(result["standing"], "CURRENT")
            (root / "a.md").write_text("changed\n")
            with self.assertRaisesRegex(ValueError, "stale threat model"):
                validate_model_binding(model, root)

    def test_path_escape_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            model = {
                "extensions": {
                    "ordivon.dev/security/source-binding": {
                        "schemaVersion": 1,
                        "architecturePaths": ["../escape"],
                        "architectureEnvelopeSha256": "sha256:" + "0" * 64,
                    }
                }
            }
            with self.assertRaisesRegex(ValueError, "unsafe architecture-envelope path"):
                validate_model_binding(model, root)


@settings(max_examples=100, derandomize=True, database=None, deadline=None)
@given(st.dictionaries(
    st.sampled_from(("a.md", "b.md", "c.md", "文档.md")),
    st.binary(max_size=1024),
    min_size=1,
))
def check_envelope_matches_independent_framing(files):
    # Build the expected byte stream from fixture coordinates, not the
    # filesystem traversal or the function under test.
    chunks = []
    for name, data in sorted(files.items()):
        label = name.encode("utf-8")
        chunks.append(struct.pack(">Q", len(label)) + label)
        chunks.append(struct.pack(">Q", len(data)) + data)
    expected = "sha256:" + hashlib.sha256(b"".join(chunks)).hexdigest()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name, data in files.items():
            (root / name).write_bytes(data)
        names = list(files)
        assert architecture_envelope_digest(root, names) == expected
        assert architecture_envelope_digest(root, names[::-1] + names) == expected


class ArchitectureEnvelopeProperties(unittest.TestCase):
    def test_independent_framing(self):
        check_envelope_matches_independent_framing()

    def test_literal_framing_vector(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a").write_bytes(b"bc")
            expected = bytes.fromhex("0000000000000001") + b"a"
            expected += bytes.fromhex("0000000000000002") + b"bc"
            self.assertEqual(
                architecture_envelope_digest(root, ["a"]),
                "sha256:" + hashlib.sha256(expected).hexdigest(),
            )
