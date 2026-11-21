use super::super::super::{
    AttemptState, JobResolution, RuntimeReleaseDisposition, RuntimeReleaseEffectBinding,
    RuntimeResult,
};
use super::identity::release_effect_json_matches;
use super::projection::ReleaseReceiptProjection;
use super::read::release_receipt_json;
use std::fs;
use std::path::Path;

pub(crate) fn inspect_receipt(
    binding: &RuntimeReleaseEffectBinding,
    job_resolution: Option<JobResolution>,
    attempt_state: Option<AttemptState>,
) -> RuntimeResult<ReleaseReceiptProjection> {
    let receipt = Path::new(&binding.receipt_path);
    let directory = match fs::symlink_metadata(receipt) {
        Ok(metadata) => Some(metadata),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => None,
        Err(_) => {
            return Ok(ReleaseReceiptProjection::reconciliation(
                "RELEASE_RECEIPT_DIRECTORY_UNAVAILABLE",
            ));
        }
    };
    let Some(directory) = directory else {
        return if job_resolution.is_none() {
            Ok(ReleaseReceiptProjection::unresolved(attempt_state))
        } else {
            Ok(ReleaseReceiptProjection::reconciliation(
                "RELEASE_RECEIPT_MISSING_AFTER_JOB_TERMINAL",
            ))
        };
    };
    if directory.file_type().is_symlink() || !directory.is_dir() {
        return Ok(ReleaseReceiptProjection::reconciliation(
            "RELEASE_RECEIPT_DIRECTORY_UNSAFE",
        ));
    }

    let effect_request = match release_receipt_json(&receipt.join("effect-request.json")) {
        Ok(Some((value, _))) => value,
        Ok(None) if job_resolution.is_none() => {
            return Ok(ReleaseReceiptProjection::unresolved(attempt_state));
        }
        Ok(None) => {
            return Ok(ReleaseReceiptProjection::reconciliation(
                "RELEASE_EFFECT_REQUEST_MISSING_AFTER_JOB_TERMINAL",
            ));
        }
        Err(issue) => return Ok(ReleaseReceiptProjection::reconciliation(&issue)),
    };
    if !release_effect_json_matches(&effect_request, binding) {
        return Ok(ReleaseReceiptProjection::reconciliation(
            "RELEASE_EFFECT_REQUEST_MISMATCH",
        ));
    }

    let result = match release_receipt_json(&receipt.join("result.json")) {
        Ok(Some(value)) => value,
        Ok(None) if job_resolution.is_none() => {
            return Ok(ReleaseReceiptProjection::unresolved(attempt_state));
        }
        Ok(None) => {
            return Ok(ReleaseReceiptProjection::reconciliation(
                "RELEASE_RESULT_MISSING_AFTER_JOB_TERMINAL",
            ));
        }
        Err(issue) => return Ok(ReleaseReceiptProjection::reconciliation(&issue)),
    };
    let (result, result_digest) = result;
    if result.get("commit").and_then(|value| value.as_str()) != Some(binding.commit.as_str())
        || !result
            .get("releaseEffect")
            .is_some_and(|value| release_effect_json_matches(value, binding))
    {
        return Ok(ReleaseReceiptProjection::reconciliation(
            "RELEASE_RESULT_MISMATCH",
        ));
    }

    let rollback = match release_receipt_json(&receipt.join("rollback-result.json")) {
        Ok(Some((value, _))) => value
            .get("status")
            .and_then(|status| status.as_str())
            .map(str::to_string),
        Ok(None) => None,
        Err(issue) => return Ok(ReleaseReceiptProjection::reconciliation(&issue)),
    };
    if rollback.as_deref() == Some("restored_previous") {
        return Ok(ReleaseReceiptProjection {
            disposition: RuntimeReleaseDisposition::RolledBack,
            terminal: true,
            available: true,
            digest: Some(result_digest),
            deployed_tool_count: result
                .pointer("/probe/toolCount")
                .and_then(|value| value.as_u64())
                .and_then(|value| u32::try_from(value).ok()),
            tool_catalog_digest: result
                .pointer("/probe/toolCatalogDigest")
                .and_then(|value| value.as_str())
                .map(str::to_string),
            rollback_status: rollback,
            issue: None,
        });
    }

    let status = result.get("status").and_then(|value| value.as_str());
    let deployed_tool_count = result
        .pointer("/probe/toolCount")
        .and_then(|value| value.as_u64())
        .and_then(|value| u32::try_from(value).ok());
    let tool_catalog_digest = result
        .pointer("/probe/toolCatalogDigest")
        .and_then(|value| value.as_str())
        .map(str::to_string);
    if status == Some("deployed") && deployed_tool_count != Some(binding.expected_tool_count) {
        return Ok(ReleaseReceiptProjection::reconciliation(
            "RELEASE_RESULT_TOOL_COUNT_MISMATCH",
        ));
    }
    let (disposition, terminal, issue) = match status {
        Some("deployed") => (RuntimeReleaseDisposition::Deployed, true, None),
        Some("not_committed") => (RuntimeReleaseDisposition::NotCommitted, true, None),
        Some("rolled_back") => (RuntimeReleaseDisposition::RolledBack, true, None),
        Some("rollback_failed") => (
            RuntimeReleaseDisposition::ReconciliationRequired,
            false,
            Some("RELEASE_ROLLBACK_FAILED".to_string()),
        ),
        Some("reconciliation_required") => (
            RuntimeReleaseDisposition::ReconciliationRequired,
            false,
            Some(
                result
                    .get("reconciliationIssue")
                    .and_then(|value| value.as_str())
                    .unwrap_or("RELEASE_RECONCILIATION_REQUIRED")
                    .to_string(),
            ),
        ),
        Some("recovery_failed") => (
            RuntimeReleaseDisposition::ReconciliationRequired,
            false,
            Some("RELEASE_RECOVERY_FAILED".to_string()),
        ),
        _ => (
            RuntimeReleaseDisposition::ReconciliationRequired,
            false,
            Some("RELEASE_RESULT_STATUS_UNKNOWN".to_string()),
        ),
    };
    Ok(ReleaseReceiptProjection {
        disposition,
        terminal,
        available: true,
        digest: Some(result_digest),
        deployed_tool_count,
        tool_catalog_digest,
        rollback_status: rollback,
        issue,
    })
}
