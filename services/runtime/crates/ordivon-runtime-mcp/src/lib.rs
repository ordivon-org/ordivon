//! MCP transport, authentication, schemas, and Runtime projection for Ordivon.
//!
//! Execution, persistence, process ownership, cancellation, result, Artifact,
//! capacity, and reconciliation semantics remain in `ordivon-runtime-core`.

#[cfg(feature = "legacy-runtime")]
pub mod server;
#[cfg(all(
    feature = "postgres-runtime",
    not(feature = "legacy-runtime"),
    any(target_os = "linux", windows)
))]
#[path = "server/pg_only.rs"]
pub mod server;
pub mod trace;

pub use trace::{append_rotating_jsonl, rotated_trace_path, DEFAULT_TRACE_ROTATION_BYTES};
