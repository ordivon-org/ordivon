"""Pure result observation contract shared by browser transports.

No browser lifecycle, provider calls, credential access or execution authority.
A snapshot alone cannot prove a provider-issued turn ID or domain acceptance.
"""
from __future__ import annotations

import hashlib

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


def select_exact_turn_output(
    messages: list[tuple[str, str]], expected_prompt: str
) -> tuple[str, bool, str | None]:
    """Resolve only an unambiguous observed user/assistant pair.

    The caller's prompt is not a provider-issued turn identifier. Repeated
    exact prompts, multiple candidate assistant messages and unstructured
    page text cannot prove which result belongs to the requested turn.
    """
    matches = [
        index
        for index, (role, text) in enumerate(messages)
        if role == "user" and text == expected_prompt
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


def recommendation(text: str) -> str | None:
    labels = ("DO_NOT_SUBMIT", "REPAIR_THEN_REREVIEW", "ACCEPTABLE_TO_SUBMIT")
    stripped = text.rstrip()
    matches = [label for label in labels if stripped.endswith(label)]
    return matches[0] if len(matches) == 1 else None


def qualify_snapshot(
    snapshot: object, target_resource: str, expected_prompt: str, page_url_after: str,
    fetch_error_text: str | None = None,
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
            standing, expected_visible, assistant_text = select_exact_turn_output(
                messages, expected_prompt
            )
            if any(
                node["role"] == "user" and node["text"] == expected_prompt and not node["visible"]
                for node in nodes
            ):
                standing = "EXPECTED_USER_TURN_AMBIGUOUS"
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
    return {
        "standing": standing,
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
