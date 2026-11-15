pub(crate) fn workspace_head_and_dirty_at(
    workspace: &Path,
) -> Result<(String, WorkspaceHeadMode, bool), UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let output = Command::new("git")
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(&workspace)
        .args([
            "status",
            "--porcelain=v2",
            "--branch",
            "-z",
            "--untracked-files=normal",
            "--ignore-submodules=none",
        ])
        .output()
        .map_err(|error| tool_unavailable("git status", error))?;
    if !output.status.success() {
        return Err(tool_failed("git status", &output.stderr));
    }
    let mut head_revision = None;
    let mut head_mode = None;
    let mut dirty = false;
    for raw in output
        .stdout
        .split(|byte| *byte == 0)
        .filter(|raw| !raw.is_empty())
    {
        if let Some(value) = raw.strip_prefix(b"# branch.oid ") {
            let value = String::from_utf8(value.to_vec()).map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("Git branch OID is not UTF-8: {error}"),
                    None,
                    false,
                )
            })?;
            head_revision = Some(value);
        } else if let Some(value) = raw.strip_prefix(b"# branch.head ") {
            head_mode = Some(match value {
                b"(detached)" => WorkspaceHeadMode::Detached,
                b"" => return Err(UniversalExecError::new(
                    UniversalExecErrorCode::MetadataCorrupt,
                    "git status returned empty branch.head",
                    Some("workspaceId"),
                    false,
                )),
                _ => WorkspaceHeadMode::Branch,
            });
        } else if !raw.starts_with(b"# ") {
            dirty = true;
        }
    }
    let head_revision = head_revision.ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::RevisionNotFound,
            "git status omitted branch.oid",
            Some("workspaceId"),
            false,
        )
    })?;
    if head_revision.len() != 40 && head_revision.len() != 64 {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionNotFound,
            "workspace HEAD did not resolve to a commit",
            Some("workspaceId"),
            false,
        ));
    }
    let head_mode = head_mode.ok_or_else(|| UniversalExecError::new(
        UniversalExecErrorCode::MetadataCorrupt,
        "git status omitted branch.head",
        Some("workspaceId"),
        false,
    ))?;
    Ok((head_revision, head_mode, dirty))
}

pub(crate) fn workspace_head_revision_at(workspace: &Path) -> Result<String, UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let revision = git_output(&workspace, ["rev-parse", "HEAD"])?
        .trim()
        .to_string();
    if revision.len() != 40 && revision.len() != 64 {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionNotFound,
            "workspace HEAD did not resolve to a commit",
            Some("workspaceId"),
            false,
        ));
    }
    Ok(revision)
}

pub fn workspace_source_state_digest(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<String, UniversalExecError> {
    let record = load_workspace_record(config, workspace_id)?;
    workspace_source_state_digest_at(Path::new(&record.workspace_path))
}

pub(crate) fn workspace_git_common_dir_at(workspace: &Path) -> Result<PathBuf, UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let common_dir = git_output(
        &workspace,
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
    )?;
    canonical_directory(Path::new(common_dir.trim()), "workspaceGitCommonDir")
}

pub(crate) fn workspace_source_state_digest_at(
    workspace: &Path,
) -> Result<String, UniversalExecError> {
    workspace_source_state_digest_with_unborn_policy(workspace, false)
}

