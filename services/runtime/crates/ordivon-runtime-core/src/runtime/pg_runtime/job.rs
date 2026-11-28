//! PostgreSQL Runtime Job admission, observation, and projection.
//! Physical cancellation is an independent use-case in job/cancellation.rs.
use super::*;
mod cancellation;
mod event_projection;

// Direct PostgreSQL Client reads must not erase SQLSTATE through io(Display).
// Keep the one shared PgAdmissionError taxonomy used by Recovery and admission.
fn pg_read_error(error: postgres::Error) -> RuntimeError {
    pg(PgAdmissionError::Database(error))
}

// Once PG has durably admitted this Job (including an exact idempotent replay),
// a later observation failure cannot retract the committed operation identity.
// The existing MCP error projection uses this witness to demand reconciliation
// instead of falsely reporting commitState=not_committed.
fn preserve_committed_job_identity<T>(
    job_id: &str,
    observed: RuntimeResult<T>,
) -> RuntimeResult<T> {
    observed.map_err(|error| error.with_operation_id(job_id))
}

/// The first observation follows a committed PG Job admission. SQLSTATE
/// serialization aborts may invalidate its read/runner reconciliation, not
/// the already-committed Job identity. Re-observe that SAME Job only; no
/// second admission or new external operation is allowed. Reuse the PG
/// admission module's proven bounded aborted-transaction backoff.
fn observe_committed_job_with_bounded_busy_recovery<T>(
    job_id: &str,
    observe: impl FnMut() -> RuntimeResult<T>,
) -> RuntimeResult<T> {
    let result = crate::pg_admission::retry_aborted_transaction(
        observe,
        |error| error.code == RuntimeErrorCode::RegistryBusy && error.retryable,
        std::thread::sleep,
    );
    preserve_committed_job_identity(job_id, result)
}

/// A direct job.observe already has a PG-authorized, durable Job identity.
/// A serializable reconciliation transaction can abort while the native OS
/// launch is still in flight. Never retry the reconciliation/effect itself on
/// that error: inspect the SAME existing Job read-only with the native bounded
/// SQLSTATE 40001/40P01 recovery instead. A starting/unknown projection is
/// not a terminal witness and does not authorize a new physical dispatch.
fn project_committed_job_after_reconcile<T>(
    job_id: &str,
    reconciliation: RuntimeResult<()>,
    project: impl FnMut() -> RuntimeResult<T>,
) -> RuntimeResult<T> {
    match reconciliation {
        Ok(()) => {}
        Err(error) if error.code == RuntimeErrorCode::RegistryBusy && error.retryable => {
            // Only the definitely aborted DB transaction is retryable.
            // Retain the possibly issued physical effect exactly once.
        }
        Err(error) => return Err(error.with_operation_id(job_id)),
    }
    observe_committed_job_with_bounded_busy_recovery(job_id, project)
}

// Keep platform admission a closed, testable contract. A Windows PG
// product must not accept Unix-only profiles, steps or host prerequisites
// before the native carrier can realize them.
pub(super) fn supports_native_pg_execution(e: &ExecutionProposal, windows: bool) -> bool {
    if windows {
        e.execution_target == ExecutionTarget::WindowsNative
            && e.execution_profile == ExecutionProfile::TrustedLocal
            && e.steps.is_empty()
            && e.host_dependencies.is_empty()
    } else {
        e.execution_target == ExecutionTarget::LocalLinux
            && matches!(
                e.execution_profile,
                ExecutionProfile::TrustedLocal | ExecutionProfile::ContainedLocal
            )
            && e.windows_context.is_none()
            && e.windows_authority == WindowsAuthority::Limited
    }
}

#[cfg(test)]
mod native_pg_target_contract_tests {
    use super::*;

    #[test]
    fn platform_target_profile_and_native_context_are_closed() {
        let mut e: ExecutionProposal = serde_json::from_value(json!({
            "workspaceId":"native-contract", "executable":"C:/Windows/System32/cmd.exe",
            "cwdRelative":".", "executionTarget":"windows_native",
            "executionProfile":"trusted_local", "windowsAuthority":"active_user"
        }))
        .unwrap();
        assert!(supports_native_pg_execution(&e, true));
        assert!(!supports_native_pg_execution(&e, false));
        e.execution_profile = ExecutionProfile::ContainedLocal;
        assert!(!supports_native_pg_execution(&e, true));
        e.execution_target = ExecutionTarget::LocalLinux;
        e.windows_authority = WindowsAuthority::Limited;
        assert!(supports_native_pg_execution(&e, false));
        assert!(!supports_native_pg_execution(&e, true));
        e.execution_profile = ExecutionProfile::TrustedLocal;
        assert!(supports_native_pg_execution(&e, false));
        e.windows_authority = WindowsAuthority::ActiveUser;
        assert!(!supports_native_pg_execution(&e, false));
    }
}

