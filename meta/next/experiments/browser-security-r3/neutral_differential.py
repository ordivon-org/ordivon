#!/usr/bin/env python3
"""Neutral direct-Chromium vs Browserless differential for CF05/CF06 coverage.

This experiment never visits ChatGPT or another protected provider, never interacts with a
challenge, never reads cookie values, and never crosses SEND. It deliberately launches direct
Chromium with --enable-automation so navigator.webdriver is matched to the current Browserless
route; the experiment then measures remaining control/runtime and cross-layer presentation
differences.

Run inside the production Browserless network namespace:

  nsenter --net=/run/netns/nv2-browserless-prod \
    <playwright-python> experiments/browser-security-r3/neutral_differential.py \
    --output evidence/browser-security/cloudflare-provider-security-exp-r3-20260918.json
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from typing import Any

HARNESS_CURRENT = pathlib.Path("/opt/ordivon/agent-automation/current")
HARNESS_SCRIPTS = HARNESS_CURRENT / "scripts"
if str(HARNESS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(HARNESS_SCRIPTS))

from agent_automation_browserless import (  # noqa: E402
    BrowserlessAutomationConfig,
    _carrier_lease,
    _read_json,
)

CHROME = pathlib.Path("/root/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome")
NETWORK_NAMESPACE = "nv2-browserless-prod"
ENDPOINT_ID = "chatgpt-carrier-11"
DISPLAY = ":193"
DEBUG_PORT = 9227
FONT_FAMILIES = (
    "Arial",
    "Segoe UI",
    "Noto Sans",
    "DejaVu Sans",
    "Liberation Sans",
    "Ubuntu",
    "Selawik",
    "Verdana",
)


def sha256_file(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def wait_json(url: str, timeout: float = 12.0) -> dict[str, Any]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                value = json.load(response)
            if isinstance(value, dict):
                return value
        except Exception:
            time.sleep(0.1)
    raise RuntimeError(f"timed out waiting for {url}")


def normalize_argument(value: str) -> str:
    replacements = (
        (r"^--remote-debugging-port=\d+$", "--remote-debugging-port=<ephemeral>"),
        (r"^--user-data-dir=.*$", "--user-data-dir=<profile>"),
    )
    for pattern, replacement in replacements:
        if re.match(pattern, value):
            return replacement
    return value


def normalize_command_line(value: object) -> list[str]:
    if isinstance(value, list):
        rows = [row for row in value if isinstance(row, str)]
    elif isinstance(value, str):
        rows = value.split()
    else:
        return []
    return [normalize_argument(row) for row in rows]


def font_resolution(container: str | None, family: str) -> str:
    if container is None:
        cmd = ["/usr/bin/fc-match", "-f", "%{family}\n", family]
    else:
        cmd = [
            "/usr/bin/podman",
            "exec",
            container,
            "/usr/bin/fc-match",
            "-f",
            "%{family}\n",
            family,
        ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
    return proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else "unresolved"


def browserless_binary_digest(container: str) -> str:
    proc = subprocess.run(
        [
            "/usr/bin/podman",
            "exec",
            container,
            "/bin/sh",
            "-lc",
            "set -eu; p=$(find /usr/local/bin/playwright-browsers -type f "
            "-path '*/chrome-linux64/chrome' -print | sort); "
            "test $(printf '%s\n' \"$p\" | sed '/^$/d' | wc -l) -eq 1; "
            "sha256sum \"$p\"",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    digest = proc.stdout.strip().split()[0]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise RuntimeError("invalid Browserless Chromium digest")
    return "sha256:" + digest


def page_observation(page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const canvas=document.createElement('canvas');
          const gl=canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
          let webgl={available:false};
          if (gl) {
            const dbg=gl.getExtension('WEBGL_debug_renderer_info');
            webgl={
              available:true,
              vendor:dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : null,
              renderer:dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : null,
              version:gl.getParameter(gl.VERSION),
              shadingLanguageVersion:gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
              extensionsCount:(gl.getSupportedExtensions()||[]).length
            };
          }
          const families=%s;
          const fontChecks=Object.fromEntries(
            families.map(f => [f, document.fonts.check('16px "'+f+'"')])
          );
          const ctx=document.createElement('canvas').getContext('2d');
          const text='Ordivon Browser Security 012345';
          const widths={};
          for (const f of families) {
            ctx.font='16px "'+f+'"';
            widths[f]=Number(ctx.measureText(text).width.toFixed(4));
          }
          return {
            webdriver:navigator.webdriver,
            userAgent:navigator.userAgent,
            platform:navigator.platform,
            language:navigator.language,
            languages:Array.from(navigator.languages||[]),
            hardwareConcurrency:navigator.hardwareConcurrency,
            deviceMemoryGiB:navigator.deviceMemory??null,
            maxTouchPoints:navigator.maxTouchPoints,
            screen:[
              screen.width,screen.height,screen.availWidth,screen.availHeight,
              screen.colorDepth,screen.pixelDepth
            ],
            devicePixelRatio:devicePixelRatio,
            windowInner:[innerWidth,innerHeight],
            windowOuter:[outerWidth,outerHeight],
            timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffsetMinutes:new Date().getTimezoneOffset(),
            webgl,
            fontChecks,
            canvasTextWidths:widths,
            prefersColorSchemeDark:matchMedia('(prefers-color-scheme: dark)').matches,
            prefersReducedMotion:matchMedia('(prefers-reduced-motion: reduce)').matches
          };
        }"""
        % json.dumps(list(FONT_FAMILIES))
    )


