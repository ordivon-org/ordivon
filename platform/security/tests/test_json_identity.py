"""Independent literal byte vectors for the existing JSON identity profile."""

import hashlib
import unittest

from hypothesis import given, settings
from hypothesis import strategies as st

from ordivon_security_v2.json_identity import canonical_json_bytes, canonical_json_digest


@settings(max_examples=100, derandomize=True, database=None, deadline=None)
@given(st.dictionaries(st.text(alphabet="abcxyz", min_size=1, max_size=6),
                       st.integers(-10000, 10000), max_size=10))
def check_sorted_metadata_bytes(metadata):
    # Restricted alphabet and integer domain permit a direct byte oracle.
    expected = ("{" + ",".join(f'"{key}":{metadata[key]}' for key in sorted(metadata))
                + "}").encode("utf-8")
    assert canonical_json_bytes(metadata) == expected
    assert canonical_json_digest(metadata) == "sha256:" + hashlib.sha256(expected).hexdigest()
    assert canonical_json_bytes(dict(reversed(list(metadata.items())))) == expected


class JsonIdentityTests(unittest.TestCase):
    def test_independent_literal_vectors(self):
        fixtures = [
            ({"z": [True, None, 1.0], "a": "文档"}, '{"a":"文档","z":[true,null,1.0]}'.encode()),
            ({"b": -0.0, "a": 1}, b'{"a":1,"b":-0.0}'),
            ([], b"[]"), ({}, b"{}"),
        ]
        for value, expected in fixtures:
            with self.subTest(value=value):
                self.assertEqual(canonical_json_bytes(value), expected)
                self.assertEqual(canonical_json_digest(value), "sha256:" + hashlib.sha256(expected).hexdigest())

    def test_generated_metadata_identity(self):
        check_sorted_metadata_bytes()

    def test_nonfinite_numbers_remain_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_json_bytes(value)
