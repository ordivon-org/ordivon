from __future__ import annotations

from collections.abc import Iterable, Mapping
from hashlib import sha256
import json
from typing import Final


DISTRIBUTION_TRUTH_ROLE: Final = "provider-native-distribution-evidence-not-goal-truth"
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
READ_EFFECTS: Final = frozenset({"read_back", "status", "metrics", "feedback"})

PROVIDER_STATES: Final = frozenset(
    {
        "prepared",
        "submitted",
        "processing",
        "published",
        "rejected",
        "withdrawn",
        "deleted",
        "unknown",
    }
)

ACTIONABILITY: Final = frozenset(
    {
        "ready",
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


def _nonnegative_int(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return int(value)


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
        actionability = "ready"
        reasons.append("local-preflight-satisfied-not-yet-dispatched")

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



def verify_provider_outcome(receipt: Mapping[str, object]) -> dict[str, object]:
    """Promote only provider-native read-back to accepted publication evidence."""

    required = {
        "carrierId",
        "effect",
        "deliveryKey",
        "providerState",
        "providerObjectId",
        "statusSource",
        "observedAtMs",
        "artifactDigest",
    }
    missing_fields = sorted(required - set(receipt))
    if missing_fields:
        raise ValueError(f"provider receipt missing fields: {', '.join(missing_fields)}")
    profile = carrier_profile(_nonempty(receipt.get("carrierId"), "carrierId"))
    effect_name = _nonempty(receipt.get("effect"), "effect")
    if effect_name not in profile["effects"]:
        raise ValueError(f"carrier {profile['carrierId']} does not expose effect {effect_name}")
    exact_delivery_key = _nonempty(receipt.get("deliveryKey"), "deliveryKey")
    state = _nonempty(receipt.get("providerState"), "providerState").lower()
    if state not in PROVIDER_STATES:
        raise ValueError(f"unsupported provider state: {state}")
    object_id_raw = receipt.get("providerObjectId")
    object_id = object_id_raw.strip() if isinstance(object_id_raw, str) else None
    if object_id == "":
        object_id = None
    status_source = _nonempty(receipt.get("statusSource"), "statusSource")
    observed_at_ms = _nonnegative_int(receipt.get("observedAtMs"), "observedAtMs")
    artifact_digest = _sha256(receipt.get("artifactDigest"), "artifactDigest")

    provider_native = object_id is not None and status_source == "provider-native-readback"
    if effect_name in {"publish_text", "publish_image", "publish_video", "publish_article", "correct"}:
        accepted_effect = provider_native and state == "published"
    elif effect_name == "delete":
        accepted_effect = provider_native and state == "deleted"
    elif effect_name == "withdraw":
        accepted_effect = provider_native and state == "withdrawn"
    else:
        accepted_effect = False
    accepted_publication = accepted_effect and effect_name.startswith("publish_")
    result: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-outcome-evidence",
        "carrierId": profile["carrierId"],
        "effect": effect_name,
        "deliveryKey": exact_delivery_key,
        "providerState": state,
        "providerObjectId": object_id,
        "statusSource": status_source,
        "observedAtMs": observed_at_ms,
        "artifactDigest": artifact_digest,
        "acceptedCarrierEffect": accepted_effect,
        "acceptedPublication": accepted_publication,
        "semanticCompletionEvaluated": False,
        "truthRole": DISTRIBUTION_TRUTH_ROLE,
        "truthBoundary": (
            "Provider-native publication standing is evidence about the carrier object only. "
            "It does not prove audience reception, goal consequence, truth of the content, or cross-carrier D2/D3 maturity."
        ),
    }
    result["evidenceDigest"] = _digest(result)
    return result


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


def bind_natural_episode(
    *,
    plan: Mapping[str, object],
    outcome: Mapping[str, object],
    goal_relevance: str,
    initiated_for: str,
    user_authorized_at_ms: int,
    recovery_evidence_ref: str | None = None,
) -> dict[str, object]:
    """Bind real work to maturity evidence without allowing synthetic publication-as-test."""

    if plan.get("kind") != "ordivon.media.distribution-plan":
        raise ValueError("plan is not a Distribution plan")
    if outcome.get("kind") != "ordivon.media.distribution-outcome-evidence":
        raise ValueError("outcome is not Distribution outcome evidence")
    if plan.get("carrierId") != outcome.get("carrierId"):
        raise ValueError("plan and outcome carrier differ")
    if plan.get("effect") != outcome.get("effect"):
        raise ValueError("plan and outcome effect differ")
    if plan.get("actionability") != "ready":
        raise ValueError("natural external episode requires a ready Distribution plan")
    if plan.get("missingAuthorities") or plan.get("missingInteractions"):
        raise ValueError("natural external episode cannot retain unresolved authority or interaction gates")
    plan_delivery_key = _nonempty(plan.get("deliveryKey"), "plan.deliveryKey")
    outcome_delivery_key = _nonempty(outcome.get("deliveryKey"), "outcome.deliveryKey")
    if plan_delivery_key != outcome_delivery_key:
        raise ValueError("plan and outcome deliveryKey differ")
    plan_artifact = _sha256(plan.get("artifactDigest"), "plan.artifactDigest")
    outcome_artifact = _sha256(outcome.get("artifactDigest"), "outcome.artifactDigest")
    if plan_artifact != outcome_artifact:
        raise ValueError("plan and outcome artifactDigest differ")
    purpose = _nonempty(initiated_for, "initiatedFor").lower().replace("_", "-")
    forbidden = {
        "architecture-test",
        "maturity-test",
        "distribution-e2e-test",
        "generate-evidence",
        "synthetic-publication",
    }
    if purpose in forbidden:
        raise ValueError("synthetic publication cannot be bound as a natural Distribution episode")
    if not bool(plan.get("publicEffect")):
        raise ValueError("natural external episode requires a public external effect")
    if not bool(plan.get("explicitUserAuthority")):
        raise ValueError("natural external episode lacks explicit user authority")
    if not bool(outcome.get("acceptedCarrierEffect")):
        raise ValueError("natural external episode lacks provider-native accepted carrier effect")
    observed_at = _nonnegative_int(outcome.get("observedAtMs"), "outcome.observedAtMs")
    authorized_at = _nonnegative_int(user_authorized_at_ms, "userAuthorizedAtMs")
    if authorized_at > observed_at:
        raise ValueError("user authority cannot postdate provider outcome observation")
    episode: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-natural-episode",
        "carrierId": plan["carrierId"],
        "effect": plan["effect"],
        "deliveryKey": plan_delivery_key,
        "artifactDigest": plan_artifact,
        "planDigest": _nonempty(plan.get("planDigest"), "planDigest"),
        "outcomeEvidenceDigest": _nonempty(outcome.get("evidenceDigest"), "outcomeEvidenceDigest"),
        "goalRelevance": _nonempty(goal_relevance, "goalRelevance"),
        "initiatedFor": purpose,
        "userAuthorizedAtMs": authorized_at,
        "providerObservedAtMs": observed_at,
        "recoveryEvidenceRef": (
            _nonempty(recovery_evidence_ref, "recoveryEvidenceRef") if recovery_evidence_ref is not None else None
        ),
        "syntheticForMaturity": False,
        "truthRole": "goal-relative-natural-distribution-episode-evidence",
    }
    episode["episodeDigest"] = _digest(episode)
    return episode


def maturity_observation(episodes: Iterable[Mapping[str, object]]) -> dict[str, object]:
    """Conservatively summarize supplied natural episodes without claiming DEFAULT automatically."""

    rows = [dict(item) for item in episodes]
    digests: set[str] = set()
    delivery_keys: set[str] = set()
    carriers: set[str] = set()
    effects: set[str] = set()
    recovery_evidence_count = 0
    for row in rows:
        if row.get("kind") != "ordivon.media.distribution-natural-episode":
            raise ValueError("maturity observation accepts only natural Distribution episodes")
        digest = _nonempty(row.get("episodeDigest"), "episodeDigest")
        if digest in digests:
            raise ValueError("duplicate natural episode identity")
        digests.add(digest)
        delivery = _nonempty(row.get("deliveryKey"), "deliveryKey")
        if delivery in delivery_keys:
            raise ValueError("duplicate delivery occurrence cannot contribute twice to maturity")
        delivery_keys.add(delivery)
        carriers.add(_nonempty(row.get("carrierId"), "carrierId"))
        effect = _nonempty(row.get("effect"), "effect")
        effects.add(effect)
        if effect in {"correct", "withdraw", "delete"} or row.get("recoveryEvidenceRef") is not None:
            recovery_evidence_count += 1
        if bool(row.get("syntheticForMaturity")):
            raise ValueError("synthetic episode cannot contribute to maturity")

    if len(rows) == 0:
        standing = "no-generic-d2-evidence"
    elif len(carriers) == 1:
        standing = "single-carrier-evidence-only"
    elif len(rows) < 3:
        standing = "cross-carrier-d2-candidate-not-d3"
    elif len(effects) < 2:
        standing = "cross-carrier-repetition-observed-effect-variation-missing"
    elif recovery_evidence_count == 0:
        standing = "cross-carrier-repetition-observed-recovery-evidence-missing"
    else:
        standing = "persistent-capability-candidate-independent-adjudication-required"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-maturity-observation",
        "episodeCount": len(rows),
        "carrierCount": len(carriers),
        "carriers": sorted(carriers),
        "effectCount": len(effects),
        "effects": sorted(effects),
        "recoveryEvidenceCount": recovery_evidence_count,
        "standing": standing,
        "defaultClaimed": False,
        "truthRole": "bounded-episode-summary-not-graduation-verdict",
    }
