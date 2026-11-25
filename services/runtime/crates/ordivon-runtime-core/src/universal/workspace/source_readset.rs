//! Scoped Workspace input commitment: explicit read set, Git HEAD and native bytes.
//! This is intentionally distinct from the complete source-state retirement CAS.

use std::{fs, path::Path};

use super::{
    canonical_directory, invalid, io_error, same_source_metadata, workspace_head_revision_at,
    UniversalExecError,
};

// Hold the original Linux Workspace directory across the traversal. Reuse
// the existing native beneath-root/no-symlink resolver, not another path policy.
struct ReadsetRoot<'a> {
    path: &'a Path,
    #[cfg(unix)]
    handle: fs::File,
}

impl ReadsetRoot<'_> {
    fn open_file(&self, relative: &Path, path: &Path) -> Result<fs::File, UniversalExecError> {
        #[cfg(unix)]
        let file = super::super::fsutil::open_regular_file_beneath(&self.handle, relative, true);
        #[cfg(windows)]
        let file = {
            let _ = relative;
            fs::File::open(path)
        };
        file.map_err(|error| io_error(path, "open scoped source", error))
    }
}

fn require_stable_file(
    path: &Path,
    expected: &fs::Metadata,
    observed: &fs::Metadata,
) -> Result<(), UniversalExecError> {
    #[cfg(unix)]
    let single_link = {
        use std::os::unix::fs::MetadataExt;
        observed.nlink() == 1
    };
    #[cfg(windows)]
    let single_link = true; // existing opened-handle Win32 check below
    if !observed.is_file() || !single_link || !same_source_metadata(expected, observed) {
        return Err(UniversalExecError::new(
            super::UniversalExecErrorCode::WorkspaceMutationIncomplete,
            format!(
                "scoped source changed during commitment: {}",
                path.display()
            ),
            Some("readPaths"),
            true,
        ));
    }
    Ok(())
}

/// Domain-separated source commitment over an explicit read set. Git HEAD is
/// always bound; unrelated mutable paths are excluded rather than disabling
/// source validation. Scoped source trees reject filesystem aliases.
pub(crate) fn workspace_source_readset_digest_at(
    workspace: &Path,
    paths: &[String],
) -> Result<String, UniversalExecError> {
    use sha2::{Digest, Sha256};
    let mut hash = Sha256::new();
    observe_scoped_paths(workspace, paths, |bytes| hash.update(bytes))?;
    Ok(format!("sha256:{}", hex::encode(hash.finalize())))
}

/// Validate the same native tree observation without manufacturing an unused
/// digest. This deliberately still reads every file: unreadable content, alias
/// rejection and observed mutation must not become success merely because a
/// caller does not need a commitment.
#[cfg(all(unix, any(feature = "postgres-registry-admission", test)))]
pub(crate) fn validate_scoped_write_paths_at(
    workspace: &Path,
    paths: &[String],
) -> Result<(), UniversalExecError> {
    observe_scoped_paths(workspace, paths, |_| {})
}

