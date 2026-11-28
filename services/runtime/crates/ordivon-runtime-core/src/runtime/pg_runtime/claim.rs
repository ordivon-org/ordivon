//! The Runtime PG database is the sole physical Workspace owner.
//! Harness may be in a different PostgreSQL database; a matching numeric
//! advisory lock in that database is NOT a Workspace close fence.
use super::*;

mod admission;
mod contract;
mod lifecycle;
mod persistence;

#[cfg(test)]
use contract::validate_key;
pub use contract::{
    WorkspaceClaimKeyRequest, WorkspaceClaimProjection, WorkspaceClaimReserveRequest,
};

#[cfg(test)]
mod claim_contract_tests;
#[cfg(all(test, target_os = "linux"))]
mod claim_physical_pg_tests;
