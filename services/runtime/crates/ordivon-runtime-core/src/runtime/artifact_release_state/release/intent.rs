use super::super::super::{
    runtime_release_effect_id, runtime_release_request_identity_digest, validate_client_request_id,
    RuntimeError, RuntimeErrorCode, RuntimeReleaseContract, RuntimeReleaseEffectBinding,
    RuntimeReleaseRequest, RuntimeResult, RUNTIME_SCHEMA_VERSION,
};
use super::super::validation::{is_lower_hex, validate_sha256_lowercase};

impl super::ReleaseStateContract {
    pub(crate) fn validate_request(request: &RuntimeReleaseRequest) -> RuntimeResult<()> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported runtime schema version",
                "schemaVersion",
            ));
        }
        validate_client_request_id(&request.client_request_id, "clientRequestId")?;
        if request.expected_tool_count == 0 {
            return Err(RuntimeError::invalid(
                "Runtime Release expectedToolCount must be positive",
                "expectedToolCount",
            ));
        }
        if !is_lower_hex(&request.commit, 40) {
            return Err(RuntimeError::invalid(
                "Runtime Release commit must be exactly 40 lowercase hexadecimal characters",
                "commit",
            ));
        }
        validate_sha256_lowercase(
            &request.candidate_manifest_digest,
            "candidateManifestDigest",
            "candidate manifest digest must use sha256",
            "candidate manifest digest must contain 64 lowercase hexadecimal characters",
        )
    }

    pub(crate) fn validate_binding_matches_request(
        binding: &RuntimeReleaseEffectBinding,
        request: &RuntimeReleaseRequest,
    ) -> RuntimeResult<()> {
        let expected_request_digest = runtime_release_request_identity_digest(request)?;
        let expected_effect_id = runtime_release_effect_id(request);
        if binding.contract != RuntimeReleaseContract::RuntimeReleaseV1
            || binding.effect_id != expected_effect_id
            || binding.request_digest != expected_request_digest
            || binding.workspace_id != request.workspace_id
            || binding.commit != request.commit
            || binding.candidate_manifest_digest != request.candidate_manifest_digest
            || binding.expected_tool_count != request.expected_tool_count
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored Runtime Release side truth does not match the request identity",
                Some("runtimeReleaseEffect"),
                false,
            ));
        }
        Ok(())
    }
}
