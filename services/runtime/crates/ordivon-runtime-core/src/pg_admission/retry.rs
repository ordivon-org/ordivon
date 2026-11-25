//! PostgreSQL admission owner: retry.

// Only a server-confirmed SQLSTATE 40001 COMMIT failure establishes a
// rolled-back database-only transaction. Other COMMIT errors (including
// connection loss) are still UNKNOWN; a caller with physical effects must
// not use this helper to infer that the effects did not happen.
pub(super) fn commit_admission_transaction(
    tx: postgres::Transaction<'_>,
) -> Result<(), super::PgAdmissionError> {
    tx.commit().map_err(|error| {
        if error.code() == Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE) {
            super::PgAdmissionError::Database(error)
        } else {
            super::PgAdmissionError::UnknownCommit
        }
    })
}

// Only retry a server-confirmed, fully aborted SERIALIZABLE transaction.
// An uncertain COMMIT or an external process effect is never eligible.
const MAX_ABORTED_TRANSACTION_ATTEMPTS: u32 = 8;
pub(crate) fn retry_aborted_transaction<T, E>(
    mut transaction: impl FnMut() -> Result<T, E>,
    is_serialization_abort: impl Fn(&E) -> bool,
    mut wait: impl FnMut(std::time::Duration),
) -> Result<T, E> {
    for attempt in 0..MAX_ABORTED_TRANSACTION_ATTEMPTS {
        match transaction() {
            Err(ref e)
                if is_serialization_abort(e) && attempt + 1 < MAX_ABORTED_TRANSACTION_ATTEMPTS =>
            {
                // 4,8,16,32,64,64,64ms; each retry re-enters the whole transaction.
                wait(std::time::Duration::from_millis(4_u64 << attempt.min(4)));
            }
            result => return result,
        }
    }
    unreachable!("last bounded attempt must return")
}
#[cfg(test)]
mod serializable_retry_tests {
    use super::*;
    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum Fault {
        Aborted,
        UnknownCommit,
        Other,
    }
    #[test]
    fn retries_complete_aborts_but_not_unknown_commit_or_other_errors() {
        let mut attempts = 0;
        let mut delays = Vec::new();
        let outcome = retry_aborted_transaction(
            || {
                attempts += 1;
                if attempts < 3 {
                    Err(Fault::Aborted)
                } else {
                    Ok(attempts)
                }
            },
            |e| *e == Fault::Aborted,
            |d| delays.push(d.as_millis() as u64),
        );
        assert_eq!(outcome, Ok(3));
        assert_eq!(delays, [4, 8]);
        for e in [Fault::UnknownCommit, Fault::Other] {
            let mut count = 0;
            let r: Result<(), Fault> = retry_aborted_transaction(
                || {
                    count += 1;
                    Err(e)
                },
                |e| *e == Fault::Aborted,
                |_| panic!("must never retry unknown or unrelated errors"),
            );
            assert_eq!(r, Err(e));
            assert_eq!(count, 1);
        }
    }
    #[test]
    fn bounded_exhaustion_preserves_serialization_error() {
        let mut count = 0;
        let mut delays = Vec::new();
        let r: Result<(), Fault> = retry_aborted_transaction(
            || {
                count += 1;
                Err(Fault::Aborted)
            },
            |e| *e == Fault::Aborted,
            |d| delays.push(d.as_millis() as u64),
        );
        assert_eq!(r, Err(Fault::Aborted));
        assert_eq!(count, 8);
        assert_eq!(delays, [4, 8, 16, 32, 64, 64, 64]);
    }
}
