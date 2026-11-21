//! Read bounded active logs and select registered terminal evidence.

use super::*;

pub(super) fn output_projection_relative_path(
    kind: &str,
    terminal: bool,
    registered_relative: Option<&str>,
) -> RuntimeResult<PathBuf> {
    let candidate = if terminal {
        registered_relative.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "terminal output has no committed Artifact path",
                Some("artifact"),
                false,
            )
        })?
    } else {
        return Ok(PathBuf::from(format!("{kind}.log")));
    };
    universal::validate_relative_path(candidate, "artifactPath").map_err(|_| {
        RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "terminal output Artifact path is not a valid relative path",
            Some("artifact"),
            false,
        )
    })
}

#[cfg(test)]
mod terminal_output_path_selection_tests {
    use super::output_projection_relative_path;

    #[test]
    fn terminal_uses_registered_seal_and_active_uses_mutable_preview() {
        let active = output_projection_relative_path("stdout", false, None).unwrap();
        assert_eq!(active.to_str(), Some("stdout.log"));
        let sealed =
            output_projection_relative_path("stdout", true, Some("sealed-stdout.log")).unwrap();
        assert_eq!(sealed.to_str(), Some("sealed-stdout.log"));
        let legacy = output_projection_relative_path("stderr", true, Some("stderr.log")).unwrap();
        assert_eq!(legacy.to_str(), Some("stderr.log"));
        assert!(output_projection_relative_path("stdout", true, None).is_err());
        assert!(output_projection_relative_path("stdout", true, Some("../escape")).is_err());
    }
}

pub(super) fn runner_result_still_absent(path: &Path) -> RuntimeResult<bool> {
    match fs::symlink_metadata(path.join("result.json")) {
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => Ok(true),
        Ok(metadata) if metadata.file_type().is_file() => Ok(false),
        Ok(_) => Err(error("Runner result path is not a regular file")),
        Err(err) => Err(io(err)),
    }
}

/// Active Runner logs are an evolving preview, not a committed Artifact.
/// Seek directly to the requested window instead of reading up to the full
/// output ceiling on every Job observation. Terminal logs use the independent
/// Artifact digest check in project() and must still verify all committed bytes.
pub(super) fn active_log_window(
    path: &Path,
    output_ceiling: u64,
    offset: Option<u64>,
    limit: u64,
) -> RuntimeResult<(Vec<u8>, u64, u64, u64)> {
    use std::io::{Read, Seek, SeekFrom};

    let mut file = fs::File::open(path).map_err(io)?;
    let available = file.seek(SeekFrom::End(0)).map_err(io)?;
    if available > output_ceiling {
        return Err(error("output exceeds retained ceiling"));
    }
    let begin = offset
        .unwrap_or(available.saturating_sub(limit))
        .min(available);
    let end = begin.saturating_add(limit).min(available);
    file.seek(SeekFrom::Start(begin)).map_err(io)?;
    let mut window = vec![0; usize::try_from(end - begin).map_err(io)?];
    file.read_exact(&mut window).map_err(io)?;
    Ok((window, begin, end, available))
}
