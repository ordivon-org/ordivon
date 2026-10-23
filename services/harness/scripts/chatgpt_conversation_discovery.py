#!/usr/bin/env python3
"""Read-only exact-marker discovery for existing ChatGPT conversations.

The provider observer only reads currently rendered ChatGPT conversation links through
a caller-owned loopback CDP session. Visible title text is hashed in the page; raw title
or marker text is never returned or persisted by this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

try:
    from chatgpt_provider_resource import chatgpt_resource_from_page_url
except ModuleNotFoundError:
    from scripts.chatgpt_provider_resource import chatgpt_resource_from_page_url

_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def _canonical_digest(value: object) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _text_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_marker_digest(value: str) -> str:
    if not isinstance(value, str) or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError("marker digest must be canonical sha256:<lowercase-hex>")
    return value


def _validate_session(session: dict[str, Any]) -> tuple[str, str]:
    if not isinstance(session, dict):
        raise ValueError("session coordinate must be an object")
    session_id = session.get("sessionId")
    endpoint = session.get("cdpEndpoint")
    if (
        not isinstance(session_id, str)
        or not session_id
        or session_id != session_id.strip()
    ):
        raise ValueError("sessionId must be non-empty and trimmed")
    if not isinstance(endpoint, str) or not endpoint or endpoint != endpoint.strip():
        raise ValueError("loopback cdpEndpoint must be non-empty and trimmed")
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme not in {"http", "https", "ws", "wss"}
        or parsed.hostname not in _LOOPBACK_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port is None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("session discovery requires one explicit loopback CDP endpoint")
    return session_id, endpoint


_VISIBLE_CONVERSATION_SCRIPT = r"""
async () => {
  const digest = async (text) => {
    const bytes = new TextEncoder().encode(text);
    const hash = await crypto.subtle.digest('SHA-256', bytes);
    return 'sha256:' + Array.from(new Uint8Array(hash))
      .map((b) => b.toString(16).padStart(2, '0')).join('');
  };
  const rows = [];
  const anchors = Array.from(document.querySelectorAll('a[href*="/c/"]'));
  for (const anchor of anchors) {
    const title = (anchor.textContent || '').trim();
    if (!title || !anchor.href) continue;
    rows.push({pageUrl: anchor.href, markerDigest: await digest(title)});
  }
  return rows;
}
"""


def observe_visible_chatgpt_conversations(
    session: dict[str, Any], marker_digest: str
) -> list[dict[str, str]]:
    """Read visible conversation-link title digests from an attached loopback CDP session."""
    _validate_marker_digest(marker_digest)
    _session_id, endpoint = _validate_session(session)
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as error:
        raise RuntimeError("Playwright is required for live conversation discovery") from error

    rows: list[dict[str, str]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(endpoint, timeout=20_000)
        for context in browser.contexts:
            for page in context.pages:
                parsed = urlsplit(page.url)
                if parsed.scheme != "https" or parsed.hostname != "chatgpt.com":
                    continue
                observed = page.evaluate(_VISIBLE_CONVERSATION_SCRIPT)
                if not isinstance(observed, list):
                    continue
                for row in observed:
                    if not isinstance(row, dict):
                        continue
                    page_url = row.get("pageUrl")
                    title_digest = row.get("markerDigest")
                    if isinstance(page_url, str) and isinstance(title_digest, str):
                        rows.append(
                            {"pageUrl": page_url, "markerDigest": title_digest}
                        )
        # Do not call browser.close(): this module attaches to a caller-owned durable browser.
    return rows


ConversationObserver = Callable[[dict[str, Any], str], list[dict[str, str]]]


def discover_exact_marker(
    session: dict[str, Any],
    marker_digest: str,
    *,
    observer: ConversationObserver = observe_visible_chatgpt_conversations,
) -> dict[str, Any]:
    """Return an exact zero/one/many binding projection for one hashed marker."""
    marker_digest = _validate_marker_digest(marker_digest)
    session_id, _endpoint = _validate_session(session)
    observed = observer(session, marker_digest)
    if not isinstance(observed, list):
        raise ValueError("conversation observer must return a list")

    normalized_rows: set[tuple[str, str]] = set()
    matched_resources: set[str] = set()
    for row in observed:
        if not isinstance(row, dict):
            continue
        row_digest = row.get("markerDigest")
        page_url = row.get("pageUrl")
        if not isinstance(row_digest, str) or _DIGEST_RE.fullmatch(row_digest) is None:
            continue
        if not isinstance(page_url, str):
            continue
        resource = chatgpt_resource_from_page_url(page_url)
        if resource is None:
            continue
        normalized_rows.add((resource, row_digest))
        if row_digest == marker_digest:
            matched_resources.add(resource)

    matches = sorted(matched_resources)
    if len(matches) == 1:
        standing = "EXACT_MATCH"
    elif matches:
        standing = "AMBIGUOUS_MATCH"
    else:
        standing = "NO_MATCH"

    evidence = {
        "schemaVersion": 1,
        "kind": "ordivon.chatgpt-conversation-discovery-evidence",
        "sessionIdentityDigest": _text_digest(session_id),
        "markerDigest": marker_digest,
        "standing": standing,
        "observations": [
            {"providerResource": resource, "markerDigest": row_digest}
            for resource, row_digest in sorted(normalized_rows)
        ],
        "matchedProviderResources": matches,
    }
    result: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.chatgpt-conversation-discovery",
        "standing": standing,
        "matchCount": len(matches),
        "markerDigest": marker_digest,
        "evidenceDigest": _canonical_digest(evidence),
        "providerEffectAttempted": False,
        "sendAttempted": False,
        "sideEffectsAttempted": False,
    }
    if len(matches) == 1:
        result["providerResource"] = matches[0]
    return result
