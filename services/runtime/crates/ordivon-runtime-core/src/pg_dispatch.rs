//! Original PG dispatch stages as real Rust modules.
//! Small facade is a live #[path] consumer in pg_admission, not a file-shaped test.
#[path = "pg_dispatch/attempt_lock.rs"]
mod attempt_lock;
#[path = "pg_dispatch/bundle_ready.rs"]
mod bundle_ready;
#[path = "pg_dispatch/dispatch_issued.rs"]
mod dispatch_issued;
#[path = "pg_dispatch/event.rs"]
mod event;
#[path = "pg_dispatch/issued_spawn.rs"]
mod issued_spawn;
#[path = "pg_dispatch/native_prehandoff.rs"]
mod native_prehandoff;
#[path = "pg_dispatch/qualification.rs"]
mod qualification;
#[path = "pg_dispatch/runner_bound.rs"]
mod runner_bound;
#[path = "pg_dispatch/types.rs"]
mod types;

#[cfg(test)]
#[path = "pg_dispatch/physical_tests.rs"]
mod physical_tests;

pub(crate) use issued_spawn::PgIssuedHarnessSpawn;
pub(crate) use types::PgRunnerBound;
pub use types::{PgBundleReady, PgDispatchIssued};
