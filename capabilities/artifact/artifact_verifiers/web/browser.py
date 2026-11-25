from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact
from artifact_core.json_validation import decode_json

from .oci import oci_source_recipe, run_oci_browser
from .toolchain import node_executable, node_package_root, web_verifier_runner


def _run_host(path: Path, verifier: Path) -> subprocess.CompletedProcess[str]:
    node = node_executable()
    if node is None:
        raise ValueError("Node/Playwright HTML verifier is unavailable")
    node_env = os.environ.copy()
    if "ARTIFACT_NODE_PACKAGE_ROOT" not in node_env:
        package_root = node_package_root()
        if package_root is not None:
            node_env["ARTIFACT_NODE_PACKAGE_ROOT"] = str(package_root)
    return subprocess.run(
        [str(node), str(verifier), str(path.resolve())],
        cwd=verifier.parent,
        text=True,
        capture_output=True,
        check=False,
        timeout=90,
        env=node_env,
    )


def web_provider_recipe(selection: str) -> dict[str, Any]:
    if selection == "host":
        return {"selection": "host"}
    if selection == "oci":
        return oci_source_recipe(web_verifier_runner())
    raise ValueError("unqualified explicit browser provider")


def verify_web_local(
    path: Path, *, provider_recipe: dict[str, Any] | None = None
) -> dict[str, Any]:
    artifact = file_fact(path)
    verifier = web_verifier_runner()
    selected = (
        provider_recipe["selection"]
        if provider_recipe is not None
        else os.environ.get("ARTIFACT_WEB_PROVIDER", "host")
    )
    provider: dict[str, Any] = {"kind": "host-local"}
    try:
        if not verifier.is_file():
            raise ValueError("HTML verifier runner unavailable")
        if selected == "oci":
            if provider_recipe is None:
                proc, provider = run_oci_browser(artifact, verifier)
            else:
                proc, provider = run_oci_browser(artifact, verifier, provider_recipe)
        elif selected == "host":
            proc = _run_host(path, verifier)
        else:
            raise ValueError("unqualified explicit browser provider")
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        TypeError,
        subprocess.TimeoutExpired,
    ) as error:
        return {
            "status": "NOT_RUN",
            "artifact": artifact,
            "providerSelection": selected,
            "digestBound": False,
            "error": str(error)[:4000],
        }

    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        value = decode_json(proc.stdout)
        if not isinstance(value, dict):
            raise ValueError("browser report must be an object")
        parsed = value
    except (ValueError, UnicodeError) as error:
        parse_error = str(error)
    digest_ok = (
        parsed is not None
        and isinstance(parsed.get("subject"), dict)
        and parsed["subject"].get("sha256") == artifact["digest"]["sha256"]
    )
    method_ok = selected == "host" or (
        parsed is not None and parsed.get("tooling") == provider["expectedTooling"]
    )
    return {
        "status": (
            "PASS"
            if proc.returncode == 0
            and parsed
            and parsed.get("status") == "PASS"
            and digest_ok
            and method_ok
            else "FAIL"
        ),
        "artifact": artifact,
        "provider": provider,
        "verifierOutput": parsed,
        "digestBound": digest_ok,
        "methodBound": method_ok,
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": (
            "Local Playwright/axe observation only; delivery profile policy "
            "decides required renderers. No deployed-origin acceptance."
        ),
    }
