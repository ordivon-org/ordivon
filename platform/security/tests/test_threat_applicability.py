import json
import unittest
from pathlib import Path

from ordivon_security_v2.subject_exposure import build_subject_exposure_snapshot
from ordivon_security_v2.threat_applicability import (
    fuse_threat_applicability,
    project_csaf_product_status,
    project_cyclonedx_vex_state,
)

D1 = "sha256:" + "1" * 64
D2 = "sha256:" + "2" * 64
D3 = "sha256:" + "3" * 64
FIXTURE = Path(__file__).parents[1] / "fixtures" / "dw02" / "exchange-replay-r1.json"


def subject(*, include_identity=True):
    identities = []
    if include_identity:
        identities = [
            {
                "id": "product",
                "ownerId": "fixture-owner",
                "sourceRef": "fixture://exchange/product",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "CURRENT_DECLARED",
                "observedAt": "2026-10-01T12:00:00+08:00",
                "evidenceRefs": ["fixture:evidence:product"],
                "dimension": "product",
                "identityRef": {
                    "scheme": "fixture-product",
                    "value": "exchange-server",
                },
            },
            {
                "id": "version",
                "ownerId": "fixture-owner",
                "sourceRef": "fixture://exchange/version",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "CURRENT_DECLARED",
                "observedAt": "2026-10-01T12:00:00+08:00",
                "evidenceRefs": ["fixture:evidence:version"],
                "dimension": "version",
                "identityRef": {
                    "scheme": "fixture-version",
                    "value": "exchange-test-build",
                },
            },
        ]
    return build_subject_exposure_snapshot(
        case_ref="case:dw02:test",
        epoch_ref="epoch:20261001",
        subject_ref="service:exchange:mail-01",
        identity_observations=identities,
        exposure_observations=[
            {
                "id": "https-surface",
                "ownerId": "fixture-network-owner",
                "sourceRef": "fixture://exchange/https",
                "sourceKind": "direct-owner-observation",
                "currentnessStanding": "CURRENT_DECLARED",
                "observedAt": "2026-10-01T12:00:00+08:00",
                "evidenceRefs": ["fixture:evidence:https"],
                "surfaceId": "https",
                "endpointRef": "https://mail.example.invalid",
                "originScope": "fixture",
                "transport": "tcp/443",
                "reachability": "REACHABLE",
            }
        ],
        required_identity_dimensions=["product", "version"],
        expected_exposure_surfaces=["https"],
        non_claims=["synthetic-test-subject"],
    )


SUBJECT = subject()


def binding(value=SUBJECT):
    return {
        "subjectRef": value["subjectRef"],
        "snapshotDigest": value["snapshotDigest"],
        "evidenceRef": value["evidenceRef"],
    }


def ev(
    ref,
    kind,
    *,
    cve="CVE-2021-26855",
    applicability=None,
    currentness="CURRENT",
    admission="ADMITTED",
    digest=D1,
    known_exploited=None,
    epss=None,
    bound_subject=SUBJECT,
):
    item = {
        "evidenceRef": ref,
        "sourceKind": kind,
        "providerNativeRef": f"fixture://{ref}",
        "artifactDigest": digest,
        "vulnerabilityRef": cve,
        "admission": admission,
        "currentness": currentness,
    }
    if kind in {"vendor-advisory", "csaf", "cyclonedx-vex", "local-observation"}:
        item["subjectBinding"] = binding(bound_subject)
    if applicability is not None:
        item["projectedApplicability"] = applicability
    if known_exploited is not None:
        item["knownExploited"] = known_exploited
    if epss is not None:
        item["epss"] = epss
    return item