fn workspace_source_state_digest_with_unborn_policy(
    workspace: &Path,
    allow_unborn: bool,
) -> Result<String, UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    // Only nested Git repositories may have no commit yet. The outer Runtime
    // Workspace still requires a real committed HEAD.
    let head_revision = match workspace_head_revision_at(&workspace) {
        Ok(commit) => commit,
        Err(error) if allow_unborn && error.code == UniversalExecErrorCode::ToolFailed => {
            let symbolic = git_output(&workspace, ["symbolic-ref", "-q", "HEAD"])?;
            let branch = symbolic.trim();
            if !branch.starts_with("refs/heads/") {
                return Err(error);
            }
            let check = Command::new("git")
                .arg("-C")
                .arg(&workspace)
                .args(["show-ref", "--verify", "--quiet", branch])
                .output()
                .map_err(|problem| tool_unavailable("git show-ref", problem))?;
            if check.status.code() != Some(1) {
                return Err(error);
            }
            format!("unborn-git-head:{branch}")
        }
        Err(error) => return Err(error),
    };
    let staged_index = git_output_bytes(&workspace, ["ls-files", "--stage", "-z"])?;
    let index_flags = git_output_bytes(&workspace, ["ls-files", "-v", "-z"])?;
    let index_digest = sha256_bytes(
        format!(
            "workspace-index-v1\0{}\0{}",
            sha256_bytes(&staged_index),
            sha256_bytes(&index_flags)
        )
        .as_bytes(),
    );
    let tracked_paths = parse_tracked_index_paths(&staged_index)?;
    let mut tracked = Vec::with_capacity(tracked_paths.len());
    for (relative, index_mode) in tracked_paths {
        tracked.push(workspace_source_entry(
            &workspace,
            &relative,
            Some(&index_mode),
        )?);
    }

    let untracked_raw = git_output_bytes(
        &workspace,
        ["ls-files", "--others", "--exclude-standard", "-z"],
    )?;
    let mut untracked_paths = parse_nul_paths(&untracked_raw, "untracked Git path")?;
    untracked_paths.sort();
    let mut untracked = Vec::with_capacity(untracked_paths.len());
    for relative in untracked_paths {
        untracked.push(workspace_source_entry(&workspace, &relative, None)?);
    }

    let state = WorkspaceSourceState {
        schema_version: 2,
        head_revision,
        index_digest,
        tracked,
        untracked,
    };
    let bytes = serde_json::to_vec(&state).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            format!("cannot serialize Workspace source state: {error}"),
            None,
            false,
        )
    })?;
    Ok(sha256_bytes(&bytes))
}

fn parse_tracked_index_paths(
    staged_index: &[u8],
) -> Result<BTreeMap<String, String>, UniversalExecError> {
    let mut paths = BTreeMap::new();
    for raw in staged_index
        .split(|byte| *byte == 0)
        .filter(|raw| !raw.is_empty())
    {
        let record = String::from_utf8(raw.to_vec()).map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::ArtifactNotUtf8,
                format!("tracked Git index record is not UTF-8: {error}"),
                None,
                false,
            )
        })?;
        let (metadata, relative) = record.split_once('\t').ok_or_else(|| {
            UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "tracked Git index record has no path separator",
                None,
                false,
            )
        })?;
        let index_mode = metadata.split_whitespace().next().ok_or_else(|| {
            UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "tracked Git index record has no mode",
                None,
                false,
            )
        })?;
        validate_relative_path(relative, "trackedPath")?;
        paths.insert(relative.to_string(), index_mode.to_string());
    }
    Ok(paths)
}

fn parse_nul_paths(bytes: &[u8], label: &str) -> Result<Vec<String>, UniversalExecError> {
    bytes
        .split(|byte| *byte == 0)
        .filter(|raw| !raw.is_empty())
        .map(|raw| {
            String::from_utf8(raw.to_vec()).map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("{label} is not UTF-8: {error}"),
                    None,
                    false,
                )
            })
        })
        .collect()
}

