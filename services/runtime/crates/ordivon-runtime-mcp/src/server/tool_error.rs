#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ToolErrorOrigin {
    McpAdapter,
    RuntimeCore,
    WorkspaceExecutor,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ToolRetryClass {
    Never,
    SafeSameRequest,
    ReconcileFirst,
    /// Workspace-scope capacity rejection: the holder Job is identified in
    /// `capacity.holderJobIds`. Observe the holder to terminal, re-observe the
    /// Workspace, reassess the original intent, then submit a fresh request —
    /// never blindly resubmit, because the Workspace state basis may have moved.
    ObserveThenReassess,
    /// Global-scope capacity rejection: another Workspace holds the capacity.
    /// Wait for capacity (observe a holder or retryAfterMs backoff), then the
    /// same request may be retried unchanged.
    WaitThenRetry,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ToolCommitState {
    NotStarted,
    NotCommitted,
    /// A durable Runtime operation identity is known to exist; reconcile it instead of creating new work.
    Committed,
    Unknown,
}

#[derive(Clone, Debug, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ToolError {
    pub code: String,
    pub message: String,
    #[serde(flatten)]
    context: Box<ToolErrorContext>,
}

#[derive(Clone, Debug, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ToolErrorContext {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub field: Option<String>,
    pub origin: ToolErrorOrigin,
    pub retry_class: ToolRetryClass,
    pub commit_state: ToolCommitState,
    pub retryable: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub retry_after_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub capacity: Option<Box<RuntimeCapacity>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub trace_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub operation_id: Option<String>,
}

impl std::ops::Deref for ToolError {
    type Target = ToolErrorContext;

    fn deref(&self) -> &Self::Target {
        &self.context
    }
}

impl std::ops::DerefMut for ToolError {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.context
    }
}

impl ToolError {
    fn internal(message: impl Into<String>) -> Self {
        Self {
            code: "INTERNAL_ERROR".to_string(),
            message: message.into(),
            context: Box::new(ToolErrorContext {
                field: None,
                origin: ToolErrorOrigin::McpAdapter,
                retry_class: ToolRetryClass::SafeSameRequest,
                commit_state: ToolCommitState::NotStarted,
                retryable: true,
                retry_after_ms: None,
                capacity: None,
                trace_id: None,
                operation_id: None,
            }),
        }
    }

    fn invalid(message: impl Into<String>, field: &str) -> Self {
        Self {
            code: "INVALID_REQUEST".to_string(),
            message: message.into(),
            context: Box::new(ToolErrorContext {
                field: Some(field.to_string()),
                origin: ToolErrorOrigin::McpAdapter,
                retry_class: ToolRetryClass::Never,
                commit_state: ToolCommitState::NotStarted,
                retryable: false,
                retry_after_ms: None,
                capacity: None,
                trace_id: None,
                operation_id: None,
            }),
        }
    }
}

impl From<RuntimeError> for ToolError {
    fn from(error: RuntimeError) -> Self {
        let code = serde_json::to_value(&error.code)
            .ok()
            .and_then(|value| value.as_str().map(ToString::to_string))
            .unwrap_or_else(|| "EXECUTION_ERROR".to_string());
        let committed_operation = error.operation_id.is_some();
        let capacity_scope = error
            .capacity
            .as_deref()
            .map(|capacity| capacity.scope.clone());
        let (retry_class, commit_state) = if committed_operation {
            (ToolRetryClass::ReconcileFirst, ToolCommitState::Committed)
        } else {
            match error.code {
                ordivon_runtime_core::RuntimeErrorCode::DispatchOutcomeUnknown
                | ordivon_runtime_core::RuntimeErrorCode::ReconciliationRequired => {
                    (ToolRetryClass::ReconcileFirst, ToolCommitState::Unknown)
                }
                ordivon_runtime_core::RuntimeErrorCode::WorkspaceExists => {
                    (ToolRetryClass::ReconcileFirst, ToolCommitState::NotStarted)
                }
                ordivon_runtime_core::RuntimeErrorCode::ConcurrencyLimit => {
                    match capacity_scope.as_deref() {
                        // The target Workspace itself holds the single-writer slot.
                        // The Agent must observe the holder Job, re-observe the
                        // Workspace, reassess the original intent, then submit a
                        // fresh request: the state basis may have moved by then.
                        Some("workspace") => (
                            ToolRetryClass::ObserveThenReassess,
                            ToolCommitState::NotStarted,
                        ),
                        // Another Workspace consumed the global capacity pool.
                        // The target Workspace has no active writer; the same
                        // request may be retried after capacity frees.
                        Some("global") => {
                            (ToolRetryClass::WaitThenRetry, ToolCommitState::NotStarted)
                        }
                        _ => (ToolRetryClass::SafeSameRequest, ToolCommitState::NotStarted),
                    }
                }
                ordivon_runtime_core::RuntimeErrorCode::DeploymentInProgress
                | ordivon_runtime_core::RuntimeErrorCode::RegistryBusy
                | ordivon_runtime_core::RuntimeErrorCode::WorkspaceBusy => {
                    (ToolRetryClass::SafeSameRequest, ToolCommitState::NotStarted)
                }
                _ if error.retryable => (
                    ToolRetryClass::SafeSameRequest,
                    ToolCommitState::NotCommitted,
                ),
                _ => (ToolRetryClass::Never, ToolCommitState::NotCommitted),
            }
        };
        Self {
            code,
            message: error.message,
            context: Box::new(ToolErrorContext {
                field: error.field,
                origin: ToolErrorOrigin::RuntimeCore,
                retry_class,
                commit_state,
                retryable: if committed_operation {
                    false
                } else {
                    error.retryable
                },
                retry_after_ms: error.retry_after_ms,
                capacity: error.capacity,
                trace_id: None,
                operation_id: error.operation_id,
            }),
        }
    }
}

