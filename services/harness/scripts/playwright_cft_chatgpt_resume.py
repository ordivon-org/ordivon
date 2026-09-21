#!/usr/bin/env python3
"""Resume one HUMAN_REQUIRED ChatGPT materialization through an exact loopback CfT session."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from chatgpt_provider_resource import chatgpt_resource_from_page_url
from playwright_browserless_chatgpt_submit import (
    PRE_EFFECT_BLOCKER_SELECTOR,
    PROMPT_SELECTOR,
    SEND_SELECTOR,
    STOP_SELECTOR,
    digest_bytes,
    digest_obj,
    human_blocker,
    stabilize_empty_composer,
    wait_for_canonical_after_send,
)

PRE_EFFECT_BLOCKED_EXIT = 42


def _loopback_endpoint(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https", "ws", "wss"}
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.port is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("CfT resume requires one explicit loopback CDP endpoint")
    return value


def _private_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def _pre_effect(path: Path, *, effect_id: str, prompt_digest: str, blocker: str, page_url: str) -> None:
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.cft-chatgpt-pre-effect-blocker",
        "effectId": effect_id,
        "promptDigest": prompt_digest,
        "blocker": blocker,
        "pageUrl": page_url,
        "providerEffectAttempted": False,
        "sendAttempted": False,
    }
    value["evidenceDigest"] = digest_obj(value)
    _private_json(path, value)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cdp-endpoint", required=True)
    p.add_argument("--session-id", required=True)
    p.add_argument("--handoff", type=Path, required=True)
    p.add_argument("--expected-handoff-digest", required=True)
    p.add_argument("--bootstrap-file", type=Path, required=True)
    p.add_argument("--effect-id", required=True)
    p.add_argument("--prompt-digest", required=True)
    p.add_argument("--handle-out", type=Path, required=True)
    p.add_argument("--pre-effect-out", type=Path, required=True)
    p.add_argument("--wait-stable-seconds", type=int, default=150)
    return p


def main() -> int:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect, sync_playwright

    a = parser().parse_args()
    endpoint = _loopback_endpoint(a.cdp_endpoint)
    handoff = json.loads(a.handoff.read_text(encoding="utf-8"))
    supplied = handoff.get("handoffDigest")
    if supplied != a.expected_handoff_digest:
        raise SystemExit("handoff digest mismatch")
    if handoff.get("effectId") != a.effect_id or handoff.get("sessionId") != a.session_id:
        raise SystemExit("handoff identity mismatch")
    if handoff.get("providerEffectAttempted") is not False or handoff.get("sendAttempted") is not False:
        raise SystemExit("handoff does not prove pre-SEND standing")
    raw = a.bootstrap_file.read_bytes()
    prompt = raw.decode("utf-8")
    if digest_bytes(raw) != a.prompt_digest:
        raise SystemExit("prompt digest mismatch")
    if not prompt.strip() or prompt != prompt.strip():
        raise SystemExit("bootstrap prompt must be non-empty and trimmed")

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(endpoint, timeout=20_000)
        try:
            contexts = browser.contexts
            if len(contexts) != 1:
                _pre_effect(
                    a.pre_effect_out, effect_id=a.effect_id, prompt_digest=a.prompt_digest,
                    blocker="cft-context-cardinality", page_url="",
                )
                return PRE_EFFECT_BLOCKED_EXIT
            pages = [p for p in contexts[0].pages if p.url.startswith("https://chatgpt.com")]
            if len(pages) != 1:
                _pre_effect(
                    a.pre_effect_out, effect_id=a.effect_id, prompt_digest=a.prompt_digest,
                    blocker="cft-chatgpt-page-cardinality", page_url="",
                )
                return PRE_EFFECT_BLOCKED_EXIT
            page = pages[0]
            blocker = human_blocker(page)
            if blocker is not None:
                _pre_effect(
                    a.pre_effect_out, effect_id=a.effect_id, prompt_digest=a.prompt_digest,
                    blocker=f"human-auth-not-complete:{blocker}", page_url=page.url,
                )
                return PRE_EFFECT_BLOCKED_EXIT
            composer = page.locator(PROMPT_SELECTOR)
            try:
                composer.wait_for(state="visible", timeout=20_000)
            except Exception as error:
                _pre_effect(
                    a.pre_effect_out, effect_id=a.effect_id, prompt_digest=a.prompt_digest,
                    blocker=f"composer-unavailable:{type(error).__name__}", page_url=page.url,
                )
                return PRE_EFFECT_BLOCKED_EXIT
            stop = page.locator(STOP_SELECTOR)
            if stop.count() > 0 and stop.is_visible():
                _pre_effect(
                    a.pre_effect_out, effect_id=a.effect_id, prompt_digest=a.prompt_digest,
                    blocker="already-generating", page_url=page.url,
                )
                return PRE_EFFECT_BLOCKED_EXIT
            if not stabilize_empty_composer(page, composer):
                _pre_effect(
                    a.pre_effect_out, effect_id=a.effect_id, prompt_digest=a.prompt_digest,
                    blocker="composer-not-empty", page_url=page.url,
                )
                return PRE_EFFECT_BLOCKED_EXIT
            composer.fill(prompt)
            modal = page.locator(PRE_EFFECT_BLOCKER_SELECTOR)
            if modal.count() > 0 and modal.is_visible():
                composer.fill("")
                _pre_effect(
                    a.pre_effect_out, effect_id=a.effect_id, prompt_digest=a.prompt_digest,
                    blocker="conversation-history-rate-limit-modal", page_url=page.url,
                )
                return PRE_EFFECT_BLOCKED_EXIT
            send = page.locator(SEND_SELECTOR)
            expect(send).to_be_visible()
            send.click()
            expect(composer).to_be_empty()
            try:
                page.locator(STOP_SELECTOR).wait_for(state="visible", timeout=10_000)
                generation_started = True
            except PlaywrightTimeoutError:
                generation_started = False
            resource = wait_for_canonical_after_send(
                page, generation_started=generation_started,
                hard_timeout_seconds=a.wait_stable_seconds,
            )
            handle = {
                "schemaVersion": 1,
                "kind": "ordivon.cft-chatgpt-page-binding",
                "effectId": a.effect_id,
                "promptDigest": a.prompt_digest,
                "browserSubstrate": "cft-human-session",
                "sessionId": a.session_id,
                "pageUrlAfterSubmit": page.url,
                "providerResource": resource or chatgpt_resource_from_page_url(page.url),
                "generationStarted": generation_started,
                "composerCleared": True,
                "assistantOutputRead": False,
            }
            handle["bindingDigest"] = digest_obj(handle)
            _private_json(a.handle_out, handle)
            print(json.dumps(handle, sort_keys=True))
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    raise SystemExit(main())
