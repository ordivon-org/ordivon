#[derive(Clone, Debug, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct TraceSummary {
    pub trace_id: String,
    pub core_ms: u64,
    pub blocking_wait_ms: Option<u64>,
    pub operation_ms: Option<u64>,
    pub join_resume_ms: Option<u64>,
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
        let joined = tokio::task::spawn_blocking(move || {
            let operation_started = Instant::now();
            let blocking_wait_ms = trace_duration_ms(operation_started.duration_since(core_started));
            let result = operation();
            let operation_finished = Instant::now();
            let operation_ms = trace_duration_ms(operation_finished.duration_since(operation_started));
            (result, blocking_wait_ms, operation_ms, operation_finished)
        })
        .await;
        let core_finished = Instant::now();
        let core_ms = trace_duration_ms(core_finished.duration_since(core_started));
        let (result, blocking_wait_ms, operation_ms, join_resume_ms) = match joined {
            Ok((result, wait_ms, operation_ms, operation_finished)) => (
                result,
                Some(wait_ms),
                Some(operation_ms),
                Some(trace_duration_ms(core_finished.duration_since(operation_finished))),
            ),
            Err(error) => (
                Err(ToolError::internal(format!(
                    "blocking operation failed to join: {error}"
                ))),
                None,
                None,
                None,
            ),
        };
        let trace = TraceSummary {
            trace_id,
            core_ms,
            blocking_wait_ms,
            operation_ms,
            join_resume_ms,
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
            "blockingWaitMs": trace.blocking_wait_ms,
            "operationMs": trace.operation_ms,
            "joinResumeMs": trace.join_resume_ms,
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
    trace_duration_ms(started.elapsed())
}

fn trace_duration_ms(duration: std::time::Duration) -> u64 {
    duration.as_millis().try_into().unwrap_or(u64::MAX)
}

fn unix_ms() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis()
}
