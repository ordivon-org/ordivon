fn workspace_record_page(
    records: Vec<crate::universal::WorkspaceRecord>,
    limit: u32,
    cursor: Option<&super::RuntimeWorkspaceListCursor>,
) -> (
    Vec<crate::universal::WorkspaceRecord>,
    Option<super::RuntimeWorkspaceListCursor>,
) {
    let mut page = records
        .into_iter()
        .filter(|record| {
            let Some(cursor) = cursor else {
                return true;
            };
            record.created_unix_ms < u128::from(cursor.created_at_ms)
                || (record.created_unix_ms == u128::from(cursor.created_at_ms)
                    && record.workspace_id > cursor.workspace_id)
        })
        .take(limit as usize + 1)
        .collect::<Vec<_>>();
    if page.len() <= limit as usize {
        return (page, None);
    }
    page.truncate(limit as usize);
    let last = page.last().expect("non-empty page after limit validation");
    let next_cursor = super::RuntimeWorkspaceListCursor {
        created_at_ms: u64::try_from(last.created_unix_ms).unwrap_or(u64::MAX),
        workspace_id: last.workspace_id.clone(),
    };
    (page, Some(next_cursor))
}

fn verify_published_bundle(
    final_path: &Path,
    request_bytes: &[u8],
    plan_bytes: &[u8],
    manifest_bytes: &[u8],
) -> RuntimeResult<()> {
    let metadata = fs::symlink_metadata(final_path)
        .map_err(|error| io_error("inspect published Attempt bundle", error))?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "published Attempt bundle is not a non-symlink directory",
            Some("bundlePath"),
            false,
        ));
    }
    for (name, expected) in [
        (RUNNER_REQUEST_FILE, request_bytes),
        (PLAN_FILE, plan_bytes),
        (BUNDLE_MANIFEST_FILE, manifest_bytes),
    ] {
        let path = final_path.join(name);
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| io_error("inspect published Attempt bundle file", error))?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "published Attempt bundle contains a non-regular file",
                Some("bundlePath"),
                false,
            ));
        }
        let observed = fs::read(&path)
            .map_err(|error| io_error("read published Attempt bundle file", error))?;
        if observed != expected {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "published Attempt bundle bytes do not match deterministic Attempt identity",
                Some("bundlePath"),
                false,
            ));
        }
    }
    Ok(())
}
