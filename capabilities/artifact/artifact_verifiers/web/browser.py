from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact

from .toolchain import node_executable, node_package_root, web_verifier_runner


def verify_web_local(path: Path) -> dict[str, Any]:
    artifact = file_fact(path)
    node = node_executable()
    verifier = web_verifier_runner()
    if node is None or not verifier.is_file():
        return {
            "status": "NOT_RUN",
            "artifact": artifact,
            "error": "Node/Playwright HTML verifier is unavailable",
        }

    node_env = os.environ.copy()
    if "ARTIFACT_NODE_PACKAGE_ROOT" not in node_env:
        package_root = node_package_root()
        if package_root is not None:
            node_env["ARTIFACT_NODE_PACKAGE_ROOT"] = str(package_root)

    proc = subprocess.run(
        [str(node), str(verifier), str(path.resolve())],
        cwd=verifier.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=90,
        env=node_env,
    )
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    try:
        parsed = json.loads(proc.stdout)
    except Exception as error:
        parse_error = str(error)

    digest_ok = (
        parsed is not None
        and parsed.get("subject", {}).get("sha256")
        == artifact["digest"]["sha256"]
    )
    return {
        "status": (
            "PASS"
            if proc.returncode == 0
            and parsed
            and parsed.get("status") == "PASS"
            and digest_ok
            else "FAIL"
        ),
        "artifact": artifact,
        "verifierOutput": parsed,
        "digestBound": digest_ok,
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": (
            "Local Playwright/axe evidence only; delivery profile policy decides "
            "which renderers are required and unsupported-host WebKit cannot be "
            "promoted to PASS."
        ),
    }
