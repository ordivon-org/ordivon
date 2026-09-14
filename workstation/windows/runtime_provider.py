#!/usr/bin/env python3
"""Materialize the Runtime-owned Windows launcher as Workstation v2 provider equipment.

The C# compiler on this node is not reproducible byte-for-byte. Authority is
therefore receipt-based: one exact Git blob and one exact compiler binary
materialize launcher bytes once, and the receipt binds the resulting digest.
Workstation may stage Runtime operator facts, but it never restarts Runtime.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import tomllib
from typing import Any

DEFAULT_CONTRACT = Path(__file__).with_name("runtime-provider.toml")
REVISION = re.compile(r"^[0-9a-f]{40}$")
MANAGED_ENV_KEYS = (
    "ORDIVON_WINDOWS_LAUNCHER_PATH",
    "ORDIVON_WINDOWS_WSL_DISTRIBUTION",
)
WINDOWS_PROVIDER_DROPIN = (
    "[Service]\n"
    "RestrictAddressFamilies=\n"
    "RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6 AF_VSOCK\n"
)
WINDOWS_PROVIDER_ADDRESS_FAMILIES = {"AF_UNIX", "AF_INET", "AF_INET6", "AF_VSOCK"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def read_contract(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text())


def provider_cfg(config: dict[str, Any]) -> dict[str, Any]:
    value = dict(config["runtime_windows_provider"])
    revision = str(value["source_revision"])
    if not REVISION.fullmatch(revision):
        raise RuntimeError("runtime_windows_provider.source_revision must be an exact lowercase commit")
    return value


def launcher_path(provider: dict[str, Any]) -> Path:
    return Path(str(provider["launcher_root"])) / str(provider["source_revision"]) / str(
        provider["launcher_filename"]
    )


def desired_runtime_environment(provider: dict[str, Any]) -> dict[str, str]:
    return {
        "ORDIVON_WINDOWS_LAUNCHER_PATH": str(launcher_path(provider)),
        "ORDIVON_WINDOWS_WSL_DISTRIBUTION": str(provider["wsl_distribution"]),
    }


def git_blob(provider: dict[str, Any]) -> bytes:
    repo = Path(str(provider["source_repo"]))
    revision = str(provider["source_revision"])
    relative = str(provider["source_path"])
    proc = subprocess.run(
        ["/usr/bin/git", "-C", str(repo), "show", f"{revision}:{relative}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"cannot materialize Runtime launcher source {revision}:{relative}: "
            + proc.stderr.decode("utf-8", errors="replace").strip()[:1000]
        )
    return proc.stdout


def expected_inputs(provider: dict[str, Any]) -> dict[str, Any]:
    source = git_blob(provider)
    source_digest = sha256_bytes(source)
    expected_source = str(provider["source_sha256"])
    compiler = Path(str(provider["compiler_path"]))
    compiler_digest = sha256_file(compiler) if compiler.is_file() and not compiler.is_symlink() else None
    return {
        "source": source,
        "sourceDigest": source_digest,
        "sourceMatchesContract": source_digest == expected_source,
        "compilerPath": str(compiler),
        "compilerDigest": compiler_digest,
        "compilerMatchesContract": compiler_digest == str(provider["compiler_sha256"]),
    }


def load_receipt(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file() or path.is_symlink():
        return None, None
    try:
        value = json.loads(path.read_text())
    except Exception as error:
        return None, str(error)
    return (value if isinstance(value, dict) else None), None


def runtime_env_state(provider: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(provider["runtime_env_file"]))
    desired = desired_runtime_environment(provider)
    counts = {key: 0 for key in MANAGED_ENV_KEYS}
    observed: dict[str, str | None] = {key: None for key in MANAGED_ENV_KEYS}
    if path.is_file():
        for raw in path.read_text(errors="replace").splitlines():
            if "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            if key in counts:
                counts[key] += 1
                observed[key] = value.strip().strip('"').strip("'")
    healthy = path.is_file() and all(
        counts[key] == 1 and observed[key] == desired[key] for key in MANAGED_ENV_KEYS
    )
    return {
        "path": str(path),
        "present": path.is_file(),
        "desired": desired,
        "observed": observed,
        "counts": counts,
        "healthy": healthy,
    }


def parse_systemd_show(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key] = value
    return values


def service_dropin_state(provider: dict[str, Any], receipt: dict[str, Any] | None) -> dict[str, Any]:
    path = Path(str(provider["service_dropin_path"]))
    regular = path.is_file() and not path.is_symlink()
    observed_digest = sha256_file(path) if regular else None
    expected_digest = sha256_bytes(WINDOWS_PROVIDER_DROPIN.encode())
    content_matches = regular and path.read_text(errors="replace") == WINDOWS_PROVIDER_DROPIN
    proc = subprocess.run(
        [
            "/usr/bin/systemctl", "show", str(provider["service_unit"]),
            "-p", "DropInPaths", "-p", "RestrictAddressFamilies", "--no-pager",
        ],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    properties = parse_systemd_show(proc.stdout) if proc.returncode == 0 else {}
    dropins = properties.get("DropInPaths", "").split()
    families = set(properties.get("RestrictAddressFamilies", "").split())
    manager_loaded = proc.returncode == 0 and str(path) in dropins
    effective_matches = families == WINDOWS_PROVIDER_ADDRESS_FAMILIES
    service_receipt = receipt.get("serviceSubstrate") if isinstance(receipt, dict) else None
    receipt_bound = isinstance(service_receipt, dict) and service_receipt == {
        "unit": str(provider["service_unit"]),
        "dropInPath": str(path),
        "dropInDigest": expected_digest,
        "restrictAddressFamilies": sorted(WINDOWS_PROVIDER_ADDRESS_FAMILIES),
    }
    return {
        "unit": str(provider["service_unit"]),
        "path": str(path),
        "presentRegular": regular,
        "expectedDigest": expected_digest,
        "observedDigest": observed_digest,
        "contentMatches": content_matches,
        "managerLoaded": manager_loaded,
        "effectiveAddressFamilies": sorted(families),
        "effectiveMatches": effective_matches,
        "receiptBound": receipt_bound,
        "systemctlError": proc.stderr.strip()[:1000] or None if proc.returncode != 0 else None,
        "healthy": content_matches and manager_loaded and effective_matches and receipt_bound,
    }


def provider_status(config: dict[str, Any]) -> dict[str, Any]:
    provider = provider_cfg(config)
    target = launcher_path(provider)
    receipt_path = Path(str(provider["receipt_path"]))
    source_error = None
    try:
        inputs = expected_inputs(provider)
    except Exception as error:
        source_error = str(error)
        inputs = {
            "sourceDigest": None,
            "sourceMatchesContract": False,
            "compilerPath": str(provider["compiler_path"]),
            "compilerDigest": None,
            "compilerMatchesContract": False,
        }
    receipt, receipt_error = load_receipt(receipt_path)
    binary_regular = target.is_file() and not target.is_symlink()
    binary_digest = sha256_file(target) if binary_regular else None
    desired_receipt = {
        "sourceRepo": str(Path(str(provider["source_repo"]))),
        "sourceRevision": str(provider["source_revision"]),
        "sourcePath": str(provider["source_path"]),
        "sourceDigest": str(provider["source_sha256"]),
        "compilerPath": str(provider["compiler_path"]),
        "compilerDigest": str(provider["compiler_sha256"]),
        "launcherPath": str(target),
    }
    receipt_fields_match = isinstance(receipt, dict) and all(
        receipt.get(key) == value for key, value in desired_receipt.items()
    )
    receipt_binary_digest = receipt.get("binaryDigest") if isinstance(receipt, dict) else None
    materialized_healthy = bool(
        inputs.get("sourceMatchesContract")
        and inputs.get("compilerMatchesContract")
        and binary_regular
        and receipt_fields_match
        and isinstance(receipt_binary_digest, str)
        and receipt_binary_digest == binary_digest
    )
    environment = runtime_env_state(provider)
    service_dropin = service_dropin_state(provider, receipt)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.windows-runtime-provider-status",
        "source": {
            "repo": str(provider["source_repo"]),
            "revision": str(provider["source_revision"]),
            "path": str(provider["source_path"]),
            "expectedDigest": str(provider["source_sha256"]),
            "observedDigest": inputs.get("sourceDigest"),
            "matches": bool(inputs.get("sourceMatchesContract")),
            "error": source_error,
        },
        "compiler": {
            "path": str(provider["compiler_path"]),
            "expectedDigest": str(provider["compiler_sha256"]),
            "observedDigest": inputs.get("compilerDigest"),
            "matches": bool(inputs.get("compilerMatchesContract")),
        },
        "launcher": {
            "path": str(target),
            "presentRegular": binary_regular,
            "digest": binary_digest,
        },
        "receipt": {
            "path": str(receipt_path),
            "present": isinstance(receipt, dict),
            "parseError": receipt_error,
            "fieldsMatch": receipt_fields_match,
            "binaryDigest": receipt_binary_digest,
            "acceptance": receipt.get("acceptance") if isinstance(receipt, dict) else None,
        },
        "materializedHealthy": materialized_healthy,
        "runtimeEnvironment": environment,
        "serviceDropIn": service_dropin,
        "healthy": materialized_healthy and bool(environment["healthy"]) and bool(service_dropin["healthy"]),
    }


def windows_path(path: Path) -> str:
    resolved = str(path.resolve())
    match = re.fullmatch(r"/mnt/([a-zA-Z])/(.*)", resolved)
    if match is None:
        raise RuntimeError(f"Windows provider path is not on a WSL-mounted drive: {resolved}")
    return match.group(1).upper() + ":\\" + match.group(2).replace("/", "\\")


def validate_context(value: dict[str, Any], authority: str) -> dict[str, Any]:
    if int(value.get("tokenType", 0)) != 1:
        raise RuntimeError(f"{authority} launcher context did not expose a Primary token")
    sid = value.get("tokenUserSid")
    if not isinstance(sid, str) or not sid:
        raise RuntimeError(f"{authority} launcher context omitted tokenUserSid")
    elevated = value.get("tokenIsElevated") is True
    integrity = int(value.get("tokenIntegrityLevelRid", 0) or 0)
    admin_attrs = int(value.get("administratorsGroupAttributes", 0) or 0)
    if authority == "limited":
        if elevated or integrity > 8192 or (admin_attrs & 0x4) != 0:
            raise RuntimeError("limited launcher context exceeded limited-token authority")
    else:
        if not elevated or integrity < 12288 or (admin_attrs & 0x4) == 0 or (admin_attrs & 0x10) != 0:
            raise RuntimeError("elevated launcher context did not prove High enabled-Administrator authority")
    environment = value.get("environment")
    if not isinstance(environment, dict):
        raise RuntimeError(f"{authority} launcher context omitted bounded environment")
    return {
        "tokenSelection": value.get("tokenSelection"),
        "tokenUserSid": sid,
        "tokenType": int(value["tokenType"]),
        "tokenIsElevated": elevated,
        "tokenIntegrityLevelRid": integrity,
        "administratorsGroupAttributes": admin_attrs,
        "environmentDigest": sha256_bytes(
            json.dumps(environment, sort_keys=True, separators=(",", ":")).encode()
        ),
    }


def probe_launcher(path: Path, authority: str) -> dict[str, Any]:
    proc = subprocess.run(
        [
            str(path),
            "--describe-runtime-context",
            "--authority",
            authority,
            "--context-env",
            "SystemRoot",
            "--context-env",
            "Path",
            "--context-env",
            "USERPROFILE",
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"launcher {authority} context probe failed rc={proc.returncode}: "
            + (proc.stderr.strip() or proc.stdout.strip())[:1000]
        )
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"launcher {authority} context returned invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"launcher {authority} context is not an object")
    return validate_context(value, authority)


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_text_atomic(path: Path, text: str, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def stage_service_dropin(provider: dict[str, Any]) -> bool:
    path = Path(str(provider["service_dropin_path"]))
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"Runtime Windows provider drop-in is not a regular file: {path}")
        if path.read_text(errors="replace") == WINDOWS_PROVIDER_DROPIN:
            return False
    write_text_atomic(path, WINDOWS_PROVIDER_DROPIN, 0o644)
    return True


def bind_service_substrate_receipt(provider: dict[str, Any]) -> bool:
    path = Path(str(provider["receipt_path"]))
    receipt, error = load_receipt(path)
    if not isinstance(receipt, dict):
        raise RuntimeError(f"cannot bind service substrate without launcher receipt: {error or path}")
    desired = {
        "unit": str(provider["service_unit"]),
        "dropInPath": str(provider["service_dropin_path"]),
        "dropInDigest": sha256_bytes(WINDOWS_PROVIDER_DROPIN.encode()),
        "restrictAddressFamilies": sorted(WINDOWS_PROVIDER_ADDRESS_FAMILIES),
    }
    if receipt.get("serviceSubstrate") == desired:
        return False
    receipt["serviceSubstrate"] = desired
    write_json_atomic(path, receipt)
    return True


def merge_runtime_environment(text: str, desired: dict[str, str]) -> str:
    out: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        if "=" in raw:
            key = raw.split("=", 1)[0]
            if key in desired:
                if key not in seen:
                    out.append(f"{key}={desired[key]}")
                    seen.add(key)
                continue
        out.append(raw)
    for key in MANAGED_ENV_KEYS:
        if key not in seen:
            out.append(f"{key}={desired[key]}")
    return "\n".join(out).rstrip() + "\n"


def stage_runtime_environment(provider: dict[str, Any]) -> bool:
    path = Path(str(provider["runtime_env_file"]))
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"Runtime environment file is not a regular file: {path}")
    before = path.read_text(errors="replace")
    after = merge_runtime_environment(before, desired_runtime_environment(provider))
    if before == after:
        return False
    mode = stat.S_IMODE(path.stat().st_mode)
    write_text_atomic(path, after, mode)
    return True


def materialize_provider(provider: dict[str, Any]) -> dict[str, Any]:
    inputs = expected_inputs(provider)
    if not inputs["sourceMatchesContract"]:
        raise RuntimeError(
            f"Runtime launcher source digest changed: expected {provider['source_sha256']}, "
            f"observed {inputs['sourceDigest']}"
        )
    if not inputs["compilerMatchesContract"]:
        raise RuntimeError(
            f"Windows compiler digest changed: expected {provider['compiler_sha256']}, "
            f"observed {inputs['compilerDigest']}"
        )
    target = launcher_path(provider)
    target.parent.mkdir(parents=True, exist_ok=True)
    build_dir = Path(tempfile.mkdtemp(prefix=".materialize-", dir=target.parent))
    try:
        source = build_dir / "Ordivon.WindowsJobLauncher.cs"
        output = build_dir / str(provider["launcher_filename"])
        source.write_bytes(inputs["source"])
        compiler = Path(str(provider["compiler_path"]))
        proc = subprocess.run(
            [
                str(compiler),
                "/nologo",
                "/optimize+",
                f"/out:{windows_path(output)}",
                windows_path(source),
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        if proc.returncode != 0 or not output.is_file():
            raise RuntimeError(
                f"Windows launcher compilation failed rc={proc.returncode}: "
                + (proc.stderr.strip() or proc.stdout.strip())[:2000]
            )
        limited = probe_launcher(output, "limited")
        elevated: dict[str, Any]
        try:
            elevated = {"available": True, **probe_launcher(output, "elevated")}
        except Exception as error:
            elevated = {"available": False, "error": str(error)[:1000]}
        binary_digest = sha256_file(output)
        os.replace(output, target)
        receipt = {
            "schemaVersion": 1,
            "kind": "ordivon.workstation.windows-runtime-provider-materialization",
            "materializedAt": utc_now(),
            "sourceMaterialization": "git_blob_at_exact_commit",
            "buildReproducibility": "compiler_output_not_assumed_reproducible",
            "sourceRepo": str(Path(str(provider["source_repo"]))),
            "sourceRevision": str(provider["source_revision"]),
            "sourcePath": str(provider["source_path"]),
            "sourceDigest": str(provider["source_sha256"]),
            "compilerPath": str(provider["compiler_path"]),
            "compilerDigest": str(provider["compiler_sha256"]),
            "launcherPath": str(target),
            "binaryDigest": binary_digest,
            "acceptance": {"limited": limited, "elevated": elevated},
        }
        write_json_atomic(Path(str(provider["receipt_path"])), receipt)
        return receipt
    finally:
        shutil.rmtree(build_dir, ignore_errors=True)


def apply_provider(config: dict[str, Any]) -> dict[str, Any]:
    provider = provider_cfg(config)
    before = provider_status(config)
    changed: list[str] = []
    materialization = None
    if not before["materializedHealthy"]:
        materialization = materialize_provider(provider)
        changed.extend([str(launcher_path(provider)), str(provider["receipt_path"])])
    env_changed = stage_runtime_environment(provider)
    if env_changed:
        changed.append(str(provider["runtime_env_file"]))
    dropin_changed = stage_service_dropin(provider)
    if dropin_changed:
        changed.append(str(provider["service_dropin_path"]))
        subprocess.run(["/usr/bin/systemctl", "daemon-reload"], check=True)
    receipt_changed = bind_service_substrate_receipt(provider)
    if receipt_changed and str(provider["receipt_path"]) not in changed:
        changed.append(str(provider["receipt_path"]))
    after = provider_status(config)
    if not after["healthy"]:
        raise RuntimeError("Windows Runtime provider failed post-materialization verification")
    return {
        "schemaVersion": 1,
        "status": "completed",
        "changedPaths": changed,
        "materialized": materialization is not None,
        "runtimeEnvironmentChanged": env_changed,
        "serviceDropInChanged": dropin_changed,
        "materializationReceiptChanged": receipt_changed,
        "runtimeRestartRequired": env_changed or dropin_changed,
        "materializationReceipt": materialization,
        "provider": after,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("command", choices=("status", "apply"))
    args = parser.parse_args()
    try:
        config = read_contract(args.contract)
        value = provider_status(config) if args.command == "status" else apply_provider(config)
        print(json.dumps(value, indent=2, sort_keys=True))
        return 0 if (args.command == "apply" or value.get("healthy")) else 1
    except Exception as error:
        print(json.dumps({"schemaVersion": 1, "status": "failed", "error": str(error)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