def browser_observation(browser) -> dict[str, Any]:
    session = browser.new_browser_cdp_session()
    try:
        version = session.send("Browser.getVersion")
        command = session.send("Browser.getBrowserCommandLine")
        system = session.send("SystemInfo.getInfo")
        targets = session.send("Target.getTargets")
        contexts = session.send("Target.getBrowserContexts")
    finally:
        session.detach()

    gpu = system.get("gpu") if isinstance(system, dict) else {}
    devices = gpu.get("devices") if isinstance(gpu, dict) else []
    selected_devices = []
    if isinstance(devices, list):
        for row in devices:
            if not isinstance(row, dict):
                continue
            selected_devices.append(
                {
                    key: row.get(key)
                    for key in ("vendorId", "deviceId", "vendorString", "deviceString")
                }
            )
    target_infos = targets.get("targetInfos") if isinstance(targets, dict) else []
    type_counts = collections.Counter(
        row.get("type")
        for row in target_infos
        if isinstance(row, dict) and isinstance(row.get("type"), str)
    )
    context_ids = contexts.get("browserContextIds") if isinstance(contexts, dict) else []
    return {
        "version": {
            key: version.get(key)
            for key in ("protocolVersion", "product", "revision", "userAgent", "jsVersion")
        },
        "commandLineArguments": normalize_command_line(command.get("arguments")),
        "systemInfo": {
            "modelName": system.get("modelName"),
            "modelVersion": system.get("modelVersion"),
            "commandLine": normalize_command_line(system.get("commandLine")),
            "gpuDevices": selected_devices,
        },
        "targetTypeCounts": dict(sorted(type_counts.items())),
        "browserContextCount": len(context_ids) if isinstance(context_ids, list) else None,
    }


def changed_paths(left: object, right: object, path: str = "$") -> list[str]:
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        out: list[str] = []
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}"
            if key not in left or key not in right:
                out.append(child)
            else:
                out.extend(changed_paths(left[key], right[key], child))
        return out
    if isinstance(left, list):
        if len(left) != len(right):
            return [path]
        out: list[str] = []
        for index, (a, b) in enumerate(zip(left, right)):
            out.extend(changed_paths(a, b, f"{path}[{index}]"))
        return out
    return [] if left == right else [path]