impl From<UniversalExecError> for ToolError {
    fn from(error: UniversalExecError) -> Self {
        let code = serde_json::to_value(&error.code)
            .ok()
            .and_then(|value| value.as_str().map(ToString::to_string))
            .unwrap_or_else(|| "UNIVERSAL_EXEC_ERROR".to_string());
        let mutation_outcome_unknown = matches!(
            error.code,
            ordivon_runtime_core::UniversalExecErrorCode::WorkspaceMutationIncomplete
        );
        Self {
            code,
            message: error.message,
            context: Box::new(ToolErrorContext {
                field: error.field,
                origin: ToolErrorOrigin::WorkspaceExecutor,
                retry_class: if mutation_outcome_unknown {
                    ToolRetryClass::ReconcileFirst
                } else if error.retryable {
                    ToolRetryClass::SafeSameRequest
                } else {
                    ToolRetryClass::Never
                },
                commit_state: if mutation_outcome_unknown {
                    ToolCommitState::Unknown
                } else {
                    ToolCommitState::NotCommitted
                },
                retryable: error.retryable,
                retry_after_ms: None,
                capacity: None,
                trace_id: None,
                operation_id: None,
            }),
        }
    }
}

#[derive(Clone, Debug, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ToolErrorEnvelope {
    pub error: ToolError,
}

#[derive(Clone, Debug)]
pub enum ToolOutcome<T> {
    Success(T),
    Error(ToolError),
}

impl<T: JsonSchema> JsonSchema for ToolOutcome<T> {
    fn inline_schema() -> bool {
        true
    }

    fn schema_name() -> Cow<'static, str> {
        Cow::Owned(format!("ToolOutcome_for_{}", T::schema_name()))
    }

    fn schema_id() -> Cow<'static, str> {
        Cow::Owned(format!("ordivon::ToolOutcome<{}>", T::schema_id()))
    }

    fn json_schema(generator: &mut SchemaGenerator) -> Schema {
        let success = generator.subschema_for::<T>();
        let error = generator.subschema_for::<ToolErrorEnvelope>();
        schemars::json_schema!({
            "oneOf": [success, error]
        })
    }
}

impl<T> IntoCallToolResult for ToolOutcome<T>
where
    T: Serialize + JsonSchema + Send + 'static,
{
    fn into_call_tool_result(self) -> Result<CallToolResponse, McpError> {
        let (ok, value, compatibility_text) = match self {
            Self::Success(result) => {
                let value = serde_json::to_value(result).map_err(|error| {
                    McpError::internal_error(format!("cannot serialize tool result: {error}"), None)
                })?;
                (true, value, "ok".to_string())
            }
            Self::Error(error) => {
                let compatibility_text = error.message.clone();
                (false, json!({ "error": error }), compatibility_text)
            }
        };
        let mut result = if ok {
            CallToolResult::success(Vec::new())
        } else {
            CallToolResult::error(vec![ContentBlock::text(compatibility_text)])
        };
        result.structured_content = Some(value);
        Ok(result.into())
    }
}

fn workspace_content_call_result(
    outcome: ToolOutcome<ordivon_runtime_core::WorkspaceContentReadResult>,
) -> Result<CallToolResult, McpError> {
    match outcome {
        ToolOutcome::Success(result) => {
            let structured = serde_json::to_value(&result.metadata).map_err(|error| {
                McpError::internal_error(
                    format!("cannot serialize workspace content metadata: {error}"),
                    None,
                )
            })?;
            let block = ContentBlock::image(
                BASE64_STANDARD.encode(&result.bytes),
                result.metadata.media_type.clone(),
            );
            let mut response = CallToolResult::success(vec![block]);
            response.structured_content = Some(structured);
            Ok(response)
        }
        ToolOutcome::Error(error) => {
            let message = error.message.clone();
            let structured = json!({ "error": error });
            let mut response = CallToolResult::error(vec![ContentBlock::text(message)]);
            response.structured_content = Some(structured);
            Ok(response)
        }
    }
}
