#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tarfile
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from ordivon_security_v2.provenance import build_provenance_statement


def _run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    output = args.output_dir.resolve()
    if _run("git", "status", "--porcelain", cwd=repo):
        raise SystemExit("builder requires a clean source repository")
    revision = _run("git", "rev-parse", "HEAD", cwd=repo)
    source_uri = "git+" + repo.as_uri()
    uv_version = _run("uv", "--version").split()[1]
    python_executable = _run("uv", "python", "find", "3.12")
    python_version = _run(python_executable, "-c", "import platform; print(platform.python_version())")

    output.mkdir(parents=True, exist_ok=True)
    for child in output.iterdir():
        if child.is_file() or child.is_symlink():
            child.unlink()
        else:
            shutil.rmtree(child)

    started = _now()
    invocation_id = "urn:uuid:" + str(uuid.uuid4())
    with tempfile.TemporaryDirectory(prefix="security-v2-slsa-build-") as td:
        root = Path(td)
        archive = root / "source.tar"
        source = root / "source"
        source.mkdir()
        with archive.open("wb") as handle:
            subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=repo, stdout=handle, check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(source, filter="data")
        subprocess.run(["uv", "build", "--wheel", "--out-dir", str(output)], cwd=source, check=True)
    finished = _now()

    wheels = list(output.glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit(f"expected exactly one wheel, observed {len(wheels)}")
    statement = build_provenance_statement(
        artifact=wheels[0],
        source_uri=source_uri,
        source_revision=revision,
        invocation_id=invocation_id,
        started_on=started,
        finished_on=finished,
        builder_versions={
            "builder-script-git-commit": revision,
            "uv": uv_version,
            "python": python_version,
        },
    )
    provenance = output / (wheels[0].name + ".provenance.intoto.json")
    provenance.write_text(json.dumps(statement, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"artifact": str(wheels[0]), "provenance": str(provenance), "sourceRevision": revision}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
