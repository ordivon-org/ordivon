//! Original PG Runtime observable capabilities: do not advertise a Linux contained execution
//! profile without the installed non-root native Runner owner.
use super::super::{error, io, universal, PgRuntime, RuntimeResult};
use serde_json::json;

impl PgRuntime {
    /// Advertise only capabilities implemented by this PostgreSQL-native entrypoint.
    #[cfg(not(windows))]
    pub fn describe(&self) -> RuntimeResult<serde_json::Value> {
        let runner = self
            .config
            .executor
            .runner_path
            .as_deref()
            .ok_or_else(|| error("native runner missing"))?;
        crate::runtime::platform::validate_runner(runner)?;
        let digest = universal::sha256_file(runner).map_err(io)?;
        // A working ordinary contained path requires the operator-owned
        // native Unix task identity. An unconfigured Runtime may still admit
        // trusted_local, but must not advertise unexecutable containment.
        let profiles = if matches!(
            (self.config.executor.workspace_uid, self.config.executor.workspace_gid),
            (Some(uid), Some(gid)) if uid != 0 && gid != 0
        ) {
            vec!["trusted_local", "contained_local"]
        } else {
            vec!["trusted_local"]
        };
        Ok(json!({
            "schemaVersion":1,
            "node":{"nodeId":"linux-pg","platform":"linux","native":true},
            "defaultRuntimeMs":30000,
            "maxRuntimeMs":self.config.executor.max_runtime_ms,
            "maxOutputBytes":self.config.executor.max_output_bytes,
            "allowedExecutableRoots":self.config.executor.allowed_executable_roots.iter()
                .map(|p|p.to_string_lossy().into_owned()).collect::<Vec<_>>(),
            "inputAuthorities":[],
            "credentialAuthorities":[],
            "inputIngressAuthorities":[],
            "credentialMaterializationBindings":[],
            "globalExecutionLimit":null,
            "scheduling":{"mode":"resource_aware_persistent_queue","node":crate::resource_scheduling::NodeResources::observe().ok(),"workspaceConcurrency":"access_leases","ownerFairness":"dominant_resource_share","requestsAreHardLimits":false,"defaultRequest":crate::resource_scheduling::ResourceRequest::default(),"memoryReserveFraction":0.05,"pressureTargets":{"cpuSomeAvg10":70,"memoryFullAvg10":5,"ioFullAvg10":40}},
            "structuredReleaseConfigured":false,
            "targets":[{
                "target":"local_linux","configured":true,"available":true,
                "executionProfiles":profiles,"structuredPlan":true,
                "immutableInputs":false,"hostDependencyCommitments":true,
                "hostDependencyContinuityScope":"runtime_host_namespace_path_witness",
                "executionProvider":{"contract":"local_linux_runner_v1","executableDigest":digest}
            }]
        }))
    }
}

#[cfg(windows)]
impl PgRuntime {
    /// Observational projection only: this does not authorize dispatch or certify
    /// the full product cutover. Use the same configured native launcher/token
    /// observations as the existing Windows Runtime, without opening SQLite.
    pub fn describe(&self) -> RuntimeResult<serde_json::Value> {
        use crate::runtime::{
            WindowsExecutionContextRequest, WindowsExecutionIdentity, WindowsPayloadPrivilege,
        };
        let runner = self
            .config
            .executor
            .runner_path
            .as_deref()
            .ok_or_else(|| error("native runner missing"))?;
        let mut supported = vec![WindowsExecutionContextRequest::new(
            WindowsExecutionIdentity::Service,
            WindowsPayloadPrivilege::Limited,
        )];
        let active = WindowsExecutionContextRequest::new(
            WindowsExecutionIdentity::ActiveUser,
            WindowsPayloadPrivilege::Limited,
        );
        if self.config.interactive_workspace_sid.is_some()
            && crate::runtime::windows::snapshot_windows_runtime_context_for(
                &self.config.windows,
                active,
            )
            .is_ok_and(|snap| {
                self.require_interactive_context(&snap.token_user_sid, snap.session_id)
                    .is_ok()
            })
        {
            supported.push(active);
        }
        let target = crate::runtime::windows::windows_pg_execution_target(
            &self.config.windows,
            runner,
            &supported,
        )?;
        Ok(json!({
            "schemaVersion":1,
            "node":{"nodeId":self.config.node_id,"platform":"windows","native":true},
            "defaultRuntimeMs":30000,"maxRuntimeMs":self.config.executor.max_runtime_ms,
            "maxOutputBytes":self.config.executor.max_output_bytes,
            "allowedExecutableRoots":self.config.executor.allowed_executable_roots.iter()
                .map(|p|p.to_string_lossy().into_owned()).collect::<Vec<_>>(),
            "inputAuthorities":[],"credentialAuthorities":[],"inputIngressAuthorities":[],
            "credentialMaterializationBindings":[],"globalExecutionLimit":null,
            "scheduling":{"mode":"resource_aware_persistent_queue","node":crate::resource_scheduling::NodeResources::observe().ok(),"workspaceConcurrency":"access_leases","ownerFairness":"dominant_resource_share","requestsAreHardLimits":false,"defaultRequest":crate::resource_scheduling::ResourceRequest::default()},
            "structuredReleaseConfigured":false,"targets":[target]
        }))
    }
}
