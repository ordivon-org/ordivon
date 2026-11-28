from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import chatgpt_provider_gate as gate  # noqa: E402
import playwright_browserless_chatgpt_submit as submit  # noqa: E402
import playwright_browserless_human_resume as resume  # noqa: E402


def test_provider_gate_is_the_single_blocker_classifier_and_selector_owner() -> None:
    assert submit.provider_blocker is gate.provider_blocker
    assert resume.provider_blocker is gate.provider_blocker
    for name in (
        "playwright_browserless_chatgpt_submit.py",
        "playwright_browserless_human_resume.py",
        "playwright_browserless_provider_preflight.py",
        "playwright_browserless_conversation_output.py",
        "playwright_browserless_turn_once.py",
    ):
        source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "CHALLENGE_SELECTOR =" not in source, name
        assert "LOGIN_SELECTOR =" not in source, name
        assert "SIGNUP_SELECTOR =" not in source, name
    for name in (
        "playwright_browserless_chatgpt_submit.py",
        "playwright_browserless_human_resume.py",
    ):
        source = (ROOT / "scripts" / name).read_text(encoding="utf-8")
        assert "def human_blocker(" not in source, name


class Page:
    url = "https://chatgpt.com/"


class Locator:
    def __init__(self, *, count: int = 0, visible: bool = False) -> None:
        self._count = count
        self._visible = visible

    def count(self) -> int:
        return self._count

    @property
    def first(self):
        return self

    def is_visible(self) -> bool:
        return self._visible


class GatePage:
    url = "https://chatgpt.com/"

    def __init__(self, selectors: dict[str, Locator]) -> None:
        self._selectors = selectors

    def title(self) -> str:
        return "ChatGPT"

    def locator(self, selector: str) -> Locator:
        return self._selectors.get(selector, Locator())


def test_provider_blocker_preserves_challenge_precedence_over_auth() -> None:
    page = GatePage(
        {
            gate.CHALLENGE_SELECTOR: Locator(count=1),
            gate.LOGIN_SELECTOR: Locator(count=1, visible=True),
        }
    )
    assert gate.provider_blocker(page) == "challenge-gated"


def test_provider_blocker_classifies_visible_auth_surface() -> None:
    page = GatePage({gate.SIGNUP_SELECTOR: Locator(count=1, visible=True)})
    assert gate.provider_blocker(page) == "auth-required"


def test_provider_blocker_returns_none_without_gate_evidence() -> None:
    assert gate.provider_blocker(GatePage({})) is None


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
