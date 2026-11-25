import hashlib
import tempfile
import unittest
from pathlib import Path

from ordivon_security_v2 import EvidenceRef, build_gate_input
from ordivon_security_v2.evidence import verified_evidence_path


class EvidenceRefTests(unittest.TestCase):
    def test_count_and_digest_cover_same_bytes_at_buffer_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "opaque"
            boundary = 256 * 1024
            for size in (0, 1, boundary - 1, boundary, boundary + 1, 3 * boundary + 17):
                with self.subTest(size=size):
                    raw = (bytes(range(256)) * ((size + 255) // 256))[:size]
                    path.write_bytes(raw)
                    ref = EvidenceRef.from_path(provider="fixture", format="opaque", path=path)
                    self.assertEqual(ref.byte_length, size)
                    self.assertEqual(ref.sha256, "sha256:" + hashlib.sha256(raw).hexdigest())

    def test_digest_binds_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.sarif"
            path.write_text('{"version":"2.1.0"}', encoding="utf-8")
            ref = EvidenceRef.from_path(provider="semgrep", format="sarif", path=path)
            self.assertEqual(verified_evidence_path(ref.to_dict()), path)
            self.assertTrue(ref.sha256.startswith("sha256:"))
            self.assertEqual(ref.byte_length, len(path.read_bytes()))

    def test_mutated_evidence_is_not_reusable_for_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.sarif"
            path.write_bytes(b'{"runs":[]}')
            bound = EvidenceRef.from_path(provider="semgrep", format="sarif", path=path)
            path.write_bytes(b'{"runs":[{"result":"changed"}]}')
            with self.assertRaisesRegex(ValueError, "changed after gate binding"):
                verified_evidence_path(bound.to_dict())

    def test_evidence_reference_rejects_invalid_length_and_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.sarif"
            path.write_bytes(b'{}')
            bound = EvidenceRef.from_path(provider="semgrep", format="sarif", path=path).to_dict()
            with self.assertRaisesRegex(ValueError, "positive integer"):
                verified_evidence_path({**bound, "byte_length": True})
            with self.assertRaisesRegex(ValueError, "invalid evidence reference"):
                verified_evidence_path({**bound, "untrusted": "extra"})

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
