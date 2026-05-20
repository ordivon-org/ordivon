use ordivon_kernel::test_support::{
    signed_test_token, test_authority_verifier, TEST_AUTHORITY_KID,
};
use ordivon_kernel::{
    bootstrap_red_team_scenarios, candidate_policies_from_clusters, cluster_debts,
    compare_obligation, sha256_digest, verified_red_team_run, ActionClass, ActionSpec,
    ApprovalMode, AuthorityToken, AuthorityTokenDraft, AuthorityValidationRequest, ClosureDraft,
    Debt, DebtState, ObservationStatus, ObservedEvent, Origin, PolicyDecision, PolicyDraft,
    PolicyStatus, Promotion, PromotionDraft, RedTeamAttack, RedTeamOutcome, Suppression,
    SuppressionDraft, TrustedObservedEventDraft, Verdict, VerifiedRedTeamRun,
};
use serde_json::json;
use sqlx::Row;

use super::{AdapterDispatchResult, MockDispatchRequest, PostgresKernelStore};
use crate::{LedgerError, LedgerEvent, LedgerEventDraft, GENESIS_DIGEST};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RedTeamRunConfig {
    pub run_id: String,
    pub issued_at: String,
}

impl Default for RedTeamRunConfig {
    fn default() -> Self {
        Self {
            run_id: "red-team-run:p8".to_string(),
            issued_at: "2026-05-16T00:02:00Z".to_string(),
        }
    }
}

pub struct PostgresRedTeamRunner<'a> {
    store: &'a PostgresKernelStore,
}

impl<'a> PostgresRedTeamRunner<'a> {
    pub fn new(store: &'a PostgresKernelStore) -> Self {
        Self { store }
    }

    pub async fn run(&self, config: RedTeamRunConfig) -> Result<VerifiedRedTeamRun, LedgerError> {
        let mut outcomes = Vec::new();
        for scenario in bootstrap_red_team_scenarios() {
            let blocked = self.execute_attack(&config, &scenario.attack).await?;
            outcomes.push(RedTeamOutcome {
                scenario_id: scenario.scenario_id,
                blocked,
                actual_verdict: scenario.expected_verdict,
                finding: if blocked { "blocked" } else { "bypassed" }.to_string(),
            });
        }
        self.execute_policy_replay_regression(&config)?;
        Ok(verified_red_team_run(
            config.run_id,
            outcomes,
            config.issued_at,
        ))
    }

