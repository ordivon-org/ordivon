#!/usr/bin/env python3
"""Check source-cut Git blob and evidence-link identity after JSON Schema validation.

Shape, enum and format checks are delegated to the pinned check-jsonschema provider
in repo:ci; this script only checks Git and cross-file facts it cannot decide.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess


def git(repo: Path, *args: str) -> str | None:
    process = subprocess.run(["git", "-C", str(repo), *args],
                             capture_output=True, text=True, timeout=12)
    return process.stdout.strip() if process.returncode == 0 else None


def check(repo: Path, packet: Path) -> list[str]:
    data = json.loads(packet.read_text(encoding="utf-8"))
    errors: list[str] = []
    cut = data["source"]["ordivonSourceCut"]
    if git(repo, "cat-file", "-t", cut) != "commit":
        errors.append("SourceCut commit unavailable")
    refs = data["references"]
    paths = [v for key, v in refs.items() if key != "consumerSources"] + refs["consumerSources"]
    root = repo.resolve()
    for path in paths:
        if not isinstance(path, str) or not path or Path(path).is_absolute():
            errors.append("non-relative evidence reference")
            continue
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            errors.append("missing/escaping reference " + path)
    bindings = data["source"]["consumerSourceBlobSha1"]
    if set(bindings) != set(refs["consumerSources"]):
        errors.append("consumer Git Blob witness paths differ from consumerSources")
    for path in refs["consumerSources"]:
        original = git(repo, "rev-parse", "--verify", f"{cut}:{path}")
        if (original is None or git(repo, "cat-file", "-t", original) != "blob"
                or original != bindings.get(path)):
            errors.append("consumer blob not bound to original cut: " + path)
    experiment_path = (root / refs["experiment"]).resolve()
    if experiment_path.is_relative_to(root) and experiment_path.is_file():
        experiment = json.loads(experiment_path.read_text(encoding="utf-8"))
        upstream = data["source"]["upstream"]["repository"].removeprefix("https://github.com/")
        if experiment.get("candidate") != upstream:
            errors.append("experiment candidate differs from upstream")
        if (experiment.get("productionReplacementAuthorized") is not False
                or not experiment.get("negative") or not experiment.get("rollback")):
            errors.append("missing negative/rollback/no-production evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    errors = check(args.repo.resolve(), args.packet.resolve())
    print(json.dumps({"standing": "PASS" if not errors else "FAIL", "issues": errors}, indent=2))
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
