#[derive(Clone)]
pub struct ServerConfig {
    pub runtime: RuntimeConfig,
    pub input_authorities: Vec<InputAuthority>,
    pub credential_authorities: Vec<CredentialAuthority>,
    pub execution: ExecutionContext,
    pub release: Option<RuntimeReleaseExecutionConfig>,
    pub input_ingress: Option<InputIngressExecutionConfig>,
    pub trace_path: Option<PathBuf>,
}

#[derive(Clone)]
pub struct RuntimeServer {
    state: Arc<ServerState>,
    #[allow(dead_code)]
    tool_router: ToolRouter<Self>,
}

struct ServerState {
    runtime: Runtime,
    executor: UniversalExecutorConfig,
    execution: ExecutionContext,
    release: Option<RuntimeReleaseExecutionConfig>,
    input_ingress: Option<InputIngressExecutionConfig>,
    trace_path: Option<PathBuf>,
}

impl RuntimeServer {
    pub fn new(config: ServerConfig) -> Result<Self, ToolError> {
        let default_runtime_ms = config.runtime.executor.max_runtime_ms;
        Self::new_with_default_runtime_ms(config, default_runtime_ms)
    }

    pub fn new_with_default_runtime_ms(
        config: ServerConfig,
        default_runtime_ms: u64,
    ) -> Result<Self, ToolError> {
        let executor = config.runtime.executor.clone();
        executor.ensure_store().map_err(ToolError::from)?;
        let runtime = Runtime::new_with_authorities_and_default_runtime(
            config.runtime,
            config.input_authorities,
            config.credential_authorities,
            default_runtime_ms,
        )
        .map_err(ToolError::from)?;
        if let Some(release) = config.release.as_ref() {
            for (path, field) in [
                (&release.source_repo, "release.sourceRepo"),
                (&release.install_dir, "release.installDir"),
                (&release.database, "release.database"),
                (&release.env_file, "release.envFile"),
                (&release.receipt_root, "release.receiptRoot"),
            ] {
                if !path.is_absolute() {
                    return Err(ToolError::invalid(
                        "Runtime Release paths must be absolute",
                        field,
                    ));
                }
            }
            if release.timeout_ms == 0 || release.timeout_ms > executor.max_runtime_ms {
                return Err(ToolError::invalid(
                    "Runtime Release timeout must fit inside Runtime maxRuntimeMs",
                    "release.timeoutMs",
                ));
            }
        }
        if let Some(ingress) = config.input_ingress.as_ref() {
            if !ingress.staging_root.is_absolute()
                || !ingress.workstation_tool.is_absolute()
                || !ingress.workstation_config.is_absolute()
            {
                return Err(ToolError::invalid(
                    "input ingress paths must be absolute operator-owned paths",
                    "inputIngress",
                ));
            }
            if ingress.authorities.is_empty() {
                return Err(ToolError::invalid(
                    "input ingress must explicitly opt in at least one authority",
                    "inputIngress.authorities",
                ));
            }
            if ingress.download_hosts.is_empty()
                || ingress
                    .download_hosts
                    .iter()
                    .any(|host| !validate_ingress_download_host_config(host))
            {
                return Err(ToolError::invalid(
                    "input ingress must explicitly configure normalized allowed downloadHosts",
                    "inputIngress.downloadHosts",
                ));
            }
            if ingress.max_bytes == 0 || ingress.max_bytes > 512 * 1024 * 1024 {
                return Err(ToolError::invalid(
                    "input ingress maxBytes must be between 1 and 512 MiB",
                    "inputIngress.maxBytes",
                ));
            }
        }
        let state = Arc::new(ServerState {
            runtime,
            executor,
            execution: config.execution,
            release: config.release,
            input_ingress: config.input_ingress,
            trace_path: config.trace_path,
        });
        Ok(Self {
            state,
            tool_router: Self::tool_router(),
        })
    }

    pub fn runtime_handle(&self) -> Runtime {
        self.state.runtime.clone()
    }

    fn decorate_tool_for_host_extensions(&self, mut tool: Tool) -> Tool {
        if tool.name.as_ref() == "input.ingest" && self.state.input_ingress.is_some() {
            tool.meta
                .get_or_insert_default()
                .0
                .insert("openai/fileParams".to_string(), json!(["file"]));
        }
        tool
    }

