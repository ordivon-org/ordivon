use serde::Serialize;
use sha2::{Digest, Sha256};
#[cfg(unix)]
use std::ffi::CString;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
#[cfg(unix)]
use std::os::fd::{AsRawFd, FromRawFd};
#[cfg(unix)]
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
#[cfg(windows)]
use std::os::windows::ffi::OsStrExt as WindowsOsStrExt;
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

use super::{UniversalExecError, UniversalExecErrorCode};

pub const WORKSPACE_ID_MIN_LENGTH: usize = 1;
pub const WORKSPACE_ID_MAX_LENGTH: usize = 96;
pub const WORKSPACE_ID_PATTERN: &str = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$";
pub const ENVIRONMENT_VARIABLE_NAME_PATTERN: &str = r"^[A-Za-z_][A-Za-z0-9_]*$";

#[cfg(unix)]
#[repr(C)]
struct OpenHow {
    flags: u64,
    mode: u64,
    resolve: u64,
}

#[cfg(unix)]
const RESOLVE_NO_MAGICLINKS: u64 = 0x02;
#[cfg(unix)]
const RESOLVE_NO_SYMLINKS: u64 = 0x04;
#[cfg(unix)]
const RESOLVE_BENEATH: u64 = 0x08;

/// Serialize the trusted PG Attempt's cancellation marker publication with
/// the native Runner's last cancel check and user Command::spawn.
#[cfg(unix)]
pub(crate) fn lock_attempt_spawn_fence(task_dir: &Path) -> Result<File, UniversalExecError> {
    let control_root =
        fs::symlink_metadata(task_dir).map_err(|error| io_error(task_dir, "stat", error))?;
    // A lock inode is stable only if the payload cannot replace its parent
    // directory entry. The PG issuer owns the root-only control directory.
    if !control_root.is_dir() || control_root.uid() != 0 || control_root.mode() & 0o077 != 0 {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "PG Attempt spawn fence requires a root-owned private control directory",
            Some("taskDir"),
            false,
        ));
    }
    let path = task_dir.join(".spawn-fence.lock");
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW | libc::O_CLOEXEC)
        .open(&path)
        .map_err(|error| io_error(&path, "open", error))?;
    let metadata = file
        .metadata()
        .map_err(|error| io_error(&path, "stat", error))?;
    // The PG control root is UID0-owned and 0700; contained child is
    // independently nonroot. Never follow or accept a replaceable lock inode.
    if !metadata.is_file()
        || metadata.uid() != 0
        || metadata.mode() & 0o077 != 0
        || metadata.nlink() != 1
    {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "PG Attempt spawn fence must be a single-link root-owned private file",
            Some("taskDir"),
            false,
        ));
    }
    file.lock()
        .map_err(|error| io_error(&path, "lock", error))?;
    Ok(file)
}

#[cfg(unix)]
pub(crate) fn open_directory_nofollow(path: &Path) -> std::io::Result<File> {
    OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_DIRECTORY | libc::O_CLOEXEC | libc::O_NOFOLLOW)
        .open(path)
}

#[cfg(unix)]
pub(crate) fn open_regular_file_beneath(
    root_file: &File,
    relative: &Path,
    deny_parent_symlinks: bool,
) -> std::io::Result<File> {
    let relative = CString::new(relative.as_os_str().as_encoded_bytes()).map_err(|_| {
        std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            "relative path contains NUL",
        )
    })?;
    let mut resolve = RESOLVE_NO_MAGICLINKS | RESOLVE_BENEATH;
    if deny_parent_symlinks {
        resolve |= RESOLVE_NO_SYMLINKS;
    }
    let how = OpenHow {
        flags: (libc::O_RDONLY | libc::O_CLOEXEC | libc::O_NOFOLLOW | libc::O_NONBLOCK) as u64,
        mode: 0,
        resolve,
    };
    let fd = unsafe {
        libc::syscall(
            libc::SYS_openat2,
            root_file.as_raw_fd(),
            relative.as_ptr(),
            &how,
            std::mem::size_of::<OpenHow>(),
        )
    };
    if fd < 0 {
        return Err(std::io::Error::last_os_error());
    }
    let file = unsafe { File::from_raw_fd(fd as i32) };
    let metadata = file.metadata()?;
    if !metadata.is_file() {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            "resolved object is not a regular file",
        ));
    }
    Ok(file)
}

#[cfg(windows)]
pub(crate) fn open_directory_nofollow(path: &Path) -> std::io::Result<File> {
    use std::os::windows::fs::{MetadataExt, OpenOptionsExt};
    use windows_sys::Win32::Storage::FileSystem::{
        FILE_ATTRIBUTE_REPARSE_POINT, FILE_FLAG_BACKUP_SEMANTICS, FILE_FLAG_OPEN_REPARSE_POINT,
    };
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT)
        .open(path)?;
    let metadata = file.metadata()?;
    if !metadata.is_dir() || metadata.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0 {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            "authority must be a native directory without a reparse point",
        ));
    }
    Ok(file)
}

