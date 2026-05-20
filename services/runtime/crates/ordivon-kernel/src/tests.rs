use super::*;
use crate::test_support::{
    signed_test_token, test_authority_verifier, test_seal_key_resolver, test_seal_signer,
    TEST_AUTHORITY_KID,
};
use serde_json::json;

fn digest(label: &str) -> String {
    sha256_digest(&json!({ "label": label })).unwrap()
}

#[test]
fn canonical_json_sorts_object_keys() {
    let left = json!({"b": 2, "a": {"z": 1, "m": 0}});
    let right = json!({"a": {"m": 0, "z": 1}, "b": 2});

    assert_eq!(
        canonical_json(&left).unwrap(),
        canonical_json(&right).unwrap()
    );
    assert_eq!(
        sha256_digest(&left).unwrap(),
        sha256_digest(&right).unwrap()
    );
}

fn action(action_class: ActionClass, target_ref: &str) -> ActionSpec {
    let mut action = ActionSpec::new(
        action_class,
        target_ref,
        ApprovalMode::Policy,
        format!("idem:{target_ref}"),
    );
    action.authority_refs = vec![format!("auth:{target_ref}")];
    action.expected_payload_hash = Some(digest(target_ref));
    action
}

fn obligation(actions: Vec<ActionSpec>) -> Obligation {
    Obligation {
        obligation_id: "obl_1".to_string(),
        intent_id: "intent_1".to_string(),
        declared_actions: actions,
        declaration_hash: "sha256:declaration".to_string(),
        expires_at: "2026-05-16T00:10:00Z".to_string(),
    }
}

fn observed(
    action_class: ActionClass,
    target_ref: &str,
    sequence: u64,
    status: ObservationStatus,
) -> ObservedEvent {
    ObservedEvent::trusted(TrustedObservedEventDraft {
        event_id: format!("evt_{sequence}_{target_ref}"),
        trace_id: "trace_1".to_string(),
        source: "adapter:mock-action".to_string(),
        source_identity: "system:mock-action-adapter".to_string(),
        observed_sequence: sequence,
        event_type: "RESOURCE_CHANGED".to_string(),
        action_class,
        target_ref: target_ref.to_string(),
        timestamp: "2026-05-16T00:00:01Z".to_string(),
        payload_hash: digest(target_ref),
        prev_event_hash: "sha256:prev".to_string(),
        origin: Origin::SystemObserved,
        status,
        authority_ref: format!("auth:{target_ref}"),
        idempotency_key: format!("idem:{target_ref}"),
    })
    .unwrap()
}

#[test]
fn ai_written_cannot_emit_observed_event() {
    let event = ObservedEvent::trusted(TrustedObservedEventDraft {
        event_id: "evt_1".to_string(),
        trace_id: "trace_1".to_string(),
        source: "ai".to_string(),
        source_identity: "codex".to_string(),
        observed_sequence: 1,
        event_type: "RESOURCE_CHANGED".to_string(),
        action_class: ActionClass::UpdateRecord,
        target_ref: "record:1".to_string(),
        timestamp: "2026-05-16T00:00:00Z".to_string(),
        payload_hash: digest("record:1"),
        prev_event_hash: "sha256:0".to_string(),
        origin: Origin::AiWritten,
        status: ObservationStatus::Observed,
        authority_ref: "auth:record:1".to_string(),
        idempotency_key: "idem:record:1".to_string(),
    });

    assert!(matches!(
        event,
        Err(KernelError::ForgedObservedEvent { .. })
    ));
}

#[test]
fn observed_event_requires_source_identity_and_target() {
    let event = ObservedEvent::trusted(TrustedObservedEventDraft {
        event_id: "evt_1".to_string(),
        trace_id: "trace_1".to_string(),
        source: "adapter:mock-action".to_string(),
        source_identity: String::new(),
        observed_sequence: 1,
        event_type: "RESOURCE_CHANGED".to_string(),
        action_class: ActionClass::UpdateRecord,
        target_ref: "record:1".to_string(),
        timestamp: "2026-05-16T00:00:00Z".to_string(),
        payload_hash: digest("record:1"),
        prev_event_hash: "sha256:0".to_string(),
        origin: Origin::SystemObserved,
        status: ObservationStatus::Observed,
        authority_ref: "auth:record:1".to_string(),
        idempotency_key: "idem:record:1".to_string(),
    });
    assert_eq!(event, Err(KernelError::MissingTrustedSourceIdentity));
}

