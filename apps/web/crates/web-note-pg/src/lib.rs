//! Native async Note persistence candidate. Not an HTTP/authentication API.
//! Local Unix socket only; bounded mature pool; uncertain carriers discarded.
mod domain;
mod error;
mod pool;
mod postgres;
pub use domain::{Note, NoteObservation, NoteState, PreparedNote};
pub use error::NoteError;
pub use pool::PoolLimits;
pub use postgres::PgNoteStore;