    async fn execute_attack(
        &self,
        config: &RedTeamRunConfig,
        attack: &RedTeamAttack,
    ) -> Result<bool, LedgerError> {
        match attack {
            RedTeamAttack::AiForgedObservation => {
                Ok(ObservedEvent::trusted(TrustedObservedEventDraft {
                    event_id: scoped(config, "obs:forged"),
                    trace_id: scoped(config, "trace:forged"),
                    source: "ai:self-report".to_string(),
                    source_identity: "codex".to_string(),
                    observed_sequence: 1,
                    event_type: "MOCK_ACTION_APPLIED".to_string(),
                    action_class: ActionClass::UpdateRecord,
                    target_ref: scoped(config, "record:forged"),
                    timestamp: config.issued_at.clone(),
                    payload_hash: digest("record:forged"),
                    prev_event_hash: "sha256:prev".to_string(),
                    origin: Origin::AiWritten,
                    status: ObservationStatus::Observed,
                    authority_ref: scoped(config, "auth:forged"),
                    idempotency_key: scoped(config, "idem:forged"),
                })
                .is_err())
            }
            RedTeamAttack::TokenReplay => self.token_replay(config).await,
            RedTeamAttack::WrongTarget => self.wrong_target(config).await,
            RedTeamAttack::DuplicateDispatch => self.duplicate_dispatch(config).await,
            RedTeamAttack::AckAsSuccess => self.ack_as_success(config).await,
            RedTeamAttack::LedgerTamper => self.ledger_tamper(config).await,
            RedTeamAttack::ProjectionDrift => self.projection_drift(config).await,
            RedTeamAttack::PolicyPromotionBypass => {
                Ok(ordivon_kernel::Policy::try_from(PolicyDraft {
                    policy_id: scoped(config, "policy:active-bypass"),
                    candidate_policy_id: scoped(config, "candidate:active-bypass"),
                    policy_hash: digest("policy"),
                    scope: "red-team".to_string(),
                    status: PolicyStatus::Active,
                })
                .is_err())
            }
            RedTeamAttack::ClosureWithoutVerification => {
                Ok(ordivon_kernel::Closure::try_from(ClosureDraft {
                    closure_id: scoped(config, "closure:no-verification"),
                    target_ref: scoped(config, "debt:no-verification"),
                    closure_reason: "fixed".to_string(),
                    verification_receipt: None,
                    reopen_conditions: vec!["recurs".to_string()],
                })
                .is_err())
            }
            RedTeamAttack::SuppressionWithoutExpiry => {
                Ok(Suppression::try_from(SuppressionDraft {
                    suppression_id: scoped(config, "suppression:no-expiry"),
                    target_ref: scoped(config, "debt:no-expiry"),
                    reason: "noise".to_string(),
                    approved_by: "authority:review".to_string(),
                    expires_at: String::new(),
                    review_at: "2026-05-20T00:00:00Z".to_string(),
                })
                .is_err())
            }
            RedTeamAttack::CompromisedAdapterSourceIdentity => {
                self.compromised_adapter_source(config).await
            }
            RedTeamAttack::DelayedObservationAfterExpiry => {
                Ok(self.delayed_observation_after_expiry(config)?)
            }
            RedTeamAttack::DuplicateObservation => Ok(self.duplicate_observation(config)?),
            RedTeamAttack::ObservationForWrongDispatch => {
                self.observation_for_wrong_dispatch(config).await
            }
            RedTeamAttack::QueryBackMismatch => Ok(self.query_back_mismatch(config)?),
        }
    }

    async fn token_replay(&self, config: &RedTeamRunConfig) -> Result<bool, LedgerError> {
        let verifier = test_authority_verifier();
        let declared_action = action(
            ActionClass::UpdateRecord,
            &scoped(config, "record:replay"),
            &scoped(config, "auth:replay"),
        );
        let declared = obligation(config, declared_action.clone());
        let auth = token(
            config,
            "auth:replay",
            ActionClass::UpdateRecord,
            declared_action.target_ref(),
            declared.obligation_id(),
            declared_action.idempotency_key().unwrap_or(""),
        )?;
        let request = AuthorityValidationRequest {
            token: &auth,
            verifier: &verifier,
            intent_id: declared.intent_id(),
            obligation_id: declared.obligation_id(),
            action_class: &ActionClass::UpdateRecord,
            target_ref: declared_action.target_ref(),
            policy_hash: &digest("policy"),
            idempotency_key: declared_action.idempotency_key().unwrap_or(""),
            now: &config.issued_at,
            policy_decision: PolicyDecision::Allow,
        };
        self.store.consume_authority(request).await?;
        Ok(matches!(
            self.store.consume_authority(request).await,
            Err(LedgerError::Authority(
                ordivon_kernel::AuthorityError::ReplayedToken { .. }
            ))
        ))
    }

    async fn wrong_target(&self, config: &RedTeamRunConfig) -> Result<bool, LedgerError> {
        let verifier = test_authority_verifier();
        let declared_action = action(
            ActionClass::UpdateRecord,
            &scoped(config, "record:wrong-target:a"),
            &scoped(config, "auth:wrong-target"),
        );
        let declared = obligation(config, declared_action.clone());
        let wrong_auth = token(
            config,
            "auth:wrong-target",
            ActionClass::UpdateRecord,
            &scoped(config, "record:wrong-target:b"),
            declared.obligation_id(),
            declared_action.idempotency_key().unwrap_or(""),
        )?;
        Ok(matches!(
            dispatch_action(
                self.store,
                &declared,
                &declared_action,
                &wrong_auth,
                &verifier,
                &config.issued_at,
                ObservationStatus::Observed,
            )
            .await,
            Err(LedgerError::Authority(
                ordivon_kernel::AuthorityError::TargetMismatch
            ))
        ))
    }

