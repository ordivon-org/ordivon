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
    verify_provider_outcome,
)


DIGEST = "sha256:" + "a" * 64
OTHER_DIGEST = "sha256:" + "b" * 64


def _authorities(carrier: str, effect: str) -> set[str]:
    profile = carrier_profile(carrier)
    return set(profile["effectAuthorityRequirements"].get(effect, profile["authorityRequirements"]))


def _interactions(carrier: str) -> set[str]:
    return set(carrier_profile(carrier)["interactionRequirements"])


def _plan(
    carrier: str = "x",
    effect: str = "publish_text",
    *,
    index: int = 1,
    authorities: set[str] | None = None,
    interactions: set[str] | None = None,
    explicit: bool = True,
) -> dict[str, object]:
    public = effect.startswith("publish_") or effect in {"correct", "withdraw", "delete"}
    kwargs: dict[str, object] = {
        "carrier_id": carrier,
        "effect": effect,
        "granted_authorities": _authorities(carrier, effect) if authorities is None else authorities,
        "satisfied_interactions": _interactions(carrier) if interactions is None and public else (interactions or set()),
        "explicit_user_authority": explicit,
    }
    if public:
        kwargs.update(
            account_identity=f"account:{carrier}:opaque",
            artifact_digest=DIGEST,
            intent_id=f"intent:{carrier}:{effect}:{index}",
        )
    return plan_delivery(**kwargs)


def _outcome(
    plan: dict[str, object],
    *,
    state: str | None = None,
    observed_at_ms: int = 2000,
    artifact_digest: str | None = None,
    status_source: str = "provider-native-readback",
) -> dict[str, object]:
    effect = str(plan["effect"])
    if state is None:
        state = "deleted" if effect == "delete" else "withdrawn" if effect == "withdraw" else "published"
    return verify_provider_outcome(
        {
            "carrierId": plan["carrierId"],
            "effect": effect,
            "deliveryKey": plan["deliveryKey"],
            "providerState": state,
            "providerObjectId": f"{plan['carrierId']}:123",
            "statusSource": status_source,
            "observedAtMs": observed_at_ms,
            "artifactDigest": artifact_digest or str(plan["artifactDigest"]),
        }
    )


def _episode(
    carrier: str,
    effect: str,
    *,
    index: int,
    recovery: str | None = None,
) -> dict[str, object]:
    plan = _plan(carrier, effect, index=index)
    return bind_natural_episode(
        plan=plan,
        outcome=_outcome(plan, observed_at_ms=2000 + index),
        goal_relevance=f"real distribution need {index}",
        initiated_for=f"release-or-correction-{index}",
        user_authorized_at_ms=1000,
        recovery_evidence_ref=recovery,
    )


