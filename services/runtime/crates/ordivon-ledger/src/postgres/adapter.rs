use ordivon_kernel::{
    compare_obligation, ActionClass, ActionSpec, AuthorityToken, AuthorityVerifier,
    ObservationStatus, ObservedEvent, PolicyDecision, PolicyDecisionRecord,
    PolicyEvaluationRequest, Receipt, TrustedObservedEventDraft,
};
use serde_json::json;
use sqlx::{Postgres, Row, Transaction};

use super::authority::{consume_authority_tx, AuthorityConsumeRequest};
use super::ledger::insert_ledger_event_tx;
use super::{db_err, enum_str, PostgresKernelStore};
use crate::{LedgerError, LedgerEvent, LedgerEventDraft, GENESIS_DIGEST};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdapterDispatchResult {
    pub dispatch_id: String,
    pub duplicate: bool,
    pub receipt: Option<Receipt>,
    pub observed_event: Option<ObservedEvent>,
}

pub struct MockDispatchRequest<'a> {
    pub obligation: &'a ordivon_kernel::Obligation,
    pub action: &'a ActionSpec,
    pub token: &'a AuthorityToken,
    pub verifier: &'a AuthorityVerifier,
    pub policy_hash: &'a str,
    pub policy_decision: PolicyDecision,
    pub policy_evaluator: &'a str,
    pub policy_reason_code: &'a str,
    pub now: &'a str,
    pub status: ObservationStatus,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdapterContract {
    pub adapter_name: String,
    pub source_identity: String,
    pub supported_action_classes: Vec<ActionClass>,
    pub dangerous_actions_sandboxed: bool,
    pub timeout_ms: u64,
    pub dry_run: bool,
}

