#!/usr/bin/env python3
"""Read one completed assistant response from an exact provider-bound ChatGPT conversation.

This read-only primitive never navigates, creates pages, fills a composer, clicks SEND, retries a turn,\nor changes the continuation ledger. The caller supplies exact prompt bytes or a durable digest and\nobserved DOM user message identity; only the existing unambiguous target may be observed.
"""

from __future__ import annotations

import argparse
import json
import rfc8785
import os
import re
import uuid
from pathlib import Path

from playwright.sync_api import sync_playwright

from browserless_substrate import BrowserlessEndpoint
from chatgpt_provider_resource import canonical_chatgpt_resource, chatgpt_resource_from_page_url
from conversation_output_evidence import (
    DOM_SNAPSHOT_ARGS,
    DOM_SNAPSHOT_EXPRESSION,
    qualify_snapshot,
    qualify_snapshot_by_digest,
    sha256_bytes,
    validate_dom_message_id,
    validate_prompt_digest,
    select_exact_turn_output as select_exact_turn_output,
    recommendation as recommendation,
)


def digest_obj(value: object) -> str:
    return sha256_bytes(rfc8785.dumps(value))


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


def observe_output(
    page,
    target_resource: str,
    expected_prompt: str,
    fetch_error_text: str | None,
    *,
    expected_dom_user_message_id: str | None = None,
) -> dict:
    """Observe through Playwright; reuse the transport-independent qualifier."""
    snapshot = page.evaluate(DOM_SNAPSHOT_EXPRESSION, DOM_SNAPSHOT_ARGS)
    return qualify_snapshot(
        snapshot,
        target_resource,
        expected_prompt,
        page.url,
        fetch_error_text,
        expected_dom_user_message_id=expected_dom_user_message_id,
    )


def read_existing_playwright_output(
    browser,
    *,
    target_resource: str,
    expected_prompt_digest: str,
    expected_dom_user_message_id: str | None = None,
) -> dict:
    """One existing-browser observation; never navigate, create or close a page."""
    if canonical_chatgpt_resource(target_resource) != target_resource:
        raise ValueError("target must be one canonical conversation resource")
    validate_prompt_digest(expected_prompt_digest)
    if expected_dom_user_message_id is not None:
        validate_dom_message_id(expected_dom_user_message_id)

    def withheld(standing: str) -> dict:
        return {
            "standing": standing,
            "observedDomUserMessageId": None,
            "evidenceScope": "OBSERVED_ROLE_PAIR_ONLY"
            if expected_dom_user_message_id is None
            else "DOM_MESSAGE_ID_REQUIRED",
            "pageUrlObserved": None,
            "observedResourceAfterWait": None,
            "targetStillBoundAfterWait": False,
            "expectedUserTurnVisible": False,
            "promptMarkersUsed": [],
            "captureMethod": None,
            "conversationFetchError": None,
            "generationActive": None,
            "assistantOutputRead": False,
            "assistantOutput": None,
            "assistantOutputDigest": None,
            "recommendation": None,
            "releaseAttempted": False,
            "mainTextChars": None,
        }

    def matching_pages(context) -> list:
        return [
            page
            for page in context.pages
            if chatgpt_resource_from_page_url(page.url) == target_resource
        ]

    try:
        contexts = browser.contexts
        if len(contexts) != 1:
            return withheld("CONTEXT_AMBIGUOUS")
        context = contexts[0]
        pages = matching_pages(context)
        if not pages:
            return withheld("TARGET_NOT_VISIBLE")
        if len(pages) != 1:
            return withheld("TARGET_AMBIGUOUS")
        page = pages[0]
        snapshot = page.evaluate(DOM_SNAPSHOT_EXPRESSION, DOM_SNAPSHOT_ARGS)
        contexts_after = browser.contexts
        if len(contexts_after) != 1 or contexts_after[0] is not context:
            return withheld("TARGET_RESOURCE_DRIFTED")
        after = matching_pages(context)
        if len(after) != 1 or after[0] is not page:
            return withheld("TARGET_RESOURCE_DRIFTED")
        observation = qualify_snapshot_by_digest(
            snapshot,
            target_resource,
            expected_prompt_digest,
            page.url,
            expected_dom_user_message_id=expected_dom_user_message_id,
        )
        # Error text and unrelated URLs are not part of the recipient's result.
        if observation["conversationFetchError"] is not None:
            observation["conversationFetchError"] = "OBSERVED"
        if observation["standing"] == "TARGET_RESOURCE_DRIFTED":
            return withheld("TARGET_RESOURCE_DRIFTED")
        return {**observation, "releaseAttempted": False, "mainTextChars": None}
    except Exception:
        return withheld("TRANSPORT_ERROR")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--endpoint-id", required=True)
    parser.add_argument("--target-resource", required=True)
    prompt_input = parser.add_mutually_exclusive_group(required=True)
    prompt_input.add_argument("--expected-user-prompt-file", type=Path)
    prompt_input.add_argument("--expected-prompt-digest")
    parser.add_argument("--observation-id")
    parser.add_argument("--receipt-out", type=Path, required=True)
    parser.add_argument("--expected-dom-user-message-id")
    args = parser.parse_args()
    if args.expected_dom_user_message_id is not None:
        validate_dom_message_id(args.expected_dom_user_message_id)

    if args.expected_prompt_digest is not None:
        if args.expected_dom_user_message_id is None or args.observation_id is None:
            parser.error(
                "digest-only reads require the observed DOM user identity and observation ID"
            )
        expected_prompt_digest = validate_prompt_digest(args.expected_prompt_digest)
        expected_prompt_file_digest = None
    else:
        expected_file_raw = args.expected_user_prompt_file.read_bytes()
        expected_prompt = expected_file_raw.decode("utf-8")
        if expected_prompt.endswith("\\r\\n"):
            expected_prompt = expected_prompt[:-2]
        elif expected_prompt.endswith("\\n"):
            expected_prompt = expected_prompt[:-1]
        if not expected_prompt.strip() or expected_prompt != expected_prompt.strip():
            raise SystemExit(
                "expected user prompt must be non-empty and trimmed after one transport newline is removed"
            )
        expected_prompt_digest = sha256_bytes(expected_prompt.encode("utf-8"))
        expected_prompt_file_digest = sha256_bytes(expected_file_raw)
    observation_id = args.observation_id if args.observation_id is not None else str(uuid.uuid4())
    if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", observation_id) is None:
        parser.error("invalid observation identity")
    target_resource = canonical_chatgpt_resource(args.target_resource)
    endpoint = endpoint_from_config(args.config, args.endpoint_id)
    connection_url = endpoint.authenticated_operator_connection_endpoint(timeout_ms=90_000)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(connection_url, timeout=20_000)
        try:
            observation = read_existing_playwright_output(
                browser,
                target_resource=target_resource,
                expected_prompt_digest=expected_prompt_digest,
                expected_dom_user_message_id=args.expected_dom_user_message_id,
            )
            receipt = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-conversation-output-receipt",
                "targetResource": target_resource,
                "browserlessEndpointId": endpoint.endpoint_id,
                "expectedUserPromptDigest": expected_prompt_digest,
                "expectedUserPromptFileDigest": expected_prompt_file_digest,
                "observationId": observation_id,
                **observation,
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
            return 0 if receipt["standing"] == "CAPTURED" else 3
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