class ThreatApplicabilityProjectionTests(unittest.TestCase):
    def test_standard_native_state_projection(self):
        self.assertEqual(project_csaf_product_status("known_affected"), "AFFECTED")
        self.assertEqual(project_csaf_product_status("fixed"), "NOT_AFFECTED")
        self.assertEqual(
            project_csaf_product_status("under_investigation"), "UNDER_INVESTIGATION"
        )
        self.assertEqual(project_csaf_product_status("unknown"), "UNDER_INVESTIGATION")
        self.assertEqual(project_cyclonedx_vex_state("exploitable"), "AFFECTED")
        self.assertEqual(project_cyclonedx_vex_state("resolved"), "NOT_AFFECTED")
        self.assertEqual(
            project_cyclonedx_vex_state("in_triage"), "UNDER_INVESTIGATION"
        )

    def test_real_dw01_snapshot_contract_is_bound(self):
        result = fuse_threat_applicability(
            subject=SUBJECT,
            vulnerability_ref="CVE-2021-26855",
            evidence=[ev("local", "local-observation", applicability="AFFECTED")],
        )
        self.assertEqual(result["subject"]["kind"], "ordivon.security.dwc-subject-exposure-snapshot")
        self.assertEqual(result["subject"]["snapshotDigest"], SUBJECT["snapshotDigest"])
        self.assertEqual(result["subject"]["identityCoverageStanding"], "COMPLETE")

    def test_exchange_historical_fixture_replays_proxylogon_and_proxyshell(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        expected = {
            "exchange-proxylogon-2021": {
                "CVE-2021-26855",
                "CVE-2021-26857",
                "CVE-2021-26858",
                "CVE-2021-27065",
            },
            "exchange-proxyshell-2021": {
                "CVE-2021-34473",
                "CVE-2021-34523",
                "CVE-2021-31207",
            },
        }
        self.assertEqual(
            {case["id"]: set(case["vulnerabilities"]) for case in fixture["cases"]},
            expected,
        )

        for case in fixture["cases"]:
            self.assertEqual(case["expectedProductStatusProjection"], "AFFECTED")
            self.assertEqual(case["expectedThreatSignal"], "KNOWN_EXPLOITED")
            for cve in case["vulnerabilities"]:
                with self.subTest(case=case["id"], cve=cve):
                    result = fuse_threat_applicability(
                        subject=SUBJECT,
                        vulnerability_ref=cve,
                        evidence=[
                            ev(
                                f"{case['id']}-product-status-{cve}",
                                "csaf",
                                cve=cve,
                                applicability=project_csaf_product_status("known_affected"),
                            ),
                            ev(
                                f"{case['id']}-kev-{cve}",
                                "cisa-kev",
                                cve=cve,
                                digest=D2,
                                known_exploited=True,
                            ),
                        ],
                    )
                    self.assertEqual(result["claim"], "AFFECTED")
                    self.assertTrue(result["threatSignals"]["knownExploited"])

    def test_proxylogon_style_vendor_plus_kev_is_affected(self):
        result = fuse_threat_applicability(
            subject=SUBJECT,
            vulnerability_ref="CVE-2021-26855",
            evidence=[
                ev("msrc-2021-03", "vendor-advisory", applicability="AFFECTED"),
                ev("cisa-kev", "cisa-kev", known_exploited=True, digest=D2),
            ],
        )
        self.assertEqual(result["claim"], "AFFECTED")
        self.assertTrue(result["threatSignals"]["knownExploited"])
        self.assertEqual(result["claimBasisEvidenceRefs"], ["msrc-2021-03"])

    def test_current_local_clearance_can_produce_not_affected(self):
        result = fuse_threat_applicability(
            subject=SUBJECT,
            vulnerability_ref="CVE-2021-26855",
            evidence=[
                ev(
                    "fresh-local-clearance",
                    "local-observation",
                    applicability="NOT_AFFECTED",
                )
            ],
        )
        self.assertEqual(result["claim"], "NOT_AFFECTED")
        self.assertEqual(result["claimBasisEvidenceRefs"], ["fresh-local-clearance"])

    def test_incomplete_dw01_identity_blocks_definitive_applicability(self):
        incomplete = subject(include_identity=False)
        result = fuse_threat_applicability(
            subject=incomplete,
            vulnerability_ref="CVE-2021-26855",
            evidence=[
                ev(
                    "adverse-but-underbound",
                    "csaf",
                    applicability="AFFECTED",
                    bound_subject=incomplete,
                )
            ],
        )
        self.assertEqual(incomplete["identityCoverageStanding"], "INCOMPLETE")
        self.assertEqual(result["claim"], "UNDER_INVESTIGATION")
        self.assertEqual(
            result["conflicts"][0]["kind"],
            "DW01_IDENTITY_BINDING_NOT_CURRENT_COMPLETE",
        )

    def test_kev_and_epss_never_mint_local_applicability(self):
        result = fuse_threat_applicability(
            subject=SUBJECT,
            vulnerability_ref="CVE-2021-26855",
            evidence=[
                ev("cisa-kev", "cisa-kev", known_exploited=True),
                ev(
                    "first-epss",
                    "first-epss",
                    digest=D2,
                    epss={
                        "probability": 0.91,
                        "percentile": 0.99,
                        "date": "2026-10-01",
                    },
                ),
            ],
        )
        self.assertEqual(result["claim"], "UNDER_INVESTIGATION")
        self.assertEqual(result["claimBasisEvidenceRefs"], [])
        self.assertTrue(result["threatSignals"]["knownExploited"])
        self.assertEqual(result["threatSignals"]["epss"][0]["probability"], 0.91)

    def test_current_vex_local_contradiction_stays_explicit(self):
        result = fuse_threat_applicability(
            subject=SUBJECT,
            vulnerability_ref="CVE-2021-26855",
            evidence=[
                ev("vendor-vex", "cyclonedx-vex", applicability="NOT_AFFECTED"),
                ev("local-version", "local-observation", applicability="AFFECTED", digest=D2),
            ],
        )
        self.assertEqual(result["claim"], "UNDER_INVESTIGATION")
        self.assertEqual(
            result["conflicts"][0]["kind"], "CURRENT_APPLICABILITY_CONTRADICTION"
        )

    def test_stale_adverse_feed_blocks_current_clearance(self):
        result = fuse_threat_applicability(
            subject=SUBJECT,
            vulnerability_ref="CVE-2021-26855",
            evidence=[
                ev(
                    "old-vendor-feed",
                    "csaf",
                    applicability="AFFECTED",
                    currentness="STALE",
                ),
                ev(
                    "fresh-local-version",
                    "local-observation",
                    applicability="NOT_AFFECTED",
                    digest=D2,
                ),
            ],
        )
        self.assertEqual(result["claim"], "UNDER_INVESTIGATION")
        self.assertEqual(result["currentness"]["applicabilityStanding"], "MIXED_HORIZON")
        self.assertEqual(
            result["conflicts"][0]["kind"],
            "NONCURRENT_ADVERSE_VS_CURRENT_CLEARANCE",
        )

    def test_stale_clearance_does_not_weaken_current_affected(self):
        result = fuse_threat_applicability(
            subject=SUBJECT,
            vulnerability_ref="CVE-2021-26855",
            evidence=[
                ev(
                    "current-local",
                    "local-observation",
                    applicability="AFFECTED",
                ),
                ev(
                    "old-clearance",
                    "csaf",
                    applicability="NOT_AFFECTED",
                    currentness="STALE",
                    digest=D2,
                ),
            ],
        )
        self.assertEqual(result["claim"], "AFFECTED")

    def test_unverified_feed_cannot_mint_clearance(self):
        result = fuse_threat_applicability(
            subject=SUBJECT,
            vulnerability_ref="CVE-2021-26855",
            evidence=[
                ev(
                    "unsigned-vex",
                    "cyclonedx-vex",
                    applicability="NOT_AFFECTED",
                    admission="UNVERIFIED",
                )
            ],
        )
        self.assertEqual(result["claim"], "UNDER_INVESTIGATION")
        self.assertEqual(result["unadmittedEvidenceRefs"], ["unsigned-vex"])

    def test_subject_mismatch_fails_closed(self):
        item = ev("wrong-subject", "csaf", applicability="AFFECTED")
        item["subjectBinding"]["snapshotDigest"] = D3
        item["subjectBinding"]["evidenceRef"] = f"dwc-subject-exposure:{D3}"
        with self.assertRaisesRegex(ValueError, "does not match DW01 subject"):
            fuse_threat_applicability(
                subject=SUBJECT,
                vulnerability_ref="CVE-2021-26855",
                evidence=[item],
            )

    def test_global_signal_cannot_smuggle_applicability(self):
        item = ev("kev", "cisa-kev", known_exploited=True)
        item["projectedApplicability"] = "AFFECTED"
        item["subjectBinding"] = binding()
        with self.assertRaisesRegex(ValueError, "CISA KEV cannot determine local applicability"):
            fuse_threat_applicability(
                subject=SUBJECT,
                vulnerability_ref="CVE-2021-26855",
                evidence=[item],
            )


if __name__ == "__main__":
    unittest.main()