fn workspace_source_entry(
    workspace: &Path,
    relative: &str,
    index_mode: Option<&str>,
) -> Result<WorkspaceSourceEntry, UniversalExecError> {
    let relative_path = validate_relative_path(relative, "sourcePath")?;
    let path = workspace.join(&relative_path);
    let before = match fs::symlink_metadata(&path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return Ok(WorkspaceSourceEntry {
                path: relative.to_string(),
                kind: if index_mode == Some("160000") {
                    "gitlink-uninitialized".to_string()
                } else {
                    "missing".to_string()
                },
                mode: 0,
                byte_length: 0,
                digest: sha256_bytes(b"missing"),
            });
        }
        Err(error) => return Err(io_error(&path, "inspect source state", error)),
    };
    let mode = source_entry_mode(&before, index_mode);
    let (kind, byte_length, digest) = if before.file_type().is_symlink() {
        let target =
            fs::read_link(&path).map_err(|error| io_error(&path, "read source symlink", error))?;
        let bytes = symlink_target_bytes(&target);
        (
            "symlink".to_string(),
            bytes.len() as u64,
            sha256_bytes(&bytes),
        )
    } else if before.is_file() {
        ("file".to_string(), before.len(), sha256_file(&path)?)
    } else if before.is_dir() {
        if is_git_worktree(&path)? {
            (
                "git-worktree".to_string(),
                0,
                workspace_source_state_digest_with_unborn_policy(&path, true)?,
            )
        } else if index_mode == Some("160000") {
            (
                "gitlink-uninitialized".to_string(),
                0,
                sha256_bytes(b"gitlink-uninitialized"),
            )
        } else {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspacePathDenied,
                format!("source path is not a regular file, symlink, or Git worktree: {relative}"),
                Some("workspaceId"),
                false,
            ));
        }
    } else {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspacePathDenied,
            format!("source path is not a regular file, symlink, or Git worktree: {relative}"),
            Some("workspaceId"),
            false,
        ));
    };
    let after = fs::symlink_metadata(&path)
        .map_err(|error| io_error(&path, "reinspect source state", error))?;
    if !same_source_metadata(&before, &after) {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceMutationIncomplete,
            format!("source path changed while its commitment was computed: {relative}"),
            Some("workspaceId"),
            true,
        ));
    }
    #[cfg(windows)]
    if !windows_source_semantics_unchanged(&path, &kind, &digest)? {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceMutationIncomplete,
            format!("source path semantics changed while its commitment was computed: {relative}"),
            Some("workspaceId"),
            true,
        ));
    }
    Ok(WorkspaceSourceEntry {
        path: relative.to_string(),
        kind,
        mode,
        byte_length,
        digest,
    })
}

#[cfg(unix)]
fn source_entry_mode(metadata: &fs::Metadata, _index_mode: Option<&str>) -> u32 {
    metadata.permissions().mode() & 0o7777
}

#[cfg(windows)]
fn source_entry_mode(_metadata: &fs::Metadata, index_mode: Option<&str>) -> u32 {
    index_mode
        .and_then(|mode| u32::from_str_radix(mode, 8).ok())
        .map(|mode| mode & 0o7777)
        .unwrap_or(0)
}

#[cfg(unix)]
fn symlink_target_bytes(target: &Path) -> Vec<u8> {
    target.as_os_str().as_bytes().to_vec()
}

#[cfg(windows)]
fn symlink_target_bytes(target: &Path) -> Vec<u8> {
    target
        .as_os_str()
        .encode_wide()
        .flat_map(u16::to_le_bytes)
        .collect()
}

fn is_git_worktree(path: &Path) -> Result<bool, UniversalExecError> {
    let output = Command::new("git")
        .arg("-C")
        .arg(path)
        .args(["rev-parse", "--is-inside-work-tree", "--show-prefix"])
        .output()
        .map_err(|error| tool_unavailable("git rev-parse worktree", error))?;
    // A plain directory inside its parent repository also reports true.
    // The empty prefix proves this directory is the Git worktree root.
    Ok(output.status.success() && output.stdout == b"true\n\n")
}

#[cfg(unix)]
fn same_source_metadata(left: &fs::Metadata, right: &fs::Metadata) -> bool {
    left.dev() == right.dev()
        && left.ino() == right.ino()
        && left.mode() == right.mode()
        && left.size() == right.size()
        && left.mtime() == right.mtime()
        && left.mtime_nsec() == right.mtime_nsec()
        && left.ctime() == right.ctime()
        && left.ctime_nsec() == right.ctime_nsec()
}

#[cfg(windows)]
fn same_source_metadata(left: &fs::Metadata, right: &fs::Metadata) -> bool {
    left.file_size() == right.file_size()
        && left.creation_time() == right.creation_time()
        && left.last_write_time() == right.last_write_time()
        && left.file_attributes() == right.file_attributes()
}

#[cfg(windows)]
fn windows_source_semantics_unchanged(
    path: &Path,
    kind: &str,
    expected_digest: &str,
) -> Result<bool, UniversalExecError> {
    let observed = match kind {
        "file" => sha256_file(path)?,
        "symlink" => {
            let target = fs::read_link(path)
                .map_err(|error| io_error(path, "reread source symlink", error))?;
            sha256_bytes(&symlink_target_bytes(&target))
        }
        "git-worktree" => workspace_source_state_digest_with_unborn_policy(path, true)?,
        "gitlink-uninitialized" => {
            if is_git_worktree(path)? {
                return Ok(false);
            }
            sha256_bytes(b"gitlink-uninitialized")
        }
        _ => return Ok(false),
    };
    Ok(observed == expected_digest)
}

