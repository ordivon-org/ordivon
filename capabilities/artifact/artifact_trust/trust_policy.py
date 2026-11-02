"""VSA trust-policy parsing, schema checking and signer key binding.

This module owns the policy representation. Cryptographic validation and
Cosign execution remain in vsa; accepted policy never proves authenticity.
"""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path
from typing import Any

from artifact_core.contracts import file_fact
from artifact_core.json_validation import validate_json_document

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VSA_TRUST_POLICY_SCHEMA = ROOT / "artifact-delivery/vsa-trust-policy-v1.schema.json"
SIGSTORE_BUNDLE_V03 = "application/vnd.dev.sigstore.bundle.v0.3+json"


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
