//! Original config input obligations, including monotonic timeout and Unix-only ownership fields.
use super::{invalid, UniversalExecError, UniversalExecutorConfig};

impl UniversalExecutorConfig {
    pub fn validate(&self) -> Result<(), UniversalExecError> {
        if !self.store_root.is_absolute() {
            return Err(invalid("store root must be absolute", "storeRoot"));
        }
        if self
            .workspace_root
            .as_ref()
            .is_some_and(|path| !path.is_absolute())
        {
            return Err(invalid("workspace root must be absolute", "workspaceRoot"));
        }
        if self.workspace_uid.is_some() != self.workspace_gid.is_some() {
            return Err(invalid(
                "workspaceUid and workspaceGid must appear together",
                "workspaceUid",
            ));
        }
        #[cfg(not(unix))]
        if self.workspace_uid.is_some() {
            return Err(invalid(
                "workspaceUid/workspaceGid are Unix-only; native platform ownership must use its own state authority",
                "workspaceUid",
            ));
        }
        if self
            .runner_path
            .as_ref()
            .is_some_and(|runner| !runner.is_absolute())
        {
            return Err(invalid("runner path must be absolute", "runnerPath"));
        }
        if self.allowed_executable_roots.is_empty() {
            return Err(invalid(
                "at least one executable root is required",
                "allowedExecutableRoots",
            ));
        }
        if self
            .allowed_executable_roots
            .iter()
            .any(|root| !root.is_absolute())
        {
            return Err(invalid(
                "all executable roots must be absolute",
                "allowedExecutableRoots",
            ));
        }
        if self.max_runtime_ms == 0 {
            return Err(invalid("max runtime must be positive", "maxRuntimeMs"));
        }
        let dispatch_ceiling_ms = self
            .max_runtime_ms
            .checked_add(5_000)
            .ok_or_else(|| invalid("max runtime exceeds platform timer range", "maxRuntimeMs"))?;
        if std::time::Instant::now()
            .checked_add(std::time::Duration::from_millis(dispatch_ceiling_ms))
            .is_none()
        {
            return Err(invalid(
                "max runtime exceeds platform monotonic clock range",
                "maxRuntimeMs",
            ));
        }
        if self.max_output_bytes == 0 {
            return Err(invalid("max output must be positive", "maxOutputBytes"));
        }
        Ok(())
    }
}
