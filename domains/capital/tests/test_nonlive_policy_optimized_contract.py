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


def _effect_fixture(tmp_path: Path):
    for folder in ("scripts", "contracts", "config"):
        (tmp_path / folder).mkdir()
    script = tmp_path / "scripts/check-nonlive-effect-authority"
    shutil.copy2(ROOT / "scripts/check-nonlive-effect-authority", script)
    data = {}
    paths = {
        "contract": "contracts/nonlive-effect-admission-v2.json",
        "real": "contracts/external-write-policy-input-v2.json",
        "authority": "config/nonlive_effect_authority.json",
    }
    for label, location in paths.items():
        data[label] = json.loads((ROOT / location).read_text(encoding="utf-8"))
        (tmp_path / location).write_text(json.dumps(data[label]), encoding="utf-8")
    return script, paths, data


@pytest.mark.parametrize("optimized", [False, True])
def test_nonlive_effect_valid_in_both_modes(tmp_path, optimized):
    script, _, _ = _effect_fixture(tmp_path)
    assert _run(script, script, optimized=optimized).returncode == 0


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("label,field", [
    ("contract", "realMoney"),
    ("contract", "externalFinancialWriteAllowed"),
    ("real", "externalFinancialWriteAllowed"),
    ("real", "providerWriteCapabilityBound"),
])
def test_nonlive_effect_rejects_real_write(tmp_path, label, field, optimized):
    script, paths, data = _effect_fixture(tmp_path)
    data[label][field] = True
    (tmp_path / paths[label]).write_text(json.dumps(data[label]), encoding="utf-8")
    result = _run(script, script, optimized=optimized)
    assert result.returncode != 0, f"real write accepted: {label}.{field} optimized={optimized}"


def _binding_fixture(tmp_path: Path):
    script, config_file, data = _fixture(
        tmp_path, "check-private-reality-readonly-preflight"
    )
    script = script.parent / "check-private-reality-credential-bindings"
    shutil.copy2(ROOT / "scripts/check-private-reality-credential-bindings", script)
    okx = tmp_path / "fake-okx.toml"
    okx.write_text("FAKE_NOT_VALID", encoding="utf-8")
    okx.chmod(0o600)
    binance = tmp_path / "fake-binance"
    binance.mkdir()
    for name in ("api_key", "private.pem", "public.pem"):
        p = binance / name
        p.write_text("FAKE_NOT_VALID", encoding="utf-8")
        p.chmod(0o600)
    executor = tmp_path / "fake-executor-excluded"
    executor.mkdir()
    bindings = data["credentialBindings"]
    bindings["OKX"]["binding"] = str(okx)
    bindings["BINANCE"]["binding"] = str(binance)
    bindings["BINANCE_USDM"]["binding"] = str(binance)
    bindings["BINANCE"]["executorBindingExplicitlyExcluded"] = str(executor)
    config_file.write_text(json.dumps(data), encoding="utf-8")
    return script, config_file, data, okx, binance


@pytest.mark.parametrize("optimized", [False, True])
def test_private_bindings_valid_synthetic_control(tmp_path, optimized):
    script, config_file, _, _, _ = _binding_fixture(tmp_path)
    result = _run(script, config_file, optimized=optimized)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("field", [
    "privateAccountDataAllowed", "externalFinancialWritesAllowed",
    "orderCapableCredentialsAllowed",
])
def test_private_bindings_reject_unauthorized_fields(tmp_path, field, optimized):
    script, config_file, data, _, _ = _binding_fixture(tmp_path)
    data[field] = True
    config_file.write_text(json.dumps(data), encoding="utf-8")
    result = _run(script, config_file, optimized=optimized)
    assert result.returncode != 0, f"private bindings accepted {field} optimized={optimized}"


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("item", ["okx", "binance-private", "binance-api"])
def test_private_bindings_reject_permissive_dummy_files(tmp_path, item, optimized):
    script, config_file, _, okx, binance = _binding_fixture(tmp_path)
    secret = {
        "okx": okx,
        "binance-private": binance / "private.pem",
        "binance-api": binance / "api_key",
    }[item]
    secret.chmod(0o644)
    result = _run(script, config_file, optimized=optimized)
    assert result.returncode != 0, f"private bindings accepted permissive {item}"


def _clock_fixture(tmp_path: Path):
    script_folder = tmp_path / "scripts"
    script_folder.mkdir()
    script = script_folder / "check-clock-quality-gate"
    shutil.copy2(ROOT / "scripts/check-clock-quality-gate", script)
    data = json.loads((ROOT / "config/clock_quality_gate.json").read_text(encoding="utf-8"))
    evidence_rel = Path(data["latestEvidence"])
    assert not evidence_rel.is_absolute() and ".." not in evidence_rel.parts
    evidence = tmp_path / evidence_rel
    evidence.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / evidence_rel, evidence)
    config_file = tmp_path / "config/clock_quality_gate.json"
    config_file.parent.mkdir(exist_ok=True)
    config_file.write_text(json.dumps(data), encoding="utf-8")
    return script, config_file, data


@pytest.mark.parametrize("optimized", [False, True])
def test_clock_valid_synthetic_control(tmp_path, optimized):
    script, config_file, _ = _clock_fixture(tmp_path)
    result = _run(script, config_file, optimized=optimized)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("field", [
    "wslIndependentNtpDaemonAllowed", "applicationClockForgeryAllowed",
])
def test_clock_rejects_inadmissible_configuration(tmp_path, field, optimized):
    script, config_file, data = _clock_fixture(tmp_path)
    data[field] = True
    config_file.write_text(json.dumps(data), encoding="utf-8")
    result = _run(script, config_file, optimized=optimized)
    assert result.returncode != 0, f"unsafe clock policy accepted {field}"
