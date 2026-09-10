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
        authority_requirements=("x-developer-app", "x-user-oauth", "x-current-api-access"),
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
        effects=("publish_video", "read_back", "status"),
        authority_requirements=(
            "douyin-developer-app",
            "douyin-video.create.bind-permission",
            "douyin-user-authorization",
        ),
        acceptance=("provider-video-id", "provider-native-review-or-status-readback"),
        correction=(),
        source_urls=(
            "https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/create-video",
            "https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/upload-video",
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
            "https://miniapp.xiaohongshu.com/doc/DC214154",
            "https://miniapp.xiaohongshu.com/doc/DC214155",
        ),
        notes=("The observed write_notes scope is planned/restricted rather than a generally available write surface; no API-write adapter may be inferred from this profile.",),
    ),
    "youtube": _profile(
        "youtube",
        "YouTube",
        native_write_standing="available-if-authorized-with-public-project-audit-constraints",
        execution_modes=("data-api",),
        effects=("publish_video", "delete", "read_back", "status", "metrics", "feedback"),
        authority_requirements=("youtube-api-project", "youtube-user-oauth", "youtube-public-upload-project-audit"),
        acceptance=("provider-video-id", "provider-native-processing-and-visibility-readback"),
        correction=("delete",),
        source_urls=(
            "https://developers.google.com/youtube/v3/docs/videos/insert",
            "https://developers.google.com/youtube/v3/guides/implementation/uploading_a_video",
        ),
        notes=("Uploads from unverified API projects can be restricted to private; public Distribution must preserve that provider constraint.",),
    ),
}


def carrier_profile(carrier_id: str) -> dict[str, object]:
    key = _nonempty(carrier_id, "carrierId").lower()
    profile = CURRENT_CARRIER_PROFILES.get(key)
    if profile is None:
        raise ValueError(f"unknown carrier: {key}")
    return json.loads(json.dumps(profile))


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
) -> dict[str, object]:
    """Plan one effect without performing it or collapsing reusable auth into per-effect consent."""

    profile = carrier_profile(carrier_id)
    effect_name = _nonempty(effect, "effect")
    authorities = sorted({_nonempty(item, "grantedAuthority") for item in granted_authorities})
    interactions = sorted({_nonempty(item, "satisfiedInteraction") for item in satisfied_interactions})
    missing = sorted(set(profile["authorityRequirements"]) - set(authorities))
    missing_interactions = sorted(set(profile["interactionRequirements"]) - set(interactions))
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
    elif effect_name in PUBLIC_EFFECTS and not explicit_user_authority:
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
        "publicEffect": effect_name in PUBLIC_EFFECTS,
        "grantedAuthorities": authorities,
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


def retry_disposition(
    *, provider_state: str, provider_object_id: str | None = None
) -> dict[str, object]:
    """Fail closed around ambiguous provider outcomes; never infer resend safety."""

    state = _nonempty(provider_state, "providerState").lower()
    if state not in PROVIDER_STATES:
        raise ValueError(f"unsupported provider state: {state}")
    object_id = provider_object_id.strip() if isinstance(provider_object_id, str) else None
    if object_id == "":
        object_id = None

    if state == "prepared" and object_id is None:
        disposition = "safe-only-before-dispatch"
    elif state in {"submitted", "processing", "unknown"}:
        disposition = "requery-provider-do-not-resend"
    elif state == "published":
        disposition = "accepted-do-not-resend"
    else:
        disposition = "new-explicit-intent-required-before-any-new-effect"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-retry-disposition",
        "providerState": state,
        "providerObjectId": object_id,
        "disposition": disposition,
        "blindResendPermitted": False,
        "truthRole": "retry-safety-decision-not-provider-state",
    }


def verify_provider_outcome(receipt: Mapping[str, object]) -> dict[str, object]:
    """Promote only provider-native read-back to accepted publication evidence."""

    required = {
        "carrierId",
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

    accepted = state == "published" and object_id is not None and status_source == "provider-native-readback"
    if state in {"published", "withdrawn", "deleted"} and object_id is None:
        accepted = False
    result: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-outcome-evidence",
        "carrierId": profile["carrierId"],
        "providerState": state,
        "providerObjectId": object_id,
        "statusSource": status_source,
        "observedAtMs": observed_at_ms,
        "artifactDigest": artifact_digest,
        "acceptedPublication": accepted,
        "deliveryTerminal": state in {"published", "rejected", "withdrawn", "deleted"},
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
) -> dict[str, object]:
    """Bind real work to maturity evidence without allowing synthetic publication-as-test."""

    if plan.get("kind") != "ordivon.media.distribution-plan":
        raise ValueError("plan is not a Distribution plan")
    if outcome.get("kind") != "ordivon.media.distribution-outcome-evidence":
        raise ValueError("outcome is not Distribution outcome evidence")
    if plan.get("carrierId") != outcome.get("carrierId"):
        raise ValueError("plan and outcome carrier differ")
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
    if not bool(outcome.get("acceptedPublication")):
        raise ValueError("natural external episode lacks provider-native accepted publication")
    observed_at = _nonnegative_int(outcome.get("observedAtMs"), "outcome.observedAtMs")
    authorized_at = _nonnegative_int(user_authorized_at_ms, "userAuthorizedAtMs")
    if authorized_at > observed_at:
        raise ValueError("user authority cannot postdate provider outcome observation")
    episode: dict[str, object] = {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-natural-episode",
        "carrierId": plan["carrierId"],
        "planDigest": _nonempty(plan.get("planDigest"), "planDigest"),
        "outcomeEvidenceDigest": _nonempty(outcome.get("evidenceDigest"), "outcomeEvidenceDigest"),
        "goalRelevance": _nonempty(goal_relevance, "goalRelevance"),
        "initiatedFor": purpose,
        "userAuthorizedAtMs": authorized_at,
        "providerObservedAtMs": observed_at,
        "syntheticForMaturity": False,
        "truthRole": "goal-relative-natural-distribution-episode-evidence",
    }
    episode["episodeDigest"] = _digest(episode)
    return episode


def maturity_observation(episodes: Iterable[Mapping[str, object]]) -> dict[str, object]:
    """Conservatively summarize supplied natural episodes without claiming DEFAULT automatically."""

    rows = [dict(item) for item in episodes]
    digests: set[str] = set()
    carriers: set[str] = set()
    for row in rows:
        if row.get("kind") != "ordivon.media.distribution-natural-episode":
            raise ValueError("maturity observation accepts only natural Distribution episodes")
        digest = _nonempty(row.get("episodeDigest"), "episodeDigest")
        if digest in digests:
            raise ValueError("duplicate natural episode identity")
        digests.add(digest)
        carriers.add(_nonempty(row.get("carrierId"), "carrierId"))
        if bool(row.get("syntheticForMaturity")):
            raise ValueError("synthetic episode cannot contribute to maturity")

    if len(rows) == 0:
        standing = "no-generic-d2-evidence"
    elif len(carriers) == 1:
        standing = "single-carrier-evidence-only"
    elif len(rows) < 3:
        standing = "cross-carrier-d2-candidate-not-d3"
    else:
        standing = "cross-carrier-repetition-observed-d3-still-requires-independent-adjudication"
    return {
        "schemaVersion": 1,
        "kind": "ordivon.media.distribution-maturity-observation",
        "episodeCount": len(rows),
        "carrierCount": len(carriers),
        "carriers": sorted(carriers),
        "standing": standing,
        "defaultClaimed": False,
        "truthRole": "bounded-episode-summary-not-graduation-verdict",
    }
