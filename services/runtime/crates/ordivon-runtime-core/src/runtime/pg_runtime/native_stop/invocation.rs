//! Native Runner identity requires the exact pre-committed systemd invocation and no live PID.
/// The cgroup v2 kernel allows removal of a cgroup only after it has become
/// empty. With verified Runner start, a collected/not-found systemd transient
/// unit AND its removed cgroup are a native terminal witness, distinct from
/// an unavailable cgroup.events read. A failed-but-loaded unit with the
/// *same verified Runner invocation*, no main PID and a removed cgroup is
/// also terminal: CollectMode=inactive deliberately preserves failed units
/// until after PostgreSQL commits the terminal result. Other loaded units
/// still require an observed recursive `populated=0` state.
///
/// This does not infer external effect success or allow a replacement Attempt.
pub(in crate::runtime::pg_runtime) fn failed_unit_matches_runner(
    load_state: Option<&str>,
    active_state: Option<&str>,
    invocation_id: Option<&str>,
    expected_invocation_id: &str,
    main_pid: Option<&str>,
) -> bool {
    !expected_invocation_id.is_empty()
        && load_state == Some("loaded")
        && active_state == Some("failed")
        && invocation_id == Some(expected_invocation_id)
        && main_pid == Some("0")
}
