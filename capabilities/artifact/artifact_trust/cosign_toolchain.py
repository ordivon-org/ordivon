from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from artifact_core.contracts import sha256_file
from artifact_core.json_validation import load_json

ROOT = Path(__file__).resolve().parents[1]

GLOBAL_ARTIFACT_TOOLCHAIN_ROOT = Path(
    os.environ.get("ARTIFACT_TOOLCHAIN_ROOT", "/opt/ordivon/external/artifact-toolchain")
)

GLOBAL_COSIGN = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "cosign/3.1.3/bin/cosign"

GLOBAL_COSIGN_ARCH_PACKAGE = (
    GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "cosign/3.1.3/provenance/cosign-3.1.3-1-x86_64.pkg.tar.zst"
)

GLOBAL_COSIGN_ARCH_PACKAGE_SIGNATURE = (
    GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "cosign/3.1.3/provenance/cosign-3.1.3-1-x86_64.pkg.tar.zst.sig"
)

COSIGN_STANDARD_BUNDLE_MIN_VERSION = (3, 0, 6)


def _selected_external_file(env_name: str, global_candidate: Path) -> Path:
    configured = os.environ.get(env_name)
    return Path(configured) if configured else global_candidate


COSIGN_LOCK_PATH = ROOT / "artifact-delivery/toolchain-v1.lock.json"

COSIGN_SELECTED_BINARY = _selected_external_file("ARTIFACT_COSIGN", GLOBAL_COSIGN)

COSIGN_ARCH_PACKAGE = _selected_external_file(
    "ARTIFACT_COSIGN_ARCH_PACKAGE",
    GLOBAL_COSIGN_ARCH_PACKAGE,
)

COSIGN_ARCH_PACKAGE_SIGNATURE = _selected_external_file(
    "ARTIFACT_COSIGN_ARCH_PACKAGE_SIGNATURE",
    GLOBAL_COSIGN_ARCH_PACKAGE_SIGNATURE,
)

_COSIGN_PROVENANCE_CACHE: dict[tuple[str, str, str], dict[str, Any]] = {}


@dataclass(frozen=True)
class TrustToolchainConfig:
    lock_path: Path
    selected_binary: Path
    arch_package: Path
    arch_package_signature: Path


def default_trust_toolchain_config() -> TrustToolchainConfig:
    return TrustToolchainConfig(
        lock_path=COSIGN_LOCK_PATH,
        selected_binary=COSIGN_SELECTED_BINARY,
        arch_package=COSIGN_ARCH_PACKAGE,
        arch_package_signature=COSIGN_ARCH_PACKAGE_SIGNATURE,
    )


def _cosign_executable(toolchain: TrustToolchainConfig) -> Path | None:
    configured = os.environ.get("ARTIFACT_COSIGN")
    if configured:
        path = Path(configured)
        return path if path.is_file() and os.access(path, os.X_OK) else None
    if toolchain.selected_binary.is_file() and os.access(toolchain.selected_binary, os.X_OK):
        return toolchain.selected_binary
    candidate = shutil.which("cosign")
    return Path(candidate) if candidate else None


