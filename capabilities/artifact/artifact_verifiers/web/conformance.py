from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact, sha256_file

from .toolchain import java_executable, vnu_jar


def verify_html_conformance(path: Path) -> dict[str, Any]:
    artifact = file_fact(path)
    jar = vnu_jar()
    java = java_executable()
    if jar is None or java is None:
        return {
            "status": "NOT_RUN",
            "artifact": artifact,
            "error": "Nu Html Checker or Java is unavailable",
        }

    proc = subprocess.run(
        [str(java), "-jar", str(jar), "--format", "json", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    parsed: dict[str, Any] | None = None
    messages: list[Any] = []
    version: str | None = None
    parse_error: str | None = None
    try:
        payload = proc.stdout.strip() or proc.stderr.strip()
        parsed = json.loads(payload)
        messages = parsed.get("messages", []) if isinstance(parsed, dict) else []
        version = parsed.get("version") if isinstance(parsed, dict) else None
    except Exception as error:
        parse_error = str(error)

    return {
        "status": (
            "PASS"
            if proc.returncode == 0 and parsed is not None and not messages
            else "FAIL"
        ),
        "artifact": artifact,
        "validator": {
            "implementation": "Nu Html Checker",
            "version": version,
            "jar": str(jar),
            "jarSha256": sha256_file(jar),
        },
        "messageCount": len(messages),
        "messages": messages[:100],
        "exitCode": proc.returncode,
        "parseError": parse_error,
        "stderr": proc.stderr.strip()[:4000],
        "boundary": (
            "Nu Html Checker conformance evidence covers HTML/CSS/SVG "
            "syntax/content-model checks; browser behavior, accessibility and "
            "deployed-origin behavior remain independent."
        ),
    }
