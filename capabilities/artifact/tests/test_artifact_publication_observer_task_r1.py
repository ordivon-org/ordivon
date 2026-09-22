from __future__ import annotations

import unittest

from artifact_capabilities.publication.observer_task import (
    build_observer_task_envelope,
    canonical_json_sha256,
)


class PublicationObserverTaskR1Tests(unittest.TestCase):
    def test_task_envelope_binds_role_scope_and_carrier(self) -> None:
        carrier = "sha256:" + "a" * 64
        value = build_observer_task_envelope(
            task_id="PC10-PAPER3-R1",
            role="BLIND_VISION",
            carrier_sha256=carrier,
            allowed_read=["page-raster/"],
            forbidden_read=["manuscript-source", "observer-results/"],
            required_outputs=["observer-a-r1.json"],
            acceptance_predicates=["PAGE_COVERAGE_100_PERCENT"],
        )
        self.assertEqual(value["carrierSha256"], carrier)
        self.assertEqual(value["role"], "BLIND_VISION")
        self.assertTrue(value["inputViewDigest"].startswith("sha256:"))

    def test_task_scope_rejects_overlap(self) -> None:
        with self.assertRaises(ValueError):
            build_observer_task_envelope(
                task_id="PC10",
                role="BLIND_VISION",
                carrier_sha256="sha256:" + "a" * 64,
                allowed_read=["source"],
                forbidden_read=["source"],
                required_outputs=["report.json"],
                acceptance_predicates=["COVERAGE"],
            )

    def test_canonical_json_digest_is_order_stable(self) -> None:
        self.assertEqual(
            canonical_json_sha256({"b": 2, "a": 1}),
            canonical_json_sha256({"a": 1, "b": 2}),
        )


if __name__ == "__main__":
    unittest.main()
