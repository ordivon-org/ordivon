from __future__ import annotations

import unittest

from ordivon_studio.distribution import (
    CURRENT_CARRIER_PROFILES,
    bind_natural_episode,
    carrier_profile,
    correction_disposition,
    delivery_key,
    maturity_observation,
    plan_delivery,
    retry_disposition,
    verify_provider_outcome,
)


DIGEST = "sha256:" + "a" * 64


def _published(carrier: str = "x", observed_at_ms: int = 2000) -> dict[str, object]:
    return verify_provider_outcome(
        {
            "carrierId": carrier,
            "providerState": "published",
            "providerObjectId": f"{carrier}:123",
            "statusSource": "provider-native-readback",
            "observedAtMs": observed_at_ms,
            "artifactDigest": DIGEST,
        }
    )


class DistributionTests(unittest.TestCase):
    def test_profiles_are_dated_and_do_not_claim_provider_contract_truth(self) -> None:
        self.assertGreaterEqual(len(CURRENT_CARRIER_PROFILES), 8)
        for carrier_id in CURRENT_CARRIER_PROFILES:
            profile = carrier_profile(carrier_id)
            self.assertEqual(profile["observedOn"], "2026-09-10")
            self.assertIn("not-provider-contract", profile["truthRole"])
            self.assertTrue(str(profile["profileDigest"]).startswith("sha256:"))

    def test_unknown_carrier_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown carrier"):
            carrier_profile("imaginary-network")

    def test_x_public_effect_requires_provider_authorities_then_exact_user_authority(self) -> None:
        blocked = plan_delivery(carrier_id="x", effect="publish_text")
        self.assertEqual(blocked["actionability"], "provider_access_required")
        self.assertIn("x-user-oauth", blocked["missingAuthorities"])
        authorities = set(carrier_profile("x")["authorityRequirements"])
        consent = plan_delivery(
            carrier_id="x",
            effect="publish_text",
            granted_authorities=authorities,
        )
        self.assertEqual(consent["actionability"], "user_action_required")
        self.assertIn("authorize-this-exact-public-effect", consent["userOperations"])
        ready = plan_delivery(
            carrier_id="x",
            effect="publish_text",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        self.assertEqual(ready["actionability"], "ready")
        self.assertFalse(ready["externalEffectPerformed"])

    def test_read_only_effect_does_not_require_per_effect_public_consent(self) -> None:
        authorities = set(carrier_profile("x")["authorityRequirements"])
        plan = plan_delivery(
            carrier_id="x",
            effect="read_back",
            granted_authorities=authorities,
        )
        self.assertEqual(plan["actionability"], "ready")
        self.assertFalse(plan["publicEffect"])

    def test_xiaohongshu_is_human_handoff_not_invented_write_api(self) -> None:
        profile = carrier_profile("xiaohongshu")
        self.assertEqual(profile["executionModes"], ["human-handoff"])
        self.assertIn("not-generally-api-writable", profile["nativeWriteStanding"])
        authorities = set(profile["authorityRequirements"])
        plan = plan_delivery(
            carrier_id="xiaohongshu",
            effect="publish_image",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        self.assertEqual(plan["actionability"], "user_action_required")
        self.assertIn("perform-provider-final-action", plan["userOperations"])
        with self.assertRaisesRegex(ValueError, "execution mode"):
            plan_delivery(
                carrier_id="xiaohongshu",
                effect="publish_image",
                granted_authorities=authorities,
                explicit_user_authority=True,
                execution_mode="api",
            )

    def test_tiktok_public_path_separates_reusable_authority_from_per_effect_consent(self) -> None:
        plan = plan_delivery(carrier_id="tiktok", effect="publish_video")
        self.assertEqual(plan["actionability"], "provider_access_required")
        self.assertIn("tiktok-public-client-audit", plan["missingAuthorities"])
        self.assertNotIn("tiktok-explicit-post-consent", plan["missingAuthorities"])
        authorities = set(carrier_profile("tiktok")["authorityRequirements"])
        interaction_blocked = plan_delivery(
            carrier_id="tiktok",
            effect="publish_video",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        self.assertEqual(interaction_blocked["actionability"], "user_action_required")
        self.assertIn("tiktok-current-creator-info-query", interaction_blocked["missingInteractions"])
        self.assertIn("tiktok-user-provided-post-metadata", interaction_blocked["missingInteractions"])
        self.assertIn("tiktok-explicit-post-consent", interaction_blocked["missingInteractions"])

    def test_douyin_preserves_per_post_perceptibility_and_review_as_distinct_boundaries(self) -> None:
        authorities = set(carrier_profile("douyin")["authorityRequirements"])
        plan = plan_delivery(
            carrier_id="douyin",
            effect="publish_video",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        self.assertEqual(plan["actionability"], "user_action_required")
        self.assertIn("douyin-user-perceivable-per-post-action", plan["missingInteractions"])
        evidence = verify_provider_outcome(
            {
                "carrierId": "douyin",
                "providerState": "processing",
                "providerObjectId": "video-1",
                "statusSource": "provider-native-readback",
                "observedAtMs": 100,
                "artifactDigest": DIGEST,
            }
        )
        self.assertFalse(evidence["acceptedPublication"])
        self.assertFalse(evidence["deliveryTerminal"])

    def test_reddit_requires_explicit_manual_user_action_after_reusable_access(self) -> None:
        authorities = set(carrier_profile("reddit")["authorityRequirements"])
        plan = plan_delivery(
            carrier_id="reddit",
            effect="publish_text",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        self.assertEqual(plan["actionability"], "user_action_required")
        self.assertEqual(plan["missingInteractions"], ["reddit-explicit-manual-user-action"])

    def test_http_or_process_success_cannot_substitute_for_provider_readback(self) -> None:
        evidence = verify_provider_outcome(
            {
                "carrierId": "x",
                "providerState": "published",
                "providerObjectId": "tweet-1",
                "statusSource": "runtime-process-success",
                "observedAtMs": 100,
                "artifactDigest": DIGEST,
            }
        )
        self.assertFalse(evidence["acceptedPublication"])

    def test_published_without_provider_identity_is_not_accepted(self) -> None:
        evidence = verify_provider_outcome(
            {
                "carrierId": "x",
                "providerState": "published",
                "providerObjectId": None,
                "statusSource": "provider-native-readback",
                "observedAtMs": 100,
                "artifactDigest": DIGEST,
            }
        )
        self.assertFalse(evidence["acceptedPublication"])

    def test_provider_native_published_identity_is_carrier_acceptance_only(self) -> None:
        evidence = _published()
        self.assertTrue(evidence["acceptedPublication"])
        self.assertFalse(evidence["semanticCompletionEvaluated"])
        self.assertIn("does not prove audience reception", evidence["truthBoundary"])

    def test_ambiguous_and_processing_outcomes_forbid_blind_resend(self) -> None:
        for state in ("submitted", "processing", "unknown"):
            decision = retry_disposition(provider_state=state, provider_object_id="maybe-1")
            self.assertEqual(decision["disposition"], "requery-provider-do-not-resend")
            self.assertFalse(decision["blindResendPermitted"])

    def test_only_predispatch_prepared_state_has_safe_retry_disposition(self) -> None:
        decision = retry_disposition(provider_state="prepared")
        self.assertEqual(decision["disposition"], "safe-only-before-dispatch")
        self.assertFalse(decision["blindResendPermitted"])

    def test_published_never_resends(self) -> None:
        decision = retry_disposition(provider_state="published", provider_object_id="post-1")
        self.assertEqual(decision["disposition"], "accepted-do-not-resend")
        self.assertFalse(decision["blindResendPermitted"])

    def test_delivery_key_binds_intent_not_only_artifact(self) -> None:
        first = delivery_key(
            carrier_id="x",
            account_identity="account:opaque-a",
            artifact_digest=DIGEST,
            effect="publish_text",
            intent_id="intent:1",
        )
        second = delivery_key(
            carrier_id="x",
            account_identity="account:opaque-a",
            artifact_digest=DIGEST,
            effect="publish_text",
            intent_id="intent:2",
        )
        self.assertNotEqual(first, second)

    def test_correction_is_capability_specific_and_preserves_provider_constraints(self) -> None:
        x_delete = correction_disposition(carrier_id="x", requested_effect="delete")
        self.assertTrue(x_delete["supportedByCurrentProfile"])
        self.assertIn("delete-any-version-deletes-entire-edit-chain", x_delete["constraintsToReobserve"])
        x_edit = correction_disposition(carrier_id="x", requested_effect="correct")
        self.assertIn("correct-within-30-minutes-of-original-post", x_edit["constraintsToReobserve"])
        self.assertIn("correct-maximum-5-edits", x_edit["constraintsToReobserve"])
        self.assertIn("correct-creates-new-provider-object-id", x_edit["constraintsToReobserve"])
        self.assertFalse(correction_disposition(carrier_id="tiktok", requested_effect="delete")["supportedByCurrentProfile"])

    def test_natural_episode_rejects_maturity_test_publication(self) -> None:
        authorities = set(carrier_profile("x")["authorityRequirements"])
        plan = plan_delivery(
            carrier_id="x",
            effect="publish_text",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        with self.assertRaisesRegex(ValueError, "synthetic publication"):
            bind_natural_episode(
                plan=plan,
                outcome=_published(),
                goal_relevance="test architecture",
                initiated_for="maturity-test",
                user_authorized_at_ms=1000,
            )

    def test_natural_episode_requires_provider_native_acceptance(self) -> None:
        authorities = set(carrier_profile("x")["authorityRequirements"])
        plan = plan_delivery(
            carrier_id="x",
            effect="publish_text",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        weak = verify_provider_outcome(
            {
                "carrierId": "x",
                "providerState": "submitted",
                "providerObjectId": "tweet-1",
                "statusSource": "provider-native-readback",
                "observedAtMs": 2000,
                "artifactDigest": DIGEST,
            }
        )
        with self.assertRaisesRegex(ValueError, "accepted publication"):
            bind_natural_episode(
                plan=plan,
                outcome=weak,
                goal_relevance="real release",
                initiated_for="release-announcement",
                user_authorized_at_ms=1000,
            )

    def test_natural_episode_binds_real_authorized_goal_relative_publication(self) -> None:
        authorities = set(carrier_profile("x")["authorityRequirements"])
        plan = plan_delivery(
            carrier_id="x",
            effect="publish_text",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        episode = bind_natural_episode(
            plan=plan,
            outcome=_published(),
            goal_relevance="announce a real accepted release",
            initiated_for="release-announcement",
            user_authorized_at_ms=1000,
        )
        self.assertFalse(episode["syntheticForMaturity"])
        self.assertTrue(str(episode["episodeDigest"]).startswith("sha256:"))

    def test_maturity_observation_does_not_turn_local_or_single_carrier_evidence_into_default(self) -> None:
        self.assertEqual(maturity_observation([])["standing"], "no-generic-d2-evidence")
        authorities = set(carrier_profile("x")["authorityRequirements"])
        plan = plan_delivery(
            carrier_id="x",
            effect="publish_text",
            granted_authorities=authorities,
            explicit_user_authority=True,
        )
        episode = bind_natural_episode(
            plan=plan,
            outcome=_published(),
            goal_relevance="real release",
            initiated_for="release-announcement",
            user_authorized_at_ms=1000,
        )
        observation = maturity_observation([episode])
        self.assertEqual(observation["standing"], "single-carrier-evidence-only")
        self.assertFalse(observation["defaultClaimed"])

    def test_cross_carrier_repetition_still_requires_independent_adjudication(self) -> None:
        episodes = []
        for index, carrier in enumerate(("x", "youtube", "x"), start=1):
            effect = "publish_text" if carrier == "x" else "publish_video"
            authorities = set(carrier_profile(carrier)["authorityRequirements"])
            plan = plan_delivery(
                carrier_id=carrier,
                effect=effect,
                granted_authorities=authorities,
                explicit_user_authority=True,
            )
            outcome = _published(carrier, observed_at_ms=2000 + index)
            episodes.append(
                bind_natural_episode(
                    plan=plan,
                    outcome=outcome,
                    goal_relevance=f"real release {index}",
                    initiated_for=f"release-announcement-{index}",
                    user_authorized_at_ms=1000,
                )
            )
        observation = maturity_observation(episodes)
        self.assertEqual(observation["carrierCount"], 2)
        self.assertIn("d3-still-requires-independent-adjudication", observation["standing"])
        self.assertFalse(observation["defaultClaimed"])


if __name__ == "__main__":
    unittest.main()
