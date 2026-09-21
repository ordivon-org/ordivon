#!/usr/bin/env python3
"""Durable pre-SEND human-auth handoff for Chrome for Testing materialization."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import rfc8785

try:
    from conversation_relay_carrier import (
        CarrierMaterializationRequest,
        MaterializationStanding,
    )
    from sqlite_conversation_materializer import TargetMaterializationObservation
    from cft_human_session import DurableSessionAuthority
except ModuleNotFoundError:
    from scripts.conversation_relay_carrier import (
        CarrierMaterializationRequest,
        MaterializationStanding,
    )
    from scripts.sqlite_conversation_materializer import TargetMaterializationObservation
    from scripts.cft_human_session import DurableSessionAuthority

CHATGPT_ROOT = "https://chatgpt.com/"


def _digest_obj(value: object) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _private_json(path: Path, value: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise RuntimeError("human handoff parent must not be a symlink")
    raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(path, 0o600)


def create_handoff(
    path: Path,
    *,
    effect_id: str,
    request_digest: str,
    session: dict[str, Any],
    blocker: str,
) -> dict[str, Any]:
    if not isinstance(effect_id, str) or not effect_id or effect_id != effect_id.strip():
        raise ValueError("effectId must be non-empty and trimmed")
    if not isinstance(request_digest, str) or not request_digest.startswith("sha256:") or len(request_digest) != 71:
        raise ValueError("requestDigest must be one SHA-256 digest")
    if blocker != "auth-required":
        raise ValueError("durable human handoff currently supports auth-required only")
    if session.get("standing") != "READY" or session.get("sessionActive") is not True:
        raise ValueError("durable human session must be READY")
    session_id = session.get("sessionId")
    operator_url = session.get("operatorURL")
    browser_digest = session.get("browserExecutableDigest")
    if not isinstance(session_id, str) or not isinstance(operator_url, str) or not operator_url:
        raise ValueError("durable human session lacks public session coordinates")
    if not isinstance(browser_digest, str) or not browser_digest.startswith("sha256:"):
        raise ValueError("durable human session lacks browser executable digest")
    value: dict[str, Any] = {
        "schemaVersion": 1,
        "kind": "ordivon.cft-human-materialization-handoff",
        "effectId": effect_id,
        "requestDigest": request_digest,
        "sessionId": session_id,
        "operatorURL": operator_url,
        "browserExecutableDigest": browser_digest,
        "blocker": blocker,
        "sessionOwner": "systemd",
        "providerEffectAttempted": False,
        "sendAttempted": False,
    }
    value["handoffDigest"] = _digest_obj(value)
    _private_json(path, value)
    return value


def load_verified_handoff(path: Path, *, expected_digest: str | None = None) -> dict[str, Any]:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("durable human handoff must be one regular non-symlink file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("kind") != "ordivon.cft-human-materialization-handoff":
        raise RuntimeError("durable human handoff shape is invalid")
    supplied = value.get("handoffDigest")
    if not isinstance(supplied, str):
        raise RuntimeError("durable human handoff lacks digest")
    body = dict(value)
    body.pop("handoffDigest", None)
    actual = _digest_obj(body)
    if supplied != actual:
        raise RuntimeError("durable human handoff digest mismatch")
    if expected_digest is not None and supplied != expected_digest:
        raise RuntimeError("durable human handoff differs from expected digest")
    if value.get("providerEffectAttempted") is not False or value.get("sendAttempted") is not False:
        raise RuntimeError("durable human handoff does not prove pre-SEND standing")
    return value


def _http_json(url: str, *, method: str = "GET") -> Any:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": "ordivon-cft-human-auth/1"})
    with urllib.request.urlopen(request, timeout=3.0) as response:
        raw = response.read(1_048_576)
        return json.loads(raw)


def prepare_chatgpt_human_session(session: dict[str, Any]) -> dict[str, Any]:
    """Open/activate one ChatGPT page through loopback CDP. Never fills or sends content."""
    if session.get("standing") != "READY":
        raise RuntimeError("durable human session is not READY")
    endpoint = session.get("cdpEndpoint")
    if not isinstance(endpoint, str):
        raise RuntimeError("durable human session lacks CDP endpoint")
    parsed = urllib.parse.urlsplit(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"} or parsed.port is None:
        raise RuntimeError("durable human session CDP endpoint must be explicit loopback HTTP")
    root = endpoint.rstrip("/")
    pages = _http_json(root + "/json/list")
    if not isinstance(pages, list):
        raise RuntimeError("CDP page inventory is invalid")
    chatgpt = [
        row
        for row in pages
        if isinstance(row, dict)
        and row.get("type") == "page"
        and isinstance(row.get("url"), str)
        and row["url"].startswith("https://chatgpt.com")
    ]
    if len(chatgpt) > 1:
        raise RuntimeError("durable human session contains multiple ChatGPT pages")
    if chatgpt:
        page = chatgpt[0]
        page_id = page.get("id")
        if isinstance(page_id, str) and page_id:
            try:
                _http_json(root + "/json/activate/" + urllib.parse.quote(page_id, safe=""))
            except Exception:
                pass
        page_url = page.get("url")
    else:
        encoded = urllib.parse.quote(CHATGPT_ROOT, safe=":/")
        page = _http_json(root + "/json/new?" + encoded, method="PUT")
        if not isinstance(page, dict) or not isinstance(page.get("url"), str):
            raise RuntimeError("CDP failed to create ChatGPT human-auth page")
        page_url = page["url"]
    return {
        "schemaVersion": 1,
        "kind": "ordivon.cft-human-session-preparation",
        "sessionId": session.get("sessionId"),
        "pageUrl": page_url,
        "providerEffectAttempted": False,
        "sendAttempted": False,
    }


class CftHumanRequiredTarget:
    """Pre-SEND target: create one durable CfT auth surface and return HUMAN_REQUIRED."""

    def __init__(
        self,
        *,
        handoff_path: Path,
        session_request_id: str,
        authority_factory=DurableSessionAuthority,
        prepare=prepare_chatgpt_human_session,
    ) -> None:
        self.handoff_path = Path(handoff_path)
        self.session_request_id = session_request_id
        self.authority_factory = authority_factory
        self.prepare = prepare
        self.last_handoff: dict[str, Any] | None = None

    def _existing(self, request: CarrierMaterializationRequest) -> TargetMaterializationObservation | None:
        if not self.handoff_path.is_file():
            return None
        handoff = load_verified_handoff(self.handoff_path)
        if handoff.get("effectId") != request.request_id or handoff.get("requestDigest") != request.request_digest:
            raise RuntimeError("durable human handoff belongs to another materialization request")
        self.last_handoff = handoff
        return TargetMaterializationObservation(
            standing=MaterializationStanding.HUMAN_REQUIRED,
            evidence_digest=handoff["handoffDigest"],
            detail="provider admission requires durable human authentication",
        )

    def materialize(self, request: CarrierMaterializationRequest) -> TargetMaterializationObservation:
        existing = self._existing(request)
        if existing is not None:
            return existing
        authority = self.authority_factory()
        session = authority.open(self.session_request_id)
        # Persist the pre-SEND handoff before any optional page preparation so process loss can
        # still recover a HUMAN_REQUIRED proof from the exact durable session.
        handoff = create_handoff(
            self.handoff_path,
            effect_id=request.request_id,
            request_digest=request.request_digest,
            session=session,
            blocker="auth-required",
        )
        self.last_handoff = handoff
        self.prepare(session)
        return TargetMaterializationObservation(
            standing=MaterializationStanding.HUMAN_REQUIRED,
            evidence_digest=handoff["handoffDigest"],
            detail="provider admission requires durable human authentication",
        )

    def reconcile(self, request: CarrierMaterializationRequest) -> TargetMaterializationObservation:
        existing = self._existing(request)
        if existing is not None:
            return existing
        return TargetMaterializationObservation(
            standing=MaterializationStanding.UNKNOWN,
            detail="no durable human handoff evidence exists for reconciliation",
        )

    def resume_after_human(self, request: CarrierMaterializationRequest) -> TargetMaterializationObservation:
        raise RuntimeError("durable human resume requires the dedicated CfT authenticated-send target")
