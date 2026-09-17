from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
from typing import Mapping

from artifact_core.contracts import file_fact


def build_pandoc_docx(
    source_path: Path,
    output_path: Path,
    pandoc: Path,
    *,
    environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Execute the bounded Markdown -> DOCX Pandoc provider contract."""
    if not pandoc.is_file():
        return {"status": "FAIL", "provider": "pandoc", "error": f"Pandoc not found: {pandoc}"}

    provider_env = os.environ.copy()
    if environment is not None:
        provider_env.update(environment)
    source_date_epoch = provider_env.get("SOURCE_DATE_EPOCH")
    source_date_epoch_fact: dict[str, object] = {
        "name": "SOURCE_DATE_EPOCH",
        "present": source_date_epoch is not None,
        "value": source_date_epoch,
        "standard": "https://reproducible-builds.org/docs/source-date-epoch/",
    }
    if source_date_epoch is not None and re.fullmatch(r"[0-9]+", source_date_epoch) is None:
        return {
            "status": "FAIL",
            "provider": "pandoc",
            "error": "SOURCE_DATE_EPOCH must be a non-negative base-10 integer number of seconds",
            "reproducibleBuildEnvironment": source_date_epoch_fact,
        }
    if source_date_epoch is None:
        provider_env.pop("SOURCE_DATE_EPOCH", None)
    else:
        source_date_epoch_fact["unixSeconds"] = int(source_date_epoch)
        provider_env["SOURCE_DATE_EPOCH"] = source_date_epoch

    output_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(pandoc), str(source_path), "-o", str(output_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
        env=provider_env,
    )
    return {
        "status": "PASS" if proc.returncode == 0 and output_path.is_file() else "FAIL",
        "provider": "pandoc",
        "returnCode": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-4000:],
        "artifact": file_fact(output_path) if output_path.is_file() else None,
        "reproducibleBuildEnvironment": source_date_epoch_fact,
    }
