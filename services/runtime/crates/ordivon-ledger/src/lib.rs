use ordivon_kernel::{sha256_digest, KernelError, Origin};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::fs::{self, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

pub const GENESIS_DIGEST: &str = "sha256:GENESIS";

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LedgerEvent {
    pub event_seq: u64,
    pub event_id: String,
    pub event_type: String,
    pub origin: Origin,
    pub created_at: String,
    pub object_type: String,
    pub object_id: String,
    pub payload: Value,
    pub payload_hash: String,
    pub prev_hash: String,
    pub event_hash: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LedgerEventDraft {
    pub event_seq: u64,
    pub event_id: String,
    pub event_type: String,
    pub origin: Origin,
    pub created_at: String,
    pub object_type: String,
    pub object_id: String,
    pub payload: Value,
    pub prev_hash: String,
}

impl LedgerEvent {
    pub fn from_draft(draft: LedgerEventDraft) -> Result<Self, LedgerError> {
        let payload_hash = sha256_digest(&draft.payload)?;
        let mut event = Self {
            event_seq: draft.event_seq,
            event_id: draft.event_id,
            event_type: draft.event_type,
            origin: draft.origin,
            created_at: draft.created_at,
            object_type: draft.object_type,
            object_id: draft.object_id,
            payload: draft.payload,
            payload_hash,
            prev_hash: draft.prev_hash,
            event_hash: String::new(),
        };
        event.event_hash = event.compute_event_hash()?;
        Ok(event)
    }

    pub fn compute_event_hash(&self) -> Result<String, KernelError> {
        sha256_digest(&json!({
            "eventSeq": self.event_seq,
            "eventId": self.event_id,
            "eventType": self.event_type,
            "origin": self.origin,
            "createdAt": self.created_at,
            "objectType": self.object_type,
            "objectId": self.object_id,
            "payloadHash": self.payload_hash,
            "prevHash": self.prev_hash
        }))
    }
}

#[derive(Debug, Eq, PartialEq)]
pub enum LedgerError {
    Kernel(KernelError),
    Authority(ordivon_kernel::AuthorityError),
    Database(String),
    Io(String),
    Json(String),
    NonAppendSequence { expected: u64, actual: u64 },
    PreviousHashMismatch { expected: String, actual: String },
    PayloadHashMismatch { event_id: String },
    EventHashMismatch { event_id: String },
    EmptySealSegment,
    ProjectionDrift { expected: String, actual: String },
    DuplicateDispatch { idempotency_key: String },
    MissingObservation { dispatch_id: String },
}

impl From<KernelError> for LedgerError {
    fn from(value: KernelError) -> Self {
        Self::Kernel(value)
    }
}

impl std::fmt::Display for LedgerError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Kernel(err) => write!(f, "{err}"),
            Self::Authority(err) => write!(f, "authority error: {err:?}"),
            Self::Database(err) => write!(f, "database error: {err}"),
            Self::Io(err) => write!(f, "io error: {err}"),
            Self::Json(err) => write!(f, "json error: {err}"),
            Self::NonAppendSequence { expected, actual } => {
                write!(f, "non-append sequence: expected {expected}, got {actual}")
            }
            Self::PreviousHashMismatch { expected, actual } => {
                write!(
                    f,
                    "previous hash mismatch: expected {expected}, got {actual}"
                )
            }
            Self::PayloadHashMismatch { event_id } => {
                write!(f, "payload hash mismatch for {event_id}")
            }
            Self::EventHashMismatch { event_id } => write!(f, "event hash mismatch for {event_id}"),
            Self::EmptySealSegment => write!(f, "cannot seal an empty ledger segment"),
            Self::ProjectionDrift { expected, actual } => {
                write!(f, "projection drift: expected {expected}, got {actual}")
            }
            Self::DuplicateDispatch { idempotency_key } => {
                write!(f, "duplicate adapter dispatch for {idempotency_key}")
            }
            Self::MissingObservation { dispatch_id } => {
                write!(f, "dispatch {dispatch_id} has no system observation")
            }
        }
    }
}

