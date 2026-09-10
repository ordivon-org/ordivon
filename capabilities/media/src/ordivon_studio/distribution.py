from __future__ import annotations

from collections.abc import Iterable, Mapping
from hashlib import sha256
import json
from typing import Final


PLAN_TRUTH_ROLE: Final = "distribution-plan-not-external-effect"
PROFILE_TRUTH_ROLE: Final = "point-in-time-carrier-capability-profile-not-provider-contract"

PUBLIC_EFFECTS: Final = frozenset(
    {
        "publish_text",
        "publish_image",
        "publish_video",
        "publish_article",
        "correct",
        "withdraw",
        "delete",
    }
)
ACTIONABILITY: Final = frozenset(
    {
        "preflight_ready",
        "user_action_required",
        "provider_access_required",
        "capability_unavailable",
        "unknown",
    }
)


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256(payload).hexdigest()


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _sha256(value: object, field: str) -> str:
    text = _nonempty(value, field)
    if not text.startswith("sha256:") or len(text) != 71:
        raise ValueError(f"{field} must be one sha256 digest")
    return text


def _profile(
    carrier_id: str,
    display_name: str,
    *,
    native_write_standing: str,
    execution_modes: tuple[str, ...],
    effects: tuple[str, ...],
    authority_requirements: tuple[str, ...],
    acceptance: tuple[str, ...],
    correction: tuple[str, ...],
    source_urls: tuple[str, ...],
    observed_on: str = "2026-09-10",
    interaction_requirements: tuple[str, ...] = (),
    correction_constraints: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> dict[str, object]:
    value: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-carrier-profile",
        "carrierId": carrier_id,
        "displayName": display_name,
        "observedOn": observed_on,
        "nativeWriteStanding": native_write_standing,
        "executionModes": list(execution_modes),
        "effects": list(effects),
        "authorityRequirements": list(authority_requirements),
        "interactionRequirements": list(interaction_requirements),
        "acceptanceEvidence": list(acceptance),
        "correctionCapabilities": list(correction),
        "correctionConstraints": list(correction_constraints),
        "sourceUrls": list(source_urls),
        "notes": list(notes),
        "truthRole": PROFILE_TRUTH_ROLE,
    }
    value["profileDigest"] = _digest(value)
    return value


