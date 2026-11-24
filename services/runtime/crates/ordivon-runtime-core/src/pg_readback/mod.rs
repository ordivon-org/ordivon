//! Snapshot-bound PostgreSQL readback: query + lifecycle + event qualifications.
//! Does not create an execution effect or infer OS finality.
mod coherence;
mod query;
mod terminal_event;
#[cfg(test)]
mod tests;
mod types;

pub use types::{PgJobReadback, PgJobSnapshot};
