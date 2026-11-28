//! Original native Workspace file mutation contract, composable and private.
mod intent;
mod physical;
mod prepare;
mod slice;

pub(crate) use intent::ensure_workspace_mutation_quiescent;
pub use prepare::mutate_workspace;
pub(crate) use slice::read_workspace_slice;
