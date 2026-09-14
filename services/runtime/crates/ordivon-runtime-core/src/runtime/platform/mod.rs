//! Native platform realization boundary for Runtime physical supervision.
//!
//! Shared Runtime semantics stay in Engine/Registry. Platform modules own OS-specific process
//! supervision and evidence mechanics. This R2 slice moves the existing Linux systemd/cgroup
//! realization behind this boundary without changing execution semantics. A native Windows
//! realization will be added independently rather than normalized into Linux concepts.

pub(crate) mod linux;

pub(crate) use linux::*;
