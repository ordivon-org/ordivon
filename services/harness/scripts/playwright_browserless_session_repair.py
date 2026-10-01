#!/usr/bin/env python3
"""Authorized private session-state replay into an isolated Browserless context.

The raw cookie bundle is an input-only credential carrier.  This process never serializes cookie
names or values to stdout/stderr, Host, receipts, prompts, or provider effects.  It creates one
isolated BrowserContext, replays only ChatGPT/OpenAI cookies, performs a no-SEND admission probe,
and destroys the context before returning a sanitized receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import time
from pathlib import Path
from typing import Any

from chatgpt_provider_gate import challenge_gated
from playwright_browserless_provider_preflight import (
    CHALLENGE_SELECTOR,
    LOGIN_SELECTOR,
    PROMPT_SELECTOR,
    PROVIDER_RATE_LIMIT_SELECTOR,
    SIGNUP_SELECTOR,
    auth,
    safe_page_ref,
    visible,
)

_ALLOWED_SUFFIXES = ("chatgpt.com", "openai.com")
_MAX_BUNDLE_BYTES = 2 * 1024 * 1024


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _private_regular_file(path: Path) -> None:
    if not path.is_absolute() or path.is_symlink():
        raise ValueError("cookie bundle must be one absolute non-symlink file")
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_BUNDLE_BYTES:
        raise ValueError("cookie bundle file shape is invalid")
    # POSIX authority: do not consume a credential carrier readable/writable by group/other.
    if os.name == "posix" and stat.S_IMODE(info.st_mode) & 0o077:
        raise ValueError("cookie bundle permissions are too broad")


def _domain_allowed(domain: str) -> bool:
    value = domain.strip().lower().lstrip(".")
    return any(value == suffix or value.endswith("." + suffix) for suffix in _ALLOWED_SUFFIXES)


def load_normalized_bundle(path: Path, expected_digest: str, *, now_s: float | None = None) -> tuple[list[dict[str, Any]], dict[str, int]]:
    _private_regular_file(path)
    observed = sha256_file(path)
    if observed != expected_digest:
        raise ValueError("cookie bundle digest mismatch")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = value if isinstance(value, list) else value.get("cookies") if isinstance(value, dict) else None
    if not isinstance(rows, list):
        raise ValueError("cookie bundle must contain one cookie list")
    now = time.time() if now_s is None else now_s
    normalized: list[dict[str, Any]] = []
    expired = 0
    outside_scope = 0
    invalid = 0
    for raw in rows:
        if not isinstance(raw, dict):
            invalid += 1
            continue
        name = raw.get("name")
        secret = raw.get("value")
        domain = raw.get("domain")
        path_value = raw.get("path", "/")
        if not all(isinstance(v, str) and v for v in (name, secret, domain, path_value)):
            invalid += 1
            continue
        if not _domain_allowed(domain):
            outside_scope += 1
            continue
        expires = raw.get("expires", raw.get("expirationDate"))
        if isinstance(expires, (int, float)) and not isinstance(expires, bool) and expires > 0:
            if float(expires) <= now:
                expired += 1
                continue
        row: dict[str, Any] = {
            "name": name,
            "value": secret,
            "domain": domain,
            "path": path_value,
            "secure": bool(raw.get("secure", False)),
            "httpOnly": bool(raw.get("httpOnly", raw.get("httponly", False))),
        }
        if isinstance(expires, (int, float)) and not isinstance(expires, bool) and expires > 0:
            row["expires"] = float(expires)
        same_site = raw.get("sameSite")
        if isinstance(same_site, str):
            canonical = {"strict": "Strict", "lax": "Lax", "none": "None"}.get(same_site.lower())
            if canonical:
                row["sameSite"] = canonical
        normalized.append(row)
    return normalized, {
        "inputCount": len(rows),
        "eligibleCount": len(normalized),
        "expiredDropped": expired,
        "outsideScopeDropped": outside_scope,
        "invalidDropped": invalid,
    }


def sanitized_receipt(endpoint_id: str, standing: str, source_digest: str, stats: dict[str, int], *, mode: str = "probe", page_url: str = "", detail_code: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-session-continuity-probe",
        "endpointId": endpoint_id,
        "standing": standing,
        "mode": mode,
        "sourceBundleDigest": source_digest,
        "pageRef": safe_page_ref(page_url),
        "cookieInputCount": stats["inputCount"],
        "cookieEligibleCount": stats["eligibleCount"],
        "expiredDropped": stats["expiredDropped"],
        "outsideScopeDropped": stats["outsideScopeDropped"],
        "invalidDropped": stats["invalidDropped"],
        "providerEffectAttempted": False,
        "clicked": False,
        "composerFilled": False,
        "sendAttempted": False,
        "assistantOutputRead": False,
        "rawCredentialProjected": False,
    }
    if detail_code:
        row["detailCode"] = detail_code
    return row


def classify(page, observe_ms: int) -> str:
    if challenge_gated(page, CHALLENGE_SELECTOR):
        return "CHALLENGE_GATED"
    if visible(page, PROVIDER_RATE_LIMIT_SELECTOR):
        return "PROVIDER_RATE_LIMITED"
    elapsed = 0
    while elapsed < observe_ms:
        if challenge_gated(page, CHALLENGE_SELECTOR):
            return "CHALLENGE_GATED"
        if visible(page, PROVIDER_RATE_LIMIT_SELECTOR):
            return "PROVIDER_RATE_LIMITED"
        if visible(page, PROMPT_SELECTOR):
            return "READY"
        if visible(page, LOGIN_SELECTOR) or visible(page, SIGNUP_SELECTOR):
            return "AUTH_REQUIRED"
        step = min(500, observe_ms - elapsed)
        if step <= 0:
            break
        page.wait_for_timeout(step)
        elapsed += step
    if challenge_gated(page, CHALLENGE_SELECTOR):
        return "CHALLENGE_GATED"
    if visible(page, PROVIDER_RATE_LIMIT_SELECTOR):
        return "PROVIDER_RATE_LIMITED"
    if visible(page, PROMPT_SELECTOR):
        return "READY"
    if visible(page, LOGIN_SELECTOR) or visible(page, SIGNUP_SELECTOR):
        return "AUTH_REQUIRED"
    return "COMPOSER_UNAVAILABLE"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--browserless-endpoint", required=True)
    p.add_argument("--browserless-token-file", type=Path, required=True)
    p.add_argument("--endpoint-id", required=True)
    p.add_argument("--cookie-bundle", type=Path, required=True)
    p.add_argument("--expected-cookie-digest", required=True)
    p.add_argument("--observe-ms", type=int, default=8000)
    p.add_argument("--mode", choices=("probe", "apply"), default="probe")
    a = p.parse_args()
    if not 0 <= a.observe_ms <= 30000:
        raise SystemExit("observe-ms must be between 0 and 30000")

    empty = {"inputCount": 0, "eligibleCount": 0, "expiredDropped": 0, "outsideScopeDropped": 0, "invalidDropped": 0}
    try:
        cookies, stats = load_normalized_bundle(a.cookie_bundle, a.expected_cookie_digest)
    except Exception as error:
        print(json.dumps(sanitized_receipt(a.endpoint_id, "SOURCE_REJECTED", a.expected_cookie_digest, empty, mode=a.mode, detail_code=type(error).__name__), sort_keys=True))
        return 0
    if not cookies:
        print(json.dumps(sanitized_receipt(a.endpoint_id, "NO_ELIGIBLE_SESSION_STATE", a.expected_cookie_digest, stats, mode=a.mode), sort_keys=True))
        return 0

    browser = None
    context = None
    close_context = False
    try:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(auth(a.browserless_endpoint, a.browserless_token_file), timeout=20_000)
                if a.mode == "probe":
                    context = browser.new_context()
                    close_context = True
                else:
                    if len(browser.contexts) != 1:
                        print(json.dumps(sanitized_receipt(a.endpoint_id, "CONTEXT_UNAVAILABLE", a.expected_cookie_digest, stats, mode=a.mode, detail_code="context-cardinality"), sort_keys=True))
                        return 0
                    context = browser.contexts[0]
                try:
                    context.add_cookies(cookies)
                except Exception as error:
                    print(json.dumps(sanitized_receipt(a.endpoint_id, "SESSION_STATE_REJECTED", a.expected_cookie_digest, stats, mode=a.mode, detail_code=type(error).__name__), sort_keys=True))
                    return 0
                page = context.new_page()
                try:
                    page.goto("https://chatgpt.com/", wait_until="domcontentloaded", timeout=30_000)
                except Exception as error:
                    print(json.dumps(sanitized_receipt(a.endpoint_id, "PROVIDER_UNAVAILABLE", a.expected_cookie_digest, stats, mode=a.mode, page_url=page.url, detail_code=type(error).__name__), sort_keys=True))
                    return 0
                standing = classify(page, a.observe_ms)
                print(json.dumps(sanitized_receipt(a.endpoint_id, standing, a.expected_cookie_digest, stats, mode=a.mode, page_url=page.url), sort_keys=True))
                return 0
        except Exception as error:
            print(json.dumps(sanitized_receipt(a.endpoint_id, "CONNECT_FAILED", a.expected_cookie_digest, stats, mode=a.mode, detail_code=type(error).__name__), sort_keys=True))
            return 0
    finally:
        try:
            if context is not None and close_context:
                context.close()
        except Exception:
            pass
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
