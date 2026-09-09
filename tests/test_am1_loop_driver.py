from __future__ import annotations

import inspect
import unittest

from ordivon_harness.loop_driver import HarnessLoopDriverIdentity, HarnessLoopDriverRef
from ordivon_harness.standalone import StandaloneHarnessRunner
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

D = "sha256:" + "e" * 64


class AM1LoopDriverTests(unittest.TestCase):
    def _bound(self):
        ref = HarnessLoopDriverRef("loop-driver:experimental-a", D)
        value, manifest = bound_contract(ref, "am1-binding")
        return value, manifest, ref

    def test_identity_requires_exact_manifest_and_driver(self) -> None:
        value, manifest, ref = self._bound()
        identity = HarnessLoopDriverIdentity.from_contract_manifest(value, manifest, driver=ref)
        self.assertEqual(identity.system_manifest_digest, value.system_manifest_ref.digest)
        identity.require_contract(value.system_manifest_ref.digest)

        wrong = HarnessLoopDriverRef("loop-driver:experimental-b", D)
        with self.assertRaisesRegex(ValueError, "manifest declaration"):
            HarnessLoopDriverIdentity.from_contract_manifest(value, manifest, driver=wrong)

    def test_manifest_bytes_must_match_contract_digest(self) -> None:
        value, manifest, ref = self._bound()
        changed = dict(manifest)
        changed["extra"] = True
        with self.assertRaisesRegex(ValueError, "differs from the Run Contract"):
            HarnessLoopDriverIdentity.from_contract_manifest(value, changed, driver=ref)

    def test_identity_cannot_attach_to_another_manifest(self) -> None:
        value, manifest, ref = self._bound()
        identity = HarnessLoopDriverIdentity.from_contract_manifest(value, manifest, driver=ref)
        with self.assertRaisesRegex(ValueError, "belongs to another Run manifest"):
            identity.require_contract("sha256:" + "f" * 64)

    def test_identity_object_exposes_no_executable_factory_surface(self) -> None:
        value, manifest, ref = self._bound()
        identity = HarnessLoopDriverIdentity.from_contract_manifest(value, manifest, driver=ref)
        for forbidden in ("factory", "build", "load", "reload"):
            self.assertFalse(hasattr(identity, forbidden))
        self.assertNotIn(
            "loop_driver_binding",
            inspect.signature(StandaloneHarnessRunner.__init__).parameters,
        )


if __name__ == "__main__":
    unittest.main()
