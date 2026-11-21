//! PostgreSQL Runtime Workspace identity, mutation and inventory.
//! Consumer-safe retirement is isolated in workspace/retirement.rs.
use super::*;
mod consumer_query;
mod effect_tx;
mod list;
mod mutation;
mod open;
mod readback;
mod retirement;
use consumer_query::workspace_consumer_sql;

#[cfg(test)]
mod workspace_active_consumer_tests;
#[cfg(test)]
mod workspace_lock_snapshot_tests;
