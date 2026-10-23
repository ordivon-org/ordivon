from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path
from types import SimpleNamespace

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
    assert cfg["uv_version"] == "0.13.5"
    assert cfg["python_version"] == "3.15.1"
    assert cfg["source_revision"] == "452c1ad2dd628008f1d5608f28158d76e49e6cc0"
    assert cfg["jev_version"] == "0.1.0"
    assert cfg["browser_harness_version"] == "0.1.13"
    assert cfg["cdp_port"] == 9338
    assert cfg["consumer_secret_relative"] == "Ordivon/Secrets/jev-fastpath-v1"
    assert cfg["require_python_utf8"] is True
    assert "TYPESAFE_API_KEY" not in raw
    assert "TEXT_MODEL_API_KEY" not in raw


def test_old_interpreter_venv_is_not_accepted_as_new_python(monkeypatch, tmp_path):
    candidate = tmp_path / ".venv-py3.15.0" / "Scripts" / "python.exe"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"test")
    cfg = {
        "jev_version": "0.1.0",
        "browser_harness_version": "0.1.13",
        "python_version": "3.15.0",
    }
    import json
    def simulate(version):
        monkeypatch.setattr(
            M, "run", lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"jev": "0.1.0", "browser_harness": "0.1.13", "python": version}),
            )
        )
        return M.package_state(cfg, {"venvPython": candidate})
    assert simulate("3.12.13")["exact"] is False
    assert simulate("3.15.0")["exact"] is True


def test_contract_requires_isolated_versioned_venv(tmp_path):
    raw = (ROOT / "workstation/windows/jev-fastpath-provider.toml").read_text()
    assert 'venv_relative = ".venv-py3.15.1"' in raw
    for escape in ('../active', '/tmp/env', '.venv-py3.12.0/../../evil'):
        f = tmp_path / "bad.toml"
        f.write_text(raw.replace('venv_relative = ".venv-py3.15.1"', f'venv_relative = "{escape}"'))
        try:
            M.config(f)
        except RuntimeError as error:
            assert "venv_relative" in str(error)
        else:
            raise AssertionError("unbounded venv path accepted")


def test_windows_wsl_path_projection_round_trip_for_drive_paths():
    value = M.windows_to_wsl(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    assert str(value) == "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
    assert M.wsl_to_windows(value) == r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def test_provider_status_exports_exact_provider_venv_python_binding():
    source = (ROOT / "workstation/windows/jev_fastpath_provider.py").read_text()
    assert '"providerVenvPath": str(p["venvPython"])' in source
    assert '"providerVenvWindows": wsl_to_windows(p["venvPython"])' in source


def test_dpapi_secret_state_requires_current_user_decryptability(monkeypatch, tmp_path):
    blob = tmp_path / "secret.dpapi"
    blob.write_bytes(b"ciphertext")
    monkeypatch.setattr(M, "wsl_to_windows", lambda _path: r"C:\\Users\\u\\secret.dpapi")
    monkeypatch.setattr(M, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=0))
    assert M.dpapi_secret_state(blob) == {"present": True, "decryptable": True}

    monkeypatch.setattr(M, "run", lambda *_args, **_kwargs: SimpleNamespace(returncode=2))
    assert M.dpapi_secret_state(blob) == {"present": True, "decryptable": False}
    assert M.dpapi_secret_state(tmp_path / "missing.dpapi") == {
        "present": False,
        "decryptable": False,
    }


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


