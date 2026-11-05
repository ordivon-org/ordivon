// Execution-bound input and credential normalization, materialization and snapshot verification.
// Keep source/digest authority at Runtime admission; no new state ownership.
fn canonical_input_binding_requests(
    inputs: &[InputBindingRequest],
) -> RuntimeResult<Vec<InputBindingRequest>> {
    if inputs.is_empty() {
        return Err(RuntimeError::invalid(
            "at least one immutable input is required",
            "inputs",
        ));
    }
    let mut canonical = Vec::with_capacity(inputs.len());
    let mut presentation_paths = BTreeSet::<PathBuf>::new();
    for (index, input) in inputs.iter().enumerate() {
        validate_input_authority_name(&input.authority, &format!("inputs[{index}].authority"))?;
        let object = validate_normal_relative_path(
            &input.relative_object,
            &format!("inputs[{index}].relativeObject"),
        )?;
        let presentation = validate_normal_relative_path(
            &input.presentation_relative_path,
            &format!("inputs[{index}].presentationRelativePath"),
        )?;
        validate_sha256_digest(
            &input.expected_digest,
            &format!("inputs[{index}].expectedDigest"),
        )?;
        for existing in &presentation_paths {
            if presentation == *existing
                || presentation.starts_with(existing)
                || existing.starts_with(&presentation)
            {
                return Err(RuntimeError::invalid(
                    "input presentation paths must not overlap as file/ancestor paths",
                    &format!("inputs[{index}].presentationRelativePath"),
                ));
            }
        }
        presentation_paths.insert(presentation.clone());
        canonical.push(InputBindingRequest {
            authority: input.authority.clone(),
            relative_object: object.to_string_lossy().into_owned(),
            expected_digest: input.expected_digest.to_ascii_lowercase(),
            presentation_relative_path: presentation.to_string_lossy().into_owned(),
        });
    }
    canonical.sort_by(|left, right| {
        (
            &left.presentation_relative_path,
            &left.authority,
            &left.relative_object,
            &left.expected_digest,
        )
            .cmp(&(
                &right.presentation_relative_path,
                &right.authority,
                &right.relative_object,
                &right.expected_digest,
            ))
    });
    Ok(canonical)
}

pub(super) fn canonical_credential_binding_requests(
    credentials: &[CredentialBindingRequest],
) -> RuntimeResult<Vec<CredentialBindingRequest>> {
    if credentials.is_empty() {
        return Err(RuntimeError::invalid(
            "at least one credential is required",
            "credentials",
        ));
    }
    let mut canonical = Vec::with_capacity(credentials.len());
    let mut names = BTreeSet::new();
    for (index, credential) in credentials.iter().enumerate() {
        validate_input_authority_name(
            &credential.authority,
            &format!("credentials[{index}].authority"),
        )?;
        validate_credential_name(
            &credential.credential,
            &format!("credentials[{index}].credential"),
        )?;
        if !names.insert(credential.credential.clone()) {
            return Err(RuntimeError::invalid(
                "credential names must be unique within one execution",
                &format!("credentials[{index}].credential"),
            ));
        }
        canonical.push(credential.clone());
    }
    canonical.sort_by(|left, right| {
        (&left.authority, &left.credential)
            .cmp(&(&right.authority, &right.credential))
    });
    Ok(canonical)
}

fn validate_credential_name(value: &str, field: &str) -> RuntimeResult<()> {
    if value.is_empty()
        || value.len() > 128
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
        || matches!(value, "." | "..")
    {
        return Err(RuntimeError::invalid(
            "credential name must use 1-128 ASCII alphanumeric/._- characters and must not be . or ..",
            field,
        ));
    }
    Ok(())
}

fn validate_input_authority_name(value: &str, field: &str) -> RuntimeResult<()> {
    if value.is_empty()
        || value.len() > 128
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
    {
        return Err(RuntimeError::invalid(
            "input authority name must use 1-128 ASCII alphanumeric/._- characters",
            field,
        ));
    }
    Ok(())
}

