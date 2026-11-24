//! Original Windows elevated-execution principal gate. Never a new credential issuer.
use super::AuthorityContract;
use crate::runtime::{
    ExecutionTarget, RuntimeError, RuntimeErrorCode, RuntimeResult, WindowsPayloadPrivilege,
};

impl AuthorityContract {
    pub(crate) fn authorize_windows_elevation(
        &self,
        allowed_principals: &[String],
    ) -> RuntimeResult<()> {
        if self.execution_target != ExecutionTarget::WindowsNative {
            return Ok(());
        }
        let context = self
            .windows_context
            .expect("Windows context is structurally required before authorization");
        if context.privilege != WindowsPayloadPrivilege::Elevated {
            return Ok(());
        }
        if allowed_principals
            .iter()
            .any(|principal| principal == &self.principal)
        {
            return Ok(());
        }
        Err(RuntimeError::new(
            RuntimeErrorCode::AuthorizationDenied,
            "authenticated principal is not authorized to request elevated Windows execution",
            Some("execution.windowsContext.privilege"),
            false,
        ))
    }
}
