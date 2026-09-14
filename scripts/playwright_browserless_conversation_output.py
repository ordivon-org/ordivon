#!/usr/bin/env python3
"""Read one completed assistant response from an exact provider-bound ChatGPT conversation.

This is a read-only evidence primitive. It never fills a composer, clicks SEND, retries a turn, or
changes the continuation ledger. The caller supplies the exact user prompt that must already be
present in the target conversation; only the assistant message immediately following that user
turn may be captured.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from browserless_substrate import BrowserlessEndpoint
from chatgpt_provider_gate import challenge_gated
from chatgpt_provider_resource import canonical_chatgpt_resource, chatgpt_resource_from_page_url

STOP_SELECTOR = 'button[data-testid="stop-button"]'
CHALLENGE_SELECTOR = 'iframe[src*="challenges.cloudflare.com"], [id*="challenge"]'
FETCH_ERROR_SELECTOR = '[data-testid="conversation-fetch-error-toaster"]'
MAIN_SELECTOR = "main"
MESSAGE_SELECTOR = "[data-message-author-role]"


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def digest_obj(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


def endpoint_from_config(path: Path, endpoint_id: str) -> BrowserlessEndpoint:
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("browserSubstrate", {}).get("endpoints", [])
    matches = [
        BrowserlessEndpoint.from_dict(row)
        for row in rows
        if isinstance(row, dict) and row.get("id") == endpoint_id
    ]
    if len(matches) != 1:
        raise SystemExit("configured Browserless endpoint id must resolve exactly once")
    endpoint = matches[0]
    if endpoint.endpoint_id != endpoint_id:
        raise SystemExit("configured Browserless endpoint identity mismatch")
    return endpoint


def prompt_markers(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    markers = [lines[0]]
    for prefix in (
        "MANUSCRIPT_SHA256=",
        "PAYLOAD_SHA256=",
        "BYTE_RANGE=",
        "PAYLOAD_END",
        "All four numbered manuscript payload chunks",
        "All four revised manuscript payload chunks",
    ):
        match = next((line for line in lines if line.startswith(prefix)), None)
        if match and match not in markers:
            markers.append(match)
    return markers


def body_anchored_output(
    body_text: str, expected_prompt: str
) -> tuple[bool, str | None, list[str]]:
    markers = prompt_markers(expected_prompt)
    if not markers or not all(marker in body_text for marker in markers):
        return False, None, markers
    exact_index = body_text.find(expected_prompt)
    if exact_index >= 0:
        tail = body_text[exact_index + len(expected_prompt) :]
    else:
        anchor = markers[-1]
        anchor_index = body_text.rfind(anchor)
        tail = body_text[anchor_index + len(anchor) :] if anchor_index >= 0 else ""
    footer_index = tail.find("ChatGPT can make mistakes.")
    if footer_index >= 0:
        tail = tail[:footer_index]
    tail = tail.strip()
    while tail.startswith("Show more"):
        tail = tail[len("Show more") :].lstrip()
    return True, tail or None, markers


def recommendation(text: str) -> str | None:
    labels = ("DO_NOT_SUBMIT", "REPAIR_THEN_REREVIEW", "ACCEPTABLE_TO_SUBMIT")
    stripped = text.rstrip()
    matches = [label for label in labels if stripped.endswith(label)]
    return matches[0] if len(matches) == 1 else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--endpoint-id", required=True)
    parser.add_argument("--target-resource", required=True)
    parser.add_argument("--expected-user-prompt-file", type=Path, required=True)
    parser.add_argument("--receipt-out", type=Path, required=True)
    args = parser.parse_args()

    expected_file_raw = args.expected_user_prompt_file.read_bytes()
    expected_prompt = expected_file_raw.decode("utf-8")
    if expected_prompt.endswith("\r\n"):
        expected_prompt = expected_prompt[:-2]
    elif expected_prompt.endswith("\n"):
        expected_prompt = expected_prompt[:-1]
    if not expected_prompt.strip() or expected_prompt != expected_prompt.strip():
        raise SystemExit(
            "expected user prompt must be non-empty and trimmed after one transport newline is removed"
        )
    expected_prompt_digest = sha256_bytes(expected_prompt.encode("utf-8"))
    expected_prompt_file_digest = sha256_bytes(expected_file_raw)
    target_resource = canonical_chatgpt_resource(args.target_resource)
    endpoint = endpoint_from_config(args.config, args.endpoint_id)
    connection_url = endpoint.authenticated_operator_connection_endpoint(timeout_ms=90_000)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(connection_url, timeout=20_000)
        try:
            if len(browser.contexts) != 1:
                raise SystemExit("Browserless output capture context cardinality changed")
            context = browser.contexts[0]
            pages = [
                page
                for page in context.pages
                if page.url.startswith("https://chatgpt.com") or page.url == "about:blank"
            ]
            page = pages[0] if len(pages) == 1 else (context.new_page() if not pages else None)
            if page is None:
                raise SystemExit("Browserless output capture page cardinality changed")
            if chatgpt_resource_from_page_url(page.url) != target_resource:
                page.goto(target_resource, wait_until="domcontentloaded", timeout=30_000)
            hydration_deadline = time.monotonic() + 20.0
            main_text = ""
            fetch_error_text = None
            while True:
                if challenge_gated(page, CHALLENGE_SELECTOR):
                    raise SystemExit("Browserless output capture is challenge-gated")
                fetch_error = page.locator(FETCH_ERROR_SELECTOR)
                if fetch_error.count() and fetch_error.first.is_visible():
                    fetch_error_text = fetch_error.first.inner_text().strip()[:240]
                    break
                observed_resource_after_wait = chatgpt_resource_from_page_url(page.url)
                if observed_resource_after_wait != target_resource:
                    break
                main = page.locator(MAIN_SELECTOR)
                main_text = main.inner_text().strip() if main.count() == 1 else ""
                if len(main_text) >= 32:
                    page.wait_for_timeout(500)
                    main = page.locator(MAIN_SELECTOR)
                    stable_text = main.inner_text().strip() if main.count() == 1 else ""
                    if (
                        len(stable_text) >= 32
                        and chatgpt_resource_from_page_url(page.url) == target_resource
                    ):
                        main_text = stable_text
                        break
                if time.monotonic() >= hydration_deadline:
                    break
                page.wait_for_timeout(500)
            observed_resource_after_wait = chatgpt_resource_from_page_url(page.url)
            target_still_bound = observed_resource_after_wait == target_resource

            stop = page.locator(STOP_SELECTOR)
            generation_active = stop.count() == 1 and stop.is_visible()
            nodes = page.locator(MESSAGE_SELECTOR)
            messages: list[tuple[str, str]] = []
            for index in range(nodes.count()):
                node = nodes.nth(index)
                role = node.get_attribute("data-message-author-role") or ""
                text = node.inner_text().strip()
                messages.append((role, text))

            matched_index = None
            for index, (role, text) in enumerate(messages):
                if role == "user" and text == expected_prompt:
                    matched_index = index
            assistant_text = None
            capture_method = None
            prompt_markers_used: list[str] = []
            if matched_index is not None:
                for role, text in messages[matched_index + 1 :]:
                    if role == "user":
                        break
                    if role == "assistant" and text:
                        assistant_text = text
                        capture_method = "role-scoped"
                        break
            body_text = page.locator("body").inner_text()
            body_visible, body_output, prompt_markers_used = body_anchored_output(
                body_text, expected_prompt
            )
            expected_user_visible = matched_index is not None or body_visible
            if assistant_text is None and body_output is not None:
                assistant_text = body_output
                capture_method = "body-anchor"

            if fetch_error_text is not None:
                standing = "CONVERSATION_FETCH_FAILED"
            elif not target_still_bound:
                standing = "TARGET_RESOURCE_DRIFTED"
            elif not expected_user_visible:
                standing = "EXPECTED_USER_TURN_NOT_VISIBLE"
            elif generation_active:
                standing = "ASSISTANT_GENERATING"
            elif assistant_text is None:
                standing = "ASSISTANT_OUTPUT_NOT_VISIBLE"
            else:
                standing = "CAPTURED"

            receipt = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-conversation-output-receipt",
                "standing": standing,
                "targetResource": target_resource,
                "browserlessEndpointId": endpoint.endpoint_id,
                "pageUrlObserved": page.url,
                "observedResourceAfterWait": observed_resource_after_wait,
                "targetStillBoundAfterWait": target_still_bound,
                "expectedUserPromptDigest": expected_prompt_digest,
                "expectedUserPromptFileDigest": expected_prompt_file_digest,
                "expectedUserTurnVisible": expected_user_visible,
                "promptMarkersUsed": prompt_markers_used,
                "captureMethod": capture_method,
                "conversationFetchError": fetch_error_text,
                "mainTextChars": len(main_text),
                "generationActive": generation_active,
                "assistantOutputRead": assistant_text is not None,
                "assistantOutput": assistant_text,
                "assistantOutputDigest": sha256_bytes(assistant_text.encode("utf-8"))
                if assistant_text is not None
                else None,
                "recommendation": recommendation(assistant_text)
                if assistant_text is not None
                else None,
                "providerEffectAttempted": False,
                "composerFilled": False,
                "sendAttempted": False,
            }
            receipt["receiptDigest"] = digest_obj(receipt)
            args.receipt_out.parent.mkdir(parents=True, exist_ok=True)
            args.receipt_out.write_text(
                json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            os.chmod(args.receipt_out, 0o600)
            print(json.dumps(receipt, sort_keys=True, ensure_ascii=False))
            return 0 if standing == "CAPTURED" else 3
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
