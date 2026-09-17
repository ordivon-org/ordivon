#!/usr/bin/env python3
"""Collect a neutral/read-only Browserless security witness source manifest.

The emitted JSON is intentionally a Security-v2 collector *source* manifest. Harness owns browser
and provider observation; Security owns canonicalization, secret-field rejection, hashing and diff.
This script never visits ChatGPT, never interacts with a provider challenge, and never crosses SEND.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

DETECTOR_VERSION = "harness-browser-security-r2"


def browserless_container_name(endpoint_id: str) -> str:
    match = re.search(r"(\d+)$", endpoint_id)
    if match is None:
        raise ValueError("Browserless endpoint id must end in a numeric suffix")
    return f"ordivon-browserless-{match.group(1)}"


def profile_cookie_metadata(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {"cookieRows": 0, "cookieHosts": 0}
    uri = f"file:{path}?mode=ro"
    with sqlite3.connect(uri, uri=True, timeout=2) as db:
        row = db.execute("SELECT COUNT(*), COUNT(DISTINCT host_key) FROM cookies").fetchone()
    if row is None:
        return {"cookieRows": 0, "cookieHosts": 0}
    return {"cookieRows": int(row[0]), "cookieHosts": int(row[1])}


def normalize_effective_launch_argv(argv: list[str]) -> list[str]:
    if not argv:
        raise ValueError("effective Chromium argv must be non-empty")
    normalized: list[str] = []
    for index, arg in enumerate(argv):
        if not isinstance(arg, str) or not arg:
            raise ValueError("effective Chromium argv entries must be non-empty strings")
        if index == 0:
            continue
        if arg.startswith("--remote-debugging-port="):
            normalized.append("--remote-debugging-port=<ephemeral>")
        else:
            normalized.append(arg)
    return normalized


def _effective_launch_argv(container: str) -> list[str] | None:
    proc = subprocess.run(
        ["/usr/bin/podman", "exec", container, "/bin/sh", "-lc", "ps -eo args="],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        line = line.strip()
        if (
            "chromium-" in line
            and "/chrome-linux64/chrome" in line
            and "--user-data-dir=/data" in line
            and "--type=" not in line
        ):
            try:
                argv = shlex.split(line)
            except ValueError:
                continue
            return normalize_effective_launch_argv(argv)
    return None


def normalize_execution_contexts(contexts: list[dict[str, Any]]) -> list[str]:
    normalized: list[str] = []
    for context in contexts:
        name = context.get("name")
        aux = context.get("auxData") if isinstance(context.get("auxData"), dict) else {}
        if aux.get("isDefault") is True:
            normalized.append("default")
        elif isinstance(name, str) and name.startswith("__playwright_utility_world"):
            normalized.append("playwright-utility")
        elif isinstance(name, str) and name:
            normalized.append("isolated-world")
        else:
            normalized.append("non-default")
    return normalized


def assemble_manifest(
    *,
    witness_id: str,
    browser_binary_digest: str,
    control_layer: dict[str, Any],
    network_authority: dict[str, Any],
    readings: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "witnessId": witness_id,
        "browserBinaryDigest": browser_binary_digest,
        "controlLayer": control_layer,
        "networkAuthority": network_authority,
        "readings": readings,
        "challengeStanding": None,
    }


def _run_json(cmd: list[str], *, timeout: float = 10) -> Any:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
    return json.loads(proc.stdout)


def _container_image_identity(container: str) -> str:
    rows = _run_json(["/usr/bin/podman", "inspect", container])
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise RuntimeError("unexpected podman inspect result")
    row = rows[0]
    for key in ("ImageDigest", "Image"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    raise RuntimeError("Browserless container image identity unavailable")


def _browser_binary_digest(container: str) -> str:
    path = "/usr/local/bin/playwright-browsers/chromium-1243/chrome-linux64/chrome"
    proc = subprocess.run(
        ["/usr/bin/podman", "exec", container, "/usr/bin/sha256sum", path],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    digest = proc.stdout.strip().split()[0]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise RuntimeError("invalid Chromium digest returned by Browserless container")
    return "sha256:" + digest


def _font_resolution(container: str, family: str) -> str:
    proc = subprocess.run(
        [
            "/usr/bin/podman",
            "exec",
            container,
            "/usr/bin/fc-match",
            "-f",
            "%{family}\n",
            family,
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    first = proc.stdout.strip().splitlines()
    return first[0] if first else "unresolved"


def _cloudflare_trace() -> dict[str, str]:
    try:
        with urllib.request.urlopen(
            "https://www.cloudflare.com/cdn-cgi/trace", timeout=10
        ) as response:
            text = response.read().decode("utf-8", errors="replace")
    except Exception as error:
        return {"standing": "UNAVAILABLE", "detail": type(error).__name__}
    values: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in {"loc", "colo", "http", "tls", "warp"}:
            values[key] = value
    values["observer"] = "python-urllib"
    return values


class _ProbeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "OrdivonNeutralProbe/1"
    sys_version = ""

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        server = self.server
        if isinstance(server, _ProbeServer) and self.path.startswith("/probe"):
            server.header_order = [name for name, _ in self.headers.items()]
            server.captured.set()
        body = (
            "<!doctype html><html><body>neutral-probe"
            "<iframe srcdoc='<html><body>child</body></html>'></iframe>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


class _ProbeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _ProbeHandler)
        self.header_order: list[str] = []
        self.captured = threading.Event()


def _tls_probe(page) -> dict[str, Any]:
    try:
        page.goto("https://tls.peet.ws/api/all", wait_until="domcontentloaded", timeout=30_000)
        value = json.loads(page.locator("body").inner_text())
        tls = value.get("tls") or {}
        http2 = value.get("http2") or {}
        return {
            "standing": "OBSERVED",
            "httpVersion": value.get("http_version"),
            "ja4": tls.get("ja4"),
            "peetprintHash": tls.get("peetprint_hash"),
            "http2AkamaiFingerprintHash": http2.get("akamai_fingerprint_hash"),
            "tlsVersionNegotiated": tls.get("tls_version_negotiated"),
        }
    except Exception as error:
        return {"standing": "UNAVAILABLE", "detail": type(error).__name__}


def _browser_js_witness(page) -> dict[str, Any]:
    return page.evaluate(
        """() => ({
          navigatorWebdriver: navigator.webdriver,
          userAgent: navigator.userAgent,
          platform: navigator.platform,
          language: navigator.language,
          languages: Array.from(navigator.languages || []),
          hardwareConcurrency: navigator.hardwareConcurrency,
          deviceMemoryGiB: navigator.deviceMemory ?? null,
          maxTouchPoints: navigator.maxTouchPoints,
          screen: [screen.width, screen.height, screen.availWidth, screen.availHeight],
          devicePixelRatio: devicePixelRatio,
          windowInner: [innerWidth, innerHeight],
          windowOuter: [outerWidth, outerHeight],
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          timezoneOffsetMinutes: new Date().getTimezoneOffset()
        })"""
    )


def _execution_context_witness(context, page) -> dict[str, Any]:
    page.locator("body").count()
    session = context.new_cdp_session(page)
    contexts: list[dict[str, Any]] = []
    session.on("Runtime.executionContextCreated", lambda event: contexts.append(event["context"]))
    session.send("Runtime.enable")
    page.wait_for_timeout(250)
    session.detach()
    shape = normalize_execution_contexts(contexts)
    return {"contextCount": len(shape), "contextShape": shape}


def _collect_host_facts(endpoint_id: str) -> dict[str, Any]:
    container = browserless_container_name(endpoint_id)
    suffix_match = re.search(r"(\d+)$", endpoint_id)
    if suffix_match is None:
        raise ValueError("Browserless endpoint id must end in a numeric suffix")
    suffix = suffix_match.group(1)
    return {
        "containerImageIdentity": _container_image_identity(container),
        "browserBinaryDigest": _browser_binary_digest(container),
        "fontResolution": {
            family: _font_resolution(container, family)
            for family in ("DejaVu Sans", "Arial", "Segoe UI", "Noto Sans")
        },
        "profileMetadata": profile_cookie_metadata(
            Path(f"/var/lib/ordivon/browserless/{suffix}/Default/Cookies")
        ),
    }


def _collect_inside_namespace(
    config_path: Path, endpoint_id: str, witness_id: str, host_facts: dict[str, Any]
) -> dict[str, Any]:
    from scripts.agent_automation_browserless import BrowserlessAutomationConfig, _read_json

    raw_config = _read_json(config_path)
    config = BrowserlessAutomationConfig.from_dict(raw_config)
    endpoint = next(
        (row for row in config.browserless_pool.endpoints if row.endpoint_id == endpoint_id), None
    )
    if endpoint is None:
        raise ValueError(f"unknown Browserless endpoint: {endpoint_id}")
    browser_digest = host_facts.get("browserBinaryDigest")
    if not isinstance(browser_digest, str) or not browser_digest.startswith("sha256:"):
        raise ValueError("host facts lack browserBinaryDigest")
    profile = host_facts.get("profileMetadata")
    fonts = host_facts.get("fontResolution")
    image_identity = host_facts.get("containerImageIdentity")
    if not isinstance(profile, dict) or not isinstance(fonts, dict) or not isinstance(image_identity, str):
        raise ValueError("host facts are incomplete")
    network_authority = raw_config.get("browserNetworkAuthority")
    if not isinstance(network_authority, dict):
        raise ValueError("browserNetworkAuthority missing from Browserless automation config")

    server = _ProbeServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(
                endpoint.authenticated_connection_endpoint(timeout_ms=90_000), timeout=30_000
            )
            try:
                if len(browser.contexts) != 1:
                    raise RuntimeError("Browserless witness requires exactly one browser context")
                context = browser.contexts[0]
                pages = context.pages
                page = pages[0] if pages else context.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/probe",
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
                if not server.captured.wait(5):
                    raise RuntimeError("neutral header probe was not captured")
                browser_js = _browser_js_witness(page)
                execution_contexts = _execution_context_witness(context, page)
                tls = _tls_probe(page)
                browser_version = browser.version
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    cloudflare = _cloudflare_trace()
    control_layer = {
        "routeFamily": "browserless/chromium",
        "endpointId": endpoint.endpoint_id,
        "networkNamespace": endpoint.network_namespace,
        "userDataDir": endpoint.user_data_dir,
        "headless": endpoint.headless,
        "launchArgs": list(endpoint.launch_args),
        "launchOwner": "browserless-puppeteer",
        "controlClient": "playwright-connect-over-cdp",
        "browserVersion": browser_version,
        "containerImageIdentity": image_identity,
    }
    readings = [
        {
            "detectorId": "cf02-transport-normalized",
            "family": "CF02",
            "detectorVersion": DETECTOR_VERSION,
            "coverage": "browser TLS/HTTP2 normalized fields from tls.peet.ws; JA3 intentionally excluded",
            "publicObservation": tls,
        },
        {
            "detectorId": "cf03-main-document-headers",
            "family": "CF03",
            "detectorVersion": DETECTOR_VERSION,
            "coverage": "main-document request header set/order against local neutral HTTP probe",
            "publicObservation": {"headerOrder": server.header_order},
        },
        {
            "detectorId": "cf04-browser-js-presentation",
            "family": "CF04",
            "detectorVersion": DETECTOR_VERSION,
            "coverage": "page-visible browser identity, automation presentation, geometry and locale",
            "publicObservation": browser_js,
        },
        {
            "detectorId": "cf05-control-observability",
            "family": "CF05",
            "detectorVersion": DETECTOR_VERSION,
            "coverage": "CDP Runtime execution-context shape only; protocol-domain subscription state remains uncovered",
            "publicObservation": execution_contexts,
        },
        {
            "detectorId": "cf06-cross-layer-consistency",
            "family": "CF06",
            "detectorVersion": DETECTOR_VERSION,
            "coverage": "coarse network geography, browser timezone/locale/geometry, and container font resolution",
            "publicObservation": {
                "network": cloudflare,
                "browser": {
                    key: browser_js[key]
                    for key in (
                        "timezone",
                        "timezoneOffsetMinutes",
                        "language",
                        "languages",
                        "screen",
                        "devicePixelRatio",
                        "windowInner",
                        "windowOuter",
                    )
                },
                "fontResolution": fonts,
            },
        },
        {
            "detectorId": "cf07-profile-metadata",
            "family": "CF07",
            "detectorVersion": DETECTOR_VERSION,
            "coverage": "non-secret Chrome persistent-profile cookie row and distinct-host counts only",
            "publicObservation": profile,
        },
    ]
    return assemble_manifest(
        witness_id=witness_id,
        browser_binary_digest=browser_digest,
        control_layer=control_layer,
        network_authority=network_authority,
        readings=readings,
    )


def _load_runtime_config(config_path: Path):
    from scripts.agent_automation_browserless import BrowserlessAutomationConfig, _read_json

    raw = _read_json(config_path)
    return BrowserlessAutomationConfig.from_dict(raw)


def _endpoint(config, endpoint_id: str):
    row = next((item for item in config.browserless_pool.endpoints if item.endpoint_id == endpoint_id), None)
    if row is None:
        raise ValueError(f"unknown Browserless endpoint: {endpoint_id}")
    return row


def _reexec_in_namespace(args: argparse.Namespace) -> int:
    from scripts.agent_automation_browserless import _carrier_lease

    config = _load_runtime_config(args.config)
    endpoint = _endpoint(config, args.endpoint_id)
    container = browserless_container_name(endpoint.endpoint_id)
    env = dict(os.environ)
    env["ORDIVON_BROWSER_SECURITY_IN_NETNS"] = "1"
    with _carrier_lease(config, endpoint.endpoint_id, blocking=False):
        if endpoint.sessions(timeout_seconds=3):
            raise RuntimeError(f"Browserless carrier busy: {endpoint.endpoint_id}")
        host_facts = _collect_host_facts(endpoint.endpoint_id)
        with tempfile.TemporaryDirectory(prefix="ordivon-browser-security-") as tmp:
            tmp_root = Path(tmp)
            host_facts_path = tmp_root / "host-facts.json"
            child_output = tmp_root / "source-manifest.json"
            host_facts_path.write_text(
                json.dumps(host_facts, sort_keys=True, separators=(",", ":")), encoding="utf-8"
            )
            os.chmod(host_facts_path, 0o600)
            cmd = [
                *endpoint.exec_prefix,
                str(config.playwright_python),
                str(Path(__file__).resolve()),
                "--config",
                str(args.config),
                "--endpoint-id",
                args.endpoint_id,
                "--witness-id",
                args.witness_id,
                "--host-facts-file",
                str(host_facts_path),
                "--output",
                str(child_output),
            ]
            proc = subprocess.Popen(cmd, env=env)
            effective_argv: list[str] | None = None
            deadline = time.monotonic() + 12
            while time.monotonic() < deadline and proc.poll() is None:
                effective_argv = _effective_launch_argv(container)
                if effective_argv is not None:
                    break
                time.sleep(0.1)
            try:
                returncode = proc.wait(timeout=120)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
                raise RuntimeError("Browser Security namespace collector timed out")
            if returncode != 0:
                return int(returncode)
            if effective_argv is None:
                raise RuntimeError("effective Browserless Chromium launch argv was not observed")
            manifest = json.loads(child_output.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict) or not isinstance(manifest.get("controlLayer"), dict):
                raise RuntimeError("Browser Security namespace collector returned malformed manifest")
            manifest["controlLayer"]["effectiveLaunchArgvNormalized"] = effective_argv
            text = json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
            if args.output is None:
                print(text, end="")
            else:
                args.output.write_text(text, encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("/etc/ordivon/agent-automation-browserless.json")
    )
    parser.add_argument("--endpoint-id", required=True)
    parser.add_argument("--witness-id", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--host-facts-file", type=Path)
    args = parser.parse_args()

    if os.environ.get("ORDIVON_BROWSER_SECURITY_IN_NETNS") != "1":
        return _reexec_in_namespace(args)
    if args.host_facts_file is None:
        raise SystemExit("--host-facts-file is required inside the browser network namespace")
    host_facts = json.loads(args.host_facts_file.read_text(encoding="utf-8"))
    if not isinstance(host_facts, dict):
        raise SystemExit("host facts must be a JSON object")

    manifest = _collect_inside_namespace(
        args.config, args.endpoint_id, args.witness_id, host_facts
    )
    text = json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.output is None:
        print(text, end="")
    else:
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
