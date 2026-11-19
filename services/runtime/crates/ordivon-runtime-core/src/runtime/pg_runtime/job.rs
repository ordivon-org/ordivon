//! PostgreSQL Runtime Job admission, observation, and projection.
//! Physical cancellation is an independent use-case in job/cancellation.rs.
use super::*;
mod cancellation;

// Direct PostgreSQL Client reads must not erase SQLSTATE through io(Display).
// Keep the one shared PgAdmissionError taxonomy used by Recovery and admission.
fn pg_read_error(error: postgres::Error) -> RuntimeError {
    pg(PgAdmissionError::Database(error))
}

// Once PG has durably admitted this Job (including an exact idempotent replay),
// a later observation failure cannot retract the committed operation identity.
// The existing MCP error projection uses this witness to demand reconciliation
// instead of falsely reporting commitState=not_committed.
fn preserve_committed_job_identity<T>(
    job_id: &str,
    observed: RuntimeResult<T>,
) -> RuntimeResult<T> {
    observed.map_err(|error| error.with_operation_id(job_id))
}

/// The first observation follows a committed PG Job admission. SQLSTATE
/// serialization aborts may invalidate its read/runner reconciliation, not
/// the already-committed Job identity. Re-observe that SAME Job only; no
/// second admission or new external operation is allowed. Reuse the PG
/// admission module's proven bounded aborted-transaction backoff.
fn observe_committed_job_with_bounded_busy_recovery<T>(
    job_id: &str,
    observe: impl FnMut() -> RuntimeResult<T>,
) -> RuntimeResult<T> {
    let result = crate::pg_admission::retry_aborted_transaction(
        observe,
        |error| error.code == RuntimeErrorCode::RegistryBusy && error.retryable,
        std::thread::sleep,
    );
    preserve_committed_job_identity(job_id, result)
}

// A foreign reference is caller-authored metadata, never execution authority.
// Without a configured same-PG issuer verifier it cannot affect the environment.
// With a verifier, preserve exact source intent for the PG transactional guard.
fn preserve_qualified_issuer_environment(
    issuer_schema: Option<&str>,
    references: &[ForeignReference],
) -> bool {
    issuer_schema.is_some()
        && references.iter().any(|reference| {
            reference.namespace == "ordivon.harness" && reference.reference_type == "dispatch_fence"
        })
}

