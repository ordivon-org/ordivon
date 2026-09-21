from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import playwright_browserless_chatgpt_submit as submit  # noqa:E402


class Page:
    url = "https://chatgpt.com/"


def args(tmp_path: Path):
    return SimpleNamespace(
        effect_id="effect-1",
        prompt_digest="sha256:" + "1" * 64,
        pre_effect_out=tmp_path / "pre.json",
    )


def test_auth_race_after_preflight_fails_pre_effect_for_durable_cft_reentry(tmp_path: Path) -> None:
    a = args(tmp_path)
    decision, handed = submit.route_provider_blocker(Page(), a, "auth-required")
    assert decision == "failed" and handed is False
    row = json.loads(a.pre_effect_out.read_text())
    assert row["blocker"] == "auth-required-after-browserless-preflight"
    assert row["providerEffectAttempted"] is False


def test_challenge_race_remains_pre_effect_hold(tmp_path: Path) -> None:
    a = args(tmp_path)
    decision, handed = submit.route_provider_blocker(Page(), a, "challenge-gated")
    assert decision == "failed" and handed is False
    row = json.loads(a.pre_effect_out.read_text())
    assert row["blocker"] == "automated-browser-challenge-unsupported"


def test_current_submit_has_no_human_transport_or_liveurl_surface() -> None:
    text = (ROOT / "scripts/playwright_browserless_chatgpt_submit.py").read_text()
    for forbidden in (
        "browserless_human_handoff",
        "browserless_human_interaction",
        "mint_handoff",
        "wait_for_human_provider_admission",
        "handle_human_gate",
        "HUMAN_REQUIRED_EXIT",
        "Browserless.reconnect",
        "live-url",
        "self-hosted-vnc",
    ):
        assert forbidden not in text


def test_current_submit_parser_has_no_handoff_arguments() -> None:
    text = (ROOT / "scripts/playwright_browserless_chatgpt_submit.py").read_text()
    for forbidden in (
        "--human-handoff-out",
        "--human-handoff-ms",
        "--human-handoff-mode",
        "--reconnect-ms",
    ):
        assert forbidden not in text
