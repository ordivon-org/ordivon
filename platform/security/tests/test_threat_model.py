import tempfile
import unittest
from pathlib import Path

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