/// Mutable previews may coexist with an existing writer, but never acquire
/// write access themselves. Keep the sealed Artifact policy unchanged.
pub(crate) fn open_active_preview_beneath(
    root_file: &File,
    relative: &Path,
) -> std::io::Result<File> {
    #[cfg(windows)]
    {
        open_windows_regular_file_beneath(root_file, relative, true)
    }
    #[cfg(not(windows))]
    {
        open_regular_file_beneath(root_file, relative, true)
    }
}

#[cfg(windows)]
pub(crate) fn open_regular_file_beneath(
    root_file: &File,
    relative: &Path,
    _deny_parent_symlinks: bool,
) -> std::io::Result<File> {
    open_windows_regular_file_beneath(root_file, relative, false)
}

#[cfg(windows)]
fn open_windows_regular_file_beneath(
    root_file: &File,
    relative: &Path,
    active_preview: bool,
) -> std::io::Result<File> {
    use std::os::windows::fs::MetadataExt;
    use std::os::windows::io::{AsRawHandle, FromRawHandle};
    use windows_sys::Wdk::Foundation::OBJECT_ATTRIBUTES;
    use windows_sys::Wdk::Storage::FileSystem::{
        NtCreateFile, FILE_NON_DIRECTORY_FILE, FILE_OPEN, FILE_OPEN_REPARSE_POINT,
        FILE_SYNCHRONOUS_IO_NONALERT,
    };
    use windows_sys::Win32::Foundation::{
        RtlNtStatusToDosError, OBJ_CASE_INSENSITIVE, OBJ_DONT_REPARSE, UNICODE_STRING,
    };
    use windows_sys::Win32::Storage::FileSystem::{
        FILE_ATTRIBUTE_NORMAL, FILE_ATTRIBUTE_REPARSE_POINT, FILE_READ_ATTRIBUTES, FILE_READ_DATA,
        FILE_SHARE_READ, FILE_SHARE_WRITE, SYNCHRONIZE,
    };
    use windows_sys::Win32::System::IO::IO_STATUS_BLOCK;
    let invalid = || {
        std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            "invalid Windows authority-relative file path",
        )
    };
    let mut path = Vec::new();
    for component in relative.components() {
        let Component::Normal(part) = component else {
            return Err(invalid());
        };
        if !path.is_empty() {
            path.push(b'\x5c' as u16);
        }
        for unit in part.encode_wide() {
            // Reject ADS and NUL. Component validation already excluded rooted paths and traversal.
            if unit == 0 || unit == b':' as u16 {
                return Err(invalid());
            }
            path.push(unit);
        }
    }
    let length =
        u16::try_from(path.len().checked_mul(2).ok_or_else(invalid)?).map_err(|_| invalid())?;
    if length == 0 {
        return Err(invalid());
    }
    let mut name = UNICODE_STRING {
        Length: length,
        MaximumLength: length,
        Buffer: path.as_mut_ptr(),
    };
    let attributes = OBJECT_ATTRIBUTES {
        Length: std::mem::size_of::<OBJECT_ATTRIBUTES>() as u32,
        RootDirectory: root_file.as_raw_handle(),
        ObjectName: &mut name,
        Attributes: OBJ_CASE_INSENSITIVE | OBJ_DONT_REPARSE,
        SecurityDescriptor: std::ptr::null_mut(),
        SecurityQualityOfService: std::ptr::null_mut(),
    };
    let mut status_block = IO_STATUS_BLOCK::default();
    let mut handle = std::ptr::null_mut();
    // SAFETY: owned directory handle and stable counted UTF-16 buffer.
    // Directory-relative name resolution and no-reparse are enforced by NT.
    let status = unsafe {
        NtCreateFile(
            &mut handle,
            FILE_READ_DATA | FILE_READ_ATTRIBUTES | SYNCHRONIZE,
            &attributes,
            &mut status_block,
            std::ptr::null(),
            FILE_ATTRIBUTE_NORMAL,
            if active_preview {
                FILE_SHARE_READ | FILE_SHARE_WRITE
            } else {
                FILE_SHARE_READ
            },
            FILE_OPEN,
            FILE_NON_DIRECTORY_FILE | FILE_SYNCHRONOUS_IO_NONALERT | FILE_OPEN_REPARSE_POINT,
            std::ptr::null(),
            0,
        )
    };
    if status < 0 {
        return Err(std::io::Error::from_raw_os_error(
            unsafe { RtlNtStatusToDosError(status) } as i32,
        ));
    }
    if handle.is_null() {
        return Err(std::io::Error::other("NT opened no file handle"));
    }
    // SAFETY: success transfers this newly opened handle to File.
    let file = unsafe { File::from_raw_handle(handle) };
    let metadata = file.metadata()?;
    if !metadata.is_file() || metadata.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0 {
        return Err(invalid());
    }
    Ok(file)
}

