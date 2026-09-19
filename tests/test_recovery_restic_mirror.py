from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("restic_mirror_verify_test", ROOT / "recovery" / "restic_mirror_verify.py")
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class ResticMirrorVerifyTests(unittest.TestCase):
    def test_extract_backup_snapshot_id_uses_summary(self) -> None:
        text = '\n'.join([
            '{"message_type":"status","percent_done":0.5}',
            '{"message_type":"summary","snapshot_id":"abc123"}',
        ])
        self.assertEqual(M.extract_backup_snapshot_id(text), "abc123")

    def test_extract_backup_snapshot_id_fails_closed_without_summary(self) -> None:
        with self.assertRaisesRegex(M.MirrorVerificationError, "snapshot_id"):
            M.extract_backup_snapshot_id('{"message_type":"status"}\n')

    def test_cross_repository_id_may_change_while_tree_metadata_identity_matches(self) -> None:
        source = {
            "id": "primary-id",
            "tree": "tree-a",
            "time": "2026-08-29T12:48:43.395787581+08:00",
            "hostname": "node",
            "username": "root",
            "paths": ["/root/workstation-lab"],
            "tags": ["workstation-lab"],
        }
        mirror = {**source, "id": "mirror-id"}
        matches = M.matching_mirror_rows(source, [mirror])
        self.assertEqual([row["id"] for row in matches], ["mirror-id"])
        self.assertEqual(M.projection_digest(source), M.projection_digest(mirror))

    def test_tree_mismatch_is_not_mirror_identity(self) -> None:
        source = {"tree": "tree-a", "time": "t", "hostname": "h", "paths": ["/x"], "tags": ["a"]}
        mirror = {**source, "tree": "tree-b", "id": "m"}
        self.assertEqual(M.matching_mirror_rows(source, [mirror]), [])


if __name__ == "__main__":
    unittest.main()
