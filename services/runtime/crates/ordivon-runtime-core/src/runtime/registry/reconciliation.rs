impl Registry {
    pub(super) fn record_reconciliation_failure(
        &self,
        attempt: &AttemptRecord,
        error: &RuntimeError,
        observed_at_ms: u64,
    ) -> RuntimeResult<()> {
        let reason_code = error.code.as_str();
        let evidence_digest = sha256_bytes(
            format!(
                "runtime-reconciliation-failure\0{}\0{}\0{}",
                attempt.attempt_id, reason_code, error.message
            )
            .as_bytes(),
        );
        let mut connection = self.open_connection()?;
        let existing: Option<(bool, String, String)> = connection
            .query_row(
                "SELECT recovery_required,recovery_reason_code,recovery_evidence_digest FROM attempts WHERE attempt_id=?1 AND recovery_required IS NOT NULL",
                [&attempt.attempt_id],
                |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot inspect recovery state"))?;
        if existing.as_ref().is_some_and(|(active, reason, evidence)| {
            *active && reason == reason_code && evidence == &evidence_digest
        }) {
            return Ok(());
        }

        let transaction = immediate(&mut connection, "reconciliation failure transaction")?;
        let current = load_attempt(&transaction, &attempt.attempt_id)?;
        transaction
            .execute(
                "UPDATE attempts SET recovery_required=1,recovery_reason_code=?1,recovery_evidence_digest=?2,recovery_observed_at_ms=?3 WHERE attempt_id=?4",
                params![reason_code, evidence_digest, observed_at_ms, current.attempt_id],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot record recovery state"))?;
        append_event(
            &transaction,
            &current.job_id,
            Some(&current.attempt_id),
            "RECONCILIATION_FAILED",
            "SYSTEM_OBSERVED",
            Some(current.state),
            None,
            reason_code,
            serde_json::json!({
                "message": error.message,
                "field": error.field,
                "retryable": error.retryable,
            }),
            observed_at_ms,
        )?;
        transaction
            .commit()
            .map_err(|error| RuntimeError::from_sql(error, "cannot commit reconciliation failure"))
    }

    pub(super) fn clear_reconciliation_failure(
        &self,
        attempt_id: &str,
        observed_at_ms: u64,
    ) -> RuntimeResult<()> {
        let mut connection = self.open_connection()?;
        let recovery_required: Option<bool> = connection
            .query_row(
                "SELECT recovery_required FROM attempts WHERE attempt_id=?1 AND recovery_required IS NOT NULL",
                [attempt_id],
                |row| row.get(0),
            )
            .optional()
            .map_err(|error| RuntimeError::from_sql(error, "cannot inspect recovery state"))?;
        if recovery_required != Some(true) {
            return Ok(());
        }

        let transaction = immediate(&mut connection, "reconciliation success transaction")?;
        let current = load_attempt(&transaction, attempt_id)?;
        let evidence_digest = sha256_bytes(
            format!("runtime-reconciliation-converged\0{attempt_id}\0{observed_at_ms}").as_bytes(),
        );
        let changed = transaction
            .execute(
                "UPDATE attempts SET recovery_required=0,recovery_reason_code='RECONCILIATION_CONVERGED',recovery_evidence_digest=?1,recovery_observed_at_ms=?2 WHERE attempt_id=?3 AND recovery_required=1",
                params![evidence_digest, observed_at_ms, attempt_id],
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot clear recovery condition"))?;
        if changed > 0 {
            append_event(
                &transaction,
                &current.job_id,
                Some(&current.attempt_id),
                "RECONCILIATION_CONVERGED",
                "SYSTEM_OBSERVED",
                Some(current.state),
                Some(current.state),
                "RECONCILIATION_CONVERGED",
                serde_json::json!({}),
                observed_at_ms,
            )?;
        }
        transaction
            .commit()
            .map_err(|error| RuntimeError::from_sql(error, "cannot commit reconciliation success"))
    }

    #[cfg(test)]
    pub(super) fn active_reservation_count(&self) -> RuntimeResult<u32> {
        let connection = self.open_connection()?;
        connection
            .query_row(
                "SELECT COUNT(*) FROM concurrency_reservations WHERE state IN ('active','held_orphaned')",
                [],
                |row| row.get(0),
            )
            .map_err(|error| RuntimeError::from_sql(error, "cannot count active reservations"))
    }
}
