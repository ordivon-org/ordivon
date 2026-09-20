#!/usr/bin/env python3
"""Private human-verification handoff helpers for Browserless carriers.

The preferred open-source/self-hosted path exposes the exact headful Browserless display through
Xvfb + x11vnc + noVNC/websockify while the automation connection stays attached. Enterprise/hosted
deployments may instead use Browserless.liveURL + reconnect. Neither path solves, clicks, evades,
or retries a provider challenge automatically.

Handoff records remain private local state (0600). Only an authorized operator may receive the
bounded loopback/live URL. Never publish hosted bearer-like URLs to Board/logs.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
from pathlib import Path


def digest_obj(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def tracking_id(effect_id: str) -> str:
    return "h-" + hashlib.sha256(effect_id.encode()).hexdigest()[:24]


def _token(path: Path) -> str:
    value = Path(path).read_text(encoding="utf-8").strip()
    if not value or any(ch.isspace() for ch in value):
        raise ValueError("Browserless token is missing or malformed")
    return value


def authenticated_connection_endpoint(
    public_endpoint: str, token_file: Path, *, tracking: str | None = None
) -> str:
    token = _token(token_file)
    p = urllib.parse.urlsplit(public_endpoint)
    query = urllib.parse.parse_qsl(p.query, keep_blank_values=True)
    query.append(("token", token))
    if tracking:
        query.append(("trackingId", tracking))
    return urllib.parse.urlunsplit(
        (p.scheme, p.netloc, p.path, urllib.parse.urlencode(query), p.fragment)
    )


def _self_hosted_vnc_handoff(
    *,
    effect_id: str,
    prompt_digest: str,
    endpoint_id: str,
    blocker: str,
    handoff_ms: int,
    tracking: str,
) -> dict:
    from browserless_human_interaction import open_transport

    prefix = "chatgpt-carrier-"
    if not endpoint_id.startswith(prefix):
        raise ValueError("self-hosted VNC handoff requires canonical Browserless carrier id")
    try:
        instance = int(endpoint_id[len(prefix) :])
    except ValueError as error:
        raise ValueError("self-hosted VNC handoff carrier id is malformed") from error
    transport = open_transport(instance)
    operator_url = transport.get("operatorURL")
    if (
        transport.get("standing") != "READY"
        or not isinstance(operator_url, str)
        or not operator_url
    ):
        raise RuntimeError("self-hosted human interaction transport is not READY")
    now_ms = int(time.time() * 1000)
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-human-verification-handoff",
        "mode": "self-hosted-vnc",
        "effectId": effect_id,
        "promptDigest": prompt_digest,
        "browserlessEndpointId": endpoint_id,
        "blocker": blocker,
        "trackingId": tracking,
        "transportInstance": instance,
        "operatorURL": operator_url,
        "createdAtMs": now_ms,
        "sessionActiveUntilMs": now_ms + int(handoff_ms),
        "sessionActive": True,
        "providerEffectAttempted": False,
        "assistantOutputRead": False,
    }
    value["handoffDigest"] = digest_obj(value)
    return value


def _live_url_handoff(
    *,
    page,
    effect_id: str,
    prompt_digest: str,
    endpoint_id: str,
    blocker: str,
    handoff_ms: int,
    reconnect_ms: int,
) -> dict:
    cdp = page.context.new_cdp_session(page)
    page_id = None
    try:
        row = cdp.send("Browserless.pageId")
        if isinstance(row, dict):
            page_id = row.get("pageId")
    except Exception:
        page_id = None
    live = cdp.send(
        "Browserless.liveURL",
        {
            "timeout": int(handoff_ms),
            "interactable": True,
            "showBrowserInterface": True,
            "resizable": True,
            "quality": 70,
        },
    )
    if (
        not isinstance(live, dict)
        or live.get("error")
        or not isinstance(live.get("liveURL"), str)
        or not live.get("liveURL")
    ):
        raise RuntimeError(
            f"Browserless.liveURL unavailable: {live.get('error') if isinstance(live, dict) else 'invalid-result'}"
        )
    reconnect = cdp.send("Browserless.reconnect", {"timeout": int(reconnect_ms)})
    if (
        not isinstance(reconnect, dict)
        or reconnect.get("error")
        or not isinstance(reconnect.get("browserWSEndpoint"), str)
        or not reconnect.get("browserWSEndpoint")
    ):
        try:
            live_id = live.get("liveURLId")
            if isinstance(live_id, str) and live_id:
                cdp.send("Browserless.closeLiveURL", {"liveURLId": live_id})
        except Exception:
            pass
        raise RuntimeError(
            f"Browserless.reconnect unavailable: {reconnect.get('error') if isinstance(reconnect, dict) else 'invalid-result'}"
        )
    now_ms = int(time.time() * 1000)
    value = {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-human-verification-handoff",
        "mode": "live-url",
        "effectId": effect_id,
        "promptDigest": prompt_digest,
        "browserlessEndpointId": endpoint_id,
        "blocker": blocker,
        "pageId": page_id,
        "liveURLId": live.get("liveURLId"),
        "liveURL": live["liveURL"],
        "reconnectEndpoint": reconnect["browserWSEndpoint"],
        "createdAtMs": now_ms,
        "sessionActiveUntilMs": now_ms + min(int(handoff_ms), int(reconnect_ms)),
        "sessionActive": True,
        "providerEffectAttempted": False,
        "assistantOutputRead": False,
    }
    value["handoffDigest"] = digest_obj(value)
    return value


def mint_handoff(
    *,
    page,
    effect_id: str,
    prompt_digest: str,
    endpoint_id: str,
    blocker: str,
    handoff_ms: int,
    reconnect_ms: int,
    mode: str = "self-hosted-vnc",
    tracking: str | None = None,
) -> dict:
    if handoff_ms <= 0 or reconnect_ms <= 0:
        raise ValueError("handoff/reconnect timeout must be positive")
    if mode == "live-url":
        return _live_url_handoff(
            page=page,
            effect_id=effect_id,
            prompt_digest=prompt_digest,
            endpoint_id=endpoint_id,
            blocker=blocker,
            handoff_ms=handoff_ms,
            reconnect_ms=reconnect_ms,
        )
    if mode != "self-hosted-vnc":
        raise ValueError(f"unsupported human handoff mode {mode}")
    return _self_hosted_vnc_handoff(
        effect_id=effect_id,
        prompt_digest=prompt_digest,
        endpoint_id=endpoint_id,
        blocker=blocker,
        handoff_ms=handoff_ms,
        tracking=tracking or tracking_id(effect_id),
    )


def write_private_handoff(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    os.chmod(path, 0o600)


def load_verified_handoff(path: Path, *, expected_digest: str | None = None) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("human handoff must be an object")
    actual = value.get("handoffDigest")
    without = dict(value)
    without.pop("handoffDigest", None)
    if not isinstance(actual, str) or digest_obj(without) != actual:
        raise ValueError("human handoff digest mismatch")
    if expected_digest is not None and actual != expected_digest:
        raise ValueError("human handoff changed from expected digest")
    if (
        value.get("providerEffectAttempted") is not False
        or value.get("assistantOutputRead") is not False
    ):
        raise ValueError("human handoff does not prove pre-effect state")
    return value


def update_handoff_state(path: Path, *, active: bool, state: str) -> dict:
    value = load_verified_handoff(path)
    value.pop("handoffDigest", None)
    value["sessionActive"] = bool(active)
    value["sessionState"] = state
    value["stateUpdatedAtMs"] = int(time.time() * 1000)
    value["handoffDigest"] = digest_obj(value)
    write_private_handoff(path, value)
    return value
