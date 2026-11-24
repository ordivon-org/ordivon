#!/usr/bin/env python3
"""Read one completed assistant response from an exact provider-bound ChatGPT conversation.

This is a read-only evidence primitive. It never fills a composer, clicks SEND, retries a turn, or
changes the continuation ledger. The caller supplies the exact user prompt that must already be
present in the target conversation; only the assistant message immediately following that user
turn may be captured.
"""

from __future__ import annotations

import argparse
import json
import rfc8785
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from browserless_substrate import BrowserlessEndpoint
from chatgpt_provider_gate import challenge_gated
from chatgpt_provider_resource import canonical_chatgpt_resource, chatgpt_resource_from_page_url
from conversation_output_evidence import (
    DOM_SNAPSHOT_ARGS, DOM_SNAPSHOT_EXPRESSION, qualify_snapshot, sha256_bytes,
    select_exact_turn_output as select_exact_turn_output,
    recommendation as recommendation,
)

STOP_SELECTOR = 'button[data-testid="stop-button"]'
CHALLENGE_SELECTOR = 'iframe[src*="challenges.cloudflare.com"], [id*="challenge"]'
FETCH_ERROR_SELECTOR = '[data-testid="conversation-fetch-error-toaster"]'
MAIN_SELECTOR = "main"


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
    page, target_resource: str, expected_prompt: str, fetch_error_text: str | None
) -> dict:
    """Observe through Playwright; reuse the transport-independent qualifier."""
    snapshot = page.evaluate(DOM_SNAPSHOT_EXPRESSION, DOM_SNAPSHOT_ARGS)
    return qualify_snapshot(snapshot, target_resource, expected_prompt, page.url, fetch_error_text)


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
            observation = observe_output(page, target_resource, expected_prompt, fetch_error_text)
            receipt = {
                "schemaVersion": 1,
                "kind": "ordivon.browserless-conversation-output-receipt",
                "targetResource": target_resource,
                "browserlessEndpointId": endpoint.endpoint_id,
                "expectedUserPromptDigest": expected_prompt_digest,
                "expectedUserPromptFileDigest": expected_prompt_file_digest,
                "mainTextChars": len(main_text),
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