# These are dated capability observations, not durable claims about provider policy.
# Re-observe the official source before any real external effect.
CURRENT_CARRIER_PROFILES: Final[dict[str, dict[str, object]]] = {
    "github": _profile(
        "github",
        "GitHub",
        native_write_standing="available-if-authorized",
        execution_modes=("native-cli-or-api",),
        effects=("publish_article", "correct", "delete", "read_back", "status", "metrics", "feedback"),
        authority_requirements=("github-account-authority", "github-write-credential"),
        acceptance=("provider-object-identity", "provider-native-readback"),
        correction=("correct", "delete"),
        source_urls=("https://docs.github.com/en/rest",),
        notes=("Existing Ordivon bounded D2 positive-control carrier; this profile does not upgrade that standing.",),
    ),
    "x": _profile(
        "x",
        "X",
        native_write_standing="available-if-authorized-and-current-api-access",
        execution_modes=("api",),
        effects=("publish_text", "publish_image", "publish_video", "correct", "delete", "read_back", "status", "metrics"),
        authority_requirements=("x-developer-app", "x-user-oauth", "x-current-api-access", "x-tweet.read-scope", "x-tweet.write-scope"),
        acceptance=("provider-object-identity", "provider-native-readback"),
        correction=("correct", "delete"),
        correction_constraints=(
            "correct-only-when-provider-edit-controls-report-eligible",
            "correct-within-30-minutes-of-original-post",
            "correct-maximum-5-edits",
            "correct-creates-new-provider-object-id",
            "delete-any-version-deletes-entire-edit-chain",
        ),
        source_urls=(
            "https://docs.x.com/x-api/posts/create-post",
            "https://docs.x.com/x-api/media/quickstart/media-upload-chunked",
        ),
        notes=("Re-observe current API access and account standing before effect admission.",),
    ),
    "tiktok": _profile(
        "tiktok",
        "TikTok",
        native_write_standing="available-after-product-scope-user-auth-and-public-client-audit",
        execution_modes=("content-posting-api",),
        effects=("publish_image", "publish_video", "read_back", "status"),
        authority_requirements=(
            "tiktok-registered-app",
            "tiktok-content-posting-api-product",
            "tiktok-video.publish-scope",
            "tiktok-user-authorization",
            "tiktok-public-client-audit",
        ),
        acceptance=("provider-publish-id", "provider-native-status-readback"),
        correction=(),
        source_urls=(
            "https://developers.tiktok.com/doc/content-posting-api-get-started/",
            "https://developers.tiktok.com/doc/content-posting-api-reference-direct-post/",
        ),
        interaction_requirements=(
            "tiktok-current-creator-info-query",
            "tiktok-user-provided-post-metadata",
            "tiktok-explicit-post-consent",
        ),
        notes=("Unaudited clients are restricted to private visibility; public Distribution therefore keeps audit as an authority requirement.",),
    ),
    "douyin": _profile(
        "douyin",
        "Douyin",
        native_write_standing="available-after-permission-review-and-user-authorization",
        execution_modes=("open-platform-api", "mobile-open-sdk"),
        effects=("publish_image", "publish_video", "read_back", "status"),
        authority_requirements=(
            "douyin-developer-app",
            "douyin-video.create-permission",
            "douyin-video.list-or-video.data-permission",
            "douyin-user-authorization",
        ),
        acceptance=("provider-video-id", "provider-native-review-or-status-readback"),
        correction=(),
        source_urls=(
            "https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video",
            "https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/upload/",
        ),
        interaction_requirements=("douyin-user-perceivable-per-post-action",),
        notes=("Submission may enter provider review and initially be visible only to the author; submitted is not published.",),
    ),
    "bilibili": _profile(
        "bilibili",
        "Bilibili",
        native_write_standing="available-after-platform-qualification-and-capability-approval",
        execution_modes=("open-platform-api",),
        effects=("publish_video", "publish_article", "read_back", "status", "metrics", "feedback"),
        authority_requirements=(
            "bilibili-identity-qualification",
            "bilibili-developer-application",
            "bilibili-content-distribution-capability",
            "bilibili-data-return-capability",
            "bilibili-account-authorization",
        ),
        acceptance=("provider-manuscript-identity", "provider-native-status-readback"),
        correction=("delete",),
        source_urls=("https://open.bilibili.com/",),
        notes=("Qualification/application state is provider authority and must be re-observed before write admission.",),
    ),
    "reddit": _profile(
        "reddit",
        "Reddit",
        native_write_standing="approval-constrained",
        execution_modes=("devvit-or-approved-data-api",),
        effects=("publish_text", "publish_image", "publish_video", "delete", "read_back", "status", "feedback"),
        authority_requirements=(
            "reddit-approved-developer-access",
            "reddit-application-or-devvit-approval",
            "reddit-user-action-permission",
        ),
        acceptance=("provider-post-identity", "provider-native-readback"),
        correction=("delete",),
        source_urls=(
            "https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy",
            "https://developers.reddit.com/docs/capabilities/server/userActions",
        ),
        interaction_requirements=("reddit-explicit-manual-user-action",),
        notes=("Do not assume historical unrestricted Data API access; current approved-access policy is an authority boundary.",),
    ),
    "xiaohongshu": _profile(
        "xiaohongshu",
        "Xiaohongshu",
        native_write_standing="not-generally-api-writable-currently-observed",
        execution_modes=("human-handoff",),
        effects=("publish_text", "publish_image", "publish_video", "read_back"),
        authority_requirements=("xiaohongshu-user-session",),
        acceptance=("human-observed-provider-object-identity", "provider-native-readback"),
        correction=(),
        source_urls=(
            "https://openaccount.xiaohongshu.com/docs/scope",
            "https://openaccount.xiaohongshu.com/docs/api-reference",
        ),
        notes=("The observed write_notes scope is planned/restricted rather than a generally available write surface; no API-write adapter may be inferred from this profile.",),
    ),
    "youtube": _profile(
        "youtube",
        "YouTube",
        native_write_standing="available-if-authorized-with-public-project-audit-constraints",
        execution_modes=("data-api",),
        effects=("publish_video", "delete", "read_back", "status", "metrics", "feedback"),
        authority_requirements=("youtube-api-project", "youtube-user-oauth", "youtube.upload-scope", "youtube-read-scope", "youtube-delete-scope", "youtube-public-upload-project-audit"),
        acceptance=("provider-video-id", "provider-native-processing-and-visibility-readback"),
        correction=("delete",),
        source_urls=(
            "https://developers.google.com/youtube/v3/docs/videos/insert",
            "https://developers.google.com/youtube/v3/guides/implementation/uploading_a_video",
        ),
        notes=("Uploads from unverified API projects can be restricted to private; public Distribution must preserve that provider constraint.",),
    ),
}


