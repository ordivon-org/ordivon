#!/usr/bin/env python3
"""R5 neutral three-arm attribution for Browser Security CF05/CF06.

Arms:
1. host-direct Chromium;
2. container-direct Chromium using the exact current Browserless image;
3. current production Browserless carrier.

The process must be launched inside the production Browserless Network-v2 namespace. Both direct
arms use identical Chromium launch arguments and an empty profile. The Browserless arm is read-only
under the existing carrier lease. The experiment visits only a data:text/html neutral page, never
visits ChatGPT or another protected provider, never interacts with a challenge, never reads cookie
values, and never crosses SEND.

This is an attribution experiment, not an evasion or provider-admission tool.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
from typing import Any

HARNESS_CURRENT = pathlib.Path(
    os.environ.get("ORDIVON_AGENT_AUTOMATION_SOURCE_ROOT", "/opt/ordivon/agent-automation/current")
)
HARNESS_SCRIPTS = HARNESS_CURRENT / "scripts"
if str(HARNESS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HARNESS_SCRIPTS))

from agent_automation_browserless import (  # noqa: E402
    BrowserlessAutomationConfig,
    _carrier_lease,
    _read_json,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]
R3_PATH = ROOT / "experiments/browser-security-r3/neutral_differential.py"
R3_SPEC = importlib.util.spec_from_file_location("browser_security_r3_neutral", R3_PATH)
if R3_SPEC is None or R3_SPEC.loader is None:
    raise RuntimeError(f"cannot load R3 observation module: {R3_PATH}")
r3 = importlib.util.module_from_spec(R3_SPEC)
R3_SPEC.loader.exec_module(r3)

HOST_CHROME = r3.CHROME
FONT_FAMILIES = r3.FONT_FAMILIES
NETWORK_NAMESPACE = "nv2-browserless-prod"
ENDPOINT_ID = "chatgpt-carrier-11"
PRODUCTION_CONTAINER = "ordivon-browserless-11"
INSTALLED_QUADLET = pathlib.Path("/etc/containers/systemd/ordivon-browserless@.container")

HOST_DISPLAY = ":195"
HOST_DEBUG_PORT = 9231
CONTAINER_DEBUG_PORT = 9232
CONTAINER_NAME = "ordivon-browser-security-r5-container-direct"
CONTAINER_DISPLAY = ":95"

DIRECT_COMMON_ARGS = (
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--enable-automation",
    "--window-size=1440,1000",
    "--no-first-run",
    "--no-default-browser-check",
)
IMAGE_RE = re.compile(r"^ghcr\.io/browserless/chromium@sha256:[0-9a-f]{64}$")


def current_image(raw: str) -> str:
    rows = [line.removeprefix("Image=") for line in raw.splitlines() if line.startswith("Image=")]
    if len(rows) != 1 or IMAGE_RE.fullmatch(rows[0]) is None:
        raise RuntimeError("installed Browserless Quadlet must contain one exact immutable image")
    return rows[0]


def direct_arguments(*, debug_port: int, profile: str) -> list[str]:
    return [
        f"--remote-debugging-port={debug_port}",
        f"--user-data-dir={profile}",
        *DIRECT_COMMON_ARGS,
        "about:blank",
    ]


def container_shell_command() -> str:
    # Keep host-direct and container-direct launch semantics aligned. Xvfb is inside the ephemeral
    # container so container filesystem/font/runtime effects are retained without touching host X11.
    args = " ".join(
        [
            f"--remote-debugging-port={CONTAINER_DEBUG_PORT}",
            "--user-data-dir=/tmp/ordivon-r5-profile",
            *DIRECT_COMMON_ARGS,
            "about:blank",
        ]
    )
    return (
        "set -eu; "
        "chrome=$(find /usr/local/bin/playwright-browsers -type f "
        "-path '*/chrome-linux64/chrome' -print | sort); "
        "test $(printf '%s\\n' \"$chrome\" | sed '/^$/d' | wc -l) -eq 1; "
        f"Xvfb {CONTAINER_DISPLAY} -screen 0 1440x1000x24 -ac -nolisten tcp "
        ">/tmp/r5-xvfb.log 2>&1 & xvfb=$!; "
        "trap 'kill $xvfb 2>/dev/null || true' EXIT INT TERM; "
        f"DISPLAY={CONTAINER_DISPLAY} \"$chrome\" {args} "
        ">/tmp/r5-chrome.log 2>&1 & chrome_pid=$!; "
        "trap 'kill $chrome_pid 2>/dev/null || true; kill $xvfb 2>/dev/null || true' "
        "EXIT INT TERM; "
        "wait $chrome_pid"
    )


def require_ports_free(ports: tuple[int, ...]) -> None:
    sockets: list[socket.socket] = []
    try:
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # A completed prior run may leave loopback connections in TIME_WAIT. That is not a
            # listening conflict and must not make the next neutral experiment fail spuriously.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
            sockets.append(sock)
    finally:
        for sock in sockets:
            sock.close()


def production_presentation_environment(container: str) -> dict[str, str]:
    proc = subprocess.run(
        [
            "/usr/bin/podman",
            "inspect",
            container,
            "--format",
            "{{range .Config.Env}}{{println .}}{{end}}",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    allowed = {"TZ", "LANG"}
    result: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in allowed:
            result[key] = value
    if "TZ" not in result:
        raise RuntimeError("production Browserless container lacks TZ presentation environment")
    return result


def normalized_browser_view(value: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(value))
    args = result.get("commandLineArguments")
    if isinstance(args, list) and args and isinstance(args[0], str) and args[0].endswith("/chrome"):
        args[0] = "<chromium-executable>"
    system = result.get("systemInfo")
    if isinstance(system, dict):
        command = system.get("commandLine")
        if (
            isinstance(command, list)
            and command
            and isinstance(command[0], str)
            and command[0].endswith("/chrome")
        ):
            command[0] = "<chromium-executable>"
    return result


def podman_container_exists(name: str) -> bool:
    return (
        subprocess.run(
            ["/usr/bin/podman", "container", "exists", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        ).returncode
        == 0
    )


def stop_ephemeral_container(name: str) -> None:
    if not podman_container_exists(name):
        return
    subprocess.run(
        ["/usr/bin/podman", "stop", "--time", "3", name],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    subprocess.run(
        ["/usr/bin/podman", "rm", "-f", name],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )


def start_container_direct(
    image: str, presentation_environment: dict[str, str]
) -> subprocess.Popen[bytes]:
    if podman_container_exists(CONTAINER_NAME):
        raise RuntimeError(f"reserved R5 container already exists: {CONTAINER_NAME}")
    env_args: list[str] = []
    for key in sorted(presentation_environment):
        if key not in {"TZ", "LANG"}:
            raise RuntimeError(f"unsafe R5 presentation environment key: {key}")
        env_args.extend(["--env", f"{key}={presentation_environment[key]}"])
    return subprocess.Popen(
        [
            "/usr/bin/podman",
            "run",
            "--rm",
            "--name",
            CONTAINER_NAME,
            "--network",
            f"ns:/run/netns/{NETWORK_NAMESPACE}",
            *env_args,
            "--entrypoint",
            "/bin/sh",
            image,
            "-lc",
            container_shell_command(),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def pair_differences(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    left_fonts: dict[str, str],
    right_fonts: dict[str, str],
) -> dict[str, object]:
    return {
        "pageChangedPaths": r3.changed_paths(left["page"], right["page"]),
        "browserChangedPaths": r3.changed_paths(
            normalized_browser_view(left["browser"]),
            normalized_browser_view(right["browser"]),
        ),
        "fontResolutionFamilies": [
            family for family in FONT_FAMILIES if left_fonts[family] != right_fonts[family]
        ],
        "canvasWidthFamilies": [
            family
            for family in FONT_FAMILIES
            if left["page"]["canvasTextWidths"][family]
            != right["page"]["canvasTextWidths"][family]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    if not HOST_CHROME.is_file():
        raise SystemExit(f"host direct Chromium missing: {HOST_CHROME}")
    if not INSTALLED_QUADLET.is_file():
        raise SystemExit(f"installed Browserless Quadlet missing: {INSTALLED_QUADLET}")

    image = current_image(INSTALLED_QUADLET.read_text(encoding="utf-8"))
    if (
        subprocess.run(
            ["/usr/bin/podman", "image", "exists", image],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        ).returncode
        != 0
    ):
        raise SystemExit("current Browserless image is not present locally")

    cfg = BrowserlessAutomationConfig.from_dict(
        _read_json("/etc/ordivon/agent-automation-browserless.json")
    )
    endpoint = next(
        (row for row in cfg.browserless_pool.endpoints if row.endpoint_id == ENDPOINT_ID),
        None,
    )
    if endpoint is None:
        raise SystemExit(f"missing endpoint: {ENDPOINT_ID}")
    if endpoint.network_namespace != NETWORK_NAMESPACE:
        raise SystemExit("endpoint Network-v2 namespace changed")
    if endpoint.sessions(timeout_seconds=3):
        raise SystemExit(f"endpoint busy: {ENDPOINT_ID}")

    require_ports_free((HOST_DEBUG_PORT, CONTAINER_DEBUG_PORT))
    if pathlib.Path("/tmp/.X11-unix/X195").exists():
        raise SystemExit("reserved R5 host Xvfb display :195 is already in use")
    if podman_container_exists(CONTAINER_NAME):
        raise SystemExit("reserved R5 container name already exists")

    host_digest = r3.sha256_file(HOST_CHROME)
    browserless_digest = r3.browserless_binary_digest(PRODUCTION_CONTAINER)
    host_fonts = {family: r3.font_resolution(None, family) for family in FONT_FAMILIES}
    browserless_fonts = {
        family: r3.font_resolution(PRODUCTION_CONTAINER, family) for family in FONT_FAMILIES
    }
    presentation_environment = production_presentation_environment(PRODUCTION_CONTAINER)

    xvfb = subprocess.Popen(
        [
            "/usr/bin/Xvfb",
            HOST_DISPLAY,
            "-screen",
            "0",
            "1440x1000x24",
            "-ac",
            "-nolisten",
            "tcp",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    host_direct: subprocess.Popen[bytes] | None = None
    container_direct: subprocess.Popen[bytes] | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="ordivon-cf-r5-host-direct-") as profile:
            env = dict(os.environ)
            env["DISPLAY"] = HOST_DISPLAY
            host_direct = subprocess.Popen(
                [str(HOST_CHROME), *direct_arguments(debug_port=HOST_DEBUG_PORT, profile=profile)],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            r3.wait_json(f"http://127.0.0.1:{HOST_DEBUG_PORT}/json/version")

            container_direct = start_container_direct(image, presentation_environment)
            r3.wait_json(f"http://127.0.0.1:{CONTAINER_DEBUG_PORT}/json/version")
            container_digest = r3.browserless_binary_digest(CONTAINER_NAME)
            container_fonts = {
                family: r3.font_resolution(CONTAINER_NAME, family) for family in FONT_FAMILIES
            }

            from playwright.sync_api import sync_playwright

            with _carrier_lease(cfg, endpoint.endpoint_id, blocking=False):
                if endpoint.sessions(timeout_seconds=3):
                    raise RuntimeError(f"endpoint became busy: {ENDPOINT_ID}")
                with sync_playwright() as pw:
                    host_browser = pw.chromium.connect_over_cdp(
                        f"http://127.0.0.1:{HOST_DEBUG_PORT}", timeout=30_000
                    )
                    try:
                        host_arm = r3.collect_arm(host_browser, create_new_page=False)
                    finally:
                        host_browser.close()

                    container_browser = pw.chromium.connect_over_cdp(
                        f"http://127.0.0.1:{CONTAINER_DEBUG_PORT}", timeout=30_000
                    )
                    try:
                        container_arm = r3.collect_arm(container_browser, create_new_page=False)
                    finally:
                        container_browser.close()

                    browserless = pw.chromium.connect_over_cdp(
                        endpoint.authenticated_connection_endpoint(timeout_ms=90_000),
                        timeout=30_000,
                    )
                    try:
                        browserless_arm = r3.collect_arm(browserless, create_new_page=True)
                    finally:
                        browserless.close()
    finally:
        if host_direct is not None:
            host_direct.terminate()
            try:
                host_direct.wait(timeout=5)
            except subprocess.TimeoutExpired:
                host_direct.kill()
                host_direct.wait(timeout=5)
        if container_direct is not None:
            stop_ephemeral_container(CONTAINER_NAME)
            try:
                container_direct.wait(timeout=5)
            except subprocess.TimeoutExpired:
                container_direct.kill()
                container_direct.wait(timeout=5)
        xvfb.terminate()
        try:
            xvfb.wait(timeout=5)
        except subprocess.TimeoutExpired:
            xvfb.kill()
            xvfb.wait(timeout=5)

    same_digest = host_digest == container_digest == browserless_digest
    output = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-neutral-attribution-r5",
        "date": "2026-09-18",
        "standing": "NEUTRAL_ATTRIBUTION_ONLY_ROOT_CAUSE_OPEN",
        "safetyBoundary": {
            "protectedProviderVisited": False,
            "challengeInteracted": False,
            "cookieValuesRead": False,
            "providerSendAttempted": False,
        },
        "controls": {
            "networkNamespace": NETWORK_NAMESPACE,
            "browserlessImage": image,
            "sameChromiumBinary": same_digest,
            "hostChromiumDigest": host_digest,
            "containerDirectChromiumDigest": container_digest,
            "browserlessChromiumDigest": browserless_digest,
            "directLaunchArgumentsMatched": True,
            "presentationEnvironmentMatched": presentation_environment,
            "webdriverMatchedByDesign": True,
            "neutralPage": "data:text/html",
        },
        "systemFontResolution": {
            "hostDirect": host_fonts,
            "containerDirect": container_fonts,
            "browserlessContainer": browserless_fonts,
        },
        "arms": {
            "hostDirect": host_arm,
            "containerDirect": container_arm,
            "browserlessCurrent": browserless_arm,
        },
        "pairwiseDifferences": {
            "hostToContainerDirect": pair_differences(
                host_arm,
                container_arm,
                left_fonts=host_fonts,
                right_fonts=container_fonts,
            ),
            "containerDirectToBrowserless": pair_differences(
                container_arm,
                browserless_arm,
                left_fonts=container_fonts,
                right_fonts=browserless_fonts,
            ),
            "hostDirectToBrowserless": pair_differences(
                host_arm,
                browserless_arm,
                left_fonts=host_fonts,
                right_fonts=browserless_fonts,
            ),
        },
        "interpretationGuard": {
            "providerCausalityEstablished": False,
            "challengeOutcomeUsedAsDetectorOracle": False,
            "containerRuntimeAttributionIsAssociational": True,
            "browserlessPathAttributionIsAssociational": True,
            "note": (
                "Host-to-container isolates container/runtime-associated presentation; "
                "container-to-Browserless isolates Browserless path-associated launch/control "
                "presentation while preserving the same image and Chromium bytes."
            ),
        },
    }
    if not same_digest:
        raise RuntimeError("R5 control failure: Chromium bytes differ across arms")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output["pairwiseDifferences"], sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