// Reuse the existing Workspace-owned disposable cache, outside the Git tree,
// for ordinary PostgreSQL Jobs. A trusted Cargo build target already uses
// its native private mount; Python bytecode and Ruff reuse the same cache owner.
// A project virtualenv is deliberately NOT redirected: one Workspace may
// contain multiple independent pyproject roots with incompatible dependencies.
fn pg_workspace_tool_environment(
    mut environment: std::collections::BTreeMap<String, String>,
    preserve_harness_fenced_request: bool,
    workspace_cache: &std::path::Path,
) -> std::collections::BTreeMap<String, String> {
    // Qualified same-PG Harness dispatch fences bind the caller's exact source
    // environment. Never silently alter their immutable effect identity.
    if !preserve_harness_fenced_request {
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
    let mut current = universal::open_directory_nofollow(&executor.store_root).map_err(io)?;
    for component in components.components() {
        let Component::Normal(name) = component else {
            return Err(RuntimeError::invalid(
                "contained cache path contains an untrusted component",
                "execution.env",
            ));
        };
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
        current = unsafe { std::fs::File::from_raw_fd(next) };
    }
    Ok(())
}

#[cfg(not(target_os = "linux"))]
fn pg_bounded_contained_cache_directory(
    _executor: &UniversalExecutorConfig,
    _path: &Path,
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
fn pg_contained_workspace_environment(
    mut environment: std::collections::BTreeMap<String, String>,
    executor: &UniversalExecutorConfig,
    workspace_id: &str,
) -> RuntimeResult<std::collections::BTreeMap<String, String>> {
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
        pg_bounded_contained_cache_directory(executor, &path)?;
        environment.insert(name.to_owned(), path.to_string_lossy().into_owned());
    }
    environment
        .entry("PATH".to_string())
        .or_insert_with(|| "/usr/bin:/bin".to_string());
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
            pg_workspace_tool_environment(original.clone(), true, Path::new("/tmp/test-cache")),
            original
        );
        let explicit = BTreeMap::from([(
            "CARGO_TARGET_DIR".to_owned(),
            "/proc/self/fd/198".to_owned(),
        )]);
        assert_eq!(
            pg_workspace_tool_environment(explicit.clone(), true, Path::new("/tmp/test-cache")),
            explicit
        );
    }

    #[test]
    fn ordinary_job_places_python_and_ruff_caches_outside_workspace_without_clobbering_intent() {
        let cache = Path::new("/runtime/cache/workspaces/ws-A");
        let actual = pg_workspace_tool_environment(Default::default(), false, cache);
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
        let preserved = pg_workspace_tool_environment(custom.clone(), false, cache);
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
        );
        assert_ne!(
            actual["PYTHONPYCACHEPREFIX"],
            unrelated["PYTHONPYCACHEPREFIX"]
        );
    }

    #[test]
    fn ordinary_pg_job_reuses_native_private_cargo_default_without_overriding_explicit() {
        let empty = BTreeMap::new();
        assert_eq!(
            pg_workspace_tool_environment(empty, false, Path::new("/tmp/test-cache"))
                ["CARGO_TARGET_DIR"],
            "/run/ordivon/cargo-target"
        );
        let explicit = BTreeMap::from([(
            "CARGO_TARGET_DIR".to_owned(),
            "/custom/agent/target".to_owned(),
        )]);
        let actual =
            pg_workspace_tool_environment(explicit.clone(), false, Path::new("/tmp/test-cache"));
        assert_eq!(actual["CARGO_TARGET_DIR"], explicit["CARGO_TARGET_DIR"]);
    }
}
impl PgRuntime {
    pub fn run(&self, proposal: &JobRunProposal) -> RuntimeResult<JobObservation> {
        super::admission_validation::validate_resource_run_proposal_structure(proposal)?;
        proposal
            .execution
            .budget
            .scheduling
            .clone()
            .unwrap_or_default()
            .validate()
            .map_err(|e| RuntimeError::invalid(e, "execution.budget.scheduling"))?;
        let identity = super::types::proposal_request_identity_digest(proposal)?;
        let mut db = self.store()?;
        // Replay before consulting mutable Workspace/executable state or policy.
        if let Some(row) = db.client.query_opt("SELECT job_id,request_digest FROM jobs WHERE principal=$1 AND client_request_id=$2", &[&proposal.principal,&proposal.client_request_id]).map_err(pg_read_error)? {
            if row.get::<_,String>(1)!=identity { return Err(pg(PgAdmissionError::IdempotencyConflict)); }
            let committed_job: String = row.get(0);
            let mut first_wait_ms = proposal.wait_ms;
            return observe_committed_job_with_bounded_busy_recovery(
                &committed_job,
                || self.observe(&proposal.principal, &JobObserveRequest { schema_version:1,job_id:committed_job.clone(),wait_ms:std::mem::replace(&mut first_wait_ms, 0),wait_until:JobObserveWaitUntil::Terminal,stdout_tail_bytes:proposal.stdout_tail_bytes,stderr_tail_bytes:proposal.stderr_tail_bytes,stdout_offset:None,stderr_offset:None }),
            );
        }
        let e = &proposal.execution;
        // ForeignReferences are not authorization. A real Harness dispatch
        // fence is only a source-owned exact-physical-intent indicator: do not
        // modify its environment before the actual issuer authority check.
        // Only an operator-configured issuer path may preserve the source environment;
        // the hint never authenticates the caller and PG still checks currentness.
        let preserve_harness_fenced_request = preserve_qualified_issuer_environment(
            self.config.harness_issuer_schema.as_deref(),
            &e.foreign_references,
        );
        if preserve_harness_fenced_request
            && e.execution_profile == ExecutionProfile::ContainedLocal
        {
            return Err(RuntimeError::invalid(
                "issuer-bound Tool environment cannot be rewritten for contained_local",
                "execution.executionProfile",
            ));
        }

        if e.execution_target != ExecutionTarget::LocalLinux
            || !matches!(
                e.execution_profile,
                ExecutionProfile::TrustedLocal | ExecutionProfile::ContainedLocal
            )
            || e.windows_context.is_some()
            || e.windows_authority != WindowsAuthority::Limited
        {
            return Err(RuntimeError::invalid(
                "PG vertical supports local_linux trusted_local or contained_local execution only",
                "execution",
            ));
        }
        // A current Issuer must not authorize unrelated physical steps/budgets.
        if self.config.harness_issuer_schema.is_some()
            && (!e.steps.is_empty() || !e.host_dependencies.is_empty() || !e.budget.is_empty())
        {
            return Err(RuntimeError::invalid(
                "issuer-fenced execution does not authorize custom budget/steps/host prerequisites",
                "execution",
            ));
        }
        // Reuse the installed Runtime validator. The committed PG plan
        // freezes the exact file set before native dispatch.
        let host_dependencies = super::host_dependency::validate_bindings(
            &e.host_dependencies,
            e.execution_target,
            e.execution_profile,
        )?;
        let timeout = e
            .timeout_ms
            .unwrap_or(self.config.executor.max_runtime_ms.min(30_000));
        let stdout = e
            .stdout_limit_bytes
            .unwrap_or(self.config.executor.max_output_bytes.min(1024 * 1024));
        let stderr = e
            .stderr_limit_bytes
            .unwrap_or(self.config.executor.max_output_bytes.min(1024 * 1024));
        if timeout == 0
            || timeout > self.config.executor.max_runtime_ms
            || stdout == 0
            || stderr == 0
            || stdout > self.config.executor.max_output_bytes
            || stderr > self.config.executor.max_output_bytes
        {
            return Err(RuntimeError::invalid(
                "execution limits exceed operator ceilings",
                "execution",
            ));
        }
        let runner = self
            .config
            .executor
            .runner_path
            .as_deref()
            .ok_or_else(|| error("native runner required"))?;
        super::platform::validate_runner(runner)?;
        let record = universal::load_workspace_record(&self.config.executor, &e.workspace_id)
            .map_err(super::super::error::map_universal_error)?;
        let workspace_generated_cache = self
            .config
            .executor
            .workspace_cache_path(&record.workspace_id);
        let cwd =
            universal::resolve_workspace_cwd(&record, &e.cwd_relative, "execution.cwdRelative")
                .map_err(io)?;
        let executable = super::platform::validate_executable(
            &self.config.executor,
            &e.executable,
            "execution.executable",
        )?;
        let source =
            universal::workspace_source_state_digest(&self.config.executor, &e.workspace_id)
                .map_err(io)?;
        // An Agent-authored plan is resolved only at new admission. Every
        // executable and cwd is checked through existing native authorities,
        // then frozen into the PostgreSQL execution plan and Runner bundle.
        let mut frozen_steps = Vec::with_capacity(e.steps.len());
        let mut cumulative_step_budget = 0_u64;
        for (index, step) in e.steps.iter().enumerate() {
            let path = super::platform::validate_executable(
                &self.config.executor,
                &step.executable,
                &format!("execution.steps[{index}].executable"),
            )?;
            let cwd = universal::resolve_workspace_cwd(
                &record,
                &step.cwd_relative,
                &format!("execution.steps[{index}].cwdRelative"),
            )
            .map_err(io)?;
            let ceiling = step
                .timeout_ms
                .unwrap_or(self.config.executor.max_runtime_ms.min(30_000));
            if ceiling == 0 || ceiling > self.config.executor.max_runtime_ms {
                return Err(RuntimeError::invalid(
                    "invalid plan step timeout",
                    "execution.steps",
                ));
            }
            cumulative_step_budget =
                cumulative_step_budget.checked_add(ceiling).ok_or_else(|| {
                    RuntimeError::invalid("plan step budget overflow", "execution.steps")
                })?;
            frozen_steps.push(RuntimeExecutionStep {
                id: step.id.clone(),
                executable: path.to_string_lossy().into_owned(),
                executable_digest: universal::sha256_file(&path).map_err(io)?,
                args: step.args.clone(),
                cwd: cwd.to_string_lossy().into_owned(),
                env: if e.execution_profile == ExecutionProfile::ContainedLocal {
                    pg_contained_workspace_environment(
                        step.env.clone(),
                        &self.config.executor,
                        &record.workspace_id,
                    )?
                } else {
                    pg_workspace_tool_environment(
                        step.env.clone(),
                        preserve_harness_fenced_request,
                        &workspace_generated_cache,
                    )
                },
                timeout_ms: ceiling,
                continue_on_error: step.continue_on_error,
            });
        }
        // When a plan supplies no job-wide timeout, the sum of resolved
        // per-step budgets is the exact finite ceiling, as on the mature Runner.
        let timeout = if !frozen_steps.is_empty() && e.timeout_ms.is_none() {
            cumulative_step_budget
        } else {
            timeout
        };
        if timeout == 0 || timeout > self.config.executor.max_runtime_ms {
            return Err(RuntimeError::invalid(
                "plan exceeds configured runtime maximum",
                "execution.timeoutMs",
            ));
        }
        let mut plan = RuntimeExecutionPlan {
            schema_version: 1,
            workspace_id: e.workspace_id.clone(),
            workspace_path: record.workspace_path.clone(),
            source_revision: record.source_revision.clone(),
            workspace_source_digest: Some(source),
            // Contained tasks can read their original Git worktree metadata
            // through the native read-only common-dir bind. Never grant a
            // writable mount of the shared source repository to an Agent.
            workspace_git_common_dir: if e.execution_profile == ExecutionProfile::ContainedLocal {
                Some(
                    universal::workspace_git_common_dir_at(Path::new(&record.workspace_path))
                        .map_err(io)?
                        .to_string_lossy()
                        .into_owned(),
                )
            } else {
                None
            },
            executable: executable.to_string_lossy().into_owned(),
            executable_digest: universal::sha256_file(&executable).map_err(io)?,
            args: e.args.clone(),
            cwd: cwd.to_string_lossy().into_owned(),
            env: if e.execution_profile == ExecutionProfile::ContainedLocal {
                pg_contained_workspace_environment(
                    e.env.clone(),
                    &self.config.executor,
                    &record.workspace_id,
                )?
            } else {
                pg_workspace_tool_environment(
                    e.env.clone(),
                    preserve_harness_fenced_request,
                    &workspace_generated_cache,
                )
            },
            timeout_ms: timeout,
            stdout_limit_bytes: stdout,
            stderr_limit_bytes: stderr,
            steps: frozen_steps,
            budget: e.budget.clone(),
            execution_profile: e.execution_profile,
            execution_target: e.execution_target,
            windows_authority: e.windows_authority,
            windows_context: None,
            windows_execution_context: None,
            // ForeignReference is an externally supplied identity/correlation
            // commitment, NEVER a credential or an authorization to dispatch.
            // Structural uniqueness is checked by the shared Runtime validator,
            // request identity hashes it, and the PG plan freezes it verbatim
            // for the native Runner and later terminal evidence.
            foreign_references: e.foreign_references.clone(),
            host_dependencies,
            input_set_id: None,
            effective_inputs: vec![],
            credential_set_id: None,
            principal: proposal.principal.clone(),
        };
        let mut contract = self.scheduling_contract(&plan)?;
        if e.budget.scheduling.is_none() {
            if let Some(max) = plan.budget.memory_max_bytes {
                contract.resources.memory_bytes = contract.resources.memory_bytes.min(max);
            }
            if let Some(max) = plan.budget.tasks_max {
                contract.resources.pids = contract.resources.pids.min(max);
            }
            if let Some(max) = plan.budget.cpu_quota_percent {
                contract.resources.cpu_millis =
                    contract.resources.cpu_millis.min(max.saturating_mul(10));
            }
        }
        if plan
            .budget
            .memory_max_bytes
            .is_some_and(|v| v < contract.resources.memory_bytes)
            || plan
                .budget
                .tasks_max
                .is_some_and(|v| v < contract.resources.pids)
            || plan
                .budget
                .cpu_quota_percent
                .is_some_and(|v| v.saturating_mul(10) < contract.resources.cpu_millis)
        {
            return Err(RuntimeError::invalid(
                "resource request exceeds its hard execution ceiling",
                "execution.budget.scheduling",
            ));
        }
        if let (Some(high), Some(max)) = (contract.memory_high_bytes, plan.budget.memory_max_bytes)
        {
            if high > max {
                return Err(RuntimeError::invalid(
                    "memoryHighBytes exceeds memoryMaxBytes",
                    "execution.budget.scheduling",
                ));
            }
        }
        for relative in &contract.workspace_access.write_paths {
            let path =
                fs::canonicalize(Path::new(&plan.workspace_path).join(relative)).map_err(io)?;
            if !path.starts_with(&plan.workspace_path) || !path.is_dir() {
                return Err(RuntimeError::invalid(
                    "writePaths requires existing contained directories",
                    "execution.budget.scheduling.workspaceAccess",
                ));
            }
        }
        if contract.workspace_access.read_only || !contract.workspace_access.write_paths.is_empty()
        {
            plan.workspace_git_common_dir = Some(
                universal::workspace_git_common_dir_at(Path::new(&plan.workspace_path))
                    .map_err(io)?
                    .to_string_lossy()
                    .into_owned(),
            );
        }
        if !contract.workspace_access.write_paths.is_empty() {
            let _ = universal::workspace_source_readset_digest_at(
                Path::new(&plan.workspace_path),
                &contract.workspace_access.write_paths,
            )
            .map_err(io)?;
        }
        if !contract.workspace_access.read_paths.is_empty() {
            plan.workspace_source_digest = Some(
                universal::workspace_source_readset_digest_at(
                    Path::new(&plan.workspace_path),
                    &contract.workspace_access.read_paths,
                )
                .map_err(io)?,
            );
        }
        plan.budget.scheduling = Some(contract);
        let plan_json = encode(&plan)?;
        let plan_digest = universal::sha256_bytes(plan_json.as_bytes());
        // An Operation commits to the resolved execution world and native
        // provider. The proposal identity remains stable for exact replay.
        // Use the existing canonical Job identity contract rather than a
        // PostgreSQL-specific digest scheme.
        let provider_digest = universal::sha256_file(runner).map_err(io)?;
        let operation_digest = JobIdentityContract::operation_digest(
            &identity,
            &plan_digest,
            OperationIdentityBindings::Provider {
                provider_digest: &provider_digest,
            },
        );
        let job = format!("job-{}", Uuid::now_v7());
        let attempt = format!("attempt-{}", Uuid::now_v7());
        let bundle = self
            .config
            .executor
            .store_root
            .join("pg-attempts")
            .join(&attempt);
        let token = universal::sha256_bytes(
            format!("runtime-launch-v1\0{attempt}\0{operation_digest}").as_bytes(),
        );
        let input = PgAdmissionInput {
            job_id: job.clone(),
            attempt_id: attempt.clone(),
            reservation_id: format!("reservation-{}", Uuid::now_v7()),
            principal: proposal.principal.clone(),
            client_request_id: proposal.client_request_id.clone(),
            request_digest: identity,
            operation_digest,
            workspace_id: e.workspace_id.clone(),
            workspace_snapshot_json: encode(
                &json!({"workspace":record,"executionProvider":{"contract":"local_linux_runner_v1","executableDigest":universal::sha256_file(runner).map_err(io)?}}),
            )?,
            execution_plan_digest: plan_digest,
            execution_plan_json: plan_json,
            launch_token_digest: universal::sha256_bytes(token.as_bytes()),
            bundle_path: bundle.to_string_lossy().into_owned(),
            unit_name: format!("ordivon-pg-{attempt}.service"),
            global_limit: 0,
            created_at_ms: now()?,
            expected_source_sha256: self.config.source_sha256.clone(),
        };
        // Planning is intentionally outside the coarse PG admission lock:
        // Git/source hashing is potentially expensive. The exact Workspace
        // lifetime identity MUST nonetheless be rebound after acquiring the
        // same global lock as workspace.close/open/mutate, before INSERT jobs.
        // The native Runner separately verifies frozen source/readset bytes
        // before physical execution; this cheap fence prevents an orphaned
        // durable Job when the Workspace was closed or replaced meanwhile.
        let workspace_guard = || {
            universal::ensure_workspace_mutation_quiescent(&self.config.executor, &e.workspace_id)
                .map_err(|_| PgAdmissionError::WorkspaceStale)?;
            let current = universal::load_workspace_record(&self.config.executor, &e.workspace_id)
                .map_err(|_| PgAdmissionError::WorkspaceStale)?;
            if current != record {
                return Err(PgAdmissionError::WorkspaceStale);
            }
            Ok(())
        };
        let job = match db
            .admit_with_workspace_guard(
                &input,
                &workspace_guard,
                self.config.harness_issuer_schema.as_deref(),
            )
            .map_err(pg)?
        {
            PgAdmissionOutcome::Created(j) | PgAdmissionOutcome::Existing(j) => j,
        };
        let _ = self.schedule_pending_jobs();
        let mut first_wait_ms = proposal.wait_ms;
        observe_committed_job_with_bounded_busy_recovery(&job, || {
            self.observe(
                &proposal.principal,
                &JobObserveRequest {
                    schema_version: 1,
                    job_id: job.clone(),
                    wait_ms: std::mem::replace(&mut first_wait_ms, 0),
                    wait_until: JobObserveWaitUntil::Terminal,
                    stdout_tail_bytes: proposal.stdout_tail_bytes,
                    stderr_tail_bytes: proposal.stderr_tail_bytes,
                    stdout_offset: None,
                    stderr_offset: None,
                },
            )
        })
    }
    pub fn observe(
        &self,
        principal: &str,
        request: &JobObserveRequest,
    ) -> RuntimeResult<JobObservation> {
        if request.schema_version != 1
            || request.wait_ms > MAX_TASK_WAIT_MS
            || request.stdout_tail_bytes > MAX_TASK_TAIL_BYTES
            || request.stderr_tail_bytes > MAX_TASK_TAIL_BYTES
        {
            return Err(RuntimeError::invalid(
                "invalid observation limits",
                "waitMs",
            ));
        }
        let deadline = Instant::now() + Duration::from_millis(request.wait_ms);
        let mut initial_signature = None;
        let mut db = self.store()?;
        let mut verified_committed_job = false;
        loop {
            // An authorization success proves this durable Job identity.
            // Every later PG projection/observation failure must preserve it
            // for reconcile-first semantics, including after a LISTEN wait.
            self.authorize(&mut db, &request.job_id, principal)
                .map_err(|e| {
                    if verified_committed_job {
                        e.with_operation_id(&request.job_id)
                    } else {
                        e
                    }
                })?;
            verified_committed_job = true;
            preserve_committed_job_identity(
                &request.job_id,
                self.reconcile(&mut db, &request.job_id),
            )?;
            let value =
                preserve_committed_job_identity(&request.job_id, self.project(&mut db, request))?;
            // Gateway observes change_or_terminal. Only compare durable
            // observable state, not time-dependent display projections.
            let signature = (
                value.status.clone(),
                value.desired_state,
                value.attempt_state,
                value.termination_intent,
                value.execution_terminal,
                value.delivery_disposition,
                value.recovery_required,
                value.stdout_available_bytes,
                value.stderr_available_bytes,
                value.artifacts.len(),
            );
            let changed = initial_signature
                .as_ref()
                .is_some_and(|start| start != &signature);
            if initial_signature.is_none() {
                initial_signature = Some(signature);
            }
            if value.execution_terminal
                || request.wait_ms == 0
                || Instant::now() >= deadline
                || (request.wait_until == JobObserveWaitUntil::ChangeOrTerminal && changed)
            {
                return Ok(value);
            }
            if value.attempt_state == Some(AttemptState::Accepted) {
                use postgres::fallible_iterator::FallibleIterator;
                db.client
                    .batch_execute("LISTEN ordivon_runtime_schedule")
                    .map_err(pg_read_error)
                    .map_err(|e| e.with_operation_id(&request.job_id))?;
                let wait = deadline
                    .saturating_duration_since(Instant::now())
                    .min(Duration::from_secs(1));
                let _ = db
                    .client
                    .notifications()
                    .timeout_iter(wait)
                    .next()
                    .map_err(pg_read_error)
                    .map_err(|e| e.with_operation_id(&request.job_id))?;
            } else if let Some(attempt_id) = value.attempt_id.as_deref() {
                let bundle = self
                    .config
                    .executor
                    .store_root
                    .join("pg-attempts")
                    .join(attempt_id);
                let start = fs::read(bundle.join("runner-start.json"))
                    .ok()
                    .and_then(|bytes| serde_json::from_slice::<RunnerStartEvidence>(&bytes).ok());
                super::platform::wait_for_attempt_change(
                    &bundle,
                    start
                        .as_ref()
                        .map(|evidence| evidence.control_group.as_str()),
                    deadline.saturating_duration_since(Instant::now()),
                );
            } else {
                thread::sleep(
                    Duration::from_millis(250)
                        .min(deadline.saturating_duration_since(Instant::now())),
                );
            }
        }
    }
    /// Projection only: never calls reconciliation or the OS execution provider.
    pub fn get(
        &self,
        principal: &str,
        job: &str,
        event_limit: u32,
    ) -> RuntimeResult<RuntimeJobInspection> {
        if event_limit > MAX_INSPECTION_EVENT_LIMIT {
            return Err(RuntimeError::invalid("event limit exceeded", "eventLimit"));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, job, principal)?;
        let snapshot = match db
            .observe_job_readonly(job, &self.config.source_sha256)
            .map_err(pg)?
        {
            PgJobReadback::Observed(s) => s,
            _ => return Err(error("inconclusive PG lifecycle")),
        };
        let (a, p, operation) = self.readback_attempt(&mut db, &snapshot)?;
        let j = db
            .client
            .query_one(
                "SELECT client_request_id,created_at_ms FROM jobs WHERE job_id=$1",
                &[&job],
            )
            .map_err(pg_read_error)?;
        let counts=db.client.query_one("SELECT count(*),COALESCE(sum(byte_length),0)::bigint,count(*) FILTER(WHERE truncated) FROM artifacts WHERE job_id=$1",&[&job]).map_err(pg_read_error)?;
        let mut by_kind = std::collections::BTreeMap::new();
        for row in db
            .client
            .query(
                "SELECT kind,count(*) FROM artifacts WHERE job_id=$1 GROUP BY kind",
                &[&job],
            )
            .map_err(pg_read_error)?
        {
            by_kind.insert(row.get(0), row.get::<_, i64>(1) as u64);
        }
        let events=db.client.query("SELECT event_sequence,event_type,origin,previous_state,new_state,reason_code,observed_at_ms FROM job_events WHERE job_id=$1 ORDER BY event_sequence LIMIT $2",&[&job,&(i64::from(event_limit)+1)]).map_err(pg_read_error)?;
        let created = j.get::<_, i64>(1) as u64;
        let mut previous = created;
        let timeline = events
            .iter()
            .take(event_limit as usize)
            .map(|r| {
                let at = r.get::<_, i64>(6) as u64;
                let delta = at.saturating_sub(previous);
                previous = at;
                RuntimeInspectionEvent {
                    sequence: r.get::<_, i64>(0) as u64,
                    attempt_id: Some(a.attempt_id.clone()),
                    event_type: r.get(1),
                    origin: r.get(2),
                    previous_state: r.get(3),
                    new_state: r.get(4),
                    reason_code: r.get(5),
                    observed_at_ms: at,
                    elapsed_ms: at.saturating_sub(created),
                    delta_ms: delta,
                    detail: None,
                }
            })
            .collect();
        let terminal = snapshot.resolution.is_some();
        let exit = db
            .client
            .query_one(
                "SELECT exit_code FROM attempts WHERE attempt_id=$1",
                &[&a.attempt_id],
            )
            .map_err(pg_read_error)?
            .get(0);
        Ok(RuntimeJobInspection {
            schema_version: 2,
            generated_at_ms: now()? as u64,
            migration_version: 0,
            job: RuntimeInspectionJob {
                job_id: job.into(),
                client_request_id: j.get(0),
                operation_digest: operation,
                workspace_id: p.workspace_id,
                source_revision: p.source_revision,
                workspace_source_digest: p.workspace_source_digest,
                created_at_ms: created,
                desired_state: if snapshot.desired_state == "run" {
                    JobDesiredState::Run
                } else {
                    JobDesiredState::Cancelled
                },
                resolution: snapshot
                    .resolution
                    .as_deref()
                    .map(JobResolution::parse)
                    .transpose()?,
                mechanically_converged: terminal,
                semantic_completion_evaluated: false,
            },
            attempts: vec![RuntimeInspectionAttempt {
                attempt_id: a.attempt_id,
                attempt_number: a.attempt_number,
                state: a.state,
                termination_intent: a.termination_intent,
                created_at_ms: a.created_at_ms,
                started_at_ms: None,
                finished_at_ms: snapshot.finished_at_ms.map(|v| v as u64),
                duration_ms: None,
                exit_code: exit,
                result_available: terminal && by_kind.contains_key("execution_result"),
                reservation_state: ReservationState::parse(&snapshot.reservation_state)?,
                reservation_release_reason: None,
                conditions: vec![],
                artifact_count: counts.get::<_, i64>(0) as u64,
                artifact_bytes: counts.get::<_, i64>(1) as u64,
                truncated_artifacts: counts.get::<_, i64>(2) as u64,
            }],
            attempts_truncated: false,
            artifacts: RuntimeInspectionArtifactSummary {
                count: counts.get::<_, i64>(0) as u64,
                bytes: counts.get::<_, i64>(1) as u64,
                truncated: counts.get::<_, i64>(2) as u64,
                by_kind,
            },
            episodes: RuntimeInspectionEpisodes::default(),
            timeline,
            events_truncated: events.len() > event_limit as usize,
        })
    }
}

