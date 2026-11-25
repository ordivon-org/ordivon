"""Bounded local OCI effect adapter; native browser logic stays in one runner."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from artifact_core.contracts import FileCommitment
from artifact_core.input_snapshot import stage_verified_input
from artifact_core.json_validation import load_json_with_digest

from .toolchain import GLOBAL_ARTIFACT_TOOLCHAIN_ROOT, ROOT

LOCK = ROOT / "artifact-delivery/web-oci-runtime-v1.lock.json"
NODE_SOURCE = ROOT / "artifact-delivery/node"
METADATA = ("package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml")


def run_oci_browser(
    artifact: dict[str, Any], verifier: Path
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    """Use one explicit local image, never pull or fall back.

    Read-only mounts protect inputs from container writes, not a concurrent
    same-principal host writer. Node metadata equality is not a full installed
    package content attestation. No arbitrary HTML safety claim.
    """
    lock, lock_sha = load_json_with_digest(LOCK)
    if (
        not isinstance(lock, dict)
        or type(lock.get("schemaVersion")) is not int
        or lock["schemaVersion"] != 1
    ):
        raise ValueError("unqualified OCI lock")
    image_id = lock["imageId"]
    manifest = lock["manifestDigest"]
    if not isinstance(image_id, str) or not re.fullmatch(r"[0-9a-f]{64}", image_id):
        raise ValueError("invalid OCI image ID")
    if not isinstance(manifest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", manifest):
        raise ValueError("invalid OCI manifest digest")
    package, package_sha = load_json_with_digest(NODE_SOURCE / "package.json")
    dependencies = package["dependencies"]
    tooling = {
        "playwright": dependencies["@playwright/test"],
        "axePlaywright": dependencies["@axe-core/playwright"],
    }
    if any(
        not isinstance(value, str)
        or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?", value)
        or lock[key] != value
        for key, value in tooling.items()
    ):
        raise ValueError("OCI image/runner method version mismatch")
    package_root = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "node" / tooling["playwright"]
    commitments = {}
    for name in METADATA:
        source = FileCommitment.from_path(NODE_SOURCE / name)
        installed = FileCommitment.from_path(package_root / name)
        if (source.sha256, source.size) != (installed.sha256, installed.size):
            raise ValueError(f"OCI Node metadata mismatch: {name}")
        commitments[name] = installed.sha256
    if commitments["package.json"] != package_sha:
        raise ValueError("OCI source package metadata changed during admission")

    podman = shutil.which("podman")
    if podman is None:
        raise ValueError("Podman unavailable")
    inspection = subprocess.run(
        [podman, "image", "inspect", image_id, "--format", "{{.Id}} {{.Digest}}"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if inspection.returncode or inspection.stdout.strip().split() != [image_id, manifest]:
        raise ValueError("OCI local image identity unavailable or mismatched")

    runner = FileCommitment.from_path(verifier)
    with tempfile.TemporaryDirectory(prefix="artifact-web-oci-") as scratch:
        root = Path(scratch)
        subject = stage_verified_input(
            Path(artifact["path"]), artifact["digest"]["sha256"], root, role="subject"
        )
        script = stage_verified_input(runner.path, runner.sha256, root, role="contract")
        if subject.size != artifact["size"]:
            raise ValueError("OCI subject size mismatch")
        subject_path = subject.path.with_name("subject.html")
        subject.path.rename(subject_path)
        for file in (subject_path, script.path):
            file.chmod(0o444)
        mounts = (
            (package_root.resolve(), "/packages"),
            (subject_path, "/input/subject.html"),
            (script.path, "/input/verify_html.mjs"),
        )
        if any(":" in str(src) or "\n" in str(src) for src, _ in mounts):
            raise ValueError("unsupported OCI bind mount path")
        options = [
            "--rm",
            "--pull=never",
            "--network=none",
            "--cap-drop=ALL",
            "--cap-add=SYS_CHROOT",
            "--security-opt=no-new-privileges",
            "--user=1000:1000",
            "--http-proxy=false",
            "--timeout=60",
            "--shm-size=256m",
        ]
        command = [podman, "run", *options]
        for src, dest in mounts:
            command.extend(["-v", f"{src}:{dest}:ro"])
        command.extend(
            [
                "-e",
                "ARTIFACT_NODE_PACKAGE_ROOT=/packages",
                "-e",
                "PLAYWRIGHT_BROWSERS_PATH=/ms-playwright",
                "-e",
                "HOME=/tmp",
                image_id,
                "node",
                "/input/verify_html.mjs",
                "/input/subject.html",
            ]
        )
        proc = subprocess.run(command, capture_output=True, text=True, check=False, timeout=75)
    return proc, {
        "kind": "podman-oci",
        "runtimeExecutable": podman,
        "runOptions": options,
        "imageId": image_id,
        "manifestDigest": manifest,
        "lockSha256": lock_sha,
        "runnerSha256": runner.sha256,
        "nodeMetadataSha256": commitments,
        "expectedTooling": tooling,
        "inputSnapshotSha256": subject.sha256,
        "scope": "DECLARED_LOCAL_CARRIER_AND_INPUT_BYTES",
    }
