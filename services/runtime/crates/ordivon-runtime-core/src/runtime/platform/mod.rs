//! Native platform realization boundary for Runtime physical supervision.
//!
//! Job/Attempt truth stays in the existing PG or legacy engine. Platform modules own OS process
//! supervision and evidence mechanics. This R2 slice moves Linux systemd/cgroup
//! realization behind this boundary without changing execution semantics. Some
//! shared path validation is still used by the Windows Core build. Linux-only
//! kernel witnesses fail closed on Windows; this is not a Windows PG writer or
//! a Windows process-tree supervisor. The native Windows launcher remains in
//! runtime::windows until its PG consumer is implemented and verified.

pub(crate) mod linux;

pub(crate) use linux::*;
