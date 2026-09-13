#!/usr/bin/env python3
"""Validate the workstation-local Zot OCI distribution carrier.

This doctor owns no registry semantics. It checks that the source-controlled deployment
spec is exactly materialized, the systemd/Podman carrier is running the pinned Zot image,
the service is loopback-bound, OCI Distribution is reachable, and an optional known
subject/referrer remains discoverable through ORAS after service lifecycle operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_CONFIG = ROOT / "config/zot/local-registry-r1.json"
SOURCE_QUADLET = ROOT / "systemd/ordivon-artifact-v2-zot-r1.container"
MATERIALIZED_CONFIG = Path("/etc/ordivon/artifact-v2/zot/config.json")
MATERIALIZED_QUADLET = Path("/etc/containers/systemd/ordivon-artifact-v2-zot-r1.container")
STORAGE = Path("/root/.local/share/ordivon-workstation/artifact-v2-zot-r1")
SERVICE = "ordivon-artifact-v2-zot-r1.service"
CONTAINER = "ordivon-artifact-v2-zot-r1"
IMAGE = "ghcr.io/project-zot/zot-linux-amd64@sha256:95a837a0afacf5b7edc0c92493f04beee6891989b8d2fd50a00cf65a1e6d4fd5"
IMAGE_DIGEST = "sha256:95a837a0afacf5b7edc0c92493f04beee6891989b8d2fd50a00cf65a1e6d4fd5"
ORAS = Path(os.environ.get("ARTIFACT_ORAS", "/opt/ordivon/external/oras/1.3.4/bin/oras"))
BASE_URL = "http://127.0.0.1:5080"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def run(args: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=timeout)


def check(checks: list[dict[str, Any]], name: str, ok: bool, **details: Any) -> None:
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", **details})


def static_configuration_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    try:
        value = json.loads(SOURCE_CONFIG.read_text())
        storage = value.get("storage", {})
        http = value.get("http", {})
        ok = (
            value.get("distSpecVersion") == "1.1.1"
            and storage.get("rootDirectory") == "/var/lib/zot"
            and storage.get("dedupe") is True
            and storage.get("gc") is True
            and storage.get("commit") is False
            and http.get("address") == "127.0.0.1"
            and str(http.get("port")) == "5080"
        )
        check(checks, "source-zot-config-boundary", ok, config=value)
    except Exception as exc:
        check(checks, "source-zot-config-boundary", False, error=str(exc))

    try:
        text = SOURCE_QUADLET.read_text()
        required = [
            f"Image={IMAGE}",
            "Pull=never",
            "Network=host",
            "ReadOnly=true",
            "Volume=/etc/ordivon/artifact-v2/zot/config.json:/etc/zot/config.json:ro",
            "Volume=/root/.local/share/ordivon-workstation/artifact-v2-zot-r1:/var/lib/zot:rw",
            "Exec=serve /etc/zot/config.json",
        ]
        missing = [item for item in required if item not in text]
        check(checks, "source-quadlet-boundary", not missing, missing=missing)
    except Exception as exc:
        check(checks, "source-quadlet-boundary", False, error=str(exc))
    return checks


def http_json(path: str) -> Any:
    with urllib.request.urlopen(BASE_URL + path, timeout=5) as response:
        body = response.read()
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return json.loads(body) if body else None


def runtime_checks(smoke_subject_digest: str | None, smoke_referrer_digest: str | None) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for source, materialized, name in [
        (SOURCE_CONFIG, MATERIALIZED_CONFIG, "config-materialization"),
        (SOURCE_QUADLET, MATERIALIZED_QUADLET, "quadlet-materialization"),
    ]:
        if source.is_file() and materialized.is_file():
            s, m = sha256_file(source), sha256_file(materialized)
            check(checks, name, s == m, sourceSha256=s, materializedSha256=m)
        else:
            check(checks, name, False, sourceExists=source.is_file(), materializedExists=materialized.is_file())

    svc = run(["systemctl", "is-active", SERVICE])
    check(checks, "systemd-service-active", svc.returncode == 0 and svc.stdout.strip() == "active", stdout=svc.stdout.strip(), stderr=svc.stderr.strip())

    inspect = run([
        "podman", "inspect", CONTAINER, "--format",
        "{{json .ImageName}}|{{json .HostConfig.NetworkMode}}|{{json .HostConfig.ReadonlyRootfs}}|{{json .Mounts}}",
    ])
    inspect_ok = False
    inspect_details: dict[str, Any] = {"stdout": inspect.stdout.strip(), "stderr": inspect.stderr.strip()}
    if inspect.returncode == 0:
        try:
            image_json, network_json, readonly_json, mounts_json = inspect.stdout.strip().split("|", 3)
            image = json.loads(image_json)
            network = json.loads(network_json)
            readonly = json.loads(readonly_json)
            mounts = json.loads(mounts_json)
            pairs = {(m.get("Source"), m.get("Destination"), bool(m.get("RW"))) for m in mounts}
            inspect_ok = (
                image == IMAGE
                and network == "host"
                and readonly is True
                and (str(MATERIALIZED_CONFIG), "/etc/zot/config.json", False) in pairs
                and (str(STORAGE), "/var/lib/zot", True) in pairs
            )
            inspect_details.update({"image": image, "network": network, "readOnly": readonly, "mounts": mounts})
        except Exception as exc:
            inspect_details["parseError"] = str(exc)
    check(checks, "podman-carrier-boundary", inspect_ok, **inspect_details)

    image = run(["podman", "image", "inspect", IMAGE, "--format", "{{.Digest}}"])
    observed_digest = image.stdout.strip()
    check(checks, "pinned-image-present", image.returncode == 0 and observed_digest == IMAGE_DIGEST, digest=observed_digest, stderr=image.stderr.strip())

    listen = run(["ss", "-ltn"])
    lines = [line for line in listen.stdout.splitlines() if ":5080" in line]
    loopback_only = bool(lines) and all("127.0.0.1:5080" in line for line in lines)
    check(checks, "loopback-listener", listen.returncode == 0 and loopback_only, listeners=lines)

    try:
        http_json("/v2/")
        check(checks, "oci-distribution-api", True)
    except Exception as exc:
        check(checks, "oci-distribution-api", False, error=str(exc))

    try:
        catalog = http_json("/v2/_catalog")
        repos = sorted(catalog.get("repositories", [])) if isinstance(catalog, dict) else []
        check(checks, "registry-catalog", bool(repos), repositories=repos)
    except Exception as exc:
        check(checks, "registry-catalog", False, error=str(exc))

    if smoke_subject_digest:
        ref = f"127.0.0.1:5080/ordivon/artifact-r2-closure-smoke@{smoke_subject_digest}"
        if not ORAS.is_file():
            check(checks, "closure-smoke-referrer", False, error=f"ORAS absent: {ORAS}")
        else:
            proc = run([str(ORAS), "discover", "--plain-http", ref, "--format", "json"])
            ok = False
            details: dict[str, Any] = {"returnCode": proc.returncode, "stderr": proc.stderr[-2000:]}
            if proc.returncode == 0:
                try:
                    value = json.loads(proc.stdout)
                    refs = value.get("referrers", [])
                    observed = sorted(str(x.get("digest")) for x in refs)
                    ok = value.get("digest") == smoke_subject_digest and (
                        smoke_referrer_digest is None or smoke_referrer_digest in observed
                    )
                    details.update({"subjectDigest": value.get("digest"), "referrerDigests": observed})
                except Exception as exc:
                    details["parseError"] = str(exc)
            check(checks, "closure-smoke-referrer", ok, **details)
    return checks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--static-only", action="store_true")
    ap.add_argument("--smoke-subject-digest")
    ap.add_argument("--smoke-referrer-digest")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    checks = static_configuration_checks()
    if not args.static_only:
        checks.extend(runtime_checks(args.smoke_subject_digest, args.smoke_referrer_digest))
    result = {
        "schemaVersion": 1,
        "kind": "artifact-local-oci-registry-doctor",
        "status": "PASS" if all(x["status"] == "PASS" for x in checks) else "FAIL",
        "checks": checks,
        "boundary": (
            "PASS establishes exact source/materialized deployment identity, the pinned local Zot carrier, "
            "loopback-only reachability and OCI Distribution/referrer availability. It does not establish "
            "public registry TLS/auth, remote availability, multi-user policy, artifact scientific/business "
            "validity, or keyless Sigstore trust."
        ),
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    sys.stdout.write(text)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