#[test]
fn serde_inputs_cannot_bypass_validated_core_constructors() {
    let forged_observation = json!({
        "eventId": "evt_forged",
        "traceId": "trace_1",
        "source": "ai",
        "sourceIdentity": "codex",
        "observedSequence": 1,
        "eventType": "RESOURCE_CHANGED",
        "actionClass": "UPDATE_RECORD",
        "targetRef": "record:1",
        "timestamp": "2026-05-16T00:00:00Z",
        "payloadHash": digest("record:1"),
        "prevEventHash": "sha256:0",
        "origin": "AI_WRITTEN",
        "status": "Observed",
        "authorityRef": "auth:record:1",
        "idempotencyKey": "idem:record:1"
    });
    assert!(serde_json::from_value::<ObservedEvent>(forged_observation).is_err());

    let invalid_token = json!({
        "jti": "auth:bad",
        "kid": TEST_AUTHORITY_KID,
        "iss": "ordivon-authority-service",
        "sub": "agent:planner",
        "audience": "adapter:mock-action",
        "intentId": "intent_1",
        "obligationId": "obl_1",
        "actionClass": "UPDATE_RECORD",
        "targetRef": "record:1",
        "policyHash": digest("policy"),
        "issuedAt": "2026-05-16T00:00:00Z",
        "notBefore": "2026-05-16T00:00:00Z",
        "expiresAt": "2026-05-16T00:05:00Z",
        "maxUseCount": 2,
        "idempotencyKey": "idem:record:1",
        "sealRef": "seal_1",
        "signature": ""
    });
    assert!(serde_json::from_value::<AuthorityToken>(invalid_token).is_err());

    let handwritten_receipt = json!({
        "receiptId": "receipt:fake",
        "intentId": "intent_1",
        "obligationId": "obl_1",
        "verdict": "ExactMatch",
        "observedEventRefs": [],
        "stateTransitions": [],
        "debtRefs": [],
        "issuedBy": "human",
        "issuedAt": "2026-05-16T00:00:00Z",
        "comparatorDigest": ""
    });
    assert!(serde_json::from_value::<Receipt>(handwritten_receipt).is_err());

    let handwritten_success_receipt = json!({
        "receiptId": "receipt:fake-success",
        "intentId": "intent_1",
        "obligationId": "obl_1",
        "verdict": "ExactMatch",
        "observedEventRefs": ["evt_1"],
        "stateTransitions": ["Receipt.Pending->Receipt.Issued"],
        "debtRefs": [],
        "issuedBy": COMPARATOR_ISSUER,
        "issuedAt": "2026-05-16T00:00:00Z",
        "comparatorDigest": digest("receipt")
    });
    assert!(serde_json::from_value::<Receipt>(handwritten_success_receipt).is_err());

    let handwritten_active_policy = json!({
        "policyId": "policy:bad",
        "candidatePolicyId": "candidate:bad",
        "policyHash": digest("policy"),
        "scope": "new-kernel-hardening",
        "status": "Active"
    });
    assert!(serde_json::from_value::<Policy>(handwritten_active_policy).is_err());

    let unverifiable_closure = json!({
        "closureId": "closure:bad",
        "targetRef": "debt:bad",
        "closureReason": "fixed",
        "verificationReceipt": null,
        "reopenConditions": []
    });
    assert!(serde_json::from_value::<Closure>(unverifiable_closure).is_err());

    let empty_target_action = json!({
        "actionClass": "UPDATE_RECORD",
        "targetRef": "",
        "cardinality": {"min": 1, "max": 1},
        "orderConstraint": "declared_order",
        "approvalMode": "policy",
        "successPredicate": "mock success"
    });
    assert!(serde_json::from_value::<ActionSpec>(empty_target_action).is_err());

    let empty_success_predicate = json!({
        "actionClass": "UPDATE_RECORD",
        "targetRef": "record:1",
        "cardinality": {"min": 1, "max": 1},
        "orderConstraint": "declared_order",
        "approvalMode": "policy",
        "successPredicate": ""
    });
    assert!(serde_json::from_value::<ActionSpec>(empty_success_predicate).is_err());

    let invalid_obligation = json!({
        "obligationId": "obl_1",
        "intentId": "intent_1",
        "declaredActions": [],
        "declarationHash": digest("declaration"),
        "expiresAt": "2026-05-16T00:10:00Z"
    });
    assert!(serde_json::from_value::<Obligation>(invalid_obligation).is_err());

    let expired_obligation = obligation(vec![action(ActionClass::UpdateRecord, "record:1")]);
    assert!(expired_obligation
        .validate_at("2026-05-16T00:10:00Z")
        .is_err());

    let hand_written_candidate = json!({
        "candidatePolicyId": "candidate:bad",
        "scope": "new-kernel-hardening",
        "ruleText": "enforce directly",
        "policyModule": null,
        "evidenceRefs": [],
        "metricsGate": {},
        "status": "Review"
    });
    assert!(serde_json::from_value::<CandidatePolicy>(hand_written_candidate).is_err());

    let missing_rollback_promotion = json!({
        "promotionId": "promotion:bad",
        "candidatePolicyRef": "candidate:bad",
        "shadowPassed": true,
        "replayPassed": true,
        "reviewerAuthorityRefs": ["authority:review"],
        "rolloutPlan": "limited",
        "rollbackPlan": ""
    });
    assert!(serde_json::from_value::<Promotion>(missing_rollback_promotion).is_err());

    let missing_expiry_suppression = json!({
        "suppressionId": "suppression:bad",
        "targetRef": "debt:bad",
        "reason": "noise",
        "approvedBy": "authority:review",
        "expiresAt": "",
        "reviewAt": "2026-05-20T00:00:00Z"
    });
    assert!(serde_json::from_value::<Suppression>(missing_expiry_suppression).is_err());
}

