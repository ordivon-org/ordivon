import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2 import EvidenceRef, build_gate_input


class EvidenceRefTests(unittest.TestCase):
    def test_digest_binds_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.sarif"
            path.write_text('{"version":"2.1.0"}', encoding="utf-8")
            ref = EvidenceRef.from_path(provider="semgrep", format="sarif", path=path)
            self.assertTrue(ref.sha256.startswith("sha256:"))
            self.assertEqual(ref.byte_length, len(path.read_bytes()))

    def test_gate_input_requires_evidence(self) -> None:
        with self.assertRaises(ValueError):
            build_gate_input(
                subject_ref="repo:test",
                subject_revision="abc",
                evidence=[],
                authority="security-verification",
            )


if __name__ == "__main__":
    unittest.main()
