from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import playwright_browserless_chatgpt_submit as submit  # noqa: E402
import playwright_browserless_human_resume as resume  # noqa: E402


class Page:
    url = "https://chatgpt.com/"


def args(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        effect_id="effect-1",
        prompt_digest="sha256:" + "1" * 64,
        pre_effect_out=tmp_path / "pre-effect.json",
        human_handoff_out=tmp_path / "handoff.json",
        endpoint_id="carrier-a",
        human_handoff_ms=60_000,
        reconnect_ms=60_000,
        human_handoff_mode="live-url",
    )


def test_submit_challenge_is_pre_effect_hold_without_handoff(tmp_path: Path) -> None:
    a = args(tmp_path)
    decision, handed_off = submit.route_provider_blocker(Page(), a, "challenge-gated")
    assert decision == "failed"
    assert handed_off is False
    receipt = json.loads(a.pre_effect_out.read_text())
    assert receipt["blocker"] == "automated-browser-challenge-unsupported"
    assert receipt["providerEffectAttempted"] is False


def test_submit_auth_race_is_pre_effect_hold_for_durable_cft_reentry(tmp_path: Path) -> None:
    a = args(tmp_path)
    decision, handed_off = submit.route_provider_blocker(Page(), a, "auth-required")
    assert decision == "failed"
    assert handed_off is False
    receipt = json.loads(a.pre_effect_out.read_text())
    assert receipt["blocker"] == "auth-required-after-browserless-preflight"
    assert receipt["providerEffectAttempted"] is False


def test_resume_challenge_blocks_without_repark(tmp_path: Path) -> None:
    a = args(tmp_path)
    handoff = {"liveURLId": "live-1"}
    with (
        mock.patch.object(resume, "repark") as repark,
        mock.patch.object(resume, "close_old_live_url") as close,
    ):
        decision, handed_off = resume.route_provider_blocker(Page(), a, handoff, "challenge-gated")
    repark.assert_not_called()
    close.assert_called_once()
    assert decision == "failed"
    assert handed_off is False
    receipt = json.loads(a.pre_effect_out.read_text())
    assert receipt["blocker"] == "automated-browser-challenge-unsupported"
    assert receipt["providerEffectAttempted"] is False


def test_resume_auth_can_repark_same_session(tmp_path: Path) -> None:
    a = args(tmp_path)
    handoff = {"liveURLId": "live-1"}
    with (
        mock.patch.object(resume, "repark", return_value=True) as repark,
        mock.patch.object(resume, "close_old_live_url") as close,
    ):
        decision, handed_off = resume.route_provider_blocker(Page(), a, handoff, "auth-required")
    close.assert_called_once()
    repark.assert_called_once()
    assert decision == "human-required"
    assert handed_off is True
    assert not a.pre_effect_out.exists()


def test_effect_executors_delegate_blocker_policy_to_provider_boundary() -> None:
    submit_text = (ROOT / "scripts/playwright_browserless_chatgpt_submit.py").read_text()
    resume_text = (ROOT / "scripts/playwright_browserless_human_resume.py").read_text()
    for text in (submit_text, resume_text):
        assert "provider_action_for_standing" in text
        assert "PROVIDER_ACTION_HUMAN_CONTROL_TRANSFER" in text
        assert "PROVIDER_ACTION_HOLD" in text
