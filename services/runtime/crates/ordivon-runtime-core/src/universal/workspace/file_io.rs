fn open_workspace_regular_file(
    record: &WorkspaceRecord,
    relative: &str,
) -> Result<(File, PathBuf), UniversalExecError> {
    let relative_path = validate_relative_path(relative, "relativePath")?;
    let workspace_root = Path::new(&record.workspace_path);
    let logical_path = workspace_root.join(&relative_path);
    let root = open_directory_nofollow(workspace_root).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::WorkspacePathDenied,
            format!("cannot open Workspace root without following symlinks: {error}"),
            Some("workspaceId"),
            false,
        )
    })?;
    let file = open_regular_file_beneath(&root, &relative_path, false).map_err(|error| {
        let code = match error.raw_os_error() {
            Some(libc::ENOENT) => UniversalExecErrorCode::WorkspacePathNotFound,
            Some(libc::ELOOP) | Some(libc::EXDEV) | Some(libc::ENOTDIR) => {
                UniversalExecErrorCode::WorkspacePathDenied
            }
            Some(libc::ENOSYS) => UniversalExecErrorCode::ToolUnavailable,
            _ if error.kind() == std::io::ErrorKind::InvalidInput => {
                UniversalExecErrorCode::WorkspacePathDenied
            }
            _ => UniversalExecErrorCode::IoError,
        };
        UniversalExecError::new(
            code,
            format!("cannot open Workspace file beneath its root: {error}"),
            Some("relativePath"),
            false,
        )
    })?;
    Ok((file, logical_path))
}

fn read_workspace_file_bounded(
    mut file: File,
    logical_path: &Path,
    max_bytes: u64,
) -> Result<Vec<u8>, UniversalExecError> {
    let metadata = file
        .metadata()
        .map_err(|error| io_error(logical_path, "inspect opened file", error))?;
    if metadata.len() > max_bytes {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::OutputLimitExceeded,
            format!("file exceeds maxBytes {max_bytes}"),
            Some("maxBytes"),
            false,
        ));
    }
    let mut bytes = Vec::with_capacity((metadata.len().min(max_bytes) + 1) as usize);
    file.by_ref()
        .take(max_bytes.saturating_add(1))
        .read_to_end(&mut bytes)
        .map_err(|error| io_error(logical_path, "read opened file", error))?;
    if bytes.len() as u64 > max_bytes {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::OutputLimitExceeded,
            format!("file exceeds maxBytes {max_bytes}"),
            Some("maxBytes"),
            false,
        ));
    }
    Ok(bytes)
}

pub fn read_workspace_text(
    config: &UniversalExecutorConfig,
    request: &WorkspaceReadRequest,
) -> Result<WorkspaceReadResult, UniversalExecError> {
    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let (file, logical_path) = open_workspace_regular_file(&record, &request.relative_path)?;
    let bytes = read_workspace_file_bounded(file, &logical_path, request.max_bytes)?;
    let digest = sha256_bytes(&bytes);
    let byte_length = bytes.len() as u64;
    let content = String::from_utf8(bytes).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ArtifactNotUtf8,
            format!("workspace file is not UTF-8: {error}"),
            Some("relativePath"),
            false,
        )
    })?;
    Ok(WorkspaceReadResult {
        workspace_id: request.workspace_id.clone(),
        relative_path: request.relative_path.clone(),
        content,
        digest,
        byte_length,
    })
}

fn verified_workspace_image_media_type(
    relative_path: &str,
    bytes: &[u8],
) -> Result<&'static str, UniversalExecError> {
    let extension = Path::new(relative_path)
        .extension()
        .and_then(|value| value.to_str())
        .map(str::to_ascii_lowercase);
    match extension.as_deref() {
        Some("png") if bytes.starts_with(b"\x89PNG\r\n\x1a\n") => Ok("image/png"),
        Some("jpg" | "jpeg") if bytes.starts_with(&[0xff, 0xd8, 0xff]) => Ok("image/jpeg"),
        Some("png" | "jpg" | "jpeg") => Err(UniversalExecError::new(
            UniversalExecErrorCode::InvalidRequest,
            "workspace image bytes do not match the file extension",
            Some("relativePath"),
            false,
        )),
        _ => Err(UniversalExecError::new(
            UniversalExecErrorCode::InvalidRequest,
            "workspace.content currently supports only verified .png, .jpg, and .jpeg images",
            Some("relativePath"),
            false,
        )),
    }
}

pub fn read_workspace_content(
    config: &UniversalExecutorConfig,
    request: &WorkspaceContentRequest,
) -> Result<WorkspaceContentReadResult, UniversalExecError> {
    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let (file, logical_path) = open_workspace_regular_file(&record, &request.relative_path)?;
    let bytes = read_workspace_file_bounded(file, &logical_path, request.max_bytes)?;
    let digest = sha256_bytes(&bytes);
    if digest != request.expected_digest {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionMismatch,
            format!(
                "workspace content digest changed: expected {}, observed {digest}",
                request.expected_digest
            ),
            Some("expectedDigest"),
            false,
        ));
    }
    let media_type = verified_workspace_image_media_type(&request.relative_path, &bytes)?;
    Ok(WorkspaceContentReadResult {
        metadata: WorkspaceContentMetadata {
            workspace_id: request.workspace_id.clone(),
            relative_path: request.relative_path.clone(),
            digest,
            media_type: media_type.to_string(),
            byte_length: bytes.len() as u64,
        },
        bytes,
    })
}