    pub(crate) fn catalog_tools(&self) -> Vec<Tool> {
        self.tool_router
            .list_all()
            .into_iter()
            .map(|tool| self.decorate_tool_for_host_extensions(tool))
            .collect()
    }

    async fn perform_input_ingress(
        &self,
        request: InputIngressToolRequest,
    ) -> Result<InputIngressToolResult, ToolError> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(ToolError::invalid(
                "schemaVersion must be 1",
                "schemaVersion",
            ));
        }
        let ingress = self.state.input_ingress.clone().ok_or_else(|| {
            ToolError::invalid(
                "input ingress is not configured on this Runtime",
                "authority",
            )
        })?;
        if !ingress
            .authorities
            .iter()
            .any(|value| value == &request.authority)
        {
            return Err(ToolError::invalid(
                "authority is not explicitly enabled for external input ingress",
                "authority",
            ));
        }
        if !validate_ingress_sha256(&request.expected_sha256) {
            return Err(ToolError::invalid(
                "expectedSha256 must be sha256:<64-hex>",
                "expectedSha256",
            ));
        }
        if request.expected_size_bytes == 0 || request.expected_size_bytes > ingress.max_bytes {
            return Err(ToolError::invalid(
                "expectedSizeBytes must be positive and no greater than configured maxBytes",
                "expectedSizeBytes",
            ));
        }
        if !validate_ingress_relative_object(&request.relative_object) {
            return Err(ToolError::invalid(
                "relativeObject must be one normalized POSIX relative path",
                "relativeObject",
            ));
        }
        if request.file.file_id.is_empty() || request.file.file_id.len() > 512 {
            return Err(ToolError::invalid(
                "file.file_id is invalid",
                "file.file_id",
            ));
        }
        let url = reqwest::Url::parse(&request.file.download_url).map_err(|_| {
            ToolError::invalid(
                "file.download_url must be a valid HTTPS URL",
                "file.download_url",
            )
        })?;
        if url.scheme() != "https" || !url.username().is_empty() || url.password().is_some() {
            return Err(ToolError::invalid(
                "file.download_url must use HTTPS without URL userinfo",
                "file.download_url",
            ));
        }
        let initial_host = url.host_str().unwrap_or_default().to_ascii_lowercase();
        if !ingress_download_host_allowed(&ingress.download_hosts, &initial_host) {
            return Err(ToolError::invalid(
                "file.download_url host is not operator-authorized for input ingress",
                "file.download_url",
            ));
        }

        std::fs::create_dir_all(&ingress.staging_root).map_err(|_| {
            ToolError::internal("cannot prepare private input-ingress staging root")
        })?;
        let metadata = std::fs::symlink_metadata(&ingress.staging_root).map_err(|_| {
            ToolError::internal("cannot observe private input-ingress staging root")
        })?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err(ToolError::internal(
                "configured input-ingress staging root is not a real directory",
            ));
        }
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt as _;
            std::fs::set_permissions(
                &ingress.staging_root,
                std::fs::Permissions::from_mode(0o700),
            )
            .map_err(|_| ToolError::internal("cannot make input-ingress staging root private"))?;
        }

        let host_file_reference_digest = format!(
            "sha256:{:x}",
            Sha256::digest(request.file.file_id.as_bytes())
        );
        let expected_sha256 = request.expected_sha256.to_ascii_lowercase();
        let mut identity = Sha256::new();
        identity.update(request.client_request_id.as_bytes());
        identity.update(b"\0");
        identity.update(request.authority.as_bytes());
        identity.update(b"\0");
        identity.update(request.relative_object.as_bytes());
        identity.update(b"\0");
        identity.update(expected_sha256.as_bytes());
        identity.update(b"\0");
        identity.update(request.expected_size_bytes.to_string().as_bytes());
        let key = format!("{:x}", identity.finalize());
        let source_name = format!("{key}.source");
        let request_name = format!("{key}.request.json");
        let source_path = ingress.staging_root.join(&source_name);
        let request_path = ingress.staging_root.join(&request_name);
        let temporary_path = ingress
            .staging_root
            .join(format!(".{key}.{}.part", Uuid::now_v7()));
        let cleanup = |paths: &[&std::path::Path]| {
            for path in paths {
                let _ = std::fs::remove_file(path);
            }
        };
        cleanup(&[&temporary_path]);

        let workstation_request = json!({
            "schemaVersion": 1,
            "requestId": request.client_request_id.clone(),
            "carrier": ingress.workstation_carrier.clone(),
            "sourceObject": source_name,
            "sourceProvenance": {
                "provider": "openai-host-file-param",
                "providerFileId": format!("host-declared-{host_file_reference_digest}"),
            },
            "expectedSha256": expected_sha256.clone(),
            "authority": request.authority.clone(),
            "relativeObject": request.relative_object.clone(),
        });
        let serialized = serde_json::to_vec(&workstation_request)
            .map_err(|_| ToolError::internal("cannot serialize Workstation ingress request"))?;
        if request_path.exists() {
            let retained = std::fs::read(&request_path).map_err(|_| {
                ToolError::internal("cannot read retained private Workstation ingress request")
            })?;
            if retained != serialized {
                return Err(ToolError::invalid(
                    "retained staging request conflicts with same durable input identity",
                    "clientRequestId",
                ));
            }
        } else {
            let mut output = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&request_path)
                .map_err(|_| {
                    ToolError::internal("cannot create private Workstation ingress request")
                })?;
            std::io::Write::write_all(&mut output, &serialized)
                .and_then(|_| output.sync_all())
                .map_err(|_| {
                    ToolError::internal("cannot persist private Workstation ingress request")
                })?;
        }

        let run_workstation = |reconcile_only: bool| -> Result<
            (std::process::ExitStatus, serde_json::Value),
            ToolError,
        > {
            let mut command = std::process::Command::new(&ingress.workstation_tool);
            command
                .arg("--config")
                .arg(&ingress.workstation_config)
                .arg("--request")
                .arg(&request_path);
            if reconcile_only {
                command.arg("--reconcile-only");
            }
            let process = command.output().map_err(|_| {
                ToolError::internal("cannot invoke Workstation input-authority ingress")
            })?;
            let body: serde_json::Value = serde_json::from_slice(&process.stdout)
                .map_err(|_| ToolError::internal("Workstation ingress returned invalid JSON"))?;
            Ok((process.status, body))
        };

        let build_result =
            |receipt: serde_json::Value| -> Result<InputIngressToolResult, ToolError> {
                if receipt.get("byteSize").and_then(serde_json::Value::as_u64)
                    != Some(request.expected_size_bytes)
                {
                    return Err(ToolError::internal(
                        "Workstation receipt byte size differs from expectedSizeBytes",
                    ));
                }
                if receipt
                    .get("observedSha256")
                    .and_then(serde_json::Value::as_str)
                    != Some(expected_sha256.as_str())
                {
                    return Err(ToolError::internal(
                        "Workstation receipt digest differs from expectedSha256",
                    ));
                }
                Ok(InputIngressToolResult {
                    schema_version: 1,
                    kind: "ordivon.runtime.input-ingress-adapter-receipt".to_string(),
                    authority: request.authority.clone(),
                    relative_object: request.relative_object.clone(),
                    expected_sha256: expected_sha256.clone(),
                    expected_size_bytes: request.expected_size_bytes,
                    host_file_reference_digest: host_file_reference_digest.clone(),
                    source_identity_standing: "HOST_DECLARED_UNVERIFIED".to_string(),
                    workstation_receipt: receipt,
                    non_claims: vec![
                        "host file reference digest is not cryptographic provider identity"
                            .to_string(),
                        "byte materialization is not Artifact/domain acceptance".to_string(),
                        "Runtime adapter success is not consumer execution success".to_string(),
                    ],
                })
            };

        let (reconcile_status, reconcile) = run_workstation(true)?;
        if !reconcile_status.success() {
            return Err(ToolError::internal(
                "Workstation ingress reconciliation failed closed",
            ));
        }
        if reconcile
            .get("commitStanding")
            .and_then(serde_json::Value::as_str)
            .is_some_and(|value| value.starts_with("COMMITTED"))
        {
            let result = build_result(reconcile)?;
            cleanup(&[&source_path, &request_path]);
            return Ok(result);
        }
        if reconcile
            .get("standing")
            .and_then(serde_json::Value::as_str)
            != Some("SOURCE_REQUIRED")
        {
            return Err(ToolError::internal(
                "Workstation ingress reconciliation did not admit a source fetch",
            ));
        }

        let staged_valid = if source_path.exists() {
            match ingress_stage_size_digest(&source_path, ingress.max_bytes) {
                Ok((size, digest))
                    if size == request.expected_size_bytes && digest == expected_sha256 =>
                {
                    true
                }
                _ => {
                    cleanup(&[&source_path]);
                    false
                }
            }
        } else {
            false
        };

        if !staged_valid {
            let mut response = ingress_pinned_https_get(url, &ingress.download_hosts).await?;
            if !response.status().is_success() {
                return Err(ToolError::internal(format!(
                    "input file download returned HTTP {}",
                    response.status().as_u16()
                )));
            }
            if let Some(length) = response.content_length() {
                if length != request.expected_size_bytes {
                    return Err(ToolError::invalid(
                        "input file Content-Length differs from expectedSizeBytes",
                        "expectedSizeBytes",
                    ));
                }
            }
            let mut output = std::fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&temporary_path)
                .map_err(|_| ToolError::internal("cannot create private input staging file"))?;
            let mut digest = Sha256::new();
            let mut observed_bytes = 0_u64;
            while let Some(chunk) = response
                .chunk()
                .await
                .map_err(|_| ToolError::internal("input file download stream failed"))?
            {
                observed_bytes = observed_bytes.saturating_add(chunk.len() as u64);
                if observed_bytes > request.expected_size_bytes {
                    cleanup(&[&temporary_path]);
                    return Err(ToolError::invalid(
                        "input file stream exceeds expectedSizeBytes",
                        "expectedSizeBytes",
                    ));
                }
                digest.update(&chunk);
                std::io::Write::write_all(&mut output, &chunk)
                    .map_err(|_| ToolError::internal("cannot write private input staging bytes"))?;
            }
            std::io::Write::flush(&mut output)
                .and_then(|_| output.sync_all())
                .map_err(|_| ToolError::internal("cannot fsync private input staging bytes"))?;
            drop(output);
            if observed_bytes != request.expected_size_bytes {
                cleanup(&[&temporary_path]);
                return Err(ToolError::invalid(
                    "input file stream length differs from expectedSizeBytes",
                    "expectedSizeBytes",
                ));
            }
            let observed_digest = format!("sha256:{:x}", digest.finalize());
            if observed_digest != expected_sha256 {
                cleanup(&[&temporary_path]);
                return Err(ToolError::invalid(
                    "downloaded input bytes do not match expectedSha256",
                    "expectedSha256",
                ));
            }
            match std::fs::hard_link(&temporary_path, &source_path) {
                Ok(()) => {}
                Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                    let (size, digest) =
                        ingress_stage_size_digest(&source_path, ingress.max_bytes)?;
                    if size != request.expected_size_bytes || digest != expected_sha256 {
                        cleanup(&[&temporary_path]);
                        return Err(ToolError::internal(
                            "concurrent input stage conflicts with expected bytes",
                        ));
                    }
                }
                Err(_) => {
                    cleanup(&[&temporary_path]);
                    return Err(ToolError::internal(
                        "cannot publish verified private input stage",
                    ));
                }
            }
            cleanup(&[&temporary_path]);
        }

        let (status, receipt) = run_workstation(false)?;
        let receipt = if status.success()
            && receipt
                .get("commitStanding")
                .and_then(serde_json::Value::as_str)
                .is_some_and(|value| value.starts_with("COMMITTED"))
        {
            receipt
        } else {
            let (retry_status, recovered) = run_workstation(true)?;
            if !retry_status.success()
                || !recovered
                    .get("commitStanding")
                    .and_then(serde_json::Value::as_str)
                    .is_some_and(|value| value.starts_with("COMMITTED"))
            {
                return Err(ToolError::internal(
                    "Workstation input-authority ingress did not converge to a committed receipt",
                ));
            }
            recovered
        };
        let result = build_result(receipt)?;
        cleanup(&[&source_path, &request_path]);
        Ok(result)
    }

    pub fn tool_catalog_digest(&self) -> String {
        let mut tools = self.catalog_tools();
        tools.sort_by(|left, right| left.name.cmp(&right.name));
        let bytes = serde_json::to_vec(&tools)
            .expect("Tool catalog serialization is infallible for generated schemas");
        format!("sha256:{:x}", Sha256::digest(bytes))
    }

    pub(crate) fn discovery_result(&self) -> DiscoverResult {
        let mut result = DiscoverResult::from_server_info(
            self.supported_protocol_versions().into_owned(),
            self.get_info(),
        );
        result.meta.get_or_insert_default().0.insert(
            "com.ordivon/runtime/toolCatalogDigest".to_string(),
            serde_json::Value::String(self.tool_catalog_digest()),
        );
        result
    }
}
