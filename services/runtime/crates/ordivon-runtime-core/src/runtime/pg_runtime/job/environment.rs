//! Workspace-owned tool environment and private cache materialization for PG Jobs.
//! Business Job admission delegates here; cache path ownership and source immutability stay explicit.
use super::*;

// Reuse the existing Workspace-owned disposable cache, outside the Git tree,
// for ordinary PostgreSQL Jobs. A trusted Cargo build target already uses
// its native private mount; Python bytecode and Ruff reuse the same cache owner.
// A project virtualenv is deliberately NOT redirected: one Workspace may
// contain multiple independent pyproject roots with incompatible dependencies.
pub(super) fn pg_workspace_tool_environment(
    mut environment: std::collections::BTreeMap<String, String>,
    preserve_harness_fenced_request: bool,
    workspace_cache: &std::path::Path,
    shared_package_cache: Option<&std::path::Path>,
) -> std::collections::BTreeMap<String, String> {
    // Qualified same-PG Harness dispatch fences bind the caller's exact source
    // environment. Never silently alter their immutable effect identity.
    if !preserve_harness_fenced_request {
        // A private XDG_CACHE_HOME would otherwise also make uv's download
        // cache private. Reuse the existing Runtime-owned trusted Linux
        // package cache, while leaving project virtualenvs and generated
        // outputs private. Contained jobs take their separate environment path.
        if let Some(shared) = shared_package_cache {
            environment
                .entry("UV_CACHE_DIR".to_string())
                .or_insert_with(|| shared.join("uv").to_string_lossy().into_owned());
        }
        environment
            .entry("CARGO_TARGET_DIR".to_string())
            .or_insert_with(|| {
                crate::runtime::build_target_contract::TRUSTED_BUILD_TARGET_PRESENTATION.to_string()
            });
        for (name, path) in [
            ("XDG_CACHE_HOME", workspace_cache.to_path_buf()),
            (
                "PYTHONPYCACHEPREFIX",
                workspace_cache.join("python-bytecode"),
            ),
            ("RUFF_CACHE_DIR", workspace_cache.join("ruff")),
        ] {
            environment
                .entry(name.to_string())
                .or_insert_with(|| path.to_string_lossy().into_owned());
        }
    }
    environment
}

/// Create the existing Runtime-owned cache directories through directory
/// handles, refusing symbolic-link traversal at *every* component. A
/// contained process owns its writable caches; it may leave a HOME/cache
/// symlink behind before its next Run. Blind create_dir_all would let the
/// next root-owned PG admission follow that link into an unrelated host path.
#[cfg(target_os = "linux")]
fn pg_bounded_contained_cache_directory(
    executor: &UniversalExecutorConfig,
    path: &Path,
    workspace_id: &str,
) -> RuntimeResult<()> {
    use std::ffi::CString;
    use std::os::fd::{AsRawFd, FromRawFd};
    use std::os::unix::ffi::OsStrExt;
    use std::path::Component;

    let components = path.strip_prefix(&executor.store_root).map_err(|_| {
        RuntimeError::invalid(
            "contained cache escaped Runtime store root",
            "execution.env",
        )
    })?;
    // The parents cache/, cache/tmp/, cache/workspaces/, cache/build/
    // are SHARED Runtime authority. Never chgrp/chmod them for a single
    // task. Only the exact private Workspace cache and its descendants
    // can become writable by that task's Unix group.
    let private_roots = [
        executor.workspace_cache_path(workspace_id),
        executor.workspace_tmp_path(workspace_id),
        executor.workspace_build_cache_path(workspace_id),
    ];
    if !private_roots.iter().any(|root| path.starts_with(root)) {
        return Err(RuntimeError::invalid(
            "contained cache is not rooted in the original Workspace",
            "execution.env",
        ));
    }
    let mut walked = executor.store_root.clone();
    let mut current = universal::open_directory_nofollow(&executor.store_root).map_err(io)?;
    for component in components.components() {
        let Component::Normal(name) = component else {
            return Err(RuntimeError::invalid(
                "contained cache path contains an untrusted component",
                "execution.env",
            ));
        };
        walked.push(name);
        let segment = CString::new(name.as_bytes()).map_err(|_| {
            RuntimeError::invalid("contained cache path contains NUL", "execution.env")
        })?;
        let open_dir = || unsafe {
            libc::openat(
                current.as_raw_fd(),
                segment.as_ptr(),
                libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
            )
        };
        let mut next = open_dir();
        if next < 0 {
            let first = std::io::Error::last_os_error();
            if first.kind() != std::io::ErrorKind::NotFound {
                return Err(RuntimeError::invalid(
                    format!("contained cache path is not a real directory: {first}"),
                    "execution.env",
                ));
            }
            let made = unsafe { libc::mkdirat(current.as_raw_fd(), segment.as_ptr(), 0o700) };
            if made < 0
                && std::io::Error::last_os_error().kind() != std::io::ErrorKind::AlreadyExists
            {
                return Err(io(std::io::Error::last_os_error()));
            }
            next = open_dir();
        }
        if next < 0 {
            return Err(RuntimeError::invalid(
                format!(
                    "contained cache is not a no-follow directory: {}",
                    std::io::Error::last_os_error()
                ),
                "execution.env",
            ));
        }
        // Only the opened, nofollow WORKSPACE-PRIVATE cache root and
        // descendants may be group-writable. A single Agent must not gain
        // ownership/write permission over other Workspaces via a shared
        // cache ancestor.
        if private_roots.iter().any(|root| walked.starts_with(root)) {
            let gid = executor.workspace_gid.ok_or_else(|| {
                RuntimeError::invalid(
                    "contained workspace GID absent",
                    "execution.executionProfile",
                )
            })?;
            if unsafe { libc::fchown(next, 0, gid) } < 0 || unsafe { libc::fchmod(next, 0o770) } < 0
            {
                let failure = std::io::Error::last_os_error();
                unsafe { libc::close(next) };
                return Err(io(failure));
            }
        }
        current = unsafe { std::fs::File::from_raw_fd(next) };
    }
    Ok(())
}