#[cfg(not(any(unix, windows)))]
pub(crate) fn open_directory_nofollow(_path: &Path) -> std::io::Result<File> {
    Err(std::io::Error::new(
        std::io::ErrorKind::Unsupported,
        "secure no-follow directory handles are not implemented for this platform",
    ))
}

#[cfg(not(any(unix, windows)))]
pub(crate) fn open_regular_file_beneath(
    _root_file: &File,
    _relative: &Path,
    _deny_parent_symlinks: bool,
) -> std::io::Result<File> {
    Err(std::io::Error::new(
        std::io::ErrorKind::Unsupported,
        "secure beneath-root file resolution is not implemented for this platform",
    ))
}

pub(crate) fn validate_id(value: &str, field: &str) -> Result<(), UniversalExecError> {
    let mut chars = value.chars();
    let valid_first = chars
        .next()
        .is_some_and(|character| character.is_ascii_alphanumeric());
    if !valid_first
        || value.len() > WORKSPACE_ID_MAX_LENGTH
        || !chars.all(|character| {
            character.is_ascii_alphanumeric() || matches!(character, '.' | '_' | '-')
        })
    {
        return Err(invalid(
            format!("{field} must match [A-Za-z0-9][A-Za-z0-9._-]{{0,95}}"),
            field,
        ));
    }
    Ok(())
}

pub(crate) fn validate_relative_path(
    value: &str,
    field: &str,
) -> Result<PathBuf, UniversalExecError> {
    let path = Path::new(value);
    if value.is_empty() || path.is_absolute() || value.as_bytes().contains(&0) {
        return Err(invalid(
            format!("{field} must be a non-empty relative path"),
            field,
        ));
    }
    if path.components().any(|component| {
        matches!(
            component,
            Component::ParentDir | Component::RootDir | Component::Prefix(_)
        )
    }) {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspacePathDenied,
            format!("{field} cannot escape the workspace"),
            Some(field),
            false,
        ));
    }
    Ok(path.to_path_buf())
}

#[cfg(unix)]
pub(crate) fn linux_exec_string_limit_bytes() -> Result<usize, UniversalExecError> {
    let page_size = unsafe { libc::sysconf(libc::_SC_PAGESIZE) };
    if page_size <= 0 {
        return Err(invalid(
            "cannot determine Linux execve per-string limit",
            "execution",
        ));
    }
    usize::try_from(page_size)
        .ok()
        .and_then(|page_size| page_size.checked_mul(32))
        .and_then(|bytes| bytes.checked_sub(1))
        .ok_or_else(|| {
            invalid(
                "Linux execve per-string limit is not representable",
                "execution",
            )
        })
}

#[cfg(unix)]
pub(crate) fn linux_exec_payload_limit_bytes() -> Result<usize, UniversalExecError> {
    let arg_max = unsafe { libc::sysconf(libc::_SC_ARG_MAX) };
    if arg_max <= 0 {
        return Err(invalid(
            "cannot determine Linux execve argv/environment limit",
            "execution",
        ));
    }
    usize::try_from(arg_max).map_err(|_| {
        invalid(
            "Linux execve argv/environment limit is not representable",
            "execution",
        )
    })
}

#[cfg(unix)]
pub(crate) fn validate_args(args: &[String]) -> Result<(), UniversalExecError> {
    let max_string_bytes = linux_exec_string_limit_bytes()?;
    if args
        .iter()
        .any(|arg| arg.len() > max_string_bytes || arg.as_bytes().contains(&0))
    {
        return Err(invalid(
            format!(
                "args contains a value that exceeds the Linux execve per-string limit of {max_string_bytes} bytes or contains NUL"
            ),
            "args",
        ));
    }
    Ok(())
}

#[cfg(all(not(unix), test))]
pub(crate) fn linux_exec_string_limit_bytes() -> Result<usize, UniversalExecError> {
    Err(UniversalExecError::new(
        UniversalExecErrorCode::ToolUnavailable,
        "Linux execve limits are unavailable on this platform",
        Some("execution"),
        false,
    ))
}

#[cfg(all(not(unix), test))]
pub(crate) fn linux_exec_payload_limit_bytes() -> Result<usize, UniversalExecError> {
    Err(UniversalExecError::new(
        UniversalExecErrorCode::ToolUnavailable,
        "Linux execve limits are unavailable on this platform",
        Some("execution"),
        false,
    ))
}

