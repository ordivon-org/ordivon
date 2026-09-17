from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Iterable
import urllib.parse

from artifact_core.contracts import file_fact, sha256_file
from artifact_core.profile_v1 import validate_profile_v1 as validate_profile
from artifact_trust.provenance import IN_TOTO_STATEMENT_V1, utc_now

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_ARTIFACT_TOOLCHAIN_ROOT = Path(os.environ.get("ARTIFACT_TOOLCHAIN_ROOT", "/opt/ordivon/external/artifact-toolchain"))
GLOBAL_COSIGN = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "cosign/3.1.3/bin/cosign"
GLOBAL_COSIGN_ARCH_PACKAGE = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "cosign/3.1.3/provenance/cosign-3.1.3-1-x86_64.pkg.tar.zst"
GLOBAL_COSIGN_ARCH_PACKAGE_SIGNATURE = GLOBAL_ARTIFACT_TOOLCHAIN_ROOT / "cosign/3.1.3/provenance/cosign-3.1.3-1-x86_64.pkg.tar.zst.sig"
DEFAULT_VSA_TRUST_POLICY_SCHEMA = ROOT / "artifact-delivery/vsa-trust-policy-v1.schema.json"
SLSA_VERIFICATION_SUMMARY_V1 = "https://slsa.dev/verification_summary/v1"
SLSA_VERSION = "1.2"
LOCAL_VSA_VERIFIER_ID = "https://ordivon.local/verifiers/artifact-delivery-v1"
SIGSTORE_BUNDLE_V03 = "application/vnd.dev.sigstore.bundle.v0.3+json"
INTOTO_DSSE_PAYLOAD_TYPE = "application/vnd.in-toto+json"
COSIGN_STANDARD_BUNDLE_MIN_VERSION = (3, 0, 6)
VSA_GATE_NAMES = frozenset({
    "profileSchema", "structural", "dependency", "semantic", "visual",
    "target", "accessibility", "conformance", "deliveryReadback",
})
ASSEMBLY_GATE_NAMES = frozenset({"companionPdf", "releaseProvenance"})


def _selected_external_file(env_name: str, global_candidate: Path, legacy_candidate: Path) -> Path:
    configured = os.environ.get(env_name)
    if configured:
        return Path(configured)
    if global_candidate.is_file():
        return global_candidate
    if legacy_candidate.is_file():
        return legacy_candidate
    return global_candidate