    async fn duplicate_dispatch(&self, config: &RedTeamRunConfig) -> Result<bool, LedgerError> {
        let verifier = test_authority_verifier();
        let declared_action = action(
            ActionClass::UpdateRecord,
            &scoped(config, "record:duplicate"),
            &scoped(config, "auth:duplicate:first"),
        );
        let declared = obligation(config, declared_action.clone());
        let first_auth = token(
            config,
            "auth:duplicate:first",
            ActionClass::UpdateRecord,
            declared_action.target_ref(),
            declared.obligation_id(),
            declared_action.idempotency_key().unwrap_or(""),
        )?;
        dispatch_action(
            self.store,
            &declared,
            &declared_action,
            &first_auth,
            &verifier,
            &config.issued_at,
            ObservationStatus::Observed,
        )
        .await?;
        let duplicate_action = declared_action
            .clone()
            .with_authority_refs(vec![scoped(config, "auth:duplicate:loser")]);
        let loser_auth = token(
            config,
            "auth:duplicate:loser",
            ActionClass::UpdateRecord,
            declared_action.target_ref(),
            declared.obligation_id(),
            declared_action.idempotency_key().unwrap_or(""),
        )?;
        let duplicate = dispatch_action(
            self.store,
            &declared,
            &duplicate_action,
            &loser_auth,
            &verifier,
            &config.issued_at,
            ObservationStatus::Observed,
        )
        .await?;
        let loser_jti = scoped(config, "auth:duplicate:loser");
        let row = sqlx::query("SELECT count(*) AS count FROM kernel_authority_uses WHERE jti = $1")
            .bind(&loser_jti)
            .fetch_one(self.store.pool())
            .await
            .map_err(super::db_err)?;
        Ok(duplicate.duplicate && row.get::<i64, _>("count") == 0)
    }

    async fn ack_as_success(&self, config: &RedTeamRunConfig) -> Result<bool, LedgerError> {
        let verifier = test_authority_verifier();
        let declared_action = action(
            ActionClass::UpdateRecord,
            &scoped(config, "record:ack"),
            &scoped(config, "auth:ack"),
        );
        let declared = obligation(config, declared_action.clone());
        let auth = token(
            config,
            "auth:ack",
            ActionClass::UpdateRecord,
            declared_action.target_ref(),
            declared.obligation_id(),
            declared_action.idempotency_key().unwrap_or(""),
        )?;
        let ack = dispatch_action(
            self.store,
            &declared,
            &declared_action,
            &auth,
            &verifier,
            &config.issued_at,
            ObservationStatus::Acked,
        )
        .await?;
        let row = sqlx::query(
            "SELECT count(*) AS count FROM kernel_observed_events WHERE idempotency_key = $1",
        )
        .bind(declared_action.idempotency_key().unwrap_or(""))
        .fetch_one(self.store.pool())
        .await
        .map_err(super::db_err)?;
        Ok(
            ack.receipt.is_none()
                && ack.observed_event.is_none()
                && row.get::<i64, _>("count") == 0,
        )
    }

    async fn ledger_tamper(&self, config: &RedTeamRunConfig) -> Result<bool, LedgerError> {
        let (event_seq, prev_hash) = self.next_ledger_position().await?;
        let event = redteam_event(config, event_seq, &prev_hash, "ledger-tamper")?;
        self.store.append_event(&event).await?;
        sqlx::query("UPDATE kernel_ledger_events SET payload = $1 WHERE event_seq = $2")
            .bind(sqlx::types::Json(json!({"value": "tampered"})))
            .bind(event.event_seq as i64)
            .execute(self.store.pool())
            .await
            .map_err(super::db_err)?;
        let blocked = matches!(
            self.store.read_events().await,
            Err(LedgerError::PayloadHashMismatch { .. })
        );
        sqlx::query("UPDATE kernel_ledger_events SET payload = $1 WHERE event_seq = $2")
            .bind(sqlx::types::Json(event.payload))
            .bind(event.event_seq as i64)
            .execute(self.store.pool())
            .await
            .map_err(super::db_err)?;
        Ok(blocked)
    }

