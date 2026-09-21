from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from chatgpt_conversation_discovery import discover_exact_marker  # noqa: E402


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


class StaticObserver:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows
        self.calls: list[tuple[dict[str, str], str]] = []

    def __call__(self, session: dict[str, str], marker_digest: str) -> list[dict[str, str]]:
        self.calls.append((dict(session), marker_digest))
        return list(self.rows)


def session() -> dict[str, str]:
    return {"sessionId": "cft-session-01", "cdpEndpoint": "http://127.0.0.1:9222"}


def test_exact_one_match_returns_canonical_provider_resource_without_send() -> None:
    marker = digest("ORDIVON-ADOPT-ONE")
    observer = StaticObserver(
        [
            {
                "pageUrl": "https://chatgpt.com/c/conversation-123?utm=ignored",
                "markerDigest": marker,
            }
        ]
    )

    value = discover_exact_marker(session(), marker, observer=observer)

    assert value["standing"] == "EXACT_MATCH"
    assert value["matchCount"] == 1
    assert value["providerResource"] == "https://chatgpt.com/c/conversation-123"
    assert value["providerEffectAttempted"] is False
    assert value["sendAttempted"] is False
    assert value["sideEffectsAttempted"] is False
    assert value["markerDigest"] == marker
    assert value["evidenceDigest"].startswith("sha256:")
    assert observer.calls == [(session(), marker)]


def test_zero_match_fails_closed() -> None:
    wanted = digest("wanted")
    observer = StaticObserver(
        [{"pageUrl": "https://chatgpt.com/c/other", "markerDigest": digest("other")}]
    )

    value = discover_exact_marker(session(), wanted, observer=observer)

    assert value["standing"] == "NO_MATCH"
    assert value["matchCount"] == 0
    assert "providerResource" not in value


def test_multiple_distinct_matches_fail_closed() -> None:
    marker = digest("same-marker")
    observer = StaticObserver(
        [
            {"pageUrl": "https://chatgpt.com/c/a", "markerDigest": marker},
            {"pageUrl": "https://chatgpt.com/c/b", "markerDigest": marker},
        ]
    )

    value = discover_exact_marker(session(), marker, observer=observer)

    assert value["standing"] == "AMBIGUOUS_MATCH"
    assert value["matchCount"] == 2
    assert "providerResource" not in value


def test_duplicate_dom_links_to_same_conversation_count_once() -> None:
    marker = digest("same-marker")
    observer = StaticObserver(
        [
            {"pageUrl": "https://chatgpt.com/c/a", "markerDigest": marker},
            {"pageUrl": "https://chatgpt.com/c/a?duplicate=1", "markerDigest": marker},
        ]
    )

    value = discover_exact_marker(session(), marker, observer=observer)

    assert value["standing"] == "EXACT_MATCH"
    assert value["matchCount"] == 1
    assert value["providerResource"] == "https://chatgpt.com/c/a"


def test_non_chatgpt_or_nonconversation_rows_do_not_become_matches() -> None:
    marker = digest("marker")
    observer = StaticObserver(
        [
            {"pageUrl": "https://example.com/c/a", "markerDigest": marker},
            {"pageUrl": "https://chatgpt.com/", "markerDigest": marker},
        ]
    )

    value = discover_exact_marker(session(), marker, observer=observer)

    assert value["standing"] == "NO_MATCH"
    assert value["matchCount"] == 0


def test_evidence_digest_is_stable_across_observation_order() -> None:
    marker = digest("marker")
    rows = [
        {"pageUrl": "https://chatgpt.com/c/a", "markerDigest": marker},
        {"pageUrl": "https://chatgpt.com/c/b", "markerDigest": digest("other")},
    ]
    first = discover_exact_marker(session(), marker, observer=StaticObserver(rows))
    second = discover_exact_marker(session(), marker, observer=StaticObserver(list(reversed(rows))))
    assert first["evidenceDigest"] == second["evidenceDigest"]


def test_raw_marker_text_cannot_enter_result_contract() -> None:
    raw_marker = "ORDIVON-RAW-MARKER-MUST-NOT-PERSIST"
    marker = digest(raw_marker)
    value = discover_exact_marker(
        session(),
        marker,
        observer=StaticObserver(
            [{"pageUrl": "https://chatgpt.com/c/a", "markerDigest": marker}]
        ),
    )
    assert raw_marker not in json.dumps(value, sort_keys=True)


@pytest.mark.parametrize(
    "bad",
    ["", "sha256:abc", "SHA256:" + "a" * 64, "sha256:" + "g" * 64],
)
def test_marker_digest_must_be_canonical_sha256(bad: str) -> None:
    with pytest.raises(ValueError, match="marker digest"):
        discover_exact_marker(session(), bad, observer=StaticObserver([]))


def test_session_coordinate_requires_loopback_cdp_endpoint() -> None:
    with pytest.raises(ValueError, match="loopback"):
        discover_exact_marker(
            {"sessionId": "cft-session-01", "cdpEndpoint": "http://10.0.0.8:9222"},
            digest("marker"),
            observer=StaticObserver([]),
        )
