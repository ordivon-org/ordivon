//! Execution provider interface: guarantee validation and Linux realization live in
//! separate typed Rust modules. Runtime owns the fixed provider selection.
mod contract;
mod linux;
#[cfg(test)]
mod local_linux_adapter_tests;
#[cfg(test)]
mod tests;

pub(crate) use linux::{LocalLinuxProvider, LocalLinuxRealizationInputs};