#[cfg(not(target_os = "linux"))]
fn pg_bounded_contained_cache_directory(
    _executor: &UniversalExecutorConfig,
    _path: &Path,
    _workspace_id: &str,
) -> RuntimeResult<()> {
    Err(RuntimeError::invalid(
        "contained_local requires Linux native directory authority",
        "execution.executionProfile",
    ))
}

/// Reuse Runtime's single workspace-owned cache roots for the already
/// supported systemd contained_local profile. Each path bound writable into
/// the native mount namespace must be derived from the admitted Workspace,
/// never from an agent-supplied environment variable. Prepare them before
/// the irreversible PG dispatch-issued/OS launch boundary.
pub(super) fn pg_contained_workspace_environment(
    mut environment: std::collections::BTreeMap<String, String>,
    executor: &UniversalExecutorConfig,
    workspace_id: &str,
    original_workspace_path: &Path,
) -> RuntimeResult<std::collections::BTreeMap<String, String>> {
    if !matches!((executor.workspace_uid, executor.workspace_gid), (Some(uid), Some(gid)) if uid != 0 && gid != 0)
    {
        return Err(RuntimeError::invalid(
            "contained_local requires operator-owned nonroot Workspace UID/GID",
            "execution.executionProfile",
        ));
    }
    let workspace_cache = executor.workspace_cache_path(workspace_id);
    let workspace_tmp = executor.workspace_tmp_path(workspace_id);
    let build_cache = executor.workspace_build_cache_path(workspace_id);
    let tooling = workspace_cache.join("tooling");
    let paths = [
        ("HOME", workspace_cache.join("home")),
        ("TMPDIR", workspace_tmp),
        ("XDG_CACHE_HOME", workspace_cache.clone()),
        ("CARGO_TARGET_DIR", build_cache.join("cargo")),
        ("UV_CACHE_DIR", tooling.join("uv")),
        ("PIP_CACHE_DIR", tooling.join("pip")),
        ("npm_config_cache", tooling.join("npm")),
        ("PNPM_HOME", tooling.join("pnpm")),
        ("COREPACK_HOME", tooling.join("corepack")),
        ("BUN_INSTALL_CACHE_DIR", tooling.join("bun/install-cache")),
        ("GOMODCACHE", tooling.join("go/mod")),
        ("GOCACHE", tooling.join("go/build")),
        (
            "PYTHONPYCACHEPREFIX",
            workspace_cache.join("python-bytecode"),
        ),
        ("RUFF_CACHE_DIR", workspace_cache.join("ruff")),
    ];
    // The native systemd property builder bind-mounts these environment
    // paths. Allowing an Agent to choose HOME=/etc/... or TMPDIR=/etc/...
    // would turn execution environment data into filesystem mount authority.
    for (name, path) in &paths {
        let qualified = path.to_string_lossy().into_owned();
        if environment
            .get(*name)
            .is_some_and(|actual| actual != &qualified)
        {
            return Err(RuntimeError::invalid(
                format!("contained_local {name} must use Workspace-owned cache"),
                "execution.env",
            ));
        }
    }
    for (name, path) in paths {
        pg_bounded_contained_cache_directory(executor, &path, workspace_id)?;
        environment.insert(name.to_owned(), path.to_string_lossy().into_owned());
    }
    environment
        .entry("PATH".to_string())
        .or_insert_with(|| "/usr/bin:/bin".to_string());
    // This EXACT environment is frozen into the PG RunnerRequest. The
    // unprivileged child runs with env_clear(): a systemd Unit --setenv or
    // inherited root control-plane environment NEVER reaches it.
    // The private Git snapshot was created before Workspace OPEN became
    // ACTIVE. A legacy Workspace with no snapshot remains unqualified.
    let private_git = workspace_cache.join("agent-git");
    if !std::fs::symlink_metadata(&private_git)
        .is_ok_and(|meta| meta.is_dir() && !meta.file_type().is_symlink())
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceStateMismatch,
            "Workspace has no independently materialized nonroot Git snapshot",
            Some("execution.workspaceId"),
            false,
        ));
    }
    pg_bounded_contained_cache_directory(executor, &private_git, workspace_id)?;
    for (name, expected) in [
        ("GIT_DIR", private_git.to_string_lossy().into_owned()),
        (
            "GIT_WORK_TREE",
            original_workspace_path.to_string_lossy().into_owned(),
        ),
    ] {
        if environment
            .get(name)
            .is_some_and(|actual| actual != &expected)
        {
            return Err(RuntimeError::invalid(
                format!("contained_local {name} cannot override original Git binding"),
                "execution.env",
            ));
        }
        environment.insert(name.to_owned(), expected);
    }
    // Git sees the root-owned worktree and rejects it for the unprivileged
    // payload. Exempt ONLY the original PG-admitted worktree in Git's
    // protected command-scope config; never authorize safe.directory='*'
    // or grant source-common-dir write authority.
    for (name, expected) in [
        ("GIT_CONFIG_COUNT", "1".to_owned()),
        ("GIT_CONFIG_KEY_0", "safe.directory".to_owned()),
        (
            "GIT_CONFIG_VALUE_0",
            original_workspace_path.to_string_lossy().into_owned(),
        ),
    ] {
        if environment
            .get(name)
            .is_some_and(|actual| actual != &expected)
        {
            return Err(RuntimeError::invalid(
                format!("contained_local {name} cannot override Git worktree identity"),
                "execution.env",
            ));
        }
        environment.insert(name.to_owned(), expected);
    }
    Ok(environment)
}

