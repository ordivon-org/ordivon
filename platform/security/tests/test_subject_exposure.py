import unittest

from ordivon_security_v2.subject_exposure import (
    SubjectExposureError,
    build_subject_exposure_snapshot,
)


def identity(
    observation_id: str,
    dimension: str,
    *,
    currentness: str = "POINT_IN_TIME_OBSERVED",
    observed_at: str | None = "2026-10-01T12:00:00+08:00",
) -> dict:
    return {
        "id": observation_id,
        "dimension": dimension,
        "ownerId": "owner:test",
        "sourceRef": f"source:{observation_id}",
        "sourceKind": "direct-owner-observation",
        "identityRef": {"scheme": "owner-native", "value": f"value:{observation_id}"},
        "currentnessStanding": currentness,
        "observedAt": observed_at,
        "evidenceRefs": [f"evidence:{observation_id}"],
    }


def exposure(
    observation_id: str,
    surface_id: str,
    *,
    reachability: str = "REACHABLE",
    currentness: str = "POINT_IN_TIME_OBSERVED",
    observed_at: str | None = "2026-10-01T12:00:00+08:00",
) -> dict:
    return {
        "id": observation_id,
        "surfaceId": surface_id,
        "ownerId": "owner:network",
        "sourceRef": f"source:{observation_id}",
        "sourceKind": "direct-owner-observation",
        "endpointRef": f"endpoint:{surface_id}",
        "originScope": "probe:test",
        "transport": "tcp",
        "reachability": reachability,
        "currentnessStanding": currentness,
        "observedAt": observed_at,
        "evidenceRefs": [f"evidence:{observation_id}"],
    }


class SubjectExposureSnapshotTests(unittest.TestCase):
    def build(self, identities=None, exposures=None, required=None, surfaces=None):
        return build_subject_exposure_snapshot(
            case_ref="case:test",
            epoch_ref="epoch:test",
            subject_ref="subject:test",
            identity_observations=identities or [],
            exposure_observations=exposures or [],
            required_identity_dimensions=required or [],
            expected_exposure_surfaces=surfaces or [],
        )

    def test_complete_current_binding(self) -> None:
        result = self.build(
            identities=[
                identity("id-product", "product"),
                identity("id-deployment", "deployment"),
            ],
            exposures=[exposure("exp-api", "api")],
            required=["product", "deployment"],
            surfaces=["api"],
        )
        self.assertEqual(result["mechanicalBindingStanding"], "COMPLETE")
        self.assertEqual(result["identityCoverageStanding"], "COMPLETE")
        self.assertEqual(result["exposureCoverageStanding"], "COMPLETE")
        self.assertEqual(result["reachableSurfaceIds"], ["api"])
        self.assertFalse(result["domainAcceptanceEstablished"])

    def test_order_does_not_change_snapshot_digest(self) -> None:
        ids = [identity("id-product", "product"), identity("id-deployment", "deployment")]
        exps = [exposure("exp-a", "a"), exposure("exp-b", "b")]
        first = self.build(ids, exps, ["product", "deployment"], ["a", "b"])
        second = self.build(
            list(reversed(ids)),
            list(reversed(exps)),
            ["deployment", "product"],
            ["b", "a"],
        )
        self.assertEqual(first["snapshotDigest"], second["snapshotDigest"])

    def test_missing_required_dimension_is_incomplete(self) -> None:
        result = self.build(
            identities=[identity("id-product", "product")],
            required=["product", "deployment"],
        )
        self.assertEqual(result["mechanicalBindingStanding"], "INCOMPLETE")
        self.assertEqual(result["identityDimensionStanding"]["deployment"], "MISSING")

    def test_historical_required_dimension_fails_closed(self) -> None:
        result = self.build(
            identities=[
                identity(
                    "id-product",
                    "product",
                    currentness="HISTORICAL_NOT_CURRENT",
                )
            ],
            required=["product"],
        )
        self.assertEqual(result["mechanicalBindingStanding"], "HISTORICAL_ONLY")
        self.assertEqual(result["observationHorizonStanding"], "STALE_PRESENT")

    def test_unknown_reachability_is_not_rewritten_as_unreachable(self) -> None:
        result = self.build(
            identities=[identity("id-product", "product")],
            exposures=[exposure("exp-api", "api", reachability="UNKNOWN")],
            required=["product"],
            surfaces=["api"],
        )
        self.assertEqual(result["exposureCoverageStanding"], "COMPLETE")
        self.assertEqual(result["unknownReachabilitySurfaceIds"], ["api"])
        self.assertEqual(result["unreachableSurfaceIds"], [])

    def test_mixed_horizon_is_visible_without_destroying_observations(self) -> None:
        result = self.build(
            identities=[
                identity("id-product", "product", observed_at="2026-10-01T12:00:00+08:00"),
                identity("id-deploy", "deployment", observed_at="2026-10-01T12:01:00+08:00"),
            ],
            required=["product", "deployment"],
        )
        self.assertEqual(result["mechanicalBindingStanding"], "COMPLETE")
        self.assertEqual(result["observationHorizonStanding"], "MIXED_HORIZON")

    def test_duplicate_observation_ids_fail_closed(self) -> None:
        with self.assertRaisesRegex(SubjectExposureError, "observation ids must be unique"):
            self.build(
                identities=[identity("same", "product")],
                exposures=[exposure("same", "api")],
            )


if __name__ == "__main__":
    unittest.main()