fn observe_scoped_paths(
    workspace: &Path,
    paths: &[String],
    mut emit: impl FnMut(&[u8]),
) -> Result<(), UniversalExecError> {
    use std::io::Read;
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let root = ReadsetRoot {
        path: &workspace,
        #[cfg(unix)]
        handle: super::super::fsutil::open_directory_nofollow(&workspace)
            .map_err(|error| io_error(&workspace, "open scoped Workspace root", error))?,
    };
    emit(b"runtime-workspace-readset-v1\0");
    emit(workspace_head_revision_at(&workspace)?.as_bytes());
    fn walk(
        root: &ReadsetRoot<'_>,
        path: &Path,
        emit: &mut impl FnMut(&[u8]),
    ) -> Result<(), UniversalExecError> {
        let relative = path
            .strip_prefix(root.path)
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
        let mut ancestor = root.path.to_path_buf();
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
        emit(relative.as_os_str().as_encoded_bytes());
        emit(&[0]);
        let meta = match fs::symlink_metadata(path) {
            Ok(v) => v,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
                emit(b"absent");
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
            emit(b"file");
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                emit(&meta.permissions().mode().to_le_bytes());
            }
            emit(&meta.len().to_le_bytes());
            let mut file = root.open_file(relative, path)?;
            let opened = file
                .metadata()
                .map_err(|error| io_error(path, "inspect opened scoped source", error))?;
            require_stable_file(path, &meta, &opened)?;
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
            let mut bytes_read = 0u64;
            let mut buffer = [0u8; 65536];
            loop {
                let size = file
                    .read(&mut buffer)
                    .map_err(|e| io_error(path, "read scoped source", e))?;
                if size == 0 {
                    break;
                }
                bytes_read = bytes_read
                    .checked_add(size as u64)
                    .ok_or_else(|| invalid("scoped source length overflow", "readPaths"))?;
                emit(&buffer[..size]);
            }
            let after_handle = file
                .metadata()
                .map_err(|error| io_error(path, "reinspect opened scoped source", error))?;
            let after_path = fs::symlink_metadata(path)
                .map_err(|error| io_error(path, "reinspect scoped source path", error))?;
            require_stable_file(path, &meta, &after_handle)?;
            require_stable_file(path, &meta, &after_path)?;
            if bytes_read != meta.len() {
                return Err(invalid(
                    "scoped source length changed during commitment",
                    "readPaths",
                ));
            }
        } else if meta.is_dir() {
            emit(b"directory");
            let mut entries = fs::read_dir(path)
                .map_err(|e| io_error(path, "list scoped source", e))?
                .collect::<Result<Vec<_>, _>>()
                .map_err(|e| io_error(path, "list scoped source", e))?;
            entries.sort_by_key(|v| v.file_name());
            for entry in entries {
                walk(root, &entry.path(), emit)?;
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
        walk(&root, &workspace.join(path), &mut emit)?;
    }
    Ok(())
}

#[cfg(test)]
mod scoped_source_tests {
    use super::super::workspace_git_command;
    use super::*;
    #[cfg(unix)]
    #[test]
    fn validation_preserves_commitment_observation_acceptance_and_error_codes() {
        let temp = tempfile::tempdir().unwrap();
        let root = temp.path();
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
                .arg(root)
                .args(args)
                .output()
                .unwrap()
                .status
                .success());
        }
        fs::create_dir(root.join("out")).unwrap();
        fs::write(root.join("out/value"), [0, 255, 3]).unwrap();
        let check = |paths: &[String], expected: bool| {
            let digest = workspace_source_readset_digest_at(root, paths);
            let validation = validate_scoped_write_paths_at(root, paths);
            assert_eq!(digest.is_ok(), expected, "{paths:?}");
            assert_eq!(validation.is_ok(), expected, "{paths:?}");
            if let (Err(a), Err(b)) = (digest, validation) {
                assert_eq!(a.code.as_str(), b.code.as_str(), "{paths:?}");
            }
        };
        check(&["out".into()], true);
        check(&["out".into(), "out".into()], true);
        check(&["out".into(), "missing".into()], true);
        check(&["../escape".into()], false);
        std::os::unix::fs::symlink("out", root.join("alias")).unwrap();
        check(&["alias/value".into()], false);
        fs::hard_link(root.join("out/value"), root.join("out/hardlink")).unwrap();
        check(&["out".into()], false);
        fs::remove_file(root.join("out/hardlink")).unwrap();
        let fifo = root.join("out/pipe");
        use std::os::unix::ffi::OsStrExt;
        let name = std::ffi::CString::new(fifo.as_os_str().as_bytes()).unwrap();
        // SAFETY: name is a live NUL-terminated string in a private fixture.
        assert_eq!(unsafe { libc::mkfifo(name.as_ptr(), 0o600) }, 0);
        check(&["out".into()], false);
        fs::remove_file(fifo).unwrap();
        check(&["out".into()], true);
    }

    #[cfg(unix)]
    #[test]
    fn scoped_open_rejects_replaced_file_and_alias_ancestor() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("input");
        fs::write(&path, b"same").unwrap();
        let before = fs::symlink_metadata(&path).unwrap();
        let root = ReadsetRoot {
            path: temp.path(),
            handle: super::super::super::fsutil::open_directory_nofollow(temp.path()).unwrap(),
        };
        fs::rename(&path, temp.path().join("original")).unwrap();
        fs::write(&path, b"same").unwrap();
        let replacement = root.open_file(Path::new("input"), &path).unwrap();
        assert!(require_stable_file(&path, &before, &replacement.metadata().unwrap()).is_err());
        fs::create_dir(temp.path().join("real")).unwrap();
        fs::write(temp.path().join("real/value"), b"same").unwrap();
        std::os::unix::fs::symlink("real", temp.path().join("alias")).unwrap();
        assert!(root
            .open_file(Path::new("alias/value"), &temp.path().join("alias/value"))
            .is_err());
    }

    #[cfg(unix)]
    #[test]
    fn scoped_observation_rejects_post_open_mutation_and_hardlink() {
        let temp = tempfile::tempdir().unwrap();
        let path = temp.path().join("input");
        fs::write(&path, b"same").unwrap();
        let opened = fs::File::open(&path).unwrap();
        let before = opened.metadata().unwrap();
        require_stable_file(&path, &before, &opened.metadata().unwrap()).unwrap();
        fs::write(&path, b"changed length").unwrap();
        assert!(require_stable_file(&path, &before, &opened.metadata().unwrap()).is_err());
        let before = opened.metadata().unwrap();
        fs::hard_link(&path, temp.path().join("alias")).unwrap();
        assert!(require_stable_file(&path, &before, &opened.metadata().unwrap()).is_err());
    }

    // The v1 commitment is a wire contract, not a file-layout contract.
    // Assemble its expected bytes independently of the traversal and guards.
    #[cfg(unix)]
    #[test]
    fn stable_scoped_tree_preserves_v1_commitment_wire_bytes() {
        use std::os::unix::fs::PermissionsExt;
        let temp = tempfile::tempdir().unwrap();
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
                .arg(temp.path())
                .args(args)
                .output()
                .unwrap()
                .status
                .success());
        }
        fs::create_dir(temp.path().join("input")).unwrap();
        let a = temp.path().join("input/a");
        let b = temp.path().join("input/b");
        fs::write(&b, [0u8, 255, 1]).unwrap();
        fs::write(&a, b"hello").unwrap();
        fs::set_permissions(&a, fs::Permissions::from_mode(0o644)).unwrap();
        fs::set_permissions(&b, fs::Permissions::from_mode(0o755)).unwrap();
        let head = workspace_git_command()
            .arg("-C")
            .arg(temp.path())
            .args(["rev-parse", "HEAD"])
            .output()
            .unwrap();
        assert!(head.status.success());
        let mut expected = b"runtime-workspace-readset-v1\0".to_vec();
        expected.extend_from_slice(String::from_utf8(head.stdout).unwrap().trim().as_bytes());
        expected.extend_from_slice(b"input\0directoryinput/a\0file");
        expected.extend_from_slice(&0o100644_u32.to_le_bytes());
        expected.extend_from_slice(&5_u64.to_le_bytes());
        expected.extend_from_slice(b"helloinput/b\0file");
        expected.extend_from_slice(&0o100755_u32.to_le_bytes());
        expected.extend_from_slice(&3_u64.to_le_bytes());
        expected.extend_from_slice(&[0u8, 255, 1]);
        expected.extend_from_slice(b"missing\0absent");
        assert_eq!(
            workspace_source_readset_digest_at(temp.path(), &["missing".into(), "input".into()])
                .unwrap(),
            super::super::super::fsutil::sha256_bytes(&expected),
        );
    }

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
