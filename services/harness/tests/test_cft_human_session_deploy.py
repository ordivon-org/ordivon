from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import cft_human_session_deploy as deploy  # noqa: E402


def browser_binding() -> dict:
    return {
        "equipmentId": "browser:playwright-chromium",
        "state": "AVAILABLE",
        "executionTarget": "local_linux",
        "executable": "/root/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome",
        "executableDigest": "sha256:" + "8" * 64,
        "bindingDigest": "sha256:" + "9" * 64,
    }


def websockify_binding() -> dict:
    return {
        "equipmentId": "browserless-websockify-0-13-0",
        "state": "AVAILABLE",
        "executionTarget": "local_linux",
        "executable": "/opt/ordivon/external/websockify/0.13.0/bin/websockify",
        "executableDigest": "sha256:" + "7" * 64,
        "bindingDigest": "sha256:" + "6" * 64,
    }


def test_render_units_binds_exact_cft_tree_into_sandbox_namespace() -> None:
    rendered = deploy.render_units(
        browser=browser_binding(), websockify=websockify_binding()
    )
    browser = rendered["ordivon-cft-human-browser@.service"].decode()
    web = rendered["ordivon-cft-human-web@.service"].decode()
    assert "@CFT_ROOT@" not in browser
    assert "@CFT_EXECUTABLE@" not in browser
    assert "@WEBSOCKIFY_EXECUTABLE@" not in web
    assert (
        "BindReadOnlyPaths=/root/.cache/ms-playwright/chromium-1243/chrome-linux64:"
        "/opt/ordivon/cft-current"
    ) in browser
    assert "ExecStart=/opt/ordivon/cft-current/chrome " in browser
    assert "/opt/ordivon/external/websockify/0.13.0/bin/websockify" in web
    assert "--no-sandbox" not in browser


def test_desired_unit_set_is_exact() -> None:
    with (
        mock.patch.object(deploy, "browser_equipment_binding", return_value=browser_binding()),
        mock.patch.object(deploy, "websockify_equipment_binding", return_value=websockify_binding()),
    ):
        value = deploy.desired_units()
    assert set(value) == {
        "ordivon-cft-human-session@.target",
        "ordivon-cft-human-display@.service",
        "ordivon-cft-human-browser@.service",
        "ordivon-cft-human-vnc@.service",
        "ordivon-cft-human-web@.service",
    }


def test_release_manifest_includes_session_authority_and_templates() -> None:
    text = (ROOT / "scripts/agent_automation_release.py").read_text()
    for required in (
        '"scripts/cft_human_session.py"',
        '"scripts/cft_human_session_auth.py"',
        '"scripts/cft_human_session_deploy.py"',
        '"systemd/ordivon-cft-human-session@.target"',
        '"systemd/ordivon-cft-human-display@.service"',
        '"systemd/ordivon-cft-human-browser@.service"',
        '"systemd/ordivon-cft-human-vnc@.service"',
        '"systemd/ordivon-cft-human-web@.service"',
    ):
        assert required in text
