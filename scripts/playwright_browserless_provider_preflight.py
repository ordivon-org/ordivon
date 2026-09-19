#!/usr/bin/env python3
"""Read-only ChatGPT provider-admission observation through one explicit Browserless endpoint.

This command never fills a composer, clicks UI, submits a prompt, or reads assistant output. It is
an operational admission signal only; Materialization still performs its own pre-effect checks immediately
before the SEND boundary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from chatgpt_provider_gate import challenge_gated

PROMPT_SELECTOR = "#prompt-textarea"
CHALLENGE_SELECTOR = 'iframe[src*="challenges.cloudflare.com"], [id*="challenge"]'
LOGIN_SELECTOR = "text=/^Log in$/i"
SIGNUP_SELECTOR = "text=/^Sign up$/i"
PROVIDER_RATE_LIMIT_SELECTOR = '[data-testid="modal-conversation-history-rate-limit"]'


def auth(public_endpoint: str, token_file: Path) -> str:
    token = token_file.read_text(encoding="utf-8").strip()
    if not token or any(ch.isspace() for ch in token):
        raise ValueError("Browserless token is missing or malformed")
    p = urlsplit(public_endpoint)
    q = parse_qsl(p.query, keep_blank_values=True)
    q.append(("token", token))
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


def safe_page_ref(url: str) -> str:
    p = urlsplit(url or "")
    if p.scheme not in {"http", "https"} or not p.hostname:
        return "unresolved"
    return f"{p.scheme}://{p.hostname}{p.path or '/'}"


def visible(page, selector: str) -> bool:
    try:
        loc = page.locator(selector)
        return loc.count() > 0 and loc.first.is_visible()
    except Exception:
        return False


def result(
    endpoint_id: str, standing: str, *, page_url: str = "", detail: str | None = None
) -> dict:
    row = {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-provider-preflight",
        "endpointId": endpoint_id,
        "standing": standing,
        "pageRef": safe_page_ref(page_url),
        "providerEffectAttempted": False,
        "clicked": False,
        "composerFilled": False,
        "sendAttempted": False,
        "assistantOutputRead": False,
    }
    if detail:
        row["detail"] = detail
    return row


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--browserless-endpoint", required=True)
    p.add_argument("--browserless-token-file", type=Path, required=True)
    p.add_argument("--endpoint-id", required=True)
    p.add_argument("--observe-ms", type=int, default=8000)
    a = p.parse_args()
    if not 0 <= a.observe_ms <= 30000:
        raise SystemExit("observe-ms must be between 0 and 30000")

    browser = None
    try:
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(
                    auth(a.browserless_endpoint, a.browserless_token_file), timeout=20_000
                )
                if len(browser.contexts) != 1:
                    print(
                        json.dumps(
                            result(
                                a.endpoint_id, "CONTEXT_UNAVAILABLE", detail="context-cardinality"
                            ),
                            sort_keys=True,
                        )
                    )
                    return 0
                ctx = browser.contexts[0]
                pages = [
                    pg
                    for pg in ctx.pages
                    if pg.url.startswith("https://chatgpt.com") or pg.url == "about:blank"
                ]
                if not pages:
                    page = ctx.new_page()
                elif len(pages) == 1:
                    page = pages[0]
                else:
                    print(
                        json.dumps(
                            result(a.endpoint_id, "CONTEXT_UNAVAILABLE", detail="page-cardinality"),
                            sort_keys=True,
                        )
                    )
                    return 0
                if page.url == "about:blank" or not page.url.startswith("https://chatgpt.com"):
                    try:
                        page.goto(
                            "https://chatgpt.com/", wait_until="domcontentloaded", timeout=30_000
                        )
                    except Exception as error:
                        print(
                            json.dumps(
                                result(
                                    a.endpoint_id,
                                    "PROVIDER_UNAVAILABLE",
                                    page_url=page.url,
                                    detail=type(error).__name__,
                                ),
                                sort_keys=True,
                            )
                        )
                        return 0

                if challenge_gated(page, CHALLENGE_SELECTOR):
                    print(
                        json.dumps(
                            result(a.endpoint_id, "CHALLENGE_GATED", page_url=page.url),
                            sort_keys=True,
                        )
                    )
                    return 0
                if visible(page, PROVIDER_RATE_LIMIT_SELECTOR):
                    print(
                        json.dumps(
                            result(a.endpoint_id, "PROVIDER_RATE_LIMITED", page_url=page.url),
                            sort_keys=True,
                        )
                    )
                    return 0

                deadline = a.observe_ms
                elapsed = 0
                while elapsed < deadline:
                    if challenge_gated(page, CHALLENGE_SELECTOR):
                        print(
                            json.dumps(
                                result(a.endpoint_id, "CHALLENGE_GATED", page_url=page.url),
                                sort_keys=True,
                            )
                        )
                        return 0
                    if visible(page, PROVIDER_RATE_LIMIT_SELECTOR):
                        print(
                            json.dumps(
                                result(a.endpoint_id, "PROVIDER_RATE_LIMITED", page_url=page.url),
                                sort_keys=True,
                            )
                        )
                        return 0
                    if visible(page, PROMPT_SELECTOR):
                        print(
                            json.dumps(
                                result(a.endpoint_id, "READY", page_url=page.url), sort_keys=True
                            )
                        )
                        return 0
                    if visible(page, LOGIN_SELECTOR) or visible(page, SIGNUP_SELECTOR):
                        print(
                            json.dumps(
                                result(a.endpoint_id, "AUTH_REQUIRED", page_url=page.url),
                                sort_keys=True,
                            )
                        )
                        return 0
                    step = min(500, deadline - elapsed)
                    if step <= 0:
                        break
                    page.wait_for_timeout(step)
                    elapsed += step

                if challenge_gated(page, CHALLENGE_SELECTOR):
                    standing = "CHALLENGE_GATED"
                elif visible(page, PROVIDER_RATE_LIMIT_SELECTOR):
                    standing = "PROVIDER_RATE_LIMITED"
                elif visible(page, PROMPT_SELECTOR):
                    standing = "READY"
                elif visible(page, LOGIN_SELECTOR) or visible(page, SIGNUP_SELECTOR):
                    standing = "AUTH_REQUIRED"
                else:
                    standing = "COMPOSER_UNAVAILABLE"
                print(
                    json.dumps(result(a.endpoint_id, standing, page_url=page.url), sort_keys=True)
                )
                return 0
        except Exception as error:
            print(
                json.dumps(
                    result(a.endpoint_id, "CONNECT_FAILED", detail=type(error).__name__),
                    sort_keys=True,
                )
            )
            return 0
    finally:
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