#[cfg(test)]
mod cargo_issuer_environment_tests {
    use super::{pg_workspace_tool_environment, preserve_qualified_issuer_environment};
    use crate::runtime::ForeignReference;
    use std::path::Path;

    fn candidate_fence() -> ForeignReference {
        ForeignReference {
            namespace: "ordivon.harness".into(),
            reference_type: "dispatch_fence".into(),
            id: "harness-dispatch-fence:test".into(),
            generation: None,
            digest: None,
        }
    }

    #[test]
    fn spoofed_harness_hint_without_issuer_cannot_bypass_private_cargo_default() {
        let fence = candidate_fence();
        let enabled = preserve_qualified_issuer_environment(None, std::slice::from_ref(&fence));
        assert!(!enabled);
        let actual = pg_workspace_tool_environment(
            Default::default(),
            enabled,
            Path::new("/tmp/test-cache"),
            None,
        );
        assert_eq!(
            actual.get("CARGO_TARGET_DIR").map(String::as_str),
            Some("/run/ordivon/cargo-target")
        );
        assert!(preserve_qualified_issuer_environment(
            Some("harness"),
            &[fence]
        ));
        assert!(!preserve_qualified_issuer_environment(Some("harness"), &[]));
    }

    #[test]
    fn unrelated_reference_does_not_change_cargo_environment() {
        let mut other = candidate_fence();
        other.namespace = "unrelated.owner".into();
        assert!(!preserve_qualified_issuer_environment(
            Some("harness"),
            &[other]
        ));
    }
    use std::collections::BTreeMap;

    #[test]
    fn issuer_bound_private_cargo_environment_keeps_exact_source_env() {
        let original = BTreeMap::from([("LANG".to_owned(), "C".to_owned())]);
        assert_eq!(
            pg_workspace_tool_environment(
                original.clone(),
                true,
                Path::new("/tmp/test-cache"),
                None
            ),
            original
        );
        let explicit = BTreeMap::from([(
            "CARGO_TARGET_DIR".to_owned(),
            "/proc/self/fd/198".to_owned(),
        )]);
        assert_eq!(
            pg_workspace_tool_environment(
                explicit.clone(),
                true,
                Path::new("/tmp/test-cache"),
                None
            ),
            explicit
        );
    }

