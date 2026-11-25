//! Native async Note persistence candidate. Not an HTTP/authentication API.
//! Local Unix socket only; bounded mature pool; uncertain carriers discarded.
mod domain;
pub mod effect;
mod error;
pub mod migration;
mod pool;
mod postgres;
pub use domain::{Note, NoteObservation, NoteState, PreparedNote};
pub use error::NoteError;
pub use pool::PoolLimits;
pub use postgres::PgNoteStore;
