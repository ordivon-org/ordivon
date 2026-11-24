"""Pure result observation contract shared by browser transports.

No browser lifecycle, provider calls, credential access or execution authority.
A snapshot alone cannot prove a provider-issued turn ID or domain acceptance.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable

try:
    from chatgpt_provider_resource import chatgpt_resource_from_page_url
except ModuleNotFoundError:
    from scripts.chatgpt_provider_resource import chatgpt_resource_from_page_url


DOM_SNAPSHOT_ARGS = {
    "mainSelector": "main",
    "messageSelector": "[data-message-author-role]",
    "stopSelector": 'button[data-testid="stop-button"]',
    "fetchErrorSelector": '[data-testid="conversation-fetch-error-toaster"]',
    "challengeSelector": 'iframe[src*="challenges.cloudflare.com"], [id*="challenge"]',
}

DOM_SNAPSHOT_EXPRESSION = """({mainSelector, messageSelector, stopSelector, fetchErrorSelector, challengeSelector}) => {
    const visible = node => !!node.getClientRects().length
        && getComputedStyle(node).visibility === "visible";
    const mains = [...document.querySelectorAll(mainSelector)];
    const messages = mains.length === 1
        ? [...mains[0].querySelectorAll(messageSelector)].map(node => ({
            role: node.getAttribute("data-message-author-role") || "",
            messageId: node.getAttribute("data-message-id"),
            text: node.innerText.trim(), visible: visible(node)
        })) : [];
    const error = [...document.querySelectorAll(fetchErrorSelector)].find(visible);
    return {
        url: location.href, messages,
        generating: [...document.querySelectorAll(stopSelector)].some(visible),
        fetchError: error ? error.innerText.trim().slice(0, 240) : null,
        challenge: [...document.querySelectorAll(challengeSelector)].some(visible)
    };
}"""


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def validate_prompt_digest(value: str) -> str:
    if (
        not isinstance(value, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
        or value == sha256_bytes(b"")
    ):
        raise ValueError("expected nonempty prompt SHA-256 digest")
    return value


def _select_turn_output(
    messages: list[tuple[str, str]], matches_prompt: Callable[[str], bool],
    *, required_index: int | None = None,
) -> tuple[str, bool, str | None]:
    """Resolve only an unambiguous observed user/assistant pair."""
    matches = [
        index
        for index, (role, text) in enumerate(messages)
        if role == "user" and matches_prompt(text)
        and (required_index is None or index == required_index)
    ]
    if not matches:
        return "EXPECTED_USER_TURN_NOT_VISIBLE", False, None
    if len(matches) != 1:
        return "EXPECTED_USER_TURN_AMBIGUOUS", True, None
    following = messages[matches[0] + 1 :]
    candidates: list[str] = []
    for role, text in following:
        if role == "user":
            break
        if role == "assistant":
            candidates.append(text)
    if len(candidates) > 1:
        return "ASSISTANT_OUTPUT_AMBIGUOUS", True, None
    if not following or following[0][0] != "assistant" or not candidates or not candidates[0]:
        return "ASSISTANT_OUTPUT_NOT_VISIBLE", True, None
    return "CAPTURED", True, candidates[0]


def select_exact_turn_output(
    messages: list[tuple[str, str]], expected_prompt: str
) -> tuple[str, bool, str | None]:
    """Text-based caller: no provider-issued turn identifier is inferred."""
    return _select_turn_output(messages, lambda text: text == expected_prompt)


def recommendation(text: str) -> str | None:
    labels = ("DO_NOT_SUBMIT", "REPAIR_THEN_REREVIEW", "ACCEPTABLE_TO_SUBMIT")
    stripped = text.rstrip()
    matches = [label for label in labels if stripped.endswith(label)]
    return matches[0] if len(matches) == 1 else None


def validate_dom_message_id(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value) is None:
        raise ValueError("expected bounded observed DOM message identity")
    return value


def _ordered_user_identities(
    snapshot: object, target_resource: str, *, before_send: bool,
) -> list[tuple[str, str]] | None:
    """A conservative visible user-prefix witness, not a provider ID certificate."""
    if (
        not isinstance(snapshot, dict)
        or chatgpt_resource_from_page_url(snapshot.get("url")) != target_resource
        or snapshot.get("challenge") is not False
        or "fetchError" not in snapshot or snapshot["fetchError"] is not None
        or type(snapshot.get("generating")) is not bool
        or (before_send and snapshot["generating"])
        or not isinstance(snapshot.get("messages"), list)
    ):
        return None
    identities = []
    seen_ids: set[str] = set()
    for node in snapshot["messages"]:
        if not isinstance(node, dict) or not isinstance(node.get("role"), str):
            return None
        message_id = node.get("messageId")
        if message_id is not None:
            try:
                validate_dom_message_id(message_id)
            except ValueError:
                return None
            if message_id in seen_ids:
                return None
            seen_ids.add(message_id)
        if node["role"] != "user":
            continue
        text = node.get("text")
        if message_id is None or node.get("visible") is not True or not isinstance(text, str) or not text:
            return None
        try:
            text_digest = sha256_bytes(text.encode("utf-8"))
        except UnicodeError:
            return None
        identities.append((message_id, text_digest))
    return identities if identities else None


def qualify_user_append_witness(
    before: object, after: object, target_resource: str, expected_prompt_digest: str,
) -> dict | None:
    """Only one appended matching user identity may witness a new observed message.

    This cannot prove provider-issued identity, exclusive SEND or consumer ACK.
    Older receipts without the witness cannot be retroactively upgraded.
    """
    digest = validate_prompt_digest(expected_prompt_digest)
    previous = _ordered_user_identities(before, target_resource, before_send=True)
    observed = _ordered_user_identities(after, target_resource, before_send=False)
    if (
        previous is None or observed is None or len(observed) != len(previous) + 1
        or observed[:-1] != previous or observed[-1][1] != digest
    ):
        return None

    def identity_digest(rows: list[tuple[str, str]]) -> str:
        return sha256_bytes(json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))

    return {
        "schemaVersion": 1,
        "kind": "ordivon.dom-user-append-witness",
        "evidenceScope": "OBSERVED_DOM_APPEND_ONLY",
        "targetResource": target_resource,
        "promptDigest": digest,
        "domUserMessageId": observed[-1][0],
        "previousUserCount": len(previous),
        "observedUserCount": len(observed),
        "previousUserIdentityDigest": identity_digest(previous),
        "observedUserIdentityDigest": identity_digest(observed),
    }


def observe_dom_snapshot(page) -> object:
    """Best-effort witness acquisition cannot rewrite the existing SEND standing."""
    try:
        return page.evaluate(DOM_SNAPSHOT_EXPRESSION, DOM_SNAPSHOT_ARGS)
    except Exception:
        return None


def _qualify_snapshot(
    snapshot: object, target_resource: str, matches_prompt: Callable[[str], bool],
    page_url_after: str, fetch_error_text: str | None = None, *,
    expected_dom_user_message_id: str | None = None,
) -> dict:
    """Classify one observed DOM cut; unknown evidence never yields output."""
    observed = None
    expected_visible = False
    assistant_text = None
    url = None
    error = None
    generating = None
    target_still_bound = False
    standing = "OBSERVATION_INVALID"
    matched_message_id = None
    if expected_dom_user_message_id is not None:
        validate_dom_message_id(expected_dom_user_message_id)
    if isinstance(snapshot, dict):
        url = snapshot.get("url")
        nodes = snapshot.get("messages")
        generation = snapshot.get("generating")
        challenge = snapshot.get("challenge")
        error_field = snapshot.get("fetchError")
        if (
            isinstance(url, str) and isinstance(nodes, list)
            and type(generation) is bool and type(challenge) is bool
            and "fetchError" in snapshot
            and (error_field is None or isinstance(error_field, str))
            and all(
                isinstance(node, dict) and isinstance(node.get("role"), str)
                and isinstance(node.get("text"), str) and type(node.get("visible")) is bool
                for node in nodes
            )
        ):
            generating = generation
            observed = chatgpt_resource_from_page_url(url)
            target_still_bound = (
                observed == target_resource
                and chatgpt_resource_from_page_url(page_url_after) == target_resource
            )
            messages = [
                (node["role"], node["text"] if node["visible"] else "")
                for node in nodes
            ]
            if expected_dom_user_message_id is None:
                standing, expected_visible, assistant_text = _select_turn_output(
                    messages, matches_prompt
                )
                if any(
                    node["role"] == "user" and matches_prompt(node["text"]) and not node["visible"]
                    for node in nodes
                ):
                    standing = "EXPECTED_USER_TURN_AMBIGUOUS"
            else:
                matches = [
                    i for i, node in enumerate(nodes)
                    if node.get("messageId") == expected_dom_user_message_id
                ]
                if not matches:
                    standing = "EXPECTED_USER_MESSAGE_ID_NOT_VISIBLE"
                elif len(matches) != 1:
                    standing = "EXPECTED_USER_MESSAGE_ID_AMBIGUOUS"
                else:
                    index = matches[0]
                    node = nodes[index]
                    if node["role"] != "user" or not node["visible"] or not matches_prompt(node["text"]):
                        standing = "EXPECTED_USER_MESSAGE_ID_CONFLICT"
                    else:
                        standing, expected_visible, assistant_text = _select_turn_output(
                            messages, matches_prompt, required_index=index,
                        )
                        matched_message_id = expected_dom_user_message_id
            error = fetch_error_text if fetch_error_text is not None else error_field
            if challenge:
                standing = "CHALLENGE_GATED"
            elif error is not None:
                standing = "CONVERSATION_FETCH_FAILED"
            elif not target_still_bound:
                standing = "TARGET_RESOURCE_DRIFTED"
            elif generating:
                standing = "ASSISTANT_GENERATING"
    if standing != "CAPTURED":
        assistant_text = None
        matched_message_id = None
    return {
        "standing": standing,
        "observedDomUserMessageId": matched_message_id,
        "evidenceScope": (
            "OBSERVED_ROLE_PAIR_ONLY" if expected_dom_user_message_id is None
            else "OBSERVED_DOM_MESSAGE_ID_MATCH" if matched_message_id is not None
            else "DOM_MESSAGE_ID_REQUIRED"
        ),
        "pageUrlObserved": url if isinstance(url, str) else None,
        "observedResourceAfterWait": observed,
        "targetStillBoundAfterWait": target_still_bound,
        "expectedUserTurnVisible": expected_visible,
        "promptMarkersUsed": [],
        "captureMethod": "role-scoped" if assistant_text is not None else None,
        "conversationFetchError": error,
        "generationActive": generating,
        "assistantOutputRead": assistant_text is not None,
        "assistantOutput": assistant_text,
        "assistantOutputDigest": sha256_bytes(assistant_text.encode("utf-8"))
        if assistant_text is not None else None,
        "recommendation": recommendation(assistant_text) if assistant_text is not None else None,
    }



def qualify_snapshot(
    snapshot: object, target_resource: str, expected_prompt: str, page_url_after: str,
    fetch_error_text: str | None = None, *,
    expected_dom_user_message_id: str | None = None,
) -> dict:
    return _qualify_snapshot(
        snapshot, target_resource, lambda text: text == expected_prompt,
        page_url_after, fetch_error_text,
        expected_dom_user_message_id=expected_dom_user_message_id,
    )


def qualify_snapshot_by_digest(
    snapshot: object, target_resource: str, expected_prompt_digest: str, page_url_after: str,
    fetch_error_text: str | None = None, *,
    expected_dom_user_message_id: str | None = None,
) -> dict:
    """Match exact observed UTF-8 bytes to a durable nonempty prompt digest.

    Equality relies on SHA-256 collision resistance. No extra normalization
    or recovery of the original prompt is required. A rendering mismatch
    withholds output rather than broadening the match.
    """
    digest = validate_prompt_digest(expected_prompt_digest)
    return _qualify_snapshot(
        snapshot, target_resource,
        lambda text: bool(text) and sha256_bytes(text.encode("utf-8")) == digest,
        page_url_after, fetch_error_text,
        expected_dom_user_message_id=expected_dom_user_message_id,
    )
