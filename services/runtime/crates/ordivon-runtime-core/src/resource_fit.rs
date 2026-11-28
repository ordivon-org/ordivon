//! Pure allocation predicate used by the PG resource transaction.
#[cfg(feature = "postgres-registry-admission")]
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
/// An opt-in storage-qualified allocation may share only with other
/// qualified allocations. Legacy jobs retain their existing behavior when
/// no qualified allocation is active. No missing estimate becomes zero.
#[cfg(feature = "postgres-registry-admission")]
pub(crate) fn combine_storage_peak(
    left: Option<u64>,
    right: Option<u64>,
) -> Result<Option<u64>, &'static str> {
    match (left, right) {
        (None, None) => Ok(None),
        (Some(a), Some(b)) if a != 0 && b != 0 => a
            .checked_add(b)
            .map(Some)
            .ok_or("storage commitment overflow"),
        _ => Err("incompatible or invalid storage commitment"),
    }
}

pub(crate) fn storage_fits(available: u64, floor: u64, reserved: u64) -> bool {
    floor
        .checked_add(reserved)
        .is_some_and(|required| required <= available)
}

#[cfg(all(test, feature = "postgres-registry-admission"))]
mod storage_tests {
    use super::*;

    #[test]
    fn storage_commitment_modes_are_symmetric_and_overflow_fails_closed() {
        assert_eq!(combine_storage_peak(None, None), Ok(None));
        assert_eq!(combine_storage_peak(Some(10), Some(10)), Ok(Some(20)));
        assert!(combine_storage_peak(None, Some(10)).is_err());
        assert!(combine_storage_peak(Some(10), None).is_err());
        assert!(combine_storage_peak(Some(0), Some(10)).is_err());
        assert!(combine_storage_peak(Some(u64::MAX), Some(1)).is_err());
    }

    #[test]
    fn concurrent_claims_cannot_each_consume_the_same_observed_space() {
        let gib = 1_u64 << 30;
        assert!(storage_fits(36 * gib, 20 * gib, 10 * gib));
        let committed = combine_storage_peak(Some(10 * gib), Some(10 * gib))
            .unwrap()
            .unwrap();
        assert!(!storage_fits(36 * gib, 20 * gib, committed));
        assert!(storage_fits(40 * gib, 20 * gib, committed));
        assert!(!storage_fits(u64::MAX, u64::MAX, 1));
        assert!(!storage_fits(19 * gib, 20 * gib, 0));
    }

    #[test]
    fn storage_arithmetic_matches_widened_oracle() {
        let values = [0, 1, 2, 16, 20, 36, u64::MAX - 1, u64::MAX];
        for available in values {
            for floor in values {
                for reserved in values {
                    assert_eq!(
                        storage_fits(available, floor, reserved),
                        (floor as u128 + reserved as u128) <= available as u128
                    );
                }
            }
        }
    }
}

#[cfg(all(kani, feature = "postgres-registry-admission"))]
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
