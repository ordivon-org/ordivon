#!/usr/bin/env python3
"""Exactly-once continuation turn into one provider-bound ChatGPT conversation via Browserless."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect, sync_playwright

from chatgpt_provider_gate import challenge_gated
from chatgpt_provider_resource import canonical_chatgpt_resource, chatgpt_resource_from_page_url

PROMPT_SELECTOR = "#prompt-textarea"
SEND_SELECTOR = 'button[data-testid="send-button"]'
STOP_SELECTOR = 'button[data-testid="stop-button"]'
CHALLENGE_SELECTOR = 'iframe[src*="challenges.cloudflare.com"], [id*="challenge"]'
FETCH_ERROR_SELECTOR = '[data-testid="conversation-fetch-error-toaster"]'
MAIN_SELECTOR = "main"
POST_SEND_ROUTE_STABILIZE_MS = 15_000
POST_SEND_ROUTE_POLL_MS = 250


def _temporary_web_route(url: str) -> bool:
    try:
        parsed = urlsplit(url)
    except (TypeError, ValueError):
        return False
    if parsed.scheme != "https" or parsed.hostname != "chatgpt.com":
        return False
    parts = [part for part in parsed.path.split("/") if part]
    return len(parts) == 2 and parts[0] == "c" and parts[1].startswith("WEB:")


def observe_post_send_route(
    page,
    target_resource: str,
    *,
    generation_started: bool,
    timeout_ms: int = POST_SEND_ROUTE_STABILIZE_MS,
) -> dict:
    """Observe provider routing after SEND without navigating or creating another effect.

    ChatGPT may briefly expose a `/c/WEB:*` client-side route after an accepted continuation
    before rebinding the page to its stable conversation resource.  That transient route is not
    sufficient evidence of target drift.  Wait only while that exact transient is present; a
    different stable canonical resource, a non-WEB unparsed route, or timeout remains fail-closed.
    """
    if timeout_ms < 0:
        raise ValueError("timeout_ms must be non-negative")
    initial_url = page.url
    initial_resource = chatgpt_resource_from_page_url(initial_url)
    current_url = initial_url
    current_resource = initial_resource
    temporary_web_route_observed = _temporary_web_route(current_url)
    deadline = time.monotonic() + timeout_ms / 1000.0
    while (
        generation_started
        and current_resource is None
        and _temporary_web_route(current_url)
        and time.monotonic() < deadline
    ):
        page.wait_for_timeout(POST_SEND_ROUTE_POLL_MS)
        current_url = page.url
        current_resource = chatgpt_resource_from_page_url(current_url)
        temporary_web_route_observed = temporary_web_route_observed or _temporary_web_route(
            current_url
        )
    return {
        "pageUrlImmediatelyAfterSend": initial_url,
        "observedResourceImmediatelyAfterSend": initial_resource,
        "postSendTemporaryWebRouteObserved": temporary_web_route_observed,
        "pageUrlAfterSend": current_url,
        "observedResourceAfterSend": current_resource,
        "targetStillBoundAfterSend": current_resource == target_resource,
    }


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def digest_obj(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


def auth(url: str, token_file: Path) -> str:
    token = token_file.read_text(encoding="utf-8").strip()
    if not token or any(ch.isspace() for ch in token):
        raise ValueError("Browserless token is missing or malformed")
    p = urlsplit(url)
    q = parse_qsl(p.query, keep_blank_values=True)
    q.append(("token", token))
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


def ensure_schema(db: sqlite3.Connection) -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS turn_effects (
          turn_request_id TEXT PRIMARY KEY,
          prompt_digest TEXT NOT NULL,
          target_coordinate TEXT NOT NULL,
          state TEXT NOT NULL,
          receipt_json TEXT,
          updated_at_ms INTEGER NOT NULL
        )
    """)
    db.commit()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--browserless-endpoint", required=True)
    p.add_argument("--browserless-token-file", type=Path, required=True)
    p.add_argument("--endpoint-id", required=True)
    p.add_argument("--target-resource", required=True)
    p.add_argument("--prompt-file", type=Path, required=True)
    p.add_argument("--turn-request-id", required=True)
    p.add_argument("--ledger", type=Path, required=True)
    p.add_argument("--receipt-out", type=Path, required=True)
    a = p.parse_args()

    raw = a.prompt_file.read_bytes()
    prompt = raw.decode("utf-8")
    if not prompt.strip() or prompt != prompt.strip():
        raise SystemExit("prompt must be non-empty and trimmed")
    prompt_digest = sha256_bytes(raw)
    target_resource = canonical_chatgpt_resource(a.target_resource)
    target_url = target_resource
    a.ledger.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(a.ledger)
    try:
        ensure_schema(db)
        row = db.execute(
            "SELECT prompt_digest,target_coordinate,state,receipt_json FROM turn_effects WHERE turn_request_id=?",
            (a.turn_request_id,),
        ).fetchone()
        if row is not None:
            if row[0] != prompt_digest or canonical_chatgpt_resource(row[1]) != target_resource:
                raise SystemExit("turn request identity conflict")
            print(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "kind": "ordivon.browserless-turn-replay",
                        "turnRequestId": a.turn_request_id,
                        "standing": row[2],
                        "safeToResend": False,
                        "receipt": json.loads(row[3]) if row[3] else None,
                    },
                    sort_keys=True,
                )
            )
            return 0

        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(
                auth(a.browserless_endpoint, a.browserless_token_file), timeout=20_000
            )
            try:
                if len(browser.contexts) != 1:
                    raise SystemExit("Browserless continuation context cardinality changed")
                ctx = browser.contexts[0]
                pages = [
                    pg
                    for pg in ctx.pages
                    if pg.url.startswith("https://chatgpt.com") or pg.url == "about:blank"
                ]
                page = pages[0] if len(pages) == 1 else (ctx.new_page() if not pages else None)
                if page is None:
                    raise SystemExit("Browserless continuation page cardinality changed")
                if chatgpt_resource_from_page_url(page.url) != target_resource:
                    page.goto(target_url, wait_until="domcontentloaded", timeout=30_000)
                # URL identity becomes visible before ChatGPT has necessarily hydrated the bound
                # conversation.  Sending while <main> is still empty can submit through the new-chat
                # state machine and produce a WEB:* draft even though the address bar still contains
                # the requested /c/<id>.  Require observable history before claiming the effect.
                hydration_deadline = time.monotonic() + 20.0
                main_text_before_send = ""
                while True:
                    if challenge_gated(page, CHALLENGE_SELECTOR):
                        raise SystemExit("Browserless continuation is challenge-gated")
                    fetch_error = page.locator(FETCH_ERROR_SELECTOR)
                    if fetch_error.count() and fetch_error.first.is_visible():
                        detail = fetch_error.first.inner_text().strip()[:240]
                        raise SystemExit(
                            f"Browserless continuation conversation fetch failed before effect claim: {detail or 'provider fetch error'}"
                        )
                    if chatgpt_resource_from_page_url(page.url) != target_resource:
                        raise SystemExit(
                            "Browserless continuation provider resource mismatch during hydration"
                        )
                    main = page.locator(MAIN_SELECTOR)
                    main_text_before_send = main.inner_text().strip() if main.count() == 1 else ""
                    composer_probe = page.locator(PROMPT_SELECTOR)
                    if (
                        len(main_text_before_send) >= 32
                        and composer_probe.count() == 1
                        and composer_probe.is_visible()
                    ):
                        page.wait_for_timeout(500)
                        if chatgpt_resource_from_page_url(page.url) != target_resource:
                            raise SystemExit(
                                "Browserless continuation provider resource drifted after history hydration"
                            )
                        fetch_error = page.locator(FETCH_ERROR_SELECTOR)
                        if fetch_error.count() and fetch_error.first.is_visible():
                            detail = fetch_error.first.inner_text().strip()[:240]
                            raise SystemExit(
                                f"Browserless continuation conversation fetch failed after hydration: {detail or 'provider fetch error'}"
                            )
                        stable_main = page.locator(MAIN_SELECTOR)
                        stable_text = (
                            stable_main.inner_text().strip() if stable_main.count() == 1 else ""
                        )
                        if len(stable_text) >= 32:
                            main_text_before_send = stable_text
                            break
                    if time.monotonic() >= hydration_deadline:
                        raise SystemExit(
                            "Browserless continuation conversation history did not hydrate before timeout"
                        )
                    page.wait_for_timeout(500)
                stop = page.locator(STOP_SELECTOR)
                if stop.count() == 1 and stop.is_visible():
                    raise SystemExit("Browserless continuation target is still generating")
                composer = page.locator(PROMPT_SELECTOR)
                composer.wait_for(state="visible", timeout=20_000)
                if composer.inner_text().strip():
                    composer.fill("")
                    if composer.inner_text().strip():
                        raise SystemExit("Browserless continuation composer is not empty")
                composer.fill(prompt)
                send = page.locator(SEND_SELECTOR)
                expect(send).to_be_visible()
                page_url_before_send = page.url
                observed_resource_before_send = chatgpt_resource_from_page_url(page_url_before_send)
                if observed_resource_before_send != target_resource:
                    composer.fill("")
                    raise SystemExit(
                        "Browserless continuation provider resource drifted after composer fill"
                    )
                fetch_error = page.locator(FETCH_ERROR_SELECTOR)
                if fetch_error.count() and fetch_error.first.is_visible():
                    composer.fill("")
                    detail = fetch_error.first.inner_text().strip()[:240]
                    raise SystemExit(
                        f"Browserless continuation conversation fetch failed after composer fill: {detail or 'provider fetch error'}"
                    )

                now = int(time.time() * 1000)
                db.execute("BEGIN IMMEDIATE")
                existing = db.execute(
                    "SELECT prompt_digest,target_coordinate,state,receipt_json FROM turn_effects WHERE turn_request_id=?",
                    (a.turn_request_id,),
                ).fetchone()
                if existing is not None:
                    db.rollback()
                    composer.fill("")
                    if (
                        existing[0] != prompt_digest
                        or canonical_chatgpt_resource(existing[1]) != target_resource
                    ):
                        raise SystemExit("turn request identity conflict after claim race")
                    print(
                        json.dumps(
                            {
                                "schemaVersion": 1,
                                "kind": "ordivon.browserless-turn-race",
                                "turnRequestId": a.turn_request_id,
                                "standing": existing[2],
                                "safeToResend": False,
                            },
                            sort_keys=True,
                        )
                    )
                    return 0
                db.execute(
                    "INSERT INTO turn_effects(turn_request_id,prompt_digest,target_coordinate,state,receipt_json,updated_at_ms) VALUES (?,?,?,?,?,?)",
                    (a.turn_request_id, prompt_digest, target_resource, "UNKNOWN", None, now),
                )
                db.commit()

                send.click()
                try:
                    expect(composer).to_be_empty(timeout=10_000)
                    composer_cleared = True
                except Exception:
                    composer_cleared = False
                try:
                    page.locator(STOP_SELECTOR).wait_for(state="visible", timeout=10_000)
                    generation_started = True
                except PlaywrightTimeoutError:
                    generation_started = False
                route_observation = observe_post_send_route(
                    page, target_resource, generation_started=generation_started
                )
                target_still_bound = route_observation["targetStillBoundAfterSend"]
                receipt = {
                    "schemaVersion": 1,
                    "kind": "ordivon.browserless-turn-receipt",
                    "turnRequestId": a.turn_request_id,
                    "promptDigest": prompt_digest,
                    "targetResource": target_resource,
                    "browserlessEndpointId": a.endpoint_id,
                    "pageUrlBeforeSend": page_url_before_send,
                    "observedResourceBeforeSend": observed_resource_before_send,
                    "historyHydratedBeforeSend": True,
                    "mainTextCharsBeforeSend": len(main_text_before_send),
                    **route_observation,
                    "composerCleared": composer_cleared,
                    "generationStarted": generation_started,
                    "assistantOutputRead": False,
                }
                receipt["receiptDigest"] = digest_obj(receipt)
                state = (
                    "COMPLETED"
                    if composer_cleared and generation_started and target_still_bound
                    else "UNKNOWN"
                )
                db.execute(
                    "UPDATE turn_effects SET state=?,receipt_json=?,updated_at_ms=? WHERE turn_request_id=?",
                    (
                        state,
                        json.dumps(receipt, sort_keys=True),
                        int(time.time() * 1000),
                        a.turn_request_id,
                    ),
                )
                db.commit()
                a.receipt_out.parent.mkdir(parents=True, exist_ok=True)
                a.receipt_out.write_text(
                    json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
                )
                os.chmod(a.receipt_out, 0o600)
                print(
                    json.dumps(
                        {
                            "schemaVersion": 1,
                            "kind": "ordivon.browserless-turn-run",
                            "turnRequestId": a.turn_request_id,
                            "standing": state,
                            "safeToResend": False,
                            "receipt": receipt,
                        },
                        sort_keys=True,
                    )
                )
                return 0
            finally:
                browser.close()
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
