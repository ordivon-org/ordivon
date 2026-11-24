use crate::universal::sha256_bytes;
use std::fs;
use std::fs::OpenOptions;
use std::io::Read;
#[cfg(unix)]
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;

const MAX_RUNTIME_RELEASE_RECEIPT_BYTES: u64 = 1_048_576;

#[cfg(unix)]
fn open_regular_file_nofollow(path: &Path) -> std::io::Result<std::fs::File> {
    OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)
}

#[cfg(windows)]
fn open_regular_file_nofollow(path: &Path) -> std::io::Result<std::fs::File> {
    use std::os::windows::fs::{MetadataExt, OpenOptionsExt};

    const FILE_FLAG_OPEN_REPARSE_POINT: u32 = 0x0020_0000;
    const FILE_ATTRIBUTE_DIRECTORY: u32 = 0x0000_0010;
    const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x0000_0400;

    let file = OpenOptions::new()
        .read(true)
        .custom_flags(FILE_FLAG_OPEN_REPARSE_POINT)
        .open(path)?;
    let metadata = file.metadata()?;
    let attributes = metadata.file_attributes();
    if !metadata.is_file()
        || attributes & FILE_ATTRIBUTE_DIRECTORY != 0
        || attributes & FILE_ATTRIBUTE_REPARSE_POINT != 0
    {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "secure receipt open requires a regular non-reparse file",
        ));
    }
    Ok(file)
}

#[cfg(not(any(unix, windows)))]
fn open_regular_file_nofollow(_path: &Path) -> std::io::Result<std::fs::File> {
    Err(std::io::Error::new(
        std::io::ErrorKind::Unsupported,
        "secure no-follow regular-file open is not implemented for this platform",
    ))
}

pub(super) fn release_receipt_json(
    path: &Path,
) -> Result<Option<(serde_json::Value, String)>, String> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(_) => return Err("RELEASE_RECEIPT_METADATA_UNAVAILABLE".to_string()),
    };
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err("RELEASE_RECEIPT_FILE_UNSAFE".to_string());
    }
    if metadata.len() > MAX_RUNTIME_RELEASE_RECEIPT_BYTES {
        return Err("RELEASE_RECEIPT_FILE_TOO_LARGE".to_string());
    }
    let mut file =
        open_regular_file_nofollow(path).map_err(|_| "RELEASE_RECEIPT_OPEN_FAILED".to_string())?;
    let mut bytes = Vec::new();
    std::io::Read::by_ref(&mut file)
        .take(MAX_RUNTIME_RELEASE_RECEIPT_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "RELEASE_RECEIPT_READ_FAILED".to_string())?;
    if bytes.len() as u64 > MAX_RUNTIME_RELEASE_RECEIPT_BYTES {
        return Err("RELEASE_RECEIPT_FILE_TOO_LARGE".to_string());
    }
    let value = serde_json::from_slice::<serde_json::Value>(&bytes)
        .map_err(|_| "RELEASE_RECEIPT_JSON_INVALID".to_string())?;
    if !value.is_object() {
        return Err("RELEASE_RECEIPT_JSON_INVALID".to_string());
    }
    Ok(Some((value, sha256_bytes(&bytes))))
}