#[cfg(test)]
mod gitlink_worktree_root_tests {
    use super::*;

    #[test]
    fn nested_gitlink_directory_does_not_inherit_parent_worktree_identity() {
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "ordivon-gitlink-root-{}-{unique}",
            std::process::id()
        ));
        fs::create_dir_all(&root).expect("create root");
        let run = |cwd: &Path, args: &[&str]| {
            let output = Command::new("git")
                .arg("-C")
                .arg(cwd)
                .args(args)
                .output()
                .expect("run git");
            assert!(
                output.status.success(),
                "git failed: {}",
                String::from_utf8_lossy(&output.stderr)
            );
            output
        };
        run(&root, &["init", "--quiet"]);
        run(&root, &["config", "user.name", "Ordivon Test"]);
        run(&root, &["config", "user.email", "ordivon@example.invalid"]);
        fs::write(root.join("README.md"), "baseline\n").expect("write baseline");
        run(&root, &["add", "README.md"]);
        run(&root, &["commit", "--quiet", "-m", "baseline"]);

        let nested = root.join("module");
        fs::create_dir_all(&nested).expect("create gitlink directory");
        run(
            &root,
            &[
                "update-index",
                "--add",
                "--cacheinfo",
                "160000,1111111111111111111111111111111111111111,module",
            ],
        );

        let inherited = run(&nested, &["rev-parse", "--is-inside-work-tree"]);
        assert_eq!(inherited.stdout, b"true\n");
        let inherited_result = is_git_worktree(&nested).expect("classify nested directory");

        run(&nested, &["init", "--quiet"]);
        let nested_repo_result = is_git_worktree(&nested).expect("classify nested repository");
        let root_result = is_git_worktree(&root).expect("classify root repository");
        fs::remove_dir_all(&root).expect("cleanup fixture");

        assert!(
            !inherited_result,
            "a directory inherited from its parent worktree is not its own worktree root"
        );
        assert!(nested_repo_result);
        assert!(root_result);
    }

    #[test]
    fn untracked_nested_git_worktree_is_digestible() {
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "ordivon-untracked-nested-root-{}-{unique}",
            std::process::id()
        ));
        fs::create_dir_all(&root).expect("create root");
        let run = |cwd: &Path, args: &[&str]| {
            let output = Command::new("git")
                .arg("-C")
                .arg(cwd)
                .args(args)
                .output()
                .expect("run git");
            assert!(
                output.status.success(),
                "git failed: {}",
                String::from_utf8_lossy(&output.stderr)
            );
            output
        };

        run(&root, &["init", "--quiet"]);
        run(&root, &["config", "user.name", "Ordivon Test"]);
        run(&root, &["config", "user.email", "ordivon@example.invalid"]);
        fs::write(root.join("README.md"), "parent\n").expect("write parent");
        run(&root, &["add", "README.md"]);
        run(&root, &["commit", "--quiet", "-m", "parent"]);

        let nested = root.join("nested");
        fs::create_dir_all(&nested).expect("create nested");
        run(&nested, &["init", "--quiet"]);
        run(&nested, &["config", "user.name", "Ordivon Test"]);
        run(&nested, &["config", "user.email", "ordivon@example.invalid"]);
        fs::write(nested.join("README.md"), "nested\n").expect("write nested");
        run(&nested, &["add", "README.md"]);
        run(&nested, &["commit", "--quiet", "-m", "nested"]);

        let untracked = git_output_bytes(
            &root,
            ["ls-files", "--others", "--exclude-standard", "-z"],
        )
        .expect("list untracked");
        let paths = parse_nul_paths(&untracked, "untracked Git path").expect("parse untracked");
        assert_eq!(paths, vec!["nested/".to_string()]);

        let entry =
            workspace_source_entry(&root, "nested/", None).expect("digest nested worktree");
        assert_eq!(entry.kind, "git-worktree");
        let digest = workspace_source_state_digest_at(&root).expect("digest parent state");
        fs::remove_dir_all(&root).expect("cleanup fixture");

        assert!(digest.starts_with("sha256:"));
    }

    #[test]
    fn outer_workspace_unborn_head_is_not_valid_source_revision() {
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "ordivon-unborn-outer-root-{}-{unique}",
            std::process::id()
        ));
        fs::create_dir_all(&root).expect("create outer root");
        let init = Command::new("git")
            .arg("-C")
            .arg(&root)
            .args(["init", "--quiet"])
            .status()
            .expect("init outer root");
        assert!(init.success());
        let rejected = workspace_source_state_digest_at(&root)
            .expect_err("outer Runtime Workspace must have a real committed HEAD");
        assert_eq!(rejected.code, UniversalExecErrorCode::ToolFailed);
        fs::remove_dir_all(root).expect("cleanup fixture");
    }

    #[test]
    fn unborn_nested_git_repo_is_observable_and_tracks_changes() {
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "ordivon-unborn-source-{}-{unique}",
            std::process::id()
        ));
        fs::create_dir_all(&root).expect("create parent");
        let run = |cwd: &Path, args: &[&str]| {
            let output = Command::new("git")
                .arg("-C")
                .arg(cwd)
                .args(args)
                .output()
                .expect("git");
            assert!(
                output.status.success(),
                "git failed: {}",
                String::from_utf8_lossy(&output.stderr)
            );
        };
        run(&root, &["init", "--quiet"]);
        run(&root, &["config", "user.name", "Ordivon Test"]);
        run(&root, &["config", "user.email", "ordivon@example.invalid"]);
        fs::write(root.join("README.md"), "parent").expect("write parent");
        run(&root, &["add", "README.md"]);
        run(&root, &["commit", "--quiet", "-m", "parent"]);
        let nested = root.join("unborn");
        fs::create_dir(&nested).expect("create nested");
        run(&nested, &["init", "--quiet"]);
        fs::write(nested.join("first.txt"), "first").expect("write nested");

        let first = workspace_source_state_digest_at(&root).expect("digest unborn nested");
        fs::write(nested.join("first.txt"), "second").expect("change nested");
        let second = workspace_source_state_digest_at(&root).expect("redigest unborn nested");
        assert_ne!(first, second);

        // An unborn branch name is part of source identity, even before commit.
        run(&nested, &["symbolic-ref", "HEAD", "refs/heads/another"]);
        let third = workspace_source_state_digest_at(&root).expect("digest new unborn branch");
        assert_ne!(second, third);
        fs::remove_dir_all(&root).expect("cleanup fixture");
    }

    #[test]
    fn ordinary_untracked_directory_cannot_be_source_git_worktree() {
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("clock")
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "ordivon-ordinary-source-directory-{}-{unique}",
            std::process::id()
        ));
        let nested = root.join("ordinary");
        fs::create_dir_all(&nested).expect("create ordinary directory");
        let status = Command::new("git")
            .arg("-C")
            .arg(&root)
            .args(["init", "--quiet"])
            .status()
            .expect("initialize parent Git repository");
        assert!(status.success());

        assert!(!is_git_worktree(&nested).expect("classify nested directory"));
        let error = workspace_source_entry(&root, "ordinary/", None)
            .err()
            .expect("a plain untracked directory must not be accepted as a Git worktree");
        assert_eq!(error.code, UniversalExecErrorCode::WorkspacePathDenied);
        fs::remove_dir_all(&root).expect("cleanup fixture");
    }
}

