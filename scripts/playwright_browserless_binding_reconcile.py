#!/usr/bin/env python3
"""Reconcile one ambiguous Browserless ChatGPT birth using its bounded reconnect endpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import sync_playwright

from chatgpt_provider_resource import canonical_chatgpt_resource, chatgpt_resource_from_page_url


def digest_obj(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def auth(url: str, token_file: Path) -> str:
    token = token_file.read_text(encoding="utf-8").strip()
    if not token or any(ch.isspace() for ch in token):
        raise ValueError("Browserless token is missing or malformed")
    p = urlsplit(url)
    q = parse_qsl(p.query, keep_blank_values=True)
    q.append(("token", token))
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), p.fragment))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--handle", type=Path, required=True)
    p.add_argument("--expected-binding-digest", required=True)
    p.add_argument("--browserless-token-file", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    original = json.loads(a.handle.read_text(encoding="utf-8"))
    actual = original.pop("bindingDigest", None)
    original["bindingDigest"] = actual
    without = dict(original)
    without.pop("bindingDigest", None)
    if actual != a.expected_binding_digest or digest_obj(without) != actual:
        raise SystemExit("binding digest mismatch")
    raw_resource = original.get("providerResource")
    resource = (
        canonical_chatgpt_resource(raw_resource)
        if isinstance(raw_resource, str) and raw_resource
        else None
    )
    if not resource:
        reconnect = original.get("reconnectEndpoint")
        if not isinstance(reconnect, str) or not reconnect:
            raise SystemExit("no reconnect endpoint")
        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(
                auth(reconnect, a.browserless_token_file), timeout=20_000
            )
            try:
                pages = [
                    pg
                    for ctx in browser.contexts
                    for pg in ctx.pages
                    if pg.url.startswith("https://chatgpt.com")
                ]
                if len(pages) == 1:
                    resource = chatgpt_resource_from_page_url(pages[0].url)
            finally:
                browser.close()
    result = {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-chatgpt-reconciliation",
        "effectId": original.get("effectId"),
        "providerResource": resource,
        "browserlessEndpointId": original.get("browserlessEndpointId"),
        "assistantOutputRead": False,
    }
    result["bindingDigest"] = digest_obj(result)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(a.out, 0o600)
    print(json.dumps(result, sort_keys=True))
    return 0 if resource else 3


if __name__ == "__main__":
    raise SystemExit(main())
