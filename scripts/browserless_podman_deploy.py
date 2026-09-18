#!/usr/bin/env python3
"""Converge the minimal host-side Podman/Quadlet objects for Browserless carriers.

The container runtime and Quadlet are upstream Podman authority. This helper only installs one
repo-owned Quadlet, imports one existing local token as a Podman secret, and seeds persistent
Chromium user-data roots from quiescent authenticated templates. Browserless owns its temporary
session DATA_DIR; the mounted authenticated root is selected explicitly through launch.userDataDir.
It does not install packages and does not mutate network namespaces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import secrets
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_SOURCE_ROOT = Path("/opt/ordivon/agent-automation/current")


def runtime_source_root() -> Path:
    explicit = os.environ.get("ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT")
    if explicit:
        return Path(explicit).resolve()
    if PRODUCTION_SOURCE_ROOT.exists():
        return PRODUCTION_SOURCE_ROOT.resolve()
    return ROOT


QUADLET_SOURCE = ROOT / "containers/ordivon-browserless@.container"
QUADLET_DEST = Path("/etc/containers/systemd/ordivon-browserless@.container")
OPERATOR_PROXY_SOURCE = ROOT / "systemd/ordivon-browserless-operator-proxy@.service"
OPERATOR_PROXY_DEST = Path("/etc/systemd/system/ordivon-browserless-operator-proxy@.service")
DISPLAY_SOURCE = ROOT / "systemd/ordivon-browserless-display@.service"
DISPLAY_DEST = Path("/etc/systemd/system/ordivon-browserless-display@.service")
IDLE_REAPER_SOURCE = ROOT / "systemd/ordivon-browserless-idle-reaper.service"
IDLE_REAPER_DEST = Path("/etc/systemd/system/ordivon-browserless-idle-reaper.service")
IDLE_REAPER_TIMER_SOURCE = ROOT / "systemd/ordivon-browserless-idle-reaper.timer"
IDLE_REAPER_TIMER_DEST = Path("/etc/systemd/system/ordivon-browserless-idle-reaper.timer")
HUMAN_VNC_SOURCE = ROOT / "systemd/ordivon-browserless-human-vnc@.service"
HUMAN_VNC_DEST = Path("/etc/systemd/system/ordivon-browserless-human-vnc@.service")
HUMAN_WEB_SOURCE = ROOT / "systemd/ordivon-browserless-human-web@.service"
HUMAN_WEB_DEST = Path("/etc/systemd/system/ordivon-browserless-human-web@.service")
BROWSER_AGENT_TARGET_SOURCE = ROOT / "systemd/ordivon-browser-agent.target"
BROWSER_AGENT_TARGET_DEST = Path("/etc/systemd/system/ordivon-browser-agent.target")
TOKEN_FILE = Path("/etc/ordivon/browserless.token")
DATA_ROOT = Path("/var/lib/ordivon/browserless")
CONFIG_FILE = Path("/etc/ordivon/agent-automation-browserless.json")
BROWSER_USE_CONFIG_FILE = Path("/etc/ordivon/browser-use-browserless.json")
CHATGPT_INSTANCES = (11, 12, 13)
BROWSER_AGENT_INSTANCES = (21,)
ALL_BROWSERLESS_INSTANCES = CHATGPT_INSTANCES + BROWSER_AGENT_INSTANCES
PLAYWRIGHT_PYTHON = Path(
    "/root/.local/share/ordivon-workstation/conversation-relay-playwright-r4/.venv/bin/python"
)
BROWSERLESS_NETWORK_SECTION = "browserless_network"
QUADLET_NAMESPACE_TOKEN = "@NETWORK_NAMESPACE@"
QUADLET_AUTHORITY_SERVICE_TOKEN = "@NETWORK_AUTHORITY_SERVICE@"
DEFAULT_TEMPLATES = tuple(
    Path(f"/root/.cache/ordivon-market-r25-agent-profile-{n}") for n in range(1, 4)
)
NOVNC_ROOT = Path("/opt/ordivon/external/novnc/1.7.0")
NOVNC_SOURCE_SHA256 = "b1003a11b6e6e8d8f7f5e5586daae7f8ca651d8aee0aa155ff9ac841c48f52c6"
WEBSOCKIFY_ROOT = Path("/opt/ordivon/external/websockify/0.13.0")
WEBSOCKIFY_SOURCE_SHA256 = "9969731116653226c4c499a8a50712c8f3f7c105c615ead7ebc6ae781f0ba954"
WEBSOCKIFY_EQUIPMENT_ID = "browserless-websockify-0-13-0"
WEBSOCKIFY_EXECUTABLE_TOKEN = "@WEBSOCKIFY_EXECUTABLE@"
EQUIPMENT_BINDING = Path("/root/tools/bin/equipment-binding")
SINGLETONS = {"SingletonLock", "SingletonCookie", "SingletonSocket"}
SKIP_DIRS = {"Cache", "Code Cache", "GPUCache", "GrShaderCache", "ShaderCache"}


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run(
    args: list[str], *, input_bytes: bytes | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(args, input=input_bytes, capture_output=True, check=check)


def systemd_unit_is_masked(unit: str) -> bool:
    """Observe an operator-owned systemd mask without changing it.

    Instance masks are a higher-level workstation policy boundary. Deployment may converge
    templates and enabled lanes, but it must not silently resurrect a deliberately masked lane.
    """
    proc = run(["/usr/bin/systemctl", "is-enabled", unit], check=False)
    raw = proc.stdout or b""
    text = raw.decode(errors="replace") if isinstance(raw, bytes) else str(raw)
    return text.strip() == "masked"


def browser_agent_instance_masked(instance: int) -> bool:
    return any(
        systemd_unit_is_masked(unit)
        for unit in (
            f"ordivon-browserless@{instance}.service",
            f"ordivon-browserless-display@{instance}.service",
            f"ordivon-browserless-operator-proxy@{instance}.service",
        )
    )


def resolve_network_binding(
    contract_path: Path = ROOT / "config/agent-automation.toml",
    *,
    receipt_path: Path | None = None,
    netns_root: Path = Path("/run/netns"),
    check_service: bool = True,
) -> dict:
    """Resolve the graduated Network v2 Browserless production authority.

    Browserless consumes one explicit Network v2 namespace/target.  The cutover
    receipt supplies generation truth; legacy Surfpath/ExteriorAnchor state is not
    eligible authority after graduation.
    """
    contract = tomllib.loads(contract_path.read_text(encoding="utf-8"))
    raw = (contract.get("agent_automation") or {}).get(BROWSERLESS_NETWORK_SECTION) or {}
    if raw.get("kind") != "network-v2":
        raise RuntimeError("Browserless network authority must be network-v2")
    name = str(raw.get("name") or "")
    namespace = str(raw.get("namespace") or "")
    service = str(raw.get("service_unit") or "")
    configured_receipt = Path(str(raw.get("receipt") or ""))
    if name != "browserless-prod":
        raise RuntimeError("Browserless Network v2 authority name mismatch")
    if not namespace or "/" in namespace or any(ch.isspace() for ch in namespace):
        raise RuntimeError("Browserless Network v2 namespace is invalid")
    if not service.endswith(".target") or "/" in service or any(ch.isspace() for ch in service):
        raise RuntimeError("Browserless Network v2 service unit is invalid")
    rp = receipt_path or configured_receipt
    if not rp.is_absolute():
        raise RuntimeError("Browserless Network v2 receipt path must be absolute")
    try:
        receipt = json.loads(rp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Browserless Network v2 production receipt unavailable: {rp}"
        ) from error
    generation = receipt.get("generationDigest")
    if receipt.get("schemaVersion") != 1 or receipt.get("standing") != "PRODUCTION_CUTOVER_PASS":
        raise RuntimeError("Browserless Network v2 production receipt is not graduated")
    if (
        not isinstance(generation, str)
        or not generation.startswith("sha256:")
        or len(generation) != 71
    ):
        raise RuntimeError("Browserless Network v2 receipt has no valid generation digest")
    if not (netns_root / namespace).exists():
        raise RuntimeError(f"Browserless Network v2 namespace is absent: {namespace}")
    if check_service:
        proc = run(["/usr/bin/systemctl", "is-active", service], check=False)
        if proc.returncode != 0 or proc.stdout.decode(errors="replace").strip() != "active":
            raise RuntimeError(f"Browserless Network v2 authority is not active: {service}")
    return {
        "kind": "network-v2",
        "name": name,
        "namespace": namespace,
        "generationDigest": generation,
        "serviceUnit": service,
        "receiptPath": str(rp),
    }


def render_quadlet(binding: dict) -> str:
    network_namespace = binding["namespace"]
    service = binding["serviceUnit"]
    if "/" in network_namespace or any(ch.isspace() for ch in network_namespace):
        raise RuntimeError("invalid Browserless network namespace")
    if (
        not isinstance(service, str)
        or not service.endswith((".service", ".target"))
        or "/" in service
        or any(ch.isspace() for ch in service)
    ):
        raise RuntimeError("invalid Browserless network authority service unit")
    text = QUADLET_SOURCE.read_text(encoding="utf-8")
    if text.count(QUADLET_NAMESPACE_TOKEN) != 1 or text.count(QUADLET_AUTHORITY_SERVICE_TOKEN) != 2:
        raise RuntimeError("Browserless Network v2 Quadlet authority tokens are malformed")
    return text.replace(QUADLET_NAMESPACE_TOKEN, network_namespace).replace(
        QUADLET_AUTHORITY_SERVICE_TOKEN, service
    )


def render_operator_proxy(binding: dict) -> str:
    text = OPERATOR_PROXY_SOURCE.read_text(encoding="utf-8")
    if text.count(QUADLET_NAMESPACE_TOKEN) != 1 or text.count(QUADLET_AUTHORITY_SERVICE_TOKEN) != 2:
        raise RuntimeError("Browserless Network v2 operator proxy authority tokens are malformed")
    return text.replace(QUADLET_NAMESPACE_TOKEN, binding["namespace"]).replace(
        QUADLET_AUTHORITY_SERVICE_TOKEN, binding["serviceUnit"]
    )


def resolve_websockify_binding(equipment_binding: Path = EQUIPMENT_BINDING) -> dict:
    """Consume the Workstation v2 compatibility binding carrier without importing its owner source."""
    proc = run(
        [str(equipment_binding), "managed", "--equipment-id", WEBSOCKIFY_EQUIPMENT_ID], check=False
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).decode(errors="replace").strip()[:1000]
        raise RuntimeError(
            f"Browserless websockify binding carrier failed: {detail or f'rc={proc.returncode}'}"
        )
    try:
        binding = json.loads(proc.stdout.decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("Browserless websockify binding carrier returned non-JSON") from error
    if not isinstance(binding, dict):
        raise RuntimeError("Browserless websockify binding carrier returned a non-object")
    if binding.get("state") != "AVAILABLE":
        raise RuntimeError("Browserless websockify managed equipment is not available")
    if binding.get("executionTarget") != "local_linux":
        raise RuntimeError("Browserless websockify managed equipment must target local_linux")
    executable = Path(str(binding.get("executable") or "")).resolve()
    root = WEBSOCKIFY_ROOT.resolve()
    try:
        executable.relative_to(root)
    except ValueError as error:
        raise RuntimeError(
            "Browserless websockify binding is outside the pinned source root"
        ) from error
    return binding


def render_human_web_unit(websockify_binding: dict | None = None) -> str:
    binding = websockify_binding or resolve_websockify_binding()
    executable = str(binding.get("executable") or "")
    if not executable.startswith("/") or any(ch.isspace() for ch in executable):
        raise RuntimeError("Browserless websockify binding has unsafe systemd executable path")
    text = HUMAN_WEB_SOURCE.read_text(encoding="utf-8")
    if text.count(WEBSOCKIFY_EXECUTABLE_TOKEN) != 1:
        raise RuntimeError("Browserless human-web unit executable token is malformed")
    return text.replace(WEBSOCKIFY_EXECUTABLE_TOKEN, executable)


def _write_if_changed(path: Path, raw: bytes, mode: int) -> bool:
    if path.is_file() and path.read_bytes() == raw:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(raw)
    os.chmod(tmp, mode)
    os.replace(tmp, path)
    return True


def network_binding_state(binding: dict) -> dict:
    expected_config = (json.dumps(render_config(binding), sort_keys=True, indent=2) + "\n").encode()
    expected_browser_use_config = (
        json.dumps(render_browser_use_config(binding), sort_keys=True, indent=2) + "\n"
    ).encode()
    expected_quadlet = render_quadlet(binding).encode()
    expected_operator_proxy = render_operator_proxy(binding).encode()
    return {
        "authority": {k: binding[k] for k in ("kind", "name", "generationDigest", "serviceUnit")},
        "namespace": binding["namespace"],
        "configCurrent": CONFIG_FILE.is_file() and CONFIG_FILE.read_bytes() == expected_config,
        "browserUseConfigCurrent": BROWSER_USE_CONFIG_FILE.is_file()
        and BROWSER_USE_CONFIG_FILE.read_bytes() == expected_browser_use_config,
        "quadletCurrent": QUADLET_DEST.is_file() and QUADLET_DEST.read_bytes() == expected_quadlet,
        "operatorProxyCurrent": OPERATOR_PROXY_DEST.is_file()
        and OPERATOR_PROXY_DEST.read_bytes() == expected_operator_proxy,
    }


def refresh_network_binding(binding: dict) -> list[str]:
    changed: list[str] = []
    config_raw = (json.dumps(render_config(binding), sort_keys=True, indent=2) + "\n").encode()
    if _write_if_changed(CONFIG_FILE, config_raw, 0o600):
        changed.append(str(CONFIG_FILE))
    browser_use_raw = (
        json.dumps(render_browser_use_config(binding), sort_keys=True, indent=2) + "\n"
    ).encode()
    if _write_if_changed(BROWSER_USE_CONFIG_FILE, browser_use_raw, 0o600):
        changed.append(str(BROWSER_USE_CONFIG_FILE))
    reload_needed = False
    if _write_if_changed(QUADLET_DEST, render_quadlet(binding).encode(), 0o644):
        changed.append(str(QUADLET_DEST))
        reload_needed = True
    if _write_if_changed(OPERATOR_PROXY_DEST, render_operator_proxy(binding).encode(), 0o644):
        changed.append(str(OPERATOR_PROXY_DEST))
        reload_needed = True
    if reload_needed:
        run(["/usr/bin/systemctl", "daemon-reload"])
    return changed


def token(*, create: bool = False) -> bytes:
    if not TOKEN_FILE.is_file() and create:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(secrets.token_urlsafe(32) + "\n", encoding="utf-8")
        os.chmod(TOKEN_FILE, 0o600)
    raw = TOKEN_FILE.read_bytes().strip()
    if len(raw) < 20 or any(ch in raw for ch in b"\r\n\t "):
        raise RuntimeError("Browserless token must be a single opaque value of at least 20 bytes")
    return raw


def render_config(binding: dict | None = None) -> dict:
    binding = binding or resolve_network_binding()
    source_root = runtime_source_root()
    network_namespace = binding["namespace"]
    endpoints = []
    for instance in CHATGPT_INSTANCES:
        endpoints.append(
            {
                "id": f"chatgpt-carrier-{instance}",
                "websocketEndpoint": f"ws://127.0.0.1:30{instance}/chromium",
                "httpEndpoint": f"http://127.0.0.1:30{instance}",
                "tokenFile": str(TOKEN_FILE),
                "networkNamespace": network_namespace,
                "operatorHttpEndpoint": f"http://127.0.0.1:131{instance}",
                "userDataDir": "/data",
                "headless": False,
                "serviceUnit": f"ordivon-browserless@{instance}.service",
            }
        )
    return {
        "schemaVersion": 1,
        "stateRoot": "/root/.local/state/ordivon-workstation/agent-automation/state",
        "playwrightPython": str(PLAYWRIGHT_PYTHON),
        "browserlessSubmitScript": str(
            source_root / "scripts/playwright_browserless_chatgpt_submit.py"
        ),
        "browserlessReconcileScript": str(
            source_root / "scripts/playwright_browserless_binding_reconcile.py"
        ),
        "browserlessTurnScript": str(source_root / "scripts/playwright_browserless_turn_once.py"),
        "browserlessPreflightScript": str(
            source_root / "scripts/playwright_browserless_provider_preflight.py"
        ),
        "browserlessHumanResumeScript": str(
            source_root / "scripts/playwright_browserless_human_resume.py"
        ),
        "temporalPython": "/root/.local/share/ordivon-workstation/temporal-agent-automation/.venv/bin/python",
        "temporalLaunchScript": str(source_root / "scripts/temporal_agent_automation_launch.py"),
        "temporalAddress": "127.0.0.1:17233",
        "temporalNamespace": "default",
        "temporalTaskQueue": "ordivon-agent-automation",
        "waitStableSeconds": 150,
        "browserlessReconnectMs": 60000,
        "browserlessHumanHandoffMs": 300000,
        "browserlessHumanHandoffMode": "self-hosted-vnc",
        "browserlessSessionTimeoutMs": 480000,
        "browserlessStartTimeoutSeconds": 20,
        "browserlessIdleTtlSeconds": 900,
        "browserlessWarmEndpointIds": ["chatgpt-carrier-11"],
        "browserNetworkAuthority": {
            k: binding[k] for k in ("kind", "name", "generationDigest", "serviceUnit")
        },
        "browserSubstrate": {"kind": "browserless", "endpoints": endpoints},
    }


def resolve_browser_use_executable() -> str:
    """Resolve the installed Browser Use CLI without assuming the uv shim still exists."""
    candidates = []
    on_path = shutil.which("browser-use")
    if on_path:
        candidates.append(Path(on_path))
    candidates.append(Path.home() / ".local/share/uv/tools/browser-use/bin/browser-use")
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file() and os.access(resolved, os.X_OK):
            return str(resolved)
    raise RuntimeError("Browser Use executable is not materialized")


def render_browser_use_config(
    binding: dict | None = None, *, browser_use_executable: str | None = None
) -> dict:
    """Render the isolated Browser Use Browserless pool.

    This pool is deliberately separate from Agent Automation's ChatGPT carriers: generic web
    tasks must not consume authenticated ChatGPT profiles or Birth capacity.
    """
    binding = binding or resolve_network_binding()
    executable = browser_use_executable or resolve_browser_use_executable()
    network_namespace = binding["namespace"]
    endpoints = []
    for instance in BROWSER_AGENT_INSTANCES:
        endpoints.append(
            {
                "id": f"browser-agent-{instance}",
                "websocketEndpoint": f"ws://127.0.0.1:30{instance}/chromium",
                "httpEndpoint": f"http://127.0.0.1:30{instance}",
                "tokenFile": str(TOKEN_FILE),
                "networkNamespace": network_namespace,
                "operatorHttpEndpoint": f"http://127.0.0.1:131{instance}",
                "userDataDir": "/data",
                "headless": False,
                "serviceUnit": f"ordivon-browserless@{instance}.service",
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browser-use-browserless-pool",
        "browserUseExecutable": executable,
        "browserUseSkill": "/root/.agents/skills/browser-use/SKILL.md",
        "browserNetworkAuthority": {
            k: binding[k] for k in ("kind", "name", "generationDigest", "serviceUnit")
        },
        "browserSubstrate": {"kind": "browserless", "endpoints": endpoints},
    }


def source_quiescent(path: Path) -> bool:
    return path.is_dir() and not any(
        (path / name).exists() or (path / name).is_symlink() for name in SINGLETONS
    )


def copy_profile(source: Path, destination: Path) -> None:
    if destination.exists():
        return
    if not source_quiescent(source):
        raise RuntimeError(f"authenticated profile template is not quiescent: {source}")

    def ignore(directory: str, names: list[str]) -> set[str]:
        skipped = {name for name in names if name in SINGLETONS or name in SKIP_DIRS}
        return skipped

    shutil.copytree(source, destination, symlinks=True, ignore=ignore)


def secret_exists() -> bool:
    return (
        run(
            ["/usr/bin/podman", "secret", "inspect", "ordivon-browserless-token"], check=False
        ).returncode
        == 0
    )


def human_transport_materialization(websockify_binding: dict | None = None) -> dict:
    def marker(root: Path) -> str | None:
        path = root / ".ordivon-source-sha256"
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError:
            return None

    novnc_marker = marker(NOVNC_ROOT)
    websockify_marker = marker(WEBSOCKIFY_ROOT)
    binding_error = None
    if websockify_binding is None:
        try:
            websockify_binding = resolve_websockify_binding()
        except Exception as error:
            binding_error = str(error)
            websockify_binding = None
    executable = Path(str((websockify_binding or {}).get("executable") or ""))
    try:
        binding_inside_root = bool(executable) and executable.resolve().is_relative_to(
            WEBSOCKIFY_ROOT.resolve()
        )
    except OSError:
        binding_inside_root = False
    value = {
        "novncRoot": str(NOVNC_ROOT),
        "novncSourceDigestMatches": novnc_marker == NOVNC_SOURCE_SHA256,
        "novncEntryPresent": (NOVNC_ROOT / "vnc.html").is_file(),
        "websockifyRoot": str(WEBSOCKIFY_ROOT),
        "websockifySourceDigestMatches": websockify_marker == WEBSOCKIFY_SOURCE_SHA256,
        "websockifyEquipmentId": WEBSOCKIFY_EQUIPMENT_ID,
        "websockifyBindingAvailable": websockify_binding is not None,
        "websockifyBindingError": binding_error,
        "websockifyBindingDigest": (websockify_binding or {}).get("bindingDigest"),
        "websockifyExecutable": (websockify_binding or {}).get("executable"),
        "websockifyExecutableDigest": (websockify_binding or {}).get("executableDigest"),
        "websockifyExecutionTarget": (websockify_binding or {}).get("executionTarget"),
        "websockifyBindingInsidePinnedSource": binding_inside_root,
    }
    value["current"] = (
        all(
            value[key] is True
            for key in (
                "novncSourceDigestMatches",
                "novncEntryPresent",
                "websockifySourceDigestMatches",
                "websockifyBindingAvailable",
                "websockifyBindingInsidePinnedSource",
            )
        )
        and value["websockifyExecutionTarget"] == "local_linux"
    )
    return value


def plan(binding: dict | None = None) -> dict:
    binding = binding or resolve_network_binding()
    binding_state = network_binding_state(binding)
    return {
        "schemaVersion": 1,
        "kind": "ordivon.browserless-podman-deployment-plan",
        "podmanPresent": Path("/usr/bin/podman").is_file(),
        "quadletSourceDigest": digest(QUADLET_SOURCE),
        "networkAuthority": {
            k: binding[k] for k in ("kind", "name", "generationDigest", "serviceUnit")
        },
        "networkNamespace": binding["namespace"],
        "quadletInstalled": binding_state["quadletCurrent"],
        "operatorProxyInstalled": binding_state["operatorProxyCurrent"],
        "displayUnitInstalled": DISPLAY_DEST.is_file()
        and DISPLAY_DEST.read_bytes() == DISPLAY_SOURCE.read_bytes(),
        "humanVncUnitInstalled": HUMAN_VNC_DEST.is_file()
        and HUMAN_VNC_DEST.read_bytes() == HUMAN_VNC_SOURCE.read_bytes(),
        "humanWebUnitInstalled": HUMAN_WEB_DEST.is_file()
        and HUMAN_WEB_DEST.read_text(encoding="utf-8") == render_human_web_unit(),
        "browserAgentTargetInstalled": BROWSER_AGENT_TARGET_DEST.is_file()
        and BROWSER_AGENT_TARGET_DEST.read_bytes() == BROWSER_AGENT_TARGET_SOURCE.read_bytes(),
        "legacyNetworkRecoveryRetired": True,
        "networkAuthorityReceipt": binding.get("receiptPath"),
        "tokenPresent": TOKEN_FILE.is_file(),
        "configInstalled": binding_state["configCurrent"],
        "browserUseConfigInstalled": binding_state["browserUseConfigCurrent"],
        "podmanSecretPresent": Path("/usr/bin/podman").is_file() and secret_exists(),
        "humanInteractionSubstrate": human_transport_materialization(),
        "profiles": [
            {
                "instance": 10 + i,
                "source": str(source),
                "sourceQuiescent": source_quiescent(source),
                "profileDirPresent": (DATA_ROOT / str(10 + i)).is_dir(),
            }
            for i, source in enumerate(DEFAULT_TEMPLATES, start=1)
        ],
        "browserAgents": [
            {
                "instance": instance,
                "id": f"browser-agent-{instance}",
                "profileDirPresent": (DATA_ROOT / str(instance)).is_dir(),
            }
            for instance in BROWSER_AGENT_INSTANCES
        ],
    }


def prepare(binding: dict | None = None) -> dict:
    binding = binding or resolve_network_binding()
    token(create=True)
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(render_config(binding), sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    os.chmod(CONFIG_FILE, 0o600)
    BROWSER_USE_CONFIG_FILE.write_text(
        json.dumps(render_browser_use_config(binding), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(BROWSER_USE_CONFIG_FILE, 0o600)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    for i, source in enumerate(DEFAULT_TEMPLATES, start=1):
        copy_profile(source, DATA_ROOT / str(10 + i))
    for instance in BROWSER_AGENT_INSTANCES:
        (DATA_ROOT / str(instance)).mkdir(parents=True, exist_ok=True)
    return plan(binding)


def apply() -> dict:
    binding = resolve_network_binding()
    prepare(binding)
    if not Path("/usr/bin/podman").is_file():
        raise RuntimeError("Podman is not installed; package authority must be converged first")
    raw = token()
    human = human_transport_materialization()
    if human.get("current") is not True:
        raise RuntimeError(
            "pinned noVNC/websockify human interaction substrate is absent or changed"
        )
    refresh_network_binding(binding)
    if not secret_exists():
        run(
            ["/usr/bin/podman", "secret", "create", "ordivon-browserless-token", "-"],
            input_bytes=raw,
        )
    for source, destination in (
        (DISPLAY_SOURCE, DISPLAY_DEST),
        (IDLE_REAPER_SOURCE, IDLE_REAPER_DEST),
        (IDLE_REAPER_TIMER_SOURCE, IDLE_REAPER_TIMER_DEST),
        (HUMAN_VNC_SOURCE, HUMAN_VNC_DEST),
        (BROWSER_AGENT_TARGET_SOURCE, BROWSER_AGENT_TARGET_DEST),
    ):
        if not destination.is_file() or destination.read_bytes() != source.read_bytes():
            destination.write_bytes(source.read_bytes())
            os.chmod(destination, 0o644)
    human_web_raw = render_human_web_unit().encode()
    if not HUMAN_WEB_DEST.is_file() or HUMAN_WEB_DEST.read_bytes() != human_web_raw:
        HUMAN_WEB_DEST.write_bytes(human_web_raw)
        os.chmod(HUMAN_WEB_DEST, 0o644)
    run(["/usr/bin/systemctl", "daemon-reload"])
    run(["/usr/bin/systemctl", "enable", "--now", "ordivon-browserless-idle-reaper.timer"])
    # ChatGPT carrier displays are lifecycle dependencies, not boot-time services. Generic
    # browser-agent displays remain static because browser-agent.target is intentionally warm.
    run(
        [
            "/usr/bin/systemctl",
            "disable",
            *[
                f"ordivon-browserless-display@{instance}.service"
                for instance in CHATGPT_INSTANCES
            ],
        ],
        check=False,
    )
    active_browser_agent_instances = tuple(
        instance
        for instance in BROWSER_AGENT_INSTANCES
        if not browser_agent_instance_masked(instance)
    )
    if active_browser_agent_instances:
        run(
            [
                "/usr/bin/systemctl",
                "enable",
                "--now",
                *[
                    f"ordivon-browserless-display@{instance}.service"
                    for instance in active_browser_agent_instances
                ],
            ]
        )
    run(
        [
            "/usr/bin/systemctl",
            "enable",
            "--now",
            *[
                f"ordivon-browserless-operator-proxy@{instance}.service"
                for instance in CHATGPT_INSTANCES + active_browser_agent_instances
            ],
        ]
    )
    if active_browser_agent_instances == BROWSER_AGENT_INSTANCES:
        run(["/usr/bin/systemctl", "enable", "--now", "ordivon-browser-agent.target"])
    else:
        run(
            ["/usr/bin/systemctl", "disable", "--now", "ordivon-browser-agent.target"],
            check=False,
        )
    return plan(binding)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prepare", action="store_true")
    p.add_argument("--apply", action="store_true")
    a = p.parse_args()
    if a.apply and a.prepare:
        p.error("choose at most one mutation mode")
    if a.apply:
        result = apply()
    elif a.prepare:
        result = prepare()
    else:
        result = plan()
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
