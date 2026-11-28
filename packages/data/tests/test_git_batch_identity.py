"""Independent native batch protocol negatives and exact object hashes."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data.git_identity import (
    partition_object_batches,
    qualify_batch_sizes,
    verify_object_batch,
)


def fixture(algorithm: str):
    def frame(kind: str, payload: bytes):
        prefix = f"{kind} {len(payload)}".encode("ascii")
        oid = hashlib.new(algorithm, prefix + b"\0" + payload).hexdigest()
        return oid, kind, oid.encode() + b" " + prefix, payload

    tree = frame("tree", b"")
    commit = frame("commit", b"tree " + tree[0].encode() + b"\n\nmessage\n")
    frames = [commit, tree]
    expected = [(oid, kind) for oid, kind, _, _ in frames]
    headers = b"".join(header + b"\n" for _, _, header, _ in frames)
    contents = b"".join(
        header + b"\n" + payload + b"\n" for _, _, header, payload in frames
    )
    return commit[0], tree[0], expected, headers, contents


class GitBatchIdentityTests(unittest.TestCase):
    def test_ordered_exact_frames_and_empty_tree(self):
        for algorithm in ("sha1", "sha256"):
            with self.subTest(algorithm=algorithm):
                commit, tree, expected, checks, data = fixture(algorithm)
                plan = qualify_batch_sizes(checks, expected, algorithm)
                verify_object_batch(
                    data, plan, algorithm, commit=commit, root_tree=tree
                )

    def test_reject_missing_wrong_kind_reordered_and_unbounded_headers(self):
        for algorithm in ("sha1", "sha256"):
            commit, tree, expected, checks, _ = fixture(algorithm)
            rows = checks.splitlines()
            for invalid in (
                checks[:-1],
                rows[0] + b"\n",
                b"\n".join(rows[::-1]) + b"\n",
                checks.replace(b"commit ", b"blob ", 1),
                checks.replace(rows[0], commit.encode() + b" missing", 1),
                checks.replace(rows[1], tree.encode() + b" tree 8388609", 1),
                checks.replace(rows[1], tree.encode() + b" tree 00", 1),
            ):
                with (
                    self.subTest(algorithm=algorithm, invalid=invalid),
                    self.assertRaises(ValueError),
                ):
                    qualify_batch_sizes(invalid, expected, algorithm)
            with (
                patch("ordivon_data.git_identity._MAX_OBJECTS", 1),
                self.assertRaisesRegex(ValueError, "object count"),
            ):
                qualify_batch_sizes(checks, expected, algorithm)

    def test_reject_changed_bytes_truncated_extra_and_wrong_root(self):
        for algorithm in ("sha1", "sha256"):
            commit, tree, expected, checks, data = fixture(algorithm)
            plan = qualify_batch_sizes(checks, expected, algorithm)
            for invalid in (
                data.replace(b"message", b"changed", 1),
                data[:-1],
                data + b"x",
                data.replace(b"tree 0\n", b"tree 1\n", 1),
            ):
                with (
                    self.subTest(algorithm=algorithm, invalid=invalid),
                    self.assertRaises(ValueError),
                ):
                    verify_object_batch(
                        invalid, plan, algorithm, commit=commit, root_tree=tree
                    )
            with self.assertRaisesRegex(ValueError, "root tree identity"):
                verify_object_batch(
                    data, plan, algorithm, commit=commit, root_tree="0" * len(tree)
                )

    def test_combined_blob_budget_and_zero_length_rejected_at_header_admission(self):
        for algorithm in ("sha1", "sha256"):
            _commit, tree, expected, checks, _ = fixture(algorithm)
            width = len(tree)
            for size in (0, 2 * 1024 * 1024 + 1):
                oid = "a" * width
                with (
                    self.subTest(algorithm=algorithm, size=size),
                    self.assertRaisesRegex(ValueError, "bounded input size"),
                ):
                    qualify_batch_sizes(
                        checks + f"{oid} blob {size}\n".encode(),
                        expected + [(oid, "blob")],
                        algorithm,
                    )
            blobs = [(f"{i:0{width}x}", "blob") for i in range(1, 33)]
            headers = b"".join(
                f"{oid} blob {2 * 1024 * 1024}\n".encode() for oid, _ in blobs
            )
            # 32 maximal Blobs plus protocol framing exceed 64 MiB.
            qualify_batch_sizes(
                checks + b"".join(headers.splitlines(keepends=True)[:-1]),
                expected + blobs[:-1],
                algorithm,
            )
            with self.assertRaisesRegex(ValueError, "bounded object bytes"):
                qualify_batch_sizes(checks + headers, expected + blobs, algorithm)
            with self.assertRaisesRegex(ValueError, "bounded batch bytes"):
                qualify_batch_sizes(
                    checks + f"{'f' * width} tree {8 * 1024 * 1024}\n".encode(),
                    expected + [("f" * width, "tree")],
                    algorithm,
                )

    def test_commit_presence_matches_batch_role(self):
        for algorithm in ("sha1", "sha256"):
            commit, tree, expected, checks, data = fixture(algorithm)
            plan = qualify_batch_sizes(checks, expected, algorithm)
            # The native wire format is header + LF + payload + LF.
            # The root tree fixture has an empty payload.
            tree_frame = checks.splitlines()[1] + b"\n\n"
            for role, raw, headers, required, accepted in (
                ("first", data, plan, True, True),
                ("later", tree_frame, plan[1:], False, True),
                ("missing-first", tree_frame, plan[1:], True, False),
                ("unexpected-later", data, plan, False, False),
            ):
                with self.subTest(algorithm=algorithm, role=role):
                    if accepted:
                        self.assertEqual(
                            verify_object_batch(
                                raw,
                                headers,
                                algorithm,
                                commit=commit,
                                root_tree=tree,
                                require_commit=required,
                            ),
                            {},
                        )
                    else:
                        with self.assertRaisesRegex(
                            ValueError, "incomplete Git object batch"
                        ):
                            verify_object_batch(
                                raw,
                                headers,
                                algorithm,
                                commit=commit,
                                root_tree=tree,
                                require_commit=required,
                            )

    def test_reject_duplicate_or_different_commit_identity(self):
        for algorithm in ("sha1", "sha256"):
            commit, tree, expected, checks, data = fixture(algorithm)
            plan = qualify_batch_sizes(checks, expected, algorithm)
            # Duplicate the complete, independently valid commit frame.
            first_frame = data[: len(plan[0][0]) + plan[0][1] + 2]
            for fault, raw, headers, requested in (
                ("duplicate", first_frame + data, [plan[0], *plan], commit),
                ("wrong-requested-oid", data, plan, "0" * len(commit)),
            ):
                with (
                    self.subTest(algorithm=algorithm, fault=fault),
                    self.assertRaisesRegex(ValueError, "commit root tree identity"),
                ):
                    verify_object_batch(
                        raw, headers, algorithm, commit=requested, root_tree=tree
                    )

    def test_partition_empty_exact_and_over_budget_obligations(self):
        with patch("ordivon_data.git_identity._MAX_BATCH_BYTES", 10):
            self.assertEqual(partition_object_batches([]), [])
            self.assertEqual(partition_object_batches([(b"abc", 5)]), [[(b"abc", 5)]])
            self.assertEqual(
                partition_object_batches([(b"a", 2), (b"b", 2), (b"c", 1)]),
                [[(b"a", 2), (b"b", 2)], [(b"c", 1)]],
            )
            for invalid in ((b"abc", -1), (b"abc", 6)):
                with (
                    self.subTest(invalid=invalid),
                    self.assertRaisesRegex(ValueError, "bounded batch bytes"),
                ):
                    partition_object_batches([(b"a", 1), invalid])
