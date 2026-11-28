//! Durable pending work, atomic native allocation and fair dispatch.
//! PostgreSQL transaction authority, native capacity, fairness, observations,
//! and the scheduler's wake loop are distinct capabilities.
use super::*;
mod allocation;
mod dispatch;
mod failure_policy;
mod issue_writer;
mod native_capacity;
mod policy;
mod readback;
mod worker;
pub(super) use policy::scheduling_readback;
#[cfg(test)]
mod scheduler_candidate_tests;
#[cfg(test)]
use crate::resource_scheduling::{
    NodeResources, ResourceRequest, ResourceScheduling, WorkspaceAccess,
};
#[cfg(test)]
use failure_policy::{decode_accepted_candidate, is_job_scoped_reconciliation_error};
#[cfg(test)]
use native_capacity::{native_resource_error, unspent_native_allocation};
#[cfg(test)]
use policy::{next_candidate, PendingCandidate, SchedulerPreflight};
#[cfg(test)]
use std::collections::BTreeMap;

// A current Attempt belongs to exactly one Job. The schema does not enforce
// uniqueness of jobs.current_attempt_id, so bind both identities at the query
// boundary instead of trusting a potentially stale/corrupted pointer.
const PENDING_JOBS_SQL: &str = "SELECT j.job_id,j.principal,j.execution_plan_json,a.attempt_id FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id WHERE j.resolution IS NULL AND j.desired_state='run' AND a.state='accepted' AND NOT EXISTS(SELECT 1 FROM job_runtime_release_effects r WHERE r.job_id=j.job_id) ORDER BY j.created_at_ms,j.job_id";

// Bind the grant and its readback to the same Job/Attempt subject. A
// historical Allocation remains a resource root, but it cannot certify a
// different current Attempt. Missing rows in the locked claim are errors.
const LOCKED_CLAIMABLE_ATTEMPT_SQL: &str = "SELECT a.state='accepted' AND j.desired_state='run' AND j.resolution IS NULL AND j.current_attempt_id IS NOT DISTINCT FROM a.attempt_id FROM attempts a JOIN jobs j ON j.job_id=a.job_id WHERE a.attempt_id=$1 AND j.job_id=$2 FOR UPDATE OF a,j";
const CONFIRMED_CURRENT_ALLOCATION_SQL: &str = "SELECT EXISTS(SELECT 1 FROM job_allocations x JOIN attempts a ON a.attempt_id=x.attempt_id JOIN jobs j ON j.job_id=a.job_id AND j.current_attempt_id=a.attempt_id WHERE j.job_id=$1 AND a.attempt_id=$2 AND x.state='active')";

const SCHEDULING_READBACK_SQL: &str = "SELECT j.execution_plan_json,a.state,EXISTS(SELECT 1 FROM job_allocations x WHERE x.attempt_id=a.attempt_id AND x.state='active'),j.desired_state,j.resolution,CASE WHEN a.state='accepted' AND j.desired_state='run' AND j.resolution IS NULL THEN EXISTS(SELECT 1 FROM job_events e WHERE e.job_id=j.job_id AND e.attempt_id=a.attempt_id AND e.event_type='SCHEDULER_ISSUE') ELSE false END FROM jobs j LEFT JOIN attempts a ON a.attempt_id=COALESCE(j.current_attempt_id,(SELECT last.attempt_id FROM attempts last WHERE last.job_id=j.job_id ORDER BY last.attempt_number DESC LIMIT 1)) AND a.job_id=j.job_id WHERE j.job_id=$1";
