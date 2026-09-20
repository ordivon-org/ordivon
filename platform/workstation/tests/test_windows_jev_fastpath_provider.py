from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "workstation/windows/jev_fastpath_provider.py"
SPEC = importlib.util.spec_from_file_location("windows_jev_fastpath_provider", MODULE_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_contract_pins_external_provider_without_credentials():
    path = ROOT / "workstation/windows/jev-fastpath-provider.toml"
    raw = path.read_text()
    cfg = tomllib.loads(raw)["jev_windows_provider"]
    assert cfg["uv_version"] == "0.12.3"
    assert cfg["python_version"] == "3.12.13"
    assert cfg["source_revision"] == "452c1ad2dd628008f1d5608f28158d76e49e6cc0"
    assert cfg["jev_version"] == "0.1.0"
    assert cfg["browser_harness_version"] == "0.1.13"
    assert cfg["cdp_port"] == 9338
    assert cfg["require_python_utf8"] is True
    assert "TYPESAFE_API_KEY" not in raw
    assert "TEXT_MODEL_API_KEY" not in raw


def test_windows_wsl_path_projection_round_trip_for_drive_paths():
    value = M.windows_to_wsl(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    assert str(value) == "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
    assert M.wsl_to_windows(value) == r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def test_config_rejects_privileged_cdp_port(tmp_path):
    src = (ROOT / "workstation/windows/jev-fastpath-provider.toml").read_text()
    path = tmp_path / "bad.toml"
    path.write_text(src.replace("cdp_port = 9338", "cdp_port = 80"))
    try:
        M.config(path)
    except RuntimeError as error:
        assert "unprivileged" in str(error)
    else:
        raise AssertionError("privileged port was admitted")


def test_receipt_basis_has_no_provider_secret_fields(monkeypatch, tmp_path):
    cfg = M.config(ROOT / "workstation/windows/jev-fastpath-provider.toml")
    p = {"profile": tmp_path / "profile"}
    monkeypatch.setattr(M, "wsl_to_windows", lambda _path: r"C:\Users\u\profile")
    value = M.receipt_basis(cfg, p, cfg["uv_exe_sha256"])
    text = repr(value)
    assert "TYPESAFE" not in text and "TEXT_MODEL" not in text
    assert value["requiredEnvironment"] == {"PYTHONUTF8": "1"}
    assert value["cdpAddress"] == "127.0.0.1"
