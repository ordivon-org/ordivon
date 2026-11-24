//! Deterministic identity sets and Host Dependency exact digest ordering.
use crate::runtime::HostDependencyBinding;
use std::collections::BTreeSet;

pub(super) fn sorted_unique<'a>(values: impl Iterator<Item = &'a str>) -> Vec<String> {
    values
        .map(str::to_owned)
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect()
}

pub(super) fn sorted_host_dependencies(
    values: &[HostDependencyBinding],
) -> Vec<HostDependencyBinding> {
    let mut values = values.to_vec();
    values.sort_by(|left, right| {
        left.path
            .cmp(&right.path)
            .then_with(|| left.expected_digest.cmp(&right.expected_digest))
    });
    values.dedup();
    values
}