#[cfg(test)]
mod committed_observation_tests {
    use super::*;

    #[test]
    fn postcommit_busy_observation_recovers_same_job_without_new_admission() {
        let mut observations = 0_u32;
        let result = observe_committed_job_with_bounded_busy_recovery("job-stable", || {
            observations += 1;
            if observations < 3 {
                Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryBusy,
                    "aborted serializable post-admission PG observation",
                    None,
                    true,
                ))
            } else {
                Ok("observed-existing-job")
            }
        })
        .unwrap();
        assert_eq!(result, "observed-existing-job");
        assert_eq!(observations, 3);

        let mut unknown_attempts = 0_u32;
        let failed: RuntimeResult<()> =
            observe_committed_job_with_bounded_busy_recovery("job-stable", || {
                unknown_attempts += 1;
                Err(RuntimeError::new(
                    RuntimeErrorCode::DispatchOutcomeUnknown,
                    "external effect outcome is unknown",
                    None,
                    false,
                ))
            });
        assert_eq!(
            unknown_attempts, 1,
            "never retry an ambiguous physical effect"
        );
        assert_eq!(
            failed.unwrap_err().operation_id.as_deref(),
            Some("job-stable")
        );

        let mut nonretryable_busy_reads = 0_u32;
        let refused: RuntimeResult<()> =
            observe_committed_job_with_bounded_busy_recovery("job-stable", || {
                nonretryable_busy_reads += 1;
                Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryBusy,
                    "not a proven aborted observation",
                    None,
                    false,
                ))
            });
        assert_eq!(nonretryable_busy_reads, 1);
        assert_eq!(
            refused.unwrap_err().operation_id.as_deref(),
            Some("job-stable")
        );

        let mut bounded_reads = 0_u32;
        let exhausted: RuntimeResult<()> =
            observe_committed_job_with_bounded_busy_recovery("job-stable", || {
                bounded_reads += 1;
                Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryBusy,
                    "serializable observation always aborted",
                    None,
                    true,
                ))
            });
        assert_eq!(
            bounded_reads, 8,
            "reuse the existing bounded PG retry budget"
        );
        let final_error = exhausted.unwrap_err();
        assert_eq!(final_error.code, RuntimeErrorCode::RegistryBusy);
        assert_eq!(final_error.operation_id.as_deref(), Some("job-stable"));
    }

    #[test]
    fn post_admission_observation_error_keeps_committed_job_identity() {
        let failed: RuntimeResult<()> = Err(RuntimeError::new(
            RuntimeErrorCode::RegistryUnavailable,
            "serializable PG observation failed after Job admission",
            None,
            false,
        ));
        let error = preserve_committed_job_identity("job-exact", failed).unwrap_err();
        assert_eq!(error.operation_id.as_deref(), Some("job-exact"));
        assert_eq!(error.code, RuntimeErrorCode::RegistryUnavailable);
        assert_eq!(
            preserve_committed_job_identity("job-exact", Ok::<_, RuntimeError>(7)).unwrap(),
            7
        );
    }

    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN"]
    fn native_postgres_direct_job_queries_preserve_sqlstate_and_exact_operation_id() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit disposable PostgreSQL server required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        for (state, expected) in [
            ("40001", RuntimeErrorCode::RegistryBusy),
            ("40P01", RuntimeErrorCode::RegistryBusy),
            ("23505", RuntimeErrorCode::RegistryUnavailable),
        ] {
            let postgres_error = db
                .batch_execute(&format!(
                    "DO $$ BEGIN RAISE EXCEPTION SQLSTATE '{state}'; END $$;"
                ))
                .unwrap_err();
            let failed: RuntimeResult<()> = Err(pg_read_error(postgres_error));
            let observed =
                preserve_committed_job_identity("job-real-direct-PG", failed).unwrap_err();
            assert_eq!(observed.code, expected, "SQLSTATE {state}");
            assert_eq!(observed.operation_id.as_deref(), Some("job-real-direct-PG"));
            if expected == RuntimeErrorCode::RegistryBusy {
                assert!(observed.retryable);
                assert_eq!(observed.retry_after_ms, Some(250));
            } else {
                assert!(!observed.retryable);
            }
        }
        let mut observed = 0_u32;
        let qualified =
            observe_committed_job_with_bounded_busy_recovery("job-real-direct-PG", || {
                observed += 1;
                if observed == 1 {
                    let abort = db
                        .batch_execute("DO $$ BEGIN RAISE EXCEPTION SQLSTATE '40001'; END $$;")
                        .unwrap_err();
                    Err(pg_read_error(abort))
                } else {
                    Ok("the original committed Job")
                }
            })
            .unwrap();
        assert_eq!(observed, 2);
        assert_eq!(qualified, "the original committed Job");
    }
}