mod environment;
mod ingress_policy;
use environment::{pg_contained_workspace_environment, pg_workspace_tool_environment};
use ingress_policy::{authorize_new_execution_profile, preserve_qualified_issuer_environment};

mod admission;
mod observation;
mod readback;

#[cfg(test)]
mod committed_observation_tests {
    use super::*;

    #[test]
    fn postcommit_busy_observation_recovers_same_job_without_new_admission() {
        let mut observations = 0_u32;
        let result = observe_committed_job_with_bounded_busy_recovery("job-stable", || {
            observations += 1;
            if observations < 3 {
                Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryBusy,
                    "aborted serializable post-admission PG observation",
                    None,
                    true,
                ))
            } else {
                Ok("observed-existing-job")
            }
        })
        .unwrap();
        assert_eq!(result, "observed-existing-job");
        assert_eq!(observations, 3);

        let mut unknown_attempts = 0_u32;
        let failed: RuntimeResult<()> =
            observe_committed_job_with_bounded_busy_recovery("job-stable", || {
                unknown_attempts += 1;
                Err(RuntimeError::new(
                    RuntimeErrorCode::DispatchOutcomeUnknown,
                    "external effect outcome is unknown",
                    None,
                    false,
                ))
            });
        assert_eq!(
            unknown_attempts, 1,
            "never retry an ambiguous physical effect"
        );
        assert_eq!(
            failed.unwrap_err().operation_id.as_deref(),
            Some("job-stable")
        );

        let mut nonretryable_busy_reads = 0_u32;
        let refused: RuntimeResult<()> =
            observe_committed_job_with_bounded_busy_recovery("job-stable", || {
                nonretryable_busy_reads += 1;
                Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryBusy,
                    "not a proven aborted observation",
                    None,
                    false,
                ))
            });
        assert_eq!(nonretryable_busy_reads, 1);
        assert_eq!(
            refused.unwrap_err().operation_id.as_deref(),
            Some("job-stable")
        );

        let mut bounded_reads = 0_u32;
        let exhausted: RuntimeResult<()> =
            observe_committed_job_with_bounded_busy_recovery("job-stable", || {
                bounded_reads += 1;
                Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryBusy,
                    "serializable observation always aborted",
                    None,
                    true,
                ))
            });
        assert_eq!(
            bounded_reads, 8,
            "reuse the existing bounded PG retry budget"
        );
        let final_error = exhausted.unwrap_err();
        assert_eq!(final_error.code, RuntimeErrorCode::RegistryBusy);
        assert_eq!(final_error.operation_id.as_deref(), Some("job-stable"));
    }

    #[test]
    fn direct_observe_busy_reconciliation_only_projects_original_job() {
        let mut reads = 0;
        let value = project_committed_job_after_reconcile(
            "job-same-physical-identity",
            Err(RuntimeError::new(
                RuntimeErrorCode::RegistryBusy,
                "aborted PG reconciliation after possible OS handoff",
                None,
                true,
            )),
            || {
                reads += 1;
                if reads == 1 {
                    Err(RuntimeError::new(
                        RuntimeErrorCode::RegistryBusy,
                        "read-only projection also aborted once",
                        None,
                        true,
                    ))
                } else {
                    Ok("PG-existing-attempt-only")
                }
            },
        )
        .unwrap();
        assert_eq!(value, "PG-existing-attempt-only");
        assert_eq!(reads, 2, "recovery only repeats same-Job PG reads");

        for (code, retryable) in [
            (RuntimeErrorCode::DispatchOutcomeUnknown, false),
            (RuntimeErrorCode::RegistryBusy, false),
            (RuntimeErrorCode::ReconciliationRequired, false),
        ] {
            let mut read_count = 0;
            let refused: RuntimeResult<()> = project_committed_job_after_reconcile(
                "job-same-physical-identity",
                Err(RuntimeError::new(
                    code.clone(),
                    "physical effect or owner status is not proven safe",
                    None,
                    retryable,
                )),
                || {
                    read_count += 1;
                    Ok(())
                },
            );
            assert_eq!(read_count, 0, "must not mask an uncertain effect");
            let error = refused.unwrap_err();
            assert_eq!(error.code, code);
            assert_eq!(
                error.operation_id.as_deref(),
                Some("job-same-physical-identity")
            );
        }
        let mut observed = 0;
        project_committed_job_after_reconcile("job-committed", Ok(()), || {
            observed += 1;
            Ok(())
        })
        .unwrap();
        assert_eq!(observed, 1, "a successful reconciliation projects once");
    }

    #[test]
    fn post_admission_observation_error_keeps_committed_job_identity() {
        let failed: RuntimeResult<()> = Err(RuntimeError::new(
            RuntimeErrorCode::RegistryUnavailable,
            "serializable PG observation failed after Job admission",
            None,
            false,
        ));
        let error = preserve_committed_job_identity("job-exact", failed).unwrap_err();
        assert_eq!(error.operation_id.as_deref(), Some("job-exact"));
        assert_eq!(error.code, RuntimeErrorCode::RegistryUnavailable);
        assert_eq!(
            preserve_committed_job_identity("job-exact", Ok::<_, RuntimeError>(7)).unwrap(),
            7
        );
    }

    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN"]
    fn pg18_committed_observation_serialization_abort_retains_external_effect_once() {
        use postgres::IsolationLevel;
        use std::io::Write;

        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit disposable PostgreSQL server required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        let mut concurrent = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        let schema = format!(
            "observation_effect_{}_{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        );
        let table = format!("{schema}.witness");
        db.batch_execute(&format!(
            "CREATE SCHEMA {schema}; CREATE TABLE {table} (id int PRIMARY KEY, value int); INSERT INTO {table} VALUES (1, 0);"
        ))
        .unwrap();

        // Establish an earlier durable row and a serializable observation snapshot.
        let mut transaction = db
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()
            .unwrap();
        assert_eq!(
            transaction
                .query_one(&format!("SELECT value FROM {table} WHERE id=1"), &[])
                .unwrap()
                .get::<_, i32>(0),
            0
        );

        // A real external file effect is not part of either database transaction.
        let mut effect = tempfile::NamedTempFile::new().unwrap();
        effect.write_all(b"effect-once\n").unwrap();
        effect.as_file().sync_all().unwrap();
        concurrent
            .execute(&format!("UPDATE {table} SET value=1 WHERE id=1"), &[])
            .unwrap();
        let abort = transaction
            .execute(&format!("UPDATE {table} SET value=2 WHERE id=1"), &[])
            .unwrap_err();
        assert_eq!(
            abort.code(),
            Some(&postgres::error::SqlState::T_R_SERIALIZATION_FAILURE)
        );
        transaction.rollback().unwrap();

        let mut reads = 0;
        let observed = project_committed_job_after_reconcile(
            "job-external-effect-witness",
            Err(pg_read_error(abort)),
            || {
                reads += 1;
                let row = db
                    .query_one(&format!("SELECT value FROM {table} WHERE id=1"), &[])
                    .map_err(pg_read_error)?;
                Ok(row.get::<_, i32>(0))
            },
        )
        .unwrap();
        assert_eq!(
            observed, 1,
            "observe the committed competing value, not the aborted update"
        );
        assert_eq!(reads, 1);
        assert_eq!(std::fs::read(effect.path()).unwrap(), b"effect-once\n");
        db.batch_execute(&format!("DROP SCHEMA {schema} CASCADE"))
            .unwrap();
    }

    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN"]
    fn native_postgres_direct_job_queries_preserve_sqlstate_and_exact_operation_id() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit disposable PostgreSQL server required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        for (state, expected) in [
            ("40001", RuntimeErrorCode::RegistryBusy),
            ("40P01", RuntimeErrorCode::RegistryBusy),
            ("23505", RuntimeErrorCode::RegistryUnavailable),
        ] {
            let postgres_error = db
                .batch_execute(&format!(
                    "DO $$ BEGIN RAISE EXCEPTION SQLSTATE '{state}'; END $$;"
                ))
                .unwrap_err();
            let failed: RuntimeResult<()> = Err(pg_read_error(postgres_error));
            let observed =
                preserve_committed_job_identity("job-real-direct-PG", failed).unwrap_err();
            assert_eq!(observed.code, expected, "SQLSTATE {state}");
            assert_eq!(observed.operation_id.as_deref(), Some("job-real-direct-PG"));
            if expected == RuntimeErrorCode::RegistryBusy {
                assert!(observed.retryable);
                assert_eq!(observed.retry_after_ms, Some(250));
            } else {
                assert!(!observed.retryable);
            }
        }
        let mut observed = 0_u32;
        let qualified =
            observe_committed_job_with_bounded_busy_recovery("job-real-direct-PG", || {
                observed += 1;
                if observed == 1 {
                    let abort = db
                        .batch_execute("DO $$ BEGIN RAISE EXCEPTION SQLSTATE '40001'; END $$;")
                        .unwrap_err();
                    Err(pg_read_error(abort))
                } else {
                    Ok("the original committed Job")
                }
            })
            .unwrap();
        assert_eq!(observed, 2);
        assert_eq!(qualified, "the original committed Job");
    }
}
