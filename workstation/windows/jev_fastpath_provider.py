#!/usr/bin/env python3
"""Materialize and verify the Windows-native Jev Ultrafast provider.

Workstation owns only node-local provider bytes, paths, and launch requirements.
It stores no model credentials and owns no Agent/Harness success semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
from typing import Any
from urllib.request import urlopen
import zipfile

DEFAULT_CONTRACT = Path(__file__).with_name("jev-fastpath-provider.toml")
REVISION = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
WINDOWS_DRIVE = re.compile(r"^([A-Za-z]):\\(.*)$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def run(args: list[str], *, env: dict[str, str] | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        timeout=timeout,
        check=False,
    )


def config(path: Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    value = dict(tomllib.loads(path.read_text())["jev_windows_provider"])
    if not REVISION.fullmatch(str(value["source_revision"])):
        raise RuntimeError("source_revision must be an exact lowercase Git commit")
    for key in ("uv_asset_sha256", "uv_exe_sha256"):
        if not SHA256.fullmatch(str(value[key])):
            raise RuntimeError(f"{key} must be an exact sha256 digest")
    port = int(value["cdp_port"])
    if not 1024 <= port <= 65535:
        raise RuntimeError("cdp_port must be an unprivileged TCP port")
    if value.get("require_python_utf8") is not True:
        raise RuntimeError("Windows Jev provider must require Python UTF-8 mode")
    return value


def localappdata_windows() -> str:
    proc = run(
        [
            "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$env:LOCALAPPDATA",
        ],
        timeout=15,
    )
    value = proc.stdout.strip().replace("\r", "")
    if proc.returncode != 0 or not value:
        raise RuntimeError("cannot resolve Windows LOCALAPPDATA")
    return value


def windows_to_wsl(path: str) -> Path:
    match = WINDOWS_DRIVE.fullmatch(path)
    if match is None:
        raise RuntimeError(f"not an absolute Windows drive path: {path}")
    drive, tail = match.groups()
    return Path("/mnt") / drive.lower() / Path(tail.replace("\\", "/"))


def wsl_to_windows(path: Path) -> str:
    resolved = str(path.resolve())
    match = re.fullmatch(r"/mnt/([a-zA-Z])/(.*)", resolved)
    if match is None:
        raise RuntimeError(f"path is not on a WSL-mounted Windows drive: {resolved}")
    return match.group(1).upper() + ":\\" + match.group(2).replace("/", "\\")


def paths(cfg: dict[str, Any]) -> dict[str, Any]:
    local_win = localappdata_windows()
    local_wsl = windows_to_wsl(local_win)
    external = local_wsl / str(cfg["external_root_relative"])
    uv_root = external / "uv" / str(cfg["uv_version"])
    python_root = external / "python"
    source_root = external / "jev-ultrafast" / str(cfg["source_revision"])
    return {
        "localAppDataWindows": local_win,
        "localAppDataWsl": local_wsl,
        "externalRoot": external,
        "uvRoot": uv_root,
        "uvExe": uv_root / "uv.exe",
        "pythonRoot": python_root,
        "pythonExe": python_root / str(cfg["python_distribution_dir"]) / "python.exe",
        "sourceRoot": source_root,
        "venvPython": source_root / ".venv" / "Scripts" / "python.exe",
        "jevExe": source_root / ".venv" / "Scripts" / "jev.exe",
        "browserHarnessExe": source_root / ".venv" / "Scripts" / "browser-harness.exe",
        "profile": local_wsl / str(cfg["profile_relative"]),
        "chrome": windows_to_wsl(str(cfg["chrome_path"])),
        "receipt": Path(str(cfg["receipt_path"])),
    }


def git_state(cfg: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
    root: Path = p["sourceRoot"]
    if not (root / ".git").exists():
        return {"present": False, "head": None, "origin": None, "trackedClean": False, "exact": False}
    head = run(["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"], timeout=15)
    origin = run(["/usr/bin/git", "-C", str(root), "remote", "get-url", "origin"], timeout=15)
    dirty = run(
        ["/usr/bin/git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
        timeout=15,
    )
    exact = (
        head.returncode == 0
        and head.stdout.strip() == str(cfg["source_revision"])
        and origin.returncode == 0
        and origin.stdout.strip() == str(cfg["source_repo"])
        and dirty.returncode == 0
        and not dirty.stdout.strip()
    )
    return {
        "present": True,
        "head": head.stdout.strip() or None,
        "origin": origin.stdout.strip() or None,
        "trackedClean": dirty.returncode == 0 and not dirty.stdout.strip(),
        "exact": exact,
    }


def package_state(cfg: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
    python: Path = p["venvPython"]
    if not python.is_file():
        return {"present": False, "jevVersion": None, "browserHarnessVersion": None, "exact": False}
    code = (
        "import importlib.metadata as m,json;"
        "print(json.dumps({'jev':m.version('jev-ultrafast'),"
        "'browser_harness':m.version('browser-harness')}))"
    )
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    proc = run([str(python), "-c", code], env=env, timeout=20)
    try:
        value = json.loads(proc.stdout) if proc.returncode == 0 else {}
    except json.JSONDecodeError:
        value = {}
    return {
        "present": proc.returncode == 0,
        "jevVersion": value.get("jev"),
        "browserHarnessVersion": value.get("browser_harness"),
        "exact": (
            value.get("jev") == str(cfg["jev_version"])
            and value.get("browser_harness") == str(cfg["browser_harness_version"])
        ),
    }


def chrome_state(cfg: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
    chrome: Path = p["chrome"]
    version = None
    if chrome.is_file():
        ps_path = str(cfg["chrome_path"]).replace("'", "''")
        proc = run(
            [
                "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f"(Get-Item '{ps_path}').VersionInfo.ProductVersion",
            ],
            timeout=15,
        )
        if proc.returncode == 0:
            version = proc.stdout.strip().replace("\r", "") or None
    return {
        "path": str(cfg["chrome_path"]),
        "present": chrome.is_file(),
        "version": version,
        "cdpAddress": "127.0.0.1",
        "cdpPort": int(cfg["cdp_port"]),
        "profileWindows": wsl_to_windows(p["profile"]),
        "loopbackOnly": True,
    }


def load_receipt(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return value if isinstance(value, dict) else None


def receipt_basis(cfg: dict[str, Any], p: dict[str, Any], uv_digest: str | None) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.windows-jev-fastpath-provider",
        "uvVersion": str(cfg["uv_version"]),
        "uvAssetUrl": str(cfg["uv_asset_url"]),
        "uvAssetDigest": str(cfg["uv_asset_sha256"]),
        "uvExecutableDigest": uv_digest,
        "pythonVersion": str(cfg["python_version"]),
        "sourceRepo": str(cfg["source_repo"]),
        "sourceRevision": str(cfg["source_revision"]),
        "jevVersion": str(cfg["jev_version"]),
        "browserHarnessVersion": str(cfg["browser_harness_version"]),
        "chromePath": str(cfg["chrome_path"]),
        "profileWindows": wsl_to_windows(p["profile"]),
        "cdpAddress": "127.0.0.1",
        "cdpPort": int(cfg["cdp_port"]),
        "requiredEnvironment": {"PYTHONUTF8": "1"},
        "secretOwnership": "consumer-owned-not-stored-by-workstation",
    }


def provider_status(cfg: dict[str, Any]) -> dict[str, Any]:
    p = paths(cfg)
    uv: Path = p["uvExe"]
    uv_digest = sha256_file(uv) if uv.is_file() else None
    uv_exact = uv_digest == str(cfg["uv_exe_sha256"])
    py: Path = p["pythonExe"]
    python_version = None
    if py.is_file():
        env = dict(os.environ)
        env["PYTHONUTF8"] = "1"
        proc = run([str(py), "--version"], env=env, timeout=15)
        if proc.returncode == 0:
            python_version = proc.stdout.strip() or proc.stderr.strip() or None
    source = git_state(cfg, p)
    packages = package_state(cfg, p)
    chrome = chrome_state(cfg, p)
    expected_receipt = receipt_basis(cfg, p, uv_digest)
    receipt = load_receipt(p["receipt"])
    receipt_bound = isinstance(receipt, dict) and receipt == expected_receipt
    physical = bool(
        uv_exact
        and python_version == f"Python {cfg['python_version']}"
        and source["exact"]
        and packages["exact"]
        and chrome["present"]
    )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.windows-jev-fastpath-provider-status",
        "physicalHealthy": physical,
        "healthy": physical and receipt_bound,
        "uv": {
            "path": str(uv),
            "expectedDigest": str(cfg["uv_exe_sha256"]),
            "observedDigest": uv_digest,
            "exact": uv_exact,
        },
        "python": {
            "path": str(py),
            "expectedVersion": str(cfg["python_version"]),
            "observedVersion": python_version,
            "exact": python_version == f"Python {cfg['python_version']}",
        },
        "source": source,
        "packages": packages,
        "chrome": chrome,
        "launchContract": {
            "pythonUtf8": True,
            "environment": {"PYTHONUTF8": "1"},
            "processLifecycle": "on-demand-no-daemon-required",
            "dedicatedProfile": True,
            "regularUserProfileReused": False,
        },
        "receipt": {
            "path": str(p["receipt"]),
            "present": isinstance(receipt, dict),
            "bound": receipt_bound,
        },
        "nonClaims": [
            "provider_credentials_present",
            "provider_network_serviceable",
            "agent_task_authorized",
            "browser_semantic_success",
        ],
    }


def download_exact_uv(cfg: dict[str, Any], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ordivon-jev-uv-") as raw:
        root = Path(raw)
        archive = root / "uv.zip"
        with urlopen(str(cfg["uv_asset_url"]), timeout=60) as response, archive.open("wb") as out:
            shutil.copyfileobj(response, out)
        observed = sha256_file(archive)
        if observed != str(cfg["uv_asset_sha256"]):
            raise RuntimeError(
                f"uv asset digest changed: expected {cfg['uv_asset_sha256']}, observed {observed}"
            )
        with zipfile.ZipFile(archive) as bundle:
            names = set(bundle.namelist())
            required = {"uv.exe", "uvw.exe", "uvx.exe"}
            if not required.issubset(names):
                raise RuntimeError(f"uv asset omitted required Windows binaries: {sorted(required - names)}")
            staged = root / "extract"
            staged.mkdir()
            for name in required:
                with bundle.open(name) as src, (staged / name).open("wb") as dst:
                    shutil.copyfileobj(src, dst)
        uv_observed = sha256_file(staged / "uv.exe")
        if uv_observed != str(cfg["uv_exe_sha256"]):
            raise RuntimeError(
                f"uv executable digest changed: expected {cfg['uv_exe_sha256']}, observed {uv_observed}"
            )
        for name in required:
            os.replace(staged / name, target.parent / name)


def ensure_python(cfg: dict[str, Any], p: dict[str, Any]) -> None:
    uv: Path = p["uvExe"]
    env = dict(os.environ)
    env["UV_PYTHON_INSTALL_DIR"] = wsl_to_windows(p["pythonRoot"])
    env["UV_MANAGED_PYTHON"] = "1"
    proc = run(
        [
            str(uv),
            "python",
            "install",
            str(cfg["python_version"]),
            "--install-dir",
            wsl_to_windows(p["pythonRoot"]),
            "--no-registry",
            "--no-bin",
            "--no-progress",
        ],
        env=env,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError("uv Windows Python materialization failed: " + (proc.stderr or proc.stdout)[-2000:])


def ensure_source(cfg: dict[str, Any], p: dict[str, Any]) -> None:
    root: Path = p["sourceRoot"]
    if root.exists() and not (root / ".git").is_dir():
        raise RuntimeError(f"Jev release path is occupied by a non-Git tree: {root}")
    if (root / ".git").is_dir():
        dirty = run(
            ["/usr/bin/git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
            timeout=20,
        )
        if dirty.returncode != 0 or dirty.stdout.strip():
            raise RuntimeError("existing Jev release has tracked source modifications")
        origin = run(["/usr/bin/git", "-C", str(root), "remote", "get-url", "origin"], timeout=15)
        if origin.returncode != 0 or origin.stdout.strip() != str(cfg["source_repo"]):
            raise RuntimeError("existing Jev release origin differs from contract")
    else:
        root.mkdir(parents=True, exist_ok=True)
        for args in (
            ["/usr/bin/git", "-C", str(root), "init", "-q"],
            ["/usr/bin/git", "-C", str(root), "remote", "add", "origin", str(cfg["source_repo"])],
        ):
            proc = run(args, timeout=30)
            if proc.returncode != 0:
                raise RuntimeError("cannot initialize exact Jev source: " + proc.stderr[-1000:])
    fetch = run(
        [
            "/usr/bin/git", "-C", str(root), "fetch", "--quiet", "--depth", "1",
            "origin", str(cfg["source_revision"]),
        ],
        timeout=120,
    )
    if fetch.returncode != 0:
        raise RuntimeError("cannot fetch exact Jev revision: " + fetch.stderr[-1500:])
    checkout = run(
        ["/usr/bin/git", "-C", str(root), "checkout", "--quiet", "--detach", "FETCH_HEAD"],
        timeout=30,
    )
    if checkout.returncode != 0:
        raise RuntimeError("cannot checkout exact Jev revision: " + checkout.stderr[-1500:])


def sync_environment(cfg: dict[str, Any], p: dict[str, Any]) -> None:
    env = dict(os.environ)
    env["UV_PYTHON_INSTALL_DIR"] = wsl_to_windows(p["pythonRoot"])
    env["UV_MANAGED_PYTHON"] = "1"
    env["PYTHONUTF8"] = "1"
    proc = run(
        [
            str(p["uvExe"]),
            "--directory",
            wsl_to_windows(p["sourceRoot"]),
            "sync",
            "--frozen",
            "--no-dev",
            "--python",
            str(cfg["python_version"]),
            "--managed-python",
            "--no-progress",
        ],
        env=env,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError("Jev frozen Windows environment sync failed: " + (proc.stderr or proc.stdout)[-2000:])


def write_receipt(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def apply_provider(cfg: dict[str, Any]) -> dict[str, Any]:
    p = paths(cfg)
    before = provider_status(cfg)
    changed: list[str] = []
    if not before["uv"]["exact"]:
        download_exact_uv(cfg, p["uvExe"])
        changed.append(str(p["uvRoot"]))
    if not before["python"]["exact"]:
        ensure_python(cfg, p)
        changed.append(str(p["pythonRoot"]))
    if not before["source"]["exact"]:
        ensure_source(cfg, p)
        changed.append(str(p["sourceRoot"]))
    if not before["packages"]["exact"]:
        sync_environment(cfg, p)
        changed.append(str(p["sourceRoot"] / ".venv"))

    after_physical = provider_status(cfg)
    if not after_physical["physicalHealthy"]:
        raise RuntimeError("Windows Jev provider failed physical post-materialization verification")
    desired_receipt = receipt_basis(cfg, p, after_physical["uv"]["observedDigest"])
    if load_receipt(p["receipt"]) != desired_receipt:
        write_receipt(p["receipt"], desired_receipt)
        changed.append(str(p["receipt"]))
    after = provider_status(cfg)
    if not after["healthy"]:
        raise RuntimeError("Windows Jev provider receipt failed post-materialization verification")
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.windows-jev-fastpath-provider-apply",
        "standing": "PASS",
        "changedPaths": changed,
        "provider": after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("command", choices=("status", "apply"))
    args = parser.parse_args()
    try:
        cfg = config(args.contract)
        value = provider_status(cfg) if args.command == "status" else apply_provider(cfg)
        print(json.dumps(value, indent=2, sort_keys=True))
        if args.command == "status":
            return 0 if value["healthy"] else 1
        return 0
    except Exception as error:
        print(json.dumps({"schemaVersion": 1, "standing": "FAILED", "error": str(error)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
