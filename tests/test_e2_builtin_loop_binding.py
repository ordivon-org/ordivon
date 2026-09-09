from __future__ import annotations

import unittest

from ordivon_harness.loop_driver import (
    DELIBERATE_THEN_ACT_LOOP_DRIVER,
    HarnessLoopDriverIdentity,
    HarnessLoopDriverRef,
    SEQUENTIAL_LOOP_DRIVER,
    builtin_scheduling_mode,
)
from anc_canonical import canonical_digest
from dataclasses import replace

from ordivon_harness.core_contracts import HarnessBoundReference
from tests.test_p0_core_contracts import contract


def bound_contract(ref, suffix: str):
    manifest = {
        "schemaVersion": 1,
        "kind": "test-loop-driver-manifest",
        "loopDriver": ref.to_dict(),
    }
    base = contract()
    run_id = f"harness-run:loop:{suffix}"
    value = replace(
        base,
        harness_run_id=run_id,
        caller_run_ref=f"trial:loop:{suffix}",
        system_manifest_ref=HarnessBoundReference(
            f"system-manifest:loop:{suffix}",
            "system-manifest",
            canonical_digest(manifest),
        ),
    )
    return value, manifest


class E2BuiltinLoopBindingTests(unittest.TestCase):
    def _identity(self, ref: HarnessLoopDriverRef, suffix: str):
        value, manifest = bound_contract(ref, suffix)
        return HarnessLoopDriverIdentity.from_contract_manifest(value, manifest, driver=ref)

    def test_builtin_modes_require_exact_manifest_bound_identity(self) -> None:
        for ref, expected in (
            (SEQUENTIAL_LOOP_DRIVER, "sequential"),
            (DELIBERATE_THEN_ACT_LOOP_DRIVER, "deliberate_then_act"),
        ):
            with self.subTest(driver=ref.driver_id):
                identity = self._identity(ref, ref.driver_id.rsplit(":", 1)[-1])
                self.assertEqual(builtin_scheduling_mode(identity), expected)

    def test_unknown_exact_driver_is_identified_but_not_executable(self) -> None:
        unknown = HarnessLoopDriverRef(
            driver_id="loop-driver:future-v1",
            driver_digest="sha256:" + "f" * 64,
        )
        identity = self._identity(unknown, "future")
        with self.assertRaisesRegex(ValueError, "no admitted built-in executable implementation"):
            builtin_scheduling_mode(identity)

    def test_absent_driver_preserves_historical_sequential_default(self) -> None:
        self.assertEqual(builtin_scheduling_mode(None), "sequential")


if __name__ == "__main__":
    unittest.main()