impl std::error::Error for LedgerError {}

#[derive(Default)]
pub struct AppendOnlyLedger {
    events: Vec<LedgerEvent>,
}

impl AppendOnlyLedger {
    pub fn append(&mut self, event: LedgerEvent) -> Result<(), LedgerError> {
        let expected_seq = self.events.len() as u64 + 1;
        if event.event_seq != expected_seq {
            return Err(LedgerError::NonAppendSequence {
                expected: expected_seq,
                actual: event.event_seq,
            });
        }

        let expected_prev = self
            .events
            .last()
            .map(|event| event.event_hash.as_str())
            .unwrap_or(GENESIS_DIGEST);
        if event.prev_hash != expected_prev {
            return Err(LedgerError::PreviousHashMismatch {
                expected: expected_prev.to_string(),
                actual: event.prev_hash,
            });
        }

        verify_event(&event)?;
        self.events.push(event);
        Ok(())
    }

    pub fn events(&self) -> &[LedgerEvent] {
        &self.events
    }
}

pub fn verify_chain(events: &[LedgerEvent]) -> Result<(), LedgerError> {
    let mut expected_prev = GENESIS_DIGEST.to_string();
    for (index, event) in events.iter().enumerate() {
        let expected_seq = index as u64 + 1;
        if event.event_seq != expected_seq {
            return Err(LedgerError::NonAppendSequence {
                expected: expected_seq,
                actual: event.event_seq,
            });
        }
        if event.prev_hash != expected_prev {
            return Err(LedgerError::PreviousHashMismatch {
                expected: expected_prev,
                actual: event.prev_hash.clone(),
            });
        }
        verify_event(event)?;
        expected_prev = event.event_hash.clone();
    }
    Ok(())
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SealManifest {
    pub segment_id: String,
    pub first_event_seq: u64,
    pub last_event_seq: u64,
    pub event_count: usize,
    pub root_digest: String,
    pub previous_seal_ref: Option<String>,
    pub sealed_at: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProjectionManifest {
    pub projection_id: String,
    pub source_first_seq: u64,
    pub source_last_seq: u64,
    pub event_count: usize,
    pub head_hash: String,
    pub rebuilt_at: String,
}

pub struct JsonlLedgerStore {
    path: PathBuf,
}

impl JsonlLedgerStore {
    pub fn new(path: impl Into<PathBuf>) -> Self {
        Self { path: path.into() }
    }

    pub fn read_events(&self) -> Result<Vec<LedgerEvent>, LedgerError> {
        read_events(&self.path)
    }

    pub fn append(&self, event: LedgerEvent) -> Result<(), LedgerError> {
        if let Some(parent) = self.path.parent() {
            fs::create_dir_all(parent).map_err(|err| LedgerError::Io(err.to_string()))?;
        }

        let mut events = self.read_events()?;
        let mut ledger = AppendOnlyLedger {
            events: std::mem::take(&mut events),
        };
        ledger.append(event.clone())?;

        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)
            .map_err(|err| LedgerError::Io(err.to_string()))?;
        let line =
            serde_json::to_string(&event).map_err(|err| LedgerError::Json(err.to_string()))?;
        writeln!(file, "{line}").map_err(|err| LedgerError::Io(err.to_string()))?;
        Ok(())
    }
}

pub fn read_events(path: &Path) -> Result<Vec<LedgerEvent>, LedgerError> {
    if !path.exists() {
        return Ok(Vec::new());
    }

    let file = fs::File::open(path).map_err(|err| LedgerError::Io(err.to_string()))?;
    let reader = BufReader::new(file);
    let mut events = Vec::new();
    for line in reader.lines() {
        let line = line.map_err(|err| LedgerError::Io(err.to_string()))?;
        if line.trim().is_empty() {
            continue;
        }
        let event: LedgerEvent =
            serde_json::from_str(&line).map_err(|err| LedgerError::Json(err.to_string()))?;
        events.push(event);
    }
    verify_chain(&events)?;
    Ok(events)
}

pub fn build_seal_manifest(
    segment_id: impl Into<String>,
    events: &[LedgerEvent],
    sealed_at: impl Into<String>,
    previous_seal_ref: Option<String>,
) -> Result<SealManifest, LedgerError> {
    let first = events.first().ok_or(LedgerError::EmptySealSegment)?;
    let last = events.last().ok_or(LedgerError::EmptySealSegment)?;
    verify_chain(events)?;
    let event_hashes: Vec<_> = events
        .iter()
        .map(|event| event.event_hash.clone())
        .collect();
    let root_digest = sha256_digest(&json!({ "eventHashes": event_hashes }))?;
    Ok(SealManifest {
        segment_id: segment_id.into(),
        first_event_seq: first.event_seq,
        last_event_seq: last.event_seq,
        event_count: events.len(),
        root_digest,
        previous_seal_ref,
        sealed_at: sealed_at.into(),
    })
}

pub fn build_projection_manifest(
    projection_id: impl Into<String>,
    events: &[LedgerEvent],
    rebuilt_at: impl Into<String>,
) -> Result<ProjectionManifest, LedgerError> {
    let first = events.first().ok_or(LedgerError::EmptySealSegment)?;
    let last = events.last().ok_or(LedgerError::EmptySealSegment)?;
    verify_chain(events)?;
    Ok(ProjectionManifest {
        projection_id: projection_id.into(),
        source_first_seq: first.event_seq,
        source_last_seq: last.event_seq,
        event_count: events.len(),
        head_hash: last.event_hash.clone(),
        rebuilt_at: rebuilt_at.into(),
    })
}

fn verify_event(event: &LedgerEvent) -> Result<(), LedgerError> {
    if sha256_digest(&event.payload)? != event.payload_hash {
        return Err(LedgerError::PayloadHashMismatch {
            event_id: event.event_id.clone(),
        });
    }
    if event.compute_event_hash()? != event.event_hash {
        return Err(LedgerError::EventHashMismatch {
            event_id: event.event_id.clone(),
        });
    }
    Ok(())
}

#[cfg(feature = "postgres")]
pub mod postgres;

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn event(seq: u64, prev_hash: &str, value: &str) -> LedgerEvent {
        LedgerEvent::from_draft(LedgerEventDraft {
            event_seq: seq,
            event_id: format!("evt_{seq}"),
            event_type: "OBJECT_RECORDED".to_string(),
            origin: Origin::SystemDerived,
            created_at: "2026-05-16T00:00:00Z".to_string(),
            object_type: "Receipt".to_string(),
            object_id: format!("receipt_{seq}"),
            payload: json!({"value": value}),
            prev_hash: prev_hash.to_string(),
        })
        .unwrap()
    }

    #[test]
    fn append_only_ledger_accepts_valid_hash_chain() {
        let mut ledger = AppendOnlyLedger::default();
        let first = event(1, GENESIS_DIGEST, "a");
        let second = event(2, &first.event_hash, "b");

        ledger.append(first).unwrap();
        ledger.append(second).unwrap();

        assert_eq!(ledger.events().len(), 2);
        assert!(verify_chain(ledger.events()).is_ok());
    }

    #[test]
    fn append_only_ledger_rejects_sequence_rewrite() {
        let mut ledger = AppendOnlyLedger::default();
        let first = event(2, GENESIS_DIGEST, "a");

        assert!(matches!(
            ledger.append(first),
            Err(LedgerError::NonAppendSequence {
                expected: 1,
                actual: 2
            })
        ));
    }

    #[test]
    fn verify_chain_rejects_tampered_payload() {
        let first = event(1, GENESIS_DIGEST, "a");
        let mut tampered = event(2, &first.event_hash, "b");
        tampered.payload = json!({"value": "changed"});

        assert!(matches!(
            verify_chain(&[first, tampered]),
            Err(LedgerError::PayloadHashMismatch { .. })
        ));
    }

    #[test]
    fn jsonl_store_persists_and_replays_valid_chain() {
        let path = temp_path("ordivon-ledger-valid.jsonl");
        let store = JsonlLedgerStore::new(&path);
        let first = event(1, GENESIS_DIGEST, "a");
        let second = event(2, &first.event_hash, "b");

        store.append(first).unwrap();
        store.append(second).unwrap();

        let events = store.read_events().unwrap();
        assert_eq!(events.len(), 2);
        assert!(verify_chain(&events).is_ok());

        let _ = fs::remove_file(path);
    }

    #[test]
    fn seal_manifest_covers_replayed_segment() {
        let first = event(1, GENESIS_DIGEST, "a");
        let second = event(2, &first.event_hash, "b");

        let manifest =
            build_seal_manifest("seg_1", &[first, second], "2026-05-16T00:00:10Z", None).unwrap();

        assert_eq!(manifest.first_event_seq, 1);
        assert_eq!(manifest.last_event_seq, 2);
        assert_eq!(manifest.event_count, 2);
        assert!(manifest.root_digest.starts_with("sha256:"));
    }

    #[test]
    fn projection_manifest_is_explicitly_rebuildable_view() {
        let first = event(1, GENESIS_DIGEST, "a");
        let second = event(2, &first.event_hash, "b");
        let expected_head = second.event_hash.clone();

        let manifest =
            build_projection_manifest("receipt_current", &[first, second], "2026-05-16T00:00:10Z")
                .unwrap();

        assert_eq!(manifest.source_first_seq, 1);
        assert_eq!(manifest.source_last_seq, 2);
        assert_eq!(manifest.head_hash, expected_head);
    }

    fn temp_path(name: &str) -> PathBuf {
        let nanos = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!("{nanos}-{name}"))
    }
}