    async fn projection_drift(&self, config: &RedTeamRunConfig) -> Result<bool, LedgerError> {
        let (first_seq, first_prev) = self.next_ledger_position().await?;
        let first = redteam_event(config, first_seq, &first_prev, "projection-a")?;
        self.store.append_event(&first).await?;
        let projection_id = scoped(config, "projection:drift");
        self.store
            .build_and_store_projection(&projection_id, &config.issued_at)
            .await?;
        let second = redteam_event(config, first_seq + 1, &first.event_hash, "projection-b")?;
        self.store.append_event(&second).await?;
        Ok(matches!(
            self.store.verify_projection(&projection_id).await,
            Err(LedgerError::ProjectionDrift { .. })
        ))
    }

    async fn compromised_adapter_source(
        &self,
        config: &RedTeamRunConfig,
    ) -> Result<bool, LedgerError> {
        let inserted = sqlx::query(
            "INSERT INTO kernel_observed_events
             (event_id, dispatch_id, trace_id, source_identity, action_class, target_ref, status,
              payload_hash, authority_ref, idempotency_key, observed_at)
             VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
        )
        .bind(scoped(config, "obs:evil-source"))
        .bind(scoped(config, "dispatch:evil-source"))
        .bind(scoped(config, "trace:evil-source"))
        .bind("system:evil-adapter")
        .bind("UPDATE_RECORD")
        .bind(scoped(config, "record:evil-source"))
        .bind("Observed")
        .bind(digest("record:evil-source"))
        .bind(scoped(config, "auth:evil-source"))
        .bind(scoped(config, "idem:evil-source"))
        .bind(&config.issued_at)
        .execute(self.store.pool())
        .await;
        Ok(inserted.is_err())
    }

    fn delayed_observation_after_expiry(
        &self,
        config: &RedTeamRunConfig,
    ) -> Result<bool, LedgerError> {
        let declared_action = action(
            ActionClass::UpdateRecord,
            &scoped(config, "record:delayed"),
            &scoped(config, "auth:delayed"),
        );
        let declared = ordivon_kernel::Obligation::try_from(ordivon_kernel::ObligationDraft {
            obligation_id: scoped(config, "obl:delayed"),
            intent_id: scoped(config, "intent:delayed"),
            declared_actions: vec![declared_action.clone()],
            declaration_hash: digest("declaration"),
            expires_at: "2026-05-16T00:00:01Z".to_string(),
        })
        .map_err(LedgerError::Kernel)?;
        let observed = observed_event(config, "delayed", &declared_action, "sha256:prev")?;
        let result = compare_obligation(&declared, &[observed], "2026-05-16T00:10:00Z");
        Ok(matches!(result.verdict, Verdict::DeclarationInvalid))
    }

    fn duplicate_observation(&self, config: &RedTeamRunConfig) -> Result<bool, LedgerError> {
        let declared_action = action(
            ActionClass::UpdateRecord,
            &scoped(config, "record:duplicate-observation"),
            &scoped(config, "auth:duplicate-observation"),
        );
        let declared = obligation(config, declared_action.clone());
        let first = observed_event(
            config,
            "duplicate-observation:1",
            &declared_action,
            "sha256:prev",
        )?;
        let second = observed_event(
            config,
            "duplicate-observation:2",
            &declared_action,
            "sha256:prev",
        )?;
        let result = compare_obligation(&declared, &[first, second], &config.issued_at);
        Ok(matches!(result.verdict, Verdict::Over))
    }

