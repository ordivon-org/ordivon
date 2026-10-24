"""Actual Capital admission policy validators must never disappear under python -O.

Only synthetic local JSON and temporary fake credential files are used.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _fixture(tmp_path: Path, name: str, *, secret_mode: int = 0o600):
    scripts = tmp_path / "scripts"
    configs = tmp_path / "config"
    scripts.mkdir(exist_ok=True)
    configs.mkdir(exist_ok=True)
    source = ROOT / "scripts" / name
    destination = scripts / name
    shutil.copy2(source, destination)
    policy_name = {
        "check-demo-execution-preflight": "demo_execution_policy.json",
        "check-nonlive-credential-provisioning": "nonlive_credential_provisioning.json",
        "check-private-reality-readonly-preflight": "private_reality_policy.json",
    }[name]
    policy = json.loads((ROOT / "config" / policy_name).read_text(encoding="utf-8"))
    if name == "check-nonlive-credential-provisioning":
        binance = tmp_path / "fake-binance"
        okx = tmp_path / "fake-okx"
        binance.mkdir()
        okx.mkdir()
        (binance / "private.pem").write_text("FAKE_KEY_NOT_VALID", encoding="utf-8")
        (binance / "private.pem").chmod(secret_mode)
        policy["venues"]["BINANCE"]["secretRoot"] = str(binance)
        policy["venues"]["OKX"]["secretRoot"] = str(okx)
    config_file = configs / policy_name
    config_file.write_text(json.dumps(policy), encoding="utf-8")
    return destination, config_file, policy


def _run(script: Path, config_file: Path, *, optimized: bool):
    env = dict(os.environ, PYTHONOPTIMIZE="1" if optimized else "0", PYTHONDONTWRITEBYTECODE="1")
    if script.name == "check-private-reality-readonly-preflight":
        # Execute the byte-for-byte policy block from the REAL shell script without
        # invoking external provider SDKs, secret locations or network probes.
        source = script.read_text(encoding="utf-8")
        first = source.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
        return subprocess.run(
            [sys.executable, "-c", first, str(config_file)],
            capture_output=True, text=True, env=env, timeout=20, check=False,
        )
    return subprocess.run(
        [str(script)], capture_output=True, text=True, env=env, timeout=20, check=False,
    )


@pytest.mark.parametrize("name", [
    "check-demo-execution-preflight",
    "check-nonlive-credential-provisioning",
    "check-private-reality-readonly-preflight",
])
@pytest.mark.parametrize("optimized", [False, True])
def test_valid_policy_is_accepted_in_both_interpreter_modes(tmp_path, name, optimized):
    script, config_file, _ = _fixture(tmp_path, name)
    result = _run(script, config_file, optimized=optimized)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name,attribute", [
    ("check-demo-execution-preflight", "externalFinancialWritesAllowed"),
    ("check-nonlive-credential-provisioning", "externalFinancialWritesAllowed"),
    ("check-private-reality-readonly-preflight", "externalFinancialWritesAllowed"),
    ("check-demo-execution-preflight", "liveWriteAdmission"),
    ("check-nonlive-credential-provisioning", "liveWriteAuthorization"),
    ("check-private-reality-readonly-preflight", "orderCapableCredentialsAllowed"),
])
@pytest.mark.parametrize("optimized", [False, True])
def test_forbidden_write_rights_are_rejected(tmp_path, name, attribute, optimized):
    script, config_file, policy = _fixture(tmp_path, name)
    policy[attribute] = "ADMITTED" if attribute == "liveWriteAdmission" else (
        "GRANTED" if attribute == "liveWriteAuthorization" else True
    )
    config_file.write_text(json.dumps(policy), encoding="utf-8")
    result = _run(script, config_file, optimized=optimized)
    assert result.returncode != 0, f"{name}: false accept of {attribute} in optimized={optimized}"


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("venue,filename", [
    ("BINANCE", "private.pem"),
    ("BINANCE", "api_key"),
    ("OKX", "config.toml"),
])
def test_world_readable_synthetic_credentials_are_rejected(
    tmp_path, venue, filename, optimized
):
    script, config_file, policy = _fixture(
        tmp_path, "check-nonlive-credential-provisioning"
    )
    secret = Path(policy["venues"][venue]["secretRoot"]) / filename
    if not secret.exists():
        secret.write_text("FAKE_CREDENTIAL_NOT_VALID", encoding="utf-8")
    secret.chmod(0o644)
    result = _run(script, config_file, optimized=optimized)
    assert result.returncode != 0, f"world-readable synthetic {filename} was accepted"
