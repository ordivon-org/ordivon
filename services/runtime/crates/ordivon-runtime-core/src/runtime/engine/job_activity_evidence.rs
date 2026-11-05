#[derive(Clone, Debug, Eq, PartialEq)]
struct JobActivitySignature {
    status: String,
    stdout_bytes: u64,
    stderr_bytes: u64,
    progress_revision: u64,
}

fn job_activity_signature(
    attempt: Option<&AttemptRecord>,
    projection: &super::JobProjection,
) -> RuntimeResult<JobActivitySignature> {
    let Some(attempt) = attempt else {
        return Ok(JobActivitySignature {
            status: projection.status.clone(),
            stdout_bytes: 0,
            stderr_bytes: 0,
            progress_revision: 0,
        });
    };
    let bundle = Path::new(&attempt.bundle_path);
    let stdout_bytes = file_length_if_present(&bundle.join(STDOUT_FILE))?;
    let stderr_bytes = file_length_if_present(&bundle.join(STDERR_FILE))?;
    let progress_revision = load_runner_progress_if_present(attempt)?
        .map(|progress| progress.revision)
        .unwrap_or(0);
    Ok(JobActivitySignature {
        status: projection.status.clone(),
        stdout_bytes,
        stderr_bytes,
        progress_revision,
    })
}

fn file_length_if_present(path: &Path) -> RuntimeResult<u64> {
    match fs::metadata(path) {
        Ok(metadata) => Ok(metadata.len()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(0),
        Err(error) => Err(io_error(&format!("inspect {}", path.display()), error)),
    }
}

pub(crate) fn load_runner_progress_if_present(
    attempt: &AttemptRecord,
) -> RuntimeResult<Option<RunnerProgress>> {
    let path = Path::new(&attempt.bundle_path).join(PROGRESS_FILE);
    if !path.exists() {
        return Ok(None);
    }
    let bytes = fs::read(&path).map_err(|error| io_error("read Runner progress", error))?;
    serde_json::from_slice(&bytes).map(Some).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid Runner progress: {error}"),
            Some("progress"),
            false,
        )
    })
}

pub(crate) fn latest_output_modified_ms(attempt: &AttemptRecord) -> RuntimeResult<Option<u64>> {
    let bundle = Path::new(&attempt.bundle_path);
    let mut latest = None;
    for path in [bundle.join(STDOUT_FILE), bundle.join(STDERR_FILE)] {
        let metadata = match fs::metadata(&path) {
            Ok(metadata) => metadata,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => continue,
            Err(error) => return Err(io_error(&format!("inspect {}", path.display()), error)),
        };
        if metadata.len() == 0 {
            continue;
        }
        let modified = metadata
            .modified()
            .map_err(|error| io_error(&format!("read {} mtime", path.display()), error))?;
        let millis = modified
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_millis();
        let millis = u64::try_from(millis).unwrap_or(u64::MAX);
        latest = Some(latest.map_or(millis, |value: u64| value.max(millis)));
    }
    Ok(latest)
}

fn load_control_error_summary_if_present(attempt: &AttemptRecord) -> RuntimeResult<Option<String>> {
    let path = Path::new(&attempt.bundle_path).join(CONTROL_RESULT_FILE);
    if !path.exists() {
        return Ok(None);
    }
    let bytes = fs::read(&path).map_err(|error| io_error("read control result", error))?;
    let evidence: ControlTerminalEvidence = serde_json::from_slice(&bytes).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid control result: {error}"),
            Some("controlResult"),
            false,
        )
    })?;
    if evidence.job_id != attempt.job_id || evidence.attempt_id != attempt.attempt_id {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "control result identity does not match Attempt",
            Some("controlResult"),
            false,
        ));
    }
    Ok(evidence.detail)
}

fn load_runner_result_if_present(
    attempt: &AttemptRecord,
) -> RuntimeResult<Option<RunnerResult>> {
    let path = Path::new(&attempt.bundle_path).join(RESULT_FILE);
    if !path.exists() {
        return Ok(None);
    }
    let bytes = fs::read(&path).map_err(|error| io_error("read Runner result", error))?;
    serde_json::from_slice(&bytes).map(Some).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid Runner result: {error}"),
            Some("result"),
            false,
        )
    })
}