    #[test]
    fn ordinary_job_places_python_and_ruff_caches_outside_workspace_without_clobbering_intent() {
        let cache = Path::new("/runtime/cache/workspaces/ws-A");
        let actual = pg_workspace_tool_environment(Default::default(), false, cache, None);
        assert_eq!(actual["XDG_CACHE_HOME"], "/runtime/cache/workspaces/ws-A");
        assert_eq!(
            actual["PYTHONPYCACHEPREFIX"],
            "/runtime/cache/workspaces/ws-A/python-bytecode"
        );
        assert_eq!(
            actual["RUFF_CACHE_DIR"],
            "/runtime/cache/workspaces/ws-A/ruff"
        );
        assert!(!actual.contains_key("UV_PROJECT_ENVIRONMENT"));
        let custom = std::collections::BTreeMap::from([
            ("XDG_CACHE_HOME".to_string(), "/custom/xdg".to_string()),
            ("PYTHONPYCACHEPREFIX".to_string(), "/custom/pyc".to_string()),
            ("RUFF_CACHE_DIR".to_string(), "/custom/ruff".to_string()),
        ]);
        let preserved = pg_workspace_tool_environment(custom.clone(), false, cache, None);
        assert_eq!(preserved["XDG_CACHE_HOME"], custom["XDG_CACHE_HOME"]);
        assert_eq!(
            preserved["PYTHONPYCACHEPREFIX"],
            custom["PYTHONPYCACHEPREFIX"]
        );
        assert_eq!(preserved["RUFF_CACHE_DIR"], custom["RUFF_CACHE_DIR"]);
        let unrelated = pg_workspace_tool_environment(
            Default::default(),
            false,
            Path::new("/runtime/cache/workspaces/ws-B"),
            None,
        );
        assert_ne!(
            actual["PYTHONPYCACHEPREFIX"],
            unrelated["PYTHONPYCACHEPREFIX"]
        );
    }

    #[test]
    fn ordinary_linux_pg_jobs_reuse_uv_download_cache_across_workspaces() {
        let shared = Path::new("/runtime/cache/shared");
        let a = pg_workspace_tool_environment(
            Default::default(),
            false,
            Path::new("/runtime/cache/workspaces/ws-A"),
            Some(shared),
        );
        let b = pg_workspace_tool_environment(
            Default::default(),
            false,
            Path::new("/runtime/cache/workspaces/ws-B"),
            Some(shared),
        );
        assert_eq!(a["UV_CACHE_DIR"], "/runtime/cache/shared/uv");
        assert_eq!(a["UV_CACHE_DIR"], b["UV_CACHE_DIR"]);
        assert_ne!(a["XDG_CACHE_HOME"], b["XDG_CACHE_HOME"]);
        assert!(!a.contains_key("UV_PROJECT_ENVIRONMENT"));

        let explicit = BTreeMap::from([("UV_CACHE_DIR".into(), "/explicit/uv".into())]);
        let kept = pg_workspace_tool_environment(
            explicit.clone(),
            false,
            Path::new("/runtime/cache/workspaces/ws-A"),
            Some(shared),
        );
        assert_eq!(kept["UV_CACHE_DIR"], "/explicit/uv");
        assert_eq!(
            pg_workspace_tool_environment(
                explicit.clone(),
                true,
                Path::new("/tmp/private"),
                Some(shared)
            ),
            explicit
        );
        let non_linux = pg_workspace_tool_environment(
            Default::default(),
            false,
            Path::new("/tmp/private"),
            None,
        );
        assert!(!non_linux.contains_key("UV_CACHE_DIR"));
    }

    #[test]
    fn ordinary_pg_job_reuses_native_private_cargo_default_without_overriding_explicit() {
        let empty = BTreeMap::new();
        assert_eq!(
            pg_workspace_tool_environment(empty, false, Path::new("/tmp/test-cache"), None)
                ["CARGO_TARGET_DIR"],
            "/run/ordivon/cargo-target"
        );
        let explicit = BTreeMap::from([(
            "CARGO_TARGET_DIR".to_owned(),
            "/custom/agent/target".to_owned(),
        )]);
        let actual = pg_workspace_tool_environment(
            explicit.clone(),
            false,
            Path::new("/tmp/test-cache"),
            None,
        );
        assert_eq!(actual["CARGO_TARGET_DIR"], explicit["CARGO_TARGET_DIR"]);
    }
}
