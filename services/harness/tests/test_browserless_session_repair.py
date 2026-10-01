import hashlib
import json
import os
from pathlib import Path

import pytest

from scripts.playwright_browserless_session_repair import load_normalized_bundle, sanitized_receipt


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def private_bundle(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "session.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    path.chmod(0o600)
    return path


def test_bundle_normalizes_authorized_scope_and_filters_expired(tmp_path: Path) -> None:
    path = private_bundle(tmp_path, [
        {"name": "session-secret-name", "value": "TOP-SECRET-VALUE", "domain": ".chatgpt.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "lax", "expires": 4102444800},
        {"name": "old", "value": "OLD-SECRET", "domain": ".openai.com", "path": "/", "expires": 1},
        {"name": "other", "value": "OTHER-SECRET", "domain": ".example.com", "path": "/"},
    ])
    rows, stats = load_normalized_bundle(path, digest(path), now_s=2)
    assert len(rows) == 1
    assert rows[0]["value"] == "TOP-SECRET-VALUE"
    assert rows[0]["sameSite"] == "Lax"
    assert stats == {"inputCount": 3, "eligibleCount": 1, "expiredDropped": 1, "outsideScopeDropped": 1, "invalidDropped": 0}


def test_sanitized_receipt_never_projects_cookie_material(tmp_path: Path) -> None:
    secret_name = "session-secret-name"
    secret_value = "TOP-SECRET-VALUE"
    path = private_bundle(tmp_path, [{"name": secret_name, "value": secret_value, "domain": ".chatgpt.com", "path": "/"}])
    rows, stats = load_normalized_bundle(path, digest(path), now_s=2)
    receipt = sanitized_receipt("carrier-11", "READY", digest(path), stats, page_url="https://chatgpt.com/?secret=should-not-survive")
    encoded = json.dumps(receipt, sort_keys=True)
    assert rows[0]["value"] == secret_value
    assert secret_name not in encoded
    assert secret_value not in encoded
    assert "should-not-survive" not in encoded
    assert receipt["rawCredentialProjected"] is False
    assert receipt["sendAttempted"] is False
    assert receipt["pageRef"] == "https://chatgpt.com/"


def test_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    path = private_bundle(tmp_path, [{"name": "a", "value": "b", "domain": ".chatgpt.com", "path": "/"}])
    with pytest.raises(ValueError, match="digest mismatch"):
        load_normalized_bundle(path, "sha256:" + "0" * 64)


def test_broad_permissions_are_rejected(tmp_path: Path) -> None:
    path = private_bundle(tmp_path, [{"name": "a", "value": "b", "domain": ".chatgpt.com", "path": "/"}])
    path.chmod(0o644)
    with pytest.raises(ValueError, match="permissions"):
        load_normalized_bundle(path, digest(path))


def test_apply_receipt_is_still_no_send(tmp_path: Path) -> None:
    path = private_bundle(tmp_path, [{"name": "a", "value": "b", "domain": ".chatgpt.com", "path": "/"}])
    _, stats = load_normalized_bundle(path, digest(path), now_s=2)
    receipt = sanitized_receipt("carrier-11", "READY", digest(path), stats, mode="apply")
    assert receipt["mode"] == "apply"
    assert receipt["providerEffectAttempted"] is False
    assert receipt["sendAttempted"] is False
    assert receipt["rawCredentialProjected"] is False
