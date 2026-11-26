"""Native Git mktree is an independent commitment oracle for listing properties."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from ordivon_data.git_tree import qualify_tree_listing


@pytest.mark.parametrize("algorithm", ["sha1", "sha256"])
@given(
    st.lists(
        st.text(alphabet="abcABCé. _\t\n", min_size=1, max_size=12).filter(
            lambda name: name not in (".", "..")
        ),
        min_size=1,
        max_size=6,
        unique=True,
    )
)
@settings(max_examples=30, derandomize=True, database=None, deadline=None)
def test_native_tree_commitment_and_every_whole_row_omission(algorithm, names):
    with TemporaryDirectory() as tmp:

        def git(*args, data=None):
            return subprocess.run(
                ["/usr/bin/git", "-C", tmp, *args],
                input=data,
                capture_output=True,
                check=True,
            ).stdout

        git("init", "-q", "--object-format=" + algorithm)
        blob = git("hash-object", "-w", "--stdin", data=b"metadata").strip()
        subtree = git(
            "mktree", "-z", data=b"100644 blob " + blob + b"\todps.json\0"
        ).strip()
        rows = []
        expected = []
        for index, name in enumerate(names):
            encoded = name.encode("utf-8")
            if index % 2 == 0:
                rows.append(b"040000 tree " + subtree + b"\t" + encoded + b"\0")
                expected.append((name + "/odps.json", blob.decode("ascii")))
            else:
                rows.append(b"100644 blob " + blob + b"\t" + encoded + b"\0")
        root = git("mktree", "-z", data=b"".join(rows)).strip().decode("ascii")
        listing = git("ls-tree", "-r", "-t", "-z", "--full-tree", root)
        native_rows = listing[:-1].split(b"\0")
        for projection in (listing, b"\0".join(reversed(native_rows)) + b"\0"):
            identities, products = qualify_tree_listing(projection, root, algorithm)
            assert identities == {root, subtree.decode("ascii")}
            assert sorted(products) == sorted(expected)

        # The finite fault dimension is exhaustive for every generated tree.
        for index in range(len(native_rows)):
            omitted = native_rows[:index] + native_rows[index + 1 :]
            with pytest.raises(ValueError, match="Git tree identity mismatch"):
                qualify_tree_listing(b"\0".join(omitted) + b"\0", root, algorithm)
