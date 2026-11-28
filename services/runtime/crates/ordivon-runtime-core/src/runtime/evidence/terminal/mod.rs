mod identity;
mod status;
#[cfg(test)]
mod tests;

use self::identity::read_and_validate_runner_result;
use self::status::terminal_state;
use super::super::{ArtifactRegistration, AttemptRecord, RuntimeResult, TerminalCommit};
use super::captured_output::validate_captured_output;
use super::resource_receipt::validate_resource_receipt;
use super::RESULT_FILE;
use crate::universal::sha256_bytes;

pub(crate) fn prepare_runner_terminal_from_bundle(
    current: &AttemptRecord,
) -> RuntimeResult<TerminalCommit> {
    let (result, result_digest, result_bytes_len) = read_and_validate_runner_result(current)?;
    let stdout = validate_captured_output(current, &result.stdout, true)?;
    let stderr = validate_captured_output(current, &result.stderr, false)?;
    let (state, reason_code) = terminal_state(current, &result);
    let infrastructure_error_digest = result
        .infrastructure_error
        .as_deref()
        .map(|message| sha256_bytes(message.as_bytes()));
    let mut artifacts = vec![stdout, stderr];
    artifacts.push(ArtifactRegistration {
        artifact_id: format!("{}.result", current.attempt_id),
        kind: "execution_result".to_string(),
        relative_path: RESULT_FILE.to_string(),
        digest: result_digest.clone(),
        media_type: "application/json".to_string(),
        byte_length: u64::try_from(result_bytes_len).unwrap_or(u64::MAX),
        truncated: false,
    });
    if let Some(receipt) = validate_resource_receipt(current)? {
        artifacts.push(receipt);
    }
    Ok(TerminalCommit {
        attempt_id: current.attempt_id.clone(),
        expected_row_version: current.row_version,
        state,
        result_digest,
        exit_code: result.exit_code,
        infrastructure_error_digest,
        finished_at_ms: u64::try_from(result.finished_unix_ms).unwrap_or(u64::MAX),
        artifacts,
        reason_code: reason_code.to_string(),
    })
}