def test_windows_native_provider_probe_uses_exact_contract_and_binds_versions(monkeypatch, tmp_path):
    """No WSL_INTEROP and no old interpreter can be used as provider evidence."""
    from hashlib import sha256

    cfg = M.config()
    local = tmp_path / "LocalAppData"
    external = local / "Ordivon" / "External"
    base = external / "jev-ultrafast" / cfg["source_revision"]
    (base / ".git").mkdir(parents=True)
    (base / cfg["venv_relative"] / "Scripts").mkdir(parents=True)
    venv_python = base / cfg["venv_relative"] / "Scripts" / "python.exe"
    venv_python.write_bytes(b"versioned-venv")
    uv_path = external / "uv" / cfg["uv_version"] / "uv.exe"
    uv_path.parent.mkdir(parents=True)
    uv_path.write_bytes(b"verified-uv-executable")
    python_path = (external / "python" / cfg["python_distribution_dir"] / "python.exe")
    python_path.parent.mkdir(parents=True)
    python_path.write_bytes(b"managed-python")
    chrome = tmp_path / "Chrome" / "chrome.exe"
    chrome.parent.mkdir()
    chrome.write_bytes(b"chrome-test")
    cfg = dict(cfg)
    cfg["uv_exe_sha256"] = "sha256:" + sha256(uv_path.read_bytes()).hexdigest()
    cfg["chrome_path"] = str(chrome)
    monkeypatch.setattr(M.shutil, "which", lambda name: "C:/Git/bin/git.exe" if name == "git" else None)

    def native_runner(argv, **_kwargs):
        cmd = " ".join(map(str, argv))
        if argv[0] == str(python_path):
            return SimpleNamespace(returncode=0, stdout="Python 3.15.1\n", stderr="")
        if argv[0] == str(venv_python):
            return SimpleNamespace(returncode=0, stdout='{"jev":"0.1.0","browser_harness":"0.1.13","python":"3.15.1"}', stderr="")
        if "rev-parse HEAD" in cmd:
            return SimpleNamespace(returncode=0, stdout=cfg["source_revision"], stderr="")
        if "remote get-url origin" in cmd:
            return SimpleNamespace(returncode=0, stdout=cfg["source_repo"], stderr="")
        if "status --porcelain" in cmd:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        raise AssertionError(f"unexpected native subprocess {cmd}")

    monkeypatch.setattr(M, "run", native_runner)
    good = M.native_provider_status(cfg, local)
    assert good["windowsPhysicalHealthy"] is True
    assert good["observerAuthority"] == "windows_native_current_user"
    assert good["receiptEvaluated"] is False
    assert good["python"]["version"] == "Python 3.15.1"
    assert good["source"]["exact"] is True
    assert good["packages"]["exact"] is True

    python_path.unlink()
    missing = M.native_provider_status(cfg, local)
    assert missing["windowsPhysicalHealthy"] is False
    assert missing["python"]["exact"] is False


def test_windows_native_probe_rejects_old_venv_and_source_revision(monkeypatch, tmp_path):
    """Exact Git identity and exact Python 3.15 package witness are mandatory."""
    from hashlib import sha256
    cfg = dict(M.config())
    ext = tmp_path / "Ordivon" / "External"
    base = ext / "jev-ultrafast" / cfg["source_revision"]
    (base / ".git").mkdir(parents=True)
    py = base / cfg["venv_relative"] / "Scripts" / "python.exe"
    py.parent.mkdir(parents=True)
    py.write_bytes(b"old-version")
    managed = ext / "python" / cfg["python_distribution_dir"] / "python.exe"
    managed.parent.mkdir(parents=True)
    managed.write_bytes(b"runtime")
    uv = ext / "uv" / cfg["uv_version"] / "uv.exe"
    uv.parent.mkdir(parents=True)
    uv.write_bytes(b"sha-bound")
    cfg["uv_exe_sha256"] = "sha256:" + sha256(uv.read_bytes()).hexdigest()
    chrome = tmp_path / "chrome.exe"
    chrome.write_bytes(b"chrome")
    cfg["chrome_path"] = str(chrome)
    monkeypatch.setattr(M.shutil, "which", lambda _name: "C:/Git/bin/git.exe")
    def bad_runner(argv, **_kwargs):
        cmd=" ".join(map(str,argv))
        if argv[0] == str(managed):
            return SimpleNamespace(returncode=0,stdout="Python 3.15.0",stderr="")
        if argv[0] == str(py):
            return SimpleNamespace(returncode=0,stdout='{"jev":"0.1.0","browser_harness":"0.1.13","python":"3.12.13"}',stderr="")
        if "rev-parse HEAD" in cmd:
            return SimpleNamespace(returncode=0,stdout="a"*40,stderr="")
        if "remote get-url origin" in cmd:
            return SimpleNamespace(returncode=0,stdout=cfg["source_repo"],stderr="")
        if "status --porcelain" in cmd:
            return SimpleNamespace(returncode=0,stdout="",stderr="")
        raise AssertionError(cmd)
    monkeypatch.setattr(M,"run",bad_runner)
    result=M.native_provider_status(cfg,tmp_path)
    assert result["windowsPhysicalHealthy"] is False
    assert result["packages"]["exact"] is False
    assert result["source"]["exact"] is False
    assert result["receiptEvaluated"] is False


def test_windows_provider_runbook_cannot_advertise_legacy_runtime_versions():
    cfg = M.config()
    doc = (ROOT / "docs/JEV_FASTPATH_PROVIDER.md").read_text()
    assert f'uv {cfg["uv_version"]}' in doc
    assert f'CPython {cfg["python_version"]}' in doc
    assert "status-native" in doc
    assert "receiptEvaluated" in doc