#[cfg(all(not(unix), test))]
pub(crate) fn validate_args(args: &[String]) -> Result<(), UniversalExecError> {
    if args.iter().any(|arg| arg.as_bytes().contains(&0)) {
        return Err(invalid("args contains NUL", "args"));
    }
    Err(UniversalExecError::new(
        UniversalExecErrorCode::ToolUnavailable,
        "Linux execve payload validation is unavailable on this platform",
        Some("args"),
        false,
    ))
}

pub(crate) fn validate_env(
    env: &std::collections::BTreeMap<String, String>,
) -> Result<(), UniversalExecError> {
    for (name, value) in env {
        let mut chars = name.chars();
        let valid_name = chars
            .next()
            .is_some_and(|first| first == '_' || first.is_ascii_alphabetic())
            && chars.all(|character| character == '_' || character.is_ascii_alphanumeric());
        if !valid_name || value.as_bytes().contains(&0) {
            return Err(invalid(format!("invalid environment entry {name}"), "env"));
        }
    }
    Ok(())
}

#[cfg(unix)]
pub(crate) fn validate_exec_payload(
    args: &[String],
    env: &std::collections::BTreeMap<String, String>,
    field: &str,
) -> Result<(), UniversalExecError> {
    validate_args(args)?;
    validate_env(env)?;
    let max_string_bytes = linux_exec_string_limit_bytes()?;
    if env.iter().any(|(name, value)| {
        name.len().saturating_add(1).saturating_add(value.len()) > max_string_bytes
    }) {
        return Err(invalid(
            format!(
                "env contains an entry that exceeds the Linux execve per-string limit of {max_string_bytes} bytes"
            ),
            "env",
        ));
    }

    let mut string_bytes = 0usize;
    for arg in args {
        string_bytes = string_bytes
            .checked_add(arg.len())
            .and_then(|value| value.checked_add(1))
            .ok_or_else(|| invalid("execve payload size overflow", field))?;
    }
    for (name, value) in env {
        string_bytes = string_bytes
            .checked_add(name.len())
            .and_then(|total| total.checked_add(1))
            .and_then(|total| total.checked_add(value.len()))
            .and_then(|total| total.checked_add(1))
            .ok_or_else(|| invalid("execve payload size overflow", field))?;
    }

    // Linux accounts argv/env pointer tables against the same stack-backed exec budget.
    // Include both terminating null pointers so admission stays on the safe side of E2BIG.
    let pointer_count = args
        .len()
        .checked_add(env.len())
        .and_then(|count| count.checked_add(2))
        .ok_or_else(|| invalid("execve pointer count overflow", field))?;
    let pointer_bytes = pointer_count
        .checked_mul(std::mem::size_of::<usize>())
        .ok_or_else(|| invalid("execve pointer size overflow", field))?;
    let required_bytes = string_bytes
        .checked_add(pointer_bytes)
        .ok_or_else(|| invalid("execve payload size overflow", field))?;
    let max_bytes = linux_exec_payload_limit_bytes()?;
    if required_bytes > max_bytes {
        return Err(invalid(
            format!(
                "argv and environment require {required_bytes} bytes, exceeding the host Linux execve limit of {max_bytes} bytes"
            ),
            field,
        ));
    }
    Ok(())
}

#[cfg(not(unix))]
pub(crate) fn validate_exec_payload(
    args: &[String],
    env: &std::collections::BTreeMap<String, String>,
    field: &str,
) -> Result<(), UniversalExecError> {
    if args.iter().any(|arg| arg.as_bytes().contains(&0)) {
        return Err(invalid("args contains NUL", field));
    }
    validate_env(env)?;
    Err(UniversalExecError::new(
        UniversalExecErrorCode::ToolUnavailable,
        "Linux execve payload validation is unavailable on this platform",
        Some(field),
        false,
    ))
}

pub(crate) fn invalid(message: impl Into<String>, field: impl Into<String>) -> UniversalExecError {
    let field = field.into();
    UniversalExecError::new(
        UniversalExecErrorCode::InvalidRequest,
        message,
        Some(&field),
        false,
    )
}

pub(crate) fn now_unix_ms() -> Result<u128, UniversalExecError> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis())
        .map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::IoError,
                format!("system clock is before unix epoch: {error}"),
                None,
                false,
            )
        })
}

pub(crate) fn sha256_bytes(bytes: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(bytes)))
}

pub(crate) fn parse_sha256_digest(value: &str) -> Option<[u8; 32]> {
    let encoded = value.strip_prefix("sha256:")?;
    // The fixed-size decoder enforces length and hexadecimal syntax.
    // The wire contract additionally rejects uppercase hexadecimal.
    let digest = <[u8; 32] as hex::FromHex>::from_hex(encoded).ok()?;
    (!encoded.bytes().any(|byte| byte.is_ascii_uppercase())).then_some(digest)
}

