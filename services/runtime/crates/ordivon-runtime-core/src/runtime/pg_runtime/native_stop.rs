//! Existing systemd/native-stop logical boundary: exact InvocationID then kernel cgroup truth.
//! Hold/LOST proof cannot trigger OS signaling, new issuer, or an extra PG transaction.
mod decision;
mod invocation;
pub(super) use decision::{decide_native_stop, NativeStopDecision};
pub(super) use invocation::failed_unit_matches_runner;

#[cfg(kani)]
mod proof;
#[cfg(test)]
mod tests;
