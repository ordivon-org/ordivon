from __future__ import annotations

from pathlib import Path
import shutil

from artifact_core.contracts import file_fact, sha256_file


def copy_exact(source_path: Path, output_path: Path) -> dict[str, object]:
    """Copy an already-native artifact and prove exact byte identity."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, output_path)
    matched = sha256_file(source_path) == sha256_file(output_path)
    return {
        "status": "PASS" if matched else "FAIL",
        "provider": "exact-file-copy",
        "source": file_fact(source_path),
        "artifact": file_fact(output_path),
        "digestMatched": matched,
    }
