from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact
from artifact_core.json_validation import validate_json_document as validate_json_document
from artifact_core.profile_v1 import validate_profile_v1 as validate_profile
from artifact_trust.cosign_toolchain import (
    _COSIGN_PROVENANCE_CACHE as _COSIGN_PROVENANCE_CACHE,
)
from artifact_trust.cosign_toolchain import (
    COSIGN_ARCH_PACKAGE as COSIGN_ARCH_PACKAGE,
)
from artifact_trust.cosign_toolchain import (
    COSIGN_ARCH_PACKAGE_SIGNATURE as COSIGN_ARCH_PACKAGE_SIGNATURE,
)
from artifact_trust.cosign_toolchain import (
    COSIGN_LOCK_PATH as COSIGN_LOCK_PATH,
)
from artifact_trust.cosign_toolchain import (
    COSIGN_SELECTED_BINARY as COSIGN_SELECTED_BINARY,
)
from artifact_trust.cosign_toolchain import (
    COSIGN_STANDARD_BUNDLE_MIN_VERSION as COSIGN_STANDARD_BUNDLE_MIN_VERSION,
)
from artifact_trust.cosign_toolchain import (
    GLOBAL_ARTIFACT_TOOLCHAIN_ROOT as GLOBAL_ARTIFACT_TOOLCHAIN_ROOT,
)
from artifact_trust.cosign_toolchain import (
    GLOBAL_COSIGN as GLOBAL_COSIGN,
)
from artifact_trust.cosign_toolchain import (
    GLOBAL_COSIGN_ARCH_PACKAGE as GLOBAL_COSIGN_ARCH_PACKAGE,
)
from artifact_trust.cosign_toolchain import (
    GLOBAL_COSIGN_ARCH_PACKAGE_SIGNATURE as GLOBAL_COSIGN_ARCH_PACKAGE_SIGNATURE,
)
from artifact_trust.cosign_toolchain import (
    TrustToolchainConfig as TrustToolchainConfig,
)
from artifact_trust.cosign_toolchain import (
    _cosign_executable as _cosign_executable,
)
from artifact_trust.cosign_toolchain import (
    _cosign_selection_provenance as _cosign_selection_provenance,
)
from artifact_trust.cosign_toolchain import (
    _selected_external_file as _selected_external_file,
)
from artifact_trust.cosign_toolchain import (
    _version_at_least as _version_at_least,
)
from artifact_trust.cosign_toolchain import (
    cosign_tool_fact as cosign_tool_fact,
)
from artifact_trust.cosign_toolchain import (
    default_trust_toolchain_config as default_trust_toolchain_config,
)
from artifact_trust.provenance import IN_TOTO_STATEMENT_V1 as IN_TOTO_STATEMENT_V1
from artifact_trust.sigstore_bundle import (
    INTOTO_DSSE_PAYLOAD_TYPE as INTOTO_DSSE_PAYLOAD_TYPE,
)
from artifact_trust.sigstore_bundle import (
    verify_sigstore_vsa_bundle_shape as verify_sigstore_vsa_bundle_shape,
)
from artifact_trust.trust_policy import (
    DEFAULT_VSA_TRUST_POLICY_SCHEMA as DEFAULT_VSA_TRUST_POLICY_SCHEMA,
)
from artifact_trust.trust_policy import (
    SIGSTORE_BUNDLE_V03 as SIGSTORE_BUNDLE_V03,
)
from artifact_trust.trust_policy import (
    _minimal_vsa_trust_policy_checks as _minimal_vsa_trust_policy_checks,
)
from artifact_trust.trust_policy import (
    _resolve_policy_path as _resolve_policy_path,
)
from artifact_trust.trust_policy import (
    validate_vsa_trust_policy as validate_vsa_trust_policy,
)
from artifact_trust.verification_summary import (
    SLSA_VERIFICATION_SUMMARY_V1 as SLSA_VERIFICATION_SUMMARY_V1,
)
from artifact_trust.verification_summary import (
    SLSA_VERSION as SLSA_VERSION,
)
from artifact_trust.verification_summary import (
    ni_sha256_uri as ni_sha256_uri,
)
from artifact_trust.verification_summary import (
    verification_summary_statement as verification_summary_statement,
)
from artifact_trust.verification_summary import (
    verify_verification_summary as verify_verification_summary,
)

LOCAL_VSA_VERIFIER_ID = "https://ordivon.local/verifiers/artifact-delivery-v1"
VSA_GATE_NAMES = frozenset({
    "profileSchema", "structural", "dependency", "semantic", "visual",
    "target", "accessibility", "conformance", "deliveryReadback",
})
ASSEMBLY_GATE_NAMES = frozenset({"companionPdf", "releaseProvenance"})



























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