#[test]
fn comparator_exact_match_for_every_action_class() {
    for action_class in ActionClass::all() {
        let action = action(action_class.clone(), "target:1");
        let result = compare_obligation(
            &obligation(vec![action]),
            &[observed(
                action_class,
                "target:1",
                1,
                ObservationStatus::Observed,
            )],
            "2026-05-16T00:00:02Z",
        );

        assert_eq!(result.verdict, Verdict::ExactMatch);
        assert!(result.receipt.debt_refs.is_empty());
        assert!(result.receipt.validate_comparator_issued().is_ok());
    }
}

#[test]
fn comparator_detects_duplicate_same_target_as_over() {
    let action = action(ActionClass::UpdateRecord, "record:1");
    let result = compare_obligation(
        &obligation(vec![action]),
        &[
            observed(
                ActionClass::UpdateRecord,
                "record:1",
                1,
                ObservationStatus::Observed,
            ),
            observed(
                ActionClass::UpdateRecord,
                "record:1",
                2,
                ObservationStatus::Observed,
            ),
        ],
        "2026-05-16T00:00:02Z",
    );

    assert_eq!(result.verdict, Verdict::Over);
    assert!(result
        .findings
        .iter()
        .any(|finding| finding.finding_type == "ACTION_CARDINALITY_EXCEEDED"));
}

#[test]
fn comparator_detects_under_over_mis_and_unverifiable() {
    let declared = obligation(vec![action(ActionClass::UpdateRecord, "record:1")]);
    assert_eq!(
        compare_obligation(&declared, &[], "2026-05-16T00:00:02Z").verdict,
        Verdict::Unverifiable
    );
    assert_eq!(
        compare_obligation(
            &declared,
            &[observed(
                ActionClass::UpdateRecord,
                "record:2",
                1,
                ObservationStatus::Observed
            )],
            "2026-05-16T00:00:02Z"
        )
        .verdict,
        Verdict::Mis
    );
    assert_eq!(
        compare_obligation(
            &declared,
            &[observed(
                ActionClass::UpdateRecord,
                "record:1",
                1,
                ObservationStatus::Acked
            )],
            "2026-05-16T00:00:02Z"
        )
        .verdict,
        Verdict::Unverifiable
    );
}

