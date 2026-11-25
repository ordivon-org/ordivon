//! Scoped Workspace input commitment: explicit read set, Git HEAD and native bytes.
//! This is intentionally distinct from the complete source-state retirement CAS.

use std::{fs, path::Path};

use super::{
    canonical_directory, invalid, io_error, workspace_head_revision_at, UniversalExecError,
};

/// Domain-separated source commitment over an explicit read set. Git HEAD is
/// always bound; unrelated mutable paths are excluded rather than disabling
/// source validation. Scoped source trees reject filesystem aliases.
pub(crate) fn workspace_source_readset_digest_at(
    workspace: &Path,
    paths: &[String],
) -> Result<String, UniversalExecError> {
    use sha2::{Digest, Sha256};
    use std::io::Read;
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let mut hash = Sha256::new();
    hash.update(b"runtime-workspace-readset-v1\0");
    hash.update(workspace_head_revision_at(&workspace)?.as_bytes());
    fn walk(root: &Path, path: &Path, hash: &mut Sha256) -> Result<(), UniversalExecError> {
        let relative = path
            .strip_prefix(root)
            .map_err(|_| invalid("source path escaped Workspace", "readPaths"))?;
        if relative.components().any(|v| {
            matches!(
                v,
                std::path::Component::ParentDir
                    | std::path::Component::RootDir
                    | std::path::Component::Prefix(_)
            )
        }) {
            return Err(invalid("invalid scoped source path", "readPaths"));
        }
        if relative.components().any(|v| v.as_os_str() == ".git") {
            return Ok(());
        }
        let mut ancestor = root.to_path_buf();
        for component in relative.components() {
            ancestor.push(component.as_os_str());
            if let Ok(meta) = fs::symlink_metadata(&ancestor) {
                if meta.file_type().is_symlink() {
                    return Err(invalid(
                        "scoped source path traversed an alias",
                        "readPaths",
                    ));
                }
            }
        }
        hash.update(relative.as_os_str().as_encoded_bytes());
        hash.update([0]);
        let meta = match fs::symlink_metadata(path) {
            Ok(v) => v,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
                hash.update(b"absent");
                return Ok(());
            }
            Err(e) => return Err(io_error(path, "inspect scoped source", e)),
        };
        if meta.file_type().is_symlink() {
            return Err(invalid(
                "scoped sources cannot traverse symlinks",
                "readPaths",
            ));
        }
        if meta.is_file() {
            #[cfg(unix)]
            {
                use std::os::unix::fs::MetadataExt;
                if meta.nlink() > 1 {
                    return Err(invalid(
                        "scoped sources cannot contain hardlinked files",
                        "readPaths",
                    ));
                }
            }
            hash.update(b"file");
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                hash.update(meta.permissions().mode().to_le_bytes());
            }
            hash.update(meta.len().to_le_bytes());
            let mut file =
                fs::File::open(path).map_err(|e| io_error(path, "open scoped source", e))?;
            #[cfg(windows)]
            {
                use std::os::windows::io::AsRawHandle;
                use windows_sys::Win32::Storage::FileSystem::{
                    GetFileInformationByHandle, BY_HANDLE_FILE_INFORMATION,
                };
                // Rust's Windows MetadataExt::number_of_links is unstable on
                // the pinned stable toolchain. Reuse the already-present
                // Win32 FileSystem binding and inspect the *opened* handle,
                // not the original path, to preserve the no-hardlinks guard.
                // SAFETY: BY_HANDLE_FILE_INFORMATION contains integer/FILETIME
                // fields, so an all-zero initial value is valid.
                let mut info: BY_HANDLE_FILE_INFORMATION = unsafe { std::mem::zeroed() };
                // SAFETY: file owns a live Windows file HANDLE; Win32 fills
                // the output POD on success. A failed observation is fatal.
                if unsafe { GetFileInformationByHandle(file.as_raw_handle() as _, &mut info) } == 0
                {
                    return Err(io_error(
                        path,
                        "inspect scoped source links",
                        std::io::Error::last_os_error(),
                    ));
                }
                if info.nNumberOfLinks != 1 {
                    return Err(invalid(
                        "scoped sources cannot contain hardlinked files",
                        "readPaths",
                    ));
                }
            }
            let mut buffer = [0u8; 65536];
            loop {
                let size = file
                    .read(&mut buffer)
                    .map_err(|e| io_error(path, "read scoped source", e))?;
                if size == 0 {
                    break;
                }
                hash.update(&buffer[..size]);
            }
        } else if meta.is_dir() {
            hash.update(b"directory");
            let mut entries = fs::read_dir(path)
                .map_err(|e| io_error(path, "list scoped source", e))?
                .collect::<Result<Vec<_>, _>>()
                .map_err(|e| io_error(path, "list scoped source", e))?;
            entries.sort_by_key(|v| v.file_name());
            for entry in entries {
                walk(root, &entry.path(), hash)?;
            }
        } else {
            return Err(invalid("unsupported file in scoped read set", "readPaths"));
        }
        Ok(())
    }
    let mut paths = paths.to_vec();
    paths.sort();
    paths.dedup();
    for path in paths {
        if path.is_empty()
            || Path::new(&path).is_absolute()
            || Path::new(&path).components().any(|v| {
                matches!(
                    v,
                    std::path::Component::ParentDir
                        | std::path::Component::RootDir
                        | std::path::Component::Prefix(_)
                )
            })
        {
            return Err(invalid("invalid scoped read path", "readPaths"));
        }
        walk(&workspace, &workspace.join(path), &mut hash)?;
    }
    Ok(format!("sha256:{}", hex::encode(hash.finalize())))
}