def _cosign_selection_provenance(
    executable: Path,
    executable_digest: str,
    cosign_lock: dict[str, Any],
    toolchain: TrustToolchainConfig,
) -> dict[str, Any]:
    failures: list[str] = []
    if cosign_lock.get("originStanding") != "ARCH_REPOSITORY_PACKAGE_SIGNATURE_VERIFIED":
        failures.append("Cosign origin standing is not an accepted signed Arch repository package")
    if not toolchain.arch_package.is_file():
        failures.append("signed Arch Cosign package is absent")
    if not toolchain.arch_package_signature.is_file():
        failures.append("Arch Cosign package detached signature is absent")
    pacman_key = shutil.which("pacman-key")
    if not pacman_key:
        failures.append("pacman-key is unavailable for Cosign package provenance verification")
    bsdtar = shutil.which("bsdtar")
    if not bsdtar:
        failures.append("bsdtar is unavailable for signed Cosign package inspection")
    expected_binary_digest = cosign_lock.get("binarySha256")
    if not isinstance(expected_binary_digest, str) or executable_digest != expected_binary_digest:
        failures.append(
            "selected Cosign binary digest does not match the locked signed-package binary digest"
        )
    if failures:
        return {
            "status": "FAIL",
            "authority": "Arch Linux package signing keyring",
            "package": str(toolchain.arch_package),
            "signature": str(toolchain.arch_package_signature),
            "failures": failures,
        }

    package_digest = sha256_file(toolchain.arch_package)
    signature_digest = sha256_file(toolchain.arch_package_signature)
    cache_key = (package_digest, signature_digest, executable_digest)
    cached = _COSIGN_PROVENANCE_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached)

    if package_digest != cosign_lock.get("archPackageSha256"):
        failures.append("Arch Cosign package digest does not match the lock")
    if signature_digest != cosign_lock.get("archPackageSignatureSha256"):
        failures.append("Arch Cosign package signature digest does not match the lock")

    signature_check = subprocess.run(
        [
            str(pacman_key),
            "--verify",
            str(toolchain.arch_package_signature),
            str(toolchain.arch_package),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    signature_text = signature_check.stdout + "\n" + signature_check.stderr
    expected_fingerprint = str(cosign_lock.get("archPackageSignerFingerprint", ""))
    if signature_check.returncode != 0:
        failures.append("Arch Cosign package signature verification failed")
    if not expected_fingerprint or expected_fingerprint not in signature_text:
        failures.append("Arch Cosign package signer fingerprint does not match the lock")
    if "Good signature" not in signature_text:
        failures.append("Arch Cosign package signature was not reported as good")

    pkginfo = subprocess.run(
        [str(bsdtar), "-xOf", str(toolchain.arch_package), ".PKGINFO"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    expected_package_version = str(cosign_lock.get("archPackageVersion", ""))
    if pkginfo.returncode != 0:
        failures.append("signed Arch Cosign package metadata could not be read")
    elif f"pkgver = {expected_package_version}" not in pkginfo.stdout:
        failures.append("signed Arch Cosign package version does not match the lock")

    embedded_digest: str | None = None
    extractor = subprocess.Popen(
        [str(bsdtar), "-xOf", str(toolchain.arch_package), "usr/bin/cosign"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if extractor.stdout is not None:
        embedded_hash = hashlib.sha256()
        for chunk in iter(lambda: extractor.stdout.read(1024 * 1024), b""):
            embedded_hash.update(chunk)
        embedded_digest = embedded_hash.hexdigest()
        extractor.stdout.close()
    if extractor.stderr is not None:
        extractor_stderr = extractor.stderr.read().decode("utf-8", errors="replace")
        extractor.stderr.close()
    else:
        extractor_stderr = ""
    extractor_returncode = extractor.wait(timeout=30)
    if extractor_returncode != 0:
        failures.append(
            f"signed Arch Cosign package binary extraction failed: {extractor_stderr[-1000:]}"
        )
    elif embedded_digest != expected_binary_digest:
        failures.append(
            "selected Cosign binary is not byte-identical to usr/bin/cosign in the signed Arch package"
        )

    result = {
        "status": "PASS" if not failures else "FAIL",
        "authority": "Arch Linux package signing keyring",
        "originStanding": cosign_lock.get("originStanding"),
        "package": {
            "path": str(toolchain.arch_package.resolve()),
            "version": expected_package_version,
            "sha256": package_digest,
        },
        "signature": {
            "path": str(toolchain.arch_package_signature.resolve()),
            "sha256": signature_digest,
            "returnCode": signature_check.returncode,
            "signerFingerprint": expected_fingerprint,
            "signer": cosign_lock.get("archPackageSigner"),
            "status": cosign_lock.get("archPackageSignatureStatus"),
        },
        "embeddedBinarySha256": embedded_digest,
        "selectedBinarySha256": executable_digest,
        "failures": failures,
        "boundary": "PASS proves the selected verifier bytes are byte-identical to usr/bin/cosign inside the exact digest-pinned Arch package whose detached signature verifies under the local Arch package keyring and locked signer fingerprint. It does not claim the bytes are the upstream Sigstore release binary.",
    }
    _COSIGN_PROVENANCE_CACHE[cache_key] = dict(result)
    return result


def cosign_tool_fact(toolchain: TrustToolchainConfig | None = None) -> dict[str, Any]:
    config = toolchain or default_trust_toolchain_config()
    executable = _cosign_executable(config)
    if executable is None:
        return {"status": "NOT_AVAILABLE", "error": "cosign executable is unavailable"}
    proc = subprocess.run(
        [str(executable), "version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )
    output = proc.stdout + "\n" + proc.stderr
    match = re.search(r"GitVersion:\s*v(\d+)\.(\d+)\.(\d+)(?:[^\s]*)?", output)
    version = tuple(int(item) for item in match.groups()) if match else None
    digest = sha256_file(executable)
    lock_error: str | None = None
    cosign_lock: dict[str, Any] = {}
    if config.lock_path.is_file():
        try:
            value = load_json(config.lock_path)
            candidate = value.get("cosign", {}) if isinstance(value, dict) else {}
            if isinstance(candidate, dict):
                cosign_lock = candidate
            else:
                lock_error = "toolchain lock cosign entry is not an object"
        except Exception as error:
            lock_error = str(error)
    else:
        lock_error = "toolchain lock is absent"
    expected_digest = cosign_lock.get("binarySha256") if cosign_lock else None
    expected_version = cosign_lock.get("observedVersion") if cosign_lock else None
    digest_ok = isinstance(expected_digest, str) and digest == expected_digest
    version_text = ".".join(str(item) for item in version) if version else None
    version_ok = isinstance(expected_version, str) and version_text == expected_version
    provenance = (
        _cosign_selection_provenance(executable, digest, cosign_lock, config)
        if lock_error is None and cosign_lock
        else {"status": "FAIL", "failures": [lock_error or "Cosign lock is unavailable"]}
    )
    status_ok = (
        proc.returncode == 0
        and version is not None
        and digest_ok
        and version_ok
        and provenance.get("status") == "PASS"
    )
    return {
        "status": "PASS" if status_ok else "FAIL",
        "path": str(executable.resolve()),
        "sha256": digest,
        "lockedSha256": expected_digest,
        "lockedDigestMatched": digest_ok,
        "version": version_text,
        "lockedVersion": expected_version,
        "lockedVersionMatched": version_ok,
        "versionTuple": list(version) if version else None,
        "rawVersion": output.strip()[:4000],
        "exitCode": proc.returncode,
        "lockError": lock_error,
        "provenance": provenance,
    }


def _version_at_least(observed: Iterable[int], minimum: tuple[int, int, int]) -> bool:
    values = tuple(int(item) for item in observed)
    return values >= minimum