#[test]
fn comparator_matrix_covers_every_action_class() {
    for action_class in ActionClass::all() {
        let primary = action(action_class.clone(), "matrix:primary");
        let missing = action(action_class.clone(), "matrix:missing");
        let declared = obligation(vec![primary.clone(), missing]);

        let exact = compare_obligation(
            &obligation(vec![primary.clone()]),
            &[observed(
                action_class.clone(),
                "matrix:primary",
                1,
                ObservationStatus::Observed,
            )],
            "2026-05-16T00:00:02Z",
        );
        assert_eq!(exact.verdict, Verdict::ExactMatch);

        let under = compare_obligation(
            &declared,
            &[observed(
                action_class.clone(),
                "matrix:primary",
                1,
                ObservationStatus::Observed,
            )],
            "2026-05-16T00:00:02Z",
        );
        assert_eq!(under.verdict, Verdict::Under);

        let over = compare_obligation(
            &obligation(vec![primary.clone()]),
            &[
                observed(
                    action_class.clone(),
                    "matrix:primary",
                    1,
                    ObservationStatus::Observed,
                ),
                observed(
                    action_class.clone(),
                    "matrix:primary",
                    2,
                    ObservationStatus::Observed,
                ),
            ],
            "2026-05-16T00:00:02Z",
        );
        assert_eq!(over.verdict, Verdict::Over);

        let mis = compare_obligation(
            &obligation(vec![primary.clone()]),
            &[observed(
                action_class.clone(),
                "matrix:wrong-target",
                1,
                ObservationStatus::Observed,
            )],
            "2026-05-16T00:00:02Z",
        );
        assert_eq!(mis.verdict, Verdict::Mis);

        let unverifiable = compare_obligation(
            &obligation(vec![primary]),
            &[observed(
                action_class,
                "matrix:primary",
                1,
                ObservationStatus::Acked,
            )],
            "2026-05-16T00:00:02Z",
        );
        assert_eq!(unverifiable.verdict, Verdict::Unverifiable);
    }
}

#[test]
fn comparator_detects_payload_and_authority_mismatch() {
    let declared = obligation(vec![action(ActionClass::UpdateRecord, "record:1")]);
    let mut event = observed(
        ActionClass::UpdateRecord,
        "record:1",
        1,
        ObservationStatus::Observed,
    );
    event.payload_hash = digest("wrong");
    assert_eq!(
        compare_obligation(&declared, &[event], "2026-05-16T00:00:02Z").verdict,
        Verdict::Mis
    );
}

fn token() -> AuthorityToken {
    signed_test_token(AuthorityTokenDraft {
        jti: "auth_1".to_string(),
        kid: TEST_AUTHORITY_KID.to_string(),
        iss: "ordivon-authority-service".to_string(),
        sub: "agent:planner".to_string(),
        audience: "adapter:mock-action".to_string(),
        intent_id: "intent_1".to_string(),
        obligation_id: "obl_1".to_string(),
        action_class: ActionClass::UpdateRecord,
        target_ref: "record:1".to_string(),
        policy_hash: digest("policy"),
        issued_at: "2026-05-16T00:00:00Z".to_string(),
        not_before: "2026-05-16T00:00:00Z".to_string(),
        expires_at: "2026-05-16T00:05:00Z".to_string(),
        max_use_count: 1,
        idempotency_key: "idem:record:1".to_string(),
        seal_ref: "seal_1".to_string(),
        signature: String::new(),
    })
    .unwrap()
}