fn validate_normal_relative_path(value: &str, field: &str) -> RuntimeResult<PathBuf> {
    let path = Path::new(value);
    if value.is_empty() || value.as_bytes().contains(&0) || path.is_absolute() {
        return Err(RuntimeError::invalid(
            "path must be non-empty, relative, and NUL-free",
            field,
        ));
    }
    let mut normalized = PathBuf::new();
    for component in path.components() {
        match component {
            std::path::Component::Normal(value) => normalized.push(value),
            _ => {
                return Err(RuntimeError::invalid(
                    "path must contain only normal relative components",
                    field,
                ));
            }
        }
    }
    if normalized.as_os_str().is_empty() {
        return Err(RuntimeError::invalid("path must not be empty", field));
    }
    Ok(normalized)
}

fn validate_sha256_digest(value: &str, field: &str) -> RuntimeResult<()> {
    let Some(hex) = value.strip_prefix("sha256:") else {
        return Err(RuntimeError::invalid("digest must use sha256:<hex>", field));
    };
    if hex.len() != 64 || !hex.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(RuntimeError::invalid(
            "digest must be 32-byte SHA-256 hex",
            field,
        ));
    }
    Ok(())
}

fn open_authority_file(root_file: &File, relative: &str, index: usize) -> RuntimeResult<File> {
    let relative_path =
        validate_normal_relative_path(relative, &format!("inputs[{index}].relativeObject"))?;
    open_regular_file_beneath(root_file, &relative_path, true).map_err(|error| {
        RuntimeError::invalid(
            format!("cannot resolve input object inside authority: {error}"),
            &format!("inputs[{index}].relativeObject"),
        )
    })
}


fn open_credential_file(root_file: &File, name: &str, index: usize) -> RuntimeResult<File> {
    validate_credential_name(name, &format!("credentials[{index}].credential"))?;
    open_regular_file_beneath(root_file, Path::new(name), true).map_err(|_| {
        RuntimeError::invalid(
            "credential is unavailable from the selected authority",
            &format!("credentials[{index}].credential"),
        )
    })
}

fn copy_input_and_digest(mut source: File, target: &Path) -> RuntimeResult<String> {
    let mut output_options = OpenOptions::new();
    output_options.write(true).create_new(true);
    configure_private_create(&mut output_options, 0o600);
    let mut output = output_options
        .open(target)
        .map_err(|error| io_error("create materialized input", error))?;
    std::io::copy(&mut source, &mut output)
        .map_err(|error| io_error("copy input object", error))?;
    output
        .sync_all()
        .map_err(|error| io_error("sync materialized input", error))?;
    sha256_file(target).map_err(map_universal_error)
}

fn collect_materialized_files(
    root: &Path,
    current: &Path,
    files: &mut BTreeSet<PathBuf>,
) -> RuntimeResult<()> {
    for entry in
        fs::read_dir(current).map_err(|error| io_error("scan materialized input set", error))?
    {
        let entry = entry.map_err(|error| io_error("read materialized input entry", error))?;
        let path = entry.path();
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| io_error("inspect materialized input entry", error))?;
        if metadata.file_type().is_symlink() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "materialized input set contains a symlink",
                Some("effectiveInputs"),
                false,
            ));
        }
        if metadata.is_dir() {
            collect_materialized_files(root, &path, files)?;
        } else if metadata.is_file() {
            let relative = path.strip_prefix(root).map_err(|_| {
                RuntimeError::new(
                    RuntimeErrorCode::WorkspaceStateMismatch,
                    "materialized input escaped its set root",
                    Some("effectiveInputs"),
                    false,
                )
            })?;
            files.insert(relative.to_path_buf());
        } else {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "materialized input set contains a non-file entry",
                Some("effectiveInputs"),
                false,
            ));
        }
    }
    Ok(())
}

