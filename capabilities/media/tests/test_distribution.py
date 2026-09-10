from __future__ import annotations

import unittest

import ordivon_studio.distribution as distribution_module

from ordivon_studio.distribution import (
    CURRENT_CARRIER_PROFILES,
    carrier_profile,
    correction_disposition,
    delivery_key,
    plan_delivery,
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




class DistributionTests(unittest.TestCase):
    def test_profiles_are_dated_and_do_not_claim_provider_contract_truth(self) -> None:
        self.assertGreaterEqual(len(CURRENT_CARRIER_PROFILES), 8)
        for carrier_id in CURRENT_CARRIER_PROFILES:
            profile = carrier_profile(carrier_id)
            self.assertEqual(profile["observedOn"], "2026-09-10")
            self.assertIn("not-provider-contract", profile["truthRole"])
            self.assertIn("effectAuthorityRequirements", profile)
            self.assertTrue(str(profile["profileDigest"]).startswith("sha256:"))

    def test_distribution_core_does_not_self_attest_provider_observations(self) -> None:
        self.assertFalse(hasattr(distribution_module, "verify_provider_outcome"))
        self.assertFalse(hasattr(distribution_module, "bind_natural_episode"))

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

    def test_new_occurrence_identity_changes_for_intent_artifact_effect_or_account(self) -> None:
        old = _plan("x", "publish_text", index=1)
        variants = [
            _plan("x", "publish_text", index=2),
            plan_delivery(
                carrier_id="x", effect="publish_text",
                granted_authorities=_authorities("x", "publish_text"),
                explicit_user_authority=True, execution_mode="api",
                account_identity="account:x:opaque", artifact_digest=OTHER_DIGEST,
                intent_id=str(old["intentId"]),
            ),
            _plan("x", "delete", index=1),
            plan_delivery(
                carrier_id="x", effect="publish_text",
                granted_authorities=_authorities("x", "publish_text"),
                explicit_user_authority=True, execution_mode="api",
                account_identity="account:x:other", artifact_digest=DIGEST,
                intent_id=str(old["intentId"]),
            ),
        ]
        for current in variants:
            self.assertNotEqual(current["deliveryKey"], old["deliveryKey"])

    def test_provider_acceptance_requirements_are_profile_requirements_not_local_proof(self) -> None:
        profile = carrier_profile("x")
        self.assertIn("provider-object-identity", profile["acceptanceEvidence"])
        self.assertIn("provider-native-readback", profile["acceptanceEvidence"])
        self.assertFalse(hasattr(distribution_module, "verify_provider_outcome"))
        self.assertFalse(hasattr(distribution_module, "bind_natural_episode"))

    def test_correction_is_capability_specific_and_preserves_provider_constraints(self) -> None:
        x_delete = correction_disposition(carrier_id="x", requested_effect="delete")
        self.assertTrue(x_delete["supportedByCurrentProfile"])
        self.assertIn("delete-any-version-deletes-entire-edit-chain", x_delete["constraintsToReobserve"])
        x_edit = correction_disposition(carrier_id="x", requested_effect="correct")
        self.assertIn("correct-within-30-minutes-of-original-post", x_edit["constraintsToReobserve"])
        self.assertIn("correct-maximum-5-edits", x_edit["constraintsToReobserve"])
        self.assertFalse(correction_disposition(carrier_id="tiktok", requested_effect="delete")["supportedByCurrentProfile"])

if __name__ == "__main__":
    unittest.main()