#[cfg(all(test, feature = "postgres-integration"))]
mod postgres_tests {
    use super::postgres::{
        AdapterDispatchResult, MockDispatchRequest, PostgresKernelStore, PostgresRedTeamRunner,
        RedTeamRunConfig,
    };
    use super::*;
    use ordivon_kernel::test_support::{
        signed_test_token, test_authority_verifier, TEST_AUTHORITY_KID,
    };
    use ordivon_kernel::{
        build_dogfood_seal, sha256_digest, verify_dogfood_seal, ActionClass, ActionSpec,
        ApprovalMode, AuthorityToken, AuthorityTokenDraft, AuthorityValidationRequest,
        ObservationStatus, Origin,
    };
    use serde_json::json;
    use sqlx::Row;

    fn digest(label: &str) -> String {
        sha256_digest(&json!({ "label": label })).unwrap()
    }

    fn event(seq: u64, prev_hash: &str, value: &str) -> LedgerEvent {
        LedgerEvent::from_draft(LedgerEventDraft {
            event_seq: seq,
            event_id: format!("pg_evt_{seq}"),
            event_type: "OBJECT_RECORDED".to_string(),
            origin: Origin::SystemDerived,
            created_at: "2026-05-16T00:00:00Z".to_string(),
            object_type: "Receipt".to_string(),
            object_id: format!("receipt_{seq}"),
            payload: json!({"value": value}),
            prev_hash: prev_hash.to_string(),
        })
        .unwrap()
    }

