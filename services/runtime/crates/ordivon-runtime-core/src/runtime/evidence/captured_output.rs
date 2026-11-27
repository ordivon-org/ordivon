use super::super::{
    ArtifactRegistration, AttemptRecord, RuntimeError, RuntimeErrorCode, RuntimeResult,
};
use super::errors::{io_error, map_universal_error};
use super::{STDERR_FILE, STDOUT_FILE};
use crate::universal::{
    open_directory_nofollow, open_regular_file_beneath, sha256_bytes, write_bytes_atomic_if_absent,
    CapturedOutput,
};
use std::{fs, path::Path};

pub(super) fn validate_captured_output(
    attempt: &AttemptRecord,
    output: &CapturedOutput,
    stdout: bool,
) -> RuntimeResult<ArtifactRegistration> {
    let expected_file = if stdout { STDOUT_FILE } else { STDERR_FILE };
    let expected_kind = if stdout { "stdout" } else { "stderr" };
    let expected_id = format!("{}.{}", attempt.attempt_id, expected_kind);
    if output.file_name != expected_file || output.artifact_id != expected_id {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Runner output identity does not match Attempt",
            Some("artifact"),
            false,
        ));
    }
    let bundle = Path::new(&attempt.bundle_path);
    #[cfg(not(unix))]
    let path = bundle.join(expected_file);

    // The Runner owns a live preview log. Its original path is not an
    // immutable Artifact even when a terminal result correctly describes
    // its bytes. Read a bounded, single original handle and verify the
    // complete Runner commitment before publishing a distinct sealed file.
    #[cfg(unix)]
    let original = {
        let root = open_directory_nofollow(bundle)
            .map_err(|error| io_error("open Attempt bundle", error))?;
        open_regular_file_beneath(&root, Path::new(expected_file), true)
            .map_err(|error| io_error("open Runner output", error))?
    };
    #[cfg(not(unix))]
    let original = {
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| io_error("inspect Runner output", error))?;
        if !metadata.file_type().is_file() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Runner output is not a regular non-symlink file",
                Some("artifact"),
                false,
            ));
        }
        fs::File::open(&path).map_err(|error| io_error("open Runner output", error))?
    };
    use std::io::Read;
    let mut bytes = Vec::new();
    original
        .take(output.retained_bytes.saturating_add(1))
        .read_to_end(&mut bytes)
        .map_err(|error| io_error("read Runner output", error))?;
    let digest = sha256_bytes(&bytes);
    if digest != output.digest || bytes.len() as u64 != output.retained_bytes {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Runner output digest or byte length changed",
            Some("artifact"),
            false,
        ));
    }

    // Reuse the native durable temp+sync+atomic-rename writer, not a second
    // Artifact database or a hard link to an inode the original producer can
    // still mutate. Exact retry must never replace different sealed bytes.
    let sealed_name = if stdout {
        "sealed-stdout.log"
    } else {
        "sealed-stderr.log"
    };
    let sealed_path = bundle.join(sealed_name);
    match fs::symlink_metadata(&sealed_path) {
        Ok(metadata) if metadata.file_type().is_file() => {}
        Ok(_) => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Sealed Artifact path is not a regular file",
                Some("artifact"),
                false,
            ));
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            write_bytes_atomic_if_absent(&sealed_path, &bytes).map_err(map_universal_error)?;
        }
        Err(error) => return Err(io_error("inspect sealed output", error)),
    }
    // A concurrent publisher can only certify exactly the same bytes.
    // Never register a temporary, partial or different file as immutable.
    validate_sealed_output(bundle, sealed_name, &bytes)?;
    Ok(ArtifactRegistration {
        artifact_id: expected_id,
        kind: expected_kind.to_string(),
        relative_path: sealed_name.to_string(),
        digest,
        media_type: "text/plain; charset=utf-8".to_string(),
        byte_length: bytes.len() as u64,
        truncated: output.truncated,
    })
}

// Validate the opened seal, not merely equal bytes observed at a pathname.
// A preexisting hard link can alias the Runner's still-mutable preview.
pub(super) fn validate_sealed_output(
    bundle: &Path,
    name: &str,
    expected: &[u8],
) -> RuntimeResult<()> {
    use std::io::Read;
    let conflict = || {
        RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Sealed Artifact is aliased or differs from Runner commitment",
            Some("artifact"),
            false,
        )
    };
    #[cfg(unix)]
    let mut file = {
        let root = open_directory_nofollow(bundle)
            .map_err(|error| io_error("open Attempt bundle", error))?;
        open_regular_file_beneath(&root, Path::new(name), true)
            .map_err(|error| io_error("open sealed output", error))?
    };
    #[cfg(windows)]
    let mut file = {
        use std::os::windows::fs::OpenOptionsExt;
        use windows_sys::Win32::Storage::FileSystem::FILE_FLAG_OPEN_REPARSE_POINT;
        fs::OpenOptions::new()
            .read(true)
            .custom_flags(FILE_FLAG_OPEN_REPARSE_POINT)
            .open(bundle.join(name))
            .map_err(|error| io_error("open sealed output", error))?
    };
    #[cfg(not(any(unix, windows)))]
    let mut file =
        fs::File::open(bundle.join(name)).map_err(|error| io_error("open sealed output", error))?;
    let single_regular_file = |file: &fs::File| -> RuntimeResult<bool> {
        let metadata = file
            .metadata()
            .map_err(|error| io_error("inspect sealed output", error))?;
        if !metadata.is_file() {
            return Ok(false);
        }
        #[cfg(unix)]
        {
            use std::os::unix::fs::MetadataExt;
            Ok(metadata.nlink() == 1)
        }
        #[cfg(windows)]
        {
            use std::os::windows::io::AsRawHandle;
            use windows_sys::Win32::Storage::FileSystem::{
                GetFileInformationByHandle, BY_HANDLE_FILE_INFORMATION,
                FILE_ATTRIBUTE_REPARSE_POINT,
            };
            // SAFETY: a live file handle and writable POD output structure.
            let mut info: BY_HANDLE_FILE_INFORMATION = unsafe { std::mem::zeroed() };
            if unsafe { GetFileInformationByHandle(file.as_raw_handle() as _, &mut info) } == 0 {
                return Err(io_error(
                    "inspect sealed output links",
                    std::io::Error::last_os_error(),
                ));
            }
            Ok(info.nNumberOfLinks == 1
                && info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT == 0)
        }
        #[cfg(not(any(unix, windows)))]
        Ok(false)
    };
    if !single_regular_file(&file)? {
        return Err(conflict());
    }
    // The Runner bytes are already retained in memory. Compare the seal
    // with a fixed-size buffer rather than allocating a second full copy.
    let mut buffer = [0_u8; 64 * 1024];
    for chunk in expected.chunks(buffer.len()) {
        let observed = &mut buffer[..chunk.len()];
        if let Err(error) = file.read_exact(observed) {
            if error.kind() == std::io::ErrorKind::UnexpectedEof {
                return Err(conflict());
            }
            return Err(io_error("read sealed output", error));
        }
        if observed != chunk {
            return Err(conflict());
        }
    }
    let extra = file
        .read(&mut buffer[..1])
        .map_err(|error| io_error("read sealed output", error))?;
    if extra != 0 || !single_regular_file(&file)? {
        return Err(conflict());
    }
    Ok(())
}
