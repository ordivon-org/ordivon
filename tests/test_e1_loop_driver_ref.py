from __future__ import annotations

import unittest

from ordivon_harness.loop_driver import HarnessLoopDriverRef


class E1LoopDriverRefTests(unittest.TestCase):
    def test_ref_round_trip_preserves_exact_identity(self) -> None:
        ref = HarnessLoopDriverRef(
            driver_id="loop-driver:sequential-v1",
            driver_digest="sha256:" + "a" * 64,
        )
        self.assertEqual(HarnessLoopDriverRef.from_dict(ref.to_dict()), ref)

    def test_ref_rejects_noncanonical_digest(self) -> None:
        with self.assertRaisesRegex(ValueError, "sha256"):
            HarnessLoopDriverRef("loop-driver:bad", "sha256:" + "A" * 64)

    def test_typed_ref_is_identity_only(self) -> None:
        ref = HarnessLoopDriverRef(
            driver_id="loop-driver:no-exec",
            driver_digest="sha256:" + "c" * 64,
        )
        for forbidden in ("build", "load", "execute", "reload", "factory"):
            self.assertFalse(hasattr(ref, forbidden))


if __name__ == "__main__":
    unittest.main()