class DistributionTests(unittest.TestCase):
    def test_profiles_are_dated_and_do_not_claim_provider_contract_truth(self) -> None:
        self.assertGreaterEqual(len(CURRENT_CARRIER_PROFILES), 8)
        for carrier_id in CURRENT_CARRIER_PROFILES:
            profile = carrier_profile(carrier_id)
            self.assertEqual(profile["observedOn"], "2026-09-10")
            self.assertIn("not-provider-contract", profile["truthRole"])
            self.assertIn("effectAuthorityRequirements", profile)
            self.assertTrue(str(profile["profileDigest"]).startswith("sha256:"))

    def test_unknown_carrier_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown carrier"):
            carrier_profile("imaginary-network")

    def test_public_effect_requires_exact_delivery_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "exact account_identity"):
            plan_delivery(carrier_id="x", effect="publish_text")

    def test_partial_delivery_identity_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "provide account_identity"):
            plan_delivery(carrier_id="x", effect="read_back", account_identity="account:x")

    def test_x_public_effect_requires_minimal_provider_authority_then_user_authority(self) -> None:
        blocked = _plan("x", "publish_text", authorities=set(), explicit=False)
        self.assertEqual(blocked["actionability"], "provider_access_required")
        self.assertIn("x-tweet.write-scope", blocked["missingAuthorities"])
        consent = _plan("x", "publish_text", explicit=False)
        self.assertEqual(consent["actionability"], "user_action_required")
        self.assertIn("authorize-this-exact-public-effect", consent["userOperations"])
        ready = _plan("x", "publish_text")
        self.assertEqual(ready["actionability"], "ready")
        self.assertTrue(str(ready["deliveryKey"]).startswith("sha256:"))
        self.assertFalse(ready["externalEffectPerformed"])

    def test_read_only_effect_uses_read_scope_not_write_scope_or_public_consent(self) -> None:
        profile = carrier_profile("x")
        required = set(profile["effectAuthorityRequirements"]["read_back"])
        self.assertIn("x-tweet.read-scope", required)
        self.assertNotIn("x-tweet.write-scope", required)
        plan = _plan("x", "read_back", authorities=required, explicit=False)
        self.assertEqual(plan["actionability"], "ready")
        self.assertFalse(plan["publicEffect"])
        self.assertEqual(plan["missingInteractions"], [])

    def test_youtube_readback_does_not_request_upload_scope(self) -> None:
        profile = carrier_profile("youtube")
        read_required = set(profile["effectAuthorityRequirements"]["read_back"])
        publish_required = set(profile["effectAuthorityRequirements"]["publish_video"])
        self.assertNotIn("youtube.upload-scope", read_required)
        self.assertIn("youtube.upload-scope", publish_required)
        self.assertIn("youtube-public-upload-project-audit", publish_required)

    def test_tiktok_separates_reusable_authority_from_per_effect_interactions(self) -> None:
        plan = _plan("tiktok", "publish_video", interactions=set())
        self.assertEqual(plan["actionability"], "user_action_required")
        self.assertIn("tiktok-current-creator-info-query", plan["missingInteractions"])
        self.assertIn("tiktok-user-provided-post-metadata", plan["missingInteractions"])
        self.assertIn("tiktok-explicit-post-consent", plan["missingInteractions"])
        read_plan = _plan(
            "tiktok",
            "read_back",
            authorities=_authorities("tiktok", "read_back"),
            explicit=False,
        )
        self.assertEqual(read_plan["missingInteractions"], [])
        self.assertNotIn("tiktok-public-client-audit", read_plan["requiredAuthorities"])

    def test_douyin_supports_image_create_and_separates_publish_from_read_authority(self) -> None:
        profile = carrier_profile("douyin")
        self.assertIn("publish_image", profile["effects"])
        self.assertTrue(any("open.douyin.com" in url for url in profile["sourceUrls"]))
        publish_required = set(profile["effectAuthorityRequirements"]["publish_video"])
        read_required = set(profile["effectAuthorityRequirements"]["read_back"])
        self.assertIn("douyin-video.create-permission", publish_required)
        self.assertNotIn("douyin-video.create-permission", read_required)
        self.assertIn("douyin-video.list-or-video.data-permission", read_required)
        interaction_blocked = _plan("douyin", "publish_video", interactions=set())
        self.assertEqual(interaction_blocked["actionability"], "user_action_required")
        self.assertIn("douyin-user-perceivable-per-post-action", interaction_blocked["missingInteractions"])

    def test_reddit_requires_manual_user_action_only_for_public_effect(self) -> None:
        public_plan = _plan("reddit", "publish_text", interactions=set())
        self.assertEqual(public_plan["actionability"], "user_action_required")
        self.assertEqual(public_plan["missingInteractions"], ["reddit-explicit-manual-user-action"])
        read_plan = _plan("reddit", "read_back", authorities=_authorities("reddit", "read_back"), explicit=False)
        self.assertEqual(read_plan["actionability"], "ready")
        self.assertEqual(read_plan["missingInteractions"], [])

    def test_xiaohongshu_remains_human_handoff_and_current_scope_source(self) -> None:
        profile = carrier_profile("xiaohongshu")
        self.assertEqual(profile["executionModes"], ["human-handoff"])
        self.assertIn("not-generally-api-writable", profile["nativeWriteStanding"])
        self.assertTrue(any("openaccount.xiaohongshu.com/docs/scope" in url for url in profile["sourceUrls"]))
        plan = _plan("xiaohongshu", "publish_image")
        self.assertEqual(plan["actionability"], "user_action_required")
        self.assertIn("perform-provider-final-action", plan["userOperations"])
        with self.assertRaisesRegex(ValueError, "execution mode"):
            plan_delivery(
                carrier_id="xiaohongshu",
                effect="publish_image",
                granted_authorities=_authorities("xiaohongshu", "publish_image"),
                explicit_user_authority=True,
                execution_mode="api",
                account_identity="account:xhs:opaque",
                artifact_digest=DIGEST,
                intent_id="intent:xhs:1",
            )

    def test_processing_is_not_publication_acceptance(self) -> None:
        plan = _plan("douyin", "publish_video")
        evidence = _outcome(plan, state="processing")
        self.assertFalse(evidence["acceptedCarrierEffect"])
        self.assertFalse(evidence["acceptedPublication"])

    def test_http_or_process_success_cannot_substitute_for_provider_readback(self) -> None:
        plan = _plan("x", "publish_text")
        evidence = _outcome(plan, status_source="runtime-process-success")
        self.assertFalse(evidence["acceptedCarrierEffect"])
        self.assertFalse(evidence["acceptedPublication"])

    def test_published_without_provider_identity_is_not_accepted(self) -> None:
        plan = _plan("x", "publish_text")
        receipt = {
            "carrierId": "x",
            "effect": plan["effect"],
            "deliveryKey": plan["deliveryKey"],
            "providerState": "published",
            "providerObjectId": None,
            "statusSource": "provider-native-readback",
            "observedAtMs": 100,
            "artifactDigest": DIGEST,
        }
        evidence = verify_provider_outcome(receipt)
        self.assertFalse(evidence["acceptedCarrierEffect"])

    def test_outcome_evidence_does_not_claim_generic_delivery_terminality(self) -> None:
        plan = _plan("x", "publish_text")
        weak = verify_provider_outcome(
            {
                "carrierId": "x",
                "effect": plan["effect"],
                "deliveryKey": plan["deliveryKey"],
                "providerState": "published",
                "providerObjectId": None,
                "statusSource": "provider-native-readback",
                "observedAtMs": 100,
                "artifactDigest": DIGEST,
            }
        )
        self.assertFalse(weak["acceptedCarrierEffect"])
        self.assertNotIn("deliveryTerminal", weak)

    def test_provider_native_published_identity_is_carrier_acceptance_only(self) -> None:
        plan = _plan("x", "publish_text")
        evidence = _outcome(plan)
        self.assertTrue(evidence["acceptedCarrierEffect"])
        self.assertTrue(evidence["acceptedPublication"])
        self.assertFalse(evidence["semanticCompletionEvaluated"])
        self.assertIn("does not prove audience reception", evidence["truthBoundary"])

    def test_delete_can_be_verified_as_carrier_effect_without_becoming_publication(self) -> None:
        plan = _plan("x", "delete")
        evidence = _outcome(plan, state="deleted")
        self.assertTrue(evidence["acceptedCarrierEffect"])
        self.assertFalse(evidence["acceptedPublication"])

    def test_delivery_key_binds_intent_not_only_artifact(self) -> None:
        first = delivery_key(
            carrier_id="x", account_identity="account:opaque-a", artifact_digest=DIGEST,
            effect="publish_text", intent_id="intent:1",
        )
        second = delivery_key(
            carrier_id="x", account_identity="account:opaque-a", artifact_digest=DIGEST,
            effect="publish_text", intent_id="intent:2",
        )
        self.assertNotEqual(first, second)

    def test_correction_is_capability_specific_and_preserves_provider_constraints(self) -> None:
        x_delete = correction_disposition(carrier_id="x", requested_effect="delete")
        self.assertTrue(x_delete["supportedByCurrentProfile"])
        self.assertIn("delete-any-version-deletes-entire-edit-chain", x_delete["constraintsToReobserve"])
        x_edit = correction_disposition(carrier_id="x", requested_effect="correct")
        self.assertIn("correct-within-30-minutes-of-original-post", x_edit["constraintsToReobserve"])
        self.assertIn("correct-maximum-5-edits", x_edit["constraintsToReobserve"])
        self.assertFalse(correction_disposition(carrier_id="tiktok", requested_effect="delete")["supportedByCurrentProfile"])

    def test_natural_episode_rejects_maturity_test_publication(self) -> None:
        plan = _plan("x", "publish_text")
        with self.assertRaisesRegex(ValueError, "synthetic publication"):
            bind_natural_episode(
                plan=plan, outcome=_outcome(plan), goal_relevance="test architecture",
                initiated_for="maturity-test", user_authorized_at_ms=1000,
            )

    def test_natural_episode_rejects_blocked_plan_even_with_fake_published_fixture(self) -> None:
        plan = _plan("x", "publish_text", authorities=set())
        self.assertEqual(plan["actionability"], "provider_access_required")
        with self.assertRaisesRegex(ValueError, "ready Distribution plan"):
            bind_natural_episode(
                plan=plan, outcome=_outcome(plan), goal_relevance="real release",
                initiated_for="release-announcement", user_authorized_at_ms=1000,
            )

    def test_natural_episode_rejects_artifact_or_occurrence_mismatch(self) -> None:
        plan = _plan("x", "publish_text")
        wrong_artifact = _outcome(plan, artifact_digest=OTHER_DIGEST)
        with self.assertRaisesRegex(ValueError, "artifactDigest differ"):
            bind_natural_episode(
                plan=plan, outcome=wrong_artifact, goal_relevance="real release",
                initiated_for="release-announcement", user_authorized_at_ms=1000,
            )
        other = _plan("x", "publish_text", index=2)
        wrong_occurrence = _outcome(other)
        with self.assertRaisesRegex(ValueError, "deliveryKey differ"):
            bind_natural_episode(
                plan=plan, outcome=wrong_occurrence, goal_relevance="real release",
                initiated_for="release-announcement", user_authorized_at_ms=1000,
            )

    def test_natural_episode_requires_provider_native_accepted_effect(self) -> None:
        plan = _plan("x", "publish_text")
        weak = _outcome(plan, state="submitted")
        with self.assertRaisesRegex(ValueError, "accepted carrier effect"):
            bind_natural_episode(
                plan=plan, outcome=weak, goal_relevance="real release",
                initiated_for="release-announcement", user_authorized_at_ms=1000,
            )

    def test_natural_episode_binds_exact_ready_authorized_occurrence(self) -> None:
        plan = _plan("x", "publish_text")
        episode = bind_natural_episode(
            plan=plan, outcome=_outcome(plan), goal_relevance="announce a real accepted release",
            initiated_for="release-announcement", user_authorized_at_ms=1000,
        )
        self.assertEqual(episode["deliveryKey"], plan["deliveryKey"])
        self.assertEqual(episode["artifactDigest"], DIGEST)
        self.assertFalse(episode["syntheticForMaturity"])

    def test_maturity_observation_stays_bounded_for_zero_or_single_carrier(self) -> None:
        self.assertEqual(maturity_observation([])["standing"], "no-generic-d2-evidence")
        observation = maturity_observation([_episode("x", "publish_text", index=1)])
        self.assertEqual(observation["standing"], "single-carrier-evidence-only")
        self.assertFalse(observation["defaultClaimed"])

    def test_cross_carrier_repetition_without_recovery_does_not_reach_persistent_candidate(self) -> None:
        episodes = [
            _episode("x", "publish_text", index=1),
            _episode("youtube", "publish_video", index=2),
            _episode("x", "publish_text", index=3),
        ]
        observation = maturity_observation(episodes)
        self.assertEqual(observation["carrierCount"], 2)
        self.assertEqual(observation["effectCount"], 2)
        self.assertEqual(observation["recoveryEvidenceCount"], 0)
        self.assertEqual(observation["standing"], "cross-carrier-repetition-observed-recovery-evidence-missing")
        self.assertFalse(observation["defaultClaimed"])

    def test_cross_carrier_repetition_with_real_correction_or_delete_is_only_d3_candidate(self) -> None:
        episodes = [
            _episode("x", "publish_text", index=1),
            _episode("youtube", "publish_video", index=2),
            _episode("x", "delete", index=3, recovery="provider-readback:delete:3"),
        ]
        observation = maturity_observation(episodes)
        self.assertEqual(observation["carrierCount"], 2)
        self.assertGreaterEqual(observation["effectCount"], 2)
        self.assertEqual(observation["recoveryEvidenceCount"], 1)
        self.assertEqual(observation["standing"], "persistent-capability-candidate-independent-adjudication-required")
        self.assertFalse(observation["defaultClaimed"])


if __name__ == "__main__":
    unittest.main()
