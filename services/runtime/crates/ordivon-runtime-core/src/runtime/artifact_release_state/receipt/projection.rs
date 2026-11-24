use super::super::super::{AttemptState, RuntimeReleaseDisposition};

pub(crate) struct ReleaseReceiptProjection {
    pub(crate) disposition: RuntimeReleaseDisposition,
    pub(crate) terminal: bool,
    pub(crate) available: bool,
    pub(crate) digest: Option<String>,
    pub(crate) deployed_tool_count: Option<u32>,
    pub(crate) tool_catalog_digest: Option<String>,
    pub(crate) rollback_status: Option<String>,
    pub(crate) issue: Option<String>,
}

impl ReleaseReceiptProjection {
    pub(super) fn unresolved(attempt_state: Option<AttemptState>) -> Self {
        let admitted = attempt_state.is_some_and(|state| state == AttemptState::Accepted);
        Self {
            disposition: if admitted {
                RuntimeReleaseDisposition::Admitted
            } else {
                RuntimeReleaseDisposition::InProgress
            },
            terminal: false,
            available: false,
            digest: None,
            deployed_tool_count: None,
            tool_catalog_digest: None,
            rollback_status: None,
            issue: None,
        }
    }

    pub(super) fn reconciliation(issue: &str) -> Self {
        Self {
            disposition: RuntimeReleaseDisposition::ReconciliationRequired,
            terminal: false,
            available: false,
            digest: None,
            deployed_tool_count: None,
            tool_catalog_digest: None,
            rollback_status: None,
            issue: Some(issue.to_string()),
        }
    }
}