#[cfg(test)]
mod scoped_source_tests {
    use super::super::workspace_git_command;
    use super::*;
    #[test]
    fn scoped_commitment_tracks_its_read_set_and_rejects_aliases() {
        let root = std::env::temp_dir().join(format!("runtime-readset-{}", uuid::Uuid::now_v7()));
        fs::create_dir_all(root.join("left")).unwrap();
        fs::create_dir(root.join("right")).unwrap();
        for args in [
            vec!["init"],
            vec![
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "--allow-empty",
                "-m",
                "source",
            ],
        ] {
            assert!(workspace_git_command()
                .arg("-C")
                .arg(&root)
                .args(args)
                .output()
                .unwrap()
                .status
                .success());
        }
        fs::write(root.join("left/input"), b"before").unwrap();
        let paths = vec!["left".to_string()];
        let before = workspace_source_readset_digest_at(&root, &paths).unwrap();
        fs::write(root.join("right/output"), b"independent").unwrap();
        assert_eq!(
            before,
            workspace_source_readset_digest_at(&root, &paths).unwrap()
        );
        fs::write(root.join("left/input"), b"changed").unwrap();
        assert_ne!(
            before,
            workspace_source_readset_digest_at(&root, &paths).unwrap()
        );
        #[cfg(unix)]
        {
            std::os::unix::fs::symlink(root.join("left"), root.join("alias")).unwrap();
            assert!(workspace_source_readset_digest_at(&root, &["alias/input".into()]).is_err());
        }
        #[cfg(windows)]
        {
            // Win32 GetFileInformationByHandle must keep the Unix nlink()
            // boundary: a same-byte hardlinked path is not safe scoped input.
            fs::hard_link(root.join("left/input"), root.join("left/hardlink")).unwrap();
            assert!(workspace_source_readset_digest_at(&root, &["left".into()]).is_err());
            fs::remove_file(root.join("left/hardlink")).unwrap();
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn scoped_commitment_is_set_order_independent_and_tracks_absent_inputs() {
        let root = tempfile::tempdir().unwrap();
        for args in [
            vec!["init"],
            vec![
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "--allow-empty",
                "-m",
                "source",
            ],
        ] {
            assert!(workspace_git_command()
                .arg("-C")
                .arg(root.path())
                .args(args)
                .output()
                .unwrap()
                .status
                .success());
        }
        fs::write(root.path().join("left"), b"same").unwrap();
        let canonical = vec!["left".to_string(), "missing".to_string()];
        let reordered = vec![
            "missing".to_string(),
            "left".to_string(),
            "left".to_string(),
        ];
        let before = workspace_source_readset_digest_at(root.path(), &canonical).unwrap();
        assert_eq!(
            before,
            workspace_source_readset_digest_at(root.path(), &reordered).unwrap()
        );
        fs::write(root.path().join("missing"), b"present").unwrap();
        assert_ne!(
            before,
            workspace_source_readset_digest_at(root.path(), &canonical).unwrap()
        );
        #[cfg(unix)]
        {
            fs::hard_link(root.path().join("left"), root.path().join("alias")).unwrap();
            assert!(workspace_source_readset_digest_at(root.path(), &canonical).is_err());
        }
    }
}
