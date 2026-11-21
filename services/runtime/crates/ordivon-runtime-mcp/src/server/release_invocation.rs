//! The already-supported structured release deployer CLI argument capability.
//! Workspace identity stays in Runtime Job/ReleaseEffect; the deployer is not a Workspace authority.
use super::{
    ExecutionBudget, ExecutionProfile, ExecutionProposal, ForeignReference, JobRunProposal,
    RuntimeReleaseApplyToolRequest, RuntimeReleaseExecutionConfig, RUNTIME_SCHEMA_VERSION,
};
use std::collections::BTreeMap;
use std::path::Path;

pub(super) fn build_release_deployer_args(
    release: &RuntimeReleaseExecutionConfig,
    request: &RuntimeReleaseApplyToolRequest,
    configured_source: &Path,
    candidate_dir: &Path,
    candidate_manifest: &Path,
    effect_id: &str,
    request_digest: &str,
) -> Vec<String> {
    let args = vec![
        "apply".to_string(),
        "--source-repo".to_string(),
        configured_source.to_string_lossy().into_owned(),
        "--commit".to_string(),
        request.commit.clone(),
        "--confirm-commit".to_string(),
        request.commit.clone(),
        "--candidate-dir".to_string(),
        candidate_dir.to_string_lossy().into_owned(),
        "--candidate-manifest".to_string(),
        candidate_manifest.to_string_lossy().into_owned(),
        "--install-dir".to_string(),
        release.install_dir.to_string_lossy().into_owned(),
        "--database".to_string(),
        release.database.to_string_lossy().into_owned(),
        "--env-file".to_string(),
        release.env_file.to_string_lossy().into_owned(),
        "--receipt-root".to_string(),
        release.receipt_root.to_string_lossy().into_owned(),
        "--service".to_string(),
        release.service_name.clone(),
        "--expected-tool-count".to_string(),
        request.expected_tool_count.to_string(),
        "--require-ref".to_string(),
        release.required_ref.clone(),
        "--effect-id".to_string(),
        effect_id.to_owned(),
        "--effect-request-digest".to_string(),
        request_digest.to_owned(),
        "--candidate-manifest-digest".to_string(),
        request.candidate_manifest_digest.clone(),
        "--drain-seconds".to_string(),
        "30".to_string(),
    ];
    let mut args = args;
    if let Some(broker_service_name) = release.broker_service_name.as_ref() {
        args.extend(["--broker-service".to_string(), broker_service_name.clone()]);
    }
    args
}

/// Bind the original Runtime Job admission to exactly one logical ReleaseEffect.
/// The Job owns Workspace identity; the physical deployer argv never does.
pub(super) fn build_release_effect_proposal(
    release: &RuntimeReleaseExecutionConfig,
    request: &RuntimeReleaseApplyToolRequest,
    principal: &str,
    global_limit: u32,
    candidate_deployer: &Path,
    effect_id: &str,
    args: Vec<String>,
) -> JobRunProposal {
    let proposal = JobRunProposal {
        schema_version: RUNTIME_SCHEMA_VERSION,
        client_request_id: request.client_request_id.clone(),
        principal: principal.to_owned(),
        global_limit,
        execution: ExecutionProposal {
            workspace_id: request.workspace_id.clone(),
            executable: candidate_deployer.to_string_lossy().into_owned(),
            args,
            cwd_relative: ".".to_string(),
            env: BTreeMap::new(),
            timeout_ms: Some(release.timeout_ms),
            stdout_limit_bytes: Some(262_144),
            stderr_limit_bytes: Some(262_144),
            steps: Vec::new(),
            budget: ExecutionBudget::default(),
            execution_profile: ExecutionProfile::TrustedLocal,
            execution_target: release.execution_target(),
            windows_authority: release.windows_authority(),
            windows_context: None,
            foreign_references: vec![ForeignReference {
                namespace: "ordivon.runtime".to_string(),
                reference_type: "runtime_release".to_string(),
                id: effect_id.to_owned(),
                generation: Some(request.commit.clone()),
                digest: Some(request.candidate_manifest_digest.clone()),
            }],
            host_dependencies: Vec::new(),
        },
        wait_ms: 0,
        stdout_tail_bytes: 0,
        stderr_tail_bytes: 0,
    };
    proposal
}

#[cfg(test)]
mod tests {
    use super::super::RuntimeReleaseExecutionPlatform;
    use super::*;
    use std::collections::BTreeMap;
    use std::path::PathBuf;

    fn configuration(broker: Option<&str>) -> RuntimeReleaseExecutionConfig {
        RuntimeReleaseExecutionConfig {
            platform: RuntimeReleaseExecutionPlatform::LocalLinux,
            source_repo: PathBuf::from("/source"),
            install_dir: PathBuf::from("/installed"),
            database: PathBuf::from("/database"),
            env_file: PathBuf::from("/settings.env"),
            receipt_root: PathBuf::from("/receipts"),
            service_name: "runtime.service".into(),
            broker_service_name: broker.map(str::to_owned),
            required_ref: "refs/tags/runtime-approved".into(),
            timeout_ms: 10000,
        }
    }

    fn release_request(workspace_id: &str) -> RuntimeReleaseApplyToolRequest {
        RuntimeReleaseApplyToolRequest {
            schema_version: 1,
            client_request_id: "release-real-request".into(),
            workspace_id: workspace_id.into(),
            commit: "a".repeat(40),
            candidate_manifest_digest: "sha256:manifest".into(),
            expected_tool_count: 23,
        }
    }