    fn action(action_class: ActionClass, target_ref: &str, token_jti: &str) -> ActionSpec {
        ActionSpec::new(
            action_class,
            target_ref,
            ApprovalMode::Policy,
            format!("idem:{token_jti}:{target_ref}"),
        )
        .with_authority_refs(vec![token_jti.to_string()])
        .with_expected_payload_hash(digest(target_ref))
    }

    fn obligation(action: ActionSpec) -> ordivon_kernel::Obligation {
        ordivon_kernel::Obligation::try_from(ordivon_kernel::ObligationDraft {
            obligation_id: format!("obl:{}", action.target_ref()),
            intent_id: "intent:pg-hardening".to_string(),
            declared_actions: vec![action],
            declaration_hash: digest("declaration"),
            expires_at: "2026-05-16T00:10:00Z".to_string(),
        })
        .unwrap()
    }

    fn token(
        jti: &str,
        action_class: ActionClass,
        target_ref: &str,
        obligation_id: &str,
        idempotency_key: &str,
    ) -> AuthorityToken {
        signed_test_token(AuthorityTokenDraft {
            jti: jti.to_string(),
            kid: TEST_AUTHORITY_KID.to_string(),
            iss: "ordivon-authority-service".to_string(),
            sub: "agent:planner".to_string(),
            audience: "adapter:mock-action".to_string(),
            intent_id: "intent:pg-hardening".to_string(),
            obligation_id: obligation_id.to_string(),
            action_class,
            target_ref: target_ref.to_string(),
            policy_hash: digest("policy"),
            issued_at: "2026-05-16T00:00:00Z".to_string(),
            not_before: "2026-05-16T00:00:00Z".to_string(),
            expires_at: "2026-05-16T00:05:00Z".to_string(),
            max_use_count: 1,
            idempotency_key: idempotency_key.to_string(),
            seal_ref: "seal:pg-hardening".to_string(),
            signature: String::new(),
        })
        .unwrap()
    }

