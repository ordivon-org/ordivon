"""Bounded, shrinkable generated tests of the real hosted archive consumer."""
from contextlib import contextmanager
import unittest

import hypothesis
from hypothesis import given, settings, strategies as st

from test_hosted_product_acceptance import ArtifactContract, SOURCE
from hosted_product_acceptance import digest

PROFILE = settings(max_examples=35, deadline=None, derandomize=True, database=None)


@contextmanager
def fixture(**kwargs):
    case = ArtifactContract("test_valid_identity")
    case.setUp()
    try:
        case.fixture(**kwargs)
        yield case
    finally:
        case.doCleanups()


class ConsumerProperties(unittest.TestCase):
    @PROFILE
    @given(payload=st.binary(min_size=1, max_size=4096), reverse=st.booleans())
    def test_valid_payload_roundtrip(self, payload, reverse):
        with fixture(payload=payload, reverse=reverse) as case:
            exe, receipt = case.verify()
            self.assertEqual(exe.read_bytes(), payload)
            self.assertEqual(receipt["executable_sha256"], digest(exe))

    @PROFILE
    @given(field=st.sampled_from(("SOURCE_COMMIT", "PRODUCT", "SOURCE_WORKTREE",
                                 "RELEASE_PUBLISHED", "QUALIFICATION", "LINUX_SCOPE",
                                 "WINDOWS_SCOPE", "BUILD_SCHEMA", "SOURCE_TREE",
                                 "ENGINE_SHA256", "TEMPLATE_LINUX_SHA256",
                                 "TEMPLATE_WINDOWS_SHA256", "ENGINE")),
           value=st.text(alphabet="0123456789xyz_", min_size=1, max_size=12))
    def test_rehashed_invalid_semantics(self, field, value):
        # All generated values deliberately violate these field domains,
        # except BUILD_SCHEMA=1; use a fixed invalid prefix for every field.
        with fixture(fields_override={field: "invalid_" + value}) as case:
            with self.assertRaisesRegex(ValueError, "source receipt differs|incomplete build identity"):
                case.verify()

    @PROFILE
    @given(name=st.text(alphabet="abcXYZ0123456789", min_size=1, max_size=24),
           prefix=st.sampled_from(("../", "/", "./", "nested/", "")))
    def test_unexpected_native_member(self, name, prefix):
        with fixture(native_name=prefix + name) as case:
            with self.assertRaisesRegex(ValueError, "native member not allowed"):
                case.verify()

    @PROFILE
    @given(replacement=st.binary(min_size=1, max_size=4096).filter(lambda b: b != b"fixture-windows"))
    def test_substitution_despite_fresh_outer_hash(self, replacement):
        with fixture(substituted_payload=replacement) as case:
            with self.assertRaisesRegex(ValueError, "manifest digest differs"):
                case.verify()


if __name__ == "__main__":
    print(f"GAME_HYPOTHESIS_VERSION={hypothesis.__version__}", flush=True)
    unittest.main(verbosity=2)
