#!/usr/bin/env python3
"""Narrow observable provider-admission gate classification for ChatGPT carriers.

This module only recognizes already-present challenge evidence. It does not solve, click, evade,
or retry a provider challenge.
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit


def cloudflare_challenge_metadata(url: str, title: str) -> bool:
    normalized_title = (title or "").strip().casefold()
    if normalized_title.startswith("just a moment"):
        return True
    try:
        parsed = urlsplit(url or "")
        if "/cdn-cgi/challenge-platform" in parsed.path:
            return True
        if any(
            key.startswith("__cf_chl_")
            for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
        ):
            return True
    except Exception:
        return False
    return False


def challenge_gated(page, selector: str) -> bool:
    try:
        if cloudflare_challenge_metadata(page.url, page.title()):
            return True
    except Exception:
        pass
    try:
        return page.locator(selector).count() > 0
    except Exception:
        return False