    async fn ensure_certification_roles(store: &PostgresKernelStore) {
        sqlx::query(
            "DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ordivon_kernel_app') THEN
                    CREATE ROLE ordivon_kernel_app;
                END IF;
            END $$",
        )
        .execute(store.pool())
        .await
        .unwrap();
        store.ensure_schema().await.unwrap();
    }

    async fn dispatch_action(
        store: &PostgresKernelStore,
        obligation: &ordivon_kernel::Obligation,
        action: &ActionSpec,
        auth: &AuthorityToken,
        verifier: &ordivon_kernel::AuthorityVerifier,
        now: &str,
        status: ObservationStatus,
    ) -> Result<AdapterDispatchResult, LedgerError> {
        let policy_hash = digest("policy");
        store
            .dispatch_mock_action(MockDispatchRequest {
                obligation,
                action,
                token: auth,
                verifier,
                policy_hash: &policy_hash,
                policy_decision: ordivon_kernel::PolicyDecision::Allow,
                policy_evaluator: "static-test-policy",
                policy_reason_code: "ALLOW_TEST",
                now,
                status,
            })
            .await
    }

    #[tokio::test]
    async fn postgres_kernel_hard_gate_covers_p1_to_p8() {
        let store = PostgresKernelStore::connect_from_env().await.unwrap();
        store.reset_kernel_tables().await.unwrap();
        let _ = super::postgres::migration_database_url_from_env().unwrap();
        let _ = super::postgres::test_admin_database_url_from_env().unwrap();

        let first = event(1, GENESIS_DIGEST, "a");
        let second = event(2, &first.event_hash, "b");
        store.append_event(&first).await.unwrap();
        store.append_event(&second).await.unwrap();
        let projection = store
            .build_and_store_projection("receipt_current", "2026-05-16T00:00:10Z")
            .await
            .unwrap();
        assert_eq!(projection.head_hash, second.event_hash);
        store.verify_projection("receipt_current").await.unwrap();

        sqlx::query("UPDATE kernel_ledger_events SET payload = $1 WHERE event_seq = 2")
            .bind(sqlx::types::Json(json!({"value": "tampered"})))
            .execute(store.pool())
            .await
            .unwrap();
        assert!(matches!(
            store.read_events().await,
            Err(LedgerError::PayloadHashMismatch { .. })
        ));
        store.reset_kernel_tables().await.unwrap();

        store.append_event(&first).await.unwrap();
        store
            .build_and_store_projection("receipt_current", "2026-05-16T00:00:10Z")
            .await
            .unwrap();
        let second = event(2, &first.event_hash, "b");
        store.append_event(&second).await.unwrap();
        assert!(matches!(
            store.verify_projection("receipt_current").await,
            Err(LedgerError::ProjectionDrift { .. })
        ));
        store.reset_kernel_tables().await.unwrap();

        ensure_certification_roles(&store).await;
        let role_event = event(1, GENESIS_DIGEST, "role-append");
        let mut role_tx = store.pool().begin().await.unwrap();
        sqlx::query("SET LOCAL ROLE ordivon_kernel_app")
            .execute(&mut *role_tx)
            .await
            .unwrap();
        sqlx::query("SELECT kernel_append_ledger_event($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)")
            .bind(role_event.event_seq as i64)
            .bind(&role_event.event_id)
            .bind(&role_event.event_type)
            .bind(super::postgres::enum_str(&role_event.origin))
            .bind(&role_event.created_at)
            .bind(&role_event.object_type)
            .bind(&role_event.object_id)
            .bind(sqlx::types::Json(&role_event.payload))
            .bind(&role_event.payload_hash)
            .bind(&role_event.prev_hash)
            .bind(&role_event.event_hash)
            .execute(&mut *role_tx)
            .await
            .unwrap();
        let app_update =
            sqlx::query("UPDATE kernel_ledger_events SET payload = $1 WHERE event_seq = $2")
                .bind(sqlx::types::Json(json!({"value": "forbidden"})))
                .bind(role_event.event_seq as i64)
                .execute(&mut *role_tx)
                .await;
        assert!(app_update.is_err());
        let _ = role_tx.rollback().await;
        store.reset_kernel_tables().await.unwrap();

        let verifier = test_authority_verifier();
        for (idx, action_class) in ActionClass::all().into_iter().enumerate() {
            let target = format!("record:class:{idx}");
            let token_jti = format!("auth:class:{idx}");
            let action = action(action_class.clone(), &target, &token_jti);
            let obligation = obligation(action.clone());
            let auth = token(
                &token_jti,
                action_class,
                &target,
                obligation.obligation_id(),
                action.idempotency_key().unwrap(),
            );
            let result = dispatch_action(
                &store,
                &obligation,
                &action,
                &auth,
                &verifier,
                "2026-05-16T00:01:00Z",
                ObservationStatus::Observed,
            )
            .await
            .unwrap();
            assert!(!result.duplicate);
            assert_eq!(
                *result.receipt.unwrap().verdict(),
                ordivon_kernel::Verdict::ExactMatch
            );
        }

        let target = "record:replay";
        let first_jti = "auth:replay:1";
        let replay_action = action(ActionClass::UpdateRecord, target, first_jti);
        let replay_obligation = obligation(replay_action.clone());
        let auth = token(
            first_jti,
            ActionClass::UpdateRecord,
            target,
            replay_obligation.obligation_id(),
            replay_action.idempotency_key().unwrap(),
        );
        store
            .consume_authority(AuthorityValidationRequest {
                token: &auth,
                verifier: &verifier,
                intent_id: replay_obligation.intent_id(),
                obligation_id: replay_obligation.obligation_id(),
                action_class: &ActionClass::UpdateRecord,
                target_ref: target,
                policy_hash: &digest("policy"),
                idempotency_key: replay_action.idempotency_key().unwrap(),
                now: "2026-05-16T00:01:00Z",
                policy_decision: ordivon_kernel::PolicyDecision::Allow,
            })
            .await
            .unwrap();
        assert!(matches!(
            store
                .consume_authority(AuthorityValidationRequest {
                    token: &auth,
                    verifier: &verifier,
                    intent_id: replay_obligation.intent_id(),
                    obligation_id: replay_obligation.obligation_id(),
                    action_class: &ActionClass::UpdateRecord,
                    target_ref: target,
                    policy_hash: &digest("policy"),
                    idempotency_key: replay_action.idempotency_key().unwrap(),
                    now: "2026-05-16T00:01:01Z",
                    policy_decision: ordivon_kernel::PolicyDecision::Allow,
                })
                .await,
            Err(LedgerError::Authority(
                ordivon_kernel::AuthorityError::ReplayedToken { .. }
            ))
        ));

        let deny_target = "record:policy-deny";
        let deny_action = action(ActionClass::UpdateRecord, deny_target, "auth:deny");
        let deny_obligation = obligation(deny_action.clone());
        let deny_auth = token(
            "auth:deny",
            ActionClass::UpdateRecord,
            deny_target,
            deny_obligation.obligation_id(),
            deny_action.idempotency_key().unwrap(),
        );
        let deny_policy_hash = digest("policy");
        let denied = store
            .dispatch_mock_action(MockDispatchRequest {
                obligation: &deny_obligation,
                action: &deny_action,
                token: &deny_auth,
                verifier: &verifier,
                policy_hash: &deny_policy_hash,
                policy_decision: ordivon_kernel::PolicyDecision::Deny,
                policy_evaluator: "static-test-policy",
                policy_reason_code: "DENY_TEST",
                now: "2026-05-16T00:01:00Z",
                status: ObservationStatus::Observed,
            })
            .await;
        assert!(matches!(
            denied,
            Err(LedgerError::Authority(
                ordivon_kernel::AuthorityError::PolicyDenied
            ))
        ));
        let denied_counts = sqlx::query(
            "SELECT
                (SELECT count(*) FROM kernel_policy_decisions WHERE decision_id = $1) AS decisions,
                (SELECT count(*) FROM kernel_authority_uses WHERE jti = $2) AS uses,
                (SELECT count(*) FROM kernel_adapter_dispatches WHERE idempotency_key = $3) AS dispatches",
        )
        .bind(format!(
            "policy-decision:{}",
            deny_action.idempotency_key().unwrap()
        ))
        .bind("auth:deny")
        .bind(deny_action.idempotency_key().unwrap())
        .fetch_one(store.pool())
        .await
        .unwrap();
        assert_eq!(denied_counts.get::<i64, _>("decisions"), 1);
        assert_eq!(denied_counts.get::<i64, _>("uses"), 0);
        assert_eq!(denied_counts.get::<i64, _>("dispatches"), 0);

        let duplicate_target = "record:duplicate";
        let duplicate_action = action(ActionClass::UpdateRecord, duplicate_target, "auth:dup:1");
        let duplicate_obligation = obligation(duplicate_action.clone());
        let first_auth = token(
            "auth:dup:1",
            ActionClass::UpdateRecord,
            duplicate_target,
            duplicate_obligation.obligation_id(),
            duplicate_action.idempotency_key().unwrap(),
        );
        dispatch_action(
            &store,
            &duplicate_obligation,
            &duplicate_action,
            &first_auth,
            &verifier,
            "2026-05-16T00:01:00Z",
            ObservationStatus::Observed,
        )
        .await
        .unwrap();
        let duplicate_action_second = duplicate_action
            .clone()
            .with_authority_refs(vec!["auth:dup:2".to_string()]);
        let second_auth = token(
            "auth:dup:2",
            ActionClass::UpdateRecord,
            duplicate_target,
            duplicate_obligation.obligation_id(),
            duplicate_action.idempotency_key().unwrap(),
        );
        let duplicate = dispatch_action(
            &store,
            &duplicate_obligation,
            &duplicate_action_second,
            &second_auth,
            &verifier,
            "2026-05-16T00:01:01Z",
            ObservationStatus::Observed,
        )
        .await
        .unwrap();
        assert!(duplicate.duplicate);

        store.reset_kernel_tables().await.unwrap();
        let concurrent_target = "record:concurrent-duplicate";
        let concurrent_action = action(
            ActionClass::UpdateRecord,
            concurrent_target,
            "auth:concurrent:1",
        );
        let concurrent_obligation = obligation(concurrent_action.clone());
        let concurrent_first_auth = token(
            "auth:concurrent:1",
            ActionClass::UpdateRecord,
            concurrent_target,
            concurrent_obligation.obligation_id(),
            concurrent_action.idempotency_key().unwrap(),
        );
        let concurrent_loser_action = concurrent_action
            .clone()
            .with_authority_refs(vec!["auth:concurrent:2".to_string()]);
        let concurrent_second_auth = token(
            "auth:concurrent:2",
            ActionClass::UpdateRecord,
            concurrent_target,
            concurrent_obligation.obligation_id(),
            concurrent_action.idempotency_key().unwrap(),
        );
        let concurrent_store = PostgresKernelStore::connect_from_env().await.unwrap();
        let verifier_one = verifier.clone();
        let verifier_two = verifier.clone();
        let (first_result, second_result) = tokio::join!(
            dispatch_action(
                &store,
                &concurrent_obligation,
                &concurrent_action,
                &concurrent_first_auth,
                &verifier_one,
                "2026-05-16T00:01:00Z",
                ObservationStatus::Observed,
            ),
            dispatch_action(
                &concurrent_store,
                &concurrent_obligation,
                &concurrent_loser_action,
                &concurrent_second_auth,
                &verifier_two,
                "2026-05-16T00:01:00Z",
                ObservationStatus::Observed,
            )
        );
        let first_result = first_result.unwrap();
        let second_result = second_result.unwrap();
        assert_ne!(first_result.duplicate, second_result.duplicate);
        let loser_jti = if first_result.duplicate {
            "auth:concurrent:1"
        } else {
            "auth:concurrent:2"
        };
        let loser_use =
            sqlx::query("SELECT count(*) AS count FROM kernel_authority_uses WHERE jti = $1")
                .bind(loser_jti)
                .fetch_one(store.pool())
                .await
                .unwrap();
        assert_eq!(loser_use.get::<i64, _>("count"), 0);

        let ack_action = action(ActionClass::UpdateRecord, "record:ack", "auth:ack");
        let ack_obligation = obligation(ack_action.clone());
        let ack_auth = token(
            "auth:ack",
            ActionClass::UpdateRecord,
            "record:ack",
            ack_obligation.obligation_id(),
            ack_action.idempotency_key().unwrap(),
        );
        let ack = dispatch_action(
            &store,
            &ack_obligation,
            &ack_action,
            &ack_auth,
            &verifier,
            "2026-05-16T00:01:00Z",
            ObservationStatus::Acked,
        )
        .await
        .unwrap();
        assert!(ack.receipt.is_none());
        assert!(ack.observed_event.is_none());

        let orphan_observation = sqlx::query(
            "INSERT INTO kernel_observed_events
             (event_id, dispatch_id, trace_id, action_class, target_ref, status,
              payload_hash, authority_ref, idempotency_key, observed_at)
             VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)",
        )
        .bind("obs:orphan")
        .bind("dispatch:missing")
        .bind("trace:orphan")
        .bind("UPDATE_RECORD")
        .bind("record:orphan")
        .bind("Observed")
        .bind(digest("record:orphan"))
        .bind("auth:orphan")
        .bind("idem:orphan")
        .bind("2026-05-16T00:01:02Z")
        .execute(store.pool())
        .await;
        assert!(orphan_observation.is_err());

        sqlx::query(
            "UPDATE kernel_schema_migrations SET checksum = 'sha256:bogus' WHERE version = 1",
        )
        .execute(store.pool())
        .await
        .unwrap();
        assert!(matches!(
            store.ensure_schema().await,
            Err(LedgerError::Database(message)) if message.contains("checksum mismatch")
        ));
        sqlx::query("DELETE FROM kernel_schema_migrations WHERE version = 1")
            .execute(store.pool())
            .await
            .unwrap();
        store.ensure_schema().await.unwrap();

        store.reset_kernel_tables().await.unwrap();
        let run = PostgresRedTeamRunner::new(&store)
            .run(RedTeamRunConfig {
                run_id: "red-team-run:p8".to_string(),
                issued_at: "2026-05-16T00:02:00Z".to_string(),
            })
            .await
            .unwrap();
        let seal = build_dogfood_seal("dogfood-seal:p8", &run);
        verify_dogfood_seal(&seal, &run).unwrap();
        assert_eq!(seal.critical_bypasses, 0);
    }
}