fn verify_effective_input_set(
    root: &Path,
    inputs: &[InputBindingRequest],
) -> RuntimeResult<Vec<EffectiveInputBinding>> {
    let root_metadata = fs::symlink_metadata(root)
        .map_err(|error| io_error("inspect materialized input set", error))?;
    if root_metadata.file_type().is_symlink() || !root_metadata.is_dir() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "materialized input set root is not a non-symlink directory",
            Some("effectiveInputs"),
            false,
        ));
    }
    let expected = inputs
        .iter()
        .map(|input| PathBuf::from(&input.presentation_relative_path))
        .collect::<BTreeSet<_>>();
    let mut observed = BTreeSet::new();
    collect_materialized_files(root, root, &mut observed)?;
    if observed != expected {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "materialized input set file inventory differs from the committed binding set",
            Some("effectiveInputs"),
            false,
        ));
    }
    let mut effective = Vec::with_capacity(inputs.len());
    for (index, input) in inputs.iter().enumerate() {
        let path = root.join(&input.presentation_relative_path);
        let metadata =
            fs::metadata(&path).map_err(|error| io_error("inspect materialized input", error))?;
        let digest = sha256_file(&path).map_err(map_universal_error)?;
        if digest != input.expected_digest {
            let field = format!("effectiveInputs[{index}].digest");
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "materialized input digest does not match the committed binding",
                Some(&field),
                false,
            ));
        }
        effective.push(EffectiveInputBinding {
            authority: input.authority.clone(),
            relative_object: input.relative_object.clone(),
            digest,
            byte_length: metadata.len(),
            presentation_relative_path: input.presentation_relative_path.clone(),
            access: InputAccessMode::ReadOnly,
        });
    }
    Ok(effective)
}

fn inspect_credential_snapshot(root: &Path) -> RuntimeResult<(String, Vec<String>)> {
    let root_metadata = fs::symlink_metadata(root)
        .map_err(|error| io_error("inspect encrypted credential snapshot set", error))?;
    if root_metadata.file_type().is_symlink() || !root_metadata.is_dir() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "encrypted credential snapshot root is not a non-symlink directory",
            Some("credentialSetId"),
            false,
        ));
    }
    let mut entries = Vec::new();
    for entry in fs::read_dir(root)
        .map_err(|error| io_error("enumerate encrypted credential snapshot", error))?
    {
        let entry = entry
            .map_err(|error| io_error("read encrypted credential snapshot entry", error))?;
        let metadata = fs::symlink_metadata(entry.path())
            .map_err(|error| io_error("inspect encrypted credential snapshot entry", error))?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "encrypted credential snapshot contains a non-regular entry",
                Some("credentialSetId"),
                false,
            ));
        }
        let name = entry.file_name().into_string().map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                "encrypted credential snapshot contains a non-UTF-8 credential name",
                Some("credentialSetId"),
                false,
            )
        })?;
        validate_credential_name(&name, "credentialSetId")?;
        entries.push(CredentialSnapshotEntry {
            name,
            digest: sha256_file(&entry.path()).map_err(map_universal_error)?,
            byte_length: metadata.len(),
        });
    }
    entries.sort_by(|left, right| left.name.cmp(&right.name));
    let manifest = serde_json::to_vec(&entries).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("cannot serialize encrypted credential snapshot manifest: {error}"),
            Some("credentialSetId"),
            false,
        )
    })?;
    let set_id = sha256_bytes(&manifest);
    let names = entries.into_iter().map(|entry| entry.name).collect();
    Ok((set_id, names))
}

pub(super) fn verify_credential_snapshot(
    root: &Path,
    expected_set_id: &str,
) -> RuntimeResult<Vec<String>> {
    let (observed_set_id, names) = inspect_credential_snapshot(root)?;
    if observed_set_id != expected_set_id {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "encrypted credential snapshot does not match the committed credential set",
            Some("credentialSetId"),
            false,
        ));
    }
    Ok(names)
}

fn effective_input_requests_from_plan(
    plan: &RuntimeExecutionPlan,
) -> RuntimeResult<Vec<InputBindingRequest>> {
    canonical_input_binding_requests(
        &plan
            .effective_inputs
            .iter()
            .map(|input| InputBindingRequest {
                authority: input.authority.clone(),
                relative_object: input.relative_object.clone(),
                expected_digest: input.digest.clone(),
                presentation_relative_path: input.presentation_relative_path.clone(),
            })
            .collect::<Vec<_>>(),
    )
}