pub(crate) fn sha256_file(path: &Path) -> Result<String, UniversalExecError> {
    let mut file = File::open(path).map_err(|error| io_error(path, "open", error))?;
    let mut hasher = Sha256::new();
    let mut buffer = [0_u8; 64 * 1024];
    loop {
        let read = file
            .read(&mut buffer)
            .map_err(|error| io_error(path, "read", error))?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

pub(crate) fn write_json_atomic(
    path: &Path,
    value: &impl Serialize,
) -> Result<(), UniversalExecError> {
    let bytes = serde_json::to_vec_pretty(value).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            format!("cannot serialize {}: {error}", path.display()),
            None,
            false,
        )
    })?;
    write_bytes_atomic(path, &bytes)
}

pub(crate) fn write_bytes_atomic(path: &Path, bytes: &[u8]) -> Result<(), UniversalExecError> {
    write_bytes_atomic_mode(path, bytes, true).map(|_| ())
}

/// Publish an immutable, newly staged file without replacing an existing name.
/// False means another publisher already owns the name, not that its bytes match.
pub(crate) fn write_bytes_atomic_if_absent(
    path: &Path,
    bytes: &[u8],
) -> Result<bool, UniversalExecError> {
    write_bytes_atomic_mode(path, bytes, false)
}

fn write_bytes_atomic_mode(
    path: &Path,
    bytes: &[u8],
    replace_existing: bool,
) -> Result<bool, UniversalExecError> {
    let parent = path
        .parent()
        .ok_or_else(|| invalid("path has no parent", "path"))?;
    fs::create_dir_all(parent).map_err(|error| io_error(parent, "create", error))?;
    let temp = parent.join(format!(
        ".{}.tmp-{}",
        path.file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("file"),
        Uuid::now_v7()
    ));
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&temp)
        .map_err(|error| io_error(&temp, "create", error))?;
    let staged = file.write_all(bytes).and_then(|_| file.sync_all());
    drop(file);
    if let Err(error) = staged {
        let _ = fs::remove_file(&temp);
        return Err(io_error(&temp, "write", error));
    }
    match rename_path_native(&temp, path, replace_existing) {
        Ok(()) => {
            sync_rename_parents(&temp, path)?;
            Ok(true)
        }
        Err(error) if !replace_existing && error.kind() == std::io::ErrorKind::AlreadyExists => {
            fs::remove_file(&temp)
                .map_err(|error| io_error(&temp, "remove losing stage", error))?;
            sync_directory(parent)?;
            Ok(false)
        }
        Err(error) => {
            let _ = fs::remove_file(&temp);
            Err(io_error(path, "publish atomic file", error))
        }
    }
}

pub(crate) fn rename_path_durable(
    source: &Path,
    destination: &Path,
    replace_existing: bool,
    operation: &str,
) -> Result<(), UniversalExecError> {
    rename_path_native(source, destination, replace_existing)
        .map_err(|error| io_error(destination, operation, error))?;
    sync_rename_parents(source, destination)
}

fn sync_rename_parents(source: &Path, destination: &Path) -> Result<(), UniversalExecError> {
    if let Some(parent) = destination.parent() {
        sync_directory(parent)?;
    }
    if let (Some(source_parent), Some(destination_parent)) = (source.parent(), destination.parent())
    {
        if source_parent != destination_parent {
            sync_directory(source_parent)?;
        }
    }
    Ok(())
}

/// Normalize DOS paths before crossing the raw Win32 rename boundary.
/// Rust's file APIs already accept long paths; MoveFileExW requires an
/// explicit verbatim carrier when the staging name exceeds MAX_PATH.
#[cfg(windows)]
fn windows_rename_path(path: &Path) -> std::io::Result<Vec<u16>> {
    use std::ffi::OsString;
    use std::path::Prefix;

    let absolute = std::path::absolute(path)?;
    let extended = match absolute.components().next() {
        Some(Component::Prefix(prefix)) => match prefix.kind() {
            Prefix::Disk(_) => {
                let mut value = OsString::from(r"\\?\");
                value.push(absolute.as_os_str());
                value
            }
            Prefix::UNC(_, _) => {
                let mut value = OsString::from(r"\\?\UNC\");
                let tail: OsString = std::os::windows::ffi::OsStringExt::from_wide(
                    &absolute
                        .as_os_str()
                        .encode_wide()
                        .skip(2)
                        .collect::<Vec<_>>(),
                );
                value.push(tail);
                value
            }
            Prefix::VerbatimDisk(_) | Prefix::VerbatimUNC(_, _) => absolute.into_os_string(),
            _ => {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::InvalidInput,
                    "rename requires a filesystem drive or UNC path",
                ));
            }
        },
        _ => {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "rename requires an absolute Windows filesystem path",
            ));
        }
    };
    // NUL must never truncate the native authority path.
    if extended.encode_wide().any(|unit| unit == 0) {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            "rename path contains NUL",
        ));
    }
    Ok(extended.encode_wide().chain(std::iter::once(0)).collect())
}

