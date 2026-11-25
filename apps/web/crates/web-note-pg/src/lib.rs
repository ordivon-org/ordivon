//! Native async Note persistence candidate. Not an HTTP/authentication API.
//! Local Unix socket only; an isolated connection per call prevents a failed
//! or cancelled transaction being recycled. Pool/TLS qualification is separate.
mod domain;
mod error;
mod postgres;
pub use domain::{Note, NoteState};
pub use error::NoteError;
pub use postgres::PgNoteStore;
