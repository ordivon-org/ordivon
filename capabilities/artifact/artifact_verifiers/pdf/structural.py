from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact

from .toolchain import qpdf_executable


def verify_pdf(path: Path) -> dict[str, Any]:
    artifact = file_fact(path)
    executable = qpdf_executable()
    if executable is None:
        return {
            "status": "FAIL",
            "artifact": artifact,
            "validator": "qpdf",
            "error": "qpdf is not installed",
            "profileValidation": "NOT_RUN",
        }
    proc = subprocess.run(
        [str(executable), "--check", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "artifact": artifact,
        "validator": str(executable),
        "exitCode": proc.returncode,
        "stdout": proc.stdout.strip()[:4000],
        "stderr": proc.stderr.strip()[:4000],
        "profileValidation": "NOT_RUN",
        "note": (
            "qpdf structural checking does not establish PDF/A or PDF/UA conformance; "
            "use veraPDF/PAC in those profiles."
        ),
    }
