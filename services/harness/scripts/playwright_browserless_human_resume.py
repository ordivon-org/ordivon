#!/usr/bin/env python3
"""Revalidate one parked Browserless human-verification session and resume the same materialization effect.

This script never solves a provider challenge. If human verification/authentication is still
required it mints a fresh same-session handoff and returns without filling the composer. Only after
READY is observed does it cross the original prompt SEND boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect, sync_playwright

from browserless_human_handoff import load_verified_handoff, mint_handoff, write_private_handoff
from chatgpt_provider_gate import challenge_gated
from chatgpt_provider_resource import chatgpt_resource_from_page_url
from provider_boundary_diagnosis import (
    PROVIDER_ACTION_HOLD,
    PROVIDER_ACTION_HUMAN_CONTROL_TRANSFER,
    provider_action_for_standing,
)

PROMPT_SELECTOR = "#prompt-textarea"
SEND_SELECTOR = 'button[data-testid="send-button"]'
STOP_SELECTOR = 'button[data-testid="stop-button"]'
CHALLENGE_SELECTOR = 'iframe[src*="challenges.cloudflare.com"], [id*="challenge"]'
LOGIN_SELECTOR = "text=/^Log in$/i"
SIGNUP_SELECTOR = "text=/^Sign up$/i"
PRE_EFFECT_BLOCKER_SELECTOR = '[data-testid="modal-conversation-history-rate-limit"]'
PRE_EFFECT_BLOCKED_EXIT = 42
HUMAN_REQUIRED_EXIT = 43


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def digest_obj(value: object) -> str:
    return digest_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


def auth(url: str, token_file: Path) -> str:
    token = token_file.read_text(encoding="utf-8").strip()
    if not token or any(ch.isspace() for ch in token):
        raise ValueError("Browserless token is missing or malformed")
    parsed = urlsplit(url)
    query = parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("token", token))
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
    )


def write_pre_effect(
    path: Path, *, effect_id: str, prompt_digest: str, blocker: str, page_url: str = ""
) -> None:
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-chatgpt-pre-effect-blocker",
        "effectId": effect_id,
        "promptDigest": prompt_digest,
        "blocker": blocker,
        "pageUrl": page_url,
        "providerEffectAttempted": False,
        "assistantOutputRead": False,
    }
    value["evidenceDigest"] = digest_obj(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def visible(page, selector: str) -> bool:
    try:
        loc = page.locator(selector)
        return loc.count() > 0 and loc.first.is_visible()
    except Exception:
        return False


def human_blocker(page) -> str | None:
    if challenge_gated(page, CHALLENGE_SELECTOR):
        return "challenge-gated"
    if visible(page, LOGIN_SELECTOR) or visible(page, SIGNUP_SELECTOR):
        return "auth-required"
    return None


def close_old_live_url(page, handoff: dict) -> None:
    live_id = handoff.get("liveURLId")
    if not isinstance(live_id, str) or not live_id:
        return
    try:
        cdp = page.context.new_cdp_session(page)
        cdp.send("Browserless.closeLiveURL", {"liveURLId": live_id})
    except Exception:
        pass


def repark(page, a, blocker: str) -> bool:
    try:
        handoff = mint_handoff(
            page=page,
            effect_id=a.effect_id,
            prompt_digest=a.prompt_digest,
            endpoint_id=a.endpoint_id,
            blocker=blocker,
            handoff_ms=a.human_handoff_ms,
            reconnect_ms=a.reconnect_ms,
            mode="live-url",
        )
        write_private_handoff(a.human_handoff_out, handoff)
        return True
    except Exception as error:
        write_pre_effect(
            a.pre_effect_out,
            effect_id=a.effect_id,
            prompt_digest=a.prompt_digest,
            blocker=f"human-handoff-refresh-unavailable:{type(error).__name__}",
            page_url=page.url,
        )
        return False


def route_provider_blocker(
    page, a, handoff: dict, blocker: str
) -> tuple[str, bool]:
    """Execute provider policy without converting challenges into Browserless handoffs."""
    standing = {
        "challenge-gated": "CHALLENGE_GATED",
        "auth-required": "AUTH_REQUIRED",
    }.get(blocker)
    action = provider_action_for_standing(standing or "CONTEXT_UNAVAILABLE")
    close_old_live_url(page, handoff)
    if action == PROVIDER_ACTION_HUMAN_CONTROL_TRANSFER:
        return ("human-required", True) if repark(page, a, blocker) else ("failed", False)
    if action != PROVIDER_ACTION_HOLD:
        raise RuntimeError(f"unexpected provider action for blocker {blocker!r}: {action}")
    write_pre_effect(
        a.pre_effect_out,
        effect_id=a.effect_id,
        prompt_digest=a.prompt_digest,
        blocker=(
            "automated-browser-challenge-unsupported"
            if blocker == "challenge-gated"
            else f"provider-policy-hold:{blocker}"
        ),
        page_url=page.url,
    )
    return "failed", False


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--handoff", type=Path, required=True)
    p.add_argument("--expected-handoff-digest", required=True)
    p.add_argument("--browserless-token-file", type=Path, required=True)
    p.add_argument("--endpoint-id", required=True)
    p.add_argument("--bootstrap-file", type=Path, required=True)
    p.add_argument("--effect-id", required=True)
    p.add_argument("--prompt-digest", required=True)
    p.add_argument("--handle-out", type=Path, required=True)
    p.add_argument("--pre-effect-out", type=Path, required=True)
    p.add_argument("--human-handoff-out", type=Path, required=True)
    p.add_argument("--wait-stable-seconds", type=int, default=20)
    p.add_argument("--reconnect-ms", type=int, default=60000)
    p.add_argument("--human-handoff-ms", type=int, default=60000)
    p.add_argument("--human-handoff-mode", choices=("live-url",), default="live-url")
    return p


def main() -> int:
    a = parser().parse_args()
    raw = a.bootstrap_file.read_bytes()
    prompt = raw.decode("utf-8")
    if digest_bytes(raw) != a.prompt_digest:
        raise SystemExit("prompt digest mismatch")
    if not prompt.strip() or prompt != prompt.strip():
        raise SystemExit("bootstrap prompt must be non-empty and trimmed")
    handoff = load_verified_handoff(a.handoff, expected_digest=a.expected_handoff_digest)
    if handoff.get("effectId") != a.effect_id or handoff.get("promptDigest") != a.prompt_digest:
        raise SystemExit("human handoff identity mismatch")
    if handoff.get("browserlessEndpointId") != a.endpoint_id:
        raise SystemExit("human handoff endpoint mismatch")
    reconnect = handoff.get("reconnectEndpoint")
    if not isinstance(reconnect, str) or not reconnect:
        write_pre_effect(
            a.pre_effect_out,
            effect_id=a.effect_id,
            prompt_digest=a.prompt_digest,
            blocker="human-handoff-reconnect-missing",
        )
        return PRE_EFFECT_BLOCKED_EXIT

    browser = None
    handed_off = False
    pw_cm = None
    try:
        try:
            pw_cm = sync_playwright()
            pw = pw_cm.__enter__()
            browser = pw.chromium.connect_over_cdp(
                auth(reconnect, a.browserless_token_file), timeout=20_000
            )
        except Exception as error:
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker=f"human-handoff-reconnect:{type(error).__name__}",
            )
            return PRE_EFFECT_BLOCKED_EXIT
        pages = [
            pg
            for ctx in browser.contexts
            for pg in ctx.pages
            if pg.url.startswith("https://chatgpt.com")
        ]
        if len(pages) != 1:
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker="human-handoff-page-cardinality",
            )
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT
        page = pages[0]
        blocker = human_blocker(page)
        if blocker is not None:
            decision, transport_handoff = route_provider_blocker(page, a, handoff, blocker)
            handed_off = transport_handoff
            if decision == "human-required":
                return HUMAN_REQUIRED_EXIT
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT

        composer = page.locator(PROMPT_SELECTOR)
        try:
            composer.wait_for(state="visible", timeout=10000)
        except Exception as error:
            blocker = human_blocker(page)
            if blocker is not None:
                decision, transport_handoff = route_provider_blocker(page, a, handoff, blocker)
                handed_off = transport_handoff
                if decision == "human-required":
                    return HUMAN_REQUIRED_EXIT
                browser.close()
                return PRE_EFFECT_BLOCKED_EXIT
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker=f"human-revalidation-composer-unavailable:{type(error).__name__}",
                page_url=page.url,
            )
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT

        close_old_live_url(page, handoff)
        stop = page.locator(STOP_SELECTOR)
        if stop.count() > 0 and stop.is_visible():
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker="already-generating",
                page_url=page.url,
            )
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT
        if composer.inner_text().strip():
            composer.fill("")
            if composer.inner_text().strip():
                write_pre_effect(
                    a.pre_effect_out,
                    effect_id=a.effect_id,
                    prompt_digest=a.prompt_digest,
                    blocker="composer-not-empty",
                    page_url=page.url,
                )
                browser.close()
                return PRE_EFFECT_BLOCKED_EXIT
        composer.fill(prompt)
        modal = page.locator(PRE_EFFECT_BLOCKER_SELECTOR)
        if modal.count() > 0 and modal.is_visible():
            composer.fill("")
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker="conversation-history-rate-limit-modal",
                page_url=page.url,
            )
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT

        send = page.locator(SEND_SELECTOR)
        expect(send).to_be_visible()
        send.click()
        expect(composer).to_be_empty()
        try:
            page.locator(STOP_SELECTOR).wait_for(state="visible", timeout=10000)
            generation_started = True
        except PlaywrightTimeoutError:
            generation_started = False
        resource = chatgpt_resource_from_page_url(page.url)
        if resource is None and a.wait_stable_seconds > 0:
            try:
                page.wait_for_url(
                    lambda value: chatgpt_resource_from_page_url(str(value)) is not None,
                    timeout=a.wait_stable_seconds * 1000,
                )
            except PlaywrightTimeoutError:
                pass
            resource = chatgpt_resource_from_page_url(page.url)

        reconnect_endpoint = None
        if resource is None and generation_started and a.reconnect_ms > 0:
            try:
                cdp = page.context.new_cdp_session(page)
                row = cdp.send("Browserless.reconnect", {"timeout": a.reconnect_ms})
                candidate = row.get("browserWSEndpoint") if isinstance(row, dict) else None
                if isinstance(candidate, str) and candidate.startswith(("ws://", "wss://")):
                    reconnect_endpoint = candidate
                    handed_off = True
            except Exception:
                reconnect_endpoint = None
        handle = {
            "schemaVersion": 1,
            "kind": "ordivon.browserless-chatgpt-page-binding",
            "effectId": a.effect_id,
            "promptDigest": a.prompt_digest,
            "browserSubstrate": "browserless",
            "browserlessEndpointId": a.endpoint_id,
            "pageUrlAfterSubmit": page.url,
            "providerResource": resource,
            "generationStarted": generation_started,
            "composerCleared": True,
            "reconnectEndpoint": reconnect_endpoint,
            "assistantOutputRead": False,
        }
        handle["bindingDigest"] = digest_obj(handle)
        a.handle_out.parent.mkdir(parents=True, exist_ok=True)
        a.handle_out.write_text(
            json.dumps(handle, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        os.chmod(a.handle_out, 0o600)
        print(json.dumps(handle, sort_keys=True))
        if resource is not None:
            browser.close()
        return 0
    finally:
        if not handed_off:
            try:
                if browser is not None:
                    browser.close()
            except Exception:
                pass
        try:
            if pw_cm is not None:
                pw_cm.__exit__(None, None, None)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
