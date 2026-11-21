//! Durable pending work, atomic native allocation and fair dispatch.
//! Logic policy and physical resource observation live in separate modules.
use super::*;
mod claim;
mod failure_policy;
mod issue_writer;
mod native_capacity;
mod policy;
mod projection;
mod queue;
#[cfg(test)]
mod scheduler_candidate_tests;
mod worker;
use crate::resource_scheduling::{
    NodeResources, ResourceRequest, ResourceScheduling, WorkspaceAccess,
};
#[cfg(test)]
use failure_policy::{decode_accepted_candidate, is_job_scoped_reconciliation_error};
#[cfg(test)]
use native_capacity::{native_resource_error, unspent_native_allocation};
pub(super) use policy::scheduling_readback;
#[cfg(test)]
use policy::{next_candidate, PendingCandidate, SchedulerPreflight};
use std::collections::{BTreeMap, BTreeSet};