/// Domain-separated source commitment over an explicit read set. Git HEAD is
/// always bound; unrelated mutable paths are excluded rather than disabling
/// source validation. Scoped source trees reject filesystem aliases.
pub(crate) fn workspace_source_readset_digest_at(workspace:&Path,paths:&[String])->Result<String,UniversalExecError>{
    use sha2::{Digest,Sha256};
    use std::io::Read;
    let workspace=canonical_directory(workspace,"workspacePath")?;
    let mut hash=Sha256::new();hash.update(b"runtime-workspace-readset-v1\0");
    hash.update(workspace_head_revision_at(&workspace)?.as_bytes());
    fn walk(root:&Path,path:&Path,hash:&mut Sha256)->Result<(),UniversalExecError>{
        let relative=path.strip_prefix(root).map_err(|_|invalid("source path escaped Workspace","readPaths"))?;
        if relative.components().any(|v|matches!(v,std::path::Component::ParentDir|std::path::Component::RootDir|std::path::Component::Prefix(_))){return Err(invalid("invalid scoped source path","readPaths"));}
        if relative.components().any(|v|v.as_os_str()==".git"){return Ok(());}
        let mut ancestor=root.to_path_buf();
        for component in relative.components(){ancestor.push(component.as_os_str());if let Ok(meta)=fs::symlink_metadata(&ancestor){if meta.file_type().is_symlink(){return Err(invalid("scoped source path traversed an alias","readPaths"));}}}
        hash.update(relative.as_os_str().as_encoded_bytes());hash.update([0]);
        let meta=match fs::symlink_metadata(path){Ok(v)=>v,Err(e)if e.kind()==std::io::ErrorKind::NotFound=>{hash.update(b"absent");return Ok(())},Err(e)=>return Err(io_error(path,"inspect scoped source",e))};
        if meta.file_type().is_symlink(){return Err(invalid("scoped sources cannot traverse symlinks","readPaths"));}
        if meta.is_file(){
            #[cfg(unix)] {use std::os::unix::fs::MetadataExt;if meta.nlink()>1{return Err(invalid("scoped sources cannot contain hardlinked files","readPaths"));}}
            hash.update(b"file");
            #[cfg(unix)] {use std::os::unix::fs::PermissionsExt;hash.update(meta.permissions().mode().to_le_bytes());}hash.update(meta.len().to_le_bytes());
            let mut file=fs::File::open(path).map_err(|e|io_error(path,"open scoped source",e))?;let mut buffer=[0u8;65536];
            loop{let size=file.read(&mut buffer).map_err(|e|io_error(path,"read scoped source",e))?;if size==0{break;}hash.update(&buffer[..size]);}
        }else if meta.is_dir(){
            hash.update(b"directory");let mut entries=fs::read_dir(path).map_err(|e|io_error(path,"list scoped source",e))?.collect::<Result<Vec<_>,_>>().map_err(|e|io_error(path,"list scoped source",e))?;
            entries.sort_by_key(|v|v.file_name());for entry in entries{walk(root,&entry.path(),hash)?;}
        }else{return Err(invalid("unsupported file in scoped read set","readPaths"));}
        Ok(())
    }
    let mut paths=paths.to_vec();paths.sort();paths.dedup();
    for path in paths{
        if path.is_empty()||Path::new(&path).is_absolute()||Path::new(&path).components().any(|v|matches!(v,std::path::Component::ParentDir|std::path::Component::RootDir|std::path::Component::Prefix(_))){return Err(invalid("invalid scoped read path","readPaths"));}
        walk(&workspace,&workspace.join(path),&mut hash)?;
    }
    Ok(format!("sha256:{}",hex::encode(hash.finalize())))
}

