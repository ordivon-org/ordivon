//! PG-native read-only ReleaseEffect projection.
//!
//! PostgreSQL is the only admission authority for this Runtime. The SQLite
//! Runtime's release *reader* is reusable only at the type/receipt-contract
//! level; its release storage and migration hooks are not PG authority.
//! This module does not admit, dispatch, or install any release.
use super::*;

mod admission;
mod observation;
mod qualification;
mod replay;
