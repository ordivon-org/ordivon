#[derive(Clone, Debug, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct TraceSummary {
    pub trace_id: String,
    pub core_ms: u64,
    pub total_ms: u64,
}


impl RuntimeServer {
    async fn run_core<T, F>(&self, tool: &'static str, operation: F) -> ToolOutcome<T>
    where
        T: Send + 'static,
        F: FnOnce() -> Result<T, ToolError> + Send + 'static,
    {
        let trace_id = next_trace_id("core");
        let total_started = Instant::now();
        let core_started = Instant::now();
        let joined = tokio::task::spawn_blocking(operation).await;
        let core_ms = elapsed_ms(core_started);
        let result = match joined {
            Ok(result) => result,
            Err(error) => Err(ToolError::internal(format!(
                "blocking operation failed to join: {error}"
            ))),
        };
        let trace = TraceSummary {
            trace_id,
            core_ms,
            total_ms: elapsed_ms(total_started),
        };
        self.record_trace(tool, &trace, result.is_ok());
        match result {
            Ok(value) => ToolOutcome::Success(value),
            Err(mut error) => {
                error.trace_id = Some(trace.trace_id);
                ToolOutcome::Error(error)
            }
        }
    }

    fn record_authority_shadow_for_bound_task(&self, tool: &str, request: &BoundTaskRun) {
        self.record_authority_shadow_candidate(tool, request.authority_shadow_candidate());
    }

    fn record_authority_shadow_for_proposal(&self, tool: &str, request: &TaskRunProposal) {
        self.record_authority_shadow_candidate(tool, proposal_authority_shadow_candidate(request));
    }

    fn record_authority_shadow_candidate(
        &self,
        tool: &str,
        candidate: Result<AuthorityEffectCandidate, FabricContractError>,
    ) {
        let Some(path) = &self.state.trace_path else {
            return;
        };
        let observed_unix_ms = unix_ms();
        let record = match candidate {
            Ok(candidate) => {
                let now_ms = observed_unix_ms.try_into().unwrap_or(u64::MAX);
                match evaluate_authority_shadow(
                    &candidate,
                    &self.state.authority_shadow_leases,
                    now_ms,
                ) {
                    Ok(decision) => json!({
                        "traceId": next_trace_id("authority-shadow"),
                        "event": "authority_shadow",
                        "tool": tool,
                        "observedUnixMs": observed_unix_ms,
                        "enforcement": "shadow",
                        "leaseCount": self.state.authority_shadow_leases.len(),
                        "candidate": candidate,
                        "decision": decision,
                    }),
                    Err(error) => json!({
                        "traceId": next_trace_id("authority-shadow"),
                        "event": "authority_shadow",
                        "tool": tool,
                        "observedUnixMs": observed_unix_ms,
                        "enforcement": "shadow",
                        "leaseCount": self.state.authority_shadow_leases.len(),
                        "candidate": candidate,
                        "evaluationError": error.to_string(),
                    }),
                }
            }
            Err(error) => json!({
                "traceId": next_trace_id("authority-shadow"),
                "event": "authority_shadow",
                "tool": tool,
                "observedUnixMs": observed_unix_ms,
                "enforcement": "shadow",
                "leaseCount": self.state.authority_shadow_leases.len(),
                "candidateError": error.to_string(),
            }),
        };

        let _guard = match GLOBAL_TRACE_LOCK.get_or_init(|| Mutex::new(())).lock() {
            Ok(guard) => guard,
            Err(error) => {
                tracing::warn!("trace lock poisoned while writing authority shadow: {error}");
                return;
            }
        };
        if let Err(error) = append_rotating_jsonl(path, &record, DEFAULT_TRACE_ROTATION_BYTES) {
            // Shadow telemetry must never become an execution dependency.
            tracing::warn!(
                "cannot append authority shadow trace {}: {error}",
                path.display()
            );
        }
    }

    fn record_trace(&self, tool: &str, trace: &TraceSummary, ok: bool) {
        let Some(path) = &self.state.trace_path else {
            return;
        };
        let _guard = match GLOBAL_TRACE_LOCK.get_or_init(|| Mutex::new(())).lock() {
            Ok(guard) => guard,
            Err(error) => {
                tracing::warn!("trace lock poisoned: {error}");
                return;
            }
        };
        let record = json!({
            "traceId": trace.trace_id,
            "tool": tool,
            "ok": ok,
            "coreMs": trace.core_ms,
            "totalMs": trace.total_ms,
            "observedUnixMs": unix_ms(),
        });
        let write_result = append_rotating_jsonl(path, &record, DEFAULT_TRACE_ROTATION_BYTES);
        if let Err(error) = write_result {
            tracing::warn!("cannot append trace {}: {error}", path.display());
        }
    }
}

fn next_trace_id(kind: &str) -> String {
    format!(
        "ordivon-{kind}-{}-{}-{}",
        std::process::id(),
        unix_ms(),
        GLOBAL_TRACE_SEQUENCE.fetch_add(1, Ordering::Relaxed)
    )
}

fn elapsed_ms(started: Instant) -> u64 {
    started.elapsed().as_millis().try_into().unwrap_or(u64::MAX)
}

fn unix_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
}