# Per-effect minimal authority sets. ``authorityRequirements`` remains a conservative carrier-level
# inventory/superset; planning uses this table so a read-only reconciliation does not request a
# write scope merely because the same carrier can also publish.
_EFFECT_AUTHORITY_REQUIREMENTS: Final[dict[str, dict[str, tuple[str, ...]]]] = {
    "github": {
        "publish_article": ("github-account-authority", "github-write-credential"),
        "correct": ("github-account-authority", "github-write-credential"),
        "delete": ("github-account-authority", "github-write-credential"),
        "read_back": ("github-account-authority",), "status": ("github-account-authority",),
        "metrics": ("github-account-authority",), "feedback": ("github-account-authority",),
    },
    "x": {
        "publish_text": ("x-developer-app", "x-current-api-access", "x-user-oauth", "x-tweet.write-scope"),
        "publish_image": ("x-developer-app", "x-current-api-access", "x-user-oauth", "x-tweet.write-scope"),
        "publish_video": ("x-developer-app", "x-current-api-access", "x-user-oauth", "x-tweet.write-scope"),
        "correct": ("x-developer-app", "x-current-api-access", "x-user-oauth", "x-tweet.write-scope"),
        "delete": ("x-developer-app", "x-current-api-access", "x-user-oauth", "x-tweet.write-scope"),
        "read_back": ("x-developer-app", "x-current-api-access", "x-user-oauth", "x-tweet.read-scope"),
        "status": ("x-developer-app", "x-current-api-access", "x-user-oauth", "x-tweet.read-scope"),
        "metrics": ("x-developer-app", "x-current-api-access", "x-user-oauth", "x-tweet.read-scope"),
    },
    "tiktok": {
        "publish_image": ("tiktok-registered-app", "tiktok-content-posting-api-product", "tiktok-video.publish-scope", "tiktok-user-authorization", "tiktok-public-client-audit"),
        "publish_video": ("tiktok-registered-app", "tiktok-content-posting-api-product", "tiktok-video.publish-scope", "tiktok-user-authorization", "tiktok-public-client-audit"),
        "read_back": ("tiktok-registered-app", "tiktok-content-posting-api-product", "tiktok-video.publish-scope", "tiktok-user-authorization"),
        "status": ("tiktok-registered-app", "tiktok-content-posting-api-product", "tiktok-video.publish-scope", "tiktok-user-authorization"),
    },
    "douyin": {
        "publish_image": ("douyin-developer-app", "douyin-video.create-permission", "douyin-user-authorization"),
        "publish_video": ("douyin-developer-app", "douyin-video.create-permission", "douyin-user-authorization"),
        "read_back": ("douyin-developer-app", "douyin-video.list-or-video.data-permission", "douyin-user-authorization"),
        "status": ("douyin-developer-app", "douyin-video.list-or-video.data-permission", "douyin-user-authorization"),
    },
    "bilibili": {
        "publish_video": ("bilibili-identity-qualification", "bilibili-developer-application", "bilibili-content-distribution-capability", "bilibili-account-authorization"),
        "publish_article": ("bilibili-identity-qualification", "bilibili-developer-application", "bilibili-content-distribution-capability", "bilibili-account-authorization"),
        "read_back": ("bilibili-developer-application", "bilibili-data-return-capability", "bilibili-account-authorization"),
        "status": ("bilibili-developer-application", "bilibili-data-return-capability", "bilibili-account-authorization"),
        "metrics": ("bilibili-developer-application", "bilibili-data-return-capability", "bilibili-account-authorization"),
        "feedback": ("bilibili-developer-application", "bilibili-data-return-capability", "bilibili-account-authorization"),
    },
    "reddit": {
        "publish_text": ("reddit-approved-developer-access", "reddit-application-or-devvit-approval", "reddit-user-action-permission"),
        "publish_image": ("reddit-approved-developer-access", "reddit-application-or-devvit-approval", "reddit-user-action-permission"),
        "publish_video": ("reddit-approved-developer-access", "reddit-application-or-devvit-approval", "reddit-user-action-permission"),
        "delete": ("reddit-approved-developer-access", "reddit-application-or-devvit-approval"),
        "read_back": ("reddit-approved-developer-access", "reddit-application-or-devvit-approval"),
        "status": ("reddit-approved-developer-access", "reddit-application-or-devvit-approval"),
        "feedback": ("reddit-approved-developer-access", "reddit-application-or-devvit-approval"),
    },
    "xiaohongshu": {
        "publish_text": ("xiaohongshu-user-session",), "publish_image": ("xiaohongshu-user-session",),
        "publish_video": ("xiaohongshu-user-session",), "read_back": ("xiaohongshu-user-session",),
    },
    "youtube": {
        "publish_video": ("youtube-api-project", "youtube-user-oauth", "youtube.upload-scope", "youtube-public-upload-project-audit"),
        "delete": ("youtube-api-project", "youtube-user-oauth", "youtube-delete-scope"),
        "read_back": ("youtube-api-project", "youtube-user-oauth", "youtube-read-scope"),
        "status": ("youtube-api-project", "youtube-user-oauth", "youtube-read-scope"),
        "metrics": ("youtube-api-project", "youtube-user-oauth", "youtube-read-scope"),
        "feedback": ("youtube-api-project", "youtube-user-oauth", "youtube-read-scope"),
    },
}