    fn options(args: &[String]) -> BTreeMap<&str, &str> {
        assert_eq!(args.first().map(String::as_str), Some("apply"));
        assert_eq!(args.len() % 2, 1, "all flags have one exact argument");
        let pairs: Vec<_> = args[1..].chunks_exact(2).collect();
        let options: BTreeMap<_, _> = pairs
            .iter()
            .map(|pair| (pair[0].as_str(), pair[1].as_str()))
            .collect();
        assert_eq!(
            options.len(),
            pairs.len(),
            "duplicate flags make the CLI ambiguous"
        );
        options
    }

    #[test]
    fn runtime_owns_workspace_identity_while_native_deployer_consumes_only_release_effect() {
        let config = configuration(None);
        let request = release_request("sensitive-workspace-owned-by-runtime");
        let make = |request: &RuntimeReleaseApplyToolRequest| {
            build_release_deployer_args(
                &config,
                request,
                Path::new("/source"),
                Path::new("/candidate"),
                Path::new("/candidate/manifest.json"),
                "effect-original",
                "sha256:effect-request",
            )
        };
        let args = make(&request);
        let args_other_workspace = make(&release_request("different-workspace"));
        assert_eq!(
            args, args_other_workspace,
            "the native deployer must not receive or distinguish the originating Workspace"
        );
        let options = options(&args);
        assert!(!options.contains_key("--workspace-id"));
        assert!(!args.iter().any(|arg| arg == &request.workspace_id));
        for (key, value) in [
            ("--source-repo", "/source"),
            ("--commit", request.commit.as_str()),
            ("--confirm-commit", request.commit.as_str()),
            ("--candidate-dir", "/candidate"),
            ("--candidate-manifest", "/candidate/manifest.json"),
            ("--install-dir", "/installed"),
            ("--database", "/database"),
            ("--env-file", "/settings.env"),
            ("--receipt-root", "/receipts"),
            ("--service", "runtime.service"),
            ("--expected-tool-count", "23"),
            ("--require-ref", "refs/tags/runtime-approved"),
            ("--effect-id", "effect-original"),
            ("--effect-request-digest", "sha256:effect-request"),
            ("--candidate-manifest-digest", "sha256:manifest"),
            ("--drain-seconds", "30"),
        ] {
            assert_eq!(
                options.get(key).copied(),
                Some(value),
                "deployer argument {key}"
            );
        }
        assert_eq!(options.len(), 16);
    }

    #[test]
    fn optional_broker_is_bound_to_its_own_native_service_not_workspace() {
        let release = release_request("workspace-real");
        let arguments = build_release_deployer_args(
            &configuration(Some("runtime-elevated-broker")),
            &release,
            Path::new("/src"),
            Path::new("/candidate"),
            Path::new("/candidate/manifest.json"),
            "effect-broker",
            "sha256:broker-request",
        );
        let options = options(&arguments);
        assert_eq!(
            options.get("--broker-service").copied(),
            Some("runtime-elevated-broker")
        );
        assert!(!options.contains_key("--workspace-id"));
        assert_eq!(options.get("--effect-id").copied(), Some("effect-broker"));
        assert_eq!(options.len(), 17);
    }

    #[test]
    fn runtime_job_proposal_binds_original_workspace_and_release_effect_independently_of_cli() {
        let config = configuration(None);
        let request = release_request("ws-claim-owned-by-runtime");
        let argv = build_release_deployer_args(
            &config,
            &request,
            Path::new("/source"),
            Path::new("/candidate"),
            Path::new("/candidate/manifest.json"),
            "effect-original",
            "sha256:effect-request",
        );
        let proposal = build_release_effect_proposal(
            &config,
            &request,
            "agent:original-issuer",
            4,
            Path::new("/candidate/ordivon-runtime-deploy"),
            "effect-original",
            argv.clone(),
        );
        assert_eq!(proposal.client_request_id, request.client_request_id);
        assert_eq!(proposal.principal, "agent:original-issuer");
        assert_eq!(proposal.global_limit, 4);
        assert_eq!(proposal.execution.workspace_id, request.workspace_id);
        assert_eq!(
            proposal.execution.executable,
            "/candidate/ordivon-runtime-deploy"
        );
        assert_eq!(proposal.execution.args, argv);
        assert_eq!(
            proposal.execution.execution_profile,
            ExecutionProfile::TrustedLocal
        );
        assert_eq!(
            proposal.execution.execution_target,
            config.execution_target()
        );
        assert_eq!(
            proposal.execution.windows_authority,
            config.windows_authority()
        );
        assert_eq!(proposal.execution.foreign_references.len(), 1);
        let effect = &proposal.execution.foreign_references[0];
        assert_eq!(effect.namespace, "ordivon.runtime");
        assert_eq!(effect.reference_type, "runtime_release");
        assert_eq!(effect.id, "effect-original");
        assert_eq!(effect.generation.as_deref(), Some(request.commit.as_str()));
        assert_eq!(
            effect.digest.as_deref(),
            Some(request.candidate_manifest_digest.as_str())
        );
        assert_eq!(proposal.execution.timeout_ms, Some(config.timeout_ms));
        assert_eq!(proposal.wait_ms, 0);
        assert_eq!(proposal.stdout_tail_bytes, 0);
        assert_eq!(proposal.stderr_tail_bytes, 0);

        let other = release_request("another-isolated-workspace");
        let other_proposal = build_release_effect_proposal(
            &config,
            &other,
            "agent:original-issuer",
            4,
            Path::new("/candidate/ordivon-runtime-deploy"),
            "effect-original",
            proposal.execution.args.clone(),
        );
        assert_ne!(
            proposal.execution.workspace_id,
            other_proposal.execution.workspace_id
        );
        assert_eq!(proposal.execution.args, other_proposal.execution.args);
        assert_eq!(
            proposal.execution.foreign_references,
            other_proposal.execution.foreign_references
        );
    }
}