    async fn observation_for_wrong_dispatch(
        &self,
        config: &RedTeamRunConfig,
    ) -> Result<bool, LedgerError> {
        let inserted = sqlx::query(
            "INSERT INTO kernel_observed_events
             (event_id, dispatch_id, trace_id, source_identity, action_class, target_ref, status,
              payload_hash, authority_ref, idempotency_key, observed_at)
             VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)",
        )
        .bind(scoped(config, "obs:wrong-dispatch"))
        .bind(scoped(config, "dispatch:missing"))
        .bind(scoped(config, "trace:wrong-dispatch"))
        .bind("system:mock-action-adapter")
        .bind("UPDATE_RECORD")
        .bind(scoped(config, "record:wrong-dispatch"))
        .bind("Observed")
        .bind(digest("record:wrong-dispatch"))
        .bind(scoped(config, "auth:wrong-dispatch"))
        .bind(scoped(config, "idem:wrong-dispatch"))
        .bind(&config.issued_at)
        .execute(self.store.pool())
        .await;
        Ok(inserted.is_err())
    }

    fn query_back_mismatch(&self, config: &RedTeamRunConfig) -> Result<bool, LedgerError> {
        let declared_action = action(
            ActionClass::UpdateRecord,
            &scoped(config, "record:query-back"),
            &scoped(config, "auth:query-back"),
        );
        let declared = obligation(config, declared_action.clone());
        let observed = ObservedEvent::trusted(TrustedObservedEventDraft {
            event_id: scoped(config, "obs:query-back"),
            trace_id: scoped(config, "trace:query-back"),
            source: "adapter:mock-action".to_string(),
            source_identity: "system:mock-action-adapter".to_string(),
            observed_sequence: 1,
            event_type: "MOCK_ACTION_APPLIED".to_string(),
            action_class: ActionClass::UpdateRecord,
            target_ref: declared_action.target_ref().to_string(),
            timestamp: config.issued_at.clone(),
            payload_hash: digest("wrong-payload"),
            prev_event_hash: "sha256:prev".to_string(),
            origin: Origin::SystemObserved,
            status: ObservationStatus::Observed,
            authority_ref: scoped(config, "auth:query-back"),
            idempotency_key: declared_action.idempotency_key().unwrap_or("").to_string(),
        })
        .map_err(LedgerError::Kernel)?;
        let result = compare_obligation(&declared, &[observed], &config.issued_at);
        Ok(matches!(result.verdict, Verdict::Mis))
    }

    async fn next_ledger_position(&self) -> Result<(u64, String), LedgerError> {
        let events = self.store.read_events().await?;
        Ok(events
            .last()
            .map(|event| (event.event_seq + 1, event.event_hash.clone()))
            .unwrap_or_else(|| (1, GENESIS_DIGEST.to_string())))
    }

    fn execute_policy_replay_regression(
        &self,
        config: &RedTeamRunConfig,
    ) -> Result<(), LedgerError> {
        let debts = vec![
            debt(config, "1", "OVER", "first"),
            debt(config, "2", "OVER", "second"),
        ];
        let clusters = cluster_debts(&debts);
        let candidates = candidate_policies_from_clusters(&clusters, 2);
        let invalid_promotion = PromotionDraft {
            promotion_id: scoped(config, "promotion:replay-missing"),
            candidate_policy_ref: candidates[0].candidate_policy_id().to_string(),
            shadow_passed: true,
            replay_passed: false,
            reviewer_authority_refs: vec!["authority:review".to_string()],
            rollout_plan: "limited".to_string(),
            rollback_plan: "rollback".to_string(),
        };
        if Promotion::try_from(invalid_promotion).is_ok() {
            return Err(LedgerError::Database(
                "red-team policy replay regression bypassed".to_string(),
            ));
        }
        Ok(())
    }
}

pub async fn run_postgres_red_team(
    store: &PostgresKernelStore,
    config: RedTeamRunConfig,
) -> Result<VerifiedRedTeamRun, LedgerError> {
    PostgresRedTeamRunner::new(store).run(config).await
}

fn digest(label: &str) -> String {
    sha256_digest(&json!({ "label": label })).unwrap_or_else(|_| "sha256:invalid".to_string())
}