#[cfg(test)] mod scoped_source_tests {
    use super::*;
    #[test] fn scoped_commitment_tracks_its_read_set_and_rejects_aliases(){
        let root=std::env::temp_dir().join(format!("runtime-readset-{}",uuid::Uuid::now_v7()));fs::create_dir_all(root.join("left")).unwrap();fs::create_dir(root.join("right")).unwrap();
        for args in [vec!["init"],vec!["-c","user.name=Test","-c","user.email=test@example.invalid","commit","--allow-empty","-m","source"]]{assert!(Command::new("git").arg("-C").arg(&root).args(args).output().unwrap().status.success());}
        fs::write(root.join("left/input"),b"before").unwrap();let paths=vec!["left".to_string()];let before=workspace_source_readset_digest_at(&root,&paths).unwrap();
        fs::write(root.join("right/output"),b"independent").unwrap();assert_eq!(before,workspace_source_readset_digest_at(&root,&paths).unwrap());
        fs::write(root.join("left/input"),b"changed").unwrap();assert_ne!(before,workspace_source_readset_digest_at(&root,&paths).unwrap());
        #[cfg(unix)] {std::os::unix::fs::symlink(root.join("left"),root.join("alias")).unwrap();assert!(workspace_source_readset_digest_at(&root,&["alias/input".into()]).is_err());}
        fs::remove_dir_all(root).unwrap();
    }
}
