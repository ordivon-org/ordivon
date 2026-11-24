//! Pure allocation predicate used by the PG resource transaction.
pub(crate) fn fits(
    cpu_used: u64,
    cpu_request: u64,
    cpu_capacity: u64,
    memory_request: u64,
    memory_free: u64,
    pids_request: u64,
    pids_free: u64,
) -> bool {
    cpu_used
        .checked_add(cpu_request)
        .is_some_and(|sum| sum <= cpu_capacity)
        && memory_request <= memory_free
        && pids_request <= pids_free
}
#[cfg(kani)]
mod proof {
    #[kani::proof]
    fn allocation_never_exceeds_observed_supply() {
        let used: u64 = kani::any();
        let request: u64 = kani::any();
        let cap: u64 = kani::any();
        let memory: u64 = kani::any();
        let free: u64 = kani::any();
        let pids: u64 = kani::any();
        let pfree: u64 = kani::any();
        let accepted = super::fits(used, request, cap, memory, free, pids, pfree);
        let specification =
            (used as u128 + request as u128) <= cap as u128 && memory <= free && pids <= pfree;
        assert_eq!(accepted, specification);
        kani::cover!(accepted);
        kani::cover!(!accepted);
        kani::cover!(used == u64::MAX && request > 0);
    }
}
