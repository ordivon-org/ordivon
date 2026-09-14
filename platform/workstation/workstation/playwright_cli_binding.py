#!/usr/bin/env python3
"""Materialize the exact local binding profile required by Microsoft @playwright/cli.

This module owns no browser-operation semantics. It only composes the exact installed
Playwright CLI entrypoint with the current Workstation-bound Chromium executable and emits
an upstream-native CLI config. Callers still invoke Microsoft playwright-cli directly.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

import equipment_binding
import tool_binding as core

CLI_EQUIPMENT_ID = "playwright-cli-0-1-18"
DEFAULT_NODE = Path("/usr/bin/node")


def _profile_identity(*, cli: Mapping[str, Any], browser: Mapping[str, Any], node: Path) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.v2.playwright-cli-binding-identity",
        "cliEquipmentId": CLI_EQUIPMENT_ID,
        "cliEntrypoint": str(cli["observedExecutable"]),
        "cliEntrypointDigest": str(cli["executableDigest"]),
        "nodeExecutable": str(node),
        "nodeExecutableDigest": core.sha256_file(node),
        "browserEquipmentId": str(browser["equipmentId"]),
        "browserExecutable": str(browser["executable"]),
        "browserExecutableDigest": str(browser["executableDigest"]),
        "browserBindingDigest": str(browser["bindingDigest"]),
    }


def resolve_profile(
    catalog: Mapping[str, Any],
    *,
    browser_binding: Mapping[str, Any] | None = None,
    node_path: Path = DEFAULT_NODE,
) -> dict[str, Any]:
    cli = core.resolve_managed(catalog, CLI_EQUIPMENT_ID)
    browser = dict(browser_binding or equipment_binding.bind_browser(catalog))
    node = node_path.resolve()
    if not node.is_file() or not os.access(node, os.X_OK):
        raise RuntimeError(f"Node.js executable is unavailable: {node}")
    if browser.get("state") != "AVAILABLE":
        raise RuntimeError("Playwright Chromium binding is not AVAILABLE")
    environment = dict(browser.get("environment") or {})
    if not environment.get("PLAYWRIGHT_BROWSERS_PATH"):
        raise RuntimeError("Playwright Chromium binding omitted PLAYWRIGHT_BROWSERS_PATH")
    identity = _profile_identity(cli=cli, browser=browser, node=node)
    config = {
        "browser": {
            "browserName": "chromium",
            "isolated": True,
            "launchOptions": {
                "headless": True,
                "executablePath": browser["executable"],
                # The current Workstation/Runtime service user is root inside WSL.
                # This is an upstream Playwright launch option, not a custom browser mode.
                "chromiumSandbox": False,
            },
        }
    }
    return {
        "schemaVersion": 1,
        "kind": "ordivon.workstation.v2.playwright-cli-binding",
        "truthRole": "node-local-upstream-cli-binding",
        "state": "AVAILABLE",
        "commandPrefix": [str(node), str(cli["observedExecutable"])],
        "environment": environment,
        "config": config,
        "bindingDigest": core.canonical_digest(identity),
        "identity": identity,
        "authorityBoundary": (
            "Workstation v2 proves only exact local Microsoft Playwright CLI + Chromium materialization "
            "and the mechanical launch profile required on this node. Playwright owns browser/session/action "
            "semantics; Runtime owns execution truth; the caller/domain owns task selection and success."
        ),
        "nonClaims": [
            "runtime_execution_admitted",
            "browser_action_authorized",
            "task_authorized",
            "domain_suitable",
            "domain_success",
        ],
    }


def _write_atomic(path: Path, value: Mapping[str, Any]) -> None:
    if not path.is_absolute():
        raise RuntimeError("config output path must be absolute")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp, 0o600)
        os.replace(temp, path)
    finally:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass


def materialize_config(profile: Mapping[str, Any], output: Path) -> dict[str, Any]:
    config = profile.get("config")
    if not isinstance(config, Mapping):
        raise RuntimeError("Playwright CLI binding profile omitted config")
    _write_atomic(output, config)
    config_digest = core.canonical_digest(config)
    return {
        **dict(profile),
        "materializedConfig": {
            "path": str(output),
            "digest": config_digest,
            "mode": "0600",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=core.CATALOG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("profile")
    materialize = sub.add_parser("materialize")
    materialize.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = core.read_catalog(args.catalog)
    profile = resolve_profile(catalog)
    if args.command == "materialize":
        profile = materialize_config(profile, args.output)
    print(json.dumps(profile, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