pub fn write_workspace_text(
    config: &UniversalExecutorConfig,
    request: &WorkspaceWriteRequest,
) -> Result<WorkspaceWriteResult, UniversalExecError> {
    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let path = resolve_workspace_write_path(&record, &request.relative_path)?;
    let before_digest = if path.exists() {
        let metadata =
            fs::symlink_metadata(&path).map_err(|error| io_error(&path, "inspect", error))?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspacePathDenied,
                "write target must be a non-symlink regular file",
                Some("relativePath"),
                false,
            ));
        }
        Some(sha256_file(&path)?)
    } else {
        None
    };
    if request.expected_digest != before_digest
        && (request.expected_digest.is_some() || before_digest.is_some())
    {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionMismatch,
            "workspace file digest does not match expectedDigest",
            Some("expectedDigest"),
            false,
        ));
    }
    let existing_permissions = fs::metadata(&path)
        .ok()
        .map(|metadata| metadata.permissions());
    write_bytes_atomic(&path, request.content.as_bytes())?;
    if let Some(permissions) = existing_permissions {
        fs::set_permissions(&path, permissions)
            .map_err(|error| io_error(&path, "set permissions", error))?;
    } else {
        let permissions = fs::metadata(&path)
            .map_err(|error| io_error(&path, "inspect", error))?
            .permissions();
        #[cfg(unix)]
        {
            let mut permissions = permissions;
            permissions.set_mode(0o644);
            fs::set_permissions(&path, permissions)
                .map_err(|error| io_error(&path, "set permissions", error))?;
        }
        #[cfg(not(unix))]
        {
            let _ = permissions;
        }
    }
    Ok(WorkspaceWriteResult {
        workspace_id: request.workspace_id.clone(),
        relative_path: request.relative_path.clone(),
        before_digest,
        after_digest: sha256_file(&path)?,
        byte_length: request.content.len() as u64,
    })
}

const MAX_GIT_DIAGNOSTIC_BYTES: usize = 64 * 1024;

fn drain_reader_bounded<R>(mut reader: R) -> JoinHandle<Vec<u8>>
where
    R: Read + Send + 'static,
{
    thread::spawn(move || {
        let mut retained = Vec::with_capacity(MAX_GIT_DIAGNOSTIC_BYTES);
        let mut buffer = [0_u8; 8 * 1024];
        loop {
            let read = match reader.read(&mut buffer) {
                Ok(0) | Err(_) => break,
                Ok(read) => read,
            };
            let remaining = MAX_GIT_DIAGNOSTIC_BYTES.saturating_sub(retained.len());
            retained.extend_from_slice(&buffer[..read.min(remaining)]);
        }
        retained
    })
}

fn finish_stream_child(
    mut child: Child,
    stderr: JoinHandle<Vec<u8>>,
    context: &str,
    intentionally_stopped: bool,
) -> Result<(), UniversalExecError> {
    if intentionally_stopped {
        let _ = child.kill();
    }
    let status = child.wait().map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::IoError,
            format!("wait for {context}: {error}"),
            None,
            true,
        )
    })?;
    let stderr = stderr.join().unwrap_or_default();
    if !intentionally_stopped && !status.success() {
        return Err(tool_failed(context, &stderr));
    }
    Ok(())
}

fn bounded_command_stdout(
    command: &mut Command,
    max_bytes: u64,
    allowed_exit_codes: &[i32],
    context: &str,
) -> Result<(Vec<u8>, bool), UniversalExecError> {
    command.stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = command
        .spawn()
        .map_err(|error| tool_unavailable(context, error))?;
    let stdout = child.stdout.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            format!("{context} stdout pipe is unavailable"),
            None,
            false,
        )
    })?;
    let stderr = child.stderr.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            format!("{context} stderr pipe is unavailable"),
            None,
            false,
        )
    })?;
    let stderr = drain_reader_bounded(stderr);
    let mut bytes = Vec::with_capacity(
        usize::try_from(
            max_bytes
                .min(super::MAX_WORKSPACE_IO_BYTES)
                .saturating_add(1),
        )
        .unwrap_or(0),
    );
    let read_result = stdout
        .take(max_bytes.saturating_add(1))
        .read_to_end(&mut bytes);
    if let Err(error) = read_result {
        let _ = child.kill();
        let _ = child.wait();
        let _ = stderr.join();
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::IoError,
            format!("read {context} output: {error}"),
            None,
            true,
        ));
    }
    let truncated = bytes.len() as u64 > max_bytes;
    if truncated {
        let _ = child.kill();
    }
    let status = child.wait().map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::IoError,
            format!("wait for {context}: {error}"),
            None,
            true,
        )
    })?;
    let stderr = stderr.join().unwrap_or_default();
    if !truncated {
        let code = status.code().unwrap_or(-1);
        if !allowed_exit_codes.contains(&code) {
            return Err(tool_failed(context, &stderr));
        }
    }
    bytes.truncate(usize::try_from(max_bytes).unwrap_or(usize::MAX));
    Ok((bytes, truncated))
}

fn bounded_utf8(
    mut bytes: Vec<u8>,
    truncated: bool,
    context: &str,
) -> Result<(String, Vec<u8>), UniversalExecError> {
    if let Err(error) = std::str::from_utf8(&bytes) {
        if truncated && error.error_len().is_none() {
            bytes.truncate(error.valid_up_to());
        } else {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::ArtifactNotUtf8,
                format!("{context} is not UTF-8: {error}"),
                None,
                false,
            ));
        }
    }
    let text = String::from_utf8(bytes.clone()).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ArtifactNotUtf8,
            format!("{context} is not UTF-8: {error}"),
            None,
            false,
        )
    })?;
    Ok((text, bytes))
}
