from __future__ import annotations

import unittest

from artifact_verification.claim_results import (
    build_explicit_claim_results,
    emits_explicit_claim_results,
    emits_profile_explicit_claim_results,
)


class ArtifactClaimResultsTests(unittest.TestCase):
    def test_only_declared_native_status_objects_are_projected(self) -> None:
        native = {
            "status": "PASS",
            "contractSchema": {"status": "PASS"},
            "nested": {"reader": {"status": "FAIL"}},
            "ambiguous": {"ok": True},
        }
        claims = build_explicit_claim_results(
            native,
            {
                "contractSchema": "/contractSchema",
                "readerMatrix": "/nested/reader",
                "missing": "/missing",
                "ambiguous": "/ambiguous",
            },
        )
        self.assertEqual(claims["contractSchema"]["status"], "PASS")
        self.assertEqual(claims["readerMatrix"]["status"], "FAIL")
        self.assertEqual(claims["missing"]["status"], "NOT_EVALUATED")
        self.assertEqual(claims["ambiguous"]["status"], "NOT_EVALUATED")
        self.assertEqual(claims["missing"]["nativePointers"], [])

    def test_overall_status_is_never_implicitly_used(self) -> None:
        claims = build_explicit_claim_results(
            {"status": "PASS"},
            {"requiredClaim": "/requiredClaim"},
        )
        self.assertEqual(claims["requiredClaim"]["status"], "NOT_EVALUATED")

    def test_json_pointer_escaping_is_supported(self) -> None:
        claims = build_explicit_claim_results(
            {"a/b": {"~field": {"status": "PASS"}}},
            {"claim": "/a~1b/~0field"},
        )
        self.assertEqual(claims["claim"]["status"], "PASS")


    def test_decorator_covers_early_return_without_using_overall_status(self) -> None:
        pointers = {"contractSchema": "/contractSchema", "reader": "/reader"}

        @emits_explicit_claim_results(pointers)
        def verifier(fail_early: bool) -> dict[str, object]:
            if fail_early:
                return {"status": "FAIL", "failures": ["precondition"]}
            return {
                "status": "PASS",
                "contractSchema": {"status": "PASS"},
                "reader": {"status": "PASS"},
            }

        early = verifier(True)
        self.assertEqual(early["claimResults"]["contractSchema"]["status"], "NOT_EVALUATED")
        self.assertEqual(early["claimResults"]["reader"]["status"], "NOT_EVALUATED")
        complete = verifier(False)
        self.assertEqual(complete["claimResults"]["contractSchema"]["status"], "PASS")
        self.assertEqual(complete["claimResults"]["reader"]["status"], "PASS")

    def test_profile_decorator_uses_only_exact_explicit_profile_mapping(self) -> None:
        mappings = {
            "a": {"alpha": "/alpha"},
            "b": {"beta": "/beta"},
        }

        @emits_profile_explicit_claim_results(mappings)
        def verifier(profile: str) -> dict[str, object]:
            return {
                "profileId": profile,
                "alpha": {"status": "PASS"},
                "beta": {"status": "PASS"},
            }

        self.assertEqual(set(verifier("a")["claimResults"]), {"alpha"})
        self.assertEqual(set(verifier("b")["claimResults"]), {"beta"})
        self.assertNotIn("claimResults", verifier("unknown"))

    def test_undeclared_claim_metadata_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "undeclared"):
            build_explicit_claim_results(
                {"x": {"status": "PASS"}},
                {"x": "/x"},
                non_claims={"other": ["no"]},
            )


if __name__ == "__main__":
    unittest.main()