fn rename_path_native(
    source: &Path,
    destination: &Path,
    replace_existing: bool,
) -> std::io::Result<()> {
    #[cfg(windows)]
    {
        use windows_sys::Win32::Storage::FileSystem::{
            MoveFileExW, MOVEFILE_REPLACE_EXISTING, MOVEFILE_WRITE_THROUGH,
        };
        let source_wide = windows_rename_path(source)?;
        let destination_wide = windows_rename_path(destination)?;
        let mut flags = MOVEFILE_WRITE_THROUGH;
        if replace_existing {
            flags |= MOVEFILE_REPLACE_EXISTING;
        }
        let moved = unsafe { MoveFileExW(source_wide.as_ptr(), destination_wide.as_ptr(), flags) };
        if moved == 0 {
            Err(std::io::Error::last_os_error())
        } else {
            Ok(())
        }
    }

    #[cfg(not(windows))]
    {
        if replace_existing {
            return fs::rename(source, destination);
        }
        #[cfg(target_os = "linux")]
        {
            let path = |p: &Path| {
                CString::new(p.as_os_str().as_encoded_bytes()).map_err(|_| {
                    std::io::Error::new(
                        std::io::ErrorKind::InvalidInput,
                        "rename path contains NUL",
                    )
                })
            };
            let source = path(source)?;
            let destination = path(destination)?;
            // Native atomic no-clobber rename handles both files and directories.
            // SAFETY: both C strings live for the syscall, with valid AT_FDCWD handles.
            let moved = unsafe {
                libc::syscall(
                    libc::SYS_renameat2,
                    libc::AT_FDCWD,
                    source.as_ptr(),
                    libc::AT_FDCWD,
                    destination.as_ptr(),
                    libc::RENAME_NOREPLACE,
                )
            };
            if moved == 0 {
                Ok(())
            } else {
                Err(std::io::Error::last_os_error())
            }
        }
        #[cfg(not(target_os = "linux"))]
        Err(std::io::Error::new(
            std::io::ErrorKind::Unsupported,
            "atomic no-replace rename unavailable",
        ))
    }
}

#[cfg(unix)]
pub(crate) fn sync_directory(path: &Path) -> Result<(), UniversalExecError> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| io_error(path, "sync directory", error))
}

#[cfg(windows)]
pub(crate) fn sync_directory(_path: &Path) -> Result<(), UniversalExecError> {
    // Windows has no documented POSIX fsync(directory) equivalent. File bytes are
    // flushed before publication and rename durability is owned by MoveFileExW with
    // MOVEFILE_WRITE_THROUGH in rename_path_durable.
    Ok(())
}

#[cfg(not(any(unix, windows)))]
pub(crate) fn sync_directory(path: &Path) -> Result<(), UniversalExecError> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| io_error(path, "sync directory", error))
}

pub(crate) fn io_error(path: &Path, operation: &str, error: std::io::Error) -> UniversalExecError {
    let code = if error.kind() == std::io::ErrorKind::StorageFull {
        UniversalExecErrorCode::WorkspaceCapacityExceeded
    } else {
        UniversalExecErrorCode::IoError
    };
    UniversalExecError::new(
        code,
        format!("cannot {operation} {}: {error}", path.display()),
        None,
        false,
    )
}

#[cfg(test)]
mod sha256_wire_contract_tests {
    use super::{parse_sha256_digest, sha256_bytes};

