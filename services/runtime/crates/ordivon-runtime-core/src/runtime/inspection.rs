use rusqlite::{params, Connection, OpenFlags};
use std::collections::BTreeMap;
use std::path::PathBuf;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use super::inspection_contract::*;
use super::registry::{CONDITION_RETIREMENT_MIGRATION_VERSION, MAX_MIGRATION_VERSION};
use super::registry_storage::RegistryStorageBoundary;
#[cfg(feature = "operator-tools")]
use super::{AttemptState, JobResolution};
use super::{
    ReservationState, RuntimeError, RuntimeErrorCode, RuntimeExecutionPlan, RuntimeResult,
};
#[cfg(feature = "operator-tools")]
use serde::Serialize;

pub(crate) const RUNTIME_INSPECTION_SCHEMA_VERSION: u32 = 2;
const MAX_INSPECTION_ATTEMPTS: u32 = 32;

#[derive(Clone, Debug)]
pub struct RuntimeInspectionConfig {
    pub db_path: PathBuf,
    pub busy_timeout_ms: u64,
}

include!("inspection/job.rs");
#[cfg(feature = "operator-tools")]
include!("inspection/operator.rs");

#[cfg(all(test, feature = "operator-tools"))]
#[path = "inspection/summary_query_tests.rs"]
mod summary_query_tests;
