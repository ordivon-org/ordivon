use ordivon_kernel::{
    ActionClass, AuthorityToken, AuthorityValidationRequest, AuthorityVerifier, PolicyDecision,
};
use sqlx::{Postgres, Transaction};

use super::{db_err, enum_str, PostgresKernelStore};
use crate::LedgerError;

impl PostgresKernelStore {
    pub async fn revoke_authority(&self, jti: &str) -> Result<(), LedgerError> {
        sqlx::query(
            "INSERT INTO kernel_authority_revocations (jti, revoked_at)
                 VALUES ($1, now()) ON CONFLICT DO NOTHING",
        )
        .bind(jti)
        .execute(&self.pool)
        .await
        .map_err(db_err)?;
        Ok(())
    }

    pub async fn consume_authority(
        &self,
        request: AuthorityValidationRequest<'_>,
    ) -> Result<(), LedgerError> {
        let mut tx = self.pool.begin().await.map_err(db_err)?;
        consume_authority_tx(
            &mut tx,
            AuthorityConsumeRequest {
                token: request.token,
                verifier: request.verifier,
                intent_id: request.intent_id,
                obligation_id: request.obligation_id,
                action_class: request.action_class,
                target_ref: request.target_ref,
                policy_hash: request.policy_hash,
                idempotency_key: request.idempotency_key,
                now: request.now,
                policy_decision: request.policy_decision,
            },
        )
        .await?;
        tx.commit().await.map_err(db_err)?;
        Ok(())
    }
}

pub(super) struct AuthorityConsumeRequest<'a> {
    pub token: &'a AuthorityToken,
    pub verifier: &'a AuthorityVerifier,
    pub intent_id: &'a str,
    pub obligation_id: &'a str,
    pub action_class: &'a ActionClass,
    pub target_ref: &'a str,
    pub policy_hash: &'a str,
    pub idempotency_key: &'a str,
    pub now: &'a str,
    pub policy_decision: PolicyDecision,
}

pub(super) async fn consume_authority_tx(
    tx: &mut Transaction<'_, Postgres>,
    request: AuthorityConsumeRequest<'_>,
) -> Result<(), LedgerError> {
    if sqlx::query("SELECT 1 FROM kernel_authority_revocations WHERE jti = $1")
        .bind(request.token.jti())
        .fetch_optional(&mut **tx)
        .await
        .map_err(db_err)?
        .is_some()
    {
        return Err(LedgerError::Authority(
            ordivon_kernel::AuthorityError::RevokedToken {
                jti: request.token.jti().to_string(),
            },
        ));
    }

    let mut in_memory = ordivon_kernel::AuthorityUseLedger::default();
    in_memory
        .validate_and_consume(AuthorityValidationRequest {
            token: request.token,
            verifier: request.verifier,
            intent_id: request.intent_id,
            obligation_id: request.obligation_id,
            action_class: request.action_class,
            target_ref: request.target_ref,
            policy_hash: request.policy_hash,
            idempotency_key: request.idempotency_key,
            now: request.now,
            policy_decision: request.policy_decision,
        })
        .map_err(LedgerError::Authority)?;

    let result = sqlx::query(
        "INSERT INTO kernel_authority_uses
             (jti, intent_id, obligation_id, action_class, target_ref, idempotency_key, used_at)
             VALUES ($1,$2,$3,$4,$5,$6,$7)
             ON CONFLICT DO NOTHING",
    )
    .bind(request.token.jti())
    .bind(request.intent_id)
    .bind(request.obligation_id)
    .bind(enum_str(request.action_class))
    .bind(request.target_ref)
    .bind(request.idempotency_key)
    .bind(request.now)
    .execute(&mut **tx)
    .await
    .map_err(db_err)?;
    if result.rows_affected() == 0 {
        return Err(LedgerError::Authority(
            ordivon_kernel::AuthorityError::ReplayedToken {
                jti: request.token.jti().to_string(),
            },
        ));
    }
    Ok(())
}
