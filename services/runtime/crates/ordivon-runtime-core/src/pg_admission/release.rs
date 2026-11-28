//! Runtime release-effect qualification; no process launch or release policy.
use super::admission::PgReleaseInsert;
use super::*;

impl PgAdmissionStore {
    /// Internal PG-only release admission. No MCP caller can invoke this until
    /// an independently qualified operator installation/reconciliation contract
    /// exists. No filesystem or systemd effects occur in this transaction.
    pub fn admit_release_effect(
        &mut self,
        input: &PgAdmissionInput,
        request: &crate::runtime::RuntimeReleaseRequest,
        receipt_path: &std::path::Path,
    ) -> Result<PgAdmissionOutcome, PgAdmissionError> {
        use crate::runtime::{
            runtime_release_effect_id, runtime_release_request_identity_digest,
            ReleaseStateContract, RuntimeReleaseContract, RuntimeReleaseEffectBinding,
        };
        ReleaseStateContract::validate_request(request)
            .map_err(|_| PgAdmissionError::InvalidInput)?;
        let expected_tool_count = i32::try_from(request.expected_tool_count)
            .map_err(|_| PgAdmissionError::InvalidInput)?;
        if !receipt_path.is_absolute()
            || receipt_path
                .components()
                .any(|part| matches!(part, std::path::Component::ParentDir))
            || request.principal != input.principal
            || request.client_request_id != input.client_request_id
            || request.workspace_id != input.workspace_id
            || runtime_release_request_identity_digest(request)
                .map_err(|_| PgAdmissionError::InvalidInput)?
                != input.request_digest
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let binding = RuntimeReleaseEffectBinding {
            contract: RuntimeReleaseContract::RuntimeReleaseV1,
            effect_id: runtime_release_effect_id(request),
            request_digest: input.request_digest.clone(),
            workspace_id: request.workspace_id.clone(),
            commit: request.commit.clone(),
            candidate_manifest_digest: request.candidate_manifest_digest.clone(),
            expected_tool_count: request.expected_tool_count,
            receipt_path: receipt_path.to_string_lossy().into_owned(),
        };
        let json = serde_json::to_string(&binding).map_err(|_| PgAdmissionError::InvalidInput)?;
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(json.as_bytes())));
        let snapshot: serde_json::Value = serde_json::from_str(&input.workspace_snapshot_json)
            .map_err(|_| PgAdmissionError::InvalidInput)?;
        if snapshot
            .get("runtimeReleaseEffectDigest")
            .and_then(serde_json::Value::as_str)
            != Some(digest.as_str())
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let columns = PgReleaseInsert {
            effect_id: binding.effect_id.clone(),
            request_digest: binding.request_digest.clone(),
            workspace_id: binding.workspace_id.clone(),
            commit: binding.commit.clone(),
            candidate_manifest_digest: binding.candidate_manifest_digest.clone(),
            expected_tool_count,
            receipt_path: binding.receipt_path.clone(),
        };
        self.admit_inner(input, Some((&columns, &digest)), None, None)
    }
}
