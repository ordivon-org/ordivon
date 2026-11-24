//! PostgreSQL Artifact identity and resource/text read capability composition.
mod content;
mod identity;
mod pagination;
mod text;

use super::*;
use identity::{read_bound_pg_artifact_registration, require_pg_artifact_identity};
use pagination::artifact_utf8_window;

#[cfg(test)]
mod utf8_artifact_progress_tests;