#[test]
fn authority_token_signature_and_replay_are_validated() {
    let verifier = test_authority_verifier();
    let mut ledger = AuthorityUseLedger::default();
    let token = token();
    assert!(ledger
        .validate_and_consume(AuthorityValidationRequest {
            token: &token,
            verifier: &verifier,
            intent_id: "intent_1",
            obligation_id: "obl_1",
            action_class: &ActionClass::UpdateRecord,
            target_ref: "record:1",
            policy_hash: &digest("policy"),
            idempotency_key: "idem:record:1",
            now: "2026-05-16T00:01:00Z",
            policy_decision: PolicyDecision::Allow,
        })
        .is_ok());
    assert!(matches!(
        ledger.validate_and_consume(AuthorityValidationRequest {
            token: &token,
            verifier: &verifier,
            intent_id: "intent_1",
            obligation_id: "obl_1",
            action_class: &ActionClass::UpdateRecord,
            target_ref: "record:1",
            policy_hash: &digest("policy"),
            idempotency_key: "idem:record:1",
            now: "2026-05-16T00:01:01Z",
            policy_decision: PolicyDecision::Allow,
        }),
        Err(AuthorityError::ReplayedToken { .. })
    ));
}

#[test]
fn authority_token_rejects_bad_signature_and_policy_deny() {
    let verifier = test_authority_verifier();
    let mut bad = token();
    bad.target_ref = "record:2".to_string();
    let mut ledger = AuthorityUseLedger::default();
    assert_eq!(
        ledger.validate_and_consume(AuthorityValidationRequest {
            token: &bad,
            verifier: &verifier,
            intent_id: "intent_1",
            obligation_id: "obl_1",
            action_class: &ActionClass::UpdateRecord,
            target_ref: "record:2",
            policy_hash: &digest("policy"),
            idempotency_key: "idem:record:1",
            now: "2026-05-16T00:01:00Z",
            policy_decision: PolicyDecision::Allow,
        }),
        Err(AuthorityError::InvalidSignature)
    );

    let valid = token();
    assert_eq!(
        ledger.validate_and_consume(AuthorityValidationRequest {
            token: &valid,
            verifier: &verifier,
            intent_id: "intent_1",
            obligation_id: "obl_1",
            action_class: &ActionClass::UpdateRecord,
            target_ref: "record:1",
            policy_hash: &digest("policy"),
            idempotency_key: "idem:record:1",
            now: "2026-05-16T00:01:00Z",
            policy_decision: PolicyDecision::Deny,
        }),
        Err(AuthorityError::PolicyDenied)
    );
}

#[test]
fn acked_side_effect_is_not_success_evidence() {
    let record = SideEffectRecord::acked(
        ActionClass::UpdateRecord,
        "record:1",
        "intent_1:obl_1:record:1",
    );

    assert!(!record.is_success_verdict_source());
}

fn debt(id: &str, severity: &str, root_cause_code: &str) -> Debt {
    Debt {
        debt_id: id.to_string(),
        debt_type: "receipt_mismatch".to_string(),
        severity: severity.to_string(),
        owner: "ordivon-core-maintainer".to_string(),
        due_at: "2026-05-23T00:00:00Z".to_string(),
        blocking_scope: "new-kernel-hardening".to_string(),
        introduced_by_receipt: format!("receipt:{id}"),
        root_cause_code: root_cause_code.to_string(),
        root_cause_hypothesis: "Free text does not affect fingerprint".to_string(),
        verification_receipt: None,
        state: DebtState::Open,
    }
}

#[test]
fn debt_fingerprint_ignores_free_text_and_clusters_stably() {
    let mut first = debt("debt:1", "medium", "OVER");
    let mut second = debt("debt:2", "high", "OVER");
    second.root_cause_hypothesis = "different prose".to_string();
    assert_eq!(debt_fingerprint(&first), debt_fingerprint(&second));
    first.root_cause_code = "MIS".to_string();
    assert_ne!(debt_fingerprint(&first), debt_fingerprint(&second));

    let clusters = cluster_debts(&[debt("debt:1", "medium", "OVER"), second]);
    let candidates = candidate_policies_from_clusters(&clusters, 2);
    assert_eq!(clusters.len(), 1);
    assert_eq!(candidates.len(), 1);
    assert!(!candidates[0].can_enforce_directly());
}