COSIGN_LOCK_PATH = ROOT / "artifact-delivery/toolchain-v1.lock.json"
COSIGN_SELECTED_BINARY = _selected_external_file(
    "ARTIFACT_COSIGN", GLOBAL_COSIGN, ROOT / ".cache/artifact-toolchain/cosign/current/bin/cosign"
)
COSIGN_ARCH_PACKAGE = _selected_external_file(
    "ARTIFACT_COSIGN_ARCH_PACKAGE",
    GLOBAL_COSIGN_ARCH_PACKAGE,
    ROOT / ".cache/artifact-toolchain/cosign/bootstrap-arch-3.1.3-1/cosign-3.1.3-1-x86_64.pkg.tar.zst",
)
COSIGN_ARCH_PACKAGE_SIGNATURE = _selected_external_file(
    "ARTIFACT_COSIGN_ARCH_PACKAGE_SIGNATURE",
    GLOBAL_COSIGN_ARCH_PACKAGE_SIGNATURE,
    Path(str(ROOT / ".cache/artifact-toolchain/cosign/bootstrap-arch-3.1.3-1/cosign-3.1.3-1-x86_64.pkg.tar.zst") + ".sig"),
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_uri(value: str, field: str) -> str:
    if not urllib.parse.urlparse(value).scheme:
        raise RuntimeError(f"{field} must be a URI")
    return value



def validate_json_document(document_path: Path, schema_path: Path, expected_kind: str | None = None) -> dict[str, Any]:
    value = load_json(document_path)
    schema = load_json(schema_path)
    failures: list[str] = []
    if not isinstance(value, dict):
        failures.append("document must be a JSON object")
    elif expected_kind is not None and value.get("kind") != expected_kind:
        failures.append(f"document kind must equal {expected_kind}")
    validator = "jsonschema"
    schema_status = "NOT_RUN"
    schema_error: str | None = None
    if importlib.util.find_spec("jsonschema") is None:
        validator = "unavailable"
        schema_error = "Python jsonschema package is not installed"
    else:
        try:
            import jsonschema  # type: ignore

            jsonschema.Draft202012Validator.check_schema(schema)
            instance = dict(value) if isinstance(value, dict) else value
            if isinstance(instance, dict):
                instance.pop("$schema", None)
            jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(instance)
            schema_status = "PASS"
        except Exception as error:
            schema_status = "FAIL"
            schema_error = str(error)
            failures.append(f"JSON Schema validation failed: {error}")
    return {
        "status": "PASS" if not failures and schema_status == "PASS" else "FAIL",
        "document": value,
        "failures": failures,
        "jsonSchema": {
            "dialect": "https://json-schema.org/draft/2020-12/schema",
            "validator": validator,
            "status": schema_status,
            "error": schema_error,
            "schemaPath": str(schema_path.resolve()),
        },
    }


def ni_sha256_uri(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).digest()
    value = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"ni:///sha-256;{value}"


def verification_summary_statement(
    subject: Path,
    profile_path: Path,
    verifier_id: str,
    verifier_versions: dict[str, str],
    passed: bool,
) -> dict[str, Any]:
    verifier_id = _require_uri(verifier_id, "verifier-id")
    profile_uri = profile_path.resolve().as_uri()
    subject_uri = ni_sha256_uri(subject)
    return {
        "_type": IN_TOTO_STATEMENT_V1,
        "subject": [{"name": subject.name, "digest": {"sha256": sha256_file(subject)}}],
        "predicateType": SLSA_VERIFICATION_SUMMARY_V1,
        "predicate": {
            "verifier": {"id": verifier_id, "version": dict(sorted(verifier_versions.items()))},
            "timeVerified": utc_now(),
            "resourceUri": subject_uri,
            "policy": {
                "uri": profile_uri,
                "digest": {"sha256": sha256_file(profile_path)},
            },
            "verificationResult": "PASSED" if passed else "FAILED",
            "verifiedLevels": ["SLSA_BUILD_LEVEL_UNEVALUATED" if passed else "FAILED"],
            "slsaVersion": SLSA_VERSION,
        },
    }


def verify_verification_summary(
    statement_path: Path,
    subject: Path,
    profile_path: Path,
    allowed_verifiers: Iterable[str] = (),
) -> dict[str, Any]:
    value = load_json(statement_path)
    failures: list[str] = []
    expected_subject = {subject.name: sha256_file(subject)}
    observed_subject: dict[str, str] = {}
    if value.get("_type") != IN_TOTO_STATEMENT_V1:
        failures.append("verification summary is not an in-toto Statement v1")
    if value.get("predicateType") != SLSA_VERIFICATION_SUMMARY_V1:
        failures.append("predicateType is not SLSA Verification Summary v1")
    for item in value.get("subject", []) if isinstance(value.get("subject"), list) else []:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            digest = item.get("digest", {}).get("sha256") if isinstance(item.get("digest"), dict) else None
            if isinstance(digest, str):
                observed_subject[item["name"]] = digest
    if observed_subject != expected_subject:
        failures.append("verification summary subject does not exactly bind the artifact")
    predicate = value.get("predicate", {}) if isinstance(value.get("predicate"), dict) else {}
    verifier = predicate.get("verifier", {}) if isinstance(predicate.get("verifier"), dict) else {}
    verifier_id = verifier.get("id")
    if not isinstance(verifier_id, str) or not urllib.parse.urlparse(verifier_id).scheme:
        failures.append("verification summary verifier.id is absent or not a URI")
    allowed = set(allowed_verifiers)
    if allowed and verifier_id not in allowed:
        failures.append("verification summary verifier.id is not allowed for this gate")
    policy = predicate.get("policy", {}) if isinstance(predicate.get("policy"), dict) else {}
    if policy.get("uri") != profile_path.resolve().as_uri():
        failures.append("verification summary policy URI does not bind the selected delivery profile")
    if policy.get("digest", {}).get("sha256") != sha256_file(profile_path):
        failures.append("verification summary policy digest does not bind the selected delivery profile")
    if predicate.get("resourceUri") != ni_sha256_uri(subject):
        failures.append("verification summary resourceUri does not bind the artifact content via RFC 6920 ni URI")
    input_attestations = predicate.get("inputAttestations")
    if input_attestations not in (None, []):
        failures.append("local v1 verification summaries must not misuse inputAttestations for raw validator output")

    verification_result = predicate.get("verificationResult")
    if verification_result not in {"PASSED", "FAILED"}:
        failures.append("verificationResult must be PASSED or FAILED")
    levels = predicate.get("verifiedLevels")
    if not isinstance(levels, list) or not levels:
        failures.append("verifiedLevels is absent or empty")
    elif verification_result == "PASSED" and "SLSA_BUILD_LEVEL_UNEVALUATED" not in levels:
        failures.append("PASSED non-SLSA policy verification must remain BUILD_LEVEL_UNEVALUATED")
    if predicate.get("slsaVersion") != SLSA_VERSION:
        failures.append(f"unexpected slsaVersion; expected {SLSA_VERSION}")
    return {
        "status": "PASS" if not failures else "FAIL",
        "statement": file_fact(statement_path),
        "subject": file_fact(subject),
        "profile": file_fact(profile_path),
        "verifier": verifier,
        "verificationResult": verification_result,
        "inputAttestations": input_attestations,
        "authenticity": "NOT_VERIFIED",
        "failures": failures,
        "boundary": "This validates unsigned in-toto/SLSA VSA structure and exact local digest bindings. External trust still requires signature/root-of-trust verification; do not treat this result as cryptographic authenticity.",
    }


def _resolve_policy_path(policy_path: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate.resolve() if candidate.is_absolute() else (policy_path.resolve().parent / candidate).resolve()


def _minimal_vsa_trust_policy_checks(value: Any) -> list[str]:
    failures: list[str] = []
    if not isinstance(value, dict):
        return ["VSA trust policy must be a JSON object"]
    if value.get("policyVersion") != 1:
        failures.append("policyVersion must equal 1")
    accepted = value.get("acceptedBundleMediaTypes")
    if accepted != [SIGSTORE_BUNDLE_V03] and not (
        isinstance(accepted, list) and accepted and set(accepted) == {SIGSTORE_BUNDLE_V03}
    ):
        failures.append("acceptedBundleMediaTypes must contain only the standardized Sigstore v0.3 JSON bundle media type")
    signers = value.get("signers")
    if not isinstance(signers, list) or not signers:
        failures.append("signers must be a non-empty array")
        return failures
    seen: set[str] = set()
    for signer in signers:
        if not isinstance(signer, dict):
            failures.append("every signer must be an object")
            continue
        signer_id = signer.get("id")
        if not isinstance(signer_id, str) or not signer_id:
            failures.append("every signer requires a non-empty id")
        elif signer_id in seen:
            failures.append(f"duplicate signer id: {signer_id}")
        else:
            seen.add(signer_id)
        mode = signer.get("mode")
        if mode not in {"public-key", "keyless"}:
            failures.append(f"unsupported signer mode for {signer_id}: {mode}")
        allowed = signer.get("allowedVerifierIds")
        if not isinstance(allowed, list) or not allowed:
            failures.append(f"signer {signer_id} requires allowedVerifierIds")
        else:
            for verifier_id in allowed:
                if not isinstance(verifier_id, str) or not urllib.parse.urlparse(verifier_id).scheme:
                    failures.append(f"signer {signer_id} contains a verifier id that is not a URI")
        if not isinstance(signer.get("requireTransparencyLog"), bool):
            failures.append(f"signer {signer_id} requires boolean requireTransparencyLog")
        if mode == "public-key":
            public_key = signer.get("publicKey")
            if not isinstance(public_key, dict) or not isinstance(public_key.get("path"), str):
                failures.append(f"public-key signer {signer_id} requires publicKey.path")
            if not isinstance(public_key, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(public_key.get("sha256", ""))):
                failures.append(f"public-key signer {signer_id} requires lowercase publicKey.sha256")
        if mode == "keyless":
            if signer.get("requireTransparencyLog") is not True:
                failures.append(f"keyless signer {signer_id} must require transparency-log verification")
            if not isinstance(signer.get("certificateIdentity"), str) or not signer.get("certificateIdentity"):
                failures.append(f"keyless signer {signer_id} requires certificateIdentity")
            issuer = signer.get("certificateOidcIssuer")
            if not isinstance(issuer, str) or not urllib.parse.urlparse(issuer).scheme:
                failures.append(f"keyless signer {signer_id} requires a URI certificateOidcIssuer")
            trusted_root = signer.get("trustedRoot")
            if trusted_root is not None:
                if not isinstance(trusted_root, dict) or not isinstance(trusted_root.get("path"), str):
                    failures.append(f"keyless signer {signer_id} trustedRoot requires path")
                if not isinstance(trusted_root, dict) or not re.fullmatch(r"[0-9a-f]{64}", str(trusted_root.get("sha256", ""))):
                    failures.append(f"keyless signer {signer_id} trustedRoot requires lowercase sha256")
    return failures


def validate_vsa_trust_policy(
    policy_path: Path,
    schema_path: Path = DEFAULT_VSA_TRUST_POLICY_SCHEMA,
) -> dict[str, Any]:
    result = validate_json_document(policy_path, schema_path)
    policy = result.get("document", {})
    failures = list(result.get("failures", []))
    failures.extend(_minimal_vsa_trust_policy_checks(policy))
    resolved_signers: dict[str, Any] = {}
    if isinstance(policy, dict):
        for signer in policy.get("signers", []) if isinstance(policy.get("signers"), list) else []:
            if not isinstance(signer, dict) or not isinstance(signer.get("id"), str):
                continue
            resolved = dict(signer)
            if signer.get("mode") == "public-key" and isinstance(signer.get("publicKey"), dict):
                public_key = signer["publicKey"]
                if isinstance(public_key.get("path"), str):
                    key_path = _resolve_policy_path(policy_path, public_key["path"])
                    key_fact: dict[str, Any] | None = None
                    if not key_path.is_file():
                        failures.append(f"trusted public key is absent for signer {signer['id']}: {key_path}")
                    else:
                        key_fact = file_fact(key_path)
                        if key_fact["digest"]["sha256"] != public_key.get("sha256"):
                            failures.append(f"trusted public key digest mismatch for signer {signer['id']}")
                    resolved["publicKeyResolved"] = key_fact
                    resolved["publicKeyPath"] = str(key_path)
            trusted_root = signer.get("trustedRoot")
            if isinstance(trusted_root, dict) and isinstance(trusted_root.get("path"), str):
                root_path = _resolve_policy_path(policy_path, trusted_root["path"])
                root_fact: dict[str, Any] | None = None
                if not root_path.is_file():
                    failures.append(f"trustedRoot is absent for signer {signer['id']}: {root_path}")
                else:
                    root_fact = file_fact(root_path)
                    if root_fact["digest"]["sha256"] != trusted_root.get("sha256"):
                        failures.append(f"trustedRoot digest mismatch for signer {signer['id']}")
                resolved["trustedRootResolved"] = root_fact
                resolved["trustedRootPath"] = str(root_path)
            resolved_signers[signer["id"]] = resolved
    schema_ok = result.get("jsonSchema", {}).get("status") == "PASS"
    return {
        "status": "PASS" if schema_ok and not failures else "FAIL",
        "policy": policy,
        "policyFact": file_fact(policy_path),
        "resolvedSigners": resolved_signers,
        "jsonSchema": result.get("jsonSchema"),
        "failures": failures,
    }


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
        failures.append("selected Cosign binary digest does not match the locked signed-package binary digest")
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
        [str(pacman_key), "--verify", str(toolchain.arch_package_signature), str(toolchain.arch_package)],
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
        failures.append(f"signed Arch Cosign package binary extraction failed: {extractor_stderr[-1000:]}")
    elif embedded_digest != expected_binary_digest:
        failures.append("selected Cosign binary is not byte-identical to usr/bin/cosign in the signed Arch package")

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


def verify_sigstore_vsa_bundle_shape(
    bundle_path: Path,
    statement_path: Path,
    accepted_media_types: Iterable[str],
    signer_mode: str,
) -> dict[str, Any]:
    failures: list[str] = []
    bundle = load_json(bundle_path)
    statement = load_json(statement_path)
    accepted = set(accepted_media_types)
    media_type = bundle.get("mediaType") if isinstance(bundle, dict) else None
    if media_type != SIGSTORE_BUNDLE_V03 or media_type not in accepted:
        failures.append("bundle is not an explicitly accepted standardized Sigstore v0.3 JSON bundle")
    envelope = bundle.get("dsseEnvelope") if isinstance(bundle, dict) else None
    signed_statement: Any = None
    if not isinstance(envelope, dict):
        failures.append("Sigstore bundle does not contain a DSSE envelope")
    else:
        if envelope.get("payloadType") != INTOTO_DSSE_PAYLOAD_TYPE:
            failures.append("DSSE payloadType is not application/vnd.in-toto+json")
        signatures = envelope.get("signatures")
        if not isinstance(signatures, list) or not signatures:
            failures.append("DSSE envelope contains no signature")
        payload = envelope.get("payload")
        if not isinstance(payload, str):
            failures.append("DSSE envelope payload is absent")
        else:
            try:
                decoded = base64.b64decode(payload, validate=True)
                signed_statement = json.loads(decoded)
            except Exception as error:
                failures.append(f"DSSE payload is not valid base64 JSON: {error}")
    if signed_statement is not None and signed_statement != statement:
        failures.append("detached VSA statement does not exactly match the JSON object authenticated by the DSSE bundle")
    verification_material = bundle.get("verificationMaterial") if isinstance(bundle, dict) else None
    tlog_entries: list[Any] = []
    if not isinstance(verification_material, dict):
        failures.append("Sigstore bundle verificationMaterial is absent")
    else:
        raw_entries = verification_material.get("tlogEntries")
        if isinstance(raw_entries, list):
            tlog_entries = raw_entries
        if signer_mode == "public-key" and not isinstance(verification_material.get("publicKey"), dict):
            failures.append("public-key signer requires standardized bundle publicKey verification material")
        if signer_mode == "keyless":
            if not isinstance(verification_material.get("certificate"), dict):
                failures.append("keyless signer requires standardized bundle leaf certificate verification material")
            if isinstance(verification_material.get("publicKey"), dict):
                failures.append("keyless signer bundle must not substitute raw publicKey verification material")
    return {
        "status": "PASS" if not failures else "FAIL",
        "bundle": file_fact(bundle_path),
        "mediaType": media_type,
        "payloadType": envelope.get("payloadType") if isinstance(envelope, dict) else None,
        "signatureCount": len(envelope.get("signatures", [])) if isinstance(envelope, dict) and isinstance(envelope.get("signatures"), list) else 0,
        "tlogEntryCount": len(tlog_entries),
        "signedStatementMatches": signed_statement == statement if signed_statement is not None else False,
        "failures": failures,
    }


def verify_signed_verification_summary(
    statement_path: Path,
    bundle_path: Path,
    subject: Path,
    profile_path: Path,
    trust_policy_path: Path,
    signer_id: str,
    toolchain: TrustToolchainConfig | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    policy_result = validate_vsa_trust_policy(trust_policy_path)
    if policy_result.get("status") != "PASS":
        failures.append("VSA trust policy did not PASS validation")
    signer = policy_result.get("resolvedSigners", {}).get(signer_id)
    if not isinstance(signer, dict):
        failures.append(f"trusted signer id is absent from policy: {signer_id}")
        signer = {}
    semantic = verify_verification_summary(statement_path, subject, profile_path)
    if semantic.get("status") != "PASS":
        failures.append("VSA semantic/digest binding validation failed")
    verifier_id = semantic.get("verifier", {}).get("id") if isinstance(semantic.get("verifier"), dict) else None
    if signer and verifier_id not in set(signer.get("allowedVerifierIds", [])):
        failures.append("VSA verifier.id is not authorized for the selected signer")
    accepted = policy_result.get("policy", {}).get("acceptedBundleMediaTypes", []) if isinstance(policy_result.get("policy"), dict) else []
    mode = str(signer.get("mode", ""))
    bundle_shape = verify_sigstore_vsa_bundle_shape(bundle_path, statement_path, accepted, mode) if bundle_path.is_file() else {
        "status": "FAIL", "failures": ["Sigstore bundle is absent"]
    }
    if bundle_shape.get("status") != "PASS":
        failures.append("Sigstore bundle shape/statement binding validation failed")
    if signer.get("requireTransparencyLog") is True and bundle_shape.get("tlogEntryCount", 0) < 1:
        failures.append("trust policy requires transparency-log evidence but bundle has no tlog entry")

    tool = cosign_tool_fact(toolchain)
    if tool.get("status") != "PASS":
        failures.append("cosign verifier provenance/version/digest validation failed")
    version_tuple = tuple(tool.get("versionTuple") or [])
    minimum = COSIGN_STANDARD_BUNDLE_MIN_VERSION
    if version_tuple and not _version_at_least(version_tuple, minimum):
        failures.append(
            f"cosign {tool.get('version')} is below the minimum allowed for standardized bundle verification: "
            + ".".join(str(item) for item in minimum)
        )
    cosign_result: dict[str, Any] = {"status": "NOT_RUN"}
    if not failures and tool.get("status") == "PASS":
        command = [
            str(tool["path"]),
            "verify-blob-attestation",
            "--bundle", str(bundle_path),
            "--check-claims=true",
            "--type", SLSA_VERIFICATION_SUMMARY_V1,
        ]
        if mode == "public-key":
            key_path = signer.get("publicKeyPath")
            if not isinstance(key_path, str):
                failures.append("resolved trusted public key is unavailable")
            else:
                command.extend(["--key", key_path])
                if signer.get("requireTransparencyLog") is not True:
                    command.append("--insecure-ignore-tlog")
        elif mode == "keyless":
            command.extend([
                "--certificate-identity", str(signer.get("certificateIdentity")),
                "--certificate-oidc-issuer", str(signer.get("certificateOidcIssuer")),
            ])
            trusted_root = signer.get("trustedRootPath")
            if isinstance(trusted_root, str):
                command.extend(["--trusted-root", trusted_root])
        else:
            failures.append(f"unsupported signer mode: {mode}")
        if not failures:
            command.append(str(subject))
            proc = subprocess.run(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
            cosign_result = {
                "status": "PASS" if proc.returncode == 0 else "FAIL",
                "exitCode": proc.returncode,
                "stdout": proc.stdout.strip()[:4000],
                "stderr": proc.stderr.strip()[:4000],
                "commandPolicy": {
                    "checkClaims": True,
                    "predicateType": SLSA_VERIFICATION_SUMMARY_V1,
                    "transparencyLogRequired": signer.get("requireTransparencyLog") is True,
                },
            }
            if proc.returncode != 0:
                failures.append("cosign cryptographic attestation verification failed")
    return {
        "status": "PASS" if not failures else "FAIL",
        "authenticity": "VERIFIED" if not failures else "NOT_VERIFIED",
        "signerId": signer_id,
        "signerMode": mode,
        "verifierId": verifier_id,
        "trustPolicy": policy_result,
        "bundleShape": bundle_shape,
        "semantic": semantic,
        "cosign": cosign_result,
        "tool": tool,
        "failures": failures,
        "boundary": "PASS requires a standardized Sigstore v0.3 DSSE bundle, exact signed-statement equality, an authorized signer->verifier.id mapping, exact VSA subject/policy/resource bindings, a provenance-verified digest/version-pinned Cosign verifier, and successful cosign verification with --check-claims=true. Keyless verification additionally requires identity/issuer policy plus transparency-log evidence. Legacy bundles are rejected before cosign verification.",
    }


def aggregate_vsa_gates(
    profile_path: Path,
    subject: Path,
    gate_paths: dict[str, Path],
    allow_local_unsigned: bool = False,
    bundles: dict[str, Path] | None = None,
    trust_policy_path: Path | None = None,
    signer_ids: dict[str, str] | None = None,
    toolchain: TrustToolchainConfig | None = None,
) -> dict[str, Any]:
    profile_result = validate_profile(profile_path)
    profile = profile_result.get("profile", {})
    required_all = {name for name, flag in profile.get("gates", {}).items() if flag is True}
    required = required_all & VSA_GATE_NAMES
    assembly_required = required_all & ASSEMBLY_GATE_NAMES
    components: dict[str, Any] = {}
    failures: list[str] = []
    bundle_paths = bundles or {}
    selected_signers = signer_ids or {}
    for gate in sorted(set(bundle_paths) - set(gate_paths)):
        failures.append(f"Sigstore bundle supplied without a corresponding VSA gate: {gate}")
    for gate in sorted(set(selected_signers) - set(gate_paths)):
        failures.append(f"trusted signer supplied without a corresponding VSA gate: {gate}")
    for gate, path in sorted(gate_paths.items()):
        if gate not in profile.get("gates", {}):
            failures.append(f"VSA supplied for undeclared gate: {gate}")
            continue
        if gate not in VSA_GATE_NAMES:
            failures.append(f"gate is assembly/provenance policy and must not be represented as a VSA gate: {gate}")
            continue
        checked = verify_verification_summary(path, subject, profile_path)
        verification_result = checked.get("verificationResult")
        signature_result: dict[str, Any] | None = None
        if checked.get("status") != "PASS":
            failures.append(f"VSA binding/shape validation failed: {gate}")
        elif verification_result != "PASSED":
            failures.append(f"VSA verificationResult is not PASSED: {gate}")
        if not allow_local_unsigned:
            bundle_path = bundle_paths.get(gate)
            signer_id = selected_signers.get(gate)
            if trust_policy_path is None:
                failures.append(f"VSA authenticity trust policy missing for production gate: {gate}")
            elif bundle_path is None:
                failures.append(f"VSA authenticity Sigstore bundle missing for production gate: {gate}")
            elif not signer_id:
                failures.append(f"VSA authenticity trusted signer id missing for production gate: {gate}")
            else:
                signature_result = verify_signed_verification_summary(
                    path, bundle_path, subject, profile_path, trust_policy_path, signer_id, toolchain=toolchain
                )
                if signature_result.get("status") != "PASS":
                    failures.append(f"VSA authenticity verification failed: {gate}")
        component = dict(checked)
        component["signature"] = signature_result
        component["authenticity"] = (
            "LOCAL_UNSIGNED_DEVELOPMENT" if allow_local_unsigned
            else "VERIFIED" if signature_result and signature_result.get("status") == "PASS"
            else "NOT_VERIFIED"
        )
        components[gate] = component
    for gate in sorted(required):
        if gate not in components:
            failures.append(f"required gate VSA missing: {gate}")
    if profile_result.get("status") != "PASS":
        failures.append("profile schema did not PASS")
    return {
        "schemaVersion": 1,
        "kind": "artifact-delivery-vsa-gate-aggregation",
        "status": "PASS" if not failures else "FAIL",
        "profileId": profile.get("id"),
        "subject": file_fact(subject),
        "requiredGates": sorted(required),
        "assemblyGates": sorted(assembly_required),
        "components": components,
        "allowLocalUnsigned": allow_local_unsigned,
        "trustPolicy": file_fact(trust_policy_path) if trust_policy_path is not None and trust_policy_path.is_file() else None,
        "bundles": {gate: file_fact(path) for gate, path in sorted(bundle_paths.items()) if path.is_file()},
        "selectedSigners": dict(sorted(selected_signers.items())),
        "failures": failures,
        "boundary": "Production aggregation requires a standardized Sigstore bundle plus a policy-authorized signer for every required VSA gate. Local unsigned mode is only for same-workspace development evidence and must not be presented as external trust.",
    }