    #[test]
    fn published_sha256_wire_digest_matches_independent_known_vectors() {
        assert_eq!(
            sha256_bytes(b""),
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
        assert_eq!(
            sha256_bytes(b"abc"),
            "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn digest_parser_preserves_canonical_lowercase_wire_format() {
        let wire = sha256_bytes(b"abc");
        assert_eq!(
            parse_sha256_digest(&wire).map(hex::encode),
            Some(wire[7..].to_owned())
        );
        assert_eq!(parse_sha256_digest(&wire.to_uppercase()), None);
        assert_eq!(
            parse_sha256_digest(&format!("sha256:{}", wire[7..].to_ascii_uppercase())),
            None
        );
        assert_eq!(
            parse_sha256_digest(&format!("sha256:{}", "00".repeat(32))),
            Some([0; 32])
        );
        assert_eq!(
            parse_sha256_digest(&format!("sha256:{}", "ff".repeat(32))),
            Some([255; 32])
        );
        for body in [
            "a".repeat(63),
            "a".repeat(65),
            format!("{}g", "a".repeat(63)),
            format!("{}é", "a".repeat(62)),
        ] {
            assert_eq!(parse_sha256_digest(&format!("sha256:{body}")), None);
        }
    }
}

#[cfg(test)]
mod durable_publication_tests {
    use super::*;

    #[test]
    fn no_replace_preserves_first_publication_and_losing_source() {
        let dir = tempfile::tempdir().unwrap();
        let source = dir.path().join("stage");
        let destination = dir.path().join("sealed");
        fs::write(&source, b"loser").unwrap();
        fs::write(&destination, b"winner").unwrap();
        assert!(rename_path_durable(&source, &destination, false, "publish").is_err());
        assert_eq!(fs::read(&destination).unwrap(), b"winner");
        assert_eq!(fs::read(&source).unwrap(), b"loser");
    }
    #[test]
    fn no_replace_preserves_existing_directory_and_replace_remains_explicit() {
        let dir = tempfile::tempdir().unwrap();
        let source = dir.path().join("source");
        let destination = dir.path().join("destination");
        fs::create_dir(&source).unwrap();
        fs::create_dir(&destination).unwrap();
        fs::write(source.join("marker"), b"new").unwrap();
        assert!(rename_path_durable(&source, &destination, false, "publish").is_err());
        assert!(source.join("marker").is_file());
        assert!(destination.is_dir());
        assert!(!destination.join("marker").exists());
        let target = dir.path().join("mutable");
        write_bytes_atomic(&target, b"old").unwrap();
        write_bytes_atomic(&target, b"new").unwrap();
        assert_eq!(fs::read(target).unwrap(), b"new");
    }

    #[cfg(windows)]
    #[test]
    fn long_path_atomic_publication_preserves_no_replace_and_explicit_replace() {
        let root = tempfile::tempdir().unwrap();
        let mut parent = root.path().to_path_buf();
        while parent.as_os_str().encode_wide().count() < 270 {
            parent.push("nested-long-path-0123456789");
        }
        fs::create_dir_all(&parent).unwrap();
        let target = parent.join("cancel-requested.json");
        assert!(write_bytes_atomic_if_absent(&target, b"first").unwrap());
        assert!(!write_bytes_atomic_if_absent(&target, b"loser").unwrap());
        assert_eq!(fs::read(&target).unwrap(), b"first");
        write_bytes_atomic(&target, b"replacement").unwrap();
        assert_eq!(fs::read(&target).unwrap(), b"replacement");
        assert_eq!(fs::read_dir(&parent).unwrap().count(), 1);
    }

    #[test]
    fn exclusive_publication_has_one_winner_and_cleans_losing_stages() {
        use std::sync::{Arc, Barrier};
        let dir = tempfile::tempdir().unwrap();
        let target = dir.path().join("sealed");
        let barrier = Arc::new(Barrier::new(8));
        let results = std::thread::scope(|scope| {
            let handles: Vec<_> = (0u8..8)
                .map(|value| {
                    let barrier = barrier.clone();
                    let target = &target;
                    scope.spawn(move || {
                        barrier.wait();
                        (
                            value,
                            write_bytes_atomic_if_absent(target, &[value]).unwrap(),
                        )
                    })
                })
                .collect();
            handles
                .into_iter()
                .map(|h| h.join().unwrap())
                .collect::<Vec<_>>()
        });
        let winners: Vec<_> = results.iter().filter(|(_, won)| *won).collect();
        assert_eq!(winners.len(), 1);
        assert_eq!(fs::read(&target).unwrap(), [winners[0].0]);
        assert!(!write_bytes_atomic_if_absent(&target, &[winners[0].0]).unwrap());
        assert!(!write_bytes_atomic_if_absent(&target, b"different").unwrap());
        assert_eq!(fs::read(&target).unwrap(), [winners[0].0]);
        assert_eq!(fs::read_dir(dir.path()).unwrap().count(), 1);
    }
}

#[cfg(all(test, windows))]
mod windows_beneath_file_tests {
    use super::*;
    use std::io::Read;

    #[test]
    fn native_artifact_bytes_and_escape_rejection() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path().join("attempt");
        fs::create_dir(&root).unwrap();
        fs::create_dir(root.join("nested")).unwrap();
        fs::write(
            root.join("nested").join("stdout.log"),
            b"registered exact bytes",
        )
        .unwrap();
        fs::write(temp.path().join("foreign.log"), b"outside").unwrap();
        let handle = open_directory_nofollow(&root).unwrap();
        let mut file =
            open_regular_file_beneath(&handle, Path::new("nested/stdout.log"), true).unwrap();
        let mut bytes = vec![];
        file.read_to_end(&mut bytes).unwrap();
        assert_eq!(bytes, b"registered exact bytes");
        for path in [
            "../foreign.log",
            "nested",
            "nested/stdout.log:alternate",
            "",
            "nested/missing",
            "C:/Windows/win.ini",
        ] {
            assert!(
                open_regular_file_beneath(&handle, Path::new(path), true).is_err(),
                "accepted {path}"
            );
        }
        // A directory junction uses a real Windows reparse point without
        // needing symbolic-link creation privilege.
        let target = temp.path().join("outside");
        fs::create_dir(&target).unwrap();
        fs::write(target.join("stdout.log"), b"foreign").unwrap();
        let junction = root.join("junction");
        let output = std::process::Command::new("cmd.exe")
            .args(["/d", "/c", "mklink", "/J"])
            .arg(&junction)
            .arg(&target)
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "junction creation failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        assert!(open_directory_nofollow(&junction).is_err());
        assert!(
            open_regular_file_beneath(&handle, Path::new("junction/stdout.log"), true).is_err()
        );
        assert!(
            open_regular_file_beneath(&handle, Path::new("junction/stdout.log"), false).is_err()
        );
        fs::remove_dir(&junction).unwrap();
    }
}

#[cfg(all(test, unix))]
mod native_attempt_spawn_fence_tests {
    use super::*;
    use std::os::unix::fs::PermissionsExt;
    use std::sync::mpsc;
    use std::thread;
    use std::time::Duration;

