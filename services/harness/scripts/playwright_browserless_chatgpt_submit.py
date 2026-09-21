#!/usr/bin/env python3
"""Submit one ChatGPT materialization through Browserless without persisting Browserless credentials.

Provider challenges/authentication expiry are never solved automatically. On self-hosted Browserless,
the exact headful running session is exposed through a bounded local noVNC transport while this
process keeps the automation connection attached; it resumes automatically only after the human
returns the page to a normal READY composer. Hosted/enterprise deployments may alternatively use
Browserless.liveURL/reconnect. No prompt is filled before provider admission succeeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

from browserless_human_handoff import (
    authenticated_connection_endpoint,
    mint_handoff,
    tracking_id,
    update_handoff_state,
    write_private_handoff,
)
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
NEW_CHAT_URL = "https://chatgpt.com/"
PRE_EFFECT_BLOCKED_EXIT = 42
HUMAN_REQUIRED_EXIT = 43


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def digest_obj(value: object) -> str:
    return digest_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--browserless-endpoint", required=True)
    p.add_argument("--browserless-token-file", type=Path, required=True)
    p.add_argument("--endpoint-id", required=True)
    p.add_argument("--bootstrap-file", type=Path, required=True)
    p.add_argument("--effect-id", required=True)
    p.add_argument("--prompt-digest", required=True)
    p.add_argument("--handle-out", type=Path, required=True)
    p.add_argument("--pre-effect-out", type=Path, required=True)
    p.add_argument("--human-handoff-out", type=Path, required=True)
    p.add_argument("--wait-stable-seconds", type=int, default=150)
    p.add_argument("--reconnect-ms", type=int, default=60000)
    p.add_argument("--human-handoff-ms", type=int, default=60000)
    p.add_argument(
        "--human-handoff-mode",
        choices=("self-hosted-vnc", "live-url"),
        default="self-hosted-vnc",
    )
    return p


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


def stabilize_empty_composer(
    page, composer, *, timeout_ms: int = 3000, quiet_ms: int = 500
) -> bool:
    """Clear persisted draft state and require a stable empty window before SEND.

    ChatGPT can asynchronously rehydrate the root-page ProseMirror draft from a persistent profile.
    One successful ``fill("")`` is therefore not proof that the fresh-materialization surface is clean. This
    helper performs only local pre-SEND edits and waits until the composer remains text-empty for a
    bounded quiet interval. It never fills the materialization prompt or activates SEND.
    """
    deadline = time.monotonic() + max(timeout_ms, quiet_ms) / 1000.0
    quiet_since: float | None = None
    while time.monotonic() < deadline:
        try:
            if composer.inner_text().strip():
                composer.fill("")
                quiet_since = None
            else:
                now = time.monotonic()
                if quiet_since is None:
                    quiet_since = now
                elif (now - quiet_since) * 1000 >= quiet_ms:
                    return True
            page.wait_for_timeout(100)
        except Exception:
            return False
    return False


def wait_for_canonical_after_send(
    page, *, generation_started: bool, hard_timeout_seconds: int, settle_seconds: int = 8
) -> str | None:
    """Observe the provider route until it becomes canonical or the SEND result is boundedly ambiguous.

    A ChatGPT materialization may stay on a client-generated ``/c/WEB:...`` route while generation is
    active. Do not turn that delay into a resend. Keep the original Browserless session attached,
    return immediately on a canonical route, and after generation stops allow only a short settle
    window. The hard ceiling is a carrier-capacity bound, not evidence that SEND failed.
    """
    resource = chatgpt_resource_from_page_url(page.url)
    if resource is not None or hard_timeout_seconds <= 0:
        return resource
    started = time.monotonic()
    deadline = started + hard_timeout_seconds
    saw_generation = bool(generation_started)
    completion_since: float | None = None
    no_generation_deadline = min(deadline, started + settle_seconds)
    while time.monotonic() < deadline:
        resource = chatgpt_resource_from_page_url(page.url)
        if resource is not None:
            return resource
        generating = visible(page, STOP_SELECTOR)
        now = time.monotonic()
        if generating:
            saw_generation = True
            completion_since = None
        elif saw_generation:
            if completion_since is None:
                completion_since = now
            elif now - completion_since >= settle_seconds:
                return None
        elif now >= no_generation_deadline:
            return None
        page.wait_for_timeout(250)
    return chatgpt_resource_from_page_url(page.url)


def human_blocker(page) -> str | None:
    if challenge_gated(page, CHALLENGE_SELECTOR):
        return "challenge-gated"
    if visible(page, LOGIN_SELECTOR) or visible(page, SIGNUP_SELECTOR):
        return "auth-required"
    return None


def park_for_human(page, a, blocker: str) -> dict | None:
    try:
        handoff = mint_handoff(
            page=page,
            effect_id=a.effect_id,
            prompt_digest=a.prompt_digest,
            endpoint_id=a.endpoint_id,
            blocker=blocker,
            handoff_ms=a.human_handoff_ms,
            reconnect_ms=a.reconnect_ms,
            mode=a.human_handoff_mode,
            tracking=tracking_id(a.effect_id),
        )
        write_private_handoff(a.human_handoff_out, handoff)
        return handoff
    except Exception as error:
        write_pre_effect(
            a.pre_effect_out,
            effect_id=a.effect_id,
            prompt_digest=a.prompt_digest,
            blocker=f"human-handoff-unavailable:{type(error).__name__}",
            page_url=page.url,
        )
        return None


def wait_for_human_provider_admission(page, a, handoff: dict) -> bool:
    """Observe only. The operator interacts through the exact Browserless X display."""
    from browserless_human_interaction import close_transport

    deadline = time.monotonic() + (a.human_handoff_ms / 1000.0)
    state = "handoff-window-expired"
    ready = False
    try:
        while time.monotonic() < deadline:
            if human_blocker(page) is None and visible(page, PROMPT_SELECTOR):
                state = "human-verified-ready"
                ready = True
                break
            page.wait_for_timeout(500)
    except Exception:
        state = "handoff-transport-lost"
    try:
        update_handoff_state(a.human_handoff_out, active=False, state=state)
    except Exception:
        pass
    if handoff.get("mode") == "self-hosted-vnc":
        try:
            close_transport(int(handoff["transportInstance"]))
        except Exception:
            pass
    return ready


def handle_human_gate(page, a, blocker: str) -> tuple[str, bool]:
    """Return (decision, transport_handed_off). decision is ready/human-required/failed."""
    handoff = park_for_human(page, a, blocker)
    if handoff is None:
        return "failed", False
    if handoff.get("mode") == "self-hosted-vnc":
        # Playwright stays attached while the human sees and interacts with that exact X display.
        return (
            "ready" if wait_for_human_provider_admission(page, a, handoff) else "human-required"
        ), False
    # live-url mode preserves the remote session through Browserless.reconnect after this process
    # disconnects; a separate human-resume operation revalidates that exact session.
    return "human-required", True


def route_provider_blocker(page, a, blocker: str) -> tuple[str, bool]:
    """Execute the single provider-boundary action for one observed local blocker."""
    standing = {
        "challenge-gated": "CHALLENGE_GATED",
        "auth-required": "AUTH_REQUIRED",
    }.get(blocker)
    action = provider_action_for_standing(standing or "CONTEXT_UNAVAILABLE")
    if action == PROVIDER_ACTION_HUMAN_CONTROL_TRANSFER:
        return handle_human_gate(page, a, blocker)
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


def main() -> int:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, expect, sync_playwright

    a = parser().parse_args()
    raw = a.bootstrap_file.read_bytes()
    prompt = raw.decode("utf-8")
    if digest_bytes(raw) != a.prompt_digest:
        raise SystemExit("prompt digest mismatch")
    if not prompt.strip() or prompt != prompt.strip():
        raise SystemExit("bootstrap prompt must be non-empty and trimmed")

    browser = None
    handed_off = False
    pw_cm = None
    try:
        try:
            endpoint = authenticated_connection_endpoint(
                a.browserless_endpoint,
                a.browserless_token_file,
                tracking=tracking_id(a.effect_id),
            )
            pw_cm = sync_playwright()
            pw = pw_cm.__enter__()
            browser = pw.chromium.connect_over_cdp(endpoint, timeout=20_000)
        except Exception as error:
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker=f"browserless-connect:{type(error).__name__}",
            )
            return PRE_EFFECT_BLOCKED_EXIT

        contexts = browser.contexts
        if len(contexts) != 1:
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker="browserless-context-cardinality",
            )
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT
        ctx = contexts[0]
        pages = [
            p
            for p in ctx.pages
            if p.url.startswith("https://chatgpt.com") or p.url == "about:blank"
        ]
        if not pages:
            page = ctx.new_page()
        elif len(pages) == 1:
            page = pages[0]
        else:
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker="browserless-page-cardinality",
            )
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT
        # Materialization differs from continuation/reconciliation: always establish a fresh provider
        # surface instead of inheriting whichever page the persistent profile last displayed.
        # Navigation is pre-SEND and remains safely retryable under the same effect identity.
        try:
            page.goto(NEW_CHAT_URL, wait_until="domcontentloaded", timeout=30_000)
        except Exception as error:
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker=f"provider-navigation:{type(error).__name__}",
                page_url=page.url,
            )
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT

        blocker = human_blocker(page)
        if blocker is not None:
            decision, transport_handoff = route_provider_blocker(page, a, blocker)
            handed_off = transport_handoff
            if decision == "human-required":
                return HUMAN_REQUIRED_EXIT
            if decision == "failed":
                browser.close()
                return PRE_EFFECT_BLOCKED_EXIT

        composer = page.locator(PROMPT_SELECTOR)
        try:
            composer.wait_for(state="visible", timeout=20_000)
        except Exception as error:
            blocker = human_blocker(page)
            if blocker is not None:
                decision, transport_handoff = route_provider_blocker(page, a, blocker)
                handed_off = transport_handoff
                if decision == "human-required":
                    return HUMAN_REQUIRED_EXIT
                if decision == "ready":
                    composer = page.locator(PROMPT_SELECTOR)
                    composer.wait_for(state="visible", timeout=10_000)
                else:
                    browser.close()
                    return PRE_EFFECT_BLOCKED_EXIT
            else:
                write_pre_effect(
                    a.pre_effect_out,
                    effect_id=a.effect_id,
                    prompt_digest=a.prompt_digest,
                    blocker=f"composer-unavailable:{type(error).__name__}",
                    page_url=page.url,
                )
                browser.close()
                return PRE_EFFECT_BLOCKED_EXIT
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
        if not stabilize_empty_composer(page, composer):
            write_pre_effect(
                a.pre_effect_out,
                effect_id=a.effect_id,
                prompt_digest=a.prompt_digest,
                blocker="composer-not-empty",
                page_url=page.url,
            )
            browser.close()
            return PRE_EFFECT_BLOCKED_EXIT
        # SEND boundary starts here. No provider prompt content was entered during human verification.
        composer.fill(prompt)
        blocker_modal = page.locator(PRE_EFFECT_BLOCKER_SELECTOR)
        if blocker_modal.count() > 0 and blocker_modal.is_visible():
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
            page.locator(STOP_SELECTOR).wait_for(state="visible", timeout=10_000)
            generation_started = True
        except PlaywrightTimeoutError:
            generation_started = False
        resource = wait_for_canonical_after_send(
            page,
            generation_started=generation_started,
            hard_timeout_seconds=a.wait_stable_seconds,
        )

        reconnect_endpoint = None
        if (
            resource is None
            and generation_started
            and a.reconnect_ms > 0
            and a.human_handoff_mode == "live-url"
        ):
            try:
                cdp = ctx.new_cdp_session(page)
                reconnect = cdp.send("Browserless.reconnect", {"timeout": a.reconnect_ms})
                candidate = (
                    reconnect.get("browserWSEndpoint")
                    if isinstance(reconnect, dict) and not reconnect.get("error")
                    else None
                )
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