def carrier_profile(carrier_id: str) -> dict[str, object]:
    key = _nonempty(carrier_id, "carrierId").lower()
    profile = CURRENT_CARRIER_PROFILES.get(key)
    if profile is None:
        raise ValueError(f"unknown carrier: {key}")
    result = json.loads(json.dumps(profile))
    result["effectAuthorityRequirements"] = {
        effect: list(requirements) for effect, requirements in _EFFECT_AUTHORITY_REQUIREMENTS.get(key, {}).items()
    }
    result.pop("profileDigest", None)
    result["profileDigest"] = _digest(result)
    return result


def delivery_key(
    *,
    carrier_id: str,
    account_identity: str,
    artifact_digest: str,
    effect: str,
    intent_id: str,
) -> str:
    """Return an exact intent key; it is not a provider idempotency guarantee."""

    profile = carrier_profile(carrier_id)
    effect_name = _nonempty(effect, "effect")
    if effect_name not in profile["effects"]:
        raise ValueError(f"carrier {profile['carrierId']} does not expose effect {effect_name}")
    value = {
        "carrierId": profile["carrierId"],
        "accountIdentity": _nonempty(account_identity, "accountIdentity"),
        "artifactDigest": _sha256(artifact_digest, "artifactDigest"),
        "effect": effect_name,
        "intentId": _nonempty(intent_id, "intentId"),
    }
    return _digest(value)


