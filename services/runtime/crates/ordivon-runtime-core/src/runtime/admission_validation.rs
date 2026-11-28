//! Storage-neutral request validation for current PG and still-consumed legacy Runtime.
//! Policy does not own PostgreSQL transactions, Jobs, or operating-system effects.
mod environment;
mod limits;
mod observation;
mod proposal;
mod request;

pub(super) use limits::{effective_limits_from_plan_json, validate_new_admission_policy};
pub(super) use observation::validate_observe_request;
#[cfg(feature = "postgres-registry-admission")]
pub(crate) use proposal::validate_resource_run_proposal_structure;
pub(super) use proposal::validate_run_proposal_structure;
pub(super) use request::validate_run_request_structure;
