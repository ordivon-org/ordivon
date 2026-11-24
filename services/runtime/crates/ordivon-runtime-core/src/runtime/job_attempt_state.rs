//! Shared Job identity and Attempt lifecycle semantic contracts.
//! This facade exposes existing contract types without coupling their implementations.
mod identity;
mod lifecycle;
pub(crate) use identity::{JobIdentityContract, OperationIdentityBindings};
pub(crate) use lifecycle::AttemptLifecycleContract;

#[cfg(test)]
mod identity_tests;
#[cfg(kani)]
mod kani_lifecycle_contract_proofs;
#[cfg(test)]
mod lifecycle_tests;
