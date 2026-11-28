//! Read bounded active logs and select registered terminal evidence.

use super::{error, io, universal, RuntimeError, RuntimeErrorCode, RuntimeResult};
use std::{
    fs,
    path::{Path, PathBuf},
};

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
pub(super) type LogWindow = (Vec<u8>, u64, u64, u64);

pub(super) fn active_log_window(
    path: &Path,
    output_ceiling: u64,
    offset: Option<u64>,
    limit: u64,
) -> RuntimeResult<Option<LogWindow>> {
    use std::io::{ErrorKind, Read, Seek, SeekFrom};

    let parent = path
        .parent()
        .ok_or_else(|| error("active output has no directory"))?;
    let name = path
        .file_name()
        .ok_or_else(|| error("active output has no file name"))?;
    let root = universal::open_directory_nofollow(parent).map_err(io)?;
    let mut file = match universal::open_active_preview_beneath(&root, Path::new(name)) {
        Ok(file) => file,
        Err(e) if e.kind() == ErrorKind::NotFound => return Ok(None),
        Err(e) => return Err(io(e)),
    };
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
    Ok(Some((window, begin, end, available)))
}

/// Verify the entire committed stream, retaining only the requested byte window.
/// The window is never returned until both length and SHA-256 are exact.
/// In particular, a zero-byte tail is not permission to skip verification.
pub(super) fn verified_terminal_log_window(
    file: impl std::io::Read,
    output_ceiling: u64,
    expected_length: i64,
    expected_digest: &str,
    offset: Option<u64>,
    limit: u64,
) -> RuntimeResult<(Vec<u8>, u64, u64, u64)> {
    use sha2::{Digest, Sha256};
    use std::io::Read;
    let conflict = || {
        RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "terminal output bytes disagree with PostgreSQL Artifact evidence",
            Some("artifact"),
            false,
        )
    };
    let expected = u64::try_from(expected_length).ok();
    let available = expected.unwrap_or(0);
    let begin = offset
        .unwrap_or(available.saturating_sub(limit))
        .min(available);
    let end = begin.saturating_add(limit).min(available);
    let mut window = Vec::new();
    let mut hash = Sha256::new();
    let mut count = 0_u64;
    let mut reader = file.take(output_ceiling.saturating_add(1));
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let n = match reader.read(&mut buffer) {
            Err(e) if e.kind() == std::io::ErrorKind::Interrupted => continue,
            r => r.map_err(io)?,
        };
        if n == 0 {
            break;
        }
        let next = count
            .checked_add(n as u64)
            .ok_or_else(|| error("output exceeds retained ceiling"))?;
        if next > output_ceiling {
            return Err(error("output exceeds retained ceiling"));
        }
        hash.update(&buffer[..n]);
        let overlap_begin = count.max(begin);
        let overlap_end = next.min(end);
        if overlap_begin < overlap_end {
            window.extend_from_slice(
                &buffer[(overlap_begin - count) as usize..(overlap_end - count) as usize],
            );
        }
        count = next;
    }
    let digest: [u8; 32] = hash.finalize().into();
    if expected != Some(count) || universal::parse_sha256_digest(expected_digest) != Some(digest) {
        return Err(conflict());
    }
    Ok((window, begin, end, count))
}

#[cfg(test)]
mod terminal_output_path_selection_tests {
    use super::{output_projection_relative_path, verified_terminal_log_window};
    use crate::runtime::RuntimeErrorCode;
    use crate::universal::sha256_bytes;

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
    #[test]
    fn streaming_terminal_window_matches_original_full_read_oracle() {
        let bytes: Vec<u8> = (0..(2 * 65536 + 17)).map(|i| (i % 251) as u8).collect();
        for data in [&bytes[..], &bytes[..65537], &bytes[..2], &bytes[..0]] {
            let length = data.len() as u64;
            let digest = sha256_bytes(data);
            for offset in [
                None,
                Some(0),
                Some(65530),
                Some(65536),
                Some(length),
                Some(u64::MAX),
            ] {
                for limit in [0, 1, 31, 65536, 131100, u64::MAX] {
                    let begin = offset.unwrap_or(length.saturating_sub(limit)).min(length);
                    let end = begin.saturating_add(limit).min(length);
                    let got = verified_terminal_log_window(
                        data,
                        length,
                        length as i64,
                        &digest,
                        offset,
                        limit,
                    )
                    .unwrap();
                    assert_eq!(
                        got,
                        (
                            data[begin as usize..end as usize].to_vec(),
                            begin,
                            end,
                            length
                        )
                    );
                }
            }
        }
    }

    #[test]
    fn streaming_terminal_window_rejects_corruption_even_outside_window_or_zero_tail() {
        let bytes = vec![42; 2 * 65536 + 1];
        let digest = sha256_bytes(&bytes);
        let mut corrupted = bytes.clone();
        corrupted[65536] ^= 1;
        for limit in [0, 1, 100] {
            for candidate in [&corrupted[..], &bytes[..bytes.len() - 1]] {
                let err = verified_terminal_log_window(
                    candidate,
                    bytes.len() as u64,
                    bytes.len() as i64,
                    &digest,
                    Some(0),
                    limit,
                )
                .unwrap_err();
                assert_eq!(err.code, RuntimeErrorCode::ArtifactIdentityConflict);
            }
        }
        for (length, expected_digest) in [
            (-1, digest.as_str()),
            (bytes.len() as i64, "sha256:invalid"),
        ] {
            assert_eq!(
                verified_terminal_log_window(
                    &bytes[..],
                    bytes.len() as u64,
                    length,
                    expected_digest,
                    None,
                    0
                )
                .unwrap_err()
                .code,
                RuntimeErrorCode::ArtifactIdentityConflict
            );
        }
        assert!(verified_terminal_log_window(
            &bytes[..],
            65536,
            bytes.len() as i64,
            &digest,
            None,
            0
        )
        .is_err());
    }
}

#[cfg(all(test, windows))]
mod native_preview_sharing_tests {
    use super::*;
    use std::io::Write;
    use std::os::windows::fs::OpenOptionsExt;
    use windows_sys::Win32::Storage::FileSystem::FILE_SHARE_READ;

    #[test]
    fn preview_coexists_with_launcher_writer_without_relaxing_sealed_open() {
        let dir = tempfile::TempDir::new().unwrap();
        let path = dir.path().join("stdout.log");
        let mut writer = fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .share_mode(FILE_SHARE_READ)
            .open(&path)
            .unwrap();
        writer.write_all(b"first").unwrap();
        let root = universal::open_directory_nofollow(dir.path()).unwrap();
        assert!(
            universal::open_regular_file_beneath(&root, Path::new("stdout.log"), true).is_err()
        );
        let first = active_log_window(&path, 64, None, 64).unwrap().unwrap();
        assert_eq!(first.0, b"first");
        writer.write_all(b"second").unwrap();
        let second = active_log_window(&path, 64, Some(first.2), 64)
            .unwrap()
            .unwrap();
        assert_eq!(second.0, b"second");
        drop(writer);
        assert!(universal::open_regular_file_beneath(&root, Path::new("stdout.log"), true).is_ok());
    }
}
