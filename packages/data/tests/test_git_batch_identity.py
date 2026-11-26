"""Independent native batch protocol negatives and exact object hashes."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/data/src"))

from ordivon_data.git_identity import qualify_batch_sizes, verify_object_batch


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