impl AdapterContract {
    pub fn mock_action() -> Self {
        Self {
            adapter_name: "mock-action".to_string(),
            source_identity: "system:mock-action-adapter".to_string(),
            supported_action_classes: ActionClass::all(),
            dangerous_actions_sandboxed: true,
            timeout_ms: 5_000,
            dry_run: true,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AdapterFailureClass {
    AckOnly,
    Partial,
    Timeout,
    Duplicate,
    OrphanObservation,
    QueryBackMismatch,
}

impl PostgresKernelStore {
    pub async fn dispatch_mock_action(
        &self,
        request: MockDispatchRequest<'_>,
    ) -> Result<AdapterDispatchResult, LedgerError> {
        let obligation = request.obligation;
        let action = request.action;
        let token = request.token;
        let now = request.now;
        let status = request.status;
        let idempotency_key = action
            .idempotency_key()
            .map(ToString::to_string)
            .ok_or_else(|| LedgerError::Database("action missing idempotency key".to_string()))?;
        let mut tx = self.pool.begin().await.map_err(db_err)?;
        let dispatch_id = format!("dispatch:{idempotency_key}");

        sqlx::query("SELECT pg_advisory_xact_lock(hashtext($1)::bigint)")
            .bind(&idempotency_key)
            .execute(&mut *tx)
            .await
            .map_err(db_err)?;

        if sqlx::query("SELECT 1 FROM kernel_adapter_dispatches WHERE idempotency_key = $1")
            .bind(&idempotency_key)
            .fetch_optional(&mut *tx)
            .await
            .map_err(db_err)?
            .is_some()
        {
            tx.rollback().await.map_err(db_err)?;
            return Ok(AdapterDispatchResult {
                dispatch_id,
                duplicate: true,
                receipt: None,
                observed_event: None,
            });
        }

        let policy_decision_id = format!("policy-decision:{idempotency_key}");
        let policy_request = PolicyEvaluationRequest {
            decision_id: policy_decision_id.clone(),
            policy_hash: request.policy_hash.to_string(),
            evaluator: request.policy_evaluator.to_string(),
            intent_id: obligation.intent_id().to_string(),
            obligation_id: obligation.obligation_id().to_string(),
            action_class: action.action_class().clone(),
            target_ref: action.target_ref().to_string(),
            idempotency_key: idempotency_key.clone(),
            created_at: now.to_string(),
        };
        let policy_record = PolicyDecisionRecord::from_request(
            &policy_request,
            request.policy_decision,
            request.policy_reason_code,
        )?;
        insert_policy_decision_tx(&mut tx, &policy_record).await?;
        if !matches!(policy_record.decision, PolicyDecision::Allow) {
            tx.commit().await.map_err(db_err)?;
            return Err(LedgerError::Authority(
                ordivon_kernel::AuthorityError::PolicyDenied,
            ));
        }

        consume_authority_tx(
            &mut tx,
            AuthorityConsumeRequest {
                token,
                verifier: request.verifier,
                intent_id: obligation.intent_id(),
                obligation_id: obligation.obligation_id(),
                action_class: action.action_class(),
                target_ref: action.target_ref(),
                policy_hash: request.policy_hash,
                idempotency_key: &idempotency_key,
                now,
                policy_decision: policy_record.decision,
            },
        )
        .await?;

        sqlx::query("LOCK TABLE kernel_ledger_events IN EXCLUSIVE MODE")
            .execute(&mut *tx)
            .await
            .map_err(db_err)?;
        let current = sqlx::query(
            "SELECT event_seq, event_hash FROM kernel_ledger_events ORDER BY event_seq DESC LIMIT 1",
        )
        .fetch_optional(&mut *tx)
        .await
        .map_err(db_err)?;
        let (event_seq, prev_hash) = if let Some(row) = current {
            (
                row.get::<i64, _>("event_seq") as u64 + 1,
                row.get::<String, _>("event_hash"),
            )
        } else {
            (1, GENESIS_DIGEST.to_string())
        };
        let ledger_event = LedgerEvent::from_draft(LedgerEventDraft {
            event_seq,
            event_id: format!("evt:{dispatch_id}"),
            event_type: "ADAPTER_DISPATCHED".to_string(),
            origin: ordivon_kernel::Origin::SystemObserved,
            created_at: now.to_string(),
            object_type: "AdapterDispatch".to_string(),
            object_id: dispatch_id.clone(),
            payload: json!({
                "dispatchId": dispatch_id,
                "actionClass": enum_str(action.action_class()),
                "targetRef": action.target_ref(),
                "idempotencyKey": idempotency_key,
                "status": "Dispatched"
            }),
            prev_hash,
        })?;
        insert_ledger_event_tx(&mut tx, &ledger_event).await?;

        let inserted = sqlx::query(
            "INSERT INTO kernel_adapter_dispatches
                 (dispatch_id, obligation_id, action_class, target_ref, idempotency_key,
                  policy_decision_id, status, dispatched_at)
                 VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                 ON CONFLICT (idempotency_key) DO NOTHING",
        )
        .bind(&dispatch_id)
        .bind(obligation.obligation_id())
        .bind(enum_str(action.action_class()))
        .bind(action.target_ref())
        .bind(&idempotency_key)
        .bind(&policy_decision_id)
        .bind("Dispatched")
        .bind(now)
        .execute(&mut *tx)
        .await
        .map_err(db_err)?;
        if inserted.rows_affected() == 0 {
            tx.rollback().await.map_err(db_err)?;
            return Ok(AdapterDispatchResult {
                dispatch_id,
                duplicate: true,
                receipt: None,
                observed_event: None,
            });
        }
        apply_mock_action_tx(&mut tx, action, &idempotency_key, now).await?;

        if matches!(
            status,
            ObservationStatus::Acked | ObservationStatus::Unknown
        ) {
            tx.commit().await.map_err(db_err)?;
            return Ok(AdapterDispatchResult {
                dispatch_id,
                duplicate: false,
                receipt: None,
                observed_event: None,
            });
        }

        let observed_target = query_back_mock_record(&mut tx, action, &idempotency_key).await?;
        let payload_hash = match action.expected_payload_hash() {
            Some(hash) => hash.to_string(),
            None => ordivon_kernel::sha256_digest(&json!({"targetRef": observed_target}))?,
        };
        let contract = AdapterContract::mock_action();
        let source_registered =
            sqlx::query("SELECT 1 FROM kernel_adapter_sources WHERE source_identity = $1")
                .bind(&contract.source_identity)
                .fetch_optional(&mut *tx)
                .await
                .map_err(db_err)?
                .is_some();
        if !source_registered {
            return Err(LedgerError::MissingObservation { dispatch_id });
        }
        let observed_event = ObservedEvent::trusted(TrustedObservedEventDraft {
            event_id: format!("obs:{dispatch_id}"),
            trace_id: format!("trace:{}", obligation.intent_id()),
            source: "adapter:mock-action".to_string(),
            source_identity: contract.source_identity,
            observed_sequence: 1,
            event_type: "MOCK_ACTION_APPLIED".to_string(),
            action_class: action.action_class().clone(),
            target_ref: action.target_ref().to_string(),
            timestamp: now.to_string(),
            payload_hash,
            prev_event_hash: ledger_event.event_hash,
            origin: ordivon_kernel::Origin::SystemObserved,
            status,
            authority_ref: token.jti().to_string(),
            idempotency_key: idempotency_key.clone(),
        })?;
        sqlx::query(
            "INSERT INTO kernel_observed_events
                 (event_id, dispatch_id, trace_id, source_identity, action_class, target_ref, status,
                  payload_hash, authority_ref, idempotency_key, observed_at)
                 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
        )
        .bind(observed_event.event_id())
        .bind(&dispatch_id)
        .bind(observed_event.trace_id())
        .bind(observed_event.source_identity())
        .bind(enum_str(observed_event.action_class()))
        .bind(observed_event.target_ref())
        .bind(enum_str(observed_event.status()))
        .bind(observed_event.payload_hash())
        .bind(observed_event.authority_ref())
        .bind(observed_event.idempotency_key())
        .bind(observed_event.timestamp())
        .execute(&mut *tx)
        .await
        .map_err(db_err)?;

        let result = compare_obligation(obligation, std::slice::from_ref(&observed_event), now);
        for debt in &result.debts {
            insert_debt_tx(&mut tx, debt).await?;
        }
        tx.commit().await.map_err(db_err)?;
        Ok(AdapterDispatchResult {
            dispatch_id,
            duplicate: false,
            receipt: Some(result.receipt),
            observed_event: Some(observed_event),
        })
    }

    pub async fn insert_debt(&self, debt: &ordivon_kernel::Debt) -> Result<(), LedgerError> {
        let mut tx = self.pool.begin().await.map_err(db_err)?;
        insert_debt_tx(&mut tx, debt).await?;
        tx.commit().await.map_err(db_err)?;
        Ok(())
    }
}

async fn insert_policy_decision_tx(
    tx: &mut Transaction<'_, Postgres>,
    record: &PolicyDecisionRecord,
) -> Result<(), LedgerError> {
    sqlx::query(
        "INSERT INTO kernel_policy_decisions
             (decision_id, policy_hash, input_digest, evaluator, decision, reason_code, created_at)
         VALUES ($1,$2,$3,$4,$5,$6,$7)
         ON CONFLICT (decision_id) DO NOTHING",
    )
    .bind(&record.decision_id)
    .bind(&record.policy_hash)
    .bind(&record.input_digest)
    .bind(&record.evaluator)
    .bind(enum_str(&record.decision))
    .bind(&record.reason_code)
    .bind(&record.created_at)
    .execute(&mut **tx)
    .await
    .map_err(db_err)?;
    Ok(())
}

async fn apply_mock_action_tx(
    tx: &mut Transaction<'_, Postgres>,
    action: &ActionSpec,
    idempotency_key: &str,
    now: &str,
) -> Result<(), LedgerError> {
    sqlx::query(
        "INSERT INTO kernel_mock_records
             (record_ref, value, deleted, last_action_class, last_idempotency_key, updated_at)
             VALUES ($1,$2,$3,$4,$5,$6)
             ON CONFLICT (record_ref) DO UPDATE SET
                value = EXCLUDED.value,
                deleted = EXCLUDED.deleted,
                last_action_class = EXCLUDED.last_action_class,
                last_idempotency_key = EXCLUDED.last_idempotency_key,
                updated_at = EXCLUDED.updated_at",
    )
    .bind(action.target_ref())
    .bind(format!("mocked:{:?}", action.action_class()))
    .bind(matches!(action.action_class(), ActionClass::DeleteRecord))
    .bind(enum_str(action.action_class()))
    .bind(idempotency_key)
    .bind(now)
    .execute(&mut **tx)
    .await
    .map_err(db_err)?;
    Ok(())
}

async fn query_back_mock_record(
    tx: &mut Transaction<'_, Postgres>,
    action: &ActionSpec,
    idempotency_key: &str,
) -> Result<String, LedgerError> {
    let row = sqlx::query(
        "SELECT record_ref, last_idempotency_key
             FROM kernel_mock_records
             WHERE record_ref = $1",
    )
    .bind(action.target_ref())
    .fetch_optional(&mut **tx)
    .await
    .map_err(db_err)?
    .ok_or_else(|| LedgerError::MissingObservation {
        dispatch_id: format!("dispatch:{idempotency_key}"),
    })?;
    let observed_idempotency: String = row.get("last_idempotency_key");
    if observed_idempotency != idempotency_key {
        return Err(LedgerError::MissingObservation {
            dispatch_id: format!("dispatch:{idempotency_key}"),
        });
    }
    Ok(row.get("record_ref"))
}

pub(super) async fn insert_debt_tx(
    tx: &mut Transaction<'_, Postgres>,
    debt: &ordivon_kernel::Debt,
) -> Result<(), LedgerError> {
    sqlx::query(
        "INSERT INTO kernel_debts
             (debt_id, debt_type, severity, owner, due_at, blocking_scope,
              introduced_by_receipt, root_cause_code, verification_receipt, state)
             VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
             ON CONFLICT (debt_id) DO NOTHING",
    )
    .bind(&debt.debt_id)
    .bind(&debt.debt_type)
    .bind(&debt.severity)
    .bind(&debt.owner)
    .bind(&debt.due_at)
    .bind(&debt.blocking_scope)
    .bind(&debt.introduced_by_receipt)
    .bind(&debt.root_cause_code)
    .bind(&debt.verification_receipt)
    .bind(enum_str(&debt.state))
    .execute(&mut **tx)
    .await
    .map_err(db_err)?;
    Ok(())
}
