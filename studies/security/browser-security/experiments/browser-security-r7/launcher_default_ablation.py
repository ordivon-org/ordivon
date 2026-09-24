#!/usr/bin/env python3
"""R7 neutral launcher-default ablation for Browser Security CF05/CF06.

Arms:
1. container-direct baseline using the R5 direct launch controls;
2. container-direct with the Browserless/Puppeteer managed launch defaults observed in R5;
3. current production Browserless carrier.

All arms use the same current Browserless image, exact Chromium bytes, Network-v2 namespace,
container runtime, TZ/LANG presentation environment, and neutral data:text/html page. This
experiment never visits ChatGPT or another protected provider, never interacts with a challenge,
never reads cookie values, and never crosses SEND.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import os
import shlex
import subprocess
import sys
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
    raise RuntimeError(f"cannot load R3 module: {R3_PATH}")
r3 = importlib.util.module_from_spec(R3_SPEC)
R3_SPEC.loader.exec_module(r3)

R5_PATH = ROOT / "experiments/browser-security-r5/container_direct_differential.py"
R5_SPEC = importlib.util.spec_from_file_location("browser_security_r5_container_direct", R5_PATH)
if R5_SPEC is None or R5_SPEC.loader is None:
    raise RuntimeError(f"cannot load R5 module: {R5_PATH}")
r5 = importlib.util.module_from_spec(R5_SPEC)
R5_SPEC.loader.exec_module(r5)

NETWORK_NAMESPACE = "nv2-browserless-prod"
ENDPOINT_ID = "chatgpt-carrier-11"
PRODUCTION_CONTAINER = "ordivon-browserless-11"
INSTALLED_QUADLET = pathlib.Path("/etc/containers/systemd/ordivon-browserless@.container")

BASELINE_CONTAINER = "ordivon-browser-security-r7-baseline"
LAUNCHER_CONTAINER = "ordivon-browser-security-r7-launcher"
BASELINE_PORT = 9235
LAUNCHER_PORT = 9236
BASELINE_DISPLAY = ":96"
LAUNCHER_DISPLAY = ":97"

# Frozen from the authoritative R5 Browser.getBrowserCommandLine observation after removing
# executable identity, dynamic remote-debugging/user-data-dir values, Chrome auto-added X11 flag
# switches, and about:blank. Duplicates are retained because launch ordering is part of the
# observed launcher surface.
BROWSERLESS_MANAGED_FLAGS = (
    "--allow-pre-commit-input",
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-component-extensions-with-background-pages",
    "--disable-crash-reporter",
    "--disable-default-apps",
    "--disable-dev-shm-usage",
    "--disable-hang-monitor",
    "--disable-infobars",
    "--disable-ipc-flooding-protection",
    "--disable-popup-blocking",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--disable-search-engine-choice-screen",
    "--disable-sync",
    "--enable-automation",
    "--export-tagged-pdf",
    "--force-color-profile=srgb",
    "--generate-pdf-document-outline",
    "--metrics-recording-only",
    "--no-first-run",
    "--password-store=basic",
    "--use-mock-keychain",
    "--disable-features=Translate,AcceptCHFrame,MediaRouter,OptimizationHints,WebUIReloadButton,WebUIOmniboxPopup,WebUIOmniboxAimPopup,ProcessPerSiteUpToMainFrameThreshold,IsolateSandboxedIframes,LocalNetworkAccessChecks",
    "--enable-features=PdfOopif",
    "--disable-extensions",
    "--no-sandbox",
    "--no-first-run",
    "--disable-component-update",
)

AUTO_OR_DYNAMIC_PREFIXES = (
    "--remote-debugging-port=",
    "--user-data-dir=",
)
AUTO_EXACT_ARGS = frozenset(
    {
        "--ozone-platform=x11",
        "--flag-switches-begin",
        "--flag-switches-end",
        "about:blank",
    }
)


def managed_flags_from_command_line(arguments: list[str]) -> list[str]:
    if not arguments:
        return []
    out: list[str] = []
    for index, value in enumerate(arguments):
        if index == 0 and value.endswith("/chrome"):
            continue
        if value in AUTO_EXACT_ARGS:
            continue
        if any(value.startswith(prefix) for prefix in AUTO_OR_DYNAMIC_PREFIXES):
            continue
        out.append(value)
    return out


def container_shell_command(
    *,
    debug_port: int,
    display: str,
    flags: tuple[str, ...],
) -> str:
    argv = [
        "$chrome",
        f"--remote-debugging-port={debug_port}",
        "--user-data-dir=/tmp/ordivon-r7-profile",
        *flags,
        "about:blank",
    ]
    quoted = " ".join(
        '"$chrome"' if row == "$chrome" else shlex.quote(row)
        for row in argv
    )
    return (
        "set -eu; "
        "chrome=$(find /usr/local/bin/playwright-browsers -type f "
        "-path '*/chrome-linux64/chrome' -print | sort); "
        "test $(printf '%s\\n' \"$chrome\" | sed '/^$/d' | wc -l) -eq 1; "
        f"Xvfb {shlex.quote(display)} -screen 0 1440x1000x24 -ac -nolisten tcp "
        ">/tmp/r7-xvfb.log 2>&1 & xvfb=$!; "
        "trap 'kill $xvfb 2>/dev/null || true' EXIT INT TERM; "
        f"DISPLAY={shlex.quote(display)} {quoted} "
        ">/tmp/r7-chrome.log 2>&1 & chrome_pid=$!; "
        "trap 'kill $chrome_pid 2>/dev/null || true; kill $xvfb 2>/dev/null || true' "
        "EXIT INT TERM; "
        "wait $chrome_pid"
    )


def start_arm_container(
    *,
    name: str,
    image: str,
    debug_port: int,
    display: str,
    flags: tuple[str, ...],
    presentation_environment: dict[str, str],
) -> subprocess.Popen[bytes]:
    if r5.podman_container_exists(name):
        raise RuntimeError(f"reserved R7 container already exists: {name}")
    env_args: list[str] = []
    for key in sorted(presentation_environment):
        if key not in {"TZ", "LANG"}:
            raise RuntimeError(f"unsafe R7 presentation environment key: {key}")
        env_args.extend(["--env", f"{key}={presentation_environment[key]}"])
    return subprocess.Popen(
        [
            "/usr/bin/podman",
            "run",
            "--rm",
            "--name",
            name,
            "--network",
            f"ns:/run/netns/{NETWORK_NAMESPACE}",
            *env_args,
            "--entrypoint",
            "/bin/sh",
            image,
            "-lc",
            container_shell_command(
                debug_port=debug_port,
                display=display,
                flags=flags,
            ),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def stop_arm(name: str, process: subprocess.Popen[bytes] | None) -> None:
    r5.stop_ephemeral_container(name)
    if process is None:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def collect_container_arm(
    pw,
    *,
    image: str,
    name: str,
    debug_port: int,
    display: str,
    flags: tuple[str, ...],
    presentation_environment: dict[str, str],
) -> dict[str, Any]:
    process: subprocess.Popen[bytes] | None = None
    try:
        process = start_arm_container(
            name=name,
            image=image,
            debug_port=debug_port,
            display=display,
            flags=flags,
            presentation_environment=presentation_environment,
        )
        r3.wait_json(f"http://127.0.0.1:{debug_port}/json/version")
        browser = pw.chromium.connect_over_cdp(
            f"http://127.0.0.1:{debug_port}", timeout=30_000
        )
        try:
            return r3.collect_arm(browser, create_new_page=False)
        finally:
            browser.close()
    finally:
        stop_arm(name, process)


def pair_summary(left: dict[str, Any], right: dict[str, Any]) -> dict[str, object]:
    return {
        "pageChangedPaths": r3.changed_paths(left["page"], right["page"]),
        "browserChangedPaths": r3.changed_paths(
            r5.normalized_browser_view(left["browser"]),
            r5.normalized_browser_view(right["browser"]),
        ),
        "managedLauncherFlagsEqual": (
            managed_flags_from_command_line(left["browser"]["commandLineArguments"])
            == managed_flags_from_command_line(right["browser"]["commandLineArguments"])
        ),
        "leftTargetTypeCounts": left["browser"]["targetTypeCounts"],
        "rightTargetTypeCounts": right["browser"]["targetTypeCounts"],
        "leftGeometry": {
            "inner": left["page"]["windowInner"],
            "outer": left["page"]["windowOuter"],
        },
        "rightGeometry": {
            "inner": right["page"]["windowInner"],
            "outer": right["page"]["windowOuter"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    if not INSTALLED_QUADLET.is_file():
        raise SystemExit("installed Browserless Quadlet missing")
    image = r5.current_image(INSTALLED_QUADLET.read_text(encoding="utf-8"))
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

    r5.require_ports_free((BASELINE_PORT, LAUNCHER_PORT))
    for name in (BASELINE_CONTAINER, LAUNCHER_CONTAINER):
        if r5.podman_container_exists(name):
            raise SystemExit(f"reserved R7 container exists: {name}")

    presentation_environment = r5.production_presentation_environment(PRODUCTION_CONTAINER)
    production_digest = r3.browserless_binary_digest(PRODUCTION_CONTAINER)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        baseline_arm = collect_container_arm(
            pw,
            image=image,
            name=BASELINE_CONTAINER,
            debug_port=BASELINE_PORT,
            display=BASELINE_DISPLAY,
            flags=tuple(r5.DIRECT_COMMON_ARGS),
            presentation_environment=presentation_environment,
        )
        launcher_arm = collect_container_arm(
            pw,
            image=image,
            name=LAUNCHER_CONTAINER,
            debug_port=LAUNCHER_PORT,
            display=LAUNCHER_DISPLAY,
            flags=BROWSERLESS_MANAGED_FLAGS,
            presentation_environment=presentation_environment,
        )
        with _carrier_lease(cfg, endpoint.endpoint_id, blocking=False):
            if endpoint.sessions(timeout_seconds=3):
                raise RuntimeError(f"endpoint became busy: {ENDPOINT_ID}")
            browserless = pw.chromium.connect_over_cdp(
                endpoint.authenticated_connection_endpoint(timeout_ms=90_000),
                timeout=30_000,
            )
            try:
                browserless_arm = r3.collect_arm(browserless, create_new_page=True)
            finally:
                browserless.close()

    observed_browserless_flags = managed_flags_from_command_line(
        browserless_arm["browser"]["commandLineArguments"]
    )
    if observed_browserless_flags != list(BROWSERLESS_MANAGED_FLAGS):
        raise RuntimeError("production Browserless managed launch surface drifted from frozen R7 control")

    baseline_flags = managed_flags_from_command_line(
        baseline_arm["browser"]["commandLineArguments"]
    )
    launcher_flags = managed_flags_from_command_line(
        launcher_arm["browser"]["commandLineArguments"]
    )
    if launcher_flags != list(BROWSERLESS_MANAGED_FLAGS):
        raise RuntimeError("R7 launcher-ablation arm did not realize frozen Browserless defaults")

    output = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-neutral-launcher-ablation-r7",
        "date": "2026-09-18",
        "standing": "NEUTRAL_LAUNCHER_ATTRIBUTION_ONLY_ROOT_CAUSE_OPEN",
        "safetyBoundary": {
            "protectedProviderVisited": False,
            "challengeInteracted": False,
            "cookieValuesRead": False,
            "providerSendAttempted": False,
        },
        "controls": {
            "networkNamespace": NETWORK_NAMESPACE,
            "browserlessImage": image,
            "chromiumDigest": production_digest,
            "presentationEnvironment": presentation_environment,
            "neutralPage": "data:text/html",
            "frozenBrowserlessManagedFlags": list(BROWSERLESS_MANAGED_FLAGS),
            "baselineManagedFlags": baseline_flags,
            "launcherManagedFlags": launcher_flags,
            "productionBrowserlessManagedFlags": observed_browserless_flags,
        },
        "arms": {
            "containerDirectBaseline": baseline_arm,
            "containerDirectLauncherMatched": launcher_arm,
            "browserlessCurrent": browserless_arm,
        },
        "pairwise": {
            "baselineToLauncherMatched": pair_summary(baseline_arm, launcher_arm),
            "launcherMatchedToBrowserless": pair_summary(launcher_arm, browserless_arm),
            "baselineToBrowserless": pair_summary(baseline_arm, browserless_arm),
        },
        "interpretationGuard": {
            "providerCausalityEstablished": False,
            "rootCauseEstablished": False,
            "challengeOutcomeUsedAsDetectorOracle": False,
            "note": (
                "Launcher-matched attribution is neutral and local. A residual difference between "
                "launcher-matched direct Chromium and Browserless is associated with service/control "
                "lifecycle or window/target management, not proven provider visibility."
            ),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output["pairwise"], sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