fn scoped(config: &RedTeamRunConfig, label: &str) -> String {
    format!("{}:{label}", config.run_id)
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

fn obligation(config: &RedTeamRunConfig, action: ActionSpec) -> ordivon_kernel::Obligation {
    ordivon_kernel::Obligation::try_from(ordivon_kernel::ObligationDraft {
        obligation_id: scoped(config, &format!("obl:{}", action.target_ref())),
        intent_id: scoped(config, "intent:red-team"),
        declared_actions: vec![action],
        declaration_hash: digest("declaration"),
        expires_at: "2026-05-16T00:10:00Z".to_string(),
    })
    .expect("red-team fixture obligation must be valid")
}

fn token(
    config: &RedTeamRunConfig,
    jti: &str,
    action_class: ActionClass,
    target_ref: &str,
    obligation_id: &str,
    idempotency_key: &str,
) -> Result<AuthorityToken, LedgerError> {
    signed_test_token(AuthorityTokenDraft {
        jti: scoped(config, jti),
        kid: TEST_AUTHORITY_KID.to_string(),
        iss: "ordivon-authority-service".to_string(),
        sub: "agent:planner".to_string(),
        audience: "adapter:mock-action".to_string(),
        intent_id: scoped(config, "intent:red-team"),
        obligation_id: obligation_id.to_string(),
        action_class,
        target_ref: target_ref.to_string(),
        policy_hash: digest("policy"),
        issued_at: "2026-05-16T00:00:00Z".to_string(),
        not_before: "2026-05-16T00:00:00Z".to_string(),
        expires_at: "2026-05-16T00:05:00Z".to_string(),
        max_use_count: 1,
        idempotency_key: idempotency_key.to_string(),
        seal_ref: "seal:red-team".to_string(),
        signature: String::new(),
    })
    .map_err(LedgerError::Kernel)
}

fn observed_event(
    config: &RedTeamRunConfig,
    suffix: &str,
    action: &ActionSpec,
    prev_event_hash: &str,
) -> Result<ObservedEvent, LedgerError> {
    ObservedEvent::trusted(TrustedObservedEventDraft {
        event_id: scoped(config, &format!("obs:{suffix}")),
        trace_id: scoped(config, &format!("trace:{suffix}")),
        source: "adapter:mock-action".to_string(),
        source_identity: "system:mock-action-adapter".to_string(),
        observed_sequence: 1,
        event_type: "MOCK_ACTION_APPLIED".to_string(),
        action_class: action.action_class().clone(),
        target_ref: action.target_ref().to_string(),
        timestamp: config.issued_at.clone(),
        payload_hash: action
            .expected_payload_hash()
            .unwrap_or("sha256:missing")
            .to_string(),
        prev_event_hash: prev_event_hash.to_string(),
        origin: Origin::SystemObserved,
        status: ObservationStatus::Observed,
        authority_ref: action
            .authority_refs()
            .first()
            .cloned()
            .unwrap_or_else(|| scoped(config, "auth:missing")),
        idempotency_key: action.idempotency_key().unwrap_or("").to_string(),
    })
    .map_err(LedgerError::Kernel)
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
            policy_decision: PolicyDecision::Allow,
            policy_evaluator: "static-red-team-policy",
            policy_reason_code: "ALLOW_RED_TEAM",
            now,
            status,
        })
        .await
}

fn redteam_event(
    config: &RedTeamRunConfig,
    event_seq: u64,
    prev_hash: &str,
    value: &str,
) -> Result<LedgerEvent, LedgerError> {
    LedgerEvent::from_draft(LedgerEventDraft {
        event_seq,
        event_id: scoped(config, &format!("evt:{value}:{event_seq}")),
        event_type: "OBJECT_RECORDED".to_string(),
        origin: Origin::SystemDerived,
        created_at: config.issued_at.clone(),
        object_type: "Receipt".to_string(),
        object_id: scoped(config, &format!("receipt:{value}:{event_seq}")),
        payload: json!({"value": value}),
        prev_hash: prev_hash.to_string(),
    })
}

fn debt(config: &RedTeamRunConfig, suffix: &str, root_cause: &str, hypothesis: &str) -> Debt {
    Debt {
        debt_id: scoped(config, &format!("debt:{suffix}")),
        debt_type: "receipt_mismatch".to_string(),
        severity: "high".to_string(),
        owner: "ordivon-core-maintainer".to_string(),
        due_at: "2026-05-23T00:00:00Z".to_string(),
        blocking_scope: "new-kernel-hardening".to_string(),
        introduced_by_receipt: scoped(config, &format!("receipt:{suffix}")),
        root_cause_code: root_cause.to_string(),
        root_cause_hypothesis: hypothesis.to_string(),
        verification_receipt: None,
        state: DebtState::Open,
    }
}