#[test]
fn closure_without_verification_and_hand_written_active_policy_are_rejected() {
    let mut debt = debt("debt:1", "high", "OVER");
    debt.state = DebtState::Closed;
    assert_eq!(
        debt.validate_closure(),
        Err(GovernanceOpsError::MissingVerificationReceipt)
    );
    let policy = Policy {
        policy_id: "policy:hand-written".to_string(),
        candidate_policy_id: "candidate:1".to_string(),
        policy_hash: digest("policy"),
        scope: "new-kernel-hardening".to_string(),
        status: PolicyStatus::Active,
    };
    assert_eq!(
        policy.validate_not_hand_written_active(),
        Err(GovernanceOpsError::HandWrittenActivePolicy)
    );
}

#[test]
fn promotion_requires_shadow_replay_review_and_rollback() {
    let candidate = CandidatePolicy {
        candidate_policy_id: "candidate-policy:1".to_string(),
        scope: "new-kernel-hardening".to_string(),
        rule_text: "deny undeclared mutating actions".to_string(),
        policy_module: None,
        evidence_refs: vec!["debt:1".to_string()],
        metrics_gate: json!({"maxFalsePositiveRate": 0}),
        status: CandidatePolicyStatus::Review,
    };
    let incomplete = Promotion {
        promotion_id: "promotion:1".to_string(),
        candidate_policy_ref: candidate.candidate_policy_id.clone(),
        shadow_passed: true,
        replay_passed: false,
        reviewer_authority_refs: vec!["authority:review".to_string()],
        rollout_plan: "limited rollout".to_string(),
        rollback_plan: "rollback to previous policy hash".to_string(),
    };

    assert_eq!(
        promote_candidate_policy(&candidate, &incomplete, digest("policy")),
        Err(GovernanceOpsError::PromotionPreconditionsNotMet)
    );

    let complete = Promotion {
        replay_passed: true,
        ..incomplete
    };
    let policy = promote_candidate_policy(&candidate, &complete, digest("policy")).unwrap();
    assert_eq!(policy.status, PolicyStatus::LimitedRollout);
}

#[test]
fn dogfood_seal_must_match_verified_red_team_run() {
    let run = verified_red_team_run(
        "red-team-run:1",
        vec![RedTeamOutcome {
            scenario_id: "rt:ai-forged-observed-event".to_string(),
            blocked: true,
            actual_verdict: Some(Verdict::DeclarationInvalid),
            finding: "blocked forged observation".to_string(),
        }],
        "2026-05-17T00:00:00Z",
    );
    let mut seal = build_dogfood_seal("dogfood-seal:1", &run);
    verify_dogfood_seal(&seal, &run).unwrap();

    seal.critical_bypasses = 0;
    seal.scenario_count = 99;
    assert!(verify_dogfood_seal(&seal, &run).is_err());
}

#[test]
fn signed_dogfood_seal_verifies_key_lifecycle_and_tamper() {
    let run = verified_red_team_run(
        "red-team-run:signed",
        vec![RedTeamOutcome {
            scenario_id: "rt:token-replay".to_string(),
            blocked: true,
            actual_verdict: None,
            finding: "blocked replay".to_string(),
        }],
        "2026-05-17T00:00:00Z",
    );
    let seal = build_dogfood_seal("dogfood-seal:signed", &run);
    let signer = test_seal_signer();
    let resolver = test_seal_key_resolver(KeyStatus::Active);
    let signed = sign_dogfood_seal(&seal, &signer, &resolver, "2026-05-17T00:00:00Z").unwrap();
    verify_signed_dogfood_seal(&signed, &run, &resolver, "2026-05-17T00:00:00Z").unwrap();

    let mut tampered = signed.clone();
    tampered.critical_bypasses = 1;
    assert!(
        verify_signed_dogfood_seal(&tampered, &run, &resolver, "2026-05-17T00:00:00Z").is_err()
    );

    let revoked = test_seal_key_resolver(KeyStatus::Revoked);
    assert!(verify_signed_dogfood_seal(&signed, &run, &revoked, "2026-05-17T00:00:00Z").is_err());
}