    #[test]
    fn cancellation_marker_publication_waits_for_step_spawn_fence() {
        let dir =
            std::env::temp_dir().join(format!("ordivon-native-spawn-fence-{}", Uuid::now_v7()));
        fs::create_dir(&dir).unwrap();
        if unsafe { libc::geteuid() } == 0 {
            fs::set_permissions(&dir, fs::Permissions::from_mode(0o700)).unwrap();
        }
        if unsafe { libc::geteuid() } != 0 {
            // Unprivileged CI cannot manufacture an authentic UID0 PG
            // Attempt control directory. Reject the unowned substitute.
            assert!(lock_attempt_spawn_fence(&dir).is_err());
            fs::remove_dir_all(&dir).unwrap();
            return;
        }
        let running_spawn = lock_attempt_spawn_fence(&dir).unwrap();
        let lock_path = dir.join(".spawn-fence.lock");
        let competing = OpenOptions::new()
            .read(true)
            .write(true)
            .open(&lock_path)
            .unwrap();
        assert!(matches!(
            competing.try_lock(),
            Err(std::fs::TryLockError::WouldBlock)
        ));
        drop(competing);
        let (started_tx, started_rx) = mpsc::channel();
        let (committed_tx, committed_rx) = mpsc::channel();
        let child_dir = dir.clone();
        let cancel = thread::spawn(move || {
            started_tx.send(()).unwrap();
            let _cancel_fence = lock_attempt_spawn_fence(&child_dir).unwrap();
            fs::write(child_dir.join("cancel-requested.json"), b"{}").unwrap();
            committed_tx.send(()).unwrap();
        });
        started_rx.recv_timeout(Duration::from_secs(2)).unwrap();
        assert!(matches!(
            committed_rx.recv_timeout(Duration::from_millis(70)),
            Err(mpsc::RecvTimeoutError::Timeout)
        ));
        assert!(!dir.join("cancel-requested.json").exists());
        drop(running_spawn);
        committed_rx.recv_timeout(Duration::from_secs(2)).unwrap();
        cancel.join().unwrap();
        // A newly started Runner must observe the marker while holding
        // the SAME root-controlled lock; it cannot start another step.
        let _next_spawn_fence = lock_attempt_spawn_fence(&dir).unwrap();
        assert!(dir.join("cancel-requested.json").is_file());
        drop(_next_spawn_fence);
        fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn attempt_spawn_fence_rejects_world_writable_or_symlinked_inodes() {
        let dir =
            std::env::temp_dir().join(format!("ordivon-native-spawn-inode-{}", Uuid::now_v7()));
        fs::create_dir(&dir).unwrap();
        if unsafe { libc::geteuid() } == 0 {
            fs::set_permissions(&dir, fs::Permissions::from_mode(0o700)).unwrap();
        }
        if unsafe { libc::geteuid() } != 0 {
            assert!(lock_attempt_spawn_fence(&dir).is_err());
        } else {
            let owned = lock_attempt_spawn_fence(&dir).unwrap();
            drop(owned);
            fs::set_permissions(&dir, fs::Permissions::from_mode(0o755)).unwrap();
            assert!(lock_attempt_spawn_fence(&dir).is_err());
            fs::set_permissions(&dir, fs::Permissions::from_mode(0o700)).unwrap();
            let path = dir.join(".spawn-fence.lock");
            fs::set_permissions(&path, fs::Permissions::from_mode(0o666)).unwrap();
            assert!(lock_attempt_spawn_fence(&dir).is_err());
            fs::remove_file(&path).unwrap();
            let innocent = dir.join("ordinary-file");
            fs::write(&innocent, b"synthetic").unwrap();
            std::os::unix::fs::symlink(&innocent, &path).unwrap();
            assert!(lock_attempt_spawn_fence(&dir).is_err());
        }
        fs::remove_dir_all(&dir).unwrap();
    }
}