def plan_delivery(
    *,
    carrier_id: str,
    effect: str,
    granted_authorities: Iterable[str] = (),
    satisfied_interactions: Iterable[str] = (),
    explicit_user_authority: bool = False,
    execution_mode: str | None = None,
    account_identity: str | None = None,
    artifact_digest: str | None = None,
    intent_id: str | None = None,
) -> dict[str, object]:
    """Plan one effect without performing it or collapsing reusable auth into per-effect consent."""

    profile = carrier_profile(carrier_id)
    effect_name = _nonempty(effect, "effect")
    is_public_effect = effect_name in PUBLIC_EFFECTS
    exact_identity_values = (account_identity, artifact_digest, intent_id)
    if is_public_effect and any(value is None for value in exact_identity_values):
        raise ValueError("public effect requires exact account_identity, artifact_digest, and intent_id")
    if any(value is not None for value in exact_identity_values) and any(
        value is None for value in exact_identity_values
    ):
        raise ValueError("delivery identity must provide account_identity, artifact_digest, and intent_id together")
    normalized_account = _nonempty(account_identity, "accountIdentity") if account_identity is not None else None
    normalized_artifact = _sha256(artifact_digest, "artifactDigest") if artifact_digest is not None else None
    normalized_intent = _nonempty(intent_id, "intentId") if intent_id is not None else None
    exact_delivery_key = (
        delivery_key(
            carrier_id=str(profile["carrierId"]),
            account_identity=normalized_account,
            artifact_digest=normalized_artifact,
            effect=effect_name,
            intent_id=normalized_intent,
        )
        if normalized_account is not None and normalized_artifact is not None and normalized_intent is not None
        else None
    )
    authorities = sorted({_nonempty(item, "grantedAuthority") for item in granted_authorities})
    interactions = sorted({_nonempty(item, "satisfiedInteraction") for item in satisfied_interactions})
    effect_authorities = profile.get("effectAuthorityRequirements", {})
    if isinstance(effect_authorities, Mapping) and effect_name in effect_authorities:
        required_authorities = set(effect_authorities[effect_name])
    else:
        required_authorities = set(profile["authorityRequirements"])
    missing = sorted(required_authorities - set(authorities))
    required_interactions = set(profile["interactionRequirements"]) if is_public_effect else set()
    missing_interactions = sorted(required_interactions - set(interactions))
    modes = list(profile["executionModes"])
    selected_mode = execution_mode or (modes[0] if len(modes) == 1 else None)
    if selected_mode is not None and selected_mode not in modes:
        raise ValueError(f"execution mode {selected_mode!r} is not supported by {profile['carrierId']}")

    reasons: list[str] = []
    user_operations: list[str] = []
    if effect_name not in profile["effects"]:
        actionability = "capability_unavailable"
        reasons.append("effect-not-in-current-carrier-profile")
    elif selected_mode is None:
        actionability = "user_action_required"
        reasons.append("execution-mode-selection-required")
        user_operations.append("select-execution-mode")
    elif missing:
        actionability = "provider_access_required"
        reasons.append("missing-provider-or-account-authority")
        user_operations.extend(missing)
    elif missing_interactions:
        actionability = "user_action_required"
        reasons.append("missing-per-effect-provider-interaction")
        user_operations.extend(missing_interactions)
    elif is_public_effect and not explicit_user_authority:
        actionability = "user_action_required"
        reasons.append("public-effect-requires-explicit-user-authority")
        user_operations.append("authorize-this-exact-public-effect")
    elif selected_mode == "human-handoff":
        actionability = "user_action_required"
        reasons.append("carrier-currently-requires-human-final-action")
        user_operations.append("perform-provider-final-action")
    else:
        actionability = "preflight_ready"
        reasons.append("local-preflight-satisfied-effect-admission-must-revalidate-current-authority")

    if actionability not in ACTIONABILITY:
        raise AssertionError("invalid actionability")
    plan: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-plan",
        "carrierId": profile["carrierId"],
        "carrierProfileDigest": profile["profileDigest"],
        "effect": effect_name,
        "executionMode": selected_mode,
        "publicEffect": is_public_effect,
        "accountIdentity": normalized_account,
        "artifactDigest": normalized_artifact,
        "intentId": normalized_intent,
        "deliveryKey": exact_delivery_key,
        "grantedAuthorities": authorities,
        "requiredAuthorities": sorted(required_authorities),
        "missingAuthorities": missing,
        "satisfiedInteractions": interactions,
        "missingInteractions": missing_interactions,
        "explicitUserAuthority": explicit_user_authority,
        "actionability": actionability,
        "reasons": reasons,
        "userOperations": sorted(set(user_operations)),
        "externalEffectPerformed": False,
        "truthRole": PLAN_TRUTH_ROLE,
    }
    plan["planDigest"] = _digest(plan)
    return plan



def correction_disposition(*, carrier_id: str, requested_effect: str) -> dict[str, object]:
    profile = carrier_profile(carrier_id)
    effect = _nonempty(requested_effect, "requestedEffect")
    supported = effect in set(profile["correctionCapabilities"])
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-correction-disposition",
        "carrierId": profile["carrierId"],
        "requestedEffect": effect,
        "supportedByCurrentProfile": supported,
        "constraintsToReobserve": list(profile["correctionConstraints"]) if supported else [],
        "actionability": "user_action_required" if supported else "capability_unavailable",
        "externalEffectPerformed": False,
        "truthRole": "correction-capability-plan-not-provider-effect",
    }