def collect_arm(browser, *, create_new_page: bool) -> dict[str, Any]:
    if len(browser.contexts) != 1:
        raise RuntimeError("R3 requires exactly one browser context")
    context = browser.contexts[0]
    if create_new_page:
        page = context.new_page()
        owns_page = True
    else:
        page = context.pages[0] if context.pages else context.new_page()
        owns_page = not bool(context.pages)
    try:
        page.goto("data:text/html,<html><body>ordivon-r3-neutral</body></html>")
        return {
            "browserVersion": browser.version,
            "page": page_observation(page),
            "browser": browser_observation(browser),
        }
    finally:
        if owns_page:
            page.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    if not CHROME.is_file():
        raise SystemExit(f"direct Chromium missing: {CHROME}")

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

    container = "ordivon-browserless-11"
    direct_digest = sha256_file(CHROME)
    container_digest = browserless_binary_digest(container)

    host_fonts = {family: font_resolution(None, family) for family in FONT_FAMILIES}
    container_fonts = {
        family: font_resolution(container, family) for family in FONT_FAMILIES
    }

    if pathlib.Path("/tmp/.X11-unix/X193").exists():
        raise SystemExit("reserved R3 Xvfb display :193 is already in use")

    xvfb = subprocess.Popen(
        [
            "/usr/bin/Xvfb",
            DISPLAY,
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
    direct = None
    try:
        with tempfile.TemporaryDirectory(prefix="ordivon-cf-r3-direct-") as profile:
            env = dict(os.environ)
            env["DISPLAY"] = DISPLAY
            direct = subprocess.Popen(
                [
                    str(CHROME),
                    f"--remote-debugging-port={DEBUG_PORT}",
                    f"--user-data-dir={profile}",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--enable-automation",
                    "--window-size=1440,1000",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "about:blank",
                ],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            wait_json(f"http://127.0.0.1:{DEBUG_PORT}/json/version")

            from playwright.sync_api import sync_playwright

            with _carrier_lease(cfg, endpoint.endpoint_id, blocking=False):
                if endpoint.sessions(timeout_seconds=3):
                    raise RuntimeError(f"endpoint became busy: {ENDPOINT_ID}")
                with sync_playwright() as pw:
                    direct_browser = pw.chromium.connect_over_cdp(
                        f"http://127.0.0.1:{DEBUG_PORT}", timeout=30_000
                    )
                    try:
                        direct_arm = collect_arm(direct_browser, create_new_page=False)
                    finally:
                        direct_browser.close()

                    browserless = pw.chromium.connect_over_cdp(
                        endpoint.authenticated_connection_endpoint(timeout_ms=90_000),
                        timeout=30_000,
                    )
                    try:
                        browserless_arm = collect_arm(
                            browserless, create_new_page=True
                        )
                    finally:
                        browserless.close()
    finally:
        if direct is not None:
            direct.terminate()
            try:
                direct.wait(timeout=5)
            except subprocess.TimeoutExpired:
                direct.kill()
                direct.wait(timeout=5)
        xvfb.terminate()
        try:
            xvfb.wait(timeout=5)
        except subprocess.TimeoutExpired:
            xvfb.kill()
            xvfb.wait(timeout=5)

    output = {
        "schemaVersion": 1,
        "kind": "ordivon.browser-security-neutral-differential-r3",
        "date": "2026-09-18",
        "standing": "NEUTRAL_DIFFERENTIAL_ONLY_ROOT_CAUSE_OPEN",
        "safetyBoundary": {
            "protectedProviderVisited": False,
            "challengeInteracted": False,
            "cookieValuesRead": False,
            "providerSendAttempted": False,
        },
        "controls": {
            "networkNamespace": NETWORK_NAMESPACE,
            "sameChromiumBinary": direct_digest == container_digest,
            "directChromiumDigest": direct_digest,
            "browserlessChromiumDigest": container_digest,
            "webdriverMatchedByDesign": True,
            "directEnableAutomation": True,
            "neutralPage": "data:text/html",
        },
        "systemFontResolution": {
            "directHost": host_fonts,
            "browserlessContainer": container_fonts,
        },
        "arms": {
            "directEnableAutomation": direct_arm,
            "browserlessCurrent": browserless_arm,
        },
        "differences": {
            "pageChangedPaths": changed_paths(
                direct_arm["page"], browserless_arm["page"]
            ),
            "browserChangedPaths": changed_paths(
                direct_arm["browser"], browserless_arm["browser"]
            ),
            "fontResolutionFamilies": [
                family
                for family in FONT_FAMILIES
                if host_fonts[family] != container_fonts[family]
            ],
            "canvasWidthFamilies": [
                family
                for family in FONT_FAMILIES
                if direct_arm["page"]["canvasTextWidths"][family]
                != browserless_arm["page"]["canvasTextWidths"][family]
            ],
        },
        "interpretationGuard": {
            "providerCausalityEstablished": False,
            "challengeOutcomeUsedAsDetectorOracle": False,
            "note": "Differences localize neutral presentation/control surfaces only.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output["differences"], sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
