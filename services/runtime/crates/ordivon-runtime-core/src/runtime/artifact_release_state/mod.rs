//! Distinct Artifact and Runtime Release contracts, composed for existing callers.
//! This module exports stable behavior; the file layout is not part of the contract.
mod artifact;
mod receipt;
mod release;
#[cfg(test)]
mod tests;
mod validation;

pub(crate) use artifact::ArtifactStateContract;
pub(crate) use release::ReleaseStateContract;
