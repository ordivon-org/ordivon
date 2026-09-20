#!/usr/bin/env python3
"""Qualify one locally available Browserless image with an isolated paired canary.

The transaction runs a control arm from the installed production Browserless execution contract,
then a candidate arm with the requested immutable image. Active on-demand carriers are cross-checked
against that contract, but sleeping carriers are not treated as failures. Both arms use the same
Network-v2 namespace, Ordivon-owned environment, headful display geometry, empty profile class and
neutral Browser Security witness suite. It never visits ChatGPT, solves a challenge, or crosses SEND.

This command is qualification-only: it does not mutate the production Quadlet or restart carriers
11/12/13. Candidate promotion is deliberately a separate authority boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_CONFIG = Path("/etc/ordivon/agent-automation-browserless.json")
INSTALLED_QUADLET = Path("/etc/containers/systemd/ordivon-browserless@.container")
SECURITY_ROOT = Path("/root/projects/ordivon-security-v2")
PLAYWRIGHT_PYTHON = Path(
    "/root/.local/share/ordivon-workstation/conversation-relay-playwright-r4/.venv/bin/python"
)
TOKEN_FILE = Path("/etc/ordivon/browserless.token")
PRODUCTION_INSTANCES = (11, 12, 13)
CANARY_INSTANCE = 91
CANARY_ENDPOINT_ID = f"chatgpt-carrier-{CANARY_INSTANCE}"
CANARY_CONTAINER = f"ordivon-browserless-{CANARY_INSTANCE}"
CANARY_PROFILE = Path(f"/var/lib/ordivon/browserless/{CANARY_INSTANCE}")
CANARY_XAUTH = Path(f"/run/ordivon/browserless-xauth/{CANARY_INSTANCE}")
CANARY_DISPLAY = f":1{CANARY_INSTANCE}"
CANARY_PORT = int(f"30{CANARY_INSTANCE}")
IMAGE_RE = re.compile(r"^ghcr\.io/browserless/chromium@sha256:[0-9a-f]{64}$")
OWNED_ENV_KEYS = (
    "CONCURRENT",
    "QUEUED",
    "TIMEOUT",
    "HEALTH",
    "MAX_CPU_PERCENT",
    "MAX_MEMORY_PERCENT",
    "DEBUG",
    "TZ",
    "XAUTHORITY",
)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def validate_image_ref(value: str) -> str:
    if not isinstance(value, str) or IMAGE_RE.fullmatch(value) is None:
        raise ValueError("candidate image must be exact ghcr.io/browserless/chromium@sha256:<64hex>")
    return value


def _run_json(args: list[str]) -> Any:
    proc = subprocess.run(args, capture_output=True, text=True, timeout=15, check=True)
    return json.loads(proc.stdout)


def _env_map(raw: object) -> dict[str, str]:
    if not isinstance(raw, list):
        raise RuntimeError("Browserless container Env must be a list")
    values: dict[str, str] = {}
    for item in raw:
        if not isinstance(item, str) or "=" not in item:
            continue
        key, value = item.split("=", 1)
        values[key] = value
    return values


def production_control_from_quadlet(
    raw: str, active_rows: dict[int, dict[str, Any]] | None = None
) -> dict[str, Any]:
    active_rows = active_rows or {}
    if not set(active_rows).issubset(PRODUCTION_INSTANCES):
        raise RuntimeError("active Browserless carrier set contains an unknown production instance")
    image_rows = [line.removeprefix("Image=") for line in raw.splitlines() if line.startswith("Image=")]
    network_rows = [
        line.removeprefix("Network=ns:/run/netns/")
        for line in raw.splitlines()
        if line.startswith("Network=ns:/run/netns/")
    ]
    env_rows = [line.removeprefix("Environment=") for line in raw.splitlines() if line.startswith("Environment=")]
    if len(image_rows) != 1:
        raise RuntimeError("installed Browserless Quadlet must contain exactly one Image= line")
    if len(network_rows) != 1 or not network_rows[0] or "/" in network_rows[0]:
        raise RuntimeError("installed Browserless Quadlet must contain one Network-v2 namespace")
    image = validate_image_ref(image_rows[0])
    environment = _env_map(env_rows)
    owned: dict[str, str] = {}
    for key in OWNED_ENV_KEYS:
        value = environment.get(key)
        if value is None:
            raise RuntimeError(f"installed Browserless Quadlet lacks env {key}")
        owned[key] = value
    namespace = network_rows[0]

    for instance, row in sorted(active_rows.items()):
        state = row.get("State")
        if not isinstance(state, dict) or state.get("Running") is not True:
            raise RuntimeError(f"active Browserless carrier {instance} is not actually running")
        observed_image = row.get("ImageName")
        if observed_image != image:
            raise RuntimeError(f"active Browserless carrier {instance} image disagrees with installed control")
        host = row.get("HostConfig")
        network_mode = host.get("NetworkMode") if isinstance(host, dict) else None
        if network_mode != f"ns:/run/netns/{namespace}":
            raise RuntimeError(
                f"active Browserless carrier {instance} Network-v2 namespace disagrees with installed control"
            )
        config = row.get("Config")
        observed_env = _env_map(config.get("Env") if isinstance(config, dict) else None)
        for key, expected in owned.items():
            if observed_env.get(key) != expected:
                raise RuntimeError(
                    f"active Browserless carrier {instance} env {key} disagrees with installed control"
                )
    return {
        "image": image,
        "networkNamespace": namespace,
        "environment": owned,
        "instances": list(PRODUCTION_INSTANCES),
        "activeInstances": sorted(active_rows),
        "inactiveInstances": sorted(set(PRODUCTION_INSTANCES) - set(active_rows)),
        "controlAuthority": "installed-rendered-quadlet",
    }


def discover_production_control() -> dict[str, Any]:
    try:
        raw = INSTALLED_QUADLET.read_text(encoding="utf-8")
    except OSError as error:
        raise RuntimeError("installed Browserless Quadlet is unavailable") from error
    active_rows: dict[int, dict[str, Any]] = {}
    for instance in PRODUCTION_INSTANCES:
        unit = f"ordivon-browserless@{instance}.service"
        active = subprocess.run(
            ["/usr/bin/systemctl", "is-active", "--quiet", unit], check=False
        ).returncode == 0
        exists = subprocess.run(
            ["/usr/bin/podman", "container", "exists", f"ordivon-browserless-{instance}"],
            check=False,
        ).returncode == 0
        if not active:
            if exists:
                raise RuntimeError(
                    f"inactive Browserless carrier {instance} still has a container; lifecycle state is ambiguous"
                )
            continue
        if not exists:
            raise RuntimeError(f"active Browserless carrier {instance} has no Podman container")
        value = _run_json(["/usr/bin/podman", "inspect", f"ordivon-browserless-{instance}"])
        if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
            raise RuntimeError(f"unexpected podman inspect result for carrier {instance}")
        active_rows[instance] = value[0]
    return production_control_from_quadlet(raw, active_rows)


def classify_canary_comparison(
    *, control_image: str, candidate_image: str, comparison: dict[str, Any]
) -> dict[str, Any]:
    if comparison.get("rootCauseEstablished") is not False:
        raise ValueError("Security comparison must preserve rootCauseEstablished=false")
    detector_rows = comparison.get("detectors")
    if not isinstance(detector_rows, list):
        raise ValueError("Security comparison lacks detector rows")
    detector_shape_drift = any(
        isinstance(row, dict) and row.get("status") in {"ADDED", "MISSING", "DETECTOR_DRIFT"}
        for row in detector_rows
    )
    detector_drift = comparison.get("detectorDrift")
    if detector_shape_drift or (isinstance(detector_drift, list) and detector_drift):
        standing = "HOLD_DETECTOR_DRIFT"
    else:
        infrastructure = comparison.get("infrastructureChanges")
        if not isinstance(infrastructure, dict):
            raise ValueError("Security comparison lacks infrastructureChanges")
        if infrastructure.get("networkAuthority") is not False:
            standing = "HOLD_NETWORK_AUTHORITY_DRIFT"
        elif comparison.get("challengeStandingChanged") is not False:
            standing = "HOLD_CHALLENGE_METADATA_DRIFT"
        elif comparison.get("changedFamilies"):
            standing = "HOLD_PRESENTATION_DRIFT"
        elif comparison.get("publicObservationChanges"):
            standing = "HOLD_PRESENTATION_DRIFT"
        elif control_image == candidate_image:
            if infrastructure.get("browserBinary") or infrastructure.get("controlLayer"):
                standing = "HOLD_CONTROL_NONREPRODUCIBLE"
            else:
                standing = "PASS_CONTROL_REPRODUCIBLE"
        else:
            standing = "PASS_EXPECTED_INFRASTRUCTURE_CHANGE"
    return {
        "standing": standing,
        "pass": standing.startswith("PASS_"),
        "controlImage": control_image,
        "candidateImage": candidate_image,
        "expectedImageChange": control_image != candidate_image,
        "rootCauseEstablished": False,
    }


def _load_production_config(namespace: str) -> dict[str, Any]:
    value = json.loads(PRODUCTION_CONFIG.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise RuntimeError("invalid production Browserless automation config")
    authority = value.get("browserNetworkAuthority")
    if not isinstance(authority, dict):
        raise RuntimeError("production config lacks browserNetworkAuthority")
    substrate = value.get("browserSubstrate")
    endpoints = substrate.get("endpoints") if isinstance(substrate, dict) else None
    if not isinstance(endpoints, list) or not endpoints:
        raise RuntimeError("production config lacks Browserless endpoints")
    observed_namespaces = {row.get("networkNamespace") for row in endpoints if isinstance(row, dict)}
    if observed_namespaces != {namespace}:
        raise RuntimeError("production config Network-v2 namespace disagrees with installed control")
    value = dict(value)
    # The canary replaces the production pool with one isolated endpoint. Production warm-residency
    # policy names production endpoint ids and therefore must not leak into the synthetic canary pool.
    value["browserlessWarmEndpointIds"] = []
    value["browserSubstrate"] = {
        "kind": "browserless",
        "endpoints": [
            {
                "id": CANARY_ENDPOINT_ID,
                "websocketEndpoint": f"ws://127.0.0.1:{CANARY_PORT}/chromium",
                "httpEndpoint": f"http://127.0.0.1:{CANARY_PORT}",
                "tokenFile": str(TOKEN_FILE),
                "networkNamespace": namespace,
                "userDataDir": "/data",
                "headless": False,
            }
        ],
    }
    return value


def _require_local_image(image: str) -> None:
    proc = subprocess.run(["/usr/bin/podman", "image", "exists", image], check=False)
    if proc.returncode != 0:
        raise RuntimeError("candidate Browserless image is not present locally; qualification never pulls")


def _require_canary_idle() -> None:
    proc = subprocess.run(
        ["/usr/bin/podman", "container", "exists", CANARY_CONTAINER], check=False
    )
    if proc.returncode == 0:
        raise RuntimeError("Browserless canary container already exists")
    active = subprocess.run(
        ["/usr/bin/systemctl", "is-active", "--quiet", f"ordivon-browserless@{CANARY_INSTANCE}.service"],
        check=False,
    )
    if active.returncode == 0:
        raise RuntimeError("reserved Browserless canary production service is active")
    if CANARY_PROFILE.exists():
        raise RuntimeError("reserved Browserless canary profile already exists")
    if Path(f"/tmp/.X11-unix/X{100 + CANARY_INSTANCE}").exists():
        raise RuntimeError("reserved Browserless canary X11 socket already exists")


def _prepare_profile() -> None:
    CANARY_PROFILE.mkdir(parents=True, mode=0o700)
    os.chmod(CANARY_PROFILE, 0o700)


def _cleanup_profile() -> None:
    if CANARY_PROFILE.exists():
        shutil.rmtree(CANARY_PROFILE)


def _start_display() -> subprocess.Popen[bytes]:
    sys.path.insert(0, str(ROOT / "scripts"))
    import browserless_display_auth

    if browserless_display_auth.QUALIFICATION_INSTANCE != CANARY_INSTANCE:
        raise RuntimeError("Browserless canary/display-auth qualification instance mismatch")
    browserless_display_auth.prepare(CANARY_INSTANCE)
    process = subprocess.Popen(
        [
            "/usr/bin/Xvfb",
            CANARY_DISPLAY,
            "-screen",
            "0",
            "1440x1000x24",
            "-nolisten",
            "tcp",
            "-auth",
            str(CANARY_XAUTH),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    socket = Path(f"/tmp/.X11-unix/X{100 + CANARY_INSTANCE}")
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if socket.exists() and process.poll() is None:
            return process
        if process.poll() is not None:
            detail = (process.stderr.read() if process.stderr else b"").decode(
                "utf-8", errors="replace"
            )[-1200:]
            _stop_display(process)
            raise RuntimeError(f"Browserless canary Xvfb exited before ready: {detail}")
        time.sleep(0.1)
    _stop_display(process)
    raise RuntimeError("Browserless canary Xvfb did not become ready")


def _stop_display(process: subprocess.Popen[bytes] | None) -> None:
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if CANARY_XAUTH.exists():
        CANARY_XAUTH.unlink()


def build_canary_podman_command(
    *, image: str, namespace: str, environment: dict[str, str]
) -> list[str]:
    validate_image_ref(image)
    if not namespace or "/" in namespace or any(ch.isspace() for ch in namespace):
        raise ValueError("invalid Network-v2 namespace")
    command = [
        "/usr/bin/podman",
        "run",
        "--name",
        CANARY_CONTAINER,
        "--rm",
        "--cgroups=split",
        "--hostname",
        CANARY_CONTAINER,
        "--pull",
        "never",
        "--shm-size",
        "2g",
        "--network",
        f"ns:/run/netns/{namespace}",
        "-d",
        "-v",
        f"{CANARY_PROFILE}:/data:U",
        "-v",
        "/tmp/.X11-unix:/tmp/.X11-unix",
        "-v",
        f"{CANARY_XAUTH}:/run/ordivon-xauth:ro",
    ]
    for key in OWNED_ENV_KEYS:
        if key == "XAUTHORITY":
            value = "/run/ordivon-xauth"
        else:
            value = environment[key]
        command.extend(["--env", f"{key}={value}"])
    command.extend(["--env", f"DISPLAY={CANARY_DISPLAY}", "--env", f"PORT={CANARY_PORT}"])
    command.extend(["--secret", "ordivon-browserless-token,type=env,target=TOKEN", image])
    return command


def _start_container(*, image: str, namespace: str, environment: dict[str, str]) -> None:
    subprocess.run(
        build_canary_podman_command(image=image, namespace=namespace, environment=environment),
        check=True,
        timeout=30,
        capture_output=True,
        text=True,
    )


def _stop_container() -> None:
    subprocess.run(
        ["/usr/bin/podman", "stop", "--time", "10", CANARY_CONTAINER],
        check=False,
        timeout=20,
        capture_output=True,
        text=True,
    )


def _wait_healthy(config_path: Path, timeout_seconds: float = 30.0) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from browserless_substrate import BrowserlessPool

    config = json.loads(config_path.read_text(encoding="utf-8"))
    endpoint = BrowserlessPool.from_dict(config["browserSubstrate"]).endpoints[0]
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        last = endpoint.health(timeout_seconds=2.0)
        if last.get("healthy") is True:
            return
        time.sleep(0.25)
    raise RuntimeError(f"Browserless canary failed health: {last}")


def _run_checked(args: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(args, check=True, env=env, timeout=120)


def _collect_arm(
    *,
    arm: str,
    image: str,
    control: dict[str, Any],
    config_path: Path,
    artifact_root: Path,
    security_root: Path,
) -> tuple[Path, Path]:
    _prepare_profile()
    source = artifact_root / f"{arm}-manifest.json"
    bundle = artifact_root / f"{arm}-bundle.json"
    try:
        _start_container(
            image=image,
            namespace=control["networkNamespace"],
            environment=control["environment"],
        )
        _wait_healthy(config_path)
        env = {**os.environ, "PYTHONPATH": str(ROOT)}
        _run_checked(
            [
                str(PLAYWRIGHT_PYTHON),
                str(ROOT / "scripts/browser_security_witness_source.py"),
                "--config",
                str(config_path),
                "--endpoint-id",
                CANARY_ENDPOINT_ID,
                "--witness-id",
                f"browserless-canary-{arm}",
                "--output",
                str(source),
            ],
            env=env,
        )
        security_env = {**os.environ, "PYTHONPATH": str(security_root / "src")}
        _run_checked(
            [
                "/usr/bin/python",
                str(security_root / "scripts/build_browser_security_witness.py"),
                str(source),
                "--output",
                str(bundle),
            ],
            env=security_env,
        )
        return source, bundle
    finally:
        _stop_container()
        _cleanup_profile()


def _compare_bundles(control: Path, candidate: Path, security_root: Path) -> dict[str, Any]:
    env = {**os.environ, "PYTHONPATH": str(security_root / "src")}
    proc = subprocess.run(
        [
            "/usr/bin/python",
            str(security_root / "scripts/compare_browser_security_bundles.py"),
            str(control),
            str(candidate),
        ],
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    value = json.loads(proc.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("Security-v2 canary comparison returned non-object JSON")
    return value


def run_canary(
    *, candidate_image: str, artifact_dir: Path | None, security_root: Path = SECURITY_ROOT
) -> dict[str, Any]:
    candidate_image = validate_image_ref(candidate_image)
    security_root = security_root.resolve()
    _require_local_image(candidate_image)
    _require_canary_idle()
    control = discover_production_control()
    _require_local_image(control["image"])
    config = _load_production_config(control["networkNamespace"])

    if artifact_dir is None:
        temp = tempfile.TemporaryDirectory(prefix="ordivon-browserless-canary-")
        artifact_root = Path(temp.name)
    else:
        temp = None
        artifact_root = artifact_dir.resolve()
        artifact_root.mkdir(parents=True, exist_ok=False)
    try:
        config_path = artifact_root / "canary-config.json"
        config_path.write_text(json.dumps(config, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.chmod(config_path, 0o600)
        display_process = _start_display()
        try:
            control_source, control_bundle = _collect_arm(
                arm="control",
                image=control["image"],
                control=control,
                config_path=config_path,
                artifact_root=artifact_root,
                security_root=security_root,
            )
            candidate_source, candidate_bundle = _collect_arm(
                arm="candidate",
                image=candidate_image,
                control=control,
                config_path=config_path,
                artifact_root=artifact_root,
                security_root=security_root,
            )
        finally:
            _stop_container()
            _cleanup_profile()
            _stop_display(display_process)

        comparison = _compare_bundles(control_bundle, candidate_bundle, security_root)
        decision = classify_canary_comparison(
            control_image=control["image"],
            candidate_image=candidate_image,
            comparison=comparison,
        )
        receipt = {
            "schemaVersion": 1,
            "kind": "ordivon.browser-security-browserless-canary-r1",
            "standing": decision["standing"],
            "pass": decision["pass"],
            "controlImage": control["image"],
            "candidateImage": candidate_image,
            "expectedImageChange": decision["expectedImageChange"],
            "canaryInstance": CANARY_INSTANCE,
            "networkNamespace": control["networkNamespace"],
            "productionInstances": control["instances"],
            "securityRevision": subprocess.run(
                ["/usr/bin/git", "-C", str(security_root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip(),
            "controlManifestSha256": sha256_file(control_source),
            "controlBundleSha256": sha256_file(control_bundle),
            "candidateManifestSha256": sha256_file(candidate_source),
            "candidateBundleSha256": sha256_file(candidate_bundle),
            "comparison": comparison,
            "providerChallengeVisited": False,
            "providerSendAttempted": False,
            "productionMutationAttempted": False,
            "rootCauseEstablished": False,
        }
        receipt_path = artifact_root / "canary-receipt.json"
        receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.chmod(receipt_path, 0o600)
        return receipt
    finally:
        if temp is not None:
            temp.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-image", required=True)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--security-root", type=Path, default=SECURITY_ROOT)
    args = parser.parse_args()
    receipt = run_canary(
        candidate_image=args.candidate_image,
        artifact_dir=args.artifact_dir,
        security_root=args.security_root,
    )
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0 if receipt["pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
